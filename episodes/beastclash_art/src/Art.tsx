import React from 'react';
import {AbsoluteFill,useCurrentFrame,interpolate,Easing} from 'remotion';
import art from './art.json';
type Part={name:string;svg:string;clip:string|null;extra?:string;outline?:string;pivot:number[]};
type A={size:number;ground:number;parts:Part[];clips?:Record<string,string>};
const ART=art as unknown as Record<'polar'|'walrus',A>;
export type Pose=Record<string,{r?:number;dx?:number;dy?:number;sy?:number}>;
const H=(s:string)=>({dangerouslySetInnerHTML:{__html:s}});
export const Stock:React.FC<{kind:'polar'|'walrus';x:number;y:number;s:number;flip?:boolean;pose?:Pose;explode?:Record<string,number[]>}>=({kind,x,y,s,flip,pose={},explode})=>{
 const a=ART[kind],k=s/a.size,id=kind+(explode?'x':'');
 return <g transform={`translate(${x} ${y}) scale(${flip?-k:k} ${k}) translate(${-a.size/2} ${-a.ground})`}>
  <defs>{a.clips&&Object.entries(a.clips).map(([n,p])=><clipPath key={n} id={`${id}-${n}`}><polygon points={p}/></clipPath>)}
   {a.clips&&<mask id={`${id}-NOT`} maskUnits="userSpaceOnUse" x={0} y={0} width={a.size} height={a.size}><rect width={a.size} height={a.size} fill="#fff"/>{Object.values(a.clips).map((p,i)=><polygon key={i} points={p} fill="#000"/>)}</mask>}</defs>
  {a.parts.map(p=>{const q=pose[p.name]||{},e=explode?.[p.name]||[0,0],[px,py]=p.pivot;
   const t=`translate(${(q.dx||0)+e[0]} ${(q.dy||0)+e[1]}) rotate(${q.r||0} ${px} ${py}) translate(${px} ${py}) scale(1 ${q.sy||1}) translate(${-px} ${-py})`;
   return <g key={p.name} transform={t}>
    {p.clip==='NOT'?<><g {...H(p.svg)}/><g mask={`url(#${id}-NOT)`} {...H(p.outline||'')}/></>:p.clip?<g clipPath={`url(#${id}-${p.clip})`} {...H(p.svg)}/>:<g {...H(p.svg)}/>}
    {p.extra&&<g {...H(p.extra)}/>}
   </g>;})}
 </g>;};
const ez=(f:number,a:number,b:number,v0:number,v1:number,e=Easing.inOut(Easing.cubic))=>interpolate(f,[a,b],[v0,v1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:e});
// 0-54 idle breathing, 54-64 anticipation, 64-70 strike, 70-90 hold/settle
export const posePolar=(f:number):Pose=>{const b=Math.sin(f/30*Math.PI*2/1.6),ant=ez(f,54,64,0,1)-ez(f,64,69,0,1),hit=ez(f,64,69,0,1,Easing.out(Easing.back(2)))-ez(f,78,90,0,1);
 const dx=ant*90-hit*230,head={r:b*1.5+ant*10-hit*14,dx:dx-hit*40,dy:-b*8+hit*30};
 return {body:{sy:1+b*.012,dx,dy:0},head,ears:head,farFront:{r:b*3-ant*35+hit*62,dx,dy:-b*4},nearFront:{r:ant*6-hit*10,dx},farLegs:{r:-ant*4+hit*8,dx:dx*.6}};};
export const poseWalrus=(f:number):Pose=>{const b=Math.sin((f+9)/30*Math.PI*2/1.9),ant=ez(f,56,66,0,1)-ez(f,66,71,0,1),hit=ez(f,66,71,0,1,Easing.out(Easing.back(2)))-ez(f,80,90,0,1);
 return {body:{sy:1+b*.014},head:{r:b*1.2+ant*9-hit*13,dy:-b*10-ant*40+hit*60,dx:-hit*70},flipper:{r:b*1.5-hit*7,dy:-b*3},tail:{r:-b*2.5+hit*5}};};
const Bg:React.FC=()=> <><rect width={1080} height={1920} fill="#BFE3F5"/><rect y={1180} width={1080} height={740} fill="#F2FAFF"/><path d="M0 1180H1080" stroke="#2A6FA8" strokeWidth={10}/></>;
export const Test:React.FC=()=>{const f=useCurrentFrame();return <AbsoluteFill><svg width={1080} height={1920}><Bg/>
 <Stock kind="walrus" x={800} y={1360} s={860} pose={poseWalrus(f)}/>
 <Stock kind="polar" x={270} y={1470} s={840} flip pose={posePolar(f)}/>
 </svg></AbsoluteFill>;};
export const Parts:React.FC<{kind:'polar'|'walrus'}>=({kind})=>{const ex=kind==='polar'?{ears:[-330,-330],head:[-330,-200],farFront:[-420,330],farLegs:[150,420],nearFront:[-120,520],body:[330,-60]}:{head:[330,-480],flipper:[330,420],tail:[-420,180],body:[0,0]};
 return <AbsoluteFill style={{background:'#C9D3DA'}}><svg width={1080} height={1080}><Stock kind={kind} x={520} y={kind==='polar'?760:800} s={600} explode={ex}/></svg></AbsoluteFill>;};
