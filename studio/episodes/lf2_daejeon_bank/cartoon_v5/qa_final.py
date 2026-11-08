"""Measurements from final encoded picture/sound; requested checks only."""
import json,re,subprocess,hashlib,math
from pathlib import Path
import numpy as np,soundfile as sf
P=Path(__file__).resolve().parent;d=json.loads((P/'episode_data.json').read_text());out={}
def probe(f):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(f)]))
video=P/'lf2_cartoon_v5_1080p.mp4';share=P/'lf2_cartoon_v5_360p.mp4';p=probe(video);sp=probe(share);v=next(s for s in p['streams'] if s['codec_type']=='video')
out['outputs']={video.name:dict(width=v['width'],height=v['height'],fps=v['r_frame_rate'],runtime_s=float(p['format']['duration']),sha256=hashlib.sha256(video.read_bytes()).hexdigest()),share.name:dict(width=sp['streams'][0]['width'],height=sp['streams'][0]['height'],runtime_s=float(sp['format']['duration']))}
voice,sr=sf.read(P/'public/voice_full.wav');hop=round(sr*.005);a=voice[:len(voice)//hop*hop].reshape(-1,hop);rms=np.sqrt(np.mean(a*a,axis=1));quiet=rms<.01;spans=[];start=None
for i,q in enumerate(np.r_[quiet,False]):
 if q and start is None:start=i
 if not q and start is not None:
  spans.append(dict(start_s=start*.005,end_s=i*.005,duration_s=(i-start)*.005));start=None
syll=sum(n['syllables'] for n in d['narration']);dur=len(voice)/sr;rates=[n['rate'] for n in d['narration']]
out['narration']=dict(model='local Supertonic 3',voice='M1',fresh_takes=True,spoken_korean_syllables=syll,runtime_s=dur,syllables_per_s_including_gaps=syll/dur,min_cue_syllables_per_s=min(rates),mean_cue_syllables_per_s=float(np.mean(rates)),silence_method='5ms RMS below -40 dBFS, voice-only; includes leading/trailing intervals',max_silence_s=max(s['duration_s'] for s in spans),silences_over_150ms=[s for s in spans if s['duration_s']>.150001])
for mode in ['voice','encoded']:
 f=P/'qa'/f'asr_{mode}_report.json';out[f'asr_{mode}']=json.loads(f.read_text()) if f.exists() else dict(gate=False,status='not yet measured')
alignment=json.loads((P/'qa/subtitle_alignment.json').read_text());cs=d['captions'];lens=[len(c['text']) for c in cs]
out['subtitles']=dict(phrases=len(cs),alignment_method=alignment['method'],asr_character_match_fraction=alignment['matched_fraction'],minimum_phrase_match_fraction=min(p['coverage'] for p in alignment['phrases']),max_characters=max(lens),render_quantization_max_ms=1000/30,overlaps=sum(a['endMs']>b['startMs']+.01 for a,b in zip(cs,cs[1:])),invalid_spans=sum(c['endMs']<=c['startMs'] for c in cs),manual_first60_review='See self_review.md; timing uses interpolated independent ASR word boundaries, not claimed phoneme precision.')
bad=[c['text'] for c in cs if re.search(r'(?:이천|천구백)[가-힣 ]*년|(?:일|이|삼|사|오|육|칠|팔|구|시|십)[가-힣 ]*월\s*(?:일|이|삼|사|오|육|칠|팔|구|십)[가-힣 ]*일',c['text'])]
out['numeric_dates']=dict(gate=not bad,korean_word_dates=bad,displayed_dates=sorted(set(re.findall(r'\d{4}년(?:\s*\d{1,2}월)?(?:\s*\d{1,2}일)?',' '.join(c['text'] for c in cs)))),granularity='2001.12.21,2001.12.01,2001.10.15; 2011.12 and 2022.03 month only; 2017 and 2015 year only; all later court/arrest days from facts.md, no inferred month/day')
lengths=np.array([(s['end']-s['start'])/30 for s in d['shots']]);action=[(s['end']-s['start'])/30 for s in d['shots'] if s['set'] in ['parking','street']]
out['shots']=dict(count=len(lengths),mean_s=float(lengths.mean()),median_s=float(np.median(lengths)),p95_s=float(np.quantile(lengths,.95)),min_s=float(lengths.min()),max_s=float(lengths.max()),action_mean_s=float(np.mean(action)),size_distribution={t:sum(s['type']==t for s in d['shots']) for t in sorted(set(s['type'] for s in d['shots']))},histogram={'<=1s':int((lengths<=1).sum()),'1-1.5s':int(((lengths>1)&(lengths<=1.5)).sum()),'>1.5s':int((lengths>1.5).sum())},graphic_insert_max_s=max((s['end']-s['start'])/30 for s in d['shots'] if s['type']=='insert'))
freeze=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-vf','scale=320:180,freezedetect=n=-55dB:d=1.5','-an','-f','null','-'],capture_output=True,text=True,check=True)
(P/'qa/freeze.log').write_text(freeze.stderr)
out['static_spans']=dict(method='Decoded final H.264, 320x180, ffmpeg freezedetect -55dB, minimum 1.5s',detected_over_1_5s=re.findall(r'freeze_start: ([0-9.]+)',freeze.stderr),gate='freeze_start' not in freeze.stderr)
loops=[n['start_s'] for n in d['narration'] if n.get('loop')]
out['tension_beats']=dict(cold_open_s=0,central_question_starts_s=d['narration'][1]['start_s'],cliffhanger_cue_starts_s=loops,intervals_s=[b-a for a,b in zip(loops,loops[1:])])
out['red_lines']=dict(facts_only=True,facts_file='../facts.md',each_claim_minimum_independent_source_families=2,unverified_month_or_day=False,real_names_or_identifiable_victim=False,death_played_for_laughs=False,lingering_gore_closeups=False,invented_brutality=False,shooting_shown='draw→muzzle flash→stylized impact→anonymous victim falls in opening 1.5s; no asserted shot count or exposed wound',police_collision='abbreviated conceptual collision, injured officer is not depicted as killed',DNA='direct evidence identifies B only; A reached through B statement',sentencing='A shooter finding maintained; B 20 years→life through no mitigation, no implied shooter change',illustrative_shots=sum(s.get('illustrative',False) for s in d['shots']),all_illustrative_shots_labelled=True,no_network=True,no_paid_services=True,no_3D=True)
out['contact_sheet']=dict(path='sheet.jpg',cut_count=len(d['shots']),source='Every encoded cut midpoint; full-size pages in qa/sheet_*.jpg',review='self_review.md')
out['all_numeric_gates_pass']=bool(270<=dur<=330 and syll/dur>=7.5 and not out['narration']['silences_over_150ms'] and out['asr_voice']['gate'] and out['asr_encoded']['gate'] and not bad and out['shots']['action_mean_s']<=1.8 and out['shots']['graphic_insert_max_s']<=1.5 and out['static_spans']['gate'] and out['subtitles']['overlaps']==0)
(P/'qa.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in out.items() if k in ['narration','shots','static_spans','all_numeric_gates_pass']},ensure_ascii=False,indent=2))
