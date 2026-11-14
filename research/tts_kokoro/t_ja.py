import sys,os
os.environ.update(HF_HOME=os.path.abspath('hf'),HF_HUB_OFFLINE='1')
from gen import synth
from asr import asr
import soundfile as sf
for i,t in enumerate(sys.argv[1:]):
    x,sr=synth('j','jf_alpha',1.1,t);sf.write(f'test/v{i}.wav',x,sr);print(t,'=>',asr(f'test/v{i}.wav','ja')['text'])
