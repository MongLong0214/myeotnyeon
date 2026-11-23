"""Data-only authorship and feature-by-feature pairwise movie inspection."""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from recipe import HERE, KIT, LIB, WISDOM, digest, options, read, resolve, save

sys.path.insert(0, str(KIT))
from improvement_log import append, finding, locked, records, store

AXES = ('anatomy','materials','contact','framing','labels','motion','hook_loop','facts','audio')


def model_call(model, prompt, schema, folder, pictures=False):
    allowed = ['--tools','Read','--allowedTools','Read'] if pictures else ['--tools','']
    cmd = ['claude','-p','--model',model,'--output-format','json','--strict-mcp-config',
           '--no-session-persistence','--disable-slash-commands',*allowed,'--json-schema',json.dumps(schema)]
    proc = subprocess.run(cmd, cwd=folder, input=prompt, capture_output=True, text=True, timeout=2400)
    if proc.returncode:
        raise RuntimeError((proc.stderr or proc.stdout)[-1200:])
    env = json.loads(proc.stdout)
    if env.get('is_error') or not env.get('structured_output'):
        raise RuntimeError('Missing structured '+model+' result: '+str(env.get('result'))[-500:])
    return env['structured_output'], list(env['modelUsage']), env.get('total_cost_usd')


def author(folder, case):
    path = folder / 'author.json'
    if path.exists():
        existing=read(path)
        rows, fallback=resolve(case,existing['submitted'])
        if rows!=existing['steps'] or fallback!=existing['fallback']:
            raise ValueError('Saved recipe no longer matches the closed step library')
        return existing
    choices = options(case)
    fields = {k: {'type': 'integer' if k=='thumbnail' else 'string'} for k in choices[0][0]}
    schema = {'type':'object','additionalProperties':False,'required':['steps'],'properties':{'steps':{
        'type':'array','minItems':len(choices),'maxItems':len(choices),'items':{'type':'object',
        'required':list(fields),'additionalProperties':False,'properties':fields}}}}
    prompt = ('You alone author this Korean silent operative short. Select one complete row per ordered stage. '
              'Select the caption that makes the visible change clearest on a phone. Use only supplied choices. '
              +json.dumps([LIB['cases'][case],choices],ensure_ascii=False))
    start = time.time()
    episode, models, cost = model_call('sonnet',prompt,schema,folder)
    rows, fallback = resolve(case,episode)
    result = dict(steps=rows, submitted=episode, fallback=fallback, models=models,
                  cost_usd=cost, started=start, seconds=round(time.time()-start,2))
    save(path,result)
    return result


def sheet(movie, output, length, fps=2):
    n = max(1,round(length*fps+.49999))
    vf = f'fps={fps},scale=180:320,tile=6x{(n+5)//6}'
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',movie,'-vf',vf,
                    '-frames:v','1',output],check=True)


