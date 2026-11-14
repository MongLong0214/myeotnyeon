import sys
from PIL import Image, ImageDraw
src,out,units,step=sys.argv[1],sys.argv[2],float(sys.argv[3]),int(sys.argv[4])
im=Image.open(src).convert('RGB'); k=im.width/units; d=ImageDraw.Draw(im)
for u in range(0,int(units),step):
    p=u*k; c=(255,0,0) if u%(step*2)==0 else (255,170,170)
    d.line([(p,0),(p,im.height)],fill=c); d.line([(0,p),(im.width,p)],fill=c)
    if u%(step*2)==0: d.text((p+2,2),str(u),fill=(0,0,200)); d.text((2,p+2),str(u),fill=(0,0,200))
im.save(out)
