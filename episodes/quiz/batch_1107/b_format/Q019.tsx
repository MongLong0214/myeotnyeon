// q019 · 계엄령 놀이 · B1 (opens on the action). Shots follow complete narration lines (case.json utterances).
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {ArticulatedGuy,RigPose,Expr,Look} from './FightRig';
import {standing} from './FightScene';
import {CourtBackground,type} from './CourtDynamic';
import {Who,Push,Snap,RestRoom,Dawn,Cell,Bars,Blanket,Burst,Sweat,Paper,Rail,S,INK,PAPER,GOLD,RED,TEAL,kf,kp,breathe,solve,gesture,ease,clamp01} from './Kit';
import type {Line,Case} from './BStandard';

// ---- stomp: frame 0 is the contact. The loop shot ends on the raised foot that lands at frame 0. ----
const STOMP={x:330,y:1340,s:1.5};
const stompRig=(f:number,foot:[number,number],lean:number,arms:number):RigPose=>{
 const r=standing();
 r.hip=[8*lean,-170+1.5*breathe(f)];r.torso=-7*lean;r.head=-4*lean+.6*breathe(f,.7);
 r.feet=[[-42,0],foot];
 r.hands=[[-150-25*arms,-300-40*arms],[140+20*arms,-330-40*arms]];
 r.handProps=[{pose:'fist'},{pose:'fist'}];
 return solve(r,{knee:[[-.2,-1],[.35,-1]],elbow:[[-1,.2],[1,.2]]});
};
const ON:[number,number]=[150,-115],UP:[number,number]=[160,-250];
const Stomper:React.FC<{foot:[number,number];lean:number;arms:number;expr:Expr;talk?:boolean}>=({foot,lean,arms,expr,talk=false})=>{
 const f=useCurrentFrame();
 return <ArticulatedGuy look="official" x={STOMP.x} y={STOMP.y} scale={STOMP.s} rig={stompRig(f,foot,lean,arms)} expr={expr} talk={talk} eye={[9,4]} label="실존 인물과 무관한 원작 성인 카툰 · 재연"/>;
};
const LumpAt=(squash:number)=><Blanket x={700} y={1405} s={1.0} squash={squash}/>;
export const StompShot:React.FC<{t:number;dur:number}>=({t})=>{
 // contact t=0 and t=27; lift between; grind after
 const lift=kf(t,[[0,0],[5,0],[16,1],[22,1.05],[27,0],[60,0]]);
 const foot:[number,number]=[ON[0]+(UP[0]-ON[0])*lift,ON[1]+(UP[1]-ON[1])*lift];
 const sq=t<6?kf(t,[[0,1],[6,0]]):t>=27&&t<33?kf(t-27,[[0,1],[6,0]]):0;
 const shake=(t>=27&&t<31?(31-t)*2.5:0)*(t%2?1:-1);
 return <AbsoluteFill style={{overflow:'hidden'}}><Snap t={t} amt={.08} origin="52% 55%"><AbsoluteFill style={{transform:`translate(${shake}px,0)`}}>
  <RestRoom/>
  {LumpAt(sq)}
  <Stomper foot={foot} lean={kf(t,[[0,1],[14,.3],[27,1],[40,.6]])} arms={kf(t,[[0,1],[14,.4],[27,1],[45,.5]])} expr={t<36?'angry':'smug'}/>
  <Burst x={STOMP.x+ON[0]*STOMP.s+20} y={STOMP.y+ON[1]*STOMP.s-5} t={t}/>
  <Burst x={STOMP.x+ON[0]*STOMP.s+20} y={STOMP.y+ON[1]*STOMP.s-5} t={t-27} s={.85}/>
 </AbsoluteFill></Snap></AbsoluteFill>;
};
export const LoopShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 // the foot climbs the whole line and peaks on the last frame; frame 0 of the video is its landing
 const p=ease(t/(dur-1));
 const lift=p*1.0;
 const foot:[number,number]=[ON[0]+(UP[0]-ON[0])*lift,ON[1]-2+(UP[1]-ON[1])*lift];
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.03} origin="52% 55%"><RestRoom/>{LumpAt(0)}
  <Stomper foot={kp(t,[[0,[46,-2]],[Math.round(dur*.35),[78,-60]],[dur-1,UP]])} lean={kf(t,[[0,0],[dur-1,1]])} arms={kf(t,[[0,.2],[dur-1,1]])} expr={t<dur*.55?'smug':'angry'} talk={false}/>
 </Push></AbsoluteFill>;
};

