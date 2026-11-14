"""CEO evidence packet for a Beast Clash v3 package: claims.md, audio proxies, meta/cover/1fps sheet, rights.md.
usage: packet.py <id>   -> upload/pkg/<id>_B/ceo_packet/"""
import os, sys, json, re, shutil, subprocess, difflib, glob, tempfile, math, hashlib
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
from pathlib import Path
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw
D = Path(__file__).resolve().parent; W = D.parents[1]; q = sys.argv[1]; P = W / 'upload/pkg' / f'{q}_B'; O = P / 'ceo_packet'; O.mkdir(exist_ok=True)
c = json.loads((P / 'case.json').read_text()); sp = json.loads((D / 'specs' / f'{q}.json').read_text())
V = P / 'video_v3.mp4'

# ---------------- 1. claims ----------------
ADFG_PB = 'https://www.adfg.alaska.gov/index.cfm?adfg=polarbear.main'; NG_PB = 'https://www.nationalgeographic.com/animals/mammals/facts/polar-bear'
NOAA = 'https://spo.nmfs.noaa.gov/sites/default/files/legacy-pdfs/CIRC32.pdf'; NG_W = 'https://www.nationalgeographic.com/animals/mammals/facts/walrus'
SW = 'https://seaworld.org/animals/all-about/walrus/characteristics/'; COS = 'https://wildlife-species.canada.ca/species-risk-registry/virtual_sara/files/cosewic/sr_Atlantic%20Walrus_2017_e.pdf'
BZ = 'https://www.brookfieldzoo.org/animals/polar-bear'; PBS = 'https://www.pbs.org/wnet/nature/blog/polar-bear-fact-sheet'
WWF = 'https://admin.arcticwwf.org/app/uploads/2022/04/29092902/circle_0217_walrus.pdf'; FWS = 'https://www.north-slope.org/wp-content/uploads/2022/04/76_fr_7634_walrus_finding.pdf'
DER = 'https://naturalresourcespolicy.org/docs/polar-bears-in-warming-climate.pdf'
NG_J = 'https://www.nationalgeographic.com/animals/mammals/facts/jaguar'; SDZ = 'https://ielc.libguides.com/sdzg/factsheets/jaguar/characteristics'
SDZD = 'https://ielc.libguides.com/sdzg/factsheets/jaguar/diet'; NZ_A = 'https://nationalzoo.si.edu/animals/green-anaconda'
NG_A = 'https://www.nationalgeographic.com/animals/reptiles/facts/green-anaconda'; WROE = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC1564077/'
HITE = 'https://www.frontiersin.org/journals/integrative-neuroscience/articles/10.3389/fnint.2019.00070/full'; LP = 'https://duke.academia.edu/RenataLeitePitman'
TA = 'https://journals.ku.edu/reptilesandamphibians/article/download/15504/14058/36316'; CAV = 'https://procarnivoros.org.br/downloads/predation-of-an-adult-puma-by-an-anaconda-in-southeastern-brazil'
NZ_K = 'https://nationalzoo.si.edu/animals/king-cobra'; NG_K = 'https://www.nationalgeographic.com/animals/reptiles/facts/king-cobra'
TAN = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC8733962/'; NG_H = 'https://www.nationalgeographic.com/animals/mammals/facts/honey-badger'
FR = 'https://www.frontiersin.org/journals/ecology-and-evolution/articles/10.3389/fevo.2020.585256/full'; BEGG = 'https://www.honeybadger.com/pdfs/diet.pdf'
DRA = 'https://pubmed.ncbi.nlm.nih.gov/25796346'; IFAW = 'https://www.ifaw.org/animals/honey-badgers'
CL = {
'bc001': [
 ('Title / L01 / card: POLAR BEAR 1,000 LB (454 kg)', [(ADFG_PB, 'The largest males can weigh in excess of 1700 lbs, but the average is 600–1200 lbs'), (NG_PB, 'Weight: 900 to 1,600 pounds')], '1,000 lb sits inside both ranges; 1,000 ÷ 2.2046 = 454 kg'),
 ('Title / L02 / card: WALRUS 3,000 LB (1,360 kg)', [(NOAA, 'Adult males attain a weight of 3,000 pounds and a length of 12 feet'), (NG_W, 'Weight: Up to 1.5 tons')], '1.5 t × 2,000 = 3,000 lb; 3,000 ÷ 2.2046 = 1,360 kg'),
 ('L03 / card: tusks up to 3 ft (39 in, 1 m)', [(NG_W, 'Their tusks, which are found on both males and females, can extend to about three feet'), (SW, 'Tusks can grow to a length of 100 cm (39 in.) in males')], '100 cm ÷ 2.54 = 39.4 in'),
 ('L04 / card: bear sprints 25 mph (40 km/h)', [(BZ, 'Polar bears can run 25 mph for short distances'), (PBS, 'they can run up to 25 mph.')], '25 × 1.609 = 40.2 km/h'),
 ('Card: walrus 19 mph / 30 km/h in water', [(COS, 'they can accelerate to about 30 km/h for a short time when chased')], 'SINGLE SOURCE. 30 ÷ 1.609 = 18.6 → 19 mph'),
 ('L08: up to 6 inches of blubber', [(COS, 'Their thick skin (2–4 cm) and blubber (1-15 cm; Fay 1985)')], 'SINGLE SOURCE (primary: Fay 1985). 15 cm ÷ 2.54 = 5.9 in'),
 ('L10 / verdict pop: "Experts say a bull walrus can more than match most polar bears"', [(WWF, 'an adult male walrus can more than match most polar bears with its size, strength, incredibly tough hide, and dangerous tusks')], 'near-verbatim quote'),
 ('L11 / verdict pop: "In most real encounters, bears leave healthy adult walruses alone"', [(WWF, 'it is common to see bears showing deference to adult walrus'), (FWS, 'some of the walruses were in poor condition and polar bears were able to kill them relatively easily'), (DER, 'it is likely that only adult male polar bears would be able to exploit walrus as prey')], 'SYNTHESIS of three sources, not a single quoted sentence; bears do kill calves/weak walruses'),
 ('Clash lines L06–L09 (charge, rear, BAM, backs away)', [], 'DRAMATIZATION, labelled in the description; not a factual claim'),
],
'bc002': [
 ('Title / L02 / card: JAGUAR 250 LB (113 kg)', [(NG_J, 'Weight: 100 to 250 pounds'), (SDZ, 'Body Weight 57-113 kg (126-249 lb)')], '250 ÷ 2.2046 = 113.4 kg'),
 ('Title / L02 / card: ANACONDA 550 LB (250 kg)', [(NZ_A, 'can weigh 550 pounds (250 kilograms)'), (NG_A, 'weigh more than 550 pounds')], '550 ÷ 2.2046 = 249.5 kg'),
 ('L03 / card: 30 FT (9 m)', [(NZ_A, 'They can reach lengths of 30 feet (9 meters)'), (NG_A, 'Green anacondas can grow to more than 29 feet')], '30 × 0.3048 = 9.14 m'),
 ("L04 / card: 1,000 N canine bite (estimated); for its size beats a lion's (BFQ 137 vs 112)", [(WROE, 'Table 1 row: Panthera onca … 83.2 … 1014 … 137 (lion BFQ 112 in the same table)'), (HITE, 'Table 2 row: Panthera onca (Felidae) jaguar 1014')], 'estimated from skulls; 1,014 N rounded to 1,000 N'),
 ('L10 / verdict pop: "Jaguars are on record eating anacondas"', [(LP, 'The first was a green anaconda that was consumed by a jaguar in Madre de Dios, Peru.'), (SDZD, 'Eat caiman (alligator), fish, turtles, iguana, anaconda, and birds')], 'Leite Pitman: abstract only (full text 403)'),
 ('L11 / verdict pop: "An anaconda eating a jaguar? No confirmed case found."', [(TA, 'prey review: no jaguar among anaconda prey records'), (CAV, 'To our knowledge, this is the first record of an anaconda preying on a top predator like the puma.')], 'ABSENCE OF EVIDENCE, worded as "no confirmed case found"; the only big-cat case is a puma'),
 ("Clash: \"Pinned! The snake can't coil in time\" (constriction)", [(NG_A, 'coil their muscular bodies around captured prey and squeeze until the animal asphyxiates')], 'DRAMATIZATION of the matchup; constriction itself is sourced'),
],
'bc003': [
 ('Title / L02 / card: HONEY BADGER 30 LB (14 kg)', [(NG_H, 'Weight: 13 to 30 pounds'), (FR, 'one of the largest (6–14 kg)')], '14 × 2.2046 = 30.9 lb'),
 ('L02 / card: KING COBRA 20 LB (9 kg)', [(NG_K, 'Weight: Up to 20 pounds')], "SINGLE SOURCE. 20 ÷ 2.2046 = 9.07 kg; supports \"the badger's heavier\""),
 ('Title / L03 / card: 18 FT (5.4 m)', [(NZ_K, 'it can reach 18 feet (5.4 meters)'), (NG_K, 'King cobras can reach 18 feet in length')], '18 × 0.3048 = 5.49 m'),
 ('L04 / card: up to 0.2 oz (~6 mL) venom per bite', [(NG_K, 'up to two-tenths of a fluid ounce'), (TAN, 'King Cobra is capable of delivering more than 1 gram (dry weight) of venom in one bite')], '0.2 × 29.57 = 5.9 mL'),
 ('L08: "Its loose, thick skin is hard to grip"', [(IFAW, 'Honey badgers have amazingly thick skin, around 6 to 8 millimeters'), (IFAW, 'very loose on their bodies, so they have a better chance of manoeuvring themselves out of the jaws of predators')], 'SINGLE SOURCE (IFAW, NGO)'),
 ('L10 / pop: "Honey badgers really do hunt cobras, and resist some venom"', [(BEGG, 'Cape cobra Naja nivea (10.5%), each contributed >10%'), (DRA, 'Honey badgers (Mellivora capensis) prey upon and survive bites from venomous snakes (Family: Elapidae)')], 'evidence is for Cape cobras in Africa, said as "cobras"'),
 ('L11 / pop: "not immune, and no real fight with a king cobra is on record"', [(IFAW, 'while not immune, they do have some resistance to neurotoxic venoms')], 'second half is ABSENCE OF EVIDENCE: no documented badger–king cobra encounter found'),
 ('Clash lines (rises, strike, ducks, backs down)', [], 'DRAMATIZATION, labelled in the description'),
]}[q]
md = [f'# {q} claims → source → quote (v3)', '', 'Every quote was fetched and checked on 2026-11-13 (research log: episodes/beastclash/research/facts.md).', '']
for claim, srcs, note in CL:
    md.append(f'## {claim}')
    for u, quote in srcs: md.append(f'- {u}\n  > "{quote}"')
    md.append(f'- note: {note}\n')
