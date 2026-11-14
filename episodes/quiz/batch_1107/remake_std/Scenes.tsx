import React from 'react';
import {SnackScene,ForkliftScene,RemakeCourt} from './RemakeScenes';
import {AbsoluteFill,Freeze,useCurrentFrame} from 'remotion';
import {ArticulatedGuy,Expr,Look,RigPose} from './FightRig';
import {standing,k,smooth} from './FightScene';
import {Actor,CourtBackground,Stamp,INK,PAPER,GOLD,RED,TEAL,type} from './CourtDynamic';

const S={stroke:INK,strokeWidth:9,strokeLinecap:'round' as const,strokeLinejoin:'round' as const};
export type Line={id:string;mode:string;text:string;from_frame:number;dur:number;start_s:number;end_s:number;shown:string};
export type Case={qid:string;kind:string;headline:string;question:string;choices:string[];correct:number;answer:string;answer_detail:string;next:string;utterances:Line[];n:number;answer_frame:number;choice_frame:number;cta_frame:number;subtitles:any[];answer_label?:string};
export const lineAt=(c:Case,f:number)=>c.utterances.find(u=>f>=u.from_frame&&f<u.from_frame+u.dur)??c.utterances[c.utterances.length-1];

const Toon:React.FC<{look?:Look;x:number;y?:number;scale?:number;expr?:Expr;gesture?:string;t?:number;rig?:RigPose;talk?:boolean;eye?:[number,number]}>=({look='hoodie',x,y=1220,scale=1.1,expr='serious',gesture,t=0,rig,talk=false,eye})=>{
 const r=rig??standing(),p=smooth(t/14);
 if(!rig){
  r.head=Math.sin(t*.1)*.8;r.hands=[[-75,-210],[75,-210]];r.elbows=[[-90,-270],[90,-270]];
  if(gesture==='collar'){r.hands[1]=[22,-300];r.elbows[1]=[95,-260];r.head=4+4*p;}
  if(gesture==='point'){r.hands[1]=[140+30*p,-280];r.elbows[1]=[80,-300];r.head=-4;}
  if(gesture==='protect'){r.hands=[[-40,-260],[50,-270]];r.elbows=[[-110,-230],[110,-250]];r.torso=8;r.head=-6;}
  if(gesture==='hurt'){r.hip=[8,-145];r.hands=[[-30,-220],[30,-220]];r.elbows=[[-85,-230],[90,-240]];r.torso=12;r.head=-8;}
  if(gesture==='palm'){r.hands=[[-120,-290],[120,-270]];r.elbows=[[-85,-250],[110,-320]];r.head=-4+7*p;}
  if(gesture==='sweat'){r.hands[1]=[22,-300];r.head=-3+9*p;r.torso=-3+7*p;}
  if(gesture==='refuse'){r.hands[0]=[-110,-300];r.head=-5+8*Math.sin(Math.min(t,30)*.18);}
  if(gesture==='flinch'){const b=k(t,[[0,0],[8,1],[18,1],[30,.2]]);r.hip=[0,-170+28*b];r.hands=[[-100,-270-100*b],[105,-275-100*b]];r.elbows=[[-120,-300],[125,-305]];r.head=-8*b;r.squash=.45*b;}
  if(gesture==='count'){const b=k(t,[[0,0],[20,1],[36,1],[56,.3],[76,0]]);r.hands=[[-80-45*b,-220-95*b],[75,-230]];r.elbows=[[-100,-290],[95,-290]];r.head=-7+12*b;}
  if(gesture==='recover'){const b=k(t,[[0,0],[16,1],[30,1],[55,.15]]);r.hands=[[-45,-270],[60-50*b,-270-115*b]];r.elbows=[[-105,-260],[105,-300]];r.head=-8+11*b;}
 }
 if(!rig)r.handProps=[{pose:gesture==='palm'||gesture==='refuse'?'open':gesture==='protect'||gesture==='flinch'?'open':'relaxed'},{pose:gesture==='point'||gesture==='count'?'point':gesture==='palm'?'open':gesture==='collar'?'pinch':'relaxed'}];
 return <ArticulatedGuy look={look} x={x} y={y} scale={scale} rig={r} expr={expr} eye={eye??(x<540?[9,0]:[-9,0])} talk={talk} label="실존 인물과 무관한 독창 성인 카툰"/>;
};

