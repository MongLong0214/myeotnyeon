// 철컹철컹 kit: strong-text style (black / deep red, huge yellow-white Korean type with thick outline, prison bars).
import React from 'react';
import {AbsoluteFill,continueRender,delayRender,staticFile} from 'remotion';
const INK='#0A0A0A',YEL='#FFD400',WHITE='#FFFFFF',RED='#B3121B',DEEP='#5A0508';
let p:Promise<void>|null=null;
export const useKFonts=()=>{const [h]=React.useState(()=>delayRender('kfonts'));
 React.useEffect(()=>{p??=Promise.all([['KHead','BlackHanSans-Regular.ttf'],['KBody','Pretendard-Bold.otf']].map(async([f,file])=>{
  const ff=await new FontFace(f,`url(${staticFile('fonts/'+file)})`).load();document.fonts.add(ff);})).then(()=>undefined);p.then(()=>continueRender(h));},[h]);};
const HEAD="'KHead', sans-serif",BODY="'KBody', sans-serif";
const T:React.FC<{x:number;y:number;size:number;fill:string;sw?:number;font?:string;ls?:number;children:React.ReactNode}>=({x,y,size,fill,sw=0,font=HEAD,ls=0,children})=>
 <text x={x} y={y} fontSize={size} fill={fill} stroke={INK} strokeWidth={sw} strokeLinejoin="round" paintOrder="stroke" fontFamily={font} textAnchor="middle" letterSpacing={ls}>{children}</text>;
const Bars:React.FC<{x0:number;x1:number;y0:number;y1:number;n:number;w:number}>=({x0,x1,y0,y1,n,w})=><g>
 {Array.from({length:n},(_,i)=>{const x=x0+(x1-x0)*(i+.5)/n;return <g key={i}><rect x={x-w/2} y={y0} width={w} height={y1-y0} fill="#2A2A2E" stroke={INK} strokeWidth={w*.18}/>
  <rect x={x-w/2+w*.18} y={y0} width={w*.16} height={y1-y0} fill="#55555C"/></g>;})}</g>;
export const MarkK:React.FC<{size?:number}>=({size=800})=><svg width={size} height={size} viewBox="0 0 800 800">
 <defs><radialGradient id="g" cx="50%" cy="45%" r="60%"><stop offset="0" stopColor={RED}/><stop offset="1" stopColor={DEEP}/></radialGradient></defs>
 <rect width={800} height={800} fill="url(#g)"/>
 <Bars x0={60} x1={740} y0={0} y1={800} n={5} w={46}/>
 <rect x={0} y={150} width={800} height={34} fill="#2A2A2E" stroke={INK} strokeWidth={8}/>
 <T x={400} y={515} size={330} fill={YEL} sw={44} ls={-6}>철컹</T>
</svg>;
export const PFPK:React.FC=()=>{useKFonts();return <AbsoluteFill><MarkK/></AbsoluteFill>;};
export const WMK:React.FC=()=>{useKFonts();return <AbsoluteFill>
 <div style={{position:'absolute',left:4,top:4,width:142,height:142,borderRadius:71,overflow:'hidden',border:`6px solid ${WHITE}`,boxSizing:'border-box'}}>
  <svg width={130} height={130} viewBox="0 0 800 800"><rect width={800} height={800} fill={DEEP}/><Bars x0={60} x1={740} y0={0} y1={800} n={5} w={40}/>
   <T x={400} y={520} size={330} fill={YEL} sw={60} ls={-10}>철컹</T></svg></div></AbsoluteFill>;};
const SX=507,SY=508,SW=1546,SH=424,CX=1280;
export const BannerK:React.FC=()=>{useKFonts();return <AbsoluteFill style={{background:INK}}>
 <svg width={2560} height={1440} style={{position:'absolute'}}>
  <defs><radialGradient id="b" cx="50%" cy="50%" r="50%"><stop offset="0" stopColor={RED}/><stop offset=".6" stopColor={DEEP}/><stop offset="1" stopColor={INK}/></radialGradient></defs>
  <rect width={2560} height={1440} fill="url(#b)"/>
  <Bars x0={0} x1={470} y0={0} y1={1440} n={4} w={54}/><Bars x0={2090} x1={2560} y0={0} y1={1440} n={4} w={54}/>
  <rect x={0} y={420} width={470} height={40} fill="#2A2A2E" stroke={INK} strokeWidth={8}/><rect x={2090} y={980} width={470} height={40} fill="#2A2A2E" stroke={INK} strokeWidth={8}/>
  <T x={CX} y={SY+215} size={250} fill={YEL} sw={40} ls={6}>철컹철컹</T>
  <T x={CX} y={SY+310} size={64} fill={WHITE} sw={14} font={BODY}>실제 판결, <tspan fill={YEL}>결과부터</tspan> 말합니다</T>
  <rect x={CX-330} y={SY+346} width={660} height={64} rx={10} fill={INK} stroke={YEL} strokeWidth={5}/>
  <T x={CX} y={SY+392} size={40} fill={WHITE} font={BODY} ls={2}>판결 → 사건 → 법원의 반전</T>
 </svg></AbsoluteFill>;};
