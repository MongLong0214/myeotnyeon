from pathlib import Path
from datetime import datetime,timezone
import time,json
W=Path(__file__).resolve().parents[5];ready=W/'production/compositor/src/cartoon/engine_v4/READY_ENGINE.txt';out=W/'episodes/v4/n18/cartoon_v4/engine_poll.json'
start=time.time();events=[]
while time.time()-start<=14400:
 now=datetime.now(timezone.utc).isoformat();ok=ready.exists();events.append({'utc':now,'ready':ok});out.write_text(json.dumps({'interval_s':180,'deadline_s':14400,'events':events},indent=2));print(now,'READY' if ok else 'waiting',flush=True)
 if ok: print(ready.read_text(),flush=True);break
 time.sleep(180)
else: raise SystemExit('Engine readiness deadline exceeded')
