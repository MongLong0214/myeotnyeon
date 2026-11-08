from pathlib import Path
import subprocess,json,hashlib,os
W=Path(__file__).resolve().parents[5];O=W/'episodes/v4/n18/cartoon_v4';main=O/'n18_cartoon_v4_1080p.mp4';patch=O/'qa/C158_patch.mp4';before=O/'qa/pre_c158_fix_1080p.mp4'
if not before.exists():main.rename(before)
filters='[0:v]split=2[before][after];[before]trim=end_frame=10846,setpts=PTS-STARTPTS[p0];[1:v]trim=end_frame=68,setpts=PTS-STARTPTS[p1];[after]trim=start_frame=10914,setpts=PTS-STARTPTS[p2];[p0][p1][p2]concat=n=3:v=1:a=0[v]'
with open(O/'patch_encode.log','w') as log:subprocess.run(['ffmpeg','-hide_banner','-y','-threads','2','-i',str(before),'-threads','2','-i',str(patch),'-filter_complex_threads','1','-filter_complex',filters,'-map','[v]','-map','0:a','-c:v','libx264','-preset','fast','-crf','16','-threads','4','-r','30','-fps_mode','cfr','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(main)],stdout=log,stderr=log,check=True)
def ahash(file):return subprocess.check_output(['ffmpeg','-v','error','-i',str(file),'-map','0:a','-c:a','copy','-f','hash','-hash','sha256','-'],text=True).strip()
a,b=ahash(before),ahash(main);assert a==b
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(main)]));v=next(s for s in probe['streams'] if s['codec_type']=='video');assert int(v['nb_frames'])==13663
(O/'visual_fix.json').write_text(json.dumps({'shot':'C158','reason':'Final encoded contact sheet revealed left-edge narrator face clipping in a close-up. Moved narrator right within the safe area.','replacement_frames':[10846,10913],'replacement_frame_count':68,'replacement_source':'qa/C158_patch.mp4','replacement_render':'Engine v4 at native 1920x1080, 30 fps; full absolute timeline frame numbers retained.','assembly':'Replaced only C158 picture frames, re-encoded native video at CRF16. Original AAC stream copied without re-encoding.','original_audio_stream_hash':a,'fixed_audio_stream_hash':b,'audio_packets_identical':True,'frames':int(v['nb_frames'])},ensure_ascii=False,indent=2))
print('C158 replaced; exact AAC packet hash preserved; 13663 frames.')
subprocess.run(['python3',str(Path(__file__).parent/'finish.py')],env={**os.environ,'N18_FORCE_FINAL_CHECK':'1'},check=True)
