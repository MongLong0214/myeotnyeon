import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {FONT} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/theme';
import {ArticulatedGuy,Point,RigPose} from './FightRig';
export const smooth=(x:number)=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x)};
export const k=(t:number,points:[number,number][])=>{
 if(t<=points[0][0])return points[0][1];
 for(let i=1;i<points.length;i++){const [at,b]=points[i],[prev,a]=points[i-1];if(t<=at)return a+(b-a)*smooth((t-prev)/(at-prev))}return points[points.length-1][1];
};
export const point=(t:number,points:[number,Point][]):Point=>[k(t,points.map(([f,p])=>[f,p[0]])),k(t,points.map(([f,p])=>[f,p[1]]))];
export const standing=():RigPose=>({hip:[0,-170],torso:0,head:0,feet:[[-30,0],[30,0]],knees:[[-25,-90],[26,-90]],hands:[[-84,-166],[84,-166]],elbows:[[-70,-230],[70,-230]]});
export const ink='#1E1712',paper='#FFF8E8',red='#C9503E',teal='#2E9285';
export const label:React.CSSProperties={position:'absolute',fontFamily:FONT,fontWeight:800,color:ink,textAlign:'center',lineHeight:1.2};
export const Banner:React.FC<{children:React.ReactNode;top?:number;dark?:boolean}>=()=>null;

// Three sustained framings. Contacts animate inside a shot; they are not cuts.
export const OPENING_SHOTS=[] as const;
export const CONTACT_FRAMES=[0,54,60,66,71,76,80,84,88,91,94,96,98,100,102,104,106,108,110,112,114,116];
export const INCIDENT_SHOTS=[
 {from:0,to:50,kind:'impact-close',action:'박치기 순간의 근접 샷. 첫 충격에만 3f 스냅 줌, 이후 같은 구도 안에서 물러남·표정·옷깃 연기.'},
 {from:50,to:143,kind:'repeated-wide',action:'한 와이드 구도에서 반복 박치기와 반응을 연기. 같은 위치의 카운터가 1에서 22까지 연속으로 오른다.'},
 {from:143,to:197,kind:'aftermath',action:'상해 발화에 맞춰 피해자가 비틀거리며 머리를 감싼다. 통증 희화화·반격 없음.'},
] as const;
export const impactState=(f:number)=>{
 const count=CONTACT_FRAMES.filter(c=>c<=f).length,last=CONTACT_FRAMES[count-1]??-999,d=f-last;
 let thrust=f<18?k(f,[[0,1],[3,1],[10,0],[18,0]]):0;
 if(f>=50&&f<=116){const i=CONTACT_FRAMES.findIndex(c=>c>=f),c=CONTACT_FRAMES[i],start=i===1?50:CONTACT_FRAMES[i-1]+1;thrust=k(f,[[start,0],[Math.max(start,c-1),.18],[c,1]]);}
 const recoil=d>=0&&d<=4?k(d,[[0,0],[1,.65],[2,1],[4,0]]):0;
 return {thrust,recoil,count,last,d};
};

const DormRoom:React.FC=()=> <svg data-environment width={1000} height={2400} viewBox="0 -430 1000 2400" style={{position:'absolute',top:-430,overflow:'visible'}}>
 <rect x={-700} y={-430} width={2500} height={2800} fill="#E7DECA"/>
 <rect x={-700} y={1100} width={2500} height={1800} fill="#B79974" stroke={ink} strokeWidth={7}/>
 {[-100,140,380,620,860,1100,1340].map(x=><path key={x} d={`M${x},1100l-260,1200`} stroke="#9D805D" strokeWidth={4}/>)}
 <g opacity={.7} stroke={ink} strokeWidth={6}>
  <rect x={20} y={480} width={22} height={620} rx={7} fill="#7B8796"/><rect x={235} y={480} width={22} height={620} rx={7} fill="#7B8796"/>
  {[670,1025].map(y=><g key={y}><rect x={20} y={y} width={240} height={30} rx={8} fill={paper}/><rect x={60} y={y-25} width={170} height={29} rx={10} fill="#7A9CC6"/></g>)}
  <rect x={790} y={410} width={230} height={300} rx={8} fill="#BFD8E8"/><path d="M905,410V710"/>
 </g>
</svg>;

const FoodBag:React.FC<{f:number}>=({f})=>{
 const drop=smooth((f-79)/13),y=960+240*drop;
 return <svg width={1000} height={1700} style={{position:'absolute',overflow:'visible'}}>
  <g transform={`translate(${600-30*drop} ${y}) rotate(${-8*drop}) scale(.83)`} stroke={ink} strokeWidth={6}>
   <path d="M-55 0H55L44 90H-43Z" fill="#E8C14A"/><path d="M-25 0V-21a25 25 0 0 1 50 0V0" fill="none"/>
   <rect x={-40} y={22} width={78} height={20} rx={4} fill={paper}/>
  </g>
 </svg>;
};

const Burst:React.FC<{d:number}>=({d})=>d>=0&&d<=3?<svg width={1000} height={1700} style={{position:'absolute',overflow:'visible',pointerEvents:'none'}}>
 <g transform={`translate(606 620) rotate(${d*12}) scale(${.75+d*.13})`} fill="#FFE16A" stroke={ink} strokeWidth={5}>
  <path d="M0 -64L16 -23L55 -43L30 -7L74 6L30 20L54 56L12 39L-2 77L-17 35L-57 52L-33 15L-75 0L-32 -14L-55 -53L-15 -32Z"/>
 </g>
