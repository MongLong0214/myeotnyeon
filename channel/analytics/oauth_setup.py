"""Read-only YouTube OAuth consent. No argument: the 몇년나옴 token (myeotnyeon.youtube.oauth_refresh_token).
With a registry key (guessthesentence, nannenderu, beastclash): pick THAT brand channel at consent; the token is stored
as myeotnyeon.youtube.oauth_refresh_token.<key> only if the consented channel id matches the registry, so a wrong pick
never overwrites another channel's token."""
import json, subprocess, sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

key = sys.argv[1] if len(sys.argv) > 1 else None
reg = {c['key']: c for c in json.loads((Path(__file__).resolve().parents[2] / 'factory/channels/registry.json').read_text())['channels']}
if key and key not in reg:
    sys.exit(f'unknown channel key {key}; one of {sorted(reg)}')
want = reg[key or 'myeotnyeon']
service = 'myeotnyeon.youtube.oauth_refresh_token' + (f'.{key}' if key and key != 'myeotnyeon' else '')
cfg = json.loads(subprocess.check_output(['security', 'find-generic-password', '-s', 'myeotnyeon.youtube.oauth_client_json', '-w']).decode())
flow = InstalledAppFlow.from_client_config(cfg, scopes=['https://www.googleapis.com/auth/yt-analytics.readonly', 'https://www.googleapis.com/auth/youtube.readonly'])
creds = flow.run_local_server(port=8765, open_browser=False, authorization_prompt_message='AUTH_URL {url}',
                              success_message=f"{want['name']} 연결 완료. 이 창을 닫아도 됩니다.", prompt='consent', access_type='offline')
ch = build('youtube', 'v3', credentials=creds).channels().list(part='snippet', mine=True).execute()
got = [(i['id'], i['snippet']['title']) for i in ch.get('items', [])]
print('CHANNELS', got)
if want['channel_id'] not in [g[0] for g in got]:
    sys.exit(f"consented channel is not {want['name']}; token NOT stored. Re-run and pick {want['handle']} at consent.")
subprocess.run(['security', 'add-generic-password', '-U', '-s', service, '-a', 'isaac', '-w', creds.refresh_token], check=True)
print('stored', service)
