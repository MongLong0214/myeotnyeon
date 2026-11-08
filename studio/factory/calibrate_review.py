#!/usr/bin/env python3
"""Read-only accepted-media controls and existing known-bad fixtures; outputs stay in factory."""
from pathlib import Path
import os,sys
ROOT=Path(__file__).resolve().parents[1]
if Path(sys.prefix)!=ROOT/'.venv' and (ROOT/'.venv/bin/python').exists():
    os.execv(str(ROOT/'.venv/bin/python'),[str(ROOT/'.venv/bin/python'),__file__,*sys.argv[1:]])
import argparse,json
import review_gates as r
from gates import finalize_review,empty_panel_gate
from longform_qa import new_output
from review_regression import FIXTURES

def accepted_short(out,cache=None):
    root=ROOT/'episodes/quiz/q014/v52';p=ROOT/'upload/pkg/q014_n15'
    doc=r.read_json(root/'render_final_aligned.json');audio=r.read_json(root/'audio.json');tim=r.read_json(root/'timing.json')
    by_id={n['id']:n for n in audio['items']}
    narration=[dict(by_id[n['id']],start_s=n['start']/doc['fps'],end_s=n['end']/doc['fps']) for n in tim['items']]
    subs=[dict(n,start_s=n['from_']/doc['fps'],end_s=n['to']/doc['fps']) for n in doc['subtitles']]
    facts_path=ROOT/'episodes/quiz/q014/facts.md'
    facts=facts_path.read_text() if facts_path.exists() else ''
    c=r.Review(ROOT/'upload/v52_q014_n15.mp4',out/'accepted_short','shorts',doc['cues'],subs,narration,audio['reference'],facts)
    for file in [root/'render_final_aligned.json',root/'audio.json',root/'timing.json',facts_path,ROOT/'upload/ledger.json']:c.bind(file)
    # Original published media, never the subsequently rebuilt package video.
    if cache:r.reuse_measurements(c,cache)
    g=r.evaluate(c,measure=not cache);report=finalize_review(c,g)
    report['control']='Owner accepted and published Shorts; shared A1–G2 QA on the original delivered encode'
    report['ledger_entry']=[e for e in r.read_json(ROOT/'upload/ledger.json')['entries'] if e.get('no')==15]
    r.write_json(c.out/'qa.json',report)
    return c,report

def recheck_longforms():
    """Rerun all gates; independent frame scan reuses already decoded JPEGs."""
    import re
    for name in ['lf2','n18']:
        directory=r.HERE/'review_runs'/f'calibrated_{name}_v6';prior=r.read_json(directory/'qa.json')
        root=r.HERE/'review_runs/calibration_inputs/lf2' if name=='lf2' else Path(prior['video']).parent
        facts=[ROOT/'episodes/lf2_daejeon_bank/facts.md'] if name=='lf2' else [ROOT/'episodes/v4/n18/facts.md',ROOT/'episodes/v4/n18/facts_enrich.md']
        c=r.load_review(prior['video'],directory,root/'shots_v6.json',root/'script_v2.md',facts)
        baseline=r.HERE/'review_runs'/f'{name}_cartoon_v6_1080p_001'
        for file in [directory/'final_asr.json',directory/'ocr.json']:
            if prior['evidence_sha256'].get(str(file))!=r.digest(file):raise ValueError('Changed cached evidence '+str(file))
            c.bind(file)
        c.asr=r.read_json(directory/'final_asr.json')['asr'];c.normalize()
        if r.digest(c.video)!=r.read_json(directory/'final_asr.json')['video_sha256']:raise ValueError('Changed long-form video')
        c.images={int(p.stem):p for p in (directory/'frames').glob('*.jpg')}
        for p in c.images.values():
            if prior['evidence_sha256'].get(str(p))!=r.digest(p):raise ValueError('Changed decoded frame '+str(p))
        log_path=baseline/'audio_measurements.log';c.bind(log_path);log=log_path.read_text()
        starts=list(map(float,re.findall(r'silence_start: ([\d.]+)',log)));ends=list(map(float,re.findall(r'silence_end: ([\d.]+)',log)))
        c.media.update(silences=[dict(start=a,end=b,duration=b-a) for a,b in zip(starts,ends)],audio_sha256=prior['gates']['F2']['evidence']['audio_sha256'] if 'audio_sha256' in prior['gates']['F2']['evidence'] else r.read_json(directory/'final_asr.json')['audio_sha256'],loudness=prior['gates']['F2']['evidence']['loudness'],loudness_log=str(log_path),frame_pages=prior['gates']['F1']['evidence']['pages'])
        r.scan_frames(c,False,write_frames=False)
        ocr=r.read_json(directory/'ocr.json');c.media.update(ocr=ocr['frames'],ocr_engine=ocr['engine'],ocr_korean=True,ocr_complete=len(ocr['frames'])==c.frames,ocr_coverage=ocr['coverage'])
        g=r.evaluate(c,measure=False);r.write_json(directory/'qa.json',finalize_review(c,g))

def ground_truth(out):
    rows=[]
    for name,expected in [('lf2',[True,True,False,False,False,False]),('n18',[True]*8)]:
        directory=r.HERE/'review_runs'/f'calibrated_{name}_v6';q=r.read_json(directory/'qa.json')
        observations=q['gates']['C3']['evidence']['character_observations'][:len(expected)]
        for obs,truth in zip(observations,expected):
            rows.append(dict(video=name,**obs,expected_character_present=truth,expected_panel_covering_character=name=='n18' and obs['shot'] in ['H002','H003','H004','H005','H006'],false_fail=truth and obs['character_present'] is False,miss=obs['character_present']!=truth))
    r.write_json(out/'ground_truth.json',rows)
    return rows

