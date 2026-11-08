# Task: analyze the Unslop skills and build an "un-AI" design system for subtitles, UI and copy — W=.

Owner: "그림체는 많이 좋아졌는데 아직 전반적으로 자막, ui등이 아직 너무 ai 스러워 / Unslop 관련 스킬들 싹 분석해서 활용해 ai스럽지않게 해줘" (the art style is much better, but the subtitles and UI still look too AI-made overall; analyze every Unslop-related skill and use them so it doesn't look AI-made).

## 1. Analyze (network allowed, collection only; do not install or run third-party code — read only)
- mshumer/unslop: how it extracts patterns and writes skill.md
- heydamir/unslop (redesigning AI-looking interfaces)
- Nutlope/hallmark (anti-AI-slop design skill)
- the-hooman-loop/anti-slop-kit, Vinayak-Shukla-03/anti-ai-slop
- unslop-ui (jc-aiwiki), and the Medium "Anti-AI-slop design skill" article
- Local skills: frontend-design, humanize-korean (Korean AI-tell patterns: subtitle and narration copy), web-design-guidelines, uiux
- Summarize each skill's core rules in `factory/unslop/SKILLS_DIGEST.md`, with sources.

## 2. Diagnose our videos
- Inputs:
  - current Shorts: W/upload/v52_q014_n15_comedy.mp4, v52_q013_n16_comedy.mp4, upload/pkg/q020_batch1107/video.mp4
  - long-form proofs: production/lf_toon/proof/*.mp4
- List the "reads as AI-made" elements in subtitles, UI and layout as `DIAGNOSIS.md`, each with frame evidence (PNGs under W/episodes/review_full/unslop/). Examples:
  - box/badge/pill overuse, uniform rounded cards, a symmetric template feel
  - meta labels ("시각비유", "판결 보도 기반 재구성"), stacked layers of text
  - generic paired fonts and weights, perfect alignment, gradients and shadows
  - AI-style copy (explanatory, translated-sounding, formulaic hooks like "그런데 반전은")
  - mechanical CTAs, emoji or arrow abuse
- Compare with reference channels: the frame-accurate measurements of human-made channels the owner referenced earlier (the Extol channel; under W/references or W/research). Contrast how they treat subtitles, layout and graphics.

## 3. Design system: `factory/unslop/STYLE_VIDEO.md`
- Subtitles: font, size, stroke and shadow, color accents, line breaks and rhythm, placement (human-edited caption feel), how emphasis words are handled.
- Header and labels: minimal. Required legal disclaimers go into the description or a small fixed corner.
- Layout: break out of the card template (full-bleed reenactment, scale changes, deliberate asymmetry).
- Copy: Korean AI-tell rules from humanize-korean — colloquial, short, no translationese.
- **Keep the hard lines:** reenactment disclosure, the demand-vs-sentence distinction, victims not identifiable.
- Provide 2–3 1080x1920 mockup frames: before/after for the same scene, as PNG in W/episodes/review_full/unslop/.

## 4. Applying it (no code changes in this task)
- Write a patch plan for where the style hooks into the Shorts template (q014 comedy-based QuizPanels / Captions) and the long-form Captions: file and function level.
- Add the "AI-tell checklist" items to factory/REVIEW_CHECKLIST.md B2 as a proposal only.
- Do not touch the running lanes (shorts-batch1107, lf-full-*) or their files.

Final message: short, in Korean, with the 5 key rules and the mockup paths.
