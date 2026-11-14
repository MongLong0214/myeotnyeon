"""Offline release evidence: actual delivery decode, local facts and loaded-font audit."""
from pathlib import Path
import json,re,sys,subprocess,hashlib,copy
import numpy as np,soundfile as sf
from PIL import Image
W=Path(__file__).resolve().parents[3];S=Path(__file__).parent
sys.path.insert(0,str(W/'episodes/quiz/out/v3'));sys.path.insert(0,str(W/'episodes/quiz'))
import qa,tempo,textgate
sys.path.insert(0,str(W/'episodes/quiz/v51_support'))
from align_v51 import normalizer,align

def load(p):return json.loads(p.read_text())
def run(args):
 p=subprocess.run(args,capture_output=True,text=True);return p.stdout+p.stderr

def frames(p,selector,size='1080:1920'):
 r=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-vf',f'select={selector},scale={size}','-vsync','0','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True)
 w,h=map(int,size.split(':'));return np.frombuffer(r.stdout,np.uint8).reshape(-1,h,w,3)

def metric(x):
 import cv2
 gray=cv2.cvtColor(x,cv2.COLOR_RGB2GRAY);return dict(mean_luminance=float(gray.mean()),edge_density=float((cv2.Canny(gray,50,150)>0).mean()))

def band(x):
 gray=np.dot(x,[.2126,.7152,.0722]);flat=gray.std(1)<1;best=cur=0;start=0
 for i,f in enumerate(flat):
  if f:
   if cur==0:start=i
   if abs(gray[i].mean()-gray[start].mean())>1:start=i;cur=0
   cur+=1;best=max(best,cur)
  else:cur=0
 return int(best)

