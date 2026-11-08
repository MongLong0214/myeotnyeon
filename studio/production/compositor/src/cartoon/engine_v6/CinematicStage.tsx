import React from 'react';
import {C,CinematicShot,SpeechFrame,StagedProp,ease} from './types';
import {Puppet,Bag} from './Puppet';
import {Car,Glyph,Set,LegacyStage} from './Stage';

const lettering={fontFamily:'ToonPretendard',fontWeight:800} as const;
const SceneSet:React.FC<{name:string;f:number}>=({name,f})=>name==='spa'?<g><rect x={-600} y={-400} width={3120} height={1900} fill="#c99f87"/>{Array.from({length:12},(_,i)=><path key={i} d={`M${i*190-100} -100V1100M-400 ${i*105-100}H2320`} stroke="#9e776f" strokeWidth={5}/>)}<path d="M240 710H1660L1780 850H130Z" fill="#9d5f50" stroke={C.ink} strokeWidth={12}/><path d="M330 710V530H1530V710" fill="#b57961" stroke={C.ink} strokeWidth={10}/></g>:name==='investigation'?<g><rect x={-600} y={-400} width={3120} height={1900} fill="#556078"/><path d="M-400 820L960 540L2320 820V1400H-400Z" fill="#34374f"/><path d="M140 160H1780V710H140Z" fill="#8d8490" stroke={C.ink} strokeWidth={12}/><path d="M180 200H1740V670H180Z" fill="#52656a" stroke={C.ink} strokeWidth={7}/><path d="M120 795H1800L1950 910H0Z" fill="#8a6967" stroke={C.ink} strokeWidth={12}/><path d="M650 58H1270" stroke="#eee6cf" strokeWidth={25}/></g>:<Set name={name} f={f}/>;
const Label:React.FC<{x:number;y:number;text:string;size?:number;color?:string}>=({x,y,text,size=32,color=C.paper})=><text x={x} y={y} textAnchor="middle" {...lettering} fontSize={size} fill={color} stroke={C.ink} strokeWidth={5} paintOrder="stroke">{text}</text>;
const Plate:React.FC<{p:StagedProp;f:number}>=({p,f})=>{
 const m=p.motion,u=m?ease((f-m.start)/Math.max(1,m.end-m.start)):0;
 const x=p.x+((m?.xTo??p.x)-p.x)*u,y=p.y+((m?.yTo??p.y)-p.y)*u,s=p.scale??1;
 const glyph=['mask','cloth','cigarette','dna','gun','camera','scale','law','clock','door','paper','question'].includes(p.kind);
 const portraits=p.portraits??[];
 return <g transform={`translate(${x} ${y}) scale(${s})`}>
 {p.kind==='car'?<><Car truck={p.truck} flip={p.flip} f={m&&u>0&&u<1?f:0}/>{(p.occupants??[]).map((role,k)=><Puppet key={k} role={role} x={k?65:-65} y={-32} scale={.16} f={17} still view="profile" flip/>)}</>:p.kind==='aimedGun'?<><path d="M-164 50Q-110 20 -50 0" stroke={C.ink} strokeWidth={29} fill="none" strokeLinecap="round"/><path d="M-164 50Q-110 20 -50 0" stroke="#343345" strokeWidth={18} fill="none" strokeLinecap="round"/><Glyph kind="gun" scale={.37}/></>:p.kind==='bag'?<Bag/>:glyph?<Glyph kind={p.kind} f={p.kind==='clock'?0:f*.1}/>:p.kind==='emptyChair'?<><path d="M-80 -20V-180Q0 -220 80 -180V-20M-100 0H100L126 65H-125ZM-90 65V160M95 65V160" fill="#568d87" stroke={C.ink} strokeWidth={12}/><path d="M-63 -210H52V-249H-63Z" fill={C.paper} stroke={C.ink} strokeWidth={5}/></>:p.kind==='file'?<><path d="M-180 -160H-40L-10 -125H180V160H-180Z" fill="#cfb880" stroke={C.ink} strokeWidth={10}/><path d="M-145 -100H146V120H-145Z" fill={C.paper} stroke={C.ink} strokeWidth={6}/>{[0,1,2,3].map(k=><path key={k} d={`M-108 ${-50+k*34}H98`} stroke="#aa9fbd" strokeWidth={7}/>)}</>:p.kind==='records'?<>{Array.from({length:8},(_,k)=><g key={k} transform={`translate(${(k%4)*76-120} ${Math.floor(k/4)*105-55})`}><path d="M-40 -100H37V100H-40Z" fill={k%2?C.purple:C.teal} stroke={C.ink} strokeWidth={6}/><path d="M-22 -62H20V-4H-22Z" fill={C.paper}/></g>)}</>:p.kind==='people'?<>{Array.from({length:6},(_,k)=><g key={k} transform={`translate(${(k%3)*105-100} ${Math.floor(k/3)*150-80})`} fill={k%2?C.purple:C.teal} stroke={C.ink} strokeWidth={6}><circle cy={-30} r={29}/><path d="M-35 10Q0 -4 35 10L45 85H-45Z"/></g>)}</>:p.kind==='fireAttempt'?<><path d="M0 -153Q-33 -70 -82 -20Q-131 82 -15 141Q110 137 93 41Q35 23 34 -67Q16 -27 0 -153Z" fill={C.red} stroke={C.ink} strokeWidth={9}/><path d="M-145 -140L148 147M148 -140L-145 147" stroke={C.yellow} strokeWidth={13} strokeDasharray="24 16"/></>:p.kind==='family'?<>{[-80,0,80].map((xx,k)=><g key={k} transform={`translate(${xx} ${k?25:0}) scale(${k?.65:.9})`} fill="#668b89" stroke={C.ink} strokeWidth={7}><circle cy={-72} r={39}/><path d="M-49 -13Q0 -43 49 -13L68 116H-68Z"/></g>)}</>:<><path d="M-238 -156Q-250 -162 -247 -140L-235 150Q-232 165 -214 160L235 150L246 -148Z" fill={p.tone??'#394759'} stroke={C.ink} strokeWidth={10}/><path d="M-218 -128H215" stroke={C.paper} strokeOpacity={.25} strokeWidth={4}/></>}
 {p.kind==='board'&&portraits.map((role,i)=><Puppet key={role} role={role} x={portraits.length===1?0:i?75:-75} y={-78} scale={.16} f={17} still anonymous take={0}/>)}
 {p.text&&<Label x={0} y={p.subtext?-8:12} text={p.text} size={Math.min(52,410/Math.max(1,Array.from(p.text).reduce((n,c)=>n+(/[가-힣]/.test(c)?1:c===' '?.35:.62),0)))}/>}
 {p.subtext&&<Label x={0} y={62} text={p.subtext} size={30} color={C.yellow}/>}
 {p.crossed&&<path d="M-174 -143L170 128M170 -143L-174 128" stroke={C.red} strokeWidth={18}/>}
 {p.fireAt!==undefined&&f>=p.fireAt&&f<p.fireAt+3&&<path transform={p.kind==='aimedGun'?'translate(20 0) scale(.37)':undefined} d="M130 -25L181 -88L197 -31L267 -16L209 17L230 66L177 35L146 68L153 14Z" fill={C.yellow} stroke={C.ink} strokeWidth={5}/>}
 {p.label&&<Label x={0} y={p.kind==='car'?143:225} text={p.label} size={32}/>}
 </g>;
};

