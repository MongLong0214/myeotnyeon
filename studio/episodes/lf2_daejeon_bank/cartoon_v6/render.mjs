import path from 'node:path';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const here=path.dirname(fileURLToPath(import.meta.url)),W=path.resolve(here,'../../..'),compositor=path.join(W,'production/compositor'),out=path.join(here,'fix2_evidence');
process.env.TMPDIR=path.join(here,'tmp');
const require=createRequire(path.join(compositor,'package.json'));
const {bundle}=require('@remotion/bundler');
const {openBrowser,getCompositions,renderStill,renderMedia}=require('@remotion/renderer');
const mode=process.argv[2]??'stills';
const data=JSON.parse(fs.readFileSync(path.join(here,'episode_data_v6fix2.json')));
const serveUrl=await bundle({entryPoint:path.join(here,'LF2.tsx'),outDir:path.join(here,'bundle'),publicDir:path.join(here,'public'),enableCaching:false,gitSource:null,webpackOverride:c=>({...c,cache:false,resolve:{...c.resolve,modules:[path.join(compositor,'node_modules'),'node_modules']}})});
const browser=await openBrowser('chrome',{browserExecutable:path.join(here,'chrome_offline.sh'),logLevel:'error'});
try{
 const comps=await getCompositions(serveUrl,{puppeteerInstance:browser,port:44861});const comp=comps[0];console.log('COMP',comp.width,comp.height,comp.durationInFrames);
 if(mode==='stills'){
  const frames=[...new Set([...data.shots.map(s=>s.start+Math.floor((s.end-s.start)*.5)),...data.shots.filter(s=>s.id==='V6_033').flatMap(s=>[s.start+10,s.start+30,s.end-7])])];
  let done=0;await Promise.all(Array.from({length:4},(_,worker)=>(async()=>{for(let i=worker;i<frames.length;i+=4){const f=frames[i];await renderStill({serveUrl,port:44862+worker,composition:comp,puppeteerInstance:browser,frame:f,scale:.5,output:path.join(out,`preview_${String(f).padStart(6,'0')}.jpg`),imageFormat:'jpeg',jpegQuality:93,overwrite:true,logLevel:'error'});if(++done%25===0)console.log('STILLS',done,frames.length);}})()));
 }else{
  let last=0;await renderMedia({serveUrl,port:44861,composition:comp,puppeteerInstance:browser,outputLocation:path.join(out,mode==='sample'?'sample.mp4':'picture_v6fix2_1080p.mp4'),...(mode==='sample'?{frameRange:[3688,Math.min(4490,comp.durationInFrames-1)]}:{}),codec:'h264',crf:18,x264Preset:'fast',pixelFormat:'yuv420p',concurrency:6,overwrite:true,logLevel:'error',onProgress:p=>{if(Date.now()-last>15000){console.log('RENDER',p.renderedFrames,p.encodedFrames,'/',comp.durationInFrames);last=Date.now()}}});
 }
}finally{await browser.close({silent:true})}
