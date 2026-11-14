"""Write licences/<engine>.md: model-card URL, YAML licence field, licence-section excerpt, code licence.
Sources are the model cards fetched to licences/raw/ (curl, no login) on 2026-10-26."""
import pathlib, re
L = pathlib.Path(__file__).resolve().parents[1] / 'licences'
RAW = L / 'raw'

def card(repo):
    f = RAW / (repo.replace('/', '_') + '.README.md')
    s = f.read_text(errors='ignore') if f.exists() else ''
    y = s.split('---')[1] if s.startswith('---') else ''
    lic = ' '.join(l.strip() for l in y.splitlines() if l.strip().lower().startswith(('license', 'license_name', 'license_link')))
    m = re.search(r'(?im)^#+\s*licen[cs]e.*?$(.*?)(?=^#+\s|\Z)', s, re.S | re.M)
    sec = (m.group(1).strip()[:900] if m else '')
    return lic, sec

ENG = {
    'supertonic3': dict(models=['Supertone/supertonic-3'], code='supertonic 1.3.1 (PyPI) - MIT (sample code, per model card); weights OpenRAIL-M (full text in work/tts/LICENSE_supertonic3.txt)',
                        status='OK - commercial use allowed under OpenRAIL-M use restrictions (no deception/impersonation etc.); disclose AI voice'),
    'chatterbox-ml': dict(models=['ResembleAI/chatterbox'], code='chatterbox-tts 0.1.7 - MIT (dist-info LICENSE, Copyright (c) 2025 Resemble AI)',
                          status='OK - MIT code + MIT weights. Output carries Resemble Perth imperceptible watermark (by design).'),
    'qwen3tts-cv': dict(models=['Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice', 'mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16'],
                        code='mlx-audio 0.6.1 - MIT (runtime); upstream Qwen3-TTS code Apache-2.0', status='OK - Apache-2.0 weights; built-in preset speakers only'),
    'qwen3tts-vd': dict(models=['Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign', 'mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16'],
                        code='mlx-audio 0.6.1 - MIT', status='OK - Apache-2.0 weights; voices designed from text descriptions (no reference audio)'),
    'melotts': dict(models=['myshell-ai/MeloTTS-Korean'], code='MeloTTS git 2091453 - MIT (Copyright (c) 2024 MyShell.ai); patched locally to KR-only imports',
                    status='OK - MIT code + weights'),
    'bark': dict(models=['suno/bark'], code='transformers 5.20.2 - Apache-2.0 (BarkModel); original suno-ai/bark code MIT', status='OK - MIT weights; ko_speaker_N presets ship with the model'),
    'voxcpm2': dict(models=['openbmb/VoxCPM2', 'mlx-community/VoxCPM2-bf16'], code='mlx-audio 0.6.1 - MIT; upstream OpenBMB/VoxCPM Apache-2.0', status='OK - Apache-2.0'),
    'ming3': dict(models=['inclusionAI/Ming-3.0-tts-0.5B'], code='mlx-audio 0.6.1 - MIT; upstream inclusionAI/Ming-3.0-tts', status='OK - MIT weights (model card); built-in voices + text voice design'),
}
REJ = {
    'OmniVoice (k2-fsa/OmniVoice)': 'k2-fsa/OmniVoice', 'Voxtral TTS (mistralai/Voxtral-4B-TTS-2603)': 'mistralai/Voxtral-4B-TTS-2603',
    'F5-TTS': 'SWivid/F5-TTS', 'MaskGCT': 'amphion/MaskGCT', 'MMS-TTS Korean': 'facebook/mms-tts-kor', 'XTTS-v2': 'coqui/XTTS-v2',
    'Higgs Audio v3': 'bosonai/higgs-audio-v3-tts-4b', 'Dramabox': 'ResembleAI/Dramabox', 'Kokoro-82M': 'hexgrad/Kokoro-82M',
}
for e, d in ENG.items():
    out = [f'# {e}', '', f'Status: {d["status"]}', f'Code/runtime: {d["code"]}', '']
    for r in d['models']:
        lic, sec = card(r)
        out += [f'## https://huggingface.co/{r}', f'Model card YAML: `{lic}`', '', 'Licence section excerpt:', '', '> ' + (sec.replace('\n', '\n> ') or '(no licence section; YAML field only)'), '']
    (L / f'{e}.md').write_text('\n'.join(out))
out = ['# Rejected / not usable (licence evidence)', '']
for name, r in REJ.items():
    lic, sec = card(r)
    out += [f'## {name} - https://huggingface.co/{r}', f'YAML: `{lic}`', '', '> ' + (sec[:600].replace('\n', '\n> ') or '(no licence section)'), '']
(L / 'REJECTED.md').write_text('\n'.join(out))
print('ok', sorted(p.name for p in L.glob('*.md')))
