import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ArticulatedGuy,RigPose} from '../q014/fight_revision/comedy/FightRig';
import {Reenactment} from './Reenactment';
import {TrainFilm} from './TrainFilm';
const I='#1E1712',P='#FFF4D7',S={stroke:I,strokeWidth:8,strokeLinejoin:'round' as const,strokeLinecap:'round' as const};
const ease=(x:number)=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x)};
const pose=():RigPose=>({hip:[0,-170],torso:0,head:0,feet:[[-30,0],[30,0]],knees:[[-25,-90],[26,-90]],hands:[[-84,-166],[84,-166]],elbows:[[-70,-230],[70,-230]]});
type U={mode:string;from_frame:number;dur:number};
type FilmCase={kind:string;qid:string;utterances:U[]};
export const caseBeat=(c:FilmCase,f:number)=>{
 const u=c.utterances.find(u=>f>=u.from_frame&&f<u.from_frame+u.dur)??c.utterances.at(-1)!;
 const j=c.utterances.indexOf(u),local=f-u.from_frame;
 if(j===0){const mode=local<27?'action':local<51?'reaction':local<99?'impact':'detail';return {mode,local:local<27?local:local<51?local-27:local<99?local-51:local-99,j,metaphor:false};}
 const count=Math.max(1,Math.round(u.dur/51)),size=u.dur/count,index=Math.min(count-1,Math.floor(local/size));
 let mode=j<=2?(['reaction','detail','counter'] as const)[index%3]:j===5?(index%2?'defendant':'verdict'):['judge','defendant','counter'][index%3];
 if(j===1&&c.kind==='parking'&&index===2)mode='reaction';
 if(j===4&&c.kind==='parking'&&index===2)mode='deposit';
 if(j===1&&c.kind==='street')mode=index%2?'reaction':'counter';
 if(j===1&&c.kind==='rolls')mode=index%2?'consequence':'reaction';
 if(j===2)mode=c.kind==='parking'?(index%2?'defendant':'deposit'):c.kind==='kick'?(index%2?'defendant':'camera'):c.kind==='rolls'||c.kind==='street'?(index%2?'defendant':'judge'):index%2?'reaction':'counter';
 if(j===3&&c.kind==='parking'&&index===2)mode='deposit';
 if(j===6)mode='teaser';
 return {mode,local:local-index*size,j,metaphor:['counter','consequence','deposit','camera'].includes(mode)};
};
export const CaseFilm:React.FC<{c:FilmCase;frame:number}>=({c,frame})=>{
 const b=caseBeat(c,frame),u=c.utterances[b.j],t=b.local/30,p=ease(t/1.55),a=pose(),v=pose();
 if(['judge','verdict','defendant'].includes(b.mode))return <TrainFilm time={b.mode==='defendant'?13.5667+Math.min(1.55,t):b.mode==='verdict'?21.8667+Math.min(2.4,t):11.9667+Math.min(1.55,t)}/>;
 if(b.mode==='deposit')return <Deposit p={p}/>;
 if(b.mode==='camera')return <Camera p={p}/>;
 if(b.mode==='counter')return <Counter kind={c.kind} p={p}/>;
 if(b.mode==='consequence')return <Consequence kind={c.kind} p={p}/>;
 if(c.kind==='parking')return <Assault mode={b.mode} t={t} p={p}/>;
 if(c.kind==='street')return <Street mode={b.mode} t={t} p={p}/>;
 if(c.kind==='store'||c.kind==='blanket'){
  const action=b.mode==='action',impact=b.mode==='impact',mode=action?'action':c.kind==='store'&&impact?'reaction':b.mode==='detail'?'result':'action';
  const sceneFrame=action?b.local:mode==='reaction'?b.local:24+Math.round(t*5);
  return <AbsoluteFill className="stage" style={{width:1000,height:1100,overflow:'hidden',background:c.kind==='store'?'#B4C4B1':'#AA987D'}}>
   <div style={{position:'absolute',top:110,width:1000,height:900,transform:`scale(${b.mode==='detail'?1.85:1.53+.10*p})`,transformOrigin:c.kind==='blanket'?'55% 78%':b.mode==='detail'?'67% 45%':'50% 72%'}}><Reenactment kind={c.kind} mode={mode} frame={sceneFrame} length={55}/></div>
  </AbsoluteFill>;
 }
 if(c.kind==='kick')return <Kick mode={b.mode} t={t} p={p}/>;
 if(c.kind==='rolls')return <Collision mode={b.mode} t={t} p={p}/>;
 return <Dogs mode={b.mode} t={t} p={p}/>;
};
const Parking=()=> <svg width="1000" height="1100"><rect width="1000" height="1100" fill="#526371"/><path d="M0,0H1000V120H0Z" fill="#B9C2B2" {...S}/><path d="M0,850H1000V1100H0Z" fill="#929B9B" {...S}/>{[70,850].map(x=><rect key={x} x={x} y={120} width={60} height={730} fill="#A2ACA0" {...S}/>)}<path d="M0,1040L370,870M670,1100L950,900" stroke={P} strokeWidth={16}/><rect x={20} y={570} width={290} height={250} rx={30} fill="#899FA7" {...S}/><circle cx={80} cy={835} r={38} fill={I}/><circle cx={270} cy={835} r={38} fill={I}/></svg>;
const Kick:React.FC<{mode:string;t:number;p:number}>=({mode,t,p})=>{
 const a=pose(),v=pose(),w=pose(),fall=mode==='action'?ease((t+.2)/.65):1;
 a.feet[1]=[270,-8];a.knees[1]=[130,-95];a.torso=18;a.hands=[[-90,-190],[80,-240]];
 v.hip=[70*fall,-170+130*fall];v.torso=60*fall;v.head=20*fall;v.knees=[[-25+110*fall,-90+80*fall],[26+100*fall,-90+80*fall]];v.hands=[[-84+220*fall,-166+150*fall],[84+110*fall,-166+150*fall]];
 const strike=mode==='impact'?ease((t+.05)/.35):mode==='reaction'?0:0;
 w.feet[0]=[-30,0];w.feet[1]=[30-245*strike,-320*strike];w.knees[1]=[-85*strike,-90-110*strike];w.torso=-12;w.hands=[[-85,-190],[85,-210]];
 const close=mode==='detail'||mode==='reaction';
 return <AbsoluteFill className="stage" style={{width:1000,height:1100,overflow:'hidden'}}><AbsoluteFill style={{width:1000,height:1100,transform:`scale(${close?1.4+.12*p:1.05+.09*p})`,transformOrigin:close?'72% 75%':'55% 75%'}}>
  <Parking/><ArticulatedGuy look="hoodie" x={350} y={1000} scale={.78} rig={a} expr="serious" eye={[12,0]}/>
  <ArticulatedGuy look="B" x={590} y={1000} scale={.82} rig={v} expr="scared" eye={[-10,0]}/>
  <ArticulatedGuy look="hoodie" x={895} y={1000} scale={.66} rig={w} expr="serious" eye={[-12,0]}/>
 </AbsoluteFill></AbsoluteFill>;
};
const Collision:React.FC<{mode:string;t:number;p:number}>=({mode,t,p})=>{
 const r=pose(),fall=mode==='action'?ease((t+.18)/.65):1;
 r.hip=[60*fall,-170+80*fall];r.torso=50*fall;r.head=-10+25*fall;r.hands=[[-90+170*fall,-200+170*fall],[100+80*fall,-220+180*fall]];r.knees=[[-25+50*fall,-90+45*fall],[26+90*fall,-90+50*fall]];
 const carX=mode==='action'?40*fall:40,close=mode==='reaction'||mode==='detail';
 return <AbsoluteFill className="stage" style={{width:1000,height:1100,overflow:'hidden'}}><AbsoluteFill style={{width:1000,height:1100,transform:`scale(${close?1.5+.1*p:1.15+.08*p})`,transformOrigin:close?'72% 65%':'50% 78%'}}>
  <svg width="1000" height="1100"><rect width="1000" height="1100" fill="#343F51"/><rect x={30} y={120} width={940} height={650} fill="#697275" {...S}/>{[100,420,740].map(x=><rect key={x} x={x} y={210} width={160} height={230} fill="#DCC998" {...S}/>)}<path d="M0,810H1000V1100H0Z" fill="#B9B7A7" {...S}/><path d="M0,1050H1000" stroke={I} strokeWidth={18}/><path d="M0,1080H1000" stroke="#6C7778" strokeWidth={35}/></svg>
  <ArticulatedGuy look="B" x={650+55*fall} y={1020} scale={.83} rig={r} expr="scared" eye={[-12,0]}/>
  <svg width="1000" height="1100"><g transform={`translate(${carX} 0)`}><path d="M-100,735L95,690L195,555H395L505,700H615Q660,700 665,770V930H-100Z" fill="#72858E" {...S}/><path d="M210,580H375L455,690H145Z" fill="#3B4E5C" {...S}/><rect x={500} y={765} width={130} height={95} rx={12} fill="#C0C5BD" {...S}/><path d="M515,775v75m25,-75v75m25,-75v75m25,-75v75m25,-75v75" stroke={I} strokeWidth={7}/><circle cx={110} cy={930} r={83} fill={I}/><circle cx={110} cy={930} r={42} fill="#A0AEAD"/><circle cx={500} cy={930} r={83} fill={I}/><circle cx={500} cy={930} r={42} fill="#A0AEAD"/><path d="M-70,910H650" stroke={I} strokeWidth={13}/></g></svg>
 </AbsoluteFill></AbsoluteFill>;
};
const Dog:React.FC<{x:number;y:number;s?:number;covered?:boolean}>=({x,y,s=1,covered})=><g transform={`translate(${x} ${y}) scale(${s})`} {...S}>
 <ellipse rx={185} ry={85} fill={covered?'#E3E3DA':'#CBAA7C'}/><path d="M-130,-20Q-230,-150 -250,-65Q-270,-30 -230,10L-150,45" fill="#CBAA7C"/><ellipse cx={-230} cy={-27} rx={19} ry={14} fill={I}/><path d="M-235,-70q25,-50 65,10" fill="#92754F"/><path d="M-193,-56l15,4" strokeWidth={7}/><path d="M-100,55v30m100,-5v20m100,-45v30M170,-15q90,-50 100,25" fill="none"/>
 {covered&&<path d="M-140,-30Q0,-155 180,-20V80H-140Z" fill="#E6E6DC"/>}
 </g>;
