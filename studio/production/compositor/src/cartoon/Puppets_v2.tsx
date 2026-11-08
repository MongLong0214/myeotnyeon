import React from 'react';

// Exact channel colours from components/toon.tsx; judge anatomy from components/rm.tsx.
export const C={ink:'#141414',line:'#1E1712',paper:'#FFFDF6',yellow:'#FFD84A',teal:'#21B8B0',red:'#F0433A',skin:'#F4CFA7',shade:'#E2AE84',wood:'#91643F',slate:'#34424C'};
export type Role='host'|'employee'|'robberA'|'robberB'|'detective'|'judge';
export type Expression='neutral'|'skeptic'|'alarm'|'resolve';
export type View='front'|'three-quarter'|'profile'|'back';
const outfits:Record<Role,[string,string,string]>={host:['#DDAF44','#B38B34','#34424C'],employee:['#497D79','#355C5A','#34424C'],robberA:['#30333C','#20232A','#242630'],robberB:['#45464C','#303137','#292A31'],detective:['#B5A58A','#92836D','#34424C'],judge:['#22232B','#15161C','#22232B']};
export const Bag:React.FC<{x?:number;y?:number;scale?:number;angle?:number}>=({x=0,y=0,scale=1,angle=0})=><g transform={`translate(${x} ${y}) rotate(${angle}) scale(${scale})`} stroke={C.line} strokeWidth={7} strokeLinejoin="round"><path d="M-37 -77 Q-37 -119 0 -119 Q38 -119 38 -77" fill="none" strokeWidth={12}/><path d="M-96 -80 Q0 -96 96 -80 L106 30 Q0 54 -109 28Z" fill="#77765E"/><path d="M-96 -80 L-70 -40 L79 -40 L96 -80" fill="#919078"/><path d="M-58 -72L-58 30M60 -72L60 30" fill="none" stroke="#515345" strokeWidth={13}/><path d="M-72 -37Q0 -20 74 -37" fill="none" strokeWidth={4}/><rect x={-13} y={-48} width={26} height={20} rx={4} fill={C.yellow}/></g>;

const Arm:React.FC<{side:number;a:number;b:number;color:string;hand:string;bag?:boolean}>=({side,a,b,color,hand,bag})=><g transform={`translate(${side*52} -302) rotate(${a})`}>
 <path d="M0 0Q-5 36 0 74" stroke={C.line} strokeWidth={28} fill="none" strokeLinecap="round"/><path d="M0 0Q-5 36 0 74" stroke={color} strokeWidth={17} fill="none" strokeLinecap="round"/>
 <g transform={`translate(0 74) rotate(${b})`}><path d="M0 0L2 68" stroke={C.line} strokeWidth={24} strokeLinecap="round"/><path d="M0 0L2 68" stroke={hand} strokeWidth={13} strokeLinecap="round"/><g transform="translate(2 75)"><path d="M-13 -8Q-21 4 -12 14Q-2 23 13 12L15 -4Q9 -19 -1 -12Z" fill={hand} stroke={C.line} strokeWidth={6}/>{bag&&<Bag x={5} y={96} scale={.65}/>}</g></g>
</g>;

