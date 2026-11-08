from pathlib import Path
import subprocess,json,re
import numpy as np
P=Path(__file__).resolve().parent
video=P/'lf2_cartoon_v4_1080p.mp4'
# Decode all frames for black/freeze windows and exact repeats.
log=P/'qa/detectors.log'
with log.open('w') as f:
 subprocess.run(['ffmpeg','-hide_banner','-y','-i',str(video),'-filter_complex','[0:v]scale=320:180,split=2[a][b];[a]blackdetect=d=0.1:pix_th=0.08:pic_th=0.98,freezedetect=n=-60dB:d=3[checked]','-map','[checked]','-an','-f','null','-','-map','[b]','-an','-f','framemd5',str(P/'qa/frame_hashes.md5')],stderr=f,stdout=subprocess.DEVNULL,check=True)
text=log.read_text();black=re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)',text)
freezes=re.findall(r'freeze_duration: ([\d.]+)',text)
hashes=[line.rsplit(',',1)[-1].strip() for line in (P/'qa/frame_hashes.md5').read_text().splitlines() if line and not line.startswith('#')]
run=longest=1;duplicates=0
for prev,cur in zip(hashes,hashes[1:]):
 if prev==cur:run+=1;duplicates+=1
 else:run=1
 longest=max(longest,run)
def decode(file):
 return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(file),'-ac','1','-ar','6000','-f','f32le','-']),dtype='<f4')
reference=decode(P/'public/soundtrack.wav');encoded=decode(video);offsets=[]
for t in [.5,30,100,200,400]:
 start=int(t*6000);ref=reference[start:start+6000].astype(float);ref-=ref.mean();scores=[]
 for lag in range(-200,201):
  sample=encoded[start+lag:start+lag+6000].astype(float);sample-=sample.mean()
  scores.append(float(np.dot(sample,ref)/(np.linalg.norm(sample)*np.linalg.norm(ref)+1e-12)))
 j=int(np.argmax(scores));offsets.append({'at_s':t,'audio_delay_ms':round((j-200)/6,4),'correlation':round(scores[j],6)})
# Peak checks at full 24 kHz, below the encoder's bandwidth.
full=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(video),'-ac','1','-ar','24000','-f','f32le','-']),dtype='<f4')
report={'decoded_frames':len(hashes),'black_windows':black,'freeze_durations_over_3s':freezes,'identical_adjacent_frames':duplicates,'longest_identical_frame_run_s':longest/30,'encoded_audio_alignment':offsets,'max_abs_audio_delay_ms':max(abs(x['audio_delay_ms']) for x in offsets),'decoded_audio_peak':float(np.max(np.abs(full))),'decoded_samples_above_unity':int((np.abs(full)>1).sum()),'all_frame_scan':'qa/detectors.log','frame_hashes':'qa/frame_hashes.md5'}
(P/'qa/encoded_checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
