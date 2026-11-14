// q024 shots re-staged on the look layer: same blocking, timing and characters as Q024.tsx. Grave tone: no impact
// frames, no speed lines on the death beat; the struggle gets weight (shoves with anticipation, decaying shake, dust).
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {type} from '../CourtDynamic';
import {S,GOLD,kf,clamp01} from '../Kit';
import {Q024Film} from '../Q024';
import {Watch} from '../Q023';
import type {Line,Case} from '../BStandard';
import {Actor,ActorOpt,act,handScreen,hand,talkTrack} from './BActing';
import {BlurSvg,Stage,Layer,Beam,Dust,Smear,Contact,shakeAt,drift,dolly,type Cam} from './BLook';
import {HomeOut,HomeWall} from './Sets';
const KNIFE=<g stroke="#1E1712" strokeWidth={5} strokeLinejoin="round"><path d="M-9 12V-46H9V12Z" fill="#3B3533"/><path d="M-11 -46H13L10 -150Q4 -168 -9 -150Z" fill="#C9CED3"/><path d="M-4 -60V-140" fill="none" stroke="#E8ECEF" strokeWidth={4}/></g>;
const SON='snack' as const,DAD='prof' as const;
const withShake=(c:Cam,f:number,hits:[number,number][],hh=1,salt=3):Cam=>{const s=shakeAt(f,hits),d=drift(f,hh,salt);return {...c,x:c.x+s.x+d.x,y:c.y+s.y+d.y,rot:c.rot+s.r+d.r*.6};};
const HomeLayers:React.FC<{door:number;children:React.ReactNode;near?:React.ReactNode}>=({door,children,near})=><>
 <Layer depth={.3} noBlur><HomeOut/></Layer>
 <Layer depth={.9} noBlur><HomeWall door={door}/></Layer>
 <Layer depth={.93}><Beam id="moon" pts={[[60,300],[420,300],[700,1500],[150,1500]]} color="#9FB8FF" opacity={.13}/></Layer>
 <Layer depth={1}>{children}</Layer>
 {near&&<Layer depth={1.4}>{near}</Layer>}
</>;

// ---- struggle: shoves alternate with anticipation; hard cut to the aftermath (shards, father alone) ----
const SHOVES:[number,number][]=[[2,1],[14,-1],[25,1],[37,-1],[46,1]];
const sway=(tt:number)=>{let p=0;for(const [at,dir] of SHOVES){p+=dir*40*act(tt,at,at+10,10,3,.25);}return p-12;};
const Shards:React.FC<{glint:number}>=({glint})=><BlurSvg svgProps={{...S,strokeWidth:6} as any}>
 {[[180,1830,0,2.2],[430,1880,40,2.6],[700,1820,-30,2.0],[890,1890,70,2.4],[560,1760,110,1.6]].map(([x,y,r,s],i)=><g key={i} transform={`translate(${x} ${y}) rotate(${r}) scale(${s})`}>
  <path d="M0 0l40 -18l22 30l-48 16Z" fill="#EDEFF2"/><path d="M8 -2l22 -10" stroke="#FFFFFF" strokeWidth={3}/>
  {(i+Math.floor(glint/9))%5===0&&<path d="M30 -30v-20M30 -30v20M30 -30h-20M30 -30h20" stroke="#FFFFFF" strokeWidth={4}/>}</g>)}
</BlurSvg>;
export const LookFight:React.FC<{t:number;dur:number}>=({t,dur})=>{
 const f=useCurrentFrame(),t0=f-t,cut=Math.round(dur*.55);
 if(t<cut){
  const dad:ActorOpt={look:DAD,x:400,y:1700,s:1.5,expr:'scared',seed:1,light:"homeNight",breath:2.4,eye:[12,0],springs:{hands:[6,.5],head:[3.4,.35],torso:[5,.5],props:null},
   pose:(r,ff)=>{const tt=ff-t0,p=sway(tt);r.hip[0]+=p/1.5;r.hands=[[120+p*.2,-330],[150+p*.2,-260]];r.handProps=[hand(0,'fist'),hand(1,'fist')];r.torso=10-p*.5;r.head=-6-p*.35;r.feet=[[-40-p*.3,0],[40+p*.15,0]];}};
  const son:ActorOpt={look:SON,x:720,y:1700,s:1.55,expr:'angry',seed:4,light:"homeNight",breath:2.4,eye:[-12,0],springs:{hands:[6,.5],head:[3.4,.35],torso:[5,.5],props:null},
   pose:(r,ff)=>{const tt=ff-t0,p=sway(tt);r.hip[0]+=p/1.55;r.hands=[[-140+p*.2,-330],[-120+p*.2,-250]];r.handProps=[hand(0,'fist'),hand(1,'fist')];r.torso=-10-p*.5;r.head=5-p*.35;r.feet=[[-40-p*.15,0],[40+p*.3,0]];}};
  const hits=SHOVES.map(([a])=>[t0+a+4,9] as [number,number]);
  const cam=withShake({...dolly(f,[[t0,{zoom:1.05}],[t0+cut,{zoom:1.1}]]),focus:1,focusAmt:5},f,hits,2.2,9);
  return <AbsoluteFill style={{overflow:'hidden'}}><Stage cam={cam} light="homeNight">
   <HomeLayers door={.35}>
    <Contact x={400} y={1704} rx={150} light="homeNight"/><Contact x={720} y={1704} rx={150} light="homeNight"/>
    <Actor {...dad}/><Actor {...son}/>
    {SHOVES.map(([a],i)=><Dust key={a} x={i%2?380:740} y={1700} t={t-a-4} n={5} s={.75} seed={a} color="#6E6258"/>)}
   </HomeLayers>
  </Stage></AbsoluteFill>;
 }
 const u=t-cut;
 const dad:ActorOpt={look:DAD,x:460,y:1640,s:1.6,expr:'shock',seed:1,light:"homeNight",breath:2.8,eye:[0,12],take:{at:t0+cut+3,from:'scared',amt:1},springs:{hands:[4.5,.45],head:[3,.35],torso:[4,.5],props:null},
  pose:(r,ff)=>{const uu=ff-t0-cut,d=uu<0?0:act(uu,0,16,16,4,.2),tr=uu>16?2.2*Math.sin(uu*2.1):0;r.hands=[[-80-140*d+tr,-200-150*d],[80+125*d-tr,-200-170*d+tr]];r.handProps=[hand(0,'open'),hand(1,'open')];r.head=-8*d;r.hip[1]+=30*d;r.torso=-8*d;},ik:{knee:[[-.4,-1],[.4,-1]]}};
 const cam=withShake({...dolly(f,[[t0+cut,{zoom:1,focus:1.4}],[t0+cut+6,{focus:1.4}],[t0+cut+20,{focus:1}],[t0+dur,{zoom:1.06}]]),focusAmt:9},f,[],.6,4);
 return <AbsoluteFill style={{overflow:'hidden'}}><Stage cam={cam} light="homeNight">
  <HomeLayers door={.35} near={<Shards glint={u}/>}>
   <Contact x={460} y={1644} rx={160} light="homeNight"/>
   <Actor {...dad}/>
  </HomeLayers>
 </Stage></AbsoluteFill>;
};

