// look v2 ("full2") shots: the five v1 proof shots re-staged on Actor2/Look2, plus two new ones (a walk and a
// sit-down) that also have a v1-look version for the side-by-side. Same blocking, timing and characters as Q021/Q024.
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {type} from '../../CourtDynamic';
import {Bars,Sweat,PAPER,RED,GOLD,INK,S,kf,clamp01} from '../../Kit';
import {Watch} from '../../Q023';
import type {Line,Case} from '../../BStandard';
import {Actor,ActorOpt,act,hand} from '../BActing';
import {Stage,Layer,Beam,Dust,Smear,Trail,SpeedLines,Contact,BlurSvg,shakeAt,drift,dolly,type Cam} from '../BLook';
import {CourtOut,CourtWall,CourtDais,CourtRailPlus,AlleyOut,AlleyWall,AlleyNear,CellOut,CellWall,HomeOut,HomeWall} from '../Sets';
import {Actor2,Actor2Opt,POSE,poseKeys2,applyPose,hand2Screen,xAt} from './Actor2';
import {talkTrack2,LIPDATA} from './Lip';
import {snapZoom,whipBetween,slowPush,dutch,ForeBars,ForeMonitor,ForeLamp,InkSplash,FlutterPaper,Flicker,flickerAt,Motes,Rain,PaneDrops} from './Look2';
type Point=[number,number];
type ShotP={t:number;dur:number;c?:Case;u?:Line};
const KNIFE=<g stroke="#1E1712" strokeWidth={5} strokeLinejoin="round"><path d="M-9 12V-46H9V12Z" fill="#3B3533"/><path d="M-11 -46H13L10 -150Q4 -168 -9 -150Z" fill="#C9CED3"/><path d="M-4 -60V-140" fill="none" stroke="#E8ECEF" strokeWidth={4}/></g>;
const cam=(c:Partial<Cam>,f:number,hits:[number,number][]=[],hh=1,salt=3):Cam=>{const b={x:0,y:0,zoom:1,rot:0,focus:1,focusAmt:18,blurX:0,blurY:0,...c},s=shakeAt(f,hits),d=drift(f,hh,salt);return {...b,x:b.x+s.x+d.x,y:b.y+s.y+d.y,rot:b.rot+s.r+d.r*.6};};
const track=(c:Case|undefined,u:Line|undefined)=>c&&u?talkTrack2(u.tts,Math.round(u.onset*30),Math.round(u.offset*30),LIPDATA[c.qid]?.rms):undefined;

// =============== q021 open: desk slam → ink-splash impact, papers jump, snap zoom, "사형" snaps in ===============
const IMPACT=3;
const pros=(t0:number):Actor2Opt=>({look:'suit',x:540,y:1650,s:1.5,expr:'angry',seed:2,light:'court',breath:2.4,blinks:[t0+30],
 springs:{hands:null,head:[3.2,.36],torso:[5,.5],props:null},eye:[0,2],lookAt:f=>f-t0<12?0:-.5*clamp01((f-t0-12)/6),
 pose:(r,f)=>{const s=f-t0,d=s<0?0:s>=IMPACT?1:Math.pow(s/IMPACT,2.2),reb=s>IMPACT?kf(s,[[IMPACT,0],[IMPACT+2,1],[IMPACT+7,0]]):0;
  r.hands[1]=[230-40*d,-518+293*d-14*reb];const p=act(s,10,24,14,4,.22);r.hands[0]=[-78-150*p,-118-300*p];
  r.handProps=[hand(0,p>.45?'point':'relaxed'),hand(1,'fist')];const lean=s<IMPACT?1:1-.4*clamp01(p);
  r.torso+=-4*lean-3*(s>=IMPACT&&s<IMPACT+5?(IMPACT+5-s)/5:0);r.head=-3*lean;r.hip[1]+=s>=IMPACT?6*kf(s,[[IMPACT,1],[IMPACT+6,0]]):0;
  r.hip[0]+=-10*clamp01(p);},ik:{elbow:[[-1,.4],[1,.4]]}});
