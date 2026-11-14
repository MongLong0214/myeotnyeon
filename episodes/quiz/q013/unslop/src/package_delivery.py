from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json, hashlib, re

W = Path('/Users/isaac/projects/verdict-kr/work')
D = W / 'episodes/quiz/q013/unslop'
E = W / 'episodes/review_full/unslop/q013'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
now = datetime.now(ZoneInfo('Asia/Seoul'))
styles = {}
for name in ['DIAGNOSIS.md', 'STYLE_VIDEO.md']:
    p = W / 'factory/unslop' / name
    styles[name] = {'exists': p.exists(), 'checked_kst': now.isoformat()}
    if p.exists():
        styles[name].update(sha256=sha(p), read_and_applied=True)
notes = json.loads((E / 'review_notes.json').read_text())
notes.update(completed_kst=now.isoformat(), style_documents_at_packaging=styles,
             style_source='Latest direct Owner correction and CEO Addendum 1 applied; both style documents read.')
notes['ceo_addendum_1_applied'] = True
notes['owner_subtitle_correction_applied'] = True
notes['style_application'] = [
    '사건 질문은 도입 0–60프레임에만 표시. 박치기 22회는 동작 구간 61–203프레임에 별도 무박스 글자로 유지.',
    '배지·양형 사정 박스·저울 위 텍스트 표찰·설명 띠·자동 노란 강조·구독 카드 제거.',
    '장면 배경을 화면 끝까지 확장하고 인물 연기를 크게 배치.',
    '보기는 원래 노출 구간을 보존하라는 이번 지시에 따라 329–662프레임 유지.',
    '일반 고딕 유지 제안 대신 이번 지시의 개성 있는 한국어 자막 요청에 따라 도현체 사용.',
    '재구성 고지는 전 구간, 시간 압축은 61–203, 시각비유는 204–754프레임에 모서리 36px 무박스 글자로 표시.',
    'CEO 추가 지시의 구형·선고 비교를 710–799프레임에 유지. Owner 가독성 지시로 64px 두 줄·가로 중앙으로 조판.',
    'Owner 자막 규격: 중심 x540, 72px, 굵기800, 검정 외곽선10px, 부드러운 그림자, 최대2줄·줄당14자, y1192–1342(62.08–69.90%).',
    '정답의 벌금 400만 원 한 구절만 #FFD400으로 강조. 내레이션 문구와 타이밍은 유지.',
]
notes['visual_review']['observations'][0] = '장식 배지·상시 사건 제목·카운터 박스·양형 목록 제거. 필수 고지와 사실 정보는 무박스 글자로 화면에 유지.'
notes['visual_review']['reviewed_from_final_mp4'] = [
    '최종 변경 후 1fps 비교 시트 전체 27개 시점 재확인',
    '최종 변경 후 64개 경계·접촉 프레임 시트 재확인',
    '최종 변경 후 f0090 원본 크기 PNG 확인; 174프레임 접촉·비식별 구도도 확인',
    'CEO 추가 지시의 화면 고지·22회·구형/선고 비교를 ceo_addendum_1_360p.png와 원본 크기 추출에서 확인',
    'Owner 자막의 모든 노출 cue를 브라우저 computed style/실제 텍스트 bounds로 측정하고 owner_correction_360p.png 확인',
]
(E / 'review_notes.json').write_text(json.dumps(notes, ensure_ascii=False, indent=2))
paths = [W / 'upload/v52_q013_n16_unslop.mp4', W / 'upload/cover_v52_q013_n16_unslop.png']
paths += sorted(E.glob('*.png'))
paths += [E / n for n in ['audio_identity.json', 'timing_preservation.json', 'audio_packets.json',
                          'video_presentation_timestamps.json', 'ffprobe.json', 'full_decode.log', 'review_notes.json',
                          'required_on_screen_information.json', 'subtitle_legibility.json', 'subtitle_layout_observed.json']]
paths += [D / n for n in ['description_note.txt', 'typecheck.log', 'original_sha256.json']]
paths += [D / 'src' / n for n in ['render.json', 'captions.json', 'Unslop.tsx', 'ComedyLogic.tsx',
                                 'FightScene.tsx', 'FightRig.tsx', 'render_unslop.cjs', 'assemble_final.py',
                                 'verify_unslop.py', 'entry.tsx', 'package_delivery.py']]
