"""sheets.py <video> <outdir> [per_sheet=60] : every decoded frame (30 fps) into labelled contact sheets"""
import sys,subprocess,math,tempfile,glob,os
from PIL import Image,ImageDraw
v,out=sys.argv[1],sys.argv[2];per=int(sys.argv[3]) if len(sys.argv)>3 else 60;os.makedirs(out,exist_ok=True)
tmp=tempfile.mkdtemp();subprocess.run(['ffmpeg','-v','error','-i',v,'-vf','scale=180:320','-vsync','0',f'{tmp}/%05d.png'],check=True)
fs=sorted(glob.glob(f'{tmp}/*.png'));cols=10;tw,th=180,320
for k in range(math.ceil(len(fs)/per)):
 part=fs[k*per:(k+1)*per];im=Image.new('RGB',(cols*tw,math.ceil(len(part)/cols)*(th+16)),'#111');d=ImageDraw.Draw(im)
 for i,f in enumerate(part):
  n=k*per+i;x=i%cols*tw;y=i//cols*(th+16);im.paste(Image.open(f),(x,y+16));d.text((x+3,y+2),f'f{n} {n/30:.2f}s',fill='white')
 im.save(f'{out}/sheet_{k:02d}_f{k*per:04d}-{k*per+len(part)-1:04d}.png')
print(len(fs),'frames',math.ceil(len(fs)/per),'sheets')
