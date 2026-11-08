#!/usr/bin/env python3
"""Rebuild through short.py, then compare decoded frames and audio locally."""
from pathlib import Path
import argparse,json,math,re,subprocess,sys
from short import W,S,save,load,sha,new_dir
from gates import empty_panel_gate,number_gate,title_gate

def run(args):return subprocess.check_output(list(map(str,args)),stderr=subprocess.STDOUT).decode()
def md5(p,codec):return run(['ffmpeg','-v','error','-i',p,'-map','0:a:0','-c:a',codec,'-f','md5','-']).strip()
def count(p):return int(run(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames','-of','csv=p=0',p]).strip())
def compare(p,q,n,out):
    reference=W/'upload'/f'v52_{q}_n{n}.mp4';video=p/'video.mp4';csv=out/f'{q}_per_frame_psnr.log'
    run(['ffmpeg','-v','error','-i',reference,'-i',video,'-filter_complex',f'[0:v][1:v]psnr=stats_file={csv}', '-an','-f','null','-'])
    values=[]
    for line in csv.read_text().splitlines():
        m=re.search(r'n:(\d+).*psnr_avg:([\d.]+|inf)',line)
        if m:values.append((int(m[1])-1,float(m[2])))
    delta=[dict(frame=f,psnr_db=v) for f,v in values if v<40]
    ca,cb=count(reference),count(video)
    aa,ab=md5(reference,'copy'),md5(video,'copy');pa,pb=md5(reference,'pcm_s32le'),md5(video,'pcm_s32le')
    result=dict(package=str(p.relative_to(W)),reference=str(reference.relative_to(W)),frame_count=dict(reference=ca,rebuild=cb,match=ca==cb),audio=dict(aac_reference=aa,aac_rebuild=ab,aac_identical=aa==ab,pcm_reference=pa,pcm_rebuild=pb,pcm_identical=pa==pb),psnr=dict(frames=len(values),minimum_db=min((v for _,v in values if math.isfinite(v)),default='inf'),all_frames_ge_40_db=not delta,infinite_frames=sum(math.isinf(v) for _,v in values),below_40=delta,per_frame_file=str(csv.relative_to(W))),gates={k:dict(status=v['status'],review_state=v.get('review_state')) for k,v in load(p/'qa.json')['gates'].items()},ready=load(p/'qa.json')['ready'])
    result['mp4_sha256']=dict(reference=sha(reference),rebuild=sha(video),identical=sha(reference)==sha(video))
    result['media_regression_pass']=ca==cb==len(values) and aa==ab and pa==pb and all(math.isinf(v) for _,v in values)
    result['automatic_gates_pass']=all(g['status']=='PASS' or g['review_state']=='NEEDS_REVIEW' for g in result['gates'].values())
    return result

def main():
    a=argparse.ArgumentParser();a.add_argument('--q013',type=Path);a.add_argument('--q014',type=Path);args=a.parse_args()
    out=S/'regression';out.mkdir(exist_ok=True)
    # Never overwrite an earlier regression proof.
    for i in range(1,100000):
        dest=out/(f'run_{i:03}')
        try:dest.mkdir();break
        except FileExistsError:continue
    packages={}
    for q,n,path in [('q013',16,args.q013),('q014',15,args.q014)]:
        if path is None:
            identity=[] if q!='q014' else ['--video-id','S-eU5rbP9yg']
            proc=subprocess.run([sys.executable,str(S/'short.py'),q,'--no',str(n),*identity],text=True,capture_output=True)
            (dest/f'{q}_build.log').write_text(proc.stdout+proc.stderr)
            m=re.search(r'^PACKAGE (.+)$',proc.stdout,re.M)
            if not m:raise RuntimeError(proc.stdout+proc.stderr)
            path=Path(m[1])
        packages[q]=path.resolve()
    results={q:compare(p,q,n,dest) for q,n in [('q013',16),('q014',15)] for p in [packages[q]]}
    p=packages['q013'];doc=load(p/'render.json')
    old_title=(W/'upload/v52_q013_n16_meta.txt').read_text()
    defects=dict(empty_panel=empty_panel_gate(W/'upload/v52_q013.mp4',p/'empty.mp4',doc),number_13=number_gate(13,'q013',dict(badge=13,endCard=13,cover=13)),prefixed_title=title_gate(old_title))
    reservations={f'{q}_n{n}':number_gate(n,q,dict(badge=n,endCard=n,cover=n)) for q,n in [('q013',16),('q013',13),('q014',16)]}
    reservation_pass=[g['status'] for g in reservations.values()]==['PASS','FAIL','FAIL']
    report=dict(results=results,number_cases=reservations,reservation_cases_pass=reservation_pass,known_defects=defects,all_media_regressions_pass=all(r['media_regression_pass'] for r in results.values()),known_defects_caught=all(g['status']=='FAIL' for g in defects.values()),all_automatic_gates_pass=all(r['automatic_gates_pass'] for r in results.values()),all_package_gates_pass=all(r['ready'] for r in results.values()),unfinished='Facts and raster red lines require CTO sign-off. q013 #16 reservation passes; q014 #15 explicitly rebuilds the same known video identity. No ledger writes.')
    save(dest/'report.json',report);print(dest/'report.json');print(json.dumps(dict(media=report['all_media_regressions_pass'],defects=report['known_defects_caught'],reservations=reservation_pass,ready=report['all_package_gates_pass']),ensure_ascii=False))
    return 0 if report['all_media_regressions_pass'] and report['known_defects_caught'] and reservation_pass and report['all_automatic_gates_pass'] else 1
if __name__=='__main__':sys.exit(main())
