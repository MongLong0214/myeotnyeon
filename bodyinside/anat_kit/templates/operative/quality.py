"""Playback measurements and the digest-bound reference or default used by the factory."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from recipe import HERE, KIT, LIB, WISDOM, digest, read, save

sys.path.insert(0,str(KIT/'gates'))
from thresholds import T


def playback(movie, expected_frames,fps=30):
    pcm=subprocess.check_output(['ffmpeg','-v','error','-i',movie,'-map','0:a:0','-ar','48000','-ac','2',
                                '-f','f32le','pipe:1'])
    sample_count=round(expected_frames*48000/fps)
    audio=np.frombuffer(pcm,dtype='<f4').reshape(-1,2)[:sample_count]
    if len(audio)!=sample_count:
        raise ValueError('Decoded audio does not cover picture')
    analysis=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',movie,'-vn','-af',
                 'loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,check=True)
    log=analysis.stderr.decode()
    loudness,_=json.JSONDecoder().raw_decode(log[log.rindex('{'):])
    seam=float(np.max(abs(audio[0]-audio[-1])))
    near=np.concatenate((audio[-512:],audio[:512]))
    local=float(np.percentile(np.max(abs(np.diff(near,axis=0)),axis=1),98))
    rms=[float(np.sqrt(np.mean(block*block))) for block in np.array_split(audio,(sample_count+4799)//4800)]
    return dict(lufs=float(loudness['input_i']),true_peak_dbtp=float(loudness['input_tp']),
                min_window_rms=min(rms),audio_seam=seam,local_delta_p98=local,frames=expected_frames,
                seam_ok=seam<=local,peak_ok=float(loudness['input_tp'])<=-1.5,
                continuous=min(rms)>1e-5)


def verified_reference(movie,audit):
    result=read(audit)
    if (result.get('_model')!='fable' or result.get('stage')!='movie' or result.get('error')
            or len(result.get('runs',[]))!=1 or
            result.get('_md5')!=hashlib.md5(movie.read_bytes()).hexdigest()):
        raise ValueError('Missing independent Fable audit of this reference')
    return dict(movie=str(movie.resolve()),audit=str(audit.resolve()),sha256=digest(movie),
            score=result['final'],certified=(result.get('pass') is True and not result['p0']
            and result['final']>=T['review_gate']['fable']['pass_final']))


def reference(root,case_folder=None):
    # A development reference can be compared even while the numerical gate is red.
    pinned=root/'comparison_reference.json'
    frozen=case_folder/'comparison_reference.json' if case_folder else None
    if frozen and frozen.exists():
        pinned=frozen
    if pinned.exists():
        record=read(pinned)
        result=verified_reference(Path(record['movie']),Path(record['audit']))
        if result['sha256']!=record['sha256']:
            raise ValueError('Reference changed')
    else:
        result=verified_reference(WISDOM/'final_surgery_v3.mp4',HERE/'evidence/surgery_v3_fable.json')
    if frozen and not frozen.exists():
        save(frozen,result)
    return result


def certified_movie(root,case,authored):
    """Production lookup can serve only an individually measured movie and its exact recipe."""
    from recipe import resolve
    folder=root/case
    state=read(folder/'trial.json')
    ref=reference(root,folder)
    if not ref['certified'] or not state.get('drafts_to_pass'):
        raise ValueError('No certified operative default for '+case)
    if digest(folder/'author.json')!=state['author_sha256']:
        raise ValueError('Certified recipe changed')
    frozen=read(folder/'author.json')['steps']
    selected,repairs=resolve(case,authored)
    tag=state['terminal_cut']
    movie=folder/(tag+'.mp4')
    audit=verified_reference(movie,folder/'gates'/(tag+'_review_fable.json'))
    last=state['drafts'][-1]
    pair=read(folder/'gates'/('pair_'+last['tag'])/'opus.json')
    gate=read(folder/'gates'/(tag+'_qualification.json'))
    if (not audit['certified'] or audit['sha256']!=state['terminal_sha256'] or
        pair['sha256'][:2]!=[last['sha256'],ref['sha256']] or not pair['pass_pair'] or
        not gate['pass'] or gate['movie_sha256']!=audit['sha256'] or
        gate['registry_sha256']!=digest(KIT/'defects.yaml')):
        raise ValueError('Operative default certification is stale')
    # Only this exact recipe has been measured. A new caption or procedure
    # requires a separate candidate measurement before production can use it.
    return dict(movie=str(movie),steps=frozen,used_default=bool(repairs or selected!=frozen))
