"""im-not-ai 2.3.2: same definitions as quiz/out/v3/textgate.py.
Reports raw signals, including legal terminology and formal source narration;
no terminology exceptions are silently subtracted from counts.
"""
import json,os,pathlib,re,sys
E=pathlib.Path(__file__).resolve().parent;W=E.parents[2]
IMNA=pathlib.Path(os.environ.get('IM_NOT_AI_DIR',W/'.deps/im-not-ai'))/'skills/humanize-korean/references'  # im-not-ai checkout; default studio/.deps/im-not-ai
sys.path.insert(0,str(IMNA));import metrics_v2 as M
source=(W/'episodes/quiz/out/v3/textgate.py').read_text()
a=source.index('# C-11:');b=source.index('\ndef gate(eid):');exec(source[a:b])
film=json.loads((W/'production/compositor/src/v4/n18-film.json').read_text());D=json.loads((E/'shots.json').read_text())
lab=[]
for s in film['shots']:
 if s['kind']=='silence':continue
 if s['kind']=='chapter':lab.append(s['chapterTitle'])
 elif s['kind']=='credits':lab+=['出처' if False else '출처 · 보도 원문',*s['lines'],'원문 URL과 발행일은 영상 설명에 수록했습니다.','화면은 직접 그린 재구성·개념도입니다. 실제 배치와 다릅니다.']
 else:lab += [*s['lines'],s['category'],s['chapterLabel'],s['date'],s['label'],s['source']]
lab+=['실제 판결 · 대법원 확정','얼차려 사망','항소심은 왜 달랐나','법정 재구성 · 개념도']
nar=[x['text'] for x in D['narration']];captions=[x['text'] for x in film['subtitles']]
doc='\n'.join(lab+captions)
f5=[m for m in F5.findall(doc) if m.split()[0] not in F5_STOP and not m.split()[0].endswith(('국적','목적','지적'))]
ends=[ending(s) for s in nar];e2=sum(1 for i in range(len(ends)-3) if len(set(ends[i:i+4]))==1)+len(PROG.findall(doc))
counts={'C-8':M.antithesis_count(doc)+len(C8_PAIR.findall(doc)),'C-11':len(C11.findall(doc)),'I-4':len(I4.findall(doc)),'E-2':e2,'F-5':len(f5)}
result=dict(version='2.3.2',checkout=str(IMNA.parents[2]),method='quiz/out/v3/textgate.py regexes and metrics_v2; complete emitted display strings; sentence endings use source narration',counts=counts,passed=all(v==0 for v in counts.values()),details={'C-11':C11.findall(doc),'F-5':f5,'narration_endings':ends},interpretation='Raw signals retained: legal contrasts/terms and repeated formal endings in the approved source script are not silently waived.')
(E/'out/textgate.json').write_text(json.dumps(result,ensure_ascii=False,indent=1));print(json.dumps(counts));(E/'out/display_text.txt').write_text(doc)
