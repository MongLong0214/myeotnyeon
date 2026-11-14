// B3 template: reusable scenes driven by the spec. Every line is split into its spec 'shots' (prop / reaction / angle
// changes every ~1.5 s), every shot has a moving camera, number pops and the 7-8 s subscribe gag are overlays.
// The loop line replays the first shot of L01 with negative time so the last frames converge on frame 0.
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {CourtBackground,type} from './CourtDynamic';
import {Who,Cell,Bars,Burst,Paper,Sweat,S,INK,PAPER,GOLD,RED,TEAL,kf,ease,clamp01} from './Kit';
import type {Look,Expr} from './FightRig';
import type {Line,Case} from './BStandard';
import {Actor,talkTrack} from './look/BActing';
import {Stage,CAM0,type LightKey} from './look/BLook';
// opt-in look layer (spec "look":"full"): every B3 character becomes a lit, sprung Actor and every shot sits in a Stage
type LookC={on:boolean;light:LightKey;track?:{from:number;v:any[]}};
const LookCtx=React.createContext<LookC>({on:false,light:'court'});
type WhoP=React.ComponentProps<typeof Who>;
const P3:React.FC<WhoP>=(o)=>{const L=React.useContext(LookCtx);if(!L.on)return <Who {...o}/>;
 const base=(r:any,f:number)=>{r.hands=[[-78,-118],[78,-118]];o.pose?.(r,f);};
 return <Actor look={o.look} x={o.x} y={o.y} s={o.s} expr={o.expr} eye={o.eye} ik={o.ik} pose={base} light={L.light} seed={Math.round((o.phase??0)*7)} weight={4} talk={o.talk?L.track:undefined} springs={{props:null}}/>;};
const LIGHT_OF:Record<string,LightKey>={kettle:'homeNight',phonecall:'courtDark',fire:'street',helmets:'courtDark',taxi:'nightStreet',deal:'street',kick:'nightStreet',motel:'homeNight',trip:'nightStreet',river:'nightStreet',cell:'cell',tv:'cell',judge:'courtDark',prosecutor:'court',react:'street',memorial:'street',cctv:'nightStreet'};
import {MemorialShot} from './Q021';
import {Car,WHEEL,DRIVER,driverPose,Street,Watch} from './Q023';

export type Shot={s:string;[k:string]:unknown};
type P={t:number;dur:number;p:Shot;i:number};
const W=1080,H=1920;
// camera: always moving (zoom + drift), direction varies with shot index
const Cam:React.FC<{t:number;dur:number;i:number;children:React.ReactNode;origin?:string}>=({t,dur,i,children,origin='50% 42%'})=>{
 const u=clamp01(t/Math.max(1,dur)),dir=[1,-1,1,-1][i%4],z=1.04+.07*ease(u),dx=dir*30*(u-.5),dy=(i%3-1)*16*(u-.5),r=dir*.6*(u-.5);
 return <AbsoluteFill style={{transform:`translate(${dx}px,${dy}px) scale(${z}) rotate(${r}deg)`,transformOrigin:origin}}>{children}</AbsoluteFill>;
};
const Bg:React.FC<{c:string;c2?:string}>=({c,c2})=><AbsoluteFill style={{background:c2?`radial-gradient(circle at 50% 40%, ${c2} 0, ${c} 70%)`:c}}/>;
const Rays:React.FC<{color:string;t:number}>=({color,t})=><svg width={W} height={H} style={{position:'absolute'}}><g transform={`translate(540 760) rotate(${t*.8})`}>{Array.from({length:14}).map((_,k)=><path key={k} d="M0 0L-90 -1500L90 -1500Z" fill={color} opacity={.18} transform={`rotate(${k*360/14})`}/>)}</g></svg>;

// ---- cafe: the deal. s = frames from the hook frame (negative during the loop line) ----
const Cafe:React.FC=()=><AbsoluteFill style={{background:'#C9B79A'}}><svg width={W} height={H} {...S}>
 <path d="M0 0H1080V1180H0Z" fill="#E4D5BA"/><path d="M80 260H520V760H80Z" fill="#A9CBD6" strokeWidth={8}/><path d="M300 260V760M80 510H520" strokeWidth={6}/>
 <path d="M640 300H1000V560H640Z" fill="#7A5A44" strokeWidth={7}/><path d="M670 330H970V530H670Z" fill="#F0E6D2" strokeWidth={5}/>
 <path d="M0 1180H1080V1920H0Z" fill="#B49A78"/><path d="M0 1180H1080" strokeWidth={9}/>