export const Open2:React.FC<ShotP>=({t:s})=>{
 const f=useCurrentFrame(),t0=f-s,o=pros(t0),hit=hand2Screen(o,t0+IMPACT,1);
 const sz=snapZoom(f,t0+IMPACT,1.13,[hit[0],1250]),z=sz.zoom*slowPush(f,t0+14,34,-.05);
 const c=cam({x:sz.x,y:sz.y,zoom:z,rot:dutch(f,t0+IMPACT,6,-2.2),focus:1,focusAmt:20},f,[[t0+IMPACT,24],[t0+IMPACT+1,10]],1.1,7);
 const trail=[0,1,2,3].filter(k=>s-k>=0&&s-k<=IMPACT).map(k=>hand2Screen(o,f-k,1)).reverse();
 const txt=s<0?0:s<4?1.35-.35*(s/4)+.0:1+.08*Math.exp(-(s-4)/3)*Math.cos((s-4)*1.1);
 return <AbsoluteFill style={{overflow:'hidden'}}>
  <Stage cam={c} light="court" impact={s-IMPACT}>
   <Layer depth={.3}><CourtOut/></Layer>
   <Layer depth={.86}><CourtWall/><CourtDais/></Layer>
   <Layer depth={.92}><Beam id="cw1" pts={[[105,130],[255,130],[760,1300],[420,1300]]} color="#F4FAFF" opacity={.24}/><Motes box={[150,200,460,1000]} n={30}/></Layer>
   <Layer depth={1}>
    {s>=0&&s<IMPACT&&<Trail path={trail} color="#FFFFFF" n={3} spread={34} opacity={.75}/>}
    <Actor2 {...o}/>
    {s===IMPACT-1&&<Smear path={[hand2Screen(o,f-1,1),hand2Screen(o,f,1),hit]} w={52} fill="#F4CFA7" opacity={.95}/>}
    <CourtRailPlus y={1330} papers={false}/>
    <FlutterPaper x={250} y={1318} w={300} h={40} rot={-4} t={s-IMPACT} label="공소장 · 사건 2023고합" seed={1} size={22}/>
    <FlutterPaper x={770} y={1312} w={180} h={44} rot={3} t={s-IMPACT-1} label="증거기록 3권" seed={2} size={22}/>
    <Dust x={hit[0]} y={1324} t={s-IMPACT} n={8} s={1.1} seed={4} color="#F4ECD6" chips="#FFF5DD" spread={1.4} floor={1336}/>
    <InkSplash x={hit[0]} y={1290} t={s-IMPACT} s={.75}/>
   </Layer>
   <Layer depth={1.5}><ForeMonitor x={980} y={1640} flip/></Layer>
   <SpeedLines t={s-IMPACT} dur={7} center={[hit[0],1320]} inner={420} n={22} color="#FFFFFF" opacity={.7}/>
  </Stage>
  {s>=0&&<div style={{...type,position:'absolute',left:40,top:120,width:1000,zIndex:21,transform:`scale(${txt})`,transformOrigin:'50% 70%'}}>
   <div style={{fontSize:96,color:PAPER}}>검찰 구형</div><div style={{fontSize:230,color:RED,letterSpacing:'-.02em',lineHeight:1}}>사형</div></div>}
 </AbsoluteFill>;
};

