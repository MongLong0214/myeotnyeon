// Beast Clash v2 character rigs: original designs drawn in code (no third-party art). Each animal is a rig of parts
// (far limbs, tail, torso, near limbs, neck, head, jaw, eye, ear) posed by the same numeric pose P as Beasts.tsx.
// Look: thick consistent ink line, 2-tone cel shading (form shadow below/behind) plus a rim light on the top-back edge,
// anatomy cues (shoulder/haunch muscle arcs, fur tufts, skin folds, whisker pads), blinking eyes, breathing idle.
// Kinds without a v2 rig yet (jaguar, anaconda, badger, cobra) fall back to the Beasts.tsx drawing through <Animal>.
import React,{useId} from 'react';
import {Beast,headOf,P,Kind,INK} from './Beasts';

export type PX=P&{swipe?:number};
type Pt=[number,number];
type Tone={base:string;shade:string;rim:string};
const rad=(a:number)=>a*Math.PI/180;
const rot=(p:Pt,a:number):Pt=>[p[0]*Math.cos(rad(a))-p[1]*Math.sin(rad(a)),p[0]*Math.sin(rad(a))+p[1]*Math.cos(rad(a))];
const c01=(u:number)=>Math.max(0,Math.min(1,u));
const mix=(a:number,b:number,u:number)=>a+(b-a)*u;
const mixP=(a:Pt,b:Pt,u:number):Pt=>[mix(a[0],b[0],u),mix(a[1],b[1],u)];
const LW=10;
const R={strokeLinecap:'round' as const,strokeLinejoin:'round' as const};

// one cel-shaded part: ink outline, rim-light sliver on the top-back edge, base tone, form shadow at the bottom-back
const Part:React.FC<{d:string;tone:Tone;lw?:number;sh?:Pt;rim?:Pt;children?:React.ReactNode}>=({d,tone,lw=LW,sh=[14,-36],rim=[9,8],children})=>{
 const id=useId().replace(/:/g,'');
 return <g>
  <clipPath id={'c'+id}><path d={d}/></clipPath>
  <mask id={'m'+id} maskUnits="userSpaceOnUse" x={-1600} y={-1600} width={3200} height={3200}><rect x={-1600} y={-1600} width={3200} height={3200} fill="#fff"/><path d={d} transform={`translate(${sh[0]} ${sh[1]})`} fill="#000"/></mask>
  <path d={d} fill={INK} stroke={INK} strokeWidth={lw*2} {...R}/>
  <g clipPath={`url(#c${id})`}>
   <rect x={-1600} y={-1600} width={3200} height={3200} fill={tone.rim}/>
   <path d={d} transform={`translate(${rim[0]} ${rim[1]})`} fill={tone.base}/>
   <rect x={-1600} y={-1600} width={3200} height={3200} fill={tone.shade} mask={`url(#m${id})`}/>
   {children}
  </g>
 </g>;
};
const ik=(a:Pt,b:Pt,l1:number,l2:number,bend:number):Pt=>{let dx=b[0]-a[0],dy=b[1]-a[1];const n=Math.hypot(dx,dy)||1,d=Math.max(1,Math.min(n,l1+l2-1));const k=(l1*l1-l2*l2+d*d)/(2*d),h=Math.sqrt(Math.max(0,l1*l1-k*k));dx/=n;dy/=n;return [a[0]+dx*k-dy*h*bend,a[1]+dy*k+dx*h*bend];};

const Eye2:React.FC<{x:number;y:number;r:number;p:PX;t:number;iris:string;skin:string;look?:number}>=({x,y,r,p,t,iris,skin,look=.32})=>{
 const id=useId().replace(/:/g,''),blink=((t%83)+83)%83<3,lid=blink?1:c01(p.lid),an=p.brow,ry=r*1.1;
 const by=y-ry-r*.4-r*.5*p.browUp;
 const brow=<path d={`M${x-r*1.35} ${by-r*.5*an}Q${x} ${by-r*.15}${' '}${x+r*1.3} ${by+r*.6*an}`} fill="none" stroke={INK} strokeWidth={r*.52} {...R}/>;
 if(p.squeeze>.5)return <g>{brow}<path d={`M${x-r*.9} ${y-r*.7}L${x+r*.75} ${y}L${x-r*.9} ${y+r*.7}`} fill="none" stroke={INK} strokeWidth={r*.38} {...R}/></g>;
 const ly=y-ry+2*ry*lid-r*.12,yb=ly+r*.7*Math.max(0,-an)*(1-lid),yf=ly+r*.8*Math.max(0,an)*(1-lid);
 return <g>
  <clipPath id={id}><ellipse cx={x} cy={y} rx={r} ry={ry}/></clipPath>
  <ellipse cx={x} cy={y} rx={r} ry={ry} fill="#FFFDF4" stroke={INK} strokeWidth={r*.3}/>
  <g clipPath={`url(#${id})`}>
   <circle cx={x+r*look} cy={y+r*.12} r={r*.66*Math.max(.75,p.pupil)} fill={iris}/>
   <circle cx={x+r*look*1.15} cy={y+r*.12} r={r*.38*p.pupil} fill={INK}/>
   <circle cx={x+r*look-r*.22} cy={y-r*.22} r={r*.2} fill="#fff"/>
   <path d={`M${x-r*1.5} ${y-ry*1.8}H${x+r*1.5}V${yf}L${x-r*1.5} ${yb}Z`} fill={skin} stroke={INK} strokeWidth={r*.22}/>
  </g>
  <ellipse cx={x} cy={y} rx={r} ry={ry} fill="none" stroke={INK} strokeWidth={r*.3}/>
  {brow}
 </g>;
};
const Drop:React.FC<{x:number;y:number;t:number}>=({x,y,t})=>{const u=((t%22)+22)%22/22;return <path d={`M${x} ${y+50*u-24}q16 24 0 36q-16 -12 0 -36Z`} fill="#9FD8F0" stroke={INK} strokeWidth={5} opacity={1-u}/>;};

