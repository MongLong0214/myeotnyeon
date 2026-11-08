"""Asset and final delivery QA. All outputs remain in cartoon_v4."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from collections import Counter
import subprocess,json,hashlib,math,sys
import numpy as np
HERE=Path(__file__).resolve().parent
D=json.loads((HERE/'episode_data.json').read_text())

def contact_sheet(final=False):
 shots=D['shots']; files=[]
 for s in shots:
  fn=HERE/'qa'/f'{s["id"]}_final.jpg' if final else HERE/'qa'/f'{s["id"]}_b.jpg'
  if fn.exists():files.append((s,fn))
 tilew,tileh,cols=320,204,10
 im=Image.new('RGB',(tilew*cols,math.ceil(len(files)/cols)*tileh),'#192631');draw=ImageDraw.Draw(im)
 for i,(s,fn) in enumerate(files):
  x=(i%cols)*tilew;y=(i//cols)*tileh
  im.paste(Image.open(fn).resize((320,180)),(x,y))
  draw.text((x+7,y+183),f'{s["id"]}  {s["start"]/30:.2f}s  {s["type"]}',fill='#f7eed7')
 im.save(HERE/('sheet.jpg' if final else 'preflight_sheet.jpg'),quality=93)
 for page in range(math.ceil(len(files)/32)):
  subset=files[page*32:(page+1)*32];pageim=Image.new('RGB',(1920,math.ceil(len(subset)/4)*294),'#192631');dr=ImageDraw.Draw(pageim)
  for i,(s,fn) in enumerate(subset):
   x=(i%4)*480;y=(i//4)*294
   pageim.paste(Image.open(fn).resize((480,270)),(x,y));dr.text((x+8,y+274),f'{s["id"]}  {s["start"]/30:.2f}s  {s["type"]}',fill='white')
  pageim.save(HERE/'qa'/f'{"final" if final else "preflight"}_page_{page+1:02}.jpg',quality=92)
 return len(files)

def probe(path):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))

def extract():
 video=HERE/'lf2_cartoon_v4_1080p.mp4'
 # A single filter pass emits one actual encoded frame at the middle of every cut.
 points=[]
 for shot in D['shots']:
  for fraction,tag in ((.27,'a_final'),(.5,'final'),(.73,'b_final')):
   points.append((shot['start']+int((shot['end']-shot['start'])*fraction),shot['id'],tag))
 points.sort()
 def balanced(terms):
  if len(terms)==1:return terms[0]
  m=len(terms)//2;return '('+balanced(terms[:m])+'+'+balanced(terms[m:])+')'
 expr=balanced([f'eq(n,{n})' for n,_,_ in points])
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf',f'select={expr.replace(",",chr(92)+",")},scale=960:540','-vsync','vfr','-q:v','2',str(HERE/'qa/encoded_%03d.jpg')],check=True)
 for i,(_,shot_id,tag) in enumerate(points):
  (HERE/'qa'/f'encoded_{i+1:03}.jpg').rename(HERE/'qa'/f'{shot_id}_{tag}.jpg')
 print('final sheet frames',contact_sheet(True))

def qa():
 video=HERE/'lf2_cartoon_v4_1080p.mp4';share=HERE/'lf2_cartoon_v4_360p.mp4'
 main=probe(video);small=probe(share);v=next(s for s in main['streams'] if s['codec_type']=='video');a=next(s for s in main['streams'] if s['codec_type']=='audio')
 frames=D['durationInFrames'];speech=D['speech'];caps=D['captions']
 starts=[math.ceil(c['startMs']/1000*30-1e-7) for c in caps];ends=[math.ceil(c['endMs']/1000*30-1e-7) for c in caps]
 active=np.array([s['amplitude']>.045 for s in speech]);coverage=np.zeros(frames,dtype=bool)
 for st,en in zip(starts,ends):coverage[st:en]=True
 host_actions={'empty','car','mask','dna','cigarette','links','crowd','identity','statement','records','scale','timeline','map'}
 hostmask=np.zeros(frames,dtype=bool)
 for s in D['shots']:
  if s['action'] in host_actions:hostmask[s['start']:s['end']]=True
 onset=np.where(active&~np.r_[False,active[:-1]]&hostmask)[0]
 delay=[]
 for i in onset:
  j=i
  while j<min(i+12,frames) and speech[j]['viseme']=='rest':j+=1
  delay.append((j-i)/30*1000)
 rawvoice=HERE.parent/'audio/voice_full.wav'
 source_same=hashlib.sha256(rawvoice.read_bytes()).hexdigest()==hashlib.sha256((HERE/'public/voice_full.wav').read_bytes()).hexdigest()==D['voiceSha256']
 motion=[]
 for s in D['shots']:
  ap=HERE/'qa'/f'{s["id"]}_a_final.jpg';bp=HERE/'qa'/f'{s["id"]}_b_final.jpg'
  if ap.exists() and bp.exists():
   aa=np.asarray(Image.open(ap).convert('RGB').resize((320,180)),dtype=float)[:154];bb=np.asarray(Image.open(bp).convert('RGB').resize((320,180)),dtype=float)[:154]
   diff=np.abs(aa-bb);motion.append({'shot':s['id'],'mean_absolute_rgb_change':round(float(diff.mean()),4),'changed_pixel_percent':round(float((diff.max(axis=2)>8).mean()*100),3)})
 qa={'delivery':{'main':str(video.relative_to(HERE.parent.parent.parent)),'share':str(share.relative_to(HERE.parent.parent.parent)),'width':v['width'],'height':v['height'],'fps':v['avg_frame_rate'],'frames':int(v['nb_frames']),'narration_s':D['audioDuration'],'video_s':float(v['duration']),'container_s':float(main['format']['duration']),'duration_error_ms':round((float(v['duration'])-D['audioDuration'])*1000,3),'within_one_frame':abs(float(v['duration'])-D['audioDuration'])<=1/30,'share_resolution':[[s for s in small['streams'] if s['codec_type']=='video'][0][k] for k in ('width','height')]},
 'narration':{'source':'audio/voice_full.wav','sha256':D['voiceSha256'],'original_copy_byte_identical':source_same,'speed':1,'added_dialogue':False},
 'shots':{'count':len(D['shots']),'max_duration_s':max((s['end']-s['start'])/30 for s in D['shots']),'over_three_seconds':sum(s['end']-s['start']>90 for s in D['shots']),'types':dict(Counter(s['type'] for s in D['shots'])),'sets':dict(Counter(s['set'] for s in D['shots'])),'purpose_and_fact_refs':'shots.json','two_samples_per_cut':len(motion),'minimum_sample_motion_rgb':min((m['mean_absolute_rgb_change'] for m in motion),default=None),'sample_motion':motion},
 'lip_sync':{'method':D['visemeMethod'],'fallback':'Local spectrum fills audible consonants outside caption intervals. Korean consonants mapped to M/F are approximations; F is supported as an engine shape.','visemes':dict(Counter(s['viseme'] for s in speech)),'presenter_acoustic_onsets_checked':len(delay),'max_frame_gate_onset_error_ms':max(delay,default=0),'frame_resolution_ms':1000/30,'phoneme_alignment_independently_verified':False,'note':'Onset metric checks waveform gate against viseme schedule, not phonetic accuracy. Only host mouths narrate; other generic faces use silent acting.'},
 'subtitles':{'count':len(caps),'source':'shots_v1.json subtitles_full, unchanged text/timing','narration_active_frame_coverage_percent':round(float((coverage&active).sum()/active.sum()*100),3),'max_start_quantization_ms':round(max(st/30*1000-c['startMs'] for st,c in zip(starts,caps)),3),'max_end_quantization_ms':round(max(en/30*1000-c['endMs'] for en,c in zip(ends,caps)),3),'original_timing_verbatim':True,'font':'local Pretendard Bold','max_lines':max(1 if len(c['text'])<=38 else 2 for c in caps),'independent_new_forced_alignment':False},
 'sound':{'bed':'Sneaky Spelunking — Joel Cummins','license':'music_license.md (copied existing local authorization)','ducking':'voice sidechain threshold .008 ratio 8 attack 12ms release 380ms; narration unity gain','sfx_count':0,'sfx_reason':'No licensed SFX in W/assets.','music_muted_s':[[26.458,33.667],[414.75,431.5]]},
 'red_lines':{'external_network':False,'uploads':False,'paid_ai':False,'blender_or_3d':False,'weapons_firing_shown':False,'gunshot_sfx':False,'impact_injury_blood_death_shown':False,'robbers_defendants_identifiable':False,'staff_blank_oval_faces':False,'invented_dialogue':False,'minor_victims_depicted':False,'new_factual_assertions':False,'evidence_cards_are_illustrations':True,'map_is_schematic_no_distances_or_tracking':True,'family_and_court_statements_are_narrator_reports':True,'case_specific_law_not_reinterpreted':True,'on_screen_text':'Narration subtitles and brief reconstruction notices at 0–2 and 8–10 seconds only.'},
 'visual_review':{'contact_sheet':'sheet.jpg','cuts_in_sheet':sum((HERE/'qa'/f'{s["id"]}_final.jpg').exists() for s in D['shots']),'all_cut_pages':'qa/final_page_*.jpg','status':'awaiting final encoded-sheet human-model inspection','fixed':['Head/neck disconnect','Reverse parking ramp and perspective','Silent alarm mouth and stern resolve mouth','Bald judge back-angle anatomy','Medium/high/low camera framing','Removed invented memorial flowers; retained conceptual empty workspace','DNA → B → statement → A evidence-link ordering'],'unresolved':[]},
 'limitations':['Viseme timing is an offline waveform/grapheme approximation, not independently forced-aligned phonemes.','Subtitle timings reuse the verified production timing; no new ASR model or network call was used.']}
 (HERE/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
 print(json.dumps({k:qa[k] for k in ('delivery','subtitles','lip_sync')},ensure_ascii=False))
if __name__=='__main__':
 mode=sys.argv[1] if len(sys.argv)>1 else 'preflight'
 if mode=='extract':extract()
 elif mode=='final':qa()
 else:print('preflight frames',contact_sheet(False))
