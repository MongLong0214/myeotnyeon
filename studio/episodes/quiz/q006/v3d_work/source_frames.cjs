const path=require('node:path'),fs=require('node:fs'),crypto=require('node:crypto');
const W=path.resolve(__dirname,'../../../..'),root=path.join(W,'production/compositor'),P=__dirname;
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
// File assets only: preserve Remotion's audio mix, with no HTTP fallback.
req('./node_modules/@remotion/renderer/dist/assets/download-file.js').downloadFile=async ({url,to,onProgress})=>{
 if(!url.startsWith('file://'))throw Error(`Network asset blocked: ${url}`);
 const src=require('node:url').fileURLToPath(url),out=to(null,'audio/wav');
 fs.mkdirSync(path.dirname(out),{recursive:true});fs.copyFileSync(src,out);
 const sizeInBytes=fs.statSync(out).size;onProgress?.({downloaded:sizeInBytes,totalSize:sizeInBytes,percent:1});return {sizeInBytes,to:out};
};
const {selectComposition,renderFrames}=req('@remotion/renderer');
(async()=>{
 const serveUrl=path.join(P,'bundle_render'),inputProps={quizStyle:'premium',typeStyle:'type2'},browserExecutable=path.join(root,'src/v4spike/chromium.sh');
 const opts={serveUrl,inputProps,browserExecutable,logLevel:'error'};
 const comp=await selectComposition({...opts,id:'Q006'}),reports={};
 for(const version of ['v3c','v3d']){
  const doc=JSON.parse(fs.readFileSync(version==='v3c'?path.join(P,'render.json.before'):path.join(root,'public/q006/render.json'),'utf8'));
  const hashes={};
  await renderFrames({...opts,composition:{...comp,props:{...comp.props,doc}},imageFormat:'png',outputDir:null,muted:true,concurrency:6,
   onStart:()=>{},onFrameUpdate:n=>{if(n%200===0)console.log(version,n)},onFrameBuffer:(buffer,frame)=>{hashes[frame]=crypto.createHash('sha256').update(buffer).digest('hex');if(frame===725||frame===764)fs.writeFileSync(path.join(P,`${version}_source_${frame}.png`),buffer)}});
  reports[version]=hashes;fs.writeFileSync(path.join(P,`${version}_source_frames.json`),JSON.stringify(hashes,null,2));
 }
 const different=Array.from({length:998},(_,i)=>i).filter(f=>reports.v3c[f]!==reports.v3d[f]);
 const r={frames_compared:998,method:'Full-resolution lossless PNG buffers from the same v3c renderer and props, before H.264 encoding; original render.json versus only the authorized card substitution.',card_interval_inclusive:[700,763],different_frames:different,outside_card_differences:different.filter(f=>f<700||f>=764),only_card_frames_differ:different.length===64&&different.every(f=>f>=700&&f<764)};
 fs.writeFileSync(path.join(P,'source_frame_compare.json'),JSON.stringify(r,null,2));console.log(JSON.stringify(r));
})().catch(e=>{console.error(e);process.exitCode=1});
