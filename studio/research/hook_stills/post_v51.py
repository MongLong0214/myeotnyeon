from pathlib import Path
import subprocess,json
W=Path(__file__).resolve().parents[2]
for q in ['q015','q012','q016','q017']:
 p=W/'research/hook_stills';src=p/f'{q}_raw.png'
 if not src.exists():continue
 out=p/f'{q}.png'
 if out.exists():continue
 # Test's teal/warm night grade, restrained optical halation, lens vignette and fine deterministic grain.
 graph="[0:v]format=gbrpf32le,split=2[base][glow];[glow]gblur=sigma=13,colorchannelmixer=rr=.12:gg=.12:bb=.12[b];[base][b]blend=all_mode=addition,eq=contrast=1.025:saturation=.91:brightness=.005,colorbalance=bs=.018:gs=.009:rh=.015,vignette=angle=0.38,noise=alls=4:allf=u,format=rgb48be[v]"
 subprocess.run(['ffmpeg','-v','error','-n','-i',str(src),'-filter_complex',graph,'-map','[v]','-frames:v','1',str(out)],check=True)
 subprocess.run(['ffmpeg','-v','error','-n','-i',str(out),'-frames:v','1','-q:v','2',str(p/f'{q}.jpg')],check=True)
 print(q,flush=True)
