import React from 'react';
import {C, ease, Role, View} from './types';
import {Bag} from './Puppet';
import {Car, Glyph} from './Stage';

// A performance has a beginning and an end. No idle cycle, line boil, or
// decorative camera jitter is used in these scenes.
type XY=[number,number];
export type PerformanceActor={
 id:string;role:Role;x:number;y:number;scale?:number;view?:View;flip?:boolean;
 to?:XY;move?:[number,number];run?:boolean;fall?:[number,number];
 left?:XY;right?:XY;leftTo?:XY;rightTo?:XY;beat?:[number,number];
 head?:[number,number];gaze?:[number,number];expression?:'neutral'|'firm'|'sad'|'surprise';
 item?:string;leftItem?:string;anonymous?:boolean;talk?:boolean;
};
type SceneProp={kind:string;x:number;y:number;scale?:number;to?:XY;beat?:[number,number];angle?:number;truck?:boolean;flip?:boolean;turn?:number;occupants?:boolean};
export type Performance={
 room:string;layout:string;actors:PerformanceActor[];props:SceneProp[];
 foreground?:'desk'|'bench'|'lab'|'rail';date?:string;place?:string;
 camera?:{from:XY;to:XY};clock:number;duration:number;
 fire?:{actor:string;start:number;end:number};fireAttempt?:boolean;
};
const mix=(a:number,b:number,u:number)=>a+(b-a)*u;
const phase=(t:number,b:[number,number]=[0,1])=>ease((t-b[0])/Math.max(.001,b[1]-b[0]));
const point=(a:XY,b:XY,u:number):XY=>[mix(a[0],b[0],u),mix(a[1],b[1],u)];
const shirt:Record<string,string>={host:C.red,employee:C.teal,detective:'#bc9ee8',analyst:'#e9f6dd',judge:'#30273c',police:'#7197d0',robberA:'#343345',robberB:'#595865',defendantA:'#5a5b6a',defendantB:'#848292',clerk:'#77b9b0',lawyer:'#5968a5',victim:'#6f9792'};

const HandProp:React.FC<{kind:string;t:number}>=({kind,t})=>{
 if(kind==='bag')return <Bag y={84} scale={.7}/>;
 if(kind==='gun')return <Glyph kind="gun" x={46} y={-5} scale={.34}/>;
 if(['mask','cloth','cigarette'].includes(kind))return <Glyph kind={kind} x={8} y={0} scale={kind==='cigarette'?.16:.25}/>;
 if(kind==='swab')return <g stroke={C.ink} strokeWidth={4}><path d="M0 0L42 -65" stroke={C.paper} strokeWidth={7}/><path d="M36 -57L48 -77" stroke={C.paper} strokeWidth={14}/></g>;
 if(kind==='flowers')return <g stroke={C.ink} strokeWidth={4}><path d="M0 36L-16 -29M0 36L25 -41M0 36L6 -63" stroke="#426d5c" strokeWidth={7}/>{[[-16,-35],[25,-44],[6,-66]].map(([x,y],i)=><g key={i} transform={`translate(${x} ${y})`}><path d="M-22 0L-8 -9L0 -27L10 -11L25 0L9 12L0 24L-9 10Z" fill={C.paper}/><circle r={7} fill={C.yellow}/></g>)}</g>;
 if(kind==='phone')return <path d="M-17 -43H22V36H-17Z" fill="#434259" stroke={C.ink} strokeWidth={6}/>;
 if(kind==='book')return <g stroke={C.ink} strokeWidth={6}><path d="M-64 -33L-3 -24L57 -45L65 44L2 65L-61 45Z" fill={C.red}/><path d="M-54 -26L-3 -15L48 -35L54 34L0 53L-53 36Z" fill={C.paper}/><path d="M-3 -15L0 53" fill="none"/><path d={`M-3 -15L${mix(48,-53,phase(t,[.22,.68]))} -35L${mix(54,-53,phase(t,[.22,.68]))} 34L0 53Z`} fill="#e8dcc2" strokeWidth={3}/></g>;
 if(kind==='evidence')return <g stroke={C.ink} strokeWidth={5}><path d="M-46 -45H50L57 61H-50Z" fill="#d3e5d1" fillOpacity={.85}/><path d="M-44 -28H50" stroke={C.teal} strokeWidth={8}/><Glyph kind="mask" y={20} scale={.18}/></g>;
 return <g transform={kind==='file'?'rotate(-8)':undefined} stroke={C.ink} strokeWidth={5}><path d="M-52 -61H39L58 -40L50 61H-57Z" fill={kind==='file'?'#cfb880':C.paper}/><path d="M-34 -29H29M-35 -7H32M-35 15H24M-34 37H8" stroke="#9c93ad" strokeWidth={5}/>{kind==='file'&&<g transform={`translate(${-13*phase(t,[.2,.7])} 0) rotate(${-32*phase(t,[.2,.7])} -45 50)`}><path d="M-44 -47H38V50H-44Z" fill={C.paper} strokeWidth={3}/><path d="M-29 -25H24M-29 -6H22M-29 15H17" stroke="#9c93ad" strokeWidth={4}/></g>}</g>;
};

