"""Assemble a 540×960 review cut with the kit's vertical layout and 2-second editorial changes."""
import argparse
import json
from functools import lru_cache
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont
import numpy as np

P = Path(__file__).resolve().parent
WORK = P.parents[2]
KIT = WORK / "anat_kit"
PLATES = P / "plates"
W, H = 540, 960
BAND_Y, BAND_H = 248, 440
AMBER = (255,194,77)
INK = (22,23,25)
ap = argparse.ArgumentParser()
ap.add_argument("draft_number",type=int,choices=range(1,6))
ap.add_argument("--draft",required=True,action="store_true")
args=ap.parse_args()
tag=f"main_draft{args.draft_number}"
raw=P/f"frames_{tag}_raw"
labels=P/f"frames_{tag}"
for d in (raw,labels,P/"gates"):
    d.mkdir(exist_ok=True)
episode=json.loads((P/"episode.json").read_text())
anchors=json.loads((P/"anchors.json").read_text())
fps=episode["fps"]
beats=episode["beats"]
nframes=round(episode["duration"]*fps)
shot_frames=2*fps
num_shots=nframes//shot_frames
# Start on the close cutaway, then pull back to the translucent whole jaw.
shot_order=(2,1,*range(3,num_shots+1))
font=ImageFont.truetype(WORK/"branding/_src/public/fonts/Pretendard-Bold.otf",25)
subprocess.run([sys.executable,str(KIT/"layout/compose.py"),str(P)],check=True)
base=Image.open(P/"comp/base.png").convert("RGB").resize((W,H),Image.Resampling.LANCZOS)
band_bg=Image.open(P/"comp/band_bg.png").convert("RGBA").resize((W,BAND_H),Image.Resampling.LANCZOS)
caps=[Image.open(P/f"comp/cap_{i}.png").convert("RGBA").resize((W,H),Image.Resampling.LANCZOS)
      for i,b in enumerate(beats)]

@lru_cache
def load(name):
    return Image.open(PLATES/f"{name}.png").convert("RGBA")

def smooth(t):
    t=min(1,max(0,t))
    return t*t*(3-2*t)

def reframe(im, zoom, dx, dy):
    # Affine sampling on premultiplied alpha retains clean edges during the push.
    w,h=im.size
    sx,sy=w/(W*zoom), h/(BAND_H*zoom)
    return im.convert("RGBa").transform((W,BAND_H),Image.Transform.AFFINE,
        (sx,0,w/2-sx*(W/2+dx),0,sy,h/2-sy*(BAND_H/2+dy)),
        resample=Image.Resampling.BICUBIC).convert("RGBA")

def leader(d, point, align, y, label):
    x=50 if align=="left" else W-50
    ax,ay=point
    edge=x+(font.getlength(label)+8)*(1 if align=="left" else -1)
    d.line([(edge,y+23),(ax,ay)],fill=(242,239,230),width=1)
    d.ellipse((ax-4,ay-4,ax+4,ay+4),fill=AMBER,outline=INK,width=1)
    d.text((x,y),label,font=font,fill=(251,248,238),
           anchor="lt" if align=="left" else "rt",stroke_width=2,stroke_fill=INK)

def draw_label(band,i,points):
    d=ImageDraw.Draw(band)
    relevant=episode["labels"]
    for item in (l for l in relevant if l["f0"]==(i-1)*shot_frames):
        if item["kind"]=="angle_arc":
            top=points["axis_top"]
            bottom=points["axis_bottom"]
            dx,dy=top[0]-bottom[0],top[1]-bottom[1]
            a=(bottom[0]-dx*.25,bottom[1]-dy*.25)
            b=(top[0]+dx*.35,top[1]+dy*.35)
            d.line([a,b],fill=INK,width=6)
            d.line([a,b],fill=AMBER,width=3)
            for cx,cy in (a,b):
                d.ellipse((cx-4,cy-4,cx+4,cy+4),fill=AMBER)
            d.text((W/2,58),item["text"],font=font,fill=(255,219,150),
                   anchor="mt",stroke_width=2,stroke_fill=INK)
        else:
            if i in (7,8,16) and item["anchor"]=="nerve":
                col,y="left",BAND_H-74
            elif item["anchor"]=="m2":
                col,y="left",50
            elif i in (10,11,12,13,14):
                col,y="right",56 if i in (10,13) else BAND_H-74
            else:
                col,y="right",54
            leader(d,points[item["anchor"]],col,y,item["text"])

