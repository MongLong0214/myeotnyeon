const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../../../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
// File assets only: preserve Remotion's audio mix, with no HTTP fallback.
req('./node_modules/@remotion/renderer/dist/assets/download-file.js').downloadFile=async ({url,to,onProgress})=>{
 if(!url.startsWith('file://'))throw Error(`Network asset blocked: ${url}`);
 const src=require('node:url').fileURLToPath(url),out=to(null,'audio/wav');
 fs.mkdirSync(path.dirname(out),{recursive:true});fs.copyFileSync(src,out);
 const sizeInBytes=fs.statSync(out).size;onProgress?.({downloaded:sizeInBytes,totalSize:sizeInBytes,percent:1});return {sizeInBytes,to:out};
};
const {bundle}=req('@remotion/bundler');
const {selectComposition,renderStill,renderMedia,getCompositions}=req('@remotion/renderer');
(async()=>{
 const mode=process.argv[2],work=__dirname,serveUrl=await bundle({entryPoint:mode==='strict'?path.join(work,'strict.tsx'):path.join(root,'src/index.ts'),outDir:path.join(work,`bundle_${mode}`),publicDir:path.join(root,'public')});
 const browserExecutable=path.join(root,'src/v4spike/chromium.sh');
 const inputProps=mode==='before'||mode==='after'?{}:{quizStyle:'premium',typeStyle:'type2'};
 const opts={serveUrl,browserExecutable,inputProps,logLevel:['audit','strict'].includes(mode)?'verbose':'error'};
 const composition=await selectComposition({...opts,id:mode==='strict'?'STRICT-Q006':mode==='audit'?'AUDIT-Q006':'Q006'});
 if(mode==='before'||mode==='after'){
  const meta=await getCompositions(opts);fs.writeFileSync(path.join(work,`compositions_${mode}.json`),JSON.stringify(meta,null,2));
  for(const frame of [90,570,850])await renderStill({...opts,composition,frame,output:path.join(work,`default_${mode}/${frame}.png`),imageFormat:'png'});
 } else if(mode==='stills'){
  for(const frame of [90,570,620,680,725,768,810,850,920,975])await renderStill({...opts,composition,frame,output:path.join(work,`type2_${frame}.png`),imageFormat:'png'});
 } else {
  const outputLocation=path.join(W,mode==='strict'?'episodes/quiz/q006/audit_v3d/strict.mp4':mode==='audit'?'episodes/quiz/q006/audit_v3d/q006.mp4':'upload/v3d_q006.mp4');
  if(fs.existsSync(outputLocation))throw Error(`Refusing to overwrite ${outputLocation}`);
  fs.mkdirSync(path.dirname(outputLocation),{recursive:true});
  await renderMedia({...opts,composition,outputLocation,codec:'h264',crf:14,pixelFormat:'yuv420p',colorSpace:'bt709',audioBitrate:'320k',scale:['audit','strict'].includes(mode)?.25:1,muted:['audit','strict'].includes(mode),concurrency:6,onProgress:p=>{if(p.renderedFrames%100===0||p.progress===1)console.log(JSON.stringify({rendered:p.renderedFrames,encoded:p.encodedFrames,progress:p.progress}))}});
 }
 console.log('DONE',mode,composition.durationInFrames);
})().catch(e=>{console.error(e);process.exitCode=1});
