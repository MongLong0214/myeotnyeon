// q025 · 거제 터널 171km 만취 사망 · B1 (frame 0 = the speedometer at 171 inside the tunnel). Serious: the victim
// is never shown; the death only as an altar with a photo silhouette. No comedy.
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {CourtBackground,type} from './CourtDynamic';
import {Who,Push,Cell,Rail,Burst,Paper,S,INK,PAPER,GOLD,RED,kf,gesture,clamp01} from './Kit';
import {Car,WHEEL,DRIVER,driverPose} from './Q023';
import type {Line,Case} from './BStandard';

const DEF='woman' as const;
// ---- tunnel: orange lamps streaming past ----
const Tunnel:React.FC<{dx:number}>=({dx})=><AbsoluteFill style={{background:'#2A2622'}}><svg width={1080} height={1920} {...S}>
 <path d="M0 0H1080V1500H0Z" fill="#3A342D"/><path d="M0 300Q540 120 1080 300V0H0Z" fill="#26211C"/>
 {[0,1,2,3,4].map(i=>{const x=((i*300-dx)%1500+1500)%1500-200;return <g key={i}><rect x={x} y={360} width={160} height={36} rx={18} fill="#FFB347" stroke="none"/><rect x={x-40} y={350} width={240} height={56} rx={28} fill="#FFB347" opacity={.25} stroke="none"/></g>;})}
 {[0,1,2,3].map(i=>{const x=((i*420-dx*1.6)%1680+1680)%1680-300;return <path key={i} d={`M${x} 1000H${x+260}`} stroke="#6A6157" strokeWidth={12}/>;})}
 <path d="M0 1500H1080V1920H0Z" fill="#45413C"/><path d="M0 1500H1080" strokeWidth={8}/>
 {[0,1,2,3].map(i=>{const x=((i*330-dx*1.3)%1320+1320)%1320-160;return <path key={i} d={`M${x} 1780H${x+150}`} stroke="#E8E2D0" strokeWidth={14}/>;})}
</svg></AbsoluteFill>;
const Speedo:React.FC<{x:number;y:number;s:number;v:number;limit?:boolean}>=({x,y,s,v})=>{const a=-120+240*Math.min(1,v/220);return <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform={`translate(${x} ${y}) scale(${s})`}>
 <circle r={150} fill="#16181C" strokeWidth={10}/>{Array.from({length:12}).map((_,i)=>{const b=(-120+240*i/11)*Math.PI/180;return <path key={i} d={`M${Math.sin(b)*118} ${-Math.cos(b)*118}L${Math.sin(b)*138} ${-Math.cos(b)*138}`} stroke={i>8?RED:PAPER} strokeWidth={8}/>;})}
 <path d={`M0 0L${Math.sin(a*Math.PI/180)*120} ${-Math.cos(a*Math.PI/180)*120}`} stroke={RED} strokeWidth={10}/><circle r={14} fill={RED} strokeWidth={4}/>
 <text y={80} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={64} fill={PAPER} stroke="none">{Math.round(v)}</text>
</g></svg>;};
// s = frames from frame 0. s<0: loop line (she grips the wheel and accelerates); s>=0: 171 and climbing past lamps.
const SpeedStage:React.FC<{s:number;text:boolean}>=({s,text})=>{
 const f=useCurrentFrame(),v=s<0?171+Math.max(-150,s*1.8):171,dx=s<0?f*Math.max(4,30+s*.3):f*30,shake=Math.sin(f*1.7)*(s<0?2+3*clamp01((s+60)/60):5);
 const grip=s<0?kf(s,[[-80,0],[-60,1]]):1;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(0,${shake}px)`}}><Tunnel dx={dx}/>
  <Car tilt={0} color="#2F3B4A" driver={<>{WHEEL(880,1030)}<Who look={DEF} x={DRIVER.x} y={DRIVER.y} s={DRIVER.s} expr="dizzy" phase={.4} eye={[10,4]} pose={driverPose(grip,Math.sin(f*.11))}/></>}/>
 </AbsoluteFill>
 <Speedo x={820} y={330} s={1.15} v={v}/>
 {text&&s>=0&&<div style={{...type,position:'absolute',left:40,top:150,width:640,fontSize:170,color:RED,zIndex:21,transform:`scale(${s<6?1+.22*Math.exp(-s/2):1})`}}>171km</div>}
 </AbsoluteFill>;
};
export const SpeedShot:React.FC<{t:number;dur:number}>=({t})=><SpeedStage s={t} text/>;
export const SpeedCover:React.FC<{t:number;dur:number}>=()=><SpeedStage s={10} text={false}/>;
export const LoopShot:React.FC<{t:number;dur:number}>=({t,dur})=><SpeedStage s={t-dur} text={false}/>;

// ---- impact: small car ahead appears, hit, burst; the driver jolts ----
export const HitShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const f=useCurrentFrame(),hit=10,d=t-hit,sh=d>=0&&d<10?(10-d)*3*(d%2?1:-1):0,stop=d>=0?Math.exp(-d/8):1,dx=f*30*(d<0?1:stop*.3);
 const ahead=kf(t,[[0,1300],[hit,640]]),shove=d>=0?Math.min(180,d*16):0;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${sh}px,${sh*.4}px) scale(${1.06})`,transformOrigin:'60% 60%'}}><Tunnel dx={dx}/>
  <Car tilt={d>=0?-2*Math.min(1,d/3):0} color="#2F3B4A" driver={<>{WHEEL(880,1030)}<Who look={DEF} x={DRIVER.x+(d>=0&&d<6?30:0)} y={DRIVER.y} s={DRIVER.s} expr={d>=2?'shock':'dizzy'} phase={.4} eye={[10,d>=2?-6:4]} pose={(r)=>{driverPose(1,d>=0?-1*Math.exp(-d/8):Math.sin(f*.11))(r);if(d>=10){r.head+=9*Math.sin((d-10)*.45);r.torso+=3*Math.sin((d-10)*.3);}}}/></>}/>
  {d>=4&&[0,1,2].map(i=>{const u=((d-4)*2+i*22)%66;return <svg key={i} width={1080} height={1920} style={{position:'absolute'}}><circle cx={980+i*30-u*.6} cy={1250-u*5} r={30+u*.9} fill="#D9D4CC" opacity={.55*(1-u/66)}/></svg>;})}
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform={`translate(${ahead+shove} 1560) scale(1.15) rotate(${d>=0?Math.min(14,d*1.5):0})`}><path d="M0 -260Q10 -330 90 -340H260Q330 -330 360 -260L380 -120V40H0Z" fill="#E7E1C9" strokeWidth={9}/><path d="M60 -250L100 -320H250L300 -250Z" fill="#5D6B7E" strokeWidth={7}/><circle cx={80} cy={50} r={60} fill="#23252B" strokeWidth={8}/><circle cx={300} cy={50} r={60} fill="#23252B" strokeWidth={8}/></g></svg>
  <Burst x={1040} y={1300} t={d} s={1.7}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- twist: judge close-up, then the settlement sheet slams in ----
