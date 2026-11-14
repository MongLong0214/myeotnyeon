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
 {from:197,to:223,kind:'custody',action:'구속기소: 법정 설정 샷. 피고인이 옷깃을 당긴다.'},
 {from:223,to:241,kind:'custody-close',action:'피고인 눈으로 스냅 줌. 온몸으로 움찔한다.'},
 {from:241,to:265,kind:'record',action:'판사가 재판 기록을 읽는다.'},
 {from:265,to:285,kind:'record-insert',action:'음주운전 전력 문서의 빠른 인서트.'},
 {from:285,to:307,kind:'reaction',action:'집행유예 기간 중 범행. 피고인이 땀을 흘린다.'},
 {from:307,to:329,kind:'period-insert',action:'집행유예 기간 중이라는 사실을 기록 클로즈업으로 연결.'},
 {from:329,to:405,kind:'question-wide',action:'가장 긴 선택 홀드 2.533초. 보기마다 스냅 줌과 별도 피고인 반응.'},
 {from:405,to:413,kind:'judge',action:'안경을 고친 판사가 집행유예 중 범행을 지적한다.'},
 {from:413,to:421,kind:'defendant-flash',action:'빠른 반응 연결 1: 피고인의 튀는 동공과 움찔.'},
 {from:421,to:429,kind:'worker-flash',action:'빠른 반응 연결 2: 피해자의 절제된 걱정 표정. 희화화 없음.'},
 {from:429,to:440,kind:'judge',action:'빠른 반응 연결 3: 판사의 단호한 지적. 27f 안에 세 인물 교환.'},
 {from:440,to:479,kind:'admonished',action:'피고인 얼굴에 3f 스냅 줌 후 땀·정지 표정, 입을 다문다.'},
 {from:479,to:524,kind:'admission',action:'피고인이 범행을 인정하며 고개를 끄덕인다. 인정이 저울에 반영된다.'},
 {from:524,to:565,kind:'bow',action:'피고인이 고개를 숙인다. 구금 생활과 반성 참작을 연결한다.'},
 {from:565,to:602,kind:'consider',action:'판사가 구금 생활을 보고 반성을 참작한다.'},
 {from:602,to:635,kind:'settlement',action:'700만 원 합의 문서. 피해자가 처벌불원 의사를 보인다.'},
 {from:635,to:663,kind:'worker',action:'피해자의 차분하고 굳은 표정. 판사가 처벌불원을 확인한다.'},
 {from:663,to:691,kind:'gavel',action:'안경 미세 동작→망치→3f 스냅 줌→676~690f 0.5초 데드팬 홀드.'},
 {from:691,to:710,kind:'verdict-reaction',action:'정지 비트에서 피고인 전신 반응으로 스매시 컷. 정답 A와 선고 금액 유지.'},
 {from:710,to:755,kind:'comparison',action:'구형 발화 시작과 함께 비교. 검찰 구형 징역 1년 / 법원 선고 벌금 400만 원.'},
] as const;
// Last 18f are the continuation of the verdict scene, with the new comparison insert.
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
 if(gesture==='flinch'){const p=k(t,[[0,0],[3,1],[15,1],[22,.4]]);r.hip=[0,-170+30*p];r.knees=[[-42,-72],[42,-72]];r.hands=[[-100,-330-105*p],[110,-330-100*p]];r.elbows=[[-125,-310],[130,-310]];r.squash=.5*p;r.head=-5*p;}
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

const Record:React.FC<{probation?:boolean;large?:boolean}>=({probation=false,large=false})=>{const f=useCurrentFrame();return <svg width={1080} height={1920} style={{position:'absolute'}}>
 <g transform={`translate(${large?520:probation?185:620} ${large?760:probation?470:900}) rotate(${probation?-8:7}) scale(${large?1.65:probation?1:.9})`}>
  <path d="M-150 -180H140L180 -135V190H-150Z" fill={PAPER} stroke={INK} strokeWidth={8}/><path d="M140 -180V-135H180" fill="#D0BB97" stroke={INK} strokeWidth={7}/>
  <text textAnchor="middle" x={10} y={-80} fontFamily="Do Hyeon" fontWeight={800} fontSize={49} fill={INK}>{probation?'집행유예':f<265?'재판 기록':'음주운전'}</text>
  <text textAnchor="middle" x={10} y={-12} fontFamily="Do Hyeon" fontWeight={800} fontSize={probation?55:42} fill={probation?'#B3483D':INK}>{probation?'기간 중':f<265?'':'전력'}</text>
  <path d="M-95 55H110M-95 85H105M-95 115H70" stroke="#B4A58C" strokeWidth={8}/>
 </g>
</svg>;};

