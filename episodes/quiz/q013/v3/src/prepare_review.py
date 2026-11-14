"""Package rendered frames and audio evidence. No review verdicts or uploads."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import subprocess, json, hashlib, math, csv, statistics, re

W=Path('/Users/isaac/projects/verdict-kr/work')
D=W/'episodes/quiz/q013/v3'
R=W/'episodes/review_full/q013_v3'
BASE=W/'upload/v52_q013_n16_unslop.mp4'
OUT=W/'upload/v52_q013_n16_v3.mp4'
R.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args): return subprocess.check_output(args)
def dump(p,data): p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def frame(n): return R/'frames'/f'f{n:04d}.png'
def sheet(ids,path,cols=5,w=216,h=384,lab=25):
    rows=math.ceil(len(ids)/cols)
    im=Image.new('RGB',(cols*w,rows*(h+lab)),'#151B22')
    draw=ImageDraw.Draw(im)
    for i,n in enumerate(ids):
        x=i%cols*w;y=i//cols*(h+lab)
        draw.text((x+5,y+3),f'f{n:03d}  {n/30:06.3f}s',font=small if w<230 else font,fill='#FFFFFF')
        with Image.open(frame(n)) as pic: im.paste(pic.convert('RGB').resize((w,h),Image.Resampling.LANCZOS),(x,y+lab))
    im.save(path)

assert all(frame(n).exists() for n in range(800)), 'Extract final frames first'
ones=list(range(210,721,30))
twelves=[210+round(i*30/12) for i in range(205)]
sheet(ones,R/'q013_v3_7-24_1fps.png',cols=6,w=270,h=480,lab=28)
sheet(twelves,R/'q013_v3_7-24_12fps.png',cols=10,w=180,h=320,lab=24)
for folder,ids in [('12fps_pages',twelves),('30fps_all',list(range(800)))]:
    dest=R/folder;dest.mkdir(exist_ok=True)
    for i in range(0,len(ids),40): sheet(ids[i:i+40],dest/f'page_{i//40+1:02d}.png')
sheet(list(range(0,800,30)),R/'q013_v3_full_1fps.png',cols=6,w=270,h=480,lab=28)

src=(D/'src/CourtDynamic.tsx').read_text()
shots=[{'from':int(a),'to':int(b),'kind':c,'action':d} for a,b,c,d in re.findall(r"\{from:(\d+),to:(\d+),kind:'([^']+)',action:'([^']+)'",src)]
incident_src=(D/'src/FightScene.tsx').read_text()
incident_shots=[{'from':int(a),'to':int(b),'kind':c,'action':d} for a,b,c,d in re.findall(r"\{from:(\d+),to:(\d+),kind:'([^']+)',action:'([^']+)'",incident_src)]
cuts=sorted(set([0]+[s['from'] for s in incident_shots]+[s['from'] for s in shots]+[755]))
all_shots=incident_shots+shots
subs=json.loads((D/'src/render.json').read_text())['subtitles']
asr=json.loads((W/'episodes/quiz/q013/v52/asr_master.json').read_text())
words=[x for s in asr['segments'] for x in s.get('words',[])]
alignment=[]
for i,a in enumerate(cuts):
    b=cuts[i+1] if i+1<len(cuts) else 800
    spoken=[s for s in subs if s['from_']<b and s['to']>a]
    nearest=min([abs(a/30-x[v]) for x in words for v in ['start','end']])
    alignment.append({'from_frame':a,'to_frame_exclusive':b,'start_s':a/30,'duration_s':(b-a)/30,'narration':[s['text'] for s in spoken],
      'action':next((s['action'] for s in all_shots if s['from']==a),'Cold open / next-case subway-arson toon teaser'),
      'nearest_archived_ASR_word_boundary_distance_s':round(nearest,4),'CTO_match':None})
dump(R/'shot_narration_alignment.json',alignment)
transition_ids=[]
for i,a in enumerate(cuts):
    b=cuts[i+1] if i+1<len(cuts) else 800
    transition_ids.extend([max(0,a-1),a,(a+b-1)//2])
dest=R/'transitions';dest.mkdir(exist_ok=True)
for i in range(0,len(transition_ids),12): sheet(transition_ids[i:i+12],dest/f'page_{i//12+1:02d}.png',cols=3,w=270,h=480,lab=28)
dump(R/'frame_manifest.json',{'video':str(OUT),'sha256':sha(OUT),'fps':30,'frames':800,'span_s':[7,24],
  '1fps':ones,'12fps':twelves,'30fps_all':{'start':0,'end_inclusive':799,'pages':20,'every_frame':True},'cut_frames':cuts,
  'sampling_note':'12fps targets are mapped to nearest actual frame of the 30fps output; timestamps identify the decoded source frame.'})

def packets(p):
    return json.loads(run(['ffprobe','-v','error','-select_streams','a:0','-show_packets','-show_entries','packet=pts,dts,duration,size,data_hash,side_data_list','-show_data_hash','sha256','-of','json',str(p)]))['packets']
def audio_hash(p,pcm=False):
    args=['ffmpeg','-v','error','-i',str(p),'-map','0:a:0']
    if pcm: args+=['-c:a','pcm_s16le','-f','s16le','pipe:1']
    else: args+=['-c:a','copy','-f','adts','pipe:1']
    return hashlib.sha256(run(args)).hexdigest()
p0,p1=packets(BASE),packets(OUT)
audio={'base':str(BASE),'output':str(OUT),'method':'ffmpeg video copy + original AAC stream copy; no audio encoding/mix',
 'aac_adts_sha256':{'base':audio_hash(BASE),'v3':audio_hash(OUT)},'decoded_pcm_s16le_sha256':{'base':audio_hash(BASE,True),'v3':audio_hash(OUT,True)},
 'audio_packet_count':{'base':len(p0),'v3':len(p1)},'packet_payloads_and_pts_dts_durations_identical':p0==p1}
audio['encoded_audio_identical']=audio['aac_adts_sha256']['base']==audio['aac_adts_sha256']['v3']
audio['decoded_audio_identical']=audio['decoded_pcm_s16le_sha256']['base']==audio['decoded_pcm_s16le_sha256']['v3']
dump(R/'audio_identity.json',audio)
baseline=json.loads((D/'source_baseline_sha256.json').read_text())
preserve={p:{'before_sha256':h,'after_sha256':sha(W/p),'unchanged':sha(W/p)==h} for p,h in baseline.items()}
dump(R/'original_preservation.json',preserve)
timing={p:{'base_sha256':sha(W/'episodes/quiz/q013/unslop/src'/p),'v3_sha256':sha(D/'src'/p)} for p in ['render.json','captions.json']}
dump(R/'timing_preservation.json',timing)

# Reference shot durations are read from the existing actual-video cut detection CSV.
reference={}
for ref in ['REF01','REF02']:
    rows=list(csv.DictReader((W/'references'/ref/'shots.csv').open()))
    durations=[float(r['dur_s']) for r in rows]
    meta=json.loads((W/'references'/ref/'meta.json').read_text())
    reference[ref]={'title':meta['title'],'url':meta['webpage_url'],'views_at_archived_measurement':meta.get('view_count'),
      'actual_video_cut_source':str(W/'references'/ref/'shots.csv'),'shots':len(rows),'median_cut_duration_s':statistics.median(durations),
      'motion_class_counts':{k:sum(r['motion_class_auto']==k for r in rows) for k in sorted({r['motion_class_auto'] for r in rows})},
      'limits':'Camera/motion and cut duration only. No unmeasured character ratio or OCR text ratio supplied. 3D look is not applied to this toon revision.'}
dump(R/'reference_measured_metrics.json',reference)
compare=Image.new('RGB',(1240,2*535),'#151B22');draw=ImageDraw.Draw(compare)
for i,(refn,ourn) in enumerate([(8,210),(20,673)]):
    y=i*535
    draw.text((15,y+10),f'REF02  {refn:.1f}s  (camera/action comparison only)',font=font,fill='white')
    pic=Image.open(D/'render'/f'ref02_{refn}.png').convert('RGB');pic.thumbnail((700,480))
    compare.paste(pic,(15,y+45+(480-pic.height)//2))
    draw.text((755,y+10),f'q013 v3 f{ourn}',font=font,fill='white')
    with Image.open(frame(ourn)) as pic: compare.paste(pic.convert('RGB').resize((270,480)),(835,y+45))
compare.save(R/'reference_side_by_side.png')
syllables=sum(bool(re.match('[가-힣]',ch)) for ch in asr['text'])
speech_time=sum(w['end']-w['start'] for w in words)
dump(R/'speech_timing.json',{'source':'unchanged original audio; archived word ASR','korean_syllables':syllables,'word_active_seconds':speech_time,'syllables_per_active_second':syllables/speech_time,'whole_video_syllables_per_second':syllables/(800/30),'limits':'Archived ASR has ending-word recognition errors; not a new transcription.'})
subprocess.run(['ffmpeg','-hide_banner','-i',str(OUT),'-map','0:a:0','-af','ebur128=peak=true','-f','null','-'],stdout=subprocess.DEVNULL,stderr=(R/'audio_loudness.log').open('w'),check=True)
probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(OUT)]))
dump(R/'media_probe.json',probe)
print(json.dumps({'output_sha256':sha(OUT),'frames':800,'1fps_frames':len(ones),'12fps_frames':len(twelves),'audio_identity':audio,'originals_unchanged':all(v['unchanged'] for v in preserve.values())},ensure_ascii=False,indent=2))
