import {Hand} from '../../../../production/lf_toon/src/Hand';
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {ArticulatedGuy,Expr,Look,RigPose} from './FightRig';
import {standing} from './FightScene';
import {CourtBackground,INK,PAPER,GOLD} from './CourtDynamic';
import type {Case,Line} from './Scenes';

const S={stroke:INK,strokeWidth:9,strokeLinecap:'round' as const,strokeLinejoin:'round' as const};
const clamp=(u:number)=>Math.max(0,Math.min(1,u));
const cubic=(u:number)=>{u=clamp(u);return u<.5?4*u*u*u:1-Math.pow(-2*u+2,3)/2;};
const quart=(u:number)=>{u=clamp(u);return u<.5?8*u*u*u*u:1-Math.pow(-2*u+2,4)/2;};
// 4f anticipation (-15%), 18f main action, 10f damped follow-through.
// m=1,k=100,c=10 => zeta=.5; an analytic response is evaluated directly per frame.
export const gesture=(t:number,main=18)=>{
 if(t<0)return 0;
 if(t<4)return -.15*cubic(t/4);
 if(t<4+main)return -.15+1.15*cubic((t-4)/main);
 if(t<14+main){const s=(t-4-main)/30;return 1+.12*Math.exp(-5*s)*Math.sin(Math.sqrt(75)*s);}
 return 1;
};
const breathe=(f:number,phase=0)=>Math.sin(2*Math.PI*f/120+phase);
const motionRig=(f:number,t:number,kind:'bench'|'reaction'|'point'|'paper',phase:number,scale:number)=>{
 const r=standing(),g=gesture(t),s=gesture(t-5);
 r.hands=[[-75,-222],[75,-220]];r.elbows=[[-105,-278],[105,-290]];
 r.hip[1]+=2*breathe(f,phase);r.torso=.22*breathe(f,phase+Math.PI/2);r.head=.24*breathe(f,phase+.7);
 if(kind==='bench'){
  r.hands[1]=[75+150*g,-220-80*g];r.hands[0]=[-75+54*s,-222-86*s];r.elbows[1]=[150,-320];r.head+=5*gesture(t-4);r.torso+=3*g;
 }else if(kind==='reaction'){
  r.hands[1]=[105-80*g,-230-60*g];r.hands[0]=[-75+36*s,-222-48*s];r.elbows[1]=[125,-275];r.head+=6*gesture(t-4);r.torso+=4*g;
 }else if(kind==='point'){
  r.hands[1]=[75+100*g,-222-70*g];r.hands[0]=[-75+56*s,-222-46*s];r.elbows[1]=[115,-325];r.head-=4*gesture(t-4);r.torso+=2*g;
 }else{
  r.hands[1]=[182.5,-220-90*s];r.hands[0]=[-55,-260];r.elbows[1]=[110,-315];r.head+=6*gesture(t-4);
 }
 // Independent sin/cos channels do not clamp or restart at the end of a hero move.
 r.hands[0][0]+=1.6*breathe(f,phase+.3);r.hands[0][1]+=1.6*breathe(f,phase+1.9);
 r.hands[1][0]+=1.6*breathe(f,phase+2.7);r.hands[1][1]+=1.6*breathe(f,phase+4.2);
 r.handProps=[{pose:kind==='paper'?'pinch':'relaxed'},{pose:kind==='point'||kind==='bench'?'point':kind==='paper'?'pinch':'relaxed'}];
 return r;
};
const Person:React.FC<{look:Look;x:number;y:number;scale:number;t:number;kind:'bench'|'reaction'|'point'|'paper';expr?:Expr;phase?:number;recordOcclusion?:boolean}>=({look,x,y,scale,t,kind,expr='serious',phase=0,recordOcclusion=false})=>{
 const f=useCurrentFrame(),r=motionRig(f,t,kind,phase,scale);
 // q004 card covers this wrist once it passes x=680. Suppress the whole hand
 // so the paper edge cannot leave an ink-only crescent. Forearm stays behind.
 if(recordOcclusion&&x+scale*r.hands[1][0]>=680)r.hideHands=[false,true];
 return <ArticulatedGuy look={look} x={x} y={y} scale={scale} rig={r} expr={expr} eye={[look==='judge'?8:-9,1.2*breathe(f,phase+.8)]} talk={look==='judge'&&kind!=='paper'} label="실존 인물과 무관한 원작 성인 캐릭터"/>;
};
const Push:React.FC<{t:number;dur:number;children:React.ReactNode}>=({t,dur,children})=><AbsoluteFill style={{transform:`scale(${1+.02*quart(t/Math.max(1,dur-1))})`,transformOrigin:'50% 50%'}}>{children}</AbsoluteFill>;
const LowRoom:React.FC=()=> <AbsoluteFill style={{background:'#D7CCB3'}}><svg width={1080} height={1920} {...S}>
 <path d="M0 0H1080V1920H0Z" fill="#D7CCB3"/>{[100,540,980].map(x=><g key={x}><path d={`M${x-40} 0L${x-75} 1130H${x+75}L${x+40} 0Z`} fill="#EEE2C8" strokeWidth={6}/></g>)}
 <path d="M190 300H730V1060H190Z" fill="#77634E"/><path d="M225 330H695V1010H225Z" fill="#9D876A"/>
 </svg></AbsoluteFill>;
