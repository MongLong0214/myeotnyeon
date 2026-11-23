"""Regenerates the regression fixtures: inputs that MUST make their check fail. usage: python make_fixtures.py (writes next to this file). Synthetic on purpose: no media is committed."""
import json, os, numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__))
def w(rel, obj):
    p = os.path.join(H, rel); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, 'w'))
# caption truth: caption claims the curve changes by >= 15 deg but the pose is the same
ep = {'beats': [{'t0': 0, 't1': 1, 'cap': [['x', [255, 255, 255]]], 'evidence': [{'type': 'pose_delta', 'joints': [0, 1, 2], 'f0': 0, 'f1': 10, 'min_deg': 15}]}], 'labels': []}
w('caption-claims-something-not-shown/episode.json', ep); w('caption-claims-something-not-shown/pose_dump.json', {str(f): [1, 1, 1, 0, 0, 0, 0, 0] for f in range(11)}); w('caption-claims-something-not-shown/scene_dump.json', {})
# ending claims ear/shoulder but the shoulder anchor is outside the band
ep2 = {'beats': [{'t0': 0, 't1': 1, 'cap': [['x', [255, 255, 255]]], 'evidence': [{'type': 'anchors_visible', 'anchors': ['A_Ear', 'A_Acro'], 'frames': [5]}]}], 'labels': []}
w('ear-shoulder-not-in-frame/episode.json', ep2); w('ear-shoulder-not-in-frame/label_pos.json', {'5': {'A_Ear': [0.5, 0.3], 'A_Acro': [0.7, 1.4]}}); w('ear-shoulder-not-in-frame/pose_dump.json', {}); w('ear-shoulder-not-in-frame/scene_dump.json', {})
# subject too small: a 350x600 subject in a 1080x800 band
os.makedirs(os.path.join(H, 'subject-too-small/frames'), exist_ok=True)
for i in range(30):
    a = np.zeros((800, 1080, 4), np.uint8); a[100:700, 360:710] = (200, 190, 170, 255); Image.fromarray(a).save(os.path.join(H, 'subject-too-small/frames/f_%04d.png' % i))
# rigid bend: whole rotation in one joint
w('rigid-bend/pose_dump.json', {str(f): [60, 0, 0, 0, 0, 0, 0, 0] for f in range(5)})
# leader lines crossing: two callouts whose leaders cross
w('leader-lines-crossing/episode.json', {'beats': [], 'labels': [{'id': 'a', 'kind': 'callout', 'anchor': 'A', 'f0': 0, 'f1': 9, 'dx': 260, 'dy': -150}, {'id': 'b', 'kind': 'callout', 'anchor': 'B', 'f0': 0, 'f1': 9, 'dx': -260, 'dy': -150}]})
w('leader-lines-crossing/label_pos.json', {'3': {'A': [0.40, 0.60], 'B': [0.60, 0.50]}})
# the fixture above must trip the *raw offsets*: checks.leaders_cross applies the same auto-layout as labels2d, so also give a raw variant
w('leader-lines-crossing/label_pos_raw.json', {'3': {'A': [0.40, 0.60], 'B': [0.60, 0.50]}})
# unreadable small text
w('unreadable-small-text/episode.json', {'beats': [], 'labels': [{'id': 'n', 'kind': 'note', 'size': 24, 'f0': 0, 'f1': 9, 'text': 'x'}, {'id': 'c', 'kind': 'callout', 'size': 40, 'f0': 0, 'f1': 9, 'text': 'x'}]})
print('fixtures written')
# dead time: 4 s of identical frames with no declared event
os.makedirs(os.path.join(H, 'dead-time-no-event/frames'), exist_ok=True)
for i in range(120):
    a = np.zeros((800, 1080, 4), np.uint8); a[100:700, 200:900] = (180, 170, 150, 255); Image.fromarray(a).save(os.path.join(H, 'dead-time-no-event/frames/f_%04d.png' % i))
w('dead-time-no-event/episode.json', {'beats': [{'t0': 0, 't1': 4}], 'labels': []})