// ---------------- polar bear ----------------
const FUR:Tone={base:'#FBF4E2',shade:'#B4C4DA',rim:'#FFFFFF'},FURFAR:Tone={base:'#C3CCDA',shade:'#9AA8C0',rim:'#D5DCE6'};
const PB_HP:Pt=[-185,-245],PB_SH:Pt=[150,-250],PB_NB:Pt=[205,-350];
const polarXf=(p:PX,t:number)=>{
 const br=Math.sin(t*.13),ph=t*.85,s=p.stride,bob=-16*s*Math.abs(Math.sin(ph))+3*br*(1-s);
 const A=p.lean-p.rear*50+s*4*Math.sin(ph*2),hp:Pt=[PB_HP[0]+p.rear*40,PB_HP[1]+p.crouch*75+bob+p.rear*18];
 const T=(q:Pt):Pt=>{const r=rot([q[0]-PB_HP[0],q[1]-PB_HP[1]],A);return [hp[0]+r[0],hp[1]+r[1]];};
 return {A,hp,T,nb:T(PB_NB),ha:A*.5+p.head+2*br,ph,br,s};
};
const TORSO='M-285 -250C-292 -350 -210 -425 -110 -402C-40 -388 20 -392 80 -422C150 -458 250 -425 268 -335C276 -280 262 -215 232 -178l14 26l-30 -8l4 28l-32 -14C120 -112 60 -104 0 -106l-8 16l-22 -14l-10 16l-24 -16C-130 -108 -210 -118 -250 -150C-275 -175 -284 -210 -285 -250Z';
const SKULL='M-5 -95C30 -150 110 -160 160 -125C195 -100 235 -92 268 -72C292 -58 300 -30 288 -8C280 6 262 12 240 12L120 22C95 30 85 45 70 62l-14 -8l-6 20l-16 -14l-10 18C0 70 -40 40 -40 -10C-40 -50 -30 -75 -5 -95Z';
const NECK='M-150 40C-90 -90 -20 -130 60 -120L80 50C20 90 -60 130 -130 130Z';
const tq=(p:Pt,q:Pt,w0:number,w1:number,dx=0)=>{const n=Math.hypot(q[0]-p[0],q[1]-p[1])||1,nx=-(q[1]-p[1])/n,ny=(q[0]-p[0])/n;return `M${p[0]+nx*w0/2+dx} ${p[1]+ny*w0/2}L${q[0]+nx*w1/2+dx} ${q[1]+ny*w1/2}L${q[0]-nx*w1/2+dx} ${q[1]-ny*w1/2}L${p[0]-nx*w0/2+dx} ${p[1]-ny*w0/2}Z`;};
const PawLeg:React.FC<{a:Pt;f:Pt;l1:number;l2:number;bend:number;w1:number;w2:number;tone:Tone;air?:number;foot?:'paw'|'toe';nail?:string}>=({a,f,l1,l2,bend,w1,w2,tone,air=0,foot='paw',nail='#EDE6D6'})=>{
 const k=ik(a,f,l1,l2,bend),seg=(p:Pt,q:Pt,w:number,col:string,dx=0)=><path d={`M${p[0]+dx} ${p[1]}L${q[0]+dx} ${q[1]}`} stroke={col} strokeWidth={w} fill="none" {...R}/>;
 const w=w2,ang=Math.atan2(f[1]-k[1],f[0]-k[0])*180/Math.PI-90,pr=air*c01(Math.abs(ang)/60)*ang*.8+air*25;
 return <g>
  <path d={tq(a,k,w1*1.1,w1*.8)+tq(k,f,w2*.96,w2*.66)} fill={INK} stroke={INK} strokeWidth={LW*2} {...R}/><circle cx={k[0]} cy={k[1]} r={w1*.42+LW} fill={INK}/><circle cx={a[0]} cy={a[1]} r={w1*.55+LW} fill={INK}/>
  <path d={tq(a,k,w1*1.1,w1*.8)+tq(k,f,w2*.96,w2*.66)} fill={tone.shade}/><circle cx={k[0]} cy={k[1]} r={w1*.42} fill={tone.shade}/><circle cx={a[0]} cy={a[1]} r={w1*.55} fill={tone.shade}/>
  <path d={tq(a,k,w1*.78,w1*.54,w1*.13)+tq(k,f,w2*.66,w2*.44,w2*.11)} fill={tone.base}/><circle cx={k[0]+w1*.1} cy={k[1]} r={w1*.28} fill={tone.base}/><circle cx={a[0]+w1*.13} cy={a[1]} r={w1*.39} fill={tone.base}/>
  <path d={`M${k[0]-bend*w1*.34} ${k[1]-10}q${bend*w1*.1} ${12} ${bend*w1*.2} 18`} stroke={INK} strokeWidth={6} fill="none" {...R}/>
  {foot==='toe'?<g transform={`translate(${f[0]} ${f[1]}) rotate(${pr*.5})`}>
   <path d={`M${-w*.6} 38C${-w*.68} 4 ${-w*.4} -22 0 -22C${w*.46} -22 ${w*.74} 4 ${w*.7} 38Z`} fill={tone.base} stroke={INK} strokeWidth={LW} {...R}/>
   <path d={`M${-w*.52} 32H${w*.62}`} stroke={tone.shade} strokeWidth={9} {...R}/>
   {[.0,.28,.52].map((u,i)=><path key={i} d={`M${w*u-4} 38q${w*.1} -26 ${w*.2} 0Z`} fill={nail} stroke={INK} strokeWidth={5} {...R}/>)}
  </g>:<g transform={`translate(${f[0]} ${f[1]}) rotate(${pr})`}>
   {[.5,.8,1.08].map((u,i)=><path key={i} d={`M${w*u-8} ${24}l${20} ${14}l${-22} ${4}Z`} fill="#3B3340" stroke={INK} strokeWidth={5} {...R}/>)}
   <path d={`M${-w*.62} 40C${-w*.75} -6 ${-w*.3} -34 ${w*.2} -30C${w*.8} -26 ${w*1.2} 0 ${w*1.16} 26C${w*1.14} 38 ${w} 42 ${w*.8} 40Z`} fill={tone.base} stroke={INK} strokeWidth={LW} {...R}/>
   <path d={`M${-w*.55} 34H${w*1.05}`} stroke={tone.shade} strokeWidth={9} {...R}/>
   <path d={`M${w*.55} 6q10 14 2 28M${w*.86} 10q10 12 4 24`} stroke={INK} strokeWidth={5} fill="none" {...R}/>
  </g>}
 </g>;
};
const Polar:React.FC<{p:PX;t:number}>=({p,t})=>{
 const X=polarXf(p,t),{T,ph,s}=X,sh=T(PB_SH),hip=T([-185,-245]),r=c01(p.rear*1.5),sw=p.swipe??0;
 const gf=(bx:number,phase:number):Pt=>[bx+120*s*Math.cos(ph+phase),-40-80*s*Math.max(0,Math.sin(ph+phase))];
 const up=(o:Pt,deg:number):Pt=>[o[0]+205*Math.cos(rad(deg)),o[1]+205*Math.sin(rad(deg))];
 const shF:Pt=[sh[0]+55,sh[1]+4],hipF:Pt=[hip[0]+62,hip[1]+2],th=mix(-62,38,sw);
 const fN=mixP(gf(sh[0]+18,0),up(sh,th),r),fF=mixP(gf(shF[0]+22,2),up(shF,th-28),r);
 const hN=gf(hip[0]-14,3.3),hF=gf(hipF[0]+4,4.6);
 const tg=`translate(${X.hp[0]} ${X.hp[1]}) rotate(${X.A}) translate(${-PB_HP[0]} ${-PB_HP[1]})`,hg=`translate(${X.nb[0]} ${X.nb[1]}) rotate(${X.ha})`;
 const jaw=p.jaw*27,J:Pt=[105,22],jr=(q:Pt):Pt=>{const v=rot([q[0]-J[0],q[1]-J[1]],jaw);return [J[0]+v[0],J[1]+v[1]];},jl=jr([262,34]);
 const air=(f:Pt)=>c01((-40-f[1])/60);
 return <g>
  <PawLeg a={hipF} f={hF} l1={125} l2={120} bend={-1} w1={120} w2={88} tone={FURFAR} air={air(hF)}/>
  <PawLeg a={shF} f={fF} l1={120} l2={122} bend={1} w1={104} w2={84} tone={FURFAR} air={Math.max(air(fF),r)}/>
  <g transform={tg}><Part d="M-268 -335C-312 -345 -335 -300 -306 -268C-290 -252 -262 -262 -258 -290Z" tone={FUR} lw={8}/></g>
  <g transform={hg}><Part d={NECK} tone={FUR}/></g>
  <g transform={tg}><g transform={`translate(0 -106) scale(1 ${1+.014*X.br}) translate(0 106)`}><Part d={TORSO} tone={FUR}>
   <path d="M96 -432C56 -360 70 -280 132 -226M-92 -402C-44 -340 -56 -258 -118 -196" stroke="#93A7C2" strokeWidth={8} fill="none" {...R}/>
   <path d="M-20 -150l12 16l12 -16M40 -150l12 16l12 -16M-150 -168l12 14l12 -14M200 -250l14 14l8 -18M180 -300l14 12l8 -16" stroke="#93A7C2" strokeWidth={6} fill="none" {...R}/>
  </Part></g></g>
  <PawLeg a={hip} f={hN} l1={125} l2={120} bend={-1} w1={136} w2={94} tone={FUR} air={air(hN)}/>
  <PawLeg a={sh} f={fN} l1={120} l2={122} bend={1} w1={116} w2={90} tone={FUR} air={Math.max(air(fN),r)}/>
  <g transform={hg}>
   <circle cx={72} cy={-142} r={24} fill={FURFAR.base} stroke={INK} strokeWidth={LW}/>
   <path d={`M${J[0]} ${J[1]-6}L262 8L${jl[0]} ${jl[1]}Z`} fill="#5A1E2B" stroke={INK} strokeWidth={6} {...R}/>
   <g transform={`rotate(${jaw} ${J[0]} ${J[1]})`}>
    {p.jaw>.25&&<path d="M226 22l9 -24l10 24M196 24l7 -15l8 15" fill="#FFFDF4" stroke={INK} strokeWidth={5} {...R}/>}
    {p.jaw>.25&&<path d="M130 26Q190 6 240 24L236 40L134 46Z" fill="#F08A9B" stroke={INK} strokeWidth={5} {...R}/>}
    <path d="M98 16L250 18C272 20 270 42 250 46L132 58C104 58 90 36 98 16Z" fill={FUR.base} stroke={INK} strokeWidth={LW} {...R}/>
    <path d="M128 50L246 40" stroke={FUR.shade} strokeWidth={8} {...R}/>
    {p.tongue>.5&&<path d={`M214 40q-4 ${52+5*Math.sin(t*.8)} 18 ${52+5*Math.sin(t*.8)}q20 0 14 -54Z`} fill="#F08A9B" stroke={INK} strokeWidth={6} {...R}/>}
   </g>
   <g transform={`rotate(${-8+6*Math.sin(t*.07)} 28 -110)`}><circle cx={26} cy={-130} r={31} fill={FUR.base} stroke={INK} strokeWidth={LW}/><circle cx={30} cy={-126} r={15} fill="#56617A"/></g>
   <Part d={SKULL} tone={FUR} sh={[10,-30]}>
    <path d="M196 -84C176 -50 178 -12 204 14" stroke="#93A7C2" strokeWidth={7} fill="none" {...R}/>
    <path d="M40 -20l14 14l8 -18M10 10l14 14l8 -18" stroke="#93A7C2" strokeWidth={6} fill="none" {...R}/>
   </Part>
   {p.jaw>.25&&<path d="M246 10l8 26l10 -26M214 12l7 18l8 -18" fill="#FFFDF4" stroke={INK} strokeWidth={5} {...R}/>}
   {p.grit>.5&&p.jaw<.3&&<g><path d="M150 6L252 0Q262 14 250 26L152 34Q140 20 150 6Z" fill="#FFFDF4" stroke={INK} strokeWidth={7} {...R}/><path d="M176 6v26M202 4v26M228 2v26M150 20L256 13" stroke={INK} strokeWidth={4}/></g>}
   {p.smile>.5&&p.jaw<.3&&p.grit<.5&&<path d="M150 14Q200 34 250 6" fill="none" stroke={INK} strokeWidth={9} {...R}/>}
   {p.oh>.5&&<ellipse cx={236} cy={22} rx={15} ry={19} fill="#5A1E2B" stroke={INK} strokeWidth={6}/>}
   <path d="M262 -64C282 -70 304 -52 300 -30C296 -12 272 -10 262 -24C254 -36 252 -58 262 -64Z" fill={INK}/><ellipse cx={280} cy={-50} rx={9} ry={5} fill="#8E93A8"/>
   <Eye2 x={150} y={-86} r={23} p={p} t={t} iris="#5B3A21" skin={FUR.base}/>
   {p.sweat>.5&&<Drop x={60} y={-170} t={t}/>}
  </g>
 </g>;
};

