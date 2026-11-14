// 철컹철컹 v2 directions A/B/C. Wordmark glyphs are hand-built geometric strokes (no font); taglines use Pretendard Bold (OFL).
import React from 'react';
import {AbsoluteFill,Img,staticFile} from 'remotion';
import {Guy,OL} from '../../episodes/quiz/batch_1107/b_format/FightRig';
import {useKFonts} from './Cheol';
const BODY="'KBody', sans-serif";
type Dir='A'|'B'|'C';
// ---------- custom geometric hangul: box 100 x 124 ----------
const STEM=(bar:boolean)=>bar?'M86 -40V164':'M86 0V64';
const CH=(k:'철'|'컹',bar:boolean)=>k==='철'
 ?{ink:['M31 0V14','M4 18H58','M31 18L5 54','M31 28L60 54',STEM(bar),'M62 32H86','M10 70H88V95H12V120H90'],ring:null}
 :{ink:['M4 8H56L42 60','M6 34H50',STEM(bar),'M62 32H86'],ring:[49,96,21]};
export const Word:React.FC<{x:number;y:number;s:number;t?:number;ink:string;accent?:string;bars?:boolean;word?:string;adv?:number}>=({x,y,s,t=15,ink,accent,bars=false,word='철컹철컹',adv=116})=>
 <g transform={`translate(${x} ${y}) scale(${s})`} fill="none" strokeWidth={t} strokeLinejoin="miter" strokeLinecap="butt">
  {[...word].map((k,i)=>{const g=CH(k as any,bars);return <g key={i} transform={`translate(${i*adv} 0)`}>
   {g.ink.map((d,j)=><path key={j} d={d} stroke={bars&&d.startsWith('M86')?(accent??ink):ink} strokeLinecap={bars&&d.startsWith('M86')?'round':'butt'}/>)}
   {g.ring&&<circle cx={g.ring[0]} cy={g.ring[1]} r={g.ring[2]} stroke={ink}/>}</g>;})}
 </g>;
const wordW=(n:number,s:number,adv=116)=>((n-1)*adv+100)*s;
const Tag:React.FC<{x:number;y:number;size:number;fill:string;accent:string;anchor?:any;ls?:number}>=({x,y,size,fill,accent,anchor='middle',ls=0})=>
 <text x={x} y={y} fontSize={size} fill={fill} fontFamily={BODY} textAnchor={anchor} letterSpacing={ls}>판결, 결과부터<tspan fill={accent}>.</tspan></text>;
// ---------- A: minimal wordmark ----------
const A={bg:'#F3EFE6',ink:'#111111',acc:'#E2361B'};
const PfpA=()=><svg width={800} height={800}><rect width={800} height={800} fill={A.bg}/>
 <g transform="translate(205 150) scale(4.1)" fill="none" strokeWidth={17} strokeLinejoin="miter">
  {['M31 0V14','M4 18H58','M31 18L5 54','M31 28L60 54','M62 32H86','M10 70H88V95H12V120H90'].map((d,i)=><path key={i} d={d} stroke={A.ink}/>)}
  <path d="M86 -40V136" stroke={A.acc} strokeWidth={17}/></g></svg>;
const BannerA=()=><svg width={2560} height={1440}><rect width={2560} height={1440} fill={A.bg}/>
 <Word x={1280-wordW(4,1.6)/2} y={600} s={1.6} ink={A.ink} accent={A.acc} bars t={16}/>
 <Tag x={1280} y={905} size={50} fill={A.ink} accent={A.acc} ls={2}/></svg>;
// ---------- B: mascot ----------
const B={bg:'#F28A2E',ink:OL,bar:'#3B3F4A',bar2:'#5C6170',cream:'#FFF6E6',skin:'#F4CFA7'};
const Bars:React.FC<{xs:number[];y0:number;y1:number;w:number}>=({xs,y0,y1,w})=><g>{xs.map((x,i)=><g key={i}>
 <rect x={x-w/2} y={y0} width={w} height={y1-y0} rx={w/2} fill={B.bar} stroke={B.ink} strokeWidth={w*.22}/>
 <rect x={x-w*.22} y={y0+w*.6} width={w*.16} height={y1-y0-w*1.2} rx={w*.08} fill={B.bar2}/></g>)}</g>;
const Fist:React.FC<{x:number;y:number;s:number}>=({x,y,s})=><g transform={`translate(${x} ${y}) scale(${s})`} stroke={B.ink} strokeWidth={9} strokeLinejoin="round" strokeLinecap="round">
 <rect x={-52} y={-40} width={104} height={80} rx={30} fill={B.skin}/>
 <path d="M-18 -38V-6M14 -38V-6" fill="none" strokeWidth={7}/></g>;
// Guy head sits ~ y=-440 local; bust shows head+shoulders
const Mascot:React.FC<{cx:number;cy:number;s:number;expr?:any}>=({cx,cy,s,expr='scared'})=>
 <g transform={`translate(${cx} ${cy}) scale(${s})`}>
  <foreignObject x={-500} y={-450} width={1000} height={900}><div style={{position:'relative',width:1000,height:900}}>
   <Guy look="inmate" x={500} y={900} scale={1} expr={expr} pose="bust" eye={[0,-6]} wobble={0}/></div></foreignObject>
 </g>;
const PfpB=()=><svg width={800} height={800}><rect width={800} height={800} fill={B.bg}/>
 <Mascot cx={400} cy={330} s={1.5} expr="scared"/>
 <Bars xs={[230,570]} y0={-40} y1={840} w={70}/>
 <Fist x={230} y={640} s={1.3}/><Fist x={570} y={640} s={1.3}/></svg>;
