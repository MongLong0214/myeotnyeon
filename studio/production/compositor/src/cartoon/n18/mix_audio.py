from pathlib import Path
import subprocess,json,shutil
W=Path(__file__).resolve().parents[5];O=W/'episodes/v4/n18/cartoon_v4'
shutil.copy2(W/'assets/music/LICENSE.md',O/'music_license.md')
music=W/'assets/music/Sneaky Spelunking - Joel Cummins.mp3'
# Match Task A: local licensed bed, voice sidechain; no licensed SFX found in assets.
cmd=['ffmpeg','-hide_banner','-y','-i',str(O/'public/narration.wav'),'-stream_loop','-1','-i',str(music),'-filter_complex','[0:a]asplit=2[voice][sc];[1:a]atrim=duration=455.433333,asetpts=PTS-STARTPTS,volume=0.10,afade=t=in:d=1.0,afade=t=out:st=451.433333:d=4[bed];[bed][sc]sidechaincompress=threshold=0.018:ratio=9:attack=8:release=230:makeup=1[duck];[voice][duck]amix=inputs=2:duration=first:normalize=0[mix]','-map','[mix]','-ar','48000','-c:a','pcm_s16le',str(O/'public/mix.wav')]
subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=open(O/'audio_mix.log','w'))
(O/'audio_manifest.json').write_text(json.dumps({'narration':'public/narration.wav','recovery':'audio_recovery.json','music':str(music.relative_to(W)),'licence':'music_license.md','music_gain_linear':.10,'ducking':{'threshold':.018,'ratio':9,'attack_ms':8,'release_ms':230},'new_sfx':[],'sfx_note':'No separately licensed SFX found in assets; original recovered track remains intact. No collapse, impact, death or invented event sound added.','normalization':False,'voice_speed_pitch_edited':False},ensure_ascii=False,indent=2))
print('mixed existing final track with local licensed ducked music')
