"""Run a measured operative trial. Resume a case in the same output directory."""
import argparse
import fcntl
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from recipe import FPS, HERE, KIT, LIB, WISDOM, assets, digest, read, save, timeline
from render import Shots
from quality import certified_movie, playback, reference
from compose import assemble, mix_audio, preflight
from review import author, compare, repairs, flag_audit_tickets

sys.path.insert(0,str(KIT/'gates'))
from thresholds import T


def audit_once(folder,tag):
    """The brief requests a terminal measurement even when the candidate is held."""
    gates=folder/'gates'
    movie=folder/(tag+'.mp4')
    result=gates/(tag+'_review_fable.json')
    receipt=gates/'measurement_fable.json'
    sha=digest(movie)
    with (gates/'measurement.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if receipt.exists():
            prev=read(receipt)
            if prev['movie_sha256']!=sha:
                raise ValueError('Terminal measurement already bound to another cut')
            if not result.exists():
                raise RuntimeError('Fable dispatch has no returned verdict; inspect the saved log')
        else:
            if result.exists():
                raise ValueError('Unbound review exists')
            save(receipt,dict(status='dispatched',movie_sha256=sha))
            with (gates/(tag+'_fable.log')).open('w') as log:
                proc=subprocess.run([sys.executable,KIT/'gates/review_gate.py',folder,tag,'--operative',
                                     '--model','fable','--runs','1','--single-audit'],stdout=log,stderr=subprocess.STDOUT)
            if proc.returncode not in (0,1) and not result.exists():
                raise RuntimeError('Audit failed; see '+str(log.name))
        verdict=read(result)
        if verdict.get('error') or hashlib.md5(movie.read_bytes()).hexdigest()!=verdict.get('_md5'):
            raise ValueError('No valid terminal Fable verdict')
        save(receipt,dict(status='measured',movie_sha256=sha,score=verdict['final'],passed=verdict['pass'],tag=tag))
        flag_audit_tickets(result)
        from improvement_log import append, finding
        append([finding(folder.name,'operative_measurement',sha,'info','episode',str(receipt.resolve()),
                        folder=str(folder.resolve()),kind='observation')])
        return verdict


def write_evidence(folder,case,rows,segments,manifest):
    topic=LIB['cases'][case]
    sources={r['pmid']:LIB['sources'][r['pmid']] for r in rows}
    credits=('https://creativecommons.org/licenses/by/4.0/ Changes made by us. '
             'BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International. '
             'Upper gingiva and teeth registered, shaped, surfaced and animated. '
             'https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html\n'
             'Studio Small 09, Leather Red 02 and Coral Gravel (Poly Haven, CC0). Metal 032 (ambientCG, CC0). '
             'Healthy gingiva by Mohamed Hamze (public domain). Black Han Sans and Pretendard (OFL 1.1). '
             'Original operative instruments, shot staging and animation.\n')
    credit_audio='\n'.join(f"{LIB['audio'][str(i)]['source']} — CC0 1.0" for i in
                          sorted({a[0] for r in rows for a in LIB['steps'][r['step']]['sfx']}))
    credit_audio+='\nContinuous Earshot D-minor score, original surgery v3 stem.\n'
    (folder/'SOURCES_AUDIO.md').write_text(credit_audio)
    shutil.copyfile(WISDOM/'LICENCE_AUDIT.md',folder/'LICENCE_AUDIT.md')
    text='\n'.join(f"PMID {pid}. {src['claim']} {src['url']}" for pid,src in sources.items())
    (folder/'SOURCES.md').write_text(topic['scope']+'\n'+text+'\n'+credits)
    case_description={
        'crown_lengthening':'잇몸이 덮은 위 앞니에서 잇몸선을 다듬은 직후 치관이 드러나는 한 사례입니다.',
        'simple_extraction':'성인의 맹출한 위 앞니 한 개를 발치 겸자로 움직여 치근과 함께 꺼내는 과정을 보여 줍니다.'}
    (folder/'description.txt').write_text(topic['title']+'\n'+case_description[case]+'\n'+
                    '\n'.join(src['url'] for src in sources.values())+'\n'+credits+credit_audio)
    save(folder/'assets.json',dict(inputs=manifest,attribution=credits,anatomy_source='DBCLS release 4.0 OBJ',
                                  instruments='original',scene_import='named materials and world only'))
    save(folder/'episode.json',dict(id=case,title=topic['title'],fps=FPS,scope=topic['scope'],steps=rows,
             layout=dict(band_y=0,band_h=1920),duration=sum(end-start for _,start,end,*_ in segments)/FPS))


def run(root,case,stop_after_render=False):
    folder=root/case
    gates=folder/'gates'
    gates.mkdir(parents=True,exist_ok=True)
    state=folder/'trial.json'
    report=read(state) if state.exists() else dict(case=case,started=time.time(),drafts=[])
    def update(status):
        report.update(status=status,elapsed_seconds=round(time.time()-report['started'],2))
        save(state,report)
    if report.get('status')=='measured':
        return report
    update('authoring')
    authored=author(folder,case)
    report['author_sha256']=digest(folder/'author.json')
    rows=authored['steps']
    rows_by_stage=rows
    segments=timeline(case,rows)
    manifest=assets(case)
    from evidence_packet import preflight_recipe
    preflight_recipe(folder,case,rows,manifest)
    write_evidence(folder,case,rows,segments,manifest)
    from description_gate import check_description
    ok,description=check_description(folder/'description.txt',narrated=False)
    if not ok:
        raise ValueError(description)
    audio=folder/'mix.wav'
    save(folder/'audio.json',mix_audio(audio,segments,LIB['steps']))
    settings={}
    previous_cut=None
    for number in range(1,6):
        tag=f'draft{number}'
        shots=Shots(root/'cache',case,settings)
        update('preflight '+tag)
        try:
            plan,proof=preflight(folder,tag,segments,shots,settings)
        except ValueError as exc:
            proof=dict(tag=tag,errors=[str(exc)],pass_stills=False)
            save(gates/(tag+'_preflight.json'),proof)
        if proof['errors']:
            from improvement_log import append, finding
            append([finding(case,'gate',error,'blocking',tag,str(gates/(tag+'_preflight.json')),
                        kind='template_ticket',owner='Astra') for error in proof['errors']])
            report.setdefault('held_preflights',{})[tag]=proof['errors']
            if previous_cut is None:
                update('blocked in still preflight')
                return report
            number,tag,plan,proof,settings,entry,certified=previous_cut
            break
        update('rendering '+tag)
        movie=assemble(folder,tag,plan,shots,settings,audio)
        if stop_after_render:
            update('awaiting comparator '+tag)
            return report
        ref=reference(root,folder)
        reference_movie=Path(ref['movie'])
        ref_audit=Path(ref['audit'])
        if digest(reference_movie)!=ref['sha256']:
            raise ValueError('Reference changed since its audit')
        certified=ref['certified']
        audible=playback(movie,proof['frames'])
        save(gates/(tag+'_audio.json'),dict(**read(folder/'audio.json'),**audible))
        from evidence_packet import contact_receipt, edition_sources
        edition_sources(folder,tag)
        result=compare(folder,tag,reference_movie,ref_audit,segments,{
            'audio.json':gates/(tag+'_audio.json'),'contact.json':contact_receipt(folder,tag),
            'facts.json':gates/(tag+'_facts.json'),'licences.md':folder/'LICENCE_AUDIT.md',
            'sources.md':folder/'SOURCES.md','assets.json':folder/'assets.json'})
        new_settings,mapped,tickets=repairs(folder,tag,result,settings,list(dict.fromkeys(s[0] for s in segments)))
        if not audible['seam_ok'] or not audible['peak_ok']:
            from improvement_log import append, finding
            already_fixed=settings.get('_audio',{}).get('phase_lock',False)
            new_settings['_audio']={'phase_lock':True}
            (tickets if already_fixed else mapped).append('encoded-audio-boundary')
            append([finding(case,'gate','Encoded audio boundary or peak exceeds its measured limit','blocking',
                            tag,str(gates/(tag+'_audio.json')),kind='template_ticket' if already_fixed else 'observation',
                            template='operative',owner='Astra',repair='phase_lock')])
        entry=dict(number=number,tag=tag,sha256=digest(movie),reference=ref['sha256'],reference_certified=certified,
                   pair_pass=result['pass_pair'],axes={k:v['verdict'] for k,v in result['axes'].items()},
                   mapped=mapped,tickets=tickets,settings=settings)
        if len(report['drafts'])>=number:
            if report['drafts'][number-1]!=entry:
                raise ValueError('Draft receipt changed')
        else:
            report['drafts'].append(entry)
        update('compared '+tag)
        previous_cut=(number,tag,plan,proof,settings,entry,certified)
        if new_settings==settings or number==5:
            break
        settings=new_settings
    # Freeze the terminal recipe and render its measurement copy at native
    # delivery size. Its camera, poses and cue clock are identical to the draft.
    update('rendering terminal measurement')
    master=Shots(root/'cache',case,settings,(1080,1920))
    final_plan=[]
    for shot,start,end,caption,stage,count,_,rows in plan:
        path,_=master.load(shot,count,'render',[])
        final_plan.append((shot,start,end,caption,stage,count,path,rows))
    final_tag='terminal'
    final_movie=assemble(folder,final_tag,final_plan,master,settings,audio)
    final_audio=playback(final_movie,proof['frames'])
    save(gates/(final_tag+'_audio.json'),dict(**read(folder/'audio.json'),**final_audio))
    selected=next(i for i in rows_by_stage if i['step'] in ('expose_crown','deliver_whole'))
    frame0=next(r for r in final_plan if r[0]==selected['step'])
    shot,start,end,caption,stage,count,path,geometry=frame0
    from compose import compose_frame
    thumb=selected['thumbnail']
    compose_frame(path,thumb,count,caption,stage,geometry[thumb]['leader'],settings.get(shot,{})).save(folder/'thumbnail.jpg',quality=94)
    audit=audit_once(folder,final_tag)
    report.update(terminal_cut=final_tag,terminal_from=tag,terminal_sha256=digest(final_movie),
                  fable=audit['final'],fable_pass=audit['pass'],p0=len(audit['p0']),p1=len(audit['p1']),
                  measured_at_draft=number,numerical_target_met=audit['final']>=T['review_gate']['fable']['pass_final'],
                  drafts_to_pass=None)
    if entry['pair_pass'] and certified and audit['pass'] and all(final_audio[k] for k in ('continuous','seam_ok','peak_ok')):
        # Apply the existing full absolute Opus and registry gates in addition
        # to the relative comparison before storing a qualified default.
        full=subprocess.run([sys.executable,KIT/'gates/review_gate.py',folder,final_tag,'--model','opus','--operative'])
        meta=subprocess.run([sys.executable,KIT/'gates/defects_meta.py'],capture_output=True,text=True)
        passed=full.returncode==0 and meta.returncode==0
        save(gates/(final_tag+'_qualification.json'),dict(movie_sha256=digest(final_movie),
             registry_sha256=digest(KIT/'defects.yaml'),opus=full.returncode,meta=meta.stdout,**{'pass':passed}))
        if passed:
            report['drafts_to_pass']=number
    update('measured')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case',choices=LIB['cases'])
    parser.add_argument('--work',type=Path,default=Path('.astra-work/operative'))
    parser.add_argument('--through-render',action='store_true')
    parser.add_argument('--recipe',type=Path,help='Production lookup for a data-only episode JSON')
    args=parser.parse_args()
    root=args.work.resolve()
    if args.recipe:
        print(json.dumps(certified_movie(root,args.case,read(args.recipe)),ensure_ascii=False))
        sys.exit(0)
    lock=root/args.case/'trial.lock'
    lock.parent.mkdir(exist_ok=True,parents=True)
    with lock.open('a') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        print(json.dumps(run(root,args.case,args.through_render),ensure_ascii=False))
