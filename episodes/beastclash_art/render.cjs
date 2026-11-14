// usage: node render.cjs  -> out/v_test.mp4, out/v_f*.png, out/v_parts_*.png
const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
const {bundle}=req('@remotion/bundler'),{selectComposition,renderStill,renderMedia}=req('@remotion/renderer');
(async()=>{
 const out=path.join(__dirname,'out');fs.mkdirSync(out,{recursive:true});
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'src/entry.tsx'),outDir:path.join(__dirname,'bundle'),webpackOverride:c=>({...c,cache:false,resolve:{...c.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})});
 const base={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),logLevel:'error'};
 for(const kind of ['polar','walrus']){const o={...base,inputProps:{kind}};const c=await selectComposition({...o,id:'PARTS'});await renderStill({...o,composition:c,frame:0,output:path.join(out,`v_parts_${kind}.png`)});}
 const o={...base,inputProps:{}},c=await selectComposition({...o,id:'TEST'});
 for(const f of (process.env.FRAMES||'0,24,62,69').split(',').map(Number))await renderStill({...o,composition:c,frame:f,output:path.join(out,`v_f${String(f).padStart(2,'0')}.png`)});
 if(!process.env.NOVIDEO)await renderMedia({...o,composition:c,outputLocation:path.join(out,'v_test.mp4'),codec:'h264',crf:18,pixelFormat:'yuv420p',muted:true});
 console.log('DONE');
})().catch(e=>{console.error(String(e).slice(0,2000));process.exit(1)});
