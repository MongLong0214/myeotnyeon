"""Compare every boundary PNG and make labeled before/after contact sheets."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, math, hashlib
import numpy as np
P = Path(__file__).resolve().parent
manifest = json.loads((P/'manifest-before.json').read_text())
report = []
for item in manifest:
    name = item['name']; frames = list(range(item['from'], item['to'] + 1))
    changed = []; images = {}
    for stage in ['before', 'after']:
        images[stage] = [Image.open(P/stage/name/f'f{f:05}.png').convert('RGB') for f in frames]
    for f, a, b in zip(frames, images['before'], images['after']):
        if not np.array_equal(np.asarray(a), np.asarray(b)): changed.append(f)
    expected = [] if item.get('aligned') else list(range(item['outroFrom'], 879 if name == 'v3_q003' else item['fullEndFrom']))
    assert changed == expected, (name, changed, expected)
    # Pixel probe in the top of the actual scene panel, clear of CTA lettering.
    # A night-lot render is the reference, not a detector applied to other episodes.
    ref = np.asarray(images['before'][frames.index(item['outroFrom'])], dtype=float)[130:145, 35:225]
    probe = []
    for f in expected:
        i = frames.index(f)
        before = np.asarray(images['before'][i], dtype=float)[130:145, 35:225]
        after = np.asarray(images['after'][i], dtype=float)[130:145, 35:225]
        old_mae = float(np.abs(before - ref).mean()); new_mae = float(np.abs(after - ref).mean())
        assert old_mae < 10 and new_mae > 25, (name, f, old_mae, new_mae)
        probe.append({'frame': f, 'before_night_reference_mae': round(old_mae, 3), 'after_night_reference_mae': round(new_mae, 3)})
    cols = 8; rows = math.ceil(len(frames) / cols); tw, th = 135, 262
    strip = Image.new('RGB', (cols*tw, 60 + rows*th*2), '#20242b'); draw = ImageDraw.Draw(strip)
    for si, stage in enumerate(['before','after']):
        y0 = 30 + si * (rows*th+30); draw.text((8, y0-22), f'{name} | {stage.upper()} | 270x480 render, thumbnail 135x240 | every frame', fill='white')
        for i, (f, im) in enumerate(zip(frames, images[stage])):
            x, y = (i % cols)*tw, y0+(i//cols)*th
            draw.rectangle((x,y,x+tw-1,y+th-1), fill='#56252b' if f in changed else '#20242b')
            draw.text((x+4,y+3), f'f{f}', fill='white')
            strip.paste(im.resize((135,240)), (x,y+20))
    strip.save(P/f'strip_{name}.jpg', quality=95, subsampling=0)
    report.append({**item, 'changed_frames': changed, 'all_other_rendered_frames_pixel_identical': True, 'night_reference_probe': probe})
(P/'boundary-results.json').write_text(json.dumps(report, indent=2))
print(json.dumps([{k:r[k] for k in ['name','frames','changed_frames','all_other_rendered_frames_pixel_identical']} for r in report], indent=2))
