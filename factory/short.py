#!/usr/bin/env python3
"""Offline v52 factory; shared B6/E4 and H15/H16 QA (2026-11-07).

CEO caught; CTO missed. --edge-fill-only scans an existing encode without rendering.
"""
from pathlib import Path
import os,sys
W=Path(__file__).resolve().parents[1]
PYTHON=W/'.venv/bin/python'
if Path(sys.prefix)!=W/'.venv' and PYTHON.exists():
    os.execv(str(PYTHON),[str(PYTHON),__file__,*sys.argv[1:]])
import argparse,copy,hashlib,json,re,shutil,subprocess,traceback
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',DO_NOT_TRACK='1')
S=Path(__file__).parent
sys.path.insert(0,str(W/'episodes/quiz'))
from episodes_n16 import EPISODES

def load(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def run(args,log=None):
    if log:
        with Path(log).open('w') as f:subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,check=True,cwd=W)
    else:return subprocess.check_output(list(map(str,args)),cwd=W).decode()
def new_dir(q,n):
    parent=W/'upload/pkg';parent.mkdir(exist_ok=True)
    for i in range(1,100000):
        p=parent/(f'{q}_n{n}'+(f'_v{i}' if i>1 else ''))
        try:p.mkdir();return p
        except FileExistsError:continue
    raise RuntimeError('No available version')
def episode(q):
    if q not in EPISODES:raise ValueError(f'Unknown episode: {q}')
    return copy.deepcopy(EPISODES[q])
