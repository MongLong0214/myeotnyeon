import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'common'))
from labio import Raw, LINES, timer
import torch
from melo.api import TTS

dev = os.environ.get('DEV', 'cpu')
model = TTS(language='KR', device=dev)
spk = model.hps.data.spk2id
print('speakers', dict(spk), flush=True)
raw = Raw('melotts')
STYLES = {'neutral': dict(speed=1.0, sdp_ratio=0.2, noise_scale=0.6, noise_scale_w=0.8),
          'fast': dict(speed=1.25, sdp_ratio=0.2, noise_scale=0.6, noise_scale_w=0.8),
          'comic': dict(speed=1.25, sdp_ratio=0.8, noise_scale=0.9, noise_scale_w=1.0)}
for name, sid in spk.items():
    for st, kw in STYLES.items():
        for ln in LINES:
            if raw.have(name, st, ln['id']):
                continue
            torch.manual_seed(1000 + ln['id'])
            t = timer()
            wav = model.tts_to_file(ln['tts'], sid, None, quiet=True, **kw)
            raw.save(name, st, ln['id'], wav, model.hps.data.sampling_rate, params=dict(kw, device=dev), gen_s=t(), text=ln['tts'])
