import sys
from PIL import Image, ImageDraw
out, cell, cols, *fs = sys.argv[1:]
cell=int(cell); cols=int(cols)
rows=(len(fs)+cols-1)//cols
S=Image.new('RGB',(cols*cell,rows*(cell+22)),'#dddddd'); d=ImageDraw.Draw(S)
for i,f in enumerate(fs):
    im=Image.open(f).convert('RGBA'); im.thumbnail((cell-8,cell-8))
    x=(i%cols)*cell; y=(i//cols)*(cell+22)
    S.paste(im,(x+(cell-im.width)//2,y+(cell-im.height)//2),im)
    d.text((x+6,y+cell+4),f.split('/')[-1][:40],fill='black')
S.save(out)
