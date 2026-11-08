# Addendum: CEO corrections (takes precedence over the original packet). Continue the same job; work done so far stays valid.

1. **Static-span, character-share and pace numbers are diagnostics, not pass criteria.**
   - Do not add camera shake, meaningless body motion or a looping idle animation just to clear the static gate. That is still a FAIL.
   - Every motion must deliver the narrated action, gaze or reaction.
   - A deliberately held, motivated shot (an emotional beat or a pause) is allowed. Record each such shot and its reason in READY_FIX.txt.
2. **Keeping the cut times is the default, not a hard constraint.**
   - Merge zoom-in/zoom-out cuts that add no new information, or replace them with a held shot.
   - Adjust the picture so it means what the unchanged audio says. Re-verify only the cut boundaries that moved.
3. **Do not build more QA tooling.** Run the existing longform_qa.py once, on the final file only.
4. **Final submission, in one package (READY_FIX.txt):**
   - the exact file paths and sha256s;
   - the changed shots with before/after frames (a single image sheet);
   - the remaining defects, stated honestly.
