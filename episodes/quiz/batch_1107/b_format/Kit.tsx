// Shared B-format helpers: limb IK with fixed bone lengths, ambient breathing, sets, props, court pieces.
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {ArticulatedGuy,Expr,Look,RigPose,Point} from './FightRig';
import {standing} from './FightScene';
import {INK,PAPER,GOLD,RED,TEAL} from './CourtDynamic';
import {gesture} from './CourtFix1';
export {gesture};
export const S={stroke:INK,strokeWidth:9,strokeLinecap:'round' as const,strokeLinejoin:'round' as const};
export const clamp01=(u:number)=>Math.max(0,Math.min(1,u));
export const ease=(u:number)=>{u=clamp01(u);return u<.5?4*u*u*u:1-Math.pow(-2*u+2,3)/2;};
export const breathe=(f:number,phase=0)=>Math.sin(2*Math.PI*f/120+phase);
// keyframes with cubic ease between points
export const kf=(t:number,pts:[number,number][])=>{if(t<=pts[0][0])return pts[0][1];for(let i=1;i<pts.length;i++){const [a,va]=pts[i-1],[b,vb]=pts[i];if(t<=b)return va+(vb-va)*ease((t-a)/(b-a));}return pts[pts.length-1][1];};
export const kp=(t:number,pts:[number,Point][]):Point=>[kf(t,pts.map(([f,p])=>[f,p[0]])),kf(t,pts.map(([f,p])=>[f,p[1]]))];
const rad=(a:number)=>a*Math.PI/180;
const rot=(p:Point,a:number):Point=>[p[0]*Math.cos(rad(a))-p[1]*Math.sin(rad(a)),p[0]*Math.sin(rad(a))+p[1]*Math.cos(rad(a))];
// two-bone IK; picks the solution whose bend points along `prefer` (unit-ish vector)
const ik=(a:Point,b:Point,l1:number,l2:number,prefer:Point):[Point,Point]=>{
 let dx=b[0]-a[0],dy=b[1]-a[1];let d=Math.hypot(dx,dy);const max=l1+l2-.5;
 if(d>max){b=[a[0]+dx/d*max,a[1]+dy/d*max];dx=b[0]-a[0];dy=b[1]-a[1];d=max;}
 d=Math.max(d,Math.abs(l1-l2)+1);
 const k=(l1*l1-l2*l2+d*d)/(2*d),h=Math.sqrt(Math.max(0,l1*l1-k*k));
 const m:Point=[a[0]+dx/d*k,a[1]+dy/d*k],n:Point=[-dy/d,dx/d];
 const e1:Point=[m[0]+n[0]*h,m[1]+n[1]*h],e2:Point=[m[0]-n[0]*h,m[1]-n[1]*h];
 const s1=(e1[0]-m[0])*prefer[0]+(e1[1]-m[1])*prefer[1],s2=(e2[0]-m[0])*prefer[0]+(e2[1]-m[1])*prefer[1];
 return [s1>=s2?e1:e2,b];
};
// Fill elbows (outward/down) and knees (forward = toward `kneeDir`) with the rig's own bone lengths.
export const solve=(r:RigPose,opt:{knee?:[Point,Point];elbow?:[Point,Point]}={})=>{
 const u=(p:Point):Point=>{const q=rot([p[0],p[1]+170],r.torso);return [r.hip[0]+q[0],r.hip[1]+q[1]];};
 const sh:[Point,Point]=[u([-50,-302]),u([50,-302])];
 const eb=opt.elbow??[[-1,.6],[1,.6]];
 const a0=ik(sh[0],r.hands[0],110,100,eb[0]),a1=ik(sh[1],r.hands[1],110,100,eb[1]);
 r.elbows=[a0[0],a1[0]];r.hands=[a0[1],a1[1]];
 const kd=opt.knee??[[-.25,-1],[.25,-1]];
 const hp:[Point,Point]=[[r.hip[0]-24,r.hip[1]],[r.hip[0]+24,r.hip[1]]];
 const l0=ik(hp[0],r.feet[0],80,90,kd[0]),l1=ik(hp[1],r.feet[1],80,90,kd[1]);
 r.knees=[l0[0],l1[0]];r.feet=[l0[1],l1[1]];
 return r;
};
// Standing person with ambient breathing; `pose` edits the rig before IK.
export const Who:React.FC<{look:Look;x:number;y:number;s:number;expr?:Expr;talk?:boolean;eye?:Point;phase?:number;pose?:(r:RigPose,f:number)=>void;ik?:{knee?:[Point,Point];elbow?:[Point,Point]};anonymous?:boolean}>=({look,x,y,s,expr='serious',talk=false,eye,phase=0,pose,ik:o})=>{
 const f=useCurrentFrame(),r=standing();
 r.hands=[[-78,-118],[78,-118]];
 r.hip=[0,-170+1.5*breathe(f,phase)];r.torso=.4*breathe(f,phase+1.3);r.head=.6*breathe(f,phase+.7);
 r.handProps=[{pose:'relaxed'},{pose:'relaxed'}];
 pose?.(r,f);
 r.hands=[[r.hands[0][0]+1.4*breathe(f,phase+.3),r.hands[0][1]+1.4*breathe(f,phase+1.9)],[r.hands[1][0]+1.4*breathe(f,phase+2.7),r.hands[1][1]+1.4*breathe(f,phase+4.2)]];
 solve(r,o);
 return <ArticulatedGuy look={look} x={x} y={y} scale={s} rig={r} expr={expr} talk={talk} eye={eye??[x<540?8:-8,1]} label="실존 인물과 무관한 원작 성인 카툰"/>;
};
export const Push:React.FC<{t:number;dur:number;amt?:number;origin?:string;children:React.ReactNode}>=({t,dur,amt=.025,origin='50% 45%',children})=><AbsoluteFill style={{transform:`scale(${1+amt*ease(t/Math.max(1,dur))})`,transformOrigin:origin}}>{children}</AbsoluteFill>;
export const Snap:React.FC<{t:number;amt?:number;origin?:string;children:React.ReactNode}>=({t,amt=.07,origin='50% 50%',children})=><AbsoluteFill style={{transform:`scale(${1+amt*(1-clamp01(t/4))})`,transformOrigin:origin}}>{children}</AbsoluteFill>;

