import React, {useLayoutEffect, useRef} from '../../../../production/compositor/node_modules/react';
import {Composition, registerRoot, useCurrentFrame, delayRender, continueRender, staticFile} from '../../../../production/compositor/node_modules/remotion';
import {Quiz, QuizDoc} from '../../../../production/compositor/src/Quiz';
const Strict: React.FC<{doc: QuizDoc | null}> = ({doc}) => {
 const frame=useCurrentFrame(),root=useRef<HTMLDivElement>(null);
 useLayoutEffect(()=>{
  const h=delayRender(`strict fonts/frame ${frame}`);
  document.fonts.ready.then(()=>{
   const el=root.current;if(!el||!doc){continueRender(h);return;}
   const rr=el.getBoundingClientRect(),k=rr.width/1080,boxes:{text:string,x0:number,y0:number,x1:number,y1:number}[]=[],bad:string[]=[];
   const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
   for(let n=walker.nextNode();n;n=walker.nextNode()){
    const text=(n.textContent??'').trim();if(!text)continue;
    let visible=true;
    for(let p=n.parentElement;p&&p!==el;p=p.parentElement){const c=getComputedStyle(p);if(c.display==='none'||c.visibility==='hidden'||Number(c.opacity)<.05)visible=false;}
    if(!visible)continue;
    const range=document.createRange();range.selectNodeContents(n);
    for(const r of Array.from(range.getClientRects())){
     if(r.width<1||r.height<1)continue;
     const b={text,x0:(r.left-rr.left)/k,y0:(r.top-rr.top)/k,x1:(r.right-rr.left)/k,y1:(r.bottom-rr.top)/k};boxes.push(b);
     if(b.x0<109||b.x1>971||b.y0<189||b.y1>1541||(b.x1>881&&b.y1>901))bad.push('zone:'+text);
     for(let p=n.parentElement;p&&p!==el;p=p.parentElement){const c=getComputedStyle(p),pr=p.getBoundingClientRect();if(['hidden','clip','scroll','auto'].includes(c.overflowX)&&(r.left<pr.left-1||r.right>pr.right+1))bad.push('clip-x:'+text);if(['hidden','clip','scroll','auto'].includes(c.overflowY)&&(r.top<pr.top-1||r.bottom>pr.bottom+1))bad.push('clip-y:'+text);}
    }
   }
   const overlaps:string[]=[];
   for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){const a=boxes[i],b=boxes[j];if(Math.min(a.x1,b.x1)-Math.max(a.x0,b.x0)>2&&Math.min(a.y1,b.y1)-Math.max(a.y0,b.y0)>2)overlaps.push(a.text+' / '+b.text);}
   const expected=doc.subtitles.find(s=>frame>=s.from_&&frame<s.to),caption=el.querySelector('[data-type2-caption]');
   const sync=(caption?.textContent??'')===(expected?.text??'')&&(caption?Number(caption.getAttribute('data-type2-caption'))===expected?.from_:!expected);
   const report=delayRender('TYPE2CHECK '+JSON.stringify({frame,bad,overlaps,sync,caption:caption?.textContent??'',texts:boxes.map(b=>b.text)})+' END');continueRender(report);continueRender(h);
  });
 },[frame,doc]);
 return <div ref={root} style={{position:'relative',width:1080,height:1920}}>{doc&&<Quiz doc={doc} quizStyle="premium" typeStyle="type2"/>}</div>;
};
registerRoot(()=> <Composition id="STRICT-Q006" component={Strict} width={1080} height={1920} fps={30} durationInFrames={998} defaultProps={{doc:null}} calculateMetadata={async()=>({props:{doc:await(await fetch(staticFile('q006/render.json'))).json()}})}/>);
