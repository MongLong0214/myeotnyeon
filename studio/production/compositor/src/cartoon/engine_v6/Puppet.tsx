import React from 'react';
import {C,Role,View,Expression,Gesture,Viseme,pop} from './types';
export type PuppetProps={role:Role;x:number;y:number;scale?:number;f:number;view?:View;expr?:Expression;gesture?:Gesture;viseme?:Viseme;mouth?:number;walk?:boolean;run?:boolean;seed?:number;flip?:boolean;bag?:boolean;lean?:number;still?:boolean;take?:number;fall?:number;anonymous?:boolean;smear?:number;hideRightArm?:boolean};
export const Bag:React.FC<{x?:number;y?:number;scale?:number;angle?:number}>=({x=0,y=0,scale=1,angle=0})=><g transform={`translate(${x} ${y}) rotate(${angle}) scale(${scale})`} stroke={C.ink} strokeWidth={9} strokeLinejoin="round"><path d="M-35 -65V-100Q0 -127 35 -100V-65" fill="none" strokeWidth={17}/><path d="M-103 -69Q-3 -89 103 -66L123 50Q3 80 -126 48Z" fill="#3f736d"/><path d="M-102 -65L-80 -28H90L103 -65Z" fill={C.teal}/><path d="M-65 -69V56M68 -69V56" stroke="#214745" strokeWidth={17}/><rect x={-18} y={-33} width={36} height={27} rx={5} fill={C.yellow}/></g>;
const shirts:Record<Role,string>={host:C.red,employee:C.teal,detective:'#bc9ee8',analyst:'#e9f6dd',judge:'#30273c',police:'#7197d0',robberA:'#343345',robberB:'#595865',defendantA:'#5a5b6a',defendantB:'#848292',clerk:'#77b9b0',lawyer:'#5968a5',victim:'#6f9792',recruit:'#648257',medic:'#deead8',instructor:'#4c6345'};
export const Puppet:React.FC<PuppetProps>=({role,x,y,scale=1,f,view='three-quarter',expr='neutral',gesture='rest',viseme='rest',mouth=0,walk=false,run=false,seed=1,flip=false,bag=false,lean=0,still=false,take=1,fall=0,anonymous=false,smear=0,hideRightArm=false})=>{
 const t=still?17:f;const host=role==='host',anon=anonymous||role==='victim'||/^(robber|defendant)/.test(role),back=view==='back',profile=view==='profile';
 const s=shirts[role]??C.red;const wild=host&&(expr==='alarm'||expr==='surprise'||expr==='wild');const sad=expr==='sad';
 const boil=Math.floor(t/3);const jx=Math.sin(boil*7.1+seed)*.8,jy=Math.cos(boil*5.7+seed)*.7;
 const cycle=t%39,throwing=gesture==='point'||gesture==='stop',fast=(run||gesture==='run');
 const overshoot=Math.sin(t*.57)*Math.exp(-Math.max(t,0)/9)*12*take;
 const bob=Math.sin(t*(fast?.55:.17)+seed)*(fast?17:5),stride=Math.sin(t*.55+seed)*(fast?45:walk?25:6);
 const anticipation=t<4?-12*(1-t/4):0;const bend=fall*88+lean+anticipation+overshoot+(sad?6:Math.sin(t*.13+seed)*3);
 const eyeDart=Math.sin(Math.floor(t/7+seed)*3.3)*10;const blink=(t+seed*19)%107<3;
 const arm=throwing?-92+Math.sin(t*.3)*13:gesture==='shrug'?-85+Math.sin(t*.4)*16:gesture==='think'?-48:fast?-stride*1.2:-15+Math.sin(t*.22)*12;
 const jaw=wild?(13+20*Math.abs(Math.sin(t*.29))):0;
 const body=<g stroke={C.ink} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round">
 <ellipse cx={0} cy={7} rx={78} ry={15} fill={C.ink} opacity={.25} stroke="none"/>
 {[-1,1].map(k=><g key={k} transform={`translate(${k*32} -133) rotate(${stride*k})`}><path d="M0 0L-3 62L3 125" fill="none" strokeWidth={35}/><path d="M0 0L-3 62L3 125" fill="none" stroke={host?'#4c2d63':'#343548'} strokeWidth={23}/><path d="M-13 114L23 119L40 139H-25Z" fill={host?C.yellow:'#282436'}/></g>)}
 <path d="M-55 -280L46 -289L65 -135Q0 -113 -65 -139Z" fill={s}/><path d="M30 -275L49 -148" stroke={C.ink} opacity={.18} strokeWidth={15}/>
 {host&&<><path d="M-21 -282L-5 -216L22 -285" fill={C.yellow}/><path d="M-6 -272L4 -262L-4 -228L-15 -244Z" fill="#594068" strokeWidth={4}/><path d="M-43 -179L-25 -186M31 -180L48 -186" fill="none" strokeWidth={5}/></>}
 {(role==='judge'||role==='lawyer'||role==='employee')&&<path d="M-23 -282L0 -231L23 -284L0 -265Z" fill={C.paper} strokeWidth={4}/>}
 {role==='medic'&&<path d="M-9 -257H9V-240H27V-222H9V-204H-9V-222H-27V-240H-9Z" fill={C.red} strokeWidth={3}/>}
 {role==='police'&&<path d="M10 -268L33 -268L32 -239L21 -229L9 -239Z" fill={C.yellow} strokeWidth={4}/>}
 {[-1,1].filter(k=>!(hideRightArm&&k===1)).map(k=><g key={k} transform={`translate(${k*49} -270) rotate(${k===1?arm:-arm*.63})`}><path d="M0 0Q-12 47 0 83L8 114" fill="none" strokeWidth={34}/><path d="M0 0Q-12 47 0 83L8 114" fill="none" stroke={s} strokeWidth={23}/><g transform="translate(8 118)"><path d={throwing&&k===1?'M-15 0L-10 -20L0 -20L4 -9L13 -58Q24 -67 27 -54L24 -10L39 -21L48 -10L34 18L4 28Z':'M-16 -10L-6 -23L7 -17L19 -20L31 -9L26 14L6 24L-11 14Z'} fill={anon?'#444354':C.skin} strokeWidth={6}/>{bag&&k===-1&&<Bag y={105} scale={.65}/>}</g></g>)}
 <path d="M-18 -309V-276Q0 -254 21 -279V-310" fill={anon?'#454350':C.skin}/>
 <g transform={`translate(${jx} ${jy-301}) rotate(${Math.sin(t*.16+seed)*4+(expr==='skeptic'?-11:0)})`}>
 <path d={`M-91 -131L-67 -198Q-8 -233 66 -195L100 -138L88 -35Q60 ${21+jaw} -13 ${15+jaw}L-82 -29Z`} fill={anon?'#272633':C.skin}/>
 {anon&&!/^(robber|defendant)/.test(role)?<><path d="M-92 -125L-95 -176Q-38 -224 54 -198L98 -144L70 -158L43 -179L-64 -157L-74 -111Z" fill="#343447"/><path d="M-67 -75Q0 -52 70 -73" fill="none" stroke="#454356" strokeWidth={4}/></>:anon?<><path d="M-92 -125L-103 -178Q-72 -230 5 -231Q91 -220 104 -154L95 -103L66 -164Q0 -190 -62 -158Z" fill={s}/><path d="M-67 -121Q0 -155 73 -116L75 -42L13 -12L-71 -37Z" fill="#1c1b29" stroke="#454356" strokeWidth={4}/><path d="M-47 -99L-14 -102M21 -103L49 -97" stroke="#78758d" strokeWidth={4}/></>:<>
 <ellipse cx={-90} cy={-80} rx={17} ry={25} fill={C.skin}/>
 {host?<path d="M-88 -127L-108 -184L-73 -178L-81 -230L-33 -205L-8 -243L10 -208L59 -215L79 -174L98 -130L62 -143L45 -170L13 -153L-20 -180L-55 -152L-70 -100Z" fill="#59334d"/>:<path d="M-91 -120L-94 -178Q-45 -226 38 -204L87 -166L96 -124L61 -145L39 -169L-20 -157L-68 -143L-72 -100Z" fill={role==='judge'?'#e4d9d3':'#42334d'}/>}
 {role==='police'&&<><path d="M-97 -169L-80 -206Q0 -227 79 -193L98 -156Z" fill={C.blue}/><path d="M-100 -163Q0 -177 105 -152L123 -132Q5 -125 -96 -148Z" fill="#2e3f78"/></>}
 {!back&&<g transform={`translate(${profile?21:4} 0) scale(${profile?.79:1} 1)`}>
 {(profile?[26]:[-41,39]).map((xx,k)=><g key={xx} transform={`translate(${xx} -111) scale(${wild?1.25:1} ${blink?.07:expr==='skeptic'&&k===0?.63:wild?1.42:1})`}><ellipse rx={host?37:30} ry={host?43:33} fill={C.paper}/><circle cx={eyeDart+(profile?9:0)} cy={wild?6:2} r={wild?4.7:7} fill={C.ink} stroke="none"/>{expr==='resolve'&&<path d="M-30 -24L31 -5L31 -35H-30Z" fill={C.skin} strokeWidth={4}/>}</g>)}
 <path d={wild?'M-80 -176L-28 -196M22 -191L79 -168':sad?'M-73 -153L-26 -167M25 -165L73 -153':expr==='skeptic'?'M-75 -166L-25 -179M25 -148L77 -141':'M-72 -160L-25 -166M25 -164L76 -155'} fill="none" strokeWidth={10}/>
 <path d="M4 -104L25 -64L-3 -57" fill={C.shade} strokeWidth={6}/>
 {wild?<g transform={`translate(0 ${jaw*.5})`}><ellipse cx={3} cy={-14} rx={40} ry={28+jaw*.36} fill="#50223c"/><path d="M-29 -27L31 -27L27 -12H-26Z" fill={C.paper} strokeWidth={4}/><ellipse cx={6} cy={10} rx={20} ry={8} fill="#e96482" strokeWidth={3}/></g>:(expr==='alarm'||expr==='surprise')?<ellipse cx={3} cy={-17} rx={19} ry={24} fill="#50223c" strokeWidth={6}/>:mouth>.04&&viseme!=='rest'?<g transform="translate(3 -19)"><ellipse rx={viseme==='O'?18:viseme==='E'?39:29} ry={viseme==='M'?3:viseme==='E'||viseme==='F'?12:10+mouth*22} fill="#50223c" strokeWidth={6}/>{viseme!=='M'&&viseme!=='O'&&<path d="M-20 -13H23L20 -2H-18Z" fill={C.paper} strokeWidth={3}/>}</g>:<path d={sad?'M-29 -8Q0 -27 31 -8':expr==='resolve'?'M-28 -15L28 -15':expr==='skeptic'?'M-28 -9L32 -18':'M-28 -15Q0 0 30 -17'} fill="none" strokeWidth={6}/>}
 {host&&<><path d="M-70 -49L-48 -42M47 -41L66 -48" fill="none" stroke={C.shade} strokeWidth={5}/><path d="M-22 14L-7 25L9 16" fill="#59334d" strokeWidth={4}/></>}
 {(wild||expr==='alarm')&&[0,1,2].map(k=><path key={k} transform={`translate(${103+k*16} ${-120+((t*7+k*30)%120)}) scale(${.7+k*.2})`} d="M0 -19Q-17 2 0 9Q17 3 0 -19Z" fill={C.blue} strokeWidth={4}/>)}
 </g>}
 {back&&<path d="M-63 -72Q0 -38 64 -67" fill="none" stroke={C.shade} strokeWidth={6}/>}
 </>}
 </g></g>;
 return <g data-character={role} data-expression={expr} transform={`translate(${x} ${y+bob}) scale(${flip?-scale:scale} ${scale}) rotate(${bend})`}>
 {((fast||throwing||smear>0)&&cycle<5)&&[2,1].map(k=><g key={k} transform={`translate(${-k*31} ${k*3}) scale(${1+k*.08} ${1-k*.035})`} opacity={.11/k}>{body}</g>)}
 <g transform={`scale(${1+Math.sin(t*.27)*.018} ${1-Math.sin(t*.27)*.018})`}>{body}</g>
 </g>;
};