// ---- sets ----
export const RestRoom:React.FC<{alt?:boolean}>=({alt=false})=><AbsoluteFill style={{background:'#9E9B86'}}><svg width={1080} height={1920} {...S}>
 <path d="M0 0H1080V1180H0Z" fill={alt?'#D6CBAE':'#C5CEBE'}/>
 <path d="M0 1180H1080V1920H0Z" fill="#9E9B86"/>{[1290,1440,1630,1880].map(y=><path key={y} d={`M0 ${y}H1080`} stroke="#8C8A76" strokeWidth={5}/>)}
 {[-200,100,400,700,1000,1300].map(x=><path key={x} d={`M540 1180L${x*1.6-324} 1920`} stroke="#8C8A76" strokeWidth={4}/>)}
 <path d="M0 1180H1080" strokeWidth={10}/>
 {alt?<g>
  <path d="M60 330H420V760H60Z" fill="#A9B9B4"/><path d="M80 350H400V740H80Z" fill="#DCE6DE" strokeWidth={6}/>{[410,470,530,590,650,710].map(y=><path key={y} d={`M80 ${y}H400`} stroke="#B3C2BA" strokeWidth={8}/>)}
  <path d="M790 420H1010V1175H790Z" fill="#8A6E52"/><circle cx={820} cy={800} r={11} fill={GOLD} strokeWidth={5}/>
  <path d="M500 120H580V170H500Z" fill="#EDEAD8" strokeWidth={6}/><path d="M540 0V120" strokeWidth={6}/>
 </g>:<g>
  {[40,190,340].map(x=><g key={x}><path d={`M${x} 420H${x+140}V1175H${x}Z`} fill="#7E93A0"/><path d={`M${x+20} 470H${x+120}M${x+20} 500H${x+120}`} stroke="#5E7380" strokeWidth={6}/><path d={`M${x+110} 760V830`} strokeWidth={8}/></g>)}
  <path d="M640 260H1010V700H640Z" fill="#A9B9B4"/><path d="M660 280H990V680H660Z" fill="#E3E9DD" strokeWidth={6}/><path d="M825 280V680M660 480H990" strokeWidth={6}/>
  <path d="M560 0V90M470 90H650V130H470Z" fill="#EDEAD8" strokeWidth={6}/>
 </g>}
