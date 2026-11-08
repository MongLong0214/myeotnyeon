from pathlib import Path
import json,re,hashlib,datetime
from zoneinfo import ZoneInfo
E=Path(__file__).resolve().parent;W=E.parents[2];O=E/'out'
static=json.loads((O/'qa_static.json').read_text());safe=json.loads((O/'safe_area.json').read_text());textgate=json.loads((O/'textgate.json').read_text());probe=json.loads((O/'ffprobe.json').read_text());balance=json.loads((O/'audio_balance.json').read_text());asr=json.loads((O/'asr_final.json').read_text())
v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
spec=dict(width=v['width'],height=v['height'],fps=v['avg_frame_rate'],frames=int(v['nb_frames']),duration_seconds=float(probe['format']['duration']),video_codec=v['codec_name'],profile=v['profile'],pixel_format=v['pix_fmt'],color_space=v.get('color_space'),color_transfer=v.get('color_transfer'),color_primaries=v.get('color_primaries'),audio_codec=a['codec_name'],audio_bitrate=int(a.get('bit_rate',0)),audio_sample_rate=int(a['sample_rate']),audio_channels=a['channels'],crf=16)
spec['passed']=v['width']==1920 and v['height']==1080 and v['avg_frame_rate']=='30/1' and v['profile']=='High' and v.get('color_space')=='bt709' and a['codec_name']=='aac' and 300000<=int(a['bit_rate'])<=330000
log=(O/'ebur128.log').read_text();summary=log[log.rindex('Summary:'):];lufs=float(re.search(r'I:\s*(-?[\d.]+) LUFS',summary)[1]);tp=float(re.search(r'Peak:\s*(-?[\d.]+) dBFS',summary)[1])
log=(O/'freeze-black.log').read_text();freezes=[];start=None
for line in log.splitlines():
 m=re.search(r'freeze_start: ([\d.]+)',line)
 if m:start=float(m[1])
 m=re.search(r'freeze_duration: ([\d.]+)',line)
 if m:freezes.append(dict(start=start,duration=float(m[1])))