const Dogs:React.FC<{mode:string;t:number;p:number}>=({mode,t,p})=>{
 const a=pose();a.torso=18+12*p;a.head=15;a.hands=[[-60,-205],[220+40*p,-185-20*p]];a.elbows=[[-90,-260],[120,-280]];
 return <AbsoluteFill className="stage" style={{width:1000,height:1100,overflow:'hidden'}}><AbsoluteFill style={{width:1000,height:1100,transform:`scale(${mode==='detail'?1.45:1.12+.12*p})`,transformOrigin:'55% 69%'}}>
  <svg width="1000" height="1100"><rect width="1000" height="1100" fill="#C8D3B9"/>{[70,390,710].map(x=><g key={x}><rect x={x} y={180} width={240} height={480} fill="#B4BFA8" {...S}/>{[40,100,160,220].map(k=><path key={k} d={`M${x+k},180v480`} stroke={I} strokeWidth={7}/>)}</g>)}<path d="M0,850H1000V1100H0Z" fill="#A99B85" {...S}/></svg>
  <ArticulatedGuy look="hoodie" x={330} y={1060} scale={.9} rig={a} expr="serious" eye={[15,15]}/>
  <svg width="1000" height="1100"><path d="M470,890H950V940H470ZM500,940v130m420,-130v130" fill="#86735A" {...S}/><Dog x={720} y={838} s={.8} covered={mode==='detail'}/>{mode==='action'&&<path d={`M${610+25*p},815q35,${10+15*p} 85,0`} stroke={I} strokeWidth={7} fill="none"/>}</svg>
 </AbsoluteFill></AbsoluteFill>;
};
const Counter:React.FC<{kind:string;p:number}>=({kind,p})=>{
 const n=kind==='dogs'?92:kind==='blanket'?3:kind==='store'?2:kind==='kick'?2:kind==='street'?4:1;
 return <AbsoluteFill className="stage" style={{width:1000,height:1100,overflow:'hidden'}}><svg width="1000" height="1100"><rect width="1000" height="1100" fill="#E1E6C9"/><path d="M500,480v490m-120,0h240M230,550H770M270,550l-120,230h240zm460,0l-120,230h240z" fill="#F2C14E" {...S}/>
  {Array.from({length:Math.min(n,92)},(_,i)=>kind==='dogs'?<g key={i} transform={`translate(${70+i%23*39} ${120+Math.floor(i/23)*75-35*p})`} fill="#667B70"><ellipse rx={15} ry={9}/><circle cx={-15} cy={-7} r={7}/><path d="M-10,5v12m20,-12v12" stroke="#667B70" strokeWidth={5}/></g>:<g key={i} transform={`translate(${(500+(i-(n-1)/2)*185)*(1-p)+(245+i%3*25)*p} ${180+400*p}) scale(${1-.72*p})`} fill="#456A72"><circle r={45}/><path d="M-45,50h90l20,150H-65zM-25,190v80m50,-80v80" stroke="#456A72" strokeWidth={22}/></g>)}
  <text x={270} y={730-30*p} textAnchor="middle" fontFamily="Pretendard" fontSize={110} fontWeight={800} fill={I}>{n}</text><text x={730} y={740+30*p} textAnchor="middle" fontFamily="Pretendard" fontSize={130} fontWeight={800} fill={I}>?</text>
 </svg></AbsoluteFill>;
};
const Consequence:React.FC<{kind:string;p:number}>=({kind,p})=><AbsoluteFill className="stage" style={{width:1000,height:1100}}><svg width="1000" height="1100"><rect width="1000" height="1100" fill="#93A49E"/><path d="M0,850H1000V1100H0Z" fill="#778C86" {...S}/>{kind==='dogs'?<Dog x={500} y={790} s={1.5} covered/>:<><path d="M175,820Q240,500 520,510Q750,510 850,820Z" fill="#E4E5D9" {...S}/><path d="M330,810Q400,620 590,660M590,810q80,-90 160,-50" fill="none" stroke="#BCC5BD" strokeWidth={12}/></>}</svg></AbsoluteFill>;

