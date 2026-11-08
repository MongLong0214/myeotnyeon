import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {openBrowser,getCompositions,renderStill,renderMedia} from '@remotion/renderer';
const here=path.dirname(fileURLToPath(import.meta.url)),W=path.resolve(here,'../../../../..'),out=path.join(W,'episodes/v4/n18/cartoon_v4');
process.env.TMPDIR=path.join(out,'tmp');fs.mkdirSync(process.env.TMPDIR,{recursive:true});
const mode=process.argv[2]??'preview';const port=mode==='preview'?41378:mode==='test'?41379:mode==='fixes'?41381:mode==='patch'?41382:41380;const engine=path.join(here,'../engine_v4/READY_ENGINE.txt');
if(!fs.existsSync(engine))throw Error('Engine v4 has not announced READY; waiting lane must poll before rendering.');
const data=JSON.parse(fs.readFileSync(path.join(out,'shots.json'),'utf8'));
const serveUrl=await bundle({entryPoint:path.join(here,'index.tsx'),outDir:path.join(out,'bundle_'+mode),publicDir:path.join(out,'public'),enableCaching:false,gitSource:null,webpackOverride:c=>({...c,cache:false})});
const browser=await openBrowser('chrome',{browserExecutable:path.join(here,'../chrome_offline.sh'),logLevel:'error'});
try{
 const comps=await getCompositions(serveUrl,{puppeteerInstance:browser,port});const comp=comps.find(c=>c.id==='N18CartoonV4');console.log(JSON.stringify(comp));
 if(mode==='preview'||mode==='fixes'){
  const subset=mode==='fixes'?data.shots.filter(s=>['clock','timeline','calendar','witness','defendant','defendants','sentence-deputy'].includes(s.view)||(s.narrator_visible&&s.set==='courtroom')):process.argv[3]==='sample'?data.shots.filter((s,i)=>i%11===0||['witness','command','sentence-appeal','memorial'].includes(s.view)):data.shots;
  for(const [i,s] of subset.entries()){
   for(const q of [.28,.72]){
    const frame=Math.floor(s.start+(s.end-s.start)*q),dest=path.join(out,'qa',`${s.id}_${q<.5?'a':'b'}.jpg`);
    if(mode==='fixes'||!fs.existsSync(dest))await renderStill({serveUrl,composition:comp,port,puppeteerInstance:browser,frame,output:dest,imageFormat:'jpeg',jpegQuality:85,scale:.5,overwrite:true,logLevel:'error'});
   }
   console.log('preview',i+1,'/',subset.length,s.id,s.view);
  }
 }else if(mode==='patch'){
  await renderMedia({serveUrl,composition:comp,port,puppeteerInstance:browser,outputLocation:path.join(out,'qa/C158_patch.mp4'),frameRange:[10846,10913],codec:'h264',crf:16,x264Preset:'fast',pixelFormat:'yuv420p',audioCodec:'aac',concurrency:2,overwrite:true,logLevel:'error'});
 }else if(mode==='test'){
  await renderMedia({serveUrl,composition:comp,port,puppeteerInstance:browser,outputLocation:path.join(out,'qa/test_12s.mp4'),frameRange:[0,359],codec:'h264',crf:20,x264Preset:'fast',pixelFormat:'yuv420p',audioCodec:'aac',concurrency:3,overwrite:true,logLevel:'error'});
 }else if(mode==='final'){
  let last=0;await renderMedia({serveUrl,composition:comp,port,puppeteerInstance:browser,outputLocation:path.join(out,'n18_cartoon_v4_1080p.mp4'),codec:'h264',crf:18,x264Preset:'fast',pixelFormat:'yuv420p',audioCodec:'aac',audioBitrate:'192k',sampleRate:48000,concurrency:4,overwrite:true,logLevel:'error',onProgress:p=>{if(p.renderedFrames-last>=300){last=p.renderedFrames;console.log('frames',p.renderedFrames,'encoded',p.encodedFrames)}}});
 }
}finally{await browser.close({silent:true});}
