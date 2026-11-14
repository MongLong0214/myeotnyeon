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
import {Actor2} from './look/v2/Actor2';
import {talkTrack2,LIPDATA,type Track2} from './look/v2/Lip';
import {useStr,str,em,localeOf,LocaleCtx} from './i18n';
import STAGE_LIB from '../../../../factory/shorts/library.json';
// opt-in look layer (spec "look":"full"): every B3 character becomes a lit, sprung Actor and every shot sits in a Stage
type LookC={on:boolean;v2?:boolean;light:LightKey;track?:{from:number;v:any[]};track2?:Track2};
const LookCtx=React.createContext<LookC>({on:false,light:'court'});
type WhoP=React.ComponentProps<typeof Who>;
const P3:React.FC<WhoP>=(o)=>{const L=React.useContext(LookCtx);if(!L.on)return <Who {...o}/>;
 const base=(r:any,f:number)=>{r.hands=[[-78,-118],[78,-118]];o.pose?.(r,f);};
 if(L.v2)return <Actor2 look={o.look} x={o.x} y={o.y} s={o.s} expr={o.expr} eye={o.eye} ik={o.ik} pose={base} light={L.light} seed={Math.round((o.phase??0)*7)} weight={4} talk={o.talk?L.track2:undefined} springs={{props:null}} shade={o.s<2}/>;
 return <Actor look={o.look} x={o.x} y={o.y} s={o.s} expr={o.expr} eye={o.eye} ik={o.ik} pose={base} light={L.light} seed={Math.round((o.phase??0)*7)} weight={4} talk={o.talk?L.track:undefined} springs={{props:null}}/>;};
const LIGHT_OF:Record<string,LightKey>={holiday:'homeNight',yard:'nightStreet',pledge:'court',factory:'street',bank:'court',scan:'homeNight',voucher:'homeNight',busargue:'court',glare:'nightStreet',printshop:'homeNight',receipt:'courtDark',salt:'street',saltwork:'street',bus:'court',cab:'nightStreet',soju:'nightStreet',chase:'nightStreet',forge:'homeNight',flee:'nightStreet',plane:'street',bb:'street',dog:'cell',kettle:'homeNight',phonecall:'courtDark',fire:'street',helmets:'courtDark',taxi:'nightStreet',deal:'court',kick:'nightStreet',motel:'homeNight',trip:'nightStreet',river:'nightStreet',cell:'cell',tv:'cell',judge:'courtDark',prosecutor:'court',react:'street',memorial:'street',cctv:'nightStreet',bar:'homeNight'};
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
 const f=useCurrentFrame(),e=clamp01((s+40)/80),ex=820-420*e,ey=1185-40*Math.sin(Math.PI*e),talk=Math.sin(f*.5);
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
const StampShot:React.FC<P>=({t,dur,p,i})=>{const L_=React.useContext(LocaleCtx),at=6,sp=t>=at?Math.min(1,(t-at)/4):0;return <AbsoluteFill><Bg c={DESK[(i+2)%5][0]}/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} style={{position:'absolute'}} {...S}><path d="M0 1050H1080V1920H0Z" fill={DESK[(i+2)%5][1]} strokeWidth={8}/></svg>
 <Paper x={540} y={760} w={720} h={520} lines={p.lines as string[]} size={(p.size as number)??90} rot={-2} stack={2}/>
 {t>=at&&<svg width={W} height={H} style={{position:'absolute'}}><g transform={`translate(560 ${(p.sy as number)??860}) rotate(-12) scale(${2.2-1.2*sp})`} opacity={sp}><rect x={-190} y={-80} width={380} height={160} rx={18} fill="none" stroke={RED} strokeWidth={16}/><text y={44} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={L_==='ko'?120:Math.min(120,Math.floor(340/Math.max(1,em(L_,String(p.stamp)))))} fill={RED}>{p.stamp as string}</text></g></svg>}
 <Burst x={560} y={(p.sy as number)??860} t={t-at} s={1.8}/></Cam></AbsoluteFill>;};
const JudgeShot:React.FC<P>=({t,dur,i})=>{const lean=kf(t,[[0,0],[10,1]]);return <AbsoluteFill><CourtBackground dark/><Cam t={t} dur={dur} i={i} origin="50% 35%">
 <P3 look="judge" x={540} y={1990} s={2.5} expr="serious" phase={.3} eye={[0,-2+5*lean]} pose={(r)=>{r.head=-5*lean+1.5*Math.sin(t*.3);r.torso=-3*lean;}}/></Cam></AbsoluteFill>;};
const Prosecutor:React.FC<P>=({t,dur,i})=>{const S_=useStr(),g=kf(t,[[2,0],[10,1]]),w=t>14?50*Math.sin((t-14)*.35):0;return <AbsoluteFill><CourtBackground/><Cam t={t} dur={dur} i={i}>
 <P3 look="suit" x={420} y={1800} s={1.75} expr="serious" talk phase={.2} eye={[12,-2]} pose={(r)=>{r.hands=[[-78,-118],[78+180*g,-118-300*g+w*g]];r.handProps=[{pose:'relaxed'},{pose:g>.5?'point':'relaxed'}];}}/>
 <Paper x={820} y={640} w={360} h={240} lines={[S_.prosecutor]} size={80} rot={5}/></Cam></AbsoluteFill>;};
const Phone:React.FC<P>=({t,dur,p,i})=>{const msgs=p.msgs as string[];return <AbsoluteFill><Bg c="#25303B" c2="#3C5366"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <g transform={`rotate(${-4+2*Math.sin(t*.1)} 540 680)`}><rect x={250} y={190} width={580} height={980} rx={60} fill="#1D1F24" strokeWidth={10}/><rect x={280} y={260} width={520} height={840} rx={24} fill="#EEF2F5" strokeWidth={4}/>
  {msgs.map((m,k)=>{const a=clamp01((t-4-k*14)/5);return <g key={k} opacity={a} transform={`translate(${k%2?0:-10} ${(1-a)*30})`}><rect x={k%2?380:300} y={340+k*190} width={400} height={130} rx={34} fill={k%2?'#FFE36E':'#FFFFFF'} strokeWidth={5}/><text x={k%2?580:500} y={420+k*190} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={44} fill={INK} stroke="none">{m}</text></g>;})}
 </g></svg></Cam></AbsoluteFill>;};
