// Library check: every stage, frames 10 and 40 of the open line, head boxes vs a typical one-line subtitle box
// (x 170-910, y 1209-1325); prints stages where a head is >12% covered. Run after any stage TSX change:
//   (cd episodes/quiz/batch_1107/b_format && B3_BUNDLE=bundle_audit node render.cjs <any built id> stills 0 && node ../../../../factory/shorts/stage_audit.cjs bundle_audit)
// Needs upload/pkg/zzq044_B/case.json as the base case.
const path=require('node:path'),fs=require('node:fs');
const D='/Users/isaac/projects/verdict-kr/work/episodes/quiz/batch_1107/b_format',W=path.resolve(D,'../../../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));req('./src/v4/offline.cjs');
const {selectComposition,renderStill}=req('@remotion/renderer');
const lib=JSON.parse(fs.readFileSync(path.join(W,'factory/shorts/library.json')));
(async()=>{const base=JSON.parse(fs.readFileSync(path.join(W,'upload/pkg/zzq044_B/case.json')));
const seek=req('./node_modules/@remotion/renderer/dist/seek-to-frame.js'),orig=seek.seekToFrame;let out=null;
seek.seekToFrame=async o=>{await orig(o);out=await o.page.evaluate(()=>{const c=document.querySelector('[data-owner-canvas]').getBoundingClientRect();
 const box=(g)=>{let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(const ch of g.querySelectorAll('path,circle,ellipse,rect,polygon')){if(ch.closest('defs,clipPath,mask,filter,title,[clip-path],[mask]'))continue;const st=getComputedStyle(ch);if(st.display==='none'||+st.opacity===0||(st.fill==='none'&&st.stroke==='none'))continue;const b=ch.getBoundingClientRect();if(b.width<1||b.height<1)continue;x0=Math.min(x0,b.left);y0=Math.min(y0,b.top);x1=Math.max(x1,b.right);y1=Math.max(y1,b.bottom);}return [x0-c.x,y0-c.y,x1-c.x,y1-c.y].map(Math.round);};
 return Array.from(document.querySelectorAll('svg[aria-label] [data-head]')).filter(g=>g.closest('svg[aria-label]').getAttribute('aria-label')!=='그림자').map(box).filter(b=>b[2]>b[0]&&b[3]>0&&b[1]<1920);});};
const opts={serveUrl:path.join(D,process.argv[2]||'bundle_zzja001'),browserExecutable:path.join(root,'src/v4spike/chromium.sh'),logLevel:'error'};
const res={};
for(const st of Object.keys(lib.stages)){const c=JSON.parse(JSON.stringify(base));c.stage=st;c.kind=st;c.utterances[0].shots=[{s:st}];c.utterances[0].mode=st;
 const o={...opts,inputProps:{c}};const comp=await selectComposition({...o,id:'VIDEO'});
 for(const f of [10,40]){await renderStill({...o,composition:comp,frame:f,output:require('node:path').join(require('node:os').tmpdir(),'aud_'+st+'_'+f+'.png')});
  const bad=out.map(b=>{const ix=Math.max(0,Math.min(b[2],910)-Math.max(b[0],170)),iy=Math.max(0,Math.min(b[3],1325)-Math.max(b[1],1209));return [b,Math.round(ix*iy/((b[2]-b[0])*(b[3]-b[1]))*100)/100];}).filter(x=>x[1]>0.12);
  res[st]=(res[st]||[]).concat(bad.length?[[f,bad]]:[]);}
 console.log(st,JSON.stringify(res[st]));}
})().catch(e=>{console.error(e);process.exit(1)});