const BannerB=()=><svg width={2560} height={1440}><rect width={2560} height={1440} fill={B.bg}/>
 <g transform="translate(560 0)"><Mascot cx={300} cy={760} s={.62} expr="scared"/>
  <Bars xs={[195,405]} y0={440} y1={1000} w={36}/><Fist x={195} y={860} s={.6}/><Fist x={405} y={860} s={.6}/></g>
 <Word x={1130} y={600} s={1.55} ink={B.ink} t={19}/>
 <Tag x={1130} y={880} size={60} fill={B.ink} accent={B.cream} anchor="start" ls={1}/></svg>;
// ---------- C: symbol ----------
const C={bg:'#121A2B',ink:'#F4F1EA',acc:'#FF5A1F',mid:'#2A3550'};
// geometric handcuffs: two rings + link, drawn on 200 box centred 0,0
const Cuffs:React.FC<{s:number;x:number;y:number;fg?:string}>=({s,x,y,fg=C.ink})=><g transform={`translate(${x} ${y}) scale(${s}) rotate(-24)`}>
 {/* straight double-swivel bar with one link */}
 <rect x={-34} y={-8} width={68} height={16} fill={fg}/>
 <rect x={-17} y={-15} width={34} height={30} rx={15} fill="none" stroke={fg} strokeWidth={10}/>
 {[[-1,fg],[1,C.acc]].map(([k,c]:any)=><g key={k}>
  <circle cx={k*96} cy={0} r={44} fill="none" stroke={c} strokeWidth={20}/>
  {/* cuff case (hinge block) on the inner side */}
  <rect x={k>0?32:-70} y={-26} width={38} height={52} rx={6} fill={c}/>
  {/* ratchet nub on the outer side */}
  <rect x={k>0?136:-152} y={-11} width={16} height={22} rx={3} fill={c}/></g>)}
</g>;
const PfpC=()=><svg width={800} height={800}><rect width={800} height={800} fill={C.bg}/><Cuffs x={400} y={400} s={2.3}/></svg>;
const BannerC=()=><svg width={2560} height={1440}><rect width={2560} height={1440} fill={C.bg}/>
 <rect x={0} y={0} width={2560} height={1440} fill="none"/>
 <Cuffs x={700} y={720} s={1.05}/>
 <rect x={890} y={590} width={6} height={260} fill={C.mid}/>
 <Word x={960} y={600} s={1.45} ink={C.ink} t={18}/>
 <Tag x={962} y={835} size={54} fill="#AEB7C9" accent={C.acc} anchor="start" ls={1}/>
 <rect x={1480} y={804} width={0} height={0}/></svg>;
const P:Record<Dir,React.FC>={A:PfpA,B:PfpB,C:PfpC},BN:Record<Dir,React.FC>={A:BannerA,B:BannerB,C:BannerC};
const BG:Record<Dir,string>={A:A.bg,B:B.bg,C:C.bg};
export const Pfp2:React.FC<{d:Dir}>=({d})=>{useKFonts();const X=P[d];return <AbsoluteFill><X/></AbsoluteFill>;};
export const Banner2:React.FC<{d:Dir}>=({d})=>{useKFonts();const X=BN[d];return <AbsoluteFill><X/></AbsoluteFill>;};
export const Wm2:React.FC<{d:Dir}>=({d})=>{const X=P[d];return <AbsoluteFill>
 <div style={{position:'absolute',left:3,top:3,width:144,height:144,borderRadius:72,overflow:'hidden',border:'4px solid #fff',boxSizing:'border-box',background:BG[d]}}>
  <div style={{transform:'scale(0.17)',transformOrigin:'0 0',width:800,height:800}}><X/></div></div></AbsoluteFill>;};
// ---------- comparison board ----------
const circ=(src:string,px:number,bg:string)=><div style={{width:px+16,height:px+16,background:bg,display:'flex',alignItems:'center',justifyContent:'center'}}>
 <Img src={src} style={{width:px,height:px,borderRadius:px/2}}/></div>;
export const Compare2:React.FC=()=>{useKFonts();return <AbsoluteFill style={{background:'#E9E9EC',fontFamily:BODY,color:'#111'}}>
 <div style={{display:'flex',gap:40,padding:50}}>{(['A','B','C'] as Dir[]).map(d=>{const p=staticFile(`assets/v2_${d}_pfp.png`),b=staticFile(`assets/v2_${d}_banner.png`);
  return <div key={d} style={{width:720,background:'#fff',padding:30,boxSizing:'border-box',borderRadius:12}}>
   <div style={{fontSize:48,marginBottom:16}}>{d} · {d==='A'?'미니멀 워드마크':d==='B'?'마스코트':'심볼'}</div>
   <Img src={p} style={{width:660,height:660,borderRadius:330}}/>
   <div style={{display:'flex',gap:14,alignItems:'center',marginTop:24}}>
    {circ(p,98,'#0F0F0F')}{circ(p,98,'#FFFFFF')}{circ(p,48,'#0F0F0F')}{circ(p,48,'#FFFFFF')}</div>
   <div style={{fontSize:26,marginTop:22,color:'#555'}}>배너 모바일 안전영역 (1546×423)</div>
   <div style={{width:660,height:660*423/1546,overflow:'hidden',position:'relative',marginTop:8}}>
    <Img src={b} style={{position:'absolute',width:2560*660/1546,left:-507*660/1546,top:-508.5*660/1546}}/></div>
   <div style={{fontSize:26,marginTop:22,color:'#555'}}>배너 전체 (TV)</div>
   <Img src={b} style={{width:660,marginTop:8}}/>
  </div>;})}</div></AbsoluteFill>;};