const Money:React.FC<P>=({t,dur,p,i})=>{const S_=useStr(),n=(p.n as number)??3;return <AbsoluteFill><Bg c="#C9B79A"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <path d="M0 1000H1080V1920H0Z" fill="#8A6A4E" strokeWidth={8}/>
 {Array.from({length:n}).map((_,k)=>{const a=clamp01((t-k*9)/6),x=220+k*320;return <g key={k} transform={`translate(${x+(1-a)*600} ${880-(1-a)*120}) rotate(${(k-1)*6}) scale(1.35)`} opacity={a}>{[0,1,2].map(j=><path key={j} d={`M-120 ${-60-j*24}H120V${-10-j*24}H-120Z`} fill="#8CC08A" strokeWidth={5}/>)}<path d="M-20 -130V-10M20 -130V-10" stroke="#F4EBD3" strokeWidth={14}/>{!p.nolabel&&<text y={90} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={60} fill={PAPER} stroke={INK} strokeWidth={8} paintOrder="stroke">{S_.nth(k+1)}</text>}</g>;})}
</svg></Cam></AbsoluteFill>;};
const Calendar:React.FC<P>=({t,dur,p,i})=>{const S_=useStr(),pop=t<6?.85+.15*ease(t/6)+.06*Math.sin(t*1.5)*(1-t/6):1,y=String(p.year??''),m=p.month?String(p.month):'';return <AbsoluteFill><Bg c="#DDD4BF"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <g transform={`translate(540 760) scale(${pop})`}><path d="M-320 -360H320V380H-320Z" fill="#FFF" strokeWidth={10}/><path d="M-320 -360H320V-200H-320Z" fill={RED} strokeWidth={10}/>{[-200,-60,80,220].map(x=><circle key={x} cx={x} cy={-360} r={18} fill="#555" strokeWidth={5}/>)}
  <text y={-250} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={80} fill="#FFF" stroke="none">{m?S_.year(y):S_.yearLabel}</text>
  <text y={m?150:120} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={m?260:210} fill={INK} stroke="none">{m?S_.month(m):y}</text></g>
</svg></Cam></AbsoluteFill>;};
const CellShot:React.FC<P>=({t,dur,p,i})=>{const rat=Math.sin(t*1.4)*10*clamp01((t-4)/6),turn=kf(t,[[dur*.5,0],[dur*.5+10,1]]);return <AbsoluteFill><Cam t={t} dur={dur} i={i}><Cell/>
 <P3 look={p.look as Look} x={540} y={1640} s={1.45} expr={(p.expr as Expr)??'tired'} phase={.8} eye={[-10*turn,6]} pose={(r)=>{r.hands=[[-200+rat,-330],[200+rat,-330]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.head=rat*.4-5*turn;}}/>
 <Bars xs={[235,845]} dx={rat*.5}/></Cam></AbsoluteFill>;};
// ---- reaction close-up: big expression, 1-2 s ----
// optional p.sc shrinks the whole drawn character with a CSS scale around its foot point; passing a smaller s to P3 instead
// would switch on Actor2's s<2 face/torso shade, which reads as a second offset head at close-up size (en003 L12, 11-14)
const BG:Record<string,[string,string]>={smug:['#3E2E4F','#7C5BA0'],shock:['#4A1F24','#C9503E'],scared:['#1F3A4A','#4F8DB0'],tired:['#2B3138','#5A6470'],concern:['#2B3138','#6B7A86'],normal:['#2D4A3E','#5FA08A'],angry:['#4A1F24','#C9503E']};
// close framing (y 2040-2140, i.e. the library 'close' 2090) is drawn 80 px higher: at 2090 the face detector's box (chin + neck) sat ~13% under
// a one-line subtitle (zzh049 L06, 11-14); specs that copied y:2090 get the fix without a spec edit
const React1:React.FC<P>=({t,dur,p,i})=>{const ex=(p.expr as Expr)??'shock',mv=(p.move as string)??'nod',[c1,c2]=BG[ex]??BG.normal,y0=(p.y as number)??1960,fy=y0>=2040&&y0<=2140?y0-80:y0;
 const pose=(r:Parameters<NonNullable<React.ComponentProps<typeof Who>['pose']>>[0])=>{
  if(mv==='nod'){r.head=8*Math.sin(t*.45);}
  if(mv==='shake'){r.head=10*Math.sin(t*.9);r.torso=3*Math.sin(t*.9);}
  if(mv==='recoil'){const k=kf(t,[[0,0],[6,1]]);r.hip[1]+=30*k;r.torso=-8*k;r.hands=[[-120*k-70,-200-250*k],[120*k+70,-200-250*k]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=-6*k;}
  if(mv==='shrug'){const k=Math.max(0,Math.sin(t*.25));r.hands=[[-160-60*k,-260-120*k],[160+60*k,-260-120*k]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=6*Math.sin(t*.2);}};
 return <AbsoluteFill><Bg c={c1} c2={c2}/><Rays color="#FFFFFF" t={t}/><Cam t={t} dur={dur} i={i} origin="50% 40%">
  <AbsoluteFill style={p.sc?{transform:`scale(${(p.sc as number)/2.45})`,transformOrigin:`540px ${fy}px`}:undefined}><P3 look={p.look as Look} x={540} y={fy} s={2.45} expr={ex} talk={false} phase={.4} eye={[0,0]} pose={pose}/></AbsoluteFill>{(ex==='shock'||ex==='scared')&&<Sweat x={780} y={560} t={t} s={1.4}/>}</Cam></AbsoluteFill>;};
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
 {Array.from({length:n}).map((_,k)=>{const a=k===0?1:clamp01((t-k*(n>5?3:5))/4);if(a<=0)return null;const g=Math.floor(k/5),j=k%5,gs=Math.ceil(n/5),w=gs>1?250:390,x0=540-(gs*w+(gs-1)*40)/2+g*(w+40),dx=w/4.5;return j<4?<path key={k} d={`M${x0+dx*(j+.5)} 640V${640+300*a}`} stroke="#F4F4E8" strokeWidth={22}/>:<path key={k} d={`M${x0-10} 900L${x0-10+(w+20)*a} ${900-260*a}`} stroke="#FFD45A" strokeWidth={22}/>;})}
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
  <P3 look="official" x={880} y={2070} s={1.0} expr="serious" phase={.4} eye={[-12,-8]} pose={(r)=>{r.hands=[[-120,-260],[-60,-300]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.torso=-6+3*Math.sin(s*.15);r.head=-4+3*Math.sin(s*.2);r.hip[0]+=10*Math.sin(s*.1);}}/>
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
// ---- restaurant yard: three young men fire toy pistols toward off-screen right. The dogs are not shown being hit. ----
const PISTOL=<g stroke="#1E1712" strokeWidth={6} strokeLinejoin="round" transform="scale(-1.7 1.7)"><path d="M-14 10V-40H14V10Z" fill="#5A5A66"/><path d="M-16 -40H74V-64H-16Z" fill="#7A7A88"/><path d="M64 -60H82V-46H64Z" fill="#C9302C"/></g>;
export const BBStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),aim=s<0?kf(s,[[-80,0],[-30,1]]):1,fire=(k:number)=>s>=0||s>-25?Math.max(0,Math.sin((s+900)*1.1+k*2)):0;
 const shooter=(look:Look,x:number,y:number,sc:number,k:number)=>{const kick=fire(k)*aim;return <P3 key={look} look={look} x={x} y={y} s={sc} expr="smug" phase={k} eye={[14,-2]} pose={(r)=>{r.hands=[[70+190*aim,-260-40*aim+6*kick],[100+240*aim,-280-50*aim-14*kick]];r.handProps=[{pose:'fist'},{pose:'grip',anchor:'wrist',side:'left',rot:6*kick-8,object:PISTOL}];r.torso=4*aim-2*kick;r.head=-3*aim+1.5*Math.sin((s+900)*.2+k);}}/>;};
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${1.06+.03*Math.sin(s*.06)}) translate(${10*Math.sin(s*.05)}px,${6*Math.sin(s*.04)}px)`,transformOrigin:'50% 50%'}}>
  <Bg c="#9FB7A0" c2="#C9DDB8"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1150H0Z" fill="#BFD3E0"/><path d="M60 360H700V1150H60Z" fill="#E8D8B8" strokeWidth={9}/><path d="M60 360L380 220L700 360Z" fill="#A8553C" strokeWidth={9}/>
   <rect x={180} y={420} width={400} height={90} rx={10} fill="#3A6A4A" strokeWidth={7}/><text x={380} y={482} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={56} fill="#FFF" stroke="none">식당</text>
   <path d="M140 600H300V800H140Z M460 600H620V800H460Z" fill="#9FC3D9" strokeWidth={7}/>
   <path d="M0 1150H1080V1920H0Z" fill="#8FA86A"/><path d="M0 1150H1080" strokeWidth={8}/>
   {[760,860,960,1060].map(x=><path key={x} d={`M${x} 1050V1300`} stroke="#8A6A4E" strokeWidth={18}/>)}<path d="M720 1100H1100M720 1220H1100" stroke="#8A6A4E" strokeWidth={14}/>
   {Array.from({length:10}).map((_,k)=>{const u=(((s+900)*2.2+k*13)%40)/40;return <circle key={k} cx={600+520*u} cy={1060-40*(k%3)+30*Math.sin(k)} r={7} fill="#FFE066" stroke="none" opacity={(s>-25?1:0)*(1-u)}/>;})}
  </svg>
  {shooter('passenger',110,1430,.9,0)}{shooter('driver',340,1470,.95,1)}{shooter('hoodie',570,1510,1.0,2)}
 </AbsoluteFill></AbsoluteFill>;
};
const DogCare:React.FC<P>=({t,dur,i})=>{const br=Math.sin(t*.18);return <AbsoluteFill><Bg c="#DDE6E8" c2="#F4F7F7"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <path d="M0 1200H1080V1920H0Z" fill="#B8C6CC"/><path d="M120 1180H960V1260H120Z" fill="#E9EEF0" strokeWidth={8}/>
 <g transform={`translate(540 1060) scale(${1+.01*br})`}>
  <ellipse cx={60} cy={60} rx={300} ry={110} fill="#E8C89A" strokeWidth={9}/><path d={`M300 40Q380 ${0+20*Math.sin(t*.6)} ${360+20*Math.sin(t*.6)} -40`} fill="none" strokeWidth={14} stroke="#C9A26E"/>
  <circle cx={-230} cy={-40} r={130} fill="#E8C89A" strokeWidth={9}/><path d="M-330 -120Q-380 0 -320 40Z" fill="#B48A5E" strokeWidth={8}/><path d="M-140 -130Q-90 -20 -150 20Z" fill="#B48A5E" strokeWidth={8}/>
  <ellipse cx={-300} cy={10} rx={40} ry={30} fill={INK}/><circle cx={-190} cy={-50} r={14} fill={INK}/>
  <path d="M-310 -150Q-230 -60 -130 -110" fill="none" stroke="#FFFFFF" strokeWidth={46}/><path d="M-310 -150Q-230 -60 -130 -110" fill="none" stroke="#D9DDE0" strokeWidth={4}/>
  <path d="M-255 -55L-215 -75" stroke="#FFFFFF" strokeWidth={30}/></g>
 <text x={540} y={560} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={70} fill={INK} stroke="none">동물병원</text>
 <g transform="translate(700 700)"><rect x={-170} y={-110} width={340} height={200} rx={16} fill="#1D2A2E" strokeWidth={7}/><path d={`M-150 0${Array.from({length:14}).map((_,k)=>{const x=-150+k*22,ph=((k*22+t*14)%220);return ` L${x} ${ph>180&&ph<200?-70:ph>200&&ph<210?40:0}`;}).join("")}`} fill="none" stroke="#4FE08A" strokeWidth={6}/></g>
</svg></Cam></AbsoluteFill>;};
// ---- flee: night street outside an exchange shop; the man runs off with a heavy bag, a plane crosses the sky. Nobody else is shown. ----
const BAG=<g stroke="#1E1712" strokeWidth={6} strokeLinejoin="round"><path d="M-60 0Q-70 -90 0 -95Q70 -90 60 0Z" fill="#3E3A36"/><path d="M-30 -95Q0 -140 30 -95" fill="none" strokeWidth={10}/><text y={-30} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={44} fill="#FFD45A" stroke="none">₩</text></g>;
export const FleeStage:React.FC<{s:number}>=({s})=>{
 const T=s+900,ph=T*.42,run=s<0?clamp01((s+60)/40):1,px=((T*16)%1800)-400;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${1.06+.02*Math.sin(s*.07)}) translate(${10*Math.sin(s*.05)}px,0)`,transformOrigin:'50% 50%'}}>
  <Street dx={T*14*run}/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <g transform={`translate(${px} 230) scale(1.3)`}><path d="M-120 0H140L170 -20H-100Z" fill="#E8ECF0" strokeWidth={6}/><path d="M-20 -10L40 -80H70L40 -10Z" fill="#C9CED6" strokeWidth={6}/><path d="M-110 -5L-140 -50H-115L-90 -10Z" fill="#C9CED6" strokeWidth={5}/><circle cx={150} cy={-8} r={7} fill={RED} stroke="none" opacity={Math.floor(T/8)%2}/></g>
   <rect x={700} y={520} width={300} height={100} rx={10} fill="#2E4B7A" strokeWidth={7}/><text x={850} y={590} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={60} fill="#FFE07A" stroke="none">환전</text>
  </svg>
  <P3 look="attacker" x={460} y={1720} s={1.45} expr="serious" phase={.2} eye={[-14,0]} pose={(r)=>{const w=Math.sin(ph)*run;r.feet=[[-30-46*w,-18*Math.max(0,w)],[30+46*w,-18*Math.max(0,-w)]];r.hip[1]+=-6*Math.abs(Math.cos(ph))*run;r.torso=-8*run;r.hands=[[-90-30*w,-200+20*w],[60,-150]];r.handProps=[{pose:'fist'},{pose:'grip',anchor:'wrist',side:'left',rot:0,object:BAG}];r.head=-3*run;}}/>
 </AbsoluteFill></AbsoluteFill>;
};
const Plane:React.FC<P>=({t,dur,i})=>{const x=-300+t*26;return <AbsoluteFill><Bg c="#3B6E9A" c2="#8CC0E0"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 {[0,1,2].map(k=><ellipse key={k} cx={((k*420-t*6)%1500+1500)%1500-200} cy={420+k*200} rx={160} ry={50} fill="#FFFFFF" stroke="none" opacity={.8}/>)}
 <g transform={`translate(${x} 760) rotate(-8) scale(2.4)`}><path d="M-120 0H140L170 -20H-100Z" fill="#E8ECF0" strokeWidth={5}/><path d="M-20 -10L40 -80H70L40 -10Z" fill="#C9CED6" strokeWidth={5}/><path d="M-110 -5L-140 -50H-115L-90 -10Z" fill="#C9CED6" strokeWidth={4}/></g>
 <text x={540} y={560} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={110} fill="#FFFFFF" stroke={INK} strokeWidth={10} paintOrder="stroke">필리핀</text>
</svg></Cam></AbsoluteFill>;};
// ---- forge (2026-11-14: laptop smaller and left, man 670 px up so the head clears the subtitle band y1192-1342 under the camera zoom and the figure is >0.4 of frame height; was 0.352 with the head in the band, zzh049 L01): a man at a laptop; a bank balance flips from 23 to 900,000,000 on screen. s = frames from frame 0. ----
export const ForgeStage:React.FC<{s:number}>=({s})=>{
 const T=s+900,flip=s<-8?0:1,glow=s>=2?Math.exp(-(s-2)/10):0;
 const shown=s<-40?'23':s<-8?String(Math.round(23+((s+40)/32)*899999977)).replace(/\B(?=(\d{3})+(?!\d))/g,','):'900,000,000';
 const jit=s>=-8&&s<48?(Math.floor(T/2)%2?6:-6)*Math.exp(-Math.max(0,s)/30):0;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${1.08+.06*Math.sin(s*.08)}) translate(${22*Math.sin(s*.07)+jit}px,${10*Math.sin(s*.05)}px) rotate(${1.2*Math.sin(s*.06)}deg)`,transformOrigin:'50% 45%'}}>
  <Bg c="#1E2230" c2="#34405A"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 1240H1080V1920H0Z" fill="#4A3A30"/><path d="M-20 1220H1100V1270H-20Z" fill="#7A5A44" strokeWidth={8}/>
   <g transform="translate(330 1000) scale(.72)"><rect x={-380} y={-300} width={760} height={470} rx={22} fill="#15171C" strokeWidth={10}/><rect x={-350} y={-270} width={700} height={410} rx={10} fill="#EEF2F5" strokeWidth={4}/>
    <rect x={-350} y={-270} width={700} height={70} fill="#2E6BD8" stroke="none"/><text x={-320} y={-222} fontFamily="Quiet Sans" fontWeight={800} fontSize={40} fill="#FFF" stroke="none">잔액증명서</text>
    <text x={0} y={-110} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={44} fill="#55606A" stroke="none">잔액</text>
    <g transform={`scale(${flip?1+.06*Math.sin(T*.5):1})`}><text x={0} y={10} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={shown.length>6?84:120} fill={flip?RED:INK} stroke="none">₩{shown}</text></g>
    {flip>0&&[0,1,2,3].map(k=><rect key={k} x={-340+((T*37+k*190)%680)} y={-60+k*22} width={70+30*k} height={10} fill={k%2?"#7FE0FF":"#FF5A8A"} stroke="none" opacity={.55}/>)}
    <rect x={-120} y={50} width={240} height={50} rx={8} fill="#C9CED6" stroke="none" opacity={.8}/><text x={0} y={86} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={30} fill={INK} stroke="none">AI 생성 중…</text>
    <path d="M-420 170H420L470 230H-470Z" fill="#2A2D34" strokeWidth={8}/></g>
   {glow>0&&<rect width={W} height={H} fill="#FFE6B0" opacity={.35*glow} stroke="none"/>}
  </svg>
  <P3 look="suit" x={860} y={1500} s={1.25} expr="smug" phase={.2} eye={[-14,-6]} pose={(r)=>{const pt=.5+.5*Math.sin(T*.12);r.hands=[[-230-40*pt,-230-30*pt],[70,-140]];r.handProps=[{pose:"point"},{pose:"relaxed"}];r.head=-4+2*Math.sin(T*.2);r.torso=-4;}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- bank vault: a man in a suit sweeps bundles into a briefcase; a counter racks up to 3,089억. s = frames from frame 0. ----
export const VaultStage:React.FC<{s:number}>=({s})=>{
 const T=s+900,sweep=Math.max(0,Math.sin(T*.35)),n=s<-8?Math.round(3089*clamp01((s+54)/30)):3089;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${1.06+.03*Math.sin(s*.06)}) translate(${10*Math.sin(s*.05)}px,${6*Math.sin(s*.04)}px)`,transformOrigin:'50% 45%'}}>
  <Bg c="#2A3238" c2="#4A5860"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <circle cx={830} cy={700} r={250} fill="#8C9AA4" strokeWidth={12}/><circle cx={830} cy={700} r={190} fill="#6E7C86" strokeWidth={8}/>
   {[0,60,120,180,240,300].map(a=><path key={a} d={`M830 700L${830+170*Math.cos((a+T*2)*Math.PI/180)} ${700+170*Math.sin((a+T*2)*Math.PI/180)}`} strokeWidth={14} stroke="#C9D1D9"/>)}<circle cx={830} cy={700} r={40} fill="#C9D1D9" strokeWidth={8}/>
   {[0,1,2,3].map(k=><g key={k}><rect x={60} y={420+k*130} width={420} height={100} fill="#5A6670" strokeWidth={6}/>{[0,1,2].map(j=><g key={j} transform={`translate(${110+j*130} ${470+k*130})`}><rect x={-50} y={-30} width={100} height={60} fill="#8CC08A" strokeWidth={5}/><path d="M-10 -30V30M10 -30V30" stroke="#F4EBD3" strokeWidth={8}/></g>)}</g>)}
   <path d="M0 1250H1080V1920H0Z" fill="#3A3A40"/><path d="M-20 1220H1100V1270H-20Z" fill="#6A6A72" strokeWidth={8}/>
   <g transform="translate(700 1230)"><path d="M-170 -120H170V0H-170Z" fill="#5A3A26" strokeWidth={8}/><path d="M-60 -120V-150H60V-120" fill="none" strokeWidth={10}/>{[0,1,2].map(j=><g key={j} transform={`translate(${-100+j*100} ${-140-20*Math.sin(T*.35+j)})`}><rect x={-45} y={-26} width={90} height={52} fill="#8CC08A" strokeWidth={5}/></g>)}</g>
   <g opacity={s<-20?1:s<-12?(-12-s)/8:0}><rect x={140} y={170} width={800} height={150} rx={18} fill="#15171C" strokeWidth={8}/><text x={540} y={275} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={96} fill="#7CFF9A" stroke="none">{n.toLocaleString('en-US')}억</text></g>
  </svg>
  <P3 look="suit" x={300} y={2170} s={1.3} expr="smug" phase={.2} eye={[14,-4]} pose={(r)=>{r.hands=[[60+120*sweep,-330+40*sweep],[180+150*sweep,-300+30*sweep]];r.handProps=[{pose:'open'},{pose:'open'}];r.torso=6*sweep;r.head=-3+2*Math.sin(T*.2);}}/>
 </AbsoluteFill></AbsoluteFill>;
};
const Gold:React.FC<P>=({t,dur,i})=>{const shine=(k:number)=>.5+.5*Math.sin(t*.4+k);return <AbsoluteFill><Bg c="#3A2E1A" c2="#7A6230"/><Rays color="#FFE07A" t={t}/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <path d="M0 1150H1080V1920H0Z" fill="#4A3A26"/>
 {[[540,1060],[400,1060],[680,1060],[470,960],[610,960],[540,860]].map(([x,y],k)=><g key={k} transform={`translate(${x} ${y})`} opacity={clamp01((t-2-k*3)/4)}><path d="M-90 0L-70 -70H70L90 0Z" fill="#E8B830" strokeWidth={7}/><path d="M-60 -60H30" stroke="#FFF1A8" strokeWidth={8} opacity={shine(k)}/></g>)}
 <rect x={300} y={520} width={480} height={110} rx={14} fill={PAPER} strokeWidth={7}/><text x={540} y={595} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={64} fill={INK} stroke="none">압수품</text>
</svg></Cam></AbsoluteFill>;};
// ---- soju: night roadside, police lights behind; a young man downs a green soju bottle. s = frames from frame 0. ----
const SOJU=<g stroke="#1E1712" strokeWidth={5} strokeLinejoin="round"><path d="M-22 0V-110Q-22 -130 -10 -140V-175H10V-140Q22 -130 22 -110V0Z" fill="#7FD49A" opacity={.95}/><rect x={-20} y={-95} width={40} height={45} fill="#F4F1E6" strokeWidth={3}/><rect x={-12} y={-190} width={24} height={16} fill="#3A7A4A"/></g>;
export const SojuStage:React.FC<{s:number}>=({s})=>{
 const T=s+900,raise=s<0?kf(s,[[-60,0],[-20,1]]):1,tip=s>=0?.85+.15*Math.sin(s*.25):kf(s,[[-20,0],[-2,.85]]),blink=Math.floor(T/6)%2;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${1.06+.03*Math.sin(s*.06)}) translate(${10*Math.sin(s*.05)}px,${6*Math.sin(s*.04)}px)`,transformOrigin:'50% 45%'}}>
  <Street dx={0}/>
  {/* police tint fades red<->blue (2026-11-14): the hard 6-frame toggle read as a background change every 6 frames (26 of q049's 45, bg rate 79 > 75) */}<AbsoluteFill style={{background:'rgba(60,120,255,.18)',opacity:.5+.5*Math.sin(T*Math.PI/12)}}/><AbsoluteFill style={{background:'rgba(255,60,60,.16)',opacity:.5-.5*Math.sin(T*Math.PI/12)}}/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}><g transform="translate(860 1380) scale(.9)"><path d="M-200 0H200V-120Q160 -200 60 -210H-80Q-170 -200 -200 -120Z" fill="#E8ECF0" strokeWidth={8}/><path d="M-200 -60H200" stroke="#2D4F8C" strokeWidth={26}/><rect x={-80} y={-250} width={160} height={40} rx={10} fill={blink?'#3F7BFF':RED} strokeWidth={6}/><text y={-80} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={44} fill="#2D4F8C" stroke="none">경찰</text><circle cx={-120} cy={10} r={44} fill="#23252B" strokeWidth={7}/><circle cx={120} cy={10} r={44} fill="#23252B" strokeWidth={7}/></g>
   <rect x={60} y={420} width={300} height={110} rx={12} fill="#2E6B3E" strokeWidth={7}/><text x={210} y={495} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={60} fill="#FFF" stroke="none">편의점</text></svg>
  <P3 look="hoodie" x={440} y={1590} s={1.3} expr={s>=-12?'smug':'angry'} phase={.2} eye={[6,-10*tip]} pose={(r)=>{r.hands=[[-90,-200],[230-40*tip,-230-90*raise]];r.handProps=[{pose:'fist'},{pose:'grip',anchor:'wrist',side:'left',rot:-10-35*tip,object:SOJU}];r.head=-8*tip+2*Math.sin(T*.3);r.torso=-6*tip;}}/>
 </AbsoluteFill></AbsoluteFill>;
};
const Chase:React.FC<P>=({t,dur,i})=>{const f=useCurrentFrame(),dx=f*24,sw=Math.sin(t*.5)*60,hit=t>=dur-14,d=t-(dur-14);return <AbsoluteFill><Cam t={t} dur={dur} i={i}><Street dx={dx}/>
 <svg width={W} height={H} style={{position:'absolute'}} {...S}>
  <g transform={`translate(${700+(hit?0:0)} ${1520}) rotate(${hit?Math.min(8,d):0})`}><path d="M0 -150Q10 -200 70 -210H230Q290 -200 310 -150L330 -60V20H0Z" fill="#9FB7C9" strokeWidth={8}/><path d="M50 -150L80 -195H220L260 -150Z" fill="#5D6B7E" strokeWidth={6}/><circle cx={70} cy={30} r={46} fill="#23252B" strokeWidth={7}/><circle cx={270} cy={30} r={46} fill="#23252B" strokeWidth={7}/></g>
  <g transform={`translate(${200+sw} ${1620})`}><path d="M0 -150Q10 -200 70 -210H230Q290 -200 310 -150L330 -60V20H0Z" fill="#C9302C" strokeWidth={8}/><path d="M50 -150L80 -195H220L260 -150Z" fill="#5D6B7E" strokeWidth={6}/><circle cx={70} cy={30} r={46} fill="#23252B" strokeWidth={7}/><circle cx={270} cy={30} r={46} fill="#23252B" strokeWidth={7}/>{[0,1,2].map(k=><path key={k} d={`M${-30-k*40} ${-120+k*30}H${-120-k*40}`} stroke="#FFF" strokeWidth={10} opacity={.7}/>)}</g>
 </svg><Burst x={760} y={1400} t={d} s={1.5}/></Cam></AbsoluteFill>;};
// ---- cab at night: elderly driver at the wheel; the passenger beside him raises a fist (no contact frame). s = frames from frame 0. ----
export const CabStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,raise=s<0?kf(s,[[-50,0],[-10,1]]):1,shake=Math.sin(T*.9)*8*raise,flinch=raise;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(1.06) translate(${3*Math.sin(f*.5)}px,${2*Math.sin(f*.7)}px)`,transformOrigin:'60% 55%'}}>
  <Street dx={T*20}/>
  <Car tilt={0} color="#F2B632" driver={<>{WHEEL(950,1040)}
   <P3 look="driver" x={850} y={1420} s={.85} expr={flinch>.5?'scared':'normal'} phase={.4} eye={[-10*flinch,2]} pose={(r)=>{driverPose(1,0)(r);r.head=-8*flinch;r.torso=4*flinch;}}/>
   <P3 look="D" x={480} y={1420} s={.85} expr="angry" phase={.2} eye={[12,0]} pose={(r)=>{r.hands=[[60,-240],[170+60*raise,-330-170*raise+shake]];r.handProps=[{pose:'relaxed'},{pose:'fist'}];r.torso=6*raise;r.head=3*Math.sin(T*.3);}}/></>}/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}><g transform="translate(700 690)"><rect x={-60} y={-30} width={120} height={50} rx={8} fill="#FFF3C0" strokeWidth={6}/><text y={10} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={34} fill={INK} stroke="none">택시</text></g></svg>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- city bus interior: a drunk passenger stands in the aisle and kicks toward the driver's cabin (no contact frame). ----
