# anat_wisdom — sources, licences, fact check

## 3D assets
| Asset | Source | Licence | Use |
|---|---|---|---|
| Skull, mandible, teeth, cervical vertebrae, inferior alveolar nerve, gingiva, head-skin regions | Z-Anatomy FBX exports, github.com/LluisV/Z-Anatomy (PC-Version/Resources/Models/FBX), local copy in work/research/anatomy3d/zanatomy/ | CC BY-SA 4.0 (Z-Anatomy), derived from BodyParts3D, CC BY-SA 2.1 JP | Base anatomy |
| Third molar | **Our modification:** a copy of Z-Anatomy "Lower first molar tooth.l", scaled 0.88 and laid horizontal (Z-Anatomy has no third molar) | CC BY-SA (derivative) | Impacted tooth |
| Inferior alveolar nerve path | **Our modification:** the canal is lowered locally so it runs about 1.4–3.4 mm under the roots (illustrative, not patient data) | CC BY-SA (derivative) | Nerve shot |
| Studio HDRI "Studio Small 09" | polyhaven.com, by Sergej Majboroda | CC0 | Reflection light only |
| Instruments (handpiece/bur, elevator, scalpel, needle) | Modelled procedurally in build.py | Ours | Not in the 10 s cut |
| Fonts: Black Han Sans, Pretendard Bold | work/branding/_src/public/fonts | OFL 1.1 | Title and captions |
| SFX (drill whine, crack, clink, pulses, room tone) | Procedural numpy, sfx.py | Ours | Audio |

**Licence implications (CC BY-SA):** every upload description must carry this attribution.
"3D anatomy: Z-Anatomy (CC BY-SA 4.0, z-anatomy.com) based on BodyParts3D © The Database Center for Life Science (CC BY-SA 2.1 JP); modified."

ShareAlike covers the 3D model data and derived meshes, so if we redistribute the .blend or meshes, they go out under CC BY-SA. The rendered video is an adaptation, so the safe reading is to license it CC BY-SA as well, or at minimum to attribute it and not add restrictive terms. That is compatible with YouTube monetisation, but anyone may re-share the video under the same licence. Hunyuan3D was not used: its licence excludes South Korea.

## Giraffe (neck test)
No open giraffe skeleton under a usable licence was confirmed. The Sketchfab Zabulu skeleton is CC BY-NC (non-commercial), and the Artec giraffe is a skull only. The neck test therefore stayed human-only.

## Fact check (episode claims)
| Claim on screen | Source | Note |
|---|---|---|
| An impacted lower third molar can lie horizontally and press on the second molar | Standard classification (Winter: horizontal/mesioangular); PMC8509309 | — |
| Steps: incision, flap, bone removal, sectioning, crown then roots, suture | NHS "Wisdom tooth removal – what happens" (cut gum; tooth removed in 1 piece or cut into 2–3 pieces; stitches); BMC Oral Health 2023 s12903-023-03086-9 | NHS phrases bone removal as "widen the socket" |
| The inferior alveolar nerve runs just below the roots; injury causes lip and chin numbness | NHS (as above); systematic review: IAN injury 0.35–8.4 % (PMC4306319) | On-screen "몇 mm" is illustrative. In our model the gap is about 3.4 mm. Real cases range from contact to several mm |
| Dry socket follows clot loss; avoid straws | Mayo Clinic (clot protects bone and nerve endings); Cleveland Clinic 17731 ("avoid straws for at least one week") | **Contested:** PubMed 22432232 ("Straws do not cause dry sockets…"). Not used in the 10 s cut. In the full episode, phrase it as "권고" |
| Dry socket after impacted mandibular third molar removal is about 5–30 % | Open Dentistry J. 5:7; J. Khyber Coll. Dent. 738 (≈20 %) | Not used in the 10 s cut |

## YouTube reused/generic-content lessons (bookmark 2120181597617922247, enricpedro/factum-skills, MIT)
- Health content is sensitive. Never present an AI voice or avatar as a doctor; label the video as a 3D illustration and cite sources.
- Everything seen and heard must be made for the channel. No EBS or hospital marks, and no copying of their exact frame or brand look. Here we use our own text brand, our own renders and procedural audio.
- "Generic/repetitive" is judged across the catalogue. Vary the concept, title shape and thumbnail per video; appeals rarely win, so prevent it rather than plan to appeal.
- Visuals must match the claims at every random point, and the models must stay consistent between shots.
- Show a human author (About page and banner).

## Third-molar mesh search (draft17, 2026-11-20)
| Source | Result |
|---|---|
| BodyParts3D parts list (dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_parts_list_e.txt) | No third molar (only 1st/2nd molars). |
| NIH 3D, "Impacted Wisdom Teeth, 3D Model" 3DPX-000281 (https://3d.nih.gov/entries/3DPX-000281), CC0 1.0 | Downloaded (VRML, 473k verts after welding). It is one cone-beam-CT isosurface with **2 connected components (mandible, maxilla). Teeth are fused into the bone surface**, so no separable third molar. Not used. |
| Sketchfab, Thingiverse, MorphoSource | Downloads need an account login or API token. Not attempted without the owner's credentials. |
| TRELLIS.2 | Needs Linux and a 24 GB NVIDIA GPU. Does not run on this Mac. |
| Used | anat_kit/assets/third_molar_l.blend: our procedural sculpt of a Z-Anatomy first-molar copy (CC BY-SA derivative), full size from draft17. |