const Parking:React.FC<{night?:boolean}>=({night=false})=><AbsoluteFill style={{background:night?'#4D5B67':'#C6D4CD'}}><svg width={1080} height={1920}>
 <path d="M0 0H1080V1060H0Z" fill={night?'#556272':'#CFD9CA'}/>
 {[70,850].map(x=><g key={x}><path d={`M${x} 0H${x+75}V1090H${x}Z`} fill={night?'#83928F':'#ACB8A4'} {...S}/><path d={`M${x-25} 1030H${x+100}V1090H${x-25}Z`} fill="#A2947B" {...S}/></g>)}
 <path d="M0 1060H1080V1920H0Z" fill={night?'#798382':'#9BA09A'} stroke={INK} strokeWidth={9}/>
 {[100,550,1000].map(x=><path key={x} d={`M${x} 1180l-320 740`} stroke={PAPER} strokeWidth={13}/>)}
 <g transform="translate(-130 0)" {...S}><path d="M0 860L95 680H340L445 850H520V1080H0Z" fill="#7A99A3"/><path d="M112 705H321L400 845H35Z" fill="#354D5B"/><circle cx={95} cy={1080} r={53} fill={INK}/><circle cx={400} cy={1080} r={53} fill={INK}/><path d="M0 960H520" fill="none"/></g>
 <g transform="translate(830 -80)" {...S}><path d="M0 860L95 680H340L445 850H520V1080H0Z" fill="#9EAAA7"/><path d="M112 705H321L400 845H35Z" fill="#354D5B"/><circle cx={95} cy={1080} r={53} fill={INK}/><circle cx={400} cy={1080} r={53} fill={INK}/></g>
 </svg></AbsoluteFill>;

const Interior:React.FC=()=> <AbsoluteFill style={{background:'#89989A'}}><svg width={1080} height={1920}>
 <path d="M0 0H1080V1100H0Z" fill="#D0DCD5"/><path d="M0 90H1080M0 170H1080" {...S}/>
 {[25,382,739].map(x=><g key={x}><rect x={x} y={285} width={310} height={430} rx={30} fill="#3F5661" {...S}/><path d={`M${x+15} 650l270 -210`} stroke="#6C858A" strokeWidth={26}/><rect x={x} y={810} width={310} height={210} rx={22} fill="#529B92" {...S}/></g>)}
 <path d="M0 1100H1080V1920H0Z" fill="#89989A" stroke={INK} strokeWidth={10}/>
 {[350,720].map(x=><g key={x}><path d={`M${x} 170v910`} stroke={INK} strokeWidth={16}/><path d={`M${x+2} 170v910`} stroke="#E4E5D8" strokeWidth={6}/></g>)}
 <path d="M0 1500H1080M0 1800H1080" stroke="#A7B3AF" strokeWidth={5}/>
 </svg></AbsoluteFill>;

const Flames:React.FC<{t:number;growth:number}>=({t,growth})=><svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}><g transform={`translate(540 1290) scale(${.45+.55*growth} ${.15+.60*growth})`} {...S}>
 <path d={`M-390 0Q-470 -130 -300 -285Q-350 -440 -200 -520Q-250 -300 -105 -290Q-15 -460 -50 ${-670+Math.sin(t*.6)*18}Q120 -550 110 -340Q245 -410 250 -580Q390 -420 300 -240Q450 -330 420 -420Q510 -170 390 0Z`} fill="#D55C30"/>
 <path d="M-300 0Q-355 -120 -205 -270Q-240 -375 -155 -430Q-180 -230 -40 -205Q75 -360 40 -490Q200 -350 150 -170Q275 -260 285 -370Q380 -130 300 0Z" fill="#EF9B38"/>
 <path d="M-165 0Q-200 -100 -95 -205Q-80 -130 0 -100Q85 -170 70 -300Q200 -150 170 0Z" fill={GOLD} strokeWidth={4}/>
 </g></svg>;

