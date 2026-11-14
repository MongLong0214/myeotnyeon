from pathlib import Path
import subprocess,json,sys
W=Path(__file__).resolve().parents[5]
R=Path(sys.argv[1]).resolve()
source=W/'upload/v52_q013_n16.mp4'
def run(args):
 print(' '.join(map(str,args)),flush=True)
 return subprocess.run(list(map(str,args)),check=True,capture_output=True)
# The original starts a GOP at frames 61 and 755. Those boundaries permit
# title and ending packets to be copied intact. Only the middle is encoded.
if not (R/'title_original.mp4').exists():run(['ffmpeg','-n','-v','error','-i',source,'-map','0:v:0','-c:v','copy','-frames:v','61','-an','-video_track_timescale','90000',R/'title_original.mp4'])
if not (R/'ending_original.mp4').exists():run(['ffmpeg','-n','-v','error','-ss','25.1666666667','-i',source,'-map','0:v:0','-c:v','copy','-frames:v','45','-an','-video_track_timescale','90000',R/'ending_original.mp4'])
# Retain original header, source footer, captions and choices as the base.
# The 694-frame renderer output supplies only the 960x864 scene panel.
# Put the original choices strip back too; its pixels and animation remain sourced
# from the original throughout the entire choice scene.
filters="[0:v]trim=start_frame=61:end_frame=755,setpts=PTS-STARTPTS,split=2[base][orig];[1:v]crop=960:864:60:468[scene];[base][scene]overlay=60:468:format=yuv420[changed];[orig]crop=960:118:60:468[choices];[changed][choices]overlay=60:468:enable='between(n,268,601)':format=yuv420[out]"
run(['ffmpeg','-n','-v','error','-i',source,'-i',R/'video_muted.mp4','-filter_complex',filters,'-map','[out]','-an','-frames:v','694','-c:v','libx264','-preset','slow','-crf','14','-profile:v','high','-level:v','4.0','-pix_fmt','yuv420p','-r','30','-bf','2','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-video_track_timescale','90000',R/'middle_composited.mp4'])
parts=R/'concat.txt'
parts.write_text(''.join("file '"+str(R/name)+"'\nduration "+format(frames/30,'.12f')+"\n" for name,frames in [('title_original.mp4',61),('middle_composited.mp4',694),('ending_original.mp4',45)]))
run(['ffmpeg','-n','-v','error','-f','concat','-safe','0','-i',parts,'-map','0:v:0','-c:v','copy','-video_track_timescale','90000',R/'video_preserved.mp4'])
run(['ffmpeg','-n','-v','error','-i',R/'video_preserved.mp4','-i',source,'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',W/'upload/v52_q013_n16_comedy.mp4'])
print('ASSEMBLED',W/'upload/v52_q013_n16_comedy.mp4',flush=True)
