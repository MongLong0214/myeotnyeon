"""Locale helpers for the B3 audio/subtitle scripts (pace.py, b3post.py, linebreak.py). ko keeps the original rules.
units(): speech-rate unit per locale — ko syllables (Hangul), en syllables (vowel groups), ja morae (pyopenjtalk reading).
norm(): what is compared for CER — ko pace.heard(), en lowercase letters with numbers spelled out, ja katakana reading.
en/ja need the Kokoro venv (research/tts_kokoro/.venv: num2words, pyopenjtalk)."""
import re
TARGET = {'ko': 6.4, 'en': 5.0, 'ja': 8.0}  # units per second (en ~215 wpm, ja brisk news-read)
SMALL = set('ャュョァィゥェォヮ')
def kana(t):
    import pyopenjtalk
    return pyopenjtalk.g2p(t, kana=True)
def mora(k): return sum(1 for ch in k if '゠' <= ch <= 'ヿ' and ch not in SMALL and ch != '・')
def en_words(t):
    from num2words import num2words
    t = t.replace('%', ' percent ').replace('&', ' and ')
    t = re.sub(r'\$\s?([\d,]+(?:\.\d+)?)\s*(million|billion|thousand)?', lambda m: f"{m[1]} {m[2] or ''} dollars", t)
    t = re.sub(r'(\d+)(st|nd|rd|th)\b', lambda m: num2words(int(m[1]), to='ordinal'), t)
    t = re.sub(r'\d[\d,]*(?:\.\d+)?', lambda m: num2words(float(m[0].replace(',', '')) if '.' in m[0] else int(m[0].replace(',', ''))), t)
    return re.sub('[^a-z]', '', t.lower())
def en_syl(t):
    from num2words import num2words
    t = re.sub(r'\d[\d,]*', lambda m: num2words(int(m[0].replace(',', ''))), t.replace('$', ''))
    n = 0
    for w in re.findall(r"[a-zA-Z']+", t):
        w = w.lower(); k = len(re.findall(r'[aeiouy]+', w))
        if w.endswith('e') and not w.endswith(('le', 'ee')) and k > 1: k -= 1
        n += max(1, k)
    return n
def abc(t):  # answer letters are read as kana names (pyopenjtalk drops Latin letters)
    return re.sub(r'[A-C]', lambda m: {'A': 'エー', 'B': 'ビー', 'C': 'シー'}[m[0]], t)
def units(t, L='ko'):
    if L == 'en': return en_syl(t)

    if L == 'ja': return mora(kana(t))
    return len(re.sub('[^가-힣]', '', t))
def norm(t, L='ko', heard=None):
    if L == 'en': return en_words(t)
    if L == 'ja': return re.sub('[^\u30a0-\u30ff]', '', kana(abc(t))).replace('ー', '').replace('スィ', 'シ')
    return heard(t) if heard else re.sub('[^가-힣]', '', t)
WL = {'ko': 'ko', 'en': 'en', 'ja': 'ja'}
