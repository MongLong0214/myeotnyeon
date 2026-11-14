// usage: node render.cjs assets|boards [ch,...]   -> ../<handle>/{profile_800,banner_2560x1440,watermark_150,preview_board}.png
const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
const {bundle}=req('@remotion/bundler'),{selectComposition,renderStill}=req('@remotion/renderer');
const H={gts:'guessthesentence',nnd:'nannenderu',bcl:'beastclashtoon',chk:'cheolkeong'};
(async()=>{
 const [mode,list]=process.argv.slice(2),chs=(list||'gts,nnd,bcl').split(','),out=path.join(__dirname,'_bundle');
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'entry.tsx'),outDir:out,publicDir:path.join(__dirname,'public'),webpackOverride:c=>({...c,cache:false,resolve:{...c.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})});
 const opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),logLevel:'error'};
 try{for(const ch of chs){const dir=path.join(W,'branding',H[ch]);fs.mkdirSync(dir,{recursive:true});
  const jobs=mode==='boards'?[['board','preview_board']]:[['pfp','profile_800'],['wm','watermark_150'],['banner','banner_2560x1440']];
  for(const [id,name] of jobs){const composition=await selectComposition({...opts,id:`${id}-${ch}`});const o=path.join(dir,name+'.png');
   await renderStill({...opts,composition,frame:0,output:o,imageFormat:'png'});
   if(mode!=='boards')fs.copyFileSync(o,path.join(__dirname,'public/assets',`${ch}_${id}.png`));console.log(o,fs.statSync(o).size);}}
 }finally{fs.rmSync(out,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exit(1)});
