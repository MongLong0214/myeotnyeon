# anat_neck_long — 거북목일 때 목 안에서 생기는 일 (16:9, 3-minute cut)

The owner's instruction was "6분 너무길어 3분짜리로 만들어", so this replaces the 6:14 plan.

**Format:** 1920x1080, 30 fps, **2:57.4 (177.4 s)**, 6 chapters of about 29 s each. The script, captions, labels and shot list are in `episode_long.json`. Narration runs at 6.4 syll/s, with 0.2 s between beats and 0.15 s between sentences. Sources are in `SOURCES_long.md`.

**Chapter unit.** Each chapter runs person → inside → mechanism → consequence and is cut to 9:16 by re-rendering its beats with a vertical camera in the neck short layout. Shot codes:
- **P**: the person (Astra human).
- **X**: inside, with the neck rig driven by the person's pose.
- **PX**: a same-size dissolve between the person and the skeleton.

There is no twin compositor in this cut. The person appears at least every 10 s. The event list never leaves more than 2 s without a change.

| # | Chapter | Time | Reuse | New (all small) |
|---|---|---|---|---|
| 1 | 폰 보는 사람 (hook) | 0:00.0–0:29.2 | Astra f1–108, neck dissolve f66–84, curve f86–146 | 16:9 cameras, silhouette outline and title card (2D) |
| 2 | 머리 무게와 부담 (kg spoken only) | 0:29.2–0:58.3 | neck load beat f84–299 (variant B), FKChain 15/30/60 | head sphere outline and centre-of-mass dot (2D) |
| 3 | 머리를 붙잡는 근육 | 0:58.3–1:27.1 | BP3D neck muscles incl. longus colli, muscle beat f726–812 | lever bracket (2D), shortening keys |
| 4 | 문자 입력 중 달라지는 목뼈 마디 각도 (some segments, while texting only; no reversal) | 1:27.1–1:58.5 | FKChain incl. turtle pose, curve line | angle arcs without numbers (2D), radiograph-look fade |
| 5 | 디스크와 신경뿌리 (hedged, separate anatomy, not linked to ch4) | 1:58.5–2:26.5 | Disc/Nuc/Herniation/cord/roots, disc beat f580–712, legend | fissure material, foramen outline (2D), hand-shake key on the rig |
| 6 | 10초 확인과 습관 + 엔딩 | 2:26.5–2:57.4 | Astra payoff f61–85 and straighten f85–115, plumb/gap, Neck Stretching mocap, neck ending f940–1079 | **chin_tuck posture** + head key on the person, phone-at-eye-level arm key, timer ring and photo card (2D) |

**Dropped from the 6-minute plan:**
- the suboccipitals, arm and hand bones and arm nerve;
- the wall, doorway and band props and the BP3D chest and back muscles;
- the three instanced spines;
- the twin compositor;
- the headache chapter.

No new BodyParts3D meshes, props or Mixamo downloads are needed. The new work is two rig keys (chin_tuck, phone up), one keyed hand shake, one material crack and the 2D graphic kinds (timer, photo card, numberless angle arc, sphere outline, lever bracket).

**Render estimate.** The per-frame costs come from the neck measurements: the draft was 0.44 s/frame (8 min for 1080 f at 25 %) and final-fast was 2.22 s/frame (40 min for 36 s on a 1080x880 band). For 1920x1080 I assumed ×1.0–1.4 on the draft and ×1.6–2.2 on the final; these multipliers are assumed, not measured.

| Ch | Frames | Draft (min) | Final-fast (min) | 9:16 short re-render (min) |
|---|---|---|---|---|
| 1 | 877 | 6–9 | 52–71 | 32 |
| 2 | 872 | 6–9 | 52–71 | 32 |
| 3 | 864 | 6–9 | 51–70 | 32 |
| 4 | 942 | 7–10 | 56–77 | 35 |
| 5 | 841 | 6–9 | 50–68 | 31 |
| 6 | 925 | 7–9 | 55–75 | 34 |
| **Total** | 5321 | **38–55** | **316–432 (5.3–7.2 h)** | 196 (3.3 h, if all six ship) |

Before committing, measure 30 frames of one P shot (hair and cloth) and one X shot at final-fast (RUNBOOK F9).

**Medical scope.** Ch4 shows angle changes in some cervical segments (mostly upper) observed while texting (Trior Simonovich 2025), plus upper-cervical extension in forward-head posture; no long-term change is implied and "마디마다 꺾인다/꺾이는" is banned (CEO ruling). Ch4 hands over to ch5 as separate anatomy ("디스크를 따로 볼게요"), so the texting angles are never linked to nerve compression. The reversed-curve claim (U1) stays out, so the short's line "C자가 펴지다가 거꾸로 휠 수도" is not reused. Ch5 ties the bulge to a worn or injured disc, never to the posture. Hand tingling is presented as root-compression anatomy, hedged.

**Open before the build.**
- The schema caps duration at 60 s and has no `chapters`/`shot`/`events` keys, so it needs a long-form schema version.
- labels2d needs the 2D kinds listed above.
- The per-beat gate declarations are written for each chapter build.
