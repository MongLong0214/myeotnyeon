// usage: node render.cjs <qid> stills <f1,f2,...> | video | cover
const path=require('node:path'),fs=require('node:fs');
const W=path.resolve(__dirname,'../../../..'),root=path.join(W,'production/compositor');
const req=require('node:module').createRequire(path.join(root,'package.json'));
req('./src/v4/offline.cjs');
const {bundle}=req('@remotion/bundler'),{selectComposition,renderStill,renderMedia}=req('@remotion/renderer');
(async()=>{
 const [q,mode,list]=process.argv.slice(2),p=path.join(W,'upload/pkg',q+'_B'),c=JSON.parse(fs.readFileSync(path.join(p,'case.json')));
 // B3 prop cards must never render empty: fail the render before it starts
 const empty=[];for(const u of c.utterances||[])for(const sh of u.shots||[]){
  if(sh.s==='calendar'&&!String(sh.year||'').trim())empty.push(u.id+':calendar.year');
  if(['paper','stamp','bubble'].includes(sh.s)&&!(sh.lines||[]).some(l=>String(l).trim()))empty.push(u.id+':'+sh.s+'.lines');
  if(sh.s==='stamp'&&!String(sh.stamp||'').trim())empty.push(u.id+':stamp.stamp');
  if(sh.s==='tally'&&(!String(sh.label||'').trim()||!((sh.n??5)>=1)))empty.push(u.id+':tally.label/n');
  if(sh.s==='phone'&&!(sh.msgs||[]).some(l=>String(l).trim()))empty.push(u.id+':phone.msgs');}
 if(empty.length){console.error('EMPTY CARD TEXT',empty.join(' '));process.exit(2);}
 // Grave cases must never carry the subscribe gag / anger mark: if the narration names a death, a family victim,
 // abuse, a child, a disabled person or an animal victim, the spec must say grave:true or the render fails (fail-closed).
 const gravePat=/숨지|숨진|사망|살해|살인|죽게|죽였|어머니|(?<!할)아버지|모친|부친|존속|노모|아동|아이를|장애|학대|고양이|강아지|반려/;
 const graveHit=(c.utterances||[]).map(u=>(u.tts||'')+' '+(u.shown||'')).join(' ').match(gravePat);
 if(graveHit&&!c.grave){console.error('GRAVE CASE WITHOUT grave:true (subscribe gag would render) — matched "'+graveHit[0]+'"');process.exit(5);}
 // en/ja: card text must fit its card (same width estimate as i18n.ts em(): CJK 1em, Latin caps/digits .66, other .54)
 if(c.locale&&c.locale!=='ko'){const em=t=>[...String(t)].reduce((a,ch)=>a+(/[　-鿿＀-￯]/.test(ch)?1:c.locale==='en'?(/[A-Z0-9$]/.test(ch)?.66:.54):.56),0),over=[];
  for(const u of c.utterances||[])for(const sh of u.shots||[]){const L=(sh.lines||[]).map(String);
   if(sh.s==='paper')L.forEach(l=>{if(em(l)*(sh.size??90)>640)over.push(`${u.id}:paper "${l}"`);});
   if(sh.s==='stamp')L.forEach(l=>{if(em(l)*(sh.size??90)>660)over.push(`${u.id}:stamp "${l}"`);});
   if(sh.s==='bubble')L.forEach((l,k)=>{if(em(l)*(k?90:(sh.size??130))>780)over.push(`${u.id}:bubble "${l}"`);});
   if(sh.s==='tally'&&em(sh.label)*84>800)over.push(`${u.id}:tally "${sh.label}"`);}
  if(over.length){console.error('CARD TEXT OVERFLOW',over.join(' '));process.exit(4);}}
 // Subtitle must not sit over a face: a react close-up (s 2.45) with y above 2100 drops the chin into the subtitle band
 // (measured q046 L12: y 2090 chin clear of the subtitle, y 2160/2300 chin under it). Only lines that show subtitles count.
 const faceSub=[];for(const u of c.utterances||[])if((u.chunks||[]).length)for(const sh of u.shots||[])if(sh.s==='react'&&(sh.y??1960)>2100)faceSub.push(u.id+':react.y='+sh.y);
 if(faceSub.length){console.error('SUBTITLE OVER FACE (react y > 2100 on a subtitled line)',faceSub.join(' '));process.exit(4);}
 // a line that names its actor ("actor": look id) may only show that character in react/cell shots,
 // unless the shot is marked "other":true (e.g. a victim's reaction on a line that names the victim)
 const wrong=[];for(const u of c.utterances||[])if(u.actor)for(const sh of u.shots||[])
  if(['react','cell'].includes(sh.s)&&sh.look&&sh.look!==u.actor&&!sh.other)wrong.push(`${u.id}:${sh.s}=${sh.look}≠${u.actor}`);
 if(c.b3&&(c.utterances||[]).some(u=>(u.shots||[]).some(sh=>['react','cell'].includes(sh.s))&&!u.actor&&!['opinion','choices','options','answer'].includes(u.mode)))
  wrong.push('lines with react/cell shots must declare "actor": '+c.utterances.filter(u=>(u.shots||[]).some(sh=>['react','cell'].includes(sh.s))&&!u.actor&&!['opinion','choices','options','answer'].includes(u.mode)).map(u=>u.id).join(','));
 if(wrong.length){console.error('ACTOR MISMATCH',wrong.join(' '));process.exit(3);}
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'entry.tsx'),outDir:path.join(__dirname,process.env.B3_BUNDLE||'bundle'),publicDir:path.join(__dirname,'public'),webpackOverride:config=>({...config,cache:false,resolve:{...config.resolve,modules:[path.join(root,'node_modules'),'node_modules']}})});
 const opts={serveUrl,browserExecutable:path.join(root,'src/v4spike/chromium.sh'),inputProps:{c},logLevel:'error'};
 if(mode==='cover'){const comp=await selectComposition({...opts,id:'COVER',inputProps:{c,cover:true}});await renderStill({...opts,inputProps:{c,cover:true},composition:comp,frame:0,output:path.join(p,'cover.jpg'),imageFormat:'jpeg',jpegQuality:93});console.log('COVER');return;}
 const seek=req('./node_modules/@remotion/renderer/dist/seek-to-frame.js'),orig=seek.seekToFrame,hands={},actors={},headsF={};
 seek.seekToFrame=async o=>{await orig(o);if(o.composition!=='VIDEO')return;const r=await o.page.evaluate(()=>{const c=document.querySelector('[data-owner-canvas]').getBoundingClientRect();
  // actor boxes (every ArticulatedGuy <svg aria-label>, shadows excluded): union of visible painted shapes, canvas px [x0,y0,x1,y1]
  const act=Array.from(document.querySelectorAll('svg[aria-label]')).filter(s=>s.getAttribute('aria-label')!=='그림자').map(s=>{let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(const ch of s.querySelectorAll('path,circle,ellipse,rect,polygon')){if(ch.closest('defs,clipPath,mask,filter,title,[clip-path],[mask]'))continue;const st=getComputedStyle(ch);if(st.display==='none'||st.visibility==='hidden'||+st.opacity===0||(st.fill==='none'&&st.stroke==='none'))continue;const b=ch.getBoundingClientRect();if(b.width<1||b.height<1)continue;x0=Math.min(x0,b.left);y0=Math.min(y0,b.top);x1=Math.max(x1,b.right);y1=Math.max(y1,b.bottom);}return [x0-c.x,y0-c.y,x1-c.x,y1-c.y].map(Math.round);}).filter(b=>b[2]>b[0]&&b[3]>b[1]&&b[0]<1080&&b[1]<1920&&b[2]>0&&b[3]>0);
  // head boxes ([data-head] group of every non-shadow ArticulatedGuy): union of visible painted shapes, canvas px [x0,y0,x1,y1]
  const box=(g)=>{let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;for(const ch of g.querySelectorAll('path,circle,ellipse,rect,polygon')){if(ch.closest('defs,clipPath,mask,filter,title,[clip-path],[mask]'))continue;const st=getComputedStyle(ch);if(st.display==='none'||st.visibility==='hidden'||+st.opacity===0||(st.fill==='none'&&st.stroke==='none'))continue;const b=ch.getBoundingClientRect();if(b.width<1||b.height<1)continue;x0=Math.min(x0,b.left);y0=Math.min(y0,b.top);x1=Math.max(x1,b.right);y1=Math.max(y1,b.bottom);}return [x0-c.x,y0-c.y,x1-c.x,y1-c.y].map(Math.round);};
  const heads=Array.from(document.querySelectorAll('svg[aria-label] [data-head]')).filter(g=>g.closest('svg[aria-label]').getAttribute('aria-label')!=='그림자').map(box).filter(b=>b[2]>b[0]&&b[3]>b[1]&&b[0]<1080&&b[1]<1920&&b[2]>0&&b[3]>0);
  return {hd:heads,h:Array.from(document.querySelectorAll('[data-hand]')).map(el=>{const b=el.getBoundingClientRect();return [Math.round(b.x-c.x),Math.round(b.y-c.y),Math.round(b.width),Math.round(b.height),el.getAttribute('data-hand')];}).filter(h=>h[2]>2&&h[3]>2&&h[0]<1080&&h[1]<1920&&h[0]+h[2]>0&&h[1]+h[3]>0),a:act};});
  hands[o.frame]=r.h;actors[o.frame]=r.a;headsF[o.frame]=r.hd;};
 const composition=await selectComposition({...opts,id:'VIDEO'});
 if(mode==='stills'){const out=path.join(__dirname,'stills',q);fs.mkdirSync(out,{recursive:true});for(const frame of list.split(',').map(Number))await renderStill({...opts,composition,frame,output:path.join(out,`f${String(frame).padStart(4,'0')}.png`),imageFormat:'png'});fs.writeFileSync(path.join(out,'boxes.json'),JSON.stringify({actors,heads:headsF}));console.log('STILLS',list);return;}
 await renderMedia({...opts,composition,outputLocation:path.join(p,'video_muted.mp4'),codec:'h264',crf:16,pixelFormat:'yuv420p',colorSpace:'bt709',muted:true,concurrency:4,onProgress:x=>{if(x.renderedFrames%150===0||x.progress===1)console.log(q,x.renderedFrames);}});
 fs.writeFileSync(path.join(p,'hand_boxes.json'),JSON.stringify(hands));fs.writeFileSync(path.join(p,'actor_boxes.json'),JSON.stringify(actors));fs.writeFileSync(path.join(p,'head_boxes.json'),JSON.stringify(headsF));
 console.log('DONE',q,composition.durationInFrames);
})().catch(e=>{console.error(e);process.exit(1)});