export const BusStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,sway=Math.sin(T*.12),kick=s<0?kf(s,[[-40,0],[-8,1]]):.6+.4*Math.max(0,Math.sin(T*.5));
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${8*sway}px,${4*Math.sin(f*.9)}px) rotate(${1.2*sway}deg) scale(1.06)`,transformOrigin:'50% 50%'}}>
  <Bg c="#3A4450" c2="#5E6B78"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1240H0Z" fill="#C9CFD6"/>{[0,1,2].map(k=><rect key={k} x={60+k*340} y={260} width={300} height={360} rx={18} fill="#9FC3D9" strokeWidth={8}/>)}
   {[0,1,2].map(k=><path key={k} d={`M${((k*360-T*18)%1300+1300)%1300-200} 360h160`} stroke="#FFFFFF" strokeWidth={14} opacity={.6}/>)}
   <path d="M0 140H1080" stroke="#8A9098" strokeWidth={16}/>{[220,520,820].map(x=><g key={x}><path d={`M${x} 140V${230+10*Math.sin(f*.2+x)}`} strokeWidth={6}/><circle cx={x} cy={250+10*Math.sin(f*.2+x)} r={22} fill="none" strokeWidth={8}/></g>)}
   <path d="M0 1240H1080V1920H0Z" fill="#5A5F66"/><path d="M0 1240H1080" strokeWidth={9}/>
   <rect x={720} y={700} width={360} height={560} fill="#2E4B7A" strokeWidth={8}/><rect x={760} y={740} width={280} height={180} fill="#9FC3D9" strokeWidth={6}/>
   <ellipse cx={900} cy={1060} rx={80} ry={80} fill="none" stroke="#1E1E22" strokeWidth={18}/>
  </svg>
  <P3 look="driver" x={900} y={1500} s={.9} expr={kick>.7?'scared':'concern'} phase={.4} eye={[-12,0]} pose={(r)=>{r.hands=[[-60,-330],[40,-330]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.head=-5*kick;}}/>
  <P3 look="official" x={380} y={1540} s={1.3} expr="angry" phase={.2} eye={[14,2]} pose={(r)=>{r.feet[1]=[40+170*kick,-40-130*kick];r.torso=-6+8*kick;r.hands=[[-160,-420],[100,-300]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.head=4*sway;}} ik={{knee:[[-.3,-1],[.6,-1]]}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- 4:25 a.m. street: a man in a hoodie points and squares up at a passer-by who backs away. No blow is drawn. ----
export const GlareStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,step=s<0?kf(s,[[-70,.3],[-20,1]]):1,jab=.5+.5*Math.sin(T*.42),fl=Math.floor(T/5)%11===6?.75:1;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${10*Math.sin(s*.05)}px,${5*Math.sin(s*.04)}px) rotate(${.8*Math.sin(s*.03)}deg) scale(${1.07+.03*Math.sin(s*.045)})`,transformOrigin:'50% 55%'}}>
  <Bg c="#121A2C" c2="#26324C"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1280H0Z" fill="#1A2238"/>
   <path d="M40 1280V320H520V1280Z" fill="#2B3450" strokeWidth={8}/>{Array.from({length:18}).map((_,k)=>{const x=90+(k%4)*110,y=380+Math.floor(k/4)*170,on=(k*7+3)%5<2;return <rect key={k} x={x} y={y} width={70} height={90} fill={on?'#F2D27A':'#3A4462'} opacity={on?.75+.25*Math.sin(T*.07+k):1} strokeWidth={5}/>;})}
   <path d="M600 1280V560H1040V1280Z" fill="#232B44" strokeWidth={8}/>{Array.from({length:8}).map((_,k)=><rect key={k} x={650+(k%3)*120} y={620+Math.floor(k/3)*190} width={70} height={90} fill={k===4?'#F2D27A':'#3A4462'} opacity={k===4?.8:1} strokeWidth={5}/>)}
   <path d="M560 1290V420" stroke="#4A4F5C" strokeWidth={22}/><path d="M560 430H660" stroke="#4A4F5C" strokeWidth={16}/><ellipse cx={660} cy={445} rx={46} ry={18} fill="#FFF2C0" opacity={fl}/>
   <path d={`M630 455L${380} 1600H${960}L690 455Z`} fill="#FFF2C0" stroke="none" opacity={.16*fl}/>
   <path d="M0 1280H1080V1920H0Z" fill="#30364A"/><path d="M0 1280H1080" strokeWidth={9}/>
   {[0,1,2,3].map(k=><path key={k} d={`M${((k*330-T*2)%1400+1400)%1400-160} 1700h150`} stroke="#5A6078" strokeWidth={10}/>)}
  </svg>
  <P3 look="passenger" x={830} y={1440} s={.95} expr={jab>.6?'scared':'concern'} phase={.5} eye={[-14,0]} pose={(r)=>{r.torso=6+4*jab;r.hands=[[-120,-260],[30,-240]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=6;r.feet=[[-40-20*jab,0],[40,0]];}}/>
  <P3 look="hoodie" x={-60+390*step} y={1640} s={1.12} expr="angry" phase={.2} eye={[16,0]} pose={(r)=>{r.torso=-4-5*jab;r.hands=[[-120,-190],[200+50*jab,-250-20*jab]];r.handProps=[{pose:'fist'},{pose:'point'}];r.head=-4+3*jab;r.feet=[[-40,0],[50+20*jab,0]];}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- bus doorway at dusk: an old passenger on the steps argues with a young driver; silhouettes of riders watch. Words only, no contact. ----
export const BusArgueStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,talk=.5+.5*Math.sin(T*.55),pop=s<0?kf(s,[[-60,.4],[-20,1]]):1,burst=.85+.15*Math.sin(T*.9);
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${9*Math.sin(s*.05)}px,${4*Math.sin(f*.7)}px) rotate(${.7*Math.sin(s*.04)}deg) scale(${1.06+.03*Math.sin(s*.045)})`,transformOrigin:'50% 55%'}}>
  <Bg c="#2C3346" c2="#4A5470"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1260H0Z" fill="#C7CCD4"/>
   {[0,1].map(k=><rect key={k} x={560+k*250} y={300} width={220} height={330} rx={16} fill="#E8A26A" strokeWidth={8}/>)}
   {[0,1].map(k=><path key={k} d={`M${560+k*250+((T*3+k*90)%200)} 420h40`} stroke="#FFE2B8" strokeWidth={10} opacity={.7}/>)}
   <path d="M0 140H1080" stroke="#8A9098" strokeWidth={16}/>{[640,880].map(x=><g key={x}><path d={`M${x} 140V${230+10*Math.sin(f*.2+x)}`} strokeWidth={6}/><circle cx={x} cy={250+10*Math.sin(f*.2+x)} r={22} fill="none" strokeWidth={8}/></g>)}
   {[0,1,2].map(k=><g key={k} opacity={.55}><circle cx={640+k*150} cy={860+6*Math.sin(T*.1+k)} r={40} fill="#5A6070" stroke="none"/><path d={`M${590+k*150} 1000Q${640+k*150} 900 ${690+k*150} 1000V1080H${590+k*150}Z`} fill="#5A6070" stroke="none"/></g>)}
   <rect x={20} y={300} width={300} height={960} fill="#2E4B7A" strokeWidth={8}/><path d="M20 1060H330M20 1160H360M20 1260H400" stroke="#1E1E22" strokeWidth={10}/>
   <path d="M0 1260H1080V1920H0Z" fill="#5A5F66"/><path d="M0 1260H1080" strokeWidth={9}/>
   <rect x={760} y={1080} width={240} height={180} rx={10} fill="#3A3F48" strokeWidth={6}/><ellipse cx={880} cy={1060} rx={90} ry={90} fill="none" stroke="#1E1E22" strokeWidth={18}/>
   <g transform={`translate(600 ${560-10*talk}) scale(${.8*pop*burst})`} opacity={pop}><path d="M-170 -80L-120 -130L-60 -95L0 -150L60 -100L130 -140L160 -70L210 -40L150 10L180 80L90 60L40 120L-20 70L-100 110L-120 40L-200 20Z" fill="#FFD45A" strokeWidth={8}/><text y={20} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={900} fontSize={84} fill="#C9302C" stroke="none">#@%!</text></g>
  </svg>
  <P3 look="passenger" x={880} y={1440} s={.9} expr={talk>.6?'angry':'concern'} phase={.4} eye={[-14,0]} pose={(r)=>{r.hands=[[-170,-220],[110,-200]];r.handProps=[{pose:'open'},{pose:'fist'}];r.head=-4*talk;}}/>
  <P3 look="prof" x={330} y={1500} s={1.1} expr="angry" phase={.2} eye={[14,0]} pose={(r)=>{r.torso=-3-4*talk;r.hands=[[-120,-200],[180+40*talk,-300-30*talk]];r.handProps=[{pose:'fist'},{pose:'point'}];r.head=-3+4*talk;r.feet=[[-40,0],[50,-40]];}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- night office: an admin worker at a desk keeps clicking "pay" with a corporate card; gift vouchers stream out, a counter climbs. ----
const VOUCHER=(k:number,x:number,y:number,r:number,o:number)=><g key={k} transform={`translate(${x} ${y}) rotate(${r})`} opacity={o}><rect x={-80} y={-44} width={160} height={88} rx={8} fill="#F4E3B0" strokeWidth={6}/><rect x={-64} y={-30} width={46} height={60} rx={4} fill="#E06A4E" strokeWidth={4}/><text x={22} y={12} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={34} fill="#5A3A1A" stroke="none">상품권</text></g>;
export const VoucherStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,tap=Math.max(0,Math.sin(T*.6)),n=s<0?Math.round(kf(s,[[-80,1],[-10,6332]])):Math.min(6332,Math.round(4800+s*40));
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${10*Math.sin(s*.05)}px,${5*Math.sin(s*.04)}px) rotate(${.6*Math.sin(s*.035)}deg) scale(${1.06+.03*Math.sin(s*.045)})`,transformOrigin:'50% 50%'}}>
  <Bg c="#1C2236" c2="#323C5C"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1300H0Z" fill="#2A3048"/>
   <rect x={600} y={180} width={400} height={300} rx={10} fill="#1E2438" strokeWidth={8}/>{[0,1,2].map(k=><rect key={k} x={630+k*125} y={210} width={105} height={240} fill="#3A4466" strokeWidth={4}/>)}
   <rect x={520} y={680} width={420} height={300} rx={16} fill="#3A4252" strokeWidth={8}/><rect x={545} y={705} width={370} height={230} rx={8} fill={tap>.8?'#9FE3B0':'#BFD8F0'} strokeWidth={5}/>
   <text x={730} y={795} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={46} fill="#1E2A3A" stroke="none">{tap>.8?'결제 완료':'결제하기'}</text>
   <text x={730} y={890} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={900} fontSize={62} fill="#C9302C" stroke="none">{n.toLocaleString('en-US')}회</text>
   <path d="M700 980L690 1000H770L760 980Z" fill="#3A4252" strokeWidth={6}/>
   <path d="M0 1000H1080V1060H0Z" fill="#7A5A44" strokeWidth={8}/><path d="M0 1060H1080V1920H0Z" fill="#232838"/>
   {Array.from({length:7}).map((_,k)=>{const u=((T*.018+k/7)%1),x=960+60*u+30*Math.sin(k*2.1),y=980-900*u+30*Math.sin(T*.1+k);return VOUCHER(k,x,y,-25+50*Math.sin(k*1.7+T*.05),u<.85?1:(1-u)/.15);})}
  </svg>
  <P3 look="woman" x={300} y={1640} s={1.2} expr="smug" phase={.2} eye={[16,-4]} pose={(r)=>{r.torso=-3;r.hands=[[-120,-220],[250,-330+25*tap]];r.handProps=[{pose:'relaxed'},{pose:'point'}];r.head=2*Math.sin(T*.1);}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- bank counter: a banker behind the teller window holds a customer's passbook and seal; stacks of cash slide into his own drawer. Customer never shown. ----
export const BankStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,stamp=Math.max(0,Math.sin(T*.35)),slide=(T*.02)%1;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${10*Math.sin(s*.05)}px,${5*Math.sin(s*.04)}px) rotate(${.6*Math.sin(s*.035)}deg) scale(${1.06+.03*Math.sin(s*.045)})`,transformOrigin:'50% 50%'}}>
  <Bg c="#20343A" c2="#3C5A60"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1240H0Z" fill="#D9DED6"/>
   <rect x={80} y={480} width={480} height={100} rx={10} fill="#1F6E6A" strokeWidth={8}/><text x={320} y={552} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={56} fill="#F4F1E6" stroke="none">기업금융 창구</text>
   <rect x={640} y={620} width={340} height={200} rx={10} fill="#2A2F3A" strokeWidth={8}/><text x={810} y={700} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={44} fill="#9FE3B0" stroke="none">대출 실행</text><text x={810} y={770} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={900} fontSize={52} fill="#FFD45A" stroke="none">{(s<0?2:3)}억 원</text>
   <path d="M0 1080H1080V1240H0Z" fill="#8A6A4E" strokeWidth={8}/><path d="M0 1240H1080V1920H0Z" fill="#3A4048"/>
   <g transform="translate(820 1040)"><rect x={-110} y={-70} width={150} height={100} rx={8} fill="#2E6FB0" strokeWidth={6}/><text x={-35} y={-8} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={34} fill="#F4F1E6" stroke="none">통장</text>
    <g transform={`translate(110 ${-60-50*stamp})`}><rect x={-22} y={-70} width={44} height={70} rx={10} fill="#C9302C" strokeWidth={6}/><rect x={-34} y={0} width={68} height={22} rx={4} fill="#8A1E1A" strokeWidth={5}/></g>
    {stamp>.9&&<circle cx={110} cy={-30} r={26} fill="none" stroke="#C9302C" strokeWidth={6}/>}</g>
   {[0,1,2].map(k=>{const u=(slide+k/3)%1,x=760-560*u,y=1000+40*Math.sin(u*3.14);return <g key={k} transform={`translate(${x} ${y})`} opacity={u<.9?1:(1-u)*10}>{[0,1].map(j=><path key={j} d={`M-70 ${-30-j*16}H70V${0-j*16}H-70Z`} fill="#8CC08A" strokeWidth={4}/>)}<path d="M-10 -66V0M10 -66V0" stroke="#F4EBD3" strokeWidth={8}/></g>;})}
   <rect x={20} y={1090} width={220} height={130} rx={8} fill="#6A4E38" strokeWidth={6}/><path d="M60 1150H200" strokeWidth={8}/>
  </svg>
  <P3 look="suit" x={360} y={1560} s={1.2} expr="smug" phase={.2} eye={[18,-4]} pose={(r)=>{r.torso=-2;r.hands=[[-170,-260],[240,-360+30*stamp]];r.handProps=[{pose:'open'},{pose:'fist'}];r.head=3*Math.sin(T*.08);}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- closed factory gate at dusk: silhouettes of workers with blank-faced protest signs behind the bars; an executive in front waves it away. No logos. ----
export const FactoryStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,wave=Math.sin(T*.4),bob=(k:number)=>22*Math.sin(T*.32+k*1.3);
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${24*Math.sin(s*.07)}px,${10*Math.sin(s*.05)}px) rotate(${1.1*Math.sin(s*.05)}deg) scale(${1.08+.05*Math.sin(s*.06)})`,transformOrigin:'50% 50%'}}>
  <Bg c="#3A2E3A" c2="#6A4E58"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <defs><linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#5A4A6E"/><stop offset="1" stopColor="#E89A6A"/></linearGradient></defs>
   <rect width={W} height={1240} fill="url(#dusk)" stroke="none"/>
   <path d="M80 1240V560L280 470V560L480 470V560L680 470V560H1000V1240Z" fill="#4A4652" strokeWidth={8}/><rect x={820} y={460} width={60} height={100} fill="#4A4652" strokeWidth={8}/>
   {[0,1,2,3,4].map(k=>{const x=170+k*180,y=1030+bob(k);return <g key={k} opacity={.75}><circle cx={x} cy={y-120} r={36} fill="#2A2630" stroke="none"/><path d={`M${x-46} ${y+40}Q${x} ${y-110} ${x+46} ${y+40}Z`} fill="#2A2630" stroke="none"/><g transform={`translate(${x} ${y-250+bob(k+2)}) rotate(${8*Math.sin(T*.3+k)})`}><path d="M0 60V130" stroke="#6A5A48" strokeWidth={8}/><rect x={-70} y={-10} width={140} height={74} rx={6} fill="#F4F1E6" strokeWidth={5}/><text y={40} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={900} fontSize={34} fill="#C9302C" stroke="none">{['임금','퇴직금','임금','체불','퇴직금'][k]}</text></g></g>;})}
   {Array.from({length:12}).map((_,k)=><path key={k} d={`M${60+k*88} 760V1240`} stroke="#2A2E36" strokeWidth={14}/>)}<path d="M40 800H1040M40 1200H1040" stroke="#2A2E36" strokeWidth={16}/>
   <path d="M0 1240H1080V1920H0Z" fill="#3A3640"/><path d="M0 1240H1080" strokeWidth={9}/>
  </svg>
  <P3 look="chair" x={560} y={1900} s={2.0} expr="smug" phase={.2} eye={[-8,0]} pose={(r)=>{r.torso=2*wave;r.hands=[[-170,-170+20*wave],[150,-160]];r.handProps=[{pose:'open'},{pose:'relaxed'}];r.head=-4+4*wave;}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- office meeting room: a senior executive slams the table and pushes a "resignation pledge" sheet at a junior employee. Words only, no blows. ----
export const PledgeStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,slam=Math.max(0,Math.sin(T*.45)),push=s<0?kf(s,[[-70,0],[-20,1]]):1;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${(slam>.9?6:0)*Math.sin(f*3)+16*Math.sin(s*.06)}px,${8*Math.sin(s*.05)}px) rotate(${.8*Math.sin(s*.04)}deg) scale(${1.07+.04*Math.sin(s*.05)})`,transformOrigin:'50% 55%'}}>
  <Bg c="#2A3340" c2="#46566A"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1240H0Z" fill="#CFC8BC"/>
   <rect x={600} y={500} width={380} height={300} rx={10} fill="#E8EEF2" strokeWidth={8}/>{[0,1,2].map(k=><path key={k} d={`M640 ${570+k*70}H${700+((T*4+k*60)%240)}`} stroke="#8A9AAA" strokeWidth={14}/>)}
   <rect x={90} y={520} width={300} height={200} rx={10} fill="#7A8A6A" strokeWidth={8}/><path d="M120 680L190 600L250 650L300 590L360 680Z" fill="#5A6A4A" strokeWidth={5}/>
   <path d="M0 1120H1080V1240H0Z" fill="#6A4E38" strokeWidth={8}/><path d="M0 1240H1080V1920H0Z" fill="#3A4048"/>
   <g transform={`translate(${640+160*push} ${940+10*Math.sin(T*.3)}) rotate(${-8+4*Math.sin(T*.2)}) scale(1.35)`}><rect x={-110} y={-70} width={220} height={140} rx={6} fill="#FFFFFF" strokeWidth={6}/><text y={-14} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={900} fontSize={42} fill={INK} stroke="none">사직 각서</text><path d="M-80 26H80M-80 50H40" stroke="#B4A58C" strokeWidth={6}/></g>
   <g transform={`translate(860 ${580-12*slam}) scale(${.7+.2*slam})`} opacity={.4+.6*slam}><path d="M-120 -60L-80 -100L-30 -70L20 -110L70 -70L120 -95L130 -30L170 0L120 30L130 90L60 70L20 110L-30 70L-90 95L-100 30L-150 10Z" fill="#FFD45A" strokeWidth={7}/><text y={20} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={900} fontSize={70} fill="#C9302C" stroke="none">#@%!</text></g>
  </svg>
  <P3 look="passenger" x={900} y={2330} s={1.25} expr={slam>.6?'scared':'concern'} phase={.5} eye={[-14,0]} pose={(r)=>{r.torso=5+3*slam;r.hands=[[-150,-230],[40,-220]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=5;}}/>
  <P3 look="official" x={360} y={1900} s={2.0} expr="angry" phase={.2} eye={[16,0]} pose={(r)=>{r.torso=-4-5*slam;r.hands=[[-130,-170],[170,-150+40*slam]];r.handProps=[{pose:'fist'},{pose:'open'}];r.head=-3+4*slam;}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- night backyard (grave): an empty wire trap with a fish plate and an unlit gas torch on a stool. No animal and no flame are ever shown. ----
export const YardStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,sway=Math.sin(T*.06);
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${14*Math.sin(s*.05)}px,${7*Math.sin(s*.04)}px) rotate(${.7*Math.sin(s*.035)}deg) scale(${1.07+.04*Math.sin(s*.05)})`,transformOrigin:'50% 50%'}}>
  <Bg c="#141A26" c2="#2A3448"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <rect width={W} height={1240} fill="#1E2638" stroke="none"/><circle cx={900} cy={560} r={46} fill="#E8E4D0" stroke="none" opacity={.8}/>
   {Array.from({length:9}).map((_,k)=><path key={k} d={`M${40+k*125} 1240V${760+10*Math.sin(k)}`} stroke="#4A3A2C" strokeWidth={34}/>)}<path d="M0 840H1080M0 1080H1080" stroke="#3A2E24" strokeWidth={18}/>
   {[0,1,2].map(k=><path key={k} d={`M${600+k*140} 1240q${10*sway} -60 ${20+8*sway} -120`} stroke="#3E5A3A" strokeWidth={10} fill="none"/>)}
   <path d="M0 1240H1080V1920H0Z" fill="#2E3426"/><path d="M0 1240H1080" strokeWidth={9}/>
   <g transform="translate(790 1000) scale(1.25)"><rect x={-170} y={-120} width={340} height={170} fill="none" stroke="#9AA3AE" strokeWidth={8}/>{Array.from({length:8}).map((_,k)=><path key={k} d={`M${-170+k*48} -120V50`} stroke="#9AA3AE" strokeWidth={4}/>)}{[0,1,2].map(k=><path key={k} d={`M-170 ${-80+k*45}H170`} stroke="#9AA3AE" strokeWidth={4}/>)}<path d={`M170 -120L${230+6*sway} -40`} stroke="#9AA3AE" strokeWidth={8}/><ellipse cx={40} cy={30} rx={60} ry={14} fill="#D8D4C8" strokeWidth={5}/><path d="M10 26q30 -14 60 0l10 -8v16z" fill="#8AA0B0" strokeWidth={4}/></g>
   <g transform="translate(940 640) scale(1.3)"><rect x={-60} y={0} width={120} height={20} fill="#6A4E38" strokeWidth={6}/><path d="M-50 20V120M50 20V120" stroke="#6A4E38" strokeWidth={10}/><rect x={-20} y={-90} width={40} height={90} rx={8} fill="#C9302C" strokeWidth={5}/><path d="M-6 -90V-120H30" stroke="#555" strokeWidth={10} fill="none"/></g>
  </svg>
  <P3 look="driver" x={300} y={1800} s={1.75} expr="serious" phase={.2} eye={[14,0]} pose={(r)=>{r.torso=2*sway;r.hands=[[-160,-150],[150,-150]];r.handProps=[{pose:'relaxed'},{pose:'relaxed'}];r.head=-2+3*sway;}}/>
 </AbsoluteFill></AbsoluteFill>;
};
const PHONE_IN_HAND=<g stroke="#1E1712" strokeWidth={5}><rect x={-26} y={-90} width={52} height={96} rx={10} fill="#2A2F3A"/><rect x={-18} y={-80} width={36} height={70} rx={4} fill="#9FC3D9"/></g>;
// ---- holiday living room: a middle-aged son yells into a phone, a towel round his neck; his elderly mother reaches out to stop him. No blow is drawn. ----
export const HolidayStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,yell=.5+.5*Math.sin(T*.5),fan=(T*.6)%(Math.PI*2);
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${14*Math.sin(s*.06)}px,${7*Math.sin(s*.05)}px) rotate(${.8*Math.sin(s*.04)}deg) scale(${1.07+.04*Math.sin(s*.05)})`,transformOrigin:'50% 50%'}}>
  <Bg c="#3A2E26" c2="#6A5442"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1240H0Z" fill="#E6D6B8"/>{Array.from({length:6}).map((_,k)=><path key={k} d={`M${k*200} 0V1240`} stroke="#D8C6A4" strokeWidth={6}/>)}
   <rect x={640} y={520} width={300} height={220} rx={8} fill="#F4EBD3" strokeWidth={8}/><text x={790} y={650} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={900} fontSize={60} fill="#C9302C" stroke="none">추석</text>
   <g transform="translate(980 1060)"><path d="M0 160V20" stroke="#555" strokeWidth={14}/><circle cy={0} r={78} fill="none" stroke="#7A8A9A" strokeWidth={10}/>{[0,1,2].map(k=><path key={k} d={`M0 0L${60*Math.cos(fan+k*2.09)} ${60*Math.sin(fan+k*2.09)}`} stroke="#9AB0C4" strokeWidth={16}/>)}</g>
   <path d="M0 1240H1080V1920H0Z" fill="#8A6A4E"/><path d="M0 1240H1080" strokeWidth={9}/>
   <g transform="translate(560 1330)"><rect x={-220} y={-30} width={440} height={60} rx={10} fill="#6A4E38" strokeWidth={6}/><g transform={`translate(260 -560) rotate(${-6+2*Math.sin(T*.2)}) scale(1.3)`}><rect x={-80} y={-44} width={160} height={88} rx={6} fill="#FFFFFF" strokeWidth={6}/><text y={14} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={900} fontSize={40} fill={INK} stroke="none">5만 원</text></g></g>
  </svg>
  <P3 look="granny" x={860} y={2120} s={1.0} expr="scared" phase={.5} eye={[-14,0]} pose={(r)=>{r.torso=-6;r.hands=[[-220,-300+20*yell],[-60,-220]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=-4;}}/>
  <P3 look="attacker" x={330} y={1800} s={1.75} expr="angry" phase={.2} eye={[14,0]} talk pose={(r)=>{r.torso=-3-4*yell;r.hands=[[-150,-160],[120,-430+20*yell]];r.handProps=[{pose:'fist'},{pose:'grip',anchor:'wrist',side:'left',rot:0,object:PHONE_IN_HAND}];r.head=-4+5*yell;}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- salt field: workers seen only from behind as small distant silhouettes raking salt; dawn-to-night sky; a clock races. ----
const SaltField:React.FC<{T:number;night:number}>=({T,night})=><svg width={W} height={H} style={{position:'absolute'}} {...S}>
 <defs><linearGradient id="saltsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={night>.5?'#1E2440':'#F2B66A'}/><stop offset="1" stopColor={night>.5?'#3A4466':'#F7E2B8'}/></linearGradient></defs>
 <rect width={W} height={760} fill="url(#saltsky)" stroke="none"/><circle cx={820} cy={night>.5?260:420} r={70} fill={night>.5?'#F4F1E6':'#FFD45A'} stroke="none"/>
 <path d="M0 760H1080V1920H0Z" fill="#C9D3D8"/>{[0,1,2,3,4,5].map(k=><path key={k} d={`M0 ${820+k*170}H1080`} stroke="#8EA0AA" strokeWidth={8}/>)}
 {[0,1,2,3].map(k=>{const x=180+k*240,y=820+(k%2)*80;return <path key={k} d={`M${x-60} ${y+40}L${x} ${y-30}L${x+60} ${y+40}Z`} fill="#F7F7F2" strokeWidth={6}/>;})}
 {[0,1,2,3,4].map(k=><path key={'h'+k} d={`M${(k*260+T*3)%1300-160} ${560+k*38}q40 -14 80 0t80 0t80 0`} stroke="#FFF4D8" strokeWidth={5} fill="none" opacity={.45+.3*Math.sin(T*.2+k)}/>)}
 {[0,1,2,3,4,5,6,7].map(k=>{const g=.5+.5*Math.sin(T*.3+k*1.9);return <path key={'g'+k} d={`M${120+k*120} ${880+(k%3)*230}l0 ${-24*g}M${108+k*120} ${868+(k%3)*230}h${24*g}`} stroke="#FFFFFF" strokeWidth={6} opacity={g}/>;})}
 {[0,1,2].map(k=>{const x=250+k*290+24*Math.sin(T*.07+k*2),y=1000+k*60+6*Math.sin(T*.35+k),r=Math.sin(T*.35+k)*30,lean=4*Math.sin(T*.35+k);return <g key={k} transform={`translate(${x} ${y}) rotate(${lean})`} opacity={.92}><circle cy={-120} r={28} fill="#3A3F48" stroke="none"/><path d="M-30 -92H30L36 20H-36Z" fill="#3A3F48" stroke="none"/><path d={`M20 -60L${80+r} ${30}`} stroke="#6A5A48" strokeWidth={9}/><path d={`M${60+r} 30H${110+r}`} stroke="#6A5A48" strokeWidth={9}/></g>;})}
</svg>;
export const SaltStage:React.FC<{s:number}>=({s})=>{
 const T=s+900,h=s<0?Math.min(17,Math.max(0,(s+90)/80*17)):17,night=s<-40?0:1;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${1.06+.03*Math.sin(s*.05)}) translate(${12*Math.sin(s*.04)}px,${6*Math.sin(s*.035)}px)`,transformOrigin:'50% 50%'}}>
  <SaltField T={T} night={night}/>
  <Watch x={540} y={1560} s={1.25} sec={((h%1)||(s>=0?.999:0))*180}/>
  <div style={{...type,position:'absolute',left:340,top:1700,width:400,fontSize:90,color:GOLD}}>{Math.floor(h)}시간</div>
 </AbsoluteFill></AbsoluteFill>;
};
const SaltWork:React.FC<P>=({t,dur,i})=><AbsoluteFill><Cam t={t} dur={dur} i={i}><AbsoluteFill style={{transform:`translate(${18*Math.sin(t*.06)}px,${10*Math.sin(t*.05)}px) scale(${1.05+.03*Math.sin(t*.04)})`}}><SaltField T={t} night={0}/></AbsoluteFill></Cam></AbsoluteFill>;
// ---- print shop: stacks of paper and a press; a man in a suit stands at the doorway holding an IOU ledger. Victim never shown. ----
const LEDGER=<g stroke="#1E1712" strokeWidth={5} strokeLinejoin="round"><rect x={-50} y={-130} width={100} height={120} rx={6} fill="#C9302C"/><path d="M-30 -100H30M-30 -75H30M-30 -50H20" stroke="#F4EBD3" strokeWidth={6}/></g>;
export const PrintStage:React.FC<{s:number}>=({s})=>{
 const T=s+900,enter=s<0?kf(s,[[-70,.55],[-25,1]]):1,flick=Math.floor(T/4)%9===4?.8:1,roll=(T*6)%200;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${1.06+.03*Math.sin(s*.05)}) translate(${12*Math.sin(s*.045)}px,${6*Math.sin(s*.035)}px)`,transformOrigin:'50% 45%',filter:`brightness(${flick})`}}>
  <Bg c="#3E3A36" c2="#6A625A"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1260H0Z" fill="#8C857A"/><rect x={80} y={470} width={300} height={90} rx={8} fill="#2E2A26" strokeWidth={6}/><text x={230} y={530} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={56} fill="#F4EBD3" stroke="none">인쇄소</text>
   <g transform="translate(760 900)"><rect x={-220} y={-260} width={440} height={300} rx={20} fill="#5A6070" strokeWidth={8}/><circle cx={-90} cy={-110} r={70} fill="#9AA0A8" strokeWidth={7}/><path d={`M-90 -110L${-90+60*Math.cos(roll/30)} ${-110+60*Math.sin(roll/30)}`} strokeWidth={8}/>
    <path d={`M-200 40H200V${60+roll*.3}H-200Z`} fill="#F4F1E6" strokeWidth={5}/></g>
   {[0,1,2].map(k=><rect key={k} x={90+k*20} y={1000-k*70} width={260} height={70} fill="#F4F1E6" strokeWidth={5}/>)}
   <path d="M0 1260H1080V1920H0Z" fill="#5A524A"/><path d="M0 1260H1080" strokeWidth={9}/>
  </svg>
  <P3 look="suit" x={-100+520*enter} y={1640} s={1.3} expr="serious" phase={.2} eye={[14,0]} pose={(r)=>{const w=Math.sin(T*.3)*(1-enter);r.feet=[[-30-30*w,0],[30+30*w,0]];r.hands=[[-80,-160],[110,-300]];r.handProps=[{pose:'fist'},{pose:'grip',anchor:'wrist',side:'left',rot:0,object:LEDGER}];r.head=-2;}}/>
 </AbsoluteFill></AbsoluteFill>;
};
const Receipt:React.FC<P>=({t,dur,i})=>{const a=kf(t,[[0,.6],[8,1]]);return <AbsoluteFill><Bg c="#22263A" c2="#3C4470"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <g transform={`translate(540 ${760-60*(1-a)}) rotate(${-4+2*Math.sin(t*.1)})`} opacity={a}><path d="M-230 -360H230V360L190 330L150 360L110 330L70 360L30 330L-10 360L-50 330L-90 360L-130 330L-170 360L-230 330Z" fill="#FFFFFF" strokeWidth={8}/>
  <text y={-260} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={56} fill={INK} stroke="none">영수증</text>
  <text y={-160} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={44} fill="#55606A" stroke="none">5월 22일 오전</text>
  <path d="M-180 -110H180" stroke="#B4A58C" strokeWidth={5} strokeDasharray="12 10"/>
  <text x={-180} y={-30} fontFamily="Quiet Sans" fontWeight={800} fontSize={60} fill={INK} stroke="none">과도</text><text x={180} y={-30} textAnchor="end" fontFamily="Quiet Sans" fontWeight={800} fontSize={60} fill={INK} stroke="none">1</text>
  <path d="M-180 40H180" stroke="#B4A58C" strokeWidth={5} strokeDasharray="12 10"/></g>
</svg></Cam></AbsoluteFill>;};
// ---- en001 living room: a woman holds up an ultrasound print toward a stunned man; a red FAKE stamp flickers on the print. ----
const SCAN=<g stroke="#1E1712" strokeWidth={5} strokeLinejoin="round"><rect x={-95} y={-190} width={190} height={150} rx={8} fill="#111"/><path d="M0 -180L-70 -60H70Z" fill="#555" stroke="none"/><ellipse cx={-18} cy={-95} rx={16} ry={11} fill="#BBB" stroke="none"/><ellipse cx={22} cy={-88} rx={16} ry={11} fill="#BBB" stroke="none"/></g>;
// layout 2026-11-13: heads end above the subtitle band (y 1192) and the print sits above the heads, below the hook band
export const ScanStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,lift=s<0?kf(s,[[-60,.2],[-18,1]]):1,shake=.5+.5*Math.sin(T*.5),fake=Math.floor(T/9)%3!==0;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${10*Math.sin(s*.05)}px,${5*Math.sin(s*.04)}px) rotate(${.7*Math.sin(s*.03)}deg) scale(${1.07+.03*Math.sin(s*.045)})`,transformOrigin:'50% 55%'}}>
  <Bg c="#5A4A5E" c2="#8A7090"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1260H0Z" fill="#C9B8C4"/><rect x={90} y={300} width={360} height={460} rx={10} fill="#9FC3D9" strokeWidth={8}/><path d="M270 300V760M90 530H450" strokeWidth={6}/>
   <rect x={640} y={340} width={300} height={220} rx={8} fill="#F4EBD3" strokeWidth={7}/><path d="M680 420Q790 360 900 440" fill="none" stroke="#C98A3E" strokeWidth={10}/>
   <path d="M0 1260H1080V1920H0Z" fill="#7A6070"/><path d="M0 1260H1080" strokeWidth={9}/>
  </svg>
  <P3 look="passenger" x={820} y={1470} s={1.05} expr={shake>.5?'shock':'scared'} phase={.5} eye={[-14,-4]} pose={(r)=>{r.torso=-5-3*shake;r.hands=[[-150,-330-30*shake],[120,-200]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=-5;}}/>
  <P3 look="lady" x={300} y={1470} s={1.05} expr="smug" phase={.2} eye={[10,-10]} pose={(r)=>{r.torso=3;r.hands=[[-80,-170],[150,-330-60*lift]];r.handProps=[{pose:'relaxed'},{pose:'point'}];r.head=-3+2*Math.sin(T*.2);}}/>
  <svg width={W} height={H} style={{position:'absolute'}}><g transform={`translate(540 ${540+30*(1-lift)}) rotate(${-4+2*Math.sin(T*.15)}) scale(${.72*(.9+.1*lift)})`}>
   <rect x={-190} y={-150} width={380} height={290} rx={10} fill="#F4F4F0" stroke={INK} strokeWidth={8}/><rect x={-165} y={-125} width={330} height={210} fill="#111" stroke="none"/>
   <path d="M0 -115L-130 75H130Z" fill="#4A4A4A"/><ellipse cx={-35} cy={-5} rx={30} ry={20} fill="#C8C8C8"/><ellipse cx={40} cy={10} rx={30} ry={20} fill="#C8C8C8"/>
   <text x={-150} y={120} fontFamily="Quiet Sans" fontWeight={800} fontSize={36} fill={INK}>ULTRASOUND</text>
   {fake&&s>-30&&<g transform={`rotate(-14) scale(${1+.06*Math.sin(T*.6)})`}><rect x={-140} y={-58} width={280} height={116} rx={14} fill="none" stroke={RED} strokeWidth={13}/><text y={36} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={96} fill={RED}>FAKE</text></g>}
  </g></svg>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- en002 streamer room: LIVE monitor, chat floods "STOP"; the streamer glares down off-frame. The animal is never shown. ----
export const StreamStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,turn=s<0?kf(s,[[-60,0],[-15,1]]):1,jolt=.5+.5*Math.sin(T*.7),live=Math.floor(T/10)%2===0;
 const chat=['STOP','wtf???','STOP!!','omg','NO!!','mods?'];
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${22*Math.sin(T*.11)+5*Math.sin(f*.9)*turn}px,${12*Math.sin(T*.09)}px) rotate(${1.6*Math.sin(T*.07)}deg) scale(${1.08+.06*Math.sin(T*.13)})`,transformOrigin:'50% 55%'}}>
  <Bg c="#2A1E3A" c2="#5A3A7A"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1300H0Z" fill="#3A2A52"/>{[0,1,2,3,4].map(k=><path key={k} d={`M0 ${200+k*180}H1080`} stroke="#6A3AA0" strokeWidth={10} opacity={.5+.3*Math.sin(T*.2+k)}/>)}
   <g transform="translate(720 780) scale(.75)"><rect x={-330} y={-250} width={660} height={430} rx={18} fill="#14121C" strokeWidth={10}/><rect x={-300} y={-220} width={420} height={370} fill="#2E2440" stroke="none"/>
    <rect x={-290} y={-210} width={110} height={50} rx={8} fill={live?RED:'#7A2020'} stroke="none"/><text x={-235} y={-174} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={34} fill="#FFF" stroke="none">LIVE</text>
    <rect x={130} y={-220} width={170} height={370} fill="#1E1A28" stroke="none"/>
    {chat.slice(0,6).map((m,k)=>{const y=-170+((k*62+T*11)%372);return <text key={k} x={140} y={y} fontFamily="Quiet Sans" fontWeight={800} fontSize={38} fill={k%2?'#FF6B6B':'#FFE07A'} stroke="none">{m}</text>;})}
   </g>
   <circle cx={150} cy={620} r={80} fill="none" stroke="#FFF7E0" strokeWidth={20} opacity={.85}/>
   <path d="M0 1300H1080V1920H0Z" fill="#241A30"/><path d="M0 1300H1080" strokeWidth={9}/><path d="M60 1290H1020V1350H60Z" fill="#4A3A5A" strokeWidth={8}/>
  </svg>
  <P3 look="woman" x={360} y={2160} s={1.25} expr="angry" phase={.2} eye={[-14,10*turn]} pose={(r)=>{r.torso=-6*turn-8*jolt;r.hands=[[-200-90*jolt*turn,-380-160*jolt*turn],[120+60*jolt,-220-80*jolt]];r.handProps=[{pose:'open'},{pose:'fist'}];r.head=-8*turn+7*jolt;}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- en003 street outside a fight night: a man fires a handgun off-frame; crowd silhouettes duck. Nobody is hit on screen. ----
const GUN=<g stroke="#1E1712" strokeWidth={5} strokeLinejoin="round"><path d="M-14 -10H70V12H-14Z" fill="#2A2A30"/><path d="M-14 -10H8L2 40H-20Z" fill="#2A2A30"/></g>;
export const ShotsStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,aim=s<0?kf(s,[[-60,0],[-14,1]]):1,ph=(((T+12)%24)+24)%24,flash=aim>.9&&(ph<4||ph>=22),kick=flash?1:0,sh=0;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${9*Math.sin(s*.05)+sh}px,${5*Math.sin(s*.04)}px) rotate(${.6*Math.sin(s*.03)}deg) scale(${1.07+.03*Math.sin(s*.045)})`,transformOrigin:'50% 55%'}}>
  <Bg c="#0E1220" c2="#26304C"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1300H0Z" fill="#161C30"/><path d="M80 300H1000V1300H80Z" fill="#2A2238" strokeWidth={8}/>
   <rect x={240} y={560} width={600} height={130} rx={14} fill="#120E18" strokeWidth={7}/><text x={540} y={650} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={76} fill={Math.floor(T/7)%2?'#FF5A8A':'#FFC0D4'} stroke="none">FIGHT NIGHT</text>
   {[0,1,2,3,4,5].map(k=><circle key={k} cx={130+k*165} cy={300} r={16} fill={(k+Math.floor(T/5))%2?'#FFE07A':'#7A6A3A'} strokeWidth={4}/>)}
   {[0,1,2].map(k=>{const d=flash?30:0;return <g key={k} opacity={.7} transform={`translate(${700+k*120} ${1120+d})`}><circle cy={-120} r={34} fill="#3A3F55" stroke="none"/><path d="M-40 -90Q0 -110 40 -90L46 60H-46Z" fill="#3A3F55" stroke="none"/></g>;})}
   <path d="M0 1300H1080V1920H0Z" fill="#2C3040"/><path d="M0 1300H1080" strokeWidth={9}/>
   {flash&&<g transform="translate(720 900)"><path d="M0 0L70 -30L50 0L90 20L40 18L60 60Z" fill="#FFE07A" stroke={RED} strokeWidth={6}/><text x={-40} y={-80} fontFamily="Quiet Sans" fontWeight={800} fontSize={110} fill="#FFE07A" stroke={INK} strokeWidth={8} paintOrder="stroke">BANG</text></g>}
  </svg>
  <P3 look="rich" x={400} y={1600} s={1.3} expr="angry" phase={.2} eye={[16,-2]} pose={(r)=>{r.torso=-4-6*kick;r.hands=[[-120,-200],[150+250*aim,-330-60*aim+20*kick]];r.handProps=[{pose:'fist'},{pose:'grip',anchor:'wrist',side:'left',rot:-8-20*kick,object:GUN}];r.head=-3-3*kick;}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- ja001 street (2026-11-14: man and bag 500 px up so the whole head stays above the subtitle band y1192-1342; below it the figure would be under 0.4 of frame height): a cash bag lies on the pavement; a man bends, grabs it and glances around. Night by default; shot "day":true = daytime palette (ja001: 正午ごろ). ----
export const CashStage:React.FC<{s:number;day?:boolean}>=({s,day=false})=>{
 const f=useCurrentFrame(),T=s+900,grab=s<0?kf(s,[[-60,0],[-12,1]]):1,look=Math.sin(T*.25),bag=1-.6*grab;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${9*Math.sin(s*.05)}px,${5*Math.sin(s*.04)}px) rotate(${.6*Math.sin(s*.03)}deg) scale(${1.07+.03*Math.sin(s*.045)})`,transformOrigin:'50% 55%'}}>
  {day?<Bg c="#9FCFEA" c2="#D6EEF8"/>:<Bg c="#121A2C" c2="#26324C"/>}
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   {day&&<path d="M0 0H1080V330H0Z" fill="#A9D8F0" stroke="none"/>}<path d={day?"M0 330H1080V1280H0Z":"M0 0H1080V1280H0Z"} fill={day?'#C9B9A0':'#1A2238'}/>{Array.from({length:12}).map((_,k)=><rect key={k} x={60+(k%4)*250} y={420+Math.floor(k/4)*210} width={120} height={120} fill={day?((k*5+1)%4<2?'#BFE0F0':'#8FB8D0'):(k*5+1)%4<2?'#F2D27A':'#3A4462'} opacity={.8} strokeWidth={5}/>)}
   <path d="M0 1280H1080V1920H0Z" fill={day?'#9A9488':'#30364A'}/><path d="M0 1280H1080" strokeWidth={9}/>
   <g transform={`translate(${760-140*grab} ${1320-120*grab}) rotate(${-10+18*grab})`}><path d="M-110 -40Q-120 80 0 90Q120 80 110 -40Q60 -80 0 -70Q-60 -80 -110 -40Z" fill="#8A7A5A" strokeWidth={8}/><path d="M-40 -66Q0 -110 40 -66" fill="none" strokeWidth={8}/>
    <text y={40} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={80} fill="#FFE07A" stroke={INK} strokeWidth={6} paintOrder="stroke">¥</text></g>
   {[0,1,2].map(k=><g key={k} opacity={bag} transform={`translate(${640+k*90} ${1330+18*k}) rotate(${-14+12*k})`}><rect x={-60} y={-28} width={120} height={56} rx={5} fill="#C9B88A" strokeWidth={5}/><circle r={14} fill="none" stroke="#7A6A3A" strokeWidth={4}/></g>)}
  </svg>
  <P3 look="driver" x={420} y={1530} s={1.15} expr="shock" phase={.3} eye={[24*look,-4]} pose={(r)=>{r.torso=10*(1-grab)+3;r.hands=[[-120,-200],[170+60*(1-grab),-200+150*(1-grab)]];r.handProps=[{pose:'open'},{pose:'fist'}];r.head=6*look;}}/>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- ja002 night expressway: a dark car streaks past light trails; a speedometer needle pins at 144. No driver is drawn. ----
export const SpeedStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,rise=s<0?kf(s,[[-70,.35],[-15,1]]):1,v=Math.round(60+84*rise),ang=-120+240*(v/180),jit=1.5*Math.sin(T*2.1);
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${4*Math.sin(T*1.7)}px,${3*Math.sin(T*1.3)}px) scale(${1.07+.03*Math.sin(s*.045)})`,transformOrigin:'50% 55%'}}>
  <Bg c="#0A0E1A" c2="#1C2440"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <path d="M0 0H1080V1180H0Z" fill="#101626"/>{Array.from({length:9}).map((_,k)=><rect key={k} x={((k*170-T*40)%1530+1530)%1530-200} y={420+(k%3)*90} width={70} height={420-(k%3)*90} fill="#1E2840" stroke="none"/>)}
   <path d="M0 1180H1080V1920H0Z" fill="#20242E"/><path d="M0 1180H1080" stroke="#8A90A0" strokeWidth={12}/>
   {Array.from({length:7}).map((_,k)=><path key={k} d={`M${((k*260-T*70)%1820+1820)%1820-300} 1760h170`} stroke="#E8E2C0" strokeWidth={14}/>)}
   {Array.from({length:6}).map((_,k)=><path key={'t'+k} d={`M${-200+((k*230-T*90)%1600+1600)%1600} ${1440+k*26}h${300+60*(k%2)}`} stroke={k%2?'#FF5A5A':'#FFE9A8'} strokeWidth={6} opacity={.55}/>)}
   <g transform={`translate(${540+6*jit} 1600)`}><path d="M-300 0Q-290 -90 -180 -110L-90 -170H120L220 -100Q300 -90 310 0V40H-300Z" fill="#2A2E38" strokeWidth={8}/><path d="M-70 -155H110L180 -100H-130Z" fill="#0E1018" strokeWidth={5}/>
    <circle cx={-170} cy={40} r={50} fill="#111" strokeWidth={8}/><circle cx={190} cy={40} r={50} fill="#111" strokeWidth={8}/><path d="M300 -30h30" stroke="#FFE07A" strokeWidth={14}/></g>
   <g transform="translate(540 760)"><circle r={250} fill="#0E1018" stroke="#C9CED6" strokeWidth={14}/>
    {Array.from({length:10}).map((_,k)=>{const a=(-120+240*k/9)*Math.PI/180;return <path key={k} d={`M${200*Math.sin(a)} ${-200*Math.cos(a)}L${230*Math.sin(a)} ${-230*Math.cos(a)}`} stroke={k>6?RED:'#C9CED6'} strokeWidth={8}/>;})}
    <path d={`M0 0L${210*Math.sin((ang+jit)*Math.PI/180)} ${-210*Math.cos((ang+jit)*Math.PI/180)}`} stroke={RED} strokeWidth={14}/><circle r={22} fill={RED} stroke="none"/>
    <text y={150} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={110} fill="#FFF" stroke="none">{v}</text><text y={205} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={40} fill="#C9CED6" stroke="none">km/h</text></g>
  </svg>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- ja003 phone close-up: a thumb taps the heart on an ex's post; the like counter climbs to 14. Only the phone is shown. ----
