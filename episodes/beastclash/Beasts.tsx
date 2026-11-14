// Beast Clash characters: original thick-outline toon animals, drawn once, posed by numbers.
// Every animal faces RIGHT in local space, origin = ground point under the body centre; flip mirrors it.
// Poses: idle, roar, charge, hit, dodge, win, tired (blendable). Anatomy: quadrupeds always draw 4 legs
// (2 far in shade, 2 near), walrus 2 fore + 2 hind flippers, snakes are limbless.
import React,{useId} from 'react';

export const INK='#201B23',PAPER='#FFF5DD',GOLD='#FFD45A',RED='#E77364',TEAL='#56C4B0';
export const S={stroke:INK,strokeWidth:9,strokeLinecap:'round' as const,strokeLinejoin:'round' as const};
type Pt=[number,number];
const rad=(a:number)=>a*Math.PI/180;
const rot=(p:Pt,a:number):Pt=>[p[0]*Math.cos(rad(a))-p[1]*Math.sin(rad(a)),p[0]*Math.sin(rad(a))+p[1]*Math.cos(rad(a))];
const clamp01=(u:number)=>Math.max(0,Math.min(1,u));

export type PoseName='idle'|'roar'|'charge'|'hit'|'dodge'|'win'|'tired';
export type P={lean:number;crouch:number;head:number;jaw:number;lid:number;brow:number;squeeze:number;stride:number;rear:number;smile:number;tongue:number;sweat:number;hood:number;rise:number;strike:number;grit:number;pupil:number;browUp:number;oh:number};
const BASE:P={lean:0,crouch:0,head:0,jaw:.04,lid:.12,brow:.35,squeeze:0,stride:0,rear:0,smile:0,tongue:0,sweat:0,hood:.5,rise:.6,strike:0,grit:0,pupil:1,browUp:0,oh:0};
export const POSES:Record<PoseName,Partial<P>>={
 idle:{smile:.6,brow:.45},
 roar:{lean:-5,crouch:.08,head:-20,jaw:1,lid:0,brow:1,pupil:.75,rear:.12,hood:1,rise:.85},
 charge:{lean:7,crouch:.22,head:8,jaw:.08,grit:1,lid:0,brow:1.1,stride:1,hood:.8,rise:.45,strike:.6},
 hit:{lean:-15,crouch:.12,head:-22,jaw:.55,squeeze:1,brow:-.5,hood:.4,rise:.5,strike:-.4},
 dodge:{lean:-11,crouch:.6,head:12,jaw:.05,oh:1,lid:0,pupil:.5,brow:-.7,hood:.6,rise:.3,strike:-.6},
 win:{lean:-5,head:-16,jaw:.05,brow:.4,browUp:1,lid:.32,rear:.35,smile:1,hood:1,rise:.95},
 tired:{lean:5,crouch:.38,head:24,jaw:.5,lid:.58,brow:-.9,pupil:.85,tongue:1,sweat:1,hood:.15,rise:.18},
};
export const pose=(a:PoseName,b?:PoseName,u=0,over:Partial<P>={}):P=>{
 const A={...BASE,...POSES[a]},B={...BASE,...POSES[b??a]},o={} as P;
 for(const k of Object.keys(BASE) as (keyof P)[])o[k]=A[k]+(B[k]-A[k])*clamp01(u);
 return {...o,...over};
};

