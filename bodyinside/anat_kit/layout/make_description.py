#!/usr/bin/env python3
"""description.txt for the upload, generated per episode from ABOUT_BLOCK.txt and SOURCES.md. usage: python make_description.py EPISODE_DIR"""
import sys, json, re
E = sys.argv[1]; ep = json.load(open(E + '/episode.json')); about = open(E + '/ABOUT_BLOCK.txt', encoding='utf-8').read().strip(); src = open(E + '/SOURCES.md', encoding='utf-8').read()
import os
rp = E + '/REFERENCES.txt'  # plain-text citations; SOURCES.md table rows must never reach the public description
refs = [l.strip() for l in open(rp, encoding='utf-8') if l.strip()] if os.path.exists(rp) else [l.strip() for l in src.splitlines() if re.search(r'https?://|\bet al\b|\d{4};\d+|doi', l, re.I) and not l.lstrip().startswith('|')]
parts = [' '.join(ep['title']), '', about, '', '내레이션 / Narration: Qwen3-TTS 12Hz-1.7B CustomVoice (speaker Sohee, Apache-2.0), local AI synthesis. SFX: procedural. Image: 3D CG illustration, not medical advice.', '', '참고 / References:'] + refs
open(E + '/description.txt', 'w', encoding='utf-8').write('\n'.join(parts) + '\n'); print('description.txt', len('\n'.join(parts)), 'chars')