// ---- bar (2026-11-14, q049): bar table at a staff birthday party: a whisky bottle pours into a glass beside a stack of cash; nobody shown
// (no character, so no one is implied to be the drinker). s = frames from frame 0 (negative during the loop line). ----
export const BarStage:React.FC<{s:number}>=({s})=>{
 const T=s+900,tilt=-28-14*(.5+.5*Math.sin(T*.09)),lvl=.35+.3*(.5+.5*Math.sin(T*.09)),slide=s<-20?kf(s,[[-70,1],[-30,0]]):0;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${18*Math.sin(T*.07)}px,${10*Math.sin(T*.05)}px) scale(${1.06+.04*Math.sin(T*.06)})`,transformOrigin:'50% 50%'}}>
  <Bg c="#1B1420" c2="#3E2A3A"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   {[0,1,2,3].map(k=><g key={k}><rect x={60} y={300+k*170} width={960} height={14} fill="#5A3E2E" strokeWidth={4}/>{[0,1,2,3,4,5].map(j=><path key={j} d={`M${110+j*160} ${300+k*170}v-70q0 -20 14 -30v-30h20v30q14 10 14 30v70z`} fill={['#7A4A2A','#3F6E4A','#8C2F3A','#C9A04A'][(j+k)%4]} strokeWidth={4} opacity={.85}/>)}</g>)}
   <path d="M0 230Q270 300 540 230T1080 230" fill="none" stroke="#E8C86A" strokeWidth={6}/>{[0,1,2,3,4,5,6,7,8].map(k=><path key={k} d={`M${60+k*120} ${250+6*Math.sin(k)}l30 0l-15 ${40+6*Math.sin(T*.2+k)}z`} fill={['#FF6B9A','#7FE0FF','#FFE07A'][k%3]} strokeWidth={3}/>)}
   <path d="M0 1000H1080V1920H0Z" fill="#2A1C16"/><path d="M-20 980H1100V1040H-20Z" fill="#6A4A34" strokeWidth={8}/>
   <g transform="translate(560 1000)"><path d="M-60 -170H60L50 0H-50Z" fill="#E8F0F4" opacity={.55} strokeWidth={6}/><path d={`M-55 ${-170*lvl}H55L50 0H-50Z`} fill="#C98A2E" opacity={.85} stroke="none"/></g>
   <g transform={`translate(470 760) rotate(${tilt})`}><path d="M-55 0V-260Q-55 -300 -25 -320V-400H25V-320Q55 -300 55 -260V0Z" fill="#8A5A2A" strokeWidth={7}/><rect x={-45} y={-210} width={90} height={110} fill="#F4E6C8" strokeWidth={4}/><rect x={-28} y={-430} width={56} height={34} fill="#2A1C16"/></g>
   <path d={`M${470+330*Math.sin(tilt*Math.PI/180)} ${760-330*Math.cos(tilt*Math.PI/180)+60}Q540 860 555 ${1000-170*lvl}`} fill="none" stroke="#C98A2E" strokeWidth={10} opacity={.8}/>
   <g transform={`translate(${830+300*slide} 975)`}>{[0,1,2,3,4].map(k=><g key={k} transform={`translate(${(k%2)*8} ${-k*26})`}><rect x={-110} y={-24} width={220} height={48} rx={6} fill="#8CC08A" strokeWidth={5}/><path d="M-20 -24V24M20 -24V24" stroke="#F4EBD3" strokeWidth={8}/></g>)}</g>
   <g transform="translate(230 975)"><path d="M-40 -90H40L34 0H-34Z" fill="#E8F0F4" opacity={.5} strokeWidth={5}/></g>
  </svg>
 </AbsoluteFill></AbsoluteFill>;
};
export const LikeStage:React.FC<{s:number}>=({s})=>{
 const f=useCurrentFrame(),T=s+900,n=s<0?Math.max(1,Math.min(14,Math.floor((s+80)/5))):14,tap=((T%10)+10)%10,press=tap<3?1:0;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`translate(${24*Math.sin(T*.11)}px,${14*Math.sin(T*.09)}px) rotate(${-2+2.5*Math.sin(T*.07)}deg) scale(${1.07+.06*Math.sin(T*.13)})`,transformOrigin:'50% 50%'}}>
  <Bg c="#1E1A2E" c2="#46365E"/>
  <svg width={W} height={H} style={{position:'absolute'}} {...S}>
   <g transform="translate(54 260) scale(.9)">
   <rect x={230} y={430} width={620} height={1240} rx={70} fill="#15161C" strokeWidth={10}/><rect x={262} y={500} width={556} height={1110} rx={26} fill="#F4F6F8" strokeWidth={4}/>
   {[0,1].map(k=><g key={k} transform={`translate(0 ${k*400})`}><circle cx={330} cy={590} r={40} fill="#9AA6B8" strokeWidth={4}/><rect x={390} y={565} width={220} height={26} rx={10} fill="#C9D1DC" stroke="none"/><rect x={300} y={650} width={480} height={22} rx={8} fill="#D9DEE6" stroke="none"/><rect x={300} y={690} width={400} height={22} rx={8} fill="#D9DEE6" stroke="none"/></g>)}
   <g transform={`translate(380 800) scale(${1+.35*press})`}><path d="M0 30C-70 -20 -50 -80 0 -50C50 -80 70 -20 0 30Z" fill={RED} strokeWidth={6}/></g>
   <text x={450} y={815} fontFamily="Quiet Sans" fontWeight={800} fontSize={64} fill={RED} stroke="none">{n}</text>
   <g transform={`translate(${410+10*press} ${900+20*press}) rotate(-20)`}><path d="M-40 0Q-50 -90 0 -110Q50 -90 40 0V220H-40Z" fill="#E8B996" strokeWidth={8}/><path d="M-26 -70Q0 -90 26 -70" fill="none" strokeWidth={5}/></g>
   {press>0&&<g transform="translate(380 760)">{[0,1,2,3,4,5].map(k=><path key={k} d="M0 -60V-95" stroke="#FFB0C0" strokeWidth={8} transform={`rotate(${k*60})`}/>)}</g>}
   </g>
  </svg>
 </AbsoluteFill></AbsoluteFill>;
};
// ---- piano: a pianist seen only from behind as a dark silhouette at a grand piano under a spotlight (no face, no likeness) ----
const PianoShot:React.FC<P>=({t,dur,i})=>{const h=Math.sin(t*.9),g=Math.sin(t*.45);return <AbsoluteFill><Bg c="#0C0E16" c2="#2A2E44"/><Cam t={t} dur={dur} i={i}><svg width={W} height={H} {...S}>
 <path d={`M540 0L${170+20*g} 1500H${910+20*g}Z`} fill="#FFF4D0" opacity={.12} stroke="none"/>
 <g transform="translate(0 300)">
 <path d="M150 1180Q160 900 520 880Q900 870 960 1050L960 1180Z" fill="#14151C" strokeWidth={8}/><path d="M520 880L880 560" stroke="#14151C" strokeWidth={14}/><path d="M560 880L880 560L940 600L620 900Z" fill="#20222C" strokeWidth={6}/>
 <rect x={170} y={1180} width={790} height={60} fill="#0E0F14" strokeWidth={6}/>{Array.from({length:14}).map((_,k)=><rect key={k} x={190+k*54} y={1186} width={44} height={46} fill="#F4F2EA" stroke="none"/>)}
 <path d="M200 1240V1500M920 1240V1500" stroke="#14151C" strokeWidth={22}/>
 <g transform={`translate(560 ${1420+4*g}) rotate(${3*g})`}><circle cy={-330} r={78} fill="#07080C" stroke="none"/><path d="M-140 -240Q0 -280 140 -240L170 60H-170Z" fill="#07080C" stroke="none"/>
  <path d={`M-130 -200L${-250+30*h} -230`} stroke="#07080C" strokeWidth={46} strokeLinecap="round"/><path d={`M130 -200L${250-30*h} -230`} stroke="#07080C" strokeWidth={46} strokeLinecap="round"/></g>
 <rect x={330} y={1540} width={420} height={80} rx={10} fill="#07080C" stroke="none"/>
 {[0,1,2].map(k=>{const y=((t*6+k*120)%360);return <text key={k} x={380+k*150} y={1000-y} fontSize={70} fill="#FFE07A" opacity={1-y/360} stroke="none">♪</text>;})}
 </g>
</svg></Cam></AbsoluteFill>;};
const SCENES:Record<string,React.FC<P>>={piano:PianoShot,receipt:Receipt,saltwork:SaltWork,chase:Chase,gold:Gold,plane:Plane,dog:DogCare,phonecall:PhoneCall,helmets:Helmets,clock:Clock,river:River,memorial:Memorial,tv:Tv,tally:Tally,trip:Trip,cctv:Cctv,bubble:Bubble,poster:Poster,cake:Cake,paper:PaperShot,stamp:StampShot,judge:JudgeShot,prosecutor:Prosecutor,phone:Phone,money:Money,calendar:Calendar,cell:CellShot,react:React1};
const StageBody:React.FC<{shot:Shot;t:number;dur:number;i:number}>=({shot,t,dur,i})=>{
 if(shot.s==='deal')return <DealStage s={t}/>;
 if(shot.s==='kick')return <KickStage s={t}/>;
 if(shot.s==='motel')return <MotelStage s={t}/>;
 if(shot.s==='taxi')return <TaxiStage s={t}/>;
 if(shot.s==='fire')return <FireStage s={t}/>;
 if(shot.s==='kettle')return <KettleStage s={t}/>;
 if(shot.s==='bb')return <BBStage s={t}/>;
 if(shot.s==='flee')return <FleeStage s={t}/>;
 if(shot.s==='forge')return <ForgeStage s={t}/>;
 if(shot.s==='vault')return <VaultStage s={t}/>;
 if(shot.s==='soju')return <SojuStage s={t}/>;
 if(shot.s==='cab')return <CabStage s={t}/>;
 if(shot.s==='bus')return <BusStage s={t}/>;
 if(shot.s==='salt')return <SaltStage s={t}/>;
 if(shot.s==='printshop')return <PrintStage s={t}/>;
 if(shot.s==='glare')return <GlareStage s={t}/>;
 if(shot.s==='busargue')return <BusArgueStage s={t}/>;
 if(shot.s==='scan')return <ScanStage s={t}/>;
 if(shot.s==='stream')return <StreamStage s={t}/>;
 if(shot.s==='shots')return <ShotsStage s={t}/>;
 if(shot.s==='cash')return <CashStage s={t} day={shot.day===true}/>;
 if(shot.s==='speed')return <SpeedStage s={t}/>;
 if(shot.s==='like')return <LikeStage s={t}/>;
 if(shot.s==='bar')return <BarStage s={t}/>;
 if(shot.s==='voucher')return <VoucherStage s={t}/>;
 if(shot.s==='bank')return <BankStage s={t}/>;
 if(shot.s==='factory')return <FactoryStage s={t}/>;
 if(shot.s==='pledge')return <PledgeStage s={t}/>;
 if(shot.s==='yard')return <YardStage s={t}/>;
 if(shot.s==='holiday')return <HolidayStage s={t}/>;
 const C=SCENES[shot.s];return C?<C t={t} dur={dur} p={shot} i={i}/>:null;};
// layout 2026-11-13 (cash, fire, glare, busargue, scan): heads moved out of the subtitle band; audit: factory/shorts/stage_audit.cjs
// per-stage framing from factory/shorts/library.json (stages[].frame = {origin:'top'|'bottom', zoom}): a zoom about the top or
// bottom edge moves the characters' heads out of the subtitle band (y 1192-1342) without leaving empty borders.
const FRAME:Record<string,{origin:string;zoom:number}>=Object.fromEntries(Object.entries((STAGE_LIB as {stages:Record<string,{frame?:{origin:string;zoom:number}}>}).stages).filter(([,v])=>v.frame).map(([k,v])=>[k,v.frame!]));
const Framed:React.FC<{s:string;children:React.ReactNode}>=({s,children})=>{const fr=FRAME[s];if(!fr)return <>{children}</>;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${fr.zoom})`,transformOrigin:`50% ${fr.origin==='top'?'0%':'100%'}`}}>{children}</AbsoluteFill></AbsoluteFill>;};
const StageFor:React.FC<{shot:Shot;t:number;dur:number;i:number}>=(p)=>{const L=React.useContext(LookCtx);if(!L.on)return <Framed s={p.shot.s}><StageBody {...p}/></Framed>;const light=LIGHT_OF[p.shot.s]??'court';
 return <LookCtx.Provider value={{...L,light}}><Stage cam={CAM0} light={light}><Framed s={p.shot.s}><StageBody {...p}/></Framed></Stage></LookCtx.Provider>;};
