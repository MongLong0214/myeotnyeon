import sys, json, glob, os, re
import mlx_whisper
M=next(glob.iglob(__import__('os').path.expanduser('~/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots/*/')))
def norm(t): return re.sub(r'[^가-힣0-9a-zA-Z]','',t)
def cer(r,h):
    r,h=norm(r),norm(h); d=list(range(len(h)+1))
    for i,c in enumerate(r,1):
        p=d[:]; d[0]=i
        for j,k in enumerate(h,1): d[j]=min(p[j]+1,d[j-1]+1,p[j-1]+(c!=k))
    return d[-1]/max(1,len(r))
def wer(r,h):
    r=[norm(w) for w in r.split()]; h=[norm(w) for w in h.split()]
    d=list(range(len(h)+1))
    for i,c in enumerate(r,1):
        p=d[:]; d[0]=i
        for j,k in enumerate(h,1): d[j]=min(p[j]+1,d[j-1]+1,p[j-1]+(c!=k))
    return d[-1]/max(1,len(r))
if sys.argv[1]=='lines':
    take=sys.argv[2]
    for l in json.load(open('lines.json')):
        f=f'audio/{l["id"]}_t{take}.wav'
        if not os.path.exists(f): continue
        h=mlx_whisper.transcribe(f,path_or_hf_repo=M,language='ko')['text'].strip()
        print(l['id'],'cer=%.3f'%cer(l['tts'],h),'|',h)
else:
    ref=' '.join(l['tts'] for l in json.load(open('lines.json')))
    h=mlx_whisper.transcribe(sys.argv[2],path_or_hf_repo=M,language='ko')['text'].strip()
    print('WER=%.3f CER=%.3f'%(wer(ref,h),cer(ref,h))); print(h)
