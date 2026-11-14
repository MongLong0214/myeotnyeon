# Per-frame (30 fps) loudness of the narration for lip sync: python3 look/v2/lipdata.py q021
# -> look/v2/lipdata/<qid>.json {"rms":[0..1 per frame]}. Mouth timing then follows the real voice (Rhubarb-style).
import sys,json,subprocess,numpy as np,pathlib
q=sys.argv[1];W=pathlib.Path(__file__).resolve().parents[6]
wav=W/'upload/pkg'/(q+'_B')/'narration.wav'
raw=subprocess.run(['ffmpeg','-v','error','-i',str(wav),'-ac','1','-ar','48000','-f','s16le','-'],capture_output=True,check=True).stdout
x=np.frombuffer(raw,np.int16).astype(np.float32)/32768;n=1600
fr=len(x)//n;r=np.sqrt((x[:fr*n].reshape(fr,n)**2).mean(1))
db=20*np.log10(r+1e-6);v=np.clip((db+50)/36,0,1)
out=pathlib.Path(__file__).parent/'lipdata'/(q+'.json');out.write_text(json.dumps({'rms':[round(float(a),3) for a in v]}))
print(q,fr,'frames',round(float((v>.25).mean()),2),'voiced')
