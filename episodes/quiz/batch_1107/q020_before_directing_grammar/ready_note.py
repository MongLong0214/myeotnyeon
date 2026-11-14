"""Produce the owner's requested per-ID producer check. Never assigns CTO PASS."""
from pathlib import Path
import json,hashlib,re
W=Path(__file__).resolve().parents[3];B=Path(__file__).parent;p=W/'upload/pkg/q020_batch1107';out=W/'episodes/review_full/shorts/q020'
load=lambda f:json.loads(Path(f).read_text())
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
c=load(p/'case.json');r=load(p/'qa.json');pagination=load(p/'subtitle_pagination.json');choices=load(p/'choices.json');shots=load(p/'shots.json')['shots']
assert r['video_sha256']==sha(p/'video.mp4')
assert all(len(line)<=14 for parent in pagination['parents'] for lines in parent['lines'] for line in lines)
assert choices['all_options_choose_time_s']>=2
assert c['utterances'][5]['from_frame']==656 and c['utterances'][6]['from_frame']==731
court=[s for s in shots if s['start_s']>=359/30 and s['end_s']<=731/30]
assert all(1<=s['end_s']-s['start_s']<=1.500001 for s in court)
ocr=[]
def texts(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if k=='text' and isinstance(v,str):ocr.append(v)
   else:texts(v)
 elif isinstance(x,list):
  for v in x:texts(v)
for line in (out/'ocr_frames.jsonl').read_text().splitlines():texts(json.loads(line))
hits=[t for t in ocr if re.search(r'재구성|시간\s*(?:압축|축약)|시각\s*비유|몇년나옴\s*#|보도\s*기반',t)]
sources=load(p/'research.json')['sources'];raw_defects=r['defects']
H={
 'H1':'실행·격차 명시. 현재 9→1000명까지 991명. 0.5명/1000뷰이면 약 1,982,000뷰가 필요하고 6편×1800뷰로는 약 5.4명이다. 실험 목표 2명/1000뷰이면 필요한 조회수는 495,500뷰(달성 보장 아님). 레버는 0초 행위, 첫 3초 행동→반응, 실제 다음 사건, 댓글 퀴즈와 선택 카드. q020에 이미 적용했고 5편 대본·설계는 준비했다. CTO 검수 뒤 첫 24시간 engagedViews/views·구독 전환을 비교해 확산할 훅을 고른다.',
 'H2':'관측 확인·발행 후 측정 대기. 0초 휘발유 붓기. 첫 3초 붓기→발화→승객 반응. 본문 1.6초 내외, 법정 1.2–1.5초, 정답 21.8667초부터, 별도 다음 사건 24.3667–25.8667초. 8/12/20년은 보기일 뿐 정답 표시는 656프레임 전까지 없음. 기존 Analytics 일별 스냅샷의 engagedViews/views를 engagement_daily.csv에 기록: 2026-11-06 반환 13개 표본 합계 4720/13618=34.66%. 누적 스냅샷 비율이며 viewed-vs-swiped-away와 다른 지표다. q020은 미발행이라 성과 없음.',
 'H3':'근거 확인·CTO 소재 판정 대기. RANKED Shorts 3위 V2-14. YouTube 원본 3개 성과 비교 중앙값 62.61배, 네이버 검색 정점/기준어 일중앙값 146.86배. 절대 검색량·조회수 예측값 아님. 1심 검찰 구형 20년/항소심 선고 12년 구별. topic_evidence.json 및 원문 4개 결속.',
 'H4':'제작자 화면 확인·CTO 판정 대기. 베이지 패널·장식 배지·회차·고지 코너·헤더 스택·검정/템플릿 엔딩 제거. 전체 화면 카툰, 음성 자막 한 층. 카드 박스는 H10에서 명시한 A/B/C 선택 기능에만 사용했다. 구형 귀속·실제 양형 인자 스탬프는 사실 표시. 원본 C3 자동 결과는 아래에 그대로 기록하며 이 설명으로 자가 면제하지 않는다.',
 'H5':'치수·문구 비교 확인. 음성 자막 전 cue 가로 중심 x540, 64px, 800, 검정 외곽선 8px, 2줄 이하·줄당 14자 이하, y1190–1344(약62–70%). 글자 강조는 노랑 한 어구. 기존 17개 부모 cue의 단어·발화 시작/끝·음성·답 공개를 유지했고 최신 H5 우선으로 긴 3개 cue만 실제 ASR 단어 경계에서 20개 페이지로 나눴다. subtitle_pagination.json에 원문·부모·자식·줄별 문자 수를 기록했다. CTO 읽기·싱크 판정 대기.',
 'H6':'장면·행동 확인·CTO 판정 대기. 법정 첫 샷은 공간이 읽히는 구도. 이어 판사 발언 제스처/표정→피고인 눈·머리·팔 반응→저울의 실제 기울임→피해자 가상 반응→재판부 판단을 1.2–1.5초로 전환. 피해 회복 미진·대중교통 신뢰 침해가 스탬프처럼 등장. 656프레임에서 법봉 타격과 나무 타격음·정답 점등. 카메라 흔들기만으로 움직임을 만들지 않았다. 실제 역사적 법봉 사용·피해자 법정 출석을 주장하지 않으며 설명란에 한계를 명시했다.',
 'H7':'그림 확인·CTO 판정 대기. 피해자 포함 모든 실제 렌더 인물은 원본 q014 계열의 눈·코·입 있는 독창 toon 얼굴이다. 얼굴 없는 작은 인물 기호를 제거하고 혐의 계수 장면도 표정 있는 성인 캐릭터로 교체했다. 실명·실제 인물 사진·외모 미사용. 얼굴/표정 확대 근거는 preview_467.png 및 전 프레임 시트.',
 'H8':'렌더 경로 확인. 전 구간 q014 ArticulatedGuy 및 2D SVG, 카툰만 사용. Blender·3D 도입/엔딩·3D 영상 입력 없음. render_source_sha256.json 및 전 프레임 시트로 확인할 수 있다.',
 'H9':f'화면·OCR 확인. 재구성/시간 축약·압축/시각비유/시리즈 코너 고지 0. 전 프레임 OCR 해당 문자열 검출 {len(hits)}건. 고지는 설명란으로 이동. 1심 검찰 구형과 항소심 선고는 사실이므로 화면에 유지. OCR 단독으로 부재를 증명하지 않고 대표·전체 시트와 함께 CTO 확인 대기.',
 'H10':f'타이밍·그림 확인·CTO 판정 대기. A/B/C는 510/517/524프레임에 색 카드로 등장하고 531프레임에 모두 펼쳐진다. 정답 656프레임까지 최소 {choices["all_options_choose_time_s"]:.3f}초 선택 시간. 댓글 요청·5→1 카운트다운. 656프레임부터 B(징역12년)만 점등, A/C는 불투명도 .24. choices.json에 보기와 정답·프레임 기록. 보기 8년은 보도된 실제 형이 아니며 오답이다.',
 'H11':'이 작업에는 외부 비공개 교체본 생성·업로드 0건. 따라서 대체본 readback 후 삭제할 YouTube ID/URL 없음. Studio 삭제 작업은 수행하지 않았다. 기존 로컬 파일은 이전 지시대로 기록으로 보존했으며 대체 전 방향임을 표시했다.',
 'H12':'직접 실행 확인. 기존 네이버·YouTube 조사 스냅샷, 로컬 TTS·Whisper·Remotion을 사용했다. 원일에게 키·파일 업로드·제작 작업을 넘기지 않았다. 불필요한 새 외부 권한·업로드 없음.',
 'H13':'CTO 판정 대기·확대 금지. 776프레임/30fps 전체 디코딩 및 F1 시트, 0–3초 91연속 프레임 PNG, 모든 컷 앞뒤·중간 대응표를 생성. CTO가 이탈 구간·MATCH·재미를 판정하기 전 CEO/원일 승인본으로 전달하지 않는다. 새 방향은 q020만 렌더. 다른 5편은 대본·설계만 준비하고 q013 v3 및 q020 CTO 검수 완료까지 HELD.'
}
checks={k:dict(producer_observation=v,cto_verdict='PENDING') for k,v in H.items()}
r.update(owner_H_self_check=checks,producer_status='NOT_APPROVED_CTO_REVIEW_PENDING',owner_ready_note=str((p/'READY.txt').resolve()),ready=False,ceo_review_eligible=False,owner_delivery_ready=False,all_A1_H13_items_are_fail_conditions=True)
r['limits']=list(dict.fromkeys([*r['limits'],'H1–H13 제작자 관측은 CTO PASS가 아니다. A–G 자동 결함을 면제하지 않으며 CEO/원일 승인본 전달을 보류한다.']))
(p/'qa.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
source_paths=[B/'entry.tsx',B/'TrainFilm.tsx',B/'CaseFilm.tsx',B/'Reenactment.tsx',W/'episodes/quiz/q014/fight_revision/comedy/FightRig.tsx',W/'factory/unslop/STYLE_VIDEO.md',W/'factory/REVIEW_CHECKLIST.md']
(p/'render_source_sha256.json').write_text(json.dumps({str(f.resolve()):sha(f) for f in source_paths},ensure_ascii=False,indent=2)+'\n')
header='제작자 self-check / CTO PASS 아님\n상태: NOT_APPROVED — 자동 미충족 항목 및 CTO 판정 대기. CEO·원일 승인본 전달 보류.\n\n'
header+='파일: '+str((p/'video.mp4').resolve())+'\nSHA256: '+sha(p/'video.mp4')+'\n규격: 1080x1920 / 30fps / 776 frames / 25.866667s\n발행 예정: CTO 순서·검수 확정 전 미정. 제안 창 2026-11-07~12 19:00 KST, 소재 1순위는 q018. 업로드/번호 배정 없음.\n'
header+='\n전 프레임: '+str((out/'F1.md').resolve())+'\n핵심 행위 0–3초 91연속프레임: '+str((out/'action_0-3s_all.png').resolve())+'\n음성↔화면·모든 컷: '+str((out/'D1_D2_cut_sheet.md').resolve())+'\n팩트·심급: '+str((out/'E3.md').resolve())+'\n'
header+='\n기존 공장 검수 A–G 결과(원값 보존, advisory도 면제 아님)\n'
for k,g in r['gates'].items():header+=f'{k}: {g["status"]} / {g.get("review_state","UNKNOWN")}\n'
header+='미충족: '+', '.join(raw_defects)+'\n원문 증거·판정 이유는 qa.json. C1은 속도 8.04음절/s이지만 ASR 쉼 경고가 남음. C3의 자막 외 텍스트 판정과 H10 기능성 카드 요구가 충돌하며 자가 PASS·면제하지 않음. D2의 일부 컷은 자동 절 경계 ±0.12초 조건 미달.\n'
header+='\nH1–H13 제작자 항목별 관측 / CTO 최종 판정 별도\n\n'+'\n\n'.join(k+': '+v for k,v in H.items())
header+='\n\n사실 출처 (구형 1심 / 선고 항소심)\n'+'\n'.join(s['publisher']+' | '+s['url']+' | '+s['sha256'] for s in sources)+'\n\n실시간 재생 미검수. 전체 디코딩·연속 시트·최종 ASR·음량/싱크 수치가 대체 근거다.\n'
(p/'READY.txt').write_text(header);(B/'READY.txt').write_text(header)
(B/'FIRST_READY.txt').write_text('NOT_APPROVED / CTO 검수용 생성 완료. CEO·원일 승인본 전달 보류.\nFINAL: '+str((p/'video.mp4').resolve())+'\nSHA256: '+sha(p/'video.mp4')+'\nREADY: '+str((p/'READY.txt').resolve())+'\nFULL_SHEET: '+str((out/'F1.md').resolve())+'\nKEY_ACTION_CONSECUTIVE: '+str((out/'action_0-3s_all.png').resolve())+'\nVOICE_PICTURE: '+str((out/'D1_D2_cut_sheet.md').resolve())+'\n나머지 5편 새 방향 렌더 보류; q013 v3·q020 CTO 검수 대기. 제작자 PASS 없음. 업로드 없음.\n')
(p/'SHA256SUMS').write_text(''.join(sha(p/n)+'  '+n+'\n' for n in ['video.mp4','cover.jpg','meta.txt','qa.json','READY.txt','choices.json','subtitle_pagination.json','render_source_sha256.json']))
print('READY written; raw defects:',raw_defects,'H9 OCR hits:',len(hits),'hash:',sha(p/'video.mp4'))