// =============== q021 street: planted walk, take, whip-pan between characters, run with planted feet ===============
export const Street2:React.FC<ShotP>=({t})=>{
 const f=useCurrentFrame(),t0=f-t;
 const flee=(x0:number,look:'passenger'|'driver',seed:number):Actor2Opt=>({look,x:x0,y:1150,s:.8,expr:f2=>f2-t0<12?'normal':'scared',seed,light:'street',cast:true,
  take:[{at:t0+11+seed%2,from:'normal',amt:1.2}],walk:{x0,v:6.5,from:t0+17,cycle:16,stance:.42,lift:34,arms:30},lookAt:f2=>f2-t0<9?.3:-1,eye:[0,0],
  pose:(r,f2)=>{const tt=f2-t0,n=kf(tt,[[9,0],[15,1]]),ru=clamp01((tt-16)/6);POSE.recoil(r,n*(1-ru)*.8,1);
   if(ru>0){r.torso+=12*ru;r.hands=[[r.hands[0][0],-200],[r.hands[1][0],-200]];r.handProps=[hand(0,'fist'),hand(1,'fist')];}}});
 const att:Actor2Opt={look:'attacker',x:300,y:1290,s:1.3,expr:'serious',seed:5,light:'street',cast:true,darts:false,breath:1.4,eye:[12,0],
  walk:{x0:300,v:1.6,from:t0-60,cycle:36,lift:16,arms:6},springs:{props:[3,.35]},
  pose:(r,f2)=>{const tt=f2-t0;r.hands=[[-78,-118],[110,-160]];r.handProps=[hand(0,'relaxed'),hand(1,'grip',KNIFE,200+8*Math.sin(tt*.17))];r.head=-2;}};
 const A=flee(700,'passenger',1),B=flee(900,'driver',2),ax=xAt(att,f);
 // framing: attacker close → whip to the two men → pull wide as they run; focus follows the framing
 // framing: attacker → whip to the two men (they notice) → whip back to the attacker as they run off; focus follows
 const onA=(ff:number)=>(xAt(att,ff)-540)*.85,onM=200,w1=whipBetween(f,t0+6,6,onA(t0+6),onM),w2=whipBetween(f,t0+21,6,onM,onA(t0+27));
 const x=t<6?onA(f):t<21?w1.x:t<27?w2.x:onA(f),blurX=w1.blurX+w2.blurX,zoom=1.18+.06*clamp01((t-27)/40),focus=t<8?1.06:t<22?.96:1.06;
 const c=cam({x,zoom,focus,focusAmt:22,blurX,rot:dutch(f,t0+16,10,1.8)},f,[],1.4,11);
 return <AbsoluteFill style={{overflow:'hidden'}}>
  <Stage cam={c} light="street">
   <Layer depth={.3}><AlleyOut/></Layer>
   <Layer depth={.86}><AlleyWall/></Layer>
   <Layer depth={.9}><Motes box={[0,300,1080,900]} n={22} color="#FFF4D6"/></Layer>
   <Layer depth={.96}>
    <Contact x={xAt(A,f)} y={1152} rx={70} light="street"/><Contact x={xAt(B,f)} y={1152} rx={70} light="street"/>
    <Actor2 {...A}/><Actor2 {...B}/>
    <Dust x={xAt(A,f)-20} y={1146} t={t-17} n={4} s={.45} seed={7} color="#BDB7A6"/><Dust x={xAt(B,f)-20} y={1146} t={t-18} n={4} s={.45} seed={9} color="#BDB7A6"/>
   </Layer>
   <Layer depth={1.06}><Contact x={ax} y={1294} rx={120} light="street"/><Actor2 {...att}/></Layer>
   <Layer depth={1.4}><AlleyNear/></Layer>
  </Stage>
 </AbsoluteFill>;
};

