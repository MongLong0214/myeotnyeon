from pathlib import Path
import sys,json,hashlib,subprocess,wave
import numpy as np
root=Path(sys.argv[1]); records=json.loads((root/'manifest.json').read_text())
for r in records:
 p=Path(r['path'])
 a=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-vn','-ac','1','-ar','44100','-f','s16le','-'],check=True,capture_output=True).stdout
 with wave.open(r['source_audio']) as w:b=w.readframes(w.getnframes())
 aa=np.frombuffer(a,dtype='<i2').astype(float);bb=np.frombuffer(b,dtype='<i2').astype(float);n=min(len(aa),len(bb));aa=aa[:n];bb=bb[:n]
 r['decoded_audio_verification']={'compared_samples':n,'sample_rate':44100,'zero_offset_correlation':float(np.corrcoef(aa,bb)[0,1]),'signal_to_encoding_error_db':float(10*np.log10(np.sum(bb*bb)/np.sum((aa-bb)**2))),'source_pcm_samples':len(b)//2,'decoded_pcm_samples':len(a)//2,'aac_is_lossy':True,'listening_review':'not performed'}
 assert r['decoded_audio_verification']['zero_offset_correlation']>.999
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
 # Record exact scope of image review separately from technical decode success.
 r['source_fact_files']=[str(Path(r['source_cue_file']).parent.parent/'facts.md')]
 if r['name'].startswith('n18'):r['source_fact_files'].append(str(Path(r['source_cue_file']).parent.parent/'facts_enrich.md'))
 r['source_fact_sha256']={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in r['source_fact_files']}
 (root/f"{r['name']}_manifest.json").write_text(json.dumps(r,ensure_ascii=False,indent=2))
 print(r['name'],r['probe']['format']['duration'],r['decoded_audio_verification'])
(root/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
