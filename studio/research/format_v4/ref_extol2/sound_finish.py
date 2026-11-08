from analyze import *
import soundfile as sf
from scipy import signal
# Reuse extracted mixture; no new source/stem download.
y,sr=sf.read(R/'ref/analysis_audio_stereo.wav');m=y.mean(1);side=(y[:,0]-y[:,1])/2
words=list(csv.DictReader((R/'ref/words.csv').open()));voice=np.zeros(len(m),bool)
for w in words:voice[max(0,int((float(w['start'])-.06)*sr)):min(len(m),int((float(w['end'])+.06)*sr))]=True
def db(x):return float(20*np.log10(max(1e-10,np.sqrt(np.mean(x*x)))))
chap=json.loads((R/'chapters.json').read_text());cuts=list(csv.DictReader((R/'cuts.csv').open()));onsets=list(csv.DictReader((R/'reference_side_onsets.csv').open()));rows=[]
for c in chap:
 a,b=c['start_s'],c['end_s'];sl=slice(int(a*sr),min(len(m),int(b*sr)));v=voice[sl];rows.append({'section':c['name'],'start_s':a,'end_s':b,'mix_dbfs':db(m[sl]),'side_dbfs':db(side[sl]),'word_mix_dbfs':db(m[sl][v]) if v.any() else None,'nonword_mix_dbfs':db(m[sl][~v]) if (~v).any() else None,'side_minus_word_mix_db':db(side[sl])-db(m[sl][v]) if v.any() else None})
csvwrite(R/'sound_by_section.csv',rows)
cues=[]
for c in chap[1:]:
 t=c['start_s'];before=side[int((t-2)*sr):int(t*sr)];after=side[int(t*sr):int((t+2)*sr)];
 def spec(x):
  f,p=signal.welch(x,sr,nperseg=1024);return p/(p.sum()+1e-20)
 p,q=spec(before),spec(after);distance=float(np.sqrt(max(0,1-np.sqrt(p*q).sum())));delta=db(after)-db(before);cues.append({'time_s':t,'chapter':c['name'],'side_before_dbfs':db(before),'side_after_dbfs':db(after),'delta_db':delta,'spectral_hellinger':distance,'cue_change_candidate':abs(delta)>=6 or distance>=.35,'interpretation':'Measured stereo texture/level change; not confirmed music track switch.'})
csvwrite(R/'sound_cues.csv',cues)
reveals=[('outcome montage',10.067),('first victim trigger',118.867),('telephone isolation',263.52),('funeral hypothetical',347.32),('infant reveal',369.633),('grenade self-end',399.4),('police absence reveal',442.08),('police hiding accusation',465.133)]
rr=[]
for name,t in reveals:
 near=min(onsets,key=lambda x:abs(float(x['time_s'])-t));cut=min(cuts,key=lambda x:abs(float(x['time_s'])-t));rr.append({'reveal':name,'time_s':t,'nearest_side_onset_s':near['time_s'],'onset_minus_reveal_s':float(near['time_s'])-t,'nearest_cut_s':cut['time_s'],'cut_minus_reveal_s':float(cut['time_s'])-t,'event_status':'Semantic timestamp ~0.5s; no SFX identity or intention inferred.'})
csvwrite(R/'sound_reveal_alignment.csv',rr)
# Loudness metadata is from input fields, never the normalization output fields.
def loud(p):
 txt=p.read_text();st=txt.rfind('{');end=txt.find('}',st)+1;d=json.loads(txt[st:end]);return {'integrated_LUFS':float(d['input_i']),'true_peak_dBTP':float(d['input_tp']),'LRA_LU':float(d['input_lra']),'method':'ffmpeg loudnorm input measurement; original audio, no normalization saved'}
dump(R/'loudness.json',{'reference2':loud(R/'lufs.log'),'n18_fast':loud(R/'n18_lufs.log')});print(json.dumps(cues,ensure_ascii=False))
