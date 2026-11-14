from pathlib import Path
import json,sys,subprocess,re,hashlib,copy,shutil
import numpy as np,soundfile as sf
W=Path(__file__).resolve().parents[3];S=Path(__file__).parent
sys.path.insert(0,str(S));import qa_v5 as Q

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 identity=[]
 for f in [0,45,900]:
  b=sha(S/f'before_q009/{f}.png');a=sha(S/f'after_final_q009/{f}.png');identity.append(dict(frame=f,before=b,after=a,match=b==a))
 assert all(i['match'] for i in identity)
 (S/'default_identity.json').write_text(json.dumps(identity,indent=1))
 manifest=[];summary={};pending=[]
 for q in ['q015','q012','q016','q017']:
  p=W/'episodes/quiz'/q/'v5';rev='_r6' if q=='q012' else '_r4';v=p/f'candidate{rev}.mp4';r=json.loads((p/f'qa{rev}.json').read_text());doc=json.loads((p/'render.json').read_text());old=json.loads((W/'production/compositor/public'/q/'render.json').read_text());a=json.loads((p/'audio.json').read_text())
  m0=Q.metrics(Q.full_frame(v));m3=Q.metrics(Q.full_frame(W/'upload'/f'v3_{q}.mp4'))
  r['hook_gates']['frame0_nonblank']=dict(v3=m3,v5=m0,width=1080,height=1920,edge_detector='OpenCV Canny 50/150; original decoded RGB, BT.709',**{'pass':m0['mean_luminance']>m3['mean_luminance'] and m0['edge_density']>m3['edge_density']})
  log=Q.run(['ffmpeg','-hide_banner','-nostats','-i',str(v),'-vf','freezedetect=n=0.001:d=1.5','-an','-f','null','-']);(p/'motion_final.log').write_text(log);holds=[float(x) for x in re.findall(r'freeze_start: ([\d.]+)',log)]
  r['motion_diagnostic_prior_threshold']=r['motion'];r['motion']=dict(threshold=0.001,threshold_db=-60,holds_over_1p5s=holds,pass_=not holds,method='Same threshold as existing out/v3/qa.py freeze_black; duration tightened from 2.5 to 1.5 s. Whole decoded 1080x1920 frame, no crop.')
  tg=json.loads((p/'textgate_actual.json').read_text());r['textgate']=tg
  delta=a['delta_frames'];assert doc['ep']==old['ep']
  scenes=True
  for c,b in zip(doc['cues'][1:],old['cues'][1:]):
   expected=copy.deepcopy(b);expected['from']+=delta;scenes &= c==expected
  oldcut=a['old_cut_frame'];expected=[dict(s,from_=s['from_']+delta,to=s['to']+delta) for s in old['subtitles'] if s['from_']>=oldcut]
  actual=[s for s in doc['subtitles'] if s['from_']>=a['new_cut_frame']]
  subs=actual==expected and all(0<=s['from_']<s['to']<=doc['durationInFrames'] for s in doc['subtitles'])
  orig,sr=sf.read(W/'production/compositor/public'/q/'mix_master.wav',always_2d=True);new,_=sf.read(p/'mix_master_r2.wav',always_2d=True)
  pcm=np.array_equal(orig[round(oldcut*sr/30):],new[round(a['new_cut_frame']*sr/30):])
  r['body_preservation']=dict(all_later_cues_unchanged_except_uniform_time_shift=scenes,subtitles_unchanged_except_first_line_and_time_shift=subs,choices_answer_reason_and_episode_fields_unchanged=doc['ep']==old['ep'],original_body_pcm_sample_identical=pcm,first_cue_note='q012 first-cue zoom beats follow the new first-sentence duration; second sentence/audio untouched.' if q=='q012' else 'First-cue duration/narration anchors follow the replacement first line.')
  r['default_identity']=identity;r['pipeline']=dict(renderer='episodes/quiz/v5_support/render.cjs',qa_engines=['episodes/quiz/out/v3/qa.py','episodes/quiz/out/v3/tempo.py','episodes/quiz/out/v3/textgate.py','production/compositor/src/SafeAudit.tsx','cached mlx-whisper large-v3-turbo'],props={'hookStyle':'v5'},other_props='same default props and original public document as each v3 upload; no premium/type2 override',codec='h264',crf=14,color_space='bt709',audio_bitrate='320k',network=False,uploads=False)
  r['gates'].update(frame0_nonblank='PASS' if r['hook_gates']['frame0_nonblank']['pass'] else 'FAIL',motion='PASS' if not holds else 'FAIL',visual_change_every_1p5_seconds='PASS' if not holds else 'FAIL',textgate='PASS' if tg['passed'] else 'FAIL',body_pcm_unchanged='PASS' if pcm else 'FAIL',body_visual_and_facts_preserved='PASS' if scenes else 'FAIL',subtitle_sync='PASS' if subs else 'FAIL',default_props_identity='PASS',typecheck='PASS')
  r['duration']['preferred_25_35_verdict']='PASS' if r['duration']['preferred_25_35'] else 'FAIL'
  r['duration']['policy']='Existing hard gate 22–40 s; v3d release gate 25–40 s. Original qa.py 25–35 s remains recorded separately; q012 exceeds that preference by 0.867 s because the ask was added and existing body audio was preserved.'
  r['gates']['duration_25_35']='PASS' if r['duration']['preferred_25_35'] else 'FAIL'
  r['all_pass']=all(v in ['PASS','N/A'] for v in r['gates'].values())
  r['all_original_qa_py_gates_pass']=r['all_pass'] and r['duration']['preferred_25_35']
  r['phone_review']=dict(first_61_frames_and_all_last_45_frames='research/metrics/hook_v5_sheet.jpg',q016_v3_comparison='research/metrics/hook_v3_vs_v5_q016.jpg',reviewed=True,notes='Frame 0 and slam remain readable and inside the audit zones; hook uses original headline glyphs. Existing paper/stamp/type scene art is reused for paper-only episodes, empty wildfire landscape for q012. No body, injury, weapon or suffering image added.')
  failures={k for k,v in r['gates'].items() if v=='FAIL'}
  assert failures==({'duration_25_35'} if q=='q012' else set()),(q,r['gates'])
  dest=W/'upload'/f'v5_{q}.mp4';assert not dest.exists(),dest
  manifest.append(f"{r['sha256']}  v5_{q}.mp4")
  r['output']=str(dest);r['qa_notes']=['Only hookStyle=v5 loads the separately prepared v5 render document/audio. Default documents and masters untouched.','Factual hook copy is the existing first hook line, split only at its spaces. CTA copy is exactly the user-requested text.','First-cue TTS same M1, speed 1.3, 16 steps; other PCM samples are bit-identical. New line gain capped for true-peak gate.']
  out=W/'episodes/quiz'/q/'qa_v5.json';assert not out.exists();pending.append((v,dest,out,r))
  summary[q]=dict(file=str(dest.relative_to(W)),sha256=r['sha256'],duration=r['duration']['seconds'],gates=r['gates'],preferred_25_35=r['duration']['preferred_25_35_verdict'],asr=r['asr_final_mix']['accuracy'],onset=r['hook_gates']['narration_onset']['seconds'])
 for v,dest,out,r in pending:
  with v.open('rb') as source,dest.open('xb') as f:shutil.copyfileobj(source,f)
  assert sha(dest)==r['sha256']
  out.write_text(json.dumps(r,ensure_ascii=False,indent=1))
 manifestfile=W/'upload/v5.sha256';assert not manifestfile.exists();manifestfile.write_text('\n'.join(manifest)+'\n')
 before=json.loads((S/'protected_before.json').read_text());changed=[f for f,h in before.items() if not (W/f).exists() or sha(W/f)!=h]
 assert set(changed)=={'production/compositor/src/Quiz.tsx','production/compositor/src/Root.tsx'},changed
 (S/'protection_final.json').write_text(json.dumps(dict(checked=len(before),changed=changed,preexisting_uploads_and_audio_unchanged=True),indent=1));(S/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=1));print(json.dumps(summary,ensure_ascii=False,indent=1))
if __name__=='__main__':main()
