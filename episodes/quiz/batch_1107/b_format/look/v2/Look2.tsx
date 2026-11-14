// look v2 ("full2") picture layer: signature camera moves, Dutch tilt, foreground occluders, ink-splash impact frames,
// paper flutter, night light flicker, per-set particles (dust motes in beams, rain on night windows). Builds on BLook.
import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {BlurSvg} from '../BLook';
import {INK} from '../../Kit';
type Point=[number,number];
const rnd=(n:number)=>{const s=Math.sin(n*127.1+311.7)*43758.5453;return s-Math.floor(s);};
const sm=(u:number)=>{u=Math.max(0,Math.min(1,u));return u*u*u*(u*(6*u-15)+10);};

// ---------- signature camera moves (return partial cams; add to your dolly) ----------
// Snap zoom: 4-frame punch to `to` with a small overshoot and settle, centred on a screen point (keeps it in place).
export const snapZoom=(f:number,at:number,to:number,center:Point,dur=4)=>{const d=f-at;if(d<0)return {zoom:1,x:0,y:0};
 const u=Math.min(1,d/dur),ov=d>dur?.06*Math.exp(-(d-dur)/4)*Math.cos((d-dur)*.9):0,z=1+(to-1)*(1-Math.pow(1-u,3))+ov*(to-1);
 return {zoom:z,x:(center[0]-540)*(1-1/z),y:(center[1]-960)*(1-1/z)};};
// Whip pan between two framings (x offsets in px) with horizontal blur peaking mid-move.
export const whipBetween=(f:number,at:number,dur:number,xa:number,xb:number,peak=34)=>{const u=(f-at)/dur;
 return {x:u<=0?xa:u>=1?xb:xa+(xb-xa)*sm(u),blurX:u<=0||u>=1?0:peak*Math.sin(Math.PI*u)**2};};
// Slow push on a reaction: eased zoom ramp from `at` over `dur`.
export const slowPush=(f:number,at:number,dur:number,amt=.08)=>1+amt*sm((f-at)/dur);
// Dutch tilt: degrees, eased in at `at` over `dur`.
export const dutch=(f:number,at:number,dur:number,deg:number)=>deg*sm((f-at)/dur);

// ---------- foreground occluders (put in a <Layer depth={1.3-1.6}>; they take the rack-focus blur) ----------
export const ForeBars:React.FC<{xs:number[];color?:string}>=({xs,color='#3F474D'})=><BlurSvg>{xs.map(x=><g key={x}><path d={`M${x-38} -200H${x+38}V2200H${x-38}Z`} fill={color} stroke={INK} strokeWidth={10}/><path d={`M${x-14} -200V2200`} stroke="#77828A" strokeWidth={12}/></g>)}</BlurSvg>;
export const ForeRail:React.FC<{y:number}>=({y})=><BlurSvg><path d={`M-200 ${y}H1280V${y+46}H-200Z`} fill="#C5A06F" stroke={INK} strokeWidth={10}/>{[60,1020].map(x=><path key={x} d={`M${x-24} ${y+40}H${x+24}V2200H${x-24}Z`} fill="#8A6040" stroke={INK} strokeWidth={10}/>)}</BlurSvg>;
export const ForeMonitor:React.FC<{x:number;y:number;flip?:boolean}>=({x,y,flip})=><BlurSvg><g transform={`translate(${x} ${y}) scale(${flip?-1:1} 1)`} stroke={INK} strokeWidth={10}>
 <path d="M-170 -150H170V90H-170Z" fill="#2C3138"/><path d="M-150 -130H150V70H-150Z" fill="#5E7B92"/><path d="M-130 -110L40 -110L-40 40H-130Z" fill="#7E9CB3" stroke="none"/>
 <path d="M-30 90V170M-110 170H110" fill="none" strokeWidth={22}/></g></BlurSvg>;
export const ForeLamp:React.FC<{x:number}>=({x})=><BlurSvg><g stroke={INK} strokeWidth={10}><path d={`M${x} 2200V1250`} stroke="#4A4038" strokeWidth={26}/><path d={`M${x-110} 1250L${x-70} 1080H${x+70}L${x+110} 1250Z`} fill="#E8C98A"/></g></BlurSvg>;

// ---------- impact: ink splash (stylised black/red-free ink, no gore) ----------
// t = frames since the hit. Big blobs + droplets fly out from the hit point and shrink away over ~10 frames.
export const InkSplash:React.FC<{x:number;y:number;t:number;s?:number;color?:string;seed?:number}>=({x,y,t,s=1,color=INK,seed=3})=>{
 if(t<0||t>7)return null;const u=t/7,k=1-u;
 return <svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}><g transform={`translate(${x} ${y}) scale(${s})`} fill={color}>
  {Array.from({length:9}).map((_,i)=>{const a=(i/9)*Math.PI*2+rnd(seed+i)*.5,d=(80+200*rnd(seed+i*3))*(.35+.65*Math.sqrt(u)),r=(18+26*rnd(seed+i*7))*k;
   return <g key={i}><ellipse cx={Math.cos(a)*d} cy={Math.sin(a)*d} rx={r*1.6} ry={r} transform={`rotate(${a*57.3} ${Math.cos(a)*d} ${Math.sin(a)*d})`}/>
    <circle cx={Math.cos(a)*d*1.35} cy={Math.sin(a)*d*1.35} r={r*.45}/><path d={`M${Math.cos(a)*30} ${Math.sin(a)*30}L${Math.cos(a+.08)*d} ${Math.sin(a+.08)*d}L${Math.cos(a-.08)*d} ${Math.sin(a-.08)*d}Z`}/></g>;})}
  <circle r={70*k*(t<2?1.2:1)}/></g></svg>;
};

