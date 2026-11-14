import React from 'react';
import {AbsoluteFill,Freeze,interpolate,spring,useCurrentFrame} from 'remotion';
import {ArticulatedGuy,Expr,RigPose} from './FightRig';
import {standing,k,smooth} from './FightScene';

export const INK='#201B23',PAPER='#FFF5DD',GOLD='#FFD45A',RED='#E77364',TEAL='#56C4B0';
export const type:React.CSSProperties={fontFamily:'Do Hyeon',fontWeight:800,color:PAPER,WebkitTextStroke:`7px ${INK}`,paintOrder:'stroke fill',textAlign:'center',lineHeight:1.08,whiteSpace:'pre-line'};
const clamp={extrapolateLeft:'clamp' as const,extrapolateRight:'clamp' as const};
export const pop=(frame:number)=>spring({frame,fps:30,config:{damping:13,stiffness:235,mass:.75}});

// Cuts change speaker, judgment or the person receiving it. Gavel: one verdict only.
export const SHOTS=[
 {from:197,to:258,kind:'custody',action:'구속기소 한 문장 동안 판사와 피고인을 함께 둔다. 피고인은 옷깃을 당기고 판사는 기록을 읽는다.'},
 {from:258,to:329,kind:'probation',action:'음주운전 집행유예 설명 한 샷. 판사가 기록을 확인하고 피고인이 땀·시선으로 반응한다.'},
 {from:329,to:401,kind:'question-wide',action:'질문 전체를 같은 구도에 유지. 선택지는 원래 시각에 강조하며 카메라 스냅 줌은 없다.'},
 {from:401,to:486,kind:'rebuke',action:'판사의 집행유예 중 범행 지적과 피고인의 반응을 한 투샷에서 연기한다.'},
 {from:486,to:527,kind:'admission',action:'범행 인정 문장. 피고인이 가슴에 손을 대고 끄덕이며 판사가 듣는다. 도장과 저울 유지.'},
 {from:527,to:590,kind:'reflection',action:'구금 중 반성 참작 문장. 같은 화면의 피고인이 고개를 숙이고 판사가 기록을 살핀다.'},
 {from:590,to:668,kind:'settlement',action:'합의·처벌불원을 한 샷으로 연결. 판사·피고인·피해자가 함께 있고 문서·도장·저울만 해당 발화에 맞춰 바뀐다.'},
 {from:668,to:710,kind:'gavel',action:'정답 문장 전체 한 투샷. 망치와 669~672f 스냅 줌, 0.5초 홀드 뒤 같은 화면에서 피고인이 반응한다.'},
 {from:710,to:755,kind:'comparison',action:'검찰 구형 문장 경계에서 비교 샷. 구형 징역 1년 / 법원 선고 벌금 400만 원.'},
] as const;
export const FACTORS=[
 {at:401,text:'집행유예 중 범행',side:-1,angle:-15,color:RED},
 {at:486,text:'범행 인정',side:1,angle:-6,color:TEAL},
 {at:527,text:'구금 중 반성 참작',side:1,angle:1,color:TEAL},
 {at:590,text:'700만 원 합의',side:1,angle:9,color:TEAL},
 {at:617,text:'피해자 처벌불원',side:1,angle:15,color:TEAL},
] as const;

export const CourtBackground:React.FC<{dark?:boolean}>=({dark=false})=><AbsoluteFill style={{background:dark?'#263743':'#DDD4BF'}}>
 <svg width={1080} height={1920} viewBox="0 0 1080 1920" style={{position:'absolute'}}>
  <path d="M0 0H1080V1040H0Z" fill={dark?'#344653':'#D7CCB3'}/>
  {[70,280,800,1010].map(x=><g key={x}><path d={`M${x-33} 0V1060H${x+33}V0`} fill={dark?'#465664':'#EDE2C9'} stroke={INK} strokeWidth={5}/><path d={`M${x-50} 1010H${x+50}V1060H${x-50}Z`} fill="#AE8F69" stroke={INK} strokeWidth={5}/></g>)}
  <path d="M0 1040H1080V1920H0Z" fill={dark?'#22313A':'#A98B6A'}/>
  {[0,180,360,540,720,900,1080].map(x=><path key={x} d={`M540 1040L${x*2-540} 1920`} stroke={dark?'#38434A':'#886C53'} strokeWidth={4}/>)}
  <path d="M0 1040H1080" stroke={INK} strokeWidth={9}/>
 </svg>