type L3=Line&{shots?:Shot[]};
export const B3Film:React.FC<{c:Case;u:Line;t:number}>=(p)=>{const lk=(p.c as Case&{look?:string}).look,on=lk==='full'||lk==='full2',u=p.u;
 if(!on)return <B3FilmIn {...p}/>;
 return <LookCtx.Provider value={{on,v2:lk==='full2',light:'court',track:talkTrack(u.tts,Math.round(u.onset*30),Math.round(u.offset*30)),track2:lk==='full2'?talkTrack2((u as Line&{lip?:string}).lip??u.tts,Math.round(u.onset*30),Math.round(u.offset*30),LIPDATA[p.c.qid]?.rms??(p.c as Case&{lip_rms?:number[]}).lip_rms):undefined}}><B3FilmIn {...p}/></LookCtx.Provider>;};
const B3FilmIn:React.FC<{c:Case;u:Line;t:number}>=({c,u,t})=>{
 const U=c.utterances as L3[];
 if(u.mode==='loop'){const first=(U[0].shots??[{s:'deal'}])[0];return <StageFor shot={first} t={t-u.dur} dur={u.dur} i={0}/>;}
 const shots=(u as L3).shots??[];if(!shots.length)return null;
 const n=shots.length,k=Math.min(n-1,Math.floor(t/(u.dur/n))),seg=Math.round(u.dur/n),idx=U.indexOf(u as L3)*3+k;
 return <StageFor shot={shots[k]} t={t-k*seg} dur={k===n-1?u.dur-k*seg:seg} i={idx}/>;
};
// ---- overlays ----
// non-ko text: shrink so the longest line fits 980px (ko keeps its tuned sizes)
const emKo=(l:string)=>[...l].reduce((w,ch)=>w+(/[가-힣]/.test(ch)?1:ch===' '?.3:/[0-9]/.test(ch)?.62:.5),0);
const fit=(c:unknown,text:string,size:number,box=980)=>Math.min(size,Math.floor(box/Math.max(1,...String(text).split('\n').map(l=>localeOf(c)==='ko'?emKo(l):em(localeOf(c),l)))));
type Pop={line:string;at:number;big:string;small:string};
export const Pops:React.FC<{c:Case}>=({c})=>{
 const f=useCurrentFrame(),pops=((c as Case&{pops?:Pop[]}).pops)??[];
 const live=pops.map(p=>{const u=c.utterances.find(x=>x.id===p.line)!;const a=u.from_frame+Math.round(p.at*u.dur);const nxt=pops.filter(q=>q.line===p.line&&q.at>p.at).map(q=>u.from_frame+Math.round(q.at*u.dur));const b=Math.min(u.from_frame+u.dur,...nxt);return {p,a,b,mode:u.mode};}).find(x=>f>=x.a&&f<x.b);
 if(!live)return null;const d=f-live.a,sc=d<6?.6+.4*ease(d/6)+.12*Math.sin(d*1.2)*(1-d/6):1;
 if(live.mode==='answer')return null;const low=live.mode==='answer2';
 return <div style={{...type,position:'absolute',left:30,top:low?1560:150,width:1020,zIndex:25,transform:`scale(${sc})`,transformOrigin:'50% 30%'}}>
  <div style={{fontFamily:'Quiet Sans',fontSize:fit(c,live.p.small,64),color:PAPER,WebkitTextStroke:`7px ${INK}`}}>{live.p.small}</div>
  <div style={{fontSize:fit(c,live.p.big,118),color:GOLD,lineHeight:1.05,letterSpacing:'-.02em'}}>{live.p.big}</div></div>;
};
// original gag: a small gavel with eyes hops in and flips a "구독" card (7.0-8.0 s), bottom-left, clear of faces and captions
export const SubGag:React.FC<{c?:unknown}>=({c})=>{const f=useCurrentFrame(),t=f-210,sub=str(c).subscribe,wide=sub.length>4;if(t<0||t>=30)return null;
 const hop=Math.abs(Math.sin(t*.35))*40,flip=kf(t,[[8,-1],[14,1]]),out=kf(t,[[24,0],[30,1]]);
 return <svg width={W} height={H} style={{position:'absolute',zIndex:26}} {...S}><g transform={`translate(${200-240*out} ${1640-hop})`}>
  <g transform="rotate(-20)"><path d="M-10 0V-120H10V0Z" fill="#A17442" strokeWidth={6}/><rect x={-70} y={-170} width={140} height={60} rx={10} fill="#AD7944" strokeWidth={6}/><circle cx={-22} cy={-140} r={8} fill={INK} stroke="none"/><circle cx={22} cy={-140} r={8} fill={INK} stroke="none"/><path d="M-14 -124Q0 -114 14 -124" fill="none" strokeWidth={4}/></g>
  <g transform={`translate(150 -150) scale(${flip} 1)`}><rect x={wide?-150:-110} y={-60} width={wide?300:220} height={120} rx={20} fill={flip>0?RED:'#EEE'} strokeWidth={7}/>{flip>0&&<text y={wide?18:22} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={wide?46:62} fill="#FFF" stroke="none">{sub}</text>}</g>
 </g></svg>;};
