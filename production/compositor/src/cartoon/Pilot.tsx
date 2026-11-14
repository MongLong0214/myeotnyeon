import React from 'react';
import {AbsoluteFill,Audio,staticFile,useCurrentFrame} from 'remotion';
import {C,Puppet,Bag} from './Puppets';
import {Parking,Car,Court,Bench,Clock,Investigation,Desk} from './Sets';
import {Subtitles} from './Subtitles';
import data from './pilot_data.json';
export const fontCss=()=>`@font-face{font-family:'Cartoon Pretendard';src:url('${staticFile('Pretendard-Bold.woff2')}') format('woff2');font-weight:700;font-display:block;}`;
export const Pilot:React.FC=()=>{
 const f=useCurrentFrame();const i=data.shots.findIndex(s=>f>=s.start&&f<s.end);const shot=data.shots[Math.max(0,i)];const p=(f-shot.start)/(shot.end-shot.start);const lf=f-shot.start;const e=data.envelope[Math.min(f,1349)]??0;
 const host=(x=350,y=906,s=.99,gesture:'rest'|'point'|'shrug'='rest',expr:'neutral'|'skeptic'|'alarm'|'resolve'='neutral')=><Puppet role="host" x={x} y={y} scale={s} f={f} mouth={e} seed={1} gesture={gesture} expr={expr}/>;
 const staff=(x:number,scale=.85,bag=false,seed=2)=><Puppet role="employee" x={x} y={904} scale={scale} f={f} seed={seed} bag={bag} gesture={bag?'hold':'rest'} view="three-quarter"/>;
 const robber=(role:'robberA'|'robberB',x:number,s=1,bag=false,view:'front'|'three-quarter'|'profile'|'back'='three-quarter',walk=false)=><Puppet role={role} x={x} y={909} scale={s} f={f} seed={role==='robberA'?3:4} view={view} walk={walk} bag={bag} gesture={bag?'hold':'rest'}/>;
 const judge=(s=.93)=><Puppet role="judge" x={960} y={887} scale={s} f={f} expr="resolve" seed={7}/>;
 let scene:React.ReactNode;
 switch(shot.view){
 case 'block':scene=<><Parking f={f}/><Car x={1500} y={805} scale={.95} van f={f}/><Car x={1110-p*170} y={859} scale={.87} f={lf}/>{host(340,904,.96,'point','skeptic')}</>;break;
 case 'approach':scene=<><Parking f={f}/><Car x={450} y={830} scale={.88} f={0}/><Car x={1530} y={775} scale={.94} van f={0}/>{robber('robberA',840+p*45,.93,false,'three-quarter',true)}{robber('robberB',1190+p*45,.84,false,'three-quarter',true)}</>;break;
 case 'staff':scene=<><Parking f={f}/><Car x={1420} y={807} scale={1.07} van f={0}/>{staff(650,.98,true)}{robber('robberA',1120,.84)}<Bag x={422} y={894} scale={.7}/></>;break;
 case 'offscreen':scene=<><Parking f={f}/><Car x={725} y={825} scale={1.15} van f={0}/>{host(1500,902,.84,'rest','resolve')}<path d="M96 356L96 610L258 610L258 356" fill="#C1CABB" stroke={C.line} strokeWidth={8}/></>;break;
 case 'court-wide':scene=<><Court f={f}/>{judge()}{robber('robberA',278,.76,false,'back')}{robber('robberB',1620,.72,false,'back')}<Bench/></>;break;
 case 'court-reverse':scene=<><Court f={f}/>{judge(.67)}<Bench/>{robber('robberA',568,.97,false,'back')}{robber('robberB',1390,.88,false,'back')}</>;break;
 case 'question':scene=<><Court f={f}/>{judge(.93)}<Bench/>{host(307,906,.97,'shrug','skeptic')}</>;break;
 case 'date':scene=<><Parking f={f}/><Clock x={1510} y={381}/><Car x={1330} y={834} scale={.92} van f={0}/>{host(505,909,1.02,'point')}</>;break;
 case 'unload':scene=<><Parking f={f}/><Car x={1510} y={795} scale={.99} van f={0}/>{staff(550,.75,true,2)}{staff(941,.88,true,5)}{staff(1300,.73,false,9)}</>;break;
 case 'three-staff':scene=<><Parking f={f}/><Car x={1450} y={760} scale={1.02} van f={0}/>{staff(411,.84,true,2)}{staff(860,.96,true,5)}{staff(1330,.79,false,9)}</>;break;
 case 'two-bags':scene=<><Parking f={f}/><ellipse cx={1050} cy={855} rx={183} ry={18} fill={C.ink} opacity={.17}/><ellipse cx={1470} cy={855} rx={183} ry={18} fill={C.ink} opacity={.17}/><Bag x={1050} y={806} scale={1.6} angle={-3}/><Bag x={1470} y={806} scale={1.6} angle={3}/>{host(355,906,1.01,'point')}</>;break;
 case 'take-bag':scene=<><Parking f={f}/><Car x={1465} y={814} scale={.9} f={0}/>{robber('robberA',540+p*30,.92)}{robber('robberB',1060+p*30,.94,true,'three-quarter',true)}<Bag x={280} y={894} scale={.72}/></>;break;
 case 'escape':scene=<><Parking f={f}/><Car x={1480} y={802} scale={.96} f={0}/>{robber('robberA',785+p*74,.94,false,'profile',true)}{robber('robberB',1170+p*74,.89,true,'profile',true)}</>;break;
 case 'amount':scene=<><Parking f={f}/><Car x={1430} y={817} scale={.97} van f={0}/>{host(510,908,1.02,'rest','resolve')}<Bag x={1110} y={890} scale={.86}/></>;break;
 case 'absence':scene=<><Parking f={f}/><Car x={1390} y={834} scale={1.04} van f={0}/><path d="M650 722L650 870L880 870L880 722" fill="none" stroke={C.line} strokeWidth={10}/><path d="M632 743L898 743L898 772L632 772Z" fill="#A4B4A7" stroke={C.line} strokeWidth={7}/><circle cx={660} cy={890} r={18} fill="#45524A"/><circle cx={870} cy={890} r={18} fill="#45524A"/></>;break;
 case 'no-camera':scene=<><Parking f={f}/>{host(630,908,1.03,'point','skeptic')}<Car x={1440} y={822} scale={.95} van f={0}/></>;break;
 case 'abandon':scene=<><Parking f={f} alternate/><Car x={490} y={829} scale={.91} f={0}/>{robber('robberA',1000+p*50,.88,false,'profile',true)}{robber('robberB',1400+p*50,.82,true,'profile',true)}</>;break;
 case 'switch':scene=<><Parking f={f} alternate/><Car x={450} y={789} scale={.73} f={0}/><Car x={1465} y={827} scale={.94} white f={lf}/>{robber('robberA',840+p*42,.9,false,'profile',true)}{robber('robberB',1165+p*42,.83,true,'profile',true)}</>;break;
 case 'provenance':scene=<><Investigation f={f}/>{host(486,908,1.01,'point','resolve')}<Desk f={f}/><path d="M1120 707L1120 628L1320 628L1320 707Z" fill="#7A856F" stroke={C.line} strokeWidth={7}/><path d="M1107 629L1334 629L1334 650L1107 650Z" fill="#A8AF96" stroke={C.line} strokeWidth={7}/></>;break;
 default:scene=<><Investigation f={f}/><Puppet role="detective" x={1100} y={908} scale={.91} f={f} expr="resolve" seed={8} gesture="point"/>{host(459,909,.94,'rest','resolve')}<Desk f={f}/></>;
 }
 // Every frame has a continuous linear camera move, plus independent puppet/prop motion.
 const zoom=1+p*.027;const pan=(i%2===0?1:-1)*p*24;const cy=-p*6;
 return <AbsoluteFill style={{background:C.paper}}><Audio src={staticFile('narration_45s.wav')}/><svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{position:'absolute',inset:0}}><style>{fontCss()}</style><g transform={`translate(${960+pan} ${480+cy}) scale(${zoom}) translate(-960 -480)`}>{scene}</g><Subtitles f={f}/></svg></AbsoluteFill>;
};
