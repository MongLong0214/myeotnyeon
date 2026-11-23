"""Burn the reusable kit graphics over verified picture and copy the approved AAC."""
import subprocess
import sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
WORK=EP.parents[1]
sys.path[:0]=[str(HERE.parent/'draft4'),str(WORK/'anat_kit/layout')]
from edit import FPS, FRAMES
from operative_captions import CaptionTrack

def compose(f,track):
    overlay=track.frame(f)
    box=overlay.getbbox()
    if box[0]<8 or box[1]<90 or box[2]>532 or box[3]>750:raise ValueError((f,box))
    with Image.open(HERE/'renders'/f'f_{f:04d}.png') as base:
        return Image.alpha_composite(base.convert('RGBA'),overlay).convert('RGB')

def main():
    track=CaptionTrack.from_files(HERE/'captions.json',HERE/'label_tracks.json',FPS,FRAMES)
    out=EP/'astra_surgery_draft5.mp4'
    temp=out.with_suffix('.partial.mp4')
    args=['nice','-n','15','ffmpeg','-nostdin','-v','error','-xerror','-y',
          '-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-framerate',str(FPS),'-i','pipe:0',
          '-i',str(HERE.parent/'draft4/earshot_master.m4a'),'-map','0:v','-map','1:a:0',
          '-vf','scale=out_color_matrix=bt709:out_range=tv,setsar=1,format=yuv420p',
          '-c:v','libx264','-preset','medium','-crf','17.5','-maxrate','3320k','-bufsize','4900k',
          '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-c:a','copy',
          '-movflags','+faststart',str(temp)]
    with subprocess.Popen(args,stdin=subprocess.PIPE) as proc:
        for f in range(1,FRAMES+1):proc.stdin.write(compose(f,track).tobytes())
        proc.stdin.close()
        if proc.wait():raise RuntimeError('ffmpeg encode failed')
    if temp.stat().st_size>=25_000_000:raise ValueError('MP4 exceeds 25 MB')
    temp.replace(out)
if __name__=='__main__':main()
