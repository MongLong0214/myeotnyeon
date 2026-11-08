// Thin adapter around the existing v52 composition and offline Remotion renderer.
const fs=require('node:fs'),path=require('node:path');
const W=path.resolve(__dirname,'..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
req('./node_modules/@remotion/renderer/dist/assets/download-file.js').downloadFile=async({url,to,onProgress})=>{
 if(!url.startsWith('file://'))throw Error('Network asset blocked: '+url);
 const src=require('node:url').fileURLToPath(url),out=to(null,'audio/wav');
 fs.mkdirSync(path.dirname(out),{recursive:true});fs.copyFileSync(src,out);
 const sizeInBytes=fs.statSync(out).size;onProgress?.({downloaded:sizeInBytes,totalSize:sizeInBytes,percent:1});return {sizeInBytes,to:out};
};
const {bundle}=req('@remotion/bundler'),{selectComposition,renderStill,renderMedia}=req('@remotion/renderer');
(async()=>{
 const work=path.resolve(process.argv[2]),cfg=JSON.parse(fs.readFileSync(path.join(work,'recipe.json')));
 const serveUrl=await bundle({entryPoint:path.join(work,'entry.tsx'),outDir:path.join(work,'bundle'),publicDir:cfg.public,
 webpackOverride:c=>({...c,resolve:{...c.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})});
 const opts={serveUrl,browserExecutable:path.join(__dirname,'offline_chromium.sh'),inputProps:{},logLevel:'error',timeoutInMilliseconds:120000};
 const composition=await selectComposition({...opts,id:'VIDEO'});
 await renderStill({...opts,composition:await selectComposition({...opts,id:'COVER'}),frame:0,output:path.join(work,'cover.jpg'),imageFormat:'jpeg',jpegQuality:95});
 const enc={codec:'h264',crf:14,pixelFormat:'yuv420p',colorSpace:'bt709',muted:true,concurrency:3};
 await renderMedia({...opts,composition,...enc,outputLocation:path.join(work,'video_muted.mp4'),onProgress:p=>{if(p.renderedFrames%150===0||p.progress===1)console.log('render',p.renderedFrames)}});
 await renderMedia({...opts,composition:await selectComposition({...opts,id:'EMPTY'}),...enc,scale:.25,frameRange:[61,cfg.storyEnd-1],outputLocation:path.join(work,'empty.mp4')});
 await renderMedia({...opts,composition:await selectComposition({...opts,id:'AUDIT'}),...enc,scale:.25,concurrency:2,logLevel:'verbose',outputLocation:path.join(work,'audit.mp4'),onBrowserLog:l=>{if(/AUDIT|HOOKCHECK/.test(l.text||''))console.log(l.text)}});
 const rendered=JSON.parse(fs.readFileSync(path.join(work,'render.json')));
 fs.writeFileSync(path.join(work,'render_complete.json'),JSON.stringify({frames:composition.durationInFrames,number:rendered.ep.no,seed:cfg.seed,cover:rendered.ep.no,badge:rendered.ep.no,endCard:rendered.ep.no}));
})().catch(e=>{console.error(e);process.exitCode=1});
