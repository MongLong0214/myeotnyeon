// LF2 directed v4: corrected blocking/contact/court actions; retains engine_v6 art verbatim.
import React, {useEffect, useState} from 'react';
import {Composition, continueRender, delayRender, registerRoot, useCurrentFrame} from 'remotion';
import {ActedStage, Performance} from './ActedStage_v7_minimal';
import {C} from '../../../production/compositor/src/cartoon/engine_v6/types';
import pretendardRegular from './fonts/Pretendard-Regular.otf';
import pretendardSemiBold from './fonts/Pretendard-SemiBold.otf';
import pretendardBold from './fonts/Pretendard-Bold.otf';
const FPS=30;
const stage=(p:Performance)=><ActedStage performance={p} f={useCurrentFrame()}/>;
const FONT='Pretendard';
// Font loading is intentionally blocking: a review render must not silently fall back.
const FontGate:React.FC<{children:React.ReactNode}>=({children})=>{
 const [handle]=useState(()=>delayRender('Pretendard local font'));
 useEffect(()=>{Promise.all([
  document.fonts.load('400 16px Pretendard'),document.fonts.load('600 16px Pretendard'),document.fonts.load('700 16px Pretendard')
 ]).then(()=>{if(!document.fonts.check('700 16px Pretendard','가나다라마바사'))throw new Error('Pretendard unavailable');continueRender(handle);}).catch(error=>{throw error;});},[handle]);
 return <><style>{`@font-face{font-family:Pretendard;src:url(${pretendardRegular}) format('opentype');font-weight:400;font-style:normal;font-display:block}@font-face{font-family:Pretendard;src:url(${pretendardSemiBold}) format('opentype');font-weight:600;font-style:normal;font-display:block}@font-face{font-family:Pretendard;src:url(${pretendardBold}) format('opentype');font-weight:700;font-style:normal;font-display:block}`}</style>{children}</>;
};

