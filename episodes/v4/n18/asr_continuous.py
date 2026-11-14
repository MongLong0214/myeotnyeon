from asr_cpu import *
import argparse
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--output',default='out/asr_continuous.json');a=p.parse_args()
print('PID',os.getpid(),flush=True)
m=load();start=time.time()
# Full 30-second context: the normal Whisper transcribe path, no script prompt.
r=m.transcribe(a.input,language='ko',fp16=False,temperature=0,condition_on_previous_text=False,verbose=False)
D=json.loads((E/'shots.json').read_text());expected=' '.join(x['text'] for x in D['narration']);errors,characters=distance(expected,r['text'])
result=dict(model='existing cached whisper-large-v3-turbo',backend='CPU',normalization='explicit lex.json number readings; whitespace/punctuation; abbreviated years expanded only in complete dates matched to adopted facts',initial_prompt=None,match=1-errors/characters,errors=errors,characters=characters,text=r['text'],segments=r['segments'],seconds=time.time()-start)
(E/a.output).write_text(json.dumps(result,ensure_ascii=False,indent=1));print('MATCH',result['match'],flush=True)
