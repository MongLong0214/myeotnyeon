# Build a 30–36 second anatomy short

Start the episode clock at topic assignment. Sonnet authors the title, captions, narration and dental label positions in episode.json. The kit owns the shots, character, transitions, projected landmarks, medical evidence, audio production and review. Stop after a passing movie, five numbered movies, two hours, or an identified blocking defect that the available parameters cannot repair.

## Start a topic

Use the production Python environment with its existing imaging, scientific and audio dependencies and the jsonschema package (4.18 or later). The Mac needs Blender with Cycles/Metal, ffmpeg, the authenticated Claude CLI, the installed DBCLS and Astra assets, MPFB with the original character assets, and the local Sohee and Whisper models. ANAT_EPISODES points to the installed episode archive. The default is episodes. The neck template pins the v3 source geometry and two comparison cameras by SHA-256. For neighbours it drives the skin, handset and anatomical landmarks from the same standing-phone capture in the opening and payoff. It trims the displayed cord at T1 in all three scenes. It reconstructs the same actor’s skin beneath the shirt for the closing shoulder projection and keeps the original armature and blink. The wisdom template builds its lower arch from the registered DBCLS surfaces.

```sh
export PY=.venv/bin/python
# Install once in this worktree if the production environment lacks jsonschema.
export PYTHONPATH="$PWD/.astra-work/kit-deps${PYTHONPATH:+:$PYTHONPATH}"
"$PY" -c 'import jsonschema' || uv pip install --python "$PY" --target "$PWD/.astra-work/kit-deps" 'jsonschema>=4.18,<5'
export ANAT_KIT="$(git rev-parse --show-toplevel)/bodyinside/anat_kit"
export ANAT_FRAME_CACHE="$PWD/.astra-work/frame-cache"
# Prime the shared template once before assigning a topic.
"$PY" "$ANAT_KIT/episode_template.py" neck_v3 "$PWD/.astra-work/neck-prime" --prime
"$PY" "$ANAT_KIT/solo.py" neck_v3 "$PWD/.astra-work/ear-position" '문자 입력 중 귀와 어깨는 어디에 보일까?'
```

Use a new episode directory each time. Choose wisdom for neighbouring molar-landmark topics. The two templates span posture comparison and orientation in the lower arch. A different mechanism needs its own supported claims and verified shots before it enters the catalog. The DBCLS archive has no third molar for an extraction simulation. The existing sectioning plan remains a development reference.

The solo command sends Sonnet the topic, frozen episode, source records and subsequent failures. It applies Sonnet's JSON response, runs the ordinary production commands and writes the resolved builder model, each preflight and submission result, wall time and stopping reason locally. A structural block belongs to the template maintainer. Every distinct movie counts towards the five-draft limit. A still score describes only the sampled pictures.

## Run the same stages individually

```sh
"$PY" "$ANAT_KIT/episode_template.py" wisdom "$PWD/episode"
# Edit episode/episode.json within the template's authored fields.
"$PY" "$ANAT_KIT/run.py" "$PWD/episode" pf01 --preflight
"$PY" "$ANAT_KIT/run.py" "$PWD/episode" draft01 --draft
```

Preflight validates the schema, attribution, claim bindings and source conditions. Opus grades the actual title, captions, speech and labels against the source records. Its clinical result includes separate decisions for the cited outcome, study conditions, time or causality, spoken qualification and graphics. Keep estimate qualifications in narration. In the texting comparison, show only the positions studied. The title and all beats must stay within the evidence. Keep source credits, disclaimer tags and kg figures out of the picture. Sohee pronounces C자 as 씨짜. Final-mix pronunciation flags go to the human listener.

The runner measures the camera, visible geometry and projected labels, renders the evidence frames and grades the composited stills. Inspect gates/preflight.json, the failing check files and the Opus findings. Any blocking class or P0 prevents a movie. Use a new preflight tag after editing. Previous drafts and their receipts remain local evidence.

Drafts use Cycles at 25% linear resolution with denoising and extra samples on translucent frames. The cache checks Blender and its build, the scene, external files, preset, sampling overrides, and individual PNG digests. It renders missing ranges per scene in serial batches, then rebuilds the split-view comparison and crossfades. Title, caption, label and narration edits reuse the same raw images. A changed scene conservatively invalidates its own ranges. Each receipt distinguishes reused and newly rendered frames and includes cache checks and compositing in the wall time. The cold cost belongs in shared template preparation only if actually paid before topic assignment. The 300-second draft limit still applies.

## Review and confirmation

The movie passes only with a passing submission receipt, the required Opus score and zero P0s. Opus reads six independent Fable picture-axis examples before those scores are combined. Its two original movie judgements, diagnostic floor, close-crop inspection, severity check, frame-pop detector and all machine checks still apply. The public references come from REFERENCES.txt. Keep the final audio and every numbered movie immutable.