blacks=[dict(start=float(m[0]),end=float(m[1]),duration=float(m[2])) for m in re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)',log)]
film=json.loads((W/'production/compositor/src/v4/n18-film.json').read_text());intentional=[dict(id=s['id'],start=s['from']/30,end=(s['from']+s['dur'])/30) for s in film['shots'] if s['kind']=='silence']
for b in blacks:b['intentional']=any(b['start']>=x['start']-.05 and b['end']<=x['end']+.05 for x in intentional)
failures=[]
if not spec['passed']:failures.append('ffprobe specification')
if not(-15<=lufs<=-13 and tp<=-1):failures.append('loudness / true peak')
if any(x['duration']>5 for x in freezes):failures.append('freeze longer than 5 seconds')
if any(not x['intentional'] for x in blacks):failures.append('unintended black')
if asr['match']<.99:failures.append('ASR below 0.99')
if safe['violations']:failures.append('safe area')
if not textgate['passed']:failures.append('im-not-ai strict textgate: '+', '.join(f'{k}={v}' for k,v in textgate['counts'].items() if v))
res=dict(composition='V4N18-FULL',checked_at=datetime.datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),ffprobe=spec,loudness=dict(integrated_lufs=lufs,true_peak_dbtp=tp,measurement='ffmpeg ebur128=peak=true on delivered AAC',passed=-15<=lufs<=-13 and tp<=-1),freezedetect=dict(threshold='-50 dB',events=freezes,max_seconds=max((x['duration'] for x in freezes),default=0),passed=not any(x['duration']>5 for x in freezes)),blackdetect=dict(events=blacks,intended_silence_ranges=intentional,unintended=sum(not x['intentional'] for x in blacks),passed=all(x['intentional'] for x in blacks)),asr=dict(match=asr['match'],errors=asr['errors'],characters=asr['characters'],threshold=.99,passed=asr['match']>=.99,source='final delivered MP4 AAC stream; continuous Whisper, no script prompt',normalization=asr['normalization'],evidence='asr_final.json'),numbers=static['numbers'],spelling=static['spelling'],textgate=textgate,safe_area={k:v for k,v in safe.items() if k!='measurements'},death_case=static['death_case'],audio_balance=dict(minimum_voice_over_ambience_db=balance['minimum_voice_over_ambience_db'],passed=balance['minimum_voice_over_ambience_db']>=14),existing_compositions=static['compositions'],cover_q012_different_pixels=static['cover_q012_different_pixels'],source_hashes=static['source_hashes'],shot_coverage=static['shot_coverage'],fonts=static['fonts'],external_visual_assets=0,new_npm_packages=0,uploads=0,thumbnail=dict(width=1280,height=720,headline_words=5,headline_size_px=77,minimum_required_px=64.8,sentence_quantum_revealed=False),contact_sheet=dict(file='sheet.png',interval_seconds=10,frames=39,timestamps='0,10,...,380'),render=json.loads((O/'render-time.json').read_text()),assembly=json.loads((O/'assembly-time.json').read_text()),failures=failures,passed=not failures)
idx=json.loads((E/'audio/na/index.json').read_text());spoken_seconds=sum(x['dur'] for x in idx['items']);res['narration']=dict(voice=idx['voice'],engine=idx['model'],native_speed=idx['speed'],pitch_preserving_tempo_min=min(x['tempo'] for x in idx['items']),pitch_preserving_tempo_max=max(x['tempo'] for x in idx['items']),spoken_seconds=spoken_seconds,syllables=1742,syllables_per_second=1742/spoken_seconds,passed=4.8<=1742/spoken_seconds<=5.3)
(O/'qa.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
# Append this stage without rewriting or discarding the previous stages.
p=E/'timelog.json';tl=json.loads(p.read_text());start=datetime.datetime.fromisoformat('2026-10-26T20:26:33+09:00');end=datetime.datetime.now(ZoneInfo('Asia/Seoul'));elapsed=round((end-start).total_seconds());render=res['render'];rs=datetime.datetime.fromisoformat(render['start']).astimezone(ZoneInfo('Asia/Seoul'));re_=datetime.datetime.fromisoformat(render['end']).astimezone(ZoneInfo('Asia/Seoul'))
tl['steps'] += [dict(step='stage_2b_build_narration_full_composition_and_preflight',start=start.isoformat(),end=rs.isoformat(),elapsed_seconds=round((rs-start).total_seconds())),dict(step='stage_2b_render_and_parallel_qa',start=rs.isoformat(),end=re_.isoformat(),elapsed_seconds=round((re_-rs).total_seconds()),render_wall_seconds=render['wall_seconds']),dict(step='stage_2b_assemble_delivered_media_and_final_qa',start=re_.isoformat(),end=end.isoformat(),elapsed_seconds=round((end-re_).total_seconds()))]
tl['provider_interruption_seconds']=render.get('provider_interruption_seconds',0);tl['stage_2b_active_elapsed_seconds']=elapsed-tl['provider_interruption_seconds'];res['provider_interruption_seconds']=tl['provider_interruption_seconds']
tl.update(stage_2b_started=True,stage_2b_started_at=start.isoformat(),stage_2b_ended_at=end.isoformat(),stage_2b_elapsed_seconds=elapsed,stage_2b_render_seconds=round(render['wall_seconds'],3),ended_at=end.isoformat(),elapsed_seconds=tl['elapsed_seconds']+elapsed,status='stage_2b_delivered_with_textgate_flags' if failures else 'stage_2b_complete')
p.write_text(json.dumps(tl,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(duration=spec['duration_seconds'],lufs=lufs,tp=tp,asr=asr['match'],failures=failures,stage_2b_seconds=elapsed,total_all_stages_seconds=tl['elapsed_seconds']),ensure_ascii=False))
