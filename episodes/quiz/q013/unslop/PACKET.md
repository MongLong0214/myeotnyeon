# Task: re-style today's 19:00 KST Short q013 #16 so it no longer looks AI-made (subtitles and UI only) — W=/Users/isaac/projects/verdict-kr/work

Owner: "오늘 발행 예약 걸려있는 숏폼도 ai스럽지않게해줘" (make today's scheduled Short not look AI-made too).
**Deadline: final render plus evidence by 16:30 KST** (it then goes through CTO and CEO review and a replacement upload).

Source: W/episodes/quiz/q013/fight_revision/comedy/ (final W/upload/v52_q013_n16_comedy.mp4, sha 5b6d2a98…). Copy it to `W/episodes/quiz/q013/unslop/src/` and work there; the original stays untouched.

## Keep (do not change)
- Audio stream (AAC payload and PCM identical), the timing of subtitles, choices and answer, the reenactment animation and its timing.
- Facts, the demand-vs-sentence distinction, victims not identifiable.

## Change: remove the AI feel from subtitles, UI and layout
1. Remove the top header stack (the small "몇년나옴? 형량 퀴즈 #16" badge, two title lines, labels).
   - Keep one line, natural like a human editor's caption (e.g. "박치기 22번. 몇 년?").
   - The series mark: a small corner text "몇년나옴 #16", not a badge.
2. Remove meta labels: "사건 재구성 · 공장 기숙사 · 시간 압축", "시각비유", "보도 기반 재구성" and the like. Replace them with one small, quiet fixed corner text, "재구성", plus a note in the description.
   - The time-compression disclosure goes into the description too.
3. Card and box template: no rounded boxes, pill badges, uniform cards, the paper-background panel frame, or the "판사가 본 사정" box list.
   - The reenactment goes full-bleed or nearly so.
   - The sentencing factors become short spoken-style captions, shown one at a time over the picture.
4. Subtitles: a Korean font with character (avoid the generic Pretendard Black + yellow highlight combination).
   - Thick white letters with a black outline, natural line breaks, size changes for emphasis only. No boxed subtitle backgrounds.
   - Keep the text identical to the narration; only line breaks and emphasis are design choices.
5. Remove the counter "박치기 00/22회" box. Show the count as one large hand-written-style digit (e.g. a "22" that grows), or as a subtitle.
6. Ending card: remove the "다음 판결도 맞혀보세요 → 구독" template card and keep only a natural one-line text.
   - Remove the black ending card with the gray background and the red subscribe button too.
7. Also read W/factory/unslop/DIAGNOSIS.md and STYLE_VIDEO.md if they exist (another lane is writing them) and apply them.

## Output
- W/upload/v52_q013_n16_unslop.mp4 (1080x1920)
- A cover if needed (a cover version without text boxes)
- A before/after sheet (1 fps, the same timestamps side by side) as PNG under W/episodes/review_full/unslop/q013/
- An audio identity check and a timing preservation check
- READY.txt with the sha256 values

No self-assigned PASS. No uploads. Final message: short, in Korean.