export const TwistShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const cut=Math.round(dur*.45),lean=kf(t,[[0,0],[10,1]]);
 if(t<cut)return <AbsoluteFill style={{overflow:'hidden'}}><CourtBackground dark/><Push t={t} dur={cut} amt={.06} origin="50% 35%">
  <Who look="judge" x={540} y={2020} s={2.6} expr="serious" phase={.3} eye={[0,-2+4*lean]} pose={(r)=>{r.head=-4*lean+1.2*Math.sin(t*.3);r.torso=-3*lean;}}/>
 </Push></AbsoluteFill>;
 const u=t-cut,sl=kf(u,[[0,0],[5,1]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><CourtBackground dark/><Push t={u} dur={dur-cut} amt={.04}>
  <Who look="judge" x={330} y={1790} s={1.7} expr="serious" phase={.3} eye={[10,-6]} pose={(r)=>{const g=gesture(u-2,10),w=u>16?60*Math.sin((u-16)*.3):0;r.hands=[[-78,-118],[78+170*g,-118-330*g+w*g]];r.handProps=[{pose:'relaxed'},{pose:g>.5?'point':'relaxed'}];}}/>
 </Push>
 <div style={{position:'absolute',left:0,top:0,width:1080,height:1920,transform:`translate(${300*(1-sl)}px,0) rotate(${4*(1-sl)}deg)`}}><Paper x={760} y={680} w={420} h={320} lines={['합의서']} size={90} rot={5} stack={2}/></div>
 </AbsoluteFill>;
};
// ---- limit: speed-limit sign 70 vs the needle; she sways ----
export const LimitShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const sway=Math.sin(t*.16),blink=Math.floor(t/6)%2===0;
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.04}><Tunnel dx={t*30}/>
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform="translate(250 400)"><circle r={150} fill="#FFF" strokeWidth={10}/><circle r={124} fill="none" stroke={RED} strokeWidth={30}/><text y={42} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={120} fill={INK} stroke="none">70</text></g></svg>
  <Speedo x={810} y={400} s={1.05} v={171+(blink?2:0)}/>
  <Who look={DEF} x={540+30*sway} y={1660} s={1.6} expr="dizzy" phase={.5} eye={[12*Math.sin(t*.25),6]} pose={(r)=>{r.head=10*sway;r.torso=6*sway;const c=Math.max(0,Math.sin(t*.2));r.hands=[[-80,-118],[50,-118-330*c]];r.handProps=[{pose:'relaxed'},{pose:c>.5?'open':'relaxed'}];}}/>
 </Push></AbsoluteFill>;
};
// ---- father: altar with a photo silhouette and white flowers; an adult mourner bows ----
const Mum:React.FC<{x:number;y:number;s?:number}>=({x,y,s=1})=><g transform={`translate(${x} ${y}) scale(${s})`} {...S} strokeWidth={5}>{[0,60,120,180,240,300].map(a=><ellipse key={a} cx={Math.sin(a*Math.PI/180)*16} cy={-Math.cos(a*Math.PI/180)*16} rx={11} ry={18} transform={`rotate(${a} ${Math.sin(a*Math.PI/180)*16} ${-Math.cos(a*Math.PI/180)*16})`} fill="#F7F4EA"/>)}<circle r={10} fill="#E9D98A"/></g>;
export const FatherShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const f=useCurrentFrame(),bow=kf(t,[[6,0],[18,1],[30,1],[40,.1],[52,1],[dur,1]]);
 return <AbsoluteFill style={{background:'#E8E1D2',overflow:'hidden'}}><Push t={t} dur={dur} amt={.04} origin="50% 35%">
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1250H0Z" fill="#EDE7DA"/><path d="M0 1250H1080V1920H0Z" fill="#B9A887"/><path d="M0 1250H1080" strokeWidth={9}/>
   <g transform="translate(400 520)"><path d="M-170 -220H170V220H-170Z" fill="#2D2B33" strokeWidth={9}/><path d="M-140 -190H140V190H-140Z" fill="#C9C3B4" strokeWidth={5}/><circle cy={-40} r={64} fill="#A79F8E" stroke="none"/><path d="M-95 160Q0 30 95 160Z" fill="#A79F8E" stroke="none"/><path d="M-170 -220L-80 -220L-170 -130Z" fill={INK}/><path d="M170 -220L80 -220L170 -130Z" fill={INK}/></g>
   {[-300,-210,-120,120,210,300].map((x,i)=><Mum key={x} x={400+x} y={790+(i%2)*40} s={1.6}/>)}
   <path d="M190 900H610V960H190Z" fill="#8A6A4E" strokeWidth={7}/>
   {[340,460].map((x,i)=><g key={x}><path d={`M${x-14} 900V840H${x+14}V900Z`} fill="#F2F0E6" strokeWidth={5}/><path d={`M${x} 838Q${x-12+2*Math.sin(f*.5+i)} 815 ${x} ${796+3*Math.sin(f*.7+i)}Q${x+12} 815 ${x} 838Z`} fill="#FFC24A" strokeWidth={4}/></g>)}
  </svg>
  <Who look="suit" x={740} y={1480} s={1.12} expr="concern" phase={.4} eye={[-10,8]} pose={(r)=>{r.hip=[0,-170+30*bow];r.torso=-22*bow;r.head=-16*bow;r.hands=[[-40,-200],[40,-200]];r.handProps=[{pose:'relaxed'},{pose:'relaxed'}];}}/>
 </Push></AbsoluteFill>;
};
// ---- money: she slides an envelope across the table and bows ----
export const MoneyShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const push=kf(t,[[4,0],[20,1]]),bow=kf(t,[[22,0],[32,1],[42,.2],[52,1],[66,1],[76,.3]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><CourtBackground/>
  <Who look={DEF} x={390} y={1520} s={1.45} expr="concern" phase={.2} eye={[12,6]} pose={(r)=>{r.torso=-14*bow;r.head=-16*bow;r.hip[1]+=40*bow;r.hands=[[60+260*push,-330],[30+200*push,-300]];r.handProps=[{pose:'open'},{pose:'open'}];}}/>
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d="M-20 1060H1100V1120H-20Z" fill="#CFAB76"/><path d="M-20 1120H1100V1940H-20Z" fill="#80573F"/>
   <g transform={`translate(${520+330*push} 1020) rotate(-4)`}><path d="M-150 -70H150V60H-150Z" fill="#F4EBD3" strokeWidth={7}/><path d="M-150 -70L0 10L150 -70" fill="none" strokeWidth={6}/><text y={-8} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={44} fill={INK} stroke="none" dy={60}>1억 8000만</text></g></svg>
 </Push></AbsoluteFill>;
};
const Stamp:React.FC<{x:number;y:number;t:number;text:string}>=({x,y,t,text})=>{if(t<0)return null;const sp=Math.min(1,t/4);return <svg width={1080} height={1920} style={{position:'absolute'}}><g transform={`translate(${x} ${y}) rotate(-10) scale(${2-.6*sp})`} opacity={sp}><rect x={-130} y={-56} width={260} height={112} rx={14} fill="none" stroke={RED} strokeWidth={12}/><text y={30} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={76} fill={RED}>{text}</text></g></svg>;};
export const FirstShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const g=Math.max(gesture(t-4,14),gesture(t-30,12)),slam=kf(t,[[0,0],[4,1]]),w=t>18?60*Math.sin((t-18)*.3):0;
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur}><CourtBackground/>
  <Who look="judge" x={360} y={1720} s={1.75} expr="serious" talk={t>4&&t<dur-6} phase={.2} eye={[10,-2]} pose={(r)=>{r.hands=[[-78,-118],[78+160*g,-118-280*g+w*g]];r.handProps=[{pose:'relaxed'},{pose:g>.5?'point':'relaxed'}];r.head=1.5*Math.sin(t*.25);}}/>
  <Who look={DEF} x={830} y={1400} s={.95} expr="scared" phase={1.1} eye={[-10,0]} pose={(r)=>{const fl=kf(t,[[6,0],[12,1]]);r.hip[1]+=10*fl;r.hands=[[-60-20*fl,-118-130*fl],[60+20*fl,-118-130*fl]];r.handProps=[{pose:'open'},{pose:'open'}];}}/>
 </Push><Rail y={1460}/>
 <div style={{...type,position:'absolute',left:40,top:150,width:1000,zIndex:21,transform:`scale(${1+.2*(1-slam)})`}}><div style={{fontSize:90}}>1심</div><div style={{fontSize:180,color:GOLD,lineHeight:1}}>징역 3년</div></div>
 </AbsoluteFill>;
};
export const AppealShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const g=Math.max(gesture(t-2,12),gesture(t-44,12)),w=t>24?60*Math.sin((t-24)*.3):0;
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><CourtBackground/>
  <Who look="judge" x={330} y={1700} s={1.7} expr="serious" talk={t>4&&t<dur-6} phase={.6} eye={[12,-4]} pose={(r)=>{r.hands=[[-78,-118],[78+150*g,-118-300*g+w*g]];r.handProps=[{pose:'relaxed'},{pose:g>.5?'point':'relaxed'}];r.head=1.5*Math.sin(t*.22);}}/>
  <Paper x={770} y={620} w={460} h={300} lines={['합의서 (2)']} size={70} rot={4} stack={1}/>
  <Stamp x={800} y={730} t={t-16} text="처벌불원"/>
 </Push><Rail y={1500}/></AbsoluteFill>;
};
// ---- answer 2: bars 3y -> 2y6m below the caption band; she in the cell ----
export const HalfShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const grow=kf(t,[[4,0],[18,1]]),cut=kf(t,[[24,0],[38,1]]),turn=kf(t,[[30,0],[42,1]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><Cell/>
  <Who look={DEF} x={540} y={1470} s={1.25} expr={t<30?'concern':'tired'} phase={.8} eye={[-8*turn,8]} pose={(r)=>{const sh=Math.sin(t*.5)*10*(1-turn);r.hands=[[-180+sh,-330],[180+sh,-330]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.head=-5*turn+sh*.3;r.hip[1]+=4*turn;}}/>
 </Push>
 <svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
  <rect x={80} y={1420} width={900} height={330} rx={18} fill="#1E232B" opacity={.85} strokeWidth={6}/>
  <path d={`M330 1480H${330+600*grow}V1560H330Z`} fill="#8E97A3" strokeWidth={6}/>
  <path d={`M330 1620H${330+600*grow*(1-cut/6)}V1700H330Z`} fill={GOLD} strokeWidth={6}/>
  <g fill={PAPER} stroke="none" fontFamily="Quiet Sans" fontWeight={800} fontSize={46}><text x={105} y={1536}>1심 3년</text><text x={105} y={1676}>2심 2.5년</text></g>
 </svg></AbsoluteFill>;
};
export const OpinionShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const cyc=Math.max(0,Math.sin(t*.13)),sway=Math.sin(t*.09);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.05} origin="50% 40%"><Cell/>
  <Who look={DEF} x={540+20*sway} y={1700} s={1.5} expr="tired" phase={.8} eye={[0,10]} pose={(r)=>{r.head=-6-5*cyc;r.hands=[[-70,-118],[40+30*cyc,-118-380*cyc]];r.handProps=[{pose:'relaxed'},{pose:cyc>.5?'open':'relaxed'}];r.torso=-3*cyc;}}/>
 </Push></AbsoluteFill>;
};
const SHOTS:Record<string,React.FC<{t:number;dur:number}>>={speed:SpeedShot,hit:HitShot,twist:TwistShot,limit:LimitShot,father:FatherShot,money:MoneyShot,first:FirstShot,appeal:AppealShot,answer2:HalfShot,opinion:OpinionShot,loop:LoopShot};
export const Q025Film:React.FC<{c:Case;u:Line;t:number}>=({u,t})=>{const Shot=SHOTS[u.mode];return Shot?<Shot t={t} dur={u.dur}/>:null;};
