"""Offline mixture measurements, not a music/SFX classifier or separated stems."""
import json, csv, subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy import signal

R=Path(__file__).resolve().parent
def scalar(x): return x.item() if isinstance(x,np.generic) else x
def dump(name,value): (R/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=scalar))
def csvout(name,rows):
    if not rows: return
    with (R/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def db(x): return float(20*np.log10(max(1e-10,np.sqrt(np.mean(np.square(x)))))) if len(x) else None
def runs(flags,step,minlen):
    changes=np.diff(np.r_[False,flags,False].astype(int)); a=np.where(changes==1)[0]; b=np.where(changes==-1)[0]
    return [{'start_s':round(x*step,3),'end_s':round(y*step,3),'duration_s':round((y-x)*step,3)} for x,y in zip(a,b) if (y-x)*step>=minlen]
def measure(label,src,boundaries,reveals):
    wav=R/(label+'_analysis.wav')
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(src),'-vn','-ar','16000','-ac','2',str(wav)],check=True)
    y,sr=sf.read(wav); m=y.mean(axis=1); side=(y[:,0]-y[:,1])/2; duration=len(m)/sr
    words=[w for s in json.loads((R/(label+'_transcript.json')).read_text())['segments'] for w in s.get('words',[]) if w['end']>w['start']]
    # ASR words are time-alignment estimates; gaps are not necessarily silence.
    speech=np.zeros(len(m),bool)
    for w in words: speech[max(0,int((w['start']-.06)*sr)):min(len(m),int((w['end']+.06)*sr))]=True
    frames=m[:len(m)//320*320].reshape(-1,320)
    energy=20*np.log10(np.maximum(1e-10,np.sqrt(np.mean(frames**2,axis=1))))
    silence=runs(energy < -60,.02,.18)
    pauses=[{'start_s':a['end'],'end_s':b['start'],'duration_s':round(b['start']-a['end'],3)} for a,b in zip(words,words[1:]) if b['start']-a['end']>=.35]
    f,t,z=signal.stft(side,sr,nperseg=1024,noverlap=704)
    mag=np.abs(z); flux=np.r_[0,np.maximum(0,np.diff(mag,axis=1)).sum(axis=0)]
    med=signal.medfilt(flux,51); mad=signal.medfilt(np.abs(flux-med),51)+1e-8
    score=(flux-med)/mad
    peaks,_=signal.find_peaks(score,height=8,distance=25,prominence=5)
    peaks=[i for i in peaks if flux[i]>np.percentile(flux,90) and db(side[max(0,int((t[i]-.05)*sr)):int((t[i]+.1)*sr)])>-50]
    onsets=[{'time_s':round(float(t[i]),3),'robust_flux_score':round(float(score[i]),2)} for i in peaks]
    # Also retain mono candidates, because a centered hit vanishes in the side channel.
    _,mt,mz=signal.stft(m,sr,nperseg=1024,noverlap=704)
    mm=np.abs(mz);mf=np.r_[0,np.maximum(0,np.diff(mm,axis=1)).sum(axis=0)]
    md=signal.medfilt(mf,51); ms=(mf-md)/(signal.medfilt(np.abs(mf-md),51)+1e-8)
    mp,_=signal.find_peaks(ms,height=8,distance=25,prominence=5)
    mono_onsets=[{'time_s':round(float(mt[i]),3),'robust_flux_score':round(float(ms[i]),2)} for i in mp if mf[i]>np.percentile(mf,90)]
    rows=[]
    for a in range(int(np.ceil(duration))):
        sl=slice(a*sr,min(len(m),(a+1)*sr)); ns=~speech[sl]
        powers=np.mean(mag[:,(t>=a)&(t<a+1)]**2,axis=1)
        def band(lo,hi): return round(float(10*np.log10(max(1e-20,powers[(f>=lo)&(f<hi)].sum()))),2)
        rows.append({'start_s':a,'end_s':min(a+1,duration),'mix_dbfs':db(m[sl]),'side_dbfs':db(side[sl]),'nonword_s':float(ns.sum()/sr),'nonword_mix_dbfs':db(m[sl][ns]),'nonword_side_dbfs':db(side[sl][ns]),'side_20_180_db':band(20,180),'side_180_4000_db':band(180,4000),'side_4000_8000_db':band(4000,8000)})
    # Side-channel energy suppresses centered narration. Stereo reverb/noise/SFX can remain.
    # Continuous >=5s side energy is evidence for a bed, not an isolated music measurement.
    flags=np.array([r['side_dbfs']>-50 for r in rows]); bed=runs(flags,1,5)
    cue=[]
    for b in boundaries:
        before=side[max(0,int((b-2)*sr)):int(b*sr)]; after=side[int(b*sr):min(len(side),int((b+2)*sr))]
        def spec(x):
            _,p=signal.welch(x,sr,nperseg=1024); return p/(p.sum()+1e-20)
        p,q=spec(before),spec(after)
        distance=float(np.sqrt(max(0,1-np.sqrt(p*q).sum())))
        delta=db(after)-db(before)
        cue.append({'boundary_s':b,'side_before_dbfs':db(before),'side_after_dbfs':db(after),'side_delta_db':delta,'spectral_hellinger':distance,'cue_change_candidate':bool(max(db(before),db(after))>-50 and (abs(delta)>=6 or distance>=.35)),'warning':'Candidate only; cannot establish track identity or editorial intent. Reject both sides below -50 dBFS to avoid numerical noise.'})
    hits=[]
    for event,at in reveals:
        near=[p for p in onsets if abs(p['time_s']-at)<=.75]
        hits.append({'event':event,'time_s':at,'side_onset_candidates':near,'mono_onset_candidates':[p for p in mono_onsets if abs(p['time_s']-at)<=.75],'interpretation':'A matching onset is not proof of an intentional reveal hit. Mono candidates may simply be consonants.'})
    summary={'duration_s':duration,'mixed_speech_dbfs':db(m[speech]),'mixed_nonword_dbfs':db(m[~speech]),'side_dbfs':db(side),'side_nonword_dbfs':db(side[~speech]),'continuous_side_bed_proxy_intervals':bed,'continuous_side_bed_proxy_share':sum(x['duration_s'] for x in bed)/duration,'nonword_windows_ge_120ms':sum(r['nonword_s']>=.12 for r in rows),'nonword_windows_with_side_above_minus50':sum(r['nonword_s']>=.12 and r['nonword_side_dbfs']>-50 for r in rows),'acoustic_silence_below_minus60_ge_180ms':silence,'narration_gaps_ge_350ms':pauses,'chapter_cue_candidates':cue,'reveal_hit_candidates':hits,'side_transient_candidate_count':len(onsets),'limitations':'No stem model downloaded. Side-channel and frequency-band measurements are stereo-bed evidence, not confirmed music coverage, composition identity, auditory emotion, or SFX counts. ASR can miss speech, particularly telephone insert.'}
    dump(label+'_audio_summary.json',summary); csvout(label+'_audio_1s.csv',rows); csvout(label+'_side_onsets.csv',onsets)
    print(label,json.dumps({k:v for k,v in summary.items() if k not in ['narration_gaps_ge_350ms','reveal_hit_candidates','chapter_cue_candidates']},ensure_ascii=False,default=scalar),flush=True)
    wav.unlink()

if __name__=='__main__':
    measure('reference',R/'reference.wav',[95.5,148,218.5,400.5],[("escape result",87.58),("gasgun fails",290.28),("repairman reports",416.66),("capture result",488.08)])
    measure('ours_fast',Path('episodes/v4/n18/out/n18_v4_type2_fast_preview_lowres.mp4'),[33.35,88.7,158.6,224.1],[("death result",23.72),("first sentence number",146.38),("appeal sentence number",226.98)])
