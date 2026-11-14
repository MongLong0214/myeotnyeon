import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ArticulatedGuy,RigPose} from '../q014/fight_revision/comedy/FightRig';
const I='#1E1712',P='#FFF4D7';
const S={stroke:I,strokeWidth:8,strokeLinecap:'round' as const,strokeLinejoin:'round' as const};
const ease=(x:number)=>{x=Math.min(1,Math.max(0,x));return x*x*(3-2*x)};
const pose=():RigPose=>({hip:[0,-170],torso:0,head:0,feet:[[-30,0],[30,0]],knees:[[-25,-90],[26,-90]],hands:[[-84,-166],[84,-166]],elbows:[[-70,-230],[70,-230]]});
export const TRAIN_SHOTS=[
 [0,.9,'pour'],[.9,1.75,'ignite'],[1.75,3.23,'recoil'],
 [3.23,4.83,'wide'],[4.83,6.43,'close'],[6.43,8.03,'smoke'],[8.03,9.63,'evacuate'],[9.63,11.9667,'figures'],
 [11.9667,13.5667,'judge'],[13.5667,15.1667,'defendant'],[15.1667,16.8667,'scales'],[16.8667,18.5667,'judge'],[18.5667,20.1667,'defendant'],[20.1667,21.8667,'scales'],[21.8667,24.3667,'verdict'],
] as const;
export const trainShot=(time:number)=>{const f=Math.round(time*30);return TRAIN_SHOTS.find(s=>f>=Math.round(s[0]*30)&&f<Math.round(s[1]*30))??TRAIN_SHOTS.at(-1)!};
const Interior=()=> <svg width="1000" height="1100" viewBox="0 0 1000 1100">
 <rect width="1000" height="1100" fill="#D0DCDA"/><path d="M0,70H1000M0,150H1000" {...S}/>
 {[40,370,700].map(x=><g key={x}><rect x={x} y={230} width={265} height={370} rx={36} fill="#4D6470" {...S}/><path d={`M${x+20},${520}l210,-160`} stroke="#617D88" strokeWidth={25}/><rect x={x} y={690} width={265} height={160} rx={22} fill="#3E9D99" {...S}/></g>)}
 <path d="M0,860H1000V1100H0Z" fill="#8E999D" {...S}/><path d="M330,150v700M680,150v700" stroke={I} strokeWidth={17}/><path d="M345,150v680M695,150v680" stroke="#E6E9DE" strokeWidth={7}/>
 <path d="M80,920H920M40,1020H960" stroke="#AAB3B3" strokeWidth={5}/>
 </svg>;