// ---- 계엄령 놀이: new angle, wide; he proclaims, two workers freeze, the lump on the floor ----
export const MartialShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const g=gesture(t-2,16);
 return <AbsoluteFill><Push t={t} dur={dur}><RestRoom alt/>
  <Blanket x={560} y={1720} s={.85}/>
  <Who look="sweeper2" x={735} y={1190} s={1.02} expr="scared" phase={1.1} eye={[-12,2]} pose={(r,f)=>{r.hands=[[-55,-160],[55,-160]];r.hip[1]+=1.5*Math.sin(f*.9);}}/>
  <Who look="sweeper3" x={950} y={1190} s={1.02} expr="concern" phase={2.3} eye={[-12,2]} pose={(r)=>{r.hands=[[-50,-165],[60,-160]];}}/>
  <Who look="official" x={290} y={1200} s={1.25} expr={t<dur*.6?'angry':'smug'} talk={t<dur-8} phase={.4} eye={[8,0]} pose={(r)=>{r.hands=[[-80-90*g,-160-280*g],[80+95*g,-160-285*g]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=-5*g+3*Math.sin(t*.2)*g;r.torso=-3*g;}}/>
 </Push></AbsoluteFill>;
};

// ---- question at 4–6 s: his close-up; bar shadows slide across and the smirk drops ----
export const HookShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const bars=ease((t-14)/16),shock=t>=26;
 return <AbsoluteFill style={{background:'#3D454C',overflow:'hidden'}}><Push t={t} dur={dur} amt={.035} origin="50% 35%">
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d="M0 0H1080V1920H0Z" fill="#4A535B" stroke="none"/><path d="M0 1500H1080" stroke="#3A4148" strokeWidth={12}/></svg>
  <Who look="official" x={540} y={2040} s={2.55} expr={shock?'shock':'smug'} eye={shock?[-10,-4]:[2,2]} phase={.9} pose={(r)=>{r.head=shock?-4:3+2*Math.sin(t*.15);r.hands=[[-70,-120],[70,-120]];}}/>
  {shock&&<Sweat x={760} y={330} t={t-26} s={1.4}/>}
 </Push>
  <svg width={1080} height={1920} style={{position:'absolute',opacity:.42*bars}}>{[0,1,2,3,4,5].map(i=><rect key={i} x={1080-bars*1200+i*190} y={0} width={70} height={1920} fill="#000"/>)}</svg>
 </AbsoluteFill>;
};

// ---- three workers at dawn; they flinch on 폭행 ----
export const VictimsShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const fist=kf(t,[[0,0],[30,0],[38,1],[52,1],[60,.85],[dur,.8]]),hit=t>=38&&t<46;
 const flinch=(d:number)=>(r:RigPose)=>{const b=kf(t-d,[[36,0],[42,1],[54,.8],[80,.55]]);r.hands=[[-78-12*b,-118-200*b],[78+12*b,-118-200*b]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=-6*b;r.hip[1]+=12*b;};
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur}><Dawn/>
  <Who look="sweeper" x={330} y={1185} s={1.2} expr={t<38?'concern':'scared'} phase={.2} eye={[-12,1]} pose={flinch(0)}/>
  <Who look="sweeper2" x={630} y={1170} s={1.12} expr={t<40?'concern':'scared'} phase={1.6} eye={[-12,1]} pose={flinch(3)}/>
  <Who look="sweeper3" x={905} y={1185} s={1.15} expr={t<42?'serious':'scared'} phase={2.9} eye={[-12,1]} pose={flinch(6)}/>

 </Push></AbsoluteFill>;
};

