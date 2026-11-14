"""Narration + a few synthesized SFX, two-pass loudnorm to -14 LUFS / -1.5 dBTP, mux with video_muted.mp4.
SFX events come from the spec ('sfx': [[shot_mode, frame_offset, kind], ...]) plus card pops and the answer gavel.
usage: mix.py <qid>"""
import sys, json, re, subprocess
from pathlib import Path
import numpy as np, soundfile as sf
D = Path(__file__).resolve().parent; W = D.parents[3]; SR = 48000
def env(n, a): t = np.arange(n) / SR; return np.exp(-t * a)
def thud(amp=.5):
    n = int(.28 * SR); t = np.arange(n) / SR; f = 70 + 60 * np.exp(-t * 30)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 14) + .35 * np.random.default_rng(1).normal(0, 1, n) * env(n, 60)
    return amp * y
def knock(amp=.45):
    n = int(.18 * SR); t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * 180 * t) + .6 * np.sin(2 * np.pi * 410 * t) + .3 * np.sin(2 * np.pi * 950 * t)) * env(n, 32)
    return amp * y / 1.9
def tick(amp=.16, hz=880):
    n = int(.09 * SR); t = np.arange(n) / SR; return amp * np.sin(2 * np.pi * hz * t) * env(n, 45)
def clank(amp=.22):
    n = int(.5 * SR); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * h * t) * env(n, d) for h, d in [(523, 9), (1310, 12), (2280, 16)]) / 3
    return amp * y
def whoosh(amp=.12, dur=.35):
    n = int(dur * SR); x = np.random.default_rng(2).normal(0, 1, n); w = np.hanning(n)
    y = np.convolve(x, np.ones(24) / 24, 'same') * w; return amp * y / np.max(np.abs(y))
KIND = dict(thud=thud, knock=knock, tick=tick, clank=clank, whoosh=whoosh)
def main(q):
    P = W / 'upload/pkg' / f'{q}_B'; c = json.loads((P / 'case.json').read_text()); spec = json.loads((D / 'specs' / f'{q}.json').read_text())
    x, sr = sf.read(P / 'narration.wav', dtype='float32'); assert sr == SR
    fx = np.zeros_like(x); events = []
    for mode, off, kind in spec.get('sfx', []):
        u = next((u for u in c['utterances'] if u['mode'] == mode), None)
        if u is None: print('SFX SKIP unknown mode', mode); continue
        events.append(((u['from_frame'] + off) / 30, kind))
    if c.get('choice_frame') is not None:  # result_first format has no quiz
        for i in range(3): events.append(((c['choice_frame'] + 3 + i * 5) / 30, 'tick'))
        events.append(((c['answer_frame'] - 1) / 30, 'knock'))
    for at, kind in events:
        y = KIND[kind]() if kind != 'tick' else tick()
        s = int(at * SR); n = min(len(y), len(fx) - s)
        if n > 0: fx[s:s + n] += y[:n]
    sf.write(P / 'sfx.wav', fx, SR, subtype='PCM_24')
    mix = x + fx; sf.write(P / 'mix_pre.wav', mix, SR, subtype='PCM_24')
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(P / 'mix_pre.wav'), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
    af = f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(P / 'mix_pre.wav'), '-af', af + ',aresample=48000', '-ac', '2', '-c:a', 'pcm_s24le', str(P / 'mix_master.wav')], check=True)
    def meas(path):
        r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
        sm = r[r.rindex('Summary:'):]; return float(re.search(r'I:\s+(-?[\d.]+) LUFS', sm)[1]), float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', sm)[1])
    I0, T0 = meas(P / 'mix_master.wav'); g = min(-14 - I0, -1.6 - T0)
    if abs(g) > .05:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(P / 'mix_master.wav'), '-af', f'volume={g:.2f}dB', '-c:a', 'pcm_s24le', str(P / 'mix_tmp.wav')], check=True); (P / 'mix_tmp.wav').replace(P / 'mix_master.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(P / 'video_muted.mp4'), '-i', str(P / 'mix_master.wav'), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', str(P / 'video.mp4')], check=True)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(P / 'video.mp4'), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    summ = r[r.rindex('Summary:'):]
    I = float(re.search(r'I:\s+(-?[\d.]+) LUFS', summ)[1]); TP = float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', summ)[1])
    (P / 'loudness.json').write_text(json.dumps(dict(integrated_lufs=I, true_peak_dbtp=TP, events=events), indent=1))
    print('MIX', q, 'I', I, 'TP', TP)
if __name__ == '__main__': main(sys.argv[1])
