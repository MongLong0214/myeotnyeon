import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {FONT} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/theme';
import {ArticulatedGuy,Point,RigPose} from './FightRig';
export const smooth=(x:number)=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x)};
export const k=(t:number,points:[number,number][])=>{
 if(t<=points[0][0])return points[0][1];
 for(let i=1;i<points.length;i++){const [at,b]=points[i],[prev,a]=points[i-1];if(t<=at)return a+(b-a)*smooth((t-prev)/(at-prev))}return points[points.length-1][1];
};
export const point=(t:number,points:[number,Point][]):Point=>[k(t,points.map(([f,p])=>[f,p[0]])),k(t,points.map(([f,p])=>[f,p[1]]))];
export const standing=():RigPose=>({hip:[0,-170],torso:0,head:0,feet:[[-30,0],[30,0]],knees:[[-25,-90],[26,-90]],hands:[[-84,-166],[84,-166]],elbows:[[-70,-230],[70,-230]]});
export const ink='#1E1712',paper='#FFF8E8',red='#C9503E',teal='#2E9285';
export const label:React.CSSProperties={position:'absolute',fontFamily:FONT,fontWeight:800,color:ink,textAlign:'center',lineHeight:1.2};
export const Banner:React.FC<{children:React.ReactNode;top?:number;dark?:boolean}>=()=>null;

// Every contact increments the counter once. First and last actions are slower;
// twenty middle actions use an explicitly time-compressed four-frame cycle.
export const CONTACT_FRAMES=[73,...Array.from({length:20},(_,i)=>85+4*i),174];
export const impactState=(f:number)=>{
 let phase=0;
 if(f>=61&&f<=82)phase=(f-61)/21;
 else if(f>=83&&f<=162)phase=((f-83)%4)/3;
 else if(f>=163&&f<=180)phase=(f-163)/17;
 const active=f>=61&&f<=180;
 const thrust=active?k(phase,[[0,0],[.28,-.22],[.55,1],[.64,1],[1,0]]):0;
 const recoil=active?k(phase,[[0,0],[.55,0],[.72,1],[1,.15]]):0;
 return {phase,thrust,recoil,count:CONTACT_FRAMES.filter(c=>c<=f).length};
};
const DormRoom:React.FC=()=> <svg data-environment width={1000} height={2400} viewBox="0 -430 1000 2400" style={{position:'absolute',top:-430}}>
 <rect y={-430} width={1000} height={2400} fill="#E7DECA"/>
 <rect y={700} width={1000} height={1600} fill="#B79974" stroke={ink} strokeWidth={7}/>
 {[140,380,620,860].map(x=><path key={x} d={`M${x},700l-194,648`} stroke="#9D805D" strokeWidth={4}/>)}
 <g opacity={.7} stroke={ink} strokeWidth={6}>
  <rect x={35} y={300} width={22} height={400} rx={7} fill="#7B8796"/><rect x={237} y={300} width={22} height={400} rx={7} fill="#7B8796"/>
  {[405,625].map(y=><g key={y}><rect x={40} y={y} width={215} height={27} rx={8} fill={paper}/><rect x={80} y={y-23} width={155} height={26} rx={10} fill="#7A9CC6"/></g>)}
  <rect x={780} y={330} width={175} height={200} rx={8} fill="#BFD8E8"/><path d="M867,330V530"/>
 </g>
 <g transform="translate(495 747)" stroke={ink} strokeWidth={6}><path d="M-43,0h86l-9,70h-69Z" fill="#E8C14A"/><path d="M-20,0v-15a20,20 0 0,1 40,0V0" fill="none"/><rect x={-33} y={17} width={65} height={16} rx={4} fill={paper}/></g>
</svg>;
export const Reenactment:React.FC<{globalOffset?:number}>=({globalOffset=0})=>{
 const f=useCurrentFrame()+globalOffset,{thrust,recoil,count}=impactState(f);
 const a=standing(),v=standing();
 a.torso=18*thrust;a.head=8*thrust;a.hip=[62*thrust,-170-6*Math.max(0,-thrust)];
 a.feet=[[-62,0],[65,0]];a.knees=[[-30+25*thrust,-88],[40+20*thrust,-90]];
 a.hands=[[-85+25*thrust,-200],[94+20*thrust,-220]];a.elbows=[[-95,-260],[105,-282]];
 const hurt=f>180?smooth((f-180)/15):0;
 v.hip=[12*recoil+18*hurt,-170+13*recoil+25*hurt];v.torso=8*recoil+9*hurt;v.head=10*recoil+4*hurt;
 v.hands=[[-65,-240],[68,-240]];v.elbows=[[-76,-270],[75,-280]];
 if(hurt>0){v.hands[0]=[-65-14*hurt,-240-220*hurt];v.elbows![0]=[-76-50*hurt,-270-70*hurt];v.knees=[[-35,-75],[40,-75]];}
 return <AbsoluteFill>
  <DormRoom/>
  <ArticulatedGuy look="B" x={670} y={823} scale={.65} rig={v} anonymous expr="concern"/>
  <ArticulatedGuy look="hoodie" x={368} y={823} scale={.65} rig={a} expr="serious" eye={[10,0]}/>
 </AbsoluteFill>;
};
