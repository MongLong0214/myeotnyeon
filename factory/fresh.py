"""Spec + archived research -> new local Supertonic M1 audio and v52 inputs."""
from pathlib import Path
import ast,copy,importlib.util,json,math,re,shutil,subprocess,sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from short import W,S,save,load,sha,episode,run
sys.path.insert(0,str(W/'episodes/quiz'))
import make


def lexicon(ep):
    tree=ast.parse((W/'episodes/S001/tts.py').read_text())
    common=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LEX' for t in n.targets))
    return [*ep.get('lex',[]),*make.EXTRA_LEX,*common]


def normalizer(ep):
    from gates import legacy
    lex=lexicon(ep)
    def norm(text):
        clean=lambda s:re.sub(r'[^가-힣0-9A-Za-z]','',s)
        # Word-clock input joins ASR tokens; restore the metric unit even
        # when m is immediately followed by Hangul (11000m상공).
        text=re.sub(r'(?<=\d)\s*m(?=[가-힣\s,.!?]|$)','미터',text)
        text=clean(legacy.canon_numbers(text))
        for a,b in lex:text=text.replace(clean(legacy.canon_numbers(a)),clean(legacy.canon_numbers(b)))
        return legacy.norm(text)
    return norm


def trim(x,sr):
    win=round(sr*.005);n=len(x)//win
    rms=np.sqrt(np.mean(x[:n*win].reshape(-1,win)**2,axis=1));idx=np.where(rms>10**(-45/20))[0]
    if not len(idx):raise RuntimeError('Silent TTS take')
    x=x[max(0,(idx[0]-2)*win):min(len(x),(idx[-1]+3)*win)]
    n=len(x)//win;rms=np.sqrt(np.mean(x[:n*win].reshape(-1,win)**2,axis=1))
    edges=np.diff(np.r_[False,rms<10**(-45/20),False].astype(int));keep=np.ones(len(x),bool)
    for a,b in zip(np.where(edges==1)[0],np.where(edges==-1)[0]):
        if b-a>16:keep[(a+8)*win:b*win]=False
    return x[keep]


