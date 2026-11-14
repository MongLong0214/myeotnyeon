// Look-dev acting layer for the B format (opt-in; see look/LOOKDEV.md). Same characters, same rig, same outlines.
// Adds: spring follow-through on hands/head/torso/prop angles (pose cross-fades instead of pops), weight shifts,
// breathing, blinks, eye darts, emotion takes (acting.ts takeAt), Rhubarb-rule lip sync, a hand-pose library,
// a suit tie that swings, a cel/rim light filter hook and a flattened cast shadow.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {ArticulatedGuy,Expr,Look,RigPose,Point} from '../FightRig';
import {standing} from '../FightScene';
import {solve,breathe} from '../Kit';
import type {HandProps} from '../../../../../production/lf_toon/src/Hand';
import {takeAt,blinkAt,rnd} from '../../../../../production/lf_toon/src/acting';
import {jamo,VisemeMouth,type Viseme} from '../../../../../production/lf_toon/src/lipsync';
import {act,back} from '../../../../../production/lf_toon/src/motion';
import {charFilter,CharFilter,BlurCtx,type LightKey,LIGHTS,OFF} from './BLook';
export {act,back};

// ---------- springs ----------
// Second-order follower of x(f), simulated over the last n frames (frame-pure: any frame can render alone).
// hz ~ 3-6 for limbs, 2-3 for heads/ties; zeta .4 = lively overshoot, .7 = settle without much rebound.
export const followN=(xs:number[],hz:number,zeta:number)=>{
 // 4 semi-implicit Euler substeps per frame (lerping the target): stable up to ~12 hz
 const w=2*Math.PI*hz,dt=1/120;let y=xs[0],v=0;
 for(let i=1;i<xs.length;i++)for(let k=1;k<=4;k++){const x=xs[i-1]+(xs[i]-xs[i-1])*k/4,a=w*w*(x-y)-2*zeta*w*v;v+=a*dt;y+=v*dt;}
 return y;
};
export const follow=(fn:(f:number)=>number,f:number,hz=4,zeta=.55,n=24)=>followN(Array.from({length:n+1},(_,i)=>fn(f-n+i)),hz,zeta);

// ---------- pose cross-fade ----------
const mix=(a:number,b:number,w:number)=>a+(b-a)*w;
const mixP=(a:Point,b:Point,w:number):Point=>[mix(a[0],b[0],w),mix(a[1],b[1],w)];
export const blendRig=(a:RigPose,b:RigPose,w:number):RigPose=>({...(w<.5?a:b),hip:mixP(a.hip,b.hip,w),torso:mix(a.torso,b.torso,w),head:mix(a.head,b.head,w),
 feet:[mixP(a.feet[0],b.feet[0],w),mixP(a.feet[1],b.feet[1],w)],knees:[mixP(a.knees[0],b.knees[0],w),mixP(a.knees[1],b.knees[1],w)],
 hands:[mixP(a.hands[0],b.hands[0],w),mixP(a.hands[1],b.hands[1],w)],squash:mix(a.squash??0,b.squash??0,w)});
// Key poses on frames; each switch cross-fades over `fade` frames with an eased (smoothstep) weight.
export const poseKeys=(t:number,keys:[number,(r:RigPose)=>void][],fade=6):RigPose=>{
 const mk=(i:number)=>{const r=standing();keys[i][1](r);return r;};
 let i=0;while(i+1<keys.length&&t>=keys[i+1][0])i++;
 const r=mk(i),d=t-keys[i][0];
 if(i===0||d>=fade)return r;
 const u=d/fade,w=u*u*(3-2*u);return blendRig(mk(i-1),r,w);
};

// ---------- hands ----------
// Small library of hand poses that read correctly on this rig. Slot 0 is the anatomical right hand.
export type HandKind='relaxed'|'point'|'fist'|'open'|'grip'|'hold';
export const hand=(slot:0|1,kind:HandKind,object?:React.ReactNode,rot?:number):HandProps=>{
 const side=slot===0?'right':'left';
 if(kind==='grip'||kind==='hold'){const p:HandProps={pose:'grip',anchor:'wrist',side,object,wrap:'handle'};if(rot!==undefined)p.rot=rot;return p;}
 return {pose:kind,side};
};

