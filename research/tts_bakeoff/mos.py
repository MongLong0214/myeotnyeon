"""UTMOS22-strong naturalness proxy (English-trained; indicative only). Runs in venvs/melo (torch)."""
import os, json, glob; HERE = os.path.dirname(os.path.abspath(__file__)); os.environ['TORCH_HOME'] = f'{HERE}/torch_hub'
import torch, librosa
pred = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True, skip_validation=True)
out = {}
for f in sorted(glob.glob(f'{HERE}/samples/*.wav')):
    x, _ = librosa.load(f, sr=16000); out[os.path.basename(f)[:-4]] = float(pred(torch.from_numpy(x).unsqueeze(0), 16000))
    print(os.path.basename(f), round(out[os.path.basename(f)[:-4]], 2))
json.dump(out, open(f'{HERE}/raw/utmos.json', 'w'), indent=1)
