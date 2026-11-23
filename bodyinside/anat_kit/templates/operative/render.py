"""Render and audit individual shots once, under a shared low-priority Blender lock."""
import fcntl
import hashlib
import json
import os
import subprocess
from pathlib import Path

from PIL import Image

from recipe import DB, HERE, LIB, SCENE, digest, read, save


def intact(path):
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except (OSError, SyntaxError):
        return False


def complete_geometry(path,count):
    try:
        result=read(path)
        return ([row['f'] for row in result['frames']]==list(range(count)) and result['inputs']
                and all(LIB['dbcls'].get(k)==v for k,v in result['inputs'].items()))
    except (OSError,ValueError,KeyError,TypeError):
        return False


class Shots:
    def __init__(self, cache, case, settings, size=(270,480)):
        self.root = cache
        self.case = case
        self.settings = settings
        self.size = size
        self.device = os.environ.get('ANAT_BLENDER_DEVICE', 'METAL')
        if self.device not in ('CPU', 'METAL'):
            raise ValueError('ANAT_BLENDER_DEVICE must be CPU or METAL')
        self.root.mkdir(exist_ok=True, parents=True)
        self.version = [digest(HERE / x) for x in ('scene.py','contact.py')]
        self.version += [LIB['archive'][str(SCENE.relative_to(SCENE.parents[2]))], LIB['dbcls']]

    def load(self, shot, count, mode, frames):
        # A full macro range can monopolize the shared workstation for tens of
        # minutes. Release both Blender locks between native-size batches.
        if mode=='render' and self.size[0]>=1080 and len(frames)>12:
            ordered=list(frames)
            rendered=0
            for start in range(0,len(ordered),12):
                folder,added=self.load(shot,count,mode,ordered[start:start+12])
                rendered+=added
            return folder,rendered
        args = dict(shot=shot, count=count, case=self.case, size=self.size, device=self.device,
                    **{k:v for k,v in self.settings.get(shot, {}).items() if k in ('distance','fstop','azimuth','empty_socket','tissue_surface')})
        script=HERE/('socket_view.py' if args.get('empty_socket') else 'scene.py')
        version=self.version+[digest(script)] if args.get('empty_socket') else self.version
        if args.get('tissue_surface'):
            script=HERE/'tissue_surface.py'
            version=version+[digest(script)]
        key = hashlib.sha256(json.dumps([version,args],sort_keys=True).encode()).hexdigest()
        folder = self.root / key
        folder.mkdir(exist_ok=True)
        if mode=='render' and all(intact(folder/f'{f:04}.png') for f in frames):
            return folder,0
        if mode=='audit' and complete_geometry(folder/'geometry.json',count):
            return folder,0
        # Serialise both the cache update and renderer across concurrent topics.
        with (self.root / 'blender.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            geometry = folder / 'geometry.json'
            if mode == 'audit':
                needed = [] if complete_geometry(geometry,count) else list(range(count))
            else:
                needed = [f for f in frames if not intact(folder / f'{f:04}.png')]
            if needed:
                spec = dict(args, mode=mode, frames=needed, out=str(folder.resolve()),
                            scene=str(SCENE), db=str(DB))
                config = folder / (mode+'.json')
                save(config, spec)
                launcher = HERE.parents[1]/'blender/launch.py'
                with (folder/(mode+'.log')).open('a') as log:
                    subprocess.run([launcher,'-b','--factory-startup','-t','4',
                                    '--python-exit-code','1','-P',script,'--',config],
                                   stdout=log, stderr=subprocess.STDOUT, check=True)
            if mode == 'audit':
                result = read(geometry)
                if [r['f'] for r in result['frames']] != list(range(count)):
                    raise ValueError('Incomplete geometry for '+shot)
                if not result['inputs'] or any(LIB['dbcls'].get(k)!=v for k,v in result['inputs'].items()):
                    raise ValueError('Unregistered source mesh')
            return folder, len(needed)