/** Explicit tableaux use one absolute scene clock, fixed axis and hard-cut cameras. */
export const Stage:React.FC<{shot:CinematicShot;f:number;speech?:SpeechFrame}>=({shot,f,speech})=>{
 const s=shot.staging;if(!s)return <LegacyStage shot={shot} f={f} speech={speech}/>;
 const camera=s.focus??{x:960,y:480,zoom:1};
 return <g data-scene={s.sceneId} data-angle={s.angleDeg??0}>
 <g transform={`translate(960 485) scale(${camera.zoom}) translate(${-camera.x} ${-camera.y})`}>
 <SceneSet name={shot.set} f={shot.serious?0:f*.3}/>
 {(s.links??[]).map((l,i)=><g key={i}><path d={`M${l.from[0]} ${l.from[1]}L${l.to[0]} ${l.to[1]}`} stroke={l.crossed?C.red:C.yellow} strokeWidth={12} fill="none" strokeDasharray={l.crossed?'17 14':undefined}/><path d={`M${l.to[0]-25} ${l.to[1]-20}L${l.to[0]} ${l.to[1]}L${l.to[0]-25} ${l.to[1]+20}`} stroke={l.crossed?C.red:C.yellow} strokeWidth={9} fill="none"/>{l.label&&<Label x={(l.from[0]+l.to[0])/2} y={(l.from[1]+l.to[1])/2-28} text={l.label} size={25}/>}</g>)}
 {(s.props??[]).filter(p=>p.kind==='car').map(p=><Plate key={p.id} p={p} f={f}/>)}
 {(s.actors??[]).map(a=>{const m=a.motion,u=m?ease((f-m.start)/Math.max(1,m.end-m.start)):0,xx=a.x+((m?.xTo??a.x)-a.x)*u,yy=a.y+((m?.yTo??a.y)-a.y)*u;
 return <g key={a.id}><Puppet {...a} x={xx} y={yy} f={a.still?17:f-s.clockStart+60} fall={(a.fall??0)+((m?.fallTo??a.fall??0)-(a.fall??0))*u} still={a.still} take={0} mouth={a.role==='host'?speech?.amplitude:0} viseme={a.role==='host'?speech?.viseme:'rest'} walk={!!m&&u>0&&u<1&&a.walk} anonymous={a.anonymous||a.role==='victim'} />{a.label&&<Label x={xx} y={yy+50} text={a.label} size={32}/>}</g>;})}
 {(s.props??[]).filter(p=>p.kind!=='car').map(p=><Plate key={p.id} p={p} f={f}/>)}
 </g>
 <path d="M0 0H1920V118H0Z" fill={C.ink} opacity={.92}/>
 {s.location&&<text x={50} y={45} {...lettering} fontSize={25} fill={C.teal}>{s.location}</text>}
 {s.heading&&<text x={50} y={91} {...lettering} fontSize={37} fill={C.paper}>{s.heading}</text>}
 {s.date&&<text x={1860} y={78} textAnchor="end" {...lettering} fontSize={40} fill={C.yellow}>{s.date}</text>}
 {s.note&&<g><path d="M50 812H1870V875H50Z" fill={C.ink} opacity={.92}/><Label x={960} y={855} text={s.note} size={29} color={C.yellow}/></g>}
 {shot.illustrative&&<text x={1860} y={162} textAnchor="end" {...lettering} fontSize={25} fill={C.yellow} stroke={C.ink} strokeWidth={5} paintOrder="stroke">비사실적 비유</text>}
 </g>;
};
