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
 const serveUrl=mode==='before'||mode==='bundle'?await bundle({entryPoint:path.join(root,'src/v52_candidates/indexRevised.ts'),outDir:path.join(work,`bundle_${mode==='before'?'before':'v52_revised'}`),publicDir:path.join(root,'public')}):path.join(work,'bundle_v52_revised');
 if(mode==='bundle')return;
 const inputProps={};
 const opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),inputProps,logLevel:mode.startsWith('audit')?'verbose':'error'};
 const composition=await selectComposition({...opts,id:(mode==='cover'?'COVER52-':['before','after','baseline'].includes(mode)?'':mode.startsWith('audit')?'V52-AUDIT-':'V52-')+q.toUpperCase()});
 if(mode==='cover'){
 const output=path.join(W,`upload/cover_v52_${q}.jpg`);if(fs.existsSync(output))throw Error('exists '+output);
 await renderStill({...opts,composition,frame:0,output,imageFormat:'jpeg',jpegQuality:95});
 }else if(['before','after','stills','baseline'].includes(mode)){
  for(const frame of (frames.length?frames.map(Number):[0,45,900])){
   const output=path.join(work,`${mode}${process.env.V52_REV||''}_${q}/${frame}.png`);if(fs.existsSync(output))throw Error(`Refusing overwrite ${output}`);
   await renderStill({...opts,composition,frame,output,imageFormat:'png'});
  }
 }else{
  const outputLocation=path.join(W,mode.startsWith('audit-')?`episodes/quiz/${q}/v52/${mode}_revised.mp4`:mode==='audit'?`episodes/quiz/${q}/v52/audit${process.env.V52_REV||''}.mp4`:`episodes/quiz/${q}/v52/candidate${process.env.V52_REV||''}.mp4`);
  if(fs.existsSync(outputLocation))throw Error(`Refusing overwrite ${outputLocation}`);
  fs.mkdirSync(path.dirname(outputLocation),{recursive:true});
  await renderMedia({...opts,composition,outputLocation,...(mode==='audit-tail'?{frameRange:[875,928]}:mode==='audit-hook'?{frameRange:[0,60]}:mode==='audit-end'?{frameRange:[755,799]}:{}),codec:'h264',crf:14,pixelFormat:'yuv420p',colorSpace:'bt709',audioBitrate:'320k',scale:mode.startsWith('audit')?.25:1,muted:mode.startsWith('audit'),concurrency:mode==='audit'?2:3,onBrowserLog:l=>{if(l.text?.includes('AUDIT')||l.text?.includes('HOOKCHECK'))console.log(l.text)},onProgress:p=>{if(p.renderedFrames%150===0||p.progress===1)console.log(JSON.stringify({rendered:p.renderedFrames,progress:p.progress}))}});
 }
 console.log('DONE',mode,q,composition.durationInFrames);
})().catch(e=>{console.error(e);process.exitCode=1});
