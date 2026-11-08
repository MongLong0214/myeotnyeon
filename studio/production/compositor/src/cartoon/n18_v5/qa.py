"""Measure delivered files, narration, cut distribution and contact sheets."""
from pathlib import Path
import json,re,subprocess,math,hashlib,difflib
import numpy as np
from PIL import Image,ImageDraw
import audio as V
E=V.E
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
def run_filter(p,filters):return subprocess.run(['ffmpeg','-hide_banner','-i',str(p),'-vf',filters,'-an','-f','null','-'],capture_output=True,text=True,check=True).stderr
def sheets():
 d=json.loads((E/'episode_data.json').read_text());shots=d['shots'];cols=6;tw=320;th=202
 canvas=Image.new('RGB',(cols*tw,math.ceil(len(shots)/cols)*th),(23,21,37));dr=ImageDraw.Draw(canvas)
 for i,s in enumerate(shots):
  p=E/'qa_frames'/f'{s["id"]}.jpg';pic=Image.open(p).convert('RGB').resize((tw,180));x=i%cols*tw;y=i//cols*th
  canvas.paste(pic,(x,y));dr.text((x+5,y+181),f'{s["id"]} {s["start"]/30:06.2f}s {s["scene"]}',fill='white')
 canvas.save(E/'sheet.jpg',quality=88)
 # Readable pages complement the full every-cut sheet.
 for page in range(math.ceil(len(shots)/24)):
  a=page*24;b=min(len(shots),a+24);im=Image.new('RGB',(1280,math.ceil((b-a)/4)*202),(23,21,37));draw=ImageDraw.Draw(im)
  for j,s in enumerate(shots[a:b]):
   pic=Image.open(E/'qa_frames'/f'{s["id"]}.jpg').resize((320,180));x=j%4*320;y=j//4*202;im.paste(pic,(x,y));draw.text((x+4,y+182),f'{s["id"]} {s["start"]/30:.2f}s {s["scene"]}',fill='white')
  im.save(E/f'qa_page_{page+1:02}.jpg',quality=90)
 print('SHEETS',len(shots),flush=True)