const Assault:React.FC<{mode:string;t:number;p:number}>=({mode,t,p})=>{
 const a=pose(),v=pose(),hit=mode==='action'?.72+.28*ease(t/.45):1;
 a.torso=10+12*hit;a.hands[1]=[100+250*hit,-240-30*hit];a.elbows![1]=[120,-290];
 if(mode==='impact'){a.hands[1]=[100,-240];a.feet[1]=[30+220*ease((t+.1)/.45),-80];a.knees[1]=[120,-145];}
 v.torso=20*hit;v.head=-15;v.hands=[[-70,-180],[50,-210]];v.elbows=[[-90,-230],[100,-270]];
 const close=mode==='reaction'||mode==='detail';
 return <AbsoluteFill className="stage" style={{width:1000,height:1100,overflow:'hidden'}}><AbsoluteFill style={{width:1000,height:1100,transform:`scale(${close?1.42+.1*p:1.16+.08*p})`,transformOrigin:close?'73% 60%':'50% 75%'}}>
  <Parking/><ArticulatedGuy look="hoodie" x={285} y={1030} scale={.95} rig={a} expr="serious" eye={[15,0]}/><ArticulatedGuy look="B" x={660+30*hit} y={1030} scale={.83} rig={v} expr="scared" eye={[-10,0]}/>
 </AbsoluteFill></AbsoluteFill>;
};
const Street:React.FC<{mode:string;t:number;p:number}>=({mode,t,p})=>{
 const a=pose(),v=pose(),hit=mode==='action'?.72+.28*ease(t/.45):1;
 a.hands[1]=[100+220*hit,-220];a.elbows![1]=[110,-295];a.torso=18;
 v.torso=20+15*hit;v.hip=[25*hit,-170+35*hit];v.head=15;v.hands=[[-100,-190],[130,-250]];
 const close=mode==='reaction'||mode==='detail';
 return <AbsoluteFill className="stage" style={{width:1000,height:1100,overflow:'hidden'}}><AbsoluteFill style={{width:1000,height:1100,transform:`scale(${close?1.43+.1*p:1.14+.09*p})`,transformOrigin:close?'82% 60%':'50% 75%'}}>
  <svg width="1000" height="1100"><rect width="1000" height="1100" fill="#C4D7D3"/>{[0,370,760].map((x,i)=><g key={x}><rect x={x} y={100+i*30} width={320} height={760} fill={i%2?'#A2ACAF':'#B7BBAD'} {...S}/><rect x={x+40} y={230} width={240} height={400} fill="#536F79" {...S}/><path d={`M${x},680h320`} stroke={I} strokeWidth={18}/></g>)}<path d="M0,860H1000V1100H0Z" fill="#929B9B" {...S}/><path d="M60,1000H940" stroke="#BBC1B7" strokeWidth={8}/></svg>
  <ArticulatedGuy look="hoodie" x={270} y={1030} scale={.9} rig={a} expr="serious" eye={[14,0]}/><ArticulatedGuy look="B" x={620+20*hit} y={1040} scale={.85} rig={v} expr="scared" eye={[-12,0]}/>
  <svg width="1000" height="1100"><g transform={`translate(${270+a.hands[1][0]*.9} ${1030+a.hands[1][1]*.9}) rotate(-8)`}><path d="M0,-11H45V15H0Z" fill="#8D7058" {...S}/><path d="M45,-8H147L165,14H45Z" fill="#D1DAD8" {...S}/></g></svg>
 </AbsoluteFill></AbsoluteFill>;
};
const Deposit:React.FC<{p:number}>=({p})=><AbsoluteFill className="stage" style={{width:1000,height:1100}}><svg width="1000" height="1100"><rect width="1000" height="1100" fill="#E1E6C9"/><path d="M150,500H850V990H150Z" fill="#A4B7A4" {...S}/><path d="M250,570H750V690H250Z" fill="#45666D" {...S}/><g transform={`translate(500 ${300+240*p})`}><rect x={-250} y={-100} width={500} height={200} fill={P} {...S}/><text textAnchor="middle" y={30} fontFamily="Pretendard" fontWeight={800} fontSize={100} fill={I}>1억 원</text></g><path d="M300,840H700" stroke={I} strokeWidth={18}/></svg></AbsoluteFill>;
const Camera:React.FC<{p:number}>=({p})=><AbsoluteFill className="stage" style={{width:1000,height:1100}}><Parking/><svg width="1000" height="1100"><g transform={`translate(500 450) rotate(${-8+16*p})`}><path d="M-250,-120H140L260,0L140,90H-250Z" fill={P} {...S}/><path d="M-110,90v120h-130" fill="none" {...S}/><circle cx={145} cy={-20} r={45} fill="#435F6C" {...S}/></g></svg></AbsoluteFill>;
