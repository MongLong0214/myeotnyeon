# Body Inside

Body Inside makes Korean-language vertical 3D anatomy Shorts for general
YouTube viewers. Each episode uses an original illustration to show something
viewers normally cannot see inside the body. The production target is Opus ≥9.5,
zero P0 findings, within five numbered drafts.

This directory holds the publishable sources, templates, gates, episode specs,
the asset manifest and the fetch script. Media, scenes, meshes and private
evidence are not in Git. [assets/MANIFEST.json](assets/MANIFEST.json) pins each
one by path, SHA-256, size and licence, with a public source where one exists.
See [Clean-checkout reproducibility](#clean-checkout-reproducibility) for what
a fresh clone can and cannot run.

## Owner and CEO rules

- Use Korean captions and no narration. Start with verified real recordings.
  Fill sound gaps with Earshot. Keep BGM continuous through the loop and duck it
  by at most 6 dB.
- Open on a striking image or action at frame 0, with the shock in the first
  1.5 seconds. Cut idle holds and empty transitions. Each answered mini-hook
  sets up the next beat. End immediately after payoff with a matched picture
  and sound join back to the opening. Omit comment-bait and share-bait.
- Scope facts to cited evidence and one illustrated example. Label compressed
  time where relevant. Establish the clinical or 3D context in the opening
  caption. Keep disclaimer chips, unsupported numbers and credits out of the
  image. Put sources and attribution in the description. Use DBCLS BodyParts3D
  4.0 for new anatomy and original geometry for the rest.
- Pick one impactful, anatomy-centered thumbnail with little to no visible
  blood. Prefer a clean, legible cutaway or the tool-to-tissue payoff.
- Set animation, simulation, render and encoding to 30 fps from the start.
  Review low resolution first. Obtain owner confirmation of the passing draft
  before rendering 1080×1920.
- Obtain explicit permission for the private upload, then separate permission
  for the exact scheduled slot. Verify the video ID and visibility after
  each operation. Never delete a video. Escalate any new or disputed medical
  claim, unclear rights and every publishing decision to the owner or CEO.

## Choose a topic

Read the numbered [queue](research/viral_refs/VIRAL_REFS.md#top-5-topics-for-body-inside).
Topic 1 has the [root canal source](episodes/anat_rootcanal/). Topic 3 maps to
`crown_lengthening` in the [operative step library](anat_kit/templates/operative/library.json).
Topics 2, 4 and 5 need their own source-scoped case and geometry. For a new case,
reuse appropriate registered steps from the library, document the scope and
sources, and have the template maintainer verify the new geometry and shots.
Use other channels' videos as editorial references for original work.

[Operative templates](anat_kit/templates/operative/) include the data-only
recipes and the [comparison evidence](anat_kit/templates/operative/evidence/).
A case is certified only when the existing factory accepts its matching
`trial.py CASE --work WORK --recipe EPISODE.json` lookup and its output has
`"used_default": false`. With `true`, the lookup returned the stored certified
cut, not your recipe. Topic 3 has a
recorded Sonnet recipe and prior trials with certification still open.
[Legacy templates](anat_kit/templates/) and the [kit runbook](anat_kit/RUNBOOK.md)
retain the historical wisdom and neck production paths, including their earlier
voice rules. Follow this README for new Body Inside episodes.

## Set up and run topic #3 preflight

Run every command from this `bodyinside/` directory. Scripts and legacy paths
are relative to it. The workstation needs `uv`, Blender, FFmpeg, ffprobe and,
for live authoring and review, an authenticated Claude CLI. Set `BLENDER` to
its executable path if Blender is installed outside the standard macOS
application location. Use a workstation shell that can launch background
Blender. On macOS a restricted shell can fail at Blender startup even when
Cycles uses the CPU. Fresh renders queue on the shared Blender lock.

The operative and replay inputs include private production media. The
preflight runs only after you restore them from the owner asset backup with
`--mirror`. A clean clone without the backup stops at the asset check (재현 불가).

```sh
uv venv --allow-existing --python 3.12 .bodyinside-venv
uv pip install --python .bodyinside-venv/bin/python numpy Pillow scipy PyYAML soundfile jsonschema opencv-python-headless
export PY="$PWD/.bodyinside-venv/bin/python" ANAT_PYTHON="$PWD/.bodyinside-venv/bin/python"
export ANAT_EPISODES="$PWD/episodes" ANAT_SHARED_KIT="$PWD/anat_kit"
export ANAT_BLENDER_DEVICE=METAL  # Match the recorded topic #3 draft plates.
MIRROR=/path/to/asset-backup      # Owner asset backup with repository-relative paths.
scripts/fetch_assets.sh --group operative --mirror "$MIRROR"
scripts/fetch_assets.sh --group topic3-replay --mirror "$MIRROR"
CASE=crown_lengthening
WORK="${BODYINSIDE_WORK:-$PWD/.bodyinside/operative}"
TAG=draft1
mkdir -p "$WORK/cache"
cp -R .astra-work/operative/replay-cache/. "$WORK/cache/"  # overwrite: only verified plates
"$PY" anat_kit/templates/operative/stage.py preflight "$CASE" --work "$WORK" --tag "$TAG" --replay-author
# For a requested low-res draft, run this in the same shell as preflight.
# "$PY" anat_kit/templates/operative/stage.py draft "$CASE" --work "$WORK" --tag "$TAG"
```

The fetch script exits non-zero and names every asset it could not restore.
The recipe, claims and licence receipt is in
`$WORK/$CASE/gates/recipe_preflight.json`. The stills are 270×480.
The preflight passes when `$WORK/$CASE/gates/draft1_preflight.json` contains
`"pass_stills": true` and an empty `errors` array. For a **preflight-only**
assignment, report that receipt. If the assignment also asks for a low-res
draft, use the same `WORK` and stop at the draft MP4. The replay uses the
recorded recipe and verified plates and reruns preflight and compositing. For a fresh render, skip the replay restore and
copy, omit `--replay-author`, and use a new `WORK`. Use `CPU` or `METAL` for Cycles. The asset script also accepts
repo-relative paths and `--verify`.
Keep review references internal and use the per-edition sources and audits. See [manifest](assets/MANIFEST.json) and
[asset rights](anat_kit/ASSETS_RIGHTS.md).

## Draft, gates, comparison, HQ and post

For an approved production assignment continue in order with the same variables.
See [rubric](anat_kit/rubric.md), [defects](anat_kit/defects.yaml) and
[thresholds](anat_kit/gates/thresholds.json). If a stage fails, inspect its
receipts, fix the defect and use a new numbered draft. Keep thresholds and
prior cuts intact. `compare` and `post` also need the six checksum-pinned anchor videos
restored below. A development reference can give a comparative diagnosis
while certification is open. The HQ command requires a certified reference
and the passing draft's owner-confirmed SHA-256. The template maintainer can
run `"$PY" anat_kit/templates/operative/certify.py --work "$WORK" --section-detail`
to audit a repair. First run the review restores in the block below and
`scripts/fetch_assets.sh episodes/anat_wisdom/astra_surgery/draft5/renders --mirror "$MIRROR"`.
Start a new case work directory to use a different reference.

```sh
STAGE=anat_kit/templates/operative/stage.py
scripts/fetch_assets.sh --group review --mirror "$MIRROR"
# Review anchors and the four adjacent-tooth meshes the audit hashes:
scripts/fetch_assets.sh episodes/anat_neck/draft21.mp4 episodes/anat_neck/draft23_0024_fable95.mp4 \
  episodes/anat_neck_v3/draft4.mp4 episodes/anat_wisdom/draft10.mp4 episodes/anat_wisdom/draft18.mp4 \
  episodes/anat_wisdom/draft23.mp4 --mirror "$MIRROR"
scripts/fetch_assets.sh research/anatomy3d/bodyparts3d_4.0/obj/isa_BP3D_4.0_obj_99/FJ1253.obj \
  research/anatomy3d/bodyparts3d_4.0/obj/isa_BP3D_4.0_obj_99/FJ1254.obj \
  research/anatomy3d/bodyparts3d_4.0/obj/isa_BP3D_4.0_obj_99/FJ1256.obj \
  research/anatomy3d/bodyparts3d_4.0/obj/isa_BP3D_4.0_obj_99/FJ1257.obj
"$PY" "$STAGE" draft   "$CASE" --work "$WORK" --tag "$TAG"
"$PY" "$STAGE" gates   "$CASE" --work "$WORK" --tag "$TAG"
"$PY" "$STAGE" compare "$CASE" --work "$WORK" --tag "$TAG"
# Set APPROVED_SHA256 to the draft digest explicitly confirmed by the owner.
"$PY" "$STAGE" hq "$CASE" --work "$WORK" --tag "$TAG" --confirmed "$APPROVED_SHA256"
"$PY" "$STAGE" post "$CASE" --work "$WORK" --tag "$TAG"
```

For `seam_ok: false`, use the existing phase-lock repair in the next tag
(`gates/draft2_settings.json` with `{"_audio":{"phase_lock":true}}`, for example).

Post checks the encoded loop and the final Opus review and refreshes the
claim, provenance and licence receipts. Inspect the rendered captions,
last-to-first picture and sound, thumbnail and final description before
requesting permission to upload. Each episode's `SOURCES.md` and
`description.txt` record its editorial and factual scope.

## Private upload, schedule and readback

Run these in order after the separate authorizations above. Use the authenticated
Body Inside Aside profile and read-only Body Inside OAuth in Keychain. Copy
[the registry example](factory/channels/registry.example.json) to
`factory/channels/registry.json` and fill in the real Body Inside channel ID,
name and handle. Git ignores that file. Set `ASIDE_BODYINSIDE_PROFILE` to the
local Aside profile ID of the Body Inside identity. Start the uploader REPL
once per session with the command below, or reuse the running session.
`VIDEO_ID` is the ID returned by the private upload. Set `PUBLISH_AT` to the
owner-approved future ISO 8601 time with the `+09:00` offset. The registry
records the usual 09:00 KST slot.

```sh
uv pip install --python "$PY" google-api-python-client google-auth-oauthlib
REPL=factory/ops/uploader/repl
"$REPL/repl_start.sh" > "$REPL/session_dir"
"$PY" scripts/bodyinside_publish.py private "$WORK/$CASE" "${TAG}_hq"
"$PY" scripts/bodyinside_publish.py readback "$VIDEO_ID"
"$PY" scripts/bodyinside_publish.py schedule "$VIDEO_ID" "$PUBLISH_AT"
"$PY" scripts/bodyinside_publish.py readback "$VIDEO_ID" --publish-at "$PUBLISH_AT"
```

If an operation times out, read back the existing ID or inspect Studio before
retrying. [Data API readback](https://developers.google.com/youtube/data/reference/rest/v3/videos)
checks visibility, licence and the scheduled time. The [channel queue](factory/ops/queue.py)
reads the same registry. Set `FACTORY_BUZZ_ROOM` and `FACTORY_BUZZ_IDENTITY`
locally to enable `queue.py gaps --notify`. The shared-factory helpers it and
the uploader mention (`channel/analytics/reauth.sh`, `langcheck.py`,
`restart_all.sh`) are not in this tree; `bodyinside_publish.py` runs `send.sh`
with recovery off. Analytics pulls and the publishing ledger hold
account data and stay out of this tree.

## Clean-checkout reproducibility

A fresh clone has every source, template, gate, spec and receipt listed here.
It does not have the media. Of the manifest's 105,451 entries, 2,236 have a
public download: 2,234 BodyParts3D 4.0 OBJ files (CC BY 4.0, extracted from the
DBCLS archive after its hash check), that archive itself, and the Blender
Human Base Meshes bundle (CC0). In the `operative` group, 17 of 54 inputs
download. The DBCLS licence and README page snapshots stay on the mirror
(NBDC website terms); the BodyParts3D CC BY 4.0 notice is quoted in
[asset rights](anat_kit/ASSETS_RIGHTS.md). Everything else is marked `"availability": "local-mirror-only"` and
needs the owner asset backup.

These steps are **재현 불가** (not reproducible) from a clean clone:

- **Topic #3 preflight and low-res draft.** They need the private operative
  inputs: the archived surgery scene `.blend`, the draft3 `.abc` meshes, the
  mucosal texture, the archived `final_surgery_v3.mp4`, the Earshot score
  `music.wav`, and the 467 recorded replay files. They also need two PubMed
  clinical figures (NOASSERTION, not redistributable). The OFL fonts, CC0
  textures and 16 CC0 Freesound recordings can be obtained from their listed
  public sources, but the script cannot download them.
- **Draft, gates, comparison, HQ and post.** These need the topic #3 inputs,
  the archived comparison reference and its audit, and the internal EBS review
  reference sheet (NOASSERTION).
- **Private upload, schedule and readback.** These need the owner's Keychain
  OAuth, Aside profile and local channel registry.
- **Legacy neck, wisdom and root canal builds.** These need `.blend` scenes,
  Z-Anatomy-derived meshes (CC BY-SA), Mixamo and Rokoko mocap, MPFB assets,
  render outputs and the legacy TTS environment. None of these are in this tree.
  Several legacy scripts also assume Blender at `/Applications/Blender.app`,
  fixed process IDs or render logs that are not kept, and the root canal
  audio mix needs the cached Freesound licence pages, which stay local.
- **Review-anchor calibration and the improvement loop.** `anat_kit/gates/anchors`,
  `calibrate.py` and `improve.py` read internal review reports and a findings
  log that are not published.

See [REPO_REPORT.md](REPO_REPORT.md) for what this tree contains and what was withheld.
