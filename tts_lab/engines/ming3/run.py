import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'common'))
from labio import Raw, LINES, timer
from personas import PERSONAS
import numpy as np, mlx.core as mx
from mlx_audio.tts.utils import load_model
from mlx_audio.tts.models.bailingmm.bailingmm import ming3_instruction as mi

REPO = 'mlx-community/Ming-3.0-tts-0.5B-bf16'
model = load_model(REPO)
raw = Raw('ming3')
ZH = {  # voice design captions (Chinese, as the cookbook trains them)
    'M30': ('三十岁出头的韩国男性，嗓音明亮略带沙哑，标准首尔口音。',
            '平稳清晰的纪录片旁白，语速适中。',
            '成人动画里语速很快的搞笑旁白，充满活力，语气调侃讽刺，音调起伏夸张，重音有力，喜剧节奏感强。'),
    'F20': ('二十多岁的韩国女性，嗓音清亮活泼，标准首尔口音。',
            '亲切平稳的新闻播报风格，语速适中。',
            '综艺节目里机智的旁白，语速快，俏皮跳跃，音调起伏戏剧化，带点调侃，喜剧节奏感强。'),
}
JOBS = []
for v in os.environ.get('VOICES', 'US_James,UK_George,US_Emma').split(','):
    JOBS.append((v, 'neutral', dict(voice=v), None))
    JOBS.append((v, 'comic', dict(instruct=mi(ip=v, emotion='高兴', speed='快速', pitch='高'), use_zero_spk_emb=True), None))
for v, (timbre, neu, com) in ZH.items():
    JOBS.append((f'design{v}', 'neutral', dict(instruct=mi(style=timbre + neu), use_zero_spk_emb=True), None))
    JOBS.append((f'design{v}', 'comic', dict(instruct=mi(style=timbre + com), use_zero_spk_emb=True), None))
    JOBS.append((f'design{v}', 'comicfast', dict(instruct=mi(style=timbre + com, speed='快速', pitch='高', emotion='高兴'), use_zero_spk_emb=True), None))
t0, n0, c0 = PERSONAS['M30']
JOBS.append(('freeM30', 'comic', dict(instruct=f'{t0} {c0}', use_zero_spk_emb=True), None))
only = os.environ.get('ONLY')
for v, st, kw, _ in JOBS:
    if only and f'{v}_{st}' not in only.split(','):
        continue
    for ln in LINES:
        if raw.have(v, st, ln['id']):
            continue
        mx.random.seed(1000 + ln['id'])
        t = timer()
        try:
            res = list(model.generate(text=ln['tts'], lang_code='ko', **kw))
        except Exception as e:
            print('FAIL', v, st, ln['id'], repr(e)[:300], flush=True); break
        wav = np.concatenate([np.array(r.audio, dtype=np.float32).reshape(-1) for r in res])
        raw.save(v, st, ln['id'], wav, res[0].sample_rate, params=dict(model=REPO, lang_code='ko', seed='1000+line', **kw), gen_s=t(), text=ln['tts'])
