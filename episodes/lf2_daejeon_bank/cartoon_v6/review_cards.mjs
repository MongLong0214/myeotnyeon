import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const here=path.dirname(fileURLToPath(import.meta.url));
const require=createRequire(path.resolve(here,'../../../production/compositor/package.json'));
const {openBrowser,getCompositions,renderStill}=require('@remotion/renderer');
const serveUrl=path.join(here,'bundle');
const browser=await openBrowser('chrome',{browserExecutable:path.join(here,'chrome_offline.sh'),logLevel:'error'});
try{
 const [composition]=await getCompositions(serveUrl,{puppeteerInstance:browser,port:44951});
 for(const frame of [365,7300,7900]) await renderStill({serveUrl,port:44951,composition,puppeteerInstance:browser,frame,scale:.5,output:path.join(here,'qa',`portrait_check_${frame}.jpg`),imageFormat:'jpeg',jpegQuality:95,overwrite:true,logLevel:'error'});
}finally{await browser.close({silent:true})}