After a failed movie, record its item boxes and claimed repairs in items.json and the revised frame windows in changes.json. Run fresh preflight, then draft02 --draft --prev draft01, continuing in sequence through draft05. Each movie gets a fresh tag. Run a matching --from stage only with verified render and assembly receipts.

After a passing draft and explicit owner confirmation, save playback.json with listener, phone, listened=true and the confirmed movie_sha256. Run final --final-fast --confirmed draftNN. The assembler preserves the approved audio packets. Audit the locked final once with Fable. Keep every artifact local. Threshold changes require an entry and reason in the threshold lock. The signed-off 11 cm floor belongs only to anat_neck_v3.

Use `episode_template.py wisdom NEW_FOLDER --prime` (or `neck_v3`) to prepare a shared template before topic assignment, using the same ANAT_FRAME_CACHE for production. The command records the preparation time, rendered ranges and noise result in prime.json. The final runner requests one independent Fable reading only after the confirmed full-resolution cut passes its other checks. gates/final_fable_audit.json binds the first outcome to the movie.

For calibration, run gates/anchors/catalog.py ARCHIVE OUTPUT to index all 43 reports and recover their crops. gates/replay_anchors.py ARCHIVE OUTPUT grades the pre-existing held-out split, blinded to historical answers. Run gates/match_anchors.py OUTPUT BASE_EVIDENCE after the replay completes. BASE_EVIDENCE is the original digest-matched blind review directory from the earlier calibration. The post-score matcher checks the combined P0 list against each numbered historical finding.

## Capture a finding and test a template fix

The runner records review items and failed gates in `factory/findings.jsonl`. Paste an owner or CEO remark with `improve.py capture EPISODE SOURCE LOCATION SEVERITY "remark"`. Use a stable episode ID across drafts. Add `--media PATH` for the reviewed cut or still, `--audio` for a sound defect, and `--directive` for an instruction that must stay under human control.

```sh
"$PY" "$ANAT_KIT/improve.py" nightly
"$PY" "$ANAT_KIT/promote.py" neck_v3 "$PWD/.astra-work/next-label-replay" --class-id label-pops-at-handoff
```

Use a new output directory for each promotion. Inspect its gates and the blind Opus vote in the promotion finding. A successful decision pins the new version on subsequent episodes. The two legacy masters use their original compositors. Wisdom draft 4 needs its frozen source bundle in `.astra-work/certified/081d063d4f03c28569d50d9b555e97db11be6301624ce3f4195bd2b03d1db0ef` or `ANAT_WISDOM_CERTIFIED_INPUTS`. It contains the original scripts, scenes, sidecars, audio and numbered band frames. Every later certified final uses its own submission, audit and render receipts.

Run `"$PY" "$ANAT_KIT/improve.py" install` to install this worktree’s LaunchAgent. Nightly runs restore missing fixture media from the local factory archive or extract the checksum-matched cut identified in the findings log. The installed `kr.verdict.anatomy-improve` LaunchAgent runs at 02:15 local time and writes `factory/IMPROVE_LOG.md`. It joins the anatomy channel's first two Pacific reporting days with published template and hook metadata. The channel's Studio collector can supply exact `first_48h` swipe-through, average view percentage and net subscriber conversion. Each value retains its source. A threshold edit requires the same reason in `thresholds.json` and the reason log, plus `_change.human_approved = true` and the recorder's `--human-approved` flag.

## Operative shorts

Run from the `bodyinside/` directory using the anatomy production Python environment (Pillow, NumPy, SciPy, PyYAML and SoundFile). The renderer uses the kit's nice-15 Blender launcher. FFmpeg, ffprobe and the authenticated Claude CLI must be on the path.

```sh
python anat_kit/templates/operative/certify.py --work .astra-work/operative
python anat_kit/templates/operative/trial.py crown_lengthening --work .astra-work/operative
python anat_kit/templates/operative/trial.py simple_extraction --work .astra-work/operative
```

Use the same work directory after an interruption. Each topic has its own recipe, geometry evidence, composited stills, numbered movies, comparator receipts and terminal Fable measurement. The cache is shared across both cases. `ANAT_SHARED_WORK` locates the source project. `ANAT_OPERATIVE_MUSIC` can point to the SHA-256-pinned surgery score. The workstation copy is in `.astra-work/operative/assets/music.wav`.

The surgery source, Alembic presets, recorded cues, licence audit and direct BodyParts3D meshes are pinned in `templates/operative/library.json`. Import a delivered endodontic edit using `catalog.py MOVIE OUTPUT.json`. Its steps enter as candidates and carry the source cut, contact proof and captions. Use `catalog.py MOVIE OUTPUT.json --step file_canal --clip FILE.mp4` to extract a registered step with its original synchronized sound.

For production use `trial.py CASE --recipe episode.json`. The input is an object with a `steps` array. Each row has `step`, `tool`, `target`, `caption`, `pmid` and `thumbnail`. The lookup returns a verified movie or reports that the case has no certified default. The timed trial command can measure candidates while certification is open. The terminal audit alone does not authorize publication.