// =============== q021 prisoner close-up: rattle, hair rings, take → tired, tears, slow push on the reaction ===============
export const Cell2:React.FC<ShotP>=({t,dur})=>{
 const f=useCurrentFrame(),t0=f-t,PULLS=[7,13,19];
 const rat=(ff:number)=>{const tt=ff-t0;let v=-4*kf(tt,[[2,0],[6,1],[7,0]]);for(const p of PULLS){const d=tt-p;if(d>=0&&d<14)v+=9*Math.exp(-d/3.2)*Math.cos(d*1.5);}return v;};
 const o:Actor2Opt={look:'inmate2',x:540,y:1660,s:1.5,expr:'tired',seed:3,light:'cell',take:[{at:t0+27,from:'concern',amt:.7}],breath:1.6,blinks:[t0+44],
  eye:[0,6],springs:{hands:[9,.6],head:[3,.36],torso:[5,.55],props:null},fx:{sweat:[t0-10,t0+30],tears:[t0+32,t0+200]},
  lookAt:ff=>kf(ff-t0,[[24,0],[30,-.7],[46,-.7],[54,0]]),
  pose:(r,ff)=>{const tt=ff-t0,v=rat(ff),turn=kf(tt,[[26,0],[38,1]]);r.hands=[[-200+v*.6,-330],[200+v*.6,-330]];r.handProps=[hand(0,'fist'),hand(1,'fist')];
   r.hip[0]+=v*.9;r.torso+=v*.25;r.head=v*.5-6*turn;r.hip[1]+=5*turn;}};
 const z=slowPush(f,t0+26,dur-26,.09),c=cam({zoom:z,y:-70*(z-1)/.09,focus:1,focusAmt:20},f,PULLS.map(p=>[t0+p,5] as [number,number]),.7,5);
 return <AbsoluteFill style={{overflow:'hidden'}}>
  <Stage cam={c} light="cell">
   <Layer depth={.3}><CellOut/></Layer>
   <Layer depth={.86}><CellWall/></Layer>
   <Layer depth={.92}><Beam id="cb" pts={[[400,330],[680,330],[860,1720],[260,1720]]} color="#E4F6FF" opacity={.22}/><Motes box={[380,340,420,1300]} n={26} color="#E9FBFF"/></Layer>
   <Layer depth={1}>
    <Contact x={540} y={1664} rx={190} light="cell"/>
    <Actor2 {...o}/>
    <Bars xs={[235,845]} dx={rat(f)*.6}/>
    {PULLS.map((p,i)=><Dust key={p} x={i%2?845:235} y={20} t={t-p} n={3} s={.5} seed={p} color="#9AA4AA" chips="#8C959C" floor={1700}/>)}
   </Layer>
   <Layer depth={1.5}><ForeBars xs={[20,1060]}/></Layer>
  </Stage>
  <Flicker amount={.06} seed={4}/>
 </AbsoluteFill>;
};

// =============== q024 home layers v2: rain on the window, flicker in the door light, DOF on the wall ===============
const Home2:React.FC<{door:number;children:React.ReactNode;near?:React.ReactNode;spill?:number}>=({door,children,near,spill=1})=><>
 <Layer depth={.3}><HomeOut/><Rain box={[60,300,360,380]} n={40} slant={.15} color="#9FB8FF" len={44}/></Layer>
 <Layer depth={.88}><HomeWall door={door} spill={spill}/><PaneDrops box={[66,306,348,368]} n={12}/></Layer>
 <Layer depth={.93}><Beam id="moon" pts={[[60,300],[420,300],[700,1500],[150,1500]]} color="#9FB8FF" opacity={.13}/></Layer>
 <Layer depth={1}>{children}</Layer>
 {near&&<Layer depth={1.45}>{near}</Layer>}
</>;
const SHOVES:[number,number][]=[[2,1],[14,-1],[25,1],[37,-1],[46,1]];
const sway=(tt:number)=>{let p=0;for(const [at,dir] of SHOVES)p+=dir*40*act(tt,at,at+10,10,3,.25);return p-12;};
const Shards:React.FC<{glint:number}>=({glint})=><BlurSvg svgProps={{...S,strokeWidth:6} as React.SVGProps<SVGSVGElement>}>
 {[[180,1830,0,2.2],[430,1880,40,2.6],[700,1820,-30,2.0],[890,1890,70,2.4],[560,1760,110,1.6]].map(([x,y,r,s],i)=><g key={i} transform={`translate(${x} ${y}) rotate(${r}) scale(${s})`}>
  <path d="M0 0l40 -18l22 30l-48 16Z" fill="#EDEFF2"/><path d="M8 -2l22 -10" stroke="#FFFFFF" strokeWidth={3}/>
  {(i+Math.floor(glint/9))%5===0&&<path d="M30 -30v-20M30 -30v20M30 -30h-20M30 -30h20" stroke="#FFFFFF" strokeWidth={4}/>}</g>)}</BlurSvg>;
