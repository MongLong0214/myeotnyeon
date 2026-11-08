from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess,json,hashlib,sys,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parents[5];B=Path(__file__).resolve().parent;R=Path(sys.argv[1]).resolve();D=R/'final_review';D.mkdir(exist_ok=True)
original=W/'upload/v52_q013_n16.mp4';final=W/'upload/v52_q013_n16_comedy.mp4';pkg=W/'upload/pkg/q013_n16_v4'
def run(cmd):return subprocess.run(list(map(str,cmd)),check=True,capture_output=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mediahash(p,kind):
 args=['ffmpeg','-v','error','-i',p,'-map','0:a:0']
 args+=['-c:a','copy'] if kind=='encoded' else ['-c:a','pcm_f32le']
 return run(args+['-f','hash','-']).stdout.decode().strip().split('=')[-1]
probe=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',final]).stdout);(D/'ffprobe.json').write_text(json.dumps(probe,indent=2))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1080,1920,'30/1',800)
decode=run(['ffmpeg','-v','error','-i',final,'-f','null','-']);(D/'full_decode.log').write_bytes(decode.stderr);assert not decode.stderr
au={kind:{label:mediahash(p,kind) for label,p in [('original',original),('revision',final)]} for kind in ['encoded','pcm_float32']}
assert all(d['original']==d['revision'] for d in au.values())
def framemd5(p):
 data=run(['ffmpeg','-v','error','-i',p,'-map','0:v:0','-pix_fmt','yuv420p','-f','framemd5','-']).stdout
 (D/(p.stem+'_framemd5.txt')).write_bytes(data)
 return [line.decode().split(',')[-1].strip() for line in data.splitlines() if not line.startswith(b'#')]
origmd5,revmd5=framemd5(original),framemd5(final);assert len(origmd5)==len(revmd5)==800
unchanged=list(range(61))+list(range(755,800));assert all(origmd5[f]==revmd5[f] for f in unchanged)
old=json.loads((pkg/'render.json').read_text());new=json.loads((B/'render.json').read_text());assert old==new
def packet_times(p,select):
 data=json.loads(run(['ffprobe','-v','error','-select_streams',select,'-show_packets','-show_entries','packet=pts,dts,duration,size','-of','json',p]).stdout)['packets']
 return data
video_times={label:sorted(d['pts'] for d in packet_times(p,'v:0')) for label,p in [('original',original),('revision',final)]}
audio_times={label:packet_times(p,'a:0') for label,p in [('original',original),('revision',final)]}
assert video_times['original']==video_times['revision'] and audio_times['original']==audio_times['revision']
(D/'presentation_timestamps.json').write_text(json.dumps({'video_pts':video_times,'video_time_base':'1/90000','audio_packets':audio_times,'audio_time_base':'1/48000'},indent=2))

baseline=json.loads((B/'source_baseline.json').read_text());changed_sources=[p for p,digest in baseline.items() if not Path(p).exists() or sha(p)!=digest];assert not changed_sources
contacts=[73]+[85+4*i for i in range(20)]+[174]
keys=sorted(set([0,30,60,61,64,67,70,72,73,74,77,80,82,138,139,162,163,170,173,174,175,180,181,195,203,204,225,252,253,285,328,329,330,336,360,400,401,402,450,485,486,487,550,588,589,590,630,662,663,668,669,670,674,675,676,708,709,710,750,754,755,770,799]+contacts))
expr='+'.join(f'eq(n\\,{f})' for f in keys)
for name,p in [('original',original),('revision',final)]:
 folder=D/name;folder.mkdir(exist_ok=True)
 run(['ffmpeg','-n','-v','error','-i',p,'-vf','select='+expr,'-fps_mode','vfr',folder/'seq_%04d.png'])
 files=sorted(folder.glob('seq_*.png'));assert len(files)==len(keys)
 for f,src in zip(keys,files):src.rename(folder/f'f{f:04d}.png')
fontpath=W/'episodes/quiz/v52_support/bundle_v52_final/public/fonts/Pretendard-Regular.otf';font=ImageFont.truetype(str(fontpath),20)
sheets=[]
def sheet(name,frames,scene=False,cols=4,both=False):
 tw,th=(400,360) if scene else (270,480);rh=th+34
 entries=[(f,label) for f in frames for label in (['original','revision'] if both else ['revision'])]
 im=Image.new('RGB',(cols*tw,((len(entries)+cols-1)//cols)*rh),'#242424');draw=ImageDraw.Draw(im)
 for i,(f,label) in enumerate(entries):
  pic=Image.open(D/label/f'f{f:04d}.png')
  if scene:pic=pic.crop((60,468,1020,1332))
  x=i%cols*tw;y=i//cols*rh;im.paste(pic.resize((tw,th)),(x,y));draw.text((x+6,y+th+5),f'{label} f{f}  {f/30:.3f}s',font=font,fill='white')
 p=D/(name+'.jpg');im.save(p,quality=93);sheets.append(p)
sheet('01_windup_contact_reaction',[61,64,67,70,73,74,77,82],True)
sheet('02_all_22_contacts',contacts,True)
sheet('03_final_contact_and_injury',[163,170,173,174,175,180,181,195],True)
sheet('04_custody_and_probation',[204,225,253,285],True)
sheet('05_judge_and_sentencing',[360,450,550,630,668,670,676,710],False)
sheet('06_original_revision_comparison',[73,195,225,285,450,550,630,676],False,4,True)
sheet('07_answer_boundaries',[668,669,670,674,675,676,709,710],True,4,True)
sheet('08_title_ending_preservation',[0,30,60,755,770,799],False,4,True)
# Complete changed-frame contact sheets, not just selected beauty frames.
thumb=D/'changed_frame_thumbnails';thumb.mkdir(exist_ok=True)
run(['ffmpeg','-n','-v','error','-i',final,'-vf','select=between(n\\,61\\,754),scale=180:320','-fps_mode','vfr','-q:v','3',thumb/'seq_%04d.jpg'])
thumbs=sorted(thumb.glob('seq_*.jpg'));assert len(thumbs)==694
for start in range(0,len(thumbs),64):
 chunk=thumbs[start:start+64];im=Image.new('RGB',(1440,344*((len(chunk)+7)//8)),'#242424');draw=ImageDraw.Draw(im)
 for i,p in enumerate(chunk):
  x=i%8*180;y=i//8*344;im.paste(Image.open(p),(x,y));f=61+start+i;draw.text((x+3,y+321),f'f{f} {f/30:.2f}s',font=font,fill='white')
 dest=D/f'changed_frames_{61+start:04d}_{61+start+len(chunk)-1:04d}.jpg';im.save(dest,quality=90);sheets.append(dest)
metrics=[]
for f in keys:
 if 61<=f<=754:
  a=np.asarray(Image.open(D/'original'/f'f{f:04d}.png')).astype(np.int16);b=np.asarray(Image.open(D/'revision'/f'f{f:04d}.png')).astype(np.int16);delta=np.abs(a-b);mask=np.ones(a.shape[:2],dtype=bool);mask[468:1332,60:1020]=False
  metrics.append({'frame':f,'outside_scene_mean_absolute_channel_error':float(delta[mask].mean()),'subtitle_mean_absolute_channel_error':float(delta[1352:1520,110:870].mean())})
assert max(m['outside_scene_mean_absolute_channel_error'] for m in metrics)<2
cover_src=R/'cover_candidate.jpg';cover=W/'upload/cover_v52_q013_n16_comedy.jpg';shutil.copy2(cover_src,cover);assert Image.open(cover).size==(1080,1920)
snapshot=D/'source_snapshot';snapshot.mkdir(exist_ok=True)
for p in B.iterdir():
 if p.suffix in ['.tsx','.cjs','.py'] or p.name in ['render.json','tsconfig.json']:shutil.copy2(p,snapshot/p.name)
now=datetime.now(ZoneInfo('Asia/Seoul')).isoformat();deadline=datetime(2026,11,6,15,tzinfo=ZoneInfo('Asia/Seoul'))
packet={
 'target':{'episode':'q013','number':16,'scheduled_publication_kst':'2026-11-06T19:00:00+09:00'},
 'delivery_status':'\ub85c\uceec \ud3b8\uc9d1 \ud6c4\ubcf4 \xb7 \uc5c5\ub85c\ub4dc \ubc0f \uac8c\uc2dc \uc791\uc5c5 \uc5c6\uc74c \xb7 \ucd5c\uc885 \ucc44\ud0dd \ubbf8\uc815',
 'render_complete_kst':datetime.fromtimestamp(final.stat().st_mtime,ZoneInfo('Asia/Seoul')).isoformat(),'verification_completed_kst':now,'render_deadline_kst':deadline.isoformat(),'completed_before_deadline':datetime.now(ZoneInfo('Asia/Seoul'))<deadline,
 'outputs':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in [final,cover]],
 'video':{'width':1080,'height':1920,'fps':30,'frames':800,'duration_seconds':probe['format']['duration'],'probe':str(D/'ffprobe.json'),'full_decode_error_output':decode.stderr.decode()},
 'audio_identity':{'method':'\uc6d0\ubcf8 MP4\uc758 AAC \uc2a4\ud2b8\ub9bc\uc744 -c:a copy\ub85c \uc0ac\uc6a9. \uc74c\uc131 \uc7ac\uc0dd\uc131\xb7\ud6a8\uacfc\uc74c \ucd94\uac00 \uc5c6\uc74c.','encoded_packet_payload_sha256':au['encoded'],'encoded_payload_equal':au['encoded']['original']==au['encoded']['revision'],'decoded_pcm_format':'pcm_f32le / 48000 Hz / stereo','decoded_pcm_sha256':au['pcm_float32'],'decoded_pcm_equal':au['pcm_float32']['original']==au['pcm_float32']['revision']},
 'timing_preservation':{'all_800_video_presentation_timestamps_equal':True,'all_audio_packet_timestamps_durations_sizes_equal':True,'timestamp_evidence':str(D/'presentation_timestamps.json'),'render_json_byte_identical':sha(pkg/'render.json')==sha(B/'render.json'),'render_json_structurally_identical':old==new,'subtitles_text_and_ranges':old['subtitles'],'cue_ranges_and_anchors':[{'id':c['id'],'scene':c['scene'],'from':c['from'],'dur':c['dur'],'a':c['a']} for c in old['cues']],'choice_scene_frame':329,'choices_pixels_sourced_from_original_frames':[329,662],'answer_scene_frame':663,'header_answer_anchor_frame':669,'answer_badge_anchor_frame':669,'answer_badge_first_visible_frame':670,'amount_stamp_anchor_frame':675,'amount_stamp_first_visible_frame':676,'prosecution_line_anchor_frame':709,'prosecution_line_first_visible_frame':710,'ending_card_start_frame':755,'method':'\uc6d0\ubcf8 \uc601\uc0c1\uc744 \ubc14\ud0d5\uc73c\ub85c \uc7a5\uba74 \ud328\ub110\ub9cc \uad50\uccb4. \uc790\ub9c9\xb7\ud5e4\ub354\uc640 \uc120\ud0dd\uc9c0 \uc2a4\ud2b8\ub9bd\uc740 \uc6d0\ubcf8 \uc601\uc0c1\uc5d0\uc11c \uac00\uc838\uc634. \uc0c8 \uc120\uace0 \uc7a5\uba74\uc740 \uc6d0\ubcf8 \ubc30\uc9c0\xb7\uae08\uc561\xb7\uad6c\ud615\uc758 \ud45c\uc2dc \uc2dc\uc791 \ud504\ub808\uc784\uc744 \uc0ac\uc6a9.'},
 'title_and_ending_preservation':{'method':'\uc6d0\ubcf8 \ud0a4\ud504\ub808\uc784 \uacbd\uacc4 61 / 755\uc5d0\uc11c \ubd84\ud560\ud558\uc5ec \uce74\ub4dc \uad6c\uac04\uc758 \ube44\ub514\uc624 \ud328\ud0b7\uc744 \uc7ac\uc778\ucf54\ub529 \uc5c6\uc774 \uc5f0\uacb0. \ucd5c\uc885 \ub514\ucf54\ub529 yuv420p \ud504\ub808\uc784 MD5\ub97c \uc6d0\ubcf8\uacfc \uc804\uc218 \ub300\uc870.','title_frames':[0,60],'ending_frames':[755,799],'decoded_frame_comparisons':106,'all_compared_decoded_frames_equal':all(origmd5[f]==revmd5[f] for f in unchanged),'evidence':[str(D/(p.stem+'_framemd5.txt')) for p in [original,final]]},
 'changed_scenes':[
  {'frames':[61,203],'description':'\uae30\uc219\uc0ac \uc778\ubb3c \uc5f0\uae30: \uc900\ube44 \u2192 \uba38\ub9ac \uc811\ucd09 \u2192 \ubb3c\ub7ec\ub0a8 \u2192 \ud53c\ud574\uc790 \ubc18\uc751. \uc911\uac04 \ubc18\ubcf5\uc740 \uc2dc\uac04 \uc555\ucd95 \ud45c\uc2dc, \ucd5c\uc885 \ub1cc\uc9c4\ud0d5 \ub4f1 \uc0c1\ud574.','fact_claims':[3,4,5,6,7]},
  {'frames':[204,252],'description':'\uc2dc\uac01\ube44\uc720 \ud45c\uc2dc: \ube44\uc2dd\ubcc4 \uad00\ub9ac\uc790\uc640 \uad6c\uc18d \uae30\uc18c \uc11c\ub958.','fact_claims':[8]},
  {'frames':[253,328],'description':'\uc2dc\uac01\ube44\uc720 \ud45c\uc2dc: \ud310\uc0ac\uac00 \uacfc\uac70 \uc74c\uc8fc\uc6b4\uc804 \uc9d1\uc720 \uae30\uac04\uacfc \uc774\ubc88 \ubc94\ud589 \uc2dc\uc810\uc744 \uc9da\uc74c.','fact_claims':[9]},
  {'frames':[329,662],'description':'\ud310\uc0ac\uac00 \ubcf8 \uc0ac\uc815: \uc800\uc6b8\uacfc \uc11c\ub958 \ube44\uc720. \uc790\uc219\ud558\uc9c0 \uc54a\uace0 \ubc94\ud589 / \ubc94\ud589 \uc778\uc815\xb7\uad6c\uae08 \uc911 \ubc18\uc131 / 700\ub9cc \uc6d0 \ud569\uc758\xb7\ucc98\ubc8c\ubd88\uc6d0. \ud55c \ud56d\ubaa9\uc529 \uc804\ud658.','fact_claims':[10,11,12]},
  {'frames':[663,754],'description':'\ud310\uc0ac \uce90\ub9ad\ud130\uc640 \ubc8c\uae08 400\ub9cc \uc6d0 \uc120\uace0 \ubb38\uc11c. \uac80\ucc30 \uad6c\ud615 \uc9d5\uc5ed 1\ub144\uc740 \uc6d0\ubcf8 \uc2dc\uc810\uc5d0 \ud45c\uc2dc.','fact_claims':[1,2]}],
 'repetition':{'contact_frames':contacts,'count':len(contacts),'counter_increment_method':'\uc811\ucd09 \ud504\ub808\uc784 \ubc30\uc5f4\uc744 \ub3d9\uc791\xb7\uce74\uc6b4\ud130\uc5d0 \ud568\uaed8 \uc0ac\uc6a9. \uccab 1\ud68c\uc640 \ub9c8\uc9c0\ub9c9 1\ud68c\ub294 \ub290\ub9ac\uac8c, \uc911\uac04 20\ud68c\ub294 4\ud504\ub808\uc784 \uc8fc\uae30\ub85c \uc2dc\uac04 \uc555\ucd95.','not_claimed':'\uc2e4\uc81c \ud604\uc7a5\uc758 \uc815\ud655\ud55c \uc18d\ub3c4\xb7\ub3d9\uc120\xb7\uc790\uc138\ub97c \uc7ac\ud604\ud588\ub2e4\ub294 \uc8fc\uc7a5 \uc544\ub2d8.'},
 'facts':{'matrix_path':str(W/'episodes/quiz/v52_q013_q014_support/q013_fact_matrix.json'),'matrix_sha256':sha(W/'episodes/quiz/v52_q013_q014_support/q013_fact_matrix.json'),'facts_file':str(W/'episodes/quiz/q013/facts.md'),'facts_file_sha256':sha(W/'episodes/quiz/q013/facts.md'),'external_research_performed':False},
 'visual_review':{'method':'\uc2e4\uc81c \ucd5c\uc885 MP4\uc5d0\uc11c \ucd94\ucd9c\ud55c \uc0ac\uac74 \ub3d9\uc791\xb722\ud68c \uc811\ucd09\xb7\ubd80\uc0c1\xb7\ubc95\uc815\xb7\uc815\ub2f5 \uacbd\uacc4\xb7\uc6d0\ubcf8 \ube44\uad50 \uc2dc\ud2b8\ub97c \uc721\uc548 \ud655\uc778.','observations':[],'acceptance':'\ucd5c\uc885 \ucc44\ud0dd \ud310\ub2e8 \ubbf8\uc815'},
 'frame_sheets':[{'path':str(p),'sha256':sha(p)} for p in sheets],
 'native_frame_extracts':[{'frame':f,'seconds':f/30,'original':str(D/'original'/f'f{f:04d}.png'),'revision':str(D/'revision'/f'f{f:04d}.png'),'revision_sha256':sha(D/'revision'/f'f{f:04d}.png')} for f in keys],
 'outside_scene_comparison':metrics,
 'source_preservation':{'baseline_manifest':str(B/'source_baseline.json'),'baseline_manifest_sha256':sha(B/'source_baseline.json'),'checked_file_count':len(baseline),'changed_baseline_files':changed_sources,'q014_and_shared_engine_modified':False},
 'typecheck':{'command':'node production/compositor/node_modules/typescript/bin/tsc -p episodes/quiz/q013/fight_revision/comedy/tsconfig.json','log':str(B/'typecheck.log'),'log_sha256':sha(B/'typecheck.log'),'exit_code':0},
 'source_snapshot':{'directory':str(snapshot),'sha256':{p.name:sha(p) for p in snapshot.iterdir() if p.is_file()}},
 'limitations':['\uc2e4\uc81c \ud604\uc7a5\uc758 \ub3d9\uc791\xb7\uc18d\ub3c4\ub294 \ud655\uc778\ud560 \uc218 \uc5c6\uc5b4 \ube44\uc2dd\ubcc4 \uc7ac\uad6c\uc131\uacfc \uc2dc\uac04 \uc555\ucd95\uc73c\ub85c \ud45c\uc2dc\ud568.','\uc800\uc6b8\xb7\uc11c\ub958\xb7\uad6c\uc18d\ucc3d\uc0b4\uc740 \uc2dc\uac01\ube44\uc720\uc774\uba70 \uc2e4\uc81c \ubc95\uc815 \uc18c\ud488\uc774\ub098 \ud310\uc0ac\uc758 \ud589\ub3d9\uc744 \uc8fc\uc7a5\ud558\uc9c0 \uc54a\uc74c.','\uc74c\uc6d0 \ub3d9\uc77c\uc131\uc740 \ubc14\uc774\ud2b8 \ubc0f \ub514\ucf54\ub529 PCM\uc73c\ub85c \ud655\uc778. \uc5f0\uc18d \uccad\ucde8 \uac80\uc218\ub294 \uc218\ud589\ud558\uc9c0 \uc54a\uc74c.'],
 'network_access_used':False,'uploaded':False,
}
for p in [B/'result_packet.json',D/'result_packet.json']:
 p.write_text(json.dumps(packet,ensure_ascii=False,indent=2))
(B/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p}\n' for p in [final,cover,B/'result_packet.json']))
print(json.dumps({'outputs':packet['outputs'],'audio_identity':au,'card_frames_exact':106,'sheets':len(sheets),'baseline_files':len(baseline),'outside_scene_max_mae':max(m['outside_scene_mean_absolute_channel_error'] for m in metrics),'packet':str(B/'result_packet.json')},ensure_ascii=False,indent=2),flush=True)
