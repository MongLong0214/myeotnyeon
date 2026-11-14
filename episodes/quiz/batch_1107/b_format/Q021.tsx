// q021 · 신림역 흉기난동 · B2 (frame 0 = the demand number, big sentence first). Serious tone: no comedy around the death.
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {ArticulatedGuy,RigPose,Look} from './FightRig';
import {standing} from './FightScene';
import {CourtBackground,type} from './CourtDynamic';
import {Who,Push,Cell,Bars,Sweat,Rail,S,INK,PAPER,GOLD,RED,TEAL,kf,breathe,solve,gesture,ease,clamp01} from './Kit';
import type {Line,Case} from './BStandard';

const KNIFE=<g stroke="#1E1712" strokeWidth={5} strokeLinejoin="round"><path d="M-9 12V-46H9V12Z" fill="#3B3533"/><path d="M-11 -46H13L10 -150Q4 -168 -9 -150Z" fill="#C9CED3"/><path d="M-4 -60V-140" fill="none" stroke="#E8ECEF" strokeWidth={4}/></g>;

// ---- opener / loop: one continuous performance. s<0 = loop line (wind-up), s=0 = desk slam = video frame 0 ----
const PROS={x:540,y:1650,s:1.5};
const prosRig=(f:number,s:number):RigPose=>{
 const r=standing();
 r.hip=[0,-170+1.5*breathe(f)];r.torso=.4*breathe(f,1.3);
 const up=s<0?kf(s,[[-84,0],[-6,1]]):1,slam=s>=0?kf(s,[[0,0],[3,1]]):0,point=s>=0?kf(s,[[12,0],[22,1]]):0;
 let h:[number,number]=[80+150*up,-118-400*up];
 if(s>=0)h=[230-40*slam,-518+293*slam];
 const lean=s<0?up:1-.4*point;
 r.torso+=-4*lean;r.head=-3*lean+(s<0?2.5*Math.sin(s*.35)*up:2*point*Math.sin(s*.25));
 r.hands=[[-78-150*point,-118-300*point+1.4*breathe(f,.3)],h];
 r.handProps=[{pose:point>.5?'point':'relaxed'},{pose:'fist'}];
 return solve(r,{elbow:[[-1,.4],[1,.4]]});
};
const OpenStage:React.FC<{s:number;zoom:number;text:boolean}>=({s,zoom,text})=>{
 const f=useCurrentFrame(),shake=s>=0&&s<5?(5-s)*3*(s%2?1:-1):0;
 return <AbsoluteFill style={{overflow:'hidden'}}>
  <AbsoluteFill style={{transform:`scale(${zoom}) translate(${shake}px,0)`,transformOrigin:'50% 55%'}}>
   <CourtBackground/>
   <ArticulatedGuy look="suit" x={PROS.x} y={PROS.y} scale={PROS.s} rig={prosRig(f,s)} expr="angry" eye={[0,2]} label="원작 성인 카툰 검사"/>
   <Rail y={1330}/>
   <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform="translate(250 1320) rotate(-4)"><path d="M-150 -16H150V16H-150Z" fill={PAPER} strokeWidth={6}/><path d="M-120 -4H110M-120 6H60" stroke="#B4A58C" strokeWidth={5}/></g></svg>
  </AbsoluteFill>
  {text&&s>=0&&<div style={{...type,position:'absolute',left:40,top:120,width:1000,zIndex:21,transform:`scale(${s<6?1+.25*Math.exp(-s/2)*Math.cos(s):1})`}}>
   <div style={{fontSize:96,color:PAPER}}>검찰 구형</div>
   <div style={{fontSize:230,color:RED,letterSpacing:'-.02em',lineHeight:1}}>사형</div>
  </div>}
 </AbsoluteFill>;
};
export const OpenShot:React.FC<{t:number;dur:number}>=({t})=><OpenStage s={t} zoom={1+.08*(1-clamp01(t/4))} text/>;
export const OpenCover:React.FC<{t:number;dur:number}>=()=><OpenStage s={30} zoom={1} text={false}/>;
export const LoopShot:React.FC<{t:number;dur:number}>=({t,dur})=><OpenStage s={t-dur} zoom={1+.08*ease(t/(dur-1))} text={false}/>;