export const Fight2:React.FC<ShotP>=({t,dur})=>{
 const f=useCurrentFrame(),t0=f-t,cut=Math.round(dur*.55);
 if(t<cut){
  const fighter=(look:'prof'|'snack',x:number,s:number,dir:1|-1,seed:number):Actor2Opt=>({look,x,y:1700,s,expr:look==='prof'?'scared':'angry',seed,light:'homeNight',breath:2.4,eye:[12*dir,0],
   springs:{hands:[6,.5],head:[3.4,.32],torso:[5,.5],props:null},hairAmt:1.4,
   pose:(r,ff)=>{const p=sway(ff-t0);r.hip[0]+=p/s;r.hands=dir>0?[[120+p*.2,-330],[150+p*.2,-260]]:[[-140+p*.2,-330],[-120+p*.2,-250]];r.handProps=[hand(0,'fist'),hand(1,'fist')];
    r.torso=dir*10-p*.5;r.head=-dir*6-p*.35;r.feet=dir>0?[[-40-p*.3,0],[40+p*.15,0]]:[[-40-p*.15,0],[40+p*.3,0]];}});
  const hits=SHOVES.map(([a])=>[t0+a+4,9] as [number,number]);
  const c=cam({...dolly(f,[[t0,{zoom:1.05}],[t0+cut,{zoom:1.1}]]),rot:2.5*Math.sin((f-t0)*.12),focus:1,focusAmt:18},f,hits,2.2,9);
  return <AbsoluteFill style={{overflow:'hidden'}}><Stage cam={c} light="homeNight">
   <Home2 door={.35} spill={flickerAt(f,2)}>
    <Contact x={400} y={1704} rx={150} light="homeNight"/><Contact x={720} y={1704} rx={150} light="homeNight"/>
    <Actor2 {...fighter('prof',400,1.5,1,1)}/><Actor2 {...fighter('snack',720,1.55,-1,4)}/>
    {SHOVES.map(([a],i)=><Dust key={a} x={i%2?380:740} y={1700} t={t-a-4} n={5} s={.75} seed={a} color="#6E6258"/>)}
   </Home2>
  </Stage><Flicker amount={.06} seed={2}/></AbsoluteFill>;
 }
 const u=t-cut;
 const dad:Actor2Opt={look:'prof',x:460,y:1640,s:1.6,expr:'shock',seed:1,light:'homeNight',breath:2.8,eye:[0,12],take:[{at:t0+cut+3,from:'scared',amt:1}],blinks:[t0+cut+22],
  springs:{hands:[4.5,.45],head:[3,.32],torso:[4,.5],props:null},fx:{sweat:[t0+cut+6,t0+cut+200]},
  pose:(r,ff)=>{const uu=ff-t0-cut,d=uu<0?0:act(uu,0,16,16,4,.2),tr=uu>16?2.2*Math.sin(uu*2.1):0;POSE.recoil(r,d,-1);
   r.hands=[[r.hands[0][0]-70*d+tr,r.hands[0][1]+20*d],[r.hands[1][0]+65*d-tr,r.hands[1][1]+20*d+tr]];r.hip[1]+=22*d;},ik:{knee:[[-.4,-1],[.4,-1]]}};
 const c=cam({...dolly(f,[[t0+cut,{focus:1.3}],[t0+cut+2,{focus:1.3}],[t0+cut+10,{focus:1}]]),zoom:slowPush(f,t0+cut,dur-cut,.08),focusAmt:20},f,[],.6,4);
 return <AbsoluteFill style={{overflow:'hidden'}}><Stage cam={c} light="homeNight">
  <Home2 door={.35} near={<Shards glint={u}/>} spill={flickerAt(f,2)}>
   <Contact x={460} y={1644} rx={160} light="homeNight"/><Actor2 {...dad}/>
  </Home2>
 </Stage><Flicker amount={.06} seed={2}/></AbsoluteFill>;
};