// ---------------- walrus ----------------
const HIDE:Tone={base:'#B8714B',shade:'#7C4530',rim:'#F2B58C'},HIDEFAR:Tone={base:'#8A5038',shade:'#6A3A2A',rim:'#9C5E44'};
const PAD:Tone={base:'#EBC49E',shade:'#BF8D68',rim:'#FFE9CF'},IVORY:Tone={base:'#FFF6DC',shade:'#D6BE8C',rim:'#FFFFFF'};
const W_PV:Pt=[-150,-30],W_NK:Pt=[185,-395],W_SH:Pt=[150,-175];
const walrusXf=(p:PX,t:number)=>{
 const br=Math.sin(t*.11),s=p.stride,hop=s*Math.abs(Math.sin(t*.55));
 const A=p.lean*.6-p.rear*40+p.strike*26+hop*-7,o:Pt=[W_PV[0]+p.strike*70+p.rear*-10,W_PV[1]-hop*26];
 const T=(q:Pt):Pt=>{const r=rot([q[0]-W_PV[0],(q[1]-W_PV[1])*(1-.13*p.crouch)],A);return [o[0]+r[0],o[1]+r[1]];};
 return {A,o,T,nk:T(W_NK),ha:A*.2+p.head*.8+1.5*br+p.strike*24-p.rear*6,br,hop};
};
const WBODY='M-345 -40C-330 -160 -225 -262 -90 -305C0 -335 55 -395 85 -470C150 -520 255 -470 262 -380C308 -300 304 -185 252 -92C222 -40 150 -8 60 -5L-250 -5C-310 -5 -345 -15 -345 -40Z';
const WFLIP='M-52 -30C-74 30 -70 92 -42 130C-56 150 -44 178 -10 184L118 186C150 190 172 174 162 154C180 144 174 122 150 120C162 102 144 86 122 94C90 70 70 20 56 -38C28 -64 -30 -62 -52 -30Z';
const WHIND='M0 -34C-60 -70 -130 -62 -164 -22l22 6l-16 14l24 4l-12 16C-90 16 -40 8 0 -4Z';
const WHEAD='M-112 44C-140 -70 -72 -166 30 -170C112 -172 172 -122 180 -50C184 0 162 52 110 72C40 98 -66 94 -112 44Z';
const Walrus:React.FC<{p:PX;t:number}>=({p,t})=>{
 const X=walrusXf(p,t),sw=p.swipe??0,jw=p.jaw*34;
 const bg=`translate(${X.o[0]} ${X.o[1]}) rotate(${X.A}) scale(1 ${1-.13*p.crouch}) translate(${-W_PV[0]} ${-W_PV[1]})`,hg=`translate(${X.nk[0]} ${X.nk[1]}) rotate(${X.ha})`;
 const sh=X.T(W_SH),fa=-sw*105+p.rear*-12+X.hop*-30-X.A*.7,wig=7*Math.sin(t*.16);
 const tusk=(dx:number,dy:number,tone:Tone,k=1)=><g transform={`translate(${dx} ${dy})`}><Part d={`M84 56C80 ${150*k} 100 ${250*k} 140 ${306*k}C146 ${236*k} 144 ${140*k} 136 56Z`} tone={tone} lw={8} sh={[-12,-8]} rim={[5,0]}><path d={`M112 80C110 ${150*k} 118 ${220*k} 132 ${270*k}`} stroke={tone.shade} strokeWidth={5} fill="none" {...R}/></Part></g>;
 return <g>
  <g transform={`translate(${-338+X.o[0]-W_PV[0]} ${-22}) rotate(${-16+wig})`}><Part d={WHIND} tone={HIDEFAR} lw={8}/></g>
  <g transform={`translate(${-340+X.o[0]-W_PV[0]} ${-12}) rotate(${6-wig*.6})`}><Part d={WHIND} tone={HIDE} lw={8}><path d="M-40 -20L-140 -24M-40 -6L-130 4" stroke={HIDE.shade} strokeWidth={6} {...R}/></Part></g>
  <g transform={`translate(${sh[0]+92} ${sh[1]-12}) rotate(${fa*.8+8})`}><Part d={WFLIP} tone={HIDEFAR} lw={9}/></g>
  <g transform={bg}><g transform={`translate(0 -5) scale(${1+.01*X.br} ${1+.016*X.br}) translate(0 5)`}><Part d={WBODY} tone={HIDE} sh={[20,-44]}>
   <path d="M306 -330C270 -190 200 -60 30 -24L30 30L360 30Z" fill="#FFE3C4" opacity={.22}/>
   <path d="M62 -410C130 -352 215 -338 286 -352M36 -338C120 -276 214 -262 300 -276M-205 -205C-120 -148 -40 -150 22 -182M-290 -70C-250 -100 -200 -108 -160 -100" stroke="#64331F" strokeWidth={8} fill="none" opacity={.75} {...R}/>
   <path d="M-60 -250q14 10 30 2M-130 -180q12 10 26 4M110 -120q16 10 30 0M40 -230q12 8 26 0" stroke="#D99A70" strokeWidth={8} fill="none" {...R}/>
  </Part></g></g>
  <g transform={`translate(${sh[0]} ${sh[1]}) rotate(${fa})`}><Part d={WFLIP} tone={HIDE} lw={9} sh={[16,-20]}><path d="M70 150L138 150M64 128L120 124" stroke={HIDE.shade} strokeWidth={6} {...R}/><path d="M-20 0C-28 50 -16 100 -4 140" stroke="#64331F" strokeWidth={6} fill="none" opacity={.6} {...R}/></Part></g>
  <g transform={hg}>
   <Part d={WHEAD} tone={HIDE} sh={[12,-34]}>
    <path d="M-96 -40C-70 -10 -66 30 -84 62M-60 -92C-36 -60 -30 -20 -44 20" stroke="#64331F" strokeWidth={8} fill="none" opacity={.7} {...R}/>
   </Part>
   <ellipse cx={176} cy={18} rx={52} ry={54} fill={PAD.shade} stroke={INK} strokeWidth={LW}/>
   {tusk(60,-8,{base:'#E6D4A8',shade:'#C4AB78',rim:'#F2E6C6'},.93)}
   <g transform={`translate(0 ${jw})`}><path d="M62 70C70 122 168 128 190 72Z" fill={HIDE.shade} stroke={INK} strokeWidth={LW} {...R}/>{p.tongue>.5&&<path d={`M112 100q-2 ${44+4*Math.sin(t*.8)} 16 ${44+4*Math.sin(t*.8)}q18 0 14 -46Z`} fill="#F08A9B" stroke={INK} strokeWidth={6} {...R}/>}</g>
   <ellipse cx={128} cy={76+jw*.5} rx={40} ry={8+jw*.55} fill="#4C1622" stroke={INK} strokeWidth={6}/>
   {p.jaw>.3&&<ellipse cx={128} cy={84+jw*.8} rx={24} ry={jw*.22} fill="#F08A9B"/>}
   {tusk(0,0,IVORY)}
   <Part d="M30 25A84 66 0 1 1 198 25A84 66 0 1 1 30 25Z" tone={PAD} sh={[8,-26]} rim={[7,6]}>
    {[0,1,2].map(i=>[0,1,2,3,4].map(j=><circle key={i*9+j} cx={70+j*24+i*6} cy={8+i*22} r={5} fill="#8A5A3C"/>))}
   </Part>
   {[0,1,2,3,4,5,6].map(i=>{const a=rad(100-i*17),x=114+84*Math.cos(a),y=25+66*Math.sin(a),l=30+(i%2)*10;return <g key={i}><path d={`M${x} ${y}l${l*Math.cos(a-.25)} ${l*Math.sin(a-.25)}`} stroke={INK} strokeWidth={11} {...R}/><path d={`M${x} ${y}l${l*Math.cos(a-.25)} ${l*Math.sin(a-.25)}`} stroke="#FFF3D6" strokeWidth={5} {...R}/></g>;})}
   <path d="M132 -50C150 -62 186 -56 192 -40C188 -26 150 -24 134 -34Z" fill="#3B2622" stroke={INK} strokeWidth={6} {...R}/>
   <Eye2 x={84} y={-88} r={19} p={p} t={t+31} iris="#3A2416" skin={HIDE.base} look={.4}/>
   {p.smile>.5&&p.jaw<.3&&<path d="M96 84Q130 104 168 80" fill="none" stroke={INK} strokeWidth={8} {...R}/>}
   {p.sweat>.5&&<Drop x={-30} y={-180} t={t}/>}
  </g>
 </g>;
};

