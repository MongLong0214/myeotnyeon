import React from 'react';
import {AbsoluteFill,useCurrentFrame,useVideoConfig} from 'remotion';
import {BarStreetSet} from '../../../../production/compositor/src/components/sets';
import {FONT} from '../../../../production/compositor/src/theme';
import {INK,PAPER} from '../../../../production/compositor/src/components/toon';
import {ArticulatedGuy,Point,RigPose} from './FightRig';
const smooth=(x:number)=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x)};
const k=(t:number,points:[number,number][])=>{
 if(t<=points[0][0])return points[0][1];
 for(let i=1;i<points.length;i++){const [at,b]=points[i],[prev,a]=points[i-1];if(t<=at)return a+(b-a)*smooth((t-prev)/(at-prev))}return points[points.length-1][1];
};
const point=(t:number,points:[number,Point][]):Point=>[k(t,points.map(([f,p])=>[f,p[0]])),k(t,points.map(([f,p])=>[f,p[1]]))];
const standing=():RigPose=>({hip:[0,-170],torso:0,head:0,feet:[[-30,0],[30,0]],knees:[[-25,-90],[26,-90]],hands:[[-84,-166],[84,-166]],elbows:[[-70,-230],[70,-230]]});

export const FightScene:React.FC<{mode:'approach'|'impact';children?:React.ReactNode}>=({mode,children})=>{
 const frame=useCurrentFrame(),{fps}=useVideoConfig(),t=frame/fps;
 let ax=332,ay=830,vx=650,vy=812,s=.54;
 const a=standing(),v=standing();
 if(mode==='approach'){
  // Short outside approach: feet plant in alternating stances, no fighting/counterattack here.
  const step=smooth((t-2.05)/.85),settle=smooth((t-2.85)/.50);
  ax=450-112*step;vx=560+90*settle;
  a.feet=[[-30+38*step,0],[30-20*step,-22*Math.sin(Math.PI*step)]];
  a.knees=[[-24+18*step,-88],[35-18*step,-86-8*Math.sin(Math.PI*step)]];
  v.feet=[[-30-25*settle,-16*Math.sin(Math.PI*settle)],[30,0]];
  v.knees=[[-32-12*settle,-90],[26,-90]];
  // One open invitation gesture occurs only under the existing '야차룰' narration.
  a.hands[1]=point(t,[[0,[84,-166]],[4.25,[84,-166]],[4.65,[145,-220]],[5.12,[145,-220]],[5.50,[90,-180]]]);
  a.elbows![1]=point(t,[[0,[70,-230]],[4.25,[70,-230]],[4.65,[115,-265]],[5.12,[115,-265]],[5.50,[80,-235]]]);
 }else{
  // One representative action, not a count of blows. No loops, bursts, victim strikes or added SFX.
  ax=k(t,[[0,330],[.27,350],[.63,380],[1.00,380],[1.45,350],[2.37,350]]);vx=610;s=.62;ay=842;vy=818;
  a.hip=point(t,[[0,[0,-170]],[.45,[-8,-178]],[.80,[20,-170]],[1.10,[10,-170]],[1.48,[0,-170]]]);
  a.torso=k(t,[[0,0],[.45,-9],[.80,14],[1.08,8],[1.48,0]]);
  a.head=k(t,[[0,0],[.45,-5],[.80,-11],[1.48,0]]);
  const rear=point(t,[[0,[302,0]],[.25,[302,0]],[.44,[326,-16]],[.63,[352,0]],[1.1,[352,0]],[1.45,[322,0]],[2.37,[322,0]]]);
  const front=point(t,[[0,[362,0]],[.10,[362,0]],[.26,[390,-18]],[.44,[412,0]],[1.1,[412,0]],[1.25,[400,-14]],[1.48,[382,0]],[2.37,[382,0]]]);
  a.feet=[[(rear[0]-ax)/s,rear[1]/s],[(front[0]-ax)/s,front[1]/s]];
  a.knees=[[(a.feet[0][0]+a.hip[0]-24)*.5,-88],[(a.feet[1][0]+a.hip[0]+24)*.5,-88]];
  // Contact target is the near upper torso silhouette. Head is never used as an injury close-up.
  const handWorld=point(t,[[0,[ax+52,ay-103]],[.45,[ax+18,ay-155]],[.80,[575,635]],[.89,[575,635]],[1.08,[ax+90,ay-143]],[1.48,[ax+55,ay-103]]]);
  a.hands[1]=[(handWorld[0]-ax)/s,(handWorld[1]-ay)/s];a.elbows=undefined;
  a.hands[0]=[-75,-190];
  a.elbows=[[-68,-245],point(t,[[0,[70,-230]],[.45,[75,-285]],[.80,[203,-280]],[.89,[203,-280]],[1.08,[150,-250]],[1.48,[75,-230]]])];
  // After contact, the guest loses support: hip drops, both knees flex, hand reaches pavement.
  v.hip=point(t,[[0,[0,-170]],[.80,[0,-170]],[1.02,[22,-151]],[1.36,[25,-100]],[1.75,[36,-42]],[2.05,[36,-35]]]);
  v.torso=k(t,[[0,0],[.80,0],[1.02,17],[1.36,28],[1.85,38],[2.37,38]]);
  v.head=k(t,[[0,0],[.80,0],[1.02,9],[1.45,15],[1.85,23],[2.37,23]]);
  v.feet=[[-30,0],[30,0]];
  v.knees=[point(t,[[0,[-25,-90]],[1.05,[-15,-75]],[1.75,[64,-10]],[2.37,[64,-10]]]),point(t,[[0,[26,-90]],[1.05,[42,-70]],[1.75,[116,-8]],[2.37,[116,-8]]])];
  v.hands=[point(t,[[0,[-84,-166]],[.85,[-84,-166]],[1.18,[-25,-170]],[1.60,[155,-25]],[1.90,[172,0]],[2.37,[172,0]]]),point(t,[[0,[84,-166]],[.85,[84,-166]],[1.18,[118,-150]],[1.65,[206,-12]],[1.90,[210,0]],[2.37,[210,0]]])];
  v.elbows=[point(t,[[0,[-70,-230]],[.85,[-70,-230]],[1.18,[-40,-215]],[1.65,[125,-65]],[1.90,[125,-45]],[2.37,[125,-45]]]),point(t,[[0,[70,-230]],[.85,[70,-230]],[1.18,[95,-205]],[1.65,[185,-75]],[1.90,[210,-35]],[2.37,[210,-35]]])];
 }
 return <AbsoluteFill>
  {mode==='impact'?<IncidentStreetSet/>:<BarStreetSet/>}
  <ArticulatedGuy look="B" x={vx} y={vy} scale={s} rig={v}/>
  <ArticulatedGuy look="hoodie" x={ax} y={ay} scale={s} rig={a}/>
  {children}
  {mode==='impact'&&<div style={{position:'absolute',left:105,top:250,fontFamily:FONT,fontWeight:700,fontSize:28,color:PAPER,background:INK,padding:'6px 14px',borderRadius:8}}>보도 기반 재구성 · 동작 축약</div>}
 </AbsoluteFill>;
};