</svg></AbsoluteFill>;
const ENV=(x:number,y:number,r:number)=><g transform={`translate(${x} ${y}) rotate(${r})`} {...S} strokeWidth={6}><path d="M-80 -50H80V50H-80Z" fill="#F4EBD3"/><path d="M-80 -50L0 10L80 -50" fill="none"/><path d="M-30 20H30" stroke="#5E8C5A" strokeWidth={10}/></g>;
export const DealStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),e=clamp01((s+40)/80),ex=820-480*e,ey=1010-90*Math.sin(Math.PI*e),talk=Math.sin(f*.5);
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${1.06+.02*Math.sin(f*.05)}) translate(${8*Math.sin(f*.04)}px,0)`,transformOrigin:'50% 45%'}}><Cafe/>
  <P3 look="granny" x={290} y={1620} s={1.45} expr="smug" talk phase={.3} eye={[12,2]} pose={(r)=>{r.hands=[[90,-330+20*talk],[150+60*e,-300]];r.handProps=[{pose:'point'},{pose:'open'}];r.head=3*talk;}}/>
  <P3 look="passenger" x={820} y={1640} s={1.42} expr="normal" phase={.7} eye={[-12,2]} pose={(r)=>{r.hands=[[-130-60*(1-e),-300],[60,-160]];r.handProps=[{pose:'open'},{pose:'relaxed'}];r.head=-2;}}/>
  <svg width={W} height={H} style={{position:'absolute'}}><path d="M40 1240H1040V1300H40Z" fill="#8A6A4E" stroke={INK} strokeWidth={8}/>{ENV(ex,ey,-10+20*e)}</svg>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- props ----
const Poster:React.FC<P>=({t,dur,i})=><AbsoluteFill><Bg c="#2D2A3A" c2="#4E4470"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <g transform={`translate(540 760) rotate(${-3+2*Math.sin(t*.1)})`}><path d="M-330 -470H330V470H-330Z" fill="#F6D7E4" strokeWidth={10}/>
  {[[-250,-380],[230,-330],[-210,300],[250,250],[0,-420]].map(([x,y],k)=><path key={k} d="M0 -34L10 -10L36 -10L15 6L23 32L0 16L-23 32L-15 6L-36 -10L-10 -10Z" fill={GOLD} strokeWidth={5} transform={`translate(${x} ${y}) scale(${1+.2*Math.sin(t*.3+k)})`}/>)}
  <rect x={-50} y={-230} width={100} height={170} rx={50} fill="#5A5D66" strokeWidth={8}/><path d="M-80 -110Q-80 0 0 0Q80 0 80 -110M0 0V120M-70 120H70" fill="none" strokeWidth={10}/>
  <text y={270} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={110} fill={INK} stroke="none">가수 딸</text></g>
</svg></Cam><div style={{...type,fontFamily:'Quiet Sans',position:'absolute',left:60,top:1400,width:960,fontSize:44,color:PAPER,WebkitTextStroke:`5px ${INK}`}}>※ 가수 본인은 이 사건과 무관</div></AbsoluteFill>;
const Cake:React.FC<P>=({t,dur,i})=>{const f=useCurrentFrame();return <AbsoluteFill><Bg c="#3B2F3A" c2="#6A4E5C"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <path d="M240 900H840V1150H240Z" fill="#F3E3C8" strokeWidth={9}/><path d="M240 900Q300 960 360 900Q420 960 480 900Q540 960 600 900Q660 960 720 900Q780 960 840 900" fill="#F7B6C8" strokeWidth={7}/><path d="M200 1150H880V1190H200Z" fill="#CFC2AE" strokeWidth={7}/>
 {['7','0'].map((d,k)=><g key={d} transform={`translate(${440+200*k} 760)`}><text textAnchor="middle" y={60} fontFamily="Quiet Sans" fontWeight={800} fontSize={220} fill="#8EC5E8" stroke={INK} strokeWidth={8} paintOrder="stroke">{d}</text><path d={`M0 -110Q${-14+3*Math.sin(f*.6+k)} -140 0 ${-170+5*Math.sin(f*.8+k)}Q14 -140 0 -110Z`} fill="#FFC24A" strokeWidth={4}/></g>)}
</svg></Cam></AbsoluteFill>;};
const DESK=[['#C9B79A','#8A6A4E'],['#9FB7C9','#4E6A8A'],['#C9A3A3','#7A4E4E'],['#A9C9A3','#4E7A52'],['#C9C29F','#7A704E']];
const PaperShot:React.FC<P>=({t,dur,p,i})=><AbsoluteFill><Bg c={DESK[i%5][0]}/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} style={{position:'absolute'}} {...S}><path d="M0 1050H1080V1920H0Z" fill={DESK[i%5][1]} strokeWidth={8}/></svg>
 <Paper x={540} y={760} w={700} h={520} lines={p.lines as string[]} size={(p.size as number)??90} rot={-3+2*Math.sin(t*.08)} stack={2}/></Cam></AbsoluteFill>;
const StampShot:React.FC<P>=({t,dur,p,i})=>{const at=6,sp=t>=at?Math.min(1,(t-at)/4):0;return <AbsoluteFill><Bg c={DESK[(i+2)%5][0]}/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} style={{position:'absolute'}} {...S}><path d="M0 1050H1080V1920H0Z" fill={DESK[(i+2)%5][1]} strokeWidth={8}/></svg>
 <Paper x={540} y={760} w={720} h={520} lines={p.lines as string[]} size={(p.size as number)??90} rot={-2} stack={2}/>
 {t>=at&&<svg width={W} height={H} style={{position:'absolute'}}><g transform={`translate(560 860) rotate(-12) scale(${2.2-1.2*sp})`} opacity={sp}><rect x={-190} y={-80} width={380} height={160} rx={18} fill="none" stroke={RED} strokeWidth={16}/><text y={44} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={120} fill={RED}>{p.stamp as string}</text></g></svg>}
 <Burst x={560} y={860} t={t-at} s={1.8}/></Cam></AbsoluteFill>;};
const JudgeShot:React.FC<P>=({t,dur,i})=>{const lean=kf(t,[[0,0],[10,1]]);return <AbsoluteFill><CourtBackground dark/><Cam t={t} dur={dur} i={i} origin="50% 35%">
 <P3 look="judge" x={540} y={1990} s={2.5} expr="serious" phase={.3} eye={[0,-2+5*lean]} pose={(r)=>{r.head=-5*lean+1.5*Math.sin(t*.3);r.torso=-3*lean;}}/></Cam></AbsoluteFill>;};
const Prosecutor:React.FC<P>=({t,dur,i})=>{const g=kf(t,[[2,0],[10,1]]),w=t>14?50*Math.sin((t-14)*.35):0;return <AbsoluteFill><CourtBackground/><Cam t={t} dur={dur} i={i}>
 <P3 look="suit" x={420} y={1800} s={1.75} expr="serious" talk phase={.2} eye={[12,-2]} pose={(r)=>{r.hands=[[-78,-118],[78+180*g,-118-300*g+w*g]];r.handProps=[{pose:'relaxed'},{pose:g>.5?'point':'relaxed'}];}}/>
 <Paper x={820} y={640} w={360} h={240} lines={['구형']} size={80} rot={5}/></Cam></AbsoluteFill>;};
const Phone:React.FC<P>=({t,dur,p,i})=>{const msgs=p.msgs as string[];return <AbsoluteFill><Bg c="#25303B" c2="#3C5366"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <g transform={`rotate(${-4+2*Math.sin(t*.1)} 540 680)`}><rect x={250} y={190} width={580} height={980} rx={60} fill="#1D1F24" strokeWidth={10}/><rect x={280} y={260} width={520} height={840} rx={24} fill="#EEF2F5" strokeWidth={4}/>
  {msgs.map((m,k)=>{const a=clamp01((t-4-k*14)/5);return <g key={k} opacity={a} transform={`translate(${k%2?0:-10} ${(1-a)*30})`}><rect x={k%2?380:300} y={340+k*190} width={400} height={130} rx={34} fill={k%2?'#FFE36E':'#FFFFFF'} strokeWidth={5}/><text x={k%2?580:500} y={420+k*190} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={44} fill={INK} stroke="none">{m}</text></g>;})}
 </g></svg></Cam></AbsoluteFill>;};
const Money:React.FC<P>=({t,dur,p,i})=>{const n=(p.n as number)??3;return <AbsoluteFill><Bg c="#C9B79A"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <path d="M0 1000H1080V1920H0Z" fill="#8A6A4E" strokeWidth={8}/>
 {Array.from({length:n}).map((_,k)=>{const a=clamp01((t-k*9)/6),x=220+k*320;return <g key={k} transform={`translate(${x+(1-a)*600} ${880-(1-a)*120}) rotate(${(k-1)*6}) scale(1.35)`} opacity={a}>{[0,1,2].map(j=><path key={j} d={`M-120 ${-60-j*24}H120V${-10-j*24}H-120Z`} fill="#8CC08A" strokeWidth={5}/>)}<path d="M-20 -130V-10M20 -130V-10" stroke="#F4EBD3" strokeWidth={14}/><text y={90} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={60} fill={PAPER} stroke={INK} strokeWidth={8} paintOrder="stroke">{k+1}번</text></g>;})}
</svg></Cam></AbsoluteFill>;};
const Calendar:React.FC<P>=({t,dur,p,i})=>{const flip=kf(t,[[2,0],[10,1]]);return <AbsoluteFill><Bg c="#DDD4BF"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <g transform="translate(540 760)"><path d="M-320 -360H320V380H-320Z" fill="#FFF" strokeWidth={10}/><path d="M-320 -360H320V-200H-320Z" fill={RED} strokeWidth={10}/>{[-200,-60,80,220].map(x=><circle key={x} cx={x} cy={-360} r={18} fill="#555" strokeWidth={5}/>)}
  <text y={-250} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={70} fill="#FFF" stroke="none">연도</text>
  <text y={120} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={210} fill={INK} stroke="none">{p.year as string}</text>
  <g transform={`scale(1 ${1-flip})`} opacity={1-flip}><path d="M-320 -200H320V380H-320Z" fill="#F4F1EA" strokeWidth={8}/></g></g>
</svg></Cam></AbsoluteFill>;};
const CellShot:React.FC<P>=({t,dur,p,i})=>{const rat=Math.sin(t*1.4)*10*clamp01((t-4)/6),turn=kf(t,[[dur*.5,0],[dur*.5+10,1]]);return <AbsoluteFill><Cam t={t} dur={dur} i={i}><Cell/>
 <P3 look={p.look as Look} x={540} y={1640} s={1.45} expr={(p.expr as Expr)??'tired'} phase={.8} eye={[-10*turn,6]} pose={(r)=>{r.hands=[[-200+rat,-330],[200+rat,-330]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.head=rat*.4-5*turn;}}/>
 <Bars xs={[235,845]} dx={rat*.5}/></Cam></AbsoluteFill>;};
// ---- reaction close-up: big expression, 1-2 s ----
const BG:Record<string,[string,string]>={smug:['#3E2E4F','#7C5BA0'],shock:['#4A1F24','#C9503E'],scared:['#1F3A4A','#4F8DB0'],tired:['#2B3138','#5A6470'],concern:['#2B3138','#6B7A86'],normal:['#2D4A3E','#5FA08A'],angry:['#4A1F24','#C9503E']};
const React1:React.FC<P>=({t,dur,p,i})=>{const ex=(p.expr as Expr)??'shock',mv=(p.move as string)??'nod',[c1,c2]=BG[ex]??BG.normal;
 const pose=(r:Parameters<NonNullable<React.ComponentProps<typeof Who>['pose']>>[0])=>{
  if(mv==='nod'){r.head=8*Math.sin(t*.45);}
  if(mv==='shake'){r.head=10*Math.sin(t*.9);r.torso=3*Math.sin(t*.9);}
  if(mv==='recoil'){const k=kf(t,[[0,0],[6,1]]);r.hip[1]+=30*k;r.torso=-8*k;r.hands=[[-120*k-70,-200-250*k],[120*k+70,-200-250*k]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=-6*k;}
  if(mv==='shrug'){const k=Math.max(0,Math.sin(t*.25));r.hands=[[-160-60*k,-260-120*k],[160+60*k,-260-120*k]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=6*Math.sin(t*.2);}};
 return <AbsoluteFill><Bg c={c1} c2={c2}/><Rays color="#FFFFFF" t={t}/><Cam t={t} dur={dur} i={i} origin="50% 40%">
  <P3 look={p.look as Look} x={540} y={(p.y as number)??1960} s={2.45} expr={ex} talk={false} phase={.4} eye={[0,0]} pose={pose}/>{(ex==='shock'||ex==='scared')&&<Sweat x={780} y={560} t={t} s={1.4}/>}</Cam></AbsoluteFill>;};
const Bubble:React.FC<P>=({t,dur,p,i})=>{const a=kf(t,[[0,.6],[6,1]]);return <AbsoluteFill><Bg c="#2E4A5A" c2="#5C8FA8"/><Rays color="#FFFFFF" t={t}/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <g transform={`translate(540 760) scale(${a}) rotate(${-3+3*Math.sin(t*.12)})`}><path d="M-400 -260Q-400 -330 -330 -330H330Q400 -330 400 -260V180Q400 250 330 250H-60L-180 380L-150 250H-330Q-400 250 -400 180Z" fill="#FFFFFF" strokeWidth={12}/>
 <text y={-10} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={(p.size as number)??130} fill={INK} stroke="none">{(p.lines as string[])[0]}</text>{(p.lines as string[])[1]&&<text y={140} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={90} fill={RED} stroke="none">{(p.lines as string[])[1]}</text>}</g>
</svg></Cam></AbsoluteFill>;};
// ---- parking garage: the kick. s = frames from frame 0 (negative during the loop line) ----
const Garage:React.FC=()=><AbsoluteFill style={{background:'#5B6066'}}><svg width={W} height={H} {...S}>
 <path d="M0 0H1080V1150H0Z" fill="#7A8088"/>{[0,1,2,3].map(k=><path key={k} d={`M${k*300+40} 0V1150`} stroke="#6A7078" strokeWidth={30}/>)}
 <path d="M0 160H1080V220H0Z" fill="#9AA0A8" strokeWidth={6}/>{[140,540,940].map(x=><rect key={x} x={x-70} y={185} width={140} height={20} rx={8} fill="#F4F0D0" stroke="none"/>)}
 <path d="M0 1150H1080V1920H0Z" fill="#4B5056"/><path d="M0 1150H1080" strokeWidth={9}/>{[200,620].map(x=><path key={x} d={`M${x} 1250L${x-80} 1920`} stroke="#E8E2C0" strokeWidth={14}/>)}
 <path d="M760 760H1080V1150H760Z" fill="#2F5E8C" strokeWidth={8}/><path d="M800 800H1040V940H800Z" fill="#9FC3D9" strokeWidth={6}/>
</svg></AbsoluteFill>;
const Lying:React.FC<{look:Look;x:number;y:number;s:number;expr:Expr;t:number}>=({look,x,y,s,expr,t})=><AbsoluteFill style={{transform:`translate(${x}px,${y}px) rotate(84deg)`,transformOrigin:'0 0'}}>
 <P3 look={look} x={0} y={0} s={s} expr={expr} phase={.5} eye={[0,8]} pose={(r)=>{r.hands=[[-120,-420+10*Math.sin(t*.6)],[90,-460]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=6*Math.sin(t*.5);}}/></AbsoluteFill>;
export const KickStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),wind=s<0?kf(s,[[-60,0],[-8,1]]):1,kick=s>=0?kf(s,[[0,.8],[3,1],[14,.2]]):kf(s,[[-8,0],[-1,.8]]),hit=s>=1&&s<8,sh=hit?(8-s)*3*(s%2?1:-1):0;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${sh}px,0) scale(${1.05+.02*Math.sin(f*.05)})`,transformOrigin:'50% 50%'}}><Garage/>
  <Lying look="driver" x={150} y={1600} s={1.15} expr={s>=1?'pain':'scared'} t={f}/>
  <P3 look="clerk" x={330} y={1760} s={1.6} expr="angry" phase={.3} eye={[12,8]} pose={(r)=>{r.torso=-6*wind+8*kick;r.feet[1]=[40+40*wind+250*kick,-40*wind-170*kick];r.hip[1]+=-10*kick;r.hands=[[-160,-300-40*kick],[120,-280]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.head=-4*kick;}} ik={{knee:[[-.3,-1],[.6,-1]]}}/>
  <Burst x={800} y={1480} t={s-1} s={1.5}/>
 </AbsoluteFill></AbsoluteFill>;
};
const Trip:React.FC<P>=({t,dur,i})=>{const sweep=kf(t,[[4,0],[14,1]]),fall=kf(t,[[10,0],[24,1]]);return <AbsoluteFill><Cam t={t} dur={dur} i={i}><Garage/>
 <AbsoluteFill style={{transform:`rotate(${-80*fall}deg)`,transformOrigin:'700px 1700px'}}><P3 look="driver" x={700} y={1700} s={1.5} expr={fall>.3?'shock':'normal'} phase={.5} eye={[-10,0]} pose={(r)=>{r.hands=[[-150*fall-78,-118-200*fall],[150*fall+78,-118-200*fall]];r.handProps=[{pose:'open'},{pose:'open'}];}}/></AbsoluteFill>
 <P3 look="hoodie" x={380} y={1700} s={1.6} expr="angry" phase={.2} eye={[12,2]} pose={(r)=>{r.feet[1]=[40+200*sweep,-60*sweep];r.torso=10*sweep;r.hands=[[-100,-250],[140+120*sweep,-300]];r.handProps=[{pose:'fist'},{pose:'open'}];}} ik={{knee:[[-.3,-1],[.6,-1]]}}/>
</Cam></AbsoluteFill>;};
const Cctv:React.FC<P>=({t,dur,i})=>{const run=clamp01(t/26),bump=t>=26&&t<34,z=1+.35*ease(clamp01(t/dur));return <AbsoluteFill><Bg c="#15181C" c2="#2A3038"/><Cam t={t} dur={dur} i={i}><AbsoluteFill style={{transform:`scale(${z})`,transformOrigin:'62% 40%'}}><svg width={W} height={H} {...S}>
 <rect x={90} y={380} width={900} height={760} rx={30} fill="#222" strokeWidth={10}/><rect x={130} y={420} width={820} height={620} fill="#3E4A44" strokeWidth={5}/>
 <g opacity={.9}><path d="M130 860H950" stroke="#5E6B64" strokeWidth={6}/>
  <g transform={`translate(${720} 860)`}><circle cy={-210} r={34} fill="#C9D1C9" strokeWidth={5}/><path d="M-30 -170H30L40 -40H-40Z" fill="#8A968E" strokeWidth={5}/><path d="M-20 -40V0M20 -40V0" strokeWidth={10}/></g>
  <g transform={`translate(${200+430*run} 860)`}><circle cy={-110} r={24} fill="#C9D1C9" strokeWidth={5}/><path d="M-18 -86H18L22 -30H-22Z" fill="#B0BAB2" strokeWidth={4}/><path d={`M-10 -30L${-14+8*Math.sin(t)} 0M10 -30L${14-8*Math.sin(t)} 0`} strokeWidth={8}/><path d="M60 -60L90 -60M70 -40L100 -40" stroke="#E8E2C0" strokeWidth={5} opacity={run<1?1:0}/></g></g>
 {bump&&<circle cx={665} cy={760} r={46} fill="none" stroke={RED} strokeWidth={10}/>}
 <circle cx={180} cy={470} r={22} fill={Math.floor(t/8)%2?RED:'#5A2420'} stroke="none"/>
 <text x={930} y={1020} textAnchor="end" fontFamily="Quiet Sans" fontWeight={800} fontSize={64} fill="#E8E2C0" stroke="none">22:40</text>
 {Array.from({length:6}).map((_,k)=><path key={k} d={`M130 ${420+((t*14+k*104)%620)}H950`} stroke="#FFFFFF" strokeWidth={3} opacity={.12}/>)}
</svg></AbsoluteFill></Cam></AbsoluteFill>;};
const Tally:React.FC<P>=({t,dur,p,i})=>{const n=(p.n as number)??5;return <AbsoluteFill><Bg c="#1F3A2E" c2="#2F5A46"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <rect x={110} y={380} width={860} height={700} rx={20} fill="#2E4B3C" stroke="#7A5A44" strokeWidth={24}/>
 <text x={540} y={520} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={84} fill="#EDEDE0" stroke="none">{p.label as string}</text>
 {Array.from({length:n}).map((_,k)=>{const a=clamp01((t-4-k*5)/4);if(a<=0)return null;return k<4?<path key={k} d={`M${330+k*90} 640V${640+300*a}`} stroke="#F4F4E8" strokeWidth={22}/>:<path key={k} d={`M290 900L${290+(680-290)*a} ${900-(900-640)*a}`} stroke="#FFD45A" strokeWidth={22}/>;})}
</svg></Cam></AbsoluteFill>;};
// ---- motel front desk: s = frames from frame 0 (negative during the loop line). The guest is never shown. ----
const MotelDesk:React.FC<{s:number}>=({s})=><svg width={W} height={H} style={{position:'absolute'}} {...S}>
 <path d="M0 0H1080V1920H0Z" fill="#4A3B4E"/><path d="M0 0H1080V1180H0Z" fill="#6B5670"/>
 <path d="M40 470H330V820H40Z" fill="#2E2433" strokeWidth={8}/>{[0,1,2].map(k=><g key={k}><rect x={70+k*85} y={510} width={60} height={90} rx={8} fill="#8A7A5A" strokeWidth={5}/><path d={`M${100+k*85} 600V660`} strokeWidth={5}/></g>)}
 <rect x={780} y={470} width={250} height={130} rx={12} fill="#2E2433" strokeWidth={8}/><text x={905} y={562} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={80} fill={s>=0&&Math.floor(s/6)%2?'#FF6B9A':'#FFB0C8'} stroke="none">모텔</text>