// ---- shared face parts ----
export const Eye:React.FC<{x:number;y:number;r:number;p:P;iris?:string;lidColor:string;look?:number}>=({x,y,r,p,iris,lidColor,look=1})=>{
 const by=y-r-9,up=14*p.browUp;
 const brow=<path d={`M${x-r*1.15} ${by-9*p.brow-up*.4}Q${x} ${by-6-up}${' '}${x+r*1.15} ${by+12*p.brow-up}`} fill="none" strokeWidth={r*.55} stroke={INK}/>;
 if(p.squeeze>.5)return <g>{brow}<path d={`M${x-r*.85} ${y-r*.75}L${x+r*.75} ${y}L${x-r*.85} ${y+r*.75}`} fill="none" strokeWidth={r*.38}/></g>;
 const ry=r*1.12,y0=y-ry+2*ry*clamp01(p.lid),dx=r*Math.sqrt(Math.max(0,1-((y0-y)/ry)**2)),pr=r*.48*p.pupil;
 return <g>
  <ellipse cx={x} cy={y} rx={r} ry={ry} fill="#FFFDF4" strokeWidth={r*.3}/>
  {iris&&<circle cx={x+r*.3*look} cy={y+r*.08} r={r*.66*Math.max(.7,p.pupil)} fill={iris} stroke="none"/>}
  <circle cx={x+r*.36*look} cy={y+r*.1} r={pr} fill={INK} stroke="none"/>
  <circle cx={x+r*.2*look} cy={y-r*.18} r={r*.2} fill="#FFF" stroke="none"/><circle cx={x+r*.5*look} cy={y+r*.32} r={r*.09} fill="#FFF" stroke="none"/>
  {p.lid>.02&&<path d={`M${x-dx} ${y0}A${r} ${ry} 0 ${p.lid>.5?1:0} 1 ${x+dx} ${y0}Z`} fill={lidColor} strokeWidth={r*.3}/>}
  <ellipse cx={x} cy={y} rx={r} ry={ry} fill="none" strokeWidth={r*.3}/>
  {brow}
 </g>;
};
// mouth overlay at the mouth line (x0..x1 at y): gritted teeth, surprised "o", smirk handled by each head
const Grit:React.FC<{x0:number;x1:number;y:number;p:P}>=({x0,x1,y,p})=>{if(p.grit<.5||p.jaw>.3)return null;const w=x1-x0;
 return <g><rect x={x0} y={y-12} width={w} height={26} rx={8} fill="#FFFDF4" strokeWidth={6}/>{[1,2,3].map(i=><path key={i} d={`M${x0+w*i/4} ${y-12}V${y+14}`} strokeWidth={4}/>)}<path d={`M${x0} ${y+1}H${x1}`} strokeWidth={4}/></g>;};
const Oh:React.FC<{x:number;y:number;p:P;r?:number}>=({x,y,p,r=16})=>p.oh>.5?<ellipse cx={x} cy={y} rx={r*.8} ry={r} fill="#6B2633" strokeWidth={6}/>:null;
const Sweat:React.FC<{x:number;y:number;t:number}>=({x,y,t})=>{const u=(t%24)/24;return <g opacity={1-u}><path d={`M${x} ${y+40*u-22}Q${x+14} ${y+40*u} ${x} ${y+40*u+12}Q${x-14} ${y+40*u} ${x} ${y+40*u-22}Z`} fill="#9FD8F0" strokeWidth={5}/></g>;};
const Tongue:React.FC<{x:number;y:number;t:number;len?:number}>=({x,y,t,len=46})=><path d={`M${x-14} ${y}Q${x-16} ${y+len+4*Math.sin(t*.9)} ${x} ${y+len+4*Math.sin(t*.9)}Q${x+16} ${y+len} ${x+14} ${y}Z`} fill="#F08A9B" strokeWidth={6}/>;

// ---- quadruped rig ----
type Quad={kind:'polar'|'jaguar'|'badger';L:number;R:number;leg:number;legW:number;body:string;far:string;paw:string;claw:string;front:number;rear:number;neck:Pt};
const QUADS:Record<string,Quad>={
 polar:{kind:'polar',L:290,R:120,leg:200,legW:66,body:'#F5F1E4',far:'#D8D2C2',paw:'#F5F1E4',claw:'#3A3036',front:-14,rear:10,neck:[.62,-.42]},
 jaguar:{kind:'jaguar',L:280,R:82,leg:180,legW:46,body:'#E9A83C',far:'#C98C2E',paw:'#E9A83C',claw:'#F4EBD8',front:0,rear:-6,neck:[.66,-.5]},
 badger:{kind:'badger',L:220,R:82,leg:84,legW:40,body:'#34302F',far:'#242021',paw:'#2A2627',claw:'#E8E0CC',front:0,rear:4,neck:[.75,-.25]},
};
const ik=(a:Pt,b:Pt,l1:number,l2:number,bend:number):Pt=>{let dx=b[0]-a[0],dy=b[1]-a[1];const d=Math.max(1,Math.min(Math.hypot(dx,dy),l1+l2-1));const k=(l1*l1-l2*l2+d*d)/(2*d),h=Math.sqrt(Math.max(0,l1*l1-k*k));const n=Math.hypot(dx,dy)||1;dx/=n;dy/=n;return [a[0]+dx*k-dy*h*bend,a[1]+dy*k+dx*h*bend];};
const bodyPath=(q:Quad)=>{const bx=q.L/2,R=q.R,ft=q.front,rt=q.rear;
 return `M${-bx-R*.75} ${-R*.05}C${-bx-R*.78} ${-R*.95-rt} ${-bx*.3} ${-R*1.05-rt} 0 ${-R-(rt+ft)/2}C${bx*.4} ${-R*.98-ft} ${bx+R*.78} ${-R*.88-ft} ${bx+R*.72} ${-R*.05}C${bx+R*.66} ${R*.58} ${bx*.4} ${R*.82} 0 ${R*.8}C${-bx*.4} ${R*.82} ${-bx-R*.72} ${R*.62} ${-bx-R*.75} ${-R*.05}Z`;};

