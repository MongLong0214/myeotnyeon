#!/usr/bin/env python3
"""Offline final-encode review, including B6 edge-fill and E4 handedness (2026-11-07).

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
    p.add_argument('--alignment',type=Path);p.add_argument('--review-inputs',type=Path)
    p.add_argument('--measurement-cache',type=Path,help='Verified factory review ASR/OCR for identical video; frames are remeasured')
    p.add_argument('--out',type=Path,help='NEW directory under factory/review_runs, never an existing episode/package')
    p.add_argument('--resume',type=Path,help='Recheck a previously generated factory review directory, retaining CTO signoffs')
    p.add_argument('--signoffs',type=Path,help='CTO-authored JSON {cto_signoffs: {item: signature}}')
    a=p.parse_args()
    if not a.edge_fill_only and not all([a.shots,a.script,a.facts]):p.error('--shots, --script and --facts are required for full review')
    if a.edge_fill_only and (a.resume or a.signoffs or a.measurement_cache):p.error('--edge-fill-only needs a new result directory, without signoffs or measurement cache')
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
    try:
        c=load_review(a.video,out,a.shots,a.script,a.facts,a.alignment,a.review_inputs)
        if a.measurement_cache:reuse_measurements(c,a.measurement_cache)
        g=evaluate(c,measure=not a.measurement_cache);report=finalize_review(c,g,prior);write_json(out/'qa.json',report)
        # No package READY or upload state is touched. Operational checks remain human-run.
        print(json.dumps(dict(output=str(out),ready=report['ready'],gates={k:v['status'] for k,v in g.items()},limits=report['limits']),ensure_ascii=False),flush=True)
        return 0 if report['ready'] else 2
    except Exception:
        write_json(out/'qa.json',dict(ready=False,limits=[LIMIT],error=traceback.format_exc(),network=False,uploads=False))
        raise
if __name__=='__main__':sys.exit(main())