// Source 13.590–41.740.  The bag in scenes 3–5 is one physical Props bag: no hand-item clone.
const event:Performance[]=[
 {room:'garage',layout:'wide',clock:0,duration:220,place:'사건 재구성',date:'2001-12-21',actors:[
  {id:'carrier1',role:'employee',x:1550,y:900,scale:.82,view:'profile',flip:true,to:[1130,875],move:[.04,.92],left:[-78,-148],leftTo:[-92,-156],leftItem:'bag'},
  {id:'carrier2',role:'employee',x:1730,y:910,scale:.76,view:'profile',flip:true,to:[1300,886],move:[.08,.92],left:[-76,-146],leftTo:[-89,-154],leftItem:'bag'},
  {id:'staff3',role:'employee',x:1850,y:920,scale:.70,view:'profile',flip:true,to:[1440,898],move:[.12,.92]}],props:[{kind:'car',x:1470,y:640,scale:.76,truck:true}],camera:{from:[0,0],to:[10,0]}},
 // Wide stable frame: truck, walking team and sedan all visible; sedan ends across the exact travel lane.
 {room:'garage',layout:'wide',clock:220,duration:99,place:'차량이 동선을 막음',date:'2001-12-21',actors:[
  {id:'carrier1',role:'employee',x:1130,y:875,scale:.82,view:'profile',flip:true,left:[-92,-156],leftItem:'bag'},
  {id:'carrier2',role:'employee',x:1300,y:886,scale:.76,view:'profile',flip:true,left:[-89,-154],leftItem:'bag'},
  {id:'staff3',role:'employee',x:1440,y:898,scale:.70,view:'profile',flip:true}],props:[
   {kind:'car',x:170,y:755,scale:1.08,to:[1010,795],beat:[.05,.66],occupants:true},
   {kind:'car',x:1470,y:640,scale:.76,truck:true}],camera:{from:[0,0],to:[0,0]}},
 // A and B remain widely separated silhouettes: A gun left, B unarmed right.
 {room:'garage',layout:'wide',clock:319,duration:202,place:'권총 등장',date:'2001-12-21',actors:[
  {id:'A',role:'robberA',x:420,y:900,scale:1.16,view:'profile',right:[104,-250],rightTo:[175,-275],item:'gun'},
  {id:'victim',role:'employee',x:1220,y:890,scale:1.00,view:'profile',flip:true,right:[78,-118],rightTo:[-5,-55],fall:[0,1],beat:[.42,.82]},
  {id:'B',role:'robberB',x:760,y:900,scale:1.02,view:'profile',flip:true,to:[840,900],move:[.56,.95],left:[-75,-150],leftTo:[-70,-130]},
  {id:'carrier2',role:'employee',x:1540,y:902,scale:.68,view:'profile',flip:true,left:[-115,-215],leftItem:'bag'},
  {id:'staff3',role:'employee',x:1720,y:910,scale:.62,view:'profile',flip:true}],props:[
   {kind:'car',x:1010,y:795,scale:1.08,occupants:true},{kind:'car',x:1510,y:610,scale:.70,truck:true},{kind:'bag',x:1298,y:815,scale:.75,to:[1200,890],beat:[.42,.82]}],camera:{from:[0,0],to:[0,0]}},
 // Drop completes before B arrives: bag remains visible on floor and separate from the fallen victim.
 {room:'garage',layout:'wide',clock:521,duration:112,place:'가방이 바닥에 남음',date:'2001-12-21',actors:[
  {id:'A',role:'robberA',x:420,y:900,scale:1.16,view:'profile',right:[175,-275],item:'gun'},
  {id:'victim',role:'employee',x:1220,y:890,scale:1.00,view:'profile',flip:true,fall:[1,1],right:[-5,-55]},
  {id:'B',role:'robberB',x:700,y:900,scale:1.02,view:'profile',flip:true,to:[1050,900],move:[.06,.90],right:[104,-125],rightTo:[150,-95]},
  {id:'carrier2',role:'employee',x:1540,y:902,scale:.68,view:'profile',flip:true,left:[-115,-215],leftItem:'bag'},
  {id:'staff3',role:'employee',x:1720,y:910,scale:.62,view:'profile',flip:true}],props:[
   {kind:'car',x:1010,y:795,scale:1.08,occupants:true},{kind:'car',x:1510,y:610,scale:.72,truck:true},{kind:'bag',x:1200,y:890,scale:.75,to:[1180,900],beat:[.08,.35]}],camera:{from:[0,0],to:[0,0]}},
 // With flip=true, B's left local hand maps to the world-right handle: x=1050-1.02*(-130)=1182.6;
// y=900+1.02*(-95)=803.1. Bag handle is y=900-127*.75=804.75.
 {room:'garage',layout:'side',clock:633,duration:58,place:'B가 손잡이에 손을 댐',date:'2001-12-21',actors:[
  {id:'A',role:'robberA',x:360,y:900,scale:1.02,view:'profile',right:[160,-265],item:'gun'},
  {id:'victim',role:'employee',x:1220,y:890,scale:.88,view:'profile',flip:true,fall:[1,1]},
  {id:'B',role:'robberB',x:1050,y:900,scale:1.02,view:'profile',flip:true,to:[1050,900],left:[-130,-95],right:[130,-95]},
  {id:'carrier2',role:'employee',x:1560,y:902,scale:.68,view:'profile',flip:true,left:[-115,-215],leftItem:'bag'},
  {id:'staff3',role:'employee',x:1740,y:910,scale:.62,view:'profile',flip:true}],props:[
   {kind:'car',x:500,y:795,scale:1.08,occupants:true},{kind:'car',x:1510,y:610,scale:.72,truck:true},{kind:'bag',x:1180,y:900,scale:.75}],camera:{from:[0,0],to:[0,0]}},
 // Floor bag disappears at this cut; the only bag is B's HandProp, inheriting the exact actor transform.
 {room:'garage',layout:'side',clock:691,duration:154,place:'B가 가방을 들고 차량으로',date:'2001-12-21',actors:[
  {id:'A',role:'robberA',x:300,y:900,scale:.94,view:'profile',right:[150,-255],item:'gun'},
  {id:'victim',role:'employee',x:1220,y:890,scale:.80,view:'profile',flip:true,fall:[1,1]},
  {id:'B',role:'robberB',x:1050,y:900,scale:1.02,view:'profile',flip:true,to:[670,900],move:[.34,.92],run:true,beat:[.05,.28],left:[-130,-95],leftTo:[-130,-235],leftItem:'bag'},
  {id:'carrier2',role:'employee',x:1560,y:902,scale:.68,view:'profile',flip:true,left:[-115,-215],leftItem:'bag'},
  {id:'staff3',role:'employee',x:1740,y:910,scale:.62,view:'profile',flip:true}],props:[
   {kind:'car',x:500,y:795,scale:1.08,occupants:true},{kind:'car',x:1510,y:610,scale:.72,truck:true}],camera:{from:[0,0],to:[0,0]}}
];

