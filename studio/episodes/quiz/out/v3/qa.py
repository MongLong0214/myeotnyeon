#!/usr/bin/env python3
"""Release gates for one rendered episode (owner stage-2 spec 2026-10-26). Writes episodes/quiz/<id>/qa.json.
usage: qa.py q011 [--sheet]   (run after render_all.sh and audit.sh)
Gates: audit bad=0 · −14±1 LUFS, true peak ≤ −1.0 dBTP · no freeze > 2.5 s · no black frames · 1080×1920 30 fps BT.709 ·
final-mix ASR vs script ≥ 0.99 · numbers on screen/speech all in facts.md · spelling/spacing patterns ·
im-not-ai display-text gate (C-8/C-11/I-4/E-2/F-5 = 0) · structure (25–35 s, reveal ≥ 75 %, a change every ≤ 1.5 s) ·
death cases: no sensational wording, no suffering/bodies, no graphic staging.
--sheet also writes review/<id>_phone.png: frames at every caption change, with the phone-hidden zones shaded."""
import json, pathlib, re, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
WORK = HERE.parents[3]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
import tempo, textgate  # noqa: E402
from episodes import EPISODES  # noqa: E402
PUB = WORK / 'production' / 'compositor' / 'public'


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout + r.stderr


def probe(mp4):
    j = json.loads(sh(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', str(mp4)]))
    v = next(s for s in j['streams'] if s['codec_type'] == 'video')
    a = next((s for s in j['streams'] if s['codec_type'] == 'audio'), {})
    fr = v['r_frame_rate'].split('/'); fps = int(fr[0]) / int(fr[1])
    res = dict(width=v['width'], height=v['height'], fps=fps, pix_fmt=v.get('pix_fmt'), color_space=v.get('color_space'),
               color_primaries=v.get('color_primaries'), color_transfer=v.get('color_transfer'), audio=a.get('codec_name'),
               audio_bitrate=a.get('bit_rate'), duration=float(j['format']['duration']))
    res['pass'] = res['width'] == 1080 and res['height'] == 1920 and abs(fps - 30) < 1e-6 and res['color_space'] == 'bt709' and res['color_primaries'] == 'bt709' and res['color_transfer'] == 'bt709'
    return res


def loud(mp4):
    out = sh(['ffmpeg', '-hide_banner', '-nostats', '-i', str(mp4), '-filter_complex', 'ebur128=peak=true', '-f', 'null', '-'])
    summ = out[out.rindex('Summary:'):]
    i = float(re.search(r'I:\s+(-?[\d.]+) LUFS', summ)[1]); tp = float(re.search(r'True peak:\s+Peak:\s+(-?[\d.]+) dBFS', summ)[1])
    return dict(integrated_lufs=i, true_peak_dbtp=tp, pass_=abs(i + 14) <= 1 and tp <= -1.0)


def freeze_black(mp4):
    fz = sh(['ffmpeg', '-hide_banner', '-nostats', '-i', str(mp4), '-vf', 'freezedetect=n=0.001:d=2.5', '-map', '0:v', '-f', 'null', '-'])
    bk = sh(['ffmpeg', '-hide_banner', '-nostats', '-i', str(mp4), '-vf', 'blackdetect=d=0.04:pix_th=0.10:pic_th=0.98', '-map', '0:v', '-f', 'null', '-'])
    freezes = re.findall(r'freeze_start: ([\d.]+)', fz); blacks = re.findall(r'black_start:([\d.]+)', bk)
    return dict(freezes_over_2_5s=[float(x) for x in freezes], black_segments=[float(x) for x in blacks], pass_=not freezes and not blacks)


# ---- final-mix ASR -----------------------------------------------------------------------------------------
UNIT = {'만': 10_000, '억': 100_000_000, '천': 1000}


def canon_numbers(s):
    """Number formats → plain integers so '1만 1천', '11,000' and '11000' compare equal; 'm' → 미터."""
    s = re.sub(r'(\d),(\d{3})', r'\1\2', s)
    def big(m):
        total, cur = 0, m.group(0)
        for num, u in re.findall(r'(\d+)\s*(억|만|천)?', cur):
            total += int(num) * UNIT.get(u, 1)
        return str(total)
    s = re.sub(r'\d+\s*(?:억|만|천)(?:\s*\d+\s*(?:억|만|천))*(?:\s*\d+)?', big, s)
    return re.sub(r'(\d)\s*m\b', r'\1미터', s)


# Standard-pronunciation spellings the recogniser writes phonetically (counted separately in the raw score).
PRON = [('마쳐', '맞혀'), ('맞춰', '맞혀'), ('2배', '두 배'), ('공일공', '010'), ('야차루를', '야차룰을')]


def norm(s, pron=True):
    s = canon_numbers(s)
    if pron:
        for a, b in PRON:
            s = s.replace(a, b)
    return re.sub(r'[^가-힣0-9]', '', s)


def cer(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, cb in enumerate(b, 1):
            d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (ca != cb))
    return d[-1] / max(1, len(a))


def asr(eid, mp4):
    import mlx_whisper
    wav = HERE / 'audit' / f'{eid}_mix16k.wav'
    sh(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(mp4), '-ac', '1', '-ar', '16000', str(wav)])
    hyp = mlx_whisper.transcribe(str(wav), path_or_hf_repo='mlx-community/whisper-large-v3-turbo', language='ko')['text'].strip()
    ref = ' '.join(s for c in EPISODES[eid]['cues'] for s in c[2])
    raw = 1 - cer(norm(ref, False), norm(hyp, False)); acc = 1 - cer(norm(ref), norm(hyp))
    wav.unlink(missing_ok=True)
    return dict(reference=ref, transcript=hyp, accuracy_raw=round(raw, 4), accuracy=round(acc, 4), pass_=acc >= 0.99,
                normalisation='numbers to integers (1만 1천 = 11,000), m → 미터, phonetic spellings ' + ', '.join(f'{a}→{b}' for a, b in PRON))


# ---- numbers, spelling ---------------------------------------------------------------------------------------
def values(s):
    return {int(x) for x in re.findall(r'\d+', canon_numbers(s))}


def numbers(eid):
    ep = EPISODES[eid]
    facts = (HERE.parents[1] / eid / 'facts.md').read_text()
    shown = values('\n'.join(textgate.labels(ep))); spoken = values(' '.join(textgate.narration(ep)))
    known = values(facts)
    missing = sorted((shown | spoken) - known)
    return dict(screen=sorted(shown), speech=sorted(spoken), not_in_facts=missing, pass_=not missing)


SPELL = [(r'  +', '두 칸 띄움'), (r'\s[,.?!]', '문장부호 앞 띄움'), (r'\d만원|\d천원|\d억원', '"만 원" 띄어쓰기'), (r'징역\d', '"징역 N" 띄어쓰기'),
         (r'[가-힣]\(', '괄호 앞 띄움 없음'), (r'\.\.', '마침표 중복'), (r'집유\d', '"집유 N" 띄어쓰기')]


def spelling(eid):
    ep = EPISODES[eid]
    texts = textgate.labels(ep) + textgate.narration(ep) + [x for c in ep['cues'] for k in ep.get('split', {}) for x in ep['split'][k]]
    hits = [(t, why) for t in texts for rx, why in SPELL if re.search(rx, t)]
    hits = [(t, w) for t, w in hits if not (w == '괄호 앞 띄움 없음' and '(' not in t)]
    return dict(issues=hits, pass_=not hits)


SENSATIONAL = ['참혹', '끔찍', '충격', '경악', '비극', '참사', '아비규환', '지옥', '화마', '잿더미', '타 죽', '불타', '숨진 채', '시신', '시체', '사체', '유해',
               '고통', '신음', '비명', '오열', '절규', '처참', '참상', '공포', '소름', '역대급', '역대 최악', '최후', '희생양',
               '무차별', '구타', '때려 죽', '뇌출혈', '뇌사', '장기', '기증', '유족', '얼굴', '10차례']


def serious(eid):
    ep = EPISODES[eid]
    if not ep.get('serious'):
        return None
    meta = (WORK / 'upload' / f'v3_{eid}_meta.txt')
    texts = textgate.labels(ep) + textgate.narration(ep) + ([meta.read_text()] if meta.exists() else [])
    words = sorted({w for t in texts for w in SENSATIONAL if w in t})
    staging = []
    for c in ep['cues']:
        p = c[5]
        if c[1] == 'incident':
            if p.get('burst') or p.get('sfx'):
                staging.append(f'{c[0]}: burst/sfx')
            if p.get('set') not in ('wildfire', 'orchard', 'memorial', 'paper', 'bigtext', 'barstreet', 'recorder'):
                staging.append(f"{c[0]}: set {p.get('set')}")
            for a in p.get('actors', []):
                if a.get('expr') in ('shock', 'scared', 'dizzy', 'smug', 'angry'):
                    staging.append(f"{c[0]}: actor expr {a.get('expr')}")
    review = {'q012': 'frames checked by eye on the phone sheet: no people in fire scenes, no bodies, no injuries; memorial = chrysanthemum + candle',
              'q014': 'frames checked by eye on the phone sheet: no people in incident scenes (street, phone recorder, charge card), no injury or body imagery; judge character only in the shared weigh/reveal scenes'}
    return dict(sensational_or_suffering_words=words, graphic_staging=staging, music='none (make.py forces it for serious episodes)',
                visual_review=review.get(eid, 'frames checked by eye on the phone sheet'),
                pass_=not words and not staging)


# ---- accuracy (coordinator 2026-10-26, q014 V3-03) -------------------------------------------------------------
# Never say or imply the sentence is final; a prosecution request may only be compared with the instance it was made in.
INSTANCE_REQUEST = {'q014': '1심', 'q012': '2심'}


def accuracy(eid):
    ep = EPISODES[eid]
    meta = WORK / 'upload' / f'v3_{eid}_meta.txt'
    texts = textgate.labels(ep) + textgate.narration(ep) + ([meta.read_text()] if meta.exists() else [])
    final = sorted({t[:60] for t in texts if '확정' in t})
    # These episodes have archived, independently reported final judgments. Keep the
    # previous no-finality rule for earlier ids, and review only the new facts here.
    verified = {
        'q015': ('중대장', '징역 5년 6개월', 'C09', ['research/raw_n18/S03.txt', 'research/raw_n18/S04.txt']),
        'q016': ('운전자', '금고 5년', 'F06', ['research/raw3/N16_1.txt', 'research/raw3/N16_3.txt']),
        'q017': ('살인 등 피고인', '무기징역', 'F07', ['research/raw3/N17_2.txt', 'research/raw3/N17_3.txt']),
    }.get(eid)
    if verified:
        who, sentence, claim, sources = verified
        facts = (HERE.parents[1] / eid / 'facts.md').read_text()
        compact = lambda s: re.sub(r'\s+', '', s)
        evidence = []
        for path in sources:
            body = (WORK / path).read_text()
            lines = [line for line in body.splitlines() if re.match(r'P\d+ ', line) and '확정' in line and compact(sentence) in compact(line)]
            evidence.append(dict(file=path, paragraphs=[line.split(' ', 1)[0] for line in lines], pass_=bool(lines)))
        reveal = next(i for i, cue in enumerate(ep['cues']) if cue[1] == 'reveal')
        early = [t for cue in ep['cues'][:reveal] for t in cue[2] if '확정' in t]
        req = [t for t in textgate.labels(ep) + textgate.narration(ep) if '구형' in t]
        request_ok = not req if eid != 'q017' else all('1심' in t and '2심' in t and '사형' in t for t in req)
        return dict(confirmed_finality=True, defendant=who, sentence=sentence, fact_id=claim, evidence=evidence,
                    finality_hits=final, finality_before_reveal=early, request_mentions=req,
                    request_same_defendant_and_instances=request_ok,
                    pass_=all(x['pass_'] for x in evidence) and claim in facts and compact(sentence) in compact(facts) and not early and request_ok)
    inst = INSTANCE_REQUEST.get(eid)
    req = [t for t in textgate.labels(ep) + textgate.narration(ep) if '구형' in t and re.search(r'\d', t)]
    unscoped = [t for t in req if inst and inst not in t]
    res = dict(no_finality_claim=not final, finality_hits=final, request_mentions=req)
    if inst:
        res.update(request_instance=inst, request_unscoped=unscoped,
                   single_defendant='archived articles name one defendant (A씨, 28); the 5-year request is his 1심 request (facts.md 정확성 점검)')
    res['pass_'] = not final and not unscoped
    return res


# ---- phone sheet ---------------------------------------------------------------------------------------------
def sheet(eid, mp4):
    from PIL import Image, ImageDraw
    doc = json.load(open(PUB / eid / 'render.json'))
    ts = sorted({s['from_'] + 6 for s in doc['subtitles']} | {c['from'] + c['dur'] - 4 for c in doc['cues']})
    tiles = []
    tmp = HERE / 'audit' / f'{eid}_sheet'; tmp.mkdir(exist_ok=True)
    for i, f in enumerate(ts):
        png = tmp / f'{i:03d}.png'
        sh(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-ss', f'{f / 30:.3f}', '-i', str(mp4), '-frames:v', '1', str(png)])
        im = Image.open(png).convert('RGB'); ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        for box in [(0, 0, 110, 1920), (970, 0, 1080, 1920), (0, 0, 1080, 190), (0, 1540, 1080, 1920), (880, 900, 1080, 1920)]:
            d.rectangle(box, fill=(255, 0, 80, 70))
        im = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB').resize((270, 480))
        ImageDraw.Draw(im).text((6, 4), f'{f}f {f / 30:.1f}s', fill=(255, 255, 0))
        tiles.append(im)
    cols = 8; rows = (len(tiles) + cols - 1) // cols
    out = Image.new('RGB', (cols * 270, rows * 480), (20, 20, 20))
    for i, t in enumerate(tiles):
        out.paste(t, ((i % cols) * 270, (i // cols) * 480))
    path = HERE / 'review' / f'{eid}_phone.png'; out.save(path)
    for p in tmp.iterdir():
        p.unlink()
    tmp.rmdir()
    return str(path.relative_to(WORK)), len(tiles)


def audit_result(eid):
    f = HERE / 'audit' / f'{eid}.txt'
    if not f.exists():
        return dict(pass_=False, note='audit.sh not run')
    lines = f.read_text().splitlines()
    bad = [l for l in lines if not l.endswith(' n=0 END')]
    return dict(frames=len(lines), bad=len(bad), pass_=len(lines) > 0 and not bad)


def main():
    eid = sys.argv[1]
    mp4 = HERE / f'{eid}.mp4'
    st, _ = tempo.check(eid)
    tg = textgate.gate(eid)
    res = dict(episode=eid, file=str(mp4.relative_to(WORK)),
               audit=audit_result(eid), probe=probe(mp4), loudness=loud(mp4), freeze_black=freeze_black(mp4),
               asr_final_mix=asr(eid, mp4), numbers=numbers(eid), spelling=spelling(eid),
               im_not_ai=dict(version='2.3.2', counts=tg['counts'], pass_=tg['passed'], risk_band=tg['detail']['risk_band']),
               structure=dict(st, pass_=st['duration_ok'] and st['reveal_ok'] and st['tempo_ok']))
    res['accuracy'] = accuracy(eid)
    s = serious(eid)
    if s:
        res['death_case'] = s
    if '--sheet' in sys.argv:
        res['phone_sheet'], n = sheet(eid, mp4)
        res['phone_sheet_frames'] = n
    gates = {k: v.get('pass_', v.get('pass')) for k, v in res.items() if isinstance(v, dict)}
    res['gates'] = gates
    res['all_pass'] = all(gates.values())
    def fix(x):
        if isinstance(x, dict):
            return {('pass' if k == 'pass_' else k): fix(v) for k, v in x.items()}
        return [fix(v) for v in x] if isinstance(x, list) else x
    res = fix(res)
    (HERE.parents[1] / eid / 'qa.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(dict(episode=eid, gates=res['gates'], all_pass=res['all_pass'], lufs=res['loudness']['integrated_lufs'], tp=res['loudness']['true_peak_dbtp'],
                          asr=res['asr_final_mix']['accuracy'], asr_raw=res['asr_final_mix']['accuracy_raw'], audit_bad=res['audit'].get('bad')), ensure_ascii=False))


if __name__ == '__main__':
    main()
