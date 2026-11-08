require('./offline.cjs');
const path=require('node:path');
const {selectComposition,renderStill}=require('@remotion/renderer');
(async()=>{
 const root=path.resolve(__dirname,'../..'),out=path.resolve(root,'../../episodes/v4/n18/out');const serveUrl=path.join(root,'build'),browserExecutable=path.join(root,'src/v4spike/chromium.sh');
 const composition=await selectComposition({serveUrl,id:'V4N18-FULL',browserExecutable,inputProps:{audio:false}});
 for(const frame of [230,1500,4150,6120,9460,10500,11400]){await renderStill({composition,serveUrl,browserExecutable,inputProps:{audio:false},frame,output:path.join(out,`preview-${frame}.png`)});console.log(frame)}
})().catch(e=>{console.error(e);process.exitCode=1});
