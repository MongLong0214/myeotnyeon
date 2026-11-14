import React from 'react';
import {AbsoluteFill,Freeze} from 'remotion';
import {ArticulatedGuy,RigPose} from '../q014/fight_revision/comedy/FightRig';
const I='#1E1712',P='#FFF4D7';
const S={stroke:I,strokeWidth:8,strokeLinecap:'round' as const,strokeLinejoin:'round' as const};
const ease=(x:number)=>{x=Math.min(1,Math.max(0,x));return x*x*(3-2*x)};
const pose=():RigPose=>({hip:[0,-170],torso:0,head:0,feet:[[-30,0],[30,0]],knees:[[-25,-90],[26,-90]],hands:[[-84,-166],[84,-166]],elbows:[[-70,-230],[70,-230]]});
export const TRAIN_SHOTS=[
 [0,.9,'pour'],[.9,1.75,'ignite'],[1.75,3.23,'recoil'],
 [3.23,4.83,'wide'],[4.83,6.43,'close'],[6.43,8.03,'smoke'],[8.03,9.6333,'evacuate'],
 [9.6333,10.4,'figures'],[10.4,11.2,'charge'],[11.2,11.9667,'charge_detail'],
 [11.9667,13.1667,'judge'],[13.1667,14.3667,'defendant'],[14.3667,15.5667,'scales'],
 [15.5667,15.8667,'culprit_snap'],[15.8667,16.1667,'victim_flash'],[16.1667,16.4667,'judge_snap'],[16.4667,16.7667,'scales_sting'],
 [16.7667,17,'judge_prepare'],[17,21.8667,'choice_hold'],
 [21.8667,21.9667,'verdict_snap'],[21.9667,22.5667,'deadpan'],[22.5667,23.5667,'judge_reply'],[23.5667,24.3667,'defendant_tail'],
] as const;
export const trainShot=(time:number)=>{const f=Math.round(time*30);return TRAIN_SHOTS.find(s=>f>=Math.round(s[0]*30)&&f<Math.round(s[1]*30))??TRAIN_SHOTS.at(-1)!};
export const isTrainCourt=(mode:string)=>['judge','defendant','culprit_snap','judge_snap','judge_prepare','choice_hold','verdict_snap','deadpan','judge_reply','defendant_tail'].includes(mode);
export const isTrainMetaphor=(mode:string)=>['figures','charge','charge_detail','scales','scales_sting'].includes(mode);
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
const Figure:React.FC<{x:number;y:number;scale?:number}>=({x,y,scale=1})=><g transform={`translate(${x} ${y}) scale(${scale})`}><path d="M-17,0h34l8,47h-50zM-10,43v32m20,-32v32" fill="#385E6B" stroke="#385E6B" strokeWidth={12}/><circle cy={-19} r={13} fill="#F3CF9F" stroke={I} strokeWidth={1.5}/><circle cx={-4.5} cy={-23} r={3.5} fill="white"/><circle cx={4.5} cy={-23} r={3.5} fill="white"/><circle cx={-4.5} cy={-23} r={1.4} fill={I}/><circle cx={4.5} cy={-23} r={1.4} fill={I}/><path d="M0,-21v5h2M-5,-11q5,-4 10,0" stroke={I} strokeWidth={1.3} fill="none"/></g>;
const Gavel:React.FC<{angle:number;impact:number}>=({angle,impact})=><svg width="1000" height="1100"><rect x={707} y={831} width={158} height={22} rx={9} fill="#5F4330" {...S}/><g transform={`translate(700 690) rotate(${angle})`}><path d="M0,0L55,118" stroke={I} strokeWidth={29}/><path d="M0,0L55,118" stroke="#A5794B" strokeWidth={15}/><g transform={`translate(55 120) scale(${1+.14*impact} ${1-.14*impact}) translate(-55 -120)`}><rect x={0} y={90} width={115} height={60} rx={12} fill="#B88D57" {...S}/><path d="M15,94v52m85,-52v52" stroke="#714F30" strokeWidth={8}/></g></g>{impact>0&&<g opacity={impact} stroke="#FFD400" strokeWidth={13} strokeLinecap="round"><path d="M740,820l-55,-45m115,45l55,-45m-90,25v-65m-22,110l-85,13m150,-13l65,13"/></g>}</svg>;
const Pencils:React.FC<{frame:number}>=({frame})=>{
 const elapsed=frame-656,recoil=elapsed>=0&&elapsed<32?-15*Math.sin((elapsed+2)/3)*Math.exp(-elapsed/8):0;
 return <svg width="1000" height="1100"><g transform={`rotate(${recoil} 550 805)`}>{[530,550,570].map((x,i)=><g key={x}><path d={`M${x-5},805V${715+i*13}l5,-16 5,16v${90-i*13}Z`} fill={['#D5AB5D','#6A9F98','#BC7560'][i]} stroke={I} strokeWidth={4}/></g>)}</g><path d="M515,765H585L578,835H522Z" fill="#6B8C84" stroke={I} strokeWidth={6}/></svg>;
};
const Sweat=()=> <svg width="1000" height="1100"><path d="M409,500Q389,527 406,535Q427,539 423,519Z" fill="#A4D7E4" stroke={I} strokeWidth={3}/></svg>;
export const TrainFilm:React.FC<{time:number}>=({time})=>{
 const [start,end,mode]=trainShot(time),t=time-start,deadpan=mode==='deadpan',p=deadpan?0:ease(t/(end-start));
 const frame=Math.round(time*30),local=frame-Math.round(start*30),snap=ease(local/3);
 const a=pose(),j=pose();a.hands[1]=[168,-215];a.elbows![1]=[110,-300];a.torso=15;
 const canAngle=(mode==='pour'?40+30*p:0)*Math.PI/180,canX=433+18*p,canY=815+12*p;
 const tipX=canX+100*Math.cos(canAngle)-8*Math.sin(canAngle),tipY=canY+100*Math.sin(canAngle)+8*Math.cos(canAngle);
 if(mode==='pour'){a.torso=15+10*p;a.hands[1]=[165+20*p,-215+15*p];}
 const legal=isTrainCourt(mode),metaphor=isTrainMetaphor(mode);
 let scale=1,origin='50% 70%';
 if(mode==='pour'){scale=1.45+.2*p;origin='45% 91%';}
 if(mode==='ignite'){scale=1.05+.12*p;origin='50% 70%';}
 if(['recoil','close'].includes(mode)){scale=1.65+.10*p;origin='77% 49%';}
 if(mode==='smoke'){scale=1.05+.12*p;}
 if(mode==='judge'){scale=1.05+.12*p;origin='50% 70%';}
 if(['judge_snap','judge_prepare','judge_reply'].includes(mode)){scale=1.30+.23*snap;origin='100% 45%';}
 if(['defendant','culprit_snap','defendant_tail'].includes(mode)){scale=1.32+.36*snap;origin='0% 48%';}
 if(mode==='verdict_snap'){scale=1.08+.46*ease((local+1)/3);origin='100% 45%';}
 if(deadpan){scale=1.65;origin='0% 48%';}
 if(mode==='choice_hold'){scale=1.03;origin='50% 70%';}
 const verdict=mode==='verdict_snap',gavelAngle=verdict?0:mode==='judge_prepare'?-10-60*p:mode==='choice_hold'?-70:-30-25*p;
 j.head=mode==='judge'?-10+14*p:0;j.torso=0;j.hands[1]=[0,-241];j.elbows![1]=[125,-310];j.hands[0]=[-105-45*p,-220-45*p];
 const glasses=mode==='judge_prepare'?p:mode==='choice_hold'&&frame>=648?ease((frame-648)/7):mode==='judge_reply'?(1-ease(local/7)):0;
 j.hands[0]=[-105+70*glasses,-220-280*glasses];j.elbows![0]=[-120,-330-30*glasses];
 const d=pose();const choicePose=mode==='choice_hold'?Math.min(3,Math.floor(local/12)):-1;
 d.head=deadpan?0:choicePose>=0?[0,8,-7,0][choicePose]:['defendant','culprit_snap','defendant_tail'].includes(mode)?-6+15*p:4;
 d.torso=deadpan?0:choicePose>=0?[0,-8,8,0][choicePose]:['defendant','culprit_snap'].includes(mode)?-6+15*p:3*p;
 d.hands=deadpan?[[-36,-218],[48,-228]]:choicePose>=0?([[[ -70,-190],[70,-190]],[[-120,-240],[130,-260]],[[-115,-290],[115,-280]],[[-36,-218],[48,-228]]] as RigPose['hands'][])[choicePose]:[[-62-65*p,-185-70*p],[62+50*p,-185-85*p]];
 const defendantExpr=deadpan?'serious':choicePose===2?'angry':['defendant','culprit_snap'].includes(mode)&&local<7?'shock':'concern';
 const defendantOnly=['defendant','culprit_snap','deadpan','defendant_tail'].includes(mode);
 const judgeOnly=['judge_snap','judge_prepare','judge_reply','verdict_snap'].includes(mode);
 return <AbsoluteFill className="stage" style={{width:1000,height:1100,overflow:'hidden'}}>
 <AbsoluteFill style={{width:1000,height:1100,transform:`scale(${scale})`,transformOrigin:origin}}>
 {legal?<><Court/>
  {!judgeOnly&&(deadpan?<Freeze frame={659}><ArticulatedGuy look="hoodie" x={290} y={1050} scale={.86} rig={d} expr="serious" eye={[-7,0]}/></Freeze>:<ArticulatedGuy look="hoodie" x={290} y={1050} scale={.86} rig={d} expr={defendantExpr} eye={[choicePose>=0?[-12,0,12,-6][choicePose]:14-22*p+(local<7?Math.sin(local*2)*4:0),4]}/>)}
  {!defendantOnly&&<ArticulatedGuy look="judge" x={700} y={895} scale={.85} rig={j} expr="serious" eye={[-14,0]}/>}
  <svg width="1000" height="1100"><path d="M480,840H980V1080H480Z" fill="#9F714E" {...S}/><path d="M475,840H990" stroke={I} strokeWidth={24}/></svg>
  {!defendantOnly&&<Pencils frame={frame}/>}
  {!defendantOnly&&<Gavel angle={gavelAngle} impact={verdict?1-ease(t/.2):0}/>}
  {deadpan&&<Sweat/>}
  {mode==='judge_reply'&&<svg width="1000" height="1100"><path d="M200,1100V570Q390,550 500,760Q580,900 580,1100Z" fill="#2E2E33" {...S}/><path d="M350,610Q470,740 525,1010" fill="none" stroke="#46464D" strokeWidth={18}/><path d="M420,820l-15,95m55,-80l-8,80" fill="none" stroke="#E4E4E4" strokeWidth={8}/></svg>}
 </>:metaphor?<>
  <svg width="1000" height="1100"><rect width="1000" height="1100" fill="#E3E7CF"/>
   {['figures','charge','charge_detail'].includes(mode)?<>
    <g transform={`translate(${mode==='figures'?710:730} ${800-100*p}) scale(${mode==='figures'?.85+.15*p:mode==='charge_detail'?1.15:1.1+.1*p})`}><text textAnchor="middle" y={-140} fontFamily="Pretendard" fontWeight={800} fontSize={45} fill={I}>살인미수 혐의</text><text textAnchor="middle" y={25} fontFamily="Pretendard" fontWeight={800} fontSize={150} fill={I}>160명</text></g>
   </>:<>
    <path d="M500,390v570m-110,10h220" fill="#F2C14E" {...S}/>
    <g transform={`rotate(${-13+27*p+8*Math.sin(local*.9)*Math.exp(-local/4)} 500 500)`}><path d="M260,500H740M290,500l-135,270h270zM710,500l-135,270h270z" fill="#F2C14E" {...S}/>
    <g transform="translate(285 680)"><text textAnchor="middle" fontFamily="Pretendard" fontSize={84} fontWeight={800} fill={I}>160</text></g>
    <g transform="translate(710 680)"><text textAnchor="middle" y={20} fontFamily="Pretendard" fontSize={110} fontWeight={800} fill={I}>?</text></g></g>
   </>}
  </svg>
  {!['scales','scales_sting'].includes(mode)&&(()=>{const r=pose();r.head=-5+8*p;r.torso=-4+5*p;r.hands=[[-45,-260],[105,-230]];return <ArticulatedGuy look="B" x={270} y={1070} scale={mode==='charge'?1.05:.9} rig={r} expr="concern" eye={[8-16*p,0]}/>;})()}
 </>:mode==='victim_flash'?<><Interior/>{(()=>{const r=pose();r.head=-5+5*p;r.torso=-8;r.hands=[[-45,-260],[110,-230]];r.elbows=[[-100,-280],[125,-310]];return <ArticulatedGuy look="B" x={580} y={1070} scale={1.26} rig={r} expr="concern" eye={[-10,3]}/>;})()}</>:<>
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
