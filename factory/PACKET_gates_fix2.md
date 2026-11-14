# Gates fix2: two new checks for defects the CTO missed and the CEO caught (N18, 2026-11-07)

CEO evidence: episodes/review_full/n18_v2/ceo_tight_review/CEO_REVIEW.md, edge_verify.jpg, temporal_edges.jpg.

1. **Edge-fill gate (automatic).** Scan every encoded frame at least every 0.2 s. Detect a frame edge (left, right, top or bottom) where the background stops, leaving a flat band with a vertical or horizontal boundary that does not belong to the scene.
   - Positive cases that must FAIL: N18 at 202.167 s, 238.333 s and 278.433 s, and 276.55–280.05 s where the band grows.
   - Negative cases that must PASS: the approved shots elsewhere in N18.
   - Add it to longform_qa.py and short.py under a new REVIEW_CHECKLIST item, with today's date and the reason "CEO caught; CTO missed".
2. **Handedness check (sign-off item, semi-automatic).** For actions with a canonical hand, such as a military salute (right hand), sample the start and peak frames of each shot whose shot spec or script mentions that action. Put them on a sign-off sheet that the CTO must check. Cases: SH034 at 133.433 s and SH037 at 142.633 s. If shots_v2.json names the salute rig, add a static check that flags any salute rig called with the left arm.
3. Run the edge-fill gate on production/lf_toon/v2/lf2/lf2_v2_1080p.mp4 now, since it uses the same engine and camera code, and report the hits with timestamps.

Fix the gate code only. Never loosen a gate to make a video pass. Each check needs a test with one real positive and one negative. Do not render or upload anything.