// ---------------- swimmers: orca, great white shark ----------------
type SwimC={dark:Tone;white:Tone;body:string;jaw:string;jp:Pt;belly:string;dorsal:string;pect:string;pectAt:Pt;tail:string;tp:Pt;eye:Pt;er:number;iris:string;head:Pt;extra:(t:number)=>React.ReactNode;teeth:number;fins?:string};
const ORCA_T:Tone={base:'#2A3042',shade:'#141724',rim:'#6E82A8'},WHITE_T:Tone={base:'#F6F8FA',shade:'#B4C3D6',rim:'#FFFFFF'},SHARK_T:Tone={base:'#7E91A6',shade:'#4E6076',rim:'#B9C8D8'};
const SWIM:Record<'orca'|'shark',SwimC>={
 orca:{dark:ORCA_T,white:WHITE_T,body:'M430 -290C400 -360 300 -420 150 -440C0 -455 -200 -420 -330 -340L-360 -322L-360 -282C-250 -230 -100 -170 60 -165C150 -162 220 -200 250 -262Z',
  jaw:'M170 -196L250 -268L425 -286C438 -262 402 -226 350 -214C290 -200 215 -182 170 -196Z',jp:[250,-266],belly:'M450 -252C300 -252 200 -236 100 -216C0 -200 -150 -216 -265 -272L-265 -100L450 -100Z',
  dorsal:'M-80 -428C-56 -560 -24 -650 14 -690C30 -610 62 -505 96 -434Z',pect:'M0 0C60 26 96 110 70 214C56 236 22 232 2 204C-34 150 -62 70 -56 22C-50 0 -22 -8 0 0Z',pectAt:[150,-205],
  tail:'M10 -44C-70 -30 -130 -16 -165 -10C-200 -78 -258 -104 -300 -98C-280 -62 -270 -30 -258 2C-270 34 -282 66 -302 102C-258 104 -200 76 -165 12C-120 18 -60 30 10 40Z',tp:[-330,-305],
  eye:[322,-298],er:15,iris:'#3A2A1E',head:[310,-320],teeth:7,
  extra:()=><><ellipse cx={258} cy={-338} rx={56} ry={22} fill="#F6F8FA" transform="rotate(-14 258 -338)"/><path d="M-70 -446C-116 -404 -186 -384 -250 -390C-205 -414 -150 -434 -70 -449Z" fill="#8792A8"/></>},
 shark:{dark:SHARK_T,white:WHITE_T,body:'M446 -312C380 -372 250 -422 100 -432C-50 -438 -220 -392 -340 -332L-340 -288C-220 -250 -80 -190 60 -185C150 -182 230 -200 270 -246L404 -282C428 -290 446 -300 446 -312Z',
  jaw:'M190 -196L268 -250L396 -278C400 -256 372 -230 330 -220C280 -210 228 -190 190 -196Z',jp:[268,-250],belly:'M460 -300C350 -290 250 -262 150 -250C0 -236 -200 -262 -350 -312L-350 -100L460 -100Z',
  dorsal:'M-46 -424C-16 -520 16 -584 58 -616C60 -542 80 -470 112 -428Z',pect:'M0 0C-20 70 -80 150 -156 194C-156 122 -114 50 -72 0Z',pectAt:[130,-212],
  tail:'M10 -28L-60 -12C-90 -80 -130 -150 -196 -196C-174 -122 -162 -60 -152 0C-162 50 -184 92 -216 124C-152 102 -90 60 -60 12L10 28Z',tp:[-330,-310],
  eye:[336,-326],er:14,iris:'#10131A',head:[320,-320],teeth:9,fins:'M-250 -372C-240 -400 -222 -414 -204 -420C-204 -398 -196 -380 -186 -368ZM-230 -262C-226 -236 -208 -222 -186 -216C-190 -236 -184 -252 -176 -262Z',
  extra:()=><path d="M150 -338q-16 34 0 68M176 -340q-16 34 0 68M202 -340q-16 32 0 64M228 -338q-14 28 0 58M252 -334q-12 24 0 50" stroke="#3E4E62" strokeWidth={6} fill="none" {...R}/>},
};
const swimXf=(k:'orca'|'shark',p:PX,t:number)=>{const s=p.stride,A=p.lean*.8-p.rear*36+p.strike*12+p.head*.25+3*Math.sin(t*.1),o:Pt=[p.strike*70,-p.rear*90+p.crouch*40+10*Math.sin(t*.08)];
 const T=(q:Pt):Pt=>{const r=rot([q[0],q[1]+300],A);return [o[0]+r[0],o[1]+r[1]-300];};return {A,o,T,beat:(9+20*s)*Math.sin(t*(.22+.5*s))};};
