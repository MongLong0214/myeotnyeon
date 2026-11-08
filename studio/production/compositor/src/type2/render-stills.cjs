// Explicitly render stills only. This entrypoint never calls renderMedia.
require('../v4/offline.cjs');
const path=require('node:path'),fs=require('node:fs');
const {bundle}=require('@remotion/bundler');
const {selectComposition,renderStill}=require('@remotion/renderer');
(async()=>{
 const root=path.resolve(__dirname,'../..'),out=path.resolve(root,'../../research/format_v4/type_v2/stills');
 fs.mkdirSync(out,{recursive:true});
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'index.ts'),outDir:'/private/tmp/mnn-type2-review',publicDir:path.join(root,'public')});
 const browserExecutable=path.join(root,'src/v4spike/chromium.sh');
 const shots=[['N18','chapter'],['N18','scene'],['N18','dossier'],['N18','measurement'],['N18','verdict'],['Q006','header'],['Q006','choices'],['Q006','reason'],['Q006','verdict']];
 const records=[];
 for(const [episode,kind] of shots){
  const id=`TYPE2-${episode}-${kind}`,composition=await selectComposition({serveUrl,id,browserExecutable});
  const output=path.join(out,`${episode.toLowerCase()}_${kind}.png`);
  await renderStill({composition,serveUrl,browserExecutable,frame:90,output,imageFormat:'png'});
  records.push({id,frame:90,width:composition.width,height:composition.height,file:path.basename(output)});console.log('STILL',id);
 }
 fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(records,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
