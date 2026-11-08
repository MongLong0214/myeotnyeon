"""Unprompted ASR of the delivered q006 AAC, using the existing local model."""
import importlib.util
import json
from pathlib import Path
import re
import time
import mlx_whisper

Q = Path(__file__).resolve().parent
W = Q.parents[2]
spec = importlib.util.spec_from_file_location('episode_tts', Q / 'tts.py')
tts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tts)

def norm(s):
    for a, b in tts.LEX:
        s = s.replace(a, b)
    return re.sub(r'[^가-힣0-9]', '', s)

def distance(a, b):
    row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev = row[:]
        row[0] = i
        for j, cb in enumerate(b, 1):
            row[j] = min(prev[j] + 1, row[j - 1] + 1, prev[j - 1] + (ca != cb))
    return row[-1]

if __name__ == '__main__':
    start = time.monotonic()
    path = W / 'upload/v3b_q006.mp4'
    result = mlx_whisper.transcribe(str(path), path_or_hf_repo='mlx-community/whisper-large-v3-turbo',
                                   language='ko', initial_prompt=None, condition_on_previous_text=False, temperature=0)
    expected = ' '.join(i['text'] for i in json.loads((Q / 'timing.json').read_text())['items'])
    a, b = norm(expected), norm(result['text'])
    errors = distance(a, b)
    output = dict(model='cached whisper-large-v3-turbo', input=str(path), initial_prompt=None,
                  normalization='Existing episode TTS number lexicon; whitespace and punctuation removed. No semantic substitutions.',
                  expected=expected, text=result['text'], normalized_expected=a, normalized_asr=b,
                  errors=errors, characters=len(a), match=1-errors/len(a),
                  passed=1-errors/len(a) >= .99, segments=result['segments'], seconds=time.monotonic()-start)
    (Q / 'asr_final_v3b.json').write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(json.dumps({k: output[k] for k in ['text', 'errors', 'characters', 'match', 'passed']}, ensure_ascii=False))
