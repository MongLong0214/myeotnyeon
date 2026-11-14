"""sheet.py <out.png> <cols> <thumb_w> <img...>  -> labelled contact sheet"""
import sys,math,re
from PIL import Image,ImageDraw
out,cols,tw=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]);files=sys.argv[4:];th=tw*16//9
im=Image.new('RGB',(cols*tw,math.ceil(len(files)/cols)*(th+18)),'#111');d=ImageDraw.Draw(im)
for i,fn in enumerate(files):
 x=i%cols*tw;y=i//cols*(th+18);im.paste(Image.open(fn).convert('RGB').resize((tw,th)),(x,y+18))
 m=re.search(r'(\d+)\D*$',fn);n=int(m[1]) if m else i;d.text((x+3,y+3),f'f{n} {n/30:.2f}s',fill='white')
im.save(out)
