"""Ingest a completed root-canal cut and pin its reusable source ranges."""
import argparse
import json
import subprocess
from pathlib import Path

from recipe import FPS, digest, read, save

ENDODONTIC = {
    'S04':('access_canal','rotary bur','pulp chamber','37772327'),
    'S05':('remove_pulp','endodontic instrument','pulp chamber','37772327'),
    'S06':('file_canal','endodontic file','registered canals','37772327'),
    'S07':('irrigate_canal','side-vented cannula','prepared canals','35338652'),
    'S08':('fill_canal','gutta-percha and sealer','prepared canals','36508541'),
    'S09':('seat_crown','definitive crown','restored clinical crown','34378217'),
}


def catalog(movie):
    ep=movie.resolve().parent
    data=read(ep/'episode.json')
    gate=read(ep/'penetration_report.json')
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',movie]))
    picture=next(s for s in probe['streams'] if s['codec_type']=='video')
    frames=int(picture['nb_frames'])
    if data['fps']!=30 or picture['r_frame_rate']!='30/1' or frames!=round(data['duration']*30):
        raise ValueError('Incomplete native 30 fps movie')
    if not any(s['codec_type']=='audio' for s in probe['streams']):
        raise ValueError('Missing soundtrack')
    measured_max=max((hit['depth_mm'] for row in gate['frames'] for hit in row['contacts']),default=0.)
    if (abs(measured_max-gate['max_depth_mm'])>1e-5 or gate['ok'] is not True or gate['threshold_mm']>.2 or
        [r['frame'] for r in gate['frames']]!=list(range(frames)) or gate['max_depth_mm']>.2):
        raise ValueError('Incomplete root canal contact proof')
    steps={}
    for beat in data['beats']:
        if beat['id'] not in ENDODONTIC:
            continue
        name,tool,target,pmid=ENDODONTIC[beat['id']]
        lo,hi=(round(beat[k]*30) for k in ('t0','t1'))
        steps[name]=dict(tool=tool,target=target,source_pmids=([pmid,'2257832'] if beat['id']=='S07' else [pmid]),caption=''.join(s[0] for s in beat['cap']),
                         claims=beat['claims'],thumbnail=(lo+hi)//2,range_0based_half_open=[lo,hi],
                         sfx=beat['sfx'])
    if len(steps)!=len(ENDODONTIC):
        raise ValueError('Missing source procedure step')
    return dict(episode=data['id'],status='candidate',movie=movie.name,
                fps=FPS,frames=frames,size=[picture['width'],picture['height']],
                contact=dict(frames=frames,maximum_depth_mm=measured_max,limit_mm=gate['threshold_mm']),
                inputs={p.name:digest(p) for p in [movie,ep/'episode.json',ep/'rootcanal.blend',
                    ep/'penetration_report.json',ep/'ASSETS.md',ep/'SOURCES.md',ep/'production/audio.py']},steps=steps)


def extract_step(movie,manifest,name,output):
    """Reuse the exact authored range with its real sound on the scene's native clock."""
    if movie.name!=manifest['movie'] or digest(movie)!=manifest['inputs'][movie.name]:
        raise ValueError('Source movie differs from the catalogued edition')
    lo,hi=manifest['steps'][name]['range_0based_half_open']
    if output.resolve()==movie.resolve():
        raise ValueError('The source film must be preserved')
    output.parent.mkdir(parents=True,exist_ok=True)
    temp=output.with_suffix('.partial.mp4')
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',movie,
                    '-vf',f'trim=start_frame={lo}:end_frame={hi},setpts=PTS-STARTPTS',
                    '-af',f'atrim=start={lo/FPS}:end={hi/FPS},asetpts=PTS-STARTPTS',
                    '-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',temp],check=True)
    probe=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries',
                                   'stream=nb_frames','-of','csv=p=0',temp],text=True)
    if int(probe)!=hi-lo:
        raise ValueError('Extracted range differs from the native frame clock')
    temp.replace(output)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('movie',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--step',choices=[s[0] for s in ENDODONTIC.values()])
    parser.add_argument('--clip',type=Path)
    a=parser.parse_args()
    if bool(a.step)!=bool(a.clip):
        parser.error('--step and --clip are used together')
    if a.step:
        extract_step(a.movie,read(a.output),a.step,a.clip)
    else:
        save(a.output,catalog(a.movie))