export const HookText:React.FC<{c:Case}>=({c})=>{const f=useCurrentFrame(),h=(c as Case&{hook_text?:string[]}).hook_text;if(!h)return null;
 const first=c.utterances[0],last=c.utterances[c.utterances.length-1];
 let a=0;if(f<first.from_frame+first.dur)a=1;else if(f>=last.from_frame+last.dur-24)a=clamp01((f-(last.from_frame+last.dur-24))/8);
 if(a<=0)return null;
 // format "result_first" (format B A/B test, 11-14): both lines big, white / yellow with a thick outline, like top Korean verdict shorts
 if((c as Case&{format?:string}).format==='result_first')return <div style={{...type,position:'absolute',left:40,top:170,width:1000,zIndex:24,opacity:a,lineHeight:1.08}}>{h.map((x,k)=><div key={k} style={{fontSize:fit(c,x,k?200:150,980),color:k?'#FFE14D':'#FFFFFF',WebkitTextStroke:`${k?18:14}px #111`,paintOrder:'stroke fill'}}>{x}</div>)}</div>;
 return <div style={{...type,position:'absolute',left:60,top:150,width:960,zIndex:24,opacity:a}}><div style={{fontSize:fit(c,h[0],100,940)}}>{h[0]}</div><div style={{fontSize:fit(c,h[1],190,940),color:RED,lineHeight:1}}>{h[1]}</div></div>;};
export {TEAL};
