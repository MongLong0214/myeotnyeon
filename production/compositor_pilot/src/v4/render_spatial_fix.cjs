require('./offline.cjs');
const path=require('node:path'),fs=require('node:fs');
const {bundle}=require('@remotion/bundler');const {selectComposition,renderMedia,renderStill}=require('@remotion/renderer');
(async()=>{
 const root=path.resolve(__dirname,'../..'),out=path.resolve(root,'../../episodes/v4/n18/out');
 const serveUrl=await bundle({entryPoint:path.join(root,'src/index.ts'),outDir:'/private/tmp/n18-stage2/corrected',publicDir:path.join(root,'public')});
 const browserExecutable=path.join(root,'src/v4spike/chromium.sh'),inputProps={audio:false};
 const composition=await selectComposition({serveUrl,id:'V4N18-FULL',browserExecutable,inputProps});
 await renderStill({composition,serveUrl,browserExecutable,inputProps,frame:230,output:path.join(out,'spatial-corrected.png')});
 const t=performance.now();await renderMedia({composition,serveUrl,browserExecutable,inputProps,outputLocation:path.join(out,'_spatial.mp4'),codec:'h264',crf:16,x264Preset:'fast',pixelFormat:'yuv420p',colorSpace:'bt709',muted:true,concurrency:3,frameRange:[195,392],imageFormat:'jpeg',jpegQuality:95});
 fs.writeFileSync(path.join(out,'spatial-render-time.json'),JSON.stringify({seconds:(performance.now()-t)/1000,frames:198},null,2));console.log('SPATIAL COMPLETE');
})().catch(e=>{console.error(e);process.exitCode=1});