// ---------- lip sync (Rhubarb timing rules on the lipsync.tsx chart) ----------
// 1. every viseme holds >= 2 frames; 2. ㅁ/ㅂ/ㅃ/ㅍ close the lips 1 frame BEFORE the syllable starts (and final ㅁ/ㅂ
// close at the end of a long syllable); 3. pauses shorter than 4 frames keep the last open shape (no flutter);
// 4. the whole track leads the audio by 1 frame.
const FINAL_LIPS=new Set([16,17,26]);
export const talkTrack=(text:string,on:number,off:number):{from:number;v:Viseme[]}=>{
 const parts=text.split(/[,.?!]/).map(s=>[...s].filter(ch=>jamo(ch))).filter(p=>p.length);
 const total=parts.reduce((a,p)=>a+p.length,0),pause=6,span=Math.max(1,off-on-pause*(parts.length-1));
 const from=on-1,n=off-on+2,v:Viseme[]=Array(n).fill('rest');
 const MED:Viseme[]=['AI','E','AI','E','E','E','E','E','O','AI','E','E','O','U','E','E','E','U','EU','E','E'];
 let cur=1;
 for(const p of parts){const d=span*p.length/total/p.length;
  p.forEach((ch,i)=>{const j=jamo(ch)!,a=Math.round(cur+i*d),b=Math.round(cur+(i+1)*d);
   for(let x=a;x<b&&x<n;x++)v[x]=MED[j.medial];
   if(FINAL_LIPS.has(j.final)&&b-a>=4){v[b-1]='MBP';v[b-2]='MBP';}
   if([6,7,8,17].includes(j.initial)){for(const x of [a-1,a])if(x>=0&&x<n)v[x]='MBP';}
  });
  cur+=span*p.length/total+pause;}
 // short rests inside a phrase keep the previous shape
 for(let i=1;i<n;i++)if(v[i]==='rest'){let j=i;while(j<n&&v[j]==='rest')j++;if(j<n&&j-i<4)for(let x=i;x<j;x++)v[x]=v[i-1];i=j;}
 // minimum hold of 2 frames
 for(let i=1;i<n-1;i++)if(v[i]!==v[i-1]&&v[i]!==v[i+1])v[i]=v[i-1];
 return {from,v};
};
export const visemeAt=(tr:{from:number;v:Viseme[]}|undefined,f:number):Viseme=>tr?(tr.v[f-tr.from]??'rest'):'rest';

// Angry talk keeps the clenched-teeth design; the viseme only sets how far the jaw drops (MBP closes it).
const OPEN:Record<Viseme,number>={rest:0,MBP:0,AI:1,E:.6,O:.75,U:.45,EU:.3};
const AngryMouth:React.FC<{open:number}>=({open})=>{const h=36+open*22,OLc='#1E1712';return <g>
 <rect x={-46} y={-410} width={92} height={h} rx={12} fill={open>0?'#5A1E1E':'#FFFFFF'} stroke={OLc} strokeWidth={6}/>
 <path d={`M-40 -404H40V-392H-40Z`} fill="#FFFFFF"/><path d={`M-40 ${-410+h-6}H40V${-410+h-16}H-40Z`} fill="#FFFFFF"/>
 {open===0&&<line x1={-46} y1={-392} x2={46} y2={-392} stroke={OLc} strokeWidth={4}/>}
 {[-23,0,23].map(x=><g key={x}><line x1={x} y1={-410} x2={x} y2={-392} stroke={OLc} strokeWidth={3}/><line x1={x} y1={-410+h-16} x2={x} y2={-410+h} stroke={OLc} strokeWidth={3}/></g>)}
 <rect x={-46} y={-410} width={92} height={h} rx={12} fill="none" stroke={OLc} strokeWidth={6}/>
</g>;};
// ---------- clothes ----------
// Suit collar + tie (the original Guy 'suit' design), pivoting at the knot and swinging on a spring.
const Tie:React.FC<{a:number}>=({a})=><g stroke="#1E1712" strokeWidth={5} strokeLinejoin="round">
 <path d="M-26,-318 L0,-262 L26,-318 Z" fill="#FFFFFF"/>
 <g transform={`rotate(${a} 0 -306)`}><path d="M-7,-306 L7,-306 L11,-236 L0,-222 L-11,-236 Z" fill="#C8372D"/></g>
