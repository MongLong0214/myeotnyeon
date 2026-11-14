import path from 'node:path';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const here=path.dirname(fileURLToPath(import.meta.url)),W=path.resolve(here,'../../..'),compositor=path.join(W,'production/compositor');
process.env.TMPDIR=path.join(here,'tmp');
const require=createRequire(path.join(compositor,'package.json'));
const {bundle}=require('@remotion/bundler');
const {openBrowser,getCompositions,renderStill,renderMedia}=require('@remotion/renderer');
const mode=process.argv[2]??'fix-stills';
const data=JSON.parse(fs.readFileSync(path.join(here,'episode_data.json')));
const serveUrl=await bundle({entryPoint:path.join(here,'LF2.tsx'),outDir:path.join(here,'bundle'),publicDir:path.join(here,'public'),enableCaching:false,gitSource:null,webpackOverride:c=>({...c,cache:false,resolve:{...c.resolve,modules:[path.join(compositor,'node_modules'),'node_modules']}})});
const browser=await openBrowser('chrome',{browserExecutable:path.join(here,'chrome_offline.sh'),logLevel:'error'});
try{
 const comps=await getCompositions(serveUrl,{puppeteerInstance:browser,port:44861});const comp=comps[0];console.log('COMP',comp.width,comp.height,comp.durationInFrames);
 if(['preview','cuts','violence','fix-stills'].includes(mode)){
  const original=JSON.parse(fs.readFileSync(path.join(here,'fix_evidence/original_shots_v6.json')));
  const frames=mode==='violence'?[0,8,13,23,31,33,36,48,65]:mode==='fix-stills'?original.map(s=>s.start+Math.floor((s.end-s.start)*.5)):data.shots.map(s=>s.start+Math.floor((s.end-s.start)*.5));
  let done=0;await Promise.all(Array.from({length:4},(_,worker)=>(async()=>{for(let i=worker;i<frames.length;i+=4){const f=frames[i];await renderStill({serveUrl,port:44862+worker,composition:comp,puppeteerInstance:browser,frame:f,scale:mode==='violence'?1:.5,output:path.join(here,'fix_evidence',`after_${String(f).padStart(6,'0')}.jpg`),imageFormat:'jpeg',jpegQuality:91,overwrite:true,logLevel:'error'});if(++done%25===0)console.log('STILLS',done,frames.length);}})()));
 }else if(mode==='labels'){
  // Render only the scene-label corrections, after the complete picture render.
  const ids=new Set([23,48,77,82,83,94,97,101,107,110,131].map(n=>`V6_${String(n).padStart(3,'0')}`));
  const patches=[];
  for(const s of data.shots.filter(s=>ids.has(s.id))){
   const output=path.join(here,'fix_evidence',`label_${s.id}.mp4`);
   await renderMedia({serveUrl,port:44861,composition:comp,puppeteerInstance:browser,outputLocation:output,frameRange:[s.start,s.end-1],codec:'h264',crf:18,x264Preset:'fast',pixelFormat:'yuv420p',concurrency:6,overwrite:true,logLevel:'error'});
   patches.push({start:s.start,end:s.end,path:output});console.log('LABEL',s.id);
  }
  fs.writeFileSync(path.join(here,'fix_evidence/label_patches.json'),JSON.stringify(patches));
 }else{
  const patchRange=mode==='bankpatch'?[data.shots[8].start,data.shots[10].end-1]:mode==='policepatch'?[data.shots[24].start,data.shots[24].end-1]:mode==='switchpatch'?[data.shots[31].start,data.shots[31].end-1]:mode==='hurtpatch'?[data.shots[25].start,data.shots[26].end-1]:null;
  let last=0;await renderMedia({serveUrl,port:44861,composition:comp,puppeteerInstance:browser,outputLocation:path.join(here,'fix_evidence',mode==='sample'?'sample_15s_silent.mp4':'picture_v6fix_1080p.mp4'),...(patchRange?{frameRange:patchRange}:mode==='sample'?{frameRange:[0,Math.min(449,comp.durationInFrames-1)]}:mode==='first60'?{frameRange:[0,1799]}:{}),codec:'h264',crf:18,x264Preset:'fast',pixelFormat:'yuv420p',concurrency:6,overwrite:true,logLevel:'error',onProgress:p=>{if(Date.now()-last>15000){console.log('RENDER',p.renderedFrames,p.encodedFrames,'/',comp.durationInFrames);last=Date.now()}}});
 }
}finally{await browser.close({silent:true})}
