// node look/cpuprof.cjs <qid> <from> <to> <comp> <off,...>  -> renders range; run under /usr/bin/time
const path=require('node:path'),fs=require('node:fs');
const B=path.resolve(__dirname,'..'),W=path.resolve(B,'../../../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));req('./src/v4/offline.cjs');
const {bundle}=req('@remotion/bundler'),{selectComposition,renderMedia}=req('@remotion/renderer');
(async()=>{const [q,from,to,id,off]=process.argv.slice(2),c=JSON.parse(fs.readFileSync(path.join(W,'upload/pkg',q+'_B','case.json')));
 const outDir=path.join(__dirname,'_bundle_cpu'+process.pid);
 const serveUrl=fs.existsSync(path.join(__dirname,'_bundle_cpu'))?path.join(__dirname,'_bundle_cpu'):await bundle({entryPoint:path.join(__dirname,'entry.tsx'),outDir:path.join(__dirname,'_bundle_cpu'),publicDir:path.join(B,'public'),webpackOverride:config=>({...config,cache:false,resolve:{...config.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})});
 const opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),inputProps:{c,lookOff:(off||'').split(',').filter(Boolean)},logLevel:'error',chromiumOptions:process.env.GL?{gl:process.env.GL}:{}};
 const comp=await selectComposition({...opts,id});const t=Date.now();
 await renderMedia({...opts,composition:comp,frameRange:[+from,+to],outputLocation:'/tmp/cpuprof.mp4',codec:'h264',muted:true,concurrency:4});
 console.log('WALL',((Date.now()-t)/(to-from+1)).toFixed(0));
})().catch(e=>{console.error(e);process.exit(1)});
