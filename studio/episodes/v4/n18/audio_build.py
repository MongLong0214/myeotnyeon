"""N18 documentary: existing Supertonic/trim/retake workflow, measured speech pace."""
from pathlib import Path
import sys,json,re,time,subprocess,hashlib
import numpy as np,soundfile as sf
from scipy.signal import resample_poly, butter,sosfilt
W=Path(__file__).resolve().parents[3]; E=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'episodes/S001'))
import tts as T
from supertonic import TTS
D=json.loads((E/'shots.json').read_text())
LEX=[('2024년 5월 23일','이천이십사년 오월 이십삼일'),('2024년 11월 12일','이천이십사년 십일월 십이일'),('2025년 1월 7일','이천이십오년 일월 칠일'),('2025년 6월 18일','이천이십오년 유월 십팔일'),('2025년 9월 25일','이천이십오년 구월 이십오일'),('5년 6개월','오 년 육 개월'),('10년','십 년'),('7년','칠 년'),('5년','오 년'),('3년','삼 년'),('6개월','육 개월'),('12사단','십이사단'),('6명','여섯 명'),('형사2부','형사이부'),('형사1부','형사일부'),('1심','일심'),('2심','이심')]
T.LEX=LEX+T.LEX
(E/'lex.json').write_text(json.dumps(LEX,ensure_ascii=False,indent=2))

