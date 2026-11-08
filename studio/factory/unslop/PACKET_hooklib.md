# Hook and caption distillation from 2 MIT repos (owner 11-07: "참고할만한게있나")

Read only these files. Use the GitHub raw URL or a shallow clone into a temporary directory (e.g. `$(mktemp -d)/hooklib`), deleted afterwards:
- coreyhaines31/marketingskills: skills/social/references/short-form-video.md, plus the hook and anti-slop parts of skills/copywriting and skills/ad-creative
- AgriciDaniel/claude-youtube: skills/claude-youtube/references/retention-scripting-guide.md, sub-skills/hook.md, sub-skills/shorts.md (if it exists)

Distill these into our rules. Do not paste whole files.

1. Write `factory/unslop/HOOKS.md`: hook formulas usable for Korean court-sentence Shorts (first 0–2 s; a frame-1 action plus a question). For each formula give one Korean example built from our own published cases (VBEjj7mPjrI q013, q020, q018).
   - Drop anything that is clickbait-false, that implies unconfirmed facts, or that mocks victims; this follows our facts and red-line rules in REVIEW_CHECKLIST.md.
2. Add the caption rules that fit the owner's existing rules to `factory/unslop/STYLE_VIDEO.md`, under a dated section. The existing owner rules always win:
   - subtitles centered horizontally;
   - legible: 72px, weight 800, with an outline;
   - not AI-looking;
   - base shot 2–3 s.
   List every conflicting rule from the repos as REJECTED, with the reason. Example: per-word color highlights may read as AI-template.
3. Add an A/B hypothesis format for subscriber-conversion tests to `channel/analytics/RULES.md`, in a few lines that tie to the existing api_pull metrics.
4. Record attribution (repo, path, MIT license, date) in `factory/THIRD_PARTY.md`.

Do not render or upload anything. Report a changed-file list and a short summary.