</svg>;
export const MotelStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),turn=s<0?kf(s,[[-50,0],[-6,1]]):1,slam=s>=0?kf(s,[[0,.85],[2,1],[12,.6]]):kf(s,[[-6,0],[-1,.8]]),sh=s>=1&&s<7?(7-s)*3*(s%2?1:-1):0;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${sh}px,0) scale(${1.05+.02*Math.sin(f*.05)})`,transformOrigin:'50% 45%'}}><MotelDesk s={s}/>
  <P3 look="attacker" x={540} y={1760} s={1.75} expr={turn>.5?'angry':'serious'} phase={.3} eye={[0,6*turn]} pose={(r)=>{const wipe=s<-8?70*Math.sin(f*.35)*(1-turn):0;r.hands=[[-150-40*slam+wipe,-420+60*slam],[150+40*slam+wipe,-420+60*slam]];r.handProps=[{pose:s<-8?'open':'fist'},{pose:s<-8?'open':'fist'}];r.torso=6*slam+3*Math.sin(f*.2)*(1-turn);r.head=-4*turn+2*slam+5*Math.sin(f*.15)*(1-turn);}}/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}><path d="M-20 1300H1100V1360H-20Z" fill="#B48A5E"/><path d="M-20 1360H1100V1940H-20Z" fill="#7A5638"/>
   {[0,1,2,3].map(k=><g key={k} transform={`translate(${380+k*70+(s>=1&&s<8?(k%2?6:-6):0)} ${1300-k*6}) rotate(${-8+k*5})`}><rect x={-80} y={-36} width={160} height={72} rx={6} fill="#8CC08A" strokeWidth={5}/><text y={14} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={36} fill={INK} stroke="none">1만</text></g>)}</svg>
 </AbsoluteFill></AbsoluteFill>;
};
const River:React.FC<P>=({t,dur,i})=>{const f=useCurrentFrame();return <AbsoluteFill><Bg c="#0E1726" c2="#1F3350"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 {[0,1,2,3,4,5].map(k=><circle key={k} cx={120+k*170} cy={260+(k%2)*40} r={4} fill="#FFF" stroke="none" opacity={.6}/>)}
 <path d="M0 900H1080V1100H0Z" fill="#2A3346" strokeWidth={0}/>{[0,1,2,3,4,5,6].map(k=><rect key={k} x={40+k*150} y={760+(k%3)*30} width={90} height={140-(k%3)*30} fill="#3A4560" strokeWidth={5}/>)}
 <path d="M0 1100H1080V1920H0Z" fill="#183150"/>{[0,1,2,3,4].map(k=><path key={k} d={`M${((k*260+f*3)%1300)-200} ${1200+k*130}q60 -20 120 0t120 0`} fill="none" stroke="#3E6A92" strokeWidth={8}/>)}
 <g transform={`translate(${300+t*9} ${1420+10*Math.sin(f*.3)}) rotate(${3*Math.sin(f*.25)}) scale(1.7)`}><path d="M-200 0H220L170 90H-160Z" fill="#E8E8E0" strokeWidth={8}/><path d="M-60 -110H90V0H-60Z" fill="#2D4F8C" strokeWidth={7}/><text x={15} y={-38} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={40} fill="#FFF" stroke="none">경찰</text><circle cx={60} cy={-130} r={14} fill={Math.floor(f/6)%2?RED:'#3F7BFF'} strokeWidth={4}/></g>
 <path d={`M${400+t*9} 1200L${40+t*9+300*Math.sin(t*.12)} 880L${240+t*9+300*Math.sin(t*.12)} 840Z`} fill="#FFF7C0" opacity={.3} stroke="none"/>
</svg></Cam></AbsoluteFill>;};
const Memorial:React.FC<P>=({t,dur})=><AbsoluteFill><MemorialShot t={t} dur={dur}/><AbsoluteFill style={{background:'#1B2A4A',opacity:.3,mixBlendMode:'multiply'}}/></AbsoluteFill>;
const Tv:React.FC<P>=({t,dur,i})=>{const x=kf(t,[[6,0],[14,1]]);return <AbsoluteFill><Cam t={t} dur={dur} i={i}><Cell/><svg width={W} height={H} style={{position:'absolute'}} {...S}>
 <g transform="translate(540 600)"><rect x={-260} y={-170} width={520} height={330} rx={20} fill="none" stroke="#C9D1D9" strokeWidth={10} strokeDasharray="30 22"/><text y={30} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={110} fill="#C9D1D9" stroke="none">TV</text>
  <path d={`M-200 -120L${-200+400*x} ${-120+240*x}`} stroke={RED} strokeWidth={26}/><path d={`M200 -120L${200-400*x} ${-120+240*x}`} stroke={RED} strokeWidth={26}/></g></svg>
 <P3 look="inmate" x={540} y={1540} s={1.3} expr="angry" phase={.2} eye={[0,-8]} pose={(r)=>{const p=Math.sin(t*.5);r.hands=[[-120,-330-40*Math.max(0,p)],[120+60*Math.max(0,p),-380-120*Math.max(0,p)]];r.handProps=[{pose:'fist'},{pose:'point'}];r.head=-6;}}/></Cam></AbsoluteFill>;};
// ---- taxi crash at night: s = frames from frame 0 (negative during the loop line). Nobody is hurt on screen. ----
const Taxi:React.FC<{x:number;rot:number}>=({x,rot})=><svg width={W} height={H} style={{position:'absolute'}} {...S}><g transform={`translate(${x+340} 1600) rotate(${-rot}) scale(-.9 .9)`}>
 <path d="M0 -260Q10 -330 90 -340H260Q330 -330 360 -260L380 -120V40H0Z" fill="#F2B632" strokeWidth={9}/><path d="M60 -250L100 -320H250L300 -250Z" fill="#5D6B7E" strokeWidth={7}/>
 <rect x={130} y={-380} width={100} height={40} rx={6} fill="#FFF3C0" strokeWidth={6}/><text x={180} y={-350} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={28} fill={INK} stroke="none">택시</text>
 <circle cx={80} cy={50} r={60} fill="#23252B" strokeWidth={8}/><circle cx={300} cy={50} r={60} fill="#23252B" strokeWidth={8}/></g></svg>;
export const TaxiStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),drive=s<0,dx=drive?f*26:f*26*Math.exp(-Math.max(0,s)/6),sh=s>=1&&s<9?(9-s)*3*(s%2?1:-1):0;
 const tx=s<0?kf(s,[[-90,1300],[0,760]]):760+Math.min(120,s*10),rot=s>=0?Math.min(10,s*1.2):0,grip=1;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${sh}px,${sh*.4}px) scale(1.06)`,transformOrigin:'60% 60%'}}>
  <Street dx={dx}/>
  <Car tilt={s>=0?-2*Math.min(1,s/3):0} color="#2B2D33" driver={<>{WHEEL(880,1030)}<P3 look="D" x={DRIVER.x} y={DRIVER.y} s={DRIVER.s} expr={s>=2?'shock':'dizzy'} phase={.4} eye={[10,s>=2?-6:4]} pose={(r)=>{driverPose(grip,s>=1?-Math.exp(-(s-1)/8):Math.sin(f*.11))(r);if(s>=10){r.head+=8*Math.sin((s-10)*.45);}}}/></>}/>
  <Taxi x={tx} rot={rot}/>
  <Burst x={820} y={1380} t={s-1} s={1.6}/>
 </AbsoluteFill></AbsoluteFill>;
};
const Clock:React.FC<P>=({t,dur,i})=>{const h=Math.min(17,t/14*17);return <AbsoluteFill><Bg c="#22263A" c2="#3C4470"/><Rays color="#FFFFFF" t={t}/><Cam t={t} dur={dur} i={i}>
 <Watch x={540} y={760} s={2.4} sec={(h%1)*180}/>
 <div style={{...type,position:'absolute',left:40,top:1000,width:1000,fontSize:150,color:GOLD}}>+{Math.floor(h)}시간</div></Cam></AbsoluteFill>;};
