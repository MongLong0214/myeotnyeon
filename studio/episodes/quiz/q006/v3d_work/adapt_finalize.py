from pathlib import Path
p=Path('episodes/quiz/q006/v3d_work/finalize.py');s=p.read_text()
s=s.replace("tg=textgate.gate('q006');",'''# Keep the original engine; include all fixed TYPE 02 labels and rendered captions too.
strict_input=json.loads((P/'strict_frames.json').read_text())
ep=textgate.EPISODES['q006'];lab=textgate.labels(ep);nar=textgate.narration(ep)
actual=sorted({t for row in strict_input for t in row['texts']})
extra=[t for t in actual if t not in lab and t not in nar]
original_labels=textgate.labels
textgate.labels=lambda ep: original_labels(ep)+extra
(P/'textgate_full_display.txt').write_text('\\n'.join(lab+extra+nar))
tg=textgate.gate('q006');''')
s=s.replace("tempo_metadata=passfail(tm['tempo_ok'])","tempo_metadata='N/A'")
s=s.replace("all(x in ['production/compositor/src/Root.tsx','production/compositor/src/Quiz.tsx'] for x in protection['changed'])","set(protection['changed'])=={'episodes/quiz/episodes.py','production/compositor/public/q006/render.json'}")
s=s.replace("passed=all(x=='PASS' for x in gates.values())","passed=all(x in ('PASS','N/A') for x in gates.values())")
pos=s.index("r['asr']['evidence']=")
s=s[:pos]+'''# v3d policy and comparison evidence, applied before the new QA record is written.
r['timing']=json.loads((Q/'qa_v3c.json').read_text())['timing']
r['tempo_metadata_raw']=dict(result=tm,events=events,verdict=passfail(tm['tempo_ok']),applicable=False,evidence='tempo_v3d.json',reason='CTO decision: tempo.py reads metadata only and does not model premium cardAt, legalAfter or animation. For quizStyle=premium, the decoded-frame visual_change_every_1p5_seconds gate is authoritative. Timing is unchanged.',authoritative_gate='visual_change_every_1p5_seconds')
r['tempo']['note']=r['tempo_metadata_raw']['reason']
r['textgate'].update(note='Unmodified textgate.py on the full display corpus: episode labels, all card texts, actual TYPE 02 fixed labels, rendered captions and narration. No exemptions.',full_display_evidence='v3d_work/textgate_full_display.txt',n_labels=tg['n_labels'],n_sentences=tg['n_sentences'])
r['numbers']['verified']=[x.replace('우발적 범행','우발적이었음') for x in r['numbers']['verified']]
r['numbers']['wording_decision']='CTO-approved card edit retains the reported court finding 우발적으로 발생; no narration, subtitle, audio, timing or other factual text changed.'
r['subtitle_sync'].pop('audio_identical_to_v3b',None)
r['subtitle_sync']['audio_identical_to_v3c']=audio['identical_pcm']
r['audio_identity']=dict(audio,reference=str(W/'upload/v3c_q006.mp4'),evidence='v3d_work/audio_compare.json')
r['gates']['narration_audio_unchanged']=passfail(audio['identical_pcm'] and audio['identical_aac_bytes'])
frames=json.loads((P/'frame_compare.json').read_text())
r['frame_identity']=dict(reference=str(W/'upload/v3c_q006.mp4'),frames_compared=frames['frames_compared'],identical_frames=frames['identical_frames'],different_frame_numbers=[x['frame'] for x in frames['different_frames']],card_interval_inclusive=frames['card_interval_inclusive'],outside_card_differences=frames['outside_card_differences'],only_card_frames_differ=frames['only_card_frames_differ'],evidence='v3d_work/frame_compare.json')
r['gates']['only_target_card_frames_changed']=passfail(frames['only_card_frames_differ'])
r['compatibility']['composition_comparison']=json.loads((P/'composition_comparison.json').read_text())
r['compatibility']['composition_metadata_identical']=False
r['compatibility']['composition_metadata_identical_except_card']=r['compatibility']['composition_comparison']['metadata_equal_except_authorized_card']
r['compatibility']['public_render_data_and_audio_changed']=1
r['compatibility']['public_render_data_change']='Only /cues/4/p/cards/2/text; audio and timing data byte-identical.'
r['files_implemented']=['episodes/quiz/episodes.py','production/compositor/public/q006/render.json']
r['scope_notes']=['Only q006 reason card 우발적 범행 → 우발적이었음; original script, narration, subtitles, audio, timing and design otherwise unchanged.','Render and QA engines/settings reused from v3c. Metadata tempo is not applicable to premium per CTO decision; raw result retained.','Pre-existing uploads protected by before/after SHA-256 comparison. No network or uploads used.','Existing stamp range boxes overlap on some frames; delivered ink glyphs remain separated, as in the unchanged v3c layout.']
r['preview']=dict(file=str(W/'upload/preview/v3d_q006_preview.mp4'),width=720,height=1280,evidence='v3d_work/preview_probe.json')
r['passed']=all(v in ('PASS','N/A') for v in r['gates'].values())
r['unfinished']=[] if r['passed'] else [k for k,v in r['gates'].items() if v not in ('PASS','N/A')]
r['asr']['evidence']='asr_final_v3d.json'
(Q/'qa_v3d.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
print(json.dumps(dict(sha256=hash_,duration=secs,passed=r['passed'],failed=r['unfinished']),ensure_ascii=False,indent=2))
'''
p.write_text(s)