const Smoke:React.FC<{t:number}>=({t})=><svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}>{[0,1,2,3,4].map(i=><ellipse key={i} cx={100+i*260+Math.sin(t*.05+i)*25} cy={300+i%2*280-t*1.5} rx={240} ry={190} fill="#647179" opacity={.22+i*.025}/>)}</svg>;

const TrainScene:React.FC<{u:Line;t:number}>=({u,t})=>{
 const f=useCurrentFrame(),mode=u.mode,a=standing(),v=standing(),p=smooth(t/24),recoil=smooth((t-35)/12);
 a.torso=14+7*p;a.head=8;a.hands=[[-90,-215],[160,-240+15*p]];a.elbows=[[-100,-280],[100,-300]];
 v.hands=[[-85-40*recoil,-220-75*recoil],[85+40*recoil,-225-75*recoil]];v.elbows=[[-100,-290],[110,-290]];v.torso=-10*recoil;v.head=8*recoil;
 const evac=mode==='evacuate';
 if(evac){const walk=Math.sin(t*.25);v.feet=[[-40-45*walk,-15*Math.max(0,walk)],[40+45*walk,-15*Math.max(0,-walk)]];v.knees=[[-50,-100],[65,-90]];v.torso=12;v.hands=[[-80,-250],[100,-290]];}
 const zoom=mode==='pour'?1+.07*smooth((t+1)/3):1;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${zoom})`,transformOrigin:'50% 49%'}}><Interior/>
 {mode==='pour'?<><Toon x={270} y={1210} scale={1.08} rig={a} expr="serious"/><Toon look="passenger" x={855} y={1230} scale={1.05} rig={v} expr={t<35?'concern':'scared'}/>
 <svg width={1080} height={1920} style={{position:'absolute'}}><g transform={`translate(${441+10*p} ${955+10*p}) rotate(${45+22*p})`} {...S}><path d="M-60 -45H50V92H-60ZM-30 -45V-72H20V-45M50 -18L95 -8V20H50" fill="#AD8A52"/><rect x={-36} y={-8} width={55} height={60} fill={PAPER} strokeWidth={4}/></g>{t<35&&<><path d="M487 1027Q540 1100 590 1190" stroke="#9C824C" strokeWidth={17} fill="none"/><ellipse cx={590} cy={1190} rx={80+50*p} ry={25} fill="#AE985F"/></>}</svg>
 {t>=24&&<Flames t={t} growth={smooth((t-24)/22)}/>}</>:<>
 {evac?<><svg width={1080} height={1920} style={{position:'absolute'}}><path d="M740 200H1080V1100H740Z" fill="#E1DCC5" {...S}/><path d="M760 230H1060V1050H760Z" fill="#B5C2B4" stroke={INK} strokeWidth={6}/></svg><Toon look="passenger" x={260+t*4.5} y={1220} rig={v} expr="concern"/><Toon look="A" x={40+t*4.0} y={1230} scale={.9} rig={v} expr="concern"/><Flames t={t} growth={.55}/><Smoke t={t}/></>:<><Toon look="passenger" x={mode==='charge'?295:450} y={1230} scale={mode==='charge'?1.13:1.35} expr="concern" gesture={mode==='charge'?'count':'recover'} t={t}/>{mode==='charge'&&<><Toon look="A" x={850} y={1210} scale={.91} expr="concern" gesture="protect" t={t}/><Stamp text={'승객 160명\n살인미수 혐의'} at={u.from_frame} color={GOLD} top={245}/></>}<Smoke t={t}/></>}
 </>}
 </AbsoluteFill></AbsoluteFill>;
};

const AssaultScene:React.FC<{u:Line;t:number;teaser?:boolean}>=({u,t,teaser=false})=>{
 const a=standing(),v=standing(),action=u.mode==='assault',hurt=u.mode==='hurt';
 const thrust=action?k(t,[[0,1],[4,1],[18,0],[30,0]]):0;
 a.torso=10+12*thrust;a.head=8*thrust;a.squash=thrust;a.feet=[[-65,0],[65,0]];
 a.hands=[[-85,-200],[110+230*thrust,-260]];a.elbows=[[-95,-270],[125,-300]];
 if(hurt){const kick=k(t,[[0,1],[4,1],[16,0],[28,0]]);a.feet[1]=[40+200*kick,-130*kick];a.knees[1]=[100,-120];a.torso=-8;}
 v.torso=action?10:13;v.head=-8;v.hip=[8,-155];v.hands=[[-25,-235],[45,-235]];v.elbows=[[-100,-255],[100,-270]];
 const protect=smooth((t-24)/20);v.hands[0]=[-45+25*protect,-270+45*protect];v.head=-5-7*protect;
 if(action&&t>=24){const attitude=k(t,[[24,0],[44,1],[57,1],[77,.3]]);a.head=-7*attitude;a.hands[1]=[110+50*attitude,-260-50*attitude];a.elbows[1]=[105,-290];}
 a.handProps=[{pose:'relaxed'},{pose:'fist'}];v.handProps=[{pose:'open'},{pose:'open'}];
 const zoom=action?1+.075*smooth((t+1)/3):1;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${zoom})`,transformOrigin:'50% 49%'}}><Parking/>
 {(action||hurt||teaser)&&<Toon x={270} y={1230} scale={1.2} rig={a} expr="angry"/>}
 <Toon look="A" x={action||hurt||teaser?790:540} y={1250} scale={action||hurt||teaser?1.12:1.3} rig={v} expr={action?'scared':'pain'}/>
 {action&&t<4&&<svg width={1080} height={1920} style={{position:'absolute'}}><path d="M610 830l18-45 10 41 47-16-29 35 42 15-43 10 17 41-37-21-26 36 3-46-43-11 42-15Z" fill={GOLD} {...S}/></svg>}
 </AbsoluteFill></AbsoluteFill>;
};

