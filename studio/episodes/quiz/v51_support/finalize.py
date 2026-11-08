from pathlib import Path
import json,hashlib,shutil,sys,re
from PIL import Image
W=Path(__file__).resolve().parents[3];S=Path(__file__).parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 identity=json.loads((S/'default_identity.json').read_text());assert all(i['match'] for i in identity)
 protected=json.loads((S/'protected.json').read_text());changed=[p for p,h in protected.items() if sha(W/p)!=h];assert not changed,changed
 for row in (W/'upload/v5.sha256').read_text().splitlines():
  h,name=row.split();assert sha(W/'upload'/name)==h
 assert (S/'tsc.log').read_text()==''
 pending=[];manifest=[];summary={}
 for q in ['q015','q012','q016','q017']:
  p=W/'episodes/quiz'/q/'v51';r=json.loads((p/'qa.json').read_text());assert r['all_hard_gates_pass'],(q,{k:v for k,v in r['gates'].items() if v=='FAIL'})
  still=W/'research/hook_stills'/f'{q}.png';assert Image.open(still).size==(1080,1920)
  r['hero_still']=dict(png=str(still.relative_to(W)),jpeg=f'research/hook_stills/{q}.jpg',sha256=sha(still),width=1080,height=1920,source='Blender CLI EEVEE, local CC0 Poly Haven assets + world2 procedural environments',visual_review='Environment only; no people, faces, victims, gore, close-up weapons, real landmark signage. Wet ground / thin haze / restrained teal and warm grade, bloom, grain, vignette.' if q!='q012' else 'Night ridge, wildfire glow, smoke haze and airborne embers. Environment only; no people, faces, victims, gore, real landmark signage.')
  old=json.loads((W/'episodes/quiz'/q/'audio/na/index.json').read_text());count=sum(len(re.findall('[가-힣]',i['tts_text'])) for i in old['items']);sec=sum(i['dur'] for i in old['items'])
  r['narration_speed']['original_cached_narration_sps']=count/sec
  r['narration_speed']['scope_note']='All narration re-synthesised in M1. Explicit target 6.2–6.6 sps prioritised. The original cached narration was already 7.5–8.05 sps, so faster-than-original articulation is incompatible with this numeric target and is not claimed.'
  r['phone_review']=dict(reviewed=True,sheet='research/metrics/hook_v51_sheet.jpg',comparison='research/metrics/hook_v3_v5_v51_q016.jpg',tile_width=432,frames=[0,15,30,60,int(round(r['duration']['seconds']*30))-20])
  r['owner_instruction_conflicts']=dict(hook='v5 cut at frame 61 (2.033s) retained. 75-frame 1→1.10 camera curve exists; full 2.5s hero exposure was not applied.',narration='Numeric 6.2–6.6 syllables/s target chosen; faster-than-original articulation not achieved because original rate was already above that target. Inter-line silence and animation holds shortened.')
  r['all_pass']=r['all_hard_gates_pass'];r['output']=str(W/'upload'/f'v51_{q}.mp4')
  dest=Path(r['output']);out=W/'episodes/quiz'/q/'qa_v51.json';assert not dest.exists() and not out.exists();assert sha(p/'candidate.mp4')==r['sha256']
  pending.append((p/'candidate.mp4',dest,out,r));manifest.append(f"{r['sha256']}  {dest.name}")
  summary[q]=dict(path=str(dest.relative_to(W)),sha256=r['sha256'],seconds=r['duration']['seconds'],syllables_per_second=r['narration_speed']['syllables_per_second'],blender_render_seconds=r['blender']['render_seconds'],gates=r['gates'],asr_accuracy=r['asr_final_mix']['accuracy'],max_subtitle_start_error_ms=r['subtitle_sync']['max_start_error_ms'],max_subtitle_end_error_ms=r['subtitle_sync']['max_end_error_ms'],max_band_pixels=r['hook_gates']['no_empty_band_0_60']['max_band_pixels'],glyph_height=r['hook_gates']['headline_glyph_height']['min_pixels'],cta_ratio=r['hook_gates']['cta_fills_half_frame']['min_ratio'])
 for src,dest,out,r in pending:
  with src.open('rb') as a,dest.open('xb') as b:shutil.copyfileobj(a,b)
  assert sha(dest)==r['sha256']
  out.write_text(json.dumps(r,ensure_ascii=False,indent=1))
 with (W/'upload/v51.sha256').open('x') as f:f.write('\n'.join(manifest)+'\n')
 (S/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=1));(S/'protected_final.json').write_text(json.dumps(dict(checked=len(protected),changed=changed,v5_manifest_verified=True,default_identity=True),indent=2));print(json.dumps(summary,ensure_ascii=False,indent=1))
if __name__=='__main__':main()
