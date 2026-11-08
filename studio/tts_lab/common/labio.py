"""Shared helpers for every engine runner: test lines in, raw wav + metadata out.
Raw files keep the engine's native sample rate; common/post.py makes the 48 kHz samples."""
import json, pathlib, time
import numpy as np, soundfile as sf

LAB = pathlib.Path(__file__).resolve().parents[1]
LINES = json.load(open(LAB / 'common' / 'texts.json'))['lines']


class Raw:
    def __init__(self, engine):
        self.engine = engine
        self.dir = LAB / 'raw' / engine
        self.dir.mkdir(parents=True, exist_ok=True)
        self.meta_path = self.dir / 'meta.json'
        self.meta = json.load(open(self.meta_path)) if self.meta_path.exists() else {}

    def name(self, voice, style, line):
        return f'{self.engine}_{voice}_{style}_{line}'

    def have(self, voice, style, line):
        return (self.dir / f'{self.name(voice, style, line)}.wav').exists()

    def save(self, voice, style, line, wav, sr, params=None, gen_s=None, text=None):
        w = np.asarray(wav, dtype=np.float32)
        if w.ndim > 1:
            w = w.reshape(-1) if 1 in w.shape else w.mean(axis=0 if w.shape[0] < w.shape[1] else 1)
        n = self.name(voice, style, line)
        sf.write(self.dir / f'{n}.wav', w, int(sr), subtype='FLOAT')
        self.meta[n] = dict(engine=self.engine, voice=voice, style=style, line=line, sr=int(sr),
                            params=params or {}, gen_seconds=None if gen_s is None else round(gen_s, 2),
                            input_text=text)
        json.dump(self.meta, open(self.meta_path, 'w'), ensure_ascii=False, indent=1)
        print('saved', n, f'{len(w)/sr:.2f}s', f'gen {gen_s:.1f}s' if gen_s else '', flush=True)


def timer():
    t = time.time()
    return lambda: time.time() - t
