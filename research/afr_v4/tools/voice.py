#!/usr/bin/env python3
"""Local English narration. Optional local model, never a paid API.
Requires: Python 3.10+, kokoro==0.9.4, soundfile, numpy, and espeak-ng.
First model use downloads public weights. No celebrity/person voice cloning.
"""
from pathlib import Path
import hashlib, json, os, sys, tempfile
ROOT=Path(__file__).resolve().parents[1]

def main():
    rel=sys.argv[1] if len(sys.argv)>1 else 'episodes/one_step_behind/episode.json'
    source=(ROOT/rel).resolve()
    if not source.is_relative_to(ROOT/'episodes'):
        raise ValueError('Episode must be inside episodes/')
    ep=json.loads(source.read_text())
    out=ROOT/'out'/ep['id']/'audio'
    out.mkdir(parents=True,exist_ok=True)
    for parent in (out,*out.parents):
        if parent.is_symlink(): raise ValueError('Refusing linked output path')
    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
    except ImportError as exc:
        raise RuntimeError('Local voice dependencies are missing. Install kokoro==0.9.4 soundfile numpy and espeak-ng. No fallback mechanical voice will be substituted.') from exc
    pipe=None
    for line in ep['audio']['lines']:
        p=out/(line['id']+'.wav'); m=out/(line['id']+'.json')
        for f in (p,m):
            if f.is_symlink() or (f.exists() and f.stat().st_nlink>1): raise ValueError('Unsafe voice output')
        key={'text':line['text'],'voice':ep['audio']['voice'],'lang':ep['audio']['lang'],'generator':'kokoro==0.9.4'}
        if p.exists() and m.exists():
            old=json.loads(m.read_text())
            if all(old.get(k)==v for k,v in key.items()) and old.get('wavHash')==hashlib.sha256(p.read_bytes()).hexdigest():
                print('REUSED',line['id']);continue
        if pipe is None: pipe=KPipeline(lang_code=ep['audio']['lang'])
        chunks=[audio for _,_,audio in pipe(line['text'],voice=ep['audio']['voice'],speed=1)]
        audio=np.concatenate(chunks)
        seconds=len(audio)/24000
        if seconds>line['maxFrames']/ep['fps']:
            raise ValueError(f"{line['id']}: {seconds:.2f}s exceeds slot. Adjust script or edit timing; no silent time-stretch.")
        fd,tmp=tempfile.mkstemp(prefix='.voice-',suffix='.wav',dir=out);os.close(fd)
        try:
            sf.write(tmp,audio,24000,subtype='PCM_16')
            digest=hashlib.sha256(Path(tmp).read_bytes()).hexdigest()
            os.replace(tmp,p)
            fd,meta_tmp=tempfile.mkstemp(prefix='.voice-',suffix='.json',dir=out);os.close(fd)
            Path(meta_tmp).write_text(json.dumps({**key,'seconds':seconds,'wavHash':digest,'model':'hexgrad/Kokoro-82M','license':'Apache-2.0'},indent=2))
            os.replace(meta_tmp,m)
        finally:
            Path(tmp).unlink(missing_ok=True)
        print('GENERATED',line['id'],round(seconds,3))
if __name__=='__main__':
    try: main()
    except Exception as exc: print('BLOCKED:',exc,file=sys.stderr);sys.exit(1)
