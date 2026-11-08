import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {openBrowser,getCompositions,renderStill,renderMedia} from '@remotion/renderer';
const here=path.dirname(fileURLToPath(import.meta.url)),W=path.resolve(here,'../../../../..'),out=path.join(W,'episodes/v4/n18/cartoon_v5');
if(!fs.existsSync(path.join(here,'../engine_v5/READY_ENGINE.txt')))throw Error('Wait for Task E engine v5 READY.');
const mode=process.argv[2]??'stills';const port=mode==='stills'?41418:mode==='preview'?41419:mode==='patch'?41421:41420;
process.env.TMPDIR=path.join(out,'tmp');fs.mkdirSync(process.env.TMPDIR,{recursive:true});
const data=JSON.parse(fs.readFileSync(path.join(out,'episode_data.json'),'utf8'));
fs.mkdirSync(path.join(out,'qa_frames'),{recursive:true});
const serveUrl=await bundle({entryPoint:path.join(here,'index.tsx'),outDir:path.join(out,'bundle_'+mode),publicDir:path.join(out,'public'),enableCaching:false,gitSource:null,webpackOverride:c=>({...c,cache:false})});
const browser=await openBrowser('chrome',{browserExecutable:path.join(here,'../chrome_offline.sh'),logLevel:'error'});
try{
 const comps=await getCompositions(serveUrl,{puppeteerInstance:browser,port});const comp=comps.find(c=>c.id==='N18CartoonV5');console.log(JSON.stringify(comp));
 if(mode==='stills'){
  for(const [i,s] of data.shots.entries()){
   const dest=path.join(out,'qa_frames',s.id+'.jpg');
   await renderStill({serveUrl,composition:comp,port,puppeteerInstance:browser,frame:Math.floor(s.start+(s.end-s.start)*.54),output:dest,imageFormat:'jpeg',jpegQuality:84,scale:.333333,overwrite:true,logLevel:'error'});
   if(i%25===0)console.log('still',i+1,'/',data.shots.length);
  }
 }else{
  const preview=mode==='preview',patch=mode==='patch';let last=0;
  const patchId=process.argv[3]??'N019';const patchShots=data.shots.filter(s=>s.narrationId===patchId);const patchStart=patchShots[0].start,patchEnd=patchShots[patchShots.length-1].end-1;
  await renderMedia({serveUrl,composition:comp,port,puppeteerInstance:browser,outputLocation:path.join(out,patch?patchId+'_patch.mp4':preview?'first60_v1.mp4':'n18_cartoon_v5_1080p.mp4'),...(preview?{frameRange:[0,1799]}:patch?{frameRange:[patchStart,patchEnd]}:{}),codec:'h264',crf:18,x264Preset:'fast',pixelFormat:'yuv420p',audioCodec:'aac',audioBitrate:'192k',sampleRate:48000,concurrency:3,overwrite:true,logLevel:'error',onProgress:p=>{if(p.renderedFrames-last>=300){last=p.renderedFrames;console.log('frames',p.renderedFrames,'encoded',p.encodedFrames)}}});
 }
}finally{await browser.close({silent:true});}
