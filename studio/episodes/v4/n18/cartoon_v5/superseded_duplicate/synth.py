"""Local Supertonic 3 M1. Offline, resumable, capped pauses, measured tempo."""
from pathlib import Path
import os,json,re,subprocess,hashlib,sys,time
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
from supertonic import TTS
W=Path(__file__).resolve().parents[5]; O=W/'episodes/v4/n18/cartoon_v5'
S=json.loads((O/'script.json').read_text()); A=O/'audio';A.mkdir(exist_ok=True)
RATE=48000;TARGET=8.65

def cap_quiet(w,sr,maximum=.085):
    hop=int(sr*.005);q=len(w)//hop
    rms=np.sqrt(np.mean(w[:q*hop].reshape(-1,hop)**2,axis=1))
    active=rms>10**(-46/20)
    ix=np.where(active)[0]
    if not len(ix):raise ValueError('TTS produced silence')
    first=max(0,(ix[0]-3)*hop);last=min(len(w),(ix[-1]+4)*hop)
    w=w[first:last];q=len(w)//hop
    rms=np.sqrt(np.mean(w[:q*hop].reshape(-1,hop)**2,axis=1));quiet=rms<=10**(-46/20)
    edges=np.diff(np.r_[False,quiet,False].astype(int));runs=list(zip(np.where(edges==1)[0],np.where(edges==-1)[0]))
    remove=[]
    for a,b in runs:
        if (b-a)*hop/sr>maximum:
            keep=int(maximum*sr/2)
            remove.append((a*hop+keep,b*hop-keep))
    chunks=[];p=0
    for a,b in remove:chunks.append(w[p:a]);p=b
    chunks.append(w[p:]);w=np.concatenate(chunks)
    fade=min(int(.003*sr),len(w)//10)
    w[:fade]*=np.linspace(0,1,fade);w[-fade:]*=np.linspace(1,0,fade)
    return w

def synthesize(tts,style,row,take=0):
    rid=row['id']; raw=A/f'{rid}_raw_{take}.wav'; dest=A/f'{rid}.wav'
    spoken=row['tts_text'];syll=len(re.findall('[가-힣]',spoken))
    speed=1.3 if take<2 else 1.2
    wav,_=tts.synthesize(spoken,voice_style=style,lang='ko',speed=speed,total_steps=24 if take else 16)
    w=cap_quiet(np.asarray(wav,dtype=np.float32).reshape(-1),44100)
    w=resample_poly(w,160,147).astype(np.float32)
    sf.write(raw,w,RATE,subtype='PCM_24')
    ratio=(len(w)/RATE)/(syll/TARGET)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',f'atempo={ratio:.9f}',str(dest)],check=True)
    z,_=sf.read(dest);z=cap_quiet(z,RATE)
    # Set consistent forward delivery without clipping.
    rms=np.sqrt(np.mean(z*z));z=z*min(.15/max(rms,1e-6),.9/max(np.max(np.abs(z)),1e-6))
    sf.write(dest,z,RATE,subtype='PCM_24')
    dur=len(z)/RATE
    return dict(row,file=f'audio/{rid}.wav',syllables=syll,duration_s=dur,sps=syll/dur,voice='M1',engine_speed=speed,steps=24 if take else 16,take=take,atempo=ratio,sha256=hashlib.sha256(dest.read_bytes()).hexdigest())

def main():
    selected=set(sys.argv[1].split(',')) if len(sys.argv)>1 else None
    path=O/'audio.json';old=json.loads(path.read_text()) if path.exists() else {'items':[]}
    records={r['id']:r for r in old['items']}
    tts=TTS(auto_download=False,intra_op_num_threads=2,inter_op_num_threads=1);style=tts.get_voice_style('M1')
    for row in S['lines']:
        if selected and row['id'] not in selected:continue
        prev=records.get(row['id'])
        if prev and not selected and prev['text']==row['text'] and (O/prev['file']).exists():continue
        row=synthesize(tts,style,row,0 if prev is None else prev['take']+1);records[row['id']]=row
        items=[records[r['id']] for r in S['lines'] if r['id'] in records]
        path.write_text(json.dumps({'model':'Supertone/supertonic-3','voice':'M1','offline':True,'target_sps':TARGET,'silence_cap_s':.085,'items':items},ensure_ascii=False,indent=2))
        print(row['id'],round(row['duration_s'],3),round(row['sps'],2),'take',row['take'],flush=True)
    print('complete',len(records),'total',sum(r['duration_s'] for r in records.values()),flush=True)
if __name__=='__main__':main()
