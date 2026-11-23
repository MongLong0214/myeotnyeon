"""Measure visible instruments and fitted points against the evaluated tooth and supporting tissue."""
from pathlib import Path
import json
import os
import sys

import bpy

episode = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(episode.parents[1] / 'anat_kit/gates'))
from penetration_gate import MeshCache, measure, use_render_modifiers

scene = bpy.context.scene
instruments = [o for o in scene.objects if o.get('instrument') or o.name.startswith(('Gutta-percha point', 'Dental dam wire frame', 'Bent irrigation connection'))]
targets = [o for o in scene.objects if o.get('mineralized') or o.name.startswith(('FJ1253', 'M1 • periodontal ligament', 'Bonded access core', 'Prepared access core', 'Ceramic crown in section'))]
use_render_modifiers(instruments + targets)
cache = MeshCache()
last_time = {}
measurements = {}
frames = []
requested = os.getenv('CONTACT_FRAMES')
indices = [int(i) for i in requested.split(',')] if requested else range(scene.frame_start, scene.frame_end + 1)
for f in indices:
    scene.frame_set(f)
    graph = bpy.context.evaluated_depsgraph_get()
    tools = [o for o in instruments if not o.hide_render]
    tissue = [o for o in targets if not o.hide_render] if tools else []
    for o in tools:
        keys = o.data.shape_keys
        if keys and not keys.use_relative and keys.eval_time != last_time.get(o.name):
            cache.local.pop(o.name, None)
            cache.world.pop(o.name, None)
            last_time[o.name] = keys.eval_time
    rows = []
    for tool in tools:
        a = cache.get(tool, graph, f)
        for target in tissue:
            pair = (tool.name, target.name)
            b = cache.get(target, graph, f)
            old = measurements.get(pair)
            if old and old[0] is a and old[1] is b:
                depth, count = old[2:]
            else:
                depth, count = measure(a, b)
                measurements[pair] = (a, b, depth, count)
            if depth or count:
                rows.append(dict(tool=tool.name, target=target.name, depth_mm=round(depth, 6), crossings=count))
    frames.append(dict(frame=f, pairs=len(tools)*len(tissue), contacts=rows))
    if requested or f % 30 == 0:
        print('CONTACT', f, [(r['tool'],r['target'],r['depth_mm']) for r in rows if r['depth_mm'] > .2], flush=True)

peak = max((r['depth_mm'] for frame in frames for r in frame['contacts']), default=0)
failed = [frame['frame'] for frame in frames if any(r['depth_mm'] > .2 for r in frame['contacts'])]
out = episode / ('production/.cache/contact-sample.json' if requested else 'penetration_report.json')
out.write_text(json.dumps(dict(ok=not failed, threshold_mm=.2, max_depth_mm=peak, failed_frames=failed, frames=frames), ensure_ascii=False))
print('RESULT', out, peak, len(failed), flush=True)
