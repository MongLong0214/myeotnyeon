import path from 'node:path';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {openBrowser,getCompositions,renderStill,renderMedia} from '@remotion/renderer';
const here=path.dirname(fileURLToPath(import.meta.url));
const W=path.resolve(here,'../../../..');
const out=path.join(W,'episodes/lf2_daejeon_bank/cartoon');
process.env.TMPDIR=path.join(out,'tmp');
const mode=process.argv[2]??'preview';
const revision=process.argv[3]??'v1';
const entry=process.argv[4]??'index.tsx';
const bundlePath=path.join(here,`bundle_${revision}`);
const browserExecutable=path.join(here,'chrome_offline.sh');
const serveUrl=fs.existsSync(bundlePath)?bundlePath:await bundle({entryPoint:path.join(here,entry),outDir:bundlePath,publicDir:path.join(out,'public'),enableCaching:false,gitSource:null,webpackOverride:c=>({...c,cache:false})});
const browser=await openBrowser('chrome',{browserExecutable,logLevel:'error'});
try{
 const comps=await getCompositions(serveUrl,{puppeteerInstance:browser,port:41373});
 const pilot=comps.find(c=>c.id==='CartoonPilot45');const atlas=comps.find(c=>c.id==='CartoonStyleSheet');
 const data=JSON.parse(fs.readFileSync(path.join(here,'pilot_data.json'),'utf8'));
 console.log('Compositions',comps.map(c=>({id:c.id,width:c.width,height:c.height,duration:c.durationInFrames})));
 if(mode==='preview'){
  const sheet=path.join(out,`qa/style_sheet_${revision}.png`);
  if(!fs.existsSync(sheet))await renderStill({serveUrl,port:41373,composition:atlas,puppeteerInstance:browser,output:sheet,overwrite:false,logLevel:'error'});
  // Two samples in every cut reveal poses and accidental intersections before final encoding.
  for(const [i,s] of data.shots.entries())for(const frac of [.28,.72]){
   const frame=Math.floor(s.start+(s.end-s.start)*frac);const dest=path.join(out,`qa/${revision}_${s.id}_${frac<.5?'a':'b'}.jpg`);
   if(!fs.existsSync(dest))await renderStill({serveUrl,port:41373,composition:pilot,puppeteerInstance:browser,frame,output:dest,imageFormat:'jpeg',jpegQuality:85,overwrite:false,logLevel:'error'});
   console.log('preview',i+1,frame);
  }
 }else if(mode==='final'){
  await renderStill({serveUrl,port:41373,composition:atlas,puppeteerInstance:browser,output:path.join(out,'style_sheet.png'),overwrite:false,logLevel:'error'});
  await renderMedia({serveUrl,port:41373,composition:pilot,puppeteerInstance:browser,outputLocation:path.join(out,'pilot_45s.mp4'),codec:'h264',crf:17,x264Preset:'medium',pixelFormat:'yuv420p',audioCodec:'aac',audioBitrate:'192k',sampleRate:48000,concurrency:5,overwrite:false,logLevel:'error',onProgress:p=>{if(p.renderedFrames%150===0)console.log('frames',p.renderedFrames,'encoded',p.encodedFrames);}});
 }
}finally{await browser.close({silent:true});}
