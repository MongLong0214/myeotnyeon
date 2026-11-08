from pathlib import Path
import json,re,hashlib
W=Path.cwd();Q=W/'episodes/quiz/q006';P=Q/'v3d_work';old=Q/'v3c_work'
# Extract exact all-frame reports from the unchanged v3c audit engines.
strict={}
for line in (P/'strict_full.log').read_text().splitlines():
 m=re.search(r'TYPE2CHECK (\{.*\}) END',line)
 if m:
  v=json.loads(m[1]);strict[v['frame']]=v
assert set(strict)==set(range(998)),len(strict)
(P/'strict_frames.json').write_text(json.dumps([strict[f] for f in range(998)],ensure_ascii=False,indent=2))
audit={}
for line in (P/'audit_full.log').read_text().splitlines():
 m=re.search(r'AUDIT q006 f=(\d+) n=.*? END',line)
 if m:audit[int(m[1])]=m[0]
assert set(audit)==set(range(998)),len(audit)
(Q/'audit_v3d/q006.txt').write_text('\n'.join(audit[f] for f in range(998))+'\n')
identity=[]
for f in [90,570,850]:
 b=hashlib.sha256((old/f'default_after/{f}.png').read_bytes()).hexdigest();a=hashlib.sha256((P/f'default_after/{f}.png').read_bytes()).hexdigest();identity.append(dict(frame=f,before_sha256=b,after_sha256=a,match=b==a))
(P/'default_identity.json').write_text(json.dumps(identity,indent=2))
# The single derived card string is the only expected composition props change.
before=(old/'compositions_after.json').read_text();after=(P/'compositions_after.json').read_text()
(P/'composition_comparison.json').write_text(json.dumps(dict(before_count=len(json.loads(before)),after_count=len(json.loads(after)),metadata_equal_except_authorized_card=before.replace('우발적 범행','우발적이었음')==after,card_text_replacements=before.count('우발적 범행')),indent=2))
(P/'compositions_before.json').write_text(before.replace('우발적 범행','우발적이었음'))
# Input protection includes every pre-existing upload and narration source.
b=json.loads((P/'protected_before.json').read_text());changed=[]
for f,h in b.items():
 p=W/f
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:changed.append(f)
(P/'protection_after.json').write_text(json.dumps(dict(checked=len(b),changed=changed),indent=2))
for f,backup in [('episodes/quiz/episodes.py','episodes.py.before'),('production/compositor/public/q006/render.json','render.json.before')]:
 assert (W/f).read_bytes()==(P/backup).read_bytes().replace('우발적 범행'.encode(),'우발적이었음'.encode())
print('strict',len(strict),'audit',len(audit),'default stills',identity,'changes',changed)