const Swimmer:React.FC<{k:'orca'|'shark';p:PX;t:number}>=({k,p,t})=>{
 const C=SWIM[k],X=swimXf(k,p,t),jw=p.jaw*(k==='orca'?24:30)+(p.grit>.5?6:0),open=jw>5,fl=14*Math.sin(t*.12);
 const teeth=(y0:number,dir:number,x0:number,x1:number)=>Array.from({length:C.teeth}).map((_,i)=>{const x=x0+(x1-x0)*i/(C.teeth-1),y=y0-(x-x0)*.115;return <path key={i} d={`M${x-9} ${y}l9 ${dir*20}l9 ${-dir*20}Z`} fill="#FFFDF4" stroke={INK} strokeWidth={4} {...R}/>;});
 return <g transform={`translate(${X.o[0]} ${X.o[1]-300}) rotate(${X.A}) scale(1 ${1-.1*p.crouch}) translate(0 300)`}>
  {k==='shark'&&<g transform={`translate(${C.pectAt[0]+70} ${C.pectAt[1]-10}) rotate(${-10-fl})`}><Part d={C.pect} tone={{base:C.dark.shade,shade:C.dark.shade,rim:C.dark.shade}} lw={8}/></g>}
  <g transform={`translate(${C.tp[0]} ${C.tp[1]}) rotate(${X.beat}) scale(${1-.12*Math.abs(Math.sin(t*.3))*p.stride} 1)`}><Part d={C.tail} tone={C.dark} sh={[10,-22]}/></g>
  <Part d={C.dorsal} tone={C.dark} sh={[16,-10]}/>{C.fins&&<path d={C.fins} fill={C.dark.shade} stroke={INK} strokeWidth={8} {...R}/>}
  {open&&<path d={`M${C.jp[0]-10} ${C.jp[1]}L${C.jp[0]+160} ${C.jp[1]-18}L${C.jp[0]+150} ${C.jp[1]+jw*2.6}Z`} fill="#5A1E2B" stroke={INK} strokeWidth={6} {...R}/>}
  <g transform={`rotate(${jw} ${C.jp[0]} ${C.jp[1]})`}>{open&&teeth(C.jp[1]-2,-1,C.jp[0]+24,C.jp[0]+150)}<Part d={C.jaw} tone={C.white} sh={[8,-18]}>{open&&p.jaw>.5&&<path d={`M${C.jp[0]+10} ${C.jp[1]+6}l120 -12l-10 22l-90 12Z`} fill="#F08A9B"/>}</Part></g>
  <Part d={C.body} tone={C.dark} sh={[18,-52]}><path d={C.belly} fill={C.white.base}/><path d={C.belly} fill={C.white.shade} transform="translate(0 62)"/>{C.extra(t)}</Part>
  {open&&teeth(C.jp[1],1,C.jp[0]+24,C.jp[0]+156)}
  <g transform={`translate(${C.pectAt[0]} ${C.pectAt[1]}) rotate(${(k==='orca'?44:12)+fl+p.stride*10})`}><Part d={C.pect} tone={C.dark} lw={9} sh={[12,-16]}/></g>
  <Eye2 x={C.eye[0]} y={C.eye[1]} r={C.er} p={p} t={t} iris={C.iris} skin={C.dark.base} look={.3}/>
  {p.smile>.5&&!open&&<path d={`M${C.jp[0]+10} ${C.jp[1]+2}q60 16 120 -16`} fill="none" stroke={INK} strokeWidth={7} {...R}/>}
  {p.sweat>.5&&<Drop x={C.eye[0]-80} y={C.eye[1]-90} t={t}/>}
 </g>;
};

// ---------------- generic heavy quadruped: elephant, rhino, hippo, crocodile ----------------
type QK='elephant'|'rhino'|'hippo'|'croc';
type QC={legUp?:number;tone:Tone;far:Tone;HP:Pt;SH:Pt;NB:Pt;torso:string;lf:[number,number,number,number];lh:[number,number,number,number];ankle:number;step:number;lift:number;gait:number;rearA:number;crouchY:number;head0:number;foot:'paw'|'toe';head:Pt;
 kids:React.ReactNode;back:(p:PX,t:number)=>React.ReactNode;face:(p:PX,t:number)=>React.ReactNode};
