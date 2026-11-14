// LF2 directed v3: reuse the existing v6 SVG engine verbatim. No replacement character art.
import React from 'react';
import {Composition, registerRoot, useCurrentFrame} from 'remotion';
import {ActedStage, Performance} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/cartoon/engine_v6/ActedStage';
import {Bag} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/cartoon/engine_v6/Puppet';
import {C} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/cartoon/engine_v6/types';
const FPS=30;
const scene=(p:Performance)=> <ActedStage performance={p} f={useCurrentFrame()}/>;

// Event source 13.590–41.740. Clocks are cue starts × 30, never evenly apportioned.
const event:Performance[]=[
 {room:'garage',layout:'wide',clock:0,duration:220,place:'사건 재구성',date:'2001-12-21',actors:[
  {id:'carrier1',role:'employee',x:1510,y:900,scale:.82,view:'three-quarter',to:[1110,875],move:[.04,.92],left:[-78,-148],leftTo:[-92,-156],leftItem:'bag'},
  {id:'carrier2',role:'employee',x:1690,y:910,scale:.76,view:'three-quarter',to:[1280,886],move:[.08,.92],left:[-76,-146],leftTo:[-89,-154],leftItem:'bag'},
  {id:'staff3',role:'employee',x:1810,y:920,scale:.70,view:'three-quarter',to:[1420,898],move:[.12,.92],right:[78,-170],rightTo:[96,-190]}
 ],props:[{kind:'car',x:1470,y:640,scale:.76,truck:true}],camera:{from:[0,0],to:[10,0]}},
 {room:'garage',layout:'wide',clock:220,duration:99,place:'사건 재구성',date:'차량이 동선을 막음',actors:[
  {id:'carrier1',role:'employee',x:1110,y:875,scale:.82,view:'three-quarter',left:[-92,-156],leftItem:'bag'},
  {id:'carrier2',role:'employee',x:1280,y:886,scale:.76,view:'three-quarter',left:[-89,-154],leftItem:'bag'},
  {id:'staff3',role:'employee',x:1420,y:898,scale:.70,view:'three-quarter',right:[78,-170],rightTo:[118,-205]}
 ],props:[{kind:'car',x:260,y:700,scale:1.04,to:[980,770],beat:[.02,.78],occupants:true},{kind:'car',x:1470,y:640,scale:.76,truck:true}],camera:{from:[0,0],to:[0,8]}},

 {room:'garage',layout:'side',clock:319,duration:394,place:'사건 재구성',date:'권총 등장',actors:[
  {id:'ra',role:'robberA',x:520,y:900,scale:1.20,view:'profile',right:[104,-250],rightTo:[175,-275],item:'gun'},
  {id:'victim',role:'employee',x:1260,y:890,scale:1.02,view:'three-quarter',right:[78,-185],rightTo:[126,-238],fall:[0,1],beat:[.46,.70]},
  {id:'carrier2',role:'employee',x:1515,y:900,scale:.76,view:'three-quarter',left:[-89,-154],leftTo:[-122,-212],leftItem:'bag'},
  {id:'staff3',role:'employee',x:1665,y:908,scale:.68,view:'three-quarter',left:[-70,-154],leftTo:[-120,-224]}
 ],props:[{kind:'car',x:1510,y:610,scale:.70,truck:true},{kind:'bag',x:1110,y:812,scale:.75}],camera:{from:[0,0],to:[-25,0]}},
 // 22.255s: two bags shown; 23.770s: the hand reaches one bag; 25.910s: exit begins.
 {room:'garage',layout:'wide',clock:713,duration:57,place:'가방 2개',date:'각각 3억 원',actors:[
  {id:'rb',role:'robberB',x:650,y:895,scale:1.04,view:'three-quarter',to:[535,888],move:[.16,.88],left:[-82,-150],leftTo:[-134,-115]},
  {id:'ra',role:'robberA',x:830,y:895,scale:.92,view:'three-quarter',to:[700,885],move:[.12,.76],right:[88,-192],rightTo:[122,-224]},
  {id:'victim',role:'employee',x:1320,y:900,scale:.76,view:'three-quarter',fall:[1,1],right:[112,-230]},
  {id:'carrier2',role:'employee',x:1510,y:902,scale:.68,view:'three-quarter',left:[-115,-215],leftItem:'bag'},
  {id:'staff3',role:'employee',x:1680,y:910,scale:.62,view:'three-quarter',left:[-112,-205]}
 ],props:[{kind:'car',x:365,y:675,scale:1.08},{kind:'car',x:1510,y:610,scale:.72,truck:true},{kind:'bag',x:520,y:820,scale:.75}],camera:{from:[0,0],to:[12,0]}},
 {room:'garage',layout:'wide',clock:770,duration:75,place:'가방 1개를 가져감',date:'운송 6억 · 탈취 3억',actors:[
  {id:'rb',role:'robberB',x:535,y:888,scale:1.04,view:'three-quarter',to:[250,875],move:[.05,.84],run:true,left:[-134,-115],leftTo:[-88,-150],leftItem:'bag'},
  {id:'ra',role:'robberA',x:700,y:885,scale:.92,view:'three-quarter',to:[375,880],move:[.10,.84],run:true,right:[122,-224],rightTo:[98,-192]},
  {id:'victim',role:'employee',x:1320,y:900,scale:.76,view:'three-quarter',fall:[1,1],right:[112,-230]},
  {id:'carrier2',role:'employee',x:1510,y:902,scale:.68,view:'three-quarter',left:[-115,-215],leftItem:'bag'},
  {id:'staff3',role:'employee',x:1680,y:910,scale:.62,view:'three-quarter',left:[-112,-205]}
 ],props:[{kind:'car',x:365,y:675,scale:1.08,to:[-360,690],beat:[.38,.95],occupants:true},{kind:'car',x:1510,y:610,scale:.72,truck:true}],camera:{from:[0,0],to:[24,0]}}
];