// ---------- paper: sheets that jump on an impact, flutter and settle; or fall from above ----------
export const FlutterPaper:React.FC<{x:number;y:number;w:number;h:number;t:number;rot?:number;label?:string;seed?:number;size?:number}>=({x,y,w,h,t,rot=0,label,seed=1,size=22})=>{
 const tt=Math.max(0,t),up=t<0?0:-70*Math.exp(-tt/5)*Math.sin(Math.min(Math.PI,tt*.35)),flap=t<0?0:24*Math.exp(-tt/7)*Math.sin(tt*.9+seed),skew=t<0?0:14*Math.exp(-tt/6)*Math.sin(tt*1.3+seed);
 return <svg width={1080} height={1920} style={{position:'absolute',overflow:'visible'}}><g transform={`translate(${x+flap*.6} ${y+up}) rotate(${rot+flap*.5}) skewX(${skew})`} stroke={INK} strokeWidth={6}>
  <path d={`M${-w/2} ${-h/2}H${w/2}V${h/2}H${-w/2}Z`} fill="#FFF5DD"/>{label&&<text y={size*.35} textAnchor="middle" fontFamily="Quiet Sans" fontWeight={800} fontSize={size} fill={INK} stroke="none">{label}</text>}
 </g></svg>;
};
export const FallingPapers:React.FC<{t:number;n?:number;x0?:number;x1?:number;seed?:number}>=({t,n=4,x0=150,x1=930,seed=2})=>t<0?null:<svg width={1080} height={1920} style={{position:'absolute',overflow:'visible'}}>
 {Array.from({length:n}).map((_,i)=>{const st=rnd(seed+i)*8,tt=t-st;if(tt<0)return null;const x=x0+(x1-x0)*rnd(seed+i*5)+60*Math.sin(tt*.18+i),y=-80+tt*(9+3*rnd(i))+20*Math.sin(tt*.3+i);
  return <g key={i} transform={`translate(${x} ${y}) rotate(${40*Math.sin(tt*.22+i*2)}) scale(${Math.cos(tt*.25+i)} 1)`} stroke={INK} strokeWidth={5}><path d="M-46 -60H46V60H-46Z" fill="#FFF5DD"/><path d="M-30 -30H30M-30 -10H24M-30 10H30" stroke="#B4A58C"/></g>;})}
</svg>;

// ---------- night light flicker (multiplies the frame; a failing tube or a TV) ----------
export const flickerAt=(f:number,seed=1)=>{const b=Math.floor(f/2);const r=rnd(b*1.7+seed);return r<.06?.55:r<.12?.8:1;};
export const Flicker:React.FC<{amount?:number;seed?:number;color?:string}>=({amount=.35,seed=1,color='#0A0C1E'})=>{const f=useCurrentFrame(),v=flickerAt(f,seed);return v>=1?null:<AbsoluteFill style={{background:color,opacity:(1-v)*amount/.45,pointerEvents:'none'}}/>;};

// ---------- particles per set ----------
// Dust motes drifting in a light beam (screen polygon given as bounding box + slant).
export const Motes:React.FC<{box:[number,number,number,number];n?:number;color?:string;seed?:number}>=({box,n=26,color='#FFF8E6',seed=5})=>{const f=useCurrentFrame(),[x,y,w,h]=box;
 return <svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}>{Array.from({length:n}).map((_,i)=>{const px=x+((rnd(seed+i)*w+f*(.3+.4*rnd(i))+18*Math.sin(f*.03+i))%w),py=y+((rnd(seed+i*3)*h+f*(.5+.5*rnd(i*2)))%h),a=.35+.5*Math.abs(Math.sin(f*.05+i));
  return <circle key={i} cx={px} cy={py} r={1.6+2.4*rnd(i*9)} fill={color} opacity={a}/>;})}</svg>;};
// Rain streaks (draw in the window's outside layer, or full frame for exteriors). Redrawn every frame, slanted.
export const Rain:React.FC<{box?:[number,number,number,number];n?:number;slant?:number;color?:string;seed?:number;len?:number}>=({box=[0,0,1080,1920],n=70,slant=.18,color='#BFD6FF',seed=7,len=70})=>{const f=useCurrentFrame(),[x,y,w,h]=box;
 return <svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}>{Array.from({length:n}).map((_,i)=>{const sp=38+20*rnd(i*3),py=y+((rnd(seed+i)*h+f*sp)%h),px=x+((rnd(seed+i*5)*w-slant*f*sp)%w+w)%w;
  return <path key={i} d={`M${px} ${py}l${-slant*len} ${len}`} stroke={color} strokeWidth={2+2*rnd(i)} opacity={.35+.3*rnd(i*7)} strokeLinecap="round"/>;})}</svg>;};
// Rain beads running down a window pane
export const PaneDrops:React.FC<{box:[number,number,number,number];n?:number;seed?:number}>=({box,n=14,seed=3})=>{const f=useCurrentFrame(),[x,y,w,h]=box;
 return <svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}>{Array.from({length:n}).map((_,i)=>{const sp=1+3*rnd(i),py=y+((rnd(seed+i)*h+f*sp)%h),px=x+rnd(seed+i*5)*w;
  return <g key={i}><path d={`M${px} ${py-30*sp}L${px} ${py}`} stroke="#9FB8E8" strokeWidth={2} opacity={.5}/><circle cx={px} cy={py} r={4} fill="#CFE0FF" stroke={INK} strokeWidth={1.5} opacity={.8}/></g>;})}</svg>;};
