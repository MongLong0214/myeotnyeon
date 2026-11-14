from pathlib import Path
import json,hashlib,subprocess,re
import numpy as np
W=Path.cwd();Q=W/'episodes/quiz/q006';P=Q/'v3d_work'
def run(args,out):
 with out.open('w') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
V=W/'upload/v3d_q006.mp4'
run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(V)],Q/'ffprobe_v3d.json')
run(['ffmpeg','-hide_banner','-nostats','-i',str(V),'-filter_complex','ebur128=peak=true','-f','null','-'],Q/'loudness_v3d.log')
run(['ffmpeg','-hide_banner','-nostats','-i',str(V),'-vf','freezedetect=n=-50dB:d=1.5,blackdetect=d=0.04:pix_th=0.10:pic_th=0.98','-an','-f','null','-'],Q/'motion_black_v3d.log')
a=[]
for version in ['v3c','v3d']:
 v=W/f'upload/{version}_q006.mp4'
 pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(v),'-map','0:a:0','-f','f32le','-'])
 aac=subprocess.check_output(['ffmpeg','-v','error','-i',str(v),'-map','0:a:0','-c:a','copy','-f','adts','-'])
 a.append((pcm,aac))
report=dict(identical_pcm=a[0][0]==a[1][0],identical_aac_bytes=a[0][1]==a[1][1],pcm_bytes=len(a[0][0]),aac_bytes=len(a[0][1]),pcm_sha256=[hashlib.sha256(x[0]).hexdigest() for x in a],aac_sha256=[hashlib.sha256(x[1]).hexdigest() for x in a])
(P/'audio_compare.json').write_text(json.dumps(report,indent=2));print('audio',report,flush=True)
# Compare every decoded output frame, not selected screenshots.
cmd=lambda v:['ffmpeg','-v','error','-i',str(W/f'upload/{v}_q006.mp4'),'-map','0:v:0','-f','rawvideo','-pix_fmt','rgb24','-']
ps=[subprocess.Popen(cmd(v),stdout=subprocess.PIPE) for v in ['v3c','v3d']]
size=1080*1920*3;diff=[];i=0
while True:
 raw=[p.stdout.read(size) for p in ps]
 if not raw[0] and not raw[1]:break
 assert all(len(x)==size for x in raw)
 if raw[0]!=raw[1]:
  x,y=[np.frombuffer(b,dtype=np.uint8).reshape(1920,1080,3) for b in raw];d=np.abs(x.astype(np.int16)-y.astype(np.int16));mask=np.any(d,axis=2);ys,xs=np.where(mask)
  diff.append(dict(frame=i,max_error=int(d.max()),mean_absolute_error=float(d.mean()),changed_pixels=int(mask.sum()),bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]))
 i+=1
assert all(p.wait()==0 for p in ps)
c=json.loads((W/'production/compositor/public/q006/render.json').read_text());cue=next(c for c in c['cues'] if c['scene']=='weigh');start=cue['from']+cue['p']['cardAt'][2];end=cue['from']+cue['dur']
r=dict(frames_compared=i,card_interval_inclusive=[start,end-1],different_frames=diff,identical_frames=i-len(diff),outside_card_differences=[d for d in diff if not start<=d['frame']<end],only_card_frames_differ=all(start<=d['frame']<end for d in diff))
(P/'frame_compare.json').write_text(json.dumps(r,indent=2));print('frame comparison',i,len(diff),'outside',len(r['outside_card_differences']),flush=True)
