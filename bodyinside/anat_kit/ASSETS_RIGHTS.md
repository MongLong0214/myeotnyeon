# Anatomy asset rights (checked 2026-11-21; not legal advice)

Method: pages opened via a fetch tool that summarises the page. Mesh files were NOT downloaded, so
poly count, closedness and per-bone separation are unverified unless stated. A 403 means I did not read that page.

## Table
| source | licence (as shown) | attribution needed? | usable mesh? | notes | URL opened |
|---|---|---|---|---|---|
| NIH 3D 3DPX-000281 Impacted Wisdom Teeth | "Public Domain" badge -> CC0 1.0 | No (CC0) | Fused CT isosurface (per brief); not checked | Cone-beam CT, LeeDock | https://3d.nih.gov/entries/3DPX-000281 |
| NIH 3D 3DPX-000380 Cervical Spine | Public Domain -> CC0 1.0 | No | Unknown: one output file "cervical_limpo"; likely one fused mesh | Source data NIAID; uploader bgobbato; method not stated | https://3d.nih.gov/entries/3DPX-000380 |
| NIH 3D 3DPX-000331 Spine Lumbar | Public Domain -> CC0 1.0 | No | Unknown, one mesh file | same uploader | https://3d.nih.gov/entries/3DPX-000331 |
| NIH 3D 3DPX-000528 Vertebrae column (incomplete) | Public Domain -> CC0 1.0 | No | Unknown; "assembled from Visible Human data" (NLM), one file incl. discs | Incomplete column | https://3d.nih.gov/entries/3DPX-000528 |
| NIH 3D 3DPX-000849 Cranium and Facial Bones | Public Domain -> CC0 1.0 | No | Unknown; one file "skull_repaired"; CT reconstruction credited to a Sketchfab author | Upstream author's rights not shown on page | https://3d.nih.gov/entries/3DPX-000849 |
| NIH 3D 3DPX-000388 Knee Model | Public Domain -> CC0 1.0 | No | Unknown; file "joelho_limpo", no description | Likely CT surface | https://3d.nih.gov/entries/3DPX-000388 |
| NIH 3D 3DPX-002636 17yo female normal heart | Public Domain -> CC0 1.0 | No | 4 output files; CT, "to scale", valves poor | Heart Library collection | https://3d.nih.gov/entries/3DPX-002636 |
| NIH 3D 3DPX-022787 Human Heart | Public Domain -> CC0 1.0 | No | Unknown; from "Biology Notes Online" | Provenance of source is weak | https://3d.nih.gov/entries/3DPX-022787 |
| NIH 3D policy | n/a | n/a | n/a | See "NIH caveat" below | https://3d.nih.gov/terms |
| NIH 3D CC BY / CC BY-NC entries (000905, 000404, 000899) | CC-BY / CC-BY-NC per search snippet only, entry pages not opened | Yes / yes / NC = unusable | - | Do not use | (not opened) |
| Smithsonian 3D (3d.si.edu) | Search snippets of 3d.si.edu/cc0 listing show CC0 facet (~3,400 items) | No if CC0 | Mostly primate/fossil skulls and bones; human: cranium of Homo sapiens, H. erectus etc. | Site returned 403 to me; nothing opened | (403: https://3d.si.edu/, /cc0, /explorer) |
| HRA 3D Reference Library (HuBMAP CCF) | "All CCF 3D reference objects are released under Attribution 4.0 International (CC BY 4.0)" | YES (CC BY) | GLB, many organs incl. heart, lungs, knee, brain (141 structures), pelvis, spinal cord; no full skeleton | Built from NLM Visible Human. Attribution only, no share-alike | https://hubmapconsortium.github.io/ccf/pages/ccf-3d-reference-library.html |
| BodyParts3D (DBCLS) README | Text: "The license ... is specified in the Creative Commons Attribution 4.0 International." Attribution: "BodyParts3D, (c) The Database Center for Life Science licensed under CC Attribution 4.0 International" | YES (CC BY) | OBJ, one per element, 99% polygon-reduced | Page says licence updated 2011/08/25 and 2025/02/27, yet its "summary" link points to by-sa/2.1/jp: contradictory. Verify with DBCLS. Still needs credit | https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/README_e.html |
| BodyParts3D Anatomography page | "BodyParts3D terms (CC BY-SA 2.1 Japan)" | Yes + share-alike | - | Older wording on a different DBCLS page | https://lifesciencedb.jp/bp3d/?lng=en |
| Z-Anatomy repo | "All the code and content ... CC BY-SA 4.0"; credits BodyParts3D as CC-BY-SA 2.1 Japan | Yes + share-alike | Blender-based; per-bone structure not confirmed | Remains SA regardless of BP3D's new licence | https://github.com/Z-Anatomy/Models-of-human-anatomy |
| OpenSim / SIMON bone geometry | NOT FOUND | ? | .vtp | Opensim page 404; search gave no licence. Gait2392 bones digitised from older studies | https://opensim.stanford.edu/work/models/index.html (404) |
| BioDigital | NOT FOUND (terms URL 404) | ? | Viewer, no mesh export known | Treat as unusable | https://www.biodigital.com/terms-of-use (404) |
| Sketchfab | per-model; CC0 models exist | per model | Search found no CC0 + separated-bones skeleton; one NIH-CT-derived separated model is CC BY | Check licence on each model page | search only; help page 404 |
| Open Anatomy / AnatomyTool Open 3D Model | CC BY-SA per search snippet | Yes + share-alike | builds on Z-Anatomy | Page connection refused | https://anatomytool.org/node/63904 (failed) |
| CC0 legal code | "waiving all of his or her rights ... copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission" | No | - | Confirms CC0 meaning | https://creativecommons.org/publicdomain/zero/1.0/ |

NIH caveat (terms 4.3): "Users are responsible for selecting and applying the appropriate license"; "NIH 3D does not enforce license terms on behalf of contributors"; visitors "must review and comply with the licensing terms associated with each file". So a CC0 badge is the uploader's claim. Keep a screenshot of each entry's badge and date, and prefer entries built from NIH/NLM data.

## Share-alike and remodelling (Creative Commons FAQ, https://creativecommons.org/faq/)
- Adaptation = "a work based on one or more pre-existing works"; whether a change counts "depends on applicable law" and generally means enough new original expression built on the earlier work.
- SA: "your adapter's license must be the same license as the license on the material you are adapting"; sharing an adaptation publicly means applying the same licence.
- "It is the expression that is protected by copyright and covered by the licenses" (ideas/facts are not). The FAQ gives no safe-harbour for re-sculpting or retopology. A remodel that follows the source's shape closely is probably still an adaptation. I did not find any FAQ line blessing it. Ask a lawyer if this matters.
- Our own procedural builds (discs, tubes) from our own parameters: no source expression, nothing needed.
- Anatomy is shared fact: building from textbook measurements/photos (not from the mesh) is a different thing from re-sculpting the mesh. Do not open Z-Anatomy meshes as a tracing base if we want to claim independence.
- Even CC BY-only sources (HRA, BP3D) need a credit, so they do not meet the no-credit goal.

## Plan per region (most to least feasible)
1. Heart: NIH 3DPX-002636 (CC0 badge, CT, 4 files) as base, or procedural (4 chambers + vessels as tubes, ~1-2 days; my estimate). Inspect mesh first.
2. Cervical spine: either NIH 3DPX-000380 (inspect: if fused, needs cutting into vertebrae, ~1-2 days manual) or procedural: C1-C7 vertebra template (body, arch, spinous process, facets) parameterised by level + discs; ~2-3 days for one template, 7 levels by parameters (my estimate). Already our discs/tubes route.
3. Skull: NIH 3DPX-000849 (CC0 badge, one file) or Smithsonian Homo sapiens cranium CC0 (unverified; site 403). Single cranium is fine for a cutaway; teeth need separate sculpt.
4. Knee: NIH 3DPX-000388 (CC0 badge) for bones, inspect mesh; ligaments/menisci/cartilage procedural (tubes, extruded sheets), ~2 days (estimate). HRA knee is CC BY, usable only with credit.
5. Lungs/brain: procedural lobes (subdivided blobs + displacement) ~1 day each (estimate); brain from HRA is CC BY (credit). No CC0 source found.
6. Hand and shoulder: no CC0 entry found. Build procedurally: carpals/metacarpals/phalanges from a primitive-bone generator (capsule + flared ends) ~3 days; scapula/humerus/clavicle sculpt ~3-4 days. Highest cost.
Fallback if the credit is acceptable for a few shots: one text-card credit line for CC BY (HRA, BP3D) is far cheaper than SA, which would force licensing of our derived meshes.

## Not verified
- Mesh quality (poly count, closed/watertight, separate bones, format) of every NIH entry: pages show only "Mesh File"; no download done.
- NIH entries 000905, 000404, 000899: licences came from search snippets only. NIH FAQ "how to cite" page not opened (credit is a courtesy, not a CC0 duty, but NIH's own citation request is unverified).
- Whether any NIH entry is single-mesh-per-bone: none confirmed. No hand/shoulder/lungs/brain/teeth CC0 entries found beyond wisdom teeth (searches only returned heart/knee/spine/skull).
- Smithsonian 3D licence page and human models: 403, only search snippets.
- BodyParts3D current licence: README says CC BY 4.0 but its link says by-sa/2.1/jp; Z-Anatomy is SA either way.
- OpenSim/SIMON, BioDigital, Thingiverse, Poly Haven, Blender Studio, Visible Human (NLM) direct terms, Sketchfab help page, AnatomyTool: not read. No anatomy assets expected from Poly Haven/Blender Studio (not checked).
- Legal effect of remodelling: only the CC FAQ general text read; no case law checked.

## DECISION 2026-11-21 (CEO): anatomy for new episodes comes from BodyParts3D Release 4.0, downloaded directly from DBCLS (CC BY 4.0). Z-Anatomy is not used for new work.
Provenance record (neck episode and every later episode on this asset pack):
| Item | Value |
|---|---|
| Download URL | https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/isa_BP3D_4.0_obj_99.zip (server listing: Release 4.0, last modified 2013-05-22 15:46, 136 MB) |
| Downloaded | 2026-11-21T01:55Z (UTC) to work/research/anatomy3d/bodyparts3d_4.0/ |
| SHA256 isa_BP3D_4.0_obj_99.zip | 40665852c49f218326590e204db91064a1ecfc3c6f8cbd7bbbcaac62c7cd409e |
| SHA256 isa_element_parts.txt (concept id -> FJ file) | a3de74423f943b0d724ae8f59b3a817f87c423a544f8db98113b1980817cbeaf |
| SHA256 isa_parts_list_e.txt | ab7796deedd49205e77f3609a1cb8c53e2bbee14ecb5c9a6ca05227469780513 |
| SHA256 README_e.html (licence section "Last updated 2025/02/25") | f9a90b4d945ad0fe50db45c712e931aa54e52667187b30d7085b6cc394f40107 |
| SHA256 lic.html ("Last updated: 2025/02/27"), copy in anat_kit/assets/bodyparts3d/lic_2025-02-27.html | 3769e8473417021089670c7a98dcfd5668480378215436f7e9aea79c8e4b029d |
| Licence notice that applies to THIS distribution | "The license for this database is specified in the Creative Commons Attribution 4.0 International. If you use data from this database, please be sure attribute this database as follows: 'BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International'." Conditions: attribute in the manner specified by the licensor when distributing the database or any adapted material. No ShareAlike. Licence page: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html ; DOI 10.18908/lsdba.nbdc00837-000 |
| Per-mesh record | every imported object carries custom property `src` = `bp3d:<FMA id>:<FJ file>:<sha256 of that .obj>`; list in episodes/<id>/bp3d_provenance.json |
| Gate | anat_kit/gates/provenance_gate.py: every renderable mesh traces to a DBCLS file hash (re-hashed on disk) or is marked `own`; any Z-Anatomy trace ('zanatomy', 'White matter') FAILS |
| Scope limit | This notice is NOT applied retroactively to the Z-Anatomy-derived wisdom assets (CC BY-SA 4.0 over BodyParts3D under its earlier licence); they stay under the dossier in anat_wisdom/review/rights_dossier.md |
Not in BodyParts3D, therefore built by us (marked `own`): intervertebral discs (fitted to the real endplates), spinal cord, spinal nerve roots and ganglia (procedural tubes), the curve line, labels, SFX.
FMA ids used (isa_parts_list_e.txt): atlas 12519, axis 12520, C3-C7 12521-12525, T1-T4 9165/9187/9209/9248, frontal 52734, occipital 52735, parietal 9613, temporal 52737, sphenoid 52736, zygomatic 52747, maxilla 9711, mandible 52748, left splenius capitis 22729, splenius cervicis 22727, semispinalis capitis 22877, semispinalis cervicis 22875, levator scapulae 32541, descending trapezius 33587, sternocleidomastoid 13409, longus colli 46284/46286/46288. The OBJ files store unwelded triangles: we weld at 0.01 mm (a change), then remesh.

## CC0 skin shell (2026-11-21): Blender Studio "Human Base Meshes" bundle v1.4.1
| Item | Value |
|---|---|
| URL | https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip (50,643,039 bytes, Last-Modified 2026-01-20) |
| SHA256 zip | 811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515 |
| SHA256 human_base_meshes_bundle.blend | 3c121505651140ceb4d69fd1d8923f7788ffadd81672f5be14845a5f2c75c137 |
| Licence | CC0 per Blender's description; the blender.org demo-files page could not be opened by our fetcher (403), so the licence wording is from a search summary. **Confirm in a browser before the About block claims it.** |
| Used | GEO-body_male_realistic (multires level 1), cut at x = 0.001 and z = 1.30, fitted over the BodyParts3D skull (max ~5 % scale), rendered as a translucent ghost |
| Gate | provenance_gate accepts `cc0:human_base_meshes_bundle_v1.4.1:<sha256 of the .blend>` only if the hash matches the file on disk |

## earshot (2026-11-21)
Installed in the kit venv: `pip install "earshot[listen] @ git+https://github.com/Leonxlnx/earshot"` -> earshot 1.0.0, commit 7a7f7c5c70d4a763a1eca4b3666af7c77e313f97, MIT licence (repository statement: every sound it makes is ours to use). Listening model laion/larger_clap_general@16c8cc3 downloaded to ~/.cache/earshot/hf. Used for all SFX (layout/sfx_earshot.py) and the audio gate.
## approved-source allowlist
`anat_kit/approved_sources.json` (65 sources, verdicts USE 26 / USE-WITH-CREDIT 26 / EXCLUDE 13) parsed from research/public_assets_survey.md; provenance_gate accepts `src = ext:<id>:<sha256>` only for non-EXCLUDE ids and lists credit-required ones.

## BodyParts3D in-video attribution check (2026-11-21, fetched https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html)
- The licence page says the licence is CC BY 4.0 and asks users to attribute with: "BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International"; the condition is "You must attribute this database in the manner specified by the author or licensor when distributing part or whole of this database or any adapted material."
- Nothing on the page (nor the archive README noted above) names a placement such as "in the video frame". The manner specified is the exact string. CC BY 4.0 s.3(a)(2) lets attribution be given "in any reasonable manner based on the medium, means, and context", including a URI or hyperlink; a platform description is a common reading for video, but it is a reading, not a DBCLS statement.
- Result for the neck episode: no in-video requirement found. Attribution is carried in description.txt (string verbatim, source link, CC BY 4.0 link, changes, other assets), gated by gates/description_gate.py. The CEO ruled the description block "necessary but not sufficient"; if a stricter reading is wanted, the open choice is to restore a short in-video credit (episode.json "credits", still supported by compose/assemble/video_gates). Not legal advice.
