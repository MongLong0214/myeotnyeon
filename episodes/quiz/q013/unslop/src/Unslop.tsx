import React,{useLayoutEffect,useRef} from 'react';
import {AbsoluteFill,Img,Sequence,continueRender,delayRender,interpolate,spring,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import {Reenactment} from './FightScene';
import {CustodyScene,ProbationScene,CourtComedy,Sentencing} from './ComedyLogic';
import data from './render.json';
import type {Caption} from '@remotion/captions';
import captionData from './captions.json';
const captions:Caption[]=captionData;

// Only the presentation changes. Authored subtitle text, ranges, cue-local clocks,
// contact animation, judge motion and verdict prop anchors stay in the copied source.
const handle=typeof document==='undefined'?null:delayRender('local Korean fonts');
if(handle!==null)Promise.all([
 ['Do Hyeon','DoHyeon-Regular.ttf','400'],['Quiet Sans','Pretendard-Bold.woff2','700']
].map(async([family,file,weight])=>{const face=await new FontFace(family,`url(${staticFile('fonts/'+file)})`,{weight}).load();document.fonts.add(face);})).then(()=>continueRender(handle));
const ink='#171512';
const lettering:React.CSSProperties={fontFamily:'Do Hyeon',fontWeight:800,color:'#fff',WebkitTextStroke:`8px ${ink}`,paintOrder:'stroke fill',lineHeight:1.18,letterSpacing:'-.015em',wordBreak:'keep-all'};
const subtitleBox:React.CSSProperties={...lettering,position:'absolute',left:90,top:1192,width:900,height:150,display:'flex',alignItems:'center',justifyContent:'center',textAlign:'center',fontSize:72,fontWeight:800,lineHeight:1.04,WebkitTextStroke:'10px #000',textShadow:'0 3px 4px rgba(0,0,0,.65)',whiteSpace:'pre'};
const Narration:React.FC<{text:string;from:number;to:number;audit?:boolean;emphasis?:string}>=({text,from,to,audit=false,emphasis})=>{
 const f=useCurrentFrame(),{width,height}=useVideoConfig(),ref=useRef<HTMLDivElement>(null),lines=text.split('\n');
 useLayoutEffect(()=>{
  if(!audit||!ref.current)return;
  const el=ref.current,cs=getComputedStyle(el),b=el.getBoundingClientRect(),canvas=el.closest('[data-owner-canvas]')!.getBoundingClientRect();
  const renderedLines=Array.from(el.querySelectorAll('[data-caption-line]')).map(line=>{const range=document.createRange();range.selectNodeContents(line);const r=range.getBoundingClientRect();return {text:line.textContent,characters:Array.from(line.textContent??'').length,centerX:r.x+r.width/2-canvas.x,top:r.top-canvas.y,bottom:r.bottom-canvas.y,width:r.width};});
  console.log('CAPTION_LAYOUT '+JSON.stringify({frame:f,from,to,canvas:{width,height},box:{x:b.x-canvas.x,y:b.y-canvas.y,width:b.width,height:b.height,centerX:b.x+b.width/2-canvas.x,bottom:b.bottom-canvas.y},fontFamily:cs.fontFamily,fontSize:cs.fontSize,fontWeight:cs.fontWeight,outline:cs.webkitTextStrokeWidth,outlineColor:cs.webkitTextStrokeColor,shadow:cs.textShadow,textAlign:cs.textAlign,lines:renderedLines}));
 },[audit,f,from,to,text,width,height]);
 return <div ref={ref} data-narration data-caption-from={from} data-caption-to={to} style={subtitleBox}><div style={{width:'100%'}}>{lines.map((line,i)=>{
  const at=emphasis?line.indexOf(emphasis):-1;
  return <div data-caption-line key={i}>{at<0?line:<>{line.slice(0,at)}<span style={{color:'#FFD400'}}>{emphasis}</span>{line.slice(at+emphasis!.length)}</>}</div>;
 })}</div></div>;
};
const clamp={extrapolateLeft:'clamp' as const,extrapolateRight:'clamp' as const};
export const Hero:React.FC<{end?:boolean}>=({end=false})=>{
 const frame=useCurrentFrame(),f=end?frame-755:frame;
 // Same hero and original camera clock, without headline strips or CTA card.
 const zoom=interpolate(f,[0,end?44:60],[end?1.04:1,end?1.10:1.12],clamp);
 const pulse=.5+.5*Math.sin(f*.31+13);
 return <AbsoluteFill style={{overflow:'hidden'}}>
  <Img src={staticFile('hook_v51/q013_clouds.png')} style={{width:1080,height:1920,objectFit:'cover',transform:`scale(${zoom})`,transformOrigin:'50% 68%',filter:`brightness(${.99+pulse*.045})`}}/>
 </AbsoluteFill>;
};
const Marks:React.FC=()=> {const f=useCurrentFrame();const disclosure=f>=61&&f<204?'재구성 · 시간 압축':f>=204&&f<755?'재구성 · 시각비유':'재구성';return <>
 <div style={{position:'absolute',left:120,top:205,fontFamily:'Quiet Sans',fontWeight:700,fontSize:27,color:'#fff',WebkitTextStroke:'3px #171512',paintOrder:'stroke fill'}}>몇년나옴 #16</div>
 <div data-disclosure style={{position:'absolute',right:120,top:205,fontFamily:'Quiet Sans',fontWeight:700,fontSize:36,color:'#fff',WebkitTextStroke:'3px #171512',paintOrder:'stroke fill',whiteSpace:'nowrap'}}>{disclosure}</div>
</>};
const Title:React.FC<{cover?:boolean}>=({cover=false})=><div style={{...lettering,position:'absolute',left:90,width:900,textAlign:'center',top:cover?635:350,fontSize:72,whiteSpace:'nowrap'}}>박치기 22번. 몇 년?</div>;
const RequiredFacts:React.FC=()=>{const f=useCurrentFrame();return <>
 {f>=61&&f<204&&<div data-headbutts-fact style={{...lettering,position:'absolute',left:90,width:900,textAlign:'center',top:350,fontSize:64,whiteSpace:'nowrap'}}>박치기 22회</div>}
 {f>=710&&<div data-demand-sentence style={{...lettering,position:'absolute',left:90,width:900,textAlign:'center',top:350,fontSize:64,whiteSpace:'pre-line'}}>{'구형 징역 1년\n→ 선고 벌금 400만 원'}</div>}
</>};
const Choices:React.FC=()=>{
 const f=useCurrentFrame();
 return <div style={{position:'absolute',left:125,top:550,display:'flex',gap:42}}>
 {data.ep.choices.map((text,i)=>{const p=spring({frame:f-i*3,fps:30,config:{damping:12,mass:.5,stiffness:180}});return <div key={text} style={{...lettering,fontSize:43,whiteSpace:'nowrap',transform:`scale(${.7+.3*p})`,opacity:Math.min(1,p*2)}}><span style={{fontSize:30,marginRight:10}}>{'ABC'[i]}</span>{text}</div>})}
 </div>;
};
const Captions:React.FC<{audit?:boolean}>=({audit=false})=>{
 const f=useCurrentFrame();
 // Match actual original visibility: first 61 frames and final 45 frames use hero UI.
 if(f<61||f>=755)return null;
 const index=captions.findIndex(x=>f*1000/30>=x.startMs&&f*1000/30<x.endMs);
 const s=data.subtitles[index];if(!s)return null;
 const end=s.from_===754;
 const breaks:Record<number,string>={286:'집행유예\n기간 중이었어요.',334:'벌금, 집행유예, 실형 중\n무엇이었을까요?',486:'다만 범행을\n모두 인정했고'};
 const text=breaks[s.from_]??s.text;
 return <Narration text={end?text.replace('\n',' '):text} from={s.from_} to={s.to} audit={audit} emphasis={s.from_===668?'벌금 400만 원':undefined}/>;
};
export const Unslop:React.FC<{audit?:boolean}>=({audit=false})=>{
 const f=useCurrentFrame();
 const bodyScale=.985+.015*(.5-.5*Math.cos(f*Math.PI/90));
 const cue=data.cues.find(c=>f>=c.from&&f<(c.id==='C5'?755:c.from+c.dur));
 const scene=cue?.id==='C1'?<Reenactment/>:cue?.id==='C2'?<CustodyScene/>:cue?.id==='C3'?<ProbationScene/>:cue?.id==='C4'?<CourtComedy at={[72,157,260]}>{null}</CourtComedy>:<Sentencing hit={6} second={46} choices={data.ep.choices} answer={data.ep.answer}/>;
 return <AbsoluteFill data-owner-canvas style={{background:'#E7E0CD',overflow:'hidden'}}>
  {f<=60?<Hero/>:f>=755?<Hero end/>:<>
   <div style={{position:'absolute',left:-110,top:180,width:1000,height:900,transform:`translate(${650*(1-bodyScale)}px,${585*(1-bodyScale)}px) scale(${1.30*bodyScale})`,transformOrigin:'0 0'}}>
    {cue&&<Sequence from={cue.from} layout="none">{scene}</Sequence>}
   </div>
   {f>=329&&f<663&&<Sequence from={329} layout="none"><Choices/></Sequence>}
  </>}
  <Marks/>
  <RequiredFacts/>
  {f<=60&&<Title/>}
  <Captions audit={audit}/>
  {f>=755&&<Narration text="다음 사건도 맞혀 보세요." from={755} to={800} audit={audit}/>}
 </AbsoluteFill>;
};
export const CoverUnslop:React.FC=()=> <AbsoluteFill><Hero/><Marks/><Title cover/></AbsoluteFill>;