</AbsoluteFill>;

const Bench:React.FC<{low?:boolean}>=({low=false})=><svg width={1080} height={1920} style={{position:'absolute',zIndex:2}}>
 <path d={low?'M70 1020L925 945L1080 1920H0Z':'M0 1000H1080V1280H0Z'} fill="#80573F" stroke={INK} strokeWidth={10}/>
 <path d={low?'M70 1020L925 945L960 1000L55 1080Z':'M0 995H1080V1040H0Z'} fill="#CFAB76" stroke={INK} strokeWidth={9}/>
 {[150,390,630,870].map(x=><path key={x} d={`M${x} 1090V1260`} stroke="#68452F" strokeWidth={13}/>)}
</svg>;

const Sweat:React.FC<{x:number;y:number;t:number}>=({x,y,t})=><svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}>
 {[0,1,2].map(i=><path key={i} d="M0 -15Q-22 15 0 27Q22 15 0 -15" transform={`translate(${x+i*23} ${y+((t*2+i*19)%70)}) rotate(-15)`} fill="#A6DDF4" stroke={INK} strokeWidth={4} opacity={.95-i*.12}/>)}
</svg>;

export const Actor:React.FC<{who:'judge'|'hoodie'|'B';x:number;y:number;scale:number;expr?:Expr;head?:number;gesture?:'point'|'admit'|'bow'|'worker'|'read'|'flinch'|'collar';t?:number;gavel?:boolean}>=({who,x,y,scale,expr='serious',head=0,gesture,t=0,gavel=false})=>{
 const f=useCurrentFrame(),r:RigPose=standing();
 r.head=head+Math.sin(t*.12)*.8;
 r.hands=[[-85,-210],[78,-215]];r.elbows=[[-90,-262],[92,-263]];
 if(gesture==='point'){const p=smooth(t/12);r.hands[1]=[105+60*p,-287-8*Math.sin(t*.12)];r.elbows![1]=[72,-305];r.head=-4;}
 if(gesture==='read'){r.hands=[[-74,-280],[73,-280]];r.head=7+Math.sin(t*.1);}
 if(gesture==='admit'){r.head=5+7*Math.sin(Math.min(t,30)*Math.PI/15);r.hands[1]=[10,-279];r.elbows![1]=[87,-250];}
 if(gesture==='bow'){const b=smooth(t/20);r.torso=-12*b;r.head=-18*b;r.hip=[-15*b,-170+40*b];r.hands=[[-10,-160],[10,-160]];r.elbows=[[-65,-230],[65,-230]];}
 if(gesture==='worker'){const p=smooth(t/18);r.hands[0]=[-55,-250];r.hands[1]=[99-35*p,-282+55*p];r.head=2+3*Math.sin(Math.min(t,24)*Math.PI/24);}
 if(gesture==='collar'){r.hands[1]=[23,-300];r.elbows![1]=[92,-260];r.head=5;}
 if(gesture==='flinch'){const p=k(t,[[0,0],[9,1],[20,1],[30,.4]]);r.hip=[0,-170+30*p];r.knees=[[-42,-72],[42,-72]];r.hands=[[-100,-330-105*p],[110,-330-100*p]];r.elbows=[[-125,-310],[130,-310]];r.squash=.5*p;r.head=-5*p;}
 if(who==='judge'&&gesture==='point'){r.hands[0]=[-35,k(t,[[0,-220],[3,-535],[10,-535],[15,-220]])];r.elbows![0]=[-125,-405];}
 let handAngle=-40;
 if(gavel){const d=f-669;handAngle=k(d,[[-7,-20],[-2,70],[0,145],[3,145],[18,145]]);r.hands[1]=[k(d,[[-7,185],[-2,80],[0,65],[18,65]]),k(d,[[-7,-480],[-2,-365],[0,-336],[18,-336]])];r.elbows![1]=[106,-330];r.head=k(d,[[-7,-5],[0,4],[8,0]]);r.hands[0]=[-35,k(d,[[-7,-535],[-4,-535],[-1,-220]])];r.elbows![0]=[-125,-405];}
 return <>
  <ArticulatedGuy look={who} x={x} y={y} scale={scale} rig={r} expr={expr} talk={gesture==='point'||gesture==='admit'||who==='B'&&f>=617&&f<635} eye={gesture==='bow'?[-4,14]:who==='judge'?(x<540?[8,0]:[-8,0]):who==='B'?(x<540?[8,1]:[-8,1]):[-7,1]} label={who==='B'?'독창 카툰 노동자':who==='judge'?'독창 카툰 판사':'독창 카툰 피고인'}/>
  {gavel&&<svg width={1080} height={1920} style={{position:'absolute',overflow:'visible',zIndex:3}}><g transform={`translate(${x+r.hands[1][0]*scale} ${y+r.hands[1][1]*scale}) rotate(${handAngle}) scale(${scale})`} stroke={INK} strokeWidth={7} strokeLinejoin="round"><path d="M-8 10V-103H8V10Z" fill="#A17442"/><rect x={-61} y={-135} width={122} height={45} rx={6} fill="#AD7944"/><path d="M-44 -135V-90M44 -135V-90" fill="none" stroke="#E6BD79" strokeWidth={8}/></g></svg>}
 </>;
};

