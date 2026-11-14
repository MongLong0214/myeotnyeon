"""Combine the v3 video with the untouched original AAC stream."""
from pathlib import Path
import subprocess

W=Path('/Users/isaac/projects/verdict-kr/work')
D=Path(__file__).resolve().parents[1]
subprocess.run([
    'ffmpeg','-v','error','-y','-i',str(D/'render/video_muted.mp4'),
    '-i',str(W/'upload/v52_q013_n16_unslop.mp4'),
    '-map','0:v:0','-map','1:a:0','-c','copy',
    '-video_track_timescale','90000','-movflags','+faststart',
    str(W/'upload/v52_q013_n16_v3.mp4'),
],check=True)