const Face:React.FC<{role:Role;expr:Expression;f:number;mouth:number;view:View;seed:number}>=({role,expr,f,mouth,view,seed})=>{
 const anonymous=role==='employee'||role==='robberA'||role==='robberB';const robber=role.startsWith('robber');const back=view==='back';const profile=view==='profile';
 const phase=(f+seed*29)%157;const blink=phase<7?Math.abs(phase-3.5)/3.5:1;
 const eyes=profile?[46]:[-36,36]; const eyeY=expr==='alarm'?-478:-470;const lid=expr==='skeptic'?.42:expr==='resolve'?.24:0;
 const fill=robber?'#191B22':role==='employee'?'#D4D9CE':C.skin;
 return <g transform={`scale(${profile?.62:view==='three-quarter'?.86:1} 1)`}>
 <path d={role==='detective'?'M-116 -470L-104 -570Q0 -602 104 -566L118 -470L98 -366Q0 -324 -98 -366Z':'M-118 -470Q-124 -570 -40 -584Q30 -596 92 -566Q132 -540 124 -470Q130 -400 96 -366Q50 -334 0 -336Q-60 -334 -96 -364Q-128 -400 -118 -470Z'} fill={back?(robber?fill:role==='employee'?'#B5C1B8':role==='judge'?C.skin:'#302A29'):fill} stroke={C.line} strokeWidth={8} strokeLinejoin="round"/>
 {!back&&!robber&&role!=='employee'&&<><path d="M70 -360Q100 -380 110 -430" stroke={C.shade} strokeWidth={12} fill="none" strokeLinecap="round"/>{!profile&&<ellipse cx={-124} cy={-452} rx={16} ry={26} fill={C.skin} stroke={C.line} strokeWidth={6}/>}<ellipse cx={124} cy={-452} rx={16} ry={26} fill={C.skin} stroke={C.line} strokeWidth={6}/></>}
 {role==='host'&&<><path d="M-115 -493Q-140 -601 -42 -613Q-22 -628 0 -608Q97 -630 120 -543L111 -500L83 -528L69 -565Q3 -530 -59 -568Q-92 -546 -100 -500Z" fill="#302A29" stroke={C.line} strokeWidth={8}/><path d="M-92 -549Q-36 -593 37 -575" fill="none" stroke="#5C4A3F" strokeWidth={10}/></>}
 {role==='detective'&&<path d="M-116 -512L-116 -577Q-16 -615 104 -581L120 -514L84 -535L67 -561L-86 -551L-95 -514Z" fill="#343139" stroke={C.line} strokeWidth={8}/>}
 {role==='judge'&&<g stroke={C.line} strokeWidth={6}><path d="M-122 -470Q-150 -500 -128 -534Q-112 -500 -100 -516Q-104 -480 -122 -470Z" fill="#E8E8E8"/><path d="M122 -470Q150 -500 128 -534Q112 -500 100 -516Q104 -480 122 -470Z" fill="#E8E8E8"/><path d="M-60 -560Q0 -596 60 -560" fill="none" stroke={C.shade} strokeWidth={8}/></g>}
 {role==='employee'&&<><path d="M-119 -494Q-126 -592 0 -598Q110 -594 123 -494L83 -524L-86 -524Z" fill="#497D79" stroke={C.line} strokeWidth={8}/><path d="M-106 -524L101 -524" stroke="#789C91" strokeWidth={10}/></>}
 {role==='robberA'&&<><path d="M-125 -424Q-169 -596 -46 -627L0 -642L76 -612Q162 -552 124 -424L105 -510Q0 -554 -103 -509Z" fill="#30333C" stroke={C.line} strokeWidth={9}/><path d="M-87 -500Q0 -530 85 -500L88 -399Q0 -355 -89 -399Z" fill="#101218" stroke="#4E515C" strokeWidth={4}/></>}
 {role==='robberB'&&<><path d="M-124 -514L-111 -596Q0 -628 111 -596L126 -513Z" fill="#55565B" stroke={C.line} strokeWidth={8}/><path d="M-126 -523Q0 -537 126 -523L122 -493Q0 -506 -123 -493Z" fill="#383940" stroke={C.line} strokeWidth={7}/><path d="M-96 -454Q0 -480 99 -454L90 -371Q0 -334 -90 -373Z" fill="#24262E" stroke="#62636C" strokeWidth={4}/></>}
 {!back&&!anonymous&&<g transform={`translate(${view==='three-quarter'?17:0} 0)`}>
  {eyes.map((x,i)=><g key={x} transform={`translate(${x} ${eyeY}) scale(1 ${Math.max(.05,blink)})`}><ellipse rx={expr==='alarm'?41:35} ry={expr==='alarm'?43:36} fill="#FFF" stroke={C.line} strokeWidth={6}/><circle cx={Math.sin(f/70+seed)*5+(profile?10:0)} cy={1} r={expr==='alarm'?4:6} fill={C.line}/>{lid>0&&<path d={`M-34 -10Q0 -45 34 -10L34 ${-26+lid*40}L-34 ${-26+lid*40}Z`} fill={C.skin} stroke={C.line} strokeWidth={4}/>}</g>)}
  <path d={expr==='alarm'?'M-72 -530L-16 -543M20 -540L77 -525':expr==='skeptic'?'M-73 -534L-13 -542M19 -520L76 -520':expr==='resolve'?'M-71 -531L-16 -514M18 -514L75 -531':'M-69 -522Q-42 -531 -16 -523M20 -523Q46 -530 71 -521'} stroke={C.line} strokeWidth={8} fill="none" strokeLinecap="round"/>
  {role==='judge'&&<g fill="none" stroke={C.line} strokeWidth={6}>{(profile?[10]:[-74,8]).map(x=><rect key={x} x={x} y={-492} width={66} height={44} rx={10}/>)}{!profile&&<path d="M-8 -472L8 -472"/>}</g>}
  <path d={profile?'M71 -451L101 -423L73 -412':'M-6 -440Q-22 -418 -2 -412'} fill="none" stroke={C.line} strokeWidth={6} strokeLinecap="round"/>
  <g transform={`translate(${profile?50:0} -391)`}>{mouth>.065?<><ellipse rx={29+mouth*7} ry={4+mouth*22} fill="#4B2928" stroke={C.line} strokeWidth={6}/>{mouth>.42&&<path d="M-21 -9Q0 -15 21 -9L17 -2L-17 -2Z" fill={C.paper}/>}</>:expr==='alarm'?<ellipse rx={20} ry={23} fill="#4B2928" stroke={C.line} strokeWidth={6}/>:<path d={expr==='skeptic'?'M-32 3Q2 6 35 -8':expr==='resolve'?'M-33 2Q0 -8 34 2':'M-30 -2Q0 12 32 -2'} fill="none" stroke={C.line} strokeWidth={7} strokeLinecap="round"/>}</g>
 </g>}
 {/* Anonymous figures never acquire facial features, including on the expression atlas. */}
 {anonymous&&!back&&<path d={expr==='alarm'?'M-96 -351L-106 -326M96 -351L107 -326':expr==='resolve'?'M-87 -372L-107 -364M87 -372L107 -364':'M-93 -380L-99 -360'} fill="none" stroke={robber?'#62636C':'#95A99D'} strokeWidth={4}/>}
 </g>;
};

