import fs from 'node:fs';import path from 'node:path';import {fileURLToPath,pathToFileURL} from 'node:url';
import {atomicWrite,sha,stable,validateEpisode} from '../src/core.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const ep=JSON.parse(fs.readFileSync(path.join(root,process.argv[2]||'episodes/one_step_behind/episode.json'))),timeline=validateEpisode(ep);
const sr=48000,n=Math.ceil(timeline.seconds*sr),l=new Float32Array(n),r=new Float32Array(n);
let seed=4831;const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return (seed>>>0)/4294967296*2-1;};
function bell(at,hz,dur,gain,pan=0){const begin=Math.round(at*sr),len=Math.round(dur*sr);for(let k=0;k<len&&begin+k<n;k++){const t=k/sr,env=(1-Math.exp(-t*100))*Math.exp(-t*3.6);const y=(Math.sin(2*Math.PI*hz*t)+.22*Math.sin(2*Math.PI*hz*2.01*t))*env*gain;l[begin+k]+=y*(1-pan)*.5;r[begin+k]+=y*(1+pan)*.5;}}
function step(at,pan){const begin=Math.round(at*sr);let low=0;for(let k=0;k<sr*.11&&begin+k<n;k++){const t=k/sr;low=low*.88+rand()*.12;const v=(low+Math.sin(t*500)*.12)*Math.exp(-t*35)*.15;l[begin+k]+=v*(1-pan)*.5;r[begin+k]+=v*(1+pan)*.5;}}
// Original, quiet synthesized accompaniment. No samples, no external song melody.
for(let bar=0;bar<Math.ceil(timeline.seconds/4);bar++){const base=[174.614,195.998,220,164.814][bar%4];for(let j=0;j<3;j++)bell(bar*4+j*.65,base*[1,1.5,2][j],2.2,.035,(j-1)*.25);}
const sourceDependencies=Object.fromEntries(timeline.shots.map(s=>[s.module,sha(fs.readFileSync(path.join(root,s.module)))]));
const timing=timeline.shots.map(({id,frames,module,params})=>({id,frames,module,params}));
for(const shot of timeline.shots){
 const mod=await import(pathToFileURL(path.join(root,shot.module)));
 for(const event of mod.soundEvents?.(shot.params||{})||[]){
  const at=shot.startFrame/ep.fps+event.t;
  if(!Number.isFinite(at)||event.t<0||event.t>=shot.frames/ep.fps)throw new Error('Sound event outside shot '+shot.id);
  if(event.type==='step')step(at,event.pan||0);
  else if(event.type==='bell')bell(at,event.hz,1.6,event.gain||.06,event.pan||0);
  else throw new Error('Unsupported sound event '+event.type);
 }
}
const pcm=Buffer.alloc(n*4);for(let i=0;i<n;i++){const fade=Math.min(1,i/(sr*.2),(n-i)/(sr*.5));pcm.writeInt16LE(Math.round(Math.max(-.95,Math.min(.95,l[i]*fade))*32767),i*4);pcm.writeInt16LE(Math.round(Math.max(-.95,Math.min(.95,r[i]*fade))*32767),i*4+2);}
const h=Buffer.alloc(44);h.write('RIFF');h.writeUInt32LE(36+pcm.length,4);h.write('WAVEfmt ',8);h.writeUInt32LE(16,16);h.writeUInt16LE(1,20);h.writeUInt16LE(2,22);h.writeUInt32LE(sr,24);h.writeUInt32LE(sr*4,28);h.writeUInt16LE(4,32);h.writeUInt16LE(16,34);h.write('data',36);h.writeUInt32LE(pcm.length,40);
const wav=Buffer.concat([h,pcm]),out=path.join(root,'out');atomicWrite(out,`${ep.id}/audio/effects.wav`,wav);atomicWrite(out,`${ep.id}/audio/effects.json`,JSON.stringify({license:'Original procedural sound; MIT source',sampleRate:sr,seconds:n/sr,sha256:sha(wav),timingKey:sha(stable({fps:ep.fps,timing,sourceDependencies,worker:sha(fs.readFileSync(fileURLToPath(import.meta.url)))}))},null,2));console.log('Original synthesized effects + accompaniment written. Listening review remains required.');
