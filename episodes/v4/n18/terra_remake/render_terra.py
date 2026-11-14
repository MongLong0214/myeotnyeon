#!/usr/bin/env python3
"""Isolated N18 Terra remake: original drawn storyboards and MP4 assembly."""
from pathlib import Path
import json, math, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).parent
SRC=ROOT.parent/'cartoon_v6'
DATA=json.loads((SRC/'episode_data_v6fix2.json').read_text())
W,H=1920,1080
FONT='/System/Library/Fonts/AppleSDGothicNeo.ttc'
BOLD='/System/Library/Fonts/AppleSDGothicNeo.ttc'

def font(n):
    try:return ImageFont.truetype(BOLD,n,index=1)
    except:return ImageFont.load_default()

def polyline(d, pts, fill, width=7): d.line(pts,fill=fill,width=width,joint='curve')
def text(d,s,xy,size,fill=(31,39,44),anchor=None): d.text(xy,s,font=font(size),fill=fill,anchor=anchor,stroke_width=1,stroke_fill=(245,239,222) if fill[0]<100 else fill)

def bg(im,kind):
 d=ImageDraw.Draw(im)
 palettes={
 'ground':((212,185,126),(116,139,109),(235,216,171)), 'barracks':((93,111,107),(46,62,67),(173,151,109)),
 'command':((116,92,77),(58,48,45),(184,157,122)), 'medical':((173,191,180),(79,108,104),(229,228,210)),
 'court':((89,57,54),(49,31,32),(177,137,91)), 'family':((122,104,83),(50,45,43),(210,185,138)),
 'memorial':((78,83,91),(37,42,48),(215,202,170)), 'policy':((94,119,123),(46,69,72),(202,216,200))}
 a,b,c=palettes[kind]; d.rectangle((0,0,W,H),fill=a)
 # ceiling-to-floor perspective, no flat wall
 d.polygon([(0,0),(W,0),(W,520),(0,600)],fill=tuple(min(255,x+25) for x in a))
 d.polygon([(0,600),(W,520),(W,H),(0,H)],fill=b)
 for x in range(-400,W+500,250): polyline(d,[(W//2,520),(x,H)],tuple(min(255,v+15) for v in b),4)
 for y in (690,820,970): polyline(d,[(0,y),(W,y-80),(W,y-75),(0,y+5)],tuple(min(255,v+18) for v in b),4)
 if kind=='ground':
  d.ellipse((120,90,720,420),fill=(133,151,111)); d.ellipse((1150,90,1860,460),fill=(120,142,103)); d.rectangle((0,550,W,570),fill=(238,234,208))
  for x in (280,620,1040,1470,1750): d.ellipse((x,735,x+35,748),fill=(127,102,74))
 if kind=='court':
  d.polygon([(520,150),(1400,150),(1540,530),(390,530)],fill=(72,43,43)); d.rectangle((780,305,1140,510),fill=(61,37,37)); d.ellipse((910,230,1010,330),outline=(200,159,102),width=10)
 if kind=='medical':
  d.polygon([(1320,110),(1780,130),(1700,630),(1260,600)],fill=(206,216,202)); d.rectangle((1420,240,1550,430),outline=(70,107,102),width=18); d.rectangle((1467,275,1503,395),fill=(70,107,102)); d.rectangle((1430,318,1540,353),fill=(70,107,102))
 if kind=='barracks':
  for x in (120,740,1360):
   d.polygon([(x,220),(x+430,190),(x+390,530),(x+10,560)],fill=(119,134,122),outline=(45,61,64)); d.line((x+20,390,x+400,360),fill=(45,61,64),width=12)
 return d

def person(d,x,y,scale,role='recruit',pose='stand',face=0):
 # articulated, weighted body with shoulders/pelvis, hands and planted boots
 skin=(189,139,104); uniform={'recruit':(76,105,75),'officer':(59,75,61),'medic':(204,212,196),'mother':(102,78,70),'father':(64,71,82),'judge':(49,39,43),'staff':(115,93,72)}.get(role,(76,105,75))
 outline=(34,39,38); s=scale
 if pose=='fall':
  # side silhouette grounded: head, bent torso, one bent knee and one extended leg
  d.ellipse((x-195*s,y-54*s,x-105*s,y+36*s),fill=skin,outline=outline,width=max(3,int(7*s)))
  d.polygon([(x-110*s,y-20*s),(x+80*s,y-38*s),(x+155*s,y+42*s),(x-75*s,y+67*s)],fill=uniform,outline=outline)
  polyline(d,[(x+105*s,y+33*s),(x+250*s,y+120*s),(x+380*s,y+118*s)],outline,max(5,int(24*s))); polyline(d,[(x+105*s,y+33*s),(x+210*s,y+170*s),(x+95*s,y+215*s)],outline,max(5,int(24*s)))
  polyline(d,[(x-10*s,y+30*s),(x-100*s,y+120*s)],uniform,max(5,int(21*s))); d.ellipse((x-122*s,y+105*s,x-80*s,y+145*s),fill=skin,outline=outline,width=3)
  return
 # torso/neck/head
 d.polygon([(x-70*s,y+70*s),(x+62*s,y+58*s),(x+95*s,y+285*s),(x-92*s,y+300*s)],fill=uniform,outline=outline)
 d.rectangle((x-17*s,y+20*s,x+18*s,y+80*s),fill=skin,outline=outline,width=max(2,int(4*s)))
 d.ellipse((x-67*s,y-86*s,x+68*s,y+65*s),fill=skin,outline=outline,width=max(3,int(6*s)))
 # hair/cap and face gaze
 if role in ('recruit','officer'): d.pieslice((x-70*s,y-98*s,x+70*s,y+24*s),180,360,fill=(47,58,48),outline=outline,width=4); d.rectangle((x-80*s,y-32*s,x+79*s,y-5*s),fill=(47,58,48),outline=outline,width=3)
 else: d.arc((x-62*s,y-93*s,x+63*s,y+39*s),190,350,fill=outline,width=max(3,int(8*s)))
 d.ellipse((x+22*s,y-25*s,x+31*s,y-15*s),fill=outline); d.line((x+17*s,y+25*s,x+39*s,y+26*s),fill=outline,width=3)
 # pose specific arms with visible hands
 if pose=='look':
  arms=[((x-62*s,y+105*s),(x-155*s,y+155*s),(x-185*s,y+110*s)),((x+62*s,y+105*s),(x+155*s,y+178*s),(x+170*s,y+125*s))]
 elif pose=='kneel':
  arms=[((x-60*s,y+115*s),(x-125*s,y+225*s),(x-68*s,y+245*s)),((x+55*s,y+115*s),(x+118*s,y+220*s),(x+58*s,y+248*s))]
 else: arms=[((x-58*s,y+105*s),(x-120*s,y+195*s),(x-98*s,y+265*s)),((x+58*s,y+105*s),(x+110*s,y+200*s),(x+95*s,y+265*s))]
 for a,b,c in arms:
  polyline(d,[a,b,c],uniform,max(4,int(26*s))); d.ellipse((c[0]-18*s,c[1]-15*s,c[0]+20*s,c[1]+19*s),fill=skin,outline=outline,width=max(2,int(3*s)))
 # legs and boot contact
 if pose=='kneel': legs=[((x-52*s,y+285*s),(x-110*s,y+390*s),(x-25*s,y+420*s)),((x+45*s,y+285*s),(x+115*s,y+370*s),(x+45*s,y+420*s))]
 else: legs=[((x-54*s,y+285*s),(x-90*s,y+430*s),(x-130*s,y+505*s)),((x+48*s,y+285*s),(x+88*s,y+428*s),(x+145*s,y+500*s))]
 for a,b,c in legs:
  polyline(d,[a,b,c],uniform,max(5,int(33*s))); d.ellipse((c[0]-34*s,c[1]-9*s,c[0]+45*s,c[1]+20*s),fill=(38,43,40),outline=outline,width=max(2,int(4*s)))

def prop_pack(d,x,y,s):
 d.rounded_rectangle((x,y,x+180*s,y+225*s),radius=int(20*s),fill=(88,75,55),outline=(36,39,38),width=max(3,int(7*s)))
 for yy in (35,85,135): d.rectangle((x+25*s,y+yy*s,x+155*s,y+(yy+25)*s),fill=(182,156,105),outline=(55,50,38),width=3)

def scene(shot,i):
 action=(shot.get('action','')+' '+shot.get('scene','')+' '+shot.get('location','')).lower()
 if any(k in action for k in ['court','judge','prosecutor','appeal','supreme','indict','sentenc']): kind='court'
 elif any(k in action for k in ['medical','hospital','transport','infirmary','medic']): kind='medical'
 elif any(k in action for k in ['family','letter','call','farewell']): kind='family'
 elif any(k in action for k in ['memorial','flower']): kind='memorial'
 elif any(k in action for k in ['policy','inspect']): kind='policy'
 elif any(k in action for k in ['barrack','sleep']): kind='barracks'
 elif any(k in action for k in ['command','report','approve']): kind='command'
 else: kind='ground'
 im=Image.new('RGB',(W,H)); d=bg(im,kind)
 # every drawing has deep focal composition, foreground subject occupies frame
 if kind=='ground':
  if any(k in action for k in ['collapse','fallen','emergency']):
   person(d,860,675,1.22,'recruit','fall'); prop_pack(d,1080,575,.65)
   person(d,420,440,.86,'recruit','look'); person(d,1450,470,.83,'officer','look')
   d.ellipse((630,910,1240,956),fill=(62,69,55))
  elif any(k in action for k in ['push','run','race','march','drill']):
   person(d,590,410,1.05,'recruit','kneel'); prop_pack(d,745,570,.58); person(d,1230,370,.8,'recruit','look'); person(d,1540,395,.76,'officer','stand')
  else:
   person(d,700,400,1.1,'recruit','look'); prop_pack(d,890,570,.66); person(d,1320,430,.82,'officer','stand')
 elif kind=='medical':
  d.polygon([(470,640),(1370,600),(1500,800),(390,850)],fill=(231,228,209),outline=(47,76,74)); d.line((490,765,1460,720),fill=(60,87,84),width=14)
  person(d,880,595,.9,'recruit','fall'); person(d,420,410,.8,'medic','look'); person(d,1450,400,.82,'medic','look')
 elif kind=='court':
  person(d,960,255,1.0,'judge','stand'); person(d,510,480,.82,'staff','look'); person(d,1400,500,.82,'staff','look'); d.polygon([(360,740),(1560,700),(1680,935),(230,965)],fill=(91,59,49),outline=(45,29,29))
 elif kind=='family':
  d.polygon([(1000,610),(1650,590),(1750,870),(930,910)],fill=(91,67,48),outline=(44,37,34)); d.rectangle((1150,650,1490,850),fill=(238,229,200),outline=(75,62,49),width=8)
  for yy in range(690,810,38): d.line((1185,yy,1450,yy-20),fill=(122,110,90),width=5)
  person(d,720,355,1.05,'mother','look')
 elif kind=='memorial':
  d.rectangle((735,225,1185,710),fill=(44,48,54),outline=(213,197,161),width=10); d.rectangle((810,295,1110,570),fill=(83,81,78));
  for x in (500,650,1260,1410): d.ellipse((x,680,x+70,750),fill=(229,225,204),outline=(90,94,92),width=3); d.line((x+35,740,x+40,850),fill=(78,122,82),width=8)
  person(d,350,430,.75,'mother','look'); person(d,1540,420,.75,'father','look')
 elif kind=='policy':
  d.rounded_rectangle((530,230,1400,710),45,fill=(223,229,208),outline=(43,74,75),width=12); text(d,'06-01  →  08-31', (965,420),72,(39,73,74),'mm'); text(d,'혹서기 관리 기간', (965,525),42,(39,73,74),'mm'); person(d,320,420,.78,'officer','look')
 elif kind=='barracks':
  person(d,490,400,.9,'recruit','look'); person(d,880,420,.9,'recruit','look'); person(d,1370,400,.9,'officer','stand')
 else:
  d.polygon([(510,650),(1410,620),(1510,895),(400,920)],fill=(105,77,59),outline=(43,37,34)); person(d,670,400,1.0,'officer','look'); person(d,1270,420,1.0,'officer','stand')
 # subtitle is deliberately sparse, identifies spoken beat but leaves drawing readable
 label=shot.get('text','').replace('\n',' ')
 if len(label)>42: label=label[:42]+'…'
 d.rounded_rectangle((92,925,1828,1035),24,fill=(20,28,30))
 text(d,label,(960,980),37,(246,241,225),'mm')
 return im

def make_assets():
 out=ROOT/'frames'; out.mkdir(parents=True,exist_ok=True)
 for i,s in enumerate(DATA['shots']): scene(s,i).save(out/f'{i:03d}_{s["id"]}.png',quality=94)
 # concise alignment includes exact source audio time and original factual text
 rows=[]
 for i,s in enumerate(DATA['shots']): rows.append({'index':i,'frame':f'frames/{i:03d}_{s["id"]}.png','shot_id':s['id'],'start_s':s['start_s'],'end_s':s['end_s'],'narration_id':s.get('narrationId'),'spoken_text':s.get('text'),'visual_action':s.get('shows'),'facts':s.get('facts',[])})
 (ROOT/'shot_alignment.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))

def encode(name, rows, audio, start=0, dur=None, scale='1920:1080'):
 concat=ROOT/f'{name}.ffconcat'
 lines=['ffconcat version 1.0']
 for r in rows:
  lines += [f"file '{(ROOT/r['frame']).as_posix()}'",f"duration {r['end_s']-r['start_s']:.6f}"]
 # demuxer duration drops final file otherwise
 lines.append(f"file '{(ROOT/rows[-1]['frame']).as_posix()}'")
 concat.write_text('\n'.join(lines)+'\n')
 cmd=['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-ss',str(start),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-vf',f'scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:(ow-iw)/2:(oh-ih)/2,format=yuv420p','-r','30','-c:v','libx264','-preset','medium','-crf','19','-c:a','aac','-b:a','192k','-shortest',str(ROOT/name)]
 subprocess.run(cmd,check=True)

def main():
 make_assets(); rows=json.loads((ROOT/'shot_alignment.json').read_text()); audio=SRC/DATA['audio']
 proof=[r for r in rows if r['start_s'] < 82]
 encode('n18_terra_proof_1080p.mp4',proof,audio,0,None)
 encode('n18_terra_remake_1080p.mp4',rows,audio)
 # derive playable delivery, no video re-render art change
 subprocess.run(['ffmpeg','-y','-i',str(ROOT/'n18_terra_remake_1080p.mp4'),'-vf','scale=640:360','-c:v','libx264','-preset','medium','-crf','20','-c:a','aac','-b:a','96k',str(ROOT/'n18_terra_remake_360p.mp4')],check=True)
if __name__=='__main__':main()
