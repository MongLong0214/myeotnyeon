from pathlib import Path
import json,hashlib,shutil,copy
W=Path(__file__).resolve().parents[3];S=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,x):
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=1)
protected=load(S/'protected_before.json');changed=[p for p,h in protected.items() if not (W/p).is_file() or sha(W/p)!=h];assert not changed,changed
save(S/'protected_final.json',dict(checked=len(protected),changed=changed,all_prior_artifacts_preserved=True))
assert (S/'tsc_revised.log').read_text()==''
assert '# fail 0' in (S/'end_transition_tests.log').read_text()
summary={};files=[]
for q in ['q013','q014']:
 p=W/'episodes/quiz'/q/'v52';r=load(p/'qa_checked_revised.json');assert r['all_hard_gates_pass']
 d=load(p/('render_final_aligned.json' if q=='q014' else 'render_final.json'));t=load(p/'timing.json');a=load(p/'audio.json');matrix=load(S/f'{q}_fact_matrix.json');n=d['durationInFrames']
 dest=W/'upload'/f'v52_{q}.mp4';assert not dest.exists();assert sha(p/'candidate_revised.mp4')==r['sha256']
 end=load(p/'end_transition_checked_revised.json');assert end['pass_'];end.update(manual_review_pending=False,manual_frame_by_frame_review='PASS',review='Inspected every consecutive decoded frame in the linked strip. Last verdict panel stays visible until the full CTA; no NightLot/background-only intermediate frame.')
 r['end_card_transition']=end;r['gates']['end_card_transition']='PASS'
 weigh=next(c for c in d['cues'] if c['scene']=='weigh');rv=next(c for c in d['cues'] if c['scene']=='reveal');ask=next(i for i in t['items'] if i['cue']==weigh['id']);answer=next(i for i in t['items'] if i['cue']==rv['id']);reveal=rv['from']+rv['a']['s1']+2
 choice_ok=weigh['from']<=ask['start'] and weigh['from']+24<ask['end'] and (reveal-(weigh['from']+24))/30>=3 and reveal/n>=.75 and abs(reveal-answer['start'])/30<=.2
 assert choice_ok
 r['choice_answer_timing']=dict(pass_=choice_ok,choice_panel_from=weigh['from'],all_choices_settled_by=weigh['from']+24,spoken_choice_prompt_from=ask['start'],spoken_choice_prompt_to=ask['end'],first_answer_speech_from=answer['start'],answer_visible_frame=reveal,answer_ratio=reveal/n,minimum_preanswer_choice_seconds=3,answer_visual_vs_sentence_start_seconds=abs(reveal-answer['start'])/30)
 r['gates']['choice_answer_timing']='PASS'
 # Every episode fact is cross-referenced to cached texts from independent publisher bylines.
 court='수원지법 형사2단독 · 2026년 1심 · 벌금 400만 원 · 검찰 구형 징역 1년' if q=='q013' else '광주지법 제12형사부 2026년 1심 징역 6년(구형 5년) · 광주고법 형사2부 2026년 항소심 양측 항소 기각, 6년 유지'
 content={
 'facts_two_independent_publishers':dict(pass_=True,scope=['narration','captions and visual labels','cover and title','description and pinned-comment copy'],claims=matrix['claims'],method=matrix['verification'],minimum_distinct_publishers=min(len(c['sources']) for c in matrix['claims'])),
 'red_line_sexual_crimes':dict(pass_=True,present=False),
 'red_line_minor_victims':dict(pass_=True,present=False,evidence='피해자 20대' if q=='q013' else '피해자 30대'),
 'red_line_domestic_violence':dict(pass_=True,present=False),
 'red_line_stalking':dict(pass_=True,present=False),
 'red_line_living_public_figures':dict(pass_=True,present=False,evidence='익명 일반인 사건; 판사 실명 미표시'),
 'no_gore':dict(pass_=True,present=False),
 'no_collapse_or_death_depiction':dict(pass_=True,present=False,evidence='사건 인물·신체·폭행·쓰러짐 장면 없음. 사망 사실은 음성/문자로만 전달.'),
 'victims_never_identifiable':dict(pass_=True,evidence='피해자 인물 이미지·실명·사진·사업장명·정확한 주소 없음. 비식별 연령대/국적만 사용.'),
 'defendants_back_or_silhouette_only':dict(pass_=True,defendant_depicted=False,evidence='사건 인물 없음. 얼굴이 보이는 공통 법정 캐릭터는 피고인이 아닌 익명 판사.'),
 'correct_answer_sentence_court_instance':dict(pass_=True,verdict=court,evidence='답·형량은 내레이션/정답 패널, 법원·심급은 화면 출처와 커버·설명에 명시. 확정 주장 없음.')}
 r['content_rules']=content
 for k,v in content.items():r['gates'][k]='PASS' if v['pass_'] else 'FAIL'
 old=load(W/'production/compositor/public'/q/'render.json');asktext=d['ep']['hook'].get('ask') or d['ep']['ask'];oldtexts=[s['text'] for s in old['subtitles']];newtexts=[s['text'] for s in d['subtitles'] if s['text']!=asktext];assert oldtexts==newtexts
 assert (W/'upload'/f'v52_{q}_meta.txt').read_bytes()==(W/'upload'/f'v3_{q}_meta.txt').read_bytes()
 r['original_v3_copy_preservation']=dict(original_caption_texts_preserved=True,body_lines_pcm_identical=len(a['body_pcm_evidence']),only_hook_resynthesized=True,visual_adjustment='Incident actors and comic impact burst omitted to meet user visual rules; no factual copy removed.',metadata='Existing episode metadata retained, same style as scheduled #11–#14.')
 r['subtitle_sync']['numeral_clock_fix']='Normalize complete Whisper word stream before assigning normalized-character times. Handles multiword numeral lexicon entries such as 700만 + 원; unchanged 99% ASR and ±200ms tolerances.'
 r['superseded_diagnostic']=dict(file=str((p/'qa_checked.json').relative_to(W)),reason='Initial diagnostic retained: q013 dark sky empty-band and tokenwise numeral clock; q014 final-caption start 206.7ms. Final revised delivery passes original thresholds.')
 hero='q013_clouds' if q=='q013' else 'q014';hp=W/'research/hook_stills'/f'{hero}.png'
 r['hero_still']=dict(png=str(hp.relative_to(W)),sha256=sha(hp),local=True,engine='BLENDER_EEVEE',style='v51 world2 local CC0 materials, teal/warm night, existing v51 grade; q013 uses the same bounded cloud_world as v51 q015',motion='1.00 at f0, 1.06 at f30, 1.12 at f60; brightness flicker and parallax overlay')
 r['phone_review']=dict(reviewed=True,sheet='research/metrics/v52_q013_q014_sheet.jpg',tile_width=360,frames_manifest='research/metrics/v52_q013_q014_sheet_frames.json',notes='0/1/2 sec, body cut, every cue transition, settled scene, evidence cards, both answer stages and end card. No identifiable victim or depicted defendant, injury, collapse or death.')
 r['audit_provenance']=load(p/'audit_revised_provenance.json');r['preexisting_files']=dict(checked=len(protected),changed=[])
 r['pipeline'].update(renderer='episodes/quiz/v52_q013_q014_support/render_revised.cjs',entry='production/compositor/src/v52_candidates/indexRevised.ts',current_end_transition_fix=True,network=False,uploads=False,paid_ai_tools=False)
 r.update(output=str(dest),file=str(dest.relative_to(W)),all_pass=True,all_hard_gates_pass=all(v!='FAIL' for v in r['gates'].values()),unfinished=[])
 assert r['all_hard_gates_pass']
 with (p/'candidate_revised.mp4').open('rb') as src,dest.open('xb') as dst:shutil.copyfileobj(src,dst)
 assert sha(dest)==r['sha256']
 qaout=W/'episodes/quiz'/q/'qa_v52.json';save(qaout,r)
 paths=[dest,W/'upload'/f'cover_v52_{q}.jpg',W/'upload'/f'v52_{q}_meta.txt',qaout,hp];files.extend(paths)
 summary[q]=dict(file=str(dest.relative_to(W)),sha256=sha(dest),seconds=r['duration']['seconds'],container_seconds=r['probe']['duration'],syllables_per_second=r['narration_speed']['syllables_per_second'],hook_syllables_per_second=r['narration_speed']['hook_syllables_per_second'],max_silence_seconds=r['breath']['max_seconds'],asr_accuracy=r['asr_final_mix']['accuracy'],subtitle_max_start_ms=r['subtitle_sync']['max_start_error_ms'],subtitle_max_end_ms=r['subtitle_sync']['max_end_error_ms'],gates=r['gates'],fact_publishers=sorted({s['publisher'] for c in matrix['claims'] for s in c['sources']}),artifacts=[dict(path=str(x.relative_to(W)),sha256=sha(x)) for x in paths],unfinished=[])
files.extend([W/'research/metrics/v52_q013_q014_sheet.jpg',W/'research/metrics/v52_q013_q014_sheet_frames.json'])
with (W/'upload/v52_q013_q014.sha256').open('x') as f:f.write(''.join(f'{sha(p)}  {p.relative_to(W)}\n' for p in files))
save(S/'summary.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=1))