const Bench:React.FC=()=> <svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
 <path d="M-50 1075L1140 1030V1920H-50Z" fill="#80573F"/><path d="M-50 1038L1140 990V1060L-50 1110Z" fill="#C5A06F"/>
 {[130,430,730,1030].map(x=><path key={x} d={`M${x} 1160v650`} stroke="#684630" strokeWidth={15}/>)}
 </svg>;
const FirstRecord:React.FC=()=> <svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
 <g transform="translate(680 760)"><path d="M0 0H320V365H0Z" fill={PAPER}/><path d="M20 26H300V343H20Z" fill="none" strokeWidth={4}/>
 <g fill={INK} stroke="none" fontFamily="Quiet Sans" fontWeight={800} textAnchor="middle"><text x={160} y={95} fontSize={74}>1심</text><text x={160} y={200} fontSize={74}>벌금</text><text x={160} y={305} fontSize={82}>5만 원</text></g></g>
 </svg>;
const Scale:React.FC<{t:number}>=({t})=>{
 const f=useCurrentFrame(),g=gesture(t-5),angle=5*Math.sin(Math.PI*g)+.45*breathe(f,1.2);
 return <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform="translate(655 1020) scale(.52)"><path d="M0 -150V190M-110 190H110L85 167H-85Z" fill="#C9AC63"/><g transform={`rotate(${angle})`}><path d="M-240 -125H240" stroke="#B1924F" strokeWidth={20}/>{[-1,1].map(side=><g key={side} transform={`translate(${side*218} -125)`}><path d="M0 0L-80 165M0 0L80 165" fill="none" strokeWidth={6}/><path d="M-98 165Q0 270 98 165Z" fill={side<0?'#9B745F':'#819B8B'}/><rect x={-24} y={113} width={48} height={52} rx={3} fill="#BAA16E" strokeWidth={5}/></g>)}</g><circle cy={-125} r={19} fill={GOLD}/></g></svg>;
};
const Shoulder:React.FC<{look:Look;t:number}>=({look,t})=>{
 const f=useCurrentFrame(),a=2*breathe(f,2.1),b=1.7*breathe(f,3.7),color=look==='snack'?'#7973A1':'#C9503E';
 return <svg width={1080} height={1920} style={{position:'absolute',transform:`translateX(${82*gesture(t-5)}px)`}} {...S}><path d={`M1090 ${778+a}Q925 ${806+a} 855 ${988+b}L734 1410Q820 1540 1090 1570Z`} fill={color}/><path d={`M1090 ${830+a}Q962 ${878+b} 923 ${1080+b}L844 1350`} fill="none" stroke={look==='snack'?'#5E597F':'#A43E2F'} strokeWidth={26}/><path d="M1040 843L1080 846V915Z" fill="#DDD4BD" strokeWidth={6}/></svg>;
};
const WitnessInsert:React.FC<{u:Line;t:number}>=({u,t})=>{
 const f=useCurrentFrame(),g=gesture(t-10,14),dy=120*(1-g);
 return <AbsoluteFill><CourtBackground/><Push t={t} dur={u.dur}><Person look="judge" x={200} y={1200} scale={.8} t={t-10} kind="paper" phase={.4}/><svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
 <path d="M0 1120L1080 1060V1920H0Z" fill="#80573F"/><path d="M0 1090L1080 1030V1100L0 1160Z" fill="#C5A06F"/>
 </svg></Push>
 <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform={`translate(350 ${310+dy})`}>
 <path d="M0 0H650V765H0Z" fill={PAPER}/><path d="M22 22H628V743H22Z" fill="none" strokeWidth={4}/>
 <text x={325} y={145} fill={INK} stroke="none" textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={98}>동료 진술</text>
 {[265,345,425,505].map((y,i)=><path key={y} d={`M74 ${y}H${i%2?525:575}`} fill="none" stroke="#9D9B8A" strokeWidth={13}/>)}
 <path d="M430 646Q470 605 494 647T559 636" fill="none" stroke={INK} strokeWidth={7}/>
 </g></svg>
 </AbsoluteFill>;
};
export const CourtFix1:React.FC<{c:Case;u:Line;t:number;playback?:React.ReactNode}>=({c,u,t,playback})=>{
 const snack=c.qid==='q004',look:Look=snack?'snack':'D';
 if(u.mode==='evidence')return <WitnessInsert u={u} t={t}/>;
 if(u.mode==='first'||u.mode==='harm')return <AbsoluteFill><Push t={t} dur={u.dur}><LowRoom/><Person look="judge" x={425} y={1320} scale={1.18} t={t} kind="bench" phase={.1} recordOcclusion={snack}/><Bench/></Push>{snack?<FirstRecord/>:<>
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d="M688 560H1038V1140H688Z" fill="#394B51"/><path d="M795 1140V1173H935V1140" fill="#394B51"/></svg>
  <div style={{position:'absolute',left:703,top:575,width:320,height:550,overflow:'hidden'}}><div style={{width:1080,height:1920,transform:'scale(.296296)',transformOrigin:'0 0'}}>{playback}</div></div>
 </>}</AbsoluteFill>;
 if(u.mode==='claim'||u.mode==='recovery')return <AbsoluteFill><Push t={t} dur={u.dur}><CourtBackground/><Person look={look} x={535} y={1640} scale={1.95} t={t} kind="reaction" phase={1.7} expr={t<21?'serious':'concern'}/><svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d="M0 1385H1080V1920H0Z" fill="#80573F"/><path d="M0 1385H1080V1415H0Z" fill="#C5A06F"/></svg></Push></AbsoluteFill>;
 return <AbsoluteFill><Push t={t} dur={u.dur}><CourtBackground/><Person look="judge" x={365} y={1240} scale={1.12} t={t} kind="point" phase={.7}/><svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d="M0 1125H875V1390H0Z" fill="#80573F"/><path d="M0 1125H875V1160H0Z" fill="#C5A06F"/></svg><Scale t={t}/></Push><Shoulder look={look} t={t}/></AbsoluteFill>;
};

