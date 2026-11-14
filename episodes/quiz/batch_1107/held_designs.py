from pathlib import Path
import json
W=Path(__file__).resolve().parents[3]
CHOICES={
 'q018':(['징역 2년','징역 3년','징역 5년'],'A',['1억 원 공탁','합의 수준 회복 아님']),
 'q019':(['징역 8개월','징역 1년 8개월','징역 3년'],'B',['반복된 폭행·강요','엄벌 탄원']),
 'q021':(['징역 30년','무기징역','사형'],'B',['심신미약 인정','이를 이유로 감경 안 함','1심 검찰 구형: 사형']),
 'q022':(['남편 징역 4개월','남편 징역 1년','남편 징역 2년'],'A',['공동상해','누범 기간']),
 'q023':(['징역 10년','징역 15년','징역 20년'],'A',['1심 선고 20년','도주치사 무죄','위험운전치사 유죄']),
}
for q,(choices,correct,factors) in CHOICES.items():
 p=W/'upload/pkg'/(q+'_batch1107');c=json.loads((p/'case.json').read_text());u=c['utterances']
 legal=[];at=u[3]['from_frame'];end=u[6]['from_frame'];modes=['judge','defendant','victim_reaction','tipping_scales']
 while at<end:
  nxt=min(at+36,end);legal.append(dict(from_frame=at,to_frame=nxt,scene=modes[len(legal)%4],acting='새 발언·판단·반응에 맞춘 눈·시선·손·몸의 연기와 구도 변화. 컷 쪼개기나 흔들기만으로 대체하지 않음'));at=nxt
 d=dict(status='DESIGN_ONLY_HELD_FOR_CTO_Q013_V3_AND_Q020',render_authorized=False,reason=c['reason'],subtitle=dict(font_px=64,weight=800,black_stroke_px=8,center_x=540,y=[1190,1344],max_lines=2,max_characters_per_line=14,wording='keep current narration; paginate overlong parent captions on actual ASR word clock after first-video review'),court_shots=legal,choices=[dict(letter=chr(65+i),text=t,pop_frame=u[4]['from_frame']+7*i) for i,t in enumerate(choices)],correct=correct,answer_frame=u[5]['from_frame'],cta_frame=u[6]['from_frame'],choose_time_s=(u[5]['from_frame']-u[4]['from_frame']-21)/30,sentencing_stamps=factors,face_rule='모든 피해자·피고인·판사에 눈·코·입과 표정. 실존 인물의 외모 미사용.',onscreen_disclosures=0,description_disclosures='보도 기반 허구 캐릭터·시간 축약·비유·법봉·가상 리액션을 설명란에만 명시.',answer_effect='정답 첫 프레임에 법봉 타격·비고어 나무 타격음. 정답 카드만 밝히고 나머지는 어둡게.',no_3d=True)
 (p/'design.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 (p/'design.txt').write_text('보류: q013 v3·q020 CTO 검수 전 새 방향 렌더 금지.\n소재: '+c['headline']+'\n선정 이유: '+c['reason']+'\n대본: '+str((p/'script.md').resolve())+'\n사실 및 심급: '+str((p/'facts.md').resolve())+'\n새 연출 설계: '+str((p/'design.json').resolve())+'\n선택지: '+' / '.join(choices)+'; 정답 '+correct+'\n양형 인자 스탬프: '+' / '.join(factors)+'\n예정 발행: CTO 검수·순서 배정 전 미정. 2026-11-07~12 매일 19:00 KST 제안, 소재 1순위 q018.\n')
 for name in ['video.mp4','cover.jpg']:
  if (p/name).exists():pass # Preserve pre-12:00 work; it is explicitly not a new-direction submission.
 r=p/'qa.json'
 if r.exists():
  qa=json.loads(r.read_text());qa.update(producer_status='HELD_PRE_1200_RENDER_NOT_SUBMITTED',latest_direction_applied=False,planned_publish_time='CTO 검수·순서 배정 전 미정 (2026-11-07~12 19:00 KST 제안)');r.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
 print(q,'design prepared; no render')
