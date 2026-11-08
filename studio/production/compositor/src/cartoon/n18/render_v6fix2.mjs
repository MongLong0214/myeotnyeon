import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {openBrowser,getCompositions,renderStill,renderMedia} from '@remotion/renderer';
const here=path.dirname(fileURLToPath(import.meta.url)),W=path.resolve(here,'../../../../..'),out=path.join(W,'episodes/v4/n18/cartoon_v6');
const mode=process.argv[2]??'stills',port=41729;
process.env.TMPDIR=path.join(out,'tmp_v6fix2');fs.mkdirSync(process.env.TMPDIR,{recursive:true});
const data=JSON.parse(fs.readFileSync(path.join(out,'episode_data_v6fix2.json'),'utf8'));
const folder=path.join(out,'fix2_stills');fs.mkdirSync(folder,{recursive:true});
const serveUrl=await bundle({entryPoint:path.join(here,'index_v6fix2.tsx'),outDir:path.join(out,'bundle_v6fix2'),publicDir:path.join(out,'public_v6fix2'),enableCaching:false,gitSource:null,webpackOverride:c=>({...c,cache:false})});
const browser=await openBrowser('chrome',{browserExecutable:path.join(here,'../chrome_offline.sh'),logLevel:'error'});
try{
 const comp=(await getCompositions(serveUrl,{puppeteerInstance:browser,port})).find(c=>c.id==='N18CartoonV6Fix2');console.log(JSON.stringify(comp));
 if(mode==='stills'){
  const ids=process.argv[3]?.split(',');
  const selected=ids?data.shots.filter(s=>ids.includes(s.id)):data.shots;
  for(const [i,s] of selected.entries()){
   await renderStill({serveUrl,composition:comp,port,puppeteerInstance:browser,frame:Math.floor((s.start+s.end)/2),output:path.join(folder,s.id+'.jpg'),imageFormat:'jpeg',jpegQuality:90,scale:.4,overwrite:true,logLevel:'error'});
   if(i%15===0)console.log('still',i+1,'/',data.shots.length);
  }
 }else{
  const patch=mode==='patch'?data.shots.find(s=>s.id===process.argv[3]):null;
  if(mode==='patch'&&!patch)throw Error('Unknown patch shot');
  let last=0;await renderMedia({serveUrl,composition:comp,port,puppeteerInstance:browser,outputLocation:path.join(out,patch?patch.id+'_fix2_patch.mp4':mode==='preview'?'v6fix2_preview.mp4':'picture_v6fix2_1080p.mp4'),...(patch?{frameRange:[patch.start,patch.end-1]}:mode==='preview'?{frameRange:[0,1799]}:{}),codec:'h264',crf:18,x264Preset:'fast',pixelFormat:'yuv420p',muted:true,concurrency:3,overwrite:true,logLevel:'error',onProgress:p=>{if(p.renderedFrames-last>=450){last=p.renderedFrames;console.log('frames',p.renderedFrames,'encoded',p.encodedFrames)}}});
 }
}finally{await browser.close({silent:true});}
