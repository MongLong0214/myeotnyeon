from analyze import *
for k in sys.argv[1:] or list(VIDEOS):
 m=meta(k);targets=[int(i*.5*m['fps']+.5) for i in range(120)];cap=cv2.VideoCapture(str(R/'tmp'/f'{k}_proxy.mp4'));sheet=Image.new('RGB',(1920,2325));dr=ImageDraw.Draw(sheet)
 for i,fr in enumerate(targets):
  x=i%8*240;y=i//8*155;sheet.paste(imageframe(cap,fr,(240,135)),(x,y+20));dr.text((x+4,y+2),f'{i*.5:04.1f}s [f{fr}]',fill='white',font=ImageFont.truetype(FONT,13))
 cap.release();sheet.save(R/f'{k}_first60_2fps.jpg',quality=88)
 for j in range(3):sheet.crop((0,j*775,1920,(j+1)*775)).save(R/f'{k}_first60_part{j+1}.jpg',quality=90)
 print(k,'CONTACT DONE',flush=True)
a=Image.open(R/'ref_first60_2fps.jpg');b=Image.open(R/'ours_first60_2fps.jpg');out=Image.new('RGB',(3840,2365));out.paste(a,(0,40));out.paste(b,(1920,40));dr=ImageDraw.Draw(out);font=ImageFont.truetype(FONT,24);dr.text((10,5),'REFERENCE: 30 fps / 2 samples per second',fill='white',font=font);dr.text((1930,5),'N18 TYPE2: 5 fps / nearest native frame (+0.1s at half-second)',fill='white',font=font);out.save(R/'ref_vs_ours_first60.jpg',quality=90)
