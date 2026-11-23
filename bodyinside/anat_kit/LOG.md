# anat_kit LOG

Version tags are written here when assets, tools and rubric are frozen (see RUNBOOK "Proof rules"). Same-version evidence is never pooled across tags.

## Current production directives
Use the DBCLS CC BY 4.0 archive for new anatomy. Keep attribution in description.txt. The person opens for two seconds before the dissolve. Use Sohee and pronounce C자 as 씨짜. Keep model kg values and their estimate qualifier in narration only. Render drafts at low resolution and wait for the owner's confirmation before a full-resolution render. The historical entries below retain earlier experiments and their outcomes.

## Time accounting for episode 2 (anat_neck) — development case
Wall-clock timestamps from file mtimes (local time, 2026-11-21). Approximate; the shared build and the episode build are logged separately on purpose.

| What | Kind | Time |
|---|---|---|
| Reading RUNBOOK/kit, fact research (agent, parallel) | setup | ~0:25 |
| Region pack "neck": base.py (Z-Anatomy import), kit_spine.py (materials, smooth_solid, cut_half, cortical_rim, disc_between, FKChain, Posture, skin_to_bodies, tint_material), solids.py (stage B, 25-70 s to run) | SHARED ASSET PACK | ~1:00 (09:29 -> ~10:30, includes four debugging loops: O(n^2) probe loop, material-slot bug, disc boolean failing, stray face plates) |
| Render tools: run.py, labelpos.py, labels2d.py, schema, fable_gate.py, rubric.md, flash gate composite fix | SHARED TOOLS | ~0:35 |
| Episode build: episode.json, build.py (stage C), SOURCES.md, draft01 | EPISODE | ~0:30 so far |
| Draft render (990 frames, half res, 16 spp) | measured | 9m40s (draft01). Target <= 5 min: see "render presets" in RUNBOOK |

Rule for the proof runs: asset-pack and tool time is logged here and NOT counted against the 2 h; episode-specific prep before the brief is forbidden.

## Findings that became code (episode 2)
- Stray geometry: leftover face plates (ethmoid, vomer, concha, lacrimal, nasal, palatine) survived the skull join and rendered as grey scraps. solids.py now deletes every mesh outside a KEEP list; the per-object hide test (hide_test.py) found them.
- Newly created objects have a stale identity matrix_world: FKChain._parent now updates the view layer first (anchors projected to y = 5.2 before the fix).
- video_gates flash gate converted straight-alpha RGBA to luma without compositing, so a layer fading in from alpha 0 looked like a 40-level flash. The gate now composites on the dark background first (measurement fix, thresholds unchanged).
- run.py waited for any process whose command line contained the Blender path, including other agents' wait loops; it now matches the executable name (`pgrep -x Blender`).

## Render speed measurements (neck, 990 frames, 1080x800 band, Apple Metal, machine shared with other renders: load average 15-18)
| Setting | Result |
|---|---|
| --draft (16 spp, 50 %, OIDN) full run | 9m40s (draft01, machine quiet), 13m (draft02), ~15m (draft03, shared load) = 0.55-0.9 s/frame |
| 30 frames, spp 1 / 10 % | 8.6 s total (~0.22 s/frame incl. ~2 s start): the scene-evaluation floor |
| 30 frames, spp 16 / 8 / 4 at 50 % | 16.7 s / 16.0 s / 18.6 s (noise from shared load: spp barely matters) |
| hide Skull / Vertebrae / cord+discs (spp 1) | 6.9 / 7.1 / 7.6 s vs 7.4 s unhidden: geometry share is small |
Reading: the draft is dominated by per-frame overhead (deforming meshes, BVH rebuild, denoise), not by samples, and by contention with other jobs. The <= 5 min draft target is NOT met (best 9m40s). Untested levers: lower voxel density for drafts (skull 0.3M verts), render every 2nd frame for pose checks, EEVEE for cut-face shots, draft at 30 % with upscale. `--final-fast` exists in rset.py (24 spp, OIDN, capped bounces, 100 %) but is UNVALIDATED: no final has been rendered yet.

## Asset-pack switch (2026-11-21)
Rebuild from Z-Anatomy to BodyParts3D 4.0 (CEO rights decision): base_bp3d.py + solids.py changes + own cord/roots: about 1 h wall clock including three debugging loops (OBJ axis import, unwelded triangles -> voxel remesh returned empty, disc probe start offset). Logged as SHARED ASSET PACK time.

## Threshold reason log
- 2026-11-21 `human_reads_as_human` ear offset in the payoff beat: 4-10 cm -> 12-15 cm (checks.human_reads_as_human gap=(0.12, 0.15)). Reason: owner instruction, "기괴한 자세" (a striking, almost grotesque severe forward-head posture); relayed by the coordinator after proof_payoff2 was approved. Anatomically possible (extreme forward head posture); the neutral ending gap limit (<= 3 cm) is unchanged. Fixture human-figure-reads-as-human still fails (skull below shoulder, ear 19 cm).
- 2026-11-21 `establishing_person` min frames: 90 -> 60. Reason: owner instruction (the opening person shot is 2 s, not 3 s); the 24-frame dissolve follows, so opening beat = 84 frames (2.8 s). Fixture establishing-shot-at-least-1-5-s (9 frames) still fails.
- 2026-11-21 20:0x on-screen kg numbers and the model-estimate chip removed (final uses variant B). Reason: owner instruction "컴퓨터 모델추정 이거빼"; the CEO condition (muted viewer must not read the kg values as measured) is met by having no kg numbers on screen; the narration keeps "컴퓨터 모델로는 ... 추정돼요". Gate no_kg_on_screen; defects.yaml model-estimate-chip-or-kg-on-screen. No 3D frame changes.
- 2026-11-21 21:3x narration: the sentence "모두에게 생기는 건 아니에요" removed from beat 3 (episode.json, episode_variantB.json). Reason: owner instruction (cut it). Rule from now on (lexicon/rubric note): no blanket "not everyone gets this" disclaimers; the hedge stays in the verbs ("수도 있어요", "휠 수 있다", "추정돼요"). facts_gate still forbids inevitability wording.
- 2026-11-21 narration lexicon (review 16 item 8): 하중 -> 하-중, 눌린 -> 눌-린 (layout/narration.py LEXICON; the recogniser heard 화중 / 물린). Tried first respelling per coordinator; result recorded below after the WER re-run.
- 2026-11-22 lexicon (review 18): '신경 쪽으로' -> '신경, 쪽으로' (heard 신경적으로), '휠 수도' -> '휠 쑤도' (heard 휘); 하-중 and 눌-린 confirmed working (ASR heard 하중, 눌린 correctly).

## 2026-11-22 anat_neck_v3: human_reads_as_human gap floor 12 -> 11 cm, this episode only
Episode override in episodes/anat_neck_v3/thresholds.json (CEO ruling: one posture as in the opening, no worsening; person ear 11.1-11.2 cm). Global default (12-15 cm) unchanged. Also: visibility_windows nf from the dump (was 990), human_gate frames from the episode, assemble.py peak-limits before loudnorm, xfade 'ease: linear' option, NLA strip scale fix in kit_astra.py.
- Upload master v3 records the CEO's exact rationale for the `anat_neck_v3`-only 11.0 cm ear-offset floor in `thresholds.json`.
