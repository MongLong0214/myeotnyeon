import path from 'node:path';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const here=path.dirname(fileURLToPath(import.meta.url));
const W=path.resolve(here,'../../..');
const compositor=path.join(W,'production/compositor');
const require=createRequire(path.join(compositor,'package.json'));
const {bundle}=require('@remotion/bundler');
const {openBrowser,getCompositions,renderStill,renderMedia}=require('@remotion/renderer');
const mode=process.argv[2]??'preview';
const data=JSON.parse(fs.readFileSync(path.join(here,'episode_data.json'),'utf8'));
const bundlePath=path.join(here,'bundle');
const serveUrl=await bundle({entryPoint:path.join(here,'LF2.tsx'),outDir:bundlePath,publicDir:path.join(here,'public'),enableCaching:false,gitSource:null,webpackOverride:c=>({...c,cache:false,resolve:{...c.resolve,modules:[path.join(compositor,'node_modules'),'node_modules']}})});
const browser=await openBrowser('chrome',{browserExecutable:path.join(here,'chrome_offline.sh'),logLevel:'error'});
try{
 const comps=await getCompositions(serveUrl,{puppeteerInstance:browser,port:41377});
 const comp=comps.find(c=>c.id==='LF2CartoonV4');
 console.log('composition',comp.width,comp.height,comp.durationInFrames);
 if(mode==='atlas'){
  await renderStill({serveUrl,port:41377,composition:comps.find(c=>c.id==='PuppetAtlasV4'),puppeteerInstance:browser,output:path.join(here,'qa/puppet_atlas.jpg'),imageFormat:'jpeg',jpegQuality:90,overwrite:true,logLevel:'error'});
 }else if(mode==='preview'||mode==='qa'){
  if(mode==='preview')await renderStill({serveUrl,port:41377,composition:comps.find(c=>c.id==='PuppetAtlasV4'),puppeteerInstance:browser,output:path.join(here,'qa/puppet_atlas.jpg'),imageFormat:'jpeg',jpegQuality:90,overwrite:true,logLevel:'error'});
  const shots=mode==='preview'?data.shots.filter((s,i)=>i<20||i%8===0):data.shots;
  // Two positions per cut expose pose and framing changes; all files stay in this lane.
  let completed=0;
  await Promise.all(Array.from({length:5},(_,worker)=>(async()=>{
   for(let j=worker;j<shots.length;j+=5){const s=shots[j];
    for(const frac of mode==='qa'?[.27,.73]:[.5]){
     const frame=s.start+Math.floor((s.end-s.start)*frac);const file=path.join(here,'qa',`${s.id}_${frac<.5?'a':'b'}.jpg`);
     await renderStill({serveUrl,port:42470+worker,composition:comp,puppeteerInstance:browser,frame,scale:.5,output:file,imageFormat:'jpeg',jpegQuality:87,overwrite:true,logLevel:'error'});
    }
    completed++;if(completed%10===0)console.log('preview',completed,'/',shots.length);
   }
  })()));
 }else if(mode==='sample'){
  await renderMedia({serveUrl,port:41377,composition:comp,puppeteerInstance:browser,outputLocation:path.join(here,'sample_12s.mp4'),frameRange:[0,359],codec:'h264',crf:19,x264Preset:'fast',concurrency:5,overwrite:true,logLevel:'error'});
 }else if(mode==='final'){
  let last=0;
  await renderMedia({serveUrl,port:41377,composition:comp,puppeteerInstance:browser,outputLocation:path.join(here,'lf2_cartoon_v4_1080p.mp4'),codec:'h264',crf:18,x264Preset:'medium',pixelFormat:'yuv420p',audioCodec:'aac',audioBitrate:'192k',sampleRate:48000,concurrency:6,overwrite:true,logLevel:'error',onProgress:p=>{if(Date.now()-last>15000){console.log('rendered',p.renderedFrames,'encoded',p.encodedFrames,'/',comp.durationInFrames);last=Date.now()}}});
 }
}finally{await browser.close({silent:true})}
