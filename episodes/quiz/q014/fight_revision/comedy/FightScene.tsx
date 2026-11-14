import React from 'react';
import {AbsoluteFill,useCurrentFrame,useVideoConfig} from 'remotion';
import {BarStreetSet} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/components/sets';
import {FONT} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/theme';
import {INK,PAPER} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/components/toon';
import {ArticulatedGuy,Point,RigPose} from './FightRig';
export const smooth=(x:number)=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x)};
export const k=(t:number,points:[number,number][])=>{
 if(t<=points[0][0])return points[0][1];
 for(let i=1;i<points.length;i++){const [at,b]=points[i],[prev,a]=points[i-1];if(t<=at)return a+(b-a)*smooth((t-prev)/(at-prev))}return points[points.length-1][1];
};
export const point=(t:number,points:[number,Point][]):Point=>[k(t,points.map(([f,p])=>[f,p[0]])),k(t,points.map(([f,p])=>[f,p[1]]))];
export const standing=():RigPose=>({hip:[0,-170],torso:0,head:0,feet:[[-30,0],[30,0]],knees:[[-25,-90],[26,-90]],hands:[[-84,-166],[84,-166]],elbows:[[-70,-230],[70,-230]]});

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
  a.torso=k(t,[[0,0],[3.4,-14],[4.0,-14],[4.25,-22],[4.65,-10],[5.5,-8]]);a.head=12;
  a.hands[0]=[-85,-205];a.elbows![0]=[-112,-270];
  v.hands=[[-64,-155],[64,-155]];v.elbows=[[-64,-230],[64,-230]];
  // One open invitation gesture occurs only under the existing '야차룰' narration.
  a.hands[1]=point(t,[[0,[84,-166]],[4.25,[84,-166]],[4.65,[145,-220]],[5.12,[145,-220]],[5.50,[90,-180]]]);
  a.elbows![1]=point(t,[[0,[70,-230]],[4.25,[70,-230]],[4.65,[115,-265]],[5.12,[115,-265]],[5.50,[80,-235]]]);
 }else{
  // One representative action, not a count of blows. No loops, bursts, victim strikes or added SFX.
  ax=k(t,[[0,320],[.34,320],[.55,350],[.70,348],[1.05,330],[2.37,330]]);vx=635;s=.62;ay=842;vy=818;
  a.hip=point(t,[[0,[0,-170]],[.34,[-22,-180]],[.55,[25,-165]],[.70,[15,-170]],[1.05,[0,-170]]]);
  a.torso=k(t,[[0,-4],[.34,-25],[.55,28],[.70,11],[1.05,-5]]);
  a.head=k(t,[[0,12],[.34,18],[.55,-9],[.70,4],[1.05,8]]);
  // One fast forward fist: six frames extension, four frames withdrawal. Feet stay planted through contact.
  a.feet=[[(285-ax)/s,0],[(390-ax)/s,0]];
  a.knees=[[(a.feet[0][0]+a.hip[0]-24)*.5,-88],[(a.feet[1][0]+a.hip[0]+24)*.5,-88]];
  const handWorld=point(t,[[0,[420,675]],[.34,[348,632]],[.55,[555,548]],[.59,[555,548]],[.72,[450,650]],[.85,[423,710]]]);
  a.hands[1]=[(handWorld[0]-ax)/s,(handWorld[1]-ay)/s];
  a.hands[0]=[-65,-230];
  a.elbows=[[-108,-265],point(t,[[0,[75,-250]],[.34,[-95,-284]],[.55,[145,-370]],[.59,[145,-370]],[.72,[110,-295]],[1.05,[72,-240]]])];
  // After contact, the guest loses support: hip drops, both knees flex, hand reaches pavement.
  v.hip=point(t,[[0,[0,-170]],[.59,[0,-170]],[.78,[22,-151]],[1.36,[25,-100]],[1.75,[36,-42]],[2.05,[36,-35]]]);
  v.torso=k(t,[[0,0],[.59,0],[.78,17],[1.36,28],[1.85,38],[2.37,38]]);
  v.head=k(t,[[0,0],[.59,0],[.78,9],[1.45,15],[1.85,23],[2.37,23]]);
  v.feet=[[-30,0],[30,0]];
  v.knees=[point(t,[[0,[-25,-90]],[.85,[-15,-75]],[1.75,[64,-10]],[2.37,[64,-10]]]),point(t,[[0,[26,-90]],[.85,[42,-70]],[1.75,[116,-8]],[2.37,[116,-8]]])];
  v.hands=[point(t,[[0,[-84,-166]],[.59,[-84,-166]],[.95,[-25,-170]],[1.60,[155,-25]],[1.90,[172,0]],[2.37,[172,0]]]),point(t,[[0,[84,-166]],[.59,[84,-166]],[.95,[118,-150]],[1.65,[206,-12]],[1.90,[210,0]],[2.37,[210,0]]])];
  v.elbows=[point(t,[[0,[-70,-230]],[.59,[-70,-230]],[.95,[-40,-215]],[1.65,[125,-65]],[1.90,[125,-45]],[2.37,[125,-45]]]),point(t,[[0,[70,-230]],[.59,[70,-230]],[.95,[95,-205]],[1.65,[185,-75]],[1.90,[210,-35]],[2.37,[210,-35]]])];
 }
 return <AbsoluteFill>
  {mode==='impact'?<IncidentStreetSet/>:<BarStreetSet/>}
  <ArticulatedGuy look="B" x={vx} y={vy} scale={s} rig={v} expr="concern" eye={[-9,0]}/>
  <ArticulatedGuy look="hoodie" x={ax} y={ay} scale={s} rig={a} expr={mode==='approach'?'smug':t<.4?'smug':'serious'} eye={[11,0]}/>
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