const Settlement:React.FC=()=>{
 const f=useCurrentFrame(),p=smooth((f-590)/12),turned=f>=617;
 return <svg width={1080} height={1920} style={{position:'absolute'}}>
 <g transform={`translate(${530-30*p} ${985-10*p}) rotate(${-12+8*p}) scale(.74)`} stroke={INK} strokeWidth={7}>
  <path d="M-205 -165H205V220H-205Z" fill={PAPER}/>
  <text textAnchor="middle" y={-75} fontFamily="Do Hyeon" fontSize={70} fontWeight={800} fill={INK} stroke="none">{turned?'처벌불원서':'합의서'}</text>
  <path d="M-140 -20H140M-140 25H90M-140 70H130" stroke="#B4A58C" strokeWidth={9}/>
  <path d="M60 145q30 -42 40 -10t40 -10" fill="none" stroke="#445E7E" strokeWidth={9}/>
 </g></svg>;
};

export const CourtDynamic:React.FC=()=>{
 const f=useCurrentFrame(),shot=SHOTS.find(s=>f>=s.from&&f<s.to)??SHOTS[0],t=f-shot.from;
 let zoom=1+smooth(t/Math.max(1,shot.to-shot.from))*.045;
 if(['custody-close','admonished','defendant-flash'].includes(shot.kind))zoom=1+.12*smooth(t/3);
 if(shot.kind==='gavel')zoom=f>=669?1+.12*smooth((f-669)/3):1;
 const whip=t<4?(4-t)*12*(shot.from===421?-1:1):0;
 const factor=FACTORS.filter(e=>f>=e.at).slice(-1)[0];
 const is=['judge','admonished','admission','bow','consider','settlement','worker'].includes(shot.kind);
 let content:React.ReactNode;
 switch(shot.kind){
  case 'custody': content=<><Actor who="judge" x={230} y={1020} scale={.85} gesture="read"/><Actor who="hoodie" x={665} y={1180} scale={1.2} expr="scared" gesture="collar" t={t}/></>;break;
  case 'custody-close': content=<><Actor who="hoodie" x={560} y={1400} scale={1.7} expr="shock" gesture="flinch" t={t}/><Sweat x={820} y={520} t={t}/></>;break;
  case 'record': content=<><Actor who="judge" x={350} y={1370} scale={1.6} expr="serious" gesture="read" t={t}/><Record/></>;break;
  case 'record-insert': content=<Record large/>;break;
  case 'period-insert': content=<Record probation large/>;break;
  case 'reaction': content=<><Actor who="hoodie" x={650} y={1370} scale={1.7} expr="scared" head={6} t={t}/><Record probation/><Sweat x={850} y={550} t={t}/></>;break;
  case 'question-wide': content=<><Actor who="judge" x={300} y={600} scale={.65} expr="serious"/><Actor who="hoodie" x={750} y={600} scale={.65} expr={f>=365?'shock':f>=346?'scared':'serious'} gesture={f>=365?'flinch':f>=346?'collar':undefined} t={f-(f>=365?365:346)}/></>;break;
  case 'defendant-flash': content=<><Actor who="hoodie" x={620} y={1400} scale={1.7} expr="shock" gesture="flinch" t={t}/><Sweat x={840} y={510} t={t}/></>;break;
  case 'worker-flash': content=<Actor who="B" x={550} y={1400} scale={1.7} expr="concern" gesture="worker" t={10}/>;break;
  case 'judge': content=<><Actor who="judge" x={270} y={1190} scale={1.35} expr="angry" gesture="point" t={t}/><Scales x={740} y={860} scale={.63}/></>;break;
  case 'admonished': content=<><Actor who="hoodie" x={620} y={1390} scale={1.65} expr={t<12?'shock':'serious'} head={k(t,[[0,0],[15,10],[24,13]])} t={t}/><Sweat x={850} y={510} t={Math.min(t,12)}/></>;break;
  case 'admission': content=<><Actor who="hoodie" x={380} y={1250} scale={1.35} expr="serious" gesture="admit" t={Math.max(0,f-486)}/><Scales x={790} y={900} scale={.59}/></>;break;
  case 'bow': content=<><Actor who="hoodie" x={610} y={1260} scale={1.5} expr="concern" gesture="bow" t={Math.max(0,f-527)}/><Scales x={240} y={875} scale={.51}/></>;break;
  case 'consider': content=<><Actor who="judge" x={275} y={1130} scale={1.25} gesture="read" t={t}/>{f>=590&&<Scales x={740} y={860} scale={.69}/>}</>;break;
  case 'settlement': content=<><Actor who="B" x={850} y={1240} scale={.9} expr="concern" gesture="worker" t={t}/><Actor who="hoodie" x={300} y={1240} scale={.85} expr="serious" gesture="bow" t={30}/><Settlement/><Scales x={520} y={460} scale={.58}/></>;break;
  case 'worker': content=<><Actor who="B" x={650} y={1390} scale={1.7} expr="concern" gesture="worker" t={t+10}/></>;break;
  case 'gavel': content=<><Actor who="judge" x={380} y={1560} scale={1.85} expr="serious" gavel/><Bench low/><svg width={1080} height={1920} style={{position:'absolute'}}><ellipse cx={615} cy={1108} rx={150} ry={30} fill="#5D3A30" stroke={INK} strokeWidth={9}/><g transform={`translate(130 1010) rotate(${f>=669&&f<676?Math.sin((f-669)*2)*12:0})`} stroke={INK} strokeWidth={6}><path d="M-30 -80H30L24 0H-22Z" fill={TEAL}/><path d="M-17 -80L-22 -150M0 -80L7 -160M17 -80L32 -142" stroke="#E8C16B" strokeWidth={12}/></g></svg></>;break;
  case 'verdict-reaction': content=<><Actor who="hoodie" x={720} y={1230} scale={1.25} expr="shock" gesture="flinch" t={t}/><Actor who="judge" x={270} y={1110} scale={.85} expr="serious"/></>;break;
  default: content=<><Actor who="judge" x={270} y={1110} scale={1.0} expr="serious"/><Actor who="hoodie" x={790} y={1140} scale={.95} expr="serious" gesture="bow" t={30}/></>;
 }
 const hit=f>=669&&f<680?(f-669):999;
 const deadpan=f>=676&&f<691;
 if(deadpan)content=<Freeze frame={676}>{content}</Freeze>;
 const shake=hit<7?Math.sin(hit*2.1)*Math.exp(-hit/3)*22:0;
 const bgPan=shot.kind==='record'||shot.kind==='judge'||shot.kind==='consider'?180:shot.kind==='admonished'||shot.kind==='bow'||shot.kind==='worker'?-180:shot.kind==='admission'?-245:0;
 return <AbsoluteFill data-shot={shot.kind}>
  <AbsoluteFill style={{transform:`translateX(${bgPan+whip*.3}px) scale(${1.6+(zoom-1)*.5})`}}><CourtBackground dark={f>=329&&f<405||f>=663}/></AbsoluteFill>
  <AbsoluteFill style={{height:1920,overflow:'hidden',transform:`translateX(${whip+shake}px) scale(${zoom})`,transformOrigin:'50% 55%'}}>{content}</AbsoluteFill>
  {is&&factor&&<Stamp text={factor.text} color={factor.color} at={factor.at} top={235}/>}
  {f>=669&&f<=672&&<AbsoluteFill style={{background:'#FFF5CC',opacity:(1-(f-669)/4)*.85}}/>}
 </AbsoluteFill>;
};