// =============== q024 night: pounding at chest height (hands clear of the face), Dutch tilt, rain, flicker ===============
const POUNDS=[4,15,26,37,48,59,70,81];
const poundAt=(tt:number)=>{let v=0,hit=-99;for(const p of POUNDS){const d=tt-p;if(d>=-4&&d<7){v=d<0?-(1-Math.cos(Math.PI*(d+4)/4))/2:d<2?-1+2*Math.pow(d/2,2):d<3?1:1-(d-3)/4;hit=p;}}return {v,hit};};
export const Night2:React.FC<ShotP>=({t,dur,c,u})=>{
 const f=useCurrentFrame(),t0=f-t,frac=clamp01(t/(dur-8));
 const son:Actor2Opt={look:'snack',x:520,y:1700,s:1.6,expr:'angry',seed:6,light:'homeNight',breath:2,eye:[12,0],talk:track(c,u),darts:false,hairAmt:1.3,
  springs:{hands:null,head:[3.2,.34],torso:[5,.5],props:[3,.3]},
  pose:(r,ff)=>{const {v}=poundAt(ff-t0),st=Math.max(0,v),bk=Math.max(0,-v);
   r.hands=[[-82-6*bk,-150+4*st],[228+18*st-30*bk,-336-6*st]];r.handProps=[hand(0,'grip',KNIFE,180+14*st-10*bk),hand(1,'fist')];
   r.torso=8*st-4*bk;r.head=4*st-3*bk;r.hip[0]+=6*st-4*bk;}};
 const hits=POUNDS.map(p=>[t0+p+2,8] as [number,number]);
 const ring=(ff:number)=>{let v=0;for(const p of POUNDS){const d=ff-t0-p-2;if(d>=0&&d<12)v+=Math.exp(-d/3)*Math.cos(d*1.8);}return v;};
 const door=.15+.03*ring(f),{v,hit}=poundAt(t),smr=v>-1&&v<1&&t-hit>=0&&t-hit<2;
 const c2=cam({zoom:slowPush(f,t0,dur,.06),rot:dutch(f,t0,20,-4),focus:1,focusAmt:18},f,hits,1.4,13);
 return <AbsoluteFill style={{overflow:'hidden'}}><Stage cam={c2} light="homeNight">
  <Home2 door={door} spill={.8+.2*flickerAt(f,6)} near={<ForeLamp x={40}/>}>
   <Contact x={520} y={1704} rx={160} light="homeNight"/>
   <Actor2 {...son}/>
   {smr&&<Smear path={[hand2Screen(son,f-1,1),hand2Screen(son,f,1)]} w={40} fill="#F2D2B4" opacity={.9}/>}
   {POUNDS.map(p=><Dust key={p} x={970} y={1170} t={t-p-2} n={3} s={.45} seed={p} color="#C9B8A2" chips="#8A6A4E" spread={.8} floor={1240}/>)}
   <Watch x={250} y={420} s={1.2} sec={180*frac}/>
  </Home2>
 </Stage><Flicker amount={.06} seed={6}/>
 <div style={{...type,position:'absolute',left:60,top:620,width:380,fontSize:86,color:GOLD,zIndex:21}}>{Math.round(60*frac)}분</div></AbsoluteFill>;
};

// =============== NEW: q021 strangers — a walk (v1 slides, v2 plants its feet) ===============
const STR:[ 'passenger'|'snack'|'driver',number,number][]=[['passenger',-60,0],['snack',330,1.4],['driver',720,2.5]];
export const Strangers1:React.FC<ShotP>=({t})=>{const f=useCurrentFrame(),t0=f-t;
 return <AbsoluteFill style={{overflow:'hidden'}}><Stage cam={cam({x:.5*3.4*t,focusAmt:5},f,[],.6,2)} light="street">
  <Layer depth={.3} noBlur><AlleyOut/></Layer><Layer depth={.86} noBlur><AlleyWall/></Layer>
  <Layer depth={1}>{STR.map(([look,x0,ph],i)=>{const o:ActorOpt={look,x:x0+t*3.4,y:1250,s:1.05,expr:'normal',seed:i+1,light:'street',cast:true,eye:[10,0],
   pose:(r,ff)=>{const tt=ff-t0,w=Math.sin(tt*.3+ph);r.feet=[[-30-32*w,-14*Math.max(0,w)],[30+32*w,-14*Math.max(0,-w)]];r.hip[1]+=-4*Math.abs(Math.cos(tt*.3+ph));r.hands=[[-78-14*w,-118],[78+14*w,-118]];}};
   return <React.Fragment key={look}><Contact x={o.x} y={1252} rx={80} light="street"/><Actor {...o}/></React.Fragment>;})}</Layer>
  <Layer depth={1.4}><AlleyNear/></Layer></Stage></AbsoluteFill>;};
