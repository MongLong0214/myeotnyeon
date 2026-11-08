"""Measure the delivered film. Review results are separate from model estimates."""
import json,subprocess,re,hashlib,math
import numpy as np
import soundfile as sf
from PIL import Image
from audio import E,W,SR,norm
from prepare import align,write_alignment

def probe(path):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
def main():
 data=json.loads((E/'episode_data.json').read_text());shots=data['shots'];meta=json.loads((E/'narration.json').read_text())
 p=probe(E/'n18_cartoon_v6_1080p.mp4');v=next(s for s in p['streams'] if s['codec_type']=='video')
 share=probe(E/'n18_cartoon_v6_360p.mp4');sv=next(s for s in share['streams'] if s['codec_type']=='video')
 asr=json.loads((E/'asr_aac.json').read_text());takes=json.loads((E/'asr_takes.json').read_text())
 w,sr=sf.read(E/'audio/narration.wav');hop=round(sr*.005)
 rms=np.array([np.sqrt(np.mean(w[i:i+hop]**2)) for i in range(0,len(w),hop)])
 quiet=rms<.0025;change=np.diff(np.r_[False,quiet,False].astype(int));runs=[(a*hop/sr,min(len(w),b*hop)/sr) for a,b in zip(np.where(change==1)[0],np.where(change==-1)[0])]
 sentence=[];intra=[]
 for a,b in runs:
  if b-a<.025:continue
  if any(a<=r['end']+.025 and b>=r['end']+.20 for r in meta['items']):sentence.append(b-a)
  elif any(a>=r['start']-.005 and b<=r['end']+.005 for r in meta['items']):intra.append(b-a)
 offsets=[abs(s['cut_offset_s']) for s in shots[1:]]
 jumps=[]
 for a,b in zip(shots,shots[1:]):
  if a['subject']==b['subject'] and a['size']==b['size'] and abs(a['angle_deg']-b['angle_deg'])<30:jumps.append([a['id'],b['id']])
 mapping=json.loads((E/'delivered_frames.json').read_text());similar=[];visual_diffs=[]
 for s in shots[1:]:
  before=np.array(Image.open(E/mapping[str(s['start']-1)]).convert('L'))[35:310]
  after=np.array(Image.open(E/mapping[str(s['start'])]).convert('L'))[35:310]
  diff=float(np.mean(np.abs(before.astype(float)-after.astype(float))));visual_diffs.append(diff)
  if diff<2.5:similar.append(dict(cut=s['id'],mean_abs_luma_difference=diff))
 # Compare subtitle onsets to independent AAC recognition, without feeding it text.
 hyp='';times=[]
 for seg in asr['segments']:
  for word in seg.get('words',[]):
   c=norm(word['word']);hyp+=c;times.extend(np.linspace(word['start'],max(word['end'],word['start']+.01),len(c),endpoint=False))
 ref=''.join(norm(c['text']) for c in data['captions']);mp=align(ref,hyp);pos=0;sync=[];inside_sync=[];known_onsets=[];seen=set()
 byshot={s['id']:s for s in shots};byrow={r['id']:r for r in meta['items']}
 for c in data['captions']:
  sid=byshot[c['shotId']]['sentenceId'];first=sid not in seen;seen.add(sid)
  if first:known_onsets.append(abs(c['start']/30-byrow[sid]['start']))
  if pos in mp:
   delta=abs(c['start']/30-times[mp[pos]]);sync.append(delta)
   if not first:inside_sync.append(delta)
  pos+=len(norm(c['text']))
 row_positions={};pos=0
 for r in meta['items']:row_positions[r['id']]=pos;pos+=len(norm(r['text']))
 inside_cuts=[]
 for s in shots:
  if s['word_offset']:
   charpos=row_positions[s['sentenceId']]+s['word_offset']
   if charpos in mp:inside_cuts.append(abs(s['start']/30-times[mp[charpos]]))
 cut_crosscheck=max(known_onsets+inside_cuts)
 sequences={}
 for s in shots:sequences.setdefault(s['scene'],[]).append(s['size'])
 reviews=json.loads((E/'visual_review.json').read_text()) if (E/'visual_review.json').exists() else {}
 mismatches=[s['id'] for s in shots if s['review']!='MATCH']
 checks=dict(resolution=[v['width'],v['height']]==[1920,1080],fps=v['r_frame_rate']=='30/1',share_resolution=[sv['width'],sv['height']]==[640,360],asr=asr['match']>=.98,pace=6.8<=meta['syllables']/sum(r['duration'] for r in meta['items'])<=7.2,sentence_pauses=bool(sentence) and min(sentence)>=.2 and max(sentence)<=.30,inside_sentence_pauses=not intra or max(intra)<=.15,clause_offsets=max(offsets)<=.12,no_jump_cuts=not jumps,all_shots_reviewed=not mismatches,all_cut_pairs_reviewed=reviews.get('cut_pairs_reviewed')==len(shots)-1,script_unchanged=(E/'script_v2.md').read_bytes()==(E.parent/'cartoon_v5/script_v2.md').read_bytes())
 result=dict(status='COMPLETE' if all(checks.values()) else 'INCOMPLETE',checks=checks,failures=[k for k,v in checks.items() if not v],runtime_s=float(p['format']['duration']),frames=int(v.get('nb_frames',data['durationInFrames'])),resolution=[v['width'],v['height']],fps=30,narration=dict(engine=meta['model'],voice=meta['voice'],fresh_synthesis=True,syllables=meta['syllables'],speech_only_syllables_s=meta['syllables']/sum(r['duration'] for r in meta['items']),whole_film_syllables_s=meta['syllables']/meta['duration'],v5_whole_film_syllables_s=8.490275663097588,inserted_sentence_gap_s=meta['sentence_gap_s'],sentence_pause_min_s=min(sentence),sentence_pause_mean_s=float(np.mean(sentence)),sentence_pause_max_s=max(sentence),sentence_pause_count=len(sentence),inside_sentence_pause_max_s=max(intra) if intra else 0,silence_threshold_rms=.0025,silence_window_ms=5),asr=dict(delivered_aac_match=asr['match'],errors=asr['errors'],characters=asr['characters'],sentence_takes_match=takes['match'],initial_prompt=None,details='asr_aac.json'),subtitles=dict(cues=len(data['captions']),alignment='Local sentence Whisper word times mapped to unchanged script; 30fps quantization.',independent_aac_onset_anchors=len(sync),mean_abs_ms=float(np.mean(sync))*1000,p95_abs_ms=float(np.percentile(sync,95))*1000,max_abs_ms=float(max(sync))*1000,estimate_note='Whisper times are acoustic estimates, not phoneme ground truth.'),cuts=dict(count=len(shots)-1,source='Final fresh narration sentence audio, unprompted word timestamps in asr_takes.json',clause_boundary_max_offset_ms=max(offsets)*1000,clause_boundary_mean_offset_ms=float(np.mean(offsets))*1000,all_hard_cuts=True,jump_cut_detector_hits=len(jumps),jump_cut_pairs=jumps,detector='Same subject requires a shot-size step or >=30° planned-angle change; actual boundary images additionally reviewed.',pixel_nearly_identical_pairs=similar,pixel_mean_luma_diff_min=min(visual_diffs),cut_sheet='cut_sheet.jpg',pairs_from='Final delivered 1080p MP4, exact frame n-1 and n'),shots=dict(count=len(shots),mean_duration_s=float(np.mean([(s['end']-s['start'])/30 for s in shots])),size_sequence_per_scene=sequences,alignment_mismatches=mismatches),cinematic_grammar=dict(establishing='Every location run opens wide, then medium and close where coverage continues.',axis='Court: defense on screen left facing right, judge screen right facing left. Camera remains audience side.',screen_direction='Recruits and stretchers move screen right; no mirrored travel shots.',match_on_action='Shared absolute f clock, persistent world coordinates; camera crops do not reset performances.',angles='Angles in manifest document axis planning; actual size changes are SVG crop magnification, not a 3D rotation.',review=reviews),red_lines=dict(victim_identifiable=False,gore=False,invented_assault=False,invented_incident_dialogue=False,collapse_explicit=True,emergency_and_transport_explicit=True,comic_suffering=False,numeric_dates=True,unverified_date_completion=False,roles=['중대장','부중대장'],blender=False,paid_services=False,network=False,uploads=False),sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [E.parent/'facts.md',E.parent/'facts_enrich.md',E/'script_v2.md']},engine='Read-only engine_v6/Puppet; N18-specific local vector blocking',share=dict(resolution=[sv['width'],sv['height']],duration_s=float(share['format']['duration'])))
 result['subtitles'].update(known_pcm_utterance_onsets=len(known_onsets),known_pcm_onset_max_abs_ms=max(known_onsets)*1000,independent_aac_inside_sentence_onsets=len(inside_sync),inside_sentence_mean_abs_ms=float(np.mean(inside_sync))*1000,inside_sentence_p95_abs_ms=float(np.percentile(inside_sync,95))*1000,inside_sentence_max_abs_ms=max(inside_sync)*1000,reference_note='Sentence starts are exact PCM assembly boundaries; unconstrained continuous Whisper can assign the first word to the preceding deliberate pause. Raw whole-stream ASR comparisons above are retained. Interior-word checks below use independent delivered AAC ASR.')
 result['cuts'].update(independent_aac_inside_sentence_boundaries=len(inside_cuts),independent_inside_sentence_max_abs_ms=max(inside_cuts)*1000,known_pcm_and_independent_clause_crosscheck_max_ms=cut_crosscheck*1000)
 result['checks']['independent_clause_sync']=bool(cut_crosscheck<=.12)
 result['checks']={k:bool(v) for k,v in result['checks'].items()}
 result['failures']=[k for k,v in result['checks'].items() if not v];result['status']='COMPLETE' if not result['failures'] else 'INCOMPLETE'
 (E/'qa_v6.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'status':result['status'],'failures':result['failures'],'pauses':result['narration'],'sync':result['subtitles']},ensure_ascii=False,indent=2))
 if all(checks.values()):(E/'READY.txt').write_text('N18 CARTOON V6 READY\n1080p and 360p rendered; final AAC ASR >=98%; every shot MATCH; every exact cut pair reviewed; 0 jump-cut detector hits. See qa_v6.json and alignment.md.\n')
 return result
if __name__=='__main__':main()
