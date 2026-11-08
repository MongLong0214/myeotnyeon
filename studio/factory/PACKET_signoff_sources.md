# Task: bind CTO sign-offs to the preserved source snapshots (small change, no full rebuild)

W = .. Edit `W/factory/gates.py` and related factory code minimally. Do not touch existing upload files or packages, except for writing new test packages. No network, no uploads.

The sign-off digest (`gates.py`, about lines 250–257) covers the package files and the gate evidence for facts, red_lines and number. It does NOT cover the source text that was actually reviewed.

## Do

1. For every source the episode's facts gate uses, resolve its preserved local snapshot file. Episode sources map to files such as `W/research/raw3/V3-02_1.txt`; the QA content_rules list file paths and their sha256. Put the sha256 of each snapshot file into the digest. Read the preserved snapshot only; never re-fetch the URL.
2. If any source a fact relies on has no preserved snapshot, the facts gate is FAIL (deterministic, not signable) with the evidence 'missing source snapshot: <id>'. The package is not READY.
3. Tests, kept to two cases on an existing package copy, with no render:
   - (a) Sign the facts gate with the current digest, then change one byte in a COPY of one source snapshot that the test points at. The sign-off must be invalidated: facts goes back to NEEDS_REVIEW and READY is false.
   - (b) Point one source at a missing snapshot: facts FAIL, not signable, READY false.
   Put them in `W/factory/tests/test_signoff_sources.py` and run them.
4. Update `factory/README.md` with one line on this rule.

## Final message (short, Korean)

The change, the two test results, and the paths.
