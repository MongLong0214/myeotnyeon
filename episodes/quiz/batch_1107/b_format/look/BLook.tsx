// Look-dev picture layer for the B format (opt-in; see look/LOOKDEV.md). Flat 2D cartoon kept: lighting is a cel
// shadow band + rim line inside each character's own outline, plus set-level haze, light spill, vignette and grain.
// Also the camera (depth layers with parallax, rack focus, whip blur, handheld, decaying shake) and impact FX.
import React from 'react';
import {AbsoluteFill,getInputProps,staticFile,useCurrentFrame} from 'remotion';
// profiling switches: inputProps.lookOff = ['charfx','blur','blend','grain','cast','grade']
export const OFF:Set<string>=new Set(((getInputProps() as any)?.lookOff)??[]);
import {handheld,whipBlur} from '../../../../../production/lf_toon/src/camera2d';
import {INK} from '../CourtDynamic';
export {whipBlur};
type Point=[number,number];

// ---------- lights ----------
// dir = unit vector from the subject toward the key light (screen space, y down). Widths in rig units.
export type SetLight={dir:Point;shadow:string;shadowOp:number;shW:number;rim:string;rimOp:number;rimW:number;
 haze:string;hazeOp:number;floorTint:string;vign:number;grain:number;castLen:number;castSkew:number;castOp:number;grade:string};
export const LIGHTS={
 // court: cool daylight from the tall windows, upper left
 court:{dir:[-.62,-.78],shadow:'#5D6A9A',shadowOp:0.38,shW:14,rim:'#F2FAFF',rimOp:.85,rimW:4,haze:'#DCEBFA',hazeOp:.32,floorTint:'#2B3A66',vign:.38,grain:.06,castLen:.22,castSkew:-38,castOp:.22,grade:''},
 courtDark:{dir:[-.5,-.86],shadow:'#24345A',shadowOp:0.34,shW:13,rim:'#9FD8FF',rimOp:.75,rimW:4,haze:'#4C7BA3',hazeOp:.25,floorTint:'#0C1630',vign:.5,grain:.06,castLen:.2,castSkew:-30,castOp:.3,grade:''},
 // street by day: warm sun high on the right, violet-blue shade
 street:{dir:[.55,-.83],shadow:'#6A5C9C',shadowOp:0.3,shW:14,rim:'#FFF3CF',rimOp:.9,rimW:4,haze:'#FFF2D6',hazeOp:.28,floorTint:'#3A2E5C',vign:.32,grain:.06,castLen:.3,castSkew:44,castOp:.26,grade:''},
 // night street: sodium orange key from a lamp above-left, cold blue shade
 nightStreet:{dir:[-.45,-.89],shadow:'#1E2552',shadowOp:0.41,shW:16,rim:'#FFB45A',rimOp:.9,rimW:5,haze:'#FF9C40',hazeOp:.22,floorTint:'#0A0F2A',vign:.55,grain:.07,castLen:.32,castSkew:-30,castOp:.35,grade:''},
 // apartment at night: warm tungsten spill from the hallway (right), cold moonlight rim from the window (left)
 homeNight:{dir:[.8,-.6],shadow:'#24284E',shadowOp:0.39,shW:15,rim:'#FFD08A',rimOp:.85,rimW:5,haze:'#FFC77A',hazeOp:.16,floorTint:'#0D1028',vign:.55,grain:.07,castLen:.24,castSkew:40,castOp:.32,grade:''},
 // cell: cold fluorescent from the ceiling + the high window shaft
 cell:{dir:[-.3,-.95],shadow:'#2E4552',shadowOp:0.38,shW:15,rim:'#D9F6EE',rimOp:.8,rimW:4,haze:'#BFE6DA',hazeOp:.2,floorTint:'#0F2028',vign:.55,grain:.07,castLen:.18,castSkew:-14,castOp:.3,grade:''},
} satisfies Record<string,SetLight>;
export type LightKey=keyof typeof LIGHTS;
export const charFilter=(k:LightKey,blur=0)=>`lk-char-${k}${blur?'-b'+blur*2:''}`;

