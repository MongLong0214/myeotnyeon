const path=require('node:path'),fs=require('node:fs');
const W='/Users/isaac/projects/verdict-kr/work',root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
const {bundle}=req('@remotion/bundler'),{selectComposition,renderStill,renderMedia}=req('@remotion/renderer');
(async()=>{
 const mode=process.argv[2]||'preview',out=path.resolve(__dirname,'../render');fs.mkdirSync(out,{recursive:true});
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'entry.tsx'),outDir:path.join(out,'bundle'),publicDir:path.join(__dirname,'public'),webpackOverride:c=>({...c,cache:false,resolve:{...c.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})});
 const audit=[];
 const opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),inputProps:{audit:mode==='preview'},logLevel:'error',onBrowserLog:l=>{const marker='CAPTION_LAYOUT ';if(l.text?.startsWith(marker))audit.push(JSON.parse(l.text.slice(marker.length)));}};
 const composition=await selectComposition({...opts,id:'VIDEO'});
 console.log(JSON.stringify({mode,output:path.join(out,'video_muted.mp4'),codec:'h264',width:composition.width,height:composition.height,fps:composition.fps,duration:composition.durationInFrames}));
 if(mode==='preview'){
  const frames=process.argv[3]?process.argv[3].split(',').map(Number):[0,40,61,73,143,193,210,260,300,329,350,375,401,420,450,490,535,565,600,630,663,668,669,673,685,710,740,754,755,780,799];
  for(const frame of frames){await renderStill({...opts,composition,frame,output:path.join(out,`f${frame}.png`),imageFormat:'png'});console.log('STILL',frame);}
  fs.writeFileSync(path.join(out,'subtitle_layout_observed.json'),JSON.stringify(audit,null,2));
 } else if(mode==='render'||mode==='animatic'){
  await renderMedia({...opts,composition,outputLocation:path.join(out,mode==='animatic'?'animatic_muted.mp4':'video_muted.mp4'),scale:mode==='animatic'?.5:1,codec:'h264',crf:mode==='animatic'?25:14,pixelFormat:'yuv420p',colorSpace:'bt709',muted:true,concurrency:3,onProgress:p=>{if(p.renderedFrames%100===0||p.progress===1)console.log(JSON.stringify({rendered:p.renderedFrames,progress:p.progress}))}});
 } else throw new Error('Use preview or render');
})().catch(e=>{console.error(e);process.exitCode=1});