export const Puppet:React.FC<{role:Role;x:number;y:number;scale?:number;f:number;expr?:Expression;view?:View;mouth?:number;gesture?:'rest'|'point'|'shrug'|'hold';walk?:boolean;seed?:number;still?:boolean;bag?:boolean}>=({role,x,y,scale=1,f,expr='neutral',view='front',mouth=0,gesture='rest',walk=false,seed=1,still=false,bag=false})=>{
 const [shirt,shade,pants]=outfits[role];const robber=role.startsWith('robber');const hand=robber?'#30323B':role==='employee'?'#C5D2C6':C.skin;
 const t=still?0:f;const wave=Math.sin(t/13+seed);const bob=still?0:Math.sin(t/8+seed)*3;const sq=still?0:Math.sin(t/11+seed)*.009;
 const tilt=(still?0:Math.sin(t/17+seed)*1.4)+(expr==='skeptic'?-7:expr==='alarm'?4:0);const walkPhase=walk?Math.sin(t/4+seed):0;
 let left=12+wave*4,right=-17-wave*4,el=8,er=-9;
 if(gesture==='point'){right=-92+wave*5;er=20;}if(gesture==='shrug'){left=67+wave*4;right=-67-wave*4;el=55;er=-55;}if(gesture==='hold'){right=-12;er=-8;}
 if(expr==='resolve'){left=28;right=-35;}if(expr==='alarm'){left=45;right=-45;el=35;er=-35;}
 const bodyScale=role==='robberB'?1.2:role==='robberA'?.85:1;const boil=still?0:Math.sin(Math.floor(t/4)*7+seed)*.48;
 return <g data-character={role} transform={`translate(${x} ${y+bob}) scale(${scale*(1+sq)} ${scale*(1-sq)})`}>
 <ellipse cx={0} cy={7} rx={91} ry={13} fill={C.ink} opacity={.15}/>
 <g transform={`scale(${bodyScale} 1)`}>
 {[-1,1].map(k=><g key={k} transform={`translate(${k*29} -170) rotate(${walkPhase*k*16})`}><path d="M0 0L1 153" stroke={C.line} strokeWidth={37} strokeLinecap="round"/><path d="M0 0L1 153" stroke={pants} strokeWidth={24} strokeLinecap="round"/><path d={`M-18 148Q${k*15} 138 ${k*36} 157L${k*37} 170L-19 170Z`} fill={role==='host'?'#EEE5CF':'#26272D'} stroke={C.line} strokeWidth={6}/></g>)}
 <path d="M-58 -170Q-66 -300 -48 -318L48 -318Q66 -300 58 -170Q0 -158 -58 -170Z" fill={shirt} stroke={C.line} strokeWidth={8} strokeLinejoin="round"/><path d="M32 -309Q51 -258 43 -179" fill="none" stroke={shade} strokeWidth={15} strokeLinecap="round"/>
 {view==='back'?<path d="M0 -307L0 -182" stroke={shade} strokeWidth={7}/>:role==='judge'?<path d="M-26 -318L0 -270L26 -318" fill="white" stroke={C.line} strokeWidth={6}/>:role==='host'?<><path d="M-28 -315L0 -261L30 -315Z" fill={C.teal} stroke={C.line} strokeWidth={5}/><path d="M-36 -294L-20 -269M37 -294L20 -269" stroke={C.line} strokeWidth={5}/></>:role==='detective'?<><path d="M-26 -314L0 -259L28 -314Z" fill={C.paper} stroke={C.line} strokeWidth={5}/><path d="M-5 -295L6 -295L10 -238L0 -228L-10 -238Z" fill={C.teal} stroke={C.line} strokeWidth={4}/></>:role==='employee'?<path d="M-37 -312L-19 -181M35 -312L18 -181" stroke="#8FA99B" strokeWidth={8}/>:<path d="M-33 -316Q0 -277 34 -316M0 -289L0 -189" fill="none" stroke={shade} strokeWidth={7}/>}
 <Arm side={-1} a={left+walkPhase*12} b={el} color={shirt} hand={hand}/><Arm side={1} a={right-walkPhase*12} b={er} color={shirt} hand={hand} bag={bag}/>
 </g>
 <g transform={`translate(${boil} -312) rotate(${tilt}) scale(1.28) translate(0 312)`}><Face role={role} expr={expr} f={t} mouth={mouth} view={view} seed={seed}/></g>
 </g>;
};
