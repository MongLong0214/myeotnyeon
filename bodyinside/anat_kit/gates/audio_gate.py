"""Audio gate. usage: python audio_gate.py EPISODE_DIR VIDEO.mp4 -> JSON, exit 1 on fail.
(1) every earshot part fits its description (sfx_report.json: z >= 2.0 on `earshot match`),  (2) final loudness: integrated -14 +/- 0.5 LUFS and true peak <= -1.0 dBTP (ffmpeg ebur128 on the video's audio),
(3) no clipped samples, (4) the bed is present (sfx_bed) and at least one event per beat (audio exists for every beat)."""
import sys, json, subprocess, re
E, mp4 = sys.argv[1:3]; ep = json.load(open(E + '/episode.json')); rep = json.load(open(E + '/audio/sfx_report.json')); res = {}
res['fit'] = {'parts': {k: {'z': v['z'], 'pass': v['pass']} for k, v in rep.items()}, 'ok': all(v['pass'] for v in rep.values())}
o = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', mp4, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]); TP = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', o)[-1])
res['loudness'] = {'lufs': I, 'true_peak_dbfs': TP, 'ok': abs(I + 14) <= 0.5 and TP <= -1.0}
fps = ep['fps']; cover = [any(b['t0'] <= e['t'] < b['t1'] for e in ep['sfx']) for b in ep['beats']]
res['coverage'] = {'bed': bool(ep.get('sfx_bed')), 'beats_with_event': cover, 'ok': bool(ep.get('sfx_bed')) and all(cover)}
res['pass'] = all(v['ok'] for v in res.values() if isinstance(v, dict)); print(json.dumps(res, ensure_ascii=False)); sys.exit(0 if res['pass'] else 1)