const Actor:React.FC<{a:PerformanceActor;t:number;seconds:number;fire?:boolean}>=({a,t,seconds,fire})=>{
 const u=phase(t,a.beat??[.12,.82]),travel=phase(t,a.move??[.02,.96]);
 const moving=!!a.to&&t>(a.move?.[0]??.02)&&t<(a.move?.[1]??.96);
 const [x,y]=point([a.x,a.y],a.to??[a.x,a.y],travel);
 const side=a.view==='profile',back=a.view==='back',front=a.view==='front';
 const anonymous=a.anonymous||a.role==='victim'||/robber|defendant/.test(a.role);
 const skin=anonymous?'#454350':C.skin,s=shirt[a.role]??C.teal;
 const stride=moving?Math.sin(seconds*(a.run?15:8))*(a.run?42:25):0;
 const bob=moving?-Math.abs(Math.sin(seconds*(a.run?15:8)))*(a.run?12:5):0;
 const fall=mix(a.fall?.[0]??0,a.fall?.[1]??0,u)*-87;
 const head=mix(a.head?.[0]??0,a.head?.[1]??0,u),gaze=mix(a.gaze?.[0]??8,a.gaze?.[1]??8,u);
 const l=point(a.left??[-72,-155],a.leftTo??a.left??[-72,-155],u);
 const r=point(a.right??[73,-155],a.rightTo??a.right??[73,-155],u);
 const limb=(hand:XY,k:number)=>{
  const shoulder:XY=[side?k*24:k*48,-270],elbow:XY=[mix(shoulder[0],hand[0],.55)+k*24,mix(-270,hand[1],.56)+20];
  return <g key={k}><path d={`M${shoulder}Q${elbow} ${hand}`} fill="none" stroke={C.ink} strokeWidth={32}/><path d={`M${shoulder}Q${elbow} ${hand}`} fill="none" stroke={s} strokeWidth={21}/><g transform={`translate(${hand})`}><path d="M-13 -10L-3 -19L10 -14L21 -2L15 17L-7 19L-17 7Z" fill={skin} stroke={C.ink} strokeWidth={5}/>{(k===1?a.item:a.leftItem)&&<HandProp kind={(k===1?a.item:a.leftItem)!} t={t}/>} {k===1&&a.item==='gun'&&fire&&<path transform="translate(102 -10) scale(.55)" d="M0 0L32 -36L40 -12L91 -22L63 7L91 34L42 23L24 51L16 18L-9 26Z" fill={C.yellow} stroke={C.ink} strokeWidth={5}/>}</g></g>;
 };
 const eyes=<g stroke={C.ink} strokeWidth={6}>
  {(side?[38]:front?[-38,37]:[-29,45]).map((ex,i)=><g key={i} transform={`translate(${ex} -105)`}><ellipse rx={side?24:i?28:33} ry={a.expression==='surprise'?37:30} fill={C.paper}/><circle cx={gaze} cy={a.expression==='sad'?9:2} r={6} fill={C.ink} stroke="none"/></g>)}
  <path d={a.expression==='sad'?'M-59 -143L-20 -158M24 -157L65 -144':a.expression==='firm'?'M-60 -160L-19 -146M24 -146L71 -162':'M-58 -151L-20 -157M24 -155L68 -149'} fill="none" strokeWidth={8}/>
  {!side&&<path d="M9 -103L30 -67L5 -59" fill={C.shade} strokeWidth={5}/>}
  {a.talk&&t>.15&&t<.8?<ellipse cx={side?49:9} cy={-23} rx={side?12:20} ry={7+Math.abs(Math.sin(seconds*9))*7} fill="#50223c" strokeWidth={5}/>:<path d={side?'M40 -27L66 -30':a.expression==='sad'?'M-22 -14Q4 -29 31 -15':'M-22 -24L33 -22'} fill="none" strokeWidth={5}/>}
 </g>;
 return <g data-character={a.role} data-view={a.view} transform={`translate(${x} ${y+bob}) scale(${a.flip?-(a.scale??1):a.scale??1} ${a.scale??1}) rotate(${fall})`} strokeLinecap="round" strokeLinejoin="round">
  <ellipse cy={5} rx={71} ry={12} fill={C.ink} opacity={.23}/>
  {[-1,1].map(k=><g key={k} transform={`translate(${side?k*17:k*30} -130) rotate(${stride*k})`} stroke={C.ink} strokeWidth={8}><path d="M0 0L-4 71L1 126" fill="none" strokeWidth={32}/><path d="M0 0L-4 71L1 126" fill="none" stroke="#343548" strokeWidth={21}/><path d="M-14 115L20 118L35 134H-24Z" fill="#282436"/></g>)}
  {limb(l,-1)}
  <path d={side?'M-35 -285L32 -277L47 -137L-38 -130Z':back?'M-63 -279L55 -281L65 -137L-64 -133Z':'M-55 -280L46 -289L65 -135Q0 -113 -65 -139Z'} fill={s} stroke={C.ink} strokeWidth={8}/>
  {!back&&(a.role==='judge'||a.role==='lawyer'||a.role==='employee')&&<path d="M-22 -282L0 -231L24 -284L0 -265Z" fill={C.paper} stroke={C.ink} strokeWidth={4}/>}
  {!back&&a.role==='host'&&<path d="M-23 -281L0 -227L23 -286L0 -262Z" fill={C.yellow} stroke={C.ink} strokeWidth={5}/>}
  {a.role==='police'&&!back&&<path d="M9 -264H33L31 -239L21 -230L10 -241Z" fill={C.yellow} stroke={C.ink} strokeWidth={4}/>}
  <path d="M-17 -315V-278Q2 -261 20 -280V-315" fill={skin} stroke={C.ink} strokeWidth={6}/>
  <g transform={`translate(0 -301) rotate(${head})`} stroke={C.ink} strokeWidth={8}>
   {side?<>
    <path d="M-67 -150L-41 -199L21 -211L67 -174L77 -113L106 -74L75 -61L73 -20L32 12L-40 -14L-65 -70Z" fill={skin}/>
    <path d="M-65 -80L-81 -159L-49 -204L10 -222L64 -193L83 -146L42 -167L15 -182L-35 -155L-39 -76Z" fill={anonymous?s:a.role==='judge'?'#e4d9d3':'#42334d'}/>
    {anonymous?<><path d="M31 -124L77 -115L104 -74L75 -61L73 -20L32 12L-11 -5L-14 -93Z" fill="#272633"/><path d="M37 -108L65 -103" stroke="#a29aaa" strokeWidth={4}/></>:eyes}
   </>:back?<>
    <path d="M-89 -133L-66 -195Q0 -225 68 -196L96 -130L84 -35Q0 22 -81 -31Z" fill={skin}/>
    <path d="M-91 -114L-95 -177Q-39 -230 43 -204L91 -161L92 -64L63 -38L-8 -25L-74 -61Z" fill={anonymous?s:a.role==='judge'?'#e4d9d3':'#42334d'}/>
   </>:<>
    <path d={front?'M-91 -131L-67 -198Q0 -225 67 -198L94 -131L84 -32Q0 22 -84 -32Z':'M-91 -131L-67 -198Q-8 -233 66 -195L100 -138L88 -35Q60 21 -13 15L-82 -29Z'} fill={skin}/>
    <path d="M-90 -120L-96 -178Q-45 -227 38 -204L87 -167L98 -123L61 -145L39 -169L-20 -157L-68 -143L-72 -99Z" fill={anonymous?s:a.role==='judge'?'#e4d9d3':a.role==='host'?'#59334d':'#42334d'}/>
    {anonymous?<><path d="M-68 -125Q0 -151 73 -115L75 -42L13 -12L-71 -37Z" fill="#272633" stroke="#55505f" strokeWidth={4}/><path d="M-44 -103L-14 -104M24 -104L49 -99" stroke="#a29aaa" strokeWidth={4}/></>:eyes}
   </>}
   {a.role==='police'&&<><path d="M-83 -171L-66 -209Q0 -229 69 -195L90 -159Z" fill={C.blue}/><path d="M-90 -163Q0 -180 93 -153L112 -134Q8 -126 -88 -148Z" fill="#2e3f78"/></>}
  </g>
  {limb(r,1)}
 </g>;
};

