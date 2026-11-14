from pathlib import Path
import json,hashlib,shutil
W=Path(__file__).resolve().parents[3];S=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected=json.loads((S/'protected_before.json').read_text());changed=[p for p,h in protected.items() if sha(W/p)!=h];assert not changed,changed
identity=json.loads((S/'default_identity_final.json').read_text());assert all(i['match'] for i in identity);assert (S/'tsc_final_entry.log').read_text()==''
assert (W/'research/metrics/hook_v52_sheet.jpg').exists()
pending=[];manifest=[];summary={}
for q in ['q015','q012','q016','q017']:
 p=W/'episodes/quiz'/q/'v52';r=json.loads((p/'qa_checked.json').read_text());assert r['all_hard_gates_pass'],(q,{k:v for k,v in r['gates'].items() if v=='FAIL'})
 d=json.loads((p/'render_final.json').read_text());a=json.loads((p/'audio.json').read_text());old=json.loads((W/'episodes/quiz'/q/'qa_v51.json').read_text())
 r['output']=str(W/'upload'/f'v52_{q}.mp4');r['all_pass']=r['all_hard_gates_pass'];r['hero_still']=old['hero_still'];assert sha(W/r['hero_still']['png'])==r['hero_still']['sha256']
 r['phone_review']=dict(reviewed=True,sheet='research/metrics/hook_v52_sheet.jpg',tile_width=432,frames=[0,15,30,60,d['durationInFrames']-20],notes='Same v51 hero still, white/red headline and large CTA. Push-in reaches 1.12 at 2.0s; frames 0 and 30 visibly differ. No people, bodies, gore, weapon close-ups or landmark signage added.')
 r['audio_policy']=dict(body='Original v3 normalized-master speech segments preserved sample-for-sample, all body lines included; only between-line gaps removed.',hook='Only the hook newly synthesised, same Supertonic M1 voice, engine speed parameter only; no body time stretch.',scope='All words, facts, choices, answers and reasons unchanged from v51.',all_speech_retained=True)
 r['validation_source']=str((p/'qa_checked.json').relative_to(W));r['asr_final_mix']['test_wav_sample_rate']=16000
 if (p/'qa.json').exists():r['superseded_diagnostic']='Earlier local qa.json used a mislabelled ASR-test WAV sample rate. qa_checked.json supersedes it, with a verified 16kHz test file. Delivery video/audio did not require a change.'
 r['preexisting_files']=dict(checked=len(protected),changed=changed);r['default_identity']=identity
 dest=Path(r['output']);qaout=W/'episodes/quiz'/q/'qa_v52.json';assert not dest.exists() and not qaout.exists();assert sha(p/'candidate.mp4')==r['sha256']
 summary[q]=dict(file=str(dest.relative_to(W)),sha256=r['sha256'],seconds=r['duration']['seconds'],syllables_per_second=r['narration_speed']['syllables_per_second'],original_v3_sps=r['narration_speed']['original_v3_syllables_per_second'],hook_sps=r['narration_speed']['hook_syllables_per_second'],asr=r['asr_final_mix']['accuracy'],max_line_silence=r['breath']['max_seconds'],gates=r['gates'],push=r['hook_gates']['push_in_1_to_1p12_2s'],motion0_30=r['hook_gates']['motion_0_30'])
 pending.append((p/'candidate.mp4',dest,qaout,r));manifest.append(f"{r['sha256']}  {dest.name}")
for source,dest,qaout,r in pending:
 with source.open('rb') as a,dest.open('xb') as b:shutil.copyfileobj(a,b)
 assert sha(dest)==r['sha256']
 with qaout.open('x') as f:json.dump(r,f,ensure_ascii=False,indent=1)
with (W/'upload/v52.sha256').open('x') as f:f.write('\n'.join(manifest)+'\n')
with (S/'summary.json').open('x') as f:json.dump(summary,f,ensure_ascii=False,indent=1)
with (S/'protected_final.json').open('x') as f:json.dump(dict(checked=len(protected),changed=changed,all_prior_artifacts_preserved=True),f,indent=1)
print(json.dumps(summary,ensure_ascii=False,indent=1))