def known_bad(out):
    cases={};before={}
    for name,directory,filename,script,facts,expected in FIXTURES:
        cache=r.HERE/'review_runs/known_bad_003'/name;baseline=r.read_json(cache/'qa.json');root=ROOT/directory
        c=r.load_review(root/filename,out/'known_bad'/name,root/'shots.json',ROOT/script,ROOT/facts);c.normalize()
        if baseline['inputs'].get(str(c.video))!=r.digest(c.video):raise ValueError('Known-bad video changed: '+name)
        ocr_path=cache/'ocr.json';c.bind(ocr_path);saved=r.read_json(ocr_path)
        c.media.update(ocr=saved['frames'],ocr_engine=saved['engine'],ocr_korean=True,ocr_complete=len(saved['frames'])==c.frames,ocr_coverage=saved['coverage'])
        c.images={int(p.stem):p for p in (cache/'frames').glob('*.jpg')}
        if expected=='C1':
            path=cache/'final_asr.json'
            if baseline['evidence_sha256'].get(str(path))!=r.digest(path):raise ValueError('Known-bad ASR changed')
            c.bind(path);c.asr=r.read_json(path)['asr'];c.normalize()
        # Target the same four defects as known_bad_003; full old reports remain intact.
        gate=r.ITEMS[expected](c)
        cases[name]=dict(expected=expected,gate=gate,caught=gate['status']=='FAIL' and gate['review_state']=='DECIDED',video_sha256=r.digest(c.video),ocr_sha256=r.digest(ocr_path),cache=str(cache))
        r.write_json(c.out/'qa.json',dict(gates={expected:gate},ready=False,scope='Known-bad targeted regression using identical encoded-frame OCR/ASR',inputs=c.inputs))
        before.update(c.inputs)
    p=ROOT/'upload/pkg/q013_n16_v4';video=ROOT/'upload/v52_q013.mp4'
    for file in [video,p/'empty.mp4',p/'render.json']:before[str(file)]=r.digest(file)
    gate=empty_panel_gate(video,p/'empty.mp4',r.read_json(p/'render.json'))
    cases['shorts_empty_panel']=dict(expected='no_empty_panel',gate=gate,caught=gate['status']=='FAIL')
    changed=[path for path,h in before.items() if r.digest(path)!=h]
    result=dict(cases=cases,all_expected_defects_caught=all(c['caught'] for c in cases.values()),changed_inputs=changed)
    r.write_json(out/'known_bad.json',result)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--short-report',type=Path);args=parser.parse_args()
    out=new_output('gate_calibration');print('CALIBRATION_OUTPUT',out,flush=True)
    short_c,short=accepted_short(out,args.short_report.parent if args.short_report else None)
    recheck_longforms()
    truth=ground_truth(out);bad=known_bad(out)
    # One accepted film is one control per gate. Human-pending, missing-input
    # and operational items are not automatic defect FAILs.
    counts={name:int(short['gates'][name]['status']=='FAIL' and short['gates'][name]['review_state']=='DECIDED') for name in r.ITEMS}
    counts['C3']+=sum(row['false_fail'] for row in truth)
    report=dict(false_fail_counts=counts,advisory_gates=[k for k,v in counts.items() if v],accepted_short_report=str(out/'accepted_short/qa.json'),ground_truth_report=str(out/'ground_truth.json'),ground_truth_character_errors=sum(row['miss'] for row in truth),known_bad_report=str(out/'known_bad.json'),known_bad_all_fail=bad['all_expected_defects_caught'],scope='False-FAIL counts: automatic DECIDED defects on owner-accepted published Shorts plus C3 character-presence ground truth (14 shots). Unlabelled long-form gates are not assumed clean.',network=False,uploads=False)
    r.write_json(r.HERE/'gate_calibration.json',report)
    for directory in (out/'known_bad').iterdir():
        path=directory/'qa.json';q=r.read_json(path);r.apply_calibration(q['gates']);r.write_json(path,q)
    # Recompute binding/readiness with the measured advisory policy, not a post-hoc ready edit.
    if short_c:
        final=finalize_review(short_c,short['gates']);final.update(control=short['control'],ledger_entry=short['ledger_entry']);r.write_json(short_c.out/'qa.json',final)
    for name in ['lf2','n18']:
        directory=r.HERE/'review_runs'/f'calibrated_{name}_v6';q=r.read_json(directory/'qa.json')
        root=r.HERE/'review_runs/calibration_inputs/lf2' if name=='lf2' else Path(q['video']).parent
        fact_paths=[ROOT/'episodes/lf2_daejeon_bank/facts.md'] if name=='lf2' else [ROOT/'episodes/v4/n18/facts.md',ROOT/'episodes/v4/n18/facts_enrich.md']
        c=r.load_review(q['video'],directory,root/'shots_v6.json',root/'script_v2.md',fact_paths)
        c.inputs=q['inputs'];c.artifacts=q['evidence_sha256']
        r.write_json(directory/'qa.json',finalize_review(c,q['gates']))
    r.write_json(out/'report.json',report)
    print(json.dumps(report,ensure_ascii=False),flush=True)
    return 0 if bad['all_expected_defects_caught'] and not bad['changed_inputs'] and not report['ground_truth_character_errors'] else 1
if __name__=='__main__':sys.exit(main())