// Court source 189.505–229.520. Cue starts: 0, 6.875, 11.900, 20.720 sec.
const court:Performance[]=[
 {room:'court',layout:'wide',clock:0,duration:206,date:'2023-01-16',place:'검찰 구형',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:960,y:550,scale:1.03,expression:'firm'},
  {id:'pros',role:'lawyer',x:355,y:930,scale:1.13,to:[650,890],move:[.08,.54],left:[-74,-162],right:[74,-162],leftTo:[-110,-258],rightTo:[110,-258],talk:true},
  {id:'A',role:'defendantA',x:1250,y:920,scale:.82,view:'back'},{id:'B',role:'defendantB',x:1510,y:920,scale:.92,view:'back'}
 ],props:[],camera:{from:[0,0],to:[18,0]}},
 {room:'court',layout:'side',clock:206,duration:151,date:'2023-02-17',place:'1심 선고',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:1450,y:670,scale:1.30,expression:'firm',right:[74,-160],rightTo:[130,-218]},
  {id:'clerk',role:'clerk',x:1120,y:820,scale:.84,to:[900,810],move:[.15,.72],left:[-70,-145],leftTo:[-104,-222],leftItem:'paper'},
  {id:'A',role:'defendantA',x:430,y:930,scale:1.02,view:'back'},{id:'B',role:'defendantB',x:680,y:930,scale:1.06,view:'back'}
 ],props:[],camera:{from:[0,0],to:[-42,0]}},
 {room:'court',layout:'reverse',clock:357,duration:265,date:'1심 판단 근거',place:'총기 경험 · 조준 · 진술',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:1350,y:675,scale:1.22,expression:'firm',right:[70,-158],rightTo:[115,-214]},
  {id:'clerk',role:'clerk',x:860,y:835,scale:.84,to:[650,820],move:[.12,.82],left:[-72,-146],leftTo:[-116,-222],leftItem:'paper'},
  {id:'A',role:'defendantA',x:350,y:930,scale:1.04,view:'back'},{id:'B',role:'defendantB',x:590,y:930,scale:1.10,view:'back'}
 ],props:[{kind:'box',x:520,y:710,scale:.65}],camera:{from:[0,0],to:[-8,8]}},
 {room:'court',layout:'wide',clock:622,duration:579,date:'2023-08-18',place:'항소심 판단',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:960,y:545,scale:1.12,expression:'firm',right:[74,-155],rightTo:[105,-215]},
  {id:'clerk',role:'clerk',x:810,y:855,scale:.86,to:[1120,840],move:[.12,.55],left:[-70,-145],leftTo:[-104,-220],leftItem:'paper'},
  {id:'A',role:'defendantA',x:500,y:925,scale:1.04,view:'back'},{id:'B',role:'defendantB',x:1440,y:925,scale:1.10,view:'back'}
 ],props:[],camera:{from:[0,0],to:[0,-12]}}
];
const CourtCard:React.FC<{f:number}>=({f})=>{
 const stage=f<206?0:f<357?1:f<622?2:f<842?3:4;
 const cards=[['검찰 구형','A: 사형 · B: 무기징역'],['1심 선고','A: 무기징역 · B: 징역 20년'],['1심 판단 근거','총기 경험 · 권총 조준 · 진술 신빙성'],['항소심 선고','A · B 모두 무기징역'],['법정형과 감경','사형 또는 무기징역 / 감경 시 상한 15년']];
 const [title,line]=cards[stage];
 return <g fontFamily="Arial, sans-serif" fontWeight="900" paintOrder="stroke" stroke={C.ink} strokeWidth="10"><rect x="60" y="705" width="1800" height="230" rx="28" fill="#34304e" opacity=".94"/><text x="960" y="788" textAnchor="middle" fill={C.yellow} fontSize="74">{title}</text><text x="960" y="875" textAnchor="middle" fill={C.paper} fontSize={stage===2||stage===4?52:64}>{line}</text>{stage===4&&<text x="960" y="922" textAnchor="middle" fill={C.paper} fontSize="39">1심 20년 선고는 법정형에 맞지 않는다는 판단</text>}</g>;
};
const VerdictOverlay:React.FC<{f:number}>=({f})=>f>=622?<g fontFamily="Arial, sans-serif" fontWeight="900" textAnchor="middle" paintOrder="stroke" stroke={C.ink} strokeWidth="8"><text x="500" y="670" fill={C.paper} fontSize="48">A · 무기징역</text><text x="1420" y="670" fill={C.paper} fontSize="48">B · 무기징역</text></g>:null;
const Block:React.FC<{kind:'event'|'court'}>=({kind})=>{const f=useCurrentFrame();const list=kind==='event'?event:court;const p=list.findLast(x=>f>=x.clock)||list[0];return <svg width="100%" height="100%" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid meet" style={{background:C.slate}}>{scene(p)}{kind==='court'&&<><VerdictOverlay f={f}/><CourtCard f={f}/></>}</svg>};
const Root=()=> <><Composition id="LF2-EVENT-DIRECTED-V3" component={()=> <Block kind="event"/>} durationInFrames={845} fps={FPS} width={426} height={240}/><Composition id="LF2-COURT-DIRECTED-V3" component={()=> <Block kind="court"/>} durationInFrames={1201} fps={FPS} width={426} height={240}/></>;
registerRoot(Root);