</g>;

// ---------- the actor ----------
export type ActorOpt={
 look:Look;x:number;y:number;s:number;expr?:Expr;
 /** pose builder, pure in f (absolute frame). Runs before springs and IK. */
 pose?:(r:RigPose,f:number)=>void;ik?:{knee?:[Point,Point];elbow?:[Point,Point]};
 eye?:Point;seed?:number;light?:LightKey;cast?:boolean;
 /** spring follow-through per channel: [hz, zeta]; set a channel to null to keep it raw (e.g. a slam that must land on its frame). */
 springs?:{hands?:[number,number]|null;head?:[number,number]|null;torso?:[number,number]|null;props?:[number,number]|null};
 take?:{at:number;from:Expr;amt?:number};talk?:{from:number;v:Viseme[]};breath?:number;weight?:number;darts?:boolean;
 anonymous?:boolean;label?:string;
};
export const rigAt=(o:ActorOpt,f:number)=>{
 const r=standing(),ph=o.seed??0,b=o.breath??1;
 r.hands=[[-78,-118],[78,-118]];
 r.hip=[0,-170+1.8*b*breathe(f,ph)];r.torso=.5*b*breathe(f,ph+1.3);r.head=.8*breathe(f,ph+.7);
 r.handProps=[{pose:'relaxed'},{pose:'relaxed'}];
 // weight shift: the hips settle onto one foot, then the other, every 2.6-3.8 s
 if(o.weight){const per=78+Math.round(rnd(ph+3)*36),i=Math.floor((f+ph*40)/per),u=((f+ph*40)%per)/per,side=(i%2?1:-1),prev=-side;
  const w=prev+(side-prev)*Math.min(1,back(u*4,1.2));r.hip[0]+=o.weight*w;r.torso+=-.12*o.weight*w;r.head+=.08*o.weight*w;}
 o.pose?.(r,f);
 // breathing lifts both hands with the chest
 const lift=1.6*b*breathe(f,ph+.3);r.hands=[[r.hands[0][0],r.hands[0][1]+lift],[r.hands[1][0],r.hands[1][1]+lift]];
 return r;
};
export const Actor:React.FC<ActorOpt>=(o)=>{
 const f=useCurrentFrame(),N=OFF.has('acting')?2:14;
 const hist=Array.from({length:N+1},(_,i)=>rigAt(o,f-N+i)),r=hist[N];
 const sp={hands:[5.5,.55] as [number,number]|null,head:[3,.42] as [number,number]|null,torso:[4,.6] as [number,number]|null,props:[3.2,.38] as [number,number]|null,...o.springs};
 const ch=(get:(q:RigPose)=>number,c:[number,number]|null|undefined)=>c?followN(hist.map(get),c[0],c[1]):get(r);
 if(sp.hands)r.hands=[[ch(q=>q.hands[0][0],sp.hands),ch(q=>q.hands[0][1],sp.hands)],[ch(q=>q.hands[1][0],sp.hands),ch(q=>q.hands[1][1],sp.hands)]];
 // head follow-through: the head trails the torso, so a body move leaves the head behind for a few frames
 r.torso=ch(q=>q.torso,sp.torso);r.head=ch(q=>q.head,sp.head);
 // held props lag behind the wrist angle
 if(sp.props)r.handProps=r.handProps!.map((h,i)=>h.object&&typeof h.rot==='number'?{...h,rot:followN(hist.map(q=>(q.handProps?.[i]?.rot as number)??(h.rot as number)),sp.props![0],sp.props![1])}:h) as [HandProps,HandProps];
 // hand-shape switches: a 2-frame squeeze hides the pop
 r.handProps=r.handProps!.map((h,i)=>{const p1=hist[N-1].handProps?.[i]?.pose??'relaxed',p2=hist[N-2].handProps?.[i]?.pose??'relaxed';return (h.pose??'relaxed')!==p1?{...h,s:.86}:(h.pose??'relaxed')!==p2?{...h,s:.94}:h;}) as [HandProps,HandProps];
 solve(r,o.ik);
 // emotion take
 let expr=o.expr??'serious',y=o.y,sq=0,squint=0;
 if(o.take){const tt=(f-o.take.at)/30,k=takeAt(tt,o.take.amt??1);if(!k.after)expr=o.take.from;sq=k.sq;squint=k.squint;y+=k.dy*14*o.s;r.hip[0]+=-k.antic*10*(o.take.amt??1);}
 r.squash=(r.squash??0)+sq*2.2;
 // eyes: blink + saccades (2-4 frame holds are not needed: saccades are 1-frame moves)
 const bl=Math.max(blinkAt(f/30,(o.seed??0)*7+1),squint);
 const base=o.eye??[o.x<540?8:-8,1];
 const dart:Point=o.darts===false?[0,0]:(()=>{const per=40+Math.round(rnd((o.seed??0)+9)*30),i=Math.floor(f/per);const a=rnd(i*3.1+(o.seed??0)),c=rnd(i*5.7+(o.seed??0)+1);return [(a-.5)*7,(c-.5)*4];})();
 const v=visemeAt(o.talk,f),mouth=v==='rest'?undefined:(expr==='angry'?<AngryMouth open={OPEN[v]}/>:<VisemeMouth v={v}/>);
 const tie=o.look==='suit'&&!OFF.has('acting')?<Tie a={follow(q=>{const h=rigAt(o,q);return h.hip[0]*.9+h.torso*1.6;},f,2.2,.3,18)-(r.hip[0]*.9+r.torso*1.6)-r.torso*.4}/>:undefined;
 const L=o.light?LIGHTS[o.light]:undefined,fb=React.useContext(BlurCtx);
 const g=<ArticulatedGuy look={o.look} x={o.x} y={y} scale={o.s} rig={r} expr={expr} eye={[base[0]+dart[0],base[1]+dart[1]]} mouth={mouth} blink={bl} filter={o.light&&!OFF.has('charfx')?`url(#${charFilter(o.light,fb)})`:fb?`url(#lk-b${fb*2})`:undefined} torsoExtra={tie} anonymous={o.anonymous} label={o.label??'실존 인물과 무관한 원작 성인 카툰'}/>;
 return <>
  {fb>0&&<svg width={0} height={0} style={{position:'absolute'}}><defs>{o.light&&!OFF.has('charfx')?<CharFilter k={o.light} blur={fb}/>:<filter id={`lk-b${fb*2}`}><feGaussianBlur stdDeviation={fb}/></filter>}</defs></svg>}
  {o.cast&&L&&!OFF.has('cast')&&<div style={{position:'absolute',inset:0,transformOrigin:`${o.x}px ${o.y}px`,transform:`scale(1,${L.castLen}) skewX(${L.castSkew}deg)`}}>
   <ArticulatedGuy look={o.look} x={o.x} y={y} scale={o.s} rig={r} expr={expr} anonymous label="그림자" filter={`url(#lk-sil-${o.light})`}/></div>}
  {sq?<div style={{position:'absolute',inset:0,transformOrigin:`${o.x}px ${y}px`,transform:`scale(${1+sq*.3},${1-sq*.28})`}}>{g}</div>:g}
 </>;
};
// Screen position of a hand at frame f (raw pose + IK, no springs): for smears and trails on unsprung hands.
export const handScreen=(o:ActorOpt,f:number,i:0|1):Point=>{const r=rigAt(o,f);solve(r,o.ik);return [o.x+o.s*r.hands[i][0],o.y+o.s*r.hands[i][1]];};
