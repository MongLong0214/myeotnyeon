from pathlib import Path
import json,re,sys,hashlib,datetime,subprocess
W=Path.cwd();Q=W/'episodes/quiz/q006';P=Q/'v3d_work';V=W/'upload/v3d_q006.mp4'
sys.path.insert(0,str(W/'episodes/quiz/out/v3'));import qa,tempo,textgate
# The existing qa.py is invoked as functions so its fixed v3 output paths are
# never written. Keep the original engines and thresholds, with the new input.
standard=dict(probe=qa.probe(V),loudness=qa.loud(V),freeze_black=qa.freeze_black(V),spelling=qa.spelling('q006'),accuracy=qa.accuracy('q006'))
(P/'qa_pipeline.json').write_text(json.dumps(standard,ensure_ascii=False,indent=2))

print(json.dumps(standard,ensure_ascii=False,indent=2))
