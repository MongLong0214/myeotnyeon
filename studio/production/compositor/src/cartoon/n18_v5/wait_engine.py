"""Read-only engine readiness poll. No network; 180 s interval, 5 h deadline."""
from pathlib import Path
from datetime import datetime, timezone
import json, time
W=Path(__file__).resolve().parents[5]
ready=W/'production/compositor/src/cartoon/engine_v5/READY_ENGINE.txt'
out=W/'episodes/v4/n18/cartoon_v5/engine_poll.json'
events=json.loads(out.read_text()).get('events',[]) if out.exists() else []
start=datetime.fromisoformat(events[0]['utc']).timestamp() if events else time.time()
while time.time()-start<=18000:
    ok=ready.exists()
    events.append({'utc':datetime.now(timezone.utc).isoformat(),'ready':ok})
    out.write_text(json.dumps({'interval_s':180,'deadline_s':18000,'events':events},indent=2))
    print(events[-1],flush=True)
    if ok:
        print(ready.read_text(),flush=True)
        break
    time.sleep(180)
else:
    raise SystemExit('Engine v5 readiness deadline exceeded after 5 h')
