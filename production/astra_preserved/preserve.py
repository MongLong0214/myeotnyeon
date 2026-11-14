import json,shutil,hashlib
from pathlib import Path
import numpy as np,soundfile as sf
R=Path('/Users/isaac/projects/verdict-kr/work');P=R/'production/astra_preserved';parts=[]
d=json.loads((R/'episodes/v4/n18/astra_12min/n18_full_narration_cues.json').read_text());sr=d['sample_rate']
for i,c in enumerate(d['cues']):
 a,s=sf.read(c['audio']);assert s==sr;parts.append(a)
 if i<len(d['cues'])-1:parts.append(np.zeros(round(sr*.17)))
sf.write(P/'n18_partial_narration.wav',np.concatenate(parts),sr);print('N18 preserved partial',sum(map(len,parts))/sr)
for f in ['render.py','representatives.json','synthesize.py','narration_additions.json','render_verification.json','representatives_asr.json']:
 shutil.copy2(R/'production/astra_12min'/f,P/f)
for ep,name in [('lf2_daejeon_bank','lf2'),('v4/n18','n18')]:
 out=P/name;out.mkdir(exist_ok=True);source=R/'episodes'/ep/'astra_12min'
 for f in source.glob('*new_animation_r2*'):shutil.copy2(f,out/f.name)
 for f in source.glob('*full_narration*'):shutil.copy2(f,out/f.name)
 for f in source.glob('*_cues.json'):
  if 'full' not in f.name:shutil.copy2(f,out/f.name)
 ad=out/'audio';ad.mkdir(exist_ok=True)
 cues=json.loads((source/f'{name}_full_narration_cues.json').read_text())['cues']
 for c in cues:shutil.copy2(c['audio'],ad/Path(c['audio']).name)
 print('preserved',out)
manifest=[dict(path=str(f.relative_to(P)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in P.rglob('*') if f.is_file() and f.name!='preservation_manifest.json']
(P/'preservation_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('preserved files',len(manifest))
