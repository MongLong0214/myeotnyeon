from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess,hashlib,json,re,shutil
from PIL import Image,ImageDraw,ImageFont
W=Path('/Users/isaac/projects/verdict-kr/work');D=W/'episodes/quiz/q013/unslop';B=D/'src';S=W/'episodes/quiz/q013/fight_revision/comedy';E=W/'episodes/review_full/unslop/q013';E.mkdir(parents=True,exist_ok=True)
old=B/'v52_q013_n16_comedy.mp4';new=W/'upload/v52_q013_n16_unslop.mp4'
def run(args):return subprocess.run(list(map(str,args)),check=True,capture_output=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ffhash(p,pcm=False):return run(['ffmpeg','-v','error','-i',p,'-map','0:a:0','-c:a','pcm_f32le' if pcm else 'copy','-f','hash','-']).stdout.decode().strip().split('=')[-1]
def probe(p):return json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',p]).stdout)
def packets(p,stream):return json.loads(run(['ffprobe','-v','error','-select_streams',stream,'-show_packets','-show_entries','packet=pts,dts,duration,size,data_hash,side_data_list','-show_data_hash','sha256','-of','json',p]).stdout)['packets']
audio={kind:{'original':ffhash(old,pcm),'unslop':ffhash(new,pcm)} for kind,pcm in [('aac_payload_sha256',False),('pcm_f32le_48000_stereo_sha256',True)]}
audio['aac_packet_payload_equal']=audio['aac_payload_sha256']['original']==audio['aac_payload_sha256']['unslop'];audio['pcm_equal']=audio['pcm_f32le_48000_stereo_sha256']['original']==audio['pcm_f32le_48000_stereo_sha256']['unslop']
a,b=packets(old,'a:0'),packets(new,'a:0');audio['audio_packet_pts_dts_durations_sizes_hashes_and_side_data_equal']=a==b;audio['packet_count']=len(a)
assert audio['aac_packet_payload_equal'] and audio['pcm_equal'] and a==b
(E/'audio_identity.json').write_text(json.dumps(audio,indent=2))
(E/'audio_packets.json').write_text(json.dumps({'original':a,'unslop':b},indent=2))
x,y=probe(old),probe(new);(E/'ffprobe.json').write_text(json.dumps({'original':x,'unslop':y},indent=2))
v=next(s for s in y['streams'] if s['codec_type']=='video');assert (v['width'],v['height'],v['r_frame_rate'],v['nb_frames'])==(1080,1920,'30/1','800')
vx,vy=packets(old,'v:0'),packets(new,'v:0');px=sorted((z['pts'],z['duration']) for z in vx);py=sorted((z['pts'],z['duration']) for z in vy);assert px==py
(E/'video_presentation_timestamps.json').write_text(json.dumps({'original':px,'unslop':py,'time_base':'1/90000'},indent=2))
original=json.loads((S/'render.json').read_text());doc=json.loads((B/'render.json').read_text());assert original==doc
# Inspect computed browser layout, including every visible narration cue and the ending UI.
observed=json.loads((D/'render/subtitle_layout_observed.json').read_text())
expected_from={s['from_'] for s in doc['subtitles'] if max(61,s['from_'])<min(755,s['to'])}|{755}
assert expected_from<={r['from'] for r in observed}
for r in observed:
 assert r['canvas']=={'width':1080,'height':1920}
 assert abs(r['box']['centerX']-540)<.05 and r['textAlign']=='center'
 assert r['box']['y']>=1920*.62 and r['box']['bottom']<=1920*.70
 assert float(r['fontSize'].removesuffix('px'))>=64 and int(r['fontWeight'])>=800
 assert float(r['outline'].removesuffix('px'))>=8 and r['outlineColor']=='rgb(0, 0, 0)' and r['shadow']!='none'
 assert 1<=len(r['lines'])<=2
 assert all(line['characters']<=14 and abs(line['centerX']-540)<.05 for line in r['lines'])
 if r['from']!=755:
  source=next(s for s in doc['subtitles'] if s['from_']==r['from'])
  assert re.sub(r'\s','',''.join(line['text'] for line in r['lines']))==re.sub(r'\s','',source['text'])
legibility={'authority':'Owner correction (2026-11-06), direct instruction takes precedence',
 'measurement':'Browser computed styles and text Range bounds, normalized relative to the 1080x1920 composition',
 'observations':len(observed),'visible_cues_covered':sorted(expected_from),'center_x':540,
 'font_px':72,'css_font_weight':800,'black_outline_px':10,'soft_shadow':'0 3px 4px rgba(0,0,0,.65)',
 'box_y':[1192,1342],'box_percent_y':[1192/1920*100,1342/1920*100],'max_lines':2,
 'max_characters_per_line_including_spaces_and_punctuation':14,'highlight':{'phrase':'벌금 400만 원','color':'#FFD400','original_frames':[668,707]},
 'words_and_authored_timing_unchanged':True,'acceptance':'CTO and CEO review pending'}
(E/'subtitle_legibility.json').write_text(json.dumps(legibility,ensure_ascii=False,indent=2))
shutil.copy2(D/'render/subtitle_layout_observed.json',E/'subtitle_layout_observed.json')
# Check the exact unmodified motion setup and articulated character implementation.
motion={}
for name,fn in [('FightScene.tsx','Reenactment'),('ComedyLogic.tsx','CustodyScene'),('ComedyLogic.tsx','ProbationScene'),('ComedyLogic.tsx','CourtComedy'),('ComedyLogic.tsx','Sentencing')]:
 def setup(p):
  t=p.read_text();start=t.index('export const '+fn+':');return t[start:t.index(' return ',start)]
 o,n=setup(S/name),setup(B/name);motion[fn]={'setup_equal':o==n,'setup_sha256':hashlib.sha256(n.encode()).hexdigest()};assert o==n
for name in ['FightScene.tsx','ComedyLogic.tsx']:
 tags=lambda p:re.findall(r'<ArticulatedGuy\b[^>]+/>',p.read_text())
 assert tags(S/name)==tags(B/name)
motion['FightRig.tsx']={'byte_identical':sha(S/'FightRig.tsx')==sha(B/'FightRig.tsx'),'sha256':sha(B/'FightRig.tsx')};assert motion['FightRig.tsx']['byte_identical']
# Copies of all original working files and original video remain unchanged.
baseline=json.loads((D/'original_sha256.json').read_text());changes=[p for p,h in baseline.items() if sha(W/p)!=h];assert not changes
# Subtitle design breaks normalize to precisely the original narration words.
breaks={286:'집행유예\n기간 중이었어요.',334:'벌금, 집행유예, 실형 중\n무엇이었을까요?',486:'다만 범행을\n모두 인정했고'}
for sub in doc['subtitles']:assert re.sub(r'\s','',breaks.get(sub['from_'],sub['text']))==re.sub(r'\s','',sub['text'])
contacts=[73]+[85+4*i for i in range(20)]+[174]
timing={'video_frames':800,'fps':30,'dimensions':[1080,1920],'duration_seconds':v['duration'],'all_video_presentation_timestamps_and_durations_equal':px==py,'audio_packets_identical':a==b,'render_json_byte_identical':sha(S/'render.json')==sha(B/'render.json'),'all_authored_subtitle_text_and_ranges_unchanged':original['subtitles']==doc['subtitles'],'subtitle_line_break_overrides':breaks,'subtitle_visibility':'Original actual visibility retained: narration subtitles use their original ranges intersected with frames [61,755); hook 0–60 and ending 755–799 use their own UI. The natural ending line replaces the CTA at the same frame 755.','subtitle_ranges':doc['subtitles'],'cue_frames_and_anchors':[{'id':c['id'],'from':c['from'],'dur':c['dur'],'a':c['a']} for c in doc['cues']],'choices':{'start_frame':329,'end_exclusive':663,'spring_starts_local':[0,3,6],'spring_config':{'damping':12,'mass':.5,'stiffness':180}},'answer':{'scene_start':663,'original_header_anchor_669_removed_as_UI':True,'answer_subtitle_start_frame':668,'document_opacity_anchor':675,'document_first_nonzero_opacity':676,'original_prosecution_label_removed_as_duplicate_UI':True,'prosecution_subtitle_start_frame':710},'scene_display_ranges':{'hook':[0,61],'C1':[61,139],'C2':[139,253],'C3':[253,329],'C4':[329,663],'C5':[663,755],'ending':[755,800]},'contact_frames':contacts,'contacts':22,'motion_source_checks':motion,'all_actor_placement_and_pose_props_unchanged_in_scene_coordinates':True,'layout_changes':'Scene viewport enlarged from scale .96 to 1.30, translated to (-110,180); background extended to portrait edges; original bodyScale51 camera clock retained. Text/label graphics removed or restyled; physical document/calendar props keep their movement clocks.','original_files_checked':len(baseline),'changed_original_files':changes,'limitations':['Timing is checked from the unchanged subtitle/cue JSON, unchanged motion formulas, copied actor props and equal final presentation timestamps. This is not a claim of pixel identity after resizing the scene.','The former factor label plates were UI and removed; the judge and scales retain their original animation clocks.'],'acceptance':'Awaiting CTO and CEO review; no self-assigned acceptance.'}
required_information={
 'authority':'CEO Addendum 1; takes precedence over earlier label removal',
 'reconstruction':{'text':'재구성','frames':[0,800],'position':'top-right corner','font_px':36,'boxed':False},
 'time_compression':{'text':'재구성 · 시간 압축','frames':[61,204],'position':'top-right corner','font_px':36,'boxed':False},
 'visual_metaphor':{'text':'재구성 · 시각비유','frames':[204,755],'position':'top-right corner','font_px':36,'boxed':False},
 'headbutts_fact':{'text':'박치기 22회','frames':[61,204],'font_px':64,'boxed':False,'also_visible_in_intro_and_original_narration_subtitle':True},
 'demand_vs_sentence':{'text':'구형 징역 1년 → 선고 벌금 400만 원','lines':['구형 징역 1년','→ 선고 벌금 400만 원'],'frames':[710,800],'font_px':64,'css_font_weight':800,'center_x':540,'boxed':False,'starts_at_unchanged_prosecution_subtitle_frame':True},
 'ranges':'start inclusive, end exclusive; frame 0 based, 30fps',
 'acceptance':'CTO and CEO review pending',
}
timing['ceo_addendum_1_on_screen_information']=required_information
timing['owner_correction_subtitle_legibility']=legibility
(E/'required_on_screen_information.json').write_text(json.dumps(required_information,ensure_ascii=False,indent=2))
(E/'timing_preservation.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2))
# Decode the entire final artifact once; errors raise, stderr is retained.
z=run(['ffmpeg','-v','error','-i',new,'-f','null','-']);(E/'full_decode.log').write_bytes(z.stderr);assert not z.stderr
# Every integer second, same decoded frame index on both sides.
frames=list(range(0,800,30));expr='+'.join(f'eq(n\\,{f})' for f in frames)
for label,p in [('before',old),('after',new)]:
 folder=E/label;folder.mkdir(exist_ok=True)
 run(['ffmpeg','-y','-v','error','-i',p,'-vf','select='+expr,'-fps_mode','vfr',folder/'seq_%03d.png'])
 for f,png in zip(frames,sorted(folder.glob('seq_*.png'))):png.rename(folder/f'f{f:04d}.png')
font=ImageFont.truetype(str(B/'public/fonts/DoHyeon-Regular.ttf'),26)
tw,th=360,640;rw=tw*2;rh=th+42;cols=3;rows=9
sheet=Image.new('RGB',(cols*rw,rows*rh+48),'#222222');draw=ImageDraw.Draw(sheet);draw.text((16,10),'q013 #16 | BEFORE / AFTER | 1 fps | identical timestamps',fill='white',font=font)
for i,f in enumerate(frames):
 ox=i%cols*rw;oy=48+i//cols*rh
 for j,label in enumerate(['before','after']):sheet.paste(Image.open(E/label/f'f{f:04d}.png').resize((tw,th),Image.Resampling.LANCZOS),(ox+j*tw,oy+42))
 draw.text((ox+8,oy+6),f'{f/30:02.0f}s  f{f:03d}  BEFORE',fill='white',font=font);draw.text((ox+tw+8,oy+6),'AFTER',fill='white',font=font)
sheet.save(E/'before_after_1fps.png')
for i in range(3):sheet.crop((0,48+i*3*rh,cols*rw,48+(i+1)*3*rh)).save(E/f'before_after_{i*9:02d}_{i*9+8:02d}s.png')
# Frame-accurate handoffs and contacts, beyond the 1fps overview.
keys=sorted(set([60,61,72,73,74,138,139,173,174,175,180,181,203,204,252,253,328,329,330,400,401,485,486,588,589,662,663,667,668,669,670,674,675,676,708,709,710,752,753,754,755,784,785,799]+contacts))
folder=E/'boundaries';folder.mkdir(exist_ok=True);expr='+'.join(f'eq(n\\,{f})' for f in keys)
run(['ffmpeg','-y','-v','error','-i',new,'-vf','select='+expr,'-fps_mode','vfr',folder/'seq_%03d.png'])
for f,png in zip(keys,sorted(folder.glob('seq_*.png'))):png.rename(folder/f'f{f:04d}.png')
evidence_frames=[61,139,204,253,329,663,710,780]
phone=Image.new('RGB',(1440,1364),'#222222');pd=ImageDraw.Draw(phone)
for i,f in enumerate(evidence_frames):
 src=(folder/f'f{f:04d}.png') if f!=780 else E/'after/f0780.png'
 ox=i%4*360;oy=i//4*682
 pd.text((ox+8,oy+6),f'f{f:03d} / {f/30:.3f}s',fill='white',font=font)
 phone.paste(Image.open(src).resize((360,640),Image.Resampling.LANCZOS),(ox,oy+42))
phone.save(E/'ceo_addendum_1_360p.png')
legibility_frames=[61,300,360,540,669,710,754,780]
phone=Image.new('RGB',(1440,1364),'#222222');pd=ImageDraw.Draw(phone)
for i,f in enumerate(legibility_frames):
 src=(folder/f'f{f:04d}.png') if f in keys else E/'after'/f'f{f:04d}.png'
 ox=i%4*360;oy=i//4*682
 pd.text((ox+8,oy+6),f'f{f:03d} / {f/30:.3f}s',fill='white',font=font)
 phone.paste(Image.open(src).resize((360,640),Image.Resampling.LANCZOS),(ox,oy+42))
phone.save(E/'owner_correction_360p.png')
shutil.copy2(D/'render/cover.png',W/'upload/cover_v52_q013_n16_unslop.png')
print(json.dumps({'audio_identity':audio,'video_frames':800,'source_files_changed':changes,'sheet':str(E/'before_after_1fps.png'),'review_acceptance':'pending'},ensure_ascii=False,indent=2))
