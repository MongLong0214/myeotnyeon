#!/usr/bin/env python3
"""Technical QA for EP001 final.mp4 → qa_tech.json + qa_frames/*.jpg.

Measures, not opinions: stream format, exact frame count, anchors, loudness, black/silent
stretches, and subtitle↔speech sync (Whisper word timestamps on the final mix vs SRT cues).
"""
import json, pathlib, subprocess, re, sys, statistics

HERE = pathlib.Path(__file__).parent
MP4 = HERE / (sys.argv[1] if len(sys.argv) > 1 else 'final.mp4')
OUT = HERE / 'qa_frames'; OUT.mkdir(exist_ok=True)
FPS = 30
res = {}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


p = json.loads(run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(MP4)]).stdout)
v = next(s for s in p['streams'] if s['codec_type'] == 'video'); a = next(s for s in p['streams'] if s['codec_type'] == 'audio')
res['format'] = dict(width=v['width'], height=v['height'], fps=v['avg_frame_rate'], frames=int(v['nb_read_frames']), vcodec=v['codec_name'],
                     pix_fmt=v.get('pix_fmt'), color_primaries=v.get('color_primaries'), acodec=a['codec_name'], sample_rate=int(a['sample_rate']),
                     channels=a['channels'], duration=float(p['format']['duration']))
res['format_ok'] = (v['width'], v['height']) == (1920, 1080) and v['avg_frame_rate'] in ('30/1', '30') and int(v['nb_read_frames']) == 14400 and int(a['sample_rate']) == 48000

# loudness of the delivered file
e = run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(MP4), '-map', '0:a', '-af', 'ebur128=peak=true', '-f', 'null', '-']).stderr
I = re.findall(r'I:\s+(-?[\d.]+) LUFS', e); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', e); LRA = re.findall(r'LRA:\s+([\d.]+) LU', e)
res['loudness'] = dict(integrated_lufs=float(I[-1]), true_peak_dbfs=float(TP[-1]), lra=float(LRA[-1]))
res['loudness_ok'] = abs(res['loudness']['integrated_lufs'] + 16) <= 1 and res['loudness']['true_peak_dbfs'] <= -1.0

# black and silence stretches
bd = run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(MP4), '-vf', 'blackdetect=d=0.5:pix_th=0.06', '-an', '-f', 'null', '-']).stderr
res['black_segments'] = [tuple(map(float, m)) for m in re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', bd)]
sd = run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(MP4), '-vn', '-af', 'silencedetect=n=-50dB:d=0.4', '-f', 'null', '-']).stderr
res['silences'] = [(float(s), float(t)) for s, t in zip(re.findall(r'silence_start: ([\d.]+)', sd), re.findall(r'silence_end: ([\d.]+)', sd))]
res['silence_before_verdict'] = [s for s in res['silences'] if s[1] >= 329.3 and s[0] <= 330.0]

# frame grabs at every cue boundary + anchors
script = json.load(open(HERE / 'script.json'))
grabs = sorted({c['in_frame'] + 15 for c in script['cues']} | {720, 9900 + 20, 13800 + 10, 14399})
for f in grabs:
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(MP4), '-vf', f'select=eq(n\\,{f}),scale=640:-2', '-frames:v', '1', str(OUT / f'f{f:05d}.jpg')])
res['frame_grabs'] = len(grabs)

# subtitle ↔ speech sync via Whisper on the final mix
try:
    import mlx_whisper
    wav = HERE / 'qa_frames' / 'final_16k.wav'
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(MP4), '-ac', '1', '-ar', '16000', str(wav)])
    r = mlx_whisper.transcribe(str(wav), path_or_hf_repo='mlx-community/whisper-large-v3-turbo', language='ko', word_timestamps=True)
    starts = [s['start'] for s in r['segments']]
    timing = json.load(open(HERE / 'timing.json'))
    na = [(it['start'] / FPS, it['end'] / FPS) for it in timing['items']]
    offs = []
    for s0, _ in na:
        near = min(starts, key=lambda x: abs(x - s0)) if starts else None
        if near is not None and abs(near - s0) < 2.0:
            offs.append(near - s0)
    res['sync'] = dict(sentences=len(na), matched=len(offs), median_offset_s=round(statistics.median(offs), 3) if offs else None,
                       p90_abs_offset_s=round(sorted(abs(o) for o in offs)[int(len(offs) * 0.9) - 1], 3) if offs else None)
    res['asr_text_chars'] = len(''.join(s['text'] for s in r['segments']).replace(' ', ''))
except Exception as ex:  # ASR is a check, not a gate
    res['sync'] = dict(error=str(ex))
json.dump(res, open(HERE / 'qa_tech.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ('format', 'format_ok', 'loudness', 'loudness_ok', 'black_segments', 'silence_before_verdict', 'sync')}, ensure_ascii=False, indent=1))