export const Stamp:React.FC<{text:string;at:number;color:string;top?:number;small?:boolean}>=({text,at,color,top=280,small=false})=>{
 const f=useCurrentFrame(),d=f-at;if(d<0)return null;
 const p=pop(d),s=d<3?1.6-.2*d:1+.22*Math.exp(-(d-3)/5)*Math.sin((d-3)*.8);
 return <div data-factor-stamp style={{...type,position:'absolute',left:95,top,width:890,fontSize:small?65:78,color,transform:`translateY(${(1-p)*-160}px) scale(${s}) rotate(${interpolate(d,[0,9],[-9,-3],clamp)}deg)`,opacity:Math.min(1,d/2)}}>{text}</div>;
};

export const Scales:React.FC<{x?:number;y?:number;scale?:number}>=({x=540,y=870,scale=1})=>{
 const f=useCurrentFrame(),idx=FACTORS.filter(e=>f>=e.at).length-1,e=FACTORS[idx],d=e?f-e.at:999;
 const prev=idx>0?FACTORS[idx-1].angle:0,target=e?.angle??0;
 const p=1-Math.exp(-d/7)*Math.cos(d*.49),angle=prev+(target-prev)*p;
 const bounce=d<16?Math.sin(d*1.3)*Math.exp(-d/5)*10:0;
 return <svg data-sentencing-scale width={1080} height={1920} style={{position:'absolute',overflow:'visible'}}>
  <g transform={`translate(${x} ${y+bounce}) scale(${scale})`} stroke={INK} strokeWidth={10} strokeLinejoin="round">
   <path d="M0 -195V245M-140 245H140L115 218H-115Z" fill="#DFB958"/>
   <g transform={`rotate(${angle})`}>
    <path d="M-275 -145H275" stroke="#A88A42" strokeWidth={22} strokeLinecap="round"/>
    {[-1,1].map(side=><g key={side} transform={`translate(${side*255} -145)`}>
     <path d="M0 0L-92 178M0 0L92 178" fill="none" strokeWidth={6}/>
     <path d="M-110 178Q0 300 110 178Z" fill={side<0?RED:TEAL}/>
     {FACTORS.filter(a=>a.side===side&&f>=a.at).map((a,i)=><g key={a.at} transform={`translate(${-55+i*33} ${154-Math.min(24,i*9)-(f-a.at<10?(10-(f-a.at))*22:0)})`}><rect x={-24} y={-42} width={48} height={55} rx={4} fill={a.color} strokeWidth={5}/><path d="M-12 -28H12M-12 -13H8" stroke={INK} strokeWidth={4}/></g>)}
    </g>)}
   </g>
   <circle cy={-145} r={24} fill={GOLD}/>
   {d>=0&&d<11&&<g transform={`translate(${(e?.side??1)*255} 45)`} stroke={GOLD} strokeWidth={8}>{[-55,0,55].map((a,i)=><path key={a} d={`M${a} 0L${a*1.7} ${-45-i%2*25}`}/>)}</g>}
  </g>
  {d>=0&&d<13&&<text x={x+(e?.side??1)*230*scale} y={y+100*scale} fill={GOLD} stroke={INK} strokeWidth={7} paintOrder="stroke" textAnchor="middle" fontFamily="Do Hyeon" fontSize={70*scale} fontWeight={800}>쿵</text>}
 </svg>;
};

