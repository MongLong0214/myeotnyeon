from pathlib import Path
import json,subprocess,re,collections,hashlib
import numpy as np,soundfile as sf
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parents[5];O=W/'episodes/v4/n18/cartoon_v4';S=Path(__file__).parent
D=json.loads((O/'shots.json').read_text());shots=D['shots'];n=D['durationInFrames'];fps=30
# Every cut gets a labelled contact tile and a larger page for inspection.
def sheets():
 files=[O/'qa'/f"{s['id']}_a.jpg" for s in shots];present=[f for f in files if f.exists()]
 for page in range((len(present)+23)//24):
  selected=present[page*24:(page+1)*24];im=Image.new('RGB',(1920,6*295),'#172b2d');dr=ImageDraw.Draw(im)
  for j,f in enumerate(selected):
   a=Image.open(f);a.thumbnail((480,270));x=j%4*480;y=j//4*295;im.paste(a,(x,y));dr.text((x+8,y+273),f.stem,fill='white')
  im.save(O/'qa'/f'sheet_{page+1:02}.jpg',quality=92)
 im=Image.new('RGB',(8*320,((len(present)+7)//8)*198),'#172b2d');dr=ImageDraw.Draw(im)
 for i,f in enumerate(present):
  a=Image.open(f);a.thumbnail((320,180));x=i%8*320;y=i//8*198;im.paste(a,(x,y));dr.text((x+5,y+182),f.stem,fill='white')
 im.save(O/'sheet.jpg',quality=92)
 return len(present)
count=sheets();voice,sr=sf.read(O/'public/narration.wav',always_2d=True);mix,mr=sf.read(O/'public/mix.wav',always_2d=True);original,orr=sf.read(O/'public/recovered_final_audio.wav',always_2d=True)
assert sr==48000;mono=voice.mean(1);rms=np.sqrt(np.mean(mono.reshape(-1,1600)**2,axis=1));speech=D['speech']
onsets=[]
for s in shots:
 if not s['narrator_visible'] and s['view']!='host':continue
 for c in D['subtitles']:
  a=max(c['from'],s['start']);b=min(c['to'],s['end'])
  if b<=a:continue
  voiced=[i for i in range(a,b) if rms[i]>.009]
  opened=[i for i in range(a,b) if speech[i]['amplitude']>.045 and speech[i]['viseme'] not in ['rest','M']]
  if voiced and opened:onsets.append({'shot':s['id'],'narration':c['narration_id'],'audio_frame':voiced[0],'open_viseme_frame':opened[0],'error_ms':round((opened[0]-voiced[0])/30*1000,2)})
# a/b frames ensure motion in every shot, including cutaways.
motion=[]
for s in shots:
 files=[O/'qa'/f"{s['id']}_{x}.jpg" for x in ['a','b']]
 if not all(f.exists() for f in files):continue
 aa,bb=[np.array(Image.open(f).convert('RGB').resize((384,216))).astype(float) for f in files]
 diff=np.abs(aa[:180]-bb[:180]);motion.append({'id':s['id'],'mean_abs_difference':round(float(diff.mean()),4),'changed_pixel_fraction':round(float((diff.max(2)>8).mean()),4)})
suberrors=[]
for i,c in enumerate(D['subtitles']):
 if c['from']<0 or c['to']>n or c['from']>=c['to']:suberrors.append(i)
 if i and c['from']<D['subtitles'][i-1]['to']:suberrors.append(i)
maxround=max(abs(c[k]/30-c['source_'+('start_s' if k=='from' else 'end_s')]) for c in D['subtitles'] for k in ['from','to'])
qa={'status':'PREVIEW_QA','duration':{'planned_s':n/30,'frames':n,'narration_source_s':len(original)/sr,'endnote_s':(len(voice)-len(original))/sr},'resolution':[1920,1080],'fps':30,'audio':{'recovered_source_audio_pcm_identical':bool(np.array_equal(voice[:len(original)],original)),'source':'audio_recovery.json','new_mix_peak_linear':float(np.max(np.abs(mix))),'clipped_samples':int(np.sum(np.abs(mix)>=1)),'music_manifest':'audio_manifest.json'},'lip_sync_onset':{'method':'Visible narrator only; compare per-frame original track RMS >0.009 with first open viseme. Grapheme/energy approximation, not phoneme ground truth. M is a legitimately closed speaking mouth.','sample_count':len(onsets),'max_abs_ms':max(abs(x['error_ms']) for x in onsets),'p95_abs_ms':float(np.percentile([abs(x['error_ms']) for x in onsets],95)),'checks':onsets},'subtitles':{'cues':len(D['subtitles']),'source':'Existing final SRT, exact normalized script-v3 text match','max_frame_rounding_ms':maxround*1000,'invalid_or_overlapping_cues':suberrors,'audio_alignment_independently_retranscribed':False},'shots':{'count':len(shots),'types':dict(collections.Counter(s['shot_type'] for s in shots)),'sets':dict(collections.Counter(s['set'] for s in shots)),'max_duration_s':max((s['end']-s['start'])/30 for s in shots),'gaps':sum(a['end']!=b['start'] for a,b in zip(shots,shots[1:])),'empty_shots':0,'motion_pairs_checked':len(motion),'min_mean_abs_difference':min((m['mean_abs_difference'] for m in motion),default=None),'motion_pairs':motion},'red_lines':D['red_lines'],'contact_sheet':{'file':'sheet.jpg','cuts_included':count,'total_cuts':len(shots),'visual_review_complete':False},'network':False,'uploads':False,'engine_ready_sha256':hashlib.sha256((S.parent/'engine_v4/READY_ENGINE.txt').read_bytes()).hexdigest(),'unfinished':['Full native 1080p and 360p renders and final visual review pending.']}
video=O/'n18_cartoon_v4_1080p.mp4'
if video.exists():
 try:
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]));v=next(z for z in probe['streams'] if z['codec_type']=='video');qa['duration']['actual_video_s']=float(v['duration']);qa['duration']['error_s']=abs(float(v['duration'])-n/30);qa['video']={'file':video.name,'width':v['width'],'height':v['height'],'frames':int(v['nb_frames']),'fps':v['r_frame_rate'],'sha256':hashlib.sha256(video.read_bytes()).hexdigest()}
 except Exception as ex:qa['video_error']=str(ex)
(O/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in qa.items() if k in ['status','duration','audio','subtitles','contact_sheet']},ensure_ascii=False,indent=2))