// Character light filter. Mask = the character's opaque silhouette, eroded past the ink outline. The shadow band is
// the part of the mask that leaves the silhouette when moved away from the light; the rim is the part that leaves
// it when moved toward the light. Multiply the band, screen the rim. Hard-edged (cel), 1px soft.
// mask -> flat colour at opacity, one primitive (cheaper than flood + composite)
const tint=(hex:string,op:number)=>{const n=parseInt(hex.slice(1),16),r=(n>>16&255)/255,g=(n>>8&255)/255,b=(n&255)/255;return `0 0 0 0 ${r} 0 0 0 0 ${g} 0 0 0 0 ${b} 0 0 0 ${op} 0`;};
export const CharFilter:React.FC<{k:LightKey;blur?:number}>=({k,blur=0})=>{const L=LIGHTS[k],[dx,dy]=L.dir;return <filter id={charFilter(k,blur)} x="-6%" y="-4%" width="112%" height="108%" colorInterpolationFilters="sRGB">
 {/* paint = non-ink, opaque pixels (luminance >= .1); ink outlines never take light */}
 <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  2.1 7.2 .72 0 -1" result="paint"/>
 <feOffset in="SourceAlpha" dx={dx*(L.shW+8)} dy={dy*(L.shW+8)} result="away"/>
 <feComposite in="paint" in2="away" operator="out" result="shM"/>
 <feColorMatrix in="shM" type="matrix" values={tint(L.shadow,L.shadowOp)} result="sh"/>
 <feOffset in="SourceAlpha" dx={-dx*(L.rimW+9)} dy={-dy*(L.rimW+9)} result="tow"/>
 <feComposite in="paint" in2="tow" operator="out" result="rimM"/>
 <feColorMatrix in="rimM" type="matrix" values={tint(L.rim,L.rimOp)} result="rim"/>
 <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="sh"/><feMergeNode in="rim"/></feMerge>
 {blur>0&&<feGaussianBlur stdDeviation={blur}/>}
</filter>;};
// flat silhouette for cast shadows (bbox-limited, cheaper than a CSS filter on a full-frame div)
const Silhouette:React.FC<{k:LightKey}>=({k})=><filter id={`lk-sil-${k}`} x="-5%" y="-5%" width="110%" height="110%"><feFlood floodColor={LIGHTS[k].floorTint} floodOpacity={LIGHTS[k].castOp*2}/><feComposite in2="SourceAlpha" operator="in"/></filter>;
export const LookDefs:React.FC=()=><svg width={0} height={0} style={{position:'absolute'}}><defs>{(Object.keys(LIGHTS) as LightKey[]).map(k=><React.Fragment key={k}><CharFilter k={k}/><Silhouette k={k}/></React.Fragment>)}</defs></svg>;

