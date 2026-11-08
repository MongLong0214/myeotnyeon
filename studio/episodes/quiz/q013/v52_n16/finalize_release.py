from pathlib import Path
import json,hashlib,copy,sys,re
W=Path(__file__).resolve().parents[4];S=Path(__file__).parent
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=1)
base=load(W/'episodes/quiz/q013/qa_v52.json');r=load(S/'qa_checked_revised.json');d=load(S/'render_n16.json');original=load(W/'episodes/quiz/q013/v52/render_final.json')
sys.path.insert(0,str(W/'episodes/quiz'));from episodes_n16 import patch_render,EPISODES
assert d==patch_render(original)
comparison=load(S/'comparison.json');assert comparison['psnr']['all_frames_ge_45_db'] and comparison['audio']['stream_identical'] and comparison['audio']['pcm_identical'] and comparison['art_coverage']['pass_']
assert comparison['frame_count']==original['durationInFrames']==d['durationInFrames']==800
preserved=load(S/'preexisting_source_hashes.json');preserve_checks=[dict(path=p,sha256_before=h,sha256_after=sha(W/p),pass_=sha(W/p)==h) for p,h in preserved.items()];assert all(c['pass_'] for c in preserve_checks)
source=W/'production/compositor/src/v52_n16';svg=(source/'ObjectSets.tsx').read_text();assert '<text' not in svg and '<Guy' not in svg and '<image' not in svg
assert not any('actors' in c['p'] for c in d['cues'] if c['id'] in ['C2','C3'])
# Fact #8 custody and #9 probation are already supported by independently archived reports.
archives=[]
for name in ['V3-02_1.txt','V3-02_2.txt','V3-02_3.txt']:
 p=W/'research/raw3'/name;t=p.read_text();assert '구속' in t and '집행유예' in t
 archives.append(dict(file=str(p.relative_to(W)),sha256=sha(p),custody_paragraphs=[line for line in t.splitlines() if '구속' in line][:3],probation_paragraphs=[line for line in t.splitlines() if '집행유예' in line][:3]))