// ---- street: daytime alley. Attacker walks in with a kitchen knife held low; two adult men turn and run. No contact. ----
const Alley:React.FC=()=><AbsoluteFill style={{background:'#9D998C'}}><svg width={1080} height={1920} {...S}>
 <path d="M0 0H1080V1180H0Z" fill="#E3D8C2"/>
 {[[0,'#C98B5A'],[360,'#6E9AB0'],[720,'#B5C26E']].map(([x,c])=><g key={x as number}><path d={`M${x} 160H${(x as number)+360}V1180H${x}Z`} fill={(x as number)%720?'#D6CCB4':'#CFC3A8'}/><path d={`M${(x as number)+20} 420H${(x as number)+340}L${(x as number)+320} 520H${(x as number)+40}Z`} fill={c as string}/><path d={`M${(x as number)+50} 560H${(x as number)+310}V1060H${(x as number)+50}Z`} fill="#9FB5BE"/><path d={`M${(x as number)+180} 560V1060`} strokeWidth={6}/><path d={`M${(x as number)+60} 220H${(x as number)+300}V340H${(x as number)+60}Z`} fill="#EDE6D2" strokeWidth={6}/></g>)}
 <path d="M0 1180H1080V1920H0Z" fill="#9D998C"/><path d="M0 1180H1080" strokeWidth={10}/>
 {[1290,1450,1660].map(y=><path key={y} d={`M0 ${y}H1080`} stroke="#8B877A" strokeWidth={5}/>)}
