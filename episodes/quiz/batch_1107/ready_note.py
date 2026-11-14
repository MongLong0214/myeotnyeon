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
grammar=load(p/'direction_grammar.json');lock=load(B/'animatic_lock.json')
assert [(s['start_s'],s['end_s']) for s in shots]==[(s['start_s'],s['end_s']) for s in lock['shots']]
hold=next(s for s in shots if s['director_mode']=='choice_hold')
assert round(hold['start_s']*30)==510 and round(hold['end_s']*30)==656
assert all(s['end_s']-s['start_s']<=1.500001 for s in court if s['director_mode']!='choice_hold')
assert all(s['end_s']-s['start_s']<hold['end_s']-hold['start_s'] for s in shots if s['director_mode']!='choice_hold')
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
 'H1':'실행·격차 명시. 제공된 기준 9→1000명까지 991명. 0.5명/1000뷰이면 약 1,982,000뷰가 필요하고 6편×1800뷰로는 약 5.4명이다. 실험 목표 2명/1000뷰이면 필요한 조회수는 495,500뷰(달성 보장 아님). 레버는 0초 행위, 첫 3초 행동→반응, 실제 다음 사건, 댓글 퀴즈와 선택 카드. q020에 이미 적용했고 5편 대본·설계는 준비했다. CTO 검수 뒤 첫 24시간 engagedViews/views·구독 전환을 비교해 확산할 훅을 고른다.',
 'H2':'관측 확인·발행 후 측정 대기. 0초 휘발유 붓기. 첫 3초 붓기→발화→승객 반응은 하드컷. 본문 1.6초 내외, 절차 3샷 각 .767/.8/.767초, 법정에는 .9초 반응 연결. 최신 소유자 지시로 가장 긴 숙고 구도는 선택 장면 17–21.8667초. 정답 21.8667초부터, 별도 다음 사건 24.3667–25.8667초. 8/12/20년은 보기이며 정답 표시는 656프레임 전까지 없음. Analytics 스냅샷 engagedViews/views는 engagement_daily.csv: 2026-11-06 반환 13개 표본 4720/13618=34.66%. 누적 스냅샷 비율이며 viewed-vs-swiped-away와 다른 지표다. q020은 미발행으로 성과 없음.',
 'H3':'근거 확인·CTO 소재 판정 대기. RANKED Shorts 3위 V2-14. YouTube 원본 3개 성과 비교 중앙값 62.61배, 네이버 검색 정점/기준어 일중앙값 146.86배. 절대 검색량·조회수 예측값 아님. 1심 검찰 구형 20년/항소심 선고 12년 구별. topic_evidence.json 및 원문 4개 결속.',
 'H4':'제작자 화면 확인·CTO 판정 대기. 베이지 패널·장식 배지·회차·고지 코너·헤더 스택·검정/템플릿 엔딩 제거. 전체 화면 카툰, 음성 자막 한 층. 카드 박스는 H10에서 명시한 A/B/C 선택 기능에만 사용했다. 구형 귀속·실제 양형 인자 스탬프는 사실 표시. 원본 C3 자동 결과는 아래에 그대로 기록하며 이 설명으로 자가 면제하지 않는다.',
 'H5':'치수·문구 비교 확인. 자막 중심 x540, 64px/800/검정 외곽선8px, 2줄 이하·줄당14자 이하, y1190–1344(약62–70%). 강조는 노랑 한 어구. 이번 연출 수정에서는 확정된 20개 자막 cue와 내레이션·답 공개 시점을 전혀 바꾸지 않았다. 이전 17개 부모 cue의 단어와 시작/끝을 유지한 페이지 분할 내역은 subtitle_pagination.json에 보존. CTO 읽기·싱크 판정 대기.',
 'H6':'장면·행동 확인·CTO 판정 대기. 360x640 음성 포함 애니매틱으로 먼저 샷 순서·길이를 잠갔고 이후 바꾸지 않았다(animatic_lock.json). 잘린 옆 인물이 끼는 클로즈업을 제거했다. 와이드→피고인 얼굴→저울→피고인/진지한 피해자/판사 .9초 연결→선택 고정 구도→3프레임 선고 snap→피고인 .6초 deadpan→어깨 너머 판사로 이어진다. 판사는 판결 전 안경을 조정하며 피고인은 카드마다 다른 포즈·옆눈. 과장·땀은 피고인의 가상 반응에만, 탄성·배경 연필 반응은 법봉/저울 비유에만 적용했다. 피해·사망·상해·피해자 반응은 개그 재료로 쓰지 않았다. 선택 구도 4.867초는 최신 지시의 의도된 최장 숙고 구도이며 일반 대화의 정체와 구별한다. 아래 자동 결과를 자가 면제하지 않는다.',
 'H7':'그림 확인·CTO 판정 대기. 피해자 포함 인물은 원본 q014의 눈·코·입 있는 독창 toon 리그·표정 범위를 그대로 썼다. 캐릭터 기하를 새로 만들거나 외부 쇼의 디자인을 복제하지 않았다. 클로즈업은 대상만 보여 주변 얼굴이 잘리는 어색한 배치를 제거했다. 어깨 너머 컷의 전경은 프레임 밖 인물의 어깨다. 피해자에는 만화적 변형·땀·익살을 추가하지 않았고 기존 입가 물방울도 감췄다. 실명·사진·실제 외모 미사용.',
 'H8':'렌더 경로 확인. 전 구간 q014 ArticulatedGuy 및 2D SVG, 카툰만 사용. Blender·3D 도입/엔딩·3D 영상 입력 없음. render_source_sha256.json 및 전 프레임 시트로 확인할 수 있다.',
 'H9':f'화면·OCR 확인. 재구성/시간 축약·압축/시각비유/시리즈 코너 고지 0. 전 프레임 OCR 해당 문자열 검출 {len(hits)}건. 고지는 설명란으로 이동. 1심 검찰 구형과 항소심 선고는 사실이므로 화면에 유지. OCR 단독으로 부재를 증명하지 않고 대표·전체 시트와 함께 CTO 확인 대기.',
 'H10':f'타이밍·그림 확인·CTO 판정 대기. A/B/C는 510/522/534프레임부터 각12프레임(.4초) 강조하며 3프레임 순간 확대·각기 다른 음색/피고인 포즈를 붙였다. 546프레임에 모두 안정된 뒤 정답656프레임까지 {choices["all_options_choose_time_s"]:.3f}초 고를 수 있다. 선택 고정 구도는 전체에서 가장 길고, 댓글 요청·5→1 카운트다운으로 숙고를 유도한다. 656프레임부터 B(징역12년)만 점등, A/C는 .24. 보기 8년은 실제 보도된 형이 아닌 오답이다. 카드 텍스트는 x110–870/y1376–1540 안, 값72px로 배치해 Shorts 조작 영역을 피했다. choices.json 참조.',
 'H11':'이 작업에는 외부 비공개 교체본 생성·업로드 0건. 따라서 대체본 readback 후 삭제할 YouTube ID/URL 없음. Studio 삭제 작업은 수행하지 않았다. 기존 로컬 파일은 이전 지시대로 기록으로 보존했으며 대체 전 방향임을 표시했다.',
 'H12':'직접 실행 확인. 기존 네이버·YouTube 조사 스냅샷, 로컬 TTS·Whisper·Remotion을 사용했다. 원일에게 키·파일 업로드·제작 작업을 넘기지 않았다. 불필요한 새 외부 권한·업로드 없음.',
 'H13':'CTO 판정 대기·확대 금지. 애니매틱 순서/타이밍 확인 후 q020만 마감했다. 776프레임/30fps 전체 F1, 첫3초 91연속프레임, .9초 반응 연결, 선택 beat, 선고snap/deadpan의 연속 PNG와 모든 컷 대응표를 생성했다. 영상의 이상한 컷·배치와 시청자가 넘길 구간은 CTO가 최종 판정한다. 제작자 PASS/MATCH 없음. 나머지 5편은 파일 변경·새 렌더 없이 q013 v3 및 q020 CTO 검수 완료까지 HELD. references/rick_and_morty/RM_DIRECTING_REFERENCE.md의 참고 문법만 적용했으며 특정 쇼의 컷 수/분을 주장하지 않는다.'
}
checks={k:dict(producer_observation=v,cto_verdict='PENDING') for k,v in H.items()}
r.update(planned_publish_time='CTO 검수·순서 확정 전 미정 (2026-11-07~12 19:00 KST 제안)',owner_H_self_check=checks,producer_status='NOT_APPROVED_CTO_REVIEW_PENDING',owner_ready_note=str((p/'READY.txt').resolve()),ready=False,ceo_review_eligible=False,owner_delivery_ready=False,all_A1_H13_items_are_fail_conditions=True)
r['limits']=list(dict.fromkeys([*r['limits'],'H1–H13 제작자 관측은 CTO PASS가 아니다. A–G 자동 결함을 면제하지 않으며 CEO/원일 승인본 전달을 보류한다.']))
(p/'qa.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
source_paths=[B/'entry.tsx',B/'TrainFilm.tsx',B/'CaseFilm.tsx',B/'Reenactment.tsx',B/'direct.cjs',B/'finish.py',B/'animatic_lock.json',W/'references/rick_and_morty/RM_DIRECTING_REFERENCE.md',W/'episodes/quiz/q014/fight_revision/comedy/FightRig.tsx',W/'factory/unslop/STYLE_VIDEO.md',W/'factory/REVIEW_CHECKLIST.md']
(p/'render_source_sha256.json').write_text(json.dumps({str(f.resolve()):sha(f) for f in source_paths},ensure_ascii=False,indent=2)+'\n')
header='제작자 self-check / CTO PASS 아님\n상태: NOT_APPROVED — 자동 미충족 항목 및 CTO 판정 대기. CEO·원일 승인본 전달 보류.\n\n'
header+='파일: '+str((p/'video.mp4').resolve())+'\nSHA256: '+sha(p/'video.mp4')+'\n규격: 1080x1920 / 30fps / 776 frames / 25.866667s\n발행 예정: CTO 순서·검수 확정 전 미정. 제안 창 2026-11-07~12 19:00 KST, 소재 1순위는 q018. 업로드/번호 배정 없음.\n'
header+='\n전 프레임: '+str((out/'F1.md').resolve())+'\n핵심 행위 0–3초 91연속프레임: '+str((out/'action_0-3s_all.png').resolve())+'\n음성↔화면·모든 컷: '+str((out/'D1_D2_cut_sheet.md').resolve())+'\n팩트·심급: '+str((out/'E3.md').resolve())+'\n'
header+='\n기존 공장 검수 A–G 결과(원값 보존, advisory도 면제 아님)\n'
for k,g in r['gates'].items():header+=f'{k}: {g["status"]} / {g.get("review_state","UNKNOWN")}\n'
header+='미충족: '+', '.join(raw_defects)+'\n원문 증거·판정 이유는 qa.json. 최신 지시의 선택 숙고·정적 박자·기능성 카드와 기존 자동 정적/자막 외 텍스트 기준이 충돌할 수 있으며 자가 PASS·면제하지 않는다. D2의 일부 짧은 반응 컷은 자동 절 경계 ±0.12초 조건에 미달할 수 있다.\n'
c1=r['gates']['C1']['evidence'];c2=r['gates']['C2']['evidence'];c3=r['gates']['C3']['evidence'];d2=r['gates']['D2']['evidence']
header+='ASR 기반 C1: 속도 '+str(c1.get('syllables_per_second'))+'음절/s, 쉼 경고 '+json.dumps([z for z in c1.get('pauses',[]) if not z.get('pass_',False)],ensure_ascii=False)+'\n'
header+='C2 정적 구간: '+str(c2.get('static_spans'))+' (최신 지시의 선택 숙고 구도 안; 자가 면제 안 함)\n'
header+='C3 관측: 인물 비율 '+str(c3.get('character_share'))+', 모션 컷 비율 '+str(c3.get('motion_share'))+'; 의도된 정적 박자·기능성 카드와 기존 기준 충돌을 CTO가 판정해야 함.\n'
header+='D2 절 경계 조건 미달: '+str(sum(not z.get('pass_',False) for z in d2.get('cuts',[])))+'/'+str(len(d2.get('cuts',[])))+'개 컷. 실제 컷·음성·자막 프레임은 D1_D2_cut_sheet.md.\n'
header+='\nH1–H13 제작자 항목별 관측 / CTO 최종 판정 별도\n\n'+'\n\n'.join(k+': '+v for k,v in H.items())
header+='\n\n사실 출처 (구형 1심 / 선고 항소심)\n'+'\n'.join(s['publisher']+' | '+s['url']+' | '+s['sha256'] for s in sources)+'\n\n실시간 재생 미검수. 전체 디코딩·연속 시트·최종 ASR·음량/싱크 수치가 대체 근거다.\n'
header+='\n애니매틱: '+str((B/'animatic_q020.mp4').resolve())+'\n타이밍 잠금: '+str((B/'animatic_lock.json').resolve())+'\n반응 연결: '+str((out/'rapid_reaction_consecutive.png').resolve())+'\n순간 확대·정적 박자: '+str((out/'snap_deadpan_consecutive.png').resolve())+'\n선택지 beat: '+str((out/'choice_beats_consecutive.png').resolve())+'\n'
(p/'READY.txt').write_text(header);(B/'READY.txt').write_text(header)
(B/'FIRST_READY.txt').write_text('NOT_APPROVED / CTO 검수용 생성 완료. CEO·원일 승인본 전달 보류.\nFINAL: '+str((p/'video.mp4').resolve())+'\nSHA256: '+sha(p/'video.mp4')+'\nREADY: '+str((p/'READY.txt').resolve())+'\nFULL_SHEET: '+str((out/'F1.md').resolve())+'\nKEY_ACTION_CONSECUTIVE: '+str((out/'action_0-3s_all.png').resolve())+'\nVOICE_PICTURE: '+str((out/'D1_D2_cut_sheet.md').resolve())+'\n나머지 5편 새 방향 렌더 보류; q013 v3·q020 CTO 검수 대기. 제작자 PASS 없음. 업로드 없음.\n')
(p/'SHA256SUMS').write_text(''.join(sha(p/n)+'  '+n+'\n' for n in ['video.mp4','cover.jpg','meta.txt','qa.json','READY.txt','choices.json','subtitle_pagination.json','render_source_sha256.json','direction_grammar.json','direction_measurements.json']))
print('READY written; raw defects:',raw_defects,'H9 OCR hits:',len(hits),'hash:',sha(p/'video.mp4'))