def prepare(p,q,n,fresh=False,video_id=None,dry_number=False):
    ep=episode(q);base=W/'episodes/quiz'/q
    public=W/'episodes/quiz/v52_q013_q014_support/bundle_v52_revised/public' if q in ['q013','q014'] else W/'production/compositor/public'
    # The existing prepared v52 WAV is the deterministic cache of the synthesized
    # hook plus unchanged v3 body. Never substitute an upload video for rendering.
    candidates=[base/'v52/render_final_aligned.json',base/'v52/render_final.json',base/'v52/render.json']
    source=next((x for x in candidates if x.exists()),None)
    from_scratch=source is None and not all((base/('v52_input' if (base/'v52_input').exists() else 'v5')/name).is_file() for name in ['audio.json','render.json'])
    regenerated=source is None or fresh
    research=[]
    prepared=base/'v52'
    if from_scratch:
        from fresh import prepare as prepare_fresh
        prepared,public,research=prepare_fresh(p,q)
        source=prepared/'render.json'
    elif regenerated:
        # Run a copied v52 stage with local-only outputs. Original source/audio stay read-only.
        prior=base/('v52_input' if (base/'v52_input').exists() else 'v5')
        if not all((prior/name).is_file() for name in ['audio.json','render.json']):
            raise RuntimeError(f'{q}: existing v52 prerequisites missing ({prior}); no alternative pipeline or network fallback')
        print('Synthesizing hook through copied v52 preparation (local Supertonic)',flush=True)
        staged=p/'public_assets';shutil.copytree(public,staged)
        target=staged/q/'v52'
        if target.exists():shutil.rmtree(target)  # only this new package copy
        prepared=p/'prepared'
        env=dict(os.environ,FACTORY_WORKSPACE=str(W),FACTORY_PUBLIC=str(staged),FACTORY_PREPARED=str(prepared))
        with (p/'prepare.log').open('w') as f:
            subprocess.run([str(PYTHON),str(S/'prepare_v52.py'),q],env=env,cwd=W,stdout=f,stderr=subprocess.STDOUT,check=True)
        source=prepared/'render.json';public=staged
    doc=load(source);seed=int(q[1:]) if q in ['q013','q014'] else doc['ep']['no'];doc['ep']['no']=n
    if q=='q013':
        for c in doc['cues']:
            if c['id'] in ['C2','C3']:c['p']['set']=dict(C2='custody_court',C3='probation_objects')[c['id']];c['p'].pop('actors',None)
    # Fail closed on stale prepared facts rather than render a previous episode entry.
    for key in ['head','answerHead','answer','source']:
        if doc['ep'][key]!=ep[key]:raise ValueError(f'Stale v52 {key}; rebuild existing v52 preparation first')
    for c in doc['cues']:
        e=next(x for x in ep['cues'] if x[0]==c['id'])
        if c['scene']=='incident' and c['p'].get('set')!=e[5].get('set'):raise ValueError(f'Stale set: {c["id"]}')
    doc['ep']['assetNo']=seed
    save(p/'episode.json',ep);save(p/'render.json',doc)
    for name in ['audio.json','timing.json']:
        shutil.copyfile(prepared/name,p/name)
    audio=load(p/'audio.json')
    lines=[line for c in ep['cues'] for line in c[2]]
    lines[0]=ep['hook']['narration']+' '+ep['hook'].get('ask',doc['ep']['ask'])
    expected=' '.join(lines)
    if audio['reference']!=expected:raise ValueError('Prepared narration differs from episode entry')
    master=public/doc['audio']
    if not master.exists():raise FileNotFoundError(master)
    shutil.copyfile(master,p/'mix_master.wav')
    # The original n16/n15 paths used this public snapshot; fonts/assets are pinned there.
    hero=public/'hook_v51'/f'{"q013_clouds" if q=="q013" else q}.png'
    if not hero.exists():raise FileNotFoundError(hero)
    shutil.copyfile(hero,p/'hero.png')
    # Keep the prior cached AAC bitstream, verified against master during QA.
    aac=base/'v52/candidate_revised.mp4'
    if not aac.exists():aac=base/'v52/candidate.mp4'
    if regenerated or not aac.exists():
        aac=p/'audio_cache.m4a'
        run(['ffmpeg','-v','error','-n','-i',master,'-c:a','aac','-b:a','320k',aac],p/'audio_encode.log')
    for f in (S/'vendor').glob('*.tsx'):shutil.copyfile(f,p/f.name)
    hook=(p/'HookV51Seed.tsx').read_text()
    if seed not in [13,14]:
        hook=hook.replace("{13: 'q013_clouds', 14: 'q014'}",f"{{{seed}: '{q}'}}")
        (p/'HookV51Seed.tsx').write_text(hook)
    cfg=dict(qid=q,number=n,seed=seed,from_scratch=from_scratch,dry_number=dry_number,video_id=video_id,hook_regenerated=regenerated,public=str(public),source=str(source),master=str(master),aac=str(aac),storyEnd=max(c['from']+c['dur'] for c in doc['cues'] if c['scene']=='incident'),source_hashes={str(x.relative_to(W)):sha(x) for x in [source,master,aac,hero,W/'episodes/quiz/episodes.py',W/'episodes/quiz/episodes_n16.py',*research]})
    save(p/'recipe.json',cfg)
    root=W/'production/compositor/src'
    hookpath=root/('v52_candidates/HookRevised' if q in ['q013','q014'] else 'v52/Hook')
    if from_scratch:
        hook52=(root/'v52/Hook.tsx').read_text()
        hook52=hook52.replace("from '../Quiz'",f"from '{root}/Quiz'").replace("from '../theme'",f"from '{root}/theme'").replace("from '../HookV51'","from './HookV51Seed'")
        hook52=re.sub(r"const HERO_IDS: Record<number, string> = .*?;",f"const HERO_IDS: Record<number, string> = {{{seed}: '{'q013_clouds' if q=='q013' else q}'}};",hook52)
        (p/'HookFresh.tsx').write_text(hook52);hookpath=p/'HookFresh'

    entry='''import React from 'react';
import {registerRoot,AbsoluteFill,Audio,Composition,Still,staticFile,useCurrentFrame} from 'remotion';
import {Quiz,QuizDoc} from './QuizPanels';
import {HookV52} from 'HOOK';
import {Cover} from 'ROOT/Cover';
import {SafeAudit} from 'ROOT/SafeAudit';
import {HookAudit51} from 'ROOT/HookAudit51';
import {ZoomAudit} from 'ROOT/v52/ZoomAudit';
import data from './render.json';
const doc=data as unknown as QuizDoc;
const heroDoc={...doc,ep:{...doc.ep,no:SEED}};
const empty={...doc,cues:doc.cues.map(c=>c.scene==='incident'?{...c,p:{...c.p,set:'paper',actors:[],props:[]}}:c)};
const Video=()=>useCurrentFrame()<=60?<AbsoluteFill><HookV52 doc={heroDoc}/>{doc.audio&&<Audio src={staticFile(doc.audio)}/>}</AbsoluteFill>:<Quiz doc={doc} hookStyle="v51"/>;
const Empty=()=> <Quiz doc={empty} hookStyle="v51"/>;
const Audit=()=> <SafeAudit label="QID"><HookAudit51 doc={doc}><ZoomAudit><Video/></ZoomAudit></HookAudit51></SafeAudit>;
registerRoot(()=> <><Composition id="VIDEO" component={Video} width={1080} height={1920} fps={30} durationInFrames={doc.durationInFrames}/><Composition id="EMPTY" component={Empty} width={1080} height={1920} fps={30} durationInFrames={doc.durationInFrames}/><Composition id="AUDIT" component={Audit} width={1080} height={1920} fps={30} durationInFrames={doc.durationInFrames}/><Still id="COVER" component={()=> <Cover doc={doc}/>} width={1080} height={1920}/></>);
'''.replace('HOOK',str(hookpath)).replace('ROOT',str(root)).replace('SEED',str(seed)).replace('QID',q)
    (p/'entry.tsx').write_text(entry)
    return cfg

