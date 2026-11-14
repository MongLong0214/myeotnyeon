const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../../../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
const {bundle}=req('@remotion/bundler'),{selectComposition,renderStill,renderMedia}=req('@remotion/renderer');
(async()=>{
 const q=process.argv[2],mode=process.argv[3]||'preview',p=path.join(W,'upload/pkg',q+'_std'),c=JSON.parse(fs.readFileSync(path.join(p,'case.json')));
 const dir=path.join(__dirname,'bundle');
 const serveUrl=process.env.REBUNDLE||!fs.existsSync(path.join(dir,'index.html'))?await bundle({entryPoint:path.join(__dirname,'entry.tsx'),outDir:dir,publicDir:path.join(__dirname,'public'),webpackOverride:config=>({...config,cache:false,resolve:{...config.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})}):dir;
 const audit=[],opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),inputProps:{c,audit:mode==='preview'},logLevel:'error',onBrowserLog:l=>{if(l.text?.startsWith('CAPTION_LAYOUT '))audit.push(JSON.parse(l.text.slice(15)));}};
 const composition=await selectComposition({...opts,id:'VIDEO'});
 console.log(JSON.stringify({q,mode,width:composition.width,height:composition.height,fps:composition.fps,frames:composition.durationInFrames}));
 if(mode==='preview'){
  const frames=process.argv[4]?process.argv[4].split(',').map(Number):[0,3,25,45,...c.utterances.map(u=>u.from_frame+15),...c.subtitles.map(s=>Math.min(c.n-1,Math.ceil(s.start_s*30)+1))];
  for(const frame of [...new Set(frames)])await renderStill({...opts,composition,frame,output:path.join(p,`preview_${frame}.png`),imageFormat:'png'});
  const coverFrame=q==='q020'?45:q==='q022'?c.utterances.find(u=>u.mode==='kick').from_frame+2:0;
  await renderStill({...opts,composition,frame:coverFrame,output:path.join(p,'cover.jpg'),imageFormat:'jpeg',jpegQuality:95,inputProps:{c,cover:true,audit:false}});
  fs.writeFileSync(path.join(p,'subtitle_layout_observed.json'),JSON.stringify(audit,null,2));
 }else{
  await renderMedia({...opts,composition,outputLocation:path.join(p,mode==='animatic'?'animatic_muted.mp4':'video_muted.mp4'),scale:mode==='animatic'?1/3:1,codec:'h264',crf:mode==='animatic'?28:14,pixelFormat:'yuv420p',colorSpace:'bt709',muted:true,concurrency:3,onProgress:p=>{if(p.renderedFrames%150===0||p.progress===1)console.log(q,p.renderedFrames,p.progress)}});
 }
 console.log('DONE',q,mode);
})().catch(e=>{console.error(e);process.exit(1)});
