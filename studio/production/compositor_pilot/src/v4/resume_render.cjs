// Resume only the tail lost in the provider interruption. All new files stay in W.
require('./offline.cjs');
const path=require('node:path'),fs=require('node:fs');
const {selectComposition,renderMedia}=require('@remotion/renderer');
const root=path.resolve(__dirname,'../..'),ep=path.resolve(root,'../../episodes/v4/n18'),out=path.join(ep,'out');
(async()=>{
 const start=new Date().toISOString(),t=performance.now();fs.writeFileSync(path.join(out,'resume.pid'),String(process.pid));
 const serveUrl=path.join(ep,'build/resume-bundle');
 const browserExecutable=path.join(root,'node_modules/.remotion/chrome-headless-shell/mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell');const inputProps={audio:false};
 const composition=await selectComposition({serveUrl,id:'V4N18-FULL',browserExecutable,inputProps});
 await renderMedia({serveUrl,composition,browserExecutable,inputProps,frameRange:[9720,composition.durationInFrames-1],outputLocation:path.join(ep,'build/tail.mp4'),codec:'h264',crf:16,x264Preset:'fast',pixelFormat:'yuv420p',colorSpace:'bt709',muted:true,concurrency:8,imageFormat:'jpeg',jpegQuality:95,onProgress:p=>{if(p.renderedFrames%100===0||p.progress===1)console.log(JSON.stringify({rendered:p.renderedFrames,progress:p.progress}))}});
 const end=new Date().toISOString(),resumeSeconds=(performance.now()-t)/1000;
 fs.writeFileSync(path.join(out,'render-time.json'),JSON.stringify({start:'2026-10-26T11:37:49.451Z',end,wall_seconds:1381.0+resumeSeconds,original_render_active_seconds:1381.0,resumed_tail_seconds:resumeSeconds,resumed_start:start,interruption_start:'2026-10-26T12:00:50Z',resumption_at:'2026-10-26T12:16:48Z',provider_interruption_seconds:958,frames:composition.durationInFrames,recovered_frames:9720,rerendered_tail_frames:composition.durationInFrames-9720,crf:16,codec:'h264',preset:'fast',recovery:'Encoded AVC data recovered from unfinished mdat; only unfinished tail rendered'},null,2));console.log('TAIL COMPLETE');
})().catch(e=>{console.error(e);process.exitCode=1});