// ---- factory fire (exterior only; nobody inside is shown). s = frames from frame 0, negative during the loop line ----
export const FireStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),g=s<0?.45+.55*clamp01((s+90)/90):1,boom=s>=1&&s<6?(6-s)/5:0,flick=(k:number)=>.85+.15*Math.sin(s*.9+k*1.7);
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${1.06+.03*Math.sin(s*.07)}) translate(${boom*6*(s%2?1:-1)+14*Math.sin(s*.05)}px,${8*Math.sin(s*.04)}px)`,transformOrigin:'50% 50%'}}>
  <Bg c="#3A3F4A" c2="#6A5A52"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   {Array.from({length:7}).map((_,k)=>{const u=(((s+900)*1.6+k*60)%420)/420,r=(80+220*u)*(.4+.6*g);return <circle key={k} cx={420+k*55+60*Math.sin(u*4+k)} cy={700-620*u} r={r} fill="#1E1E22" stroke="none" opacity={(.9-.6*u)*g}/>;})}
   <path d="M120 700H960V1420H120Z" fill="#B9BEC4" strokeWidth={10}/><path d="M120 700L540 560L960 700Z" fill="#8C939B" strokeWidth={10}/>
   {[0,1,2,3].map(k=><path key={k} d={`M${120+k*210} 700V1420`} stroke="#9EA4AB" strokeWidth={8}/>)}
   <rect x={400} y={620} width={280} height={70} rx={8} fill="#2E4B7A" strokeWidth={6}/><text x={540} y={670} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={44} fill="#FFF" stroke="none">전지 공장</text>
   {[200,420,640,860].map((x,k)=><g key={x}><rect x={x-70} y={780} width={140} height={130} fill="#3A2A22" strokeWidth={7}/>
    <path d={`M${x-60} 905Q${x-40} ${840-50*flick(k)*g} ${x-10} 880Q${x} ${800-70*flick(k+3)*g} ${x+20} 880Q${x+45} ${830-50*flick(k+5)*g} ${x+60} 905Z`} fill="#FF8A2A" stroke="#FFD24A" strokeWidth={5} opacity={g}/></g>)}
   {[200,420,640,860].map(x=><rect key={x} x={x-70} y={1060} width={140} height={130} fill="#6E7A86" strokeWidth={7}/>)}
   <path d="M0 1420H1080V1920H0Z" fill="#4A4B50"/><path d="M0 1420H1080" strokeWidth={9}/>
   <g transform="translate(40 1560)"><path d="M0 0H420V200H0Z" fill="#C9302C" strokeWidth={8}/><path d="M300 -70H420V0H300Z" fill="#C9302C" strokeWidth={8}/><path d="M320 -55H400V-10H320Z" fill="#9FC3D9" strokeWidth={5}/>
    <rect x={40} y={-30} width={200} height={30} fill="#DDD" strokeWidth={5}/><circle cx={330} cy={-90} r={18} fill={Math.floor((s+900)/5)%2?'#3F7BFF':RED} strokeWidth={4}/>
    <text x={150} y={120} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={56} fill="#FFF" stroke="none">119</text>
    <circle cx={90} cy={210} r={45} fill="#23252B" strokeWidth={7}/><circle cx={340} cy={210} r={45} fill="#23252B" strokeWidth={7}/></g>
   <path d={`M780 1500Q${660+30*Math.sin(s*.3)} 1100 ${560+20*Math.sin(s*.25)} 900`} fill="none" stroke="#BFE6FF" strokeWidth={22} opacity={.8*g}/>
  </svg>
  <P3 look="official" x={880} y={1930} s={1.0} expr="serious" phase={.4} eye={[-12,-8]} pose={(r)=>{r.hands=[[-120,-260],[-60,-300]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.torso=-6+3*Math.sin(s*.15);r.head=-4+3*Math.sin(s*.2);r.hip[0]+=10*Math.sin(s*.1);}}/>
  {boom>0&&<AbsoluteFill style={{background:'#FFE6B0',opacity:.4*boom}}/>}
 </AbsoluteFill></AbsoluteFill>;
};
const Helmets:React.FC<P>=({t,dur,p,i})=>{const n=(p.n as number)??23,k=(p.k as number)??20;return <AbsoluteFill><Bg c="#2B2F38" c2="#4A5260"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 {Array.from({length:n}).map((_,j)=>{const col=j%5,row=Math.floor(j/5),x=170+col*185,y=470+row*175,on=t>=4+j*1.1,hi=j<k&&t>=4+n*1.1+4;return <g key={j} transform={`translate(${x} ${y})`} opacity={on?1:0}>
  <path d="M-62 20Q-62 -60 0 -60Q62 -60 62 20Z" fill={hi?GOLD:'#E8E2D2'} strokeWidth={7}/><path d="M-78 20H78V36H-78Z" fill={hi?GOLD:'#E8E2D2'} strokeWidth={7}/></g>;})}
 <text x={540} y={1440} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={60} fill={GOLD} stroke="none" opacity={clamp01((t-4-n*1.1-4)/4)}>노란색 = 파견 근로자</text>
</svg></Cam></AbsoluteFill>;};
// ---- kettle: dim apartment kitchen at midday blinds; a man lifts a steaming electric kettle. Nobody else is shown. ----
const KETTLE=<g stroke="#1E1712" strokeWidth={6} strokeLinejoin="round"><path d="M-60 0L-50 -150Q0 -175 50 -150L60 0Z" fill="#D9DDE2"/><path d="M50 -130Q95 -110 70 -40" fill="none" strokeWidth={14}/><path d="M-50 -150L-95 -175L-80 -135" fill="#D9DDE2"/><rect x={-30} y={-180} width={60} height={22} rx={8} fill="#5A6070"/><circle cx={-20} cy={-40} r={9} fill="#FF5A3A" strokeWidth={3}/></g>;
export const KettleStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),heat=s<0?clamp01((s+90)/80):1,lift=s>=0?kf(s,[[0,.85],[6,1]]):kf(s,[[-14,0],[-1,.85]]),turn=s>=0?kf(s,[[4,0],[14,1]]):0;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${1.06+.03*Math.sin(s*.06)}) translate(${12*Math.sin(s*.05)}px,${6*Math.sin(s*.04)}px)`,transformOrigin:'50% 45%'}}>
  <Bg c="#4A4552" c2="#6E6676"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1180H0Z" fill="#7A7282"/>{Array.from({length:9}).map((_,k)=><path key={k} d={`M620 ${180+k*44}H1020`} stroke="#E8DCC0" strokeWidth={22} opacity={.6}/>)}<path d="M620 170H1020V580H620Z" fill="none" strokeWidth={8}/>
   <path d="M0 1180H1080V1920H0Z" fill="#5A4E46"/><path d="M-20 1100H1100V1180H-20Z" fill="#B9A68A" strokeWidth={8}/><path d="M-20 1180H1100V1260H-20Z" fill="#8A7660" strokeWidth={8}/>
   <path d="M60 300H420V560H60Z" fill="#9AA0A8" strokeWidth={7}/><path d="M80 320H400V540H80Z" fill="#3A3F48"/>
  </svg>
  <P3 look="official" x={400} y={1790} s={1.55} expr="serious" phase={.3} eye={[14,4+6*turn]} pose={(r)=>{r.hands=[[-70,-200],[170+60*lift,-230-110*lift]];r.handProps=[{pose:'relaxed'},{pose:'grip',anchor:'wrist',side:'left',rot:-10+30*turn,object:KETTLE}];r.torso=4*turn;r.head=-3+4*turn+1.5*Math.sin(s*.3);}}/>
  <svg width={W} height={H} style={{position:'absolute'}}>{Array.from({length:6}).map((_,k)=>{const u=(((s+900)*1.5+k*25)%150)/150,x0=720+90*lift+70*turn;return <circle key={k} cx={x0+30*Math.sin(u*6+k)} cy={1180-300*lift-60-u*360} r={18+40*u} fill="#FFFFFF" opacity={(.55-.5*u)*heat}/>;})}</svg>
 </AbsoluteFill></AbsoluteFill>;
};
const PhoneCall:React.FC<P>=({t,dur,i})=>{const ring=Math.sin(t*1.3)*6;return <AbsoluteFill><Bg c="#23263A" c2="#3E4470"/><Rays color="#FFFFFF" t={t}/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <g transform={`translate(540 700) rotate(${ring})`}><rect x={-170} y={-300} width={340} height={600} rx={44} fill="#1D1F24" strokeWidth={10}/><rect x={-145} y={-250} width={290} height={480} rx={20} fill="#2F7A5A" strokeWidth={4}/>
  <text y={-120} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={44} fill="#FFF" stroke="none">통화 중</text><text y={-50} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={60} fill="#FFF" stroke="none">{`0${Math.floor(t/30)}:${String(Math.floor(t%30)*2).padStart(2,'0')}`}</text>
  <circle cx={0} cy={120} r={56} fill={RED} strokeWidth={6}/></g>
 <text x={540} y={1150} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={72} fill={GOLD} stroke={INK} strokeWidth={8} paintOrder="stroke">범행 전날</text>
</svg></Cam></AbsoluteFill>;};
const SCENES:Record<string,React.FC<P>>={phonecall:PhoneCall,helmets:Helmets,clock:Clock,river:River,memorial:Memorial,tv:Tv,tally:Tally,trip:Trip,cctv:Cctv,bubble:Bubble,poster:Poster,cake:Cake,paper:PaperShot,stamp:StampShot,judge:JudgeShot,prosecutor:Prosecutor,phone:Phone,money:Money,calendar:Calendar,cell:CellShot,react:React1};
const StageBody:React.FC<{shot:Shot;t:number;dur:number;i:number}>=({shot,t,dur,i})=>{
 if(shot.s==='deal')return <DealStage s={t}/>;
 if(shot.s==='kick')return <KickStage s={t}/>;
 if(shot.s==='motel')return <MotelStage s={t}/>;
 if(shot.s==='taxi')return <TaxiStage s={t}/>;
 if(shot.s==='fire')return <FireStage s={t}/>;
 if(shot.s==='kettle')return <KettleStage s={t}/>;
 const C=SCENES[shot.s];return C?<C t={t} dur={dur} p={shot} i={i}/>:null;};