def measure():
 d=json.loads((E/'episode_data.json').read_text());m=json.loads((E/'narration.json').read_text());video=E/'n18_cartoon_v5_1080p.mp4';p=probe(video);v=next(s for s in p['streams'] if s['codec_type']=='video')
 shots=d['shots'];length=np.array([(s['end']-s['start'])/30 for s in shots]);action=np.array([(s['end']-s['start'])/30 for s in shots if not s['serious']]);insert=[s for s in shots if s['type']=='insert'];acting=[s for s in shots if s['characterActing']]
 sil=subprocess.run(['ffmpeg','-hide_banner','-i',str(V.A/'voice.wav'),'-af','silencedetect=noise=-45dB:d=0.01','-f','null','-'],capture_output=True,text=True,check=True).stderr
 silence=[float(x) for x in re.findall(r'silence_duration: ([\d.]+)',sil)]
 visual=run_filter(video,'freezedetect=n=-50dB:d=1.5,blackdetect=d=0.1:pix_th=0.08')
 (E/'video_detection.log').write_text(visual)
 freeze=[float(x) for x in re.findall(r'freeze_duration: ([\d.]+)',visual)]
 black=re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)',visual)
 loud=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-vn','-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True,check=True).stderr
 (E/'loudness.log').write_text(loud);summary=loud[loud.rfind('Summary:'):]
 lufs=float(re.search(r'I:\s*([\d.-]+) LUFS',summary)[1]);tp=float(re.search(r'Peak:\s*([\d.-]+) dBFS',summary)[1])
 asr=json.loads((E/'asr_final.json').read_text());takes=json.loads((E/'asr_takes.json').read_text())
 # Independent continuous-AAC ASR word times provide a useful timing audit,
 # not manual phoneme ground truth. Compare caption onsets after char alignment.
 ref=V.norm(' '.join(r['text'] for r in m['items']));hyp='';word_times=[]
 for seg in asr['segments']:
  for word in seg.get('words',[]):
   chars=V.norm(word['word']);hyp+=chars
   word_times.extend(np.linspace(word['start'],max(word['start']+.01,word['end']),len(chars),endpoint=False).tolist())
 mapping={}
 for block in difflib.SequenceMatcher(None,ref,hyp,autojunk=False).get_matching_blocks():
  for k in range(block.size):mapping[block.a+k]=block.b+k
 prefix=[];onset_errors=[]
 for c in d['captions']:
  at=len(V.norm(' '.join(prefix)));matched=mapping.get(at)
  if matched is not None and matched<len(word_times):onset_errors.append((c['start']/30-word_times[matched])*1000)
  prefix.append(c['text'])
 share_probe=probe(E/'n18_cartoon_v5_360p.mp4');share_v=next(x for x in share_probe['streams'] if x['codec_type']=='video')
 dates=[c['text'] for c in d['captions'] if re.search(r'이천[가-힣\s]*년|(?:오월|유월|육월|칠월|팔월|구월)\s*[가-힣]+일',c['text'])]
 gaps=[(b['start']-a['end'])/30 for a,b in zip(shots,shots[1:]) if b['start']!=a['end']]
 loops=[r['start'] for r in m['items'] if r['beat'] in ['question','loop']]
 failures=[]
 checks=dict(share_resolution=share_v['width']==640 and share_v['height']==360,resolution=v['width']==1920 and v['height']==1080,fps=v['r_frame_rate']=='30/1',duration_270_to_330=270<=float(p['format']['duration'])<=330,pace=m['syllables']/m['duration']>=7.5,silence=max(silence,default=0)<=.15,asr=asr['match']>=.98,numeric_dates=not dates,insert_duration=max((s['end']-s['start'])/30 for s in insert)<=1.5,action_shot_average=float(np.mean(action))<=1.8,static_span=not freeze,no_black=not black,continuous_shots=not gaps,no_audio_clipping=tp<0)
 failures=[k for k,val in checks.items() if not val]
 result=dict(status='COMPLETE' if not failures else 'NEEDS_FIX',checks=checks,failures=failures,runtime_s=float(p['format']['duration']),frames=int(v['nb_frames']),resolution=[v['width'],v['height']],fps=30,narration=dict(engine=m['model'],voice=m['voice'],syllables=m['syllables'],whole_film_syl_s=m['syllables']/m['duration'],speech_only_syl_s=m['syllables']/sum(r['duration'] for r in m['items']),minimum_sentence_syl_s=min(r['syllables']/r['duration'] for r in m['items']),silence_threshold_db=-45,maximum_silence_s=max(silence,default=0),silence_events=len(silence)),asr=dict(delivered_aac_match=asr['match'],errors=asr['errors'],characters=asr['characters'],sentence_takes_match=takes['match'],no_prompt=True,details='asr_final.json'),subtitles=dict(cues=len(d['captions']),timing='Local Whisper word times aligned to script characters; no forced phoneme ground truth.',frame_quantization_max_ms=16.67,independent_aac_asr_anchor_count=len(onset_errors),independent_aac_asr_onset_median_abs_ms=float(np.median(np.abs(onset_errors))),independent_aac_asr_onset_p95_abs_ms=float(np.percentile(np.abs(onset_errors),95)),independent_aac_asr_onset_max_abs_ms=float(np.max(np.abs(onset_errors))),manual_review='See self_review.md; automatic ASR times are estimates.'),numeric_dates=dict(korean_word_date_hits=dates,scan='Rendered subtitle text'),shots=dict(count=len(shots),mean_s=float(np.mean(length)),median_s=float(np.median(length)),p95_s=float(np.percentile(length,95)),max_s=float(np.max(length)),action_mean_s=float(np.mean(action)),insert_count=len(insert),max_insert_s=max((s['end']-s['start'])/30 for s in insert),gaps=gaps),acting_characters=dict(shots=len(acting),present_shots=sum(s.get('characterPresent',False) for s in shots),held_character_shots=[s['id'] for s in shots if s.get('characterPresent') and not s['characterActing']],total_shots=len(shots),shot_share=len(acting)/len(shots),time_share=sum(s['end']-s['start'] for s in acting)/d['durationInFrames'],method='Shot manifest classification, checked against every-cut images. Held hospital-loss and witness-collapse figures are excluded. Generic breathing alone is not counted as a new action; figures are drilling, collapsing, checking/transporting, testifying, reading/gesturing or bowing. No automated person detector.'),retention=dict(cold_open_complete_s=m['items'][0]['end'],question_complete_s=m['items'][1]['end'],loop_times_s=loops,maximum_loop_gap_s=max(np.diff(loops))),video_detection=dict(freeze_events=freeze,black_events=black,threshold='ffmpeg freezedetect -50dB for 1.5s; blackdetect .1s'),audio=dict(integrated_lufs=lufs,true_peak_dbtp=tp),red_lines=dict(victim_identifiable=False,gore=False,invented_incident_dialogue=False,invented_assault=False,collapse_and_emergency_shown=True,comic_suffering=False,role_names=['중대장','부중대장'],source_scope=['facts.md','facts_enrich.md accepted rows']),sources={x:hashlib.sha256((E.parent/x).read_bytes()).hexdigest() for x in ['facts.md','facts_enrich.md']},external_network=False,remotion_loopback_only=True,uploads=False,engine='Read-only engine_v5/Puppet with N18-specific Recruit, Medic and staging; READY events in engine_poll.json',share=dict(resolution=[share_v['width'],share_v['height']],fps=share_v['r_frame_rate'],duration=share_probe['format']['duration']))
 (E/'qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':
 import sys
 if len(sys.argv)>1 and sys.argv[1]=='sheets':sheets()
 else:measure()
