"""Render N18 representatives using the existing B-path Chromium wrapper."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,json,os,shlex,subprocess,time
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',type=Path,default=ROOT.parents[1]/'episodes/v4/n18/rep')
parser.add_argument('--stills-only',action='store_true')
args=parser.parse_args()
OUT=args.output_dir.resolve()
ENV={**os.environ,'npm_config_cache':'/tmp/verdict-n18-npm-cache'}
COMMON=['--browser-executable=src/v4spike/chromium.sh','--port=3145']

def run(label,args):
 command=['npx','--no-install','remotion',*args,*COMMON]
 start=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds');t=time.monotonic()
 with (OUT/f'{label}.log').open('w') as f:
  f.write('$ '+shlex.join(command)+'\n');f.flush()
  subprocess.run(command,cwd=ROOT,env=ENV,stdout=f,stderr=subprocess.STDOUT,check=True)
 result=dict(run=label,start=start,end=datetime.now(ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds'),wall_seconds=round(time.monotonic()-t,3),command=command)
 print(json.dumps(result),flush=True)
 return result

if __name__=='__main__':
 OUT.mkdir(parents=True,exist_ok=True)
 metrics=[]
 for i in range(1,4):
  cid=f'V4N18-REP{i}'
  metrics.append(run(cid+'-still',['still','src/index.ts',cid,str(OUT/f'{cid}.png'),'--frame=90']))
  (OUT/'render-times.json').write_text(json.dumps(metrics,indent=2)+'\n')
 if args.stills_only:
  raise SystemExit(0)
 for i in range(1,4):
  cid=f'V4N18-REP{i}'
  metrics.append(run(cid+'-clip',['render','src/index.ts',cid,str(OUT/f'{cid}.mp4'),'--codec=h264','--crf=18','--pixel-format=yuv420p','--color-space=bt709','--concurrency=3']))
  (OUT/'render-times.json').write_text(json.dumps(metrics,indent=2)+'\n')
 metrics.append(run('COVER-Q012-after',['still','src/index.ts','COVER-Q012',str(OUT/'COVER-Q012-after.png')]))
 (OUT/'render-times.json').write_text(json.dumps(metrics,indent=2)+'\n')
