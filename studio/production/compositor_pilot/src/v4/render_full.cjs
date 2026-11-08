// Existing dependencies only. Local file/stdio transport, no listening socket.
require('./offline.cjs');
const path=require('node:path'),fs=require('node:fs');
const {renderMedia,selectComposition}=require('@remotion/renderer');
const root=path.resolve(__dirname,'../..');
const out=path.resolve(root,'../../episodes/v4/n18/out');
(async()=>{
 const started=new Date().toISOString(),t=performance.now();
 const serveUrl=path.join(root,'build');
 const browserExecutable=path.join(root,'src/v4spike/chromium.sh');
 const composition=await selectComposition({serveUrl,id:'V4N18-FULL',browserExecutable,inputProps:{audio:false}});
 await renderMedia({inputProps:{audio:false},composition,serveUrl,browserExecutable,outputLocation:path.join(out,'_picture.mp4'),codec:'h264',crf:16,x264Preset:'fast',pixelFormat:'yuv420p',colorSpace:'bt709',muted:true,concurrency:8,imageFormat:'jpeg',jpegQuality:95,onProgress:p=>{if(p.renderedFrames%100===0||p.progress===1)process.stdout.write(JSON.stringify({rendered:p.renderedFrames,encoded:p.encodedFrames,progress:p.progress})+'\n')}});
 fs.writeFileSync(path.join(out,'render-time.json'),JSON.stringify({start:started,end:new Date().toISOString(),wall_seconds:(performance.now()-t)/1000,frames:composition.durationInFrames,crf:16,concurrency:8,codec:'h264',preset:'fast'},null,2));
 console.log('RENDER COMPLETE');
})().catch(e=>{console.error(e);process.exitCode=1});
