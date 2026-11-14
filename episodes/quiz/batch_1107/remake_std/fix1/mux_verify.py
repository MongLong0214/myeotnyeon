from pathlib import Path
import subprocess,json,hashlib,sys
import numpy as np,soundfile as sf
from scipy.signal import correlate
D=Path(__file__).resolve().parent.parent;W=D.parents[3];F=D/'fix1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(a):return subprocess.run(list(map(str,a)),capture_output=True,check=True).stdout
def packets(p):
 x=json.loads(run(['ffprobe','-v','error','-select_streams','a','-show_packets','-show_data_hash','sha256','-of','json',p]))
 keys=['pts','dts','duration','size','data_hash','side_data_list']
 return [{k:r.get(k) for k in keys} for r in x['packets']]
def pcm(p):return run(['ffmpeg','-v','error','-i',p,'-map','0:a:0','-ar','48000','-ac','2','-c:a','pcm_s32le','-f','s32le','-'])
def main(q,rough=False):
 p=W/f'upload/pkg/{q}_std';b=F/'before'/q;v=p/('animatic_muted.mp4' if rough else 'video_muted.mp4');out=p/('animatic.mp4' if rough else 'video.mp4')
 run(['ffmpeg','-v','error','-y','-i',v,'-i',b/'original.m4a','-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',out])
 oldpack=packets(b/'video.mp4');newpack=packets(out);assert oldpack==newpack,'AAC payload/timing changed'
 oldpcm=pcm(b/'video.mp4');newpcm=pcm(out);assert oldpcm==newpcm,'Decoded audio changed'
 base=json.loads((F/'before.json').read_text())[q]
 assert all(sha(W/n)==h for n,h in base['immutable'].items()),'Narration/timing/subtitles/facts or cover mutated'
 if not rough:
  c=json.loads((p/'case.json').read_text());a=c['answer_frame'];master,sr=sf.read(p/'mix_master.wav',dtype='float64');fx,_=sf.read(p/'mix_effects.wav',dtype='float64');decoded=np.frombuffer(newpcm,dtype='<i4').reshape(-1,2).astype(np.float64)/(2**31)
  at=a*1600;n=min(len(decoded),len(master));start=at-2400;end=at+8160
  stem=(fx-master)[at:at+5760].mean(axis=1);residual=(decoded[:n]-master[:n])[start:end].mean(axis=1)
  corr=correlate(residual,stem,mode='valid',method='fft');lag=int(np.argmax(corr));source_peak=at+int(np.argmax(np.abs(stem)));decoded_peak=start+lag+int(np.argmax(np.abs(stem)))
  result=dict(qid=q,original_video_sha256=base['video_sha256'],new_video_sha256=sha(out),aac_packet_payload_pts_dts_duration_and_skip_samples_identical=True,aac_packet_count=len(oldpack),decoded_48k_stereo_s32le_sha256=hashlib.sha256(newpcm).hexdigest(),decoded_audio_byte_identical=True,narration_and_timing_files_unchanged=True,immutable_files=base['immutable'],picture_leads_sound=dict(visual_contact_frame=a-1,source_sfx_main_peak_sample=source_peak,source_sfx_main_peak_frame=source_peak//1600,decoded_residual_main_peak_sample=decoded_peak,decoded_residual_main_peak_frame=decoded_peak//1600,frame_lead=decoded_peak//1600-(a-1),matched_filter_offset_samples=start+lag-at,method='Decode final AAC, subtract unchanged narration master, and cross-correlate the known 120ms SFX stem over +/-50ms. Source main-peak offset plus matched event onset determines peak frame. CTO visual contact confirmation pending.'),CTO_verdict=None)
  (p/'fix1_audio_identity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  print(q,'audio identical',len(oldpack),'packets; picture lead',result['picture_leads_sound']['frame_lead'],'frame',flush=True)
if __name__=='__main__':main(sys.argv[1],len(sys.argv)>2 and sys.argv[2]=='rough')
