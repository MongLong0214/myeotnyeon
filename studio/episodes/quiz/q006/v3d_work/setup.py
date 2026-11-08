from pathlib import Path
import json,hashlib
W=Path.cwd();P=W/'episodes/quiz/q006/v3d_work';old=P.with_name('v3c_work')
assert not (W/'upload/v3d_q006.mp4').exists()
paths=list((W/'upload').glob('*'))+list((W/'upload/preview').glob('*'))+list((W/'production/compositor/src').rglob('*'))+list((W/'production/compositor/public').rglob('*'))+list((W/'episodes/quiz/q006').glob('*'))+list((W/'episodes/quiz/out/v3').glob('*.py'))+[W/'episodes/quiz/episodes.py']
paths=[p for p in paths if p.is_file()]
(P/'protected_before.json').write_text(json.dumps({str(p.relative_to(W)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))
for f in ['render.cjs','strict.tsx','asr.py','sheets.py','finalize.py']:
 (P/f).write_text((old/f).read_text().replace('v3c','v3d'))
for f in ['episodes/quiz/episodes.py','production/compositor/public/q006/render.json']:
 p=W/f;b=p.read_bytes();assert b.count('우발적 범행'.encode())==1
 (P/(p.name+'.before')).write_bytes(b)
 p.write_bytes(b.replace('우발적 범행'.encode(),'우발적이었음'.encode()))
print('Only the target card bytes replaced in episodes.py and derived render.json; baseline hashes saved.')