const court:Performance[]=[
 // Prosecutor alone at a lectern facing listening judge; no judge gesture.
 {room:'court',layout:'side',clock:0,duration:206,date:'2023-01-16',place:'검찰 구형',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:1480,y:665,scale:1.12,view:'profile',flip:true,expression:'firm',left:[-72,-155],right:[73,-155]},
  {id:'pros',role:'lawyer',x:540,y:910,scale:1.10,view:'profile',to:[660,900],move:[.10,.42],right:[88,-165],rightTo:[145,-250],talk:true},
  {id:'A',role:'defendantA',x:980,y:930,scale:.82,view:'profile',flip:true},{id:'B',role:'defendantB',x:1190,y:930,scale:.86,view:'profile',flip:true}],props:[],camera:{from:[0,0],to:[0,0]}},
 // First instance: judge reads; clerk separately carries the written decision to the bench; defendants face judge.
 {room:'court',layout:'reverse',clock:206,duration:151,date:'2023-02-17',place:'1심 선고',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:1260,y:640,scale:1.25,view:'profile',flip:true,expression:'firm',head:[18,-4],gaze:[-4,18],beat:[.48,.78],left:[-70,-155],right:[74,-160],rightTo:[108,-215],item:'paper',talk:[.56,.90]},
  {id:'A',role:'defendantA',x:360,y:930,scale:1.00,view:'profile'},{id:'B',role:'defendantB',x:620,y:930,scale:1.04,view:'profile'}],props:[],camera:{from:[0,0],to:[-18,0]}},
 // Grounds: the judge continues to read the record; no fictional handoff is shown.
 {room:'court',layout:'side',clock:357,duration:265,date:'1심 판단 근거',place:'기록을 읽는 재판장',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:1380,y:650,scale:1.24,view:'profile',flip:true,expression:'firm',head:[14,-2],gaze:[-4,16],beat:[.50,.78],right:[76,-175],rightTo:[95,-220],item:'paper',talk:[.58,.91]},
  {id:'clerk',role:'clerk',x:930,y:855,scale:.82,view:'profile',right:[72,-150],left:[-70,-145]},
  {id:'A',role:'defendantA',x:430,y:930,scale:1.00,view:'profile'},{id:'B',role:'defendantB',x:700,y:930,scale:1.08,view:'profile'}],props:[{kind:'box',x:1050,y:770,scale:.56}],camera:{from:[0,0],to:[-12,0]}},
 // Appeal: judge reads, raises head, then speaks while the defendants look toward the bench.
 {room:'court',layout:'wide',clock:622,duration:579,date:'2023-08-18',place:'항소심 판단',foreground:'bench',actors:[
  {id:'judge',role:'judge',x:960,y:550,scale:1.10,expression:'firm',head:[22,-6],gaze:[-5,18],right:[-42,-180],rightTo:[115,-215],item:'paper',beat:[.42,.72],talk:[.58,.93]},
  {id:'A',role:'defendantA',x:430,y:925,scale:1.04,view:'profile',head:[0,12],left:[-74,-105]},
  {id:'B',role:'defendantB',x:1490,y:925,scale:1.10,view:'profile',flip:true,head:[0,-12],left:[-74,-215]}],props:[],camera:{from:[0,0],to:[0,-8]}}
];
const Lectern=()=> <g stroke={C.ink} strokeWidth="10"><path d="M430 695H650L690 900H390Z" fill="#4d6571"/><path d="M418 695H662L630 638H450Z" fill={C.paper}/><text x="540" y="770" textAnchor="middle" fontFamily={FONT} fontSize="44" fontWeight="700" fill={C.yellow} strokeWidth="5">검찰</text></g>;
// Caption text is intentionally absent here: ASS is the sole text layer for spoken cues.
// The complete scene is uniformly reduced once, reserving a neutral bottom field.
// This separates captions from feet, the fallen victim, bags, and court furniture.
const Block:React.FC<{kind:'event'|'court'}>=({kind})=>{const f=useCurrentFrame();const list=kind==='event'?event:court;const p=list.findLast(x=>f>=x.clock)||list[0];return <svg width="100%" height="100%" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid meet" style={{background:C.slate}}>{stage(p)}{kind==='court'&&f<206&&<Lectern/>}</svg>};
const Root=()=> <FontGate><Composition id="LF2-EVENT-DIRECTED-V5" component={()=> <Block kind="event"/>} durationInFrames={845} fps={FPS} width={640} height={360}/><Composition id="LF2-COURT-DIRECTED-V5" component={()=> <Block kind="court"/>} durationInFrames={1201} fps={FPS} width={640} height={360}/></FontGate>;
registerRoot(Root);
