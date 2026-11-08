import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'common'))
from labio import Raw, LINES, timer
import torch
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

dev = os.environ.get('DEV', 'mps' if torch.backends.mps.is_available() else 'cpu')
model = ChatterboxMultilingualTTS.from_pretrained(device=dev)
raw = Raw('chatterbox-ml')
STYLES = {  # built-in voice (conds.pt shipped in ResembleAI/chatterbox); no reference clip
    'neutral': dict(exaggeration=0.5, cfg_weight=0.5, temperature=0.8),
    'comic': dict(exaggeration=1.0, cfg_weight=0.3, temperature=0.8),
    'comic2': dict(exaggeration=1.5, cfg_weight=0.3, temperature=0.9),
}
for st, kw in STYLES.items():
    for ln in LINES:
        if raw.have('builtin', st, ln['id']):
            continue
        torch.manual_seed(1234)
        t = timer()
        wav = model.generate(ln['tts'], language_id='ko', **kw)
        raw.save('builtin', st, ln['id'], wav.squeeze().cpu().numpy(), model.sr, params=dict(kw, device=dev), gen_s=t(), text=ln['tts'])