const EL:Tone={base:'#A3A8B8',shade:'#6E7389',rim:'#D3D8E2'},ELF:Tone={base:'#7C8196',shade:'#62677B',rim:'#8A8FA3'};
const RH:Tone={base:'#B3ADA2',shade:'#7C766D',rim:'#DCD8CF'},RHF:Tone={base:'#8C867C',shade:'#6F6A62',rim:'#989288'};
const HI:Tone={base:'#A8879A',shade:'#735A6C',rim:'#D2BBCB'},HIF:Tone={base:'#836878',shade:'#684F5F',rim:'#8F7484'};
const CR:Tone={base:'#74924C',shade:'#4B6534',rim:'#B0C980'},CRF:Tone={base:'#587339',shade:'#43592B',rim:'#63803F'},HORN:Tone={base:'#EFE6CC',shade:'#C2B48C',rim:'#FFFFFF'};
const fold=(d:string,c:string)=><path d={d} stroke={c} strokeWidth={8} fill="none" opacity={.8} {...R}/>;
const QUAD:Record<QK,QC>={
 elephant:{legUp:.5,tone:EL,far:ELF,HP:[-200,-300],SH:[170,-290],NB:[250,-470],lf:[150,140,118,108],lh:[150,140,132,112],ankle:36,step:90,lift:50,gait:.55,rearA:26,crouchY:50,head0:0,foot:'toe',head:[100,-40],
  torso:'M-330 -330C-340 -470 -230 -572 -80 -562C40 -556 150 -592 240 -542C312 -500 312 -380 282 -300C250 -240 150 -224 40 -228C-100 -232 -220 -218 -290 -250C-320 -270 -330 -300 -330 -330Z',
  kids:<>{fold('M120 -560C80 -480 90 -360 150 -270M-120 -556C-70 -470 -80 -350 -150 -262M-10 -250q20 14 44 0M-240 -420q16 12 34 2M60 -420q16 12 34 2','#5C6177')}</>,
  back:(p,t)=><g><path d={`M-326 -420C-370 -380 -372 -300 -356 -${230+10*Math.sin(t*.1)}`} stroke={INK} strokeWidth={30} fill="none" {...R}/><path d={`M-326 -420C-370 -380 -372 -300 -356 -${230+10*Math.sin(t*.1)}`} stroke={EL.base} strokeWidth={12} fill="none" {...R}/><path d="M-372 -240l8 46l14 -40l12 38l4 -44Z" fill="#3B3340" stroke={INK} strokeWidth={6} {...R}/></g>,
  face:(p,t)=>{const r=Math.max(p.jaw,p.rear*.7),sw=10*Math.sin(t*.09),tx=(u:number):Pt=>[150+40*u+(120+60*u)*r*u+sw*u*u,40+300*u-(430*u*u+40*u)*r],pts=[0,.34,.67,1].map(tx),d=`M${pts[0][0]} ${pts[0][1]}C${pts[1][0]} ${pts[1][1]} ${pts[2][0]} ${pts[2][1]} ${pts[3][0]} ${pts[3][1]}`,fl=8*Math.sin(t*.1)+18*r;
   const tusk=(dx:number,tn:Tone)=><g transform={`translate(${dx} 0)`}><Part d="M92 58C120 130 200 170 300 132C230 136 170 96 140 40Z" tone={tn} lw={8} sh={[0,-14]} rim={[2,6]}/></g>;
   return <g>{tusk(46,{base:'#D9CDA6',shade:'#BBAA7C',rim:'#E5DBBB'})}
    <path d={d} stroke={INK} strokeWidth={92} fill="none" {...R}/><path d={d} stroke={EL.shade} strokeWidth={72} fill="none" {...R}/><path d={d} stroke={EL.base} strokeWidth={50} fill="none" transform="translate(10 -6)" {...R}/>
    {[.3,.45,.6,.75,.9].map(u=>{const q=tx(u);return <path key={u} d={`M${q[0]-26} ${q[1]}q26 12 52 0`} stroke="#5C6177" strokeWidth={6} fill="none" {...R}/>;})}
    <Part d="M-70 -134C20 -196 132 -176 172 -92C202 -30 192 52 140 82C80 112 -20 102 -72 40C-102 -20 -102 -92 -70 -134Z" tone={EL} sh={[12,-34]}>{fold('M40 -150C70 -120 70 -90 50 -70M130 20q20 20 10 46','#5C6177')}</Part>
    {p.jaw>.3&&<path d="M96 84q34 60 70 -6Z" fill="#5A1E2B" stroke={INK} strokeWidth={6} {...R}/>}
    {tusk(0,HORN)}
    <g transform={`rotate(${fl} -20 -90)`}><Part d="M-10 -150C-140 -214 -262 -110 -244 30C-228 140 -128 186 -52 116C-12 60 0 -50 -10 -150Z" tone={EL} sh={[14,-30]}><path d="M-30 -110C-130 -150 -210 -70 -200 20C-190 100 -120 130 -70 86" stroke="#C08C96" strokeWidth={12} fill="none" opacity={.55} {...R}/></Part></g>
    <Eye2 x={104} y={-44} r={16} p={p} t={t} iris="#4A3020" skin={EL.base}/>{p.sweat>.5&&<Drop x={20} y={-200} t={t}/>}
   </g>;}},
 rhino:{legUp:.3,tone:RH,far:RHF,HP:[-190,-215],SH:[150,-225],NB:[225,-335],lf:[112,108,108,92],lh:[112,108,122,96],ankle:34,step:100,lift:60,gait:.75,rearA:14,crouchY:50,head0:14,foot:'toe',head:[150,-20],
  torso:'M-300 -260C-310 -380 -220 -440 -100 -430C-20 -425 60 -472 150 -452C232 -432 272 -360 262 -280C250 -200 160 -170 40 -172C-90 -175 -200 -165 -260 -190C-290 -210 -300 -235 -300 -260Z',
  kids:<>{fold('M96 -456C56 -380 66 -270 120 -200M-110 -428C-66 -360 -76 -260 -134 -196M-40 -300q22 12 46 0M190 -330q16 14 6 40','#666058')}</>,
  back:(p,t)=><g><path d={`M-298 -300C-336 -280 -338 -230 -${326+6*Math.sin(t*.12)} -180`} stroke={INK} strokeWidth={26} fill="none" {...R}/><path d={`M-298 -300C-336 -280 -338 -230 -${326+6*Math.sin(t*.12)} -180`} stroke={RH.base} strokeWidth={10} fill="none" {...R}/></g>,
  face:(p,t)=>{const jw=p.jaw*20;return <g>
    <g transform={`rotate(${-12+8*Math.sin(t*.08)} 0 -90)`}><path d="M-24 -88C-50 -150 -20 -176 6 -150C20 -128 14 -100 -2 -84Z" fill={RH.base} stroke={INK} strokeWidth={LW} {...R}/><path d="M-12 -100C-28 -136 -12 -150 0 -138" stroke="#8E6E6E" strokeWidth={8} fill="none" {...R}/></g>
    <g transform={`rotate(${jw} 90 88)`}><path d="M86 84L250 90C264 102 258 124 236 126L112 122C84 114 76 98 86 84Z" fill={RH.base} stroke={INK} strokeWidth={LW} {...R}/><path d="M110 116L240 118" stroke={RH.shade} strokeWidth={8} {...R}/></g>
    {p.jaw>.3&&<path d={`M90 86L250 88L${244} ${96+jw*2.2}Z`} fill="#5A1E2B" stroke={INK} strokeWidth={6} {...R}/>}
    <Part d="M150 -76C162 -122 182 -152 208 -164C200 -126 202 -96 204 -62Z" tone={HORN} lw={8} sh={[8,-6]} rim={[4,2]}/>
    <Part d="M214 -50C228 -136 270 -200 326 -226C304 -154 298 -92 292 -18Z" tone={HORN} lw={9} sh={[12,-6]} rim={[5,2]}><path d="M236 -70q30 10 56 4M246 -110q24 8 44 2" stroke={HORN.shade} strokeWidth={5} fill="none"/></Part>
    <Part d="M-50 -90C20 -130 120 -112 190 -72C250 -42 292 -12 302 40C306 76 282 96 240 96L80 90C10 85 -50 50 -70 -10C-76 -50 -70 -75 -50 -90Z" tone={RH} sh={[10,-30]}>{fold('M40 -112C66 -70 60 -20 30 20M170 -76C150 -40 150 0 170 40','#666058')}</Part>
    <ellipse cx={270} cy={44} rx={12} ry={8} fill={INK}/>
    {p.grit>.5&&p.jaw<.3&&<path d="M150 92H244" stroke={INK} strokeWidth={9} {...R}/>}
    <Eye2 x={112} y={-40} r={15} p={p} t={t} iris="#4A3020" skin={RH.base}/>{p.sweat>.5&&<Drop x={10} y={-170} t={t}/>}
   </g>;}},
 hippo:{legUp:.3,tone:HI,far:HIF,HP:[-200,-175],SH:[170,-180],NB:[225,-315],lf:[88,84,112,98],lh:[88,84,124,102],ankle:34,step:80,lift:44,gait:.7,rearA:12,crouchY:36,head0:4,foot:'toe',head:[130,-30],
  torso:'M-310 -230C-320 -360 -210 -420 -60 -415C60 -412 180 -420 250 -370C292 -330 292 -230 252 -170C200 -130 60 -120 -80 -122C-200 -124 -290 -150 -310 -230Z',
  kids:<><path d="M300 -210C200 -150 0 -140 -320 -170L-320 -90L300 -90Z" fill="#E2B0AC" opacity={.6}/>{fold('M110 -416C76 -350 84 -250 130 -180M-130 -412C-86 -350 -94 -250 -150 -176M-20 -160q22 12 46 0','#5E4758')}</>,
  back:(p,t)=><path d={`M-306 -290q-36 14 -${34+8*Math.sin(t*.2)} 60`} stroke={INK} strokeWidth={24} fill="none" {...R}/>,
  face:(p,t)=>{const jw=p.jaw*40+(p.grit>.5?4:0),open=jw>8;return <g>
    {open&&<path d={`M10 46L290 30L${286} ${60+jw*3.4}L40 ${90+jw}Z`} fill="#8E3346" stroke={INK} strokeWidth={6} {...R}/>}
    <g transform={`rotate(${jw} 16 52)`}>
     {open&&<><path d="M236 40l14 -78l22 78ZM196 42l8 -34l12 34Z" fill="#FFFDF4" stroke={INK} strokeWidth={6} {...R}/><path d="M60 58Q170 30 262 48L250 80L70 92Z" fill="#F08A9B" stroke={INK} strokeWidth={5} {...R}/></>}
     <Part d="M24 38L282 32C314 50 316 102 282 120L80 130C20 126 -4 80 24 38Z" tone={{base:'#C39BA8',shade:'#8E6A7A',rim:'#E6CBD4'}} sh={[8,-22]}/></g>
    <g transform={`rotate(${-10+10*Math.sin(t*.1)} 0 -110)`}><path d="M-16 -100C-34 -146 -8 -160 10 -140C20 -124 16 -108 6 -96Z" fill={HI.base} stroke={INK} strokeWidth={LW} {...R}/></g>
    <Part d="M-70 -80C-30 -112 20 -150 70 -128C100 -116 104 -104 120 -100C160 -112 236 -116 272 -82C312 -40 312 20 282 38L40 46C-30 42 -80 12 -90 -28C-92 -55 -85 -70 -70 -80Z" tone={HI} sh={[10,-32]}>{fold('M120 -100C100 -60 104 -10 130 30M210 -96q-10 40 6 80','#5E4758')}</Part>
    {open&&<path d="M250 38l10 44l14 -44ZM214 40l7 22l9 -22Z" fill="#FFFDF4" stroke={INK} strokeWidth={5} {...R}/>}
    <ellipse cx={262} cy={-66} rx={13} ry={8} fill={INK} transform="rotate(-20 262 -66)"/>
    {[0,1,2].map(i=><circle key={i} cx={200+i*24} cy={0+i%2*14} r={4} fill="#5E4758"/>)}
    <Eye2 x={62} y={-98} r={17} p={p} t={t} iris="#4A3020" skin={HI.base}/>{p.sweat>.5&&<Drop x={-20} y={-170} t={t}/>}
   </g>;}},
 croc:{tone:CR,far:CRF,HP:[-170,-88],SH:[150,-92],NB:[215,-118],lf:[52,50,58,46],lh:[56,52,66,50],ankle:24,step:70,lift:30,gait:.9,rearA:32,crouchY:16,head0:0,foot:'paw',head:[120,-20],
  torso:'M-240 -92C-228 -166 -100 -196 20 -190C120 -186 206 -172 250 -140C262 -100 236 -58 184 -48C60 -34 -100 -34 -206 -48C-232 -58 -242 -74 -240 -92Z',
  kids:<><path d="M270 -96C100 -70 -100 -70 -250 -86L-250 -20L270 -20Z" fill="#DDD79C"/>{[-180,-120,-60,0,60,120,180].map(x=><path key={x} d={`M${x} -150q14 -20 30 0M${x+16} -112q14 -18 28 0`} stroke={CR.shade} strokeWidth={7} fill="none" {...R}/>)}</>,
  back:(p,t)=>{const sw=14*Math.sin(t*.14)+10*p.stride*Math.sin(t*.7);return <g>
    <g transform={`translate(-215 -96) rotate(${sw})`}><Part d="M30 -60C-100 -72 -230 -50 -360 14C-240 34 -110 44 30 34Z" tone={CR} sh={[10,-22]}><path d="M40 0C-100 6 -230 20 -350 20L-350 60L40 60Z" fill="#DDD79C"/></Part>
     <path d={Array.from({length:8}).map((_,i)=>`M${-10-i*40} ${-64+i*8}l-16 -${26-i*2}l-18 ${28-i*2}`).join('')} fill={CR.base} stroke={INK} strokeWidth={7} {...R}/></g>
    <path d={Array.from({length:10}).map((_,i)=>`M${-210+i*42} -${176+10*Math.sin(i*.34)}l18 -30l20 30`).join('')} fill={CR.base} stroke={INK} strokeWidth={8} {...R}/></g>;},
  face:(p,t)=>{const jw=p.jaw*30+(p.grit>.5?5:0),open=jw>4,zig=(y:number,d:number)=>Array.from({length:9}).map((_,i)=>`M${44+i*24} ${y-i*.9}l8 ${d*15}l8 ${-d*15}Z`).join('');return <g>
    {open&&<path d={`M0 6L262 -2L${252} ${14+jw*4.2}Z`} fill="#8E3346" stroke={INK} strokeWidth={6} {...R}/>}
    <g transform={`rotate(${jw} -6 8)`}>{open&&<path d={zig(6,-1)} fill="#FFFDF4" stroke={INK} strokeWidth={4} {...R}/>}
     <Part d="M-10 2L262 -4C276 8 266 28 244 30L30 48C-14 48 -30 20 -10 2Z" tone={{base:'#DDD79C',shade:'#A9A468',rim:'#F2EEC4'}} lw={9} sh={[6,-14]}/></g>
    <Part d="M-44 -50C-20 -70 10 -72 30 -76C44 -100 84 -104 100 -74C150 -56 220 -44 258 -42C286 -40 292 -10 270 0L20 8C-30 8 -54 -20 -44 -50Z" tone={CR} lw={9} sh={[8,-20]}>{[120,150,180,210].map(x=><path key={x} d={`M${x} -40q10 -12 22 0`} stroke={CR.shade} strokeWidth={6} fill="none" {...R}/>)}</Part>
    <path d={zig(2,1)} fill="#FFFDF4" stroke={INK} strokeWidth={4} {...R}/>
    <ellipse cx={262} cy={-34} rx={9} ry={6} fill={INK}/>
    <Eye2 x={66} y={-70} r={15} p={{...p,pupil:p.pupil*.7}} t={t} iris="#D9C63A" skin={CR.base}/>{p.sweat>.5&&<Drop x={-10} y={-130} t={t}/>}
   </g>;}},
};
const quadXf=(k:QK,p:PX,t:number)=>{const q=QUAD[k],br=Math.sin(t*.12),ph=t*q.gait,s=p.stride,bob=-12*s*Math.abs(Math.sin(ph))+3*br*(1-s);
 const A=p.lean*.6-p.rear*q.rearA+s*3*Math.sin(ph*2),hp:Pt=[q.HP[0]+p.rear*24+p.strike*50,q.HP[1]+p.crouch*q.crouchY+bob];
 const T=(v:Pt):Pt=>{const r=rot([v[0]-q.HP[0],v[1]-q.HP[1]],A);return [hp[0]+r[0],hp[1]+r[1]];};
 return {q,A,hp,T,nb:T(q.NB),ha:A*.4+p.head*.6+2*br+q.head0+p.strike*-14,ph,br,s};};