// ---------- camera ----------
export type Cam={x:number;y:number;zoom:number;rot:number;focus:number;focusAmt:number;blurX:number;blurY:number};
export const CAM0:Cam={x:0,y:0,zoom:1,rot:0,focus:1,focusAmt:0,blurX:0,blurY:0};
const CamCtx=React.createContext<Cam>(CAM0);
// A depth layer: depth 1 = the actors' plane; <1 farther (moves and zooms less), >1 nearer. Rack focus blurs by
// |depth - focus| * focusAmt px. Motion blur (whips) only on layers that move with the camera.
export const BlurCtx=React.createContext(0);
// Layer blur (rack focus) is applied inside the layer's own SVG content (bbox-limited filters: BlurSvg, Actor), not as
// a CSS filter on the full-frame layer: full-frame CSS blur was the single largest render cost. `css` forces the old way.
export const blurStep=(b:number)=>b<1||OFF.has('blur')?0:Math.round(b*2)/2;
export const Layer:React.FC<{depth:number;children:React.ReactNode;noBlur?:boolean;css?:boolean}>=({depth,children,noBlur,css})=>{
 const c=React.useContext(CamCtx),d=depth;
 const z=1+(c.zoom-1)*d,blur=noBlur?0:blurStep(Math.abs(d-c.focus)*c.focusAmt);
 const bx=c.blurX*d,by=c.blurY*d,id=`mb-${Math.round(bx*2)}-${Math.round(by*2)}`;
 const filt=[css&&blur?`blur(${blur}px)`:'',bx>.6||by>.6?`url(#${id})`:''].join(' ').trim();
 return <AbsoluteFill style={{transformOrigin:'540px 960px',transform:`rotate(${c.rot*d}deg) scale(${z}) translate(${-c.x*d}px,${-c.y*d}px)`,filter:filt||undefined}}>
  {(bx>.6||by>.6)&&<svg width={0} height={0} style={{position:'absolute'}}><filter id={id} x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation={`${(bx).toFixed(1)} ${(by).toFixed(1)}`}/></filter></svg>}
  <BlurCtx.Provider value={css?0:blur}>{children}</BlurCtx.Provider></AbsoluteFill>;
};
// Full-frame SVG whose content takes the layer's focus blur (filter region = content bbox).
export const BlurSvg:React.FC<{children:React.ReactNode;style?:React.CSSProperties;svgProps?:React.SVGProps<SVGSVGElement>}>=({children,style,svgProps})=>{
 const b=React.useContext(BlurCtx),id=`fb-${b*2}`;
 return <svg width={1080} height={1920} style={{position:'absolute',overflow:'visible',...style}} {...svgProps}>
  {b>0&&<filter id={id} x="-20%" y="-5%" width="140%" height="110%"><feGaussianBlur stdDeviation={b}/></filter>}
  <g filter={b>0?`url(#${id})`:undefined}>{children}</g></svg>;
};
export const Stage:React.FC<{cam:Cam;light:LightKey;impact?:number;children:React.ReactNode;grain?:boolean}>=({cam,light,impact=-1,children,grain=true})=>{
 const L=LIGHTS[light];
 // impact frame: frame 0 = inverted high-contrast ink frame, frame 1 = bleached flash, then normal
 const imp=OFF.has('grade')&&impact!==0&&impact!==1?undefined:impact===0?'grayscale(1) contrast(5) invert(1)':impact===1?'grayscale(.6) contrast(1.6) brightness(1.35)':L.grade||undefined;
 return <AbsoluteFill style={{overflow:'hidden',filter:imp}}>
  <LookDefs/>
  <CamCtx.Provider value={cam}>{children}</CamCtx.Provider>
  <Atmos light={light} grain={grain}/>
 </AbsoluteFill>;
};
// haze (light falloff from the top), floor tint (bottom gets the set's shade colour), vignette, grain
export const Atmos:React.FC<{light:LightKey;grain?:boolean}>=({light,grain=true})=>{
 const f=useCurrentFrame(),L=LIGHTS[light],g=Math.floor(f/2);
 const ox=Math.floor((Math.sin(g*12.9898)*.5+.5)*384),oy=Math.floor((Math.cos(g*78.233)*.5+.5)*384);
 if(OFF.has('blend'))return null;
 return <>
  {/* one normal-blend overlay: haze at the top, the set's shade colour at the floor, vignette (no blend modes: cheap) */}
  <AbsoluteFill style={{background:`radial-gradient(ellipse 75% 62% at 50% 46%,transparent 60%,rgba(8,6,16,${L.vign*.8}) 100%),linear-gradient(180deg,transparent 70%,${L.floorTint}55 100%)`}}><AbsoluteFill style={{background:`linear-gradient(180deg,${L.haze} 0%,transparent 40%)`,opacity:L.hazeOp*.8}}/></AbsoluteFill>
  {grain&&!OFF.has('grain')&&<AbsoluteFill style={{backgroundImage:`url(${staticFile('look/grain.png')})`,backgroundPosition:`${ox}px ${oy}px`,opacity:L.grain*1.5}}/>}
 </>;
};