def prepare(p,q):
    from supertonic import TTS
    import mlx_whisper
    from gates import align_v51,legacy
    ep=episode(q);out=p/'prepared';out.mkdir();public=p/'public_assets';public.mkdir()
    shutil.copytree(W/'production/compositor/public/fonts',public/'fonts')
    sources=[]
    for sid in ep['sources']:
        matches=sorted((W/'research').glob(f'raw*/{sid}.txt'))
        if len(matches)!=1:raise RuntimeError(f'Expected one archived research source for {sid}: {matches}')
        sources.append(matches[0])
    save(p/'research.json',dict(sources=[dict(file=str(f.relative_to(W)),sha256=sha(f)) for f in sources],review_state='NEEDS_REVIEW'))
    hero_dir=p/'hero_build'
    print('Building new hero with existing Blender/world2 builder',flush=True)
    run(['/Applications/Blender.app/Contents/MacOS/Blender','--offline-mode','--factory-startup','-b','--python',S/'build_hero.py','--',q,hero_dir],p/'hero_build.log')
    (public/'hook_v51').mkdir();shutil.copyfile(hero_dir/f'{q}_raw.png',public/'hook_v51'/f'{"q013_clouds" if q=="q013" else q}.png')
    norm=normalizer(ep);lex=lexicon(ep)
    model=next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
    tts=TTS(auto_download=False,intra_op_num_threads=1,inter_op_num_threads=1);style=tts.get_voice_style('M1')
    records=[];waves=[];cur=0;items=[];subs=[];cues=[]
    # The shared caption chunker is code, never an episode's prepared layout.
    spec=importlib.util.spec_from_file_location('shared_layout',W/'episodes/S001/layout.py');layout=importlib.util.module_from_spec(spec);spec.loader.exec_module(layout)
    for cid,scene,lines,claims,pad,props in ep['cues']:
        cue_items=[]
        for k,line in enumerate(lines,1):
            text=line
            if not records:text=ep['hook']['narration']+' '+ep['hook'].get('ask','몇 년 받았을까?')
            spoken=text
            for a,b in lex:spoken=spoken.replace(a,b)
            if re.search('[0-9A-Za-z]',spoken):raise RuntimeError(f'Unmapped numeral: {spoken}')
            syll=len(re.findall('[가-힣]',spoken));speed=1.3;selected=None;best=None;auditioned=0
            for take in range(12):
                x,_=tts.synthesize(spoken,voice_style=style,lang='ko',speed=speed,total_steps=16,silence_duration=.08)
                x=resample_poly(trim(np.asarray(x,np.float32).reshape(-1),44100),160,147).astype(np.float32)
                rate=syll/(len(x)/48000);f=out/f'{cid}_{k}_take{take}.wav';sf.write(f,x,48000,subtype='PCM_24')
                if rate<7.5:
                    speed=float(np.clip(speed*math.sqrt(8.0/rate),.7,2));print(cid,k,'tune',rate,speed,flush=True);continue
                ar=mlx_whisper.transcribe(str(f),path_or_hf_repo=str(model),language='ko',temperature=0,condition_on_previous_text=False,word_timestamps=True)
                acc=1-legacy.cer(norm(text),norm(ar['text']));print(cid,k,'take',take,'sps',rate,'ASR',acc,ar['text'],flush=True)
                save(out/f'{cid}_{k}_take{take}_asr.json',ar)
                auditioned+=1
                if best is None or acc>best[0]:best=(acc,x,f,rate,speed)
                if acc>=.99:selected=(x,f,rate);break
                # Like v3 best-of-six, retain the best measured take rather than
                # accepting the first imperfect line. Full master/AAC still need .99.
                if auditioned>=6:break
            if selected is None and best is not None and best[0]>=.92:
                _,x,f,rate,speed=best;selected=(x,f,rate)
            if selected is None:raise RuntimeError(f'No passing M1 narration take: {cid}_{k}')
            x,f,rate=selected;start=cur/1600;end=(cur+len(x))/1600;sid=f'{cid}_{k}'
            rec=dict(id=sid,cue=cid,text=text,tts_text=spoken,syllables=syll,duration=len(x)/48000,sps=rate,engine_speed=speed,steps=16,voice='M1',resynthesized=True,file=str(f.relative_to(W)),source_sha256=sha(f),new_start_sample=cur,samples=len(x))
            records.append(rec);waves.append(x);it=dict(id=sid,cue=cid,text=text,start=start,end=end,start_sample=cur,end_sample=cur+len(x),file=rec['file']);items.append(it);cue_items.append(it);cur+=len(x)
            chunks=ep.get('split',{}).get(sid) or layout.chunks(line)
            if len(records)==1:chunks=[*chunks,ep['hook'].get('ask','몇 년 받았을까?')]
            if re.sub(r'\s','',''.join(chunks))!=re.sub(r'\s','',text):raise RuntimeError(f'Caption text mismatch {sid}')
            for chunk in chunks:subs.append(dict(from_=round(start),to=round(end),text=chunk))
        a={}
        cin=0 if not cues else round(cue_items[0]['start'])-4
        for k,it in enumerate(cue_items,1):a[f's{k}']=round(it['start'])-cin;a[f'e{k}']=round(it['end'])-cin
        cues.append(dict(id=cid,scene=scene,**{'from':cin},a=a,p=make.resolve(props,a)))
    n=max(660,math.ceil(items[-1]['start'])+45,math.ceil(cur/1600))
    for i,c in enumerate(cues):c['dur']=(cues[i+1]['from'] if i+1<len(cues) else n)-c['from']
    master=np.zeros((n*1600,2),np.float32);joined=np.concatenate(waves);master[:len(joined)]=joined[:,None]
    sf.write(out/'raw.wav',master,48000,subtype='PCM_24')
    # Two-pass loudness as the existing v3 mixer; speech remains M1 at natural rate.
    proc=subprocess.run(['ffmpeg','-hide_banner','-i',str(out/'raw.wav'),'-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    m=json.loads(proc.stderr[proc.stderr.rindex('{'):proc.stderr.rindex('}')+1])
    af=f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
    run(['ffmpeg','-v','error','-n','-i',out/'raw.wav','-af',af,'-ar','48000','-c:a','pcm_s24le',out/'mix_master.wav'],p/'normalize.log')
    audio=dict(episode=q,voice='M1',engine='Supertone/supertonic-3',reference=' '.join(r['text'] for r in records),items=records,all_lines_resynthesized=True,body_pcm_evidence=[],network=False)
    doc=dict(fps=30,durationInFrames=n,ep=dict(no=ep['no'],head=ep['head'],ask='몇 년 받았을까?',answerHead=ep['answerHead'],choices=ep.get('choices',make.CHOICES),answer=ep['answer'],source=ep['source'],hook={k:v for k,v in ep['hook'].items() if k in ['style','lines','ask','narration']}),cues=cues,subtitles=subs,audio=f'{q}/v52/mix_master.wav')
    ar=mlx_whisper.transcribe(str(out/'mix_master.wav'),path_or_hf_repo=str(model),language='ko',temperature=0,condition_on_previous_text=False,word_timestamps=True)
    save(out/'asr_master.json',ar);rows,acc=align_v51.align(doc,audio,ar,norm)
    fullacc=1-legacy.cer(norm(audio['reference']),norm(ar['text']))
    if fullacc<.99:raise RuntimeError(f'New master ASR below .99: {fullacc}; no render attempted')
    for sub,row in zip(doc['subtitles'],rows):sub['from_']=row['start'];sub['to']=row['end']
    for a,b in zip(doc['subtitles'],doc['subtitles'][1:]):a['to']=max(a['from_']+1,min(a['to'],b['from_']))
    save(out/'audio.json',audio);save(out/'timing.json',dict(items=items));save(out/'render.json',doc)
    pub=public/q/'v52';pub.mkdir(parents=True);shutil.copyfile(out/'mix_master.wav',pub/'mix_master.wav')
    return out,public,sources


def metadata(ep):
    title=ep.get('title') or ' '.join(ep['hook']['lines'])
    urls=[]
    for sid in ep['sources']:
        source=next((W/'research').glob(f'raw*/{sid}.txt'))
        match=re.search(r'^URL:\s*(https?://\S+)',source.read_text(),re.M)
        urls.append(f'{sid}: {match[1] if match else str(source.relative_to(W))}')
    description=' '.join(t for c in ep['cues'] if c[1]=='incident' for t in c[2])
    return ('[제목]\n'+title+' #형량퀴즈 #몇년나옴\n\n[설명]\n'+description+' '+ep['source']+'\n출처: '+' · '.join(urls)+
            '\n\n판결 보도를 바탕으로 재구성한 영상입니다. 실제 현장 영상이 아니며, 내레이션은 AI 음성 합성(Supertonic 3 M1)입니다.\n#몇년나옴 #형량퀴즈 #판결 #shorts\n\n[고정 댓글]\n여러분이 판사라면? 👇\n')
