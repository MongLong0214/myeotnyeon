"""Offline LF2 frame timing and audio analysis. Writes only cartoon_v4."""
from pathlib import Path
import json,subprocess,math,shutil,hashlib
import numpy as np
HERE=Path(__file__).resolve().parent
W=HERE.parents[2]
source=json.loads((HERE.parent/'shots_v1.json').read_text())
FPS=30
DURATION=source['duration_s']
FRAMES=math.ceil(DURATION*FPS)
# Full original voice remains byte-for-byte intact; audio mix gets a new licensed bed.
voice=HERE.parent/'audio/voice_full.wav'
shutil.copy2(voice,HERE/'public/voice_full.wav')
font=W/'production/compositor/node_modules/pretendard/dist/web/static/woff2/Pretendard-Bold.woff2'
shutil.copy2(font,HERE/'public/Pretendard-Bold.woff2')
raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(voice),'-f','f32le','-ac','1','-ar','24000','-'])
audio=np.frombuffer(raw,dtype='<f4'); pad=np.pad(audio,(0,FRAMES*800-len(audio)));chunks=pad.reshape(-1,800)
rms=np.sqrt(np.mean(chunks**2,axis=1)); envelope=np.clip((rms-.004)/.075,0,1)**.7
# Data-driven syllable anchors: weighted narration graphemes use the existing sentence
# boundaries, then snap within +/-40 ms to local energy peaks. This is an offline
# viseme approximation, not claimed forced phoneme alignment.
subs=[];speech=[{'amplitude':round(float(a),4),'viseme':'rest'} for a in envelope]
for cue in source['subtitles_full']:
 subs.append({'text':cue['text'],'startMs':cue['start_s']*1000,'endMs':cue['end_s']*1000,'timestampMs':cue['start_s']*1000,'confidence':None,'narrationId':cue['narration_id']})
 chars=[c for c in cue['text'] if '\uac00'<=c<='\ud7a3']
 if not chars: continue
 start=max(0,round(cue['start_s']*FPS));end=min(FRAMES,round(cue['end_s']*FPS))
 energy=np.maximum(rms[start:end]-.003,.001)**.35
 cumulative=np.cumsum(energy);cumulative/=cumulative[-1]
 for j in range(start,end):
  idx=min(len(chars)-1,int(cumulative[j-start]*len(chars)))
  code=ord(chars[idx])-0xac00;initial=code//588;vowel=(code%588)//28;final=code%28
  phase=(cumulative[j-start]*len(chars))%1
  if final in (1,2,7,16,17,18,19,20,22,23,24,25,26,27) and phase>.72: shape='M'
  elif initial in (6,7,8,17) and phase<.22: shape='M' if initial==6 else 'F'
  elif vowel in (8,9,10,11,12,13,14,15,16,17):shape='O'
  elif vowel in (1,3,5,7,19,20):shape='E'
  else:shape='A'
  speech[j]['viseme']=shape if envelope[j]>.045 else 'rest'
# Fill audible consonants outside the sentence caption intervals from local spectrum.
# This keeps the narrator mouth onset tied to the waveform even in subtitle gaps.
for i,fr in enumerate(speech):
 if fr['amplitude']>.045 and fr['viseme']=='rest':
  spectrum=np.abs(np.fft.rfft(chunks[i]*np.hanning(800)))**2
  freq=np.fft.rfftfreq(800,1/24000)
  high=float(spectrum[freq>3500].sum()/max(1e-12,spectrum.sum()))
  fr['viseme']='F' if high>.13 else 'E' if spectrum[(freq>1400)&(freq<3000)].sum()>spectrum[(freq>300)&(freq<1200)].sum() else 'A'