const Quadruped:React.FC<{k:QK;p:PX;t:number}>=({k,p,t})=>{
 const X=quadXf(k,p,t),{q,T,ph,s}=X,sh=T(q.SH),hip=T(q.HP),r=Math.min(1,p.rear*1.4),sw=p.swipe??0,fl=q.lf[0]+q.lf[1]-12;
 const gf=(bx:number,phase:number):Pt=>[bx+q.step*s*Math.cos(ph+phase),-q.ankle-q.lift*s*Math.max(0,Math.sin(ph+phase))];
 const up=(o:Pt,deg:number):Pt=>[o[0]+fl*Math.cos(rad(deg)),o[1]+fl*Math.sin(rad(deg))];
 const dxF=q.lf[2]*.5,shF:Pt=[sh[0]+dxF,sh[1]+2],hipF:Pt=[hip[0]+dxF,hip[1]+2],th=mix(40,66,sw)-(1-r)*0;
 const rest=q.SH[0]+12,fN=mixP(gf(rest+(sh[0]-q.SH[0])*.5,0),up(sh,th),r*(q.legUp??1)),fF=mixP(gf(rest+dxF+(sh[0]-q.SH[0])*.5,2),up(shF,th-22),r*(q.legUp??1)),hN=gf(hip[0]-8,3.3),hF=gf(hipF[0],4.6);
 const tg=`translate(${X.hp[0]} ${X.hp[1]}) rotate(${X.A}) translate(${-q.HP[0]} ${-q.HP[1]})`,hg=`translate(${X.nb[0]} ${X.nb[1]}) rotate(${X.ha})`,air=(f:Pt)=>Math.max(0,Math.min(1,(-q.ankle-f[1])/50));
 const leg=(a:Pt,f:Pt,L:[number,number,number,number],bend:number,tone:Tone,k2=1)=><PawLeg a={a} f={f} l1={L[0]} l2={L[1]} bend={bend} w1={L[2]*k2} w2={L[3]*k2} tone={tone} air={air(f)} foot={q.foot}/>;
 return <g>
  {leg(hipF,hF,q.lh,-1,q.far,.92)}{leg(shF,fF,q.lf,1,q.far,.92)}
  <g transform={tg}>{q.back(p,t)}<g transform={`scale(1 ${1+.012*X.br})`}><Part d={q.torso} tone={q.tone} sh={[16,-44]}>{q.kids}</Part></g></g>
  {leg(hip,hN,q.lh,-1,q.tone)}{leg(sh,fN,q.lf,1,q.tone)}
  <g transform={hg}>{q.face(p,t)}</g>
 </g>;
};