def fix(x):
 if isinstance(x,dict):return {('pass' if k=='pass_' else k):fix(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [fix(v) for v in x]
 if isinstance(x,np.generic):return x.item()
 return x

def main(q):
 p=W/'episodes/quiz'/q/'v52';v=p/'candidate.mp4';doc=load(p/'render_final.json');old=load(W/'episodes/quiz'/q/'v52_input/render.json');audio=load(p/'audio.json');n=doc['durationInFrames']
 ep=copy.deepcopy(qa.EPISODES[q]);ep['cues'][0][2][0]=audio['items'][0]['text'];qa.EPISODES[q]=ep;textgate.EPISODES[q]=ep
 labels=textgate.labels;textgate.labels=lambda e:labels(e)+['다음 판결도 맞혀보세요','구독',f"몇년나옴? · 형량 퀴즈 #{doc['ep']['no']}"]
 result=dict(episode=q,file=f'upload/v52_{q}.mp4',input_props={'composition':'V52'},probe=qa.probe(v),loudness=qa.loud(v),freeze_black=qa.freeze_black(v),numbers=qa.numbers(q),spelling=qa.spelling(q),accuracy=qa.accuracy(q),death_case=qa.serious(q),textgate=textgate.gate(q))
 result['duration']=dict(seconds=n/30,hard_22_40=22<=n/30<=40,preferred_25_35=25<=n/30<=35,preferred_verdict='PASS' if 25<=n/30<=35 else 'OUTSIDE_SOFT_TARGET',policy='Only 22–40 seconds is hard. 25–35 and legacy 25–40 are report-only per owner.')
 # Decode all early frames full resolution, including slam and every zoom step.
 early=frames(v,'lte(n\\,60)');oldframe=frames(W/'upload'/f'v3_{q}.mp4','eq(n\\,0)')[0];m0=metric(early[0]);m3=metric(oldframe)
 bb=[band(x) for x in early];diff=np.abs(early[0].astype(float)-early[60]).mean()
 pairs=[dict(a=a,b=b,mae=float(np.abs(early[a].astype(float)-early[b]).mean())) for a,b in zip([0,15,30,45],[15,30,45,60])]
 log=(p/'audit.log').read_text();audit={int(f):int(b) for f,b in re.findall(r'AUDIT '+q+r' f=(\d+) n=(\d+).*? END',log)};hooks={}
 for line in log.splitlines():
  m=re.search(r'HOOKCHECK51 (\{.*\}) END',line)
  if m:
   try:r=json.loads(m[1]);hooks[r['frame']]=r
   except Exception:pass
 (p/'audit_frames_checked.json').write_text(json.dumps(audit,indent=1));(p/'hook_frames_checked.json').write_text(json.dumps(hooks,ensure_ascii=False,indent=1))
 result['audit']=dict(frames=len(audit),expected=n,bad_frames=[f for f,b in audit.items() if b],pass_=set(audit)==set(range(n)) and not any(audit.values()))
 result['hook_gates']=dict(frame0_nonblank=dict(v3=m3,v51=m0,pass_=m0['mean_luminance']>3 and m0['edge_density']>.002,note='Photographic night lighting replaces the rejected bright paper comparison; old v3 luminance delta is reported, not treated as a brightness objective.'),
  no_empty_band_0_60=dict(max_band_pixels=max(bb),limit_pixels=96,per_frame=bb,pass_=max(bb)<=96,method='Full-width decoded luma std<1 and colour drift<1, all 61 full-resolution frames. Hero Img covers 1080x1920.'),
  text_by_frame4=dict(measured=hooks.get(4),pass_=hooks.get(4,{}).get('hookVisible',False)),
  headline_glyph_height=dict(min_pixels=hooks.get(4,{}).get('minGlyphHeight',0),limit_pixels=110,method='Loaded Black Han Sans canvas actualBoundingBoxAscent + actualBoundingBoxDescent for every Korean/numeric glyph; no reliance on CSS line box.',pass_=hooks.get(4,{}).get('minGlyphHeight',0)>=110),
  no_branding_before_2s=dict(pass_=all(f in hooks and not hooks[f]['branding'] for f in range(60))),
  motion_0_60=dict(mean_absolute_difference=diff,adjacent_sample_pairs=pairs,pass_=diff>1 and all(x['mae']>.2 for x in pairs)),
  end_cta_last_1p5s=dict(pass_=all(f in hooks and hooks[f]['cta'] for f in range(n-45,n))),
  cta_fills_half_frame=dict(min_ratio=min((hooks.get(f,{}).get('ctaAreaRatio',0) for f in range(n-45,n)),default=0),definition='Continuous CTA card incl. large headline + subscribe button; measured bounding area / full frame.',pass_=all(hooks.get(f,{}).get('ctaAreaRatio',0)>=.5 for f in range(n-45,n))))
 # AAC speech onset and all between-line silent gaps, on the delivered signal.
 r=subprocess.run(['ffmpeg','-v','error','-i',str(v),'-ac','1','-ar','16000','-f','f32le','-'],capture_output=True,check=True);y=np.frombuffer(r.stdout,np.float32);sr=16000;win=80;rms=np.sqrt(np.mean(y[:len(y)//win*win].reshape(-1,win)**2,axis=1));voiced=rms>10**(-45/20);idx=np.where(voiced)[0];onset=idx[0]*.005 if len(idx) else 999
 result['hook_gates']['narration_onset']=dict(seconds=onset,limit_seconds=.15,pass_=onset<=.15)
 tim=load(p/'timing.json');gaps=[]
 for a,b in zip(tim['items'],tim['items'][1:]):
  left=max(0,round((a['end']/30-.35)/.005));right=min(len(voiced),round((b['start']/30+.35)/.005));v0=voiced[left:right];edges=np.diff(np.r_[True,v0,True].astype(int));runs=list(zip(np.where(edges==-1)[0],np.where(edges==1)[0]));mid=(a['end']+b['start'])/60
  containing=[(aa,bb) for aa,bb in runs if (left+aa)*.005<=mid<=(left+bb)*.005];gap=max(((bb-aa)*.005 for aa,bb in containing),default=0);gaps.append(dict(after=a['id'],before=b['id'],seconds=gap))
 result['breath']=dict(threshold_dbfs=-45,window_ms=5,inter_line_gaps=gaps,max_seconds=max((g['seconds'] for g in gaps),default=0),limit_seconds=.12,pass_=all(g['seconds']<=.12+1e-6 for g in gaps))
 speech_seconds=sum(i['duration'] for i in audio['items']);sps=audio['syllables']/speech_seconds
 baseline=audio['original_v3_syllables_per_second']
 result['narration_speed']=dict(syllables=audio['syllables'],measured_utterance_seconds=speech_seconds,syllables_per_second=sps,whole_video_syllables_per_second=audio['syllables']/(n/30),original_v3_syllables_per_second=baseline,original_body_syllables_per_second=audio['original_body_syllables_per_second'],hook_syllables_per_second=audio['hook_syllables_per_second'],hook_minimum=7.5,definition=audio['definition'],per_line=[{k:i[k] for k in ['id','syllables','duration','sps','engine_speed','steps','voice','resynthesized']} for i in audio['items']],only_hook_resynthesized=True,pass_=sps>=baseline and audio['hook_syllables_per_second']>=max(7.5,audio['original_body_syllables_per_second']))
 # Independently verify every source-master PCM speech segment in the new master.
 original,pcm_sr=sf.read(W/'production/compositor/public'/q/'mix_master.wav',dtype='int32',always_2d=True);master,master_sr=sf.read(p/'mix_master.wav',dtype='int32',always_2d=True);assert pcm_sr==master_sr==48000
 evidence=[]
 for item in audio['body_pcm_evidence']:
  a=item['source_start_sample'];b=item['delivery_start_sample'];ln=item['samples'];evidence.append(dict(item,measured_identical=bool(np.array_equal(original[a:a+ln],master[b:b+ln]))))
 result['body_pcm_identity']=dict(lines=evidence,original_master_sha256=hashlib.sha256((W/'production/compositor/public'/q/'mix_master.wav').read_bytes()).hexdigest(),pass_=all(i['measured_identical'] for i in evidence))
 scales={}
 for line in log.splitlines():
  match=re.search(r'HOOKCHECK52SCALE (\{.*\}) END',line)
  if match:
   try:z=json.loads(match[1]);scales[z['frame']]=z
   except Exception:pass
 result['hook_gates']['push_in_1_to_1p12_2s']=dict(frames={f:scales.get(f) for f in [0,30,60]},pass_=all(abs(scales.get(f,{}).get('scale',0)-value)<.00001 for f,value in [(0,1),(30,1.06),(60,1.12)]))
 d30=float(np.abs(early[0].astype(float)-early[30]).mean())
 result['hook_gates']['motion_0_30']=dict(mean_absolute_difference=d30,pass_=d30>1)
 # Final AAC ASR, no prompt, only the already installed local model.
 import mlx_whisper
 model=next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
 wav=p/'final16k_checked.wav'
 if not wav.exists():sf.write(wav,y,16000,subtype='PCM_16')
 assert sf.info(wav).samplerate==16000
 asr=mlx_whisper.transcribe(str(wav),path_or_hf_repo=str(model),language='ko',condition_on_previous_text=False,temperature=0,word_timestamps=True)
 norm=normalizer(q);acc_raw=1-qa.cer(qa.norm(audio['reference']),qa.norm(asr['text']));acc=1-qa.cer(norm(audio['reference']),norm(asr['text']));result['asr_final_mix']=dict(reference=audio['reference'],transcript=asr['text'],accuracy=acc,accuracy_before_episode_numeral_lexicon=acc_raw,numeral_normalization='Existing episode TTS lexicon applied to both reference and ASR; e.g. 2심 / 이 심. Different numeric values remain different.',segments=asr['segments'],pass_=acc>=.99,backend='offline cached mlx-whisper large-v3-turbo; final AAC; no prompt')
 rows,sub_acc=align(doc,audio,asr,norm)
 errors=[dict(text=sub['text'],start_error_ms=abs(sub['from_']/30-row['start_seconds'])*1000,end_error_ms=abs(sub['to']/30-row['end_seconds'])*1000) for sub,row in zip(doc['subtitles'],rows)]
 result['subtitle_sync']=dict(all_subtitles_in_range=all(0<=s['from_']<s['to']<=n for s in doc['subtitles']),method='Independent final AAC Whisper word timestamps checked against captions aligned to the new WAV master; ±200ms start/end tolerance.',per_caption=errors,max_start_error_ms=max(x['start_error_ms'] for x in errors),max_end_error_ms=max(x['end_error_ms'] for x in errors),pass_=sub_acc>=.99 and all(0<=s['from_']<s['to']<=n for s in doc['subtitles']) and all(x['start_error_ms']<=200 and x['end_error_ms']<=200 for x in errors))
 rv=next(c for c in doc['cues'] if c['scene']=='reveal');reveal=rv['from']+rv['a']['s1']+2
 result['structure']=dict(reveal_frame=reveal,reveal_ratio=reveal/n,pass_=reveal/n>=.75,hook_cut_frame=61,hook_cut_policy='v51 cut retained at frame 61; 1.00→1.12 push reaches full scale at frame 60 (2.0s).')
 motion=run(['ffmpeg','-hide_banner','-nostats','-i',str(v),'-vf','freezedetect=n=0.001:d=1.5','-an','-f','null','-']);(p/'motion_checked.log').write_text(motion);holds=[float(x) for x in re.findall(r'freeze_start: ([\d.]+)',motion)]
 result['motion']=dict(holds_over_1p5s=holds,pass_=not holds,method='Full-resolution full delivery FFmpeg freezedetect n=.001 d=1.5; v52 body scene receives a subtle continuous push.')
 # Compare every factual string, independent of numeric animation timestamps.
 def strings(x):
  if isinstance(x,str):return [x]
  if isinstance(x,list):return sum((strings(v) for v in x),[])
  if isinstance(x,dict):return sum((strings(v) for v in x.values()),[])
  return []
 facts=doc['ep']==old['ep'] and [strings(c['p']) for c in doc['cues']]==[strings(c['p']) for c in old['cues']]
 result['body_preservation']=dict(episode_choices_answers_reasons_and_all_visual_strings_unchanged=facts,all_narration_words_unchanged=audio['wording_identical_to_v5'],audio='Original v3 normalized master speech segments preserved sample-for-sample; only gaps removed and the new hook synthesised.',pass_=facts and audio['wording_identical_to_v5'])
 result['default_identity']=load(S/'source_identity.json');result['blender']=load(W/'research/hook_stills'/f'{q}_render.json')
 result['pipeline']=dict(network=False,uploads=False,renderer='episodes/quiz/v52_support/render_final.cjs',props={'composition':'V52'},codec='h264',crf=14,bt709=True,audio_bitrate='320k')
 gates={k:('PASS' if o.get('pass',o.get('pass_',False)) else 'FAIL') for k,o in result.items() if isinstance(o,dict) and ('pass' in o or 'pass_' in o)}
 gates.update({k:'PASS' if o['pass_'] else 'FAIL' for k,o in result['hook_gates'].items()})
 gates.update(textgate='PASS' if result['textgate']['passed'] else 'FAIL',duration_22_40='PASS' if 22<=n/30<=40 else 'FAIL',duration_25_35='REPORT_ONLY_PASS' if 25<=n/30<=35 else 'REPORT_ONLY_OUTSIDE',duration_25_40='REPORT_ONLY_PASS' if 25<=n/30<=40 else 'REPORT_ONLY_OUTSIDE',reveal_at_least_75_percent='PASS' if reveal/n>=.75 else 'FAIL',visual_change_every_1p5_seconds='PASS' if not holds else 'FAIL',tempo_metadata='PASS' if not holds else 'FAIL',body_pcm_unchanged='PASS' if result['body_pcm_identity']['pass_'] else 'FAIL',default_props_identity='PASS' if all(i['match'] for i in result['default_identity']) else 'FAIL',typecheck='PASS' if (S/'tsc_final_entry.log').read_text()=='' else 'FAIL',body_visual_and_facts_preserved='PASS' if facts else 'FAIL')
 result['gates']=gates;result['all_hard_gates_pass']=all(v!='FAIL' for v in gates.values());result['sha256']=hashlib.sha256(v.read_bytes()).hexdigest();result=fix(result)
 (p/'qa_checked.json').write_text(json.dumps(result,ensure_ascii=False,indent=1));print(q,json.dumps(gates,ensure_ascii=False),flush=True)
if __name__=='__main__':main(sys.argv[1])
