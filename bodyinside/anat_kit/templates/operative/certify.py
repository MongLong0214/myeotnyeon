"""Build the repaired surgery reference on verified source poses and audit it once."""
import argparse
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image
from recipe import HERE, KIT, LIB, RECORDINGS, SCENE, WISDOM, assets, digest, read, save
from compose import assemble, compose_frame, mix_audio
from render import intact
from trial import audit_once
from quality import playback, reference, verified_reference

# Native plate numbering starts at one; each selected pose occupies one output frame.
CUT = {name:(item['source_start'],item['frames'],item['camera'],item['caption'],item['stage'],item['sfx'])
       for name,item in LIB['surgery_ranges'].items()}
STAGES=['마취','절개','골 삭제','분할','발치','세척','봉합']


class ArchiveShots:
    size=(360,640)

    def __init__(self,root,cortical_window=False,finish_surfaces=False,section_detail=False):
        self.root=root
        self.cortical_window=cortical_window
        self.finish_surfaces=finish_surfaces
        self.section_detail=section_detail
        self.cut=CUT.copy()
        if cortical_window:
            ordered={}
            for shot,item in LIB['surgery_ranges'].items():
                if shot=='deliver_root':
                    ordered.update(LIB['surgery_root_insertions'])
                ordered[shot]=item|item.get('window_edit',{})
                if finish_surfaces:
                    ordered[shot].update(item.get('finish_edit',{}))
            self.cut={shot:(item['source_start'],item['frames'],item['camera'],item['caption'],item['stage'],item['sfx'])
                      for shot,item in ordered.items()}
        self.root.mkdir(parents=True,exist_ok=True)
        self.audit=WISDOM/'penetration_report.json'
        self.inputs={}
        for name,expected in LIB['archive'].items():
            path=WISDOM/name
            if digest(path)!=expected:
                raise ValueError('Source drift: '+name)
            self.inputs[name]=expected
        if not read(self.audit)['ok']:
            raise ValueError('Source contact gate failed')

    def load(self,shot,count,mode,frames,base=False):
        start,expected,camera,*_=self.cut[shot]
        if count!=expected:
            raise ValueError('Unexpected registered range')
        script=HERE/'archive_scene.py'
        original=CUT.get(shot)
        pose_range=original if original and original[:3]==self.cut[shot][:3] else self.cut[shot]
        identity=[shot,pose_range,self.inputs,digest(script),digest(HERE/'contact.py')]
        if self.cortical_window and not base:
            if shot in ('deliver_first_root','deliver_root'):
                original,rendered=self.load(shot,count,mode,frames,base=True)
                out=self.root/(original.name+'-root-crop-072')
                out.mkdir(exist_ok=True)
                if mode=='audit':
                    info=read(original/'geometry.json')
                    if any(r['leader'] for r in info['frames']):
                        raise ValueError('The delivery reframe requires unlabelled footage')
                    info['crop_xywh']=[.14,.015,.72,.72]
                    save(out/'geometry.json',info)
                    save(out/'audit.json',dict(read(original/'audit.json'),catalog_shot=shot))
                else:
                    for f in frames:
                        path=out/f'{f:04}.png'
                        if not intact(path):
                            with Image.open(original/path.name) as im:
                                w,h=im.size
                                bounds=tuple(round(x) for x in (.14*w,.015*h,.86*w,.735*h))
                                im.crop(bounds).resize(im.size,Image.Resampling.LANCZOS).save(path)
                return out,rendered
            if shot in ('reflect','drill','suction'):
                script=HERE/'cortical_window.py'
                identity.append(digest(script))
        if self.finish_surfaces and shot in ('fracture','reflect','drill','suction','section','separate','elevate',
                                             'divide_roots','deliver_first_root','deliver_root','irrigate','specimen','suture'):
            script=HERE/'finish_surfaces.py'
            identity.extend((digest(script),digest(HERE/'alveolar_support.py')))
        if self.section_detail and shot in ('fracture','inject','incise_wisdom','section','separate','elevate',
                                            'divide_roots','deliver_first_root','deliver_root','specimen'):
            script=HERE/'section_detail.py'
            identity.append(digest(script))
        key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
        out=self.root/key
        out.mkdir(exist_ok=True)
        geometry=out/'geometry.json'
        if mode=='audit' and geometry.is_file() and len(read(geometry)['frames'])==count:
            return out,0
        if mode=='render' and all(intact(out/f'{f:04}.png') for f in frames):
            return out,0
        with (self.root/'blender.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            if mode=='audit':
                missing=[] if geometry.exists() else list(range(count))
            else:
                missing=[]
                rows=read(geometry)['frames']
                for f in frames:
                    path=out/f'{f:04}.png'
                    if intact(path):
                        continue
                    if rows[f]['can_reuse']:
                        original=SCENE.parent/'renders'/f'f_{start+f:04}.png'
                        with Image.open(original) as image:
                            image.convert('RGB').resize(self.size,Image.Resampling.LANCZOS).save(path)
                    else:
                        missing.append(f)
            if missing:
                spec=out/(mode+'.json')
                source_shot='deliver_root' if shot in LIB['surgery_root_insertions'] else shot
                save(spec,dict(shot=source_shot,catalog_shot=shot,start=start,out=str(out),audit=str(self.audit),
                               camera='Macro '+camera,frames=missing,mode=mode))
                with (out/(mode+'.log')).open('a') as log:
                    subprocess.run([KIT/'blender/launch.py',
                    '-b','--factory-startup',SCENE,'-t','4','--python-exit-code','1','-P',script,'--',spec],
                    stdout=log,stderr=subprocess.STDOUT,check=True)
            return out,len(missing)


def build(root,edition,cortical_window=False,finish_surfaces=False,section_detail=False):
    folder=root/edition
    gates=folder/'gates'
    gates.mkdir(parents=True,exist_ok=True)
    shots=ArchiveShots(root/'cache',cortical_window or finish_surfaces or section_detail,
                       finish_surfaces or section_detail,section_detail)
    assets('crown_lengthening')
    specs={k:dict(frames=v[1],sfx=v[-1]) for k,v in shots.cut.items()}
    for v in specs.values():
        for i,*_ in v['sfx']:
            if digest(RECORDINGS/f'{i}.mp3')!=LIB['audio'][str(i)]['sha256']:
                raise ValueError('Unaudited recording')
    segments=[]
    for k,(_,n,_,caption,stage,_) in shots.cut.items():
        segments.append((k,24 if k=='fracture' else 0,n,caption,
                         (stage,7,STAGES[stage-1]) if stage else None))
    segments.append(('fracture',0,24,CUT['fracture'][3],None))
    plan=[]
    errors=[]
    for shot,start,end,caption,stage in segments:
        count=specs[shot]['frames']
        path,_=shots.load(shot,count,'audit',[])
        rows=read(path/'geometry.json')['frames']
        if len(rows)!=count:
            raise ValueError('Incomplete repaired geometry')
        errors.extend([dict(shot=shot,frame=r['original'],hits=r['depths']) for r in rows[start:end]
                       if any(d[-1]>.2 for d in r['depths'])])
        errors.extend([dict(shot=shot,frame=r['original'],bur_clearance_mm=r['bur_gap_mm'])
                       for r in rows[start:end] if r.get('bur_gap_mm',0)>.2])
        f=(start+end)//2
        shots.load(shot,count,'render',[f])
        compose_frame(path,f,count,caption,stage,rows[f]['leader'],{}).save(gates/(shot+'.jpg'))
        plan.append((shot,start,end,caption,stage,count,path,rows))
    save(gates/'preflight.json',dict(tag='surgery',errors=errors,pass_stills=not errors))
    if errors:
        raise ValueError(f'{len(errors)} repaired poses failed penetration; see preflight')
    audio=folder/'mix.wav'
    save(folder/'audio.json',mix_audio(audio,segments,specs))
    movie=assemble(folder,'surgery',plan,shots,{'_audio':{'phase_lock':True}},audio)
    coverage=sum(s[2]-s[1] for s in segments)
    decoded=playback(movie,coverage)
    save(gates/'surgery_audio.json',dict(**read(folder/'audio.json'),**decoded))
    if not all(decoded[k] for k in ('seam_ok','continuous','peak_ok')):
        raise ValueError('Repaired reference failed decoded audio checks')
    save(folder/'episode.json',dict(id='wisdom_operative',fps=30,duration=sum(s[2]-s[1] for s in segments)/30,
         layout=dict(band_y=0,band_h=1920),steps=segments))
    credits=('BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International. '
             'Adjacent teeth and gingiva registered and surfaced. Project-authored third molar, instruments, '
             'mucosal flap, radial socket bed, cortical cover and fluid effects. Studio Small 09, Leather Red 02 '
             'and Coral Gravel (Poly Haven CC0), Metal 032 (ambientCG CC0), gingival texture by Mohamed Hamze '
             '(public domain), clot material by Paco Salas (Blendkit Royalty Free), Black Han Sans and Pretendard (OFL). '
             'Freesound CC0 recordings and Earshot score. Original 3D-COSI instrument adaptations as credited below.\n')
    references=('Instrument scans by Gijs Luijten and colleagues, 3D-COSI v1.1. '
                'Changes made by us include simplifying the Willinger raspatory and small Langenbeck retractor, '
                'registering the working ends, applying a steel finish, and animation. '
                'https://doi.org/10.5281/zenodo.10091715\nhttps://creativecommons.org/licenses/by/4.0/')
    clinical=('이 사례에서는 매복된 아래 사랑니를 분할해 발치합니다.\n'
              'https://pubmed.ncbi.nlm.nih.gov/36508551/\nhttps://pubmed.ncbi.nlm.nih.gov/33854724/\n')
    for name in ('description.txt','SOURCES.md'):
        (folder/name).write_text(clinical+credits+references+'\nhttps://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html\n')
    from description_gate import check_description
    ok,details=check_description(folder/'description.txt',narrated=False)
    if not ok:
        raise ValueError(details)
    shutil.copyfile(WISDOM/'LICENCE_AUDIT.md',folder/'LICENCE_AUDIT.md')
    (folder/'SOURCES_AUDIO.md').write_text('\n'.join(str(LIB['audio'][str(i)]) for i in sorted({
        i for step in specs.values() for i,*_ in step['sfx']}))+'\nContinuous Earshot D minor score.\n')
    save(folder/'assets.json',dict(movie=movie.name,movie_sha256=digest(movie),
         archive_inputs=shots.inputs,derivations=credits,
         excluded_geometry=read(plan[0][-2]/'geometry.json')['excluded'],
         cortical_cover=('Original shell fitted continuously to the registered socket, removed in eight '
                         'overlapping bands behind the audited bur sweep' if cortical_window else
                         'Original cortical underside extended to the registered socket'),
         proof=[dict(shot=r[0],geometry=str(r[-2]/'geometry.json')) for r in plan]))
    audit_once(folder,'surgery')
    return verified_reference(movie,gates/'surgery_review_fable.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,default=Path('.astra-work/operative'))
    parser.add_argument('--edition',default='surgery_repair1')
    parser.add_argument('--cortical-window',action='store_true',
                        help='Use the socket-fitted, progressively milled cortex and reframed delivery')
    parser.add_argument('--finish-surfaces',action='store_true',
                        help='Also match root materials, settle the tied wound and hold the clear specimen tray')
    parser.add_argument('--section-detail',action='store_true',
                        help='Also track the opening tools, separate cut-face shading and reseat the upper specimen')
    args=parser.parse_args()
    root=args.work.resolve()
    result=build(root,args.edition,args.cortical_window or args.finish_surfaces or args.section_detail,
                 args.finish_surfaces or args.section_detail,args.section_detail)
    save(root/args.edition/'reference.json',result)
    current=reference(root)
    if (result['certified'],result['score'])>(current['certified'],current['score']):
        save(root/'comparison_reference.json',result)
    print(result)
