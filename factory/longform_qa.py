#!/usr/bin/env python3
"""Offline final-encode review, including B6/E4 and H15/H16 (2026-11-07).

CEO caught; CTO missed. Existing episode/package inputs are read-only.
"""
from pathlib import Path
import os,sys
ROOT=Path(__file__).resolve().parents[1]
PYTHON=ROOT/'.venv/bin/python'
if Path(sys.prefix)!=ROOT/'.venv' and PYTHON.exists():
    os.execv(str(PYTHON),[str(PYTHON),__file__,*sys.argv[1:]])
import argparse,json,traceback
from review_gates import load_review,evaluate,write_json,LIMIT,reuse_measurements,Review,b6,read_json
from gates import finalize_review

def h15_h16_only(video,out,shots=None,script=None,subtitles=None,format='longform'):
    """Read-only existing-media diagnostics; never issues READY or an approval."""
    from review_gates import h15,h16,ocr_frames
    data=read_json(shots) if shots else []
    doc=data if isinstance(data,dict) else {}
    c=Review(Path(video),Path(out),format,data if isinstance(data,list) else doc.get('shots',[]),
             doc.get('subtitles',doc.get('captions',doc.get('subtitle_cues',[]))),[],Path(script).read_text() if script else '','')
    files=[Path(p).resolve() for p in subtitles or []]
    if shots:
        root=Path(shots).parent
        files.extend(p.resolve() for p in [root/'subtitles.srt',root/'timeline.json',root/'captions.json'] if p.is_file())
        c.bind(shots)
    if script:c.bind(script)
    c.config['subtitle_files']=list(map(str,dict.fromkeys(files)))
    c.normalize()
    # Only the one-second/shot/overview evidence is decoded here. The full
    # review still performs its existing exhaustive frame and OCR measurements.
    gates={}
    try:gates['H15']=h15(c)
    except Exception as e:gates['H15']=dict(status='FAIL',review_state='DECIDED',evidence=dict(error=str(e)))
    # Reuse local OCR implementation on sampled existing frames as a backup.
    coverage='H15 representative/motion/10 s overview samples only; full review OCR remains every frame'
    ocr_frames(c,coverage=coverage)
    try:gates['H16']=h16(c)
    except Exception as e:gates['H16']=dict(status='FAIL',review_state='DECIDED',evidence=dict(error=str(e),hits=[]))
    for p in sorted(out.rglob('*')):
        if p.is_file():
            from review_gates import digest
            c.artifacts[str(p.resolve())]=digest(p)
    report=dict(ready=False,scope='H15/H16 only',format=format,video=str(c.video),gates=gates,
                inputs=c.inputs,evidence_sha256=c.artifacts,network=False,uploads=False)
    write_json(out/'h15_h16_qa.json',report)
    print(json.dumps(dict(output=str(out),gates={k:v['status'] for k,v in gates.items()},
        automatic_repetition_fail=gates['H15']['evidence'].get('repetition_fail'),
        presenter_candidates=len(gates['H15']['evidence'].get('presenter_candidates',[])),
        numeral_hits=len(gates['H16']['evidence']['hits'])),ensure_ascii=False),flush=True)
    return 2 if any(g['status'] in {'FAIL','INPUT_MISSING'} for g in gates.values()) else 0

def new_output(label):
    parent=Path(__file__).resolve().parent/'review_runs';parent.mkdir(exist_ok=True)
    for i in range(1,100000):
        p=parent/f'{label}_{i:03}'
        try:p.mkdir();return p
        except FileExistsError:continue
    raise RuntimeError('No available output directory')

