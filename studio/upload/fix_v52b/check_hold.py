import subprocess,sys,json,math
from pathlib import Path
import numpy as np
p=Path(__file__).resolve().parent
q=sys.argv[1]
a,b,h={'012':(917,921,916),'016':(841,844,840),'017':(623,626,622)}[q]
fc=f'[0:v]split[s][r];[s][r]freezeframes=first={a}:last={b}:replace={h},select=between(n\\,{h}\\,{b})[v]'
r=subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(p.parent/f'v52_q{q}.mp4'),'-filter_complex',fc,'-map','[v]','-fps_mode','passthrough','-f','framemd5','-'],check=True,stdout=subprocess.PIPE)
(p/f'q{q}_preencode_hold.framemd5').write_bytes(r.stdout)
hashes=[l.rsplit(',',1)[-1].strip() for l in r.stdout.decode().splitlines() if l and not l.startswith('#')]
assert len(hashes)==b-h+1
assert len(set(hashes))==1
r=subprocess.run(['ffmpeg','-v','error','-threads','2','-i',str(p/f'v52b_q{q}.mp4'),'-vf',f'select=between(n\\,{h}\\,{b})','-fps_mode','passthrough','-pix_fmt','yuv420p','-f','rawvideo','-'],check=True,stdout=subprocess.PIPE)
frames=np.frombuffer(r.stdout,np.uint8).reshape((-1,1080*1920*3//2))
assert len(frames)==b-h+1
ref=frames[0].astype(np.float64)
results=[]
for i,fr in enumerate(frames[1:],start=a):
 mse=np.mean((fr.astype(np.float64)-ref)**2)
 psnr=10*math.log10(255**2/mse) if mse else float('inf')
 assert psnr>=45
 results.append({'frame':i,'psnr_vs_output_held':psnr})
(p/f'q{q}_hold_check.json').write_text(json.dumps({'preencode_md5':hashes[0],'exact_preencode_repeats':len(hashes)-1,'decoded_output_hold_comparison':results},indent=2)+'\n')
print(q,results)
