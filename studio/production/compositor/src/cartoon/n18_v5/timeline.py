"""Build character-first cuts, sample-exact voice master and local score."""
from pathlib import Path
import json,re,math,shutil,hashlib
import numpy as np,soundfile as sf
W=Path(__file__).resolve().parents[5];S=Path(__file__).parent;O=W/'episodes/v4/n18/cartoon_v5'

STAGING={
 'host':('narrator','eye dart / recoil / jaw drop / accusatory palm / double take; editorial satire'),
 'ground':('recruits','wide or rear view; six anonymous recruits march, arms and legs cycle; no singled-out victim, no distress or fall'),
 'barracks':('recruits','rear-view collective turns and reaches; no invented event dialogue'),
 'command':('commanders','faceless commander and deputy; illustrative arm pivots, weight shifts and head turns, never invented quotation'),
 'investigation':('investigator','investigator reads, flips a page, compares and reacts; illustrative investigation'),
 'hospital':('medics','anonymous medics hurry past closed hospital doors; no patient, collapse or treatment visible'),
 'transport':('medics','medic silhouette gestures toward moving unmarked transport; no patient, invented route or ambulance siren'),
 'letter':('narrator','narrator reads a symbolic letter; mother is not impersonated; no voice clone or reenacted conversation'),
 'memorial':('mourners','unidentifiable rear-view mourners lower heads and place symbolic flowers; no caricature or pain performance'),
 'witness':('witness','anonymous rear-view witness raises a hand and turns toward bench; no invented speech'),
 'prosecution':('prosecutor','generic faceless prosecutor gestures and opens a folder; numbers kept with the correct defendant'),
 'defendant':('commanders','faceless commander and deputy; restrained illustrative head and arm motion'),
 'court':('court','non-identifiable judge, clerk and defendant silhouettes; page turn, bench gesture, reaction cut; no fake event dialogue'),
 'reform':('investigator','illustrative investigator and medic demonstrate hearing/checking/readiness; no claim of observed implementation'),
}
INSERTS={'N017':'books','N023':'clock','N029':'clock','N036':'certificate','N054':'sentence','N056':'sentence','N071':'sentence','N076':'sentence','N081':'date'}

def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2))