sums = ''.join(f'{sha(p)}  {p.relative_to(W)}\n' for p in paths)
(D / 'SHA256SUMS').write_text(sums)
ready = f'''q013 #16 — 2026-11-06 19:00 KST 예약 Short / UI·자막 수정본
준비 시각: {now.isoformat()}
마감: 2026-11-06 16:30 KST
상태: CTO·CEO 검토 대기. 자체 채택 판정 없음. 업로드 작업 없음.

영상: upload/v52_q013_n16_unslop.mp4
규격: 1080×1920 / 30 fps / 800 frames / 영상 26.666667초, 오디오 26.667초
커버: upload/cover_v52_q013_n16_unslop.png (텍스트 박스 없음)
전후 비교: episodes/review_full/unslop/q013/before_after_1fps.png
0–26초의 정각, 같은 프레임을 좌 원본 / 우 수정본으로 배치. 3장 분할 시트도 포함.
세부 경계·22회 접촉: episodes/review_full/unslop/q013/boundaries/ 및 boundary_contact_sheet.png
설명란 교체 안내: episodes/quiz/q013/unslop/description_note.txt
CEO 추가 지시 증빙: episodes/review_full/unslop/q013/ceo_addendum_1_360p.png
Owner 자막 수정 증빙: episodes/review_full/unslop/q013/owner_correction_360p.png
Owner 자막 실측: episodes/review_full/unslop/q013/subtitle_legibility.json 및 subtitle_layout_observed.json

Owner correction 적용:
- 각 줄의 실제 텍스트 중심과 자막 박스 중심 모두 x540. 좌우 오프셋 없음.
- 72px / CSS 굵기800 / 흰색 / 검정 외곽선10px / 부드러운 그림자.
- 최대2줄, 공백·문장부호를 포함해 줄당14자 이하.
- 고정 자막 박스 y1192–1342, 화면 높이의62.08–69.90%. 얼굴을 가리지 않는 위치.
- 정답의 벌금 400만 원 한 구절만 #FFD400으로 강조. 박스·띠 없음.
- 모든 노출 내레이션 cue와 엔딩 UI를 브라우저에서 실측. 문구·타이밍 변경 없음.

CEO Addendum 1 적용 (이전 UI 제거 지시보다 우선):
- 재구성: 전 구간, 우측 상단 36px 무박스 글자.
- 시간 압축: 61–203프레임, 재구성 · 시간 압축으로 고지.
- 시각비유: 204–754프레임, 재구성 · 시각비유로 고지.
- 박치기 22회: 도입 제목·원래 자막 외에도 61–203프레임에 64px 무박스 글자로 유지.
- 구형 징역 1년 → 선고 벌금 400만 원: 원래 구형 발화 시작710프레임부터 끝799프레임까지 유지. Owner 가독성 지시로64px·두 줄·가로 중앙 조판.
- 설명란에도 상세 안내를 유지하되 화면 고지를 대체하지 않음.

검사:
- AAC payload SHA256 및 PCM float32 48kHz stereo SHA256: 원본과 동일.
- 오디오 1,252개 패킷의 payload hash·PTS·DTS·duration·size·side data: 동일.
- 영상 800프레임의 PTS·duration: 동일.
- render.json의 자막 문구·시작/종료·장면 cue·앵커: 동일. 일부 줄바꿈만 변경.
- 실제 본문 자막 노출은 원본처럼 [61,755)에서 원래 구간과 교차함. 오프닝 0–60, 엔딩 755–799 UI 경계 유지.
- 보기 329–662 / 정답 자막 668 / 선고 문서 첫 표시 676 / 구형 자막 710 / 엔딩 755 유지.
- 원본의 669프레임 정답 헤더는 삭제. 선고·구형은 원래 자막·음성과 추가된 710프레임 비교 문구로 구분.
- FightRig 파일, 인물 pose 계산, ArticulatedGuy props: 원본과 동일. 화면 크기·배치 변경, 텍스트 UI 제거/수정.
- 양형 표찰을 없애고 한 구간씩 내레이션 자막으로 전달. 판사·저울의 동작 시계 유지.
- 원본 소스와 comedy MP4 변경 파일: 0개. src 복사본에서 작업.
- TypeScript 종료 코드 0. 전체 MP4 디코딩 오류 출력 없음.
- 최종 MP4의 27개 1fps 시점과 64개 경계·접촉 프레임 시트 확인.

DIAGNOSIS.md와 STYLE_VIDEO.md의 Owner correction을 읽고 적용함. 최신 Owner 자막 지시와 CEO Addendum 1의 필수 화면 고지를 함께 유지. 도현체와 원래 보기 노출 시간 유지.
연속 청취는 별도 수행하지 않았으며 전체 오디오 payload·PCM·패킷 비교로 동일성을 확인.

원본 MP4 SHA256: 5b6d2a9820610798adc8f361458336e47de95c972e0a2a17fbefc92a93948b01
전체 산출물 SHA256 (workspace 상대 경로):
{sums}'''
(D / 'READY.txt').write_text(ready)
(E / 'READY.txt').write_text(ready)
print(json.dumps({'completed_kst': now.isoformat(), 'video_sha256': sha(paths[0]),
                  'ready': str(D / 'READY.txt'), 'style_docs': styles}, ensure_ascii=False, indent=2))
