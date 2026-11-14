const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
const {bundle}=req('@remotion/bundler');const {selectComposition,renderStill,renderMedia}=req('@remotion/renderer');
(async()=>{
 const q=process.argv[2],mode=process.argv[3]||'stills',p=path.join(W,'upload/pkg',q+'_batch1107');
 const c=JSON.parse(fs.readFileSync(process.argv[4]||path.join(p,'case.json')));
 const bundleDir=path.join(__dirname,'bundle');
 let serveUrl;
 if(process.env.REBUNDLE||!fs.existsSync(path.join(bundleDir,'index.html'))){serveUrl=await bundle({entryPoint:path.join(__dirname,'entry.tsx'),outDir:bundleDir,publicDir:path.join(__dirname,'public'),webpackOverride:config=>({...config,cache:false,resolve:{...config.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})});}
 else serveUrl=bundleDir;
 const opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),inputProps:{c},logLevel:'error'};
 const composition=await selectComposition({...opts,id:'VIDEO'});
 if(mode==='stills'){
  for(const frame of [...(q==='q020'?[395,431,467,503,539,575,611,656,662,692,731]:[]),0,6,15,30,60,89,c.utterances[1].from_frame+15,c.utterances[2].from_frame+15,c.utterances[3].from_frame+15,c.utterances[5].from_frame+10,c.n-30]){
   await renderStill({...opts,composition,frame,output:path.join(p,`preview_${frame}.png`),imageFormat:'png'});
  }
  await renderStill({...opts,composition:await selectComposition({...opts,id:'COVER'}),frame:0,output:path.join(p,'cover.jpg'),imageFormat:'jpeg',jpegQuality:95});
 }else{
  await renderMedia({...opts,composition,outputLocation:path.join(mode==='animatic'?__dirname:p,mode==='animatic'?'animatic_q020_muted.mp4':'video_muted.mp4'),scale:mode==='animatic'?1/3:1,codec:'h264',crf:mode==='animatic'?28:16,pixelFormat:'yuv420p',colorSpace:'bt709',muted:true,concurrency:3,onProgress:p=>{if(p.renderedFrames%150===0||p.progress===1)console.log(q,p.renderedFrames,p.progress)}});
 }
 console.log('DONE',q,mode);
})().catch(e=>{console.error(e);process.exit(1)});