const StageFor:React.FC<{shot:Shot;t:number;dur:number;i:number}>=(p)=>{const L=React.useContext(LookCtx);if(!L.on)return <StageBody {...p}/>;const light=LIGHT_OF[p.shot.s]??'court';
 return <LookCtx.Provider value={{...L,light}}><Stage cam={CAM0} light={light}><StageBody {...p}/></Stage></LookCtx.Provider>;};
type L3=Line&{shots?:Shot[]};
export const B3Film:React.FC<{c:Case;u:Line;t:number}>=(p)=>{const on=(p.c as Case&{look?:string}).look==='full',u=p.u;
 if(!on)return <B3FilmIn {...p}/>;
 return <LookCtx.Provider value={{on,light:'court',track:talkTrack(u.tts,Math.round(u.onset*30),Math.round(u.offset*30))}}><B3FilmIn {...p}/></LookCtx.Provider>;};
const B3FilmIn:React.FC<{c:Case;u:Line;t:number}>=({c,u,t})=>{
 const U=c.utterances as L3[];
 if(u.mode==='loop'){const first=(U[0].shots??[{s:'deal'}])[0];return <StageFor shot={first} t={t-u.dur} dur={u.dur} i={0}/>;}
 const shots=(u as L3).shots??[];if(!shots.length)return null;
 const n=shots.length,k=Math.min(n-1,Math.floor(t/(u.dur/n))),seg=Math.round(u.dur/n),idx=U.indexOf(u as L3)*3+k;
 return <StageFor shot={shots[k]} t={t-k*seg} dur={k===n-1?u.dur-k*seg:seg} i={idx}/>;
};
// ---- overlays ----
type Pop={line:string;at:number;big:string;small:string};
export const Pops:React.FC<{c:Case}>=({c})=>{
 const f=useCurrentFrame(),pops=((c as Case&{pops?:Pop[]}).pops)??[];
 const live=pops.map(p=>{const u=c.utterances.find(x=>x.id===p.line)!;const a=u.from_frame+Math.round(p.at*u.dur);const nxt=pops.filter(q=>q.line===p.line&&q.at>p.at).map(q=>u.from_frame+Math.round(q.at*u.dur));const b=Math.min(u.from_frame+u.dur,...nxt);return {p,a,b,mode:u.mode};}).find(x=>f>=x.a&&f<x.b);
 if(!live)return null;const d=f-live.a,sc=d<6?.6+.4*ease(d/6)+.12*Math.sin(d*1.2)*(1-d/6):1;
 if(live.mode==='answer')return null;const low=live.mode==='answer2';
 return <div style={{...type,position:'absolute',left:30,top:low?1560:150,width:1020,zIndex:25,transform:`scale(${sc})`,transformOrigin:'50% 30%'}}>
  <div style={{fontFamily:'Quiet Sans',fontSize:64,color:PAPER,WebkitTextStroke:`7px ${INK}`}}>{live.p.small}</div>
  <div style={{fontSize:118,color:GOLD,lineHeight:1.05,letterSpacing:'-.02em'}}>{live.p.big}</div></div>;
};
// original gag: a small gavel with eyes hops in and flips a "구독" card (7.0-8.0 s), bottom-left, clear of faces and captions
export const SubGag:React.FC=()=>{const f=useCurrentFrame(),t=f-210;if(t<0||t>=30)return null;
 const hop=Math.abs(Math.sin(t*.35))*40,flip=kf(t,[[8,-1],[14,1]]),out=kf(t,[[24,0],[30,1]]);
 return <svg width={W} height={H} style={{position:'absolute',zIndex:26}} {...S}><g transform={`translate(${200-240*out} ${1640-hop})`}>
  <g transform="rotate(-20)"><path d="M-10 0V-120H10V0Z" fill="#A17442" strokeWidth={6}/><rect x={-70} y={-170} width={140} height={60} rx={10} fill="#AD7944" strokeWidth={6}/><circle cx={-22} cy={-140} r={8} fill={INK} stroke="none"/><circle cx={22} cy={-140} r={8} fill={INK} stroke="none"/><path d="M-14 -124Q0 -114 14 -124" fill="none" strokeWidth={4}/></g>
  <g transform={`translate(150 -150) scale(${flip} 1)`}><rect x={-110} y={-60} width={220} height={120} rx={20} fill={flip>0?RED:'#EEE'} strokeWidth={7}/>{flip>0&&<text y={22} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={62} fill="#FFF" stroke="none">구독</text>}</g>
 </g></svg>;};
export const HookText:React.FC<{c:Case}>=({c})=>{const f=useCurrentFrame(),h=(c as Case&{hook_text?:string[]}).hook_text;if(!h)return null;
 const first=c.utterances[0],last=c.utterances[c.utterances.length-1];
 let a=0;if(f<first.from_frame+first.dur)a=1;else if(f>=last.from_frame+last.dur-24)a=clamp01((f-(last.from_frame+last.dur-24))/8);
 if(a<=0)return null;
 return <div style={{...type,position:'absolute',left:40,top:150,width:1000,zIndex:24,opacity:a}}><div style={{fontSize:100}}>{h[0]}</div><div style={{fontSize:190,color:RED,lineHeight:1}}>{h[1]}</div></div>;};
export {TEAL};