# Scene choices follow source facts. Every action is conceptual reconstruction;
# no incident dialogue or violence is enacted. Graphics have no body text.
plans=[
 [('parking','block'),('parking-reverse','approach'),('parking','reaction')],
 [('court','court'),('court','judge'),('court','verdict')],
 [('exterior','exterior'),('parking','staff')],
 [('parking-reverse','staff'),('parking','bags'),('parking-reverse','bags')],
 [('parking','depart'),('parking-reverse','depart'),('parking','empty')],
 [('parking','empty'),('parking-reverse','switch'),('getaway','car')],
 [('street','police'),('street','police'),('street','police')],
 [('street','police'),('street','police'),('investigation','records')],
 [('getaway','car'),('parking-reverse','car'),('parking','car')],
 [('evidence','evidence'),('evidence','mask'),('evidence','mask')],
 [('lab','lab'),('lab','dna'),('evidence','mask')],
 [('lab','dna'),('lab','links'),('lab','lab')],
 [('evidence','mask'),('evidence','archive')],
 [('evidence','archive'),('investigation','trace'),('investigation','timeline')],
 [('evidence','evidence'),('lab','lab'),('lab','dna')],
 [('lab','dna'),('lab','lab'),('lab','links')],
 [('arcade','arcade'),('arcade','cigarette'),('arcade','arcade')],
 [('evidence','mask'),('arcade','cigarette'),('lab','links')],
 [('lab','lab'),('lab','dna'),('investigation','trace')],
 [('investigation','crowd'),('investigation','trace'),('investigation','crowd')],
 [('investigation','crowd'),('investigation','clues'),('investigation','trace')],
 [('investigation','clues'),('getaway','car'),('investigation','trace')],
 [('investigation','clues'),('investigation','trace'),('investigation','crowd')],
 [('lab','dna'),('lab','identity'),('investigation','trace')],
 [('investigation','identity'),('investigation','links'),('investigation','trace')],
 [('investigation','trace'),('investigation','timeline'),('investigation','map')],
 [('evidence','archive'),('evidence','trace'),('evidence','archive')],
 [('investigation','map'),('investigation','statement'),('investigation','links')],
 [('spa','spa'),('spa','spa'),('investigation','links')],
 [('investigation','timeline'),('investigation','trace'),('investigation','interview')],
 [('investigation','interview'),('investigation','statement'),('investigation','trace')],
 [('court','court'),('court','statement'),('court','judge')],
 [('court','split'),('court','statement'),('court','judge')],
 [('investigation','statement'),('investigation','interview'),('investigation','statement')],
 [('investigation','statement'),('investigation','interview'),('court','judge')],
 [('court','timeline'),('court','court'),('court','judge')],
 [('court','court'),('court','judge'),('court','records')],
 [('court','records'),('court','timeline'),('court','judge')],
 [('court','court'),('court','split'),('court','judge')],
 [('court','judge'),('court','records'),('court','court')],
 [('court','statement'),('court','judge'),('court','records')],
 [('court','records'),('court','judge'),('court','court')],
 [('court','court'),('court','statement'),('court','judge')],
 [('court','court'),('court','statement'),('court','judge')],
 [('court','court'),('court','scale'),('court','judge')],
 [('court','timeline'),('court','verdict'),('court','judge')],
 [('court','judge'),('court','court'),('court','records')],
 [('court','records'),('court','scale'),('court','judge')],
 [('court','scale'),('court','judge'),('court','records')],
 [('court','records'),('court','scale'),('court','judge')],
 [('court','judge'),('court','scale'),('court','verdict')],
 [('court','court'),('court','records'),('court','judge')],
 [('court','records'),('court','scale'),('court','verdict')],
 [('court','split'),('court','judge'),('court','court')],
 [('court','judge'),('court','verdict'),('court','court'),('court','scale')],
 [('court','timeline'),('court','judge'),('court','verdict')],
 [('memorial','memorial'),('memorial','memorial'),('memorial','memorial')],
 [('investigation','trace'),('memorial','memorial'),('investigation','archive')],
 [('evidence','mask'),('lab','identity'),('investigation','links')],
 [('court','records'),('court','judge'),('court','verdict')]
]
assert len(plans)==len(source['narration'])
shots=[]
types=['wide','medium','close-up','over-the-shoulder','low-angle','high-angle','insert']
for ni,n in enumerate(source['narration']):
 start=round(n['start_s']*FPS);end=round(n['end_s']*FPS) if ni<len(plans)-1 else FRAMES
 count=max(2,math.ceil((end-start)/81));plan=plans[ni]
 boundaries=[round(start+(end-start)*j/count) for j in range(count+1)]
 if ni==0:boundaries=[0,30,105,179,240];plan=[('exterior','exterior'),('parking','block'),('parking-reverse','approach'),('parking','reaction')];count=4
 for j in range(count):
  setname,action=plan[min(j,len(plan)-1)];idx=len(shots)
  stype=types[(ni*2+j)%len(types)]
  if action in ('mask','dna','cigarette','links','crowd','clues','identity','map','records','scale','timeline'):stype='insert' if j%2 else 'medium'
  elif action=='judge':stype='close-up' if (ni+j)%2 else 'over-the-shoulder'
  elif action=='police':stype=['wide','close-up','medium'][j%3]
  elif action=='court':stype=['wide','over-the-shoulder','high-angle'][j%3]
  elif action=='memorial':stype=['wide','medium','insert'][j%3]
  elif action=='exterior':stype='wide'
  elif action=='lab':stype='close-up' if j%2==0 else 'medium'
  if stype=='close-up' and action not in ('reaction','police','lab','archive','trace','judge'):stype='medium'
  if stype=='over-the-shoulder' and action not in ('court','judge','reaction','spa'):stype='medium'
  if stype=='insert' and action not in ('mask','dna','cigarette','links','clues','identity','map','records','scale','timeline','memorial','crowd'):stype='medium'
  mood='courtroom' if setname=='court' else 'night' if setname=='street' else 'reflective' if setname=='memorial' else 'tense' if setname in ('parking','parking-reverse','getaway') else 'day'
  shots.append(dict(id=f'V4_{idx+1:03}',start=boundaries[j],end=boundaries[j+1],set=setname,type=stype,action=action,mood=mood,index=idx,variant=(1 if ni in (24,27,28,58) else 2) if action=='links' else ni%6,facts=n['facts'],narrationId=n['id'],purpose=f'{n["id"]} / {action}: {n["text"]}'))
# Boundary rounding is one presentation frame, narration is never retimed.
assert shots[0]['start']==0 and shots[-1]['end']==FRAMES
assert all(a['end']==b['start'] for a,b in zip(shots,shots[1:]))
assert max(s['end']-s['start'] for s in shots)<=90
out={'fps':FPS,'durationInFrames':FRAMES,'audioDuration':len(audio)/24000,'shots':shots,'captions':subs,'speech':speech,'narration':source['narration'],'voiceSha256':hashlib.sha256(voice.read_bytes()).hexdigest(),'visemeMethod':'Korean grapheme/vowel mapping within existing caption times, energy-weighted progression and per-frame RMS gate. Approximate, not forced phoneme alignment.'}
(HERE/'episode_data.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')))
(HERE/'shots.json').write_text(json.dumps(shots,ensure_ascii=False,indent=2))
# Music uses the locally licensed original with explicit voice sidechain. No SFX
# asset in W/assets is licensed, so none is synthesized or imported.
license_path=W/'assets/music/LICENSE.md'
shutil.copy2(license_path,HERE/'music_license.md')
print(json.dumps({'frames':FRAMES,'shots':len(shots),'maxShot':max((s['end']-s['start'])/30 for s in shots),'voice_s':len(audio)/24000,'captions':len(subs)}))
