// q024 · 흉기 든 아들 살해한 의대교수 · B2 (frame 0 = the knife and "1시간"). Grave tone: no comic beats, no wound,
// no body. The son's threat and the father's act are shown only as the court found them.
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {CourtBackground,type} from './CourtDynamic';
import {Who,Push,Cell,Rail,Paper,S,INK,PAPER,GOLD,RED,kf,gesture,ease,clamp01} from './Kit';
import {Watch} from './Q023';
import type {Line,Case} from './BStandard';

const KNIFE=<g stroke="#1E1712" strokeWidth={5} strokeLinejoin="round"><path d="M-9 12V-46H9V12Z" fill="#3B3533"/><path d="M-11 -46H13L10 -150Q4 -168 -9 -150Z" fill="#C9CED3"/><path d="M-4 -60V-140" fill="none" stroke="#E8ECEF" strokeWidth={4}/></g>;
const SON='snack' as const,DAD='prof' as const;

// ---- apartment at night: entrance door on the right, hallway light ----
const Home:React.FC<{door?:number;dark?:boolean}>=({door=0,dark=true})=><AbsoluteFill style={{background:dark?'#3B3A44':'#8C8578'}}><svg width={1080} height={1920} {...S}>
 <path d="M0 0H1080V1240H0Z" fill={dark?'#575566':'#CDBFA6'}/>
 <path d="M0 1240H1080V1920H0Z" fill={dark?'#4A4239':'#9C8366'}/>{[1340,1500,1720].map(y=><path key={y} d={`M0 ${y}H1080`} stroke={dark?'#3E372F':'#866F55'} strokeWidth={5}/>)}
 <path d="M0 1240H1080" strokeWidth={10}/>
 <path d="M690 380H1010V1240H690Z" fill="#1E1D24"/>
 <path d={`M690 380H${1010-300*door}V1240H690Z`} fill="#8A6A4E"/>
 {door<.5&&<circle cx={970-280*door} cy={820} r={14} fill={GOLD} strokeWidth={5}/>}
 <path d="M60 300H420V680H60Z" fill={dark?'#6E6C80':'#E6DCC5'} strokeWidth={7}/><path d="M60 490H420M240 300V680" strokeWidth={6}/>
 <path d="M500 0V110M430 110H570V150H430Z" fill="#EDEAD8" strokeWidth={6}/>
 <ellipse cx={500} cy={170} rx={120} ry={30} fill="#FFE9A8" stroke="none" opacity={.35}/>
</svg></AbsoluteFill>;