</svg></AbsoluteFill>;
export const Dawn:React.FC=()=><AbsoluteFill style={{background:'#8F9089'}}><svg width={1080} height={1920} {...S}>
 <path d="M0 0H1080V1160H0Z" fill="#AFC0CB"/><path d="M0 760L180 640L360 700L560 600L780 690L1080 620V1160H0Z" fill="#8FA3A6" strokeWidth={7}/>
 <path d="M0 1160H1080V1920H0Z" fill="#7F817C"/><path d="M0 1160H1080" strokeWidth={10}/>{[0,1,2,3,4,5].map(i=><path key={i} d={`M${40+i*200} 1500H${150+i*200}`} stroke="#E9E1C6" strokeWidth={16}/>)}
 <g transform="translate(-40 560)"><path d="M40 160H520V560H40Z" fill="#4E8A61"/><path d="M60 180H500V300H60Z" fill="#6FAE80" strokeWidth={6}/><path d="M520 300H760L840 420V560H520Z" fill="#E7E3D6"/><path d="M560 330H730L790 420H560Z" fill="#9EB6C4" strokeWidth={6}/>{[150,420,700].map(x=><g key={x}><circle cx={x} cy={580} r={62} fill={INK}/><circle cx={x} cy={580} r={24} fill="#9A9C94"/></g>)}<path d="M60 420H500" stroke="#3E6F4E" strokeWidth={12}/></g>
</svg></AbsoluteFill>;
export const Cell:React.FC=()=><AbsoluteFill style={{background:'#59626A'}}><svg width={1080} height={1920} {...S}>
 <path d="M0 0H1080V1260H0Z" fill="#6F7A82"/>{[200,480,760].map(y=><path key={y} d={`M0 ${y}H1080`} stroke="#66717A" strokeWidth={6}/>)}
 <path d="M0 1260H1080V1920H0Z" fill="#4B535A"/><path d="M0 1260H1080" strokeWidth={9}/>
</svg></AbsoluteFill>;
export const Bars:React.FC<{xs:number[];dx?:number;opacity?:number}>=({xs,dx=0,opacity=1})=><svg width={1080} height={1920} style={{position:'absolute',opacity}} {...S}>
 {xs.map(x=><g key={x}><path d={`M${x+dx-17} -20H${x+dx+17}V1940H${x+dx-17}Z`} fill="#3F474D" strokeWidth={7}/><path d={`M${x+dx-6} -20V1940`} stroke="#77828A" strokeWidth={6}/></g>)}
 <path d={`M${Math.min(...xs)+dx-40} 1120H${Math.max(...xs)+dx+40}V1150H${Math.min(...xs)+dx-40}Z`} fill="#3F474D" strokeWidth={7}/>
</svg>;
// Blanket over a curled adult; only the shoe soles show (no face, no body detail).
export const Blanket:React.FC<{x:number;y:number;s?:number;squash?:number}>=({x,y,s=1,squash=0})=><svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
 <g transform={`translate(${x} ${y}) scale(${s*(1+.05*squash)} ${s*(1-.09*squash)})`}>
  <ellipse cx={20} cy={8} rx={330} ry={34} fill="rgba(0,0,0,.25)" stroke="none"/>
  <g transform="translate(300 -40)"><path d="M0 -50Q46 -64 58 -26Q64 12 20 22L-6 18Z" fill="#EDEDE6"/><path d="M8 -38Q36 -40 42 -14" fill="none" stroke="#B9B9B0" strokeWidth={6}/><path d="M-6 -2Q44 -8 60 22Q64 54 18 60L-8 54Z" fill="#EDEDE6"/></g>
  <path d="M-330 0Q-345 -150 -230 -205Q-120 -300 30 -280Q170 -290 250 -200Q330 -130 318 0Z" fill="#7D9CC6"/>
  <path d="M-250 -170L-80 -40M-140 -255L80 -60M20 -282L230 -90M-300 -60L-160 -230M-160 -10L60 -265M30 -20L250 -210" fill="none" stroke="#5F7FAA" strokeWidth={6}/>
  <path d="M-330 0Q-200 -40 -60 -10Q120 20 318 0" fill="none" stroke="#5F7FAA" strokeWidth={8}/>
  <path d="M-180 -120Q-150 -150 -110 -140M100 -200Q140 -220 170 -190" fill="none" stroke="#A9C0DD" strokeWidth={8}/>
 </g></svg>;
