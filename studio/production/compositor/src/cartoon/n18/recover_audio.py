from pathlib import Path
import json,re,subprocess,hashlib,shutil,math
import numpy as np,soundfile as sf
W=Path(__file__).resolve().parents[5];E=W/'episodes/v4/n18';O=E/'cartoon_v4';S=Path(__file__).parent
source=E/'out/n18_v4char_polished3_720p.mp4';srt=E/'out/n18_v4char_polished3.srt';d=json.loads((O/'shots.json').read_text());duration=d['durationInFrames']/30
norm=lambda x:re.sub(r'[^가-힣0-9a-zA-Z]','',x)
cues=[]
for b in srt.read_text().strip().split('\n\n'):
 _,t,text=b.split('\n',2);ts=[]
 for v in t.split(' --> '):
  h,m,s=v.replace(',','.').split(':');ts.append(int(h)*3600+int(m)*60+float(s))
 cues.append({'start_s':ts[0],'end_s':ts[1],'text':text.replace('\n','')})
assert ''.join(norm(x['text']) for x in cues)==''.join(norm(x['text']) for x in d['narration'])
# Preserve the complete local final AAC track, including all spoken samples and cadence.
raw=O/'public/recovered_final_audio.wav'
subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-vn','-c:a','pcm_s16le',str(raw)],check=True)
a,sr=sf.read(raw,always_2d=True);raw_frames=len(a);target=round(duration*sr);assert raw_frames<=target
padded=np.zeros((target,a.shape[1]));padded[:raw_frames]=a
sf.write(O/'public/narration.wav',padded,sr,subtype='PCM_16')
# Use verified existing caption cue timings, preserving their text. Frame rounding <= 16.7ms.
pos=0
for n in d['narration']:
 st=pos;pos+=len(norm(n['text']));cs=[];ci=0
 for c in cues:
  ce=ci+len(norm(c['text']))
  if ci<pos and ce>st:cs.append(c)
  ci=ce
 n['approved_start_frame']=n['start_frame'];n['approved_end_voice_frame']=n['end_voice_frame']
 n['start_frame']=round((cs[0]['start_s']+.03)*30);n['end_voice_frame']=round(cs[-1]['end_s']*30);n['start_s']=n['start_frame']/30;n['voice_end_s']=n['end_voice_frame']/30
# Keep the two purposeful visual beats for each line, retimed to the surviving final voiced version.
by={n['id']:n for n in d['narration']};groups={}
for s in d['shots']:
 if s['narration_id']:groups.setdefault(s['narration_id'],[]).append(s)
for i,n in enumerate(d['narration']):
 start=0 if i==0 else n['start_frame'];end=d['narration'][i+1]['start_frame'] if i+1<len(d['narration']) else math.ceil(raw_frames/sr*30)
 group=groups[n['id']]
 for j,s in enumerate(group):
  s['start']=round(start+(end-start)*j/len(group));s['end']=round(start+(end-start)*(j+1)/len(group));s['start_s']=s['start']/30;s['end_s']=s['end']/30
credits=[s for s in d['shots'] if s.get('endnote')];start=credits[0]['start']=math.ceil(raw_frames/sr*30)
for j,s in enumerate(credits):
 s['start']=round(start+(d['durationInFrames']-start)*j/len(credits));s['end']=round(start+(d['durationInFrames']-start)*(j+1)/len(credits));s['start_s']=s['start']/30;s['end_s']=s['end']/30
sub=[];pos=0;ci=0
for c in cues:
 while ci<len(d['narration'])-1 and pos>=sum(len(norm(x['text'])) for x in d['narration'][:ci+1]):ci+=1
 sub.append({'from':round(c['start_s']*30),'to':round(c['end_s']*30),'text':c['text'],'narration_id':d['narration'][ci]['id'],'source_start_s':c['start_s'],'source_end_s':c['end_s']});pos+=len(norm(c['text']))
for i,narr in enumerate(d['narration']):
 narr['approved_end_frame']=narr['end_frame'];narr['approved_end_s']=narr['end_s']
 narr['end_frame']=d['narration'][i+1]['start_frame'] if i+1<len(d['narration']) else start
 narr['end_s']=narr['end_frame']/30
 narr['voice_duration_s']=(narr['end_voice_frame']-narr['start_frame'])/30
 narr['pause_after_s']=(narr['end_frame']-narr['end_voice_frame'])/30
 narr['timing_basis']='Surviving exact-text final SRT; approved_* fields retain script_v3 reference timing.'
for ch in d['chapters']:
 ch['approved_start_s']=ch['start_s'];ch['start_s']=by[ch['row']]['start_s']
d['approved_judgement_silences']=d.pop('judgement_silences')
d['subtitles']=sub;d['audio_status']='exact-text local final audio recovered without speech edits; silence appended to approved 455.433s duration';d['endnotes_start_frame']=start
mono=padded.mean(1);nframes=d['durationInFrames'];samples=round(sr/30);speech=[];rms=[]
for i in range(nframes):
 z=mono[i*samples:(i+1)*samples];r=float(np.sqrt(np.mean(z*z)));rms.append(r)
 scale=min(1,max(0,(r-.005)*8));spec=np.abs(np.fft.rfft(z*np.hanning(len(z))));freq=np.fft.rfftfreq(len(z),1/sr)
 low=float(spec[(freq>150)&(freq<700)].sum());mid=float(spec[(freq>700)&(freq<2000)].sum());hi=float(spec[(freq>2000)&(freq<6000)].sum())
 active=any(n['start_frame']<=i<n['end_voice_frame'] for n in d['narration'])
 v='rest' if r<.009 or not active else 'F' if hi>mid*.85 else 'O' if low>mid*1.65 else 'E' if mid>low*1.15 else 'A'
 speech.append({'amplitude':round(scale if active else 0,4),'viseme':v})
d['speech']=speech
(O/'shots.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));(S/'data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
shutil.copy(W/'production/compositor/public/fonts/Pretendard-Bold.woff2',O/'public/Pretendard-Bold.woff2')
report={'source_video':str(source.relative_to(W)),'source_srt':str(srt.relative_to(W)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_audio_samples':raw_frames,'sample_rate':sr,'channels':a.shape[1],'source_duration_s':raw_frames/sr,'output_duration_s':duration,'appended_silence_s':(target-raw_frames)/sr,'narration_text_normalized_characters':pos,'narration_text_matches_script_v3':True,'speech_retimed':False,'speed_pitch_gain_changed':False,'source_audio_contains_existing_mix':True,'na_directory_mismatch':'audio/na/index.json is a different older script; not used','subtitle_rounding_max_s':max(abs(c['from']/30-c['source_start_s']) for c in sub)}
(O/'audio_recovery.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
