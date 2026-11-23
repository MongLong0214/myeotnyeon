from html import unescape
from pathlib import Path
import hashlib
import json
import re

ROOT = Path('.sfx-work/recordings')
CUES = [
    (728347, 'High-speed turbine. Speed changes and a separate recorded grit layer follow tool load.'),
    (707344, 'Slow-speed pass on the roots. The page names the recording a dental slow handpiece.'),
    (707321, 'Dental suction pipe drawing mouthwash. Used behind milling and exposed during aspiration.'),
    (680616, 'Irrigation stream from a real syringe. Edited the nozzle contact-mic channel.'),
    (212178, 'Water spray from a pump bottle. Starts the handpiece irrigation and rinse.'),
    (209576, 'Water-dropper gurgles for small surface bubbles and liquid settling.'),
    (593682, 'Chicken and knife contact for soft incision texture.'),
    (540338, 'Wet fruit and knife contact for a quieter scalpel pass.'),
    (211605, 'Wet tissue movement Foley for retraction, root release and the gauze set-down.'),
    (574752, 'Recorded celery snaps for the two tooth cracks and quieter root releases.'),
    (816678, 'Steel knife on sharpening stone for the rasp under loaded bur passes.'),
    (816680, 'Short steel-on-stone scrapes for elevator contact against the kerf and bone.'),
    (155913, 'Real tweezers against a tooth for forceps closures and metal contacts.'),
    (456772, 'Sewing pin through fabric for needle contacts.'),
    (563779, 'Recorded hand embroidery through taut linen for needle travel and suture pulls.'),
    (10219, 'Real scissors snip for the thread trim.'),
    (481935, 'One small metal object set down on a metal tray. Mixed under the specimen set-down.'),
    (406512, 'Quiet operating-room tone and distant monitor cadence from the same field recording.'),
    (12328, 'Sparse plucked and ambient suspense underscore. Publisher-supplied music master.'),
]
intro = '''# Audio sources

Verified 2026-11-23 against the linked item pages. The licences permit commercial synchronized use without mandatory attribution. The Pixabay music listing showed no Content ID registration badge. [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) · [Pixabay Content License](https://pixabay.com/service/license-summary/)

Each SHA-256 identifies the exact MP3 ingested. Freesound inputs are the public high-quality previews listed on the source pages. The effects use recorded material throughout. The incision, bone scrape, cracks and suture use recorded Foley where clinical close-mic recordings were unavailable. The handpiece page labels its recording as a slow handpiece and uses “fast hand drill” in the description. The score is an existing release from 2021 and its listing describes plucked strings and ambient pads without specifying the performance or recording method.

The six WAV stems are printed for local editing at 48 kHz, stereo, 24-bit PCM. They share the video's 52.65 s start and duration and sum to the pre-AAC master. The Pixabay excerpts are incorporated into edited cues and score automation in those scene-length stems.

| Use in mix | Source and creator | Licence | SHA-256 |
| --- | --- | --- | --- |
'''
lines = [intro]
for asset, use in CUES:
    p = ROOT / f'{asset}.mp3'
    page = p.with_suffix('.html').read_text()
    title = unescape(re.search(r'<title>([^<]+)', page)[1]).strip()
    if title.startswith('Freesound - '):
        assert re.search(r'Go to the full license text[^>]+creativecommons\.org/publicdomain/zero/1\.0', page), asset
        url = f'https://freesound.org/s/{asset}/'
        title = title.removeprefix('Freesound - ')
        licence = 'CC0 1.0'
    else:
        url = re.search(r'<link\b[^>]+rel="canonical"[^>]+href="([^"]+)', page)[1]
        title = title.split(' | ')[0]
        assert 'https://pixabay.com/service/license-summary/' in page, asset
        assert 'Content ID Registered' not in page, asset
        licence = 'Pixabay Content License'
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    lines.append(f'| {use} | [{title}]({url}) | {licence} | `{digest}` |\n')
Path('SOURCES_AUDIO.md').write_text(''.join(lines))