export const Strangers2:React.FC<ShotP>=({t})=>{const f=useCurrentFrame(),t0=f-t;
 const A=STR.map(([look,x0,ph],i):Actor2Opt=>({look,x:x0,y:1250,s:1.05,expr:'normal',seed:i+1,light:'street',cast:true,eye:[10,0],
  walk:{x0,v:3.4,from:t0-40-Math.round(ph*8),cycle:26,lift:22,arms:15},lookAt:ff=>i===1?kf(ff-t0,[[30,0],[36,.8],[50,.8],[56,0]]):0}));
 return <AbsoluteFill style={{overflow:'hidden'}}><Stage cam={cam({x:.5*3.4*t,focus:1,focusAmt:20},f,[],.6,2)} light="street">
  <Layer depth={.3}><AlleyOut/></Layer><Layer depth={.86}><AlleyWall/></Layer>
  <Layer depth={.9}><Motes box={[0,300,1080,900]} n={22} color="#FFF4D6"/></Layer>
  <Layer depth={1}>{A.map((o)=><React.Fragment key={o.look}><Contact x={xAt(o,f)} y={1252} rx={80} light="street"/><Actor2 {...o}/></React.Fragment>)}</Layer>
  <Layer depth={1.4}><AlleyNear/></Layer></Stage></AbsoluteFill>;};

// =============== NEW: q024 claim — the father sits down, argues, then head in hands ===============
const Chair:React.FC<{x:number;y:number;s:number;front?:boolean}>=({x,y,s,front})=><svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
 <g transform={`translate(${x} ${y}) scale(${s})`}>{front?<path d="M-88 -100H88V-82H-88Z" fill="#8A6040" strokeWidth={7}/>:<>
  <path d="M-80 -95V-250H80V-95Z" fill="#7A5236" strokeWidth={8}/><path d="M-62 -232H62V-125H-62Z" fill="#8F6444" strokeWidth={6}/>
  <path d="M-92 -100H92V-82H-92Z" fill="#9C7150" strokeWidth={7}/>{[-80,80].map(k=><path key={k} d={`M${k} -84V0`} strokeWidth={12}/>)}</>}</g></svg>;
const claimPose=(t0:number)=>(r:import('../../FightRig').RigPose,ff:number)=>{const tt=ff-t0;
 const p=poseKeys2(tt,[[0,()=>{}],[8,q=>POSE.handsOnKnees(q,1)],[30,q=>{POSE.lean(q,1,-1);q.hands=[[-150,-215],[150,-215]];q.handProps=[{pose:'open'},{pose:'open'}];}],
  [42,q=>{POSE.lean(q,.3,1);q.hands=[[-120,-190],[190,-220]];q.handProps=[{pose:'open'},{pose:'open'}];}],[46,q=>POSE.slump(q,.6)],[52,q=>{POSE.slump(q,1);POSE.handsOnKnees(q,1);q.head+=-4;}]],9);
 applyPose(r,p);};
