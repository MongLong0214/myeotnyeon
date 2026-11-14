import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {assert,validateEpisode,atomicWrite,checkPNG,rejectLinks} from '../src/core.mjs';
import {server,openBrowser,lockOutput} from './runtime.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),out=path.join(root,'out');
const episode=process.argv[2]||'episodes/one_step_behind/episode.json';
assert(episode.startsWith('episodes/')&&!episode.includes('..'),'Invalid episode path');
const e=JSON.parse(fs.readFileSync(path.join(root,episode))),timeline=validateEpisode(e);
assert(fs.existsSync(path.join(root,'vendor/todai/src/anime.js')),'Run npm run setup first.');
rejectLinks(out);fs.mkdirSync(out,{recursive:true});const release=lockOutput(out,`${e.id}/boards/.lock`),http=await server(root);let browser;
const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
try{
 browser=await openBrowser();let html=`<!doctype html><meta charset="utf-8"><title>${escape(e.title)} — boards</title><style>body{font:16px system-ui;background:#f4f1ed;color:#222;margin:30px}section{display:flex;gap:10px;margin-bottom:28px}img{width:180px}h2{margin-top:36px}p{max-width:900px}</style><h1>${escape(e.title)}</h1><p>STORYBOARDS FROM ACTUAL SCENE KEY POSES. Not a final animation. Review framing, actions and story order; motion and sound require the rendered sequence.</p>`;
 for(const s of timeline.shots){const page=await browser.newPage({viewport:{width:270,height:480}});
  try{const q=new URLSearchParams({episode,shot:s.id,width:'270',height:'480',capture:'1'});await page.goto(http.url+'/web/index.html?'+q);await page.evaluate(()=>window.ready);
   const info=await page.evaluate(()=>window.factoryInfo);assert(!/(swiftshader|llvmpipe|software)/i.test(info.gpu),'Software renderer; use an explicitly configured diagnostic environment, not a silent fallback.');
   html+=`<h2>${escape(s.id)} · ${s.startFrame/e.fps}s–${s.endFrame/e.fps}s</h2><p>${escape(s.intent)}</p><section>`;
   for(const f of [0,Math.floor(s.frames/2),s.frames-1]){const url=await page.evaluate(f=>window.renderFrame(f),f),data=Buffer.from(url.split(',')[1],'base64');checkPNG(data,270,480);const n=`${s.id}_${f}.png`;atomicWrite(out,`${e.id}/boards/${n}`,data);html+=`<figure><img src="${n}"><figcaption>frame ${f}</figcaption></figure>`;}
   html+='</section>';
  }finally{await page.close();}
 }
 atomicWrite(out,`${e.id}/boards/index.html`,html);console.log(`out/${e.id}/boards/index.html`);
}finally{await browser?.close();await http.close();release();}