// Existing street SVG copied locally solely to omit the camera in the narrated CCTV-free scene.
const W=1000,H=900;
const S={stroke:INK,strokeWidth:8,strokeLinejoin:'round' as const,strokeLinecap:'round' as const};
const IncidentStreetSet: React.FC = () => {
  const f = useCurrentFrame();
  const glow = 0.85 + 0.08 * Math.sin(f * 0.21);
  return (
    <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
      <defs><linearGradient id="bsSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#141A33" /><stop offset="1" stopColor="#2A2F55" /></linearGradient></defs>
      <rect x={0} y={0} width={W} height={H} fill="url(#bsSky)" />
      {Array.from({ length: 14 }, (_, i) => <circle key={`bst${i}`} cx={(i * 263) % 1000} cy={(i * 71) % 180 + 20} r={i % 3 ? 2 : 3} fill="#FFF6C8" opacity={0.7} />)}
      <rect x={40} y={170} width={640} height={540} fill="#4E4058" {...S} />
      {Array.from({ length: 6 }, (_, r) => <line key={`br${r}`} x1={40} y1={240 + r * 80} x2={680} y2={240 + r * 80} stroke="#433650" strokeWidth={5} />)}
      <rect x={110} y={300} width={250} height={170} rx={10} fill="#FFC766" opacity={glow} {...S} />
      <line x1={235} y1={300} x2={235} y2={470} stroke={INK} strokeWidth={6} />
      <rect x={430} y={360} width={170} height={350} rx={8} fill="#FFB547" opacity={glow} {...S} />
      <circle cx={580} cy={540} r={9} fill={INK} />
      <g transform="translate(470 230)">
        <rect x={0} y={0} width={110} height={80} rx={14} fill="#F2C14E" stroke={INK} strokeWidth={6} />
        <rect x={22} y={18} width={46} height={46} rx={6} fill="#FFFDF6" stroke={INK} strokeWidth={5} />
        <path d="M68,28 q20,0 20,14 q0,14 -20,14" fill="none" stroke={INK} strokeWidth={5} />
        <rect x={22} y={14} width={46} height={12} rx={5} fill="#FFFDF6" stroke={INK} strokeWidth={4} />
      </g>

      <rect x={680} y={250} width={120} height={460} fill="#0E1120" stroke={INK} strokeWidth={6} />
      <rect x={800} y={210} width={220} height={500} fill="#3B3247" {...S} />
      <rect x={-20} y={700} width={W + 40} height={220} fill="#5A5A66" {...S} />
      <line x1={-20} y1={760} x2={1020} y2={760} stroke="#6E6E7A" strokeWidth={6} />
      <g transform="translate(900 700)">
        <rect x={-8} y={-420} width={16} height={420} fill="#2A2F3A" stroke={INK} strokeWidth={4} />
        <ellipse cx={0} cy={-424} rx={40} ry={14} fill="#FFE9A8" stroke={INK} strokeWidth={4} />
      </g>
    </svg>
  );
};