const Props:React.FC<{p:SceneProp;t:number}>=({p,t})=>{
 const u=phase(t,p.beat),[x,y]=point([p.x,p.y],p.to??[p.x,p.y],u);
 return <g transform={`translate(${x} ${y}) scale(${p.scale??1}) rotate(${(p.angle??0)+(p.turn??0)*u})`}>
  {p.kind==='car'?<><Car truck={p.truck} flip={p.flip} f={p.to?t*35:0}/>{p.occupants&&<><path d="M-60 -55V-87Q-37 -116 -17 -88V-55" fill="#272633" stroke={C.ink} strokeWidth={6}/><path d="M31 -55V-85Q53 -112 75 -86V-55" fill="#595865" stroke={C.ink} strokeWidth={6}/></>}</>:p.kind==='bag'?<Bag/>:p.kind==='monitor'?<g stroke={C.ink} strokeWidth={8}><path d="M-130 -132H130V43H-130Z" fill="#4d6571"/><path d="M-109 -112H109V20H-109Z" fill="#163a40"/>{[-68,-16,44,86].map((xx,i)=><g key={i}>{[0,1,2,3,4].map(j=><path key={j} d={`M${xx-9} ${-89+j*23+(i%2)*6}H${xx+10}`} stroke={i<2?C.teal:C.yellow} strokeWidth={5}/>)}</g>)}<path d="M-18 43V75M-72 77H72" fill="none"/></g>:p.kind==='microscope'?<g stroke={C.ink} strokeWidth={9}><path d="M-62 -127L-30 -161L18 -125L-10 -92Z" fill={C.paper}/><path d="M3 -102Q99 -31 16 41L-35 53" fill="none" stroke="#bdd9cc" strokeWidth={24}/><path d="M-80 67H81L103 91H-96ZM-91 5H28" fill="#a7bcb9"/><circle cy={-4} r={19} fill={C.teal}/></g>:p.kind==='tray'?<g stroke={C.ink} strokeWidth={6}><path d="M-110 -38H106L129 41H-128Z" fill="#b5b9bd"/><path d="M-92 -25H90L100 18H-99Z" fill="#e5e0ce"/></g>:p.kind==='box'?<g stroke={C.ink} strokeWidth={7}><path d="M-96 -50H93V78H-96Z" fill="#b99f76"/><path d="M-111 -80H110V-42H-111Z" fill="#d4bc8e"/><path d="M-27 -31H35V5H-27Z" fill={C.paper}/></g>:p.kind==='chair'?<g stroke={C.ink} strokeWidth={8}><path d="M-67 -177Q0 -216 68 -178V-23H-67Z" fill="#568d87"/><path d="M-79 -21H78L107 20H-103ZM-76 20V118M78 20V118" fill="#3a686a"/></g>:p.kind==='candle'?<g stroke={C.ink} strokeWidth={4}><path d="M-14 -39H14V50H-14Z" fill={C.paper}/><path d="M0 -42Q-20 -65 0 -90Q19 -65 0 -42Z" fill={C.yellow}/></g>:p.kind==='coat'?<path d="M-70 -181L-20 -211L0 -173L23 -210L72 -181L96 -53L60 -42L48 -137L53 83H-51L-46 -137L-64 -42L-99 -55Z" fill={C.teal} stroke={C.ink} strokeWidth={8}/>:<HandProp kind={p.kind} t={t}/>}
 </g>;
};

