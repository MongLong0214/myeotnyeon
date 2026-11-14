"""local mlx whisper-large-v3-turbo transcript of each wav: asr.py <lang> <wav...>"""
import os, sys
os.environ.update(HF_HUB_OFFLINE='1')
from pathlib import Path
import mlx_whisper
M = next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
def asr(path, lang, words=False):
    return mlx_whisper.transcribe(str(path), path_or_hf_repo=str(M), language=lang, temperature=0, condition_on_previous_text=False, word_timestamps=words, verbose=None)
if __name__ == '__main__':
    for p in sys.argv[2:]: print(Path(p).stem, '|', asr(p, sys.argv[1])['text'].strip())
