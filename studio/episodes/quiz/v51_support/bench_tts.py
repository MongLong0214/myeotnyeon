import time
from supertonic import TTS
s=time.monotonic();t=TTS(auto_download=False,intra_op_num_threads=1,inter_op_num_threads=1);print('load',time.monotonic()-s,flush=True);s=time.monotonic();x,_=t.synthesize('다음 사건도 맞혀 보세요.',voice_style=t.get_voice_style('M1'),lang='ko',speed=1.1,total_steps=8);print('synth',time.monotonic()-s,len(x.reshape(-1))/44100,flush=True)