export const Claim1:React.FC<ShotP>=({t,dur})=>{const f=useCurrentFrame(),t0=f-t;
 const o:ActorOpt={look:'prof',x:540,y:1640,s:1.5,expr:t<50?'concern':'tired',seed:3,light:'court',eye:[0,-4],
  pose:(r,ff)=>{const tt=ff-t0,st=clamp01((tt-8)/18);r.hip[1]+=75*st;r.hands=tt<50?[[-120,-250],[120,-250]]:[[-128,-452],[128,-452]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=tt<50?3*Math.sin(tt*.3):-12;}};
 return <AbsoluteFill style={{overflow:'hidden'}}><Stage cam={cam({zoom:1+.03*t/dur,focusAmt:5},f,[],.5,3)} light="court">
  <Layer depth={.3} noBlur><CourtOut/></Layer><Layer depth={.86} noBlur><CourtWall/><CourtDais/></Layer>
  <Layer depth={1}><Chair x={540} y={1640} s={1.5}/><Actor {...o}/></Layer></Stage></AbsoluteFill>;};
export const Claim2:React.FC<ShotP>=({t,dur,c,u})=>{const f=useCurrentFrame(),t0=f-t;
 const sit=(ff:number)=>{const tt=ff-t0;return tt<8?0:tt<10?-.04*Math.sin(Math.PI*(tt-8)/2):clamp01((tt-10)/16);};
 const o:Actor2Opt={look:'prof',x:540,y:1640,s:1.5,expr:ff=>ff-t0<46?'concern':'tired',seed:3,light:'court',eye:[0,-2],talk:track(c,u),breath:1.6,
  sit,seat:95,take:[{at:t0+46,from:'concern',amt:.6}],blinks:[t0+6,t0+28],fx:{sweat:[t0+30,t0+90],tears:[t0+50,t0+200]},
  lookAt:ff=>kf(ff-t0,[[0,0],[3,-.2],[8,-.2],[14,0],[30,0],[34,-.6],[42,.5],[50,0]]),
  hairAmt:1.2,springs:{hands:[5,.75],head:[3,.38],torso:[4.5,.55],props:null},pose:claimPose(t0)};
 const cc=cam({...dolly(f,[[t0,{zoom:1}],[t0+40,{zoom:1.02}],[t0+dur,{zoom:1.1,y:-40}]]),focus:1,focusAmt:20,rot:dutch(f,t0+52,14,-1.5)},f,[],.5,3);
 return <AbsoluteFill style={{overflow:'hidden'}}><Stage cam={cc} light="court">
  <Layer depth={.3}><CourtOut/></Layer><Layer depth={.86}><CourtWall/><CourtDais/></Layer>
  <Layer depth={.92}><Beam id="cw2" pts={[[105,130],[255,130],[760,1300],[420,1300]]} color="#F4FAFF" opacity={.2}/><Motes box={[150,200,460,1000]} n={24}/></Layer>
  <Layer depth={1}><Contact x={540} y={1644} rx={170} light="court"/><Chair x={540} y={1640} s={1.5}/><Actor2 {...o}/></Layer>
  <Layer depth={1.5}><ForeMonitor x={990} y={1680} flip/></Layer></Stage></AbsoluteFill>;};

// ---------------- films ----------------
type SH=React.FC<ShotP>;
import {Q021Film} from '../../Q021';
import {Q024Film} from '../../Q024';
import {Q021_LOOK} from '../ShotsQ021';
import {Q024_LOOK} from '../ShotsQ024';
const film=(map:Record<string,SH>,Base:React.FC<{c:Case;u:Line;t:number}>)=>({c,u,t}:{c:Case;u:Line;t:number})=>{const Sh=map[u.mode];return Sh?<Sh t={t} dur={u.dur} c={c} u={u}/>:<Base c={c} u={u} t={t}/>;};
export const FILMS_V1:Record<string,React.FC<{c:Case;u:Line;t:number}>>={q021:film({...Q021_LOOK,strangers:Strangers1},Q021Film),q024:film({...Q024_LOOK as Record<string,SH>,claim:Claim1},Q024Film)};
export const FILMS_V2:Record<string,React.FC<{c:Case;u:Line;t:number}>>={q021:film({open:Open2,street:Street2,opinion:Cell2,strangers:Strangers2},Q021Film),q024:film({fight:Fight2,night:Night2,claim:Claim2},Q024Film)};
