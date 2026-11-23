"""Mesh provenance gate. usage: Blender -b EPISODE.blend -P provenance_gate.py -- OUT.json
Every renderable object (MESH/CURVE/FONT) must carry custom property `src`:
  "bp3d:<FMA>:<FJ file id>:<sha256>"  (parts joined with ' | ', optional ' (derived)' suffix)  -> the sha256 must equal the hash of that file in the DBCLS Release 4.0 archive on disk
  "own"                                                                                         -> built by us (procedural)
Anything else, a missing property, a hash mismatch, or any trace of Z-Anatomy ('zanatomy' path, 'White matter', Z-Anatomy material names) FAILS.
Z-Anatomy-derived wisdom assets are NOT covered by the DBCLS notice and must never pass this gate."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from asset_paths import asset
import bpy, sys, json, hashlib, os, re
OUT = sys.argv[sys.argv.index('--') + 1]
BP = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../research/anatomy3d/bodyparts3d_4.0/obj/isa_BP3D_4.0_obj_99/')
BAD = re.compile(r'zanatomy|z-anatomy|white matter', re.I); res = {'objects': 0, 'bp3d_parts': 0, 'own': 0, 'fail': []}
cache = {}
def sha(p):
    if p not in cache: cache[p] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    return cache[p]
for o in bpy.data.objects:
    if o.type not in ('MESH', 'CURVE', 'CURVES', 'FONT'): continue
    res['objects'] += 1; src = o.get('src', ''); txt = ' '.join([o.name, str(src)] + [m.name for m in o.data.materials if m])
    if BAD.search(txt): res['fail'].append({'obj': o.name, 'why': 'Z-Anatomy trace', 'src': str(src)[:80]}); continue
    if not src: res['fail'].append({'obj': o.name, 'why': 'no src property'}); continue
    if src == 'own' or src.startswith('own:'): res['own'] += 1; continue
    if src.startswith('cc0:human_base_meshes_bundle_v1.4.1:'):   # CC0 asset: sha256 of the bundle .blend must match the file on disk
        hb = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../research/anatomy3d/human_base_meshes/x/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend')
        if os.path.exists(hb) and sha(hb) == src.split(':')[-1]: res['cc0'] = res.get('cc0', 0) + 1
        else: res['fail'].append({'obj': o.name, 'why': 'cc0 hash mismatch'})
        continue
    if src.startswith('astra:'):   # Astra's character (MakeHuman/MPFB CC0 assets, own build script) + Mixamo mocap: astra:<sha256 human_final.blend>|mocap:<sha256 Texting>:<sha256 Looking Down>; hashes must equal the files on disk (astra_human/SOURCES.md)
        ak = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'astra_human'); hs = re.fullmatch(r'astra:([0-9a-f]{64})\|mocap:([0-9a-f]{64}):([0-9a-f]{64})', src)
        fl = [asset('astra_human/human_final.blend'), asset('assets/mocap/Texting While Standing.fbx'), asset('assets/mocap/Looking Down.fbx')]
        if hs and all(os.path.exists(p) and sha(p) == h for p, h in zip(fl, hs.groups())): res['astra_character'] = res.get('astra_character', 0) + 1
        else: res['fail'].append({'obj': o.name, 'why': 'astra/mocap hash mismatch or bad format'})
        continue
    if src.startswith('mpfb:'):   # MPFB2 (CC0 output) human + Mixamo mocap: mpfb:<sha256 human_mpfb.blend>|mocap:<sha256 Texting>|<sha256 Looking Down>|<sha256 Standing Idle>; every hash must equal the file on disk
        ak = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets'); hs = re.fullmatch(r'mpfb:([0-9a-f]{64})\|mocap:([0-9a-f]{64})\|([0-9a-f]{64})\|([0-9a-f]{64})', src)
        fl = [asset('assets/mpfb/human_mpfb.blend')] + [asset('assets/mocap/' + n + '.fbx') for n in ('Texting While Standing', 'Looking Down', 'Standing Idle')]
        if hs and all(os.path.exists(p) and sha(p) == h for p, h in zip(fl, hs.groups())): res['mpfb_mocap'] = res.get('mpfb_mocap', 0) + 1
        else: res['fail'].append({'obj': o.name, 'why': 'mpfb/mocap hash mismatch or bad format'})
        continue
    if src.startswith('ext:'):   # asset from the approved-source list (approved_sources.json, from research/public_assets_survey.md): ext:<id>:<sha256>
        _a = {x['id']: x for x in json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'approved_sources.json')))}
        _id = src.split(':')[1]
        if _id not in _a or _a[_id]['verdict'] == 'EXCLUDE': res['fail'].append({'obj': o.name, 'why': 'source not approved or EXCLUDE', 'src': _id})
        else:
            row = _a[_id]
            licensed_file = row.get('local_file','').removeprefix('anat_kit/')
            path = asset(licensed_file) if licensed_file else ''
            if not row.get('sha256') or not os.path.isfile(path) or sha(path) != row['sha256'] or src.split(':')[-1] != row['sha256']:
                res['fail'].append({'obj':o.name,'why':'missing verified local asset or hash mismatch','src':_id})
            else:
                res['ext'] = res.get('ext',0)+1
                if row['verdict']=='USE-WITH-CREDIT': res.setdefault('credit_required',[]).append(_id)
        continue
    for part in src.replace(' (derived)', '').split(' | '):
        m = re.fullmatch(r'bp3d:(FMA\d+):(FJ\w+):([0-9a-f]{64})', part.strip())
        if not m: res['fail'].append({'obj': o.name, 'why': 'bad src format', 'src': part[:60]}); continue
        f = BP + m.group(2) + '.obj'
        if not os.path.exists(f): res['fail'].append({'obj': o.name, 'why': 'file missing', 'file': m.group(2)})
        elif sha(f) != m.group(3): res['fail'].append({'obj': o.name, 'why': 'sha256 mismatch', 'file': m.group(2)})
        else: res['bp3d_parts'] += 1
for im in bpy.data.images:
    if BAD.search(im.filepath or ''): res['fail'].append({'image': im.name, 'why': 'Z-Anatomy path'})
res['ok'] = not res['fail']; json.dump(res, open(OUT, 'w'), indent=1); print('PROVENANCE', json.dumps(res)[:400]); sys.exit(0)
