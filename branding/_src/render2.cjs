// usage: node render2.cjs assets|compare [A,B,C] -> ../cheolkeong_v2/{A,B,C}/... and compare.png
const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
const {bundle}=req('@remotion/bundler'),{selectComposition,renderStill}=req('@remotion/renderer');
(async()=>{const [mode,list]=process.argv.slice(2),ds=(list||'A,B,C').split(','),out=path.join(__dirname,'_bundle2'),base=path.join(W,'branding/cheolkeong_v2');
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'entry2.tsx'),outDir:out,publicDir:path.join(__dirname,'public'),webpackOverride:c=>({...c,cache:false,resolve:{...c.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})});
 const opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),logLevel:'error'};
 const go=async(id,o)=>{const composition=await selectComposition({...opts,id});await renderStill({...opts,composition,frame:0,output:o,imageFormat:'png'});console.log(o);};
 try{if(mode==='compare')await go('compare',path.join(base,'compare.png'));
  else for(const d of ds){const dir=path.join(base,d);fs.mkdirSync(dir,{recursive:true});
   for(const [id,n] of [['pfp','profile_800'],['wm','watermark_150'],['banner','banner_2560x1440']]){const o=path.join(dir,n+'.png');await go(`${id}-${d}`,o);
    if(id!=='wm')fs.copyFileSync(o,path.join(__dirname,'public/assets',`v2_${d}_${id}.png`));}}}
 finally{fs.rmSync(out,{recursive:true,force:true});}})().catch(e=>{console.error(e);process.exit(1)});
