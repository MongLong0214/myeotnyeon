# Task: q013 #16 Shorts reenactment revision (the q014 comedy method) — W=/Users/isaac/projects/verdict-kr/work

## Background
- The owner praised the reenactment scene in q014's comedy revision: "어제올린 숏폼 재현 장면 맘에들었어" (I liked the reenactment scene in yesterday's Short).
  - File: W/upload/v52_q014_n15_comedy.mp4
  - Source: W/episodes/quiz/q014/fight_revision/comedy/ — entry.tsx, FightScene.tsx, FightRig.tsx, ComedyLogic.tsx, ObjectSets.tsx, render_fight.cjs, result_packet.json
  - Method: keep the original audio stream and the subtitle, choice and answer timing; replace only the picture with character acting, visual metaphors, and the sequence wind-up → action → contact → reaction.
- Current q013 #16: W/upload/v52_q013_n16.mp4 (package W/upload/pkg/q013_n16_v4). The incident scenes show an empty dormitory room with a "박치기 22번" (22 headbutts) label, a courthouse building and a magnifying glass. There is no character acting, which matches the owner's earlier "인물 없음·교육자료" (no characters, teaching material) complaint.

## Do
- Copy into W/episodes/quiz/q013/fight_revision/comedy/ and work there. Do not modify q014 or the shared engine.
- Keep: the original audio stream and decoded PCM, the subtitle, choice and answer timing, and the title card and ending card.
- Rebuild the incident scenes (about 2–8 s) with the q014 characters and rig. Facts only (W/episodes/quiz/v52_q013_q014_support/q013_fact_matrix.json, the facts file):
  - In a dormitory at the factory, the manager headbutts a Vietnamese worker in his 20s over a change of food-delivery spot.
  - The worker ends up with a concussion and other injuries.
  - Manager: a faceless or silhouette caricature allowed. Victim: unidentifiable, no gore, never mocked.
  - Show the repetition (22 times) through motion and a counter, without gore.
- Courtroom and sentencing scenes: in the q014 style, the judge character with the "판사가 본 사정" (what the judge weighed) items and visual metaphors.
  - Clearly separate the actual reenactment from the metaphors.
  - Do not over-fill the screen with text.
- Output:
  - W/upload/v52_q013_n16_comedy.mp4 (1080x1920)
  - a cover candidate cover_v52_q013_n16_comedy.jpg
  - result_packet.json with the sha256 values, an audio/PCM identity check, timing preservation, and frame sheets of the changed frames
- **Deadline: render complete by 15:00 KST today.** It must be published at 19:00 today.

No self-assigned PASS. No uploads or network access. Final message: short, in Korean.
