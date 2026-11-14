import React from 'react';
import {CourtFix1,ChoiceGavel} from './CourtFix1';
import {AbsoluteFill,Freeze,useCurrentFrame} from 'remotion';
import {ArticulatedGuy,Look,RigPose,Expr} from './FightRig';
import {standing,k,smooth} from './FightScene';
import {Actor,CourtBackground,Stamp,INK,PAPER,GOLD,RED,TEAL,type} from './CourtDynamic';
import {Case,Line} from './Scenes';
const S={stroke:INK,strokeWidth:9,strokeLinecap:'round' as const,strokeLinejoin:'round' as const};
const Body:React.FC<{look:Look;x:number;y?:number;scale?:number;t:number;expr?:Expr;gesture?:string;rig?:RigPose;talk?:boolean}>=({look,x,y=1215,scale=1,t,expr='concern',gesture,rig,talk=false})=>{
 const r=rig??standing(),p=smooth(t/18);
 if(!rig){r.head=Math.sin(t*.085);r.hands=[[-75,-222],[78,-227]];r.elbows=[[-95,-283],[100,-286]];
 if(gesture==='offer'){r.hands[1]=[108+60*p,-270];r.elbows[1]=[90,-310];r.head=-6+3*p;}
 if(gesture==='explain'){r.hands[0]=[-80-40*p,-255-35*p];r.hands[1]=[78+35*p,-227];r.head=-5+8*p;}
 if(gesture==='collar'){r.hands[1]=[22,-300];r.head=4+6*p;r.elbows[1]=[95,-270];}
 if(gesture==='protect'){r.hands=[[-30,-240],[32,-247]];r.elbows=[[-102,-260],[103,-267]];r.head=-7;r.torso=5;}
 if(gesture==='flinch'){const b=k(t,[[0,0],[8,1],[22,1],[42,.1],[68,.15]]);r.hip=[0,-170+22*b];r.hands=[[-90-20*b,-250-55*b],[90+20*b,-253-55*b]];r.head=-8*b;r.squash=.36*b;}
 if(gesture==='relief'){r.hands[1]=[40,-280-45*p];r.elbows[1]=[110,-280];r.head=4-5*p;r.torso=-2*p;}
 }
 if(!rig)r.handProps=[{pose:gesture==='protect'||gesture==='flinch'?'open':'relaxed'},{pose:gesture==='offer'?'open':gesture==='collar'?'pinch':'relaxed'}];
 return <ArticulatedGuy look={look} x={x} y={y} scale={scale} rig={r} expr={expr} talk={talk} eye={x<540?[8,0]:[-8,0]} label="별도 원작 성인 캐릭터"/>;
};
const Snack:React.FC<{x:number;y:number;scale?:number;custard?:boolean}>=({x,y,scale=1,custard=false})=><g transform={`translate(${x} ${y}) scale(${scale})`} {...S}>{custard?<><path d="M-75 10Q-94 -75 -35 -101Q30 -129 81 -56L80 10Q0 48 -75 10Z" fill="#D8AB62"/><path d="M-73 -3Q0 -29 79 -2" fill="none" stroke="#EAD1A0" strokeWidth={12}/></>:<><ellipse cy={4} rx={87} ry={46} fill="#573A2F"/><path d="M-84 -28Q0 -77 84 -28V-2Q0 38 -84 -2Z" fill="#ECE1C7"/><ellipse cy={-31} rx={85} ry={43} fill="#664637"/><path d="M-57 -45Q-11 -66 34 -45" stroke="#94705A" fill="none" strokeWidth={6}/></>}</g>;
const Office:React.FC=()=> <AbsoluteFill style={{background:'#C9D1C7'}}><svg width={1080} height={1920} {...S}>
 <path d="M0 0H1080V1080H0Z" fill="#CFD7CE"/><path d="M0 1080H1080V1920H0Z" fill="#9B9B8E"/><path d="M0 1120H1080M0 1500H1080" stroke="#B4B4A6" strokeWidth={4}/>
 <path d="M670 220H1020V1100H670Z" fill="#54686B"/><path d="M703 263H987V1040H703Z" fill="#7D9190"/><path d="M847 263V1040" stroke="#B7C3B8" strokeWidth={6}/>
 <path d="M25 920H600V1015H25Z" fill="#A6835D"/><path d="M78 1015V1280M535 1015V1280" strokeWidth={25}/>
 <path d="M95 680H330V910H95Z" fill="#4B5B64"/><path d="M190 910V948M130 948H260" strokeWidth={13}/>
 </svg></AbsoluteFill>;
