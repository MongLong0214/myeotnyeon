"""Normalize numeral phrases across Whisper word boundaries, keeping measured times.
Existing clock normalized each token separately, e.g. '700만' + '원에', so
multiword episode lexicon entries were missed. Thresholds are unchanged.
"""
import re,difflib
import numpy as np
def character_clock(asr,norm):
 chars=[];starts=[];ends=[]
 for seg in asr['segments']:
  for w in seg.get('words',[]):
   raw=re.sub(r'[^가-힣0-9A-Za-z]','',w['word'])
   for i,c in enumerate(raw):
    chars.append(c);starts.append(w['start']+(w['end']-w['start'])*i/len(raw));ends.append(w['start']+(w['end']-w['start'])*(i+1)/len(raw))
 raw=''.join(chars);normalized=norm(raw);ss=np.zeros(len(normalized));ee=np.zeros(len(normalized))
 for tag,a,b,c,d in difflib.SequenceMatcher(None,raw,normalized,autojunk=False).get_opcodes():
  if d==c:continue
  if tag=='equal':ss[c:d]=starts[a:b];ee[c:d]=ends[a:b]
  else:
   start=starts[min(a,len(starts)-1)];end=ends[min(max(a,b-1),len(ends)-1)]
   bounds=np.linspace(start,end,d-c+1);ss[c:d]=bounds[:-1];ee[c:d]=bounds[1:]
 return normalized,ss,ee