(O / 'claims.md').write_text('\n'.join(md)); print('1 claims', O / 'claims.md')

# ---------------- 2. audio proxies ----------------
A = O / 'audio'; A.mkdir(exist_ok=True)
wav = A / 'final_mix.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(V), '-vn', '-ac', '1', '-ar', '16000', str(wav)], check=True)
import mlx_whisper
M = next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
r = mlx_whisper.transcribe(str(wav), path_or_hf_repo=str(M), language='en', temperature=0, condition_on_previous_text=False, verbose=None)
heard = ' '.join(s['text'].strip() for s in r['segments'])
script = ' '.join(l['tts'] for l in sp['lines'])
sys.path.insert(0, str(D)); from importlib import util
spec = util.spec_from_file_location('bld_norm', D / 'build.py')
src = (D / 'build.py').read_text(); ns = {}
ns['re'] = re; exec(src[src.index('ONES ='):src.index('def voiced')], ns)
a, b = ns['norm'](script), ns['norm'](heard)
sm = difflib.SequenceMatcher(None, a, b); ops = [(t, ' '.join(a[i1:i2]), ' '.join(b[j1:j2])) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != 'equal']
x, sr = sf.read(P / 'mix_master.wav', dtype='float32')  # the v3 mix (mix.py rewrites it per run; v3 ran last)
x1 = x.mean(1) if x.ndim > 1 else x
clip = int((np.abs(x) >= 0.999).sum())
ld = json.loads((P / 'loudness_v3.json').read_text())
sil = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(V), '-af', 'silencedetect=noise=-40dB:d=0.5', '-f', 'null', '-'], capture_output=True, text=True).stderr
sils = re.findall(r'silence_start: ([\d.]+)[\s\S]*?silence_end: ([\d.]+)', sil)
# loop seam: last 1.5 s + first 1.5 s of the final mix
n = int(1.5 * sr); seam = np.concatenate([x1[-n:], x1[:n]])
im = Image.new('RGB', (1600, 400), 'white'); d = ImageDraw.Draw(im)
step = len(seam) / 1600
for i in range(1600):
    seg = seam[int(i * step):int((i + 1) * step)]; hi, lo = float(seg.max()), float(seg.min())
    d.line([(i, 200 - hi * 180), (i, 200 - lo * 180)], fill='#2050a0')
