# Character assets and rights

The human, clothing, hair underlay and face textures come from the MakeHuman core mesh and system assets installed with MPFB 2.0.18. The core graphics assets are CC0 1.0. The local system-pack manifest identifies their author as `makehuman_system` and lists the individual assets as CC0. The mesh and material headers also record the September 2020 CC0 release by Data Collection AB, Joel Palmius and Jonas Hauquier. [MakeHuman Community asset licence](https://static.makehumancommunity.org/about/license.html) · [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)

| Included asset | Local source relative to the installed extension or system asset pack | Use and licence |
|---|---|---|
| HM08 human | Extension `data/3dobjs/base.obj` and `data/targets/` | Body, face, hands, macro body shape and fitted facial details. CC0. |
| Facial morphs | `data/targets/nose/`, `chin/`, `asym/`, `eyes/` and `expression/units/asian/` | Nose bridge, chin, cheek and brow asymmetry, lower lids, mouth compression and blink. The build lists the target names and weights. CC0. |
| Game-engine armature | `data/rigs/standard/rig.game_engine.json` and `weights.game_engine.json` | Armature and skin weights, fitted to the cast before animation. CC0. |
| Skin | `skins/young_asian_male/young_lightskinned_male_diffuse3.png` | Face, lips, hands and body albedo. Custom tint, pore bump and subsurface settings. CC0 source. |
| Hair | `hair/short01/short01.mhclo`, its OBJ and `short01_diffuse.png` | Fitted alpha-textured underlay. Individually tapered fibers are generated along the strand directions in the source texture. CC0 source. |
| Eyes | `eyes/high-poly/high-poly.mhclo`, its OBJ and `eyes/materials/brown_eye.png` | Eye globes, sclera and brown iris. Gaze and corneal highlight are authored in the build. CC0 source. |
| Brows and lashes | `eyebrows/eyebrow012/` and `eyelashes/eyelashes01/` | Fitted MHCLO/OBJ geometry and matching PNG opacity/color textures. Lash movement follows the eyelid morph. CC0. |
| T-shirt and jeans | `clothes/male_casualsuit06/` | MHCLO/OBJ set and diffuse, AO and tangent-normal PNGs. Adapted jersey dye, folds, neck binding and hems. CC0 source. |
| Sneakers | `clothes/shoes05/` | Fitted MHCLO/OBJ canvas shoes, weight definition and `shoes05_diffuse.png`. CC0. |

## Motion

Both captures came from the project’s licensed Adobe Mixamo downloads. Adobe permits royalty-free use in commercial films. The blend contains the character-specific baked performance and handset actions. The FBXs remain in the project’s mocap directory. [Adobe Mixamo FAQ](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html) · [Project download and rights record](../assets/mocap/USAGE.md)

| Local source | Contribution | Original FBX SHA-256 |
|---|---|---|
| `../assets/mocap/Texting While Standing.fbx` | Body sway, torso rotation, elbow directions, wrist trajectory and supporting-thumb motion. | `e26ed165cd1a3f72fe07a09cb4445ff187bc92b71ce5f86d31b9fdb081698a2f` |
| `../assets/mocap/Looking Down.fbx` | Captured neck and head rotation blended into the authored posture arc. | `d5abdbe1ebea97e2f1e54831ba38f17007c1a1917aa4ebae2326534750b86dab` |

## Skeleton calibration reference

BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International. The build reads local Release 4.0 coordinates for the calibration in `anchors.json`. It measures the cranium, mandible, paired sclerae and cervical vertebrae, rescales the measurements to the character, and computes posed transforms. The character blend and proofs contain the human surface and accessories. The reference anatomy is supplied by the episode at integration. [BodyParts3D archive licence](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html) · [Release 4.0 archive](https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip)

## Original work

The phone enclosure, rear camera, messenger artwork, spectacles, generated strand layer, cloth finishing, contact poses, lighting, camera and backdrop were created in `make_human.py` for this production. The interface artwork uses hand-drawn geometric glyphs. These elements have no external asset or font dependency.
