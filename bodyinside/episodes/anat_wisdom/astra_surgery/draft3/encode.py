"""Burn editable captions onto the retained clean frames, preserving the chosen audio."""
import argparse
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
EPISODE = HERE.parent.parent
FONTS = EPISODE.parents[1]/'branding/_src/public/fonts'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--captions', type=Path, default=HERE/'captions.ko.ass')
parser.add_argument('--audio', type=Path, default=EPISODE/'astra_surgery_draft2.mp4')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
codec = subprocess.check_output(['ffprobe','-v','error','-select_streams','a:0',
    '-show_entries','stream=codec_name','-of','default=nw=1:nk=1',str(args.audio)],text=True).strip()
encode_audio = ['-c:a','copy'] if codec=='aac' else ['-c:a','aac','-b:a','192k']
caption_filter = f'ass={args.captions.resolve()}:fontsdir={FONTS}'
subprocess.run(['nice','-n','15','ffmpeg','-v','error','-xerror','-y','-framerate','20',
    '-start_number','1','-i',str(HERE/'renders/f_%04d.png'),'-i',str(args.audio),'-map','0:v:0','-map','1:a:0',
    '-vf',caption_filter+',scale=out_color_matrix=bt709:out_range=tv,setsar=1,format=yuv420p',
    '-c:v','libx264','-preset','medium','-crf','17','-maxrate','4100k','-bufsize','3100k',
    '-color_primaries','bt709','-colorspace','bt709','-color_trc','bt709',
    *encode_audio,'-movflags','+faststart',str(args.output)],check=True)
