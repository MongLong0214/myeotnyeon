"""Burn the continuous Korean caption band and mux the mastered Earshot soundtrack."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

from PIL import Image,ImageFont
from edit import DURATION,FPS,FRAMES,SHOTS

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
FONTS=ROOT.parents[1]/'branding/_src/public/fonts'
CUES=[
    (0,'사랑니가 ','갈라진다',''),
    (3.20,'먼저 ','국소 마취','를 한다'),
    (6.15,'① 잇몸을 ','절개','한다'),
    (9.85,'잇몸을 ','젖힌다',''),
    (12.50,'② ','뼈','를 갈아낸다'),
    (16.45,'고인 피를 ','흡입','한다'),
    (18.55,'③ 치아에 ','홈','을 낸다'),
    (22.30,'홈을 따라 ','가른다',''),
    (24.70,'','치아 머리','부터 꺼낸다'),
    (27.35,'남은 ','뿌리','를 나눈다'),
    (28.25,'④ ','뿌리','를 하나씩 뽑는다'),
    (34.95,'빈자리에 ','피','가 고인다'),
    (37.35,'','식염수','로 씻어낸다'),
    (40.40,'다시 ','피','가 차오른다'),
    (42.40,'⑤ 잇몸을 ','꿰맨다',''),
    (44.75,'','매듭','을 조인다'),
    (46.96,'남은 ','실 끝','을 자른다'),
    (48.65,'','거즈','에 조각을 놓는다'),
]

SIZE=54
CAPTION=HERE/'captions.ko.ass'
BAND=HERE/'caption_band.png'
FINAL=ROOT/'astra_surgery_draft4.mp4'

def stamp(t):
    h,cs=divmod(round(t*100),360000);m,cs=divmod(cs,6000);s,cs=divmod(cs,100)
    return f'{h}:{m:02}:{s:02}.{cs:02}'

def captions():
    font=ImageFont.truetype(str(FONTS/'Pretendard-Bold.otf'),SIZE)
    # libass includes the typeface's ascender and descender in its font-size convention.
    # The wider Pillow measurement also guards against any player using a taller fallback.
    stops=[c[0] for c in CUES]+[DURATION]
    body=[]
    for i,(_,pre,word,post) in enumerate(CUES):
        if font.getlength(pre+word+post)>511:
            raise ValueError(f'Caption too wide: {pre}{word}{post}')
        text=pre+r'{\1c&H69BEFF&}'+word+r'{\1c&HF8FAFC&}'+post
        body.append(f'Dialogue: 0,{stamp(stops[i])},{stamp(stops[i+1])},Step,,0,0,0,,{text}')
    if any(not any(a<=shot[1][0][0]<b for a,b in zip(stops,stops[1:])) for shot in SHOTS):
        raise ValueError('Uncaptioned cut')
    CAPTION.write_text('''[Script Info]
Title: 매복 사랑니 발치
ScriptType: v4.00+
PlayResX: 540
PlayResY: 960
ScaledBorderAndShadow: yes
WrapStyle: 2
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Step,Pretendard,54,&H00F8FAFC,&H0069BEFF,&H50100C0E,&H8809060B,-1,0,0,0,100,100,0,0,1,0.8,1,2,17,17,81,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''+ '\n'.join(body)+'\n')
    # The band is steady across cuts. Its gradual upper edge leaves the lower surgical field visible.
    band=Image.new('RGBA',(540,230))
    for y in range(230):
        q=min(1,max(0,y/125))
        opacity=round(246*q*q*(3-2*q))
        band.paste((22,16,21,opacity),(0,y,540,y+1))
    band.save(BAND)

def encode():
    frames=Path(os.environ.get('ASTRA4_FRAMES',str(HERE/'renders')))
    absent=[i for i in range(1,FRAMES+1) if not (frames/f'f_{i:04d}.png').exists()]
    if absent:raise RuntimeError(f'Missing {len(absent)} frames beginning at {absent[0]}')
    temp=FINAL.with_name(FINAL.stem+'.partial.mp4')
    with tempfile.TemporaryDirectory(prefix='astra-caption-font-') as fonts_tmp:
        (Path(fonts_tmp)/'Pretendard-Bold.otf').symlink_to(FONTS/'Pretendard-Bold.otf')
        subprocess.run(['nice','-n','15','ffmpeg','-nostdin','-v','warning','-xerror','-y',
            '-framerate',str(FPS),'-start_number','1','-i',str(frames/'f_%04d.png'),
            '-i',str(BAND),'-i',str(HERE/'earshot_master.m4a'),
            '-filter_complex',f'[0:v][1:v]overlay=0:730:format=rgb,ass={CAPTION}:fontsdir={fonts_tmp},scale=out_color_matrix=bt709:out_range=tv,setsar=1,format=yuv420p[v]',
            '-map','[v]','-map','2:a:0','-c:v','libx264','-preset','medium','-crf','17.5','-maxrate','3390k','-bufsize','4800k',
            '-color_primaries','bt709','-colorspace','bt709','-color_trc','bt709','-c:a','copy','-movflags','+faststart',str(temp)],check=True)
    if temp.stat().st_size>=25_000_000:raise RuntimeError('Output exceeds the requested size')
    temp.replace(FINAL)

if __name__=='__main__':
    captions()
    if '--prepare' not in sys.argv:encode()