def compare(folder, tag, reference, ref_audit, segments, evidence):
    movie = folder/(tag+'.mp4')
    packet = folder/'gates'/('pair_'+tag)
    packet.mkdir(parents=True,exist_ok=True)
    path = packet/'opus.json'
    inputs = [digest(movie),digest(reference),digest(ref_audit)]
    if path.exists():
        result=read(path)
        if result['sha256']!=inputs:
            raise ValueError('Pairwise review belongs to different bytes')
        return result
    seconds = sum(end-start for _,start,end,*_ in segments)/30
    from fractions import Fraction
    from quality import playback
    for source,name,duration in [(movie,'candidate',seconds),(reference,'reference',None)]:
        if duration is None:
            info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
                       '-show_entries','stream=nb_frames,r_frame_rate','-of','json',source]))['streams'][0]
            fps=float(Fraction(info['r_frame_rate']))
            frames=int(info['nb_frames'])
            duration=frames/fps
            save(packet/'reference_audio.json',playback(source,frames,fps))
        sheet(source,packet/(name+'.jpg'),duration)
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',source,'-filter_complex',
                        'aformat=channel_layouts=stereo,showwavespic=s=960x144:colors=orange:split_channels=1',
                        '-frames:v','1',packet/(name+'_wave.png')],check=True)
    # Inspect the working region at native crop size and sample short transients
    # between the wide-sheet images. The previous Fable packet already contains
    # the original reference crops.
    original_packet=ref_audit.parent/('review_'+ref_audit.name.removesuffix('_review_fable.json'))
    for pic in sorted(original_packet.glob('still_f*.png'))[::3]:
        shutil.copyfile(pic,packet/('ref_'+pic.name))
    cursor=0
    for shot,start,end,*_ in segments[:-1]:
        f=cursor+(end-start)//2
        subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{f/30:.6f}','-i',movie,'-frames:v','1',
                        packet/f'{shot}_f{f}.png'],check=True)
        cursor+=end-start
    for name,p in evidence.items():
        shutil.copyfile(p,packet/name)
    old_measurements = ref_audit.parent/('review_'+ref_audit.name.removesuffix('_review_fable.json'))/'measurements.json'
    if old_measurements.exists():
        shutil.copyfile(old_measurements,packet/'reference_playback.json')
    axis = {'type':'object','required':['verdict','shot','class','evidence'],'properties':{
        'verdict':{'enum':['worse','equal','better','unverified']},
        'shot':{'enum':list(dict.fromkeys(s[0] for s in segments))+['episode']},
        'class':{'type':'string'},'evidence':{'type':'string','minLength':1}}}
    schema = {'type':'object','required':list(AXES),'properties':{key:axis for key in AXES}}
    prompt = ((KIT/'rubric.md').read_text()+'\nPairwise diagnostic. Open both image sheets (2 fps, 6 columns, '
        'left to right) and every evidence file listed below. Which cut is worse on each axis? Judge the '
        'candidate relative to the reference. Cite the candidate time and what is visible. Both are silent-caption '
        'operatives with recorded Foley and continuous music. Compare measurements for audio, distinguish the '
        'limits of listening. Each class should describe the actual problem. Use framing-too-tight, focus-soft, '
        'caption-crowded, contact-hidden, surface-waxy (enamel or gingiva has a uniformly synthetic sheen), '
        'socket-obscured (delivered tooth still blocks the socket payoff), '
        'or before-after-unclear (the change in exposed crown cannot be compared) only when directly warranted. Name other defects specifically. '
        'Report visible comparative strengths as well as defects. The two decoded waveforms, peak, '
        'short-window RMS and seam measurements allow an objective audio comparison. Report limits for '
        'properties that require listening.\n'+str(segments)+'\nFiles: '+
        ', '.join(p.name for p in packet.iterdir()))
    axes,models,cost = model_call('opus',prompt,schema,packet,True)
    if set(axes)!=set(AXES):
        raise ValueError('Incomplete comparator')
    result=dict(sha256=inputs,models=models,cost_usd=cost,axes=axes,
                pass_pair=all(a['verdict'] in ('better','equal') for a in axes.values()))
    save(path,result)
    return result


def repairs(folder,tag,result,settings,shots):
    settings = {k:v.copy() for k,v in settings.items()}
    tickets=[]
    mapped=[]
    for axis,item in result['axes'].items():
        if item['verdict'] not in ('worse','unverified'):
            continue
        key=item['class']
        setting={'framing-too-tight':('distance',1.25),'focus-soft':('fstop',75),'surface-waxy':('tissue_surface',True),
                 'material-reads-as-clay-wax-plastic-concrete':('tissue_surface',True),
                 'caption-crowded':('caption_scale',.82),'contact-hidden':('azimuth',-12)}.get(key)
        affected=shots if item['shot']=='episode' else [item['shot']]
        if key=='socket-obscured' and 'socket_payoff' in shots:
            setting,affected=('empty_socket',True),['socket_payoff']
        if key=='before-after-unclear' and 'margin_payoff' in shots:
            setting,affected=('compare_margin',True),['margin_payoff']
        changes=[]
        if setting:
            for shot in affected:
                params=settings.setdefault(shot,{})
                if params.get(setting[0])!=setting[1]:
                    params[setting[0]]=setting[1]
                    changes.append(shot)
        (mapped if changes else tickets).append(key)
        append([finding(folder.name,'opus',item['evidence'],'blocking',item['shot'],
                 str(folder/'gates'/('pair_'+tag)/'opus.json')+'#'+axis,
                 edition=tag,media=str(folder/(tag+'.mp4')),kind='observation' if changes else 'template_ticket',
                 template='operative',repair=setting if changes else None,owner='Astra',finding_class=key)])
    return settings, mapped, tickets


def flag_audit_tickets(audit):
    # capture_run already owns these exact findings. Assign them in place so
    # the nightly recurrence counter sees each observed defect only once.
    source=str(audit.resolve())
    with locked():
        rows=records()
        for row in rows:
            if row.get('source')=='fable' and row.get('ref','').split('#')[0]==source:
                row.update(owner='Astra',template='operative')
                if row['description'].startswith('review could not verify '):
                    row['kind']='observation'
                else:
                    row.update(kind='template_ticket',template_ticket=True)
        store(rows)
