import sys; from PIL import Image
a=sys.argv[1:]; out=a[0]; fr=a[1:]
ims=[Image.open(f).convert('RGBA') for f in fr]; w,h=ims[0].size; n=len(ims); cols=2 if n>1 else 1; rows=(n+1)//2
S=Image.new('RGB',(w*cols,h*rows),(30,30,34))
for i,im in enumerate(ims):
    bg=Image.new('RGBA',im.size,(30,30,34,255)); bg.alpha_composite(im); S.paste(bg.convert('RGB'),((i%cols)*w,(i//cols)*h))
S.save(out)
