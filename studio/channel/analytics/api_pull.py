import json, subprocess, datetime, sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
def kc(s): return subprocess.check_output(['security','find-generic-password','-s',s,'-w']).decode().strip()
cfg=json.loads(kc('KEYCHAIN_SERVICE_PREFIX.youtube.oauth_client_json'))['installed']
creds=Credentials(None,refresh_token=kc('KEYCHAIN_SERVICE_PREFIX.youtube.oauth_refresh_token'),token_uri=cfg['token_uri'],client_id=cfg['client_id'],client_secret=cfg['client_secret'],scopes=['https://www.googleapis.com/auth/yt-analytics.readonly','https://www.googleapis.com/auth/youtube.readonly'])
ya=build('youtubeAnalytics','v2',credentials=creds)
end=datetime.date.today().isoformat(); start='2026-10-20'
out={}
def q(**kw):
    try: return ya.reports().query(ids='channel==MINE',startDate=start,endDate=end,**kw).execute()
    except Exception as e: return {'error':str(e)[:300]}
out['per_video']=q(metrics='views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost,likes,comments,shares',dimensions='video',sort='-views',maxResults=50)
out['traffic']=q(metrics='views',dimensions='insightTrafficSourceType',sort='-views')
out['daily']=q(metrics='views,subscribersGained,subscribersLost',dimensions='day',sort='day')
out['shorts_swipe']=q(metrics='views,engagedViews',dimensions='video',sort='-views',maxResults=50)
p=f'channel/analytics/daily/api_{end}.json'
import os; os.makedirs('channel/analytics/daily',exist_ok=True); json.dump(out,open(p,'w'),ensure_ascii=False,indent=1); print(p)
for k,v in out.items(): print(k, 'ERR '+v['error'] if 'error' in v else f"rows={len(v.get('rows',[]))} cols={[c['name'] for c in v.get('columnHeaders',[])]}")