const QuadHead:React.FC<{q:Quad;p:P;t:number}>=({q,p,t})=>{
 const jaw=p.jaw*30;
 if(q.kind==='polar'){const c=q.body;return <g>
  <path d={`M40 6L190 0L${40+rot([140,24],jaw)[0]} ${6+rot([140,24],jaw)[1]}Z`} fill="#6B2633" strokeWidth={6}/>
  <g transform={`rotate(${jaw} 40 6)`}><path d="M40 6L178 8Q186 20 172 32L48 34Q30 22 40 6Z" fill={c} strokeWidth={8}/>{p.jaw>.3&&<path d="M150 10l8 -14l8 14M118 12l8 -12l8 12" fill="#FFF" strokeWidth={4}/>}</g>
  <circle cx={34} cy={-84} r={24} fill={c} strokeWidth={8}/><circle cx={32} cy={-90} r={10} fill="#4A3F46" stroke="none"/>
  <path d="M-30 -14C-30 -92 58 -112 112 -80C150 -62 186 -52 202 -30C212 -14 204 6 186 6L60 10C18 16 -30 22 -30 -14Z" fill={c} strokeWidth={9}/>
  <ellipse cx={198} cy={-24} rx={17} ry={13} fill={INK}/>
  {p.jaw>.3&&<path d="M168 6l7 14l7 -14M140 8l7 13l7 -13" fill="#FFF" strokeWidth={4}/>}
  {p.smile>.5&&p.jaw<.3&&<path d="M128 -4Q156 16 190 -10" fill="none" strokeWidth={9}/>}
  {p.tongue>.5&&<Tongue x={160} y={22} t={t}/>}
  <Grit x0={120} x1={184} y={4} p={p}/><Oh x={172} y={14} p={p}/>
  <Eye x={108} y={-50} r={27} p={p} lidColor={c}/>
 </g>;}
 if(q.kind==='jaguar'){const c=q.body;return <g>
  <path d={`M40 6L160 4L${40+rot([118,22],jaw)[0]} ${6+rot([118,22],jaw)[1]}Z`} fill="#6B2633" strokeWidth={6}/>
  <g transform={`rotate(${jaw} 40 6)`}><path d="M40 6L150 8Q158 20 146 30L48 30Q30 20 40 6Z" fill="#F7E6C4" strokeWidth={8}/>{p.jaw>.3&&<path d="M128 10l7 -16l7 16" fill="#FFF" strokeWidth={4}/>}</g>
  <circle cx={34} cy={-86} r={26} fill={c} strokeWidth={8}/><circle cx={32} cy={-92} r={11} fill="#7A4B2A" stroke="none"/>
  <path d="M-24 -10C-26 -96 74 -116 124 -80C152 -60 168 -46 170 -24C172 -6 162 8 146 8L50 12C10 16 -24 18 -24 -10Z" fill={c} strokeWidth={9}/>
  <ellipse cx={140} cy={-4} rx={30} ry={15} fill="#F7E6C4" stroke="none"/>
  {[[50,-60],[66,-78],[30,-40],[72,-34],[96,-92]].map(([x,y],i)=><circle key={i} cx={x} cy={y} r={6} fill={INK} stroke="none"/>)}
  <path d="M160 -34L174 -26L160 -16Z" fill="#B5655A" strokeWidth={5}/>
  {p.jaw>.3&&<path d="M150 8l6 16l6 -16" fill="#FFF" strokeWidth={4}/>}
  {p.smile>.5&&p.jaw<.3&&<path d="M108 -2Q132 16 162 -8" fill="none" strokeWidth={9}/>}
  <path d="M150 -6l50 -8M150 0l52 4" strokeWidth={3} fill="none"/>
  {p.tongue>.5&&<Tongue x={136} y={22} t={t}/>}
  <Grit x0={96} x1={150} y={6} p={p}/><Oh x={140} y={16} p={p}/>
  <Eye x={96} y={-50} r={26} p={p} iris="#C9D23A" lidColor={c}/>
 </g>;}
 const c=q.body;return <g>
  <path d={`M30 4L132 2L${30+rot([100,18],jaw)[0]} ${4+rot([100,18],jaw)[1]}Z`} fill="#6B2633" strokeWidth={6}/>
  <g transform={`rotate(${jaw} 30 4)`}><path d="M30 4L124 6Q130 16 120 24L36 24Q22 16 30 4Z" fill={c} strokeWidth={7}/>{p.jaw>.3&&<path d="M104 8l6 -12l6 12" fill="#FFF" strokeWidth={4}/>}</g>
  <path d="M-20 -6C-20 -62 60 -80 112 -52C136 -40 150 -28 152 -12C152 2 140 6 126 6L40 8C8 12 -20 12 -20 -6Z" fill={c} strokeWidth={9}/>
  <path d="M-20 -44C10 -78 76 -82 118 -50L104 -42C66 -64 18 -60 -20 -22Z" fill="#D6D2C6" strokeWidth={6}/>
  <ellipse cx={150} cy={-14} rx={11} ry={9} fill={INK}/>
  {p.smile>.5&&p.jaw<.3&&<path d="M96 -2Q118 10 138 -2" fill="none" stroke="#D6D2C6" strokeWidth={6}/>}
  {p.tongue>.5&&<Tongue x={110} y={18} t={t} len={36}/>}
  <Grit x0={80} x1={130} y={5} p={p}/><Oh x={124} y={12} p={p} r={12}/>
  <Eye x={78} y={-30} r={21} p={p} lidColor={c}/>
 </g>;
};
const Tail:React.FC<{q:Quad;p:P;t:number;at:Pt}>=({q,p,t,at})=>{
 const w=Math.sin(t*.25)*(1+p.stride);
 if(q.kind==='polar')return <ellipse cx={at[0]-6} cy={at[1]-6} rx={22} ry={18} fill={q.body} strokeWidth={8}/>;
 if(q.kind==='badger')return <path d={`M${at[0]+10} ${at[1]}Q${at[0]-60} ${at[1]-30+8*w} ${at[0]-74} ${at[1]-6+10*w}Q${at[0]-50} ${at[1]+14} ${at[0]+10} ${at[1]+24}Z`} fill="#3A3534" strokeWidth={8}/>;
 const d=`M${at[0]} ${at[1]}C${at[0]-90} ${at[1]+40} ${at[0]-150} ${at[1]+120+20*w} ${at[0]-210} ${at[1]+40+40*w}`;
 return <g><path d={d} fill="none" strokeWidth={42} stroke={INK}/><path d={d} fill="none" strokeWidth={26} stroke={q.body}/><path d={d} fill="none" strokeWidth={26} stroke={INK} strokeDasharray="12 34" strokeDashoffset={-40}/><circle cx={at[0]-210} cy={at[1]+40+40*w} r={14} fill={INK}/></g>;
};
const BodyPattern:React.FC<{q:Quad}>=({q})=>{
 const bx=q.L/2,R=q.R;
 if(q.kind==='jaguar'){const pts:Pt[]=[];for(let i=0;i<7;i++)for(let j=0;j<3;j++)pts.push([-bx-R*.4+i*(q.L+R)/6+(j%2)*28,-R*.7+j*R*.55]);
  return <g>{pts.map(([x,y],i)=><g key={i}><circle cx={x} cy={y} r={17} fill="#CF8B2C" stroke={INK} strokeWidth={7} strokeDasharray="15 9"/><circle cx={x+2} cy={y} r={4} fill={INK} stroke="none"/></g>)}<path d={`M${-bx} ${R*.55}Q0 ${R*.95} ${bx+R*.3} ${R*.45}L${bx+R*.3} ${R}L${-bx} ${R}Z`} fill="#F7E6C4" stroke="none"/></g>;}
 if(q.kind==='badger')return <path d={`M${-bx-R} ${-R*1.3}H${bx+R}V${-R*.3}C${bx*.4} ${-R*.1} ${-bx*.4} ${-R*.45} ${-bx-R} ${-R*.15}Z`} fill="#D6D2C6" stroke={INK} strokeWidth={6}/>;
 return <path d={`M${-bx*.2} ${R*.3}Q${bx*.3} ${R*.5} ${bx*.7} ${R*.2}`} fill="none" stroke="#D8D2C2" strokeWidth={6}/>;
};
const QuadBeast:React.FC<{q:Quad;p:P;t:number}>=({q,p,t})=>{
 const id=useId().replace(/:/g,'');
 const g=t*.42,st=p.stride,bob=-12*st*Math.abs(Math.sin(g))+2*Math.sin(t*(p.tongue>.5?.5:.1));
 const legLen=q.leg+q.R*.3,cy=-(legLen*.97-q.R*.3)*(1-.28*p.crouch)+bob-q.R*.3*0;
 const C:Pt=[0,cy-q.R*.3],bx=q.L/2,R=q.R;
 const wp=(pl:Pt):Pt=>{const r=rot(pl,p.lean);return [C[0]+r[0],C[1]+r[1]];};
 const legs=[{j:[bx*.82,R*.32] as Pt,ph:0,front:true,near:true},{j:[bx*.82+16,R*.28] as Pt,ph:2.2,front:true,near:false},{j:[-bx*.9,R*.32] as Pt,ph:Math.PI,front:false,near:true},{j:[-bx*.9+16,R*.28] as Pt,ph:Math.PI+2.2,front:false,near:false}];
 const l1=legLen*.52,l2=legLen*.52;
 const leg=(L:typeof legs[0])=>{const a=wp(L.j);let f:Pt=[a[0]+(L.front?8:-6)+70*st*Math.sin(g+L.ph),-46*st*Math.max(0,Math.cos(g+L.ph))];
  if(L.front&&L.near&&p.rear>0)f=[f[0]+90*p.rear,f[1]-170*p.rear];
  const k=ik(a,f,l1,l2,L.front?-1:1),w=q.legW*(L.near?1:.92),col=L.near?q.body:q.far;
  const d=`M${a[0]} ${a[1]}L${k[0]} ${k[1]}L${f[0]} ${f[1]-w*.3}`;
  return <g key={L.ph}><path d={d} fill="none" stroke={INK} strokeWidth={w+18}/><path d={d} fill="none" stroke={col} strokeWidth={w}/>
   <ellipse cx={f[0]+w*.25} cy={f[1]-w*.3} rx={w*.62} ry={w*.4} fill={L.near?q.paw:q.far} strokeWidth={8}/>
   {[0,1,2].map(i=><path key={i} d={`M${f[0]+w*.6+i*0} ${f[1]-w*.5+i*w*.22}l${q.kind==='badger'&&L.front?30:14} 4`} stroke={q.claw} strokeWidth={q.kind==='badger'&&L.front?8:6}/>)}
  </g>;};
 const neck=wp([bx+R*q.neck[0],R*q.neck[1]]),tailAt=wp([-bx-R*.68,-R*.35]);
 return <g {...S}>
  {legs.filter(l=>!l.near).map(leg)}
  <Tail q={q} p={p} t={t} at={tailAt}/>
  {legs.filter(l=>l.near).map(leg)}
  {q.kind!=='badger'&&(()=>{const b0=wp([bx+R*.1,-R*.35]),nw=R*(q.kind==='polar'?.95:.8),d=`M${b0[0]} ${b0[1]}L${neck[0]+12} ${neck[1]-28}`;return <g><path d={d} stroke={INK} strokeWidth={nw+18}/><path d={d} stroke={q.body} strokeWidth={nw}/></g>;})()}
  <g transform={`translate(${C[0]} ${C[1]}) rotate(${p.lean})`}>
   <clipPath id={`b${id}`}><path d={bodyPath(q)}/></clipPath>
   <path d={bodyPath(q)} fill={q.body}/>
   <g clipPath={`url(#b${id})`}><BodyPattern q={q}/></g>
   <path d={bodyPath(q)} fill="none"/>
  </g>
  <g transform={`translate(${neck[0]} ${neck[1]}) rotate(${p.lean+p.head}) scale(${q.kind==='polar'?1.15:1})`}><QuadHead q={q} p={p} t={t}/></g>
  {p.sweat>.5&&<Sweat x={neck[0]+60} y={neck[1]-130} t={t}/>}
 </g>;
};

