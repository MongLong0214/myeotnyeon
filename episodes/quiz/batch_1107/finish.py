"""Encode, preserve review evidence and run the existing factory checklist."""
from pathlib import Path
import sys,json,re,hashlib,subprocess,math,difflib,os
import numpy as np
import soundfile as sf
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parents[3];B=Path(__file__).parent
sys.path.insert(0,str(W/'factory'));sys.path.insert(0,str(W/'episodes/quiz/v52_q013_q014_support'))
from review_gates import load_review,evaluate,write_json,korean_number,final_asr
from gates import fact_gate,finalize_review
from alignment_word_clock import character_clock
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(a):subprocess.run(list(map(str,a)),check=True)
def norm(t):return re.sub('[^가-힣]','',re.sub(r'\d+',lambda m:korean_number(m[0]),t))
def align(q):
 import mlx_whisper
 p=W/'upload/pkg'/f'{q}_batch1107';c=load(p/'case.json');model=next((Path.home()/'.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
 ar=mlx_whisper.transcribe(str(p/'mix_master.wav'),path_or_hf_repo=str(model),language='ko',condition_on_previous_text=False,temperature=0,word_timestamps=True)
 write_json(p/'asr_master.json',ar)
 actual,starts,ends=character_clock(ar,norm);expected=norm(' '.join(u['text'] for u in c['utterances']))
 match=difflib.SequenceMatcher(None,expected,actual,autojunk=False);mapping={}
 for block in match.get_matching_blocks():
  for i in range(block.size):mapping[block.a+i]=block.b+i
 acc=match.ratio();print('MASTER_ASR',q,acc,ar['text'],flush=True)
 offset=0;subs=[]
 for u in c['utterances']:
  text=u['text'];chunks=[]
  for sentence in re.split(r'(?<=[.!?])\s+',text):
   chunk=''
   for word in sentence.split():
    if len(chunk)+len(word)+1>24 and chunk:chunks.append(chunk);chunk=word
    else:chunk+=(' ' if chunk else '')+word
   if chunk:chunks.append(chunk)
  for chunk in chunks:
   # Text shown to viewers uses Arabic numerals, including sentences in subtitles.
   shown=chunk
   for a,b in [('삼십 년','30년'),('백육십','160'),('구천육백만','9,600만'),('십이 년','12년'),('이십 년','20년'),('오호선','5호선'),('오 년','5년'),('삼 년','3년'),('이 년','2년'),('일 년 팔 개월','1년 8개월'),('사 개월','4개월'),('일억 원','1억 원'),('십 년','10년'),('일심','1심'),('항소심','항소심')]:shown=shown.replace(a,b)
   size=len(norm(chunk));ids=[mapping[z] for z in range(offset,offset+size) if z in mapping]
   if not ids:
    if subs and subs[-1]['start_s']>=u['start_s']:
     subs[-1]['text']+=' '+shown;subs[-1]['reference']+=' '+chunk;subs[-1]['end_s']=u['end_s'];subs[-1]['alignment_limit']='ASR omitted this utterance tail; included in previous cue through utterance end. Human listening required.';offset+=size;continue
    raise ValueError(('ASR clause not aligned',q,chunk))
   a=max(u['start_s'],float(starts[min(ids)]));b=min(u['end_s'],float(ends[max(ids)]))
   subs.append(dict(start_s=a,end_s=max(a+.04,b),text=shown,reference=chunk));offset+=size
 for a,b in zip(subs,subs[1:]):a['end_s']=min(a['end_s'],b['start_s'])
 c['subtitles']=subs;write_json(p/'case.json',c)
 doc=load(p/'shots.json');doc['subtitles']=subs
 # Record real reframings at <=1.8 seconds, preserving the action/reaction axis.
 shots=[]
 for i,u in enumerate(c['utterances']):
  s=next(s for s in doc['shots'] if s['id'].split('.')[0]==u['id'])
  shots.append(dict(s,id=u['id'],start_s=u['start_s'],end_s=u['end_s'],shot_size='wide' if i in [0,3,6] else 'medium' if i in [1,4] else 'medium-close',camera='continuous motivated push / reaction reframe; no internal cut',graphic=c['display'][i]))
 doc['shots']=shots;write_json(p/'shots.json',doc)
 write_json(p/'subtitle_alignment.json',dict(accuracy=acc,reference=' '.join(u['text'] for u in c['utterances']),actual=ar['text'],clauses=subs,method='Local Whisper word timestamps, normalized spoken numbers, character alignment. Producer alignment is evidence, never CTO MATCH.'))
def encode(q):
 p=W/'upload/pkg'/f'{q}_batch1107';c=load(p/'case.json');x,sr=sf.read(p/'mix_master.wav',dtype='float32');rng=np.random.default_rng(1107)
 # Dry non-gore emphasis: soft low-frequency hit at frame zero, brief air at cuts.
 for k,u in enumerate(c['utterances']):
  start=round(u['start_s']*sr);length=min(round(sr*.085),len(x)-start);t=np.arange(length)/sr
  hit=(np.sin(2*np.pi*(95 if k==0 else 150)*t)*np.exp(-t*60)+rng.normal(0,.12,length)*np.exp(-t*95))*.045
  x[start:start+length]+=hit[:,None]
 if q=='q020':
  # Owner's requested gavel and timed choices: symbolic non-gore wood/thump sounds.
  # Three separate .4-second option beats, each with a different timbre.
  events=[(c['utterances'][4]['start_s'],.030,480),
          (c['utterances'][4]['start_s']+.4,.027,960),
          (c['utterances'][4]['start_s']+.8,.035,170),
          (c['utterances'][5]['start_s'],.075,82)]
  for seconds,amp,hz in events:
   at=round(seconds*sr);n=min(round(sr*.14),len(x)-at);t=np.arange(n)/sr
   envelope=55 if hz==480 else 25 if hz==960 else 38
   hit=amp*(np.sin(2*np.pi*hz*t)*np.exp(-t*envelope)+(.15 if hz==960 else .4)*np.sin(2*np.pi*1250*t)*np.exp(-t*90))
   x[at:at+n]+=hit[:,None]
 sf.write(p/'mix_effects.wav',x,sr,subtype='PCM_24')
 run(['ffmpeg','-v','error','-y','-i',p/'video_muted.mp4','-i',p/'mix_effects.wav','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-movflags','+faststart',p/'video.mp4'])
def qa(q):
 p=W/'upload/pkg'/f'{q}_batch1107';c=load(p/'case.json');sources=load(p/'research.json')['sources'];out=W/'episodes/review_full/shorts'/q;out.mkdir(parents=True,exist_ok=True)
 reference=B/'reference_q014_10s.mp4'
 if not reference.exists():run(['ffmpeg','-v','error','-y','-ss','8','-i',W/'upload/v52_q014_n15_comedy.mp4','-t','10','-an','-c:v','libx264','-crf','18',reference])
 bible=B/'style.txt';bible.write_text((W/'factory/unslop/STYLE_VIDEO.md').read_text()+'\nRender: q014 original ArticulatedGuy 2D SVG, flat palette #1E1712 outlines. Owner correction: centered 64px/800/stroke8 black. Subtitle content and stored timestamps unchanged.\n')
 interest=B/'interest.json'
 if not interest.exists():
  data=[]
  for f in ['viral_candidates.json','v3_candidates.json']:
   d=load(W/'research'/f);data+=d if isinstance(d,list) else d['candidates']
  write_json(interest,dict(candidates=data,interest=load(W/'research/interest/2026-10-26.json')))
 rank_path=W/'research/topic_scores'/(c['candidate'].lower()+'.json');rank=load(rank_path);topic_snapshot=p/'topic_evidence.json';write_json(topic_snapshot,rank)
 interest_rows=[dict(kind='search_volume',file=str(topic_snapshot),value=rank.get('search_summary',{}).get('peak_over_anchor_median'),metric='검색 상대지수 정점 / 기준어 일중앙값; 절대 검색량 아님',query=rank.get('search_summary',{}).get('query'),observed_at=rank.get('search_summary',{}).get('observed_at')),dict(kind='community',file=str(topic_snapshot),value=rank.get('outrage_input'),metric='YouTube 원본 표본의 댓글/1천뷰 중앙값; 감정 측정값 아님',youtube_query=rank.get('youtube',{}).get('query'),youtube_performance=rank.get('demand_inputs'),observed_at=rank.get('enriched_at'))]
 cfg=dict(subtitle_band=[.62,.70],topic_criteria='Owner: 사망·흉악·폭력·공분 최우선. 확인된 판결만, 금융·기술 범죄 감점. 이번 편은 '+c['reason'],interest_evidence=interest_rows,references=[dict(channel='몇년나옴 / owner-approved q014 comedy',video=str(reference),metrics=dict(views=1288,source='channel/analytics/REPORT_2026-11-06.md'),time_s=1,our_time_s=0)],style_bible=str(bible),renderers=['2D SVG / q014 ArticulatedGuy'],sources=[dict(s,file=str(W/s['file'])) for s in sources],pronunciation_lexicon={},batch_overrides=['Owner 12:00 / H9: 화면 재연·시간 축약·비유·시리즈 고지 0, 설명란에만 고지. 구형·선고 구별은 사실이므로 유지','H10: A/B/C 기능성 선택 카드·카운트다운·정답만 점등은 요청된 연출. 다른 패널·배지·템플릿 엔딩 없음','H5: 64px 800 black8 x540 y1190–1344. 긴 부모 cue만 동일 단어·ASR 발화 경계로 페이지 분할; 부모 시작·끝과 음성·답 공개는 유지','번호 미배정; 새 방향 q020 한 편만 렌더. 나머지는 CTO q013 v3 및 q020 검수까지 HELD','최신 문법 지시: 0.9초 반응 연결, 3프레임 snap, 0.6초 정적 표정, 선택 구도146프레임 숙고. 자동 결과를 자가 면제하지 않음. 자체 타이밍이지 R&M 실측 컷 수가 아님'])
 write_json(p/'review_inputs.json',cfg)
 context=load_review(p/'video.mp4',out,p/'shots.json',p/'script.md',p/'facts.md',review_inputs=p/'review_inputs.json',format='shorts')
 gates=evaluate(context)
 # Exact existing fact gate used by short.py, unchanged. Human semantics remain pending.
 facts=fact_gate(p,q);gates['factory_facts']=facts
 # 0.0–3.0s: every encoded frame, no sampled-frame substitute.
 paths=[context.images[n] for n in range(min(context.frames,91))]
 for part in range(math.ceil(len(paths)/30)):
  chunk=paths[part*30:(part+1)*30];sheet=Image.new('RGB',(1200,math.ceil(len(chunk)/6)*380),'#171C20');d=ImageDraw.Draw(sheet)
  for k,f in enumerate(chunk):
   n=part*30+k;im=Image.open(f);im.thumbnail((200,355));x=k%6*200;y=k//6*380;sheet.paste(im,(x,y+24));d.text((x+4,y+3),f'f{n} / {n/30:.3f}s',fill='white')
  sheet.save(out/f'hook_0-3s_{part+1:02}.png')
 # Single full consecutive sheet and quick review sheets all come from delivered frames.
 sheets=[('action_0-3s_all.png',list(range(min(context.frames,91))),7,180),('revision_0-3s_6fps.png',[min(context.frames-1,round(t*context.fps/6)) for t in range(19)],5,216),('revision_1fps.png',[min(context.frames-1,round(t*context.fps)) for t in range(math.ceil(context.duration))],6,180)]
 if q=='q020':
  sheets += [('rapid_reaction_consecutive.png',list(range(467,494)),7,180),('snap_deadpan_consecutive.png',list(range(656,678)),7,180),('choice_beats_consecutive.png',list(range(510,546)),6,180)]
 for name,numbers,cols,tw in sheets:
  th=round(tw*context.height/context.width);canvas=Image.new('RGB',(cols*tw,math.ceil(len(numbers)/cols)*(th+24)),'#171C20');draw=ImageDraw.Draw(canvas)
  for j,n in enumerate(numbers):
   im=Image.open(context.images[n]);im.thumbnail((tw,th));x=j%cols*tw;y=j//cols*(th+24);canvas.paste(im,(x,y+24));draw.text((x+3,y+3),f'f{n} / {n/context.fps:.3f}s',fill='white')
  canvas.save(out/name)
 for f in out.glob('*.png'):context.artifacts[str(f.resolve())]=sha(f)
 report=finalize_review(context,gates)
 report.update(qid=q,number=None,producer_status='REVIEW_REQUIRED',factory_facts_entrypoint='factory/gates.py:fact_gate (called by factory/short.py)',video_sha256=sha(p/'video.mp4'),planned_publish_time='2026-11-07T19:00:00+09:00 (CTO 확정 전)' if q=='q020' else f'2026-11-{8+["q018","q023","q022","q019","q021"].index(q):02}T19:00:00+09:00 (CTO 확정 전)',answer_window=[c['utterances'][5]['start_s'],c['utterances'][5]['end_s']],cta_window=[c['utterances'][6]['start_s'],c['utterances'][6]['end_s']],limits=[*report['limits'],'사람의 사실 의미·독립 취재·소품 명칭·음화 일치 검수와 CTO/CEO 서명 대기.','영상 번호 미배정. 업로드하지 않음.','Owner 최신 지시: A1–H13 모두 불합격 조건. 기존 자동 엔진의 advisory 표시는 면제가 아님.'])
 report.update(ready=False,ceo_review_eligible=False,owner_delivery_ready=False,all_A1_H13_items_are_fail_conditions=True)
 write_json(p/'qa.json',report)
 (p/'SHA256SUMS').write_text('\n'.join(sha(p/n)+'  '+n for n in ['video.mp4','cover.jpg','meta.txt','qa.json'])+'\n')
 (p/'handoff.txt').write_text('최종 파일: '+str(p/'video.mp4')+'\nSHA256: '+sha(p/'video.mp4')+'\n예정: '+report['planned_publish_time']+'\n전 프레임 시트: '+str(out/'F1.md')+'\n핵심 행위 연속 시트: '+str(out/'hook_0-3s_01.png')+'\n음성↔화면: '+str(out/'D1_D2_cut_sheet.md')+'\n사실·구형/선고·출처: '+str(out/'E3.md')+'\n남은 결함 및 한계: '+str(p/'qa.json')+'\n제작자 PASS 없음. CTO/CEO 검수 대기.\n')
 print(json.dumps(dict(qid=q,defects=report['defects'],input_missing=report['input_missing'],video_sha256=report['video_sha256']),ensure_ascii=False),flush=True)
if __name__=='__main__':
 q,mode=sys.argv[1:3]
 {'align':align,'encode':encode,'qa':qa}[mode](q)
