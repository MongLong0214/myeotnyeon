// Directed v2 uses the approved LF2 v6 SVG Puppet/ActedStage verbatim; no new character design.
import React from 'react';
import {Composition, registerRoot, useCurrentFrame} from 'remotion';
import {ActedStage, Performance} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/cartoon/engine_v6/ActedStage';
import {Bag} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/cartoon/engine_v6/Puppet';
import {C} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/cartoon/engine_v6/types';
const FPS=30;
const scene=(p:Performance)=> <ActedStage performance={p} f={useCurrentFrame()}/>;
const event:Performance[]=[
 {room:'garage',layout:'wide',clock:0,duration:210,place:'사건 재구성',date:'2001-12-21',actors:[
  {id:'staff1',role:'employee',x:1450,y:900,scale:.78,view:'back',to:[1120,875],move:[.05,.9],anonymous:true},
  {id:'staff2',role:'employee',x:1620,y:910,scale:.72,view:'back',to:[1280,885],move:[.1,.9],anonymous:true},
  {id:'staff3',role:'employee',x:1770,y:920,scale:.66,view:'back',to:[1400,895],move:[.15,.9],anonymous:true}],props:[{kind:'car',x:1440,y:640,scale:.76,truck:true},{kind:'bag',x:1120,y:812,scale:.75},{kind:'bag',x:1270,y:812,scale:.75}],camera:{from:[0,0],to:[20,0]}},
 {room:'garage',layout:'wide',clock:210,duration:165,place:'사건 재구성',date:'2001-12-21',actors:[
  {id:'ra',role:'robberA',x:245,y:905,scale:.92,to:[610,875],move:[.12,.86],run:true,right:[85,-166],rightTo:[155,-220],item:'gun',anonymous:true},
  {id:'rb',role:'robberB',x:115,y:915,scale:1.03,to:[500,885],move:[.1,.86],run:true,left:[-75,-135],leftTo:[-108,-175],anonymous:true},
  {id:'staff',role:'employee',x:1320,y:880,scale:.78,view:'back',right:[75,-180],rightTo:[125,-230],anonymous:true}],props:[{kind:'car',x:410,y:715,scale:1.0,to:[670,690],beat:[.05,.7],occupants:true},{kind:'car',x:1460,y:620,scale:.72,truck:true},{kind:'bag',x:1120,y:812,scale:.75},{kind:'bag',x:1270,y:812,scale:.75}],camera:{from:[0,0],to:[0,10]}},
 {room:'garage',layout:'side',clock:375,duration:178,place:'사건 재구성',date:'권총 등장',actors:[
  {id:'ra',role:'robberA',x:600,y:900,scale:1.25,view:'profile',right:[100,-260],rightTo:[180,-280],item:'gun',anonymous:true},
  {id:'staff',role:'employee',x:1295,y:895,scale:1.05,view:'back',fall:[0,1],beat:[.34,.72],anonymous:true},
  {id:'other',role:'employee',x:1590,y:900,scale:.8,view:'back',left:[-70,-180],leftTo:[-120,-245],anonymous:true}],props:[{kind:'car',x:1510,y:610,scale:.7,truck:true},{kind:'bag',x:1110,y:815,scale:.76},{kind:'bag',x:1260,y:815,scale:.76}],camera:{from:[0,0],to:[-30,0]}},
 {room:'garage',layout:'wide',clock:553,duration:292,place:'사건 재구성',date:'가방 2개 중 1개',actors:[
  {id:'rb',role:'robberB',x:560,y:895,scale:1.05,to:[290,875],move:[.1,.64],run:true,left:[-86,-150],leftTo:[-86,-150],leftItem:'bag',anonymous:true},
  {id:'ra',role:'robberA',x:745,y:895,scale:.92,to:[345,880],move:[.18,.68],run:true,right:[90,-200],rightTo:[120,-235],anonymous:true},
  {id:'staff',role:'employee',x:1350,y:900,scale:.75,view:'back',right:[76,-185],anonymous:true}],props:[{kind:'car',x:365,y:675,scale:1.08,to:[-360,690],beat:[.62,.96],occupants:true},{kind:'car',x:1510,y:610,scale:.72,truck:true},{kind:'bag',x:1245,y:815,scale:.75}],camera:{from:[0,0],to:[30,0]}}
];
const court:Performance[]=[
 {room:'court',layout:'wide',clock:0,duration:206,date:'2023-01-16',place:'검찰 구형',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:960,y:550,scale:1.03,expression:'firm'},
  {id:'pros',role:'lawyer',x:355,y:930,scale:1.13,to:[650,890],move:[.1,.55],left:[-74,-162],right:[74,-162],leftTo:[-110,-260],rightTo:[110,-260],talk:true},
  {id:'A',role:'defendantA',x:1250,y:920,scale:.82,view:'back',anonymous:true},{id:'B',role:'defendantB',x:1510,y:920,scale:.92,view:'back',anonymous:true}],props:[],camera:{from:[0,0],to:[25,0]}},
 {room:'court',layout:'side',clock:206,duration:184,date:'2023-02-17',place:'1심 선고',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:1450,y:670,scale:1.3,expression:'firm',right:[74,-160],rightTo:[130,-218]},
  {id:'clerk',role:'clerk',x:1150,y:820,scale:.82,to:[900,810],move:[.18,.76],leftItem:'paper',talk:false},
  {id:'A',role:'defendantA',x:430,y:930,scale:1.02,view:'back',anonymous:true},{id:'B',role:'defendantB',x:680,y:930,scale:1.06,view:'back',anonymous:true}],props:[],camera:{from:[0,0],to:[-45,0]}},
 {room:'court',layout:'reverse',clock:390,duration:270,date:'1심 판단 근거',place:'기록과 진술',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:1350,y:675,scale:1.22,expression:'firm'},
  {id:'clerk',role:'clerk',x:860,y:835,scale:.84,to:[650,820],move:[.12,.84],leftItem:'paper'},
  {id:'A',role:'defendantA',x:350,y:930,scale:1.04,view:'back',anonymous:true},{id:'B',role:'defendantB',x:590,y:930,scale:1.10,view:'back',anonymous:true}],props:[{kind:'box',x:520,y:710,scale:.65}],camera:{from:[0,0],to:[-10,10]}},
 {room:'court',layout:'wide',clock:660,duration:541,date:'2023-08-18',place:'항소심',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:960,y:545,scale:1.12,expression:'firm',right:[74,-155],rightTo:[105,-215]},
  {id:'clerk',role:'clerk',x:810,y:855,scale:.86,to:[1120,840],move:[.14,.55],leftItem:'paper'},
  {id:'A',role:'defendantA',x:500,y:925,scale:1.04,view:'back',anonymous:true},{id:'B',role:'defendantB',x:1440,y:925,scale:1.10,view:'back',anonymous:true}],props:[],camera:{from:[0,0],to:[0,-14]}}
];
const Block:React.FC<{kind:'event'|'court'}>=({kind})=>{const f=useCurrentFrame();const list=kind==='event'?event:court;const p=list.findLast(x=>f>=x.clock)||list[0];return <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{background:C.slate}}>{scene(p)}{kind==='event'&&f>=553&&<g transform={`translate(${560+Math.min(1,(f-553)/190)*-280} ${790-Math.min(1,(f-553)/190)*70})`}><Bag scale={.72}/></g>}{kind==='court'&&f>=1000&&<g><text x="500" y="825" fill={C.paper} stroke={C.ink} strokeWidth="8" paintOrder="stroke" fontSize="48" fontWeight="900">A  무기징역</text><text x="1380" y="825" fill={C.paper} stroke={C.ink} strokeWidth="8" paintOrder="stroke" fontSize="48" fontWeight="900">B  무기징역</text></g>}</svg>};
const Root=()=> <><Composition id="LF2-EVENT-DIRECTED-V2" component={()=> <Block kind="event"/>} durationInFrames={845} fps={FPS} width={640} height={360}/><Composition id="LF2-COURT-DIRECTED-V2" component={()=> <Block kind="court"/>} durationInFrames={1201} fps={FPS} width={640} height={360}/></>;
registerRoot(Root);
