"""raw/<engine>/*.wav -> samples/*.wav (48 kHz mono, trimmed, -18 LUFS, peak <= -1 dBFS),
auditions/*.mp3 (3 lines, 0.5 s gaps) and metrics/prosody.json. Run with engines/analysis/.venv.
Usage: post.py [engine ...]   (default: every engine under raw/)"""
import json, pathlib, subprocess, sys, math, re
from fractions import Fraction
import numpy as np, soundfile as sf, pyloudnorm as pyln, parselmouth
from scipy.signal import resample_poly

LAB = pathlib.Path(__file__).resolve().parents[1]
SR = 48000
LINES = {l['id']: l for l in json.load(open(LAB / 'common' / 'texts.json'))['lines']}
meter = pyln.Meter(SR)


def to48(w, sr):
    if sr == SR:
        return w
    f = Fraction(SR, sr).limit_denominator(1000)
    return resample_poly(w, f.numerator, f.denominator).astype(np.float32)


def frame_db(w, hop=480, win=960):
    n = max(1, 1 + (len(w) - win) // hop)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    idx = np.minimum(idx, len(w) - 1)
    r = np.sqrt(np.mean(w[idx] ** 2, axis=1) + 1e-12)
    return 20 * np.log10(r)


def trim(w, rel=-40.0, pad=0.05):
    db = frame_db(w)
    on = np.where(db > max(db.max() + rel, -65))[0]
    if not len(on):
        return w
    s = max(0, on[0] * 480 - int(pad * SR)); e = min(len(w), (on[-1] + 2) * 480 + int(pad * SR))
    w = w[s:e].copy()
    f = int(0.005 * SR); ramp = np.linspace(0, 1, f, dtype=np.float32)
    w[:f] *= ramp; w[-f:] *= ramp[::-1]
    return w


def normalize(w):
    try:
        lufs = meter.integrated_loudness(w)
        if np.isfinite(lufs):
            w = w * (10 ** ((-18.0 - lufs) / 20))
    except ValueError:
        pass
    pk = np.abs(w).max()
    if pk > 0.891:
        w = w * (0.891 / pk)
    return w.astype(np.float32)


def prosody(w):
    snd = parselmouth.Sound(w.astype(np.float64), SR)
    pitch = snd.to_pitch_ac(time_step=0.01, pitch_floor=65, pitch_ceiling=600)
    f0 = pitch.selected_array['frequency']; f0 = f0[f0 > 0]
    db = frame_db(w, hop=480, win=1200)        # 10 ms hop, 25 ms window
    speech = db > db.max() - 35
    out = dict(voiced_frac=round(len(f0) / max(1, len(db)), 3))
    if len(f0) > 10:
        st = 12 * np.log2(f0 / np.median(f0))
        out.update(f0_median_hz=round(float(np.median(f0)), 1), f0_std_st=round(float(st.std()), 2),
                   f0_range_st=round(float(np.percentile(st, 95) - np.percentile(st, 5)), 2),
                   f0_mad_st=round(float(1.4826 * np.median(np.abs(st - np.median(st)))), 2),
                   f0_p10_p90_st=round(float(np.percentile(st, 90) - np.percentile(st, 10)), 2),
                   f0_slope_abs_st_per_s=round(float(np.mean(np.abs(np.diff(st))) * 100), 1))
    if speech.sum() > 10:
        d = db[speech]
        # energy contour: smooth to syllable-ish scale (~80 ms) and measure its spread / movement
        k = np.ones(8) / 8; sm = np.convolve(db, k, mode='same')[speech]
        out.update(rms_db_std=round(float(d.std()), 2), rms_db_p90_p10=round(float(np.percentile(d, 90) - np.percentile(d, 10)), 2),
                   energy_mod_db_per_s=round(float(np.mean(np.abs(np.diff(sm))) * 100), 1))
    # pauses: runs of >=120 ms below speech threshold inside the trimmed clip
    sil = ~speech; runs, c = [], 0
    for s in sil:
        if s: c += 1
        else:
            if c >= 12: runs.append(c)
            c = 0
    out['pause_s'] = round(sum(runs) * 0.01, 2); out['n_pauses'] = len(runs)
    return out


def hangul(s):
    return len(re.findall(r'[가-힣]', s))


def main():
    engines = sys.argv[1:] or sorted(p.name for p in (LAB / 'raw').iterdir() if p.is_dir())
    mpath = LAB / 'metrics' / 'prosody.json'; mpath.parent.mkdir(exist_ok=True)
    metrics = json.load(open(mpath)) if mpath.exists() else {}
    (LAB / 'samples').mkdir(exist_ok=True); (LAB / 'auditions').mkdir(exist_ok=True)
    for eng in engines:
        meta = json.load(open(LAB / 'raw' / eng / 'meta.json'))
        groups = {}
        for n, m in meta.items():
            w, sr = sf.read(LAB / 'raw' / eng / f'{n}.wav', dtype='float32', always_2d=True)
            w = normalize(trim(to48(w.mean(axis=1), sr)))
            sf.write(LAB / 'samples' / f'{n}.wav', w, SR, subtype='PCM_24')
            dur = len(w) / SR
            metrics[n] = dict(engine=eng, voice=m['voice'], style=m['style'], line=m['line'], dur=round(dur, 3),
                              cps=round(hangul(m.get('input_text') or LINES[m['line']]['tts']) / dur, 2),
                              params=m.get('params', {}), gen_seconds=m.get('gen_seconds'), **prosody(w))
            groups.setdefault((m['voice'], m['style']), {})[m['line']] = w
        for (v, st), ws in groups.items():
            if set(ws) != {1, 2, 3}:
                continue
            gap = np.zeros(int(0.5 * SR), np.float32)
            a = np.concatenate([ws[1], gap, ws[2], gap, ws[3]])
            tmp = LAB / 'auditions' / f'.{eng}_{v}_{st}.wav'
            sf.write(tmp, a, SR, subtype='PCM_16')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(tmp), '-ac', '1', '-ar', str(SR), '-c:a', 'libmp3lame', '-b:a', '128k',
                            str(LAB / 'auditions' / f'{eng}_{v}_{st}.mp3')], check=True)
            tmp.unlink()
        print(eng, len(meta), 'samples', len(groups), 'auditions', flush=True)
    json.dump(metrics, open(mpath, 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
