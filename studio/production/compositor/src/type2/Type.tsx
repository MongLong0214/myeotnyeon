import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadType2Fonts} from './fonts';
loadType2Fonts();
export const ink='#10110f',white='#eae8df',lime='#b5bf28',red='#ed2919';
const clamp={extrapolateLeft:'clamp',extrapolateRight:'clamp'} as const;
// No CSS-time animations: every mark is tied to the composition frame.
export const useTypeTime=()=>{const frame=useCurrentFrame();const {fps}=useVideoConfig();return {frame,t:frame*30/fps};};
export const Cut:React.FC<{at?:number;until?:number;children:React.ReactNode}>=({at=0,until=132,children})=>{const {t}=useTypeTime();return t>=at&&t<until?<>{children}</>:null;};
export const Texture:React.FC<{paper?:boolean;scan?:boolean}>=({paper=false,scan=false})=>{
 const {frame}=useTypeTime();return <><svg width="100%" height="100%" style={{position:'absolute',inset:0,opacity:paper?.16:.1,mixBlendMode:paper?'multiply':'screen',pointerEvents:'none'}}><filter id="t2-grain"><feTurbulence type="fractalNoise" baseFrequency={paper?'.48':'.82'} numOctaves="3" seed={paper?41:41+Math.floor(frame/3)}/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#t2-grain)"/></svg>{scan&&<AbsoluteFill style={{pointerEvents:'none',background:'repeating-linear-gradient(0deg,transparent 0px,transparent 3px,#0008 3px,#0008 4px)',opacity:.45}}/>}</>;
};
export const RecordGrid:React.FC=()=> <AbsoluteFill style={{backgroundColor:'#080908',backgroundImage:'linear-gradient(#a5a59b30 1px,transparent 1px),linear-gradient(90deg,#a5a59b30 1px,transparent 1px)',backgroundSize:'96px 96px',backgroundPosition:'-8px -12px'}}/>;
/** C04, C12: skewed heavy gothic, granular lime face, hard edit. */
export const ChapterCard:React.FC<{number:string;title:string}>=({number,title})=>{
 const {t,frame}=useTypeTime();const reveal=interpolate(t,[0,18],[.07,1],clamp);
 return <AbsoluteFill style={{background:'#171816',color:lime,justifyContent:'center',alignItems:'center'}}>
  <svg width="1920" height="1080" style={{position:'absolute',opacity:.17}}><path d="M710 180V900M870 100V980M1030 100V980M1190 180V900" stroke="#999b91" strokeWidth="14"/><path d="M730 980Q720 630 820 610L850 530Q785 440 820 310Q850 160 970 180Q1100 190 1110 330Q1140 460 1050 540L1080 610Q1200 650 1210 980Z" fill="#808477"/></svg>
  <svg width="1500" height="240" viewBox="0 0 1500 240" style={{position:'relative',transform:'skewX(-9deg)'}}><defs><filter id="t2-erode"><feTurbulence type="fractalNoise" baseFrequency=".55" numOctaves="2" seed={Math.floor(frame/2)+12}/><feColorMatrix type="luminanceToAlpha"/><feComponentTransfer><feFuncA type="discrete" tableValues={`0 0 ${reveal} 1`}/></feComponentTransfer><feComposite in="SourceGraphic" operator="in"/></filter></defs><text x="750" y="170" textAnchor="middle" fill={lime} fontFamily="T2 Black" fontSize="142" letterSpacing="-7" filter="url(#t2-erode)">{number}. {title}</text></svg>
  <Texture scan/>
 </AbsoluteFill>;
};
/** C01/C08: compact serif date; decoded R2 F0..30 shows a true typing reveal. */
export const DateLine:React.FC<{text:string;x?:number;y?:number;align?:'center'|'left'}>=({text,x=540,y=42,align='center'})=>{
 const {t}=useTypeTime();return <Cut><div style={{position:'absolute',left:x,top:y,width:840,textAlign:align,fontFamily:'T2 Song',fontSize:43,lineHeight:1.1,letterSpacing:'-.04em',color:white,textShadow:'1px 2px #181813'}}>{text.slice(0,Math.max(0,Math.floor(t*1.1)))}</div></Cut>;
};
/** C02: one line, fixed baseline, 2px hard edge rather than a blurred halo. */
export const Subtitle:React.FC<{text:string;portrait?:boolean}>=({text,portrait=false})=><Cut at={4}><div style={{position:'absolute',left:portrait?62:120,top:portrait?1250:935,width:portrait?870:1680,textAlign:portrait?'left':'center',fontFamily:'T2 Sans',fontWeight:600,fontSize:portrait?57:48,lineHeight:portrait?1.25:1.15,letterSpacing:'-.045em',whiteSpace:'pre-line',color:'#f2f1e9',WebkitTextStroke:portrait?'1.5px #111':'1px #111',paintOrder:'stroke fill',textShadow:'1px 2px 0 #111'}}>{text}</div></Cut>;
export const SourceLine:React.FC<{text:string;portrait?:boolean}>=({text,portrait=false})=><div style={{position:'absolute',left:portrait?62:26,top:portrait?1435:1040,fontFamily:'T2 Coding',fontSize:portrait?23:19,lineHeight:1.3,color:'#b2b2a9',letterSpacing:'-.03em'}}>{text}</div>;
/** C19/20 role label: square ink strip and a small pointer, no badge pill. */
export const EvidenceLabel:React.FC<{text:string;x:number;y:number}>=({text,x,y})=><div style={{position:'absolute',left:x,top:y,fontFamily:'T2 Song',fontSize:38,color:white,background:ink,border:`3px solid ${white}`,padding:'5px 14px',lineHeight:1.2}}>{text}<span style={{position:'absolute',left:25,bottom:-21,width:0,height:0,borderTop:`19px solid ${white}`,borderRight:'12px solid transparent'}}/></div>;
/** C03: the annotation is attached to a bracket in scene coordinates. */
export const MeasurementLabel:React.FC<{text:string}>=({text})=>{const {t}=useTypeTime();return <svg width="1920" height="1080" style={{position:'absolute',inset:0}}><path d="M489 629v26H1350v-26" fill="none" stroke="#eee091" strokeWidth="3" strokeDasharray="4 8" transform="rotate(-7.4 1035 500)" style={{clipPath:`inset(0 ${(1-interpolate(t,[0,18],[0,1],clamp))*100}% 0 0)`}}/>{t>=24&&<text x="1380" y="615" fontFamily="T2 Sans" fontWeight="600" fontSize="49" fill="#eee7c5">{text}</text>}</svg>;};
const RoleCutout:React.FC=()=> <svg viewBox="0 0 460 570" width="460" height="570"><defs><clipPath id="t2-role"><circle cx="230" cy="310" r="198"/></clipPath><pattern id="t2-dot" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#111"/></pattern></defs><circle cx="230" cy="310" r="198" fill="#34372f" stroke={white} strokeWidth="6"/><g clipPath="url(#t2-role)"><path d="M0 570L48 402Q80 364 154 350L170 314Q130 278 133 208Q137 105 230 102Q320 105 324 205Q327 276 288 316L303 350Q399 370 420 417L460 570Z" fill="#c5c4ba"/><path d="M100 431L360 401M95 451L366 421M90 471L371 441M85 491L376 461M80 511L381 481" stroke="#83857c" strokeWidth="3"/><path d="M0 0H460V570H0Z" fill="url(#t2-dot)" opacity=".4"/></g></svg>;
/** C05/06: fixed portrait at left, heading high/right, lines accumulate. */
export const DossierCard:React.FC<{verdict?:boolean}>=({verdict=false})=>{
 const {t}=useTypeTime();const lines=[['2024년 5월 23일','규정을 위반한 군기훈련'],['2025년 1월 7일 · 1심','징역 5년'],['2025년 6월 18일 · 2심','징역 5년 6개월']];
 return <AbsoluteFill style={{color:white}}><RecordGrid/><div style={{position:'absolute',left:340,top:210}}><RoleCutout/></div><div style={{position:'absolute',left:850,top:102,fontFamily:'T2 Myeongjo',fontWeight:800,fontSize:65,letterSpacing:'-.04em'}}>중대장</div>
  <div style={{position:'absolute',left:900,top:217,fontFamily:'T2 Myeongjo',fontSize:40,lineHeight:1.45,letterSpacing:'-.045em'}}>{lines.slice(0,verdict?3:2).map(([date,body],i)=>{const n=Math.max(0,Math.floor((t-i*25-4)*2));return <div key={date} style={{marginBottom:35,visibility:n>0?'visible':'hidden'}}><div>{date.slice(0,n)}</div><div style={{fontSize:verdict&&i===2?68:39,fontWeight:verdict&&i===2?800:400,marginTop:2,minHeight:verdict&&i===2?98:56}}>{body.slice(0,Math.max(0,n-date.length))}</div></div>;})}{verdict&&t>=66&&<div style={{fontSize:30,marginTop:23}}>2025년 9월 25일 · 상고 기각, 확정</div>}</div>
  <Subtitle text={verdict?'중대장 징역 5년 6개월이 확정됐습니다.':'1심은 중대장에게 징역 5년을 선고했습니다.'}/><SourceLine text={verdict?'한겨레 · 뉴시스 · KBS / 2025.09.25':'뉴시스 · 뉴스1 / 2025.01.07'}/><Texture/>
 </AbsoluteFill>;
};
