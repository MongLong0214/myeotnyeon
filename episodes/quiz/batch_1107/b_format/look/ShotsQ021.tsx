// q021 shots re-staged on the look layer: same blocking, timing and characters as Q021.tsx.
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {type} from '../CourtDynamic';
import {Bars,Sweat,PAPER,RED,kf,clamp01} from '../Kit';
import {Q021Film} from '../Q021';
import type {Line,Case} from '../BStandard';
import {Actor,ActorOpt,act,handScreen,hand,talkTrack} from './BActing';
import {BlurSvg,Stage,Layer,Beam,Dust,Smear,Trail,SpeedLines,Contact,shakeAt,drift,dolly,whip,type Cam} from './BLook';
import {CourtOut,CourtWall,CourtDais,CourtRailPlus,AlleyOut,AlleyWall,AlleyNear,CellOut,CellWall} from './Sets';
type Point=[number,number];
const KNIFE=<g stroke="#1E1712" strokeWidth={5} strokeLinejoin="round"><path d="M-9 12V-46H9V12Z" fill="#3B3533"/><path d="M-11 -46H13L10 -150Q4 -168 -9 -150Z" fill="#C9CED3"/><path d="M-4 -60V-140" fill="none" stroke="#E8ECEF" strokeWidth={4}/></g>;
const withShake=(c:Cam,f:number,hits:[number,number][],hh=1,salt=3):Cam=>{const s=shakeAt(f,hits),d=drift(f,hh,salt);return {...c,x:c.x+s.x+d.x,y:c.y+s.y+d.y,rot:c.rot+s.r+d.r*.6};};

// ---- opener: the prosecutor's desk slam (impact on s=3) and the point ----
const IMPACT=3;
const prosecutor=(t0:number):ActorOpt=>({look:'suit',x:540,y:1650,s:1.5,expr:'angry',seed:2,light:'court',breath:2.2,
 springs:{hands:null,head:[3.2,.4],torso:[5,.5],props:null},
 eye:[0,2],
 pose:(r,f)=>{const s=f-t0;
  // slam hand (slot 1): raised and still before 0 (the loop wind-up), accelerating down onto the desk, small rebound
  const d=s<0?0:s>=IMPACT?1:Math.pow(s/IMPACT,2.2),reb=s>IMPACT?kf(s,[[IMPACT,0],[IMPACT+2,1],[IMPACT+7,0]]):0;
  r.hands[1]=[230-40*d,-518+293*d-14*reb];
  // point (slot 0): anticipation pull-in, then overshoot and settle
  const p=act(s,10,24,14,4,.22);
  r.hands[0]=[-78-150*p,-118-300*p];
  r.handProps=[hand(0,p>.45?'point':'relaxed'),hand(1,'fist')];
  const lean=s<IMPACT?1:1-.4*clamp01(p);
  r.torso+=-4*lean-3*(s>=IMPACT&&s<IMPACT+5?(IMPACT+5-s)/5:0);r.head=-3*lean+(s>=0?2*clamp01(p)*Math.sin(s*.25):0);
  r.hip[1]+=s>=IMPACT?6*kf(s,[[IMPACT,1],[IMPACT+6,0]]):0;
 },ik:{elbow:[[-1,.4],[1,.4]]}});
