"""Write the requested producer H self-check and file hashes; CTO verdict stays open."""
from pathlib import Path
import json,hashlib,sys,shutil,datetime
W=Path(__file__).resolve().parents[4];D=Path(__file__).parent
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main(q):
 p=W/'upload/pkg'/f'{q}_std';c=load(p/'case.json');qa=load(p/'qa.json');r=W/'episodes/review_full/shorts'/q;out=r/'std'
 layout=load(p/'subtitle_layout_observed.json')
 observed={}
 for x in layout:
  for line in x['lines']:
   assert line['characters']<=14 and line['width']<=900,(x,line)
  assert x['fontSize']=='72px' and x['fontWeight']=='800' and x['outline']=='10px' and abs(x['centerX']-540)<.1,x
  observed[x['frame']]=x
 # The renderer's source is snapshotted per package so later case-specific work
 # cannot silently change the evidence for an already rendered file.
 sd=p/'render_source';sd.mkdir(exist_ok=True)
 for f in D.glob('*.tsx'):shutil.copy2(f,sd/f.name)
 for name in ['render.cjs','prepare_std.py','finish_std.py','package_std.py']:shutil.copy2(D/name,sd/name)
 source_hashes={str(f.relative_to(p)):sha(f) for f in sorted(sd.iterdir())}
 dump(p/'render_source_sha256.json',source_hashes)
 dump(p/'direction.json',dict(template=dict(video=str(W/'upload/v52_q013_n16_v3.mp4'),sha256=sha(W/'upload/v52_q013_n16_v3.mp4'),source=str(W/'episodes/quiz/q013/v3/src')),shots=[dict(from_frame=u['from_frame'],to_frame=u['from_frame']+u['dur'],mode=u['mode'],text=u['text']) for u in c['utterances']],snap_zooms=[dict(at=0,frames=3,reason='act'),dict(at=c['answer_frame'],frames=3,reason='answer')],choice=dict(first=c['choice_frame'],all_visible=c['choice_frame']+8,answer=c['answer_frame'],selection_seconds=(c['answer_frame']-c['choice_frame']-8)/30,correct='ABC'[c['correct']]),subtitle=dict(font='Quiet Sans / Pretendard ExtraBold',px=72,weight=800,outline_px=10,center_x=540,max_lines=2,max_characters=14,box_y=[1192,1342]),source_hashes=source_hashes,producer_verdict=None,CTO_verdict=None))
 src=load(p/'research.json')['sources']
 rows={
 'H1':'제공 기준 구독자 9→1,000, 격차 991. 0초 행위, 질문·댓글 선택, 끝의 선고와 다음 사건 연결을 실제 적용. 이번 산출은 3편이며 미게시 영상의 성장 효과를 확정하지 않음.',
 'H2':f'0초 행위 재현, 음성 시작 0초. 정답 {c["answer_frame"]/30:.3f}s부터, 다음 사건 CTA {c["cta_frame"]/30:.3f}s부터. 이전 1.5–2초 컷 대신 최신 H14의 대사 경계 2–3초 리듬 적용. 11-06 기존 analytics 일일 스냅샷의 engagedViews/views는 별도 누적 비율이며 viewed-vs-swiped와 구분. 신작 성과는 게시 전 미측정.',
 'H3':f'RANKED Shorts #{c["rank"]} · {c["candidate"]}. topic_evidence.json에 네이버 검색과 YouTube 수요 원본 근거. 공분 점수나 구형 차이로 부당판결을 단정하지 않음.',
 'H4':'소스는 승인된 q013 v3의 FightRig·CourtDynamic·폰트·팔레트·자막·선택지 문법. 화면 전체 카툰, 중복 헤더·회차 배지·패널·설명 띠·가짜 UI 없음. H10 요청의 선택 카드만 사용. 최종 AI 티 판단은 CTO 대기.',
 'H5':f'브라우저에서 {len(observed)}개 실제 렌더 프레임의 자막 배치를 계측. 72px / 800 / 검정 10px, x540 중앙, 최대 2줄·줄당 14자 이하. 전체 저장 cue 검사와 subtitle_layout_observed.json 참조. 한 어구만 노란색 강조.',
 'H6':'법정은 판사·피고인 투샷, 대사 한 줄마다 한 샷. 판사 지적→피고인 옷깃·전신 반응을 같은 구도 안에서 연기. 사실에 맞는 도장과 기울어지는 저울. 답 공개 때만 망치와 순간 줌. 판정 CTO 대기.',
 'H7':'모든 성인 인물은 승인된 독창 Toon rig의 눈·코·입과 표정 사용. 여성 피해자/배우자도 별도 원작 캐릭터. anonymous 얼굴 숨김 미사용. 실존 피해자의 신상·외모 미재현. 시각 판정 CTO 대기.',
 'H8':'전체 Remotion 2D SVG. Blender/3D/실사 클립 입력 없음. 시작과 다음 사건도 동일 카툰.',
 'H9':'화면 내 재구성·시간압축·시각비유·시리즈 코너 고지 0. 해당 설명은 meta.txt 설명란에만 수록. 구형/선고와 심급 구분은 사실이므로 유지.',
 'H10':f'A/B/C 큰 색 카드가 4프레임 간격으로 등장. 댓글로 골라보세요. 전체 선택지가 나온 뒤 {(c["answer_frame"]-c["choice_frame"]-8)/30:.3f}초 선택 가능. 정답 {"ABC"[c["correct"]]}만 점등, 나머지 흐림. 해당 화면은 최종 시트로 CTO 검수 대기.',
 'H11':'업로드·교체·예약 없음. 이 작업에서 원격 비공개 잔존본이 생기지 않았음. 기존 로컬 작업은 같은 세션의 보존 지시에 따라 보존. 원격 삭제 대상/ID를 임의로 만들지 않음.',
 'H12':'기존 로컬 소스·음성 엔진·ASR·팩토리 검수 도구·저장된 네이버/YouTube 수요 근거로 직접 제작. 새 키나 사용자 대행 작업 요청 없음.',
 'H13':'전체 변경 구간 모든 30fps 프레임을 F1 연속 시트로 보존. 2fps 한 장은 빠른 보기용으로 전수 시트를 대체하지 않음. q020 먼저 완성·FIRST_READY 기록 후 다음 두 편 진행. CTO 전수 시각 판정과 CEO 승인은 대기, 제작자 PASS/MATCH 없음.',
 'H14':'모든 실제 컷은 개별 합성된 완결 대사 경계. 기본 샷 2–3초, CTA 1.5초. 문장 중간 반응 컷 없음. 순간 줌은 0초 행위와 정답 두 지점(각 3프레임)뿐. 리듬 최종 판단은 CTO 대기.',
 }
 qa.update(video_sha256=sha(p/'video.mp4'),producer_self_check={k:dict(observation=v,CTO_verdict='PENDING') for k,v in rows.items()},render_source_sha256=source_hashes,planned_publish_time='2026-11-07 · CTO 검수/업로드 순서/일일 1편 한도 확인 후 확정, 예약 없음')
 dump(p/'qa.json',qa)
 raw='\n'.join(k+': '+v['status']+' / '+v.get('review_state','') for k,v in qa['gates'].items())
 defects=[]
 for k in qa['defects']:
  ev=qa['gates'][k]['evidence']
  if k=='C1':detail=f'발화 {ev.get("syllables_per_second")}음절/s, 쉼 진단 '+str([x for x in ev.get('pauses',[]) if not x.get('pass_')])
  elif k=='C2':detail='정지 진단 '+str(ev.get('static_spans',ev))[:1600]
  elif k=='C3':detail=f'인물 {ev.get("character_share")}, 모션 {ev.get("motion_share")}, 자막 밖 OCR {len(ev.get("non_subtitle_text",[]))}건. 질문/양형 도장/기능성 선택지를 포함하는 원시 진단; 자동 결과를 제작자가 면제하지 않음.'
  elif k=='D2':detail='절 경계 ±0.12s 원시 진단: '+str([x for x in ev.get('cuts',[]) if not x.get('pass_')])
  elif k=='D3':detail=str(ev)
  else:detail=str(ev)[:1200]
  defects.append(k+': '+detail)
 text=f'{q} · q013 v3 표준 · CTO 검수용\n상태: RENDERED / NOT APPROVED. 제작자 PASS/MATCH 없음.\n파일: {p/"video.mp4"}\nSHA256: {sha(p/"video.mp4")}\n규격: 1080×1920 / H.264·AAC / 30fps / {c["n"]}프레임 / {c["duration"]:.3f}초\n표준: {W/"upload/v52_q013_n16_v3.mp4"}\n표준 SHA256: {sha(W/"upload/v52_q013_n16_v3.mp4")}\n번호: 미배정. 업로드 없음.\n게시 예정: {qa["planned_publish_time"]}\n마감: 2026-11-07 09:00 KST\n\n제작자 자체 점검 (H1–H14, CTO 판정은 전부 대기)\n'+'\n'.join(k+': '+v for k,v in rows.items())
 text+='\n\n사실·법적 범위\n'+(p/'facts.md').read_text()+'\n출처\n'+'\n'.join(s['publisher']+' | '+s['url']+' | snapshot '+str(W/s['file'])+' | sha256 '+s['sha256'] for s in src)
 text+='\n\n검수 경로\n2fps 전체: '+str(r/'std_2fps.png')+'\n전체 30fps: '+str(out/'F1.md')+'\n핵심 행위 연속: '+str(r/'std_action_consecutive.png')+'\n정답 연속: '+str(r/'std_answer_consecutive.png')+'\n음성 ↔ 화면·컷: '+str(out/'D1_D2_cut_sheet.md')+'\n사실 게이트: '+str(out/'E3.md')+'\n표준 나란히: '+str(out/'B1.md')+'\n실제 자막 계측: '+str(p/'subtitle_layout_observed.json')+'\n\nA1–G2 원시 결과 (자동 PASS는 CTO 승인 아님)\n'+raw
 text+='\n\n남은 결함·한계\n'+('\n'.join(defects) if defects else '자동 DECIDED FAIL 없음. 사람 의미·시각 검수는 별도 대기.')+'\n입력 누락: '+str(qa['input_missing'])+'\n실시간 재생 미검수. 최종 AAC 믹스 ASR·음량·전체 연속 프레임으로 대체. 원문 전체 판결문 미확보 범위는 보도 교차 확인까지만 주장. CTO/CEO 서명·운영 G1/G2는 아직 수행 전.\n'
 (p/'READY.txt').write_text(text)
 if q=='q020':
  first=W/'episodes/quiz/batch_1107/FIRST_READY.txt'
  first.write_text(f'q020_std FIRST RENDER READY — NOT CTO APPROVED\n{p/"video.mp4"}\nsha256 {sha(p/"video.mp4")}\nREADY {p/"READY.txt"}\n2fps {r/"std_2fps.png"}\nq020를 먼저 렌더·검수자료 패키징 완료. 이 기록 뒤 q018_std·q022_std 계속 제작.\n업로드·번호 배정 없음.\n')
 manifest=['video.mp4','cover.jpg','meta.txt','qa.json','READY.txt','case.json','shots.json','direction.json','render_source_sha256.json','subtitle_layout_observed.json']
 (p/'SHA256SUMS').write_text(''.join(sha(p/n)+'  '+n+'\n' for n in manifest))
 print(q,sha(p/'video.mp4'),'raw defects',qa['defects'],flush=True)
if __name__=='__main__':main(sys.argv[1])