def edge_only(video,out,shots=None):
    """Read-only video scan. Partial review never creates READY or CTO approval."""
    data=read_json(shots) if shots else []
    c=Review(video,out,'longform',data if isinstance(data,list) else data['shots'],[],[],'','')
    c.normalize();gate=b6(c)
    write_json(out/'edge_fill_qa.json',dict(ready=False,scope='B6 only',video=str(c.video),gates={'B6':gate},network=False,uploads=False))
    print(json.dumps(dict(output=str(out),gate='B6',status=gate['status'],
                          sampled_frames=gate['evidence']['sampled_frames'],
                          max_sample_gap_s=gate['evidence']['max_sample_gap_s'],
                          intervals=gate['evidence']['intervals']),ensure_ascii=False),flush=True)
    return 0 if gate['status']=='PASS' else 2

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('video',type=Path);p.add_argument('--shots',type=Path)
    p.add_argument('--script',type=Path);p.add_argument('--facts',type=Path,nargs='+',action='extend')
    p.add_argument('--edge-fill-only',action='store_true',help='Only B6: decode existing video, no ASR/render/upload; --shots optionally maps hits')
    p.add_argument('--h15-h16-only',action='store_true',help='Only composition/presenter/subtitle checks on existing video; no ASR/render/upload or approval')
    p.add_argument('--subtitles',type=Path,nargs='+',action='extend',help='Additional SRT/subtitle JSON/labelled script sources for H16')
    p.add_argument('--alignment',type=Path);p.add_argument('--review-inputs',type=Path)
    p.add_argument('--measurement-cache',type=Path,help='Verified factory review ASR/OCR for identical video; frames are remeasured')
    p.add_argument('--out',type=Path,help='NEW directory under factory/review_runs, never an existing episode/package')
    p.add_argument('--resume',type=Path,help='Recheck a previously generated factory review directory, retaining CTO signoffs')
    p.add_argument('--signoffs',type=Path,help='CTO-authored JSON {cto_signoffs: {item: signature}}')
    a=p.parse_args()
    if a.edge_fill_only and a.h15_h16_only:p.error('Select one partial review mode')
    partial=a.edge_fill_only or a.h15_h16_only
    if not partial and not all([a.shots,a.script,a.facts]):p.error('--shots, --script and --facts are required for full review')
    if partial and (a.resume or a.signoffs or a.measurement_cache):p.error('Partial reviews need a new result directory, without signoffs or measurement cache')
    if a.out and a.resume:p.error('--out and --resume are exclusive')
    if a.resume:
        out=a.resume.resolve()
        if not out.is_relative_to(Path(__file__).resolve().parent/'review_runs') or not (out/'qa.json').is_file():p.error('--resume must be an existing factory/review_runs result')
        prior=json.loads((out/'qa.json').read_text())
    else:
        out=a.out.resolve() if a.out else new_output(a.video.stem)
        if a.out:
            if out.exists():p.error('--out must not exist')
            if not out.is_relative_to(Path(__file__).resolve().parent/'review_runs'):p.error('--out must be inside factory/review_runs/')
            out.mkdir(parents=True)
        prior={}
    if a.signoffs:prior=json.loads(a.signoffs.read_text())
    print('REVIEW_OUTPUT',out,flush=True)
    (out/'READY').unlink(missing_ok=True)
    if a.edge_fill_only:return edge_only(a.video,out,a.shots)
    if a.h15_h16_only:return h15_h16_only(a.video,out,a.shots,a.script,a.subtitles)
    try:
        c=load_review(a.video,out,a.shots,a.script,a.facts,a.alignment,a.review_inputs)
        c.config.setdefault('subtitle_files',[]).extend(str(p.resolve()) for p in a.subtitles or [])
        if a.measurement_cache:reuse_measurements(c,a.measurement_cache)
        g=evaluate(c,measure=not a.measurement_cache);report=finalize_review(c,g,prior);write_json(out/'qa.json',report)
        # No package READY or upload state is touched. Operational checks remain human-run.
        print(json.dumps(dict(output=str(out),ready=report['ready'],gates={k:v['status'] for k,v in g.items()},limits=report['limits']),ensure_ascii=False),flush=True)
        return 0 if report['ready'] else 2
    except Exception:
        write_json(out/'qa.json',dict(ready=False,limits=[LIMIT],error=traceback.format_exc(),network=False,uploads=False))
        raise
if __name__=='__main__':sys.exit(main())
