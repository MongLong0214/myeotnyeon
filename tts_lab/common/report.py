"""metrics/prosody.json + metrics/asr.json + licences -> report.json (per sample and per config) + ranked print."""
import json, pathlib, statistics as S
LAB = pathlib.Path(__file__).resolve().parents[1]
P = json.load(open(LAB / 'metrics' / 'prosody.json')); A = json.load(open(LAB / 'metrics' / 'asr.json'))
LIC = {'supertonic3': 'OpenRAIL-M weights / MIT code - commercial OK (use restrictions; AI disclosure)',
       'chatterbox-ml': 'MIT weights + MIT code - commercial OK (Perth watermark in output)',
       'qwen3tts-cv': 'Apache-2.0 weights; mlx-audio MIT - commercial OK', 'qwen3tts-vd': 'Apache-2.0 weights; mlx-audio MIT - commercial OK',
       'melotts': 'MIT weights + MIT code - commercial OK', 'bark': 'MIT weights; transformers Apache-2.0 - commercial OK',
       'voxcpm2': 'Apache-2.0 weights; mlx-audio MIT - commercial OK', 'ming3': 'MIT weights; mlx-audio MIT - commercial OK'}
samples, cfg = [], {}
for n, p in sorted(P.items()):
    a = A.get(n, {})
    row = dict(name=n, file=f'samples/{n}.wav', **{k: p.get(k) for k in ('engine', 'voice', 'style', 'line', 'dur', 'cps', 'gen_seconds', 'f0_median_hz', 'f0_std_st', 'f0_mad_st', 'f0_p10_p90_st', 'f0_range_st', 'rms_db_std', 'rms_db_p90_p10', 'energy_mod_db_per_s', 'pause_s')},
               asr=a.get('asr'), cer=a.get('cer'), params=p.get('params'))
    samples.append(row)
    cfg.setdefault((p['engine'], p['voice'], p['style']), []).append(row)
configs = []
for (e, v, st), rows in cfg.items():
    m = lambda k: round(S.mean([r[k] for r in rows if r.get(k) is not None]), 3) if any(r.get(k) is not None for r in rows) else None
    c = dict(engine=e, voice=v, style=st, licence=LIC.get(e), n=len(rows), audition=f'auditions/{e}_{v}_{st}.mp3',
             cer={r['line']: r['cer'] for r in rows}, mean_cer=m('cer'), max_cer=max((r['cer'] or 0) for r in rows),
             cps=m('cps'), total_dur=round(sum(r['dur'] for r in rows), 2), gen_s_per_line=m('gen_seconds'),
             f0_std_st=m('f0_std_st'), f0_mad_st=m('f0_mad_st'), f0_p10_p90_st=m('f0_p10_p90_st'), f0_range_st=m('f0_range_st'), f0_median_hz=m('f0_median_hz'),
             rms_db_std=m('rms_db_std'), energy_mod=m('energy_mod_db_per_s'), pause_s=m('pause_s'), params=rows[0]['params'])
    configs.append(c)
base = next(c for c in configs if c['engine'] == 'supertonic3' and c['voice'] == 'M2' and c['style'] == 'sp120')
for c in configs:
    ok = c['n'] == 3 and c['mean_cer'] is not None
    # comic score: expressiveness relative to the current voice, gated by intelligibility and pace
    c['score'] = None if not ok else round(
        (c['f0_p10_p90_st'] or 0) / base['f0_p10_p90_st'] + 0.5 * (c['rms_db_std'] or 0) / base['rms_db_std']
        + 0.5 * min(c['cps'] / base['cps'], 1.25) - 8 * c['mean_cer'] - (1 if c['max_cer'] > 0.15 else 0), 3)
configs.sort(key=lambda c: -(c['score'] if c['score'] is not None else -9))
json.dump(dict(generated='2026-10-26', baseline=dict(engine='supertonic3', voice='M2', style='sp120'),
               texts=json.load(open(LAB / 'common' / 'texts.json')),
               method=dict(samples='48 kHz mono, trimmed (-40 dB rel), -18 LUFS, peak <= -1 dBFS', asr='mlx-community/whisper-large-v3-turbo, ko; CER on Hangul only, digits read as Sino-Korean',
                           cps='Hangul syllables of the TTS input / trimmed duration', f0='Praat AC pitch 65-600 Hz, std and p5-p95 range in semitones re median',
                           energy='10 ms frame RMS dB over speech frames: std; energy_mod = mean |d/dt| of 80 ms-smoothed dB',
                           score='f0_p10_p90/base + 0.5*rms_std/base + 0.5*min(cps/base,1.25) - 8*mean_cer - 1 if any line CER>0.15 (base = supertonic3 M2 sp120)'),
               configs=configs, samples=samples), open(LAB / 'report.json', 'w'), ensure_ascii=False, indent=1)
print(f"{'engine':14} {'voice':12} {'style':10} score  cer   maxc  cps   f0sd  f0p10-90 rmsSD gen/l")
for c in configs[:int(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else 40]:
    print(f"{c['engine']:14} {c['voice']:12} {c['style']:10} {c['score'] if c['score'] is not None else '-':>5} {c['mean_cer']:.3f} {c['max_cer']:.2f} {c['cps']:5.2f} {c['f0_std_st']:5.2f} {c['f0_p10_p90_st']:5.2f} {c['rms_db_std']:5.2f} {c['gen_s_per_line']}")
