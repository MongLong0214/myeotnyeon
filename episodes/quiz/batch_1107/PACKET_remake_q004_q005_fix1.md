# q004/q005 remake: CTO review FAIL (fix1)

Reviewed: episodes/review_full/shorts/q004/std_1fps.png and q005/std_1fps.png.

Pass, keep as is:
- frame-1 hooks;
- A/B/C cards;
- answer reveal;
- next-case end card;
- victim depiction per the facts (q005);
- subtitle style.

## F1. The courtroom section is static (owner H rule: "재판 판결씬 … 최대한 동적이고 다이나믹하게")
- q004 runs 6–14 s, q005 runs 7–14 s. Both are the same two-person full shot (judge left, defendant right) held for about 8 s, and only the pose changes.
- Rebuild that span as 2–3 s shots with different framings:
  - a low angle on the bench with a push-in;
  - a defendant reaction close-up;
  - an over-the-shoulder shot to the judge;
  - an insert of the evidence or the CCTV;
  - a gavel hit on the beat.
- Apply factory/unslop/MOTION_NUMBERS.md:
  - one hero move per shot;
  - anticipation and follow-through;
  - ambient motion that never stops;
  - picture leads sound by 1 frame.
- Keep the narration audio and its timing byte-identical.

## F2. The small slanted red and teal labels at the top of the court shots look templated
Examples: "1심 벌금 5만 원", "먹어도 된다고 들었다", "모멸감·정신적 고통", "합의≠처벌 감경". They repeat the subtitle in a small, hard-to-read font, and this falls under the STYLE_VIDEO ban list (AI-looking UI). Remove them. If a number must stay on screen, put it inside the scene as a prop, such as a document, a screen or a sign, at a readable size.

## F3. Apply the new hook rules (factory/unslop/HOOKS.md) to the first 2 s only if they strengthen it without changing facts. Report what changed.

Re-render both, then update the sheets (0–3 s, 1 fps) and READY.txt. Do not upload. Stop for CTO review.
