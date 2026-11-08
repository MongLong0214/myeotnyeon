"""Align numeric script phrases to independent Whisper word timestamps."""
import json,difflib
from pathlib import Path
from asr import norm
P=Path(__file__).resolve().parent
d=json.loads((P/'episode_data.json').read_text());r=json.loads((P/'qa/asr_voice.json').read_text())
words=[w for s in r['segments'] for w in s.get('words',[])];chars=[];spans=[]
for w in words:
 text=norm(w['word']);dur=max(.01,w['end']-w['start'])
 for i,ch in enumerate(text):chars.append(ch);spans.append((w['start']+dur*i/len(text),w['start']+dur*(i+1)/len(text)))
expected=''.join(norm(c['text']) for c in d['captions']);recognized=''.join(chars);mapping={}
for block in difflib.SequenceMatcher(None,expected,recognized,autojunk=False).get_matching_blocks():
 for j in range(block.size):mapping[block.a+j]=spans[block.b+j]
pos=0;details=[]
for c in d['captions']:
 n=len(norm(c['text']));hit=[mapping[i] for i in range(pos,pos+n) if i in mapping];coverage=len(hit)/max(1,n)
 old=(c['startMs'],c['endMs'])
 if coverage>.78:
  c['startMs']=round(hit[0][0]*1000,2);c['endMs']=round(hit[-1][1]*1000,2);c['timestampMs']=c['startMs'];c['confidence']=round(coverage,4)
 details.append(dict(text=c['text'],coverage=coverage,old_ms=old,aligned_ms=[c['startMs'],c['endMs']]))
 pos+=n
for i,c in enumerate(d['captions']):
 if i+1<len(d['captions']):c['endMs']=min(c['endMs'],d['captions'][i+1]['startMs'])
 if c['endMs']<=c['startMs']:c['endMs']=c['startMs']+33.34
(P/'episode_data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
(P/'captions.json').write_text(json.dumps(d['captions'],ensure_ascii=False,indent=2))
(P/'qa/subtitle_alignment.json').write_text(json.dumps(dict(method='Sequence alignment of normalized Korean script graphemes to independent Whisper word timestamps; linear interpolation inside ASR words, not a phoneme aligner',matched_fraction=len(mapping)/len(expected),phrases=details),ensure_ascii=False,indent=2))
def stamp(t):
 ms=round(t);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(P/'subtitles.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['startMs'])} --> {stamp(c['endMs'])}\n{c['text']}" for i,c in enumerate(d['captions'])))
print('Aligned',len(d['captions']),'phrases; matched',len(mapping)/len(expected))
