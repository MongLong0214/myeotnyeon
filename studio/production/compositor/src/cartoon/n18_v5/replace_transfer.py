"""Apply the corrected transfer sentence and restrained memorial entrance."""
import json,subprocess,time
import audio as V
E=V.E;d=json.loads((E/'episode_data.json').read_text());start=time.time()
main=E/'n18_cartoon_v5_1080p.mp4';out=E/'n18_cartoon_v5_corrected.mp4'
args=['ffmpeg','-v','error','-y','-i',str(main)];filters=[];ranges=[];previous='0:v'
for i,sid in enumerate(['N019','N072'],1):
 shots=[s for s in d['shots'] if s['narrationId']==sid];a=shots[0]['start'];b=shots[-1]['end']-1
 args+=['-i',str(E/f'{sid}_patch.mp4')]
 filters.extend([f'[{i}:v]setpts=PTS-STARTPTS+{a}/30/TB[p{i}]',f'[{previous}][p{i}]overlay=enable=between(n\\,{a}\\,{b}):eof_action=pass:repeatlast=0[v{i}]'])
 previous=f'v{i}';ranges.append(dict(id=sid,start_frame=a,end_frame_inclusive=b))
args+=['-i',str(E/'public/mix.wav'),'-filter_complex',';'.join(filters),'-map',f'[{previous}]','-map','3:a','-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p','-r','30','-frames:v',str(d['durationInFrames']),'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(out)]
subprocess.run(args,check=True)
main.replace(E/'render_before_corrections.mp4');out.replace(main)
(E/'transfer_correction.json').write_text(json.dumps(dict(ranges=ranges,preserved_runtime_s=d['duration'],reason='F16 transfer sentence restored after isolating obsolete duplicate; memorial entrance given serious camera/audio tone.',video='Targeted Remotion replacement frames over base render, whole-file CRF16 encoding; new complete AAC from corrected mix',seconds=time.time()-start),ensure_ascii=False,indent=2))
print('CORRECTIONS COMPLETE',ranges,flush=True)
