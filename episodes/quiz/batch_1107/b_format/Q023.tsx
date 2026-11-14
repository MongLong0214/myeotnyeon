// q023 · 압구정 롤스로이스 · B1 (frame 0 = the car on the kerb). Serious tone: the victim is never shown, the death only as a memorial.
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {RigPose} from './FightRig';
import {CourtBackground,type} from './CourtDynamic';
import {Who,Push,Cell,Bars,Sweat,Rail,Burst,Paper,S,INK,PAPER,GOLD,RED,kf,gesture} from './Kit';
import {MemorialShot} from './Q021';
import type {Line,Case} from './BStandard';

const PHONE=<g stroke="#1E1712" strokeWidth={5} strokeLinejoin="round"><rect x={-20} y={-80} width={40} height={74} rx={7} fill="#2B2F36"/><rect x={-13} y={-72} width={26} height={54} rx={3} fill="#7FC8E8"/></g>;
const walk=(r:RigPose,ph:number,amp=40)=>{const w=Math.sin(ph);r.feet=[[-30-amp*w,-14*Math.max(0,w)],[30+amp*w,-14*Math.max(0,-w)]];r.hip[1]+=-4*Math.abs(Math.cos(ph));};

// ---- night street: shop fronts, kerb at y 1500 ----
export const Street:React.FC<{dx?:number}>=({dx=0})=>{const o=((dx%360)+360)%360;return <AbsoluteFill style={{background:'#2B3140'}}><svg width={1080} height={1920} {...S}>
 <path d="M0 0H1080V1500H0Z" fill="#323A4C"/>
 {[-360,0,360,720,1080].map(x0=>{const x=x0-o;return <g key={x0}><path d={`M${x} 150H${x+360}V1500H${x}Z`} fill="#3D4659" strokeWidth={6}/><path d={`M${x+40} 380H${x+320}V900H${x+40}Z`} fill="#F2D48A" opacity={.85} strokeWidth={6}/><path d={`M${x+180} 380V900`} strokeWidth={6}/><path d={`M${x+30} 250H${x+330}V330H${x+30}Z`} fill="#5A6680" strokeWidth={6}/></g>;})}
 <path d="M0 1500H1080V1560H0Z" fill="#8D8A82"/><path d="M0 1560H1080V1920H0Z" fill="#3E4148"/><path d="M0 1500H1080M0 1560H1080" strokeWidth={8}/>
 {[0,1,2,3].map(i=>{const x=((i*300-o*1.2)%1200+1200)%1200-60;return <path key={i} d={`M${x} 1760H${x+140}`} stroke="#E8E2D0" strokeWidth={14}/>;})}
</svg></AbsoluteFill>;};
// ---- the car: side view, faces right, driver visible through the side window ----
const CAR_BODY='M-40 1250Q-40 1180 40 1150L230 1120L300 660Q320 600 380 600H880Q930 600 960 650L1060 1100Q1130 1110 1150 1180V1625H-40Z';
const WINDOW='M340 1150L380 680Q386 650 420 650H870Q900 650 912 680L1010 1150Z';
export const Car:React.FC<{tilt:number;driver:React.ReactNode;color?:string}>=({tilt,driver,color='#ECEAE4'})=><AbsoluteFill style={{transform:`rotate(${tilt}deg)`,transformOrigin:'90% 95%'}}>
 <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d={WINDOW} fill="#5D6B7E"/></svg>
 {driver}
 <svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
  <path d={`${CAR_BODY} ${WINDOW}`} fillRule="evenodd" fill={color} strokeWidth={10}/>
  <path d="M100 1290H1080" stroke="#C9C6BE" strokeWidth={10}/><path d="M560 1180V1450M820 1180V1450" strokeWidth={6}/>
  <path d="M700 1200H780" strokeWidth={14}/>
  {[200,1010].map(x=><g key={x}><circle cx={x} cy={1520} r={130} fill="#23252B" strokeWidth={10}/><circle cx={x} cy={1520} r={62} fill="#B8BCC4" strokeWidth={8}/></g>)}
 </svg>
