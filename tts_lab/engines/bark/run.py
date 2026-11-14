import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'common'))
from labio import Raw, LINES, timer
import torch
from transformers import AutoProcessor, BarkModel

dev = os.environ.get('DEV', 'mps' if torch.backends.mps.is_available() else 'cpu')
proc = AutoProcessor.from_pretrained('suno/bark')
model = BarkModel.from_pretrained('suno/bark').to(dev)
sr = model.generation_config.sample_rate
raw = Raw('bark')
STYLES = {'neutral': dict(), 'comic': dict(semantic_temperature=0.95, coarse_temperature=0.8)}
spk_list = os.environ.get('SPK', ','.join(str(i) for i in range(10))).split(',')
for s in spk_list:
    preset = f'v2/ko_speaker_{s}'
    for st in os.environ.get('STY', 'neutral,comic').split(','):
        for ln in LINES:
            if raw.have(f'ko{s}', st, ln['id']):
                continue
            torch.manual_seed(1000 + ln['id'])
            t = timer()
            inp = proc(ln['tts'], voice_preset=preset).to(dev)
            with torch.no_grad():
                wav = model.generate(**inp, do_sample=True, **STYLES[st])
            raw.save(f'ko{s}', st, ln['id'], wav.squeeze().float().cpu().numpy(), sr,
                     params=dict(preset=preset, **STYLES[st], device=dev), gen_s=t(), text=ln['tts'])
