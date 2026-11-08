import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {openBrowser,getCompositions,renderStill,renderMedia} from '@remotion/renderer';
const here=path.dirname(fileURLToPath(import.meta.url)),W=path.resolve(here,'../../../../..'),out=path.join(W,'episodes/v4/n18/cartoon_v6');
if(!fs.existsSync(path.join(here,'../engine_v6/READY_ENGINE.txt')))throw Error('Engine v6 is not ready.');
const mode=process.argv[2]??'stills',port=mode==='stills'?41618:mode==='preview'?41619:mode==='check'?41621:mode==='patch'?41622:41620;
process.env.TMPDIR=path.join(out,'tmp');fs.mkdirSync(process.env.TMPDIR,{recursive:true});
const data=JSON.parse(fs.readFileSync(path.join(out,'episode_data.json'),'utf8'));
const folder=path.join(out,'qa_frames');fs.mkdirSync(folder,{recursive:true});
const serveUrl=await bundle({entryPoint:path.join(here,'index.tsx'),outDir:path.join(out,'bundle_'+mode),publicDir:path.join(out,'public'),enableCaching:false,gitSource:null,webpackOverride:c=>({...c,cache:false})});
const browser=await openBrowser('chrome',{browserExecutable:path.join(here,'../chrome_offline.sh'),logLevel:'error'});
try{
 const comp=(await getCompositions(serveUrl,{puppeteerInstance:browser,port})).find(c=>c.id==='N18CartoonV6');console.log(JSON.stringify(comp));
 if(mode==='stills'||mode==='check'){
  const selected=mode==='check'?data.shots.filter(s=>['H014','H015','H023','H027','H034','H038','H050','H051','H052','H053','H054','H061','H086','H092','H105','H142','H144','H145','H147','H149'].includes(s.id)):data.shots;
  for(const [i,s] of selected.entries()){
   await renderStill({serveUrl,composition:comp,port,puppeteerInstance:browser,frame:Math.floor((s.start+s.end)/2),output:path.join(folder,s.id+'.jpg'),imageFormat:'jpeg',jpegQuality:90,scale:1/3,overwrite:true,logLevel:'error'});
   if(i%20===0)console.log('still',i+1,'/',data.shots.length);
  }
 }else{
  const patch=mode==='patch'?data.shots.find(s=>s.id===(process.argv[3]??'H036')):null;
  let last=0;await renderMedia({serveUrl,composition:comp,port,puppeteerInstance:browser,outputLocation:path.join(out,patch?patch.id+'_patch.mp4':mode==='preview'?'first60.mp4':'n18_cartoon_v6_1080p.mp4'),...(patch?{frameRange:[patch.start,patch.end-1]}:mode==='preview'?{frameRange:[0,1799]}:{}),codec:'h264',crf:18,x264Preset:'fast',pixelFormat:'yuv420p',audioCodec:'aac',audioBitrate:'192k',sampleRate:48000,concurrency:3,overwrite:true,logLevel:'error',onProgress:p=>{if(p.renderedFrames-last>=600){last=p.renderedFrames;console.log('frames',p.renderedFrames,'encoded',p.encodedFrames)}}});
 }
}finally{await browser.close({silent:true});}
