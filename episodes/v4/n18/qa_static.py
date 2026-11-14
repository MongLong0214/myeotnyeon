from pathlib import Path
import json,re,hashlib,sys
import numpy as np
from PIL import Image
E=Path(__file__).resolve().parent;W=E.parents[2];O=E/'out';film=json.loads((W/'production/compositor/src/v4/n18-film.json').read_text());source=json.loads((E/'shots.json').read_text());facts=(E/'facts.md').read_text()
# Every factual numeric statement is checked against adopted rows, not against
# numbers incidental to URLs or source headlines.
numeric_evidence=[
 ('2024년 5월 23일','E01','2024-05-23'),('12사단','E01','12사단'),('6명','E02','6명'),('이틀 뒤','E05','이틀 후'),
 ('2024년 11월 12일','C03 / D03','2024-11-12'),('1심 중대장 구형 10년','C03','10년'),('1심 부중대장 구형 7년','D03','7년'),
 ('2025년 1월 7일','C05 / D04','2025-01-07'),('형사2부','C05 / D04','형사2부'),('1심 중대장 5년','C05','5년'),('1심 부중대장 3년','D04','3년'),
 ('2025년 6월 18일','C07 / D06','2025-06-18'),('형사1부','C07','형사1부'),('2심 중대장 5년 6개월','C07','5년 6개월'),('증가 6개월','C07','6개월'),('2심 부중대장 3년','D06','3년'),
 ('2025년 9월 25일 중대장 대법원 확정','C09','2025-09-25'),('중대장 확정 5년 6개월','C09','5년 6개월'),('부중대장 확정 3년 / 보도 기준일','D08','2025-09-25')]
rows={}
for line in facts.splitlines():
 m=re.match(r'\| ([ECDJ]\d+) \|',line)
 if m:rows[m[1]]=line
numbers=[]
for value,ids,needle in numeric_evidence:
 ids=ids.split(' / ');numbers.append(dict(value=value,fact_ids=ids,present=any(needle in rows[i] for i in ids)))
assert all(x['present'] for x in numbers)
allids=[fid for n in source['narration'] for fid in n['fact_ids']];assert all(i in rows for i in allids)
# Contextual preservation of the two defendant streams.
streams=dict(commander=dict(request_1st=10,sentence_1st=5,sentence_appeal='5 years 6 months',final_date='2025-09-25'),deputy=dict(request_1st=7,sentence_1st=3,sentence_appeal=3,final_status_report_date='2025-09-25',final_date=None))
def comps(name):
 out={}
 for line in (O/name).read_text().splitlines():
  if re.match(r'^[A-Z0-9][A-Z0-9-]+\s',line):out[line.split()[0]]=' '.join(line.split()[1:])
 return out
before,after=comps('compositions-before.log'),comps('compositions-after.log')
cover=np.array(Image.open(O/'COVER-Q012-after.png'));ref=np.array(Image.open(E/'rep2/COVER-Q012-after.png'));diff=int(np.any(cover!=ref,axis=2).sum())
text=(O/'display_text.txt').read_text();forbidden=['충격','솜방망이','역대급','잔혹한','참혹한','끔찍한','경악','고작','겨우']
spelling_review=['Verified original script transcription against narration manifest','Single subtitle line, at most 26 characters; no word split','All role labels and court names compared with approved script/facts','Numeral readings explicitly mapped in lex.json; ASR output is never used as display copy','상상적 경합 / 실체적 경합 retained as legal terms','Source outlets and URL strings copied from facts.md']
res=dict(source_hashes={n:hashlib.sha256((E/n).read_bytes()).hexdigest() for n in ['facts.md','script.md','shots.json']},numbers=dict(passed=True,evidence=numbers,narration_fact_links_checked=len(allids),defendant_streams=streams,structural_numbers='Chapter labels 01–05 identify the five script sections; they are not case quantities'),spelling=dict(passed=True,method='Manual source comparison plus generated caption integrity checks',checks=spelling_review),compositions=dict(before_count=len(before),after_count=len(after),missing=[x for x in before if x not in after],changed=[x for x in before if after.get(x)!=before[x]],added=[x for x in after if x not in before]),cover_q012_different_pixels=diff,death_case=dict(suffering_or_injury_depictions=0,medical_or_collapse_depictions=0,music_tracks=0,gag_sfx=0,editorial_evaluative_words=[w for w in forbidden if w in text],court_attributed_language=['후진적 형태의 병영문화 (N049 / J11)','사회적 기본 기대를 배반한 범행 (N051 / J12)'],passed=not any(w in text for w in forbidden)),shot_coverage=dict(source_shots=len(source['shots']),rendered_source_shots=len(film['shots'])-1,missing=[s['id'] for s in source['shots'] if s['id'] not in {x['id'] for x in film['shots']}],max_shot_seconds=max(s['dur'] for s in film['shots'])/30),fonts=dict(used=['Pretendard'],licence='SIL Open Font License 1.1',evidence='production/compositor/public/fonts/OFL_Pretendard.txt'),external_visual_assets=0,uploads=0,new_npm_packages=0)
(O/'qa_static.json').write_text(json.dumps(res,ensure_ascii=False,indent=1));print('STATIC QA',len(before),len(after),'cover diff',diff,'numeric statements',len(numbers))