const Fridge:React.FC<{t:number;amount?:boolean}>=({t,amount=false})=><svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
 <g transform="translate(55 470)"><rect width={340} height={670} rx={22} fill="#DDE1D1"/><path d="M24 34H315V623H24Z" fill="#B7C6BD"/><path d="M24 260H315M24 450H315" stroke="#E8E4D5" strokeWidth={16}/><path d="M-28 0L-176 60V645L-28 670Z" fill="#F2EBDD"/><path d="M-45 200L-140 235V330L-45 310Z" fill="#C5CCC0"/><Snack x={105} y={235} scale={.65}/>{!amount&&<Snack x={245} y={425} custard scale={.65}/>}</g>
 {amount&&<g><Snack x={350} y={1020} scale={1.0}/><Snack x={300+320*smooth(t/60)} y={895+125*smooth(t/60)} custard scale={.65+.35*smooth(t/60)}/><text x={350} y={1130} textAnchor="middle" fontFamily="Do Hyeon" fontSize={68} fill={GOLD} strokeWidth={8} paintOrder="stroke">450원</text><text x={300+320*smooth(t/60)} y={1005+125*smooth(t/60)} textAnchor="middle" fontFamily="Do Hyeon" fontSize={68} fill={GOLD} strokeWidth={8} paintOrder="stroke">600원</text></g>}
 </svg>;
