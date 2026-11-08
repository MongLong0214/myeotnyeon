import json,sys
from pathlib import Path
import cv2
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));import measure_all as a
for vid in json.loads((R/'inventory.json').read_text())['long']:
 d=R/vid
 if not (d/'transcript.internal.json').exists():continue
 x=json.loads((d/'transcript.internal.json').read_text());gaps=[(s['end']+t['start'])/2 for s,t in zip(x['segments'],x['segments'][1:]) if t['start']-s['end']>1.5];cap=cv2.VideoCapture(str(d/'analysis_proxy.mp4'));fps=cap.get(cv2.CAP_PROP_FPS)
 if gaps:a.sheet_frames(cap,gaps,fps,d/'narration_gaps.jpg',4,(320,180))
 cap.release()
