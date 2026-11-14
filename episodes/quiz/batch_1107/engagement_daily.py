"""Read existing authorized Analytics snapshots; never uploads or changes a video."""
from pathlib import Path
import csv,json
W=Path(__file__).resolve().parents[3];B=Path(__file__).parent
rows=[]
for p in sorted((W/'channel/analytics/daily').glob('api_*.json')):
 d=json.loads(p.read_text());v=d.get('shorts_swipe',{});ix={h['name']:i for i,h in enumerate(v.get('columnHeaders',[]))}
 if not {'video','views','engagedViews'}<=ix.keys():continue
 for r in v.get('rows',[]):
  views=r[ix['views']];engaged=r[ix['engagedViews']]
  rows.append([p.stem[4:],r[ix['video']],views,engaged,round(engaged/views,8) if views else None,str(p.relative_to(W))])
with (B/'engagement_daily.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['snapshot_date','video_id','views','engagedViews','engagedViews/views','source']);w.writerows(rows)
print(len(rows),'video observations; cumulative snapshot ratios, not viewed-vs-swiped-away')
