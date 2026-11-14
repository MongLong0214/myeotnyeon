import json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path('/Users/isaac/projects/verdict-kr/work');P=R/'production/astra_12min';records=[]
font=ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc',16)
for name,c in json.loads((P/'representatives.json').read_text()).items():
 out=R/'episodes'/c['episode']/'astra_12min';video=out/f'{name}_new_animation_r2.mp4';meta=json.loads((out/f'{name}_cues.json').read_text());dest=out/'review_r2';dest.mkdir(exist_ok=True)
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]));assert any(s['codec_type']=='audio' for s in info['streams']);assert any(s['codec_type']=='video' for s in info['streams'])
 sheet=Image.new('RGB',(1440,295*len(meta['cues'])))
 frame_meta=[]
 for i,cue in enumerate(meta['cues']):
  for j,fraction in enumerate([.1,.5,.9]):
   t=cue['start']+(cue['end']-cue['start'])*fraction;f=dest/f"{cue['id']}_{j}.png"
   subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(f)],check=True)
   im=Image.open(f);im.thumbnail((480,270));sheet.paste(im,(480*j,295*i));d=ImageDraw.Draw(sheet);d.text((480*j+6,295*i+272),f"{cue['id']} · {t:.3f}s · {cue['action']}",font=font,fill='white')
   frame_meta.append(dict(cue=cue['id'],time=t,frame=str(f),text=cue['text']))
 sheet.save(dest/'actual_video_sheet.jpg')
 records.append(dict(video=str(video),sha256=hashlib.sha256(video.read_bytes()).hexdigest(),duration=float(info['format']['duration']),streams=[dict(type=s['codec_type'],codec=s['codec_name']) for s in info['streams']],frames=frame_meta,visual_acceptance='PENDING_ACTUAL_FRAME_REVIEW'))
 (dest/'frames.json').write_text(json.dumps(frame_meta,ensure_ascii=False,indent=2))
(P/'render_verification.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print([(r['video'],r['duration'],len(r['frames'])) for r in records])