d.line([(800, 0), (800, 400)], fill='red', width=3); d.text((8, 8), f'{q} loop seam: last 1.5 s | first 1.5 s (red line = wrap point), final mix, mono', fill='black')
im.save(A / 'loop_seam.png')
dj = dict(transcript=heard, script=script, word_match=round(sm.ratio(), 3), diffs=ops, integrated_lufs=ld['integrated_lufs'], true_peak_dbtp=ld['true_peak_dbtp'], clipped_samples=clip, silences_over_0_5s_at_minus40dB=[[float(s), float(e)] for s, e in sils])
(A / 'audio_proxies.json').write_text(json.dumps(dj, indent=1))
(A / 'audio_proxies.md').write_text(f"""# {q} audio proxies (final mix of {V.name})

**These are machine proxies. They do not replace listening by ear on a phone speaker and on headphones.**

- Loudness: {ld['integrated_lufs']} LUFS integrated, true peak {ld['true_peak_dbtp']} dBTP (ffmpeg ebur128 on {V.name})
- Clipping: {clip} samples at |x| ≥ 0.999 in mix_master.wav (48 kHz, 24-bit)
- Silences ≥ 0.5 s below −40 dB: {', '.join(f'{float(s):.2f}–{float(e):.2f}s' for s, e in sils) or 'none'}
- Loop seam waveform: loop_seam.png (last 1.5 s → first 1.5 s)
- Whisper (local mlx whisper-large-v3-turbo, offline) on the whole final mix vs the TTS script: word match {sm.ratio():.3f}

## Diff (script → heard), after number/“vs” normalisation
""" + ('\n'.join(f'- {t}: "{s1}" → "{s2}"' for t, s1, s2 in ops) or '- none') + f"""

## Full transcript
{heard}
""")
print('2 audio', A / 'audio_proxies.md', A / 'loop_seam.png')