const Record:React.FC<{probation?:boolean;large?:boolean;shared?:boolean}>=({probation=false,large=false,shared=false})=>{const f=useCurrentFrame();return <svg width={1080} height={1920} style={{position:'absolute'}}>
 <g transform={`translate(${shared?540:large?520:probation?185:620} ${shared?470:large?760:probation?470:900}) rotate(${probation?-8:7}) scale(${shared?.75:large?1.65:probation?1:.9})`}>
  <path d="M-150 -180H140L180 -135V190H-150Z" fill={PAPER} stroke={INK} strokeWidth={8}/><path d="M140 -180V-135H180" fill="#D0BB97" stroke={INK} strokeWidth={7}/>
  <text textAnchor="middle" x={10} y={-80} fontFamily="Do Hyeon" fontWeight={800} fontSize={49} fill={INK}>{probation?'집행유예':f<265?'재판 기록':'음주운전'}</text>
  <text textAnchor="middle" x={10} y={-12} fontFamily="Do Hyeon" fontWeight={800} fontSize={probation?55:42} fill={probation?'#B3483D':INK}>{probation?'기간 중':f<265?'':'전력'}</text>
  <path d="M-95 55H110M-95 85H105M-95 115H70" stroke="#B4A58C" strokeWidth={8}/>
 </g>
</svg>;};

const Settlement:React.FC<{shared?:boolean}>=({shared=false})=>{
 const f=useCurrentFrame(),p=smooth((f-590)/12),turned=f>=617;
 return <svg width={1080} height={1920} style={{position:'absolute'}}>
 <g transform={`translate(${shared?650:530-30*p} ${shared?1050:985-10*p}) rotate(${-12+8*p}) scale(${shared?.52:.74})`} stroke={INK} strokeWidth={7}>
  <path d="M-205 -165H205V220H-205Z" fill={PAPER}/>
  <text textAnchor="middle" y={-75} fontFamily="Do Hyeon" fontSize={70} fontWeight={800} fill={INK} stroke="none">{turned?'처벌불원서':'합의서'}</text>
  <path d="M-140 -20H140M-140 25H90M-140 70H130" stroke="#B4A58C" strokeWidth={9}/>
  <path d="M60 145q30 -42 40 -10t40 -10" fill="none" stroke="#445E7E" strokeWidth={9}/>
 </g></svg>;
};