// ---------------- registry ----------------
// geometry in local units at s=1, facing right: sc = scale in wide shots, reach = snout tip, back = rear extent, top = standing height
type Geo={sc:number;reach:number;back:number;top:number;head:Pt;cx:number;off:number};
export const GEO:Record<Kind,Geo>={
 polar:{sc:.8,reach:505,back:310,top:470,head:[355,-430],cx:40,off:0},
 walrus:{sc:.84,reach:390,back:500,top:570,head:[235,-450],cx:-20,off:0},
 jaguar:{sc:.95,reach:390,back:330,top:430,head:[290,-360],cx:60,off:0},
 anaconda:{sc:1,reach:390,back:330,top:420,head:[290,-330],cx:0,off:230},
 badger:{sc:1.25,reach:310,back:250,top:270,head:[230,-200],cx:50,off:0},
 cobra:{sc:.95,reach:360,back:330,top:560,head:[290,-470],cx:0,off:230},
 orca:{sc:.74,reach:432,back:630,top:690,head:[310,-320],cx:-60,off:0},
 shark:{sc:.74,reach:446,back:545,top:616,head:[320,-320],cx:-40,off:0},
 elephant:{sc:.66,reach:555,back:375,top:640,head:[350,-510],cx:0,off:0},
 rhino:{sc:.7,reach:540,back:340,top:470,head:[375,-355],cx:0,off:0},
 hippo:{sc:.76,reach:530,back:345,top:450,head:[355,-345],cx:0,off:0},
 croc:{sc:.78,reach:485,back:580,top:250,head:[335,-138],cx:-40,off:0},
};
export const HAS_RIG:Partial<Record<Kind,boolean>>={polar:true,walrus:true,orca:true,shark:true,elephant:true,rhino:true,hippo:true,croc:true};
// head centre in local units for a pose (camera targets, effects)
export const headPos=(kind:Kind,p:PX,t:number):Pt=>{
 if(kind==='polar'){const X=polarXf(p,t),v=rot([150,-70],X.ha);return [X.nb[0]+v[0],X.nb[1]+v[1]];}
 if(kind==='walrus'){const X=walrusXf(p,t),v=rot([60,-50],X.ha);return [X.nk[0]+v[0],X.nk[1]+v[1]];}
 if(kind==='orca'||kind==='shark')return swimXf(kind,p,t).T(SWIM[kind].head);
 if(kind==='elephant'||kind==='rhino'||kind==='hippo'||kind==='croc'){const X=quadXf(kind,p,t),v=rot(X.q.head,X.ha);return [X.nb[0]+v[0],X.nb[1]+v[1]];}
 const h=headOf(kind,p,t);return [h[0]+GEO[kind].off,h[1]];
};
// x,y = ground point under the body centre (screen/world units), s = scale; sq = squash(-)/stretch(+); ghost = smear trail vector
export const Animal:React.FC<{kind:Kind;x:number;y:number;s:number;flip?:boolean;p:PX;t:number;sq?:number;ghost?:Pt;tilt?:number}>=({kind,x,y,s,flip=false,p,t,sq=0,ghost,tilt=0})=>{
 const body=HAS_RIG[kind]?(kind==='polar'?<Polar p={p} t={t}/>:kind==='walrus'?<Walrus p={p} t={t}/>:kind==='orca'||kind==='shark'?<Swimmer k={kind} p={p} t={t}/>:<Quadruped k={kind as QK} p={p} t={t}/>):<Beast kind={kind} x={(GEO[kind].off)} y={0} s={1} p={p} t={t}/>;
 const g=(dx:number,dy:number,o:number,k:number)=><g key={k} opacity={o} transform={`translate(${x+dx} ${y+dy}) scale(${(flip?-1:1)*s*(1-sq*.55)} ${s*(1+sq)}) rotate(${tilt})`}>{body}</g>;
 return <g>{ghost&&[3,2,1].map(i=>g(-ghost[0]*i/3,-ghost[1]*i/3,.16+.05*(3-i),i))}{g(0,0,1,0)}</g>;
};