# ---------------- 3. meta, cover, mp4 path, 1 fps sheet ----------------
shutil.copy(P / 'meta.txt', O / 'meta.txt'); shutil.copy(P / 'cover_v3.jpg', O / 'cover_v3.jpg')
tmp = tempfile.mkdtemp(); subprocess.run(['ffmpeg', '-v', 'error', '-i', str(V), '-vf', 'fps=1,scale=216:384', f'{tmp}/%03d.png'], check=True)
fs = sorted(glob.glob(f'{tmp}/*.png')); cols = 7; sheet = Image.new('RGB', (cols * 216, math.ceil(len(fs) / cols) * 400), '#111'); dd = ImageDraw.Draw(sheet)
for i, f in enumerate(fs):
    sheet.paste(Image.open(f), (i % cols * 216, i // cols * 400 + 16)); dd.text((i % cols * 216 + 4, i // cols * 400 + 2), f'{i:02d}s', fill='white')
sheet.save(O / 'sheet_1fps.png')
sha = hashlib.sha256(V.read_bytes()).hexdigest()
(O / 'FINAL.txt').write_text(f'final video: {V}\nsha256: {sha}\ncover: {P / "cover_v3.jpg"}\nmeta: {P / "meta.txt"} (copied verbatim here)\n1 fps sheet: sheet_1fps.png ({len(fs)} frames)\nall-frame sheets: {P / "sheets_v3"}\n')
print('3 meta/cover/sheet', O / 'FINAL.txt', O / 'sheet_1fps.png')

# ---------------- 4. rights ----------------
(O / 'rights.md').write_text(f"""# {q} rights

## Voice
- Kokoro-82M (hexgrad), voice **af_bella**, run locally from research/tts_kokoro (weights kokoro-v1_0.pth, voices/af_bella.pt in the local HF cache).
- License: Apache-2.0. Model card https://huggingface.co/hexgrad/Kokoro-82M: "license: apache-2.0" and "This is an Apache-licensed model, and Kokoro has been deployed in numerous projects and commercial APIs." Python packages kokoro 0.9.4 / misaki 0.9.4: License: Apache License (dist-info METADATA).
- af_bella is one of the model's bundled voices (VOICES.md lists af_bella); it is not a cloned real person's voice.
- No audio was sent to any external service. The description discloses "Narration: Kokoro AI voice."

## Fonts (embedded in the render, from episodes/beastclash/public/fonts)
- Lilita One — SIL Open Font License 1.1, Copyright (c) 2011 Juan Montoreano, Reserved Font Name Lilita (OFL_LilitaOne.txt; from github.com/google/fonts ofl/lilitaone). Titles, cards, pops.
- Pretendard ExtraBold — SIL Open Font License 1.1, Copyright (c) 2021 Kil Hyung-jin, Reserved Font Name Pretendard (OFL_Pretendard.txt). Subtitles, small labels.
- OFL allows use in videos; the fonts are not sold or redistributed on their own.

## Imagery and sound
- No third-party imagery: every animal, background and effect is SVG drawn in code (episodes/beastclash/Beasts.tsx, Film.tsx). The public/ folder contains only the two fonts and their licenses, and the only staticFile() loads in Film.tsx are those fonts. No stock footage, photos, clip art or traced references.
- Characters are original designs (thick-outline toon), not taken from any existing show.
- SFX (whoosh, thud, knock, tick, clank) are synthesized with numpy in code (episodes/quiz/batch_1107/b_format/mix.py generators). No music.

## Tooling (not part of the output)
- Remotion (render), mlx whisper-large-v3-turbo (MIT; transcription checks only). The Remotion license is the existing pipeline's; it was not re-checked here.
""")
print('4 rights', O / 'rights.md')