# visibility window: arc still visible at f200 although its windows end at 135
w('arc-visible-outside-beats/scene_dump.json', {'CurveLine': {str(f): 1.0 for f in range(300)}})
# blinking glow: on/off three times
w('muscle-glow-blinks/scene_dump.json', {'MuscleGlow': {str(f): (1.0 if (f // 10) % 2 == 0 else 0.0) for f in range(100)}})
# reversed C weaker than the C
w('reversed-curve-weak/pose_dump.json', {'380': [-4, -5, -6, -5, -4, -3, 0, 0], '510': [1, 1, 1, 1, 1, 1, 0, 0]})
# ear and acromion on top of each other
w('plumb-landmarks-too-close/label_pos.json', {'9': {'A_Ear': [0.5, 0.50], 'A_Acro': [0.5, 0.55]}})
# no red pixels at the contact
os.makedirs(os.path.join(H, 'herniation-not-visible/frames'), exist_ok=True)
for i in range(0, 12):
    a = np.zeros((400, 540, 4), np.uint8); a[100:300, 100:400] = (200, 190, 170, 255); a[200:210, 250:260] = (230, 190, 160, 255); Image.fromarray(a).save(os.path.join(H, 'herniation-not-visible/frames/f_%04d.png' % i))
# load arrow without a second anchor
w('load-arrow-in-air/episode.json', {'beats': [], 'labels': [{'id': 'k', 'kind': 'load', 'anchor': 'A_Head', 'f0': 0, 'f1': 9, 'kg': 12, 'text': 'x'}]})

w('label-spans-caption-change/episode.json', {'beats': [{'t0': 0, 't1': 10}, {'t0': 10, 't1': 20}], 'labels': [{'id': 'x', 'kind': 'note', 'f0': 250, 'f1': 400}]})
w('audio-poor-fit/sfx_report.json', {'tick': {'z': 0.9, 'pass': False}})

# opening speck: tiny static subject, no motion
os.makedirs(os.path.join(H, 'opening-speck/frames'), exist_ok=True)
for i in range(20):
    a = np.zeros((800, 1080, 4), np.uint8); a[300:400, 480:600] = (200, 190, 170, 255); Image.fromarray(a).save(os.path.join(H, 'opening-speck/frames/f_%04d.png' % i))
# legend covering the subject anchor
w('graphics-cover-subject/episode.json', {'beats': [], 'labels': [{'id': 'lg', 'kind': 'legend', 'f0': 0, 'f1': 9, 'dx': 100, 'dy': 100}]}); w('graphics-cover-subject/label_pos.json', {'0': {'A_Contact': [0.2, 0.2], 'A_C56': [0.9, 0.9], 'A_Root': [0.9, 0.9]}})
# landmark marker missing at the ending
w('landmark-marker-missing/scene_dump.json', {'EarMarker': {str(f): 0.0 for f in range(990)}})
# bass-only audio
import soundfile as sf
t = np.arange(48000 * 4) / 48000; sf.write(os.path.join(H, 'audio-bass-only.wav'), (0.3 * np.sin(2 * np.pi * 80 * t)).astype(np.float32), 48000)
os.makedirs(os.path.join(H, 'audio-bass-only'), exist_ok=True); os.replace(os.path.join(H, 'audio-bass-only.wav'), os.path.join(H, 'audio-bass-only/sfx.wav'))

w('plumb-line-jog/episode.json', {'beats': [{'t0': 0, 't1': 1, 'cap': [['x', [255, 255, 255]]], 'evidence': [{'type': 'anchors_aligned', 'a': 'A_Ear', 'b': 'A_Acro', 'frames': [9], 'max_dx': 0.04}]}], 'labels': []}); w('plumb-line-jog/label_pos.json', {'9': {'A_Ear': [0.60, 0.2], 'A_Acro': [0.45, 0.7]}}); w('plumb-line-jog/pose_dump.json', {}); w('plumb-line-jog/scene_dump.json', {})
w('hook-event-late/episode.json', {'beats': [{'t0': 0, 't1': 1, 'cap': [['x', [255, 255, 255]]], 'evidence': [{'type': 'dump_change', 'key': 'VertebraTint', 'f0': 0, 'f1': 12, 'min': 0.5}]}], 'labels': []}); w('hook-event-late/scene_dump.json', {'VertebraTint': {str(f): 0.9 for f in range(30)}}); w('hook-event-late/pose_dump.json', {})
w('bottom-space-unused/episode.json', {'layout': {'band_y': 520, 'band_h': 800}})

w('shoulder-dot-on-spine/label_pos.json', {'_plumb': {'900': {'in_skin': True, 'outside_spine_bbox': False, 'ear_above': True}}})
w('plumb-pill-covers-dot/episode.json', {'beats': [], 'labels': [{'id': 'p', 'kind': 'plumb', 'f0': 0, 'f1': 9, 'pill_dx': 60, 'pill_half_w': 70}]})
os.makedirs(os.path.join(H, 'audio-quiet-beat'), exist_ok=True)
t = np.arange(48000 * 6) / 48000; sig = 0.3 * np.sin(2 * np.pi * 900 * t); sig[48000 * 3:] *= 0.1; sf.write(os.path.join(H, 'audio-quiet-beat/sfx.wav'), sig.astype(np.float32), 48000)
w('hidden-object-renders-dark/scene_dump.json', {'SkinRender': {str(f): 1.0 for f in range(300)}})
# review 6: plumb drawn with the shoulder dot floating 80 px off the projected acromion and the label 120 px from its dot (the draft10 ending)
w('plumb-dots-off-landmarks/label_pos.json', {'_plumb': {'900': {'ear': [0.40, 0.30], 'shoulder': [0.40, 0.70], 'in_skin': True, 'ear_in_skin': True, 'outside_spine_bbox': True, 'ear_above': True, 'ear_in_outline': True}}})
w('plumb-dots-off-landmarks/plumb_draw.json', {'900': {'k': 1.0, 'ear': [432.0, 264.0], 'acro': [512.0, 616.0], 'line': [[432.0, 264.0], [512.0, 616.0]], 'poly': [[410, 240], [455, 240], [455, 290], [410, 290]], 'pill_ear': [300, 245, 400, 285], 'pill_acro': [250, 600, 350, 640]}})
# review 7: ear dot and outline over the cerebellum, 130 px behind the jaw joint (draft11 f970)
w('ear-behind-jaw-joint/label_pos.json', {'_plumb': {'900': {'ear': [0.40, 0.30], 'shoulder': [0.40, 0.70], 'in_skin': True, 'ear_in_skin': True, 'outside_spine_bbox': True, 'ear_above': True, 'ear_in_outline': True}}})
w('ear-behind-jaw-joint/plumb_draw.json', {'900': {'k': 1.0, 'ear': [432.0, 264.0], 'acro': [432.0, 616.0], 'tmj': [562.0, 300.0], 'line': [[432.0, 264.0], [432.0, 616.0]], 'poly': [[410, 240], [455, 240], [455, 290], [410, 290]], 'pill_ear': [450, 245, 520, 285], 'pill_acro': [330, 600, 400, 640]}})