def synth():
 tts=TTS(auto_download=False); style=tts.get_voice_style(voice_name='M1'); items=[]
 for it in D['narration']:
  f=E/'audio/na'/f"{it['id']}.wav"; raw=f.with_suffix('.raw.wav')
  if not f.exists():
   wav,_=tts.synthesize(T.tts_text(it['text']),voice_style=style,lang='ko',speed=1.0,total_steps=16)
   w=T.trim(np.asarray(wav,dtype=np.float32).reshape(-1),44100)
   sf.write(raw,resample_poly(w,160,147),48000,subtype='PCM_24')
   rate=(len(w)/44100)/(it['voice_frames']/30)
   # Preserve the approved timing using pitch-preserving, measured tempo adjustment.
   subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',f'atempo={rate:.8f}',str(f)],check=True)
   print(it['id'],'native_sps',round(it['syllables']/(len(w)/44100),3),'tempo',round(rate,4),flush=True)
  rawdur=sf.info(raw).duration if raw.exists() else sf.info(f).duration
  info=sf.info(f); items.append(dict(it,file=str(f.relative_to(E)),dur=info.duration,native_duration=rawdur,native_speed=1.0,tempo=rawdur/(it['voice_frames']/30),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
  (E/'audio/na/index.json').write_text(json.dumps(dict(voice='M1',speed=1.0,steps=16,model='Supertone/supertonic-3',items=items),ensure_ascii=False,indent=1))
 print('TOTAL',sum(x['dur'] for x in items),'s; syllables/s',D['narration_syllables']/sum(x['dur'] for x in items),flush=True)


def mix():
 sys.path.insert(0,str(W/'production/audio'))
 from synth import place,stereo,SR
 total=(D['duration_frames']+45)/30;n=round(total*SR); voice=np.zeros(n,dtype=np.float32)
 items=json.loads((E/'audio/na/index.json').read_text())['items'];margins=[]
 for it in items:
  x,sr=sf.read(E/it['file'],dtype='float32');assert sr==SR
  target=round(it['voice_frames']/30*SR)
  # A few resampler samples must not overlap the next sentence or its pause.
  x=x[:target]; rms=np.sqrt(np.mean(x*x));x*=10**(-21/20)/max(rms,1e-9)
  place(voice,x,round((it['t_start']+1.5)*SR))
  margins.append(dict(id=it['id'],voice_rms_dbfs=float(20*np.log10(np.sqrt(np.mean(x*x))))))
 rng=np.random.default_rng(18026);noise=rng.standard_normal(n,dtype=np.float32)
 air=sosfilt(butter(2,[90,2400],btype='band',fs=SR,output='sos'),noise).astype(np.float32)
 air/=np.sqrt(np.mean(air*air));air*=10**(-42/20)
 outdoors_end=round((46.4+1.5)*SR);air[:outdoors_end]*=10**(3/20)
 for s in D['shots']:
  if s['kind'] in ('chapter','silence','credits'):
   air[round((s['t_start']+1.5)*SR):round((s['t_end']+1.5)*SR)]=0
 air[:45*SR//30]=0
 effects=np.zeros(n,dtype=np.float32);events=[]
 chapter_times=[0]+[x['t_start']+1.5 for x in D['shots'] if x['kind']=='chapter']
 verdict_ids={'N034','N036','N052','N054','N059','N060'}
 for at,role,peak in [(t,'chapter',-34) for t in chapter_times]+[(x['t_start']+1.5,'verdict',-28) for x in items if x['id'] in verdict_ids]:
  nn=round(.8*SR);t=np.arange(nn)/SR;envelope=np.sin(np.linspace(0,np.pi,nn))**2
  tone=(np.sin(2*np.pi*50*t)*envelope*10**(peak/20)).astype(np.float32)
  place(effects,tone,round(at*SR));events.append(dict(start=at,duration=.8,role=role,waveform='50 Hz sine with sin² envelope',peak_dbfs=peak))
 # Intentional pre-verdict silence includes the room tone; no music anywhere.
 for s in D['shots']:
  if s['kind']=='silence':
   a,b=round((s['t_start']+1.5)*SR),round((s['t_end']+1.5)*SR)
   for arr in (air,effects,voice):arr[a:b]=0
 for it in items:
  a=round((it['t_start']+1.5)*SR);b=a+round(it['voice_frames']/30*SR)
  ar=np.sqrt(np.mean(air[a:b]**2));vr=np.sqrt(np.mean(voice[a:b]**2));margins[next(i for i,x in enumerate(items) if x['id']==it['id'])]['voice_over_ambience_db']=float(20*np.log10(vr/max(ar,1e-10)))
 for name,x in [('voice',voice),('ambience',air),('transitions',effects)]:sf.write(E/f'audio/stem_{name}.wav',x,SR,subtype='PCM_24')
 raw=E/'audio/mix_raw.wav';master=E/'audio/mix_master.wav'
 mono=voice+air+effects;sf.write(raw,np.stack([mono,mono],1),SR,subtype='FLOAT')
 p=subprocess.run(['ffmpeg','-hide_banner','-i',str(raw),'-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
 m=json.loads(p[p.rindex('{'):p.rindex('}')+1]);(E/'out/loudnorm-input.json').write_text(json.dumps(m,indent=2))
 af=f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',af,'-ar',str(SR),'-c:a','pcm_s24le',str(master)],check=True)
 import shutil
 pub=W/'production/compositor/public/v4n18';pub.mkdir(exist_ok=True);shutil.copy(master,pub/'mix_master.wav')
 (E/'out/audio_balance.json').write_text(json.dumps(dict(music=False,gag_sfx=False,minimum_voice_over_ambience_db=min(x['voice_over_ambience_db'] for x in margins),sentence_measurements=margins,events=events),indent=1))
 licences=dict(external_audio_files=[],procedural=[dict(file='audio/stem_ambience.wav',source='audio_build.py: seeded Gaussian noise, bandpass 90–2400 Hz',licence='Original procedural sound generated for this production; no third-party audio recording'),dict(file='audio/stem_transitions.wav',source='audio_build.py: original 50 Hz sine, 0.8 s sin² envelope',licence='Original procedural sound generated for this production; no third-party audio recording')],narration=dict(source='Existing local Supertone/supertonic-3 pipeline; M1',licence='OpenRAIL-M (existing model licence)',commercial_use=True),music=False)
 (E/'audio_licences.json').write_text(json.dumps(licences,ensure_ascii=False,indent=2))
 print('MIX COMPLETE',total,'seconds',flush=True)

if __name__=='__main__':
 if '--mix' in sys.argv: mix()
 else: synth()
