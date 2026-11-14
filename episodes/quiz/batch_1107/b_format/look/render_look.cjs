// usage: node look/render_look.cjs <qid> <BEFORE|LOOK> <from-to:out.mp4>[,<from-to:out.mp4>...]   (video ranges)
//        node look/render_look.cjs <qid> <BEFORE|LOOK> stills <outDir> <f1,f2,...>
const path=require('node:path'),fs=require('node:fs');
const B=path.resolve(__dirname,'..'),W=path.resolve(B,'../../../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
const {bundle}=req('@remotion/bundler'),{selectComposition,renderMedia,renderStill}=req('@remotion/renderer');
(async()=>{
 const [q,id,jobs,a4,a5]=process.argv.slice(2),c=JSON.parse(fs.readFileSync(path.join(W,'upload/pkg',q+'_B','case.json')));
 const outDir=path.join(__dirname,'_bundle_'+q+'_'+id+'_'+process.pid);
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'entry.tsx'),outDir,publicDir:path.join(B,'public'),webpackOverride:config=>({...config,cache:false,resolve:{...config.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})});
 const opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),inputProps:{c},logLevel:'error'};
 const composition=await selectComposition({...opts,id});
 try{
  if(jobs==='stills'){fs.mkdirSync(a4,{recursive:true});for(const fr of a5.split(',').map(Number))await renderStill({...opts,composition,frame:fr,output:path.join(a4,`${id}_f${String(fr).padStart(4,'0')}.png`),imageFormat:'png'});console.log('STILLS');return;}
  for(const j of jobs.split(',')){const [r,out]=j.split(':'),[from,to]=r.split('-').map(Number),t=Date.now();
   await renderMedia({...opts,composition,frameRange:[from,to],outputLocation:out,codec:'h264',crf:14,pixelFormat:'yuv420p',muted:true,concurrency:4});
   console.log('DONE',id,q,from,to,((Date.now()-t)/1000).toFixed(1)+'s',(((Date.now()-t)/(to-from+1))).toFixed(0)+'ms/frame');}
 }finally{fs.rmSync(outDir,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1)});