def metadata(q,n,from_scratch=False):
    if from_scratch:
        from fresh import metadata as fresh_metadata
        return fresh_metadata(episode(q))
    choices=[W/'upload'/f'v52_{q}_n{n}_meta_final.txt',W/'upload'/f'v52_{q}_meta.txt']
    source=next((f for f in choices if f.exists()),None)
    if source is None:raise FileNotFoundError(f'{q}: series metadata is missing')
    text=source.read_text();text=re.sub(r'형량 퀴즈 #\d+\s*·\s*','',text)
    return text

def seal(p,report):
    from review_gates import LIMIT
    report.setdefault('limits',[])
    if LIMIT not in report['limits']:report['limits'].append(LIMIT)
    (p/'READY').unlink(missing_ok=True)
    save(p/'qa.json',report)
    names=['video.mp4','cover.jpg','meta.txt','qa.json','review_sheet.jpg','episode.json','render.json','audio.json','timing.json','hero.png','recipe.json','entry.tsx','render_complete.json']
    (p/'SHA256').write_text(''.join(f'{sha(p/name)}  {name}\n' for name in names if (p/name).exists()))
    if report.get('ready') and not report.get('dry_number'):(p/'READY').write_text(sha(p/'SHA256')+'\n')

def build(q,n,fresh=False,video_id=None,dry_number=False,review_inputs=None,review_script=None):
    p=new_dir(q,n);print('PACKAGE',p,flush=True)
    try:
        cfg=prepare(p,q,n,fresh,video_id,dry_number);(p/'meta.txt').write_text(metadata(q,n,cfg['from_scratch']))
        if review_inputs:
            source=Path(review_inputs).resolve();review=load(source)
            for row in review.get('references',[]):row['video']=str((source.parent/row['video']).resolve())
            for row in [*review.get('sources',[]),*review.get('interest_evidence',[])]:row['file']=str((source.parent/row['file']).resolve())
            if review.get('style_bible'):review['style_bible']=str((source.parent/review['style_bible']).resolve())
            save(p/'review_inputs.json',review)
        if review_script:shutil.copyfile(review_script,p/'script.md')
        if dry_number:(p/'TEST_ARTIFACT').write_text('Local number-gate test. Not for upload; no ledger writes.\n')
        print('Rendering existing v52 composition',flush=True)
        run(['node',S/'render.cjs',p],p/'render.log')
        run(['ffmpeg','-v','error','-n','-i',p/'video_muted.mp4','-i',cfg['aac'],'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',p/'video.mp4'],p/'mux.log')
        from gates import evaluate
        report=evaluate(p);seal(p,report)
        print(json.dumps(dict(package=str(p),ready=report['ready'],gates={k:v['status'] for k,v in report['gates'].items()}),ensure_ascii=False),flush=True)
        return 0 if report['ready'] else 2
    except BaseException as e:
        seal(p,dict(ready=False,gates={'build':dict(status='FAIL',evidence=str(e))},error=traceback.format_exc()))
        raise

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('qid',nargs='?');a.add_argument('--no',type=int);a.add_argument('--check',type=Path);a.add_argument('--fresh-hook',action='store_true',help='Re-run the existing local Supertonic hook preparation, instead of its deterministic cache')
    a.add_argument('--dry-number',action='store_true',help='Exercise number gate without consuming it; test artifact, never READY')
    a.add_argument('--video-id',help='Existing published/scheduled video identity for a same-video rebuild')
    a.add_argument('--edge-fill-only',type=Path,metavar='VIDEO',help='Run shared B6 on an existing encode, without rendering or uploading')
    a.add_argument('--h15-h16-only',type=Path,metavar='VIDEO',help='Run shared composition/presenter/subtitle checks on an existing encode; no render/upload')
    a.add_argument('--shots',type=Path,help='Shot metadata for --h15-h16-only; otherwise samples every 1 s')
    a.add_argument('--subtitles',type=Path,nargs='+',action='extend',help='SRT/subtitle JSON/labelled script sources for --h15-h16-only')
    a.add_argument('--review-inputs',type=Path,help='Local checklist references, sources and metadata')
    a.add_argument('--review-script',type=Path,help='Script with timed COLD_OPEN/CENTRAL_QUESTION/CLIFFHANGER markers')
    args=a.parse_args()
    if args.h15_h16_only:
        if args.check or args.qid or args.no is not None or args.edge_fill_only:a.error('--h15-h16-only is separate from build/--check/--edge-fill-only')
        from longform_qa import h15_h16_only,new_output
        return h15_h16_only(args.h15_h16_only,new_output(args.h15_h16_only.stem+'_h15_h16'),
                            args.shots,args.review_script,args.subtitles,format='shorts')
    if args.shots or args.subtitles:a.error('--shots/--subtitles require --h15-h16-only')
    if args.edge_fill_only:
        if args.check or args.qid or args.no is not None:a.error('--edge-fill-only is separate from build/--check')
        from longform_qa import edge_only,new_output
        return edge_only(args.edge_fill_only,new_output(args.edge_fill_only.stem+'_edge_fill'))
    if args.check and (args.review_inputs or args.review_script):
        a.error('--review-inputs/--review-script are for new builds; --check reads the package review_inputs.json/script.md')
    if args.check:
        p=args.check.resolve()
        if not p.is_relative_to(W/'upload/pkg'):a.error('--check must point into upload/pkg')
        from gates import evaluate
        # Remove READY before any check, including a crashing check.
        (p/'READY').unlink(missing_ok=True)
        report=evaluate(p);seal(p,report);print(json.dumps(dict(ready=report['ready'],gates={k:v['status'] for k,v in report['gates'].items()}),ensure_ascii=False));return 0 if report['ready'] else 2
    if not args.qid or not re.fullmatch(r'q\d{3}',args.qid) or args.no is None or args.no<1:a.error('short.py qNNN --no N')
    return build(args.qid,args.no,args.fresh_hook,args.video_id,args.dry_number,args.review_inputs,args.review_script)
if __name__=='__main__':sys.exit(main())