// ---------- camera helpers (all frame-pure) ----------
// Decaying shake from hits: [frame, amplitude px]. Each hit rings for ~10 frames with an exponential decay.
export const shakeAt=(f:number,hits:[number,number][])=>{let x=0,y=0,r=0;for(const [at,a] of hits){const d=f-at;if(d<0||d>18)continue;const e=a*Math.exp(-d/4.5);x+=e*Math.sin(d*2.3+at);y+=e*.7*Math.cos(d*2.9+at);r+=e*.035*Math.sin(d*1.7+at);}return {x,y,r};};
export const drift=(f:number,amount=1,salt=3)=>{const h=handheld(f/30,amount,salt);return {x:h.dx,y:h.dy,r:h.rot};};
const sm=(u:number)=>{u=Math.max(0,Math.min(1,u));return u*u*u*(u*(6*u-15)+10);};
// eased dolly between keyed cameras [frame, partial cam]; quintic ease, no velocity pop at the keys
export const dolly=(f:number,keys:[number,Partial<Cam>][]):Cam=>{
 const get=(k:keyof Cam)=>{const pts=keys.filter(([,c])=>c[k]!==undefined).map(([t,c])=>[t,c[k] as number] as [number,number]);if(!pts.length)return CAM0[k];
  if(f<=pts[0][0])return pts[0][1];for(let i=1;i<pts.length;i++)if(f<=pts[i][0]){const [a,va]=pts[i-1],[b,vb]=pts[i];return va+(vb-va)*sm((f-a)/(b-a));}return pts[pts.length-1][1];};
 return {x:get('x'),y:get('y'),zoom:get('zoom'),rot:get('rot'),focus:get('focus'),focusAmt:get('focusAmt'),blurX:0,blurY:0};
};
// whip: camera offset dx over `dur` frames ending at `at+dur`, with horizontal blur peaking mid-move
export const whip=(f:number,at:number,dur:number,dx:number)=>{const u=(f-at)/dur;return {x:u>=1?0:u<=0?dx:dx*(1-sm(u)),blur:whipBlur(f,at,dur,26)};};

