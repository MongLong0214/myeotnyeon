import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {FONT} from '../../../../../production/compositor/src/theme';
import {ArticulatedGuy} from './FightRig';
import {standing,k,point,smooth} from './FightScene';
const ink='#1E1712',yellow='#F2C14E';
const label:React.CSSProperties={position:'absolute',fontFamily:FONT,fontWeight:800,color:ink,textAlign:'center'};
const Phone:React.FC<{x:number;y:number;rot?:number;scale?:number}>=({x,y,rot=0,scale=1})=><g transform={`translate(${x} ${y}) rotate(${rot}) scale(${scale})`}>
 <rect x={-55} y={-100} width={110} height={200} rx={22} fill="#445069" stroke={ink} strokeWidth={8}/><rect x={-39} y={-74} width={78} height={140} rx={8} fill="#ECF2D7" stroke={ink} strokeWidth={5}/><circle cy={40} r={18} fill="#C9503E" stroke={ink} strokeWidth={4}/><path d="M-26,-20h10v-20h10v45h10v-38h10v23h12" fill="none" stroke={ink} strokeWidth={5}/><circle cy={82} r={5} fill="#ECF2D7"/>
</g>;
export const RecorderComedy:React.FC=()=>{
 const f=useCurrentFrame(),r=standing();r.torso=k(f,[[0,-12],[50,-12],[68,-24],[92,-17],[115,-3],[148,6]]);r.head=k(f,[[0,14],[70,14],[96,-8],[110,8]]);
 r.hands=[[-72,-185],[160,-285]];r.elbows=[[-98,-260],[85,-330]];
 const insert=f>=115&&f<126;const metaphor=f>=67,fold=smooth((f-110)/17);
 return <AbsoluteFill style={{background:metaphor?'#C9DF92':'#4E4058'}}>
  <svg width={1000} height={900} style={{position:'absolute'}}><rect y={760} width={1000} height={140} fill="#8E9E7F" stroke={ink} strokeWidth={8}/>{!metaphor&&<><rect x={650} y={250} width={200} height={510} fill="#1F2231" stroke={ink} strokeWidth={8}/><path d="M670,250L850,180V760H670Z" fill="#302E41" stroke={ink} strokeWidth={8}/></>}</svg>
  <ArticulatedGuy look="hoodie" x={insert?340:360} y={insert?1080:810} scale={insert?1.18:.71} rig={r} expr={fold>.5?'shock':'smug'} eye={[10,-3]}/>
  <svg width={1000} height={900} style={{position:'absolute',pointerEvents:'none'}}>
   {!insert&&<Phone x={474} y={608} rot={-8}/>}
   {metaphor&&<g transform={`translate(662 390) rotate(${fold*65})`}><path d="M-190,0Q0,-240 190,0Q100,-35 0,0Q-100,-35 -190,0" fill={yellow} stroke={ink} strokeWidth={10}/><path d="M0,-110V160q0,55 45,25" fill="none" stroke={ink} strokeWidth={12}/><text y={-50} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={48}>면책?</text>{fold>.3&&<path d="M-80,-140L75,-20M75,-140L-80,-20" stroke="#C9503E" strokeWidth={16}/>}</g>}
  </svg>
  <div style={{...label,top:32,left:70,width:860,fontSize:48,color:metaphor?ink:'#FFFDF6'}}>검찰 판단 · 녹음 시도</div>
  <div style={{...label,top:110,left:95,width:810,fontSize:35,color:'#FFFDF6',background:ink,borderRadius:12,padding:'8px 0'}}>{metaphor?'시각비유 · 녹음 ≠ 면책':'CCTV 없는 곳으로 불러내'}</div>
  <div style={{...label,top:810,left:60,width:880,fontSize:27,background:'#E7E0CD',borderRadius:8,padding:'4px 0'}}>보도 기반 재구성 · 허구 캐릭터 / 비유 장면</div>
 </AbsoluteFill>;
};
export const CourtComedy:React.FC<{children:React.ReactNode}>=({children})=>{
 const f=useCurrentFrame(),insert=f>=102&&f<114,a=standing(),j=standing();const move=smooth((f-69)/30),surprise=smooth((f-100)/10);
 a.torso=k(f,[[0,-18],[69,-18],[100,-5],[110,15],[140,8],[245,6],[260,-5],[335,0]]);a.head=k(f,[[0,12],[100,12],[110,-12],[145,0]]);a.hands=[[-85,-205],[110-50*surprise,-235-40*surprise]];a.elbows=[[-105,-270],[90,-300]];
 j.hands=[[55,-230],[110,-220]];j.elbows=[[0,-270],[95,-280]];j.head=k(f,[[0,0],[72,0],[100,-8],[140,-8],[155,0]]);
 const px=440+300*move,py=566-80*Math.sin(Math.PI*move);
 return <AbsoluteFill style={{background:'#E7E0CD'}}>
  <svg width={1000} height={900} style={{position:'absolute'}}><rect x={0} y={270} width={1000} height={570} fill="#CDBB99"/><path d="M0,780H1000" stroke={ink} strokeWidth={8}/><path d="M430,675Q620,770 810,650" stroke="#B0A184" strokeWidth={26} fill="none"/></svg>
  <ArticulatedGuy look="hoodie" x={insert?485:275} y={insert?1160:805} scale={insert?1.23:.63} rig={a} expr={f<100?'smug':f<135?'shock':'tired'} eye={[10,0]}/>
  {!insert&&<ArticulatedGuy look="judge" x={770} y={790} scale={.58} rig={j} expr="serious" eye={[-10,3]}/> }
  {!insert&&<svg width={1000} height={900} style={{position:'absolute'}}>
   <rect x={640} y={625} width={330} height={190} rx={14} fill="#A27547" stroke={ink} strokeWidth={8}/>
   <path d="M640,630L950,630L920,540H680Z" fill="#FAF0CC" stroke={ink} strokeWidth={7}/>
   <Phone x={px} y={py} scale={.56} rot={move*90}/>
   {f>=100&&<text x={795} y={728} textAnchor="middle" fontSize={44} fontFamily={FONT} fontWeight={900} fill={ink}>증거</text>}
  </svg>}
  {children}
  <div style={{...label,top:140,left:45,width:910,fontSize:41}}>판사가 본 사정</div>
  <div style={{...label,top:208,left:70,width:860,fontSize:30,color:'#FFFDF6',background:ink,borderRadius:12,padding:'8px 0'}}>시각비유 · 녹음이 증거로 돌아오다</div>
  {f>=69&&<div style={{...label,top:810,left:60,width:880,fontSize:31,background:'#E7E0CD',borderRadius:8,padding:'4px 0'}}>{f<136?'피고인이 남긴 녹음':f<245?'법원: 저항 못 하는데 계속 가격':'녹음 뒤 “신고하려면 하라”'}</div>}
 </AbsoluteFill>;
};
