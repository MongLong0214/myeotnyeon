#!/usr/bin/env python3
"""Synthesize every narration sentence with Supertonic 3 (local, OpenRAIL-M).

Subtitles keep digits; the TTS input spells numbers and Latin initials in Hangul so
the voice cannot pick the wrong reading (e.g. 3시 → 세 시). Output: audio/na/*.wav
(48 kHz mono, silence-trimmed) + audio/na/index.json with durations.
"""
import json, pathlib, re, sys, hashlib
import numpy as np, soundfile as sf
from scipy.signal import resample_poly

HERE = pathlib.Path(__file__).parent
VOICE = sys.argv[1] if len(sys.argv) > 1 else 'M2'
SPEED = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
STEPS = 16

LEX = [  # order matters: longer first
    ('131미터', '백삼십일 미터'),
    ('200미터', '이백 미터'),
    ('4미터', '사 미터'),
    ('10미터', '십 미터'),
    ('1년 6개월', '일 년 육 개월'),
    ('징역 4년', '징역 사 년'),
    ('6개월', '육 개월'),
    ('8주', '팔 주'),
    ('6주', '육 주'),
    ('20대', '이십 대'),
    ('30대', '삼십 대'),
    ('2022년 7월 28일', '이천이십이 년 칠 월 이십팔 일'), ('2023년 8월 16일', '이천이십삼 년 팔 월 십육 일'),
    ('3시 30분쯤', '세 시 삼십 분쯤'), ('3시 반', '세 시 반'), ('2023년', '이천이십삼 년'), ('2024년', '이천이십사 년'), ('2022년', '이천이십이 년'),
    ('8월 말', '팔 월 말'), ('5월쯤', '오 월쯤'), ('8월', '팔 월'), ('34일', '삼십사 일'),
    ('1년 이상 10년 이하', '일 년 이상 십 년 이하'), ('징역 1년', '징역 일 년'), ('1년인데', '일 년인데'),
    ('8개월', '팔 개월'), ('2년', '이 년'), ('3년', '삼 년'), ('120시간', '백이십 시간'), ('300만 원', '삼백만 원'),
    ('2주', '이 주'), ('112', '일일이'),
    ('1심', '일심'), ('A씨', '에이씨'), ('B씨', '비씨'), ('CCTV', '씨씨티비'), ('특수상해', '특수 상해'),
]


def tts_text(s):
    for a, b in LEX:
        s = s.replace(a, b)
    left = re.findall(r'[0-9A-Za-z]+', s)
    if left:
        raise SystemExit(f'unmapped token {left} in: {s}')
    return s


def trim(w, sr, thr=0.01, pad=0.04):
    a = np.abs(w)
    idx = np.where(a > thr)[0]
    if not len(idx):
        return w
    s = max(0, idx[0] - int(pad * sr)); e = min(len(w), idx[-1] + int(pad * sr))
    return w[s:e]


def main():
    from supertonic import TTS
    tts = TTS(auto_download=True)
    style = tts.get_voice_style(voice_name=VOICE)
    script = json.load(open(HERE / (sys.argv[3] if len(sys.argv) > 3 else 'script_text.json')))
    out = HERE / 'audio' / 'na'
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for c in script['cues']:
        for i, s in enumerate(c['narration']):
            sid = f"{c['cue_id']}_{i+1}"
            t = tts_text(s)
            wav, _ = tts.synthesize(t, voice_style=style, lang='ko', speed=SPEED, total_steps=STEPS)
            w = np.asarray(wav, dtype=np.float32).reshape(-1)
            w = trim(w, 44100)
            w48 = resample_poly(w, 160, 147).astype(np.float32)
            f = out / f'{sid}.wav'
            sf.write(f, w48, 48000, subtype='PCM_24')
            index.append(dict(id=sid, cue=c['cue_id'], text=s, tts_text=t, file=str(f.relative_to(HERE)),
                              dur=round(len(w48) / 48000, 3), sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
            print(sid, index[-1]['dur'], t[:40])
    json.dump(dict(voice=VOICE, speed=SPEED, steps=STEPS, model='Supertone/supertonic-3', items=index),
              open(out / 'index.json', 'w'), ensure_ascii=False, indent=1)
    print('total', round(sum(x['dur'] for x in index), 1), 's')


if __name__ == '__main__':
    main()
