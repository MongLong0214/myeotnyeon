# Task: myeotnyeon repository migration audit (read-only research plus one document) — W=/Users/isaac/projects/verdict-kr/work

Allowed: reading, git log/diff/show, running existing tests, `commitlore` lookups (context/limits/ruled-out/warnings/guard).
Forbidden: remote push, creating or cancelling ACP runs, moving or deleting production directories, any production code change.
The only output is **`W/docs/REPO_MIGRATION_AUDIT.md`** (an appendix to the existing plan, docs/REPO_ARCHITECTURE_PLAN.md).

## Contents
1. **Run A facts:**
   - The run ID is run_b86c2fe61ad8402a963074f5.
   - The current contract: read ~/.agent-control-plane local records and the repo's .agent-control-plane/project.json. If you cannot access them, mark it missing.
   - The latest BLOCK: on c2d0460d, 42 findings. If the original findings cannot be reached, record that as missing.
   - Mark which of the existing acceptance criteria the current operation still needs, and which to drop.
2. **The unmerged branches** of /Users/isaac/projects/myeotnyeon (the 20+ task/* branches). For each branch:
   - base, its unique change files and LOC, the tests it contains, and whether those tests pass when run (run them in an isolated worktree: `git worktree add` under the scratch area, removed when done);
   - whether the same function exists in current verdict-kr/work operations or overlaps with it;
   - a verdict: reuse / preserve only / drop.
3. **Inventory of the current operating code** (verdict-kr/work local git):
   - modules, entry points and dependencies;
   - external path references (absolute paths, ~/.aside, keychain item names), media references, secret boundaries.
4. **The first migration unit proposal:** a small unit that can be switched over and rolled back on its own (e.g. factory/lib + review_gates + REVIEW_CHECKLIST). It must have:
   - owned paths, verification commands, an equivalence test (identical output on the same input before and after the move);
   - the switch-over procedure and the rollback method.
5. **CommitLore:** the existing decision records related to the repo (commitlore context/guard for the main paths).

Final message: short, in Korean.
