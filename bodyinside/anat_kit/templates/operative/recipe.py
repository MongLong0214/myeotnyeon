"""Closed episode authoring vocabulary and immutable source assets."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parents[1]
LIB = json.loads((HERE / 'library.json').read_text())
WORK = Path(os.environ.get('ANAT_SHARED_WORK', KIT.parent))
WISDOM = WORK / 'episodes/anat_wisdom'
DB = WORK / 'research/anatomy3d/bodyparts3d_4.0'
FONTS = WORK / 'branding/_src/public/fonts'
MUSIC = Path(os.environ.get('ANAT_OPERATIVE_MUSIC', KIT.parent/'.astra-work/operative/assets/music.wav'))
SCENE = WISDOM / 'astra_surgery/draft5/surgery_draft5.blend'
RECORDINGS = WISDOM / 'sfx_real/.sfx-work/recordings'
FPS = 30


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def options(case):
    rows = []
    for name in LIB['cases'][case]['steps']:
        spec = LIB['steps'][name]
        rows.append([dict(step=name, tool=spec['tool'], target=spec['target'], pmid=spec['pmid'],
                          caption=caption, thumbnail=spec['thumbnail']) for caption in spec['captions']])
    return rows


def resolve(case, authored):
    """Unknown fields and permutations cannot change the immutable source timeline."""
    allowed = options(case)
    default = [row[0] for row in allowed]
    if not isinstance(authored, dict) or set(authored) != {'steps'}:
        return default, ['invalid envelope']
    rows = authored['steps']
    if not isinstance(rows, list) or len(rows) != len(allowed):
        return default, ['invalid step count']
    repairs = []
    for i, (row, choices) in enumerate(zip(rows, allowed, strict=True)):
        if row in choices:
            default[i] = row
        else:
            repairs.append(choices[0]['step'])
    return default, repairs


def timeline(case, rows):
    topic = LIB['cases'][case]
    # The uninterrupted 60-frame cold open straddles the playback boundary.
    hook = topic['hook_shot']
    segments = [(hook, 24, 60, topic['hook'], None)]
    for i,row in enumerate(rows,1):
        spec = LIB['steps'][row['step']]
        segments.append((row['step'], 0, spec['frames'], row['caption'], (i,len(rows),spec['stage'])))
    segments.append((hook,0,24,topic['hook'],None))
    return segments


def assets(case):
    uses = {str(cue[0]) for name in LIB['cases'][case]['steps'] for cue in LIB['steps'][name]['sfx']}
    expected = {SCENE: LIB['archive'][str(SCENE.relative_to(WISDOM))], MUSIC: LIB['music_sha256']}
    expected.update({WISDOM/name: LIB['archive'][name] for name in ['LICENCE_AUDIT.md','sfx_real/SOURCES_AUDIO.md']})
    expected.update({FONTS/name: sha for name,sha in LIB['fonts'].items()})
    expected.update({DB/'obj/isa_BP3D_4.0_obj_99'/(name+'.obj'): sha for name,sha in LIB['dbcls'].items() if name not in ('FJ3269','FJ3375')})
    expected.update({WORK/name: sha for name,sha in LIB['source_files'].items()})
    expected.update({RECORDINGS/(i+'.mp3'): LIB['audio'][i]['sha256'] for i in uses})
    for path, expected_sha in expected.items():
        if digest(path) != expected_sha:
            raise ValueError(f'Asset differs from licence manifest: {path}')
    return {str(p): h for p,h in expected.items()}