// ---- night: he pounds on the door (anticipation, fast strike, contact, recoil); door and light rattle ----
const POUNDS=[4,15,26,37,48,59,70,81];
const poundAt=(tt:number)=>{let v=0,hit=-99;for(const p of POUNDS){const d=tt-p;if(d>=-4&&d<7){v=d<0?-(1-Math.cos(Math.PI*(d+4)/4))/2:d<2?-1+2*Math.pow(d/2,2):d<3?1:1-(d-3)/4;hit=p;}}return {v,hit};};
export const LookNight:React.FC<{t:number;dur:number;c?:Case;u?:Line}>=({t,dur,u})=>{
 const f=useCurrentFrame(),t0=f-t,frac=clamp01(t/(dur-8));
 const tr=u?talkTrack(u.tts,Math.round(u.onset*30),Math.round(u.offset*30)):undefined;
 const son:ActorOpt={look:SON,x:620,y:1700,s:1.6,expr:'angry',seed:6,light:"homeNight",breath:2,eye:[12,0],talk:tr,darts:false,
  springs:{hands:null,head:[3.2,.38],torso:[5,.5],props:[3,.32]},
  pose:(r,ff)=>{const tt=ff-t0,{v}=poundAt(tt);const strike=Math.max(0,v),back=Math.max(0,-v);
   r.hip[0]+=22;r.hands=[[-70-6*back,-150+4*strike],[195+55*strike-15*back,-395-10*strike-15*back]];
   r.handProps=[hand(0,'grip',KNIFE,180+14*strike-10*back),hand(1,'fist')];r.torso=8*strike-4*back;r.head=5*strike-3*back;r.hip[0]+=6*strike-4*back;}};
 const hits=POUNDS.map(p=>[t0+p+2,8] as [number,number]);
 const ring=(ff:number)=>{let v=0;for(const p of POUNDS){const d=ff-t0-p-2;if(d>=0&&d<12)v+=Math.exp(-d/3)*Math.cos(d*1.8);}return v;};
 const door=.15+.03*ring(f);
 const cam=withShake({...dolly(f,[[t0,{zoom:1}],[t0+dur,{zoom:1.05}]]),rot:-1.2,focus:1,focusAmt:5},f,hits,1.4,13);
 const {v,hit}=poundAt(t),sm=v>-1&&v<1&&t-hit>=0&&t-hit<2;
 return <AbsoluteFill style={{overflow:'hidden'}}><Stage cam={cam} light="homeNight">
  <HomeLayers door={door}>
   <Contact x={620} y={1704} rx={160} light="homeNight"/>
   <Actor {...son}/>
   {sm&&<Smear path={[handScreen(son,f-1,1),handScreen(son,f,1)]} w={40} fill="#F2D2B4" opacity={.9}/>}
   {POUNDS.map(p=><Dust key={p} x={1000} y={1020} t={t-p-2} n={3} s={.45} seed={p} color="#C9B8A2" chips="#8A6A4E" spread={.8} floor={1240}/>)}
   <Watch x={250} y={420} s={1.2} sec={180*frac}/>
  </HomeLayers>
 </Stage>
 <div style={{...type,position:'absolute',left:60,top:620,width:380,fontSize:86,color:GOLD,zIndex:21}}>{Math.round(60*frac)}분</div></AbsoluteFill>;
};

export const Q024_LOOK:Record<string,React.FC<{t:number;dur:number;c?:Case;u?:Line}>>={fight:LookFight,night:LookNight};
export const Q024LookFilm:React.FC<{c:Case;u:Line;t:number}>=({c,u,t})=>{const Sh=Q024_LOOK[u.mode];return Sh?<Sh t={t} dur={u.dur} c={c} u={u}/>:<Q024Film c={c} u={u} t={t}/>;};
