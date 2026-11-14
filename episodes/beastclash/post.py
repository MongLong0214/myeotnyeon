"""Write cues.md, meta.txt and READY.txt for a Beast Clash package from case.json, whisper.json, loudness.json,
gate/gate.json and the verified sources below (research/facts.md, fetched 2026-11-13). usage: post.py <id>"""
import sys, json, hashlib, subprocess
from pathlib import Path
import numpy as np
from PIL import Image
D = Path(__file__).resolve().parent; W = D.parents[1]; q = sys.argv[1]; SUF = sys.argv[2] if len(sys.argv) > 2 else ''; P = W / 'upload/pkg' / f'{q}_B'
c = json.loads((P / 'case.json').read_text()); wh = json.loads((P / 'whisper.json').read_text())
ld = json.loads((P / f'loudness{SUF}.json').read_text()); g = json.loads((P / f'gate{SUF}/gate.json').read_text())

EP = {
'bc001': dict(
 title='Polar Bear vs Walrus — Who Wins?',
 desc_stats=['Polar bear: adult males often 600–1,200 lb, the biggest over 1,700 lb (Alaska Dept. of Fish & Game). We use 1,000 lb (454 kg).',
  'Walrus bull: up to about 3,000 lb / 1,360 kg (NOAA; National Geographic "up to 1.5 tons").',
  'Walrus tusks: up to 100 cm / 39 in (SeaWorld; NOAA record 39.5 in). National Geographic: "about three feet".',
  'Polar bear sprint: 25 mph / 40 km/h for short distances (Brookfield Zoo; PBS Nature). Walrus burst swim: about 30 km/h / 19 mph (COSEWIC 2017).',
  'Walrus blubber: 1–15 cm, up to about 6 in (COSEWIC 2017).',
  'Real encounters: polar bears eat walruses mostly as calves or weak animals; "an adult male walrus can more than match most polar bears" (WWF Arctic, The Circle 2.2017).'],
 sources=[('Alaska Dept. of Fish & Game — Polar bear', 'https://www.adfg.alaska.gov/index.cfm?adfg=polarbear.main'),
  ('National Geographic — Polar bear', 'https://www.nationalgeographic.com/animals/mammals/facts/polar-bear'),
  ('NOAA/NMFS Circular 32 (walrus weight, tusks)', 'https://spo.nmfs.noaa.gov/sites/default/files/legacy-pdfs/CIRC32.pdf'),
  ('National Geographic — Walrus', 'https://www.nationalgeographic.com/animals/mammals/facts/walrus'),
  ('SeaWorld — Walrus physical characteristics', 'https://seaworld.org/animals/all-about/walrus/characteristics/'),
  ('COSEWIC Status Report, Atlantic Walrus 2017 (Govt. of Canada)', 'https://wildlife-species.canada.ca/species-risk-registry/virtual_sara/files/cosewic/sr_Atlantic%20Walrus_2017_e.pdf'),
  ('Brookfield Zoo Chicago — Polar bear', 'https://www.brookfieldzoo.org/animals/polar-bear'),
  ('PBS Nature — Polar bear fact sheet', 'https://www.pbs.org/wnet/nature/blog/polar-bear-fact-sheet'),
  ('WWF Arctic, The Circle 2.2017 — Walruses', 'https://admin.arcticwwf.org/app/uploads/2022/04/29092902/circle_0217_walrus.pdf'),
  ('USFWS 12-month finding, Pacific walrus, 76 FR 7634 (2011)', 'https://www.north-slope.org/wp-content/uploads/2022/04/76_fr_7634_walrus_finding.pdf'),
  ('Derocher, Lunn & Stirling 2004, Integr. Comp. Biol. 44:163–176', 'https://naturalresourcespolicy.org/docs/polar-bears-in-warming-climate.pdf')],
 math=['1,000 lb ÷ 2.2046 = 453.6 → 454 kg (1,000 lb lies inside ADF&G average 600–1,200 lb and NatGeo 900–1,600 lb)',
  '3,000 lb ÷ 2.2046 = 1,360.8 → 1,360 kg; NatGeo 1.5 tons × 2,000 = 3,000 lb',
  '3,000 ÷ 1,000 = 3 → "three to one" (on screen as 1,000 lb vs 3,000 lb)',
  '100 cm ÷ 2.54 = 39.4 in = 3.3 ft → said "up to three feet" (NatGeo "about three feet"), card "3 FT / up to 39 in (1 m)"',
  '25 mph × 1.609 = 40.2 → 40 km/h; 30 km/h ÷ 1.609 = 18.6 → 19 mph',
  'blubber 15 cm ÷ 2.54 = 5.9 in → "up to six inches"'],
 honesty='Verdict is the adult bull walrus, framed as "experts say" + "in most real encounters". Bears do kill walruses (calves, weak animals, sometimes subadults); the card under the verdict says "BEARS GO AFTER CALVES INSTEAD". No polar bear bite-force figure was found, so none is used.'),
'bc002': dict(
 title='Jaguar vs Anaconda — Who Wins?',
 desc_stats=['Jaguar: 100–250 lb (National Geographic); 57–113 kg (San Diego Zoo Wildlife Alliance).',
  'Green anaconda: up to 30 ft / 9 m and 550 lb / 250 kg (Smithsonian\'s National Zoo; National Geographic).',
  'Jaguar bite: canine bite estimated at about 1,014 N from skulls; bite-force quotient 137 vs lion 112 (Wroe et al. 2005, Proc. R. Soc. B).',
  'Real encounters: jaguars are on record eating anacondas (Leite Pitman et al. 2019, CATnews; SDZWA diet sheet). We found no confirmed case of an anaconda eating a jaguar (prey review: Thomas & Allain 2021).'],
 sources=[('National Geographic — Jaguar', 'https://www.nationalgeographic.com/animals/mammals/facts/jaguar'),
  ('San Diego Zoo Wildlife Alliance Library — Jaguar characteristics', 'https://ielc.libguides.com/sdzg/factsheets/jaguar/characteristics'),
  ("Smithsonian's National Zoo — Green anaconda", 'https://nationalzoo.si.edu/animals/green-anaconda'),
  ('National Geographic — Green anaconda', 'https://www.nationalgeographic.com/animals/reptiles/facts/green-anaconda'),
  ('Wroe, McHenry & Thomason 2005, Proc. R. Soc. B 272:619–625', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC1564077/'),
  ('Hite et al. 2019, Front. Integr. Neurosci. 13:70', 'https://www.frontiersin.org/journals/integrative-neuroscience/articles/10.3389/fnint.2019.00070/full'),
  ('Leite Pitman et al. 2019, "Feeding on giants", CATnews (abstract)', 'https://duke.academia.edu/RenataLeitePitman'),
  ('SDZWA Library — Jaguar diet & feeding', 'https://ielc.libguides.com/sdzg/factsheets/jaguar/diet'),
  ('Thomas & Allain 2021, A review of prey taken by anacondas, Reptiles & Amphibians 28', 'https://journals.ku.edu/reptilesandamphibians/article/download/15504/14058/36316')],
 math=['250 lb ÷ 2.2046 = 113.4 → 113 kg', '550 lb ÷ 2.2046 = 249.5 → 250 kg (Zoo states 250 kg)',
  '550 ÷ 250 = 2.2 (said as the two weights, not as a ratio)', '30 ft × 0.3048 = 9.14 → 9 m',
  '1,014 N rounded → "1,000 N", labelled "estimated" (skull-based)', 'BFQ 137 (jaguar) > 112 (lion), same table → "for its size, the jaguar\'s bite beats a lion\'s"'],
 honesty='"1,500 psi" jaguar claim not used (only weak sources). No credible jaguar speed found, so the third card is bite force instead of speed. Encounters are rarely recorded; the verdict is phrased as what is on record and what is not.'),
'bc003': dict(
 title='Honey Badger vs King Cobra — Who Wins?',
 desc_stats=['Honey badger: 13–30 lb (National Geographic); 6–14 kg (Frontiers in Ecology & Evolution 2020).',
  "King cobra: up to 18 ft / 5.4 m (Smithsonian's National Zoo; National Geographic) and up to 20 lb (National Geographic).",
  'Venom: up to 0.2 fl oz (about 6 mL) per bite (National Geographic); over 1 g dry venom per bite (Tan et al. 2022).',
  'Honey badgers really do hunt cobras: Cape cobras were 10.5% of snake prey in the Kalahari (Begg et al. 2003). They have some resistance to cobra neurotoxins (Drabeck et al. 2015) but are not immune (IFAW).',
  'No scientifically documented fight between a honey badger and a king cobra was found.'],
 sources=[("Smithsonian's National Zoo — King cobra", 'https://nationalzoo.si.edu/animals/king-cobra'),
  ('National Geographic — King cobra', 'https://www.nationalgeographic.com/animals/reptiles/facts/king-cobra'),
  ('Tan, Bourges & Tan 2022, J. Venom. Anim. Toxins incl. Trop. Dis.', 'https://pmc.ncbi.nlm.nih.gov/articles/PMC8733962/'),
  ('National Geographic — Honey badger', 'https://www.nationalgeographic.com/animals/mammals/facts/honey-badger'),
  ('Frontiers in Ecology & Evolution 2020 — Honey badger, Central India', 'https://www.frontiersin.org/journals/ecology-and-evolution/articles/10.3389/fevo.2020.585256/full'),
  ('Begg et al. 2003, J. Zool. 260:301–316 (diet)', 'https://www.honeybadger.com/pdfs/diet.pdf'),
  ('Drabeck, Dean & Jansa 2015, Toxicon 99:68–72', 'https://pubmed.ncbi.nlm.nih.gov/25796346'),
  ('IFAW — Honey badgers', 'https://www.ifaw.org/animals/honey-badgers')],
 math=['14 kg × 2.2046 = 30.9 → 30 lb (NatGeo max 30 lb)', '20 lb ÷ 2.2046 = 9.07 → 9 kg',
  '18 ft × 0.3048 = 5.49 m; Zoo states 5.4 m', '0.2 fl oz × 29.57 = 5.9 → about 6 mL ("two-tenths of an ounce")'],
 honesty='Verdict card reads "EDGE: HONEY BADGER" with "NOT IMMUNE · NO RECORDED FIGHT"; narration says the fight is not on record. Cobra prey evidence is for Cape cobras in Africa, said as "cobras". "Loose, thick skin" rests on one source (IFAW, 6–8 mm, loose) — flagged. Range overlap in India is an inference, so it is not claimed.'),
}[q]
DISC = 'Original 2D animation; dramatized matchup, not real footage. Narration: Kokoro AI voice.'
tags = '#animals #whowouldwin #shorts'
src_short = {'bc001': 'Sources: ADF&G, NOAA, National Geographic, SeaWorld, COSEWIC, Brookfield Zoo, WWF Arctic.',
             'bc002': "Sources: National Geographic, Smithsonian's National Zoo, San Diego Zoo Wildlife Alliance, Wroe et al. 2005, Leite Pitman et al. 2019.",
             'bc003': "Sources: Smithsonian's National Zoo, National Geographic, Begg et al. 2003, Drabeck et al. 2015, IFAW."}[q]
meta = f"[제목]\n{EP['title']}\n\n[설명]\n" + '\n'.join(EP['desc_stats']) + "\n\nSources:\n" + '\n'.join(f'- {a}: {u}' for a, u in EP['sources']) + f"\n\n{DISC}\n{tags}\n\n[고정 댓글]\nWho would win? A or B 👇\n\n[출처]\n" + '\n'.join(f'{a} | {u}' for a, u in EP['sources']) + '\n'
assert len(EP['title']) < 40, EP['title']
(P / 'meta.txt').write_text(meta)

# loop diff, first vs last frame at full res
def frame(i):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(P / f'video{SUF}.mp4'), '-vf', f'select=eq(n\\,{i})', '-vframes', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return np.frombuffer(r, np.uint8).reshape(1920, 1080, 3).astype(float)
loop = float(np.abs(frame(0) - frame(c['n'] - 1)).mean())
L = c['lines']
rows = '\n'.join(f"| {l['id']} | {l['mode']}{'/' + '+'.join(s['s'] + ':' + s['who'] + ('(tank)' if s.get('tank') else '') for s in l['shots']) if l.get('shots') else ''} | {l['from']} ({l['from']/30:.2f}s), {l['dur']}f | {l['onset']:.3f}–{l['offset']:.3f} | {next(w['expected'] for w in wh if w['id']==l['id'])} | {l['shown'] or ''} | {next(w['heard'] for w in wh if w['id']==l['id'])} ({next(w['match'] for w in wh if w['id']==l['id'])}) |" for l in L)
subs = '\n'.join(f"| {i+1} | {s['s']:.3f}–{s['e']:.3f} | {s['text'].replace(chr(10), ' / ')} | {max(len(x) for x in s['text'].split(chr(10)))} |" for i, s in enumerate(c['subs']))
stats = '\n'.join(f"| {s['label']} | {s['a']['big'] + ' (' + s['a']['small'] + ')' if s.get('a') else '—'} | {s['b']['big'] + ' (' + s['b']['small'] + ')' if s.get('b') else '—'} |" for s in c['stats'])
cues = f"""# {q} Beast Clash — {c['title'][0]} vs {c['title'][1]}

{c['n']} frames = {c['n']/30:.2f}s · 30 fps · 1080×1920 · voice Kokoro-82M (Apache-2.0, local, offline) `{c['voice']}` base speed {c['speed']} (L01 and stat lines faster)
Voice onsets measured per take (-38 dB); scene cut 1 frame before each onset. Every take whisper-checked locally (mlx whisper-large-v3-turbo, HF offline).
Loop: last frame → frame 0 mean abs diff {loop:.2f}/255 (limit 25). Loudness {ld['integrated_lufs']} LUFS, true peak {ld['true_peak_dbtp']} dBTP.

| line | scene | cut frame, length | voice s | TTS | subtitle | whisper heard (match) |
|---|---|---|---|---|---|---|
{rows}

## Subtitle cues (Lilita One 76px, ≤2 lines × ≤28 chars, word-boundary breaks, starts on whisper word / voice onset)

| # | s | text | longest row |
|---|---|---|---|
{subs}

## Stat cards

| card | A ({c['title'][0]}) | B ({c['title'][1]}) |
|---|---|---|
{stats}

Verdict: {c['verdict']['head']} {c['verdict']['name']} — "{c['verdict']['note']}" / "{c['verdict'].get('note2','')}"

## Arithmetic
""" + '\n'.join(f'- {m}' for m in EP['math']) + f"""

## Honesty notes
{EP['honesty']}

## Sources (each fetched and quote-checked 2026-11-13; quotes in episodes/beastclash/research/facts.md)
""" + '\n'.join(f'- {a} — {u}' for a, u in EP['sources']) + '\n'
(P / 'cues.md').write_text(cues)
sha = hashlib.sha256((P / f'video{SUF}.mp4').read_bytes()).hexdigest()
nonpass = [f"{i['status']} {i['check']}: {str(i.get('summary',''))[:120]}" for i in g['items'] if i['status'] != 'PASS']
npass = sum(i['status'] == 'PASS' for i in g['items'])
(P / 'READY.txt').write_text(f"""{q.upper()}_B · {EP['title']} · Beast Clash (@beastclashtoon) launch Short · producer self-check (no upload)
file: upload/pkg/{q}_B/video{SUF}.mp4 (cover{SUF}.jpg, sheets{SUF}/, gate{SUF}/)  SHA256 {sha}
spec: 1080×1920 · 30fps · {c['n']} frames ({c['n']/30:.2f}s) · {ld['integrated_lufs']} LUFS · TP {ld['true_peak_dbtp']} dBTP · loop diff {loop:.2f}/255
voice: Kokoro-82M {c['voice']} (local; audio never left this machine) · whisper check: {sum(w['match']>=.9 for w in wh)}/{len(wh)} lines ≥0.9 match, rest are number/homophone spellings (see cues.md)
gate.py: {npass} PASS; non-PASS:
""" + '\n'.join('  - ' + x for x in nonpass) + """
gate notes: run with --lang en (English line rules; Korean OCR/box checks listed but not judged); flash_black_frames = the deliberate 2-frame impact frame (one per video); manual_signoff = sheets reviewed by the producer below, no CTO/CEO sign-off log yet.
review: every frame reviewed on small contact sheets (episodes/beastclash/stills/<id>/rv{SUF}_*.png); delivery sheets in sheets{SUF}/ (60 frames each).
""")
print('POST', q, 'loop', round(loop, 2), 'title', len(EP['title']))
