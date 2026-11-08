const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../../..'),root=path.join(W,'production/compositor');const req=require('node:module').createRequire(root+'/package.json');req(root+'/src/v4/offline.cjs');
const {bundle}=req('@remotion/bundler'),{selectComposition,renderStill}=req('@remotion/renderer');
(async()=>{const serveUrl=await bundle({entryPoint:root+'/src/index.ts',outDir:__dirname+'/bundle_preview',publicDir:root+'/public'});
for(const q of process.argv.slice(2)){
 const doc=JSON.parse(fs.readFileSync(W+`/episodes/quiz/${q}/v5/render.json`));doc.audio=null;
 const opts={serveUrl,browserExecutable:root+'/src/v4spike/chromium.sh',inputProps:{hookStyle:'v51',doc},logLevel:'verbose',onBrowserLog:l=>{if(l.text?.includes('AUDIT')||l.text?.includes('HOOKCHECK'))console.log(l.text)}};
 // Metadata is loaded via v51 props, so use a supplied explicit composition for visual-only previews.
 const composition={id:'AUDIT-'+q.toUpperCase(),width:1080,height:1920,fps:30,durationInFrames:doc.durationInFrames,props:{...opts.inputProps,label:q},defaultProps:{},defaultCodec:null,defaultOutName:null,defaultVideoImageFormat:null,defaultPixelFormat:null,defaultProResProfile:null};
 for(const frame of [0,4,30,doc.durationInFrames-20]){const output=__dirname+`/preview_${q}/${frame}.png`;if(fs.existsSync(output))throw Error('exists '+output);await renderStill({...opts,composition,frame,output,imageFormat:'png'});}
}
})().catch(e=>{console.error(e);process.exitCode=1});