const Room:React.FC<{name:string;layout:string}>=({name,layout})=>{
 const side=layout==='side'||layout==='reverse',reverse=layout==='reverse';
 if(name==='garage'||name==='street'||name==='arcade'||name==='spa'){
  const garage=name==='garage',street=name==='street',arcade=name==='arcade';
  return <g stroke={C.ink} strokeLinejoin="round"><rect x={-300} y={-200} width={2520} height={1500} fill={garage?'#615374':street?'#52678c':arcade?'#42345f':'#c99f87'}/><path d={side?'M-300 600L1520 420L2220 780V1250H-300Z':'M-300 830L960 430L2220 830V1250H-300Z'} fill={garage?'#918092':street?'#36364f':arcade?'#30283f':'#9d736e'} strokeWidth={10}/>
  {garage?<>{[120,side?850:1650].map((x,i)=><g key={x}><path d={`M${x-65} -100H${x+65}V730L${x-65} 790Z`} fill={i?'#61546d':'#7f6b86'} strokeWidth={10}/><path d={`M${x-65} 505L${x+65} 460V550L${x-65} 595Z`} fill={C.yellow} strokeWidth={5}/></g>)}<path d={side?'M700 340L1550 280V650L700 740Z':'M500 190H1400V620H500Z'} fill="#342b46" strokeWidth={12}/><path d="M400 920L760 735M1370 742L1800 919" stroke={C.paper} strokeWidth={8}/><path d="M430 82H840M1120 82H1470" stroke={C.paper} strokeWidth={19}/></>:street?<>{[90,400,790,1320,1650].map((x,i)=><g key={x}><path d={`M${x} ${180+i%2*60}H${x+220}V650H${x}Z`} fill={i%2?'#393d65':'#435075'} strokeWidth={8}/>{[0,1,2].map(j=><path key={j} d={`M${x+45} ${270+j*94}H${x+80}M${x+136} ${270+j*94}H${x+171}`} stroke={C.yellow} strokeWidth={24}/>)}</g>)}<path d="M-100 920L2020 725" stroke={C.yellow} strokeWidth={11}/></>:arcade?<>{[160,520,1400,1770].map((x,i)=><g key={x} transform={`translate(${x} 0)`}><path d="M-130 260H130L150 780H-150Z" fill={i%2?'#ac6596':'#685e9a'} strokeWidth={10}/><path d="M-100 302H100V530H-100Z" fill="#1e3340" strokeWidth={8}/><path d="M-112 560H112L130 635H-130Z" fill="#d1a5aa" strokeWidth={7}/><circle cy={599} r={13} fill={C.red}/></g>)}</>:<>{Array.from({length:8},(_,i)=><path key={i} d={`M${i*260} 80V780M0 ${i*100+90}H1920`} stroke="#9e776f" strokeWidth={5}/>)}<path d="M130 730H1800L1900 820H70Z" fill="#b57961" strokeWidth={10}/></>}
 </g>;
 }
 if(name==='court')return <g stroke={C.ink} strokeWidth={10} strokeLinejoin="round"><rect x={-300} y={-200} width={2520} height={1500} fill="#e8ad83"/><path d="M-300 850L960 440L2220 850V1300H-300Z" fill="#cc7f6e"/>{layout==='wide'?<><path d="M320 140H1600V520H320Z" fill="#a45156"/>{[375,560,1360,1545].map(x=><path key={x} d={`M${x} 140V520`} stroke="#efb88e" strokeWidth={33}/>)}<circle cx={960} cy={248} r={73} fill="#efb88e"/><Glyph kind="scale" x={960} y={243} scale={.32} color="#71394d"/></>:side?<><path d={reverse?'M0 140H650V770H0Z':'M1370 140H1920V770H1370Z'} fill="#a45156"/><path d="M200 210L1710 150M200 250L1710 190" stroke="#a45156" strokeWidth={21}/><path d={reverse?'M950 330H1780V520H950Z':'M110 330H940V520H110Z'} fill="#f0d0ab"/><path d="M170 720H780M1130 710H1730" stroke="#71394d" strokeWidth={30}/></>:<><path d="M310 130H1610V740H310Z" fill="#a45156"/>{[385,590,1320,1540].map(x=><path key={x} d={`M${x} 130V740`} stroke="#efb88e" strokeWidth={45}/>)}<circle cx={960} cy={265} r={97} fill="#efb88e"/><Glyph kind="scale" x={960} y={260} scale={.43} color="#71394d"/></>}</g>;
 const lab=name==='lab',memorial=name==='memorial';
 return <g stroke={C.ink} strokeWidth={9} strokeLinejoin="round"><rect x={-300} y={-200} width={2520} height={1500} fill={lab?'#326966':memorial?'#b4d3ce':'#556078'}/><path d="M-300 850L1120 460L2220 850V1300H-300Z" fill={lab?'#235550':memorial?'#9ebdb7':'#34374f'}/>
  {memorial?<><path d="M120 150H780V650H120Z" fill="#e9edc9" stroke="#638b89" strokeWidth={15}/><path d="M450 150V650M120 400H780" stroke="#8aada4" strokeWidth={10}/><path d="M1070 720H1740L1840 820H1010Z" fill="#69988b"/></>:<>{[side?170:140,side?650:1510].map((x,i)=><g key={x}><path d={`M${x} 170H${x+280}V720H${x}Z`} fill={lab?'#184743':'#393b50'}/>{[0,1,2,3].map(j=><g key={j}><path d={`M${x} ${270+j*105}H${x+280}`} stroke={lab?'#397d77':'#796b7e'} strokeWidth={9}/>{!lab&&[0,1,2,3,4].map(k=><path key={k} d={`M${x+21+k*48} ${208+j*105}H${x+50+k*48}V${265+j*105}H${x+21+k*48}Z`} fill={k%2?C.purple:'#687f87'} strokeWidth={3}/>)}</g>)}</g>)}<g transform={reverse?"translate(360 0)":undefined}><path d="M570 175H1320V540H570Z" fill={lab?'#285451':'#8d99ac'}/><path d="M815 175V540M1070 175V540M570 360H1320" stroke={lab?'#397d77':'#4b556c'} strokeWidth={14}/><path d="M550 553H1340" strokeWidth={18}/></g><path d="M720 80H1200" stroke={C.paper} strokeWidth={23}/></>}
 </g>;
};

