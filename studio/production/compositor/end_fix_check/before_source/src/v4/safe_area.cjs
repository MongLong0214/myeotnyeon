require('./offline.cjs');
const path=require('node:path'),fs=require('node:fs');
const root=path.resolve(__dirname,'../..'),out=path.resolve(root,'../../episodes/v4/n18/out');
const dist=path.join(root,'node_modules/@remotion/renderer/dist');
const take=require(path.join(dist,'take-frame.js')),original=take.takeFrame;
const {seekToFrame}=require(path.join(dist,'seek-to-frame.js'));
const film=require('./n18-film.json');const measured=[];
const frames=[...new Set([...film.shots.map(s=>s.from+Math.floor(s.dur/2)),...film.subtitles.map(s=>s.from_+2)])].sort((a,b)=>a-b);
take.takeFrame=async options=>{
 const page=options.freePage;
 for(const frame of frames){
  await seekToFrame({frame,page,composition:'V4N18-FULL',timeoutInMilliseconds:30000,indent:false,logLevel:'error',attempt:0});
  const r=await page.evaluate(()=>[...document.querySelectorAll('[data-safe]')].filter(e=>e.textContent.trim()).map(e=>{const range=document.createRange();range.selectNodeContents(e);const r=range.getBoundingClientRect();return{text:e.textContent,x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height}}));
  measured.push({frame,text:r});
 }
 const violations=measured.flatMap(x=>x.text.filter(t=>t.x<96-.1||t.right>1824+.1||t.y<54-.1||t.bottom>993.6+.1).map(t=>({frame:x.frame,...t})));
 fs.writeFileSync(path.join(out,'safe_area.json'),JSON.stringify({method:'Chromium DOM Range glyph bounds after fonts/renderReady; all shot midpoints and subtitle starts',sampled_frames:frames.length,safe_rect:{left:96,right:1824,top:54,bottom:993.6},violations,passed:!violations.length,measurements:measured},null,1));
 return original(options);
};
const {selectComposition,renderStill}=require('@remotion/renderer');
(async()=>{
 const serveUrl='/private/tmp/n18-stage2/corrected',browserExecutable=path.join(root,'src/v4spike/chromium.sh'),inputProps={audio:false};
 const composition=await selectComposition({serveUrl,id:'V4N18-FULL',browserExecutable,inputProps});
 await renderStill({composition,serveUrl,browserExecutable,inputProps,frame:90,output:path.join(out,'safe-area-last.png')});console.log('SAFE COMPLETE');
})().catch(e=>{console.error(e);process.exitCode=1});
