#!/usr/bin/env python3
"""Download Poly Haven (CC0) assets: models/textures as .blend+textures, HDRIs as .hdr.
Usage: ph_get.py RES id [id ...]   (RES: 1k/2k/4k)"""
import json, sys, os, urllib.request, hashlib, pathlib
res = sys.argv[1]
root = pathlib.Path(__file__).parent
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'verdict-kr-asset-fetch'}), timeout=120).read()
for aid in sys.argv[2:]:
    info = json.loads(get(f'https://api.polyhaven.com/info/{aid}'))
    files = json.loads(get(f'https://api.polyhaven.com/files/{aid}'))
    d = root / aid; d.mkdir(exist_ok=True)
    got = []
    if 'hdri' in files:
        r = files['hdri'][res]['hdr']; b = get(r['url']); (d / os.path.basename(r['url'])).write_bytes(b); got.append(r['url'])
    else:
        blend = files['blend'][res]['blend']
        b = get(blend['url']); (d / os.path.basename(blend['url'])).write_bytes(b); got.append(blend['url'])
        for rel, f in blend.get('include', {}).items():
            p = d / rel; p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists(): p.write_bytes(get(f['url']))
            got.append(f['url'])
    src = dict(id=aid, name=info.get('name'), type=info.get('type'), authors=info.get('authors'), license='CC0 1.0 (Poly Haven)',
               license_url='https://polyhaven.com/license', page=f'https://polyhaven.com/a/{aid}', resolution=res, files=got)
    (d / 'source.json').write_text(json.dumps(src, ensure_ascii=False, indent=1))
    print('ok', aid, len(got), 'files')
