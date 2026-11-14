from pathlib import Path
import sys,json,re,shutil,hashlib,subprocess,math,os
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
W=Path(__file__).resolve().parents[3];B=Path(__file__).parent
sys.path.insert(0,str(B));sys.path.insert(0,str(W/'factory'))
from specs import CASES
from fresh import trim
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 from supertonic import TTS
 from bs4 import BeautifulSoup
 tts=TTS(auto_download=False,intra_op_num_threads=1,inter_op_num_threads=1);style=tts.get_voice_style('M1')
 candidates=[]
 for f in ['viral_candidates.json','v3_candidates.json']:
  obj=json.loads((W/'research'/f).read_text());candidates+=obj if isinstance(obj,list) else obj['candidates']
 used=json.loads((W/'upload/ledger.json').read_text())['entries']
 assert not {c['qid'] for c in CASES}&{e['qid'] for e in used}
 for i,c in enumerate(CASES):
  if len(sys.argv)>1 and c['qid']!=sys.argv[1]:continue
  p=W/'upload/pkg'/f"{c['qid']}_batch1107";p.mkdir(exist_ok=True);(p/'audio').mkdir(exist_ok=True)
  sources=[]
  if c['candidate'].startswith('V'):
   src=next(x for x in candidates if x['id']==c['candidate'])
   for s in src['sources']:
    f=next((W/'research').glob(f"raw*/{s['id']}.txt"),None)
    if f:sources.append(dict(id=s['id'],publisher=s['publisher'],file=str(f.relative_to(W)),url=s['url'],sha256=sha(f)))
  elif c['candidate']=='sillim':
   entries=[('연합뉴스','sillim_775019293e.json','연합뉴스'),('공공뉴스','sillim_fb51784d00.json','공공뉴스')]
   for pub,name,_ in entries:
    raw=W/'research/topic_scores/sources'/name;d=json.loads(raw.read_text());soup=BeautifulSoup(d['body'],'html.parser')
    article=soup.select_one('#article-view-content-div') if pub=='공공뉴스' else soup.select_one('.story-news.article') or soup.select_one('.story-news')
    if article is None:raise ValueError(('Missing source body',name))
    text=article.get_text(' ',strip=True);assert '무기징역' in text and len(text)>400
    f=B/'sources'/f'sillim_{pub}_body.txt';f.write_text('URL: '+d['url']+'\nPUBLISHER: '+pub+'\nSNAPSHOT: '+str(raw.relative_to(W))+'\nSNAPSHOT_SHA256: '+sha(raw)+'\n\n'+text+'\n')
    sources.append(dict(id='sillim_'+pub,publisher=pub,file=str(f.relative_to(W)),url=d['url'],sha256=sha(f)))
  elif c['candidate']=='rolls':
   entries=[('헤럴드경제','rolls_17501c02d5.json','[헤럴드경제=안세연 기자]','[email removed]'),('뉴스핌','rolls_3a3cb7e400.json','[서울=뉴스핌]','[email removed]')]
   for pub,name,startmark,endmark in entries:
    raw=W/'research/topic_scores/sources'/name;d=load(raw) if 'load' in globals() else json.loads(raw.read_text());text=BeautifulSoup(d['body'],'html.parser').get_text(' ',strip=True)
    a=text.find(startmark);b=text.find(endmark,a);assert a>=0 and b>a,(name,a,b)
    text=text[a:b+len(endmark)];f=B/'sources'/f'rolls_{pub}_body.txt';f.write_text('URL: '+d['url']+'\nPUBLISHER: '+pub+'\nSNAPSHOT: '+str(raw.relative_to(W))+'\nSNAPSHOT_SHA256: '+sha(raw)+'\n\n'+text+'\n')
    assert '징역 10년' in text and '도주' in text
    sources.append(dict(id='rolls_'+pub,publisher=pub,file=str(f.relative_to(W)),url=d['url'],sha256=sha(f)))
  else:
   names={'N13':[('KBS','N13_KBS.html','https://n.news.naver.com/mnews/article/056/0011924681'),('YTN','N13_YTN.html','https://n.news.naver.com/mnews/article/052/0002175223')],
          'N06':[('연합뉴스','N06_YNA.txt','https://n.news.naver.com/mnews/article/001/0014951956'),('뉴스1','N06_NEWS1.txt','https://news.nate.com/view/20240927n11717')]}
   for pub,name,url in names[c['candidate']]:
    raw=B/'sources'/name;soup=BeautifulSoup(raw.read_text(),'html.parser');article=soup.select_one('#dic_area') or soup.select_one('#realArtcContents')
    if article is None:raise ValueError(f'Article body missing {raw}')
    text=article.get_text('\n',strip=True)
    assert len(text)>300 and '징역' in text,(raw,len(text))
    f=B/'sources'/f'{c["candidate"]}_{pub}_body.txt';f.write_text('URL: '+url+'\nPUBLISHER: '+pub+'\nFETCHED: 2026-11-06\n\n'+text+'\n')
    sources.append(dict(id=f'{c["candidate"]}_{pub}',publisher=pub,file=str(f.relative_to(W)),url=url,sha256=sha(f)))
  if c['candidate']=='sillim':
   f=B/'sources/sillim_scourt_2024do10197.txt'
   sources.append(dict(id='sillim_scourt',publisher='대법원',file=str(f.relative_to(W)),url='https://www.scourt.go.kr/supreme/news/NewsViewAction2.work?gubun=702&seqnum=1586',sha256=sha(f)))
  assert len({s['publisher'] for s in sources})>=2
  save(p/'research.json',dict(sources=sources,review_state='NEEDS_REVIEW'))
  save(p/'recipe.json',dict(qid=c['qid'],number=None,from_scratch=True,batch='1107',no_upload=True,series_label='몇년나옴 #N'))
  utterances=[];waves=[];cur=0
  for j,(mode,text) in enumerate(c['lines']):
   f=p/'audio'/f'{j:02}.wav';spoken=text;cachekey=f.with_suffix('.text')
   if not f.exists() or (cachekey.exists() and cachekey.read_text()!=text):
    syll=len(re.findall('[가-힣]',spoken));speed=1.3
    for take in range(8):
     x,_=tts.synthesize(spoken,voice_style=style,lang='ko',speed=speed,total_steps=16,silence_duration=.06)
     x=resample_poly(trim(np.asarray(x,np.float32).reshape(-1),44100),160,147).astype(np.float32)
     rate=syll/(len(x)/48000)
     if 7.65<=rate<=9.5:break
     speed=min(2.,max(.7,speed*math.sqrt(8.2/rate)))
    if rate<7.5:raise ValueError(('pace',c['qid'],j,rate))
    sf.write(f,x,48000,subtype='PCM_24')
   cachekey.write_text(text)
   x,sr=sf.read(f,dtype='float32');assert sr==48000
   # Exact frame boundaries, a short physical speech tail, no inter-sentence card.
   frames=math.ceil(len(x)/1600);pad=frames*1600-len(x);x=np.pad(x,(0,pad))
   start=cur/48000;end=(cur+len(x))/48000
   utterances.append(dict(id=f'S{j+1}',mode=mode,text=text,tts_text=spoken,start_s=start,end_s=end,from_frame=cur//1600,dur=frames,syllables=len(re.findall('[가-힣]',spoken)),sps=len(re.findall('[가-힣]',spoken))/(len(x)/48000),file=str(f.relative_to(W)),sha256=sha(f)))
   print(c['qid'],j,round(end-start,3),'seconds',flush=True)
   waves.append(x);cur+=len(x)
  n=cur//1600;duration=n/30
  assert 20<=duration<=30,(c['qid'],duration)
  # Final 45 frames always show the next case; voice begins on this exact cut.
  # CEO addendum 2: readable answer first, followed by a separate 1.5-second CTA.
  answer_start=utterances[-2]['from_frame']
  answer_frames=max(75,utterances[5]['dur'])
  for j in [5,6]:
   x=waves[j];length=len(x);frames=answer_frames if j==5 else 45;target=frames*1600
   if length>target:
    dest=p/'audio'/f'{j:02}_fixed.wav';subprocess.run(['ffmpeg','-v','error','-y','-i',str(p/'audio'/f'{j:02}.wav'),'-af',f'atempo={length/target}',str(dest)],check=True)
    x,_=sf.read(dest,dtype='float32')
   waves[j]=np.pad(x[:target],(0,max(0,target-len(x))))
   start=answer_start if j==5 else answer_start+answer_frames
   utterances[j].update(start_s=start/30,end_s=(start+frames)/30,from_frame=start,dur=frames,sps=utterances[j]['syllables']/min(frames/30,length/48000))
  next_start=answer_start+answer_frames;next_frames=45;n=next_start+45;duration=n/30
  # The final short CTA take can run slightly longer: compress it only, preserving pitch.
  if next_frames!=45:
   src=p/'audio/06.wav';dest=p/'audio/06_cta.wav';speed=(len(waves[-1])/48000)/1.5
   subprocess.run(['ffmpeg','-v','error','-y','-i',str(src),'-af',f'atempo={speed}',str(dest)],check=True)
   x,_=sf.read(dest,dtype='float32');x=np.pad(x[:72000],(0,max(0,72000-len(x))))
   waves[-1]=x;utterances[-1].update(end_s=next_start/30+1.5,dur=45,sps=utterances[-1]['syllables']/1.5)
   n=next_start+45;duration=n/30
  assert 20<=duration<=30,(c['qid'],'final duration',duration)
  sf.write(p/'raw.wav',np.concatenate(waves),48000,subtype='PCM_24')
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(p/'raw.wav'),'-af','loudnorm=I=-14:TP=-1.5:LRA=11','-ar','48000','-ac','2',str(p/'mix_master.wav')],check=True)
  subtitles=[];shots=[]
  for j,u in enumerate(utterances):
   # Captions are timed to each synthesized clause. Each line is short enough for mobile.
   text=u['text'];chunks=re.split(r'(?<=[.!?])\s+',text)
   total=sum(len(z) for z in chunks);at=u['start_s']
   for z in chunks:
    end=min(u['end_s'],at+(u['end_s']-u['start_s'])*len(z)/total)
    subtitles.append(dict(start_s=at,end_s=end,text=z));at=end
   shots.append(dict(id=u['id'],start_s=u['start_s'],end_s=u['end_s'],subject=c['headline'] if j<5 else '법원 선고' if j==5 else '다음 사건',location=c['kind'] if j<3 else 'court' if j<6 else CASES[(i+1)%6]['kind'],shot_size='wide' if j in [0,3,6] else 'medium',screen_direction='left_to_right',axis_side='A',character_acting=True,action=c['label'][j],intended_label=c['label'][j],facts=[f'F{j+1}'],actors=[dict(role='anonymous defendant',acting=True),dict(role='anonymous adult victim',acting=True)],graphic=c['display'][j]))
  order=['q020','q022','q018','q019','q023','q021'];nxt=next(z for z in CASES if z['qid']==order[(order.index(c['qid'])+1)%6])
  c=dict(c,n=n,duration=duration,utterances=utterances,subtitles=subtitles,next_qid=nxt['qid'],next_kind=nxt['kind'],next_headline=nxt['headline'],next_question=nxt['question'])
  save(p/'case.json',c);save(p/'shots.json',dict(shots=shots,subtitles=subtitles,narration=utterances));save(p/'audio.json',dict(reference=' '.join(u['text'] for u in utterances),items=utterances,engine='Supertonic 3 M1'))
  cues=[(u['id'],'reveal' if u['mode']=='answer' else 'incident',[u['text']],[],0,dict(lines=[c['display'][j]],actors=shots[j]['actors'])) for j,u in enumerate(utterances)]
  save(p/'episode.json',dict(qid=c['qid'],answerHead=c['answer'],cues=cues))
  (p/'facts.md').write_text('# '+c['headline']+'\n\n채택 심급: '+c['court']+'. 선고와 구형을 구분한다. 기사 날짜를 선고 날짜로 채우지 않으며 화면에 사건 날짜를 표시하지 않는다.\n\n'+'\n'.join(f'- F{j+1}: {u["text"]} — sources: '+', '.join(s['id'] for s in sources) for j,u in enumerate(utterances[:6]))+'\n\n## 금지선\n피해자 실명·실제 외모 미사용. 고어·비웃음·희화화 없음. 1회 대표 동작은 횟수 재현이 아님. 재판부 이름·피고인 나이 생략.\n')
  (p/'script.md').write_text('[COLD_OPEN @ 0.000]\n[CENTRAL_QUESTION @ 0.000]\n'+'\n'.join(f'## {u["id"]} · {u["start_s"]:.3f}–{u["end_s"]:.3f}s · {u["mode"]}\n{u["text"]}\n화면: {c["label"][j]}' for j,u in enumerate(utterances))+'\n')
  (p/'meta.txt').write_text('[제목]\n'+c['title']+'\n\n[설명]\n댓글로 정답 먼저 → 마지막 선고를 보기 전에 예상 형량을 남겨 주세요.\n'+c['headline']+' 사건의 '+c['court']+' 선고를 묻습니다. 구형과 선고는 다릅니다.\n몇년나옴 #N — 업로드 번호는 CTO 배정 전입니다.\n판결 보도 기반 2D 재구성. 실제 현장 영상이 아니며 동작은 축약했습니다. 피해자 비식별. 내레이션: Supertonic 3 M1 AI 합성.\n다음 판결도 맞혀보세요 → 구독\n#몇년나옴 #판결 #shorts\n\n[출처]\n'+'\n'.join(s['publisher']+' | '+s['url'] for s in sources)+'\n\n[고정 댓글]\n정답 보기 전 예상 형량부터 댓글로! 다음 판결도 맞혀보세요 → 구독\n')
  print(c['qid'],duration,'s',min(u['sps'] for u in utterances),'sps',flush=True)
if __name__=='__main__':main()