</svg>:null;

export const Reenactment:React.FC<{globalOffset?:number;opening?:boolean;hideCounter?:boolean}>=({globalOffset=0,opening=false,hideCounter=false})=>{
 const f=useCurrentFrame()+globalOffset,shot=INCIDENT_SHOTS.find(s=>f>=s.from&&f<s.to)??INCIDENT_SHOTS[2];
 const {thrust,recoil,count,d}=impactState(f),grab=1,hurt=smooth((f-143)/16);
 const a=standing(),v=standing(),sc=1.15,mx=300+30*grab,wx=760+38*hurt,feetY=1280;
 a.torso=12*thrust;a.head=8*thrust;a.squash=thrust;
 a.hip=[20*thrust,-170-5*Math.max(0,-thrust)];a.feet=[[-65,0],[60,0]];
 a.knees=[[-40+15*thrust,-85],[42+12*thrust,-90]];
 a.hands=[[-83,-190],[195,-330]];a.elbows=[[-100,-265],[125,-337]];
 if(grab>0){a.hands[1]=[(wx-30-mx)/sc,-318+10*recoil];a.elbows![1]=[148,-320];}
 v.hip=[10*recoil+12*hurt,-170+15*recoil+25*hurt];v.torso=5*recoil+7*hurt;v.head=6*recoil+5*hurt;
 v.hands=[[-139,-309],[73,-205]];v.elbows=[[-90,-304],[90,-265]];
 if(grab>0){v.hands=[[-24,-278],[55,-266]];v.elbows=[[-95,-260],[100,-250]];}
 if(hurt>0){
  const tr=v.torso*Math.PI/180,hr=v.head*Math.PI/180,nx=v.hip[0]+148*Math.sin(tr),ny=v.hip[1]-148*Math.cos(tr);
  v.hands=([-1,1].map(side=>[nx+side*176*Math.cos(hr)+193*Math.sin(hr),ny+side*176*Math.sin(hr)-193*Math.cos(hr)]) as [Point,Point]);
  v.elbows=[[-145,-410],[180,-405]];v.knees=[[-42,-75],[45,-75]];v.feet=[[-55-15*hurt,0],[45+20*hurt,0]];
 }
 a.handProps=[{pose:'grip'},{pose:'fist'}];v.handProps=[{pose:'open'},{pose:'open'}];
 const camera=shot.kind==='impact-close'?[1.43+.07*smooth(f/3),-330,-300,-2]:shot.kind==='repeated-wide'?[1.4,-210,-250,2]:[1.55,-700,-330,0];
 let [z,x,y,roll]=camera;
 const hit=count>0&&d>=0&&d<=3;
 const nudge=f<4?Math.sin(f*2.2+1)*8*(1-f/4):0;
 const c=CONTACT_FRAMES.filter(c=>c<=f).length;
 const rollingCount=Math.max(0,c-1)+smooth(Math.min(1,Math.max(0,d)/2));
 return <AbsoluteFill data-incident-shot={shot.kind} style={{background:'#E7DECA',overflow:'hidden'}}>
  <div style={{position:'absolute',left:x+nudge,top:y,width:1000,height:1900,transform:`scale(${z})`,transformOrigin:'0 0'}}>
   <AbsoluteFill style={{transform:`rotate(${roll}deg)`,transformOrigin:'500px 900px'}}>
    <DormRoom/>
    <ArticulatedGuy look="B" x={wx} y={feetY} scale={sc} rig={v} expr={hurt>.1||hit?'pain':'scared'} eye={[-8,0]} label="베트남 국적 노동자를 표현한 독창 캐릭터"/>
    {shot.kind!=='aftermath'&&<svg width={1000} height={1700} style={{position:'absolute',overflow:'visible'}}><g transform={`translate(${wx-30} ${feetY-318*sc+10*recoil*sc})`} stroke={ink} strokeWidth={5}><path d="M0 0L34 24L5 47L-18 21Z" fill="#3FB8A9"/><path d="M-3 10L20 25M0 19L3 38" fill="none"/></g></svg>}
    {shot.kind!=='aftermath'&&<ArticulatedGuy look="hoodie" x={mx} y={feetY} scale={sc} rig={a} expr="angry" eye={[11,-1]} talk={f>14&&f<45} label="공장 관리자 독창 캐릭터"/>}
    <FoodBag f={100}/>
    {f<4&&<Burst d={f}/>}
   </AbsoluteFill>
  </div>
  {f<50&&<div style={{position:'absolute',left:70,top:245,width:940,fontFamily:'Do Hyeon',fontSize:99,fontWeight:800,textAlign:'center',color:paper,WebkitTextStroke:`7px ${ink}`,paintOrder:'stroke fill'}}>박치기 22번. 몇 년?</div>}
  {f>=50&&!hideCounter&&<div data-continuous-counter style={{position:'absolute',left:90,top:245,width:900,display:'flex',justifyContent:'center',alignItems:'center',gap:20,fontFamily:'Do Hyeon',fontSize:88,fontWeight:800,color:c===22?'#FFD45A':paper,WebkitTextStroke:`8px ${ink}`,paintOrder:'stroke fill'}}><span>박치기</span><div style={{height:108,width:125,overflow:'hidden',textAlign:'center'}}><div style={{transform:`translateY(${-rollingCount*108}px)`}}>{Array.from({length:23},(_,i)=><div key={i} style={{height:108,lineHeight:'108px'}}>{i}</div>)}</div></div><span>/ 22</span></div>}
 </AbsoluteFill>;
};
