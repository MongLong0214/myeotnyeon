"""Compose the registered captions and contact recordings on a native 30 fps clock."""
import fcntl
import hashlib
import inspect
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

from recipe import FONTS, FPS, KIT, LIB, MUSIC, RECORDINGS, digest, read, save

sys.path.insert(0,str(KIT/'layout'))
from operative_captions import OperativeCaptions

STYLE = OperativeCaptions(FONTS/'Pretendard-Bold.otf',FONTS/'BlackHanSans-Regular.ttf')
RATE=48000


def compare_surface(base, before, frame, count, marker):
    ref_path,ref_marker=before
    if marker is None or ref_marker is None:
        raise ValueError('Registered comparison needs a visible common enamel landmark')
    with Image.open(ref_path) as image:
        old=image.convert('RGBA')
    w,h=base.size
    dx=(ref_marker['x']-marker['x'])*w/540
    dy=(ref_marker['y']-marker['y'])*h/960
    old=old.transform(base.size,Image.Transform.AFFINE,(1,0,dx,0,1,dy),Image.Resampling.BICUBIC)
    u=frame/max(1,count-1)
    fraction=max(0,min(1,(u-.14)/.64))
    edge=round(w*(1-fraction*fraction*(3-2*fraction)))
    if edge:
        base.alpha_composite(old.crop((0,0,edge,h)))
    if 0<edge<w:
        ImageDraw.Draw(base).line((edge,0,edge,h),fill=(255,223,163,255),width=max(1,w//270))
    return base


def comparison_frames(shots,shot,count,frames,settings):
    if not settings.get(shot,{}).get('compare_margin'):
        return {}
    ref_count=LIB['steps']['inspect_margin']['frames']
    indices={f:round(f*(ref_count-1)/(count-1)) for f in frames}
    path,_=shots.load('inspect_margin',ref_count,'audit',[])
    rows=read(path/'geometry.json')['frames']
    shots.load('inspect_margin',ref_count,'render',set(indices.values()))
    return {f:(path/f'{r:04}.png',rows[r]['leader']) for f,r in indices.items()}


def compose_frame(folder, f, count, caption, stage, marker, settings, before=None):
    with Image.open(folder/f'{f:04}.png') as im:
        base = im.convert('RGBA')
    if before:
        base=compare_surface(base,before,f,count,marker)
    lines = caption.split('|')
    # Hook phase continues from the last frame into the first across the loop.
    overlay = STYLE.overlay(lines, lines[-1], f/FPS, (count-f)/FPS, stage, None)
    scale = settings.get('caption_scale',1.)
    if scale != 1:
        box = overlay.getbbox()
        tile = overlay.crop(box)
        tile = tile.resize((round(tile.width*scale),round(tile.height*scale)),Image.Resampling.LANCZOS)
        overlay=Image.new('RGBA',overlay.size)
        overlay.alpha_composite(tile,((540-tile.width)//2,box[1]))
    if marker:
        STYLE.callout(overlay,marker)
    box=overlay.getbbox()
    if not box or box[0]<8 or box[1]<90 or box[2]>532 or box[3]>750:
        raise ValueError(('caption or leader outside safe zone',box))
    base.alpha_composite(overlay.resize(base.size,Image.Resampling.LANCZOS))
    return base.convert('RGB')


def mix_audio(path, segments, steps):
    frames=sum(end-start for _,start,end,*_ in segments)
    length=frames*(RATE//FPS)
    bed,sr=sf.read(MUSIC,dtype='float32',always_2d=True)
    width=RATE//2
    if sr!=RATE or len(bed)<length+width:
        raise ValueError('Score stem does not cover edit')
    out=bed[:length].copy()
    weight=(.5-.5*np.cos(np.linspace(0,np.pi,width)))[:,None]
    out[:width]=bed[length:length+width]*(1-weight)+out[:width]*weight
    power=[float(np.sqrt(np.mean(a*a))) for a in np.array_split(out,math.ceil(frames/3))]
    if min(power)<1e-5:
        raise ValueError('Missing music bed')
    cues=[]
    index=0
    for shot,start,end,*_ in segments:
        for ident,phase,offset,duration in steps.get(shot,{}).get('sfx',[]):
            count=steps[shot]['frames']
            local=round(phase*(count-1))
            if not start<=local<end:
                continue
            pos=(index+local-start)*(RATE//FPS)
            cmd=['ffmpeg','-v','error','-ss',str(offset),'-i',RECORDINGS/f'{ident}.mp3',
                 '-t',str(duration),'-ar',str(RATE),'-ac','2','-f','f32le','pipe:1']
            pcm=np.frombuffer(subprocess.check_output(cmd),dtype='<f4').reshape(-1,2).copy()
            if len(pcm)<round(duration*RATE)-64 or np.max(abs(pcm))<1e-5:
                raise ValueError(f'Missing recording at {ident} offset {offset}')
            pcm=pcm[:length-pos]
            fade=min(RATE//80,len(pcm)//2)
            pcm[:fade]*=np.linspace(0,1,fade)[:,None]
            pcm[-fade:]*=np.linspace(1,0,fade)[:,None]
            out[pos:pos+len(pcm)] += pcm * (.24/max(.02,float(np.max(abs(pcm)))))
            cues.append(dict(recording=ident,frame=index+local-start,source_in=offset,duration=duration))
        index+=end-start
    sf.write(path,out,RATE,subtype='PCM_24')
    return dict(cues=cues,minimum_music_rms=min(power),narration=False,samples=length,
                music_sha256=digest(MUSIC))


def geometry_errors(shot, rows):
    errors=[]
    for row in rows:
        f=row['f']
        if any(d[-1]>.2 for d in row['depths']):
            errors.append(f'{shot} f{f}: tool penetrates hard tissue beyond 0.2 mm')
        if shot in ('incise','crown_hook') and (row['tissue_gap'] is None or row['tissue_gap']>.2):
            errors.append(f'{shot} f{f}: scalpel misses gingiva')
        if shot in ('luxate','deliver_whole','extraction_hook') and (
                len(row['gaps'])!=2 or max(row['gaps'])>.2):
            errors.append(f'{shot} f{f}: forceps contact lost')
    if shot=='grasp' and rows and (len(rows[-1]['gaps'])!=2 or max(rows[-1]['gaps'])>.2):
        errors.append('grasp: either forceps beak misses its seated contact')
    return errors


def preflight(folder,tag,segments,shots,settings):
    from thresholds import T
    stills=folder/'gates'/(tag+'_stills')
    stills.mkdir(exist_ok=True,parents=True)
    errors=[]
    plan=[]
    cursor=0
    for shot,start,end,caption,stage in segments:
        spec=LIB['steps'].get(shot,{})
        count=spec.get('frames',60)
        path,_=shots.load(shot,count,'audit',[])
        rows=read(path/'geometry.json')['frames']
        errors.extend(geometry_errors(shot,rows[start:end]))
        cps=len(caption.replace('|','').replace(' ',''))/(count/FPS)
        wording=T['media_checks']['on_screen_wording']['banned']
        if cps>T['media_checks']['caption_reading_speed']['max_cps'] or any(w in caption for w in wording):
            errors.append(f'{shot}: caption violates reading or wording limit')
        samples=sorted({start,(start+end)//2,end-1,max(start,min(end-1,spec.get('thumbnail',start)))})
        shots.load(shot,count,'render',samples)
        comparison=comparison_frames(shots,shot,count,samples,settings)
        for f in samples:
            im=compose_frame(path,f,count,caption,stage,rows[f]['leader'],settings.get(shot,{}),comparison.get(f))
            im.save(stills/f'f_{cursor+f-start:04}.jpg',quality=95)
        plan.append((shot,start,end,caption,stage,count,path,rows))
        cursor+=end-start
    result=dict(tag=tag,errors=errors,frames=cursor,pass_stills=not errors,
                geometry=[str(p/'geometry.json') for *_,p,_ in plan])
    save(folder/'gates'/(tag+'_preflight.json'),result)
    return plan,result


def chunk_key(start,end,caption,stage,settings):
    # Audio fixes must preserve finished picture ranges.
    paint=inspect.getsource(compose_frame)+inspect.getsource(compare_surface)+inspect.getsource(comparison_frames)
    values=[start,end,caption,stage,settings,paint,digest(KIT/'layout/operative_captions.py')]
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()


def seam_master(audio):
    """Retain the music across the wrap while removing the codec's edge step."""
    pcm,rate=sf.read(audio,dtype='float32',always_2d=True)
    if rate!=RATE:
        raise ValueError('Unexpected source sample rate')
    # Offset the local waveform to a shared zero crossing. This keeps the
    # oscillation and synth bed audible on both sides of the splice.
    span=round(.012*RATE)
    taper=(.5+.5*np.cos(np.linspace(0,np.pi,span)))[:,None]
    pcm[:span]-=pcm[0].copy()*taper
    pcm[-span:]-=pcm[-1].copy()*taper[::-1]
    output=audio.with_name(audio.stem+'_seam.wav')
    sf.write(output,pcm,RATE,subtype='PCM_24')
    proc=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',output,'-af',
        'loudnorm=I=-14:TP=-1.8:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    measurements,_=json.JSONDecoder().raw_decode(proc.stderr[proc.stderr.rindex('{'):])
    gain=min(-14-float(measurements['input_i']),-1.8-float(measurements['input_tp']))
    return output,f'volume={gain:.4f}dB'


def assembly_signature(plan, settings, audio):
    return hashlib.sha256(json.dumps({
        'shots':[(shot,start,end,caption,stage,str(path)) for shot,start,end,caption,stage,_,path,_ in plan],
        'settings':settings,'audio':digest(audio),'compositor':digest(Path(__file__)),
        'layout':digest(KIT/'layout/operative_captions.py')},sort_keys=True).encode()).hexdigest()


def assemble(folder,tag,plan,shots,settings,audio):
    movie=folder/(tag+'.mp4')
    ledger=folder/'gates'/(tag+'_assembly.json')
    signature=assembly_signature(plan, settings, audio)
    previous=read(ledger) if ledger.is_file() else {}
    if previous.get('signature')==signature and movie.is_file() and digest(movie)==previous['sha256']:
        return movie
    chunks=[]
    receipt=[]
    for shot,start,end,caption,stage,count,path,rows in plan:
        comparison=comparison_frames(shots,shot,count,range(start,end),settings)
        _,rendered=shots.load(shot,count,'render',range(start,end))
        key=chunk_key(start,end,caption,stage,settings.get(shot,{}))
        chunk=path/(key+'.mp4')
        with chunk.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            if not chunk.exists():
                temp=chunk.with_suffix('.partial.mp4')
                w,h=shots.size
                cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}',
                     '-framerate','30','-i','pipe:0','-an','-c:v','libx264','-crf','16',
                     '-pix_fmt','yuv420p','-threads','3',temp]
                with subprocess.Popen(cmd,stdin=subprocess.PIPE) as enc:
                    for f in range(start,end):
                        im=compose_frame(path,f,count,caption,stage,rows[f]['leader'],settings.get(shot,{}),comparison.get(f))
                        enc.stdin.write(im.tobytes())
                    enc.stdin.close()
                    if enc.wait():
                        raise RuntimeError('Shot encode failed')
                temp.replace(chunk)
        chunks.append(chunk.resolve())
        receipt.append(dict(shot=shot,frames=end-start,rendered=rendered,range_sha256=digest(chunk)))
    concat=folder/(tag+'.ffconcat')
    concat.write_text(''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in chunks))
    movie=folder/(tag+'.mp4')
    temp=movie.with_suffix('.partial.mp4')
    frames=sum(r['frames'] for r in receipt)
    tone='loudnorm=I=-14:TP=-1.8:LRA=9'
    if settings.get('_audio',{}).get('phase_lock'):
        audio,tone=seam_master(audio)
    audio_filter=f'{tone},aresample={RATE},atrim=end_sample={frames*(RATE//FPS)},asetpts=N/SR/TB'
    subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',concat,'-i',audio,
                    '-map','0:v','-map','1:a','-c:v','copy','-af',audio_filter,
                    '-ar',str(RATE),'-c:a','aac','-b:a','192k','-movflags','+faststart',temp],check=True)
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',temp]))
    video,aac=info['streams']
    if video['r_frame_rate']!='30/1' or int(video['nb_frames'])!=frames or abs(float(aac['duration'])-frames/FPS)>.035:
        raise ValueError('Encoded clock or coverage changed')
    temp.replace(movie)
    if previous.get('sha256')==digest(movie):
        receipt=previous['ranges']
    save(ledger,dict(signature=signature,sha256=digest(movie),frames=frames,ranges=receipt))
    return movie
