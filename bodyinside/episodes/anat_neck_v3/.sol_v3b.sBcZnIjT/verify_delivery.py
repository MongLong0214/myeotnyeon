import hashlib
import json
import os
from pathlib import Path
import subprocess

stage = Path(__file__).resolve().parent
root = stage.parent
tag = 'final_hq_v3b'
approved = root / '.sol_v3.mNVBQ6v4'
video = stage / f'{tag}.mp4'

def ffprobe(path, *args):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', *args, '-of', 'json', str(path)]))

def streamhash(path):
    return subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0',
                                    '-c:a', 'copy', '-f', 'streamhash', '-hash', 'sha256', '-'], text=True).strip()

stream_filter = ('-show_entries', 'stream=index,codec_name,codec_type,r_frame_rate,time_base,start_time,duration,nb_frames,width,height')
old = ffprobe(root / 'final_hq_v3.mp4', *stream_filter)
new = ffprobe(video, *stream_filter)
assert old == new, (old, new)
audio = streamhash(video)
draft = root / 'draft4.mp4'
assert audio == streamhash(draft) == streamhash(root / 'final_hq_v3.mp4')
audio_filter = ('-select_streams', 'a:0', '-show_streams', '-show_data_hash', 'sha256',
                '-show_entries', 'stream=codec_name,time_base,duration_ts,initial_padding,extradata_hash')
assert ffprobe(video, *audio_filter)['streams'] == ffprobe(draft, *audio_filter)['streams']
packet_filter = ('-select_streams', 'a:0', '-show_packets', '-show_data_hash', 'sha256',
                 '-show_entries', 'packet=pts,dts,duration,size,flags,data_hash:packet_side_data')
assert ffprobe(video, *packet_filter) == ffprobe(draft, *packet_filter)

for frame in [*range(301), *range(726, 761), *range(819, 924)]:
    old_path = approved / 'frames_final_hq_v3' / f'f_{frame:04}.png'
    new_path = stage / f'frames_{tag}' / old_path.name
    assert os.path.samefile(old_path, new_path) or old_path.read_bytes() == new_path.read_bytes(), frame
for name in ('episode.json', 'thresholds.json'):
    assert (stage/name).read_bytes() == (approved/name).read_bytes()
assert os.path.samefile(stage/'comp', approved/'comp')
old_labels, new_labels = [json.loads((d/'label_pos.json').read_text()) for d in (approved, stage)]
assert set(old_labels) == set(new_labels)
assert {key for key in old_labels if old_labels[key] != new_labels[key]} <= {str(f) for f in range(761,819)}
assert old_labels['_plumb'] == new_labels['_plumb']

status = {}
for group in ('gates', 'checks', 'provenance', 'facts', 'defects_meta', 'penetration', 'audio',
              'narration', 'description', 'credit_ui'):
    data = json.loads((stage / 'gates' / f'{tag}_{group}.json').read_text())
    status[group] = data.get('pass', data.get('ok'))
    if group in ('gates', 'checks'):
        items = [value for value in data.values() if isinstance(value, dict) and 'ok' in value]
        print(group, f'{sum(value["ok"] for value in items)}/{len(items)}')
        print({key: value for key, value in data.items() if isinstance(value, dict) and not value.get('ok', True)})
print(status)
print(new)
print(audio)
print('SHA256', hashlib.file_digest(video.open('rb'), 'sha256').hexdigest())
assert all(status.values()), status
