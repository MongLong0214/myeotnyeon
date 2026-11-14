import os,json,subprocess,csv,hashlib,sys
from pathlib import Path
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
def sheet(times,path,cols=5,size=(320,180)):
 cap=cv2.VideoCapture(str(R/'tmp/ref_proxy.mp4')); out=Image.new('RGB',(cols*size[0],((len(times)+cols-1)//cols)*(size[1]+22)))
 dr=ImageDraw.Draw(out)
 for i,t in enumerate(times):
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,im=cap.read()
  if not ok: raise ValueError(t)
  x=i%cols*size[0];y=i//cols*(size[1]+22);out.paste(Image.fromarray(cv2.cvtColor(cv2.resize(im,size),cv2.COLOR_BGR2RGB)),(x,y+22));dr.text((x+4,y+3),f'{t:.2f}s',font=ImageFont.truetype(FONT,13),fill='white')
 cap.release();out.save(R/path,quality=90)
if len(sys.argv)>1 and sys.argv[1]=='overview':
 sheet(list(range(0,522,6)),'overview_labeled.jpg',6)
 for a in [0,20,40]:sheet([x+.5 for x in range(a,a+20)],f'first60_{a:02}.jpg',4,(400,225))
if len(sys.argv)>1 and sys.argv[1]=='audio':
 sys.path.insert(0,str(R));from measure_audio import measure
 d=json.loads((R/'ref/whisper_words.json').read_text());d['segments']=[s for s in d['segments'] if s['id']!=100];(R/'reference_transcript.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));(R/'reference_transcript.txt').write_text('\n'.join(f"{s['start']:.2f}–{s['end']:.2f} {s['text'].strip()}" for s in d['segments']))
 measure('reference',R/'reference.mp4',[131.1,231.9,416.0,473.8],[("first shot",117),("post office isolation",263.52),("funeral reversal",347.32),("police hidden",460),("final massacre",397.72)])
 from measure import audio
 audio('ref')
