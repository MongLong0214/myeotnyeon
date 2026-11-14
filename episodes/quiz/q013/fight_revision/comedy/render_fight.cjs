const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../../../../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
req('./node_modules/@remotion/renderer/dist/assets/download-file.js').downloadFile=async ({url,to,onProgress})=>{
 if(!url.startsWith('file://'))throw Error(`Network asset blocked: ${url}`);
 const src=require('node:url').fileURLToPath(url),out=to(null,'audio/wav');fs.mkdirSync(path.dirname(out),{recursive:true});fs.copyFileSync(src,out);const sizeInBytes=fs.statSync(out).size;onProgress?.({downloaded:sizeInBytes,totalSize:sizeInBytes,percent:1});return{sizeInBytes,to:out};
};
const {bundle}=req('@remotion/bundler');const {selectComposition,renderStill,renderMedia}=req('@remotion/renderer');
(async()=>{
 const mode=process.argv[2]||'stills';let out,serveUrl;
 if(mode==='stills'){
  out=path.join(__dirname,'render_'+new Date().toISOString().replace(/[:.]/g,'-'));fs.mkdirSync(out);
  serveUrl=await bundle({entryPoint:path.join(__dirname,'entry.tsx'),outDir:path.join(out,'bundle'),publicDir:path.join(W,'episodes/quiz/v52_q013_q014_support/bundle_v52_revised/public'),webpackOverride:config=>({...config,cache:false,resolve:{...config.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})});
  fs.writeFileSync(path.join(out,'render_state.json'),JSON.stringify({out,serveUrl}));console.log('OUTPUT',out);
 }else{
  out=path.resolve(process.argv[3]);serveUrl=JSON.parse(fs.readFileSync(path.join(out,'render_state.json'))).serveUrl;
 }
 const opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),inputProps:{},logLevel:'error'};
 const composition=await selectComposition({...opts,id:mode==='audit'?'AUDIT':'VIDEO'});
 if(composition.width!==1080||composition.height!==1920||composition.fps!==30||composition.durationInFrames!==800)throw Error('Composition changed');
 if(mode==='stills'){
  for(const frame of [61,67,73,77,82,85,139,163,174,180,195,225,285,360,450,550,630,668,669,670,675,676,709,710,754,755]){
   await renderStill({...opts,composition,frame,output:path.join(out,`preview_f${String(frame).padStart(4,'0')}.png`),imageFormat:'png'});console.log('STILL',frame);
  }
  const coverComp=await selectComposition({...opts,id:'COVER'});
  await renderStill({...opts,composition:coverComp,frame:0,output:path.join(out,'cover_candidate.jpg'),imageFormat:'jpeg',jpegQuality:95});console.log('COVER');
 }else{
  const outputLocation=path.join(out,mode==='audit'?'audit.mp4':'video_muted.mp4');if(fs.existsSync(outputLocation))throw Error('Output exists');
  await renderMedia({...opts,composition,logLevel:mode==='audit'?'verbose':'error',...(mode==='audit'?{frameRange:[61,754]}:{frameRange:[61,754]}),outputLocation,codec:'h264',crf:14,pixelFormat:'yuv420p',colorSpace:'bt709',muted:true,concurrency:2,scale:mode==='audit'?.25:1,onProgress:p=>{if(p.renderedFrames%100===0||p.progress===1)console.log(JSON.stringify({rendered:p.renderedFrames,progress:p.progress}))},onBrowserLog:l=>{if(mode==='audit'&&(l.text?.includes('AUDIT')||l.text?.includes('HOOKCHECK')))console.log(l.text)}});
  console.log('DONE',outputLocation);
 }
})().catch(e=>{console.error(e);process.exitCode=1});