def jaw(i,u):
    n=f"jaw_{shot_order[i-1]:02}"
    push=(u if i%2 else 1-u)
    zoom=1.04+.14*push
    dx=(u-.5)*(20 if i%2 else -22)
    dy=(u-.5)*(13 if i in (1,7,11,13,15) else -11)
    plate=reframe(load(n),zoom,dx,dy)
    pts={k:(W/2+(x-.5)*W*zoom+dx,BAND_H/2+(y-.5)*BAND_H*zoom+dy)
         for k,(x,y) in anchors[n].items()}
    return plate,pts

def background(plate):
    canvas=band_bg.copy()
    canvas.alpha_composite(plate)
    return canvas

def band(f):
    i,j=divmod(f,shot_frames)
    i+=1
    current, pts=jaw(i,j/(shot_frames-1))
    clean=background(current)
    comp=clean.copy()
    draw_label(comp,i,pts)
    if i>1 and j<16:
        previous,prevpts=jaw(i-1,1)
        prevclean=background(previous)
        prevcomp=prevclean.copy()
        if i % 2 == 0:
            draw_label(prevcomp,i-1,prevpts)
        k=smooth((j+1)/16)
        return Image.blend(previous,current,k),Image.blend(prevcomp,comp,k)
    return current,comp

def loud_audio():
    src=str(P/"audio/sfx.wav")
    limited=str(P/"audio/main_limited.wav")
    normalized=str(P/"audio/main_norm.wav")
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-af",
                    "alimiter=limit=0.35:attack=3:release=60:level=false:latency=1",limited],check=True)
    norm="loudnorm=I=-14:TP=-1.5:LRA=11"
    check=subprocess.run(["ffmpeg","-hide_banner","-i",limited,"-af",norm+":print_format=json",
                          "-f","null","-"],check=True,capture_output=True,text=True).stderr
    m=json.loads(check[check.rindex("{"):check.rindex("}")+1])
    terms=f":measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
    subprocess.run(["ffmpeg","-v","error","-y","-i",limited,"-af",
                    norm+terms+":linear=true,aresample=48000",normalized],check=True)
    return normalized

audio=loud_audio()
out=P.parent/f"{tag}.mp4"
cmd=["ffmpeg","-v","error","-y","-f","rawvideo","-pixel_format","rgb24","-video_size",
     f"{W}x{H}","-framerate",str(fps),"-i","pipe:0","-i",audio,"-c:v","libx264",
     "-threads","4","-preset","fast","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",
     "-t",str(episode["duration"]),"-movflags","+faststart",str(out)]
with subprocess.Popen(cmd,stdin=subprocess.PIPE) as encoder:
    beat_id=0
    for f in range(nframes):
        while f>=int(beats[beat_id]["t1"]*fps):
            beat_id+=1
        plate,b=band(f)
        plate.save(raw/f"f_{f:04}.png",compress_level=1)
        b.save(labels/f"f_{f:04}.png",compress_level=1)
        page=base.copy()
        page.paste(b.convert("RGB"),(0,BAND_Y))
        page.paste(caps[beat_id],mask=caps[beat_id].getchannel("A"))
        encoder.stdin.write(page.tobytes())
    encoder.stdin.close()
    if encoder.wait():
        raise SystemExit("ffmpeg failed")
cols=4
sheet=Image.new("RGB",(cols*180,((num_shots+cols-1)//cols)*320),INK)
for i in range(num_shots):
    sample=2*i+1 if i else 0
    shot=subprocess.run(["ffmpeg","-v","error","-ss",str(sample),"-i",str(out),"-frames:v","1",
        "-vf","scale=180:320","-f","rawvideo","-pix_fmt","rgb24","pipe:1"],check=True,capture_output=True).stdout
    sheet.paste(Image.frombytes("RGB",(180,320),shot),((i%cols)*180,(i//cols)*320))
sheet.save(P.parent/f"sheet_{tag}.png")
man=[dict(name="BodyParts3D Release 4.0",licence="CC BY 4.0"),
     dict(name="Z-Anatomy cutaway (owner review pending)",licence="CC BY-SA 4.0")]
(P/"assets.json").write_text(json.dumps(man,indent=2)+"\n")
layout=dict(fps=fps,safe=[60,180,1020,1500], text_boxes_file=str(P/"comp/text_boxes.json"),
    assets_manifest=str(P/"assets.json"),episode_json=str(P/"episode.json"),
    allowed_hue_bins=[0,1,11],
    event_checks=[dict(name=f"picture change at {i*2}s",a=i*shot_frames-15,b=i*shot_frames+14,
                      roi=[.06,.12,.94,.90],metric="luma_delta",min=1.0)
                  for i in range(1,num_shots)])
(P/"gates/layout.json").write_text(json.dumps(layout,indent=2)+"\n")
print(out)