// ---------- FX ----------
const rnd=(n:number)=>{const s=Math.sin(n*127.1+311.7)*43758.5453;return s-Math.floor(s);};
// Speed lines: radial toward a focus (`center`), or parallel (`angle` deg). Redrawn on 2s. t = frames since start.
export const SpeedLines:React.FC<{t:number;dur:number;center?:Point;angle?:number;n?:number;color?:string;inner?:number;opacity?:number}>=({t,dur,center,angle=0,n=28,color='#FFFFFF',inner=420,opacity=.8})=>{
 if(t<0||t>=dur)return null;const g=Math.floor(t/2),fade=Math.min(1,(dur-t)/4)*Math.min(1,(t+1)/2);
 return <svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}} opacity={opacity*fade}>
  {Array.from({length:n}).map((_,i)=>{const a=rnd(i*7.3+g*1.7),b=rnd(i*3.1+g*5.3),w=4+10*rnd(i+g*2.2);
   if(center){const th=a*Math.PI*2,r0=inner+b*260,r1=r0+500+300*rnd(i*9+g),c=Math.cos(th),s=Math.sin(th),px=-s*w,py=c*w;
    return <path key={i} d={`M${center[0]+c*r0} ${center[1]+s*r0}L${center[0]+c*r1+px} ${center[1]+s*r1+py}L${center[0]+c*r1-px} ${center[1]+s*r1-py}Z`} fill={color}/>;}
   const th=angle*Math.PI/180,c=Math.cos(th),s=Math.sin(th),y=a*2200-140,x=b*1400-160,len=260+400*rnd(i*5+g);
   return <path key={i} d={`M${x-s*y*0} ${y}l${c*len} ${s*len}l${-s*w*.5} ${c*w*.5}Z`} transform={`translate(${-c*0} 0)`} fill={color}/>;})}
 </svg>;
};
// Smear: a 1-2 frame stretched limb/prop along `path` (screen points, oldest first), ink outline + fill, tapered.
export const Smear:React.FC<{path:Point[];w:number;fill:string;opacity?:number}>=({path,w,fill,opacity=1})=>{
 if(path.length<2)return null;const d='M'+path.map(p=>`${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join('L');
 return <svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}} opacity={opacity}>
  {path.slice(1).map((p,i)=>{const q=path[i],k=(i+1)/(path.length-1),ww=w*(.35+.65*k);return <g key={i}>
   <path d={`M${q[0]} ${q[1]}L${p[0]} ${p[1]}`} stroke={INK} strokeWidth={ww+12} strokeLinecap="round"/></g>;})}
  {path.slice(1).map((p,i)=>{const q=path[i],k=(i+1)/(path.length-1),ww=w*(.35+.65*k);return <path key={'f'+i} d={`M${q[0]} ${q[1]}L${p[0]} ${p[1]}`} stroke={fill} strokeWidth={ww} strokeLinecap="round"/>;})}
  <path d={d} fill="none" stroke="rgba(255,255,255,.35)" strokeWidth={w*.18} strokeLinecap="round"/>
 </svg>;
};
// Motion trail: thin streak lines behind a moving point (screen path, oldest first).
export const Trail:React.FC<{path:Point[];color?:string;n?:number;spread?:number;opacity?:number}>=({path,color='#FFFFFF',n=3,spread=26,opacity=.7})=>{
 if(path.length<2)return null;const a=path[0],b=path[path.length-1],dx=b[0]-a[0],dy=b[1]-a[1],d=Math.hypot(dx,dy)||1,nx=-dy/d,ny=dx/d;
 if(d<18)return null;
 return <svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}} opacity={opacity}>
  {Array.from({length:n}).map((_,i)=>{const o=(i-(n-1)/2)*spread;const pts=path.map(p=>`${p[0]+nx*o} ${p[1]+ny*o}`).join('L');return <path key={i} d={'M'+pts} fill="none" stroke={color} strokeWidth={7-Math.abs(o)/spread*2} strokeLinecap="round"/>;})}
 </svg>;
};
// Dust puffs (outlined, flat) + debris chips with gravity and one bounce. t = frames since the hit.
export const Dust:React.FC<{x:number;y:number;t:number;n?:number;s?:number;seed?:number;color?:string;chips?:string;spread?:number;floor?:number}>=({x,y,t,n=7,s=1,seed=1,color='#E9E2D2',chips,spread=1,floor})=>{
 if(t<0||t>26)return null;const u=t/26;
 return <svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}>
  {Array.from({length:n}).map((_,i)=>{const a=(rnd(seed+i*3.3)-.5)*Math.PI*spread-Math.PI/2,v=(60+90*rnd(seed+i))*s,r=(16+18*rnd(seed+i*2))*s*(.6+1.2*Math.sqrt(u));
   const px=x+Math.cos(a)*v*Math.sqrt(u)*1.6,py=y+Math.sin(a)*v*Math.sqrt(u)*.7-20*u*s;
   const rr=r*Math.sin(Math.PI*Math.min(1,u*1.15+.08));return rr>1?<circle key={i} cx={px} cy={py} r={rr} fill={color} stroke={INK} strokeWidth={4}/>:null;})}
  {chips&&Array.from({length:Math.ceil(n*.9)}).map((_,i)=>{const a=(rnd(seed+i*5.1)-.5)*2.4,vx=Math.sin(a)*(9+9*rnd(seed+i*7))*s,vy=-(14+12*rnd(seed+i*9))*s;
   const fl=floor??y+40*s;let px=x+vx*t,py=y+vy*t+1.6*s*t*t;if(py>fl){py=fl-Math.abs(Math.sin(t*.6))*6;}
   return <path key={'c'+i} d="M-9 -5L8 -8L10 6L-6 8Z" transform={`translate(${px} ${py}) rotate(${t*(30+40*rnd(i))}) scale(${s})`} fill={chips} stroke={INK} strokeWidth={3} opacity={u<.8?1:(1-u)*5}/>;})}
 </svg>;
};
// Light spill: soft beam polygons (window shafts, door gaps) screened over the picture. pts in screen space.
export const Beam:React.FC<{pts:Point[];color:string;opacity:number;id:string;from?:Point;to?:Point}>=({pts,color,opacity,id,from=[0,0],to=[0,1]})=>
 <svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}>
  <defs><linearGradient id={id} x1={from[0]} y1={from[1]} x2={to[0]} y2={to[1]}><stop offset="0" stopColor={color} stopOpacity={opacity}/><stop offset="1" stopColor={color} stopOpacity={0}/></linearGradient></defs>
  <path d={'M'+pts.map(p=>p.join(' ')).join('L')+'Z'} fill={`url(#${id})`}/>
 </svg>;
// Soft contact shadow (multiply) for feet / props on the floor, in the set's shade colour
export const Contact:React.FC<{x:number;y:number;rx:number;ry?:number;light:LightKey;op?:number}>=({x,y,rx,ry=rx*.16,light,op=.5})=>
 <svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}>
  <defs><radialGradient id={`ct-${light}`}><stop offset="0" stopColor={LIGHTS[light].floorTint} stopOpacity={1}/><stop offset="1" stopColor={LIGHTS[light].floorTint} stopOpacity={0}/></radialGradient></defs>
  <ellipse cx={x} cy={y} rx={rx} ry={ry} fill={`url(#ct-${light})`} opacity={op}/>
 </svg>;
