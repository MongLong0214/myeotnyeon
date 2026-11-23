"""Composite the native 30 fps plates, operative captions and two section transitions."""
import argparse
import bisect
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
EP=Path(__file__).resolve().parent.parent
WORK=EP.parents[1]
CACHE=EP/'production/.cache'
sys.path.insert(0,str(WORK/'anat_kit/layout'))
from operative_captions import OperativeCaptions, S

FONTS=WORK/'branding/_src/public/fonts'
STYLE=OperativeCaptions(FONTS/'Pretendard-Bold.otf',FONTS/'BlackHanSans-Regular.ttf')
SPEC=json.loads((EP/'episode.json').read_text())
N=round(SPEC['duration']*SPEC['fps'])
FPS=SPEC['fps']
def cue(frame,lines,keyword,stage):
    return (frame,tuple(lines),keyword,tuple(stage))
def make_cues():
    cues=[]
    for beat in SPEC['beats'][:8]:
        lines=''.join(t for t,c in beat['cap']).split('\n')
        word=next(t for t,c in beat['cap'] if c==[255,202,107])
        cues.append(cue(round(beat['t0']*FPS),lines,word,beat['stage']))
    for change in SPEC['beats'][8]['caption_cues']:
        cues.append(cue(round(change['t0']*FPS),change['lines'],change['keyword'],change['stage']))
    switch=round(SPEC['loop']['caption_switch_at_full_occlusion_s']*FPS)
    cues.append(cue(switch,cues[0][1],cues[0][2],cues[0][3]))
    return cues
CUES=make_cues()
STARTS=[c[0] for c in CUES]