// Only the background judge changes in the last 27f of the approved choice hold.
// The cards/text/timing and all answer frames remain untouched. Contact is one
// frame before the pre-existing AAC impact; no audio sample is moved or remixed.
export const ChoiceGavel:React.FC<{c:Case}>=({c})=>{
 const f=useCurrentFrame(),impact=c.answer_frame-1,d=f-(impact-26),a=clamp((d-4)/22),r=standing();
 const p=d<4?-.15*cubic(d/4):-.15+1.15*a*a*a;
 r.hands=[[-85,-210],[155-90*p,-570+79*p]];r.elbows=[[-90,-262],[120,-370]];r.head=.24*breathe(f,.6)+3*p;
 r.hip[1]+=1.5*breathe(f,.2);r.hands[0][1]+=1.5*breathe(f,1.8);const angle=-20+165*p,x=300,y=630,s=.7,h=r.hands[1];r.handProps=[{pose:"relaxed"},{pose:"grip",anchor:"wrist",side:"left",rot:angle,object:<g stroke="#1E1712" strokeWidth={6} strokeLinejoin="round"><path d="M-8 10V-103H8V10Z" fill="#A17442"/><rect x={-61} y={-135} width={122} height={45} rx={6} fill="#AD7944"/><path d="M-44 -135V-90M44 -135V-90" fill="none" stroke="#D1AE78" strokeWidth={5}/></g>}];
 return <><ArticulatedGuy look="judge" x={x} y={y} scale={s} rig={r} expr="serious" eye={[8,.7*breathe(f,2.1)]}/><svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
 <path d="M95 409H540V478H95Z" fill="#80573F"/><path d="M95 400H540V420H95Z" fill="#C5A06F"/><ellipse cx={390} cy={400} rx={50} ry={12} fill="#5D3A30" strokeWidth={5}/>

 </svg></>;
};
