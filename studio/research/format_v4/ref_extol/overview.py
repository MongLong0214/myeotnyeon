from analyze import *
for k in sys.argv[1:] or list(VIDEOS):
 d=R/k;m=meta(k);cap=cv2.VideoCapture(str(R/'tmp/ref_proxy.mp4' if k=='ref' else VIDEOS[k]));times=list(range(0,math.ceil(m['duration']),3))
 for a in range(0,len(times),50):
  ts=times[a:a+50];sheet=Image.new('RGB',(1600,202*math.ceil(len(ts)/5)));dr=ImageDraw.Draw(sheet)
  for j,t in enumerate(ts):
   x=j%5*320;y=j//5*202;sheet.paste(imageframe(cap,round(t*m['fps']),(320,180)),(x,y+22));dr.text((x+3,y+2),f'{t}s',fill='white',font=ImageFont.truetype(FONT,15))
  sheet.save(d/f'overview_{a//50+1:02}.jpg',quality=90)
 cap.release()