const Flames:React.FC<{growth:number;time:number}>=({growth,time})=>{
 const h=80+growth*650,w=110+growth*360,flicker=25*Math.sin(time*11);
 return <svg width="1000" height="1100"><ellipse cx={520} cy={1050} rx={w} ry={45} fill="#C28736" opacity={.7}/>
 <g transform={`translate(520 1070) scale(${w/450} ${h/600})`}>
  <path d={`M-450,0Q-480,-130 -350,-230Q-400,-360 -260,-470Q-285,-290 -160,-270Q-70,-450 -90,${-650+flicker}Q80,-520 75,-340Q200,-380 235,${-600-flicker}Q360,-470 290,-260Q390,-340 410,-430Q490,-200 430,0Z`} fill="#D75929" {...S}/>
  <path d={`M-355,0Q-390,-110 -245,-250Q-270,-355 -180,-410Q-210,-220 -70,-190Q40,-330 15,${-490-flicker}Q170,-350 140,-185Q260,-270 290,-370Q385,-140 350,0Z`} fill="#F29732" stroke={I} strokeWidth={5}/>
  <path d="M-190,0Q-235,-100 -120,-200Q-105,-120 -25,-90Q65,-160 60,-290Q180,-150 185,0Z" fill="#FFE075"/>
 </g></svg>;
};
const Passenger:React.FC<{reaction:number;x?:number;y?:number;scale?:number;walk?:number}>=({reaction,x=765,y=1030,scale=.88,walk=0})=>{
 const r=pose();r.hip=[15*reaction,-170+10*reaction];r.torso=-25*reaction;r.head=15*reaction;
 r.hands=[[-90-75*reaction,-166-140*reaction],[84+75*reaction,-166-125*reaction]];
 r.elbows=[[-90-40*reaction,-230-70*reaction],[90+50*reaction,-230-60*reaction]];
 if(walk){r.feet=[[-30-60*Math.sin(walk),-25*Math.max(0,Math.cos(walk))],[30+60*Math.sin(walk),-25*Math.max(0,-Math.cos(walk))]];r.knees=[[-50,-100],[70,-80]];r.hands=[[-100,-200],[120,-240]];r.torso=18;}
 return <ArticulatedGuy look="B" x={x} y={y} scale={scale} rig={r} expr="scared" eye={[-14,0]}/>;
};
const Smoke:React.FC<{t:number;amount:number}>=({t,amount})=><svg width="1000" height="1100">{Array.from({length:10},(_,i)=><ellipse key={i} cx={80+i%4*300+20*Math.sin(t+i)} cy={220+Math.floor(i/4)*290-50*t} rx={220} ry={190} fill={i%2?'#626E74':'#8A9497'} opacity={amount*(.24+i*.025)}/>)}</svg>;
const Court=()=> <svg width="1000" height="1100"><rect width="1000" height="1100" fill="#C9D4AF"/><path d="M0,880H1000V1100H0Z" fill="#A47B57" {...S}/><rect x={70} y={120} width={860} height={670} rx={35} fill="#AABE91" {...S}/>{[220,500,780].map(x=><path key={x} d={`M${x},150v600`} stroke="#8FA87A" strokeWidth={55}/>)}<path d="M500,190v190m-130,-110h260m-250,0l-46,95h92zm250,0l-46,95h92z" fill={P} {...S}/></svg>;
const Figure:React.FC<{x:number;y:number;scale?:number}>=({x,y,scale=1})=><g transform={`translate(${x} ${y}) scale(${scale})`} fill="#385E6B"><circle cy={-19} r={13}/><path d="M-17,0h34l8,47h-50zM-10,43v32m20,-32v32" stroke="#385E6B" strokeWidth={12}/></g>;
export const TrainFilm:React.FC<{time:number}>=({time})=>{
 const [start,end,mode]=trainShot(time),t=time-start,p=ease(t/(end-start));
 const a=pose(),j=pose();a.hands[1]=[168,-215];a.elbows![1]=[110,-300];a.torso=15;
 const canAngle=(mode==='pour'?40+30*p:0)*Math.PI/180,canX=433+18*p,canY=815+12*p;
 const tipX=canX+100*Math.cos(canAngle)-8*Math.sin(canAngle),tipY=canY+100*Math.sin(canAngle)+8*Math.cos(canAngle);
 if(mode==='pour'){a.torso=15+10*p;a.hands[1]=[165+20*p,-215+15*p];}
 const legal=['judge','defendant','verdict'].includes(mode),metaphor=['figures','scales'].includes(mode);
 let scale=1,origin='50% 70%';
 if(mode==='pour'){scale=1.45+.2*p;origin='45% 91%';}
 if(mode==='ignite'){scale=1.05+.12*p;origin='50% 70%';}
 if(['recoil','close'].includes(mode)){scale=1.65+.10*p;origin='77% 49%';}
 if(mode==='smoke'){scale=1.05+.12*p;}
 if(mode==='judge'||mode==='verdict'){scale=mode==='judge'?1.50+.10*p:1.15+.22*p;origin='65% 45%';}
 if(mode==='defendant'){scale=1.75+.12*p;origin='30% 48%';}
 j.head=mode==='judge'?-10+20*p:0;j.hands[1]=[125+80*p,-250-80*p];j.elbows![1]=[90,-330];j.hands[0]=[-105,-220];
 const d=pose();d.head=mode==='defendant'?20*p:7;d.torso=10*p;d.hands=[[-62,-185],[62,-185]];
 return <AbsoluteFill className="stage" style={{width:1000,height:1100,overflow:'hidden'}}>
 <AbsoluteFill style={{width:1000,height:1100,transform:`scale(${scale})`,transformOrigin:origin}}>
 {legal?<><Court/>
  <ArticulatedGuy look="hoodie" x={290} y={1050} scale={.86} rig={d} expr={p<.5?'serious':'concern'} eye={[14,4]}/>
  <ArticulatedGuy look="judge" x={700} y={895} scale={.85} rig={j} expr={p<.5?'serious':'angry'} eye={[-14,0]}/>
  <svg width="1000" height="1100"><path d="M480,840H980V1080H480Z" fill="#9F714E" {...S}/><path d="M475,840H990" stroke={I} strokeWidth={24}/></svg>
 </>:metaphor?<>
  <svg width="1000" height="1100"><rect width="1000" height="1100" fill="#E3E7CF"/>
   {mode==='figures'?<>
    {Array.from({length:160},(_,i)=><g key={i} opacity={p<.75?1:1-(p-.75)*3}><Figure x={70+i%16*57} y={150+Math.floor(i/16)*58} scale={.4}/></g>)}
    <g transform={`translate(500 ${900-100*p}) scale(${.8+.2*p})`}><rect x={-240} y={-100} width={480} height={180} rx={24} fill={P} {...S}/><text textAnchor="middle" dominantBaseline="middle" y={0} fontFamily="Pretendard" fontWeight={800} fontSize={124} fill={I}>160</text></g>
   </>:<>
    <path d="M500,390v570m-110,10h220M260,500H740M290,500l-135,270h270zM710,500l-135,270h270z" fill="#F2C14E" {...S}/>
    <g transform={`translate(285 ${680-40*p})`}><rect x={-115} y={-80} width={230} height={130} rx={15} fill={P} {...S}/><text textAnchor="middle" fontFamily="Pretendard" fontSize={84} fontWeight={800} fill={I}>160</text></g>
    <g transform={`translate(710 ${680+40*p})`}><rect x={-100} y={-75} width={200} height={130} rx={15} fill={P} {...S}/><text textAnchor="middle" y={20} fontFamily="Pretendard" fontSize={110} fontWeight={800} fill={I}>?</text></g>
    <Figure x={500} y={220} scale={1.4}/>
   </>}
  </svg>
 </>:<>
  <Interior/>
  {mode!=='evacuate'&&<ArticulatedGuy look="hoodie" x={285} y={1030} scale={.9} rig={a} expr="serious" eye={[12,12]}/>}
  {mode==='evacuate'?<>
   <svg width="1000" height="1100"><rect x={770} y={160} width={230} height={700} fill="#F0E7C8" {...S}/><path d="M780,170L960,840" stroke="#91B0A1" strokeWidth={20}/></svg>
   <Passenger x={340+480*p} y={1040} reaction={.5} walk={t*7+.2}/><Passenger x={80+480*p} y={1030} scale={.7} reaction={.5} walk={t*7+2}/>
  </>:<Passenger reaction={['recoil','close'].includes(mode)?ease((t+.12)/.55):.25} x={['recoil','close'].includes(mode)?760+35*p:765}/>}
  {['pour','ignite'].includes(mode)&&<svg width="1000" height="1100"><g transform={`translate(${canX} ${canY}) rotate(${canAngle*180/Math.PI})`}><path d="M-62,-40H45V95H-62ZM-35,-40v-28h48v28M45,-18l55,10v34H45" fill="#B99258" {...S}/><rect x={-40} y={-10} width={56} height={58} fill={P} stroke={I} strokeWidth={5}/></g>{mode==='pour'&&<><path d={`M${tipX},${tipY}Q${tipX+30},970 600,1030`} stroke="#9C824C" strokeWidth={20} fill="none"/><ellipse cx={600} cy={1035} rx={80+80*p} ry={22+15*p} fill="#B9A066"/></>}</svg>}
  {!['pour','recoil','close','evacuate'].includes(mode)&&<Flames growth={mode==='ignite'?.02+.93*p:.65+.08*Math.sin(time*2)} time={time}/>}
  {['recoil','close'].includes(mode)&&<svg width="1000" height="1100"><path d="M150,1100q-80,-150 50,-330q-10,120 100,180q80,-130 110,-300q150,190 140,450Z" fill="#EE8B32" stroke={I} strokeWidth={8}/></svg>}
  {['smoke','evacuate','wide'].includes(mode)&&<Smoke t={t} amount={mode==='smoke'?.5+.5*p:mode==='wide'?.35:.65}/>}
 </>}
 </AbsoluteFill>
 </AbsoluteFill>;
};
