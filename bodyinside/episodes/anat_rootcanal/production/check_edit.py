"""Decode every frame, check the picture clock and loop, and extract review images from the delivery."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from audio import loudness

EP=Path(__file__).resolve().parent.parent
CACHE=EP/'production/.cache'
FONT=EP.parents[1]/'branding/_src/public/fonts/Pretendard-Bold.otf'
FRAMES=[0,76,125,200,320,388,554,656,784,880]
NAMES=['치료 전','치수 감염','뿌리 끝 농양','치수 접근','치수 제거','근관 성형','세척·건조','근관 충전','다음 내원','수복 후']

def read_frame(stream,n):
    data=bytearray()
    while len(data)<n:
        buf=stream.read(n-len(data))
        if not buf:break
        data.extend(buf)
    return data
def check(variant):
    draft=variant=='draft'
    path=EP/('rootcanal_draft1.mp4' if draft else 'rootcanal_final.mp4')
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
    v,a=info['streams']
    w,h=v['width'],v['height']
    assert (w,h)==((540,960) if draft else (1080,1920))
    assert v['codec_name']=='h264' and a['codec_name']=='aac' and a['sample_rate']=='48000' and a['channels']==2
    assert v['avg_frame_rate']==v['r_frame_rate']=='30/1' and int(v['nb_frames'])==930
    assert abs(float(v['duration'])-31)<1e-5 and abs(float(a['duration'])-31)<.001
    pts=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_packets','-show_entries','packet=pts','-of','json',str(path)]))
    timebase=np.prod([1/int(v['time_base'].split('/')[1]),int(v['time_base'].split('/')[0])])
    clock=np.sort([int(p['pts']) for p in pts['packets']])*timebase
    if not np.allclose(clock,np.arange(930)/30,atol=1e-6):raise ValueError('Nonuniform frame timestamps')
    cmd=['ffmpeg','-nostdin','-v','error','-xerror','-i',str(path),'-map','0:v:0','-an','-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-']
    sheet=Image.new('RGB',(1300,1006),'#222122')
    d=ImageDraw.Draw(sheet)
    font=ImageFont.truetype(str(FONT),17)
    hashes=set();small=[];black=[];minimum_luma=256;maximum_luma=0
    sys.path.insert(0,str(EP.parents[1]/'anat_kit/gates'))
    from noise_metric import frame_metrics
    noise_samples=[]
    hot_counts=[]
    ring=np.ones((3,3),np.uint8);ring[1,1]=0
    with subprocess.Popen(cmd,stdout=subprocess.PIPE) as proc:
        for f in range(930):
            data=read_frame(proc.stdout,w*h*3)
            if len(data)!=w*h*3:raise ValueError(('Incomplete picture',f))
            hashes.add(hashlib.blake2s(data,digest_size=16).digest())
            rgb=np.frombuffer(data,dtype=np.uint8).reshape(h,w,3)
            gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
            neighbors=cv2.dilate(gray,ring,borderType=cv2.BORDER_REPLICATE)
            hot_counts.append(int(((cv2.subtract(gray,neighbors)>60)&(gray>200)).sum()))
            if f%30==0:
                noise_samples.append(frame_metrics(gray)[0])
            proxy=cv2.resize(rgb,(90,160),interpolation=cv2.INTER_AREA)
            small.append(proxy)
            luma=cv2.cvtColor(proxy,cv2.COLOR_RGB2GRAY)
            if np.quantile(luma,.99)<16:black.append(f)
            minimum_luma=min(minimum_luma,float(luma.mean()));maximum_luma=max(maximum_luma,float(luma.mean()))
            if draft and f in FRAMES:
                idx=FRAMES.index(f);px=idx%5*260+5;py=idx//5*503+5
                tile=Image.fromarray(rgb).resize((250,444),Image.Resampling.LANCZOS)
                sheet.paste(tile,(px,py))
                d.text((px+1,py+450),NAMES[idx],font=font,fill='#FFF9ED')
                d.text((px+1,py+474),f'{f/30:05.2f} s   ·   f{f:03d}',font=font,fill='#D8C9B5')
            if not draft and f==388:Image.fromarray(rgb).save(EP/'thumbnail.png')
        if proc.stdout.read(1):raise ValueError('Extra video frames')
        if proc.wait():raise RuntimeError('Decode failed')
    if draft:sheet.save(EP/'sheet_draft1.png')
    assert len(hashes)==930 and not black,(len(hashes),black)
    thumbs=np.stack(small)
    deltas=np.abs(np.diff(thumbs.astype(np.int16),axis=0)).mean(axis=(1,2,3))
    seam=np.abs(thumbs[-1].astype(np.int16)-thumbs[0]).mean()
    if seam>np.percentile(deltas[:44],99)+1:raise ValueError(('Loop cut stands out from hook motion',seam))
    freeze=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(path),'-an','-vf','freezedetect=n=0.002:d=0.5','-f','null','-'],capture_output=True,text=True,check=True)
    if 'freeze_start:' in freeze.stderr:raise ValueError(freeze.stderr)
    quiet=loudness(path)
    assert abs(float(quiet['input_i'])+14)<.1 and float(quiet['input_tp'])<=-1.5
    report=dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),width=w,height=h,fps=30,frames=930,duration_s=31,unique_frames=len(hashes),black_frames=black,loop_mean_rgb_delta=float(seam),hook_neighbor_mean_delta=float(np.mean(deltas[:44])),mean_luma_range=[minimum_luma,maximum_luma],lufs_i=float(quiet['input_i']),true_peak_dbtp=float(quiet['input_tp']))
    report.update(freezes_500ms=0,isolated_bright_pixels_max_per_frame=max(hot_counts),sampled_flat_luma_noise_median=round(float(np.median(noise_samples)),3),noise_samples=len(noise_samples))
    if draft:np.savez_compressed(CACHE/'draft-review.npz',rgb=thumbs)
    else:
        ref=np.load(CACHE/'draft-review.npz')['rgb']
        mad=np.abs(thumbs.astype(np.int16)-ref).mean(axis=(1,2,3))
        report.update(draft_comparison_median_rgb_delta=float(np.median(mad)),draft_comparison_peak_rgb_delta=float(mad.max()),draft_comparison_peak_frame=int(mad.argmax()))
    (CACHE/f'{variant}-verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':check(sys.argv[1])