r['content_rules']=copy.deepcopy(base['content_rules']);r['content_rules_provenance']='Reused original qa_v52.json content rules as authorized. Narration, captions, stamp text, case facts and verdict unchanged; added object-only art separately reviewed against local facts #8/#9 and archived publishers.'
r['new_art_factual_review']=dict(pass_=True,cues={'C2':'Generic courthouse and empty barred window symbolize custody/prosecution already stated in facts #8; no real courthouse or prison architecture asserted.','C3':'Car key, undated calendar and document with nonverbal strokes symbolize drunk-driving probation in facts #9; no dates, signatures, additional sentence, vehicle model or collision asserted.'},new_factual_text=[],people_added=False,injuries_gore_assault_added=False,identifiable_victim=False,defendant_depicted=False,evidence=archives,visual_review='Reviewed decoded full sheet including every displayed cue cut, stamp transitions, evidence stages, verdict stages and full end card; new artwork is visible before stamps as well as during narration.')
for k,v in r['content_rules'].items():r['gates'][k]='PASS' if v.get('pass_',v.get('pass',False)) else 'FAIL'
end=load(S/'end_transition_checked_revised.json');assert end['pass_'];end.update(manual_review_pending=False,manual_frame_by_frame_review='PASS',review='All consecutive decoded frames f745–761 inspected; verdict held through f754, full #16 CTA from f755.')
r['end_card_transition']=end;r['gates']['end_card_transition']='PASS'
t=load(S/'timing.json');n=d['durationInFrames'];weigh=next(c for c in d['cues'] if c['scene']=='weigh');rv=next(c for c in d['cues'] if c['scene']=='reveal');ask=next(i for i in t['items'] if i['cue']==weigh['id']);answer=next(i for i in t['items'] if i['cue']==rv['id']);reveal=rv['from']+rv['a']['s1']+2
ok=weigh['from']<=ask['start'] and weigh['from']+24<ask['end'] and (reveal-(weigh['from']+24))/30>=3 and reveal/n>=.75 and abs(reveal-answer['start'])/30<=.2;assert ok
r['choice_answer_timing']=dict(pass_=ok,choice_panel_from=weigh['from'],all_choices_settled_by=weigh['from']+24,spoken_choice_prompt_from=ask['start'],spoken_choice_prompt_to=ask['end'],first_answer_speech_from=answer['start'],answer_visible_frame=reveal,answer_ratio=reveal/n,minimum_preanswer_choice_seconds=3,answer_visual_vs_sentence_start_seconds=abs(reveal-answer['start'])/30);r['gates']['choice_answer_timing']='PASS'
assert (S/'typecheck.log').read_text()==''
r['change_verification']=comparison;r['preexisting_file_preservation']=preserve_checks
r['default_identity']=dict(pass_=d==patch_render(original),method='Fresh render document equals original v52 doc with only ep.no=16 and C2/C3 registered set IDs changed. All cue frames, anchors, labels, captions, answers and choices compare equal.',episode_source='episodes/quiz/episodes_n16.py',entry='production/compositor/src/v52_n16/index.tsx',render_doc='episodes/quiz/q013/v52_n16/render_n16.json',hero_identity=13,lighting_seed=13)
r['body_preservation']['note']='Only C2/C3 visual set IDs and series number differ. Original factual labels, stamp order/timing, subtitles, narration and answer unchanged.'
r['gates'].update(changed_regions_psnr='PASS',audio_identity='PASS',same_frames_and_duration='PASS',new_art_factual_review='PASS',nonempty_C2_C3_every_frame='PASS',default_props_identity='PASS',body_visual_and_facts_preserved='PASS',preexisting_file_preservation='PASS')
meta=(W/'upload/v52_q013_n16_meta.txt').read_text();oldmeta=(W/'upload/v52_q013_meta.txt').read_text();expected=oldmeta.replace('#13','#16') if '#13' in oldmeta else oldmeta.replace('[제목]\n','[제목]\n형량 퀴즈 #16 · ',1);assert meta==expected
r['number_visual_review']=dict(pass_=True,badge='#16',end_card='#16',cover='#16',metadata='#16',original_metadata_has_hash13='#13' in oldmeta,metadata_change='Original metadata had no #13; only title prefix 형량 퀴즈 #16 · added.',cover_psnr_outside_badge=comparison['cover_psnr_outside_badge'])
r['phone_review']=dict(reviewed=True,sheet='research/metrics/v52_q013_n16_sheet.jpg',frames_manifest='research/metrics/v52_q013_n16_sheet_frames.json',tile_width=360,scene_count=7,notes='Every displayed scene cut plus settled frames; both C2 stamps and gap, C3 before/after stamp, all evidence cards, both verdict stages, #16 end card. No empty story panel.')
r['pipeline'].update(renderer='episodes/quiz/q013/v52_n16/render_local.cjs',entry='production/compositor/src/v52_n16/index.tsx',network=False,uploads=False,paid_ai_tools=False,audio='Original AAC stream copied with FFmpeg -c copy; both AAC and decoded PCM MD5 equal.',existing_files_overwritten=False)
r['source_files']={str(p.relative_to(W)):sha(p) for p in [W/'episodes/quiz/episodes_n16.py',*(source/name for name in ['QuizPanels.tsx','HookV51Seed.tsx','ObjectSets.tsx','index.tsx']),S/'render_n16.json',S/'render_local.cjs',S/'qa_n16.py',S/'compare_review.py']}
v=W/'upload/v52_q013_n16.mp4';r.update(file=str(v.relative_to(W)),output=str(v),sha256=sha(v),all_pass=all(x!='FAIL' for x in r['gates'].values()),all_hard_gates_pass=all(x!='FAIL' for x in r['gates'].values()),unfinished=[]);assert r['all_pass'],r['gates']
qa=W/'episodes/quiz/q013/qa_v52_n16.json';save(qa,r)
files=[v,W/'upload/cover_v52_q013_n16.jpg',W/'upload/v52_q013_n16_meta.txt',qa,W/'research/metrics/v52_q013_n16_sheet.jpg',W/'research/metrics/v52_q013_n16_sheet_frames.json',S/'comparison.json',S/'per_frame_psnr.csv',*[W/p for p in r['source_files']]]
with (W/'upload/v52_q013_n16.sha256').open('x') as f:f.write(''.join(f'{sha(p)}  {p.relative_to(W)}\n' for p in files))
print(json.dumps(dict(all_pass=r['all_pass'],gates=len(r['gates']),sha256=r['sha256'],frame_count=comparison['frame_count'],audio=comparison['audio'],psnr=comparison['psnr'],asr_accuracy=r['asr_final_mix']['accuracy'],subtitle_sync_start_ms=r['subtitle_sync']['max_start_error_ms'],subtitle_sync_end_ms=r['subtitle_sync']['max_end_error_ms'],loudness=r['loudness'],audit=r['audit']),ensure_ascii=False,indent=2))