// ---- walrus: 2 fore flippers, 2 hind flippers, tusks from the upper jaw, whisker pad ----
const WalrusBeast:React.FC<{p:P;t:number}>=({p,t})=>{
 const c='#C08A68',far='#9E6F53',g=t*.35,und=p.stride*Math.sin(g);
 const raise=-22*p.rear+p.lean-4*(p.jaw>.8?1:0),flat=p.crouch*.6;
 const P0:Pt=[-260,0];
 const body=`M-300 -10C-320 -150 -190 -270 -20 -${300-50*flat}C90 -${340-70*flat} 205 -300 225 -190C245 -90 210 -10 150 0Z`;
 const tr=`translate(${P0[0]+12*und} 0) rotate(${raise} 0 0) translate(${-P0[0]} 0) scale(${1+.04*und} ${1-.04*und-.08*flat})`;
 const neck=rot([150,-285+70*flat],raise);
 const flip=(x:number,col:string,ph:number)=>{const s=p.stride*Math.sin(g+ph);return <path d={`M${x} -90C${x+30} -40 ${x+50+30*s} -10 ${x+110+40*s} 0C${x+60} 10 ${x+10} 6 ${x-20} -6Z`} fill={col} strokeWidth={8}/>;};
 const jaw=p.jaw*22;
 return <g {...S}>
  <g transform={tr}>
   {flip(70,far,2)}
   <path d="M-290 -30C-360 -40 -400 -10 -420 10C-380 14 -330 6 -280 0Z" fill={far} strokeWidth={8}/>
   <path d={body} fill={c}/>
   {[-180,-90,0,80].map((x,i)=><path key={i} d={`M${x} -${210-10*i}Q${x+20} -${170-10*i} ${x+6} -${120-10*i}`} fill="none" stroke="#9E6F53" strokeWidth={6}/>)}
   <path d="M-300 -10C-350 -30 -400 -20 -430 -50C-400 -10 -350 10 -290 6Z" fill={c} strokeWidth={8}/>
   {flip(110,c,0)}
  </g>
  <g transform={`translate(${neck[0]+12*und} ${neck[1]}) rotate(${p.head+raise})`}>
   <path d="M-40 10C-60 -80 40 -130 110 -100C160 -78 180 -30 170 10C160 40 120 50 70 46C10 44 -30 40 -40 10Z" fill={c} strokeWidth={9}/>
   <g transform={`rotate(${jaw} 90 40)`}><path d="M70 40Q120 90 160 44" fill="#6B2633" strokeWidth={7}/></g>
   <path d="M118 30L112 190Q120 200 128 190L142 34Z" fill="#FFF6DE" strokeWidth={8}/>
   <path d="M148 28L150 176Q158 186 164 176L170 30Z" fill="#E9DEC2" strokeWidth={7}/>
   <path d="M70 0C70 -40 120 -50 150 -30C190 -40 220 -10 210 20C200 50 150 50 140 40C110 56 70 40 70 0Z" fill="#D9A684" strokeWidth={8}/>
   {[[100,0],[120,14],[160,-6],[180,14],[140,20],[96,22]].map(([x,y],i)=><circle key={i} cx={x} cy={y} r={4} fill="#7A4B3A" stroke="none"/>)}
   {[0,1,2,3].map(i=><path key={i} d={`M${110+20*i} 38l${-4+i*3} 16`} strokeWidth={4} fill="none"/>)}
   {p.smile>.5&&p.jaw<.3&&<path d="M90 34Q130 52 176 30" fill="none" strokeWidth={6}/>}
   {p.tongue>.5&&<Tongue x={120} y={50} t={t}/>}
   <Grit x0={96} x1={166} y={44} p={p}/><Oh x={130} y={52} p={p}/>
   <Eye x={58} y={-50} r={23} p={p} lidColor={c}/>
   {p.smile>.5&&<path d={`M150 ${120+6*Math.sin(t*.4)}l10 -18l10 18l-10 18Z`} fill="#FFF" strokeWidth={4}/>}
  </g>
  {p.sweat>.5&&<Sweat x={neck[0]+40} y={neck[1]-170} t={t}/>}
 </g>;
};