</AbsoluteFill>;
export const DRIVER={x:620,y:1590,s:1.35};
export const driverPose=(grip:number,sway:number)=>(r:RigPose)=>{r.hands=[[150+50*grip,-390+40*grip],[200+50*grip,-430+40*grip]];r.handProps=[{pose:grip>.5?'fist':'relaxed'},{pose:grip>.5?'fist':'relaxed'}];r.head=6*sway;r.torso=3*sway;};
export const WHEEL=(x:number,y:number)=><svg width={1080} height={1920} style={{position:'absolute'}} {...S}><ellipse cx={x} cy={y} rx={34} ry={92} fill="none" stroke="#2A2C31" strokeWidth={22}/><ellipse cx={x} cy={y} rx={34} ry={92} fill="none" strokeWidth={5}/></svg>;
// s = frames from impact. s<0: rolling toward the kerb (loop line); s>=0 impact (video frame 0) and after.
const CrashStage:React.FC<{s:number;text:boolean}>=({s,text})=>{
 const f=useCurrentFrame(),roll=s<0?-s*9:0,hit=s>=1?Math.exp(-(s-1)/6):0,shake=s>=1&&s<9?(9-s)*3*(s%2?1:-1):0;
 const tilt=s>=0?-3*kf(s,[[0,0],[3,1]]):0,sway=Math.sin(f*.11);
 const grip=s<0?kf(s,[[-60,0],[-40,1]]):1;
 return <AbsoluteFill style={{overflow:'hidden'}}>
  <AbsoluteFill style={{transform:`translate(${shake}px,${shake*.4}px) scale(${1+.06*hit})`,transformOrigin:'80% 60%'}}>
   <Street dx={roll*1.0+f*(s<0?0:0)}/>
   <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform={`translate(1000 ${1500}) rotate(${s>=0?kf(s,[[0,0],[5,-38]]):0})`}><path d="M-40 0H40L30 -200H-30Z" fill="#E0B23A" strokeWidth={7}/><path d="M-30 -140H30M-34 -70H34" stroke="#1E1712" strokeWidth={14}/></g></svg>
   <Car tilt={tilt} driver={<>{WHEEL(880,1030)}<Who look="rich" x={DRIVER.x} y={DRIVER.y} s={DRIVER.s} expr={s>=2?'shock':'dizzy'} phase={.4} eye={[10,s>=0?-4:6]} pose={driverPose(grip,s>=1?-1*hit:sway)}/></>}/>
   <Burst x={1010} y={1350} t={s} s={1.6}/>
  </AbsoluteFill>
  {text&&s>=0&&s<46&&<div style={{...type,position:'absolute',left:40,top:150,width:1000,fontSize:150,color:RED,zIndex:21,transform:`scale(${s<6?1+.22*Math.exp(-s/2):1})`}}>쾅!</div>}
 </AbsoluteFill>;
};
export const CrashShot:React.FC<{t:number;dur:number}>=({t})=><CrashStage s={t} text/>;
export const CrashCover:React.FC<{t:number;dur:number}>=()=><CrashStage s={12} text={false}/>;
export const LoopShot:React.FC<{t:number;dur:number}>=({t,dur})=><CrashStage s={t-dur} text={false}/>;

// ---- death: memorial only (shared memorial staging from q021), night tint ----
export const DiedShot:React.FC<{t:number;dur:number}>=({t,dur})=><AbsoluteFill><MemorialShot t={t} dur={dur}/><AbsoluteFill style={{background:'#1B2A4A',opacity:.32,mixBlendMode:'multiply'}}/></AbsoluteFill>;

