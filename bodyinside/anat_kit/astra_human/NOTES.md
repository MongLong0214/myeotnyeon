# Body Inside character handoff

Open `human_final.blend` and play frames **1–126 at 30 fps**. To move the cast into the episode, append the collection **Human | character** and transform **HumanRoot**. It contains the rig, skinned surfaces, hair, spectacles and animated phone. The camera, backdrop and lights live in **Studio | profile proofs**. All ten scene images are packed.

| Editorial range | Performance | Proof |
|---|---|---|
| 1–60 | The worker reads and taps the phone. The slump completes within the owner’s revised two-second opening. | [Mid-slump, frame 31](proof_open.png) |
| 61–85 | The payoff opens on a more pronounced upper-back curve and forward head. At frame 85 the near ear is **13.59 cm** anterior to the shoulder marker. | [Peak, frame 85](proof_payoff.png) |
| 85–115 | The worker lifts his gaze and straightens over 30 frame intervals. The ear finishes within **0.1 mm** of the shoulder’s anterior–posterior coordinate. | [Neutral, frame 115](proof_neutral.png) |
| 116–126 | Upright settle with the handset still in the hands. | |

The rig’s NLA strips have corresponding handset strips. Both actions are baked on every frame. The opening source action retains frames 61–108 as a moving hold for a 3.6-second cut. Its first 60 frames are the editorial opening. For the longer cut, move both payoff strips to frame 109, extend both opening strips through frame 108 at unit speed, and set the scene end to 174.

## Character and picture

The actor has a textured complexion, separate eye globes, brows, blinking lids and lashes, and fine wire spectacles. A short dark crop combines textured roots with 25,745 tapered curves. The cotton tee has a fitted collar, turned hems and diagonal folds over denim trousers. The left hand carries the handset. The right index follows the screen while the other three fingers flex and the thumb relaxes into the palm. The finger contacts are authored over the captured performance.

The fixed camera sits about 19° forward of a true profile to keep the near eye, phone display and neck silhouette visible together. Each proof is a 1080 × 880 RGB PNG rendered in Cycles at 32 samples with Open Image Denoise. The quarter-size draft check used four samples and the same lights. Skin, shirt and background read cleanly at 270 × 220. Fine fiber detail softens at that size.

## Skeleton alignment

`anchors.json` has one record per editorial frame and a separate `opening_tail_frames` array for the 48 optional source frames. Lengths are metres. Matrices are row-major and operate on column vectors. The actor faces world −Y, with +Z up.

- `head_world` and `neck_world` are the evaluated **HumanRig** pose-bone world matrices for `head` and `neck_01`.
- `bp3d_skull_to_world` maps the neutral episode skull into the posed human. It includes the fitted scale. `head_center` tracks the center of the registered cranial bounding box. `skull_orientation_wxyz` gives the rotation as a quaternion.
- `cervical_centers` gives C1–C7 positions. `bp3d_vertebra_to_world` gives an absolute map for each neutral episode vertebra. Apply each map to its corresponding part in the reference pose. For an object with its own origin, compose the map with that object’s neutral world matrix.
- The reference frame follows the episode importer. Convert raw BodyParts3D OBJ millimetres to metres and add `(0, 0.089, 0.072)` before applying these maps. The episode’s prepared meshes already use that frame. If **HumanRoot** is moved after import, premultiply by its placement transform.

The fit uses the crown, occiput, chin, paired eye centers and paired ear-canal estimates. Across the full performance, including the tail, the maximum landmark residual was **21.51 mm** and the RMS residual was **15.44 mm**. A separate rest-pose check sampled **6,098** cranial-vault vertices against the skin and found zero outward displacement at those samples. The export includes the source landmarks, soft-tissue offsets and per-frame errors.

## Limits

The ear and shoulder measurements use a near-side tragus point and the T-shirt surface over the acromion. Ear-canal estimates account for the largest registration residual. C1–C7 are virtual joints along a smooth fitted curve. Their motion is suitable for aligning the episode illustration, with limited accuracy for individual disc motion. Cloth folds and hair are bound to the performance. The handset contact is tuned for the supplied camera and actions.

## Rebuild

The build uses Blender 5.2, MPFB 2.0.18, the installed MakeHuman system assets, the two project FBXs and the local BodyParts3D 4.0 reference archive. `MPFB_ASSETS` and `BP3D_REFERENCE` can point to alternate locations. From this directory on the production Mac, the following commands keep MPFB runtime files in local scratch space.

```sh
blender_bin=/Applications/Blender.app/Contents/MacOS/Blender
mpfb_extension="$HOME/Library/Application Support/Blender/5.2/extensions/user_default/mpfb"
mkdir -p .build/runtime/extensions/user_default .build/tmp
cp -R "$mpfb_extension" .build/runtime/extensions/user_default/
export BLENDER_USER_RESOURCES="$PWD/.build/runtime"
export TMPDIR="$PWD/.build/tmp"
"$blender_bin" -b --factory-startup --python-exit-code 1 -P make_human.py
"$blender_bin" -b --factory-startup --python-exit-code 1 -P render_proofs.py
"$blender_bin" -b --factory-startup --python-exit-code 1 -P render_proofs.py -- --draft
```

This run used a temporary workspace copy of Blender 5.2.3 with the Metal availability check disabled. The installed binary crashed during GPU detection in the restricted environment. Cycles rendered the proofs on CPU. The saved blend and Python scripts use standard Blender data and APIs.