export const SnackScene:React.FC<{u:Line;t:number}>=({u,t})=>{
 const mode=u.mode,r=standing(),reach=k(t,[[0,1],[10,1],[35,0],[65,0]]);
 const eat=smooth((t-35)/25);r.hands=[[-135-80*reach+110*eat,-270-30*reach-140*eat],[82,-215]];r.elbows=[[-90,-300],[100,-280]];r.torso=-8*reach;r.head=-7+4*eat;
 if(mode==='snack')r.handProps=[{pose:'grip',objectSpace:'scene',object:<Snack x={r.hands[0][0]} y={r.hands[0][1]-12/1.12} scale={.52/1.12}/>},{pose:'relaxed'}];
 const zoom=mode==='snack'?1+.065*smooth((t+1)/3):1;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${zoom})`,transformOrigin:'50% 48%'}}><Office/>
 <Fridge t={t} amount={mode==='amount'}/>
 <Body look="snack" x={mode==='amount'?850:690} y={1235} scale={mode==='amount'?.79:1.12} t={t} rig={mode==='snack'?r:undefined} expr="concern" gesture="explain"/>

 </AbsoluteFill></AbsoluteFill>;
};
const Yard:React.FC=()=> <AbsoluteFill style={{background:'#AEBAB4'}}><svg width={1080} height={1920} {...S}><path d="M0 0H1080V1060H0Z" fill="#BDC9BE"/><path d="M0 1060H1080V1920H0Z" fill="#928D7F"/><path d="M65 290H1000V1055H65Z" fill="#8B9992"/><path d="M10 290L535 90L1065 290Z" fill="#79827D"/>{[70,260,450,640,830].map(x=><path key={x} d={`M${x} 320V1050`} stroke="#A6B1A4" strokeWidth={13}/>)}<path d="M0 1270H1080M0 1570H1080" stroke="#AAA392" strokeWidth={5}/><path d="M70 580H170V930H70Z" fill="#57645B"/><path d="M85 605H155V900H85Z" fill="#A5B4A7"/></svg></AbsoluteFill>;
const Bricks:React.FC<{y:number}>=({y})=><svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform={`translate(365 ${y})`}><path d="M-240 0H225V40H-240Z" fill="#B39467"/>{[-200,-55,90].map(x=><path key={x} d={`M${x} 40V86h40V40Z`} fill="#796342"/>)}{[0,1,2,3,4].map(row=><g key={row}>{[0,1,2].map(col=><rect key={col} x={-205+col*135-(row%2?15:0)} y={-105-row*85} width={132} height={82} rx={4} fill={row%2?'#B77B57':'#A96F4F'} strokeWidth={6}/>)}</g>)}</g></svg>;
export const ForkliftScene:React.FC<{u:Line;t:number;courtPlayback?:boolean}>=({u,t,courtPlayback=false})=>{
 const f=useCurrentFrame();
 const mode=u.mode,lift=mode==='lift'?55+150*smooth(t/55):205,travel=mode==='move'?110*smooth(t/65):0,bedY=1335-lift;
 const v=standing();v.handProps=[{pose:'fist'},{pose:'fist'}];v.hands=[[-45,-235],[45,-235]];v.elbows=[[-85,-260],[85,-260]];v.feet=[[-32,0],[32,0]];v.head=-4;
 const driver=standing();driver.handProps=[{pose:'grip'},{pose:'grip'}];driver.hands=[[-100,-267],[-35,-267]];driver.elbows=[[-85,-300],[40,-285]];driver.feet=[[-38,-5],[36,-5]];driver.head=-6+4*smooth(t/25);
 if(courtPlayback){
  const breath=(phase:number)=>Math.sin(2*Math.PI*f/120+phase);
  v.hip[1]+=1.5*breath(.3);v.head+=.24*breath(1.9);v.hands[0][1]+=1.2*breath(3.2);v.hands[1][1]+=1.2*breath(4.8);
  driver.hip[1]+=1.5*breath(1.1);driver.head+=.24*breath(2.7);driver.hands[0][1]+=1.2*breath(.7);driver.hands[1][1]+=1.2*breath(2.3);
 }
 const zoom=mode==='lift'?1+.065*smooth((t+1)/3):1;
 const work=standing(),place=k(t,[[0,0],[18,1],[38,1],[62,0]]);work.torso=5+10*place;work.head=-3+3*place;work.hands=[[-30+35*place,-240+45*place],[32+165*place,-247+85*place]];work.elbows=[[-102,-260],[103+20*place,-267+25*place]];
 if(mode==='reason')return <AbsoluteFill><Yard/><Body look="migrant" x={320} y={1260} scale={1.04} t={t} rig={work} expr="concern"/><Body look="D" x={800} y={1250} scale={.99} t={t} gesture="explain" expr="serious"/><svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d="M40 1310H600V1410H40Z" fill="#AC7F59"/><rect x={480} y={1075} width={170} height={115} rx={6} fill="#B77B57"/><path d="M480 1130H650" strokeWidth={6}/></svg></AbsoluteFill>;
 return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transform:`scale(${zoom})`,transformOrigin:'50% 50%'}}><Yard/><AbsoluteFill style={{transform:`translateX(${-travel}px)`}}>
 <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g><path d="M710 1050H1045V1315H720Z" fill="#D8AA44"/><path d="M945 920H1050V1080H945Z" fill="#C59737"/><path d="M710 675V1190M1010 675V1060M680 675H1040" fill="none" strokeWidth={20}/><path d="M698 1310V610H646V1310" fill="#4F5855"/><path d={`M665 ${bedY+40}H90V${bedY+65}H665Z`} fill="#68716D"/><path d="M785 1085H925V1115H785Z" fill="#34423E"/><circle cx={760} cy={1320} r={96} fill="#343C39"/><circle cx={1010} cy={1320} r={80} fill="#343C39"/><circle cx={760} cy={1320} r={42} fill="#93998C"/><circle cx={1010} cy={1320} r={35} fill="#93998C"/></g></svg>
 <Body look="D" x={860} y={1110} scale={.61} t={t} rig={driver} expr="serious"/>
 <Bricks y={bedY}/><Body look="migrant" x={373} y={bedY-10} scale={.96} t={t} rig={v} expr="concern"/>
 <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform={`translate(365 ${bedY})`}><path d="M-225 -338Q0 -365 220 -338V-140Q0 -110 -225 -140Z" fill="#E8EFE7" fillOpacity={.32} stroke="#D7E2D7" strokeWidth={8}/>{[-318,-260,-200,-142].map(y=><path key={y} d={`M-225 ${y}Q0 ${y-24} 220 ${y}`} stroke="#F6F5E8" strokeWidth={7} fill="none" opacity={.9}/>)}</g></svg>
 </AbsoluteFill></AbsoluteFill></AbsoluteFill>;
};
const Balance:React.FC<{c:Case;f:number}>=({c,f})=>{
 const factors=c.utterances.filter(u=>c.qid==='q004'?['evidence','factor'].includes(u.mode):['harm','recovery'].includes(u.mode));const i=factors.filter(u=>u.from_frame<=f).length-1,at=i>=0?factors[i].from_frame:-1000,d=f-at;
 const target=c.qid==='q004'?i<0?0:9+7*i:i<0?0:i===0?-15:8;const prev=i<1?0:c.qid==='q004'?9:-15;
 const angle=prev+(target-prev)*(1-Math.exp(-Math.max(0,d)/8)*Math.cos(d*.4));
 return <svg width={1080} height={1920} style={{position:'absolute'}}><g transform="translate(535 1010) scale(.38)" {...S}><path d="M0 -185V245M-140 245H140L112 219H-112Z" fill="#DFB958"/><g transform={`rotate(${angle})`}><path d="M-275 -145H275" stroke="#A88A42" strokeWidth={22}/>{[-1,1].map(side=><g key={side} transform={`translate(${side*255} -145)`}><path d="M0 0L-92 178M0 0L92 178" fill="none" strokeWidth={6}/><path d="M-110 178Q0 300 110 178Z" fill={side<0?RED:TEAL}/>{i>=0&&side===(c.qid==='q004'?1:i===0?-1:1)&&<rect x={-30} y={123-Math.max(0,10-d)*18} width={60} height={60} rx={4} fill={GOLD} strokeWidth={5}/>}</g>)}</g><circle cy={-145} r={24} fill={GOLD}/></g></svg>;
};
export const RemakeCourt:React.FC<{c:Case;u:Line;t:number}>=({c,u,t:elapsed})=>{
 const f=useCurrentFrame(),mode=u.mode,answer=mode==='answer',choice=mode==='choices';const t=answer&&elapsed>=7&&elapsed<22?7:elapsed;
 if(!choice&&!answer)return <CourtFix1 c={c} u={u} t={elapsed} playback={c.qid==='q005'?<ForkliftScene u={{...u,mode:'lift'}} t={20+elapsed*.5} courtPlayback/>:undefined}/>;
 const snack=c.qid==='q004',look:Look=snack?'snack':'D',wide=choice,judgeX=wide?300:235,defX=wide?760:815;
 const zoom=answer?1+.08*smooth((t+1)/3):1,judgeY=wide?630:1200,defY=wide?650:1260;
 const content=<AbsoluteFill style={{transform:answer&&!snack?'translateY(220px)':'none'}}>
 {!answer&&!(choice&&f>=c.answer_frame-27)&&<Actor who="judge" x={judgeX} y={judgeY} scale={wide?.70:1.1} expr={!snack&&['harm','factor'].includes(mode)&&t<35?'angry':'serious'} gesture={t<36?'point':'read'} t={t<36?t:t-36}/>}
 {choice&&f>=c.answer_frame-27&&<ChoiceGavel c={c}/>}
 <Body look={look} x={defX} y={defY} scale={wide?.70:1.08} t={answer&&t>=22?t-22:t>=32&&!answer?t-32:t} expr={answer?(snack?'concern':'shock'):t>32?'concern':'serious'} gesture={answer?(snack?'relief':t<22?'collar':'flinch'):t>=32?'flinch':'collar'}/>
 {!wide&&!answer&&<Balance c={c} f={f}/>}
 {answer&&<><Freeze frame={669+Math.min(20,t)}><Actor who="judge" x={judgeX} y={1230} scale={1.15} expr="serious" gavel/></Freeze><svg width={1080} height={1920} style={{position:'absolute',zIndex:2}} {...S}><path d="M20 930H570V1160H20Z" fill="#80573F"/><path d="M20 930H570V970H20Z" fill="#CFAB76"/><ellipse cx={385} cy={950} rx={85} ry={17} fill="#5D3A30" strokeWidth={7}/></svg></>}
 </AbsoluteFill>;
 return <AbsoluteFill><CourtBackground dark={wide||f>=c.answer_frame}/><AbsoluteFill style={{transform:`scale(${zoom})`,transformOrigin:'50% 55%'}}>{answer&&t>=7&&t<22?<Freeze frame={c.answer_frame+7}>{content}</Freeze>:content}</AbsoluteFill>{answer&&t<4&&<AbsoluteFill style={{background:'#FFF5CC',opacity:.65*(1-t/4)}}/>}</AbsoluteFill>;
};