// ---- twist: judge close-up, then the "3분" stopwatch slams in ----
export const Watch:React.FC<{x:number;y:number;s:number;sec:number}>=({x,y,s,sec})=>{const a=sec/180*360;return <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform={`translate(${x} ${y}) scale(${s})`}>
 <path d="M-22 -150H22V-118H-22Z" fill="#C9CED3" strokeWidth={7}/><circle r={120} fill={PAPER} strokeWidth={10}/><circle r={120} fill="none" stroke={RED} strokeWidth={18} strokeDasharray={`${2*Math.PI*104*sec/180} 999`} transform="rotate(-90) scale(.865)"/>
 <path d={`M0 0L${Math.sin(a*Math.PI/180)*88} ${-Math.cos(a*Math.PI/180)*88}`} strokeWidth={10}/><circle r={10} fill={INK}/>
</g></svg>;};
export const TwistShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const cut=Math.round(dur*.42),lean=kf(t,[[0,0],[10,1]]);
 if(t<cut)return <AbsoluteFill style={{overflow:'hidden'}}><CourtBackground dark/><Push t={t} dur={cut} amt={.06} origin="50% 35%">
  <Who look="judge" x={540} y={2020} s={2.6} expr="serious" phase={.3} eye={[0,-2+4*lean]} pose={(r)=>{r.head=-4*lean+1.2*Math.sin(t*.3);r.torso=-3*lean;}}/>
 </Push></AbsoluteFill>;
 const u=t-cut,sec=Math.min(180,u*9);
 return <AbsoluteFill style={{overflow:'hidden'}}><CourtBackground dark/><Push t={u} dur={dur-cut} amt={.04}>
  <Who look="judge" x={360} y={1790} s={1.7} expr="serious" talk={false} phase={.3} eye={[10,-6]} pose={(r)=>{const g=gesture(u-2,10);r.hands=[[-78,-118],[78+170*g,-118-330*g]];r.handProps=[{pose:'relaxed'},{pose:g>.5?'point':'relaxed'}];}}/>
  <Watch x={770} y={720} s={1.5*(u<4?1+.2*(4-u)/4:1)} sec={sec}/>
 </Push>
 <div style={{...type,position:'absolute',left:480,top:180,width:580,fontSize:170,color:GOLD,zIndex:21}}>3분</div></AbsoluteFill>;
};
// ---- leave: walks off along the pavement, turns, walks back; the car on the kerb behind ----
export const LeaveShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const half=dur*.5,back=t>=half,u=back?t-half:t,x=back?160+u*7.5:780-u*7.5,sec=Math.min(180,t/(dur-6)*180);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><Street dx={0}/>
  <AbsoluteFill style={{transform:'translate(560px,592px) scale(.55)',transformOrigin:'0 0'}}><Car tilt={-3} driver={null}/></AbsoluteFill>
  <Who look="rich" x={x} y={1580} s={1.45} expr={back?'concern':'dizzy'} phase={.2} eye={[back?12:-12,2]} pose={(r)=>{walk(r,t*.3,30);r.hands=[[-78-12*Math.sin(t*.3),-118],[78+12*Math.sin(t*.3),-118]];r.head=3*Math.sin(t*.13);}}/>
  <Watch x={880} y={330} s={.9} sec={sec}/>
 </Push></AbsoluteFill>;
};
// ---- court: 1st instance 20 years ----
export const FirstShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const g=Math.max(gesture(t-4,14),gesture(t-46,14)),slam=kf(t,[[0,0],[4,1]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur}><CourtBackground/>
  <Who look="judge" x={360} y={1720} s={1.75} expr="angry" talk={t>6&&t<dur-6} phase={.2} eye={[10,-2]} pose={(r)=>{const w=t>22?70*Math.sin((t-22)*.3):0;r.hands=[[-78,-118],[78+160*g,-118-280*g+w*g]];r.handProps=[{pose:'relaxed'},{pose:g>.5?'point':'relaxed'}];r.head=-3*g+1.5*Math.sin(t*.25);}}/>
  <Who look="suit" x={880} y={1380} s={.95} expr="serious" phase={1.1} eye={[-10,0]} pose={(r)=>{const n=kf(t,[[40,0],[48,1],[56,0],[64,1],[72,0]]);r.head=8*n;r.hands=[[-70,-118],[70,-118]];}}/>
 </Push><Rail y={1460}/>
 <div style={{...type,position:'absolute',left:40,top:150,width:1000,zIndex:21,transform:`scale(${1+.2*(1-slam)})`}}><div style={{fontSize:90}}>1심</div><div style={{fontSize:180,color:GOLD,lineHeight:1}}>징역 20년</div></div>
 </AbsoluteFill>;
};
// ---- appeal: the "도주치사" sheet gets struck through and stamped 무죄 ----
export const AcquitShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const g=Math.max(gesture(t-2,12),gesture(t-40,12)),strike=kf(t,[[10,0],[22,1]]),stamp=t>=26,sp=stamp?Math.min(1,(t-26)/4):0;
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><CourtBackground/>
  <Who look="judge" x={330} y={1700} s={1.7} expr="serious" talk={t>4&&t<dur-6} phase={.6} eye={[12,-4]} pose={(r)=>{const w=t>30?70*Math.sin((t-30)*.3):0;r.hands=[[-78,-118],[78+150*g,-118-300*g+w*g]];r.handProps=[{pose:'relaxed'},{pose:g>.5?'point':'relaxed'}];r.head=1.5*Math.sin(t*.22)+(t>44?5*Math.sin((t-44)*.5)*Math.exp(-(t-44)/20):0);}}/>
  <Paper x={760} y={640} w={440} h={300} lines={['도주치사']} size={84} rot={4}/>
  <svg width={1080} height={1920} style={{position:'absolute'}}><g transform="translate(760 640) rotate(4)"><path d={`M-190 -40L${-190+380*strike} ${-40+10*strike}`} stroke={RED} strokeWidth={16} strokeLinecap="round"/>
   {stamp&&<g transform={`translate(60 80) rotate(-12) scale(${2-.6*sp})`} opacity={sp}><rect x={-120} y={-56} width={240} height={112} rx={14} fill="none" stroke={RED} strokeWidth={12}/><text y={30} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={80} fill={RED}>무죄</text></g>}</g></svg>
 </Push><Rail y={1500}/></AbsoluteFill>;
};
// ---- phone: dazed, pats pockets, finds the phone ----
export const PhoneShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const pat=t<dur*.55,find=kf(t,[[dur*.55,0],[dur*.55+10,1]]),sway=Math.sin(t*.12);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.04} origin="50% 35%"><Street dx={120}/>
  <Who look="rich" x={540+30*sway} y={1900} s={2.3} expr={pat?'dizzy':'concern'} phase={.5} eye={[pat?14*Math.sin(t*.25):0,14*find]} pose={(r)=>{const p=Math.abs(Math.sin(t*.45));r.torso=8*sway;r.head=10*Math.sin(t*.25);
   if(pat){r.hands=[[-100-25*p,-130-90*p],[100+25*(1-p),-130-90*(1-p)]];r.handProps=[{pose:'open'},{pose:'open'}];}
   else{r.hands=[[-78,-118],[50,-118-150*find]];r.handProps=[{pose:'relaxed'},{pose:'grip',anchor:'wrist',side:'left',rot:0,object:PHONE}];}}} ik={{elbow:[[-.3,1],[.3,1]]}}/>
 </Push></AbsoluteFill>;
};
// ---- still guilty of dangerous driving causing death ----
export const GuiltyShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const g=gesture(t-2,12),stamp=t>=14,sp=stamp?Math.min(1,(t-14)/4):0,fl=kf(t,[[16,0],[22,1],[40,1],[56,.5]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><CourtBackground/>
  <Paper x={300} y={560} w={500} h={260} lines={['위험운전치사']} size={66} rot={-3}/>
  <svg width={1080} height={1920} style={{position:'absolute'}}>{stamp&&<g transform={`translate(330 640) rotate(-10) scale(${2-.6*sp})`} opacity={sp}><rect x={-120} y={-56} width={240} height={112} rx={14} fill="none" stroke={RED} strokeWidth={12}/><text y={30} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={80} fill={RED}>유죄</text></g>}</svg>
  <Who look="rich" x={760} y={1640} s={1.75} expr={t<16?'concern':'scared'} phase={1.2} eye={[-10,-2]} pose={(r)=>{r.hip[1]+=14*fl;r.head=-6*fl+4*g*0;const sh=t>22?7*Math.sin(t*1.7):0;r.hands=[[-70-20*fl+sh,-118-140*fl],[70+20*fl-sh,-118-140*fl]];r.handProps=[{pose:'open'},{pose:'open'}];r.head+=sh*.4;}}/>
  {t>=22&&<Sweat x={880} y={760} t={t-22} s={1.2}/>}
 </Push><Rail y={1520}/></AbsoluteFill>;
};
// ---- answer 2: half of the first sentence; bars 20 -> 10 below the caption band ----
export const HalfShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const grow=kf(t,[[4,0],[18,1]]),cut=kf(t,[[24,0],[38,1]]),turn=kf(t,[[30,0],[42,1]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><Cell/>
  <Who look="rich" x={540} y={1560} s={1.25} expr={t<30?'concern':'tired'} phase={.8} eye={[-8*turn,8]} pose={(r)=>{r.hands=[[-180,-330],[180,-330]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.head=-5*turn;r.hip[1]+=4*turn;}}/>
  <Bars xs={[260,820]}/>
 </Push>
 <svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
  <rect x={80} y={1420} width={900} height={330} rx={18} fill="#1E232B" opacity={.85} strokeWidth={6}/>
  <path d={`M300 1480H${300+600*grow}V1560H300Z`} fill="#8E97A3" strokeWidth={6}/>
  <path d={`M300 1620H${300+300*cut}V1700H300Z`} fill={GOLD} strokeWidth={6}/>
  <g fill={PAPER} stroke="none" fontFamily="Quiet Sans" fontWeight={800} fontSize={50}><text x={110} y={1538}>1심 20</text><text x={110} y={1678}>확정 10</text></g>
 </svg></AbsoluteFill>;
};
// ---- opinion: in the cell, rattles the bars, looks down ----
export const OpinionShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const rat=t>=4&&t<34?Math.sin(t*1.6)*13:0,turn=kf(t,[[24,0],[34,1]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><Cell/>
  <Who look="rich" x={540} y={1700} s={1.5} expr={t<24?'concern':'tired'} phase={.8} eye={[-10*turn,6]} pose={(r)=>{r.hands=[[-200+rat,-330],[200+rat,-330]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.head=rat*.4-5*turn;r.hip[1]+=4*turn;}}/>
  <Bars xs={[235,845]} dx={rat*.6}/>
 </Push></AbsoluteFill>;
};
const SHOTS:Record<string,React.FC<{t:number;dur:number}>>={crash:CrashShot,died:DiedShot,twist:TwistShot,leave:LeaveShot,first:FirstShot,acquit:AcquitShot,phone:PhoneShot,guilty:GuiltyShot,answer2:HalfShot,opinion:OpinionShot,loop:LoopShot};
export const Q023Film:React.FC<{c:Case;u:Line;t:number}>=({u,t})=>{const Shot=SHOTS[u.mode];return Shot?<Shot t={t} dur={u.dur}/>:null;};