export const CourtDynamic:React.FC=()=>{
 const f=useCurrentFrame(),shot=SHOTS.find(s=>f>=s.from&&f<s.to)??SHOTS[0],t=f-shot.from;
 const zoom=shot.kind==='gavel'&&f>=669?1+.09*smooth((f-669)/3):1;
 const factor=FACTORS.filter(e=>f>=e.at).slice(-1)[0];
 const factorsVisible=['rebuke','admission','reflection','settlement'].includes(shot.kind);
 let content:React.ReactNode;
 switch(shot.kind){
  case 'custody': content=<><Actor who="judge" x={230} y={1120} scale={.95} gesture="read" t={t}/><Actor who="hoodie" x={750} y={1240} scale={1.2} expr={t<24?'scared':'serious'} gesture="collar" t={t}/></>;break;
  case 'probation': content=<><Actor who="judge" x={225} y={1190} scale={1.12} gesture="read" t={t}/><Actor who="hoodie" x={825} y={1240} scale={1.08} expr={t<28?'serious':'scared'} gesture="collar" t={t}/><Record probation shared/><Sweat x={955} y={720} t={Math.min(t,20)}/></>;break;
  case 'question-wide': content=<><Actor who="judge" x={300} y={600} scale={.65} expr="serious"/><Actor who="hoodie" x={750} y={600} scale={.65} expr={f>=365?'shock':f>=346?'scared':'serious'} gesture={f>=365?'flinch':f>=346?'collar':undefined} t={f-(f>=365?365:346)}/></>;break;
  case 'rebuke': content=<><Actor who="judge" x={235} y={1190} scale={1.1} expr="angry" gesture="point" t={t}/><Actor who="hoodie" x={810} y={1260} scale={1.15} expr={t<32?'scared':'serious'} gesture={t<36?'collar':'bow'} t={t<36?t:t-36}/><Sweat x={955} y={705} t={Math.min(t,24)}/><Scales x={520} y={1020} scale={.38}/></>;break;
  case 'admission': content=<><Actor who="judge" x={220} y={1120} scale={.85} expr="serious" gesture="read" t={t}/><Actor who="hoodie" x={785} y={1280} scale={1.32} expr="serious" gesture="admit" t={t}/><Scales x={490} y={1020} scale={.4}/></>;break;
  case 'reflection': content=<><Actor who="judge" x={225} y={1190} scale={1.05} expr="serious" gesture="read" t={t}/><Actor who="hoodie" x={800} y={1260} scale={1.18} expr="concern" gesture="bow" t={t}/><Scales x={520} y={1020} scale={.38}/></>;break;
  case 'settlement': content=<><Actor who="judge" x={175} y={1190} scale={.85} expr="serious" gesture={f<617?'read':'point'} t={f<617?t:f-617}/><Actor who="hoodie" x={505} y={1190} scale={.9} expr="serious" gesture="bow" t={30}/><Actor who="B" x={925} y={1240} scale={.85} expr="concern" gesture="worker" t={Math.max(0,f-617)}/><Settlement shared/><Scales x={540} y={410} scale={.33}/></>;break;
  case 'gavel': content=<><Actor who="judge" x={240} y={1230} scale={1.15} expr="serious" gavel/><Actor who="hoodie" x={825} y={1280} scale={1.1} expr={f<669?'serious':'shock'} gesture={f<691?'collar':'flinch'} t={f<691?0:f-691}/><svg width={1080} height={1920} style={{position:'absolute',zIndex:2}}><path d="M20 930H570V1380H20Z" fill="#80573F" stroke={INK} strokeWidth={10}/><path d="M20 930H570V970H20Z" fill="#CFAB76" stroke={INK} strokeWidth={9}/>{[110,290,470].map(x=><path key={x} d={`M${x} 1010V1320`} stroke="#68452F" strokeWidth={13}/>)}<ellipse cx={390} cy={950} rx={85} ry={17} fill="#5D3A30" stroke={INK} strokeWidth={7}/></svg></>;break;
  default: content=<><Actor who="judge" x={270} y={1110} scale={1.0} expr="serious"/><Actor who="hoodie" x={790} y={1140} scale={.95} expr="serious" gesture="bow" t={30}/></>;
 }
 const deadpan=f>=676&&f<691;
 if(deadpan)content=<Freeze frame={676}>{content}</Freeze>;
 return <AbsoluteFill data-shot={shot.kind} data-camera-snap={f>=669&&f<=672?'answer':undefined}>
  <CourtBackground dark={shot.kind==='question-wide'||f>=668}/>
  <AbsoluteFill style={{height:1920,overflow:'hidden',transform:`scale(${deadpan?1.09:zoom})`,transformOrigin:'50% 55%'}}>{content}</AbsoluteFill>
  {factorsVisible&&factor&&<Stamp text={factor.text} color={factor.color} at={factor.at} top={235}/>}
  {f>=669&&f<=672&&<AbsoluteFill style={{background:'#FFF5CC',opacity:(1-(f-669)/4)*.85}}/>}
 </AbsoluteFill>;
};