const BOWERS:{x:number;look:Look;d:number}[]=[{x:250,look:'sweeper',d:0},{x:830,look:'sweeper2',d:5}];
// ---- 교주: he stands on a crate, towel draped like a robe, rays behind; two workers forced to bow (foreground, below the captions) ----
export const CultShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const g=gesture(t-3,18),spin=t*.6;
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} origin="50% 30%"><RestRoom/>
  <svg width={1080} height={1920} style={{position:'absolute'}}><g transform={`translate(540 520) rotate(${spin})`}>{Array.from({length:12}).map((_,i)=><path key={i} d="M0 0L-70 -900L70 -900Z" transform={`rotate(${i*30})`} fill={i%2?'#F3D77A':'#EBC75A'} opacity={.55}/>)}</g></svg>
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d="M380 1000H700V1180H380Z" fill="#3E7CB0"/><path d="M400 1030H680M400 1080H680M400 1130H680" stroke="#2F5F88" strokeWidth={8}/>
   <path d="M405 480Q540 430 675 480L700 960Q540 990 380 960Z" fill="#F2EFE6" strokeWidth={8}/><path d="M430 540L420 930M650 540L660 930" stroke="#D9D4C6" strokeWidth={10}/></svg>
  <Who look="official" x={540} y={1000} s={1.3} expr="smug" talk={t>10&&t<dur-10} phase={.5} eye={[0,-3]} pose={(r)=>{r.hands=[[-80-120*g,-160-300*g],[80+120*g,-160-300*g]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=-6*g*Math.sin(t*.12);}}/>
  {BOWERS.map(({x,look,d})=><Who key={x} look={look} x={x} y={2060} s={1.0} expr="concern" phase={x/300} eye={[0,10]} pose={(r)=>{const b=kf(t-d,[[0,.2],[18,1],[dur,1]]);r.torso=-10*b;r.head=-14*b;r.hip=[-8*b,-170+20*b];r.hands=[[-60,-200],[60,-200]];}}/>)}
 </Push></AbsoluteFill>;
};

