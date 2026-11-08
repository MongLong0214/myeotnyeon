const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../../..'),root=path.join(W,'production/compositor');
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
 const [mode,q='q009',...frames]=process.argv.slice(2),work=__dirname;
 const serveUrl=mode==='before'||mode==='bundle'?await bundle({entryPoint:path.join(root,'src/v52/indexFinal.ts'),outDir:path.join(work,`bundle_${mode==='before'?'before':'v52_final'}`),publicDir:path.join(root,'public')}):path.join(work,'bundle_v52_final');
 if(mode==='bundle')return;
 const inputProps={};
 const opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),inputProps,logLevel:mode==='audit'?'verbose':'error'};
 const composition=await selectComposition({...opts,id:(['before','after','baseline'].includes(mode)?'':mode==='audit'?'V52-AUDIT-':'V52-')+q.toUpperCase()});
 if(['before','after','stills','baseline'].includes(mode)){
  for(const frame of (frames.length?frames.map(Number):[0,45,900])){
   const output=path.join(work,`${mode}${process.env.V52_REV||''}_${q}/${frame}.png`);if(fs.existsSync(output))throw Error(`Refusing overwrite ${output}`);
   await renderStill({...opts,composition,frame,output,imageFormat:'png'});
  }
 }else{
  const outputLocation=path.join(W,mode==='audit'?`episodes/quiz/${q}/v52/audit${process.env.V52_REV||''}.mp4`:`episodes/quiz/${q}/v52/candidate${process.env.V52_REV||''}.mp4`);
  if(fs.existsSync(outputLocation))throw Error(`Refusing overwrite ${outputLocation}`);
  fs.mkdirSync(path.dirname(outputLocation),{recursive:true});
  await renderMedia({...opts,composition,outputLocation,codec:'h264',crf:14,pixelFormat:'yuv420p',colorSpace:'bt709',audioBitrate:'320k',scale:mode==='audit'?.25:1,muted:mode==='audit',concurrency:mode==='audit'?2:3,onBrowserLog:l=>{if(l.text?.includes('AUDIT')||l.text?.includes('HOOKCHECK'))console.log(l.text)},onProgress:p=>{if(p.renderedFrames%150===0||p.progress===1)console.log(JSON.stringify({rendered:p.renderedFrames,progress:p.progress}))}});
 }
 console.log('DONE',mode,q,composition.durationInFrames);
})().catch(e=>{console.error(e);process.exitCode=1});