// ---- snakes: tapered tube along a spline, head along the tangent ----
type SnakeK={kind:'anaconda'|'cobra';R:number;len:number;body:string;belly:string;mark:string};
const SNAKES:Record<string,SnakeK>={
 anaconda:{kind:'anaconda',R:70,len:1250,body:'#62803A',belly:'#D8C66A',mark:'#1E2416'},
 cobra:{kind:'cobra',R:30,len:1150,body:'#6B6436',belly:'#EADF9E',mark:'#E8D88A'},
};
const SnakeBeast:React.FC<{k:SnakeK;p:P;t:number}>=({k,p,t})=>{
 const N=70,pts:Pt[]=[],sway=Math.sin(t*.12)*(1-p.squeeze)*.6;
 const rise=k.kind==='cobra'?p.rise:p.rise*.55,strike=p.strike+.25*p.stride*Math.sin(t*.5);
 const groundLen=k.len*.55,hx=40+180*strike+30*sway,hy=-(80+(k.kind==='cobra'?430:330)*rise);
 const sp=Math.min(1,.5+.2*p.crouch);
 for(let i=0;i<=N;i++){const s=i/N;
  if(s<sp){const u=s/sp;pts.push([-groundLen*(1-u)*.8-120*u*(1-u)+(-60)*u,-10-(k.kind==='anaconda'?60:40)*Math.sin(u*Math.PI*2.4+t*.08+p.stride*t*.4)*(1-u*.5)]);}
  else{const u=(s-sp)/(1-sp),a:Pt=[-60,-10],c1:Pt=[hx-200,-20+hy*.1],c2:Pt=[hx-220,hy+40],b:Pt=[hx-40,hy];
   const m=1-u;pts.push([m*m*m*a[0]+3*m*m*u*c1[0]+3*m*u*u*c2[0]+u*u*u*b[0],m*m*m*a[1]+3*m*m*u*c1[1]+3*m*u*u*c2[1]+u*u*u*b[1]]);}}
 const r=(s:number)=>k.R*(s<.85?.22+.78*Math.sin(Math.PI*Math.min(1,s*1.1)*.5):.88);
 const seg=(col:string,extra:number)=>pts.slice(0,-1).map((a,i)=>{const b=pts[i+1];return <path key={i} d={`M${a[0]} ${a[1]}L${b[0]} ${b[1]}`} stroke={col} strokeWidth={2*r(i/N)+extra} strokeLinecap="round"/>;});
 const hd=pts[N],pv=pts[N-2],ang=Math.atan2(hd[1]-pv[1],hd[0]-pv[0])*180/Math.PI;
 const headAng=ang*.25+p.head*.6;
 const hoodW=k.kind==='cobra'?k.R*(1+2.2*p.hood):0;
 const hoodPts=k.kind==='cobra'?[N-14,N-10,N-6,N-3].map(i=>pts[i]):[];
 const jaw=p.jaw*34,fl=(Math.floor(t/9)%3===0);
 return <g {...S}>
  {k.kind==='cobra'&&p.hood>.05&&(()=>{const hp=pts[N-8],hq=pts[N-6],an=Math.atan2(hq[1]-hp[1],hq[0]-hp[0])*180/Math.PI,rx=k.R*3.3,ry=k.R*(1+2.4*p.hood);
   return <g transform={`translate(${hp[0]} ${hp[1]}) rotate(${an})`}><ellipse rx={rx} ry={ry} fill={k.body} strokeWidth={9}/><ellipse cx={-6} rx={rx*.72} ry={ry*.62} fill={k.belly} strokeWidth={5}/>{[-1,1].map(sg=><path key={sg} d={`M${-rx*.5} ${sg*ry*.35}Q0 ${sg*ry*.6} ${rx*.5} ${sg*ry*.3}`} fill="none" stroke={INK} strokeWidth={7}/>)}</g>;})()}
  {seg(INK,16)}{seg(k.body,0)}
  {pts.slice(4,-3).map((a,i)=>{const j=i+4;if(j%(k.kind==='cobra'?5:4))return null;const b=pts[j+1],an=Math.atan2(b[1]-a[1],b[0]-a[0]),rr=r(j/N)*.8;
   return k.kind==='cobra'?<path key={j} d={`M${a[0]-Math.sin(an)*rr} ${a[1]+Math.cos(an)*rr}L${a[0]+Math.sin(an)*rr} ${a[1]-Math.cos(an)*rr}`} stroke={k.mark} strokeWidth={Math.max(4,rr*.4)}/>
    :<ellipse key={j} cx={a[0]+Math.sin(an)*rr*.25*((j/4)%2?1:-1)} cy={a[1]-Math.cos(an)*rr*.25*((j/4)%2?1:-1)} rx={rr*.42} ry={rr*.3} transform={`rotate(${an*180/Math.PI} ${a[0]} ${a[1]})`} fill={k.mark} stroke="none"/>;})}
  <g transform={`translate(${hd[0]} ${hd[1]}) rotate(${headAng})`}>
   {p.jaw>.4&&fl===false&&null}
   {(fl||p.jaw>.5)&&<path d={`M${k.R*2.1} 6l${30+10*Math.sin(t)} 0l10 -8M${k.R*2.1+30+10*Math.sin(t)} 6l10 8`} stroke="#D2384A" strokeWidth={5} fill="none"/>}
   <g transform={`rotate(${jaw} ${-k.R*.4} ${k.R*.3})`}><path d={`M${-k.R*.4} ${k.R*.3}L${k.R*1.9} ${k.R*.25}Q${k.R*1.95} ${k.R*.7} ${k.R*1.5} ${k.R*.8}L${-k.R*.3} ${k.R*.8}Z`} fill={k.belly} strokeWidth={7}/>{p.jaw>.3&&k.kind==='cobra'&&<path d={`M${k.R*1.6} ${k.R*.3}l-5 -14`} stroke="#FFF" strokeWidth={5}/>}</g>
   {p.jaw>.3&&<path d={`M${-k.R*.4} ${k.R*.3}L${k.R*1.9} ${k.R*.25}L${-k.R*.3+rot([k.R*2.2,0],jaw)[0]} ${k.R*.3+rot([k.R*2.2,0],jaw)[1]}Z`} fill="#6B2633" strokeWidth={5}/>}
   <path d={`M${-k.R*.9} ${k.R*.5}C${-k.R*1.1} ${-k.R*.9} ${k.R*.4} ${-k.R*1.15} ${k.R*1.4} ${-k.R*.6}C${k.R*2.1} ${-k.R*.35} ${k.R*2.3} ${k.R*.1} ${k.R*1.95} ${k.R*.32}L${-k.R*.5} ${k.R*.4}Z`} fill={k.body} strokeWidth={9}/>
   {k.kind==='anaconda'&&<path d={`M${-k.R*.2} ${-k.R*.4}L${k.R*1.2} ${-k.R*.15}`} stroke={k.mark} strokeWidth={8}/>}
   {p.smile>.5&&p.jaw<.3&&<path d={`M${k.R*.6} ${k.R*.25}Q${k.R*1.2} ${k.R*.55} ${k.R*1.8} ${k.R*.2}`} fill="none" strokeWidth={6}/>}
   <Grit x0={k.R*.7} x1={k.R*1.7} y={k.R*.32} p={p}/><Oh x={k.R*1.6} y={k.R*.45} p={p} r={12}/>
   <Eye x={k.R*.55} y={-k.R*.42} r={k.kind==='cobra'?21:23} p={p} iris={k.kind==='cobra'?'#C9862E':'#C9B23A'} lidColor={k.body}/>
  </g>
  {p.sweat>.5&&<Sweat x={hd[0]} y={hd[1]-80} t={t}/>}
 </g>;
};