const OpenStage:React.FC<{s:number;text:boolean}>=({s,text})=>{
 const f=useCurrentFrame(),t0=f-s,o=prosecutor(t0);
 const zoom=1+.1*(1-clamp01(s/9))**2+.035*clamp01((s-9)/38);
 const cam=withShake({...dolly(f,[[t0,{zoom,focus:1,focusAmt:5}]]),zoom},f,[[t0+IMPACT,24],[t0+IMPACT+1,10]],1.1,7);
 const hit:Point=handScreen(o,t0+IMPACT,1),trail=[0,1,2,3].filter(k=>s-k>=0&&s-k<=IMPACT).map(k=>handScreen(o,f-k,1)).reverse();
 return <AbsoluteFill style={{overflow:'hidden'}}>
  <Stage cam={cam} light="court" impact={s-IMPACT}>
   <Layer depth={.3} noBlur><CourtOut/></Layer>
   <Layer depth={.88} noBlur><CourtWall/><CourtDais/></Layer>
   <Layer depth={.92}><Beam id="cw1" pts={[[105,130],[255,130],[760,1300],[420,1300]]} color="#F4FAFF" opacity={.22} from={[0,0]} to={[0,1]}/></Layer>
   <Layer depth={1}>
    {s>=0&&s<IMPACT&&<Trail path={trail} color="#FFFFFF" n={3} spread={34} opacity={.75}/>}
    <Actor {...o}/>
    {s===IMPACT-1&&<Smear path={[handScreen(o,f-1,1),handScreen(o,f,1),hit]} w={52} fill="#F4CFA7" opacity={.95}/>}
    <CourtRailPlus y={1330}/>
    <Dust x={hit[0]} y={1324} t={s-IMPACT} n={8} s={1.1} seed={4} color="#F4ECD6" chips="#FFF5DD" spread={1.4} floor={1336}/>
   </Layer>
   <SpeedLines t={s-IMPACT} dur={7} center={[hit[0],1320]} inner={420} n={22} color="#FFFFFF" opacity={.7}/>
  </Stage>
  {text&&s>=0&&<div style={{...type,position:'absolute',left:40,top:120,width:1000,zIndex:21,transform:`scale(${s<6?1+.25*Math.exp(-s/2)*Math.cos(s):1})`}}>
   <div style={{fontSize:96,color:PAPER}}>검찰 구형</div>
   <div style={{fontSize:230,color:RED,letterSpacing:'-.02em',lineHeight:1}}>사형</div>
  </div>}
 </AbsoluteFill>;
};
export const LookOpen:React.FC<{t:number;dur:number}>=({t})=><OpenStage s={t} text/>;

// ---- street: the attacker walks in; two men notice (take), turn and run. Focus racks from them to him. ----
const walk=(r:any,ph:number,amp=40)=>{const w=Math.sin(ph);r.feet=[[-30-amp*w,-14*Math.max(0,w)],[30+amp*w,-14*Math.max(0,-w)]];r.hip[1]+=-5*Math.abs(Math.cos(ph));r.torso+=1.5*Math.sin(ph*2);};
export const LookStreet:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const f=useCurrentFrame(),t0=f-t;
 const run=(ff:number)=>clamp01((ff-t0-16)/10);
 const flee=(x0:number,look:'passenger'|'driver',ph:number,seed:number):ActorOpt=>{
  const x=(ff:number)=>{const tt=ff-t0;return x0+(tt>16?run(ff)*(tt-16)*7:0);};
  return {look,x:x(f),y:1150,s:.8,expr:'scared',seed,light:'street',take:{at:t0+11+seed%2,from:'normal',amt:1.2},cast:true,
   pose:(r,ff)=>{const tt=ff-t0,ru=run(ff),n=kf(tt,[[9,0],[15,1]]);walk(r,tt*(.35+.3*ru)+ph,30+22*ru);
    r.hands=[[-78-30*ru+14*Math.sin(tt*.6+ph)*ru,-118-60*ru-40*n*(1-ru)],[78+30*ru-14*Math.sin(tt*.6+ph)*ru,-118-60*ru-40*n*(1-ru)]];
    r.handProps=[hand(0,n>.5&&ru<.5?'open':'fist'),hand(1,n>.5&&ru<.5?'open':'fist')];r.head=-8*n+4*ru;r.torso+=12*ru-4*n*(1-ru);},eye:[-12,0]};
 };
 const att:ActorOpt={look:'attacker',x:300+t*1.6,y:1290,s:1.3,expr:'serious',seed:5,light:'street',cast:true,darts:false,breath:1.4,eye:[12,0],
  pose:(r,ff)=>{const tt=ff-t0;walk(r,tt*.22,26);r.hands=[[-78+10*Math.sin(tt*.22),-118],[110-8*Math.sin(tt*.22),-160]];r.handProps=[hand(0,'relaxed'),hand(1,'grip',KNIFE,200+10*Math.sin(tt*.22))];r.head=-2;}};
 const w=whip(f,t0-3,9,420),focus=kf(t,[[0,.96],[18,.96],[30,1.06]]);
 const cam=withShake({x:w.x+.25*t*1.6,y:0,zoom:1+.04*clamp01(t/dur),rot:0,focus,focusAmt:12,blurX:w.blur,blurY:0},f,[],1.4,11);
 const A=flee(700,'passenger',.5,1),B=flee(900,'driver',2,2);
 return <AbsoluteFill style={{overflow:'hidden'}}>
  <Stage cam={cam} light="street">
   <Layer depth={.3} noBlur><AlleyOut/></Layer>
   <Layer depth={.86} noBlur><AlleyWall/></Layer>
   <Layer depth={.96}>
    <Contact x={A.x} y={1152} rx={70} light="street"/><Contact x={B.x} y={1152} rx={70} light="street"/>
    {t>=16&&t<34&&<Trail path={[[A.x-120,1030],[A.x-40,1030]]} color="#FFFFFF" n={3} spread={40} opacity={.6*(1-(t-16)/18)}/>}
    <Actor {...A}/><Actor {...B}/>
    <Dust x={A.x-30} y={1146} t={t-17} n={3} s={.42} seed={7} color="#BDB7A6"/><Dust x={B.x-30} y={1146} t={t-18} n={3} s={.42} seed={9} color="#BDB7A6"/>
   </Layer>
   <Layer depth={1.06}><Contact x={att.x} y={1294} rx={120} light="street"/><Actor {...att}/></Layer>
   <Layer depth={1.4}><AlleyNear/></Layer>
  </Stage>
 </AbsoluteFill>;
};