def main():
    script=json.loads((O/'script.json').read_text()); meta=json.loads((O/'audio.json').read_text())
    assert len(meta['items'])==len(script['lines'])
    public=O/'public';public.mkdir(exist_ok=True);(O/'qa').mkdir(exist_ok=True)
    shutil.copyfile(W/'production/compositor/public/fonts/Pretendard-Bold.woff2',public/'Pretendard-Bold.woff2')
    pieces=[];narration=[];shots=[];pos=0;gap=1920
    for k,row in enumerate(meta['items']):
        w,sr=sf.read(O/row['file']);assert sr==48000
        start=pos;pieces.append(w);pos+=len(w)
        item=dict(row,start_sample=start,end_sample=pos,start_s=start/sr,end_s=pos/sr,start=round(start/sr*30),end=round(pos/sr*30))
        narration.append(item)
        if k<len(meta['items'])-1:pieces.append(np.zeros(gap));pos+=gap
        st=round(start/sr*30);en=round(pos/sr*30)
        insert=INSERTS.get(row['id']); ilen=24 if insert else 0
        stop=en-ilen
        cuts=max(1,math.ceil((stop-st)/48))
        for j in range(cuts):
            a=round(st+(stop-st)*j/cuts);b=round(st+(stop-st)*(j+1)/cuts)
            # Alternating inserts never dominate. Narrator cutaways are acting too.
            stage=row['stage'] if j%3!=2 else 'host'
            actor,acting=STAGING[stage];i=len(shots)
            shots.append(dict(id=f'F{i+1:03d}',start=a,end=b,narration_id=row['id'],stage=stage,actor=actor,acting_character=True,acting=acting,shot_type=['wide','medium','close','low','rear','dutch','profile'][i%7],camera=['whip','crash','snap','dutch','push','snap'][i%6],variant=i%6,chapter=row['chapter'],facts=row['facts'],insert=False,cliffhanger=row['cliffhanger'] and j==cuts-1,illustrative=True))
        if insert:
            i=len(shots);shots.append(dict(id=f'F{i+1:03d}',start=stop,end=en,narration_id=row['id'],stage=insert,actor=None,acting_character=False,acting=None,shot_type='insert',camera='crash',variant=i%6,chapter=row['chapter'],facts=row['facts'],insert=True,cliffhanger=False,illustrative=True))
    voice=np.concatenate(pieces)
    frames=math.ceil(len(voice)/48000*30);voice=np.pad(voice,(0,frames*1600-len(voice)))
    shots[-1]['end']=frames
    sf.write(public/'narration.wav',voice,48000,subtype='PCM_24')
    # Deterministic original 146 BPM electronic score; drums, bass, arp and stings.
    # Each sound is synthesized locally below. No external samples or melody.
    rng=np.random.default_rng(1805);music=np.zeros(len(voice));fx=np.zeros(len(voice));bpm=146;beat=60/bpm
    def put(buf,t,w,volume=1):
        a=int(t*48000);b=min(len(buf),a+len(w))
        if a<0 or a>=len(buf):return
        buf[a:b]+=w[:b-a]*volume
    def kick():
        t=np.arange(int(.20*48000))/48000;return np.sin(2*np.pi*(42*t+8*(1-np.exp(-30*t))))*np.exp(-23*t)*.45
    def hat():
        n=int(.06*48000);t=np.arange(n)/48000;z=rng.normal(0,1,n);return (z-np.roll(z,1))*np.exp(-80*t)*.045
    def snare():
        t=np.arange(int(.13*48000))/48000;return (rng.normal(0,1,len(t))*.14+np.sin(2*np.pi*180*t)*.11)*np.exp(-35*t)
    def note(hz,length=.22):
        t=np.arange(int(length*48000))/48000;return (np.sin(2*np.pi*hz*t)+.24*np.sin(4*np.pi*hz*t))*np.exp(-12*t)*np.minimum(t*150,1)
    def whoosh(length=.10):
        t=np.arange(int(length*48000))/48000;n=rng.normal(0,1,len(t));return (n-np.roll(n,1))*np.sin(np.pi*t/length)**2*.10
    bases=[55,55,65.406,49];dur=len(voice)/48000
    for b in range(math.ceil(dur/beat)):
        tm=b*beat
        current=next((n for n in narration if n['start_s']<=tm<n['end_s']),narration[-1])
        reflective=current['stage'] in ['memorial','letter','witness']
        level=.18 if reflective else .52
        if not reflective or b%2==0:put(music,tm,kick(),level)
        if b%4 in (1,3) and not reflective:put(music,tm,snare(),level)
        if not reflective:
            put(music,tm,hat(),level);put(music,tm+beat/2,hat(),level*.8)
        base=bases[(b//16)%4]
        put(music,tm,note(base,.32),.1 if reflective else .17)
        if b%2==0:put(music,tm+beat/2,note(base*2**([0,7,10,12][(b//2)%4]/12)*4),.012 if reflective else .032)
    for sh in shots:
        t=sh['start']/30
        # No comedy hits in bereavement or medical beats.
        if sh['stage'] in ['memorial','letter','witness','hospital','transport']:continue
        if sh['camera']=='whip':put(fx,t,whoosh(),.20)
        if sh['camera']=='crash':put(fx,t,kick(),.15)
        if sh['cliffhanger']:
            put(fx,t,note(330,.24),.042);put(fx,t+.10,note(415.3,.24),.032)
    # Voice-driven continuous ducking, no slow release hiding the next line.
    hop=480;aa=np.pad(voice,(0,(-len(voice))%hop)).reshape(-1,hop)
    rms=np.sqrt(np.mean(aa*aa,axis=1));duck=np.repeat(np.where(rms>.009,.50,.85),hop)[:len(voice)]
    bed=music*duck
    mixed=voice+bed+fx
    gain=min(1,.88/max(np.max(np.abs(mixed)),1e-8));mixed*=gain
    stereo=np.stack([mixed+bed*.025,mixed-bed*.025],axis=1)
    sf.write(public/'mix.wav',stereo,48000,subtype='PCM_24');sf.write(O/'music.wav',music,48000,subtype='PCM_24');sf.write(O/'sfx.wav',fx,48000,subtype='PCM_24')
    # Temporary captions; replaced by ASR aligned ones before final render.
    captions=[]
    for n in narration:
        parts=re.findall(r'.{1,24}(?:\s|$)',n['text'])
        if not parts:parts=[n['text']]
        # Preserve every character while splitting on words.
        parts=[];line=''
        for w in n['text'].split():
            if len(line+' '+w)>24 and line:parts.append(line);line=w
            else:line=(line+' '+w).strip()
        if line:parts.append(line)
        weights=[len(re.sub(r'\s','',p)) for p in parts];total=sum(weights);used=0
        for p,weight in zip(parts,weights):
            a=n['start']+round((n['end']-n['start'])*used/total);used+=weight;b=n['start']+round((n['end']-n['start'])*used/total)
            captions.append(dict(start=a,end=b,text=p,narration_id=n['id'],alignment='provisional proportional; final ASR word alignment pending'))
    data=dict(fps=30,width=1920,height=1080,durationInFrames=frames,narration=narration,shots=shots,captions=captions,voice='M1',red_lines=script['red_lines'])
    dump(O/'shots.json',data);dump(S/'data.json',data)
    (O/'shot_list.md').write_text('# N18 v5 · character acting shots\n\nAll sets and actions are illustrative. No documentary blocking or dialogue is asserted. The source-backed second officer is 부중대장. Only rear/wide anonymous recruits; no collapse, patient or death. Insert duration 0.8 s.\n\n| Cut | Time | Stage / character | Acting | Camera | Facts |\n|---|---|---|---|---|---|\n'+'\n'.join(f"| {s['id']} | {s['start']/30:.3f}–{s['end']/30:.3f} | {s['stage']} / {s['actor'] or 'none'} | {s['acting'] or 'animated insert'} | {s['camera']} / {s['shot_type']} | {', '.join(s['facts'])} |" for s in shots))
    dump(O/'audio_manifest.json',dict(voice='Supertonic 3 M1; local cached weights; OpenRAIL-M in /tts/LICENSE_supertonic3.txt',music='Original locally synthesized 146 BPM score; no samples; source timeline.py',sfx='Original deterministic noise/sine percussion and whooshes; source timeline.py',ducking='10 ms RMS from narration; .5 active / .85 quiet',gain=gain,peak=float(np.max(np.abs(stereo))),network=False,uploads=False))
    print('runtime',frames/30,'s; cuts',len(shots),'acting',sum(s['acting_character'] for s in shots),'syllables/s',sum(n['syllables'] for n in narration)/(frames/30),flush=True)
if __name__=='__main__':main()