export type Kind='polar'|'walrus'|'jaguar'|'anaconda'|'badger'|'cobra'|'orca'|'shark'|'elephant'|'rhino'|'hippo'|'croc';   // the last six are drawn by Rig.tsx only
export const NAMES:Record<Kind,string>={polar:'POLAR BEAR',walrus:'WALRUS',jaguar:'JAGUAR',anaconda:'ANACONDA',badger:'HONEY BADGER',cobra:'KING COBRA'};
// x,y = ground point in canvas px; s = scale; flip = face left; t = frames since shot start (drives cycles)
export const Beast:React.FC<{kind:Kind;x:number;y:number;s:number;flip?:boolean;p:P;t:number;rot?:number}>=({kind,x,y,s,flip=false,p,t,rot:r=0})=>
 <g transform={`translate(${x} ${y}) rotate(${r}) scale(${flip?-s:s} ${s})`}>
  {kind==='walrus'?<WalrusBeast p={p} t={t}/>:kind==='anaconda'||kind==='cobra'?<SnakeBeast k={SNAKES[kind]} p={p} t={t}/>:<QuadBeast q={QUADS[kind]} p={p} t={t}/>}
 </g>;
// head centre in local units (facing right, s=1, ground origin) for the pose at time t; mirrors the drawing math
// above so the camera can frame faces exactly (snakes exclude the 230 x offset Film adds).
export const headOf=(kind:Kind,p:P,t:number):Pt=>{
 if(kind==='walrus'){const g=t*.35,und=p.stride*Math.sin(g),raise=-22*p.rear+p.lean-4*(p.jaw>.8?1:0),flat=p.crouch*.6,n=rot([150,-285+70*flat],raise),h=rot([80,-30],p.head+raise);return [n[0]+12*und+h[0],n[1]+h[1]];}
 if(kind==='anaconda'||kind==='cobra'){const k=SNAKES[kind],sway=Math.sin(t*.12)*(1-p.squeeze)*.6,rise=k.kind==='cobra'?p.rise:p.rise*.55,strike=p.strike+.25*p.stride*Math.sin(t*.5);
  const hx=40+180*strike+30*sway,hy=-(80+(k.kind==='cobra'?430:330)*rise),h=rot([k.R*.6,-k.R*.1],-3.1+p.head*.6);return [hx-40+h[0],hy+h[1]];}
 const q=QUADS[kind],g=t*.42,st=p.stride,bob=-12*st*Math.abs(Math.sin(g))+2*Math.sin(t*(p.tongue>.5?.5:.1));
 const legLen=q.leg+q.R*.3,cy=-(legLen*.97-q.R*.3)*(1-.28*p.crouch)+bob,C:Pt=[0,cy-q.R*.3],bx=q.L/2,R=q.R;
 const n=rot([bx+R*q.neck[0],R*q.neck[1]],p.lean),hc:Pt=kind==='polar'?[110,-46]:kind==='jaguar'?[75,-40]:[65,-25],h=rot(hc,p.lean+p.head);
 return [C[0]+n[0]+h[0],C[1]+n[1]+h[1]];
};
