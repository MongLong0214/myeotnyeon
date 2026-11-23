#!/usr/bin/env python3
"""Attribution lives in the video description (owner: no in-video credit). usage: python description_gate.py EPISODE_DIR -> JSON, exit 1 on fail.
description.txt must carry: the DBCLS BodyParts3D string verbatim, the source link, the CC BY 4.0 link, the changes made, and the other credited assets (CC0 base mesh, HDRI, fonts, narration voice)."""
import sys, os, json
REQ = {'dbcls_string': 'BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International', 'source_link': 'https://dbarchive.biosciencedbc.jp/en/bodyparts3d/',
       'cc_by_link': 'https://creativecommons.org/licenses/by/4.0/', 'changes': 'Changes made by us', 'other_assets': 'Poly Haven', 'narration_voice': 'Qwen3-TTS'}
def check_description(path, *, narrated=True):
    if not os.path.exists(path): return False, {'error': 'no description.txt'}
    t = open(path, encoding='utf-8').read(); miss = [k for k, v in REQ.items() if (narrated or k != 'narration_voice') and v not in t]
    # public text only: no markdown tables/bold, no internal paths, no build notes
    miss += [f'internal_markup:{m}' for m in ('| ', '**', 'anat_kit/', 'draft', '.blend', 'Screen says') if m in t]
    if any(line.lstrip().startswith('|') and line.count('|') > 1 for line in t.splitlines()):
        miss.append('internal_markup:table row')
    return not miss, {'missing': miss, 'chars': len(t)}
if __name__ == '__main__':
    ok, r = check_description(os.path.join(sys.argv[1], 'description.txt')); print(json.dumps({'ok': ok, **r}, ensure_ascii=False)); sys.exit(0 if ok else 1)
