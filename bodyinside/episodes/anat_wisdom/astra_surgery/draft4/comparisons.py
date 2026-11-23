"""Make shot comparisons at source-equivalent times in the two finished MP4s."""
import io
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont
from edit import at,FPS
from finish import FONTS,ROOT,FINAL,HERE

OUT=HERE/'comparisons'
BEFORE=ROOT/'surgery_draft3_sfx.mp4'
FONT=FONTS/'Pretendard-Bold.otf'
CASES=[
    ('오프닝 · 갈라지는 치관',1.90,1.55),
    ('국소 마취',5.70,None),
    ('잇몸 절개',8.85,None),
    ('치조골 삭제',14.80,None),
    ('흡입하는 순간',17.30,None),
    ('치아에 홈 내기',20.55,None),
    ('뿌리 꺼내기',30.10,None),
    ('발치와에 고이는 피',37.05,None),
    ('봉합사 자르기',47.70,None),
    ('거즈 위의 치아 조각',52.25,43.50),
]

def still(path,t):
    data=subprocess.check_output(['nice','-n','15','ffmpeg','-nostdin','-v','error','-ss',f'{t:.3f}','-i',str(path),
                                  '-map','0:v:0','-frames:v','1','-f','image2pipe','-c:v','png','-'])
    return Image.open(io.BytesIO(data)).convert('RGB')

def font(size):return ImageFont.truetype(str(FONT),size)
def timestamp(t):return f'{int(t//60):02}:{t%60:05.2f}'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    thumb_w=192;gap=8;tw=2*thumb_w+gap;th=423
    overview=Image.new('RGB',(2*tw+3*24,5*th+110),(240,237,233))
    board=ImageDraw.Draw(overview);board.text((24,25),'매복 사랑니 발치  /  장면 비교',font=font(37),fill='#221c20')
    board.text((overview.width-24,38),'왼쪽  초안 3     /     오른쪽  초안 4',anchor='ra',font=font(19),fill='#544a4e')
    for i,(label,out_t,reference) in enumerate(CASES):
        shot,src=at(out_t);old_t=round(src*FPS)/FPS if reference is None else reference
        before=still(BEFORE,old_t);after=still(FINAL,out_t)
        if before.size!=(540,960) or after.size!=(540,960):raise ValueError('Comparison dimensions')
        pair=Image.new('RGB',(1152,1104),(240,237,233))
        d=ImageDraw.Draw(pair);d.text((24,18),label,font=font(37),fill='#221c20')
        labels=('초안 3','초안 4') if i!=9 else ('초안 3 · 마지막 장면','초안 4 · 새 장면')
        for x,im,ver,tm in [(24,before,labels[0],old_t),(588,after,labels[1],out_t)]:
            d.text((x,80),ver,font=font(22),fill='#544a4e')
            d.text((x+540,80),timestamp(tm),font=font(21),fill='#544a4e',anchor='ra')
            pair.paste(im,(x,116))
        pair.save(OUT/f'{i+1:02d}_{shot}.png',compress_level=4)
        x=24+(i%2)*(tw+24);y=100+(i//2)*th
        board.text((x,y),label,font=font(24),fill='#2f292b')
        for k,(im,tm) in enumerate(((before,old_t),(after,out_t))):
            xx=x+k*(thumb_w+gap);overview.paste(im.resize((thumb_w,341),Image.Resampling.LANCZOS),(xx,y+35))
            board.text((xx,y+382),timestamp(tm),font=font(15),fill='#66575d')
    overview.save(OUT/'all_shots.jpg',quality=93,subsampling=0)

if __name__=='__main__':main()
