const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../../../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
req('./node_modules/@remotion/renderer/dist/assets/download-file.js').downloadFile=async ({url,to,onProgress})=>{
 if(!url.startsWith('file://'))throw Error(`Network asset blocked: ${url}`);
 const src=require('node:url').fileURLToPath(url),out=to(null,'audio/wav');
 fs.mkdirSync(path.dirname(out),{recursive:true});fs.copyFileSync(src,out);
 const sizeInBytes=fs.statSync(out).size;onProgress?.({downloaded:sizeInBytes,totalSize:sizeInBytes,percent:1});return {sizeInBytes,to:out};
};
const {bundle}=req('@remotion/bundler');
const {selectComposition,renderStill,renderMedia}=req('@remotion/renderer');
(async()=>{
 const work=path.join(W,'episodes/quiz/q013/v52_n16');
 const mode=process.argv[2] || 'bundle';
 const serveUrl=mode==='bundle'?await bundle({entryPoint:path.join(root,'src/v52_n16/index.tsx'),outDir:path.join(work,'bundle_local'),publicDir:path.join(W,'episodes/quiz/v52_q013_q014_support/bundle_v52_revised/public')}):path.join(work,'bundle_local');
 if(mode==='bundle')return;
 const opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),inputProps:{},logLevel:'error'};
 const composition=await selectComposition({...opts,id:'V52-Q013-N16'});
 if(mode==='preview'){for(const frame of [61,160,200,240,260,300,328,770])await renderStill({...opts,composition,frame,output:path.join(work,`preview_${frame}.png`),imageFormat:'png'});return;}
 if(mode==='final'){
 const outputLocation=path.join(work,'video_muted.mp4');
 if(fs.existsSync(outputLocation))throw Error('exists '+outputLocation);
 await renderMedia({...opts,composition,outputLocation,codec:'h264',crf:14,pixelFormat:'yuv420p',colorSpace:'bt709',muted:true,concurrency:3,onProgress:p=>{if(p.renderedFrames%150===0||p.progress===1)console.log(JSON.stringify({rendered:p.renderedFrames,progress:p.progress}))}});
 const cover=await selectComposition({...opts,id:'COVER-Q013-N16'});
 await renderStill({...opts,composition:cover,frame:0,output:path.join(W,'upload/cover_v52_q013_n16.jpg'),imageFormat:'jpeg',jpegQuality:95});
 return;}
 const audit=await selectComposition({...opts,id:'AUDIT-Q013-N16'});
 await renderMedia({...opts,composition:audit,logLevel:'verbose',outputLocation:path.join(work,'audit.mp4'),codec:'h264',crf:14,pixelFormat:'yuv420p',colorSpace:'bt709',scale:.25,muted:true,concurrency:2,onBrowserLog:l=>{if(l.text?.includes('AUDIT')||l.text?.includes('HOOKCHECK'))console.log(l.text)}});
 console.log('DONE',mode,composition.durationInFrames);
})().catch(e=>{console.error(e);process.exitCode=1});