export const Burst:React.FC<{x:number;y:number;t:number;s?:number}>=({x,y,t,s=1})=>{if(t<0||t>5)return null;const g=1-t/6;return <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><g transform={`translate(${x} ${y}) scale(${s*(.8+.4*(1-g))})`} opacity={g}>
 <path d="M0 -95L22 -32L88 -52L42 0L96 40L28 40L30 104L-6 48L-60 92L-48 26L-110 6L-48 -18L-70 -78L-14 -42Z" fill={GOLD}/>
 {[-60,-20,20,60].map(a=><path key={a} d={`M${Math.sin(rad(a))*120} ${-Math.cos(rad(a))*120}L${Math.sin(rad(a))*175} ${-Math.cos(rad(a))*175}`} strokeWidth={10}/>)}
</g></svg>;};
export const Sweat:React.FC<{x:number;y:number;t:number;s?:number}>=({x,y,t,s=1})=><svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}>
 {[0,1].map(i=><path key={i} d="M0 -18Q-26 18 0 32Q26 18 0 -18" transform={`translate(${x+i*34*s} ${y+((t*2.2+i*23)%60)*s}) scale(${s})`} fill="#A6DDF4" stroke={INK} strokeWidth={4}/>)}
</svg>;
// In-world paper with text, padded; coordinates are screen space.
export const Paper:React.FC<{x:number;y:number;w:number;h:number;lines:string[];size:number;rot?:number;color?:string;stack?:number}>=({x,y,w,h,lines,size,rot:r=0,color=INK,stack=0})=><svg width={1080} height={1920} style={{position:'absolute'}} {...S}>
 <g transform={`translate(${x} ${y}) rotate(${r})`}>
  {Array.from({length:stack}).map((_,i)=><path key={i} d={`M${-w/2+6*(i+1)} ${-h/2+6*(i+1)}H${w/2+6*(i+1)}V${h/2+6*(i+1)}H${-w/2+6*(i+1)}Z`} fill="#E9DFC4" strokeWidth={6}/>)}
  <path d={`M${-w/2} ${-h/2}H${w/2}V${h/2}H${-w/2}Z`} fill={PAPER} strokeWidth={7}/>
  <g fill={color} stroke="none" fontFamily="Quiet Sans" fontWeight={800} textAnchor="middle">{lines.map((l,i)=><text key={i} x={0} y={-h/2+size*1.25+i*size*1.18} fontSize={size}>{l}</text>)}</g>
  {[0,1,2].map(i=><path key={i} d={`M${-w/2+40} ${-h/2+size*1.25+lines.length*size*1.18+i*28}H${w/2-40-(i%2)*50}`} fill="none" stroke="#B4A58C" strokeWidth={7}/>)}
 </g></svg>;
export const Rail:React.FC<{y:number}>=({y})=><svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d={`M-20 ${y}H1100V${y+40}H-20Z`} fill="#C5A06F"/><path d={`M-20 ${y+40}H1100V1940H-20Z`} fill="#80573F"/>{[90,330,570,810,1050].map(x=><path key={x} d={`M${x} ${y+60}V1900`} stroke="#684630" strokeWidth={14}/>)}</svg>;
export {INK,PAPER,GOLD,RED,TEAL};
