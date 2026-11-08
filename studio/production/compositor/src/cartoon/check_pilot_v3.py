"""Measure the delivered film and extract each cut. All outputs are exclusive creations."""
from pathlib import Path
import json, subprocess, wave, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
W=Path(__file__).resolve().parents[4]
E=W/'episodes/lf2_daejeon_bank/cartoon';S=Path(__file__).parent
D=json.loads((S/'pilot_data.json').read_text()); movie=E/'pilot_45s.mp4'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(movie)]))
# Decode every frame, including all inter-cut intervals, without creating a second video.
cmd=['ffmpeg','-v','error','-threads','2','-filter_threads','1','-i',str(movie),'-vf','scale=384:216','-an','-pix_fmt','gray','-f','rawvideo','pipe:1']
p=subprocess.Popen(cmd,stdout=subprocess.PIPE);n=384*216;prev=None;metrics=[];frame=0;shot_stats=[[] for _ in D['shots']];duplicates=[]
while True:
 raw=p.stdout.read(n)
 if not raw: break
 if len(raw)!=n: raise RuntimeError('Incomplete frame')
 arr=np.frombuffer(raw,np.uint8).astype(np.float32)
 if prev is not None:
  mae=float(np.mean(np.abs(arr-prev)));metrics.append(mae)
  if mae==0:duplicates.append(frame)
  for i,s in enumerate(D['shots']):
   if s['start']<frame<s['end']:shot_stats[i].append(mae);break
 prev=arr;frame+=1
if p.wait()!=0:raise RuntimeError('Video decode failed')
def pcm(file):
 with wave.open(str(file),'rb') as r:
  w=r.getsampwidth();raw=r.readframes(min(r.getnframes(),45*r.getframerate()))
 if w==3:
  b=np.frombuffer(raw,np.uint8).reshape(-1,3).astype(np.int32);v=b[:,0]|(b[:,1]<<8)|(b[:,2]<<16);v=np.where(v&0x800000,v-0x1000000,v).astype(float)/8388608
 else:v=np.frombuffer(raw,'<i2').astype(float)/32768
 return raw,v
src_bytes,src=pcm(E.parent/'audio/voice_first90.wav');excerpt_bytes,_=pcm(E/'public/narration_45s.wav')
audio_raw=subprocess.check_output(['ffmpeg','-v','error','-threads','2','-filter_threads','1','-i',str(movie),'-vn','-ac','1','-ar','48000','-f','f32le','pipe:1'])
audio=np.frombuffer(audio_raw,'<f4')[:2160000];rms=np.sqrt(np.mean(audio.reshape(1350,1600)**2,axis=1));source_rms=np.array(D['rms'])
# Conservative upper bound: every character takes one full 46px em.
# Actual font coverage and clipping were reviewed in the rendered frames.
widths=[len(line)*46 for c in D['subtitles'] for line in c['text'].split('\n')]
# Extract exactly one midpoint per cut from the final encoded MP4.
if list((E/'qa').glob('final_cut_*.png')):raise FileExistsError('Final cut stills already exist')
frames=[(s['start']+s['end'])//2 for s in D['shots']]
select='+'.join(f'eq(n,{f})' for f in frames)
subprocess.run(['ffmpeg','-v','error','-n','-threads','2','-filter_threads','1','-i',str(movie),'-vf',f"select='{select}'",'-fps_mode','vfr',str(E/'qa/final_cut_%02d.png')],check=True)
canvas=Image.new('RGB',(1920,1554),'#fffdf6');draw=ImageDraw.Draw(canvas)
label_font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
head_font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',25)
draw.text((16,13),'CARTOON PILOT / FINAL MP4 / 1920 x 1080 / 30 fps / 45.00 s / 20 cuts',font=head_font,fill='#141414')
for i,(s,f) in enumerate(zip(D['shots'],frames)):
 x=(i%4)*480;y=54+(i//4)*300;tile=Image.open(E/f'qa/final_cut_{i+1:02}.png').convert('RGB');tile=tile.resize((480,270),Image.Resampling.LANCZOS)
 canvas.paste(tile,(x,y+30));draw.text((x+8,y+6),f'{s["id"]}  {s["start"]/30:05.2f}-{s["end"]/30:05.2f}s  frame {f}',font=label_font,fill='#141414')
with (E/'pilot_sheet.jpg').open('xb') as out:canvas.save(out,quality=94,subsampling=0)
within=[v for a in shot_stats for v in a]
report=dict(frame_count=frame,probe=probe,cut_count=len(D['shots']),character_shots=sum(s['character'] for s in D['shots']),character_frames=sum(s['end']-s['start'] for s in D['shots'] if s['character']),character_shot_percent=100*sum(s['character'] for s in D['shots'])/len(D['shots']),character_time_percent=100*sum(s['end']-s['start'] for s in D['shots'] if s['character'])/1350,mean_cut_s=45/len(D['shots']),max_cut_s=max(s['end']-s['start'] for s in D['shots'])/30,min_cut_s=min(s['end']-s['start'] for s in D['shots'])/30,within_shot_frame_pairs=len(within),min_within_shot_mae=min(within),mean_within_shot_mae=float(np.mean(within)),motion_shots=sum(all(v>0 for v in a) for a in shot_stats),duplicate_frame_indices=duplicates,subtitle_max_lines=max(len(c['text'].split('\n')) for c in D['subtitles']),subtitle_conservative_max_width_px=max(widths),subtitle_min_x_px=960-max(widths)/2-4,subtitle_max_x_px=960+max(widths)/2+4,audio_rms_correlation=float(np.corrcoef(rms,source_rms)[0,1]),pcm_excerpt_bit_identical=src_bytes==excerpt_bytes,excerpt_pcm_sha256=hashlib.sha256(excerpt_bytes).hexdigest(),mp4_sha256=hashlib.sha256(movie.read_bytes()).hexdigest(),cuts=[dict(s,frame=frames[i],min_frame_mae=min(shot_stats[i]),mean_frame_mae=float(np.mean(shot_stats[i]))) for i,s in enumerate(D['shots'])])
with (E/'qa/render_measurements.json').open('x') as out:json.dump(report,out,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['probe','cuts']},ensure_ascii=False,indent=2))
