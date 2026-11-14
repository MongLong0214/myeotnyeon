// usage: node render.cjs sheet <kind,...> | <id> stills <f1,f2,...> | <id> video | <id> cover
const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
const {bundle}=req('@remotion/bundler'),{selectComposition,renderStill,renderMedia}=req('@remotion/renderer');
(async()=>{
 const [q,mode,list]=process.argv.slice(2),SUF=process.env.SUF||'';
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'entry.tsx'),outDir:path.join(__dirname,'bundle'),publicDir:path.join(__dirname,'public'),webpackOverride:config=>({...config,cache:false,resolve:{...config.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})});
 const base={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),logLevel:'error'};
 if(q==='sheet'){const out=path.join(__dirname,'stills/model');fs.mkdirSync(out,{recursive:true});for(const kind of mode.split(',')){const o={...base,inputProps:{kind}};const comp=await selectComposition({...o,id:'SHEET'});await renderStill({...o,composition:comp,frame:Number(list||0),output:path.join(out,kind+'.png'),imageFormat:'png'});}console.log('SHEET',mode);return;}
 const p=path.join(W,'upload/pkg',q+'_B'),c=JSON.parse(fs.readFileSync(path.join(p,'case.json')));
 const opts={...base,inputProps:{c}};
 if(mode==='cover'){const o={...base,inputProps:{c,cover:true}};const comp=await selectComposition({...o,id:'COVER'});await renderStill({...o,composition:comp,frame:0,output:path.join(p,`cover${SUF}.jpg`),imageFormat:'jpeg',jpegQuality:93});console.log('COVER');return;}
 const composition=await selectComposition({...opts,id:'VIDEO'});
 if(mode==='stills'){const out=path.join(__dirname,'stills',q);fs.mkdirSync(out,{recursive:true});for(const frame of list.split(',').map(Number))await renderStill({...opts,composition,frame,output:path.join(out,`f${String(frame).padStart(4,'0')}.png`),imageFormat:'png'});console.log('STILLS',list);return;}
 await renderMedia({...opts,composition,outputLocation:path.join(p,`video_muted${SUF}.mp4`),codec:'h264',crf:16,pixelFormat:'yuv420p',colorSpace:'bt709',muted:true,concurrency:4,onProgress:x=>{if(x.renderedFrames%150===0||x.progress===1)console.log(q,x.renderedFrames);}});
 console.log('DONE',q,composition.durationInFrames);
})().catch(e=>{console.error(String(e).slice(0,2000));process.exit(1)});
