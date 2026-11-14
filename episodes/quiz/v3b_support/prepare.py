"""Apply the approved premium timing to the five explicitly selected episodes."""
import ast, copy, json, pathlib, pprint, re, sys
W=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(W/'episodes/quiz'))
import episodes, make
P=W/'episodes/quiz/episodes.py'
s=P.read_text();tree=ast.parse(s)
ids=['q007','q008','q009','q010','q012']
# Concise evidence captions keep 84px serif type on one line, inside the phone rail.
cards={
'q007':[('피해 성격','보증금은 전 재산'),('피해 규모','피해자 500여 명')],
'q008':[('범행 후 태도','범행 인정·반성'),('피해 회복','유족과 합의'),('피해 회복','업무방해 공탁')],
'q009':[('범행 수법','매우 잔혹한 수법'),('범행 후 태도','진정한 반성 없음')],
'q010':[('배심원 의견','5명은 30년 의견'),('범행 후 태도','반성 없는 태도')],
'q012':[('불리한 사정','결과가 매우 무거움'),('죄명','실화·과실로 낸 불'),('2심 검찰 구형','징역 3년')],
}
orders={'q007':['C1','C2','C6','C3','C5','C4','C7'],'q008':['C1','C2','C3','C4','C6','C5','C7'],'q009':['C1','C2','C3','C4','C6','C5','C7','C8'],'q010':['C1','C2','C3','C7','C4','C6','C5','C8']}
# A comma after a connective ending is punctuation only; spoken words and source facts stay unchanged.
def punct(x):
 return re.sub(r'((?:고|며|지만|면서|아서|어서|는데|은데|던데|[가-힣]자))\s*,',r'\1',x)
replacements=[]
for eid in ids:
 ep=copy.deepcopy(episodes.EPISODES[eid])
 # q012 is stored before _hook inserts its first narration sentence.
 if eid=='q012':
  ep=copy.deepcopy(episodes.NEW[eid])
 ep['quizStyle']='premium'
 cues={c[0]:list(c) for c in ep['cues']}
 qid={'q007':'C3','q008':'C4','q009':'C4','q010':'C4','q012':'CQ'}[eid]
 if eid=='q012':
  old=cues['C5'];old[2]=old[2][1:];old[5]['cardFrom']=1
  ep['split'].pop('C5_1',None)
  for i in range(1,4):ep['split'][f'C5_{i}']=ep['split'].pop(f'C5_{i+1}')
  cues[qid]=[qid,'quiz',['자, 몇 년 받았을까요?'],[],0.3,{}]
  order=['C1','C2','C3','C4',qid,'C5','C6','C7']
 else:
  cues[qid][2]=cues[qid][2][:1];cues[qid][4]=0.3;order=orders[eid]
  ep.get('split',{}).pop(f'{qid}_2',None)
 reason={'q007':'C5','q008':'C6','q009':'C6','q010':'C6','q012':'C5'}[eid]
 cues[reason][1]='weigh'
 cues[reason][5]={'cards':[dict(tag=a,text=b) for a,b in cards[eid]],'cardAt':{'q007':[0,65],'q008':[0,50,97],'q009':[0,130],'q010':[0,115],'q012':[0,'s2','s3']}[eid]}
 # cardAt can reference measured sentence anchors; make.resolve supports cardAt below.
 if eid=='q012':cues[reason][5]={'cards':[dict(tag=a,text=b) for a,b in cards[eid]],'cardFrom':1}
 if eid=='q007':
  # Other defendants' sentences are not the answer to this quiz (the main defendant).
  cues['C6'][5]['tags']=[t for t in cues['C6'][5]['tags'] if '주범' not in t['text']]
 if eid=='q009':
  # Preserve the post-verdict arrest account. Allow reading time for both evidence cards.
  cues[reason][4]=6.5
 for c in cues.values():
  c[2]=[punct(t) for t in c[2]]
  if c[1]=='incident':c[5]['punch']=list(range(30,390,36))
  if c[1]=='outro':c[4]=0.2;c[5]={'staged':True,'logoAt':14,'punch':[30]}
  if c[1]=='reveal':c[4]=0.2
 # Preserve all legal details in the verdict, keeping the large first line uncluttered.
 if eid=='q010':cues['C5'][5]={'lines':['징역 25년','1심 선고'],'legal':'검찰 구형 20년보다 무거움'}
 if eid=='q012':cues['C6'][5]={'lines':['징역 2년 6개월','집행유예 3년'],'legal':'1심 선고','legalAfter':{'s':2,'text':'2심 유지 · 검찰 항소 기각'},'headAt':2}
 if eid=='q007':cues['C4'][5]['legal']='법정 최고형 · 대법원 확정'
 if eid=='q009':cues['C5'][5]['legal']='1심 집행유예 → 2심 실형'
 ep['cues']=[tuple(cues[k]) for k in order]
 ep['split']={k:[punct(t) for t in v] for k,v in ep.get('split',{}).items()}
 # Replace only the literal belonging to this episode, preserving every other entry byte-for-byte.
 for node in ast.walk(tree):
  if isinstance(node,ast.Dict):
   for k,v in zip(node.keys,node.values):
    if isinstance(k,ast.Constant) and k.value==eid:
     lines=s.splitlines(keepends=True);start=sum(map(len,lines[:v.lineno-1]))+v.col_offset;end=sum(map(len,lines[:v.end_lineno-1]))+v.end_col_offset
     replacements.append((start,end,pprint.pformat(ep,width=140,sort_dicts=False)))
for a,b,t in sorted(replacements,reverse=True):s=s[:a]+t+s[b:]
P.write_text(s)