export const ActedStage:React.FC<{performance:Performance;f:number}>=({performance:p,f})=>{
 const local=f-p.clock,t=Math.min(1,Math.max(0,local/Math.max(1,p.duration-1))),seconds=local/30;
 const camera=p.camera?point(p.camera.from,p.camera.to,phase(t,[0,1])):[0,0];
 return <g data-performance={p.room}>
  <g transform={`translate(${-camera[0]} ${-camera[1]})`}>
   <Room name={p.room} layout={p.layout}/>
   {p.props.filter(x=>x.kind==='car'||x.kind==='chair'||x.kind==='coat').map((x,i)=><Props key={i} p={x} t={t}/>)}
   {p.actors.map(a=><Actor key={a.id} a={a} t={t} seconds={seconds} fire={p.fire?.actor===a.id&&local>=p.fire.start&&local<p.fire.end}/>)}
   {p.fireAttempt&&t>.3&&t<.72&&<path d="M1280 690Q1257 663 1279 638Q1275 658 1297 669Q1314 687 1280 690Z" fill={C.yellow} stroke={C.ink} strokeWidth={5}/>}
   {p.foreground==='bench'&&<path d={p.layout==='wide'?'M560 509H1360V631H560Z':'M300 711H1620V896H300Z'} fill="#71394d" stroke={C.ink} strokeWidth={12}/>}
   {p.foreground==='rail'&&<path d="M700 793H1810V837H700ZM740 837V1030M1180 837V1030M1740 837V1030" fill="#a45156" stroke={C.ink} strokeWidth={10}/>}
   {(p.foreground==='desk'||p.foreground==='lab')&&<path d={p.layout==='side'?'M580 704L1430 635L1770 744L760 840Z':'M320 702H1570L1720 807H200Z'} fill={p.foreground==='lab'?'#59a59b':'#8a6967'} stroke={C.ink} strokeWidth={11}/>}
   {p.props.filter(x=>!['car','chair','coat'].includes(x.kind)).map((x,i)=><Props key={i} p={x} t={t}/>)}
  </g>
  {(p.place||p.date)&&<g fontFamily="ToonPretendard" fontWeight={800} fontSize={30} fill={C.paper} stroke={C.ink} strokeWidth={6} paintOrder="stroke"><text x={54} y={68}>{p.place}</text><text x={1866} y={68} textAnchor="end" fill={C.yellow}>{p.date}</text></g>}
 </g>;
};
