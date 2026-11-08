import subprocess,json,re,sys,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent
w=p.parent
q=sys.argv[1]
a,b,h={'012':(917,921,916),'016':(841,844,840),'017':(623,626,622)}[q]
orig=w/f'v52_q{q}.mp4'; out=p/f'v52b_q{q}.mp4'
def run(args):
 return subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
results={'span':[a,b],'held':h}
for label,f in [('input',orig),('output',out)]:
 probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_format','-show_streams','-of','json',str(f)]).stdout)
 (p/f'q{q}_{label}_ffprobe.json').write_text(json.dumps(probe,indent=2)+'\n')
 audio=run(['ffmpeg','-v','error','-i',str(f),'-map','0:a:0','-c:a','copy','-f','md5','-']).stdout.decode().strip()
 pcm=run(['ffmpeg','-v','error','-i',str(f),'-map','0:a:0','-c:a','pcm_s32le','-f','md5','-']).stdout.decode().strip()
 lr=run(['ffmpeg','-hide_banner','-nostats','-i',str(f),'-map','0:a:0','-af','ebur128=peak=true','-f','null','-']).stderr.decode()
 (p/f'q{q}_{label}_r128.log').write_text(lr)
 integrated=float(re.findall(r'I:\s+(-?[\d.]+) LUFS',lr)[-1])
 results[label]={'audio_md5':audio,'pcm_md5':pcm,'lufs':integrated}
print(q,'audio/loudness complete',flush=True)
log=p/f'q{q}_psnr.log'
fc=f'[0:v]split=2[s][r];[s][r]freezeframes=first={a}:last={b}:replace={h}[expected];[1:v][expected]psnr=stats_file={log}:stats_version=2[v]'
r=run(['ffmpeg','-hide_banner','-nostats','-threads','2','-i',str(orig),'-threads','2','-i',str(out),'-filter_complex_threads','2','-filter_complex',fc,'-map','[v]','-an','-f','null','-'])
(p/f'q{q}_psnr_summary.log').write_text(r.stderr.decode())
rows=[]
for line in log.read_text().splitlines():
 if not line.startswith('n:'):continue
 vals=dict(x.split(':',1) for x in line.split()); vals['frame']=int(vals['n'])-1
 rows.append(vals)
expected_count={'012':967,'016':890,'017':672}[q]
assert len(rows)==expected_count,(q,len(rows))
outside=[r for r in rows if not a<=r['frame']<=b]
minimum=min(outside,key=lambda r:float(r['psnr_avg']))
results['outside']={'count':len(outside),'minimum_psnr':float(minimum['psnr_avg']),'minimum_frame':minimum['frame'],'per_plane_min':{c:min(float(r['psnr_'+c]) for r in outside) for c in ['y','u','v']}}
results['replaced']=[{'frame':r['frame'],'psnr':float(r['psnr_avg']),'y':float(r['psnr_y']),'u':float(r['psnr_u']),'v':float(r['psnr_v'])} for r in rows if a<=r['frame']<=b]
assert results['outside']['minimum_psnr']>=42
assert min(r['psnr'] for r in results['replaced'])>=45
assert results['input']['audio_md5']==results['output']['audio_md5']
assert results['input']['pcm_md5']==results['output']['pcm_md5']
assert results['input']['lufs']==results['output']['lufs']
(p/f'q{q}_metrics.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results),flush=True)