const KickScene:React.FC<{u:Line;t:number}>=({u,t})=>{
 const trip=u.mode==='trip',kick=u.mode==='kick',a=standing(),v=standing(),w=standing();
 const fall=trip?.45+.55*smooth(t/22):1,hit=kick?k(t,[[0,.9],[3,1],[15,0],[25,0]]):0;
 const withdraw=trip?smooth((t-30)/22):1;
 a.feet=[[-75,0],[-45+75*withdraw,-10+10*withdraw]];a.knees=[[-45,-90],[-25+50*withdraw,-90]];a.torso=12-7*withdraw;a.hands=[[-90,-210],[85,-235]];
 // Rotate the intact rig around its feet. Do not twist the head away from the body.
 v.hands=[[-40,-270],[65,-265]];v.elbows=[[-95,-255],[100,-265]];
 w.hands=[[-90,-220],[90,-220]];w.torso=-6-7*hit;w.feet[0]=[-30,0];w.feet[1]=[30-268*hit,-220*hit];w.knees[1]=[-110*hit,-90-65*hit];w.head=-4;
 const zoom=trip?1+.065*smooth((t+1)/3):1;
 const accusation=u.mode==='claim',evidence=u.mode==='evidence';
 if(kick&&t>22){const g=smooth((t-22)/24);w.hands[1]=[90+35*g,-220-65*g];w.head=6*g;a.hands[1]=[85-55*g,-235-45*g];}
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${zoom})`,transformOrigin:'50% 51%'}}><Parking night/>
 {trip||kick?<><Toon x={220} y={1200} scale={.94} rig={a} expr="angry"/><AbsoluteFill style={{transform:`rotate(${75*fall}deg)`,transformOrigin:'150px 1200px'}}><Toon look="driver" x={150} y={1200} scale={1.0} rig={v} expr="pain"/></AbsoluteFill><Toon look="clerk" x={840} y={1200} scale={.82} rig={w} expr="angry"/></>:<><Toon look="driver" x={accusation?290:evidence?345:380} y={1250} scale={accusation?.97:evidence?1.10:1.2} expr="concern" gesture="recover" t={t}/><Toon x={accusation?775:evidence?805:850} y={accusation?1210:1240} scale={accusation?1.1:evidence?1.08:.9} expr={accusation?'angry':evidence&&t>24?'shock':'serious'} gesture={accusation?'point':evidence&&t>=24?'flinch':'collar'} t={evidence&&t>=24?t-24:t}/></>}
 </AbsoluteFill></AbsoluteFill>;
};

const Scales:React.FC<{c:Case;f:number}>=({c,f})=>{
 const factors=c.utterances.filter(u=>(c.qid==='q018'?['victim','recovery']:['recovery','trust','factor']).includes(u.mode)),i=factors.filter(u=>u.from_frame<=f).length-1;
 const at=i>=0?factors[i].from_frame:-1000,d=f-at,target=i<0?0:-9-i*5,prev=i<=0?0:-9-(i-1)*5;
 const angle=prev+(target-prev)*(1-Math.exp(-Math.max(0,d)/8)*Math.cos(d*.4));
 return <svg width={1080} height={1920} style={{position:'absolute'}}><g transform="translate(535 1010) scale(.38)" {...S}>
  <path d="M0 -185V245M-140 245H140L112 219H-112Z" fill="#DFB958"/><g transform={`rotate(${angle})`}><path d="M-275 -145H275" stroke="#A88A42" strokeWidth={22}/>{[-1,1].map(side=><g key={side} transform={`translate(${side*255} -145)`}><path d="M0 0L-92 178M0 0L92 178" fill="none" strokeWidth={6}/><path d="M-110 178Q0 300 110 178Z" fill={side<0?RED:TEAL}/>{side<0&&factors.slice(0,i+1).map((u,j)=><rect key={u.id} x={-60+j*34} y={120-j*7-(f-u.from_frame<10?(10-(f-u.from_frame))*20:0)} width={47} height={55} rx={4} fill={RED} strokeWidth={5}/>)}</g>)}</g><circle cy={-145} r={24} fill={GOLD}/>
 </g></svg>;
};

export const Court:React.FC<{c:Case;u:Line;t:number}>=({c,u,t:elapsed})=>{
 const t=u.mode==='answer'&&elapsed>=7&&elapsed<22?7:elapsed;
 const f=useCurrentFrame(),mode=u.mode,answer=mode==='answer',choice=mode==='choices',victim=mode==='victim',deposit=mode==='deposit',wife=mode==='wife';
 const wide=choice,judgeX=wide?300:victim?190:235,defX=wide?760:victim?520:815;
 const judgeY=wide?630:1200,defY=wide?650:1260;
 const judgeScale=wide?.70:victim?.85:mode==='recovery'?1.04:1.10,defScale=wide?.70:victim?.80:mode==='recovery'?1.18:1.08;
 const factorText:Record<string,string>={recovery:c.qid==='q018'?'피해 회복 불충분':'대부분 피해 미회복',trust:'대중교통 신뢰 침해',victim:'피해자는 엄벌 요구',factor:c.qid==='q022'?'공동 폭행 · 죄질 불량':'공탁 ≠ 자동 감형'};
 const zoom=mode==='answer'?1+.08*smooth((t+1)/3):1;
 const content=<>
  {!answer&&<Actor who="judge" x={judgeX} y={judgeY} scale={judgeScale} expr={['recovery','trust','factor'].includes(mode)&&t<36?'angry':'serious'} gesture={['recovery','trust','factor'].includes(mode)&&t<36?'point':'read'} t={t<36?t:t-36}/>}
  <Toon x={defX} y={defY} scale={defScale} expr={answer?'shock':deposit?'smug':t>=32&&t<53?'shock':t<24?'serious':'concern'} gesture={answer?(t<22?'sweat':'flinch'):deposit||wide&&t<32?'palm':t>=32?'flinch':'collar'} t={answer&&t>=22?t-22:t>=32&&!answer&&!deposit?t-32:t} eye={wide?[t<16?-9:t<32?0:9,Math.min(14,t/5)]:undefined}/>
  {victim&&<Toon look={c.qid==='q018'?'A':'B'} x={840} y={1210} scale={.70} expr="concern" gesture="refuse" t={t}/>}
  {!wide&&!answer&&<Scales c={c} f={f}/>}
  {deposit&&<svg width={1080} height={1920} style={{position:'absolute'}}><g transform={`translate(535 ${935-35*smooth(t/20)}) rotate(-6)`} {...S}><path d="M-130 -130H130V130H-130Z" fill={PAPER}/><text textAnchor="middle" y={-30} stroke="none" fill={INK} fontFamily="Do Hyeon" fontSize={45}>법원 공탁</text><text textAnchor="middle" y={50} stroke="none" fill={INK} fontFamily="Do Hyeon" fontSize={62}>1억 원</text></g></svg>}
  {answer&&<><Freeze frame={669+Math.min(20,t)}><Actor who="judge" x={judgeX} y={1230} scale={1.15} expr="serious" gavel/></Freeze><svg width={1080} height={1920} style={{position:'absolute',zIndex:2}}><path d="M20 930H570V1160H20Z" fill="#80573F" {...S}/><path d="M20 930H570V970H20Z" fill="#CFAB76" {...S}/><ellipse cx={385} cy={950} rx={85} ry={17} fill="#5D3A30" stroke={INK} strokeWidth={7}/></svg></>}
  {wife&&<Toon look="clerk" x={535} y={1210} scale={.90} expr="concern" gesture="collar" t={t}/>}
 </>;
 return <AbsoluteFill><CourtBackground dark={wide||f>=c.answer_frame}/><AbsoluteFill style={{transform:`scale(${zoom})`,transformOrigin:'50% 55%'}}>{mode==='answer'&&t>=7&&t<22?<Freeze frame={c.answer_frame+7}>{content}</Freeze>:content}</AbsoluteFill>
  {factorText[mode]&&<Stamp text={factorText[mode]} at={u.from_frame+4} color={RED} top={230} small/>}
  {mode==='demand'&&<div style={{...type,position:'absolute',left:90,top:255,width:900,fontSize:68,color:GOLD}}>1심 검찰 구형 20년<div style={{fontSize:48,color:PAPER,marginTop:20}}>법원 선고와 다름</div></div>}
  {mode==='answer'&&t<4&&<AbsoluteFill style={{background:'#FFF5CC',opacity:.65*(1-t/4)}}/>}
 </AbsoluteFill>;
};

export const Film:React.FC<{c:Case;u:Line;t:number}>=({c,u,t})=>{
 if(c.kind==='snack')return ['snack','amount'].includes(u.mode)?<SnackScene u={u} t={t}/>:<RemakeCourt c={c} u={u} t={t}/>;
 if(c.kind==='forklift')return ['lift','move','reason'].includes(u.mode)?<ForkliftScene u={u} t={t}/>:<RemakeCourt c={c} u={u} t={t}/>;
 const court=c.kind==='train'?['demand','recovery','trust','choices','answer'].includes(u.mode):c.kind==='parking'?['deposit','victim','recovery','factor','choices','answer'].includes(u.mode):['factor','choices','answer','wife'].includes(u.mode);
 if(court)return <Court c={c} u={u} t={t}/>;
 if(c.kind==='train')return <TrainScene u={u} t={t}/>;
 if(c.kind==='parking')return <AssaultScene u={u} t={t}/>;
 return <KickScene u={u} t={t}/>;
};