// ---- prisoner close-up: rattles the bars (anticipation, pulls, bars ring), then the take: concern -> tired ----
export const LookCell:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const f=useCurrentFrame(),t0=f-t;
 const PULLS=[7,13,19];
 const rat=(ff:number)=>{const tt=ff-t0;let v=-4*kf(tt,[[2,0],[6,1],[7,0]]);for(const p of PULLS){const d=tt-p;if(d>=0&&d<14)v+=9*Math.exp(-d/3.2)*Math.cos(d*1.5);}return v;};
 const o:ActorOpt={look:'inmate2',x:540,y:1660,s:1.5,expr:'tired',seed:3,light:'cell',take:{at:t0+27,from:'concern',amt:.7},breath:1.6,
  eye:[0,6],springs:{hands:[9,.6],head:[3,.38],torso:[5,.55],props:null},
  pose:(r,ff)=>{const tt=ff-t0,v=rat(ff),turn=kf(tt,[[26,0],[38,1]]);r.hands=[[-200+v*.6,-330],[200+v*.6,-330]];r.handProps=[hand(0,'fist'),hand(1,'fist')];
   r.hip[0]+=v*.9;r.torso+=v*.25;r.head=v*.5-6*turn;r.hip[1]+=5*turn;}};
 const cam=withShake({...dolly(f,[[t0,{zoom:1,y:0}],[t0+dur,{zoom:1.07,y:-60}]]),focus:1,focusAmt:6},f,PULLS.map(p=>[t0+p,5] as [number,number]),.7,5);
 return <AbsoluteFill style={{overflow:'hidden'}}>
  <Stage cam={cam} light="cell">
   <Layer depth={.3} noBlur><CellOut/></Layer>
   <Layer depth={.88} noBlur><CellWall/></Layer>
   <Layer depth={.92}><Beam id="cb" pts={[[400,330],[680,330],[860,1720],[260,1720]]} color="#E4F6FF" opacity={.2}/></Layer>
   <Layer depth={1}>
    <Contact x={540} y={1664} rx={190} light="cell"/>
    <Actor {...o}/>
    <Bars xs={[235,845]} dx={rat(f)*.6}/>
    {PULLS.map((p,i)=><Dust key={p} x={i%2?845:235} y={20} t={t-p} n={3} s={.5} seed={p} color="#9AA4AA" chips="#8C959C" floor={1700}/>)}
    {t>=24&&<Sweat x={700} y={760} t={t-24} s={1.2}/>}
   </Layer>
   <Layer depth={1.4}><BlurSvg>{[30,1050].map(x=><g key={x}><path d={`M${x-34} -200H${x+34}V2200H${x-34}Z`} fill="#3F474D" stroke="#201B23" strokeWidth={9}/><path d={`M${x-12} -200V2200`} stroke="#77828A" strokeWidth={10}/></g>)}</BlurSvg></Layer>
  </Stage>
 </AbsoluteFill>;
};

export const Q021_LOOK:Record<string,React.FC<{t:number;dur:number}>>={open:LookOpen,street:LookStreet,opinion:LookCell};
export const Q021LookFilm:React.FC<{c:Case;u:Line;t:number}>=({c,u,t})=>{const S=Q021_LOOK[u.mode];return S?<S t={t} dur={u.dur}/>:<Q021Film c={c} u={u} t={t}/>;};
export {talkTrack};
