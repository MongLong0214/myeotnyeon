# Task: put the production code and records under Git version control — W=/Users/isaac/projects/verdict-kr/work (100 GB, mostly media)

Goal: the factory code, scripts, facts tables, metadata and decision records must be traceable through git history. No media goes into git.

1. Run `git init` in W (local only: **no remote, no push**). Create the `main` branch.
2. `.gitignore`: by default, exclude every media and large binary file.
   - Exclude by extension: mp4/mov/wav/mp3/m4a/aac/flac/png/jpg/jpeg/webp/gif/zip/npz/pt/bin/onnx/safetensors.
   - Exclude these directories: node_modules, .venv, out, renders, bundle, frames, tmp, _work, tts_lab models/caches, review_runs/**/(images), and every render_* output.
   - Exclude any single file over 1 MB as well, using a check script.
   - Include: *.py *.ts *.tsx *.js *.cjs *.mjs *.json (small ones only) *.md *.txt *.csv *.jsonl (small ones only) *.sh, plus config files.
3. **Secret screen (mandatory):**
   - Before staging, scan for API keys, tokens, cookies, passwords, private keys and personal emails/phone numbers. Find files with patterns plus entropy.
   - Exclude any hit from git: add it to .gitignore and list it in a report. Do not change the original files.
   - Keep the Naver key in its excluded state.
4. Make the first commit by functional area: factory / production / episodes(scripts and facts) / upload (meta and ledger) / docs. Message format: `area: summary`.
   - Run `commitlore init --mcp-scope none` and then `commitlore doctor` in W. If they fail, record the reason only.
5. Write `W/REPO.md`, at most one page: what is tracked, what is excluded, and how to commit and record changes.
6. Report: tracked file count and total size, the excluded categories, secret-screen hits (file names only, never the values), and the commit list.

Do not modify, delete or move any existing file, except for creating .gitignore and REPO.md. Final message: short, in Korean.