</svg></AbsoluteFill>;
const walk=(r:RigPose,ph:number,amp=40)=>{const w=Math.sin(ph);r.feet=[[-30-amp*w,-14*Math.max(0,w)],[30+amp*w,-14*Math.max(0,-w)]];r.hip[1]+=-4*Math.abs(Math.cos(ph));};
export const StreetShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const notice=kf(t,[[8,0],[16,1]]),run=clamp01((t-16)/10);
 const flee=(x0:number,d:number,look:Look,ph:number)=>{const x=x0+run*(t-16)*7;return <Who key={look} look={look} x={x} y={1150} s={.8} expr={notice>.5?'scared':'normal'} phase={ph} eye={[-12,0]} pose={(r)=>{walk(r,t*(.35+.3*run)+ph,30+20*run);r.hands=[[-78-30*run,-118-60*run],[78+30*run,-118-60*run]];r.head=-6*notice;r.torso=10*run;}}/>;};
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.04}><Alley/>
  {flee(700,0,'passenger',.5)}{flee(900,1,'driver',2)}
  <Who look="attacker" x={300+t*1.6} y={1290} s={1.3} expr="serious" phase={.2} eye={[12,0]} pose={(r)=>{walk(r,t*.22,26);r.hands=[[-78,-118],[110,-160]];r.handProps=[{pose:'relaxed'},{pose:'grip',anchor:'wrist',side:'left',rot:200,object:KNIFE}];r.head=-2;}}/>
 </Push></AbsoluteFill>;
};
// ---- hook: his face; the light goes cold, eyes turn to camera ----
export const HookShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const look=kf(t,[[10,0],[22,1]]),cold=ease(t/dur);
 return <AbsoluteFill style={{background:'#2C3238',overflow:'hidden'}}><Push t={t} dur={dur} amt={.05} origin="50% 32%">
  <svg width={1080} height={1920} style={{position:'absolute'}}><rect width={1080} height={1920} fill="#3A424A"/><path d="M0 0H1080V600Q540 520 0 600Z" fill="#323940"/><rect width={1080} height={1920} fill="#16304a" opacity={.45*cold}/></svg>
  <Who look="attacker" x={540} y={2060} s={2.5} expr="serious" phase={.6} eye={[12-12*look,2-2*look]} pose={(r)=>{r.head=4*(1-look)+.5*Math.sin(t*.2);r.hands=[[-70,-118],[70,-118]];}}/>
 </Push></AbsoluteFill>;
};
// ---- memorial: flowers and notes at the spot; a man lays a white flower and bows ----
const Mum:React.FC<{x:number;y:number;s?:number}>=({x,y,s=1})=><g transform={`translate(${x} ${y}) scale(${s})`} {...S} strokeWidth={5}><path d="M0 0L-6 90" fill="none" stroke="#4E7A44" strokeWidth={8}/>{[0,60,120,180,240,300].map(a=><ellipse key={a} cx={Math.sin(a*Math.PI/180)*16} cy={-Math.cos(a*Math.PI/180)*16} rx={11} ry={18} transform={`rotate(${a} ${Math.sin(a*Math.PI/180)*16} ${-Math.cos(a*Math.PI/180)*16})`} fill="#F7F4EA"/>)}<circle r={10} fill="#E9D98A"/></g>;
export const MemorialShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const f=useCurrentFrame(),lay=kf(t,[[0,0],[22,1],[34,1],[50,0]]),bow=kf(t,[[44,0],[62,1],[dur,1]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03} origin="40% 55%"><Alley/>
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
   {[[70,560,'#F6E58D'],[220,520,'#A9DEF9'],[150,700,'#FFC6D9'],[330,660,'#F6E58D'],[480,560,'#C9F2C7'],[420,760,'#FFFFFF']].map(([x,y,c],i)=><g key={i} transform={`rotate(${(i%3-1)*5} ${x} ${y})`}><path d={`M${x} ${y}h120v120h-${120}Z`} fill={c as string} strokeWidth={5}/><path d={`M${(x as number)+18} ${(y as number)+44}h80M${(x as number)+18} ${(y as number)+72}h56`} stroke="#8E8A7E" strokeWidth={6}/></g>)}
   {[[70,1110],[160,1135],[250,1100],[340,1140],[430,1110],[110,1160],[300,1170],[200,1060],[390,1050]].map(([x,y],i)=><Mum key={i} x={x} y={y-70} s={1.9}/>)}
   {[60,500].map((x,i)=><g key={x}><path d={`M${x-18} 1175H${x+18}V1095H${x-18}Z`} fill="#F2F0E6" strokeWidth={5}/><path d={`M${x} 1092Q${x-15+2*Math.sin(f*.5+i)} 1064 ${x} ${1040+4*Math.sin(f*.7+i)}Q${x+15} 1064 ${x} 1092Z`} fill="#FFC24A" strokeWidth={4}/></g>)}
  </svg>
  <Who look="driver" x={640} y={1175} s={1.15} expr="concern" phase={.4} eye={[-10,10]} pose={(r)=>{r.hip=[-10*bow,-170+30*lay+4*bow];r.torso=-14*lay-16*bow;r.head=-10*lay-14*bow;r.hands=[[-78+(-140)*lay,-118+40*lay],[78,-118]];r.handProps=[{pose:lay>.2&&t<34?'grip':'relaxed',anchor:'wrist',rot:150,object:lay>.2&&t<34?<Mum x={0} y={-60} s={.8}/>:undefined},{pose:'relaxed'}];}} ik={{knee:[[-.4,-1],[.4,-1]]}}/>
 </Push></AbsoluteFill>;
};
// ---- strangers: ordinary passers-by keep crossing; nobody looks back ----
export const StrangersShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const P:[Look,number,number,number,number][]=[['passenger',-60,1250,1.05,0],['snack',330,1250,1.05,1.4],['driver',720,1250,1.05,2.5]];
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><Alley/>
  {P.map(([look,x0,y,s,ph])=>{const x=x0+t*3.4;return <Who key={look} look={look} x={x} y={y} s={s} expr="normal" phase={ph} eye={[10,0]} pose={(r)=>{walk(r,t*.3+ph,32);r.hands=[[-78-14*Math.sin(t*.3+ph),-118],[78+14*Math.sin(t*.3+ph),-118]];}}/>;})}
 </Push></AbsoluteFill>;
};
// ---- court ----
export const ClaimShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const hold=kf(t,[[0,0],[12,1]]),sw=Math.sin(t*.16);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur}><CourtBackground/>
  <Who look="inmate2" x={540} y={1700} s={1.65} expr="concern" talk={t>6&&t<dur-8} phase={.3} eye={[6*sw,-4]} pose={(r)=>{r.head=5*sw*hold;r.torso=2*sw*hold;const rub=6*Math.sin(t*.5)*hold;r.hands=[[-78-125*hold,-118-420*hold+rub],[78+125*hold,-118-420*hold-rub]];r.handProps=[{pose:hold>.5?'fist':'relaxed'},{pose:hold>.5?'fist':'relaxed'}];}}/>
 </Push><Rail y={1450}/></AbsoluteFill>;
};
const Scale2:React.FC<{t:number}>=({t})=>{
 const drop=kf(t,[[6,0],[14,1]]),hit=t>=14?Math.exp(-(t-14)/6)*Math.sin((t-14)*.9)*6:0;
 return <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform="translate(730 600) scale(1.1)">
  <path d="M0 -40V430M-120 430H120L96 404H-96Z" fill="#C9AC63"/>
  <g transform={`rotate(${hit})`}><path d="M-230 -40H230" stroke="#B1924F" strokeWidth={18}/>
   {[-1,1].map(side=><g key={side} transform={`translate(${side*210} -40)`}><path d="M0 0L-80 170M0 0L80 170" fill="none" strokeWidth={6}/><path d="M-100 170Q0 260 100 170Z" fill={side<0?'#9B745F':'#819B8B'}/></g>)}
   <g transform={`translate(-210 ${130-220*(1-drop)})`}><path d="M-80 -70H80V40H-80Z" fill={PAPER} strokeWidth={6}/><text y={-6} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={36} fill={INK} stroke="none">심신미약</text></g>
   <g transform="translate(210 130)"><path d="M-80 -70H80V40H-80Z" fill="#E7DCC0" strokeWidth={6}/><text y={-6} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={36} fill={INK} stroke="none">범행 내용</text></g>
  </g><circle cy={-40} r={18} fill={GOLD}/></g></svg>;
};
export const FirstShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const shake=kf(t,[[36,0],[42,1],[48,-1],[54,1],[60,0]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur}><CourtBackground/>
  <Who look="judge" x={215} y={1330} s={1.2} expr="serious" talk={t>40} phase={.2} eye={[10,-2]} pose={(r)=>{const g=gesture(t-36,14);r.head=6*shake;r.hands=[[-78,-118],[78+120*g,-118-200*g]];r.handProps=[{pose:'relaxed'},{pose:g>.5?'point':'relaxed'}];}}/>
  <Scale2 t={t}/>
 </Push><Rail y={1200}/></AbsoluteFill>;
};
export const CruelShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const g=gesture(t-2,14),fl=kf(t,[[8,0],[14,1],[30,1],[50,.6]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur}><CourtBackground/>
  <Who look="inmate2" x={850} y={1220} s={.95} expr={t<10?'serious':'scared'} phase={1.2} eye={[-10,2]} pose={(r)=>{r.hip[1]+=14*fl;r.head=-6*fl;r.hands=[[-60-20*fl,-118-120*fl],[60+20*fl,-118-120*fl]];r.handProps=[{pose:'open'},{pose:'open'}];}}/>
  <Who look="judge" x={330} y={1720} s={1.75} expr="angry" talk={t>4&&t<dur-6} phase={.4} eye={[10,0]} pose={(r)=>{r.hands=[[-78,-118],[78+160*g,-118-260*g]];r.handProps=[{pose:'relaxed'},{pose:g>.5?'point':'relaxed'}];r.torso=4*g;r.head=-3*g+1.5*Math.sin(t*.25);}}/>
 </Push><Rail y={1480}/></AbsoluteFill>;
};
// ---- answer 2: ankle monitor blinks ----
export const MonitorShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const look2=kf(t,[[48,0],[58,1],[72,1],[80,0]]),lift=kf(t,[[6,0],[18,1],[34,1],[46,0]]),down=kf(t,[[0,0],[14,1]]),blink=Math.floor(t/8)%2===0;
 return <AbsoluteFill style={{overflow:'hidden'}}><CourtBackground dark/><Push t={t} dur={dur} amt={.03} origin="50% 70%">
  <Who look="inmate2" x={540} y={1640} s={1.45} expr={t<30?'shock':'tired'} phase={.5} eye={[0,8+8*down]} pose={(r)=>{r.head=-8*down+6*look2;r.feet[1]=[40+20*lift+15*look2,-60*lift-40*look2];r.torso=-5*look2;r.hands=[[-78,-118],[78,-118]];}} ik={{knee:[[-.2,-1],[.5,-1]]}}/>
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform={`translate(${540+1.45*(40+20*lift+15*look2)} ${1640+1.45*(-60*lift-40*look2)-38})`}><path d="M-50 -32H50V32H-50Z" fill="#2E3338" strokeWidth={7}/><circle cx={26} cy={0} r={12} fill={blink?'#FF4A3D':'#5A2420'} strokeWidth={3}/></g></svg>
 </Push></AbsoluteFill>;
};
export const CellShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const rat=t>=6&&t<22?Math.sin(t*2.2)*6:0,turn=kf(t,[[26,0],[36,1]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><Cell/>
  <Who look="inmate2" x={540} y={1660} s={1.5} expr={t<26?'concern':'tired'} phase={.8} eye={[-10*turn,6]} pose={(r)=>{r.hands=[[-200+rat,-330],[200+rat,-330]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.head=rat*.4-5*turn;r.hip[1]+=4*turn;}}/>
  <Bars xs={[235,845]} dx={rat*.6}/>
 </Push></AbsoluteFill>;
};
const SHOTS:Record<string,React.FC<{t:number;dur:number}>>={open:OpenShot,street:StreetShot,hook:HookShot,memorial:MemorialShot,strangers:StrangersShot,claim:ClaimShot,first:FirstShot,cruel:CruelShot,answer2:MonitorShot,opinion:CellShot,loop:LoopShot};
export const Q021Film:React.FC<{c:Case;u:Line;t:number}>=({u,t})=>{const Shot=SHOTS[u.mode];return Shot?<Shot t={t} dur={u.dur}/>:null;};