// ---- opener / loop: one performance. s<0 door opens and he steps in (loop line); s>=0 knife up (= video frame 0) ----
const OpenStage:React.FC<{s:number;text:boolean;zoom:number}>=({s,text,zoom})=>{
 const f=useCurrentFrame(),door=s<0?kf(s,[[-80,0],[-50,1]]):1,step=s<0?kf(s,[[-55,0],[-20,1]]):1,raise=s>=0?kf(s,[[0,.8],[4,1]]):kf(s,[[-14,0],[-1,.8]]);
 const back=s>=0?kf(s,[[0,0],[10,1]]):0,shake=s>=0&&s<5?(5-s)*3*(s%2?1:-1):0;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${zoom}) translate(${shake}px,0)`,transformOrigin:'55% 45%'}}>
  <Home door={door}/>
  <Who look={DAD} x={300-30*back} y={1620} s={1.45} expr={s<-20?'concern':'scared'} phase={.3} eye={[12,0]} pose={(r)=>{r.hands=[[-60-60*back,-200-150*back],[60+80*back,-220-160*back]];r.handProps=[{pose:'open'},{pose:'open'}];r.torso=-6*back;r.head=-4*back;}}/>
  <Who look={SON} x={1260-540*step} y={1700} s={1.62} expr="angry" talk={s>=0} phase={.6} eye={[-12,0]} pose={(r)=>{r.hands=[[-70,-150],[100+30*raise,-160-300*raise]];r.handProps=[{pose:'fist'},{pose:'grip',anchor:'wrist',side:'left',rot:180-170*raise,object:KNIFE}];r.torso=5*raise;r.head=2*Math.sin(f*.2);}}/>
 </AbsoluteFill>
 {text&&s>=0&&<div style={{...type,position:'absolute',left:40,top:130,width:1000,zIndex:21,transform:`scale(${s<6?1+.25*Math.exp(-s/2)*Math.cos(s):1})`}}>
  <div style={{fontSize:96}}>흉기 든 아들</div><div style={{fontSize:200,color:RED,lineHeight:1}}>1시간</div></div>}
 </AbsoluteFill>;
};
export const OpenShot:React.FC<{t:number;dur:number}>=({t})=><OpenStage s={t} text zoom={1+.08*(1-clamp01(t/4))}/>;
export const OpenCover:React.FC<{t:number;dur:number}>=()=><OpenStage s={20} text={false} zoom={1}/>;
export const LoopShot:React.FC<{t:number;dur:number}>=({t,dur})=><OpenStage s={t-dur} text={false} zoom={1+.08*ease(t/(dur-1))}/>;

// ---- struggle (no weapon contact shown), hard cut to the aftermath: shards on the floor, father alone ----
const Shards:React.FC=()=><svg width={1080} height={1920} style={{position:'absolute'}} {...S} strokeWidth={5}>{[[300,1560,0],[420,1600,40],[560,1570,-30],[640,1620,70],[360,1650,110]].map(([x,y,r],i)=><path key={i} d={`M${x} ${y}l40 -18l22 30l-48 16Z`} fill="#EDEFF2" transform={`rotate(${r} ${x} ${y})`}/>)}</svg>;
export const FightShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const cut=Math.round(dur*.55);
 if(t<cut){const p=Math.sin(t*.35)*28,sh=(t%4<2?1:-1)*4;
  return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${sh}px,0) scale(1.05)`,transformOrigin:'50% 45%'}}><Home/>
   <Who look={DAD} x={400+p} y={1700} s={1.5} expr="scared" phase={.2} eye={[12,0]} pose={(r)=>{r.hands=[[120,-330],[150,-260]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.torso=10;r.head=-6;}}/>
   <Who look={SON} x={720+p} y={1700} s={1.55} expr="angry" phase={.5} eye={[-12,0]} pose={(r)=>{r.hands=[[-140,-330],[-120,-250]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.torso=-10;r.head=5;}}/>
  </AbsoluteFill></AbsoluteFill>;}
 const u=t-cut,shake=kf(u,[[20,0],[26,1],[32,0]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={u} dur={dur-cut} amt={.05} origin="40% 45%"><Home/><Shards/>
  <Who look={DAD} x={420} y={1640} s={1.6} expr="shock" phase={.2} eye={[0,12]} pose={(r)=>{const d=kf(u,[[0,0],[14,1]]);r.hands=[[-70-40*d,-200-200*d],[70+40*d,-200-200*d]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=-8*d+3*shake;r.hip[1]+=30*d;r.torso=-8*d;}} ik={{knee:[[-.4,-1],[.4,-1]]}}/>
 </Push></AbsoluteFill>;
};
// ---- hook: the father, white coat, cold light ----
export const HookShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const look=kf(t,[[8,0],[20,1]]),cold=ease(t/dur);
 return <AbsoluteFill style={{background:'#2C3238',overflow:'hidden'}}><Push t={t} dur={dur} amt={.06} origin="50% 32%">
  <svg width={1080} height={1920} style={{position:'absolute'}}><rect width={1080} height={1920} fill="#3A424A"/><rect width={1080} height={1920} fill="#16304a" opacity={.45*cold}/></svg>
  <Who look={DAD} x={540} y={2010} s={2.45} expr="tired" phase={.6} eye={[10-10*look,4-4*look]} pose={(r)=>{const h=kf(t,[[14,0],[26,1],[44,1],[54,.2]]);r.head=4*(1-look)+.6*Math.sin(t*.2)-4*h;r.hands=[[-70,-118],[60-10*h,-118-330*h]];r.handProps=[{pose:'relaxed'},{pose:h>.4?'open':'relaxed'}];}}/>
 </Push><div style={{...type,position:'absolute',left:40,top:150,width:1000,fontSize:110,color:PAPER,zIndex:21,opacity:clamp01(t/4)}}>의대 교수</div></AbsoluteFill>;
};
// ---- grudge: mother's memorial frame; the son points at the father ----
export const GrudgeShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const g=Math.max(gesture(t-4,14),gesture(t-40,14)),turn=kf(t,[[20,0],[34,1]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><Home dark={false}/>
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform="translate(540 430)"><path d="M-110 -140H110V140H-110Z" fill="#2D2B33" strokeWidth={8}/><path d="M-85 -115H85V115H-85Z" fill="#C9C3B4" strokeWidth={5}/><circle cy={-20} r={42} fill="#A79F8E" stroke="none"/><path d="M-60 95Q0 20 60 95Z" fill="#A79F8E" stroke="none"/><path d="M-110 -140L-40 -140L-110 -70Z" fill={INK}/></g>
   {[-150,150].map(x=><g key={x} transform={`translate(${540+x} 610)`}><circle r={26} fill="#F7F4EA" strokeWidth={5}/><circle r={10} fill="#E9D98A" strokeWidth={4}/></g>)}</svg>
  <Who look={SON} x={760} y={1700} s={1.6} expr="angry" talk={t>4} phase={.4} eye={[-12,0]} pose={(r)=>{const j=g*45*Math.max(0,Math.sin(t*.45));r.hands=[[-78-180*g-j,-118-290*g+.4*j],[78,-118]];r.handProps=[{pose:g>.5?'point':'relaxed'},{pose:'fist'}];r.torso=4*g;r.head=-2*g+5*Math.sin(t*.3);}}/>
  <Who look={DAD} x={250} y={1690} s={1.4} expr="tired" phase={.1} eye={[12-24*turn,6]} pose={(r)=>{const w=kf(t,[[44,0],[56,1],[70,1],[80,0]]);r.head=-6*turn-3*w;r.torso=-4*turn;r.hands=[[-70,-118],[70-20*w,-118-360*w]];r.handProps=[{pose:'relaxed'},{pose:w>.4?'open':'relaxed'}];}}/>
 </Push></AbsoluteFill>;
};
// ---- night: pounding at the door, the hour runs out ----
export const NightShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const pound=Math.max(0,Math.sin(t*.55)),frac=clamp01(t/(dur-8));
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.04}><Home door={.15+.1*pound}/>
  <Who look={SON} x={620} y={1700} s={1.6} expr="angry" talk phase={.4} eye={[12,0]} pose={(r)=>{r.hands=[[-70,-150],[150+70*pound,-470+60*pound]];r.handProps=[{pose:'grip',anchor:'wrist',side:'right',rot:180,object:KNIFE},{pose:'fist'}];r.torso=8*pound;r.head=5*pound;}}/>
  <Watch x={250} y={420} s={1.2} sec={180*frac}/>
 </Push><div style={{...type,position:'absolute',left:60,top:620,width:380,fontSize:86,color:GOLD,zIndex:21}}>{Math.round(60*frac)}분</div></AbsoluteFill>;
};
// ---- court ----
export const ClaimShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const sh=Math.sin(t*.3),hand=kf(t,[[0,0],[10,1]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur}><CourtBackground/>
  <Who look={DAD} x={540} y={1640} s={1.6} expr="concern" talk={t>4&&t<dur-6} phase={.3} eye={[6*sh,-4]} pose={(r)=>{const a=Math.sin(t*.28),b=Math.sin(t*.28+2);r.head=9*sh*hand;r.torso=3*sh;r.hands=[[-90-40*a,-200-160*hand*Math.max(0,a)],[90+40*b,-200-160*hand*Math.max(0,b)]];r.handProps=[{pose:'open'},{pose:'open'}];}}/>
 </Push><Rail y={1420}/></AbsoluteFill>;
};
const Stamp:React.FC<{x:number;y:number;t:number;text:string}>=({x,y,t,text})=>{if(t<0)return null;const sp=Math.min(1,t/4);return <svg width={1080} height={1920} style={{position:'absolute'}}><g transform={`translate(${x} ${y}) rotate(-10) scale(${2-.6*sp})`} opacity={sp}><rect x={-120} y={-56} width={240} height={112} rx={14} fill="none" stroke={RED} strokeWidth={12}/><text y={30} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={80} fill={RED}>{text}</text></g></svg>;};
export const IntentShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const g=gesture(t-2,12),w=t>26?60*Math.sin((t-26)*.3):0;
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><CourtBackground/>
  <Who look="judge" x={330} y={1700} s={1.7} expr="serious" talk={t>4&&t<dur-6} phase={.6} eye={[12,-4]} pose={(r)=>{r.hands=[[-78,-118],[78+150*g,-118-300*g+w*g]];r.handProps=[{pose:'relaxed'},{pose:g>.5?'point':'relaxed'}];r.head=1.5*Math.sin(t*.22);}}/>
  <Paper x={770} y={620} w={460} h={280} lines={['살인의 고의']} size={74} rot={4}/>
  <Stamp x={820} y={720} t={t-16} text="인정"/>
 </Push><Rail y={1500}/></AbsoluteFill>;
};
const Scale3:React.FC<{t:number;left:string;right:string}>=({t,left,right})=>{
 const drop=kf(t,[[6,0],[14,1]]),tilt=-9*kf(t,[[14,0],[22,1]]),hit=t>=14?Math.exp(-(t-14)/6)*Math.sin((t-14)*.9)*5:0;
 return <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform="translate(700 560) scale(1.05)">
  <path d="M0 -40V430M-120 430H120L96 404H-96Z" fill="#C9AC63"/>
  <g transform={`rotate(${tilt+hit})`}><path d="M-230 -40H230" stroke="#B1924F" strokeWidth={18}/>
   {[-1,1].map(side=><g key={side} transform={`translate(${side*210} -40) rotate(${-(tilt+hit)})`}><path d="M0 0L-80 170M0 0L80 170" fill="none" strokeWidth={6}/><path d="M-100 170Q0 260 100 170Z" fill={side<0?'#9B745F':'#819B8B'}/>
    <g transform={`translate(0 ${side<0?130-220*(1-drop):130})`}><path d="M-125 -70H125V40H-125Z" fill={side<0?PAPER:'#E7DCC0'} strokeWidth={6}/><text y={-6} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={50} fill={INK} stroke="none">{side<0?left:right}</text></g></g>)}
  </g><circle cy={-40} r={18} fill={GOLD}/></g></svg>;
};
export const FearShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const nod=kf(t,[[30,0],[36,1],[42,0],[48,1],[54,0]]),fl=kf(t,[[18,0],[26,1],[50,1],[64,.4]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur}><CourtBackground/>
  <Who look="judge" x={260} y={1560} s={1.25} expr="serious" talk={t>4&&t<dur-6} phase={.2} eye={[10,-2]} pose={(r)=>{r.head=6*nod;r.hands=[[-78,-118],[78,-118]];}}/>
  <Scale3 t={t} left="순간적 공포" right="살인 고의"/>
  <Who look={DAD} x={850} y={1520} s={1.1} expr={t<18?'concern':'tired'} phase={1.1} eye={[-10,4]} pose={(r)=>{r.head=-5*fl;r.hip[1]+=10*fl;r.hands=[[-70-20*fl,-118-200*fl],[70+20*fl,-118-200*fl]];r.handProps=[{pose:'relaxed'},{pose:'relaxed'}];}}/>
 </Push><Rail y={1360}/></AbsoluteFill>;
};
// ---- answer 2: the daughter's letter; father in the cell lowers his head ----
export const LetterShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const slide=kf(t,[[2,0],[14,1]]),bow=kf(t,[[24,0],[40,1]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03}><Cell/>
  <Who look={DAD} x={540} y={1470} s={1.3} expr={t<24?'concern':'tired'} phase={.8} eye={[0,8+6*bow]} pose={(r)=>{const sob=bow*4*Math.sin(t*.9),c=Math.max(0,Math.sin((t-24)*.14))*bow;r.head=-10*bow+sob*.5;r.torso=-6*bow;r.hip[1]+=sob;r.hands=[[-70,-118],[50,-118-380*c]];r.handProps=[{pose:'relaxed'},{pose:c>.5?'open':'relaxed'}];}}/>
 </Push>
 <div style={{position:'absolute',left:0,top:0,width:1080,height:1920,transform:`translateY(${300*(1-slide)}px)`,opacity:slide}}><Paper x={540} y={1600} w={760} h={250} lines={['처벌을 원하지 않습니다']} size={60} rot={-2}/></div>
 </AbsoluteFill>;
};
// ---- opinion: father alone in the cell, hand to his eyes ----
export const OpinionShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const cyc=Math.max(0,Math.sin(t*.13)),sway=Math.sin(t*.09);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.05} origin="50% 40%"><Cell/>
  <Who look={DAD} x={540+20*sway} y={1700} s={1.5} expr="tired" phase={.8} eye={[0,10]} pose={(r)=>{r.head=-6-5*cyc;r.hands=[[-70,-118],[40+30*cyc,-118-380*cyc]];r.handProps=[{pose:'relaxed'},{pose:cyc>.5?'open':'relaxed'}];r.torso=-3*cyc;}}/>
 </Push></AbsoluteFill>;
};
const SHOTS:Record<string,React.FC<{t:number;dur:number}>>={open:OpenShot,fight:FightShot,hook:HookShot,grudge:GrudgeShot,night:NightShot,claim:ClaimShot,intent:IntentShot,fear:FearShot,answer2:LetterShot,opinion:OpinionShot,loop:LoopShot};
export const Q024Film:React.FC<{c:Case;u:Line;t:number}>=({u,t})=>{const Shot=SHOTS[u.mode];return Shot?<Shot t={t} dur={u.dur}/>:null;};
