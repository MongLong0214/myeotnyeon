import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {ArticulatedGuy,RigPose,Point} from '../q014/fight_revision/comedy/FightRig';
const ink='#1E1712',paper='#FFF4D7',teal='#3FB8A9',red='#C9503E';
const stroke={stroke:ink,strokeWidth:8,strokeLinejoin:'round' as const,strokeLinecap:'round' as const};
const smooth=(v:number)=>{v=Math.min(1,Math.max(0,v));return v*v*(3-2*v)};
const mix=(a:number,b:number,t:number)=>a+(b-a)*smooth(t);
const pose=():RigPose=>({hip:[0,-170],torso:0,head:0,feet:[[-30,0],[30,0]],knees:[[-25,-90],[26,-90]],hands:[[-84,-166],[84,-166]],elbows:[[-70,-230],[70,-230]]});
export const Reenactment:React.FC<{kind:string;mode:string;frame?:number;length?:number}>=({kind,mode,frame,length=100})=>{
 const f=useCurrentFrame(),t=(frame??f)/30+.24,progress=Math.min(1,(frame??f)/length);
 const a=pose(),v=pose(),judge=pose();let ax=280,ay=810,vx=660,vy=810,s=.66;
 const action=mode==='action',reaction=mode==='reaction',result=mode==='result';
 const attack=smooth((t+.12)/.34),recover=smooth((t-.28)/.6),fall=smooth((t-.3)/.72);
 a.torso=action?mix(-26,24,attack)-recover*22:reaction?-10:0;
 a.head=action?-10:reaction?12:0;
 v.head=action?mix(0,24,fall):reaction?-12:0;
 if(action){a.hands[1]=[mix(70,390,attack)-recover*260,mix(-220,-350,attack)+recover*100];a.elbows![1]=[mix(55,210,attack)-recover*140,-280];v.hands=[[mix(-84,-150,fall),mix(-166,-260,fall)],[mix(84,140,fall),mix(-166,-250,fall)]];v.torso=18*fall;}
 if(reaction){a.hands[1]=[130,-260];a.elbows![1]=[110,-315];v.hands=[[-140,-300],[120,-240]];v.elbows=[[-140,-260],[105,-305]];v.torso=mix(18,0,progress);}
 if(result){v.hands=[[-65,-360],[100,-190]];v.elbows=[[-100,-300],[100,-260]];v.head=-15;}
 const court=['court','question','answer'].includes(mode);
 if(court){judge.hands[1]=[mix(100,180,progress),-210];judge.elbows![1]=[100,-280];a.hands=[[-68,-175],[68,-175]];a.torso=6;v.head=-8;}
 if(kind==='kick'&&action){
  a.hands[1]=[180,-200];a.elbows![1]=[110,-270];
  v.hip=[60*fall,-170+128*fall];v.torso=42*fall;v.knees=[[100*fall-25,-90+80*fall],[120*fall+26,-90+80*fall]];v.hands=[[120*fall-84,-166+150*fall],[160*fall+84,-166+150*fall]];
 }
 if(kind==='blanket'&&action){ax=440;a.hands=[[-75,-180],[75,-200]];a.feet[1]=[mix(30,170,attack),-80+recover*80];a.knees[1]=[100,-160+recover*70];a.torso=mix(-10,20,attack);}
 if(kind==='store'&&reaction){a.hands[1]=[212,-410];a.elbows![1]=[100,-340];}
 if(kind==='salt'&&action){v.torso=mix(20,34,attack);v.hands=[[-170,-150],[80,-280]];v.elbows=[[-80,-235],[50,-315]];a.hands[1]=[110,-210];a.torso=-8;}
 if(kind==='train'&&action){a.hands[1]=[145,-180];a.elbows![1]=[110,-270];v.hands=[[-160,-265],[130,-270]];v.torso=20*fall;vx=660+100*fall;}
 const courtBg=<svg width={1000} height={900}><rect width={1000} height={900} fill="#DBDBB8"/><rect x={65} y={90} width={870} height={600} rx={20} fill="#B9C99D" {...stroke}/>{[185,440,695].map(x=><path key={x} d={`M${x},135v480`} stroke="#94AB83" strokeWidth={48}/>)}<path d="M0,720H1000V900H0Z" fill="#A47857" {...stroke}/><path d="M500,130v160m-95,-85h190m-180,0l-38,75h76zm170,0l-38,75h76z" fill={paper} {...stroke}/></svg>;
 const bg=<svg width={1000} height={900}>
  <rect width={1000} height={900} fill={kind==='train'?'#CFDBDD':kind==='salt'?'#C7DCDD':kind==='blanket'?'#D5DCC3':'#D3D7D2'}/>
  {kind==='store'&&<>{[60,370,680].map((x,j)=><g key={x}><rect x={x} y={180} width={270} height={410} fill="#DAE6BA" {...stroke}/>{[270,390,510].map(y=><g key={y}><path d={`M${x},${y}h270`} {...stroke}/>{[35,105,175].map((v,k)=><rect key={v} x={x+v} y={y-70} width={45} height={65} rx={5} fill={['#D9A66E','#F0D177','#91B5A6'][(j+k)%3]} {...stroke}/>)}</g>)}</g>)}<path d="M0,695H1000V900H0Z" fill="#B4C4B1" {...stroke}/></>}
  {kind==='blanket'&&<><rect x={660} y={130} width={250} height={570} fill="#91A7A0" {...stroke}/><path d="M0,720H1000V900H0Z" fill="#AA987D" {...stroke}/><path d="M80,180h410v210H80Z" fill={paper} {...stroke}/><path d="M110,240h320M110,290h240" stroke="#B7C3A5" strokeWidth={15}/></>}
  {kind==='salt'&&<><path d="M0,580L1000,500V900H0Z" fill="#ECE7CE" {...stroke}/>{[620,715,815].map(y=><path key={y} d={`M0,${y}L1000,${y-80}`} stroke="#9BBAC2" strokeWidth={22}/>)}<path d="M750,540l110,-180 120,180zM40,650l170,-190 140,180z" fill="#FFF8E3" {...stroke}/><circle cx={120} cy={120} r={65} fill="#F2C14E"/></>}
  {kind==='train'&&<><path d="M0,85H1000M0,180H1000M0,670H1000" {...stroke}/>{[50,380,710].map(x=><g key={x}><rect x={x} y={220} width={250} height={250} rx={35} fill="#667981" {...stroke}/><rect x={x} y={510} width={250} height={160} rx={20} fill="#3E9E9B" {...stroke}/></g>)}<path d="M0,700H1000V900H0Z" fill="#969A9E" {...stroke}/><path d="M320,180v510M680,180v510" stroke={ink} strokeWidth={15}/></>}
  {['parking','kick'].includes(kind)&&<><path d="M0,0H1000V620H0Z" fill="#576475"/><path d="M0,650H1000V900H0Z" fill="#858D90" {...stroke}/><path d="M80,760L280,670M620,880L890,700" stroke={paper} strokeWidth={13}/><rect x={30} y={270} width={940} height={280} rx={30} fill="#405060" {...stroke}/><path d="M0,0H1000V100H0Z" fill="#C7C8B7"/>{[150,810].map(x=><rect key={x} x={x} y={90} width={50} height={560} fill="#A8B1A8" {...stroke}/>)}<rect x={60} y={510} width={270} height={120} rx={35} fill="#849DAA" {...stroke}/><circle cx={115} cy={630} r={38} fill={ink}/><circle cx={280} cy={630} r={38} fill={ink}/></>}
 </svg>;
 const camera=action?1+Math.min(progress,.8)*.07:reaction?1.08+progress*.10:result?1.1+progress*.08:1+progress*.18;
 return <AbsoluteFill style={{overflow:'hidden',transform:`scale(${camera})`,transformOrigin:'50% 60%'}}>
  {court?courtBg:bg}
  {court?<>
   <ArticulatedGuy look="hoodie" x={255} y={835} scale={.55} rig={a} expr="serious" eye={[12,0]}/>
   <ArticulatedGuy look="judge" x={690} y={730} scale={.6} rig={judge} expr="serious" eye={[-12,0]}/>
   <svg width={1000} height={900}><path d="M450,690H965V860H450Z" fill="#926846" {...stroke}/><path d="M460,690H970" stroke={ink} strokeWidth={25}/></svg>
  </>:<>
   {!(kind==='blanket'&&action)&&<ArticulatedGuy look="B" x={vx} y={vy} scale={s} rig={v} expr={action||reaction?'scared':'concern'} eye={[-10,0]}/>}
   {kind==='blanket'&&action&&<svg width={1000} height={900}><path d="M470,810q15,-150 80,-105q70,-125 135,0q120,-60 160,105Z" fill="#8096B0" {...stroke}/><path d="M550,800q30,-110 70,-70M690,800q40,-90 70,-60" fill="none" stroke="#526B8C" strokeWidth={14}/><ellipse cx={830} cy={805} rx={45} ry={19} fill="#E2C39E" {...stroke}/></svg>}
   <ArticulatedGuy look="hoodie" x={ax} y={ay} scale={s} rig={a} expr="serious" eye={[10,0]}/>
   {kind==='kick'&&action&&t>.4&&<Kicker progress={smooth((t-.4)/.65)}/>}
   {kind==='salt'&&action&&<svg width={1000} height={900}><path d="M548,690L760,805M700,805h150m-140,0v26m30,-26v26m30,-26v26m30,-26v26m30,-26v26" fill="none" {...stroke}/></svg>}
   {kind==='train'&&(action||reaction)&&<svg width={1000} height={900}><ellipse cx={490} cy={800} rx={155} ry={27} fill="#A77E52" opacity={.9}/>{action&&<><g transform="translate(398 680) rotate(40)"><path d="M-45,-25h75v105h-75zM-25,-25v-22h45v22M30,-10l42,10v30H30" fill="#B9925D" {...stroke}/><path d="M-22,15h38v35h-38z" fill={paper} stroke={ink} strokeWidth={5}/></g><path d="M455,714Q490,755 490,795" fill="none" stroke="#A77E52" strokeWidth={17}/></>}{[390,465,540].map((x,i)=><path key={x} d={`M${x},815q-50,-80 0,-${130+25*Math.sin(t*7+i)}q85,80 45,130Z`} fill="#E47B3B" stroke={ink} strokeWidth={7}/>)}{reaction&&[430,520,590].map((x,i)=><ellipse key={x} cx={x} cy={mix(480,130,progress)+i*70} rx={100} ry={150} fill="#707779" opacity={.45}/>)}</svg>}
   {kind==='store'&&reaction&&<svg width={1000} height={900}><g transform={`translate(420 540) rotate(${mix(-35,20,progress)})`}><path d="M-60,-90H60V0H-60ZM-55,0v100m110,-100v100" fill="#9DAF96" {...stroke}/></g></svg>}
   {mode==='result'&&kind==='salt'&&<svg width={1000} height={900}><g transform={`translate(${mix(650,370,progress)} 640)`}><rect x={-100} y={-60} width={200} height={120} fill="#C9DF92" {...stroke}/><circle r={30} fill="none" {...stroke}/></g></svg>}
  </>}
 </AbsoluteFill>;
};
const Kicker:React.FC<{progress:number}>=({progress})=>{
 const r=pose();r.feet[0]=[-30,0];r.feet[1]=[mix(30,-200,progress),mix(0,-90,progress)];r.knees[1]=[-90,-140];r.hands=[[-80,-180],[80,-200]];r.torso=12;
 return <ArticulatedGuy look="hoodie" x={890} y={815} scale={.54} rig={r} expr="serious" eye={[-12,0]}/>;
};
