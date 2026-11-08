#!/usr/bin/env python3
"""Read-only known-bad proof, writing only new factory/review_runs artifacts."""
from pathlib import Path
import os,sys
ROOT=Path(__file__).resolve().parents[1]
PYTHON=ROOT/'.venv/bin/python'
if Path(sys.prefix)!=ROOT/'.venv' and PYTHON.exists():os.execv(str(PYTHON),[str(PYTHON),__file__,*sys.argv[1:]])
import json,traceback
from concurrent.futures import ThreadPoolExecutor,as_completed
import review_gates as r
from longform_qa import new_output
from gates import empty_panel_gate,finalize_review

FIXTURES=[
    ('lf2_v4','episodes/lf2_daejeon_bank/cartoon_v4','lf2_cartoon_v4_1080p.mp4','episodes/lf2_daejeon_bank/script_v1.md','episodes/lf2_daejeon_bank/facts.md','E1'),
    ('n18_v4','episodes/v4/n18/cartoon_v4','n18_cartoon_v4_1080p.mp4','episodes/v4/n18/script_v3.md','episodes/v4/n18/facts.md','C3'),
    ('lf2_v5','episodes/lf2_daejeon_bank/cartoon_v5','lf2_cartoon_v5_1080p.mp4','episodes/lf2_daejeon_bank/cartoon_v5/script_v2.md','episodes/lf2_daejeon_bank/facts.md','C1')]

def fixture(f,out):
    name,directory,filename,script,facts,expected=f;root=ROOT/directory;dest=out/name
    c=r.load_review(root/filename,dest,root/'shots.json',ROOT/script,ROOT/facts)
    before=dict(c.inputs);print('Regression:',name,flush=True)
    if name=='lf2_v5':
        gates=r.evaluate(c);report=finalize_review(c,gates)
    else:
        # These fixtures isolate dates and prop cards, so ASR is not required.
        c.normalize();r.scan_frames(c,False);r.ocr_frames(c)
        gates={'E1':r.e1(c),'C3':r.c3(c)}
        report=dict(gates=gates,limits=[r.LIMIT],ready=False,network=False,uploads=False,
                    inputs=c.inputs,not_evaluated=sorted(set(r.ITEMS)-set(gates)),
                    scope='Targeted EVERY-encoded-frame/OCR regression, not complete release QA')
    r.write_json(dest/'qa.json',report)
    fired=[k for k,v in gates.items() if v['status']=='FAIL' and v['review_state']=='DECIDED']
    missed=[] if expected in fired else [expected]
    if name=='lf2_v4' and not gates['E1']['evidence'].get('korean_word_dates'):missed.append('E1 Korean-word-date detector')
    if name=='n18_v4' and gates['C3']['evidence'].get('character_share_pass',True):missed.append('C3 character share')
    if name=='lf2_v5' and gates['C1']['evidence'].get('pace_pass',True):missed.append('C1 long-form pace window')
    case=dict(expected=expected,fired=fired,missed=missed,
              review_pending=[k for k,v in gates.items() if v['review_state']=='NEEDS_REVIEW'],
              report=str(dest/'qa.json'),expected_evidence=gates[expected]['evidence'],
              decoded_frames=c.media.get('decoded_frames'),ocr_frames=len(c.media.get('ocr',[])),
              ocr_complete=c.media.get('ocr_complete'),figure_detector=c.media.get('figure_detector'))
    if name=='lf2_v5':case['cut_sheet']=gates['D2']['evidence'].get('sheet')
    # normalize() binds the video before decoding; retain that first hash too.
    for path,h in c.inputs.items():before.setdefault(path,h)
    print('Regression complete:',name,'missed=',missed,flush=True)
    return name,case,before

def main():
    out=new_output('known_bad');print('REGRESSION_OUTPUT',out,flush=True);cases={};before={}
    # Independent local media jobs, one local ASR job; no remote/model agents.
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(fixture,f,out):f for f in FIXTURES}
        for future in as_completed(futures):
            f=futures[future]
            try:
                name,case,inputs=future.result();cases[name]=case;before.update(inputs)
            except Exception:
                cases[f[0]]=dict(expected=f[-1],fired=[],missed=[f[-1]],error=traceback.format_exc())
    p=ROOT/'upload/pkg/q013_n16_v4';video=ROOT/'upload/v52_q013.mp4'
    for file in [video,p/'empty.mp4',p/'render.json']:before[str(file.resolve())]=r.digest(file)
    g=empty_panel_gate(video,p/'empty.mp4',r.read_json(p/'render.json'))
    cases['shorts_empty_panel']=dict(expected='no_empty_panel',fired=['no_empty_panel'] if g['status']=='FAIL' else [],missed=[] if g['status']=='FAIL' else ['no_empty_panel'],gate=g)
    cases=dict(sorted(cases.items()))
    changed=[p for p,h in before.items() if not Path(p).is_file() or r.digest(p)!=h]
    gaps=[f'{name}: {item}' for name,c in cases.items() for item in c['missed']]
    report=dict(cases=cases,all_expected_defects_caught=not gaps,gaps=gaps,inputs_unchanged=not changed,changed_inputs=changed,
                limitations=[r.LIMIT,'OCR covers every encoded frame; small/stylized/low-contrast text may still be misrecognized.',
                              'Local figure detector may miss cartoon characters.','D2 semantic image/narration mismatch needs CTO; timing cannot decide meaning.'],network=False,uploads=False)
    r.write_json(out/'report.json',report)
    lines=['# 알려진 결함 회귀 결과','', '| 입력 | 기대 게이트 | 발화한 확정 FAIL | 놓친 기대 게이트 |','|---|---|---|---|']
    for name,c in cases.items():lines.append(f'| {name} | {c["expected"]} | {", ".join(c["fired"])} | {", ".join(c["missed"]) or "없음"} |')
    lines.extend(['',f'입력 변경: {changed or "없음"}',f'LF2 v5 D2 전 컷·중간 프레임: {cases["lf2_v5"].get("cut_sheet")}', '',
                  '그림·발화의 의미상 불일치는 CTO 샷별 검수가 필요하다. 전 프레임 OCR도 작거나 장식적이거나 대비가 낮은 글자를 오인식할 수 있다.'])
    (out/'report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(report=str(out/'report.json'),caught=not gaps,gaps=gaps,inputs_unchanged=not changed),ensure_ascii=False),flush=True)
    return 0 if not gaps and not changed else 1
if __name__=='__main__':sys.exit(main())
