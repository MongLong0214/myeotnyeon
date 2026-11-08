"""Render only the two LF2 representative clips with frozen cue audio."""
import hashlib, json, math, shutil, subprocess
from pathlib import Path

BLENDER='/Applications/Blender.app/Contents/MacOS/Blender'
ROOT=Path('.')
PROD=ROOT/'production/astra_12min/action_revision'
RENDERER=PROD/'lf2_representative_renderer.py'
OUT=ROOT/'episodes/lf2_daejeon_bank/astra_12min'
TARGETS={'lf2_court':'lf2_court_cues.json','lf2_event':'lf2_event_cues.json'}

def run(cmd): subprocess.run(cmd, check=True)
def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
def dur(path): return float(probe(path)['format']['duration'])
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def render(name, cue_file):
    cp=OUT/cue_file; clip=json.loads(cp.read_text()); final=OUT/f'{name}_LF2_ACTION_V3_426x240.mp4'
    clips=[]; actual=[]; offset=0.0
    for i,cue in enumerate(clip['cues']):
        frames=OUT/'lf2_v3_frames'/cue['id']; expected=math.ceil((cue['end']-cue['start'])*12)
        # Clear this candidate's per-cue frames so stale frame counts cannot satisfy validation.
        if frames.exists(): shutil.rmtree(frames)
        run([BLENDER,'-b','-t','2','--python',str(RENDERER),'--',str(cp),str(i)])
        count=len(list(frames.glob('frame_*.png')))
        if count != expected: raise RuntimeError((cue['id'],count,expected))
        part=OUT/f'{cue["id"]}_LF2_ACTION_V3.mp4'
        run(['ffmpeg','-y','-v','error','-framerate','12','-i',str(frames/'frame_%04d.png'),'-i',cue['audio'],
             '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-shortest',str(part)])
        d=dur(part); clips.append(part)
        actual.append({'id':cue['id'],'action':cue['action'],'text':cue['text'],'audio':cue['audio'],'audio_sha256':sha(Path(cue['audio'])),'cue_duration':cue['end']-cue['start'],'delivered_start':offset,'delivered_end':offset+d,'delivered_duration':d,'frames':count,'video':str(part)})
        offset+=d
    concat=OUT/f'{name}_LF2_ACTION_V3.concat.txt'; concat.write_text(''.join("file '"+str(p)+"'\n" for p in clips))
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(final)])
    run(['ffmpeg','-v','error','-i',str(final),'-f','null','-'])
    evidence=OUT/'lf2_v3_review_frames'; evidence.mkdir(exist_ok=True)
    extracts=[]; image_paths=[]
    for item in actual:
        span=item['delivered_end']-item['delivered_start']
        for phase,ratio in [('start',.04),('contact',.34),('middle',.58),('end',.92)]:
            t=item['delivered_start']+span*ratio
            png=evidence/f'{name}_{item["id"]}_{phase}.png'
            run(['ffmpeg','-y','-v','error','-ss',f'{t:.6f}','-i',str(final),'-frames:v','1',str(png)])
            extracts.append({'cue':item['id'],'phase':phase,'time':t,'path':str(png)})
            image_paths.append(png)
    # A durable 4×4 JPG contact sheet; each tile maps to the ordered manifest extracts list.
    sheet=OUT/f'{name}_LF2_ACTION_V3_review_sheet.jpg'
    cmd=['ffmpeg','-y','-v','error']
    for p in image_paths: cmd += ['-i',str(p)]
    cmd += ['-filter_complex',''.join(f'[{i}:v]scale=426:240[v{i}];' for i in range(len(image_paths))) + ''.join(f'[v{i}]' for i in range(len(image_paths)))+'xstack=inputs=16:layout=0_0|426_0|852_0|1278_0|0_240|426_240|852_240|1278_240|0_480|426_480|852_480|1278_480|0_720|426_720|852_720|1278_720','-frames:v','1',str(sheet)]
    run(cmd)
    record={'candidate':'LF2_ACTION_V3','path':str(final),'sha256':sha(final),'resolution':'426x240','full_decode':True,'probe':probe(final),'cues':actual,'extracts':extracts,'review_sheet':str(sheet),'review_order':'For each cue in sequence: start, contact, middle, end.','cue_audio_preserved':all(x['audio_sha256']==next(c['sha256'] for c in clip['cues'] if c['id']==x['id']) for x in actual)}
    manifest=OUT/f'{name}_LF2_ACTION_V3_manifest.json'; manifest.write_text(json.dumps(record,ensure_ascii=False,indent=2))
    return record,manifest

all_records=[]
for name,cf in TARGETS.items():
    r,m=render(name,cf); all_records.append({'name':name,'manifest':str(m),'path':r['path'],'duration':r['probe']['format']['duration'],'sha256':r['sha256']})
master=OUT/'LF2_ACTION_V3_manifest.json'; master.write_text(json.dumps(all_records,ensure_ascii=False,indent=2))
print(json.dumps({'master_manifest':str(master),'outputs':all_records},ensure_ascii=False,indent=2))
