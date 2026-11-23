"""Phone-safe Korean procedural captions, stage markers and tracked anatomical labels.

At the design resolution of 540 × 960, pass a caption with lines and keyword,
an optional (current, total, stage name) and a projected callout {label, side, x, y}.
Call overlay() at the display frame rate with elapsed and remaining cue times.
For an episode, use CaptionTrack.from_files(cues, tracks, fps, frame_count).
Cues are [start_seconds, [line1, line2], highlighted_word, [step,total,name] or null].
Tracks map a one-based frame to {label,side,x,y} at the 540 × 960 design resolution.
The CLI emits this transparent RGBA overlay as rawvideo to stdout for FFmpeg.
"""
import bisect
import json
import math
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S=3
WHITE='#FFF9ED'
AMBER='#FFCA6B'
INK='#21191A'

class OperativeCaptions:
    def __init__(self,bold_font,display_font=None):
        self.bold=str(Path(bold_font))
        self.display=str(Path(display_font or bold_font))

    @lru_cache(maxsize=32)
    def font(self,size,display=False):
        return ImageFont.truetype(self.display if display else self.bold,round(size*S))

    @lru_cache(maxsize=96)
    def title(self,lines,keyword):
        if not 1<=len(lines)<=2 or not keyword or not any(keyword in line for line in lines):
            raise ValueError('Supply one or two caption lines containing the highlighted word')
        # Work in actual ink bounds. Korean glyphs from different typefaces
        # have different ascenders even at the same nominal point size.
        result=Image.new('RGBA',(482*S,137*S))
        draw=ImageDraw.Draw(result)
        y=5*S
        for line in lines:
            size=60 if keyword in line else 53
            font=self.font(size,True)
            while font.getlength(line)>440*S:
                size-=1
                if size<32:raise ValueError(f'Caption needs a shorter line break: {line}')
                font=self.font(size,True)
            parts=line.partition(keyword)
            runs=[(parts[0],WHITE),(parts[1],AMBER),(parts[2],WHITE)] if parts[1] else [(line,WHITE)]
            a,b,c,d=font.getbbox(line)
            x=(result.width-font.getlength(line))/2
            for run,colour in runs:
                if run:
                    draw.text((x,y-b),run,font=font,fill=colour,stroke_width=round(1.7*S),stroke_fill=INK)
                    x+=font.getlength(run)
            y+=d-b+9*S
        box=result.getbbox()
        if box is None:raise ValueError('Empty caption')
        result=result.crop((max(0,box[0]-8*S),0,min(result.width,box[2]+8*S),min(result.height,box[3]+10*S)))
        shade=Image.new('RGBA',result.size)
        shade.putalpha(result.getchannel('A').filter(ImageFilter.GaussianBlur(2.1*S)).point(lambda a:round(.64*a)))
        shadow=Image.new('RGBA',result.size);shadow.alpha_composite(shade,(0,3*S));shadow.alpha_composite(result)
        return shadow

    @lru_cache(maxsize=32)
    def stage(self,number,total,name):
        number_text=f'{number:02d}'
        small=self.font(18);num=self.font(21)
        progress=f'/ {total:02d}'
        w=round(92*S+small.getlength(name));h=35*S
        im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im)
        d.rounded_rectangle((0,0,w-1,h-1),radius=h/2,fill=(30,24,26,226),outline=(255,243,217,155),width=S)
        d.rounded_rectangle((3*S,3*S,40*S,32*S),radius=12*S,fill=AMBER)
        d.text((21*S,17*S),number_text,font=num,fill=INK,anchor='mm')
        d.text((45*S,17*S),progress,font=self.font(14),fill='#EEE2D2',anchor='lm')
        d.line((76*S,10*S,76*S,25*S),fill=(255,255,255,90),width=S)
        d.text((82*S,17*S),name,font=small,fill=WHITE,anchor='lm')
        return im.resize((round(w/S),35),Image.Resampling.LANCZOS)

    def overlay(self,lines,keyword,elapsed,remaining,stage=None,callout=None):
        img=Image.new('RGBA',(540,960))
        title=self.title(tuple(lines),keyword)
        q=min(1,max(0,elapsed/.17))
        ease=1-(1-q)**3
        scale=.93+.07*ease+.012*math.sin(math.pi*q)
        out=min(1,max(0,remaining/.105))
        w,h=round(title.width*scale/S),round(title.height*scale/S)
        tile=title.resize((w,h),Image.Resampling.LANCZOS)
        tile.putalpha(tile.getchannel('A').point(lambda a:round(a*(.48+.52*ease)*(.44+.56*out))))
        title_y=(150 if stage else 146)+round(5*(1-ease))
        img.alpha_composite(tile,((540-w)//2,title_y))
        if stage:
            pill=self.stage(*stage);img.alpha_composite(pill,((540-pill.width)//2,108))
        if callout:
            self.callout(img,callout)
        return img

    def callout(self,img,spec):
        x,y=spec['x'],spec['y']
        label=spec['label'];side=spec['side']
        # Position the plate in the outside lane. The inner line terminates at
        # the projected mesh point, leaving the working end of the tool visible.
        high=Image.new('RGBA',(540*S,960*S));d=ImageDraw.Draw(high)
        font=self.font(19);w=round(font.getlength(label)/S)+22
        left=28 if side=='left' else 485-w
        inner=left+w if side=='left' else left
        if abs(inner-x)<32:
            left=485-w if side=='left' else 28
            inner=left if side=='left' else left+w
        ty=round(max(310,min(696,y-57)))
        sign=1 if x>inner else -1
        pts=[(inner,ty),(inner+16*sign,ty),(x,y)]
        for width,colour in [(3.4,(31,24,23,204)),(1.45,(255,244,215,255))]:
            d.line([(round(a*S),round(b*S)) for a,b in pts],fill=colour,width=round(S*width),joint='curve')
        d.rounded_rectangle((left*S,(ty-16)*S,(left+w)*S,(ty+16)*S),radius=6*S,fill=(34,28,30,233),outline=(248,227,193,218),width=S)
        d.text(((left+w/2)*S,ty*S),label,font=font,anchor='mm',fill=WHITE)
        for r,col in [(4.5,INK),(3,AMBER),(.95,INK)]:
            d.ellipse(((x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S),fill=col)
        overlay=high.resize(img.size,Image.Resampling.LANCZOS)
        opacity=spec.get('opacity',1.)
        if opacity<1:overlay.putalpha(overlay.getchannel('A').point(lambda a:round(a*opacity)))
        img.alpha_composite(overlay)


class CaptionTrack:
    def __init__(self,style,cues,tracks,fps,frame_count):
        self.style=style
        self.cues=cues
        self.tracks=tracks
        self.fps=fps
        self.frame_count=frame_count
        self.starts=[cue[0] for cue in cues]
        if fps<=0 or frame_count<1 or not self.starts or self.starts[0]!=0:
            raise ValueError('A caption track needs positive duration and a first cue at zero')
        if self.starts!=sorted(set(self.starts)) or self.starts[-1]>=frame_count/fps:
            raise ValueError('Cue starts must increase and fall within the picture duration')

    @classmethod
    def from_files(cls,cues,tracks,fps,frame_count,font_dir=None):
        fonts=Path(font_dir) if font_dir else Path(__file__).resolve().parents[2]/'branding/_src/public/fonts'
        style=OperativeCaptions(fonts/'Pretendard-Bold.otf',fonts/'BlackHanSans-Regular.ttf')
        markers=json.loads(Path(tracks).read_text()) if tracks else {}
        return cls(style,json.loads(Path(cues).read_text()),markers,fps,frame_count)

    def frame(self,number):
        if not 1<=number<=self.frame_count:raise IndexError(number)
        t=(number-1)/self.fps
        i=bisect.bisect_right(self.starts,t)-1
        start,lines,word,stage=self.cues[i]
        end=self.starts[i+1] if i+1<len(self.cues) else self.frame_count/self.fps
        return self.style.overlay(lines,word,t-start,end-t,stage,self.tracks.get(str(number)))


if __name__=='__main__':
    import argparse
    import sys
    parser=argparse.ArgumentParser(description='Write 540 × 960 RGBA caption frames to stdout')
    parser.add_argument('cues',type=Path)
    parser.add_argument('--tracks',type=Path)
    parser.add_argument('--fps',type=float,required=True)
    parser.add_argument('--frames',type=int,required=True)
    parser.add_argument('--font-dir',type=Path)
    args=parser.parse_args()
    track=CaptionTrack.from_files(args.cues,args.tracks,args.fps,args.frames,args.font_dir)
    for frame in range(1,args.frames+1):
        sys.stdout.buffer.write(track.frame(frame).tobytes())