@lru_cache(maxsize=180)
def header(i,enter,leave,scale):
    start,lines,word,stage=CUES[i]
    im=Image.new('RGBA',(540*scale,292*scale))
    if scale==1:
        overlay=STYLE.overlay(lines,word,enter/FPS,leave/FPS,stage)
        return overlay.crop((0,0,540,292))
    title=STYLE.title(lines,word)
    q=min(1,enter/(FPS*.17)); ease=1-(1-q)**3
    zoom=.93+.07*ease+.012*math.sin(math.pi*q)
    out=min(1,leave/(FPS*.105))
    w,h=(round(size*zoom/S)*scale for size in title.size)
    tile=title.resize((w,h),Image.Resampling.LANCZOS)
    tile.putalpha(tile.getchannel('A').point(lambda a:round(a*(.48+.52*ease)*(.44+.56*out))))
    im.alpha_composite(tile,((im.width-w)//2,scale*(150+round(5*(1-ease)))))
    # Use the kit's stroke geometry for the badge at its native high-resolution design scale.
    n,total,name=stage;font=STYLE.font(18)
    pw=round(92*S+font.getlength(name));ph=35*S
    pill=Image.new('RGBA',(pw,ph));d=ImageDraw.Draw(pill)
    d.rounded_rectangle((0,0,pw-1,ph-1),radius=ph/2,fill=(30,24,26,226),outline=(255,243,217,155),width=S)
    d.rounded_rectangle((3*S,3*S,40*S,32*S),radius=12*S,fill='#FFCA6B')
    d.text((21*S,17*S),f'{n:02d}',font=STYLE.font(21),fill='#21191A',anchor='mm')
    d.text((45*S,17*S),f'/ {total:02d}',font=STYLE.font(14),fill='#EEE2D2',anchor='lm')
    d.line((76*S,10*S,76*S,25*S),fill=(255,255,255,90),width=S)
    d.text((82*S,17*S),name,font=font,fill='#FFF9ED',anchor='lm')
    pill=pill.resize((scale*round(pw/S),35*scale),Image.Resampling.LANCZOS)
    im.alpha_composite(pill,((im.width-pill.width)//2,108*scale))
    return im

def border(plate,frame):
    # Replace exposed neutral studio background at the outer lip and section edge of the wide hook.
    if not (frame<45 or frame>=915):return plate
    arr=np.array(plate);h,w=arr.shape[:2]
    for y0,y1 in [(0,h//7),(9*h//10,h)]:
        roi=arr[y0:y1].astype(np.float32)
        sat=np.ptp(roi,axis=2);lum=roi.mean(axis=2)
        near=(sat<20)&(lum>94)&(lum<187)
        count,cc,stats,_=cv2.connectedComponentsWithStats(near.astype('uint8'),8)
        ids=np.unique(cc[0 if y0==0 else -1]);ids=ids[ids!=0]
        if not len(ids):continue
        connected=np.isin(cc,ids)
        alpha=np.clip((21-sat)/15,0,1)*connected
        alpha=cv2.GaussianBlur(alpha,(0,0),.7*w/540)[:,:,None]
        base=np.array([57,28,30]) if y0==0 else np.array([83,50,41])
        patch=base[None,None,:]+(lum[:,:,None]-145)*.33
        arr[y0:y1]=np.uint8(np.clip(roi*(1-alpha)+patch*alpha,0,255))
    return Image.fromarray(arr)

class Program:
    def __init__(self,variant):
        self.base=CACHE/variant
        self.reveal=CACHE/(variant+'_reveal')
        self.scale=1 if variant=='draft' else 2
        self.ext='jpg' if variant=='draft' else 'png'
        self.anchors=json.loads((CACHE/'anchors.json').read_text())
        self.w,self.h=540*self.scale,960*self.scale
        self.x=np.arange(self.w,dtype='float32')[None,:]/self.w
        self.y=np.arange(self.h,dtype='float32')[:,None]/self.h
        self.surface=None

    def read(self,folder,f):
        with Image.open(folder/f'{f:04}.{self.ext}') as im:
            if im.size!=(self.w,self.h):raise ValueError((f,im.size))
            return im.convert('RGB')

    def picture(self,f):
        plate=self.read(self.base,f)
        if 862<=f<=874:
            alternate=self.read(self.reveal,f)
            if f in (867,868):
                a=np.asarray(plate.resize((54,96)),dtype=np.int16)
                b=np.asarray(alternate.resize((54,96)),dtype=np.int16)
                if np.mean(np.abs(a-b))<1:
                    raise ValueError(f'Section and exterior render identically at {f}')
            exterior,section=(alternate,plate) if f<868 else (plate,alternate)
            progress=(f-862)/12;progress=progress*progress*(3-2*progress)
            sweep=1.55*progress-.23-self.x-.10*(self.y-.5)
            weight=np.uint8(np.clip(sweep/.20+.5,0,1)*255)
            plate=Image.composite(exterior,section,Image.fromarray(weight))
        return border(plate,f)

    def foreground(self,f,im):
        if not 909<=f<=920:return im
        if self.surface is None:
            # Enlarge a strip of the original rim with macro defocus for the foreground occluder.
            hero=self.read(self.base,0)
            sx=self.scale
            src=hero.crop(tuple(round(v*sx) for v in (124,390,186,729)))
            src=src.resize((self.w*3,self.h),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(15*sx))
            rgb=np.asarray(src)
            self.surface=Image.fromarray(np.uint8(np.clip(rgb*[.35,.26,.24]+[18,10,11],0,255)))
        v=(f-909)/11
        # Broad enough to occlude every scanline before the camera changes at frame 915.
        left=1.19-3.51*v;right=left+1.95
        curve=.075*(self.y-.45)+.055*np.sin(math.pi*(self.y-.15))
        xx=self.x+curve
        alpha=np.minimum(np.clip((xx-left)/.095,0,1),np.clip((right-xx)/.095,0,1))
        shift=round((1-v)*self.w*1.6)
        foreground=self.surface.crop((shift,0,shift+self.w,self.h))
        return Image.composite(foreground,im,Image.fromarray(np.uint8(255*alpha)))

    def frame(self,f):
        plate=self.picture(f)
        i=bisect.bisect_right(STARTS,f)-1
        enter=8 if i in (0,len(CUES)-1) else min(8,f-STARTS[i])
        stop=STARTS[i+1] if i+1<len(CUES) else N
        leave=8 if i>=len(CUES)-2 else min(8,stop-f)
        top=header(i,enter,leave,self.scale)
        plate.paste(top,(0,0),top)
        anchor=self.anchors.get(str(f))
        if anchor:
            x,y=anchor['x'],anchor['y']
            if not 4<x<536 or not 8<y<952:raise ValueError((f,anchor))
            label=Image.new('RGBA',plate.size)
            STYLE.callout(label,anchor)
            plate.paste(label,(0,0),label)
        return self.foreground(f,plate)

def assemble(variant):
    program=Program(variant)
    name='rootcanal_draft1' if variant=='draft' else 'rootcanal_final'
    writing=CACHE/(name+'.writing.mp4')
    audio=CACHE/'rootcanal-audio.m4a'
    cmd=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{program.w}x{program.h}','-framerate',str(FPS),'-i','-','-i',str(audio),'-map','0:v','-map','1:a','-vf','scale=out_color_matrix=bt709:out_range=tv,setsar=1,format=yuv420p','-c:v','libx264','-crf','17' if variant=='draft' else '15','-preset','fast','-threads','4','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv','-c:a','copy','-movflags','+faststart',str(writing)]
    with subprocess.Popen(cmd,stdin=subprocess.PIPE) as proc:
        try:
            for f in range(N):proc.stdin.write(program.frame(f).tobytes())
        finally:proc.stdin.close()
        if proc.wait():raise RuntimeError('FFmpeg encoding failed')
    writing.replace(EP/(name+'.mp4'))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('variant',choices=['draft','final']);a.add_argument('--stills',type=int,nargs='+')
    args=a.parse_args()
    if args.stills:
        program=Program(args.variant)
        for f in args.stills:program.frame(f).save(CACHE/f'comp-{args.variant}-{f:04}.jpg',quality=96)
    else:assemble(args.variant)