// ---- court ----
export const DemandShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const up=gesture(t,14);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur}><CourtBackground/>
  <Who look="suit" x={330} y={1700} s={1.8} expr="serious" talk={t<dur-6} phase={.3} eye={[9,0]} pose={(r)=>{r.hands=[[-70,-150],[169,-444+70*(1-up)]];r.handProps=[{pose:'relaxed'},{pose:'fist'}];}}/>
  <Paper x={800} y={700+126*(1-up)} w={330} h={400} lines={['검찰 구형','징역 5년']} size={66} rot={0} color={INK}/>
 </Push><Rail y={1560}/></AbsoluteFill>;
};
export const RemorseShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const n=t<8?1:t<16?2:3,pet=t>=34,beg=kf(t,[[0,0],[10,1],[30,1],[36,.6],[44,1]]);
 const drop=(at:number)=>-60*(1-ease((t-at)/5));
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur}><CourtBackground/>
  <Who look="judge" x={265} y={1240} s={1.3} expr="serious" phase={.2} eye={[10,7]} pose={(r)=>{r.hands=[[-60,-260],[70,-255]];r.handProps=[{pose:'relaxed'},{pose:'relaxed'}];r.head=4*Math.sin(t*.08);}}/>
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d="M-20 1010H660V1260H-20Z" fill="#80573F"/><path d="M-20 985H660V1020H-20Z" fill="#C5A06F"/></svg>
  <Paper x={300} y={905+drop(n===1?0:n===2?8:16)} w={270} h={210} lines={['반성문']} size={56} rot={-5} stack={n-1}/>
  {pet&&<Paper x={500} y={915+drop(34)} w={260} h={200} lines={['탄원서']} size={56} rot={6} stack={2}/>}
  <Who look="inmate" x={850} y={1330} s={1.35} expr="concern" phase={1.4} eye={[-12,4]} pose={(r)=>{r.hands=[[-42-6*beg,-250-55*beg],[42+6*beg,-250-55*beg]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=-3*beg+2*Math.sin(t*.5)*beg;r.torso=-6*beg;}} ik={{elbow:[[-1,.9],[1,.9]]}}/>
 </Push></AbsoluteFill>;
};
export const PleaShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const nod=kf(t,[[10,0],[22,1],[34,0]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur}><CourtBackground/>
  <Who look="sweeper2" x={200} y={1170} s={1.0} expr="serious" phase={.6} eye={[10,2]}/>
  <Who look="sweeper3" x={880} y={1170} s={1.0} expr="serious" phase={2.1} eye={[-10,2]}/>
  <Who look="sweeper" x={540} y={1520} s={1.5} expr={t<20?'concern':'serious'} talk={t>=14&&t<dur-12} phase={1.2} eye={[0,2]} pose={(r)=>{const c=kf(t,[[24,0],[36,1],[dur,1]]);r.head=-5*nod;r.hands=[[-78+48*c,-118-150*c],[78,-118]];r.handProps=[{pose:c>.5?'fist':'relaxed'},{pose:'relaxed'}];}}/>
 </Push><Rail y={1400}/></AbsoluteFill>;
};

// ---- after the answer: in the cell ----
export const CellShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const sigh=kf(t,[[8,0],[24,1],[44,.6],[60,1]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><Push t={t} dur={dur} amt={.02}><Cell/>
  <Who look="inmate" x={540} y={1660} s={1.5} expr={t<30?'tired':'concern'} phase={.8} eye={[0,8]} pose={(r)=>{const rat=t>=40&&t<58?Math.sin(t*2.2)*6:0;r.hands=[[-200+rat,-330],[200+rat,-330]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.head=-4*sigh+rat*.4;r.hip[1]+=6*sigh;}}/>
  <Bars xs={[235,845]} dx={t>=40&&t<58?Math.sin(t*2.2)*4:0}/>
 </Push></AbsoluteFill>;
};
export const SlumpShot:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const b=kf(t,[[0,0],[14,1],[40,1],[dur,.85]]);
 return <AbsoluteFill style={{overflow:'hidden'}}><CourtBackground dark/><Push t={t} dur={dur} amt={.03}>
  <Who look="inmate" x={540} y={1690} s={1.6} expr={t<18?'shock':'tired'} phase={.4} eye={[0,6]} pose={(r)=>{const h=kf(t,[[34,0],[46,1],[dur,1]]);r.head=-6*b+3*h*Math.sin(t*.3);r.hip[1]+=10*b;r.torso=2*b;r.hands=[[-78-60*h,-120-330*h],[78+60*h,-120-330*h]];r.handProps=[{pose:h>.5?'open':'relaxed'},{pose:h>.5?'open':'relaxed'}];}}/>
  {t<18&&<Sweat x={790} y={600} t={t} s={1.3}/>}
 </Push></AbsoluteFill>;
};

const SHOTS:Record<string,React.FC<{t:number;dur:number}>>={stomp:StompShot,martial:MartialShot,hook:HookShot,victims:VictimsShot,cult:CultShot,demand:DemandShot,remorse:RemorseShot,plea:PleaShot,answer2:SlumpShot,opinion:CellShot,loop:LoopShot};
export const Q019Film:React.FC<{c:Case;u:Line;t:number}>=({u,t})=>{
 const Shot=SHOTS[u.mode];
 return Shot?<Shot t={t} dur={u.dur}/>:null;
};
