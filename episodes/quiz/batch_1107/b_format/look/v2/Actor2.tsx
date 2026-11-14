// look v2 actor ("full2"): v1 Actor + hair sway, planted-foot walks, sit/stand, eye-led head turns, drawn brows and
// cheeks that move with emotion, voice-driven Rhubarb lip sync, emotional blinks, per-part cel shade (face + torso),
// fabric folds that follow the pose, tear/sweat FX, arm layering (arms crossed, head in hands), key-pose library with
// overlapping pose-to-pose. Same rig, same drawings, same ink: everything is drawn on the FightRig opt-in hooks.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {ArticulatedGuy,Expr,Look,RigPose,Point,skinOf} from '../../FightRig';
import {standing} from '../../FightScene';
import {solve,breathe} from '../../Kit';
import type {HandProps} from '../../../../../../production/lf_toon/src/Hand';
import {takeAt,blinkAt,rnd} from '../../../../../../production/lf_toon/src/acting';
import {VisemeMouth} from '../../../../../../production/lf_toon/src/lipsync';
import {back} from '../../../../../../production/lf_toon/src/motion';
import {BlurCtx,LIGHTS,OFF,type LightKey} from '../BLook';
import {followN,blendRig} from '../BActing';
import {lipAt,type Track2} from './Lip';
const INKC='#1E1712';
const sm=(u:number)=>{u=Math.max(0,Math.min(1,u));return u*u*(3-2*u);};
const mix=(a:number,b:number,w:number)=>a+(b-a)*w;
type RigS=RigPose&{sit?:number};

// ---------------- key-pose library (rig units; slot 0 = anatomical right = screen left) ----------------
export const POSE={
 lean:(r:RigPose,a:number,dir=1)=>{r.torso+=9*a*dir;r.hip[0]-=8*a*dir;r.head+=5*a*dir;},
 slump:(r:RigPose,a:number)=>{r.hip[1]+=10*a;r.torso+=-3*a;r.head+=-14*a;r.hands=[[mix(r.hands[0][0],-58,a),mix(r.hands[0][1],-104,a)],[mix(r.hands[1][0],58,a),mix(r.hands[1][1],-104,a)]];},
 recoil:(r:RigPose,a:number,dir=-1)=>{r.hip[0]+=18*a*dir;r.torso+=7*a*dir;r.head+=6*a*dir;r.hip[1]+=8*a;
  r.hands=[[mix(r.hands[0][0],-120,a),mix(r.hands[0][1],-350,a)],[mix(r.hands[1][0],115,a),mix(r.hands[1][1],-360,a)]];r.handProps=[{pose:a>.4?'open':'relaxed'},{pose:a>.4?'open':'relaxed'}];},
 point:(r:RigPose,a:number,side:1|-1=1)=>{const i=side>0?1:0;r.hands[i]=[mix(r.hands[i][0],side*235,a),mix(r.hands[i][1],-372,a)];
  r.hip[0]+=side*14*a;r.torso+=-side*3*a;r.head+=side*3*a;r.feet[i]=[r.feet[i][0]+side*28*a,r.feet[i][1]];
  r.handProps![i]={pose:a>.5?'point':'relaxed'};},
 // DISABLED until hand layering over the face is tested: throws so no episode can use it by accident.
 headInHands:(_r:RigPose,_a:number)=>{throw new Error('POSE.headInHands is disabled (hand layering untested)');},
 _headInHandsUntested:(r:RigPose,a:number)=>{r.head+=-12*a;r.torso+=-6*a;r.hip[1]+=6*a;r.hands=[[mix(r.hands[0][0],-128,a),mix(r.hands[0][1],-452,a)],[mix(r.hands[1][0],128,a),mix(r.hands[1][1],-452,a)]];r.handProps=[{pose:a>.5?'open':'relaxed'},{pose:a>.5?'open':'relaxed'}];},
 armsCrossed:(r:RigPose,a:number)=>{r.hands=[[mix(r.hands[0][0],52,a),mix(r.hands[0][1],-252,a)],[mix(r.hands[1][0],-56,a),mix(r.hands[1][1],-246,a)]];r.handProps=[{pose:'fist'},{pose:'fist'}];r.head+=2*a;},
 handsOnKnees:(r:RigPose,a:number)=>{r.hands=[[mix(r.hands[0][0],-46,a),mix(r.hands[0][1],-108,a)],[mix(r.hands[1][0],46,a),mix(r.hands[1][1],-108,a)]];r.handProps=[{pose:'relaxed'},{pose:'relaxed'}];},
};
// Pose-to-pose with overlap: hips/feet move first, torso 2 f later, arms 3 f, head 5 f (follow-through on top comes
// from the actor's springs).
export const poseKeys2=(t:number,keys:[number,(r:RigPose)=>void][],fade=10):RigPose=>{
 const mk=(i:number)=>{const r=standing();r.hands=[[-78,-118],[78,-118]];r.handProps=[{pose:'relaxed'},{pose:'relaxed'}];keys[i][1](r);return r;};
 let i=0;while(i+1<keys.length&&t>=keys[i+1][0])i++;
 const cur=mk(i);if(i===0)return cur;const d=t-keys[i][0];if(d>=fade+6)return cur;
 const prv=mk(i-1),w=(dl:number)=>sm((d-dl)/fade),o=blendRig(prv,cur,w(0)),wt=w(2),wa=w(3),wh=w(5);
 o.torso=mix(prv.torso,cur.torso,wt);o.head=mix(prv.head,cur.head,wh);
 o.hands=[[mix(prv.hands[0][0],cur.hands[0][0],wa),mix(prv.hands[0][1],cur.hands[0][1],wa)],[mix(prv.hands[1][0],cur.hands[1][0],wa),mix(prv.hands[1][1],cur.hands[1][1],wa)]];
 o.handProps=wa<.5?prv.handProps:cur.handProps;return o;
};
export const applyPose=(r:RigPose,p:RigPose)=>{r.hip=[...p.hip];r.torso=p.torso;r.head=p.head;r.feet=[[...p.feet[0]],[...p.feet[1]]];r.hands=[[...p.hands[0]],[...p.hands[1]]];r.handProps=p.handProps;r.squash=p.squash;};

// ---------------- planted-foot walk ----------------
// The character moves v px/frame (screen) from frame `from`. Each foot is planted (fixed in the world) for `stance` of
// the cycle and swings in an arc to its next plant, so feet never slide. Hips dip at each contact, arms counter-swing.
export type Walk={x0:number;v:number;from:number;to?:number;cycle?:number;stance?:number;lift?:number;arms?:number};
export const walkX=(w:Walk,f:number)=>w.x0+w.v*Math.max(0,Math.min(f,w.to??1e9)-w.from);
const walkLocal=(w:Walk,f:number,s:number)=>{
 const C=w.cycle??30,st=w.stance??.62,lift=w.lift??24,T=Math.max(0,Math.min(f,w.to??1e9)-w.from),X=walkX(w,f),moving=f>w.from&&f<(w.to??1e9);
 const feet:[Point,Point]=[[0,0],[0,0]];
 for(const i of [0,1]){const off=i*.5,ph=T/C+off,k=Math.floor(ph),u=ph-k;
  const plant=(kk:number)=>walkX(w,w.from+C*(kk-off)+st*C/2);
  let wx,wy=0;if(u<st)wx=plant(k);else{const us=(u-st)/(1-st);wx=mix(plant(k),plant(k+1),sm(us));wy=-lift*Math.sin(Math.PI*us);}
  if(T===0){wx=X;wy=0;}
  feet[i]=[(i?30:-30)+(wx-X)/s,wy];}
 const ph=T/C;return {feet,bob:moving?4*Math.cos(4*Math.PI*ph)-1:0,swing:moving?Math.sin(2*Math.PI*ph):0};
};

// ---------------- face: brows, cheeks, shade, tears/sweat ----------------
type Emo={raise:number;knit:number;cheek:number};
const EMO:Record<Expr,Emo>={angry:{raise:-.4,knit:1,cheek:1},serious:{raise:-.2,knit:.6,cheek:0},concern:{raise:.2,knit:-.9,cheek:0},scared:{raise:.6,knit:-1,cheek:0},
 tired:{raise:-.2,knit:-.7,cheek:.5},shock:{raise:1.2,knit:0,cheek:0},pain:{raise:0,knit:-1.2,cheek:1},smug:{raise:.1,knit:.2,cheek:.6},normal:{raise:0,knit:0,cheek:0},talk:{raise:.1,knit:0,cheek:0},dizzy:{raise:.3,knit:0,cheek:0}};
const FACE='M-118,-470 Q-124,-570 -40,-584 Q30,-596 92,-566 Q132,-540 124,-470 Q130,-400 96,-366 Q50,-334 0,-336 Q-60,-334 -96,-364 Q-128,-400 -118,-470 Z';
const TORSO='M-58,-170 Q-66,-300 -48,-318 L48,-318 Q66,-300 58,-170 Q0,-158 -58,-170 Z';
// Closed eyes (blinks, squints, crying): lids fill the eye in skin, with a lash arc that curves down (sad: slightly
// higher at the inner corner). Drawn over the rig's eye so no empty circle ever shows.
const ClosedEyes:React.FC<{big:boolean;sad:boolean;skin:string}>=({big,sad,skin})=>{const r=big?46:38;return <g>{[-36,36].map(x=><g key={x}>
 <circle cx={x} cy={-470} r={r+3} fill={skin} stroke={INKC} strokeWidth={6}/>
 <path d={`M${x-r+6} ${-468+(sad?(x<0?4:-4):0)}Q${x} ${-468+r*.55} ${x+r-6} ${-468-(sad?(x<0?4:-4):0)}`} fill="none" stroke={INKC} strokeWidth={7} strokeLinecap="round"/>
 <path d={`M${x+(x<0?-r+8:r-8)} -462l${x<0?-9:9} 6`} stroke={INKC} strokeWidth={5} strokeLinecap="round"/></g>)}</g>;};
const Brows:React.FC<{e:Emo;big:boolean;w:number}>=({e,big,w})=><g stroke={INKC} strokeWidth={w} strokeLinecap="round" fill="none">
 {[-1,1].map(s=>{const base=big?-544:-528,yo=base-12*e.raise-(e.knit>0?4*e.knit:-8*e.knit),yi=base-12*e.raise+(e.knit>0?16*e.knit:14*e.knit);
  return <path key={s} d={`M${s*74} ${yo}Q${s*46} ${Math.min(yo,yi)-7} ${s*16} ${yi}`}/>;})}
</g>;
const Cheeks:React.FC<{c:number;squint:number}>=({c,squint})=>c<=.05&&squint<=.05?null:<g stroke={INKC} strokeWidth={5} strokeLinecap="round" fill="none" opacity={Math.min(1,.4+c)}>
 {[-1,1].map(s=><path key={s} d={`M${s*44} ${-420-6*squint}Q${s*62} ${-430-8*squint} ${s*80} ${-420-6*squint}`}/>)}
</g>;
export type FX={tears?:[number,number];sweat?:[number,number]};
const Tears:React.FC<{t:number}>=({t})=>{const k=t%26,y=-430+k*3.2;return <g stroke={INKC} strokeWidth={3.5}>
 {[-1,1].map(s=><g key={s}><path d={`M${s*20} -434Q${s*36} -426 ${s*52} -434`} fill="#A6DDF4" strokeWidth={3}/>
  <path d={`M${s*48} -430Q${s*52} ${-430+(y+430)/2} ${s*50} ${y}`} fill="none" stroke="#7CC8FF" strokeWidth={7} strokeLinecap="round"/>
  <path d="M0 -10Q-8 4 0 10Q8 4 0 -10" transform={`translate(${s*50} ${y+8})`} fill="#A6DDF4"/></g>)}</g>;};
const SweatBead:React.FC<{t:number;side:number}>=({t,side})=>{const k=t%34,g=Math.min(1,k/8),sl=Math.max(0,k-8),x=side*(104+sl*.5),y=-532+sl*sl*.18;
 return <path d="M0 -14Q-11 4 0 12Q11 4 0 -14" transform={`translate(${x} ${y}) scale(${.5+.6*g})`} fill="#A6DDF4" stroke={INKC} strokeWidth={4}/>;};
const AngryMouth:React.FC<{open:number}>=({open})=>{const h=36+open*22;return <g>
 <rect x={-46} y={-410} width={92} height={h} rx={12} fill={open>0?'#5A1E1E':'#FFFFFF'} stroke={INKC} strokeWidth={6}/>
 <path d="M-40 -404H40V-392H-40Z" fill="#FFFFFF"/><path d={`M-40 ${-410+h-6}H40V${-410+h-16}H-40Z`} fill="#FFFFFF"/>
 {open===0&&<line x1={-46} y1={-392} x2={46} y2={-392} stroke={INKC} strokeWidth={4}/>}
 {[-23,0,23].map(x=><g key={x}><line x1={x} y1={-410} x2={x} y2={-392} stroke={INKC} strokeWidth={3}/><line x1={x} y1={-410+h-16} x2={x} y2={-410+h} stroke={INKC} strokeWidth={3}/></g>)}
 <rect x={-46} y={-410} width={92} height={h} rx={12} fill="none" stroke={INKC} strokeWidth={6}/></g>;};
// talking while sad/worried: frowning upper lip, no teeth, narrower opening (the open grin read as laughing)
const SadMouth:React.FC<{open:number;round:boolean}>=({open,round})=>{const w=round?20:32;return open<=0?<path d={`M${-w},-384 Q0,-400 ${w},-384`} stroke={INKC} strokeWidth={7} fill="none" strokeLinecap="round"/>:
 <path d={`M${-w},-384 Q0,-402 ${w},-384 Q${w*.6},${-380+20*open} 0,${-378+22*open} Q${-w*.6},${-380+20*open} ${-w},-384Z`} fill="#5A1E1E" stroke={INKC} strokeWidth={6} strokeLinejoin="round"/>;};
const Tie:React.FC<{a:number}>=({a})=><g stroke={INKC} strokeWidth={5} strokeLinejoin="round"><path d="M-26,-318 L0,-262 L26,-318 Z" fill="#FFFFFF"/>
 <g transform={`rotate(${a} 0 -306)`}><path d="M-7,-306 L7,-306 L11,-236 L0,-222 L-11,-236 Z" fill="#C8372D"/></g></g>;

// rim-only light filter for v2 (the shadow side is painted per part instead)
const tint=(hex:string,op:number)=>{const n=parseInt(hex.slice(1),16);return `0 0 0 0 ${(n>>16&255)/255} 0 0 0 0 ${(n>>8&255)/255} 0 0 0 0 ${(n&255)/255} 0 0 0 ${op} 0`;};
const RimFilter:React.FC<{id:string;k:LightKey;blur:number}>=({id,k,blur})=>{const L=LIGHTS[k],[dx,dy]=L.dir;return <filter id={id} x="-15%" y="-15%" width="130%" height="130%" colorInterpolationFilters="sRGB">
 <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  2.1 7.2 .72 0 -1" result="paint"/>
 <feOffset in="SourceAlpha" dx={dx*(L.shW+8)} dy={dy*(L.shW+8)} result="away"/><feComposite in="paint" in2="away" operator="out" result="shM"/>
 <feColorMatrix in="shM" type="matrix" values={tint(L.shadow,L.shadowOp*.7)} result="sh"/>
 <feOffset in="SourceAlpha" dx={-dx*(L.rimW+14)} dy={-dy*(L.rimW+14)} result="tow"/><feComposite in="paint" in2="tow" operator="out" result="rimM"/>
 <feColorMatrix in="rimM" type="matrix" values={tint(L.rim,Math.min(1,L.rimOp*1.15))} result="rim"/>
 <feMerge result="lit"><feMergeNode in="SourceGraphic"/><feMergeNode in="sh"/><feMergeNode in="rim"/></feMerge>
 {/* keep light strictly inside the opaque silhouette: no fringe outside the character */}
 <feComponentTransfer in="SourceAlpha" result="solid"><feFuncA type="linear" slope={1.6} intercept={-.6}/></feComponentTransfer>
 <feComposite in="lit" in2="solid" operator="in" result="inside"/>
 <feComposite in="SourceGraphic" in2="solid" operator="out" result="edge"/>
 <feMerge><feMergeNode in="edge"/><feMergeNode in="inside"/></feMerge>
 {blur>0&&<feGaussianBlur stdDeviation={blur}/>}</filter>;};

// ---------------- the actor ----------------
export type Actor2Opt={look:Look;x:number;y:number;s:number;expr?:Expr|((f:number)=>Expr);
 pose?:(r:RigPose,f:number)=>void;ik?:{knee?:[Point,Point];elbow?:[Point,Point]};eye?:Point;seed?:number;light?:LightKey;cast?:boolean;
 springs?:{hands?:[number,number]|null;head?:[number,number]|null;torso?:[number,number]|null;props?:[number,number]|null};
 take?:{at:number;from:Expr;amt?:number}[];talk?:Track2;breath?:number;weight?:number;darts?:boolean;anonymous?:boolean;label?:string;
 walk?:Walk;sit?:(f:number)=>number;seat?:number;lookAt?:(f:number)=>number;blinks?:number[];fx?:FX;
 arm0?:'back'|'front'|'top'|((f:number)=>'back'|'front'|'top');hairAmt?:number;shade?:boolean;folds?:boolean;
};
const exprAt=(o:Actor2Opt,f:number):Expr=>typeof o.expr==='function'?o.expr(f):(o.expr??'serious');
export const xAt=(o:Actor2Opt,f:number)=>o.walk?walkX(o.walk,f):o.x;
export const rig2At=(o:Actor2Opt,f:number)=>{
 const r=standing(),ph=o.seed??0,b=o.breath??1;
 r.hands=[[-78,-118],[78,-118]];r.hip=[0,-170+1.8*b*breathe(f,ph)];r.torso=.5*b*breathe(f,ph+1.3);r.head=.8*breathe(f,ph+.7);
 r.handProps=[{pose:'relaxed'},{pose:'relaxed'}];
 if(o.weight&&!o.walk){const per=78+Math.round(rnd(ph+3)*36),i=Math.floor((f+ph*40)/per),u=((f+ph*40)%per)/per,side=(i%2?1:-1);
  const w=-side+2*side*Math.min(1,back(u*4,1.2));r.hip[0]+=o.weight*w;r.torso+=-.12*o.weight*w;r.head+=.08*o.weight*w;}
 let sw=0;if(o.walk){const w=walkLocal(o.walk,f,o.s);r.feet=w.feet;r.hip[1]+=w.bob;sw=w.swing;}
 o.pose?.(r,f);
 if(o.lookAt)r.head+=5*o.lookAt(f);
 if(o.walk){const a=o.walk.arms??16;r.hands=[[r.hands[0][0]+a*sw,r.hands[0][1]-3*Math.abs(sw)],[r.hands[1][0]-a*sw,r.hands[1][1]-3*Math.abs(sw)]];}
 const st=o.sit?sm(o.sit(f)):0;
 if(st>0){const seat=o.seat??95;r.hip[1]=mix(r.hip[1],-seat,st);r.torso+=-16*Math.sin(Math.PI*st)+2*st;r.feet=[[-38,0],[38,0]];}
 const lift=1.6*b*breathe(f,ph+.3);r.hands=[[r.hands[0][0],r.hands[0][1]+lift],[r.hands[1][0],r.hands[1][1]+lift]];
 (r as RigS).sit=st;return r as RigS;
};
const solve2=(r:RigS,o:Actor2Opt)=>{solve(r,o.ik);const st=r.sit??0;if(st>0){const k=sm(st);r.knees=[[mix(r.knees[0][0],r.hip[0]-46,k),mix(r.knees[0][1],r.hip[1]-6,k)],[mix(r.knees[1][0],r.hip[0]+46,k),mix(r.knees[1][1],r.hip[1]-6,k)]];}return r;};
export const hand2Screen=(o:Actor2Opt,f:number,i:0|1):Point=>{const r=solve2(rig2At(o,f),o);return [xAt(o,f)+o.s*r.hands[i][0],o.y+o.s*r.hands[i][1]];};

export const Actor2:React.FC<Actor2Opt>=(o)=>{
 const f=useCurrentFrame(),N=20,X=xAt(o,f);
 const hist=Array.from({length:N+1},(_,i)=>rig2At(o,f-N+i)),r=hist[N],raw=hist.map(h=>({head:h.head,hipx:h.hip[0],hipy:h.hip[1],torso:h.torso}));
 const sp={hands:[5.5,.55] as [number,number]|null,head:[3,.42] as [number,number]|null,torso:[4,.6] as [number,number]|null,props:[3.2,.38] as [number,number]|null,...o.springs};
 const ch=(get:(q:RigPose)=>number,c:[number,number]|null|undefined)=>c?followN(hist.map(get),c[0],c[1]):get(r);
 if(sp.hands)r.hands=[[ch(q=>q.hands[0][0],sp.hands),ch(q=>q.hands[0][1],sp.hands)],[ch(q=>q.hands[1][0],sp.hands),ch(q=>q.hands[1][1],sp.hands)]];
 r.torso=ch(q=>q.torso,sp.torso);r.head=ch(q=>q.head,sp.head);
 if(sp.props)r.handProps=r.handProps!.map((h,i)=>h.object&&typeof h.rot==='number'?{...h,rot:followN(hist.map(q=>(q.handProps?.[i]?.rot as number)??(h.rot as number)),sp.props![0],sp.props![1])}:h) as [HandProps,HandProps];
 r.handProps=r.handProps!.map((h,i)=>{const p1=hist[N-1].handProps?.[i]?.pose??'relaxed',p2=hist[N-2].handProps?.[i]?.pose??'relaxed';return (h.pose??'relaxed')!==p1?{...h,s:.86}:(h.pose??'relaxed')!==p2?{...h,s:.94}:h;}) as [HandProps,HandProps];
 solve2(r,o);
 // expression + takes (several allowed)
 let expr=exprAt(o,f),y=o.y,sq=0,squint=0,pop=0;
 for(const tk of o.take??[]){const tt=(f-tk.at)/30;if(tt<-.4||tt>1.2)continue;const k=takeAt(tt,tk.amt??1);if(!k.after)expr=tk.from;sq+=k.sq;squint=Math.max(squint,k.squint);y+=k.dy*14*o.s;r.hip[0]+=-k.antic*10*(tk.amt??1);if(k.after)pop=Math.max(pop,Math.exp(-tt*5));}
 r.squash=(r.squash??0)+sq*2.2;
 // blinks: idle + emotional beats (takes and listed frames)
 const beat=[...(o.blinks??[]),...(o.take??[]).map(t=>t.at+8)].reduce((m,b)=>{const a=f-b;return a>=0&&a<5?Math.max(m,a<2?a/2+.5:1-(a-2)/3):m;},0);
 const bl0=Math.max(blinkAt(f/30,(o.seed??0)*7+1),squint,beat),closed=bl0>.75,bl=closed?undefined:bl0;
 // eyes lead the head: gaze target 3 frames ahead, head (sprung) follows
 const base=o.eye??[X<540?8:-8,1];
 const dart:Point=o.darts===false?[0,0]:(()=>{const per=40+Math.round(rnd((o.seed??0)+9)*30),i=Math.floor(f/per);return [(rnd(i*3.1+(o.seed??0))-.5)*7,(rnd(i*5.7+(o.seed??0)+1)-.5)*4];})();
 const gaze=o.lookAt?11*o.lookAt(f+3):0;
 // heavy lids (tired/smug/serious/pain or a half blink): drop the pupil below the lid line so it never vanishes
 const LID:Partial<Record<Expr,number>>={tired:.55,smug:.4,serious:.25,pain:.3},lidNow=Math.max(LID[expr]??0,bl??0),R0=expr==='shock'||expr==='scared'?46:38,drop=Math.max(0,Math.min(R0-10,-R0+2*R0*lidNow+9-base[1]));
 // mouth: voice track
 const lp=lipAt(o.talk,f),sad=expr==='concern'||expr==='tired'||expr==='scared'||expr==='pain',mouth=lp.v==='rest'?undefined:expr==='angry'?<AngryMouth open={lp.open}/>:sad?<SadMouth open={lp.v==='MBP'?0:lp.open} round={lp.v==='O'||lp.v==='U'}/>:<g transform={`translate(0 -392) scale(1 ${.7+.45*lp.open}) translate(0 392)`}><VisemeMouth v={lp.v}/></g>;
 // hair: sways against head rotation and hip motion, rings after impacts
 const hA=(o.hairAmt??1)*1.9,hf=(arr:number[],hz:number,z:number)=>followN(arr,hz,z)-arr[arr.length-1];
 const hair=hA?Math.max(-20,Math.min(20,hA*(1.7*hf(raw.map(q=>q.head),2.4,.2)+1.1*hf(raw.map(q=>q.torso),2.4,.22)-.35*hf(raw.map(q=>q.hipx),2.2,.25)))):0;
 const hairY=hA?Math.max(-.06,Math.min(.06,.006*hf(raw.map(q=>q.hipy),2.6,.2))):0;
 // emotion → brows / cheeks (pop on takes, lift with loud syllables)
 const E=EMO[expr]??EMO.normal,emo={raise:E.raise+.5*pop+.25*lp.open*(lp.v==='AI'||lp.v==='O'?1:.4),knit:E.knit,cheek:E.cheek+squint*.6};
 const L=o.light?LIGHTS[o.light]:undefined,fb=React.useContext(BlurCtx),lx=L?L.dir[0]:-.6,ly=L?L.dir[1]:-.8,cid=`a2-${o.look}-${o.seed??0}`;
 const shadeOn=o.shade!==false&&!!L&&!OFF.has('charfx'),big=expr==='shock'||expr==='scared';
 const tie=o.look==='suit'?<Tie a={followN(hist.map(q=>q.hip[0]*.9+q.torso*1.6),2.2,.3)-(r.hip[0]*.9+r.torso*1.6)-r.torso*.4}/>:undefined;
 const fx=o.fx??{},inR=(w?:[number,number])=>w&&f>=w[0]&&f<w[1];
 const headExtra=<>
  {shadeOn&&<g><clipPath id={cid+'f'}><path d={FACE}/></clipPath><g clipPath={`url(#${cid}f)`}><path fillRule="evenodd" d={`M-300 -800H300V-200H-300Z ${FACE}`} transform={`translate(${lx*46} ${ly*30})`} fill={L!.shadow} opacity={.55}/></g></g>}
  {!o.anonymous&&closed&&<ClosedEyes big={big} sad={emo.knit<0} skin={skinOf(o.look)}/>}
  {!o.anonymous&&<Brows e={emo} big={big} w={expr==='angry'||expr==='serious'?10:8}/>}
  {!o.anonymous&&<Cheeks c={emo.cheek} squint={squint}/>}
  {inR(fx.tears)&&<Tears t={f-fx.tears![0]}/>}
  {inR(fx.sweat)&&<><SweatBead t={f-fx.sweat![0]} side={1}/><SweatBead t={f-fx.sweat![0]+17} side={-1}/></>}
 </>;
 // torso: per-part shade + folds that follow the arms and the bend
 const sh0=-302,arm=[0,1].map(i=>Math.max(0,Math.min(1,(sh0-r.hands[i][1])/160)));
 const torsoExtra=<>
  {shadeOn&&<g><clipPath id={cid+'t'}><path d={TORSO}/></clipPath><g clipPath={`url(#${cid}t)`}><path fillRule="evenodd" d={`M-200 -400H200V-100H-200Z ${TORSO}`} transform={`translate(${lx*34} ${ly*16})`} fill={L!.shadow} opacity={.5}/></g></g>}
  {o.folds!==false&&<g stroke={INKC} strokeOpacity={.42} strokeWidth={4} fill="none" strokeLinecap="round">
   {[0,1].map(i=>{const s=i?1:-1,a=arm[i];return a>.08?<path key={i} d={`M${s*46} -300Q${s*(40-14*a)} ${-270+10*a} ${s*(30-20*a)} ${-250+30*a}M${s*50} -282Q${s*42} -262 ${s*(40-10*a)} -244`}/>:null;})}
   {Math.abs(r.torso)>3&&<path d={`M${Math.sign(r.torso)*-52} -196q${Math.sign(r.torso)*12} -6 ${Math.sign(r.torso)*20} 4M${Math.sign(r.torso)*-54} -214q${Math.sign(r.torso)*10} -5 ${Math.sign(r.torso)*16} 3`}/>}
   {(r.sit??0)>.4&&<path d="M-34 -196Q0 -186 34 -196M-24 -214Q0 -206 24 -214"/>}
  </g>}
  {tie}
 </>;
 // elbows: crease on the inner side when the arm bends (front arm always; back arm only when clear of the torso)
 const a0=typeof o.arm0==='function'?o.arm0(f):(o.arm0??'back');
 const rad=(a:number)=>a*Math.PI/180,rot=(p:Point,a:number):Point=>[p[0]*Math.cos(rad(a))-p[1]*Math.sin(rad(a)),p[0]*Math.sin(rad(a))+p[1]*Math.cos(rad(a))];
 const shp=(i:number):Point=>{const q=rot([i?50:-50,-132],r.torso);return [r.hip[0]+q[0],r.hip[1]+q[1]];};
 const rigExtra=o.folds===false?undefined:<g stroke={INKC} strokeOpacity={.5} strokeWidth={4} fill="none" strokeLinecap="round">{[0,1].map(i=>{
  const s=shp(i),e=r.elbows![i],h=r.hands[i],u1=[e[0]-s[0],e[1]-s[1]],u2=[h[0]-e[0],h[1]-e[1]],cr=u1[0]*u2[1]-u1[1]*u2[0],dt=u1[0]*u2[0]+u1[1]*u2[1],bend=Math.abs(Math.atan2(cr,dt))*180/Math.PI;
  if(bend<40)return null;if(i===0&&a0==='back'&&Math.abs(e[0]-r.hip[0])<75)return null;
  const n1=Math.hypot(u1[0],u1[1])||1,ox=-u1[1]/n1*Math.sign(cr)*7,oy=u1[0]/n1*Math.sign(cr)*7;
  return <path key={i} d={`M${e[0]+ox-u1[0]/n1*9} ${e[1]+oy-u1[1]/n1*9}Q${e[0]+ox*1.6} ${e[1]+oy*1.6} ${e[0]+ox+u2[0]/Math.hypot(u2[0],u2[1])*9} ${e[1]+oy+u2[1]/Math.hypot(u2[0],u2[1])*9}`}/>;})}</g>;
 const fid=`a2r-${o.light}-${fb*2}`;
 const g=<ArticulatedGuy look={o.look} x={X} y={y} scale={o.s} rig={r} expr={expr} eye={[base[0]+dart[0]+gaze,base[1]+(drop>0?Math.max(0,dart[1]):dart[1])+drop]} mouth={mouth} blink={bl}
  filter={o.light&&!OFF.has('charfx')?`url(#${fid})`:fb?`url(#lk-b${fb*2})`:undefined} torsoExtra={torsoExtra} headExtra={headExtra} rigExtra={rigExtra}
  hair={`translate(0 -500) skewX(${hair.toFixed(2)}) scale(1 ${(1+hairY).toFixed(3)}) translate(0 500)`} noBrows={!o.anonymous} arm0Layer={a0} anonymous={o.anonymous} label={o.label??'실존 인물과 무관한 원작 성인 카툰'}/>;
 return <>
  <svg width={0} height={0} style={{position:'absolute'}}><defs>{o.light&&!OFF.has('charfx')?<RimFilter id={fid} k={o.light} blur={fb}/>:fb?<filter id={`lk-b${fb*2}`}><feGaussianBlur stdDeviation={fb}/></filter>:null}</defs></svg>
  {o.cast&&L&&!OFF.has('cast')&&<div style={{position:'absolute',inset:0,transformOrigin:`${X}px ${o.y}px`,transform:`scale(1,${L.castLen}) skewX(${L.castSkew}deg)`}}>
   <ArticulatedGuy look={o.look} x={X} y={y} scale={o.s} rig={r} expr={expr} anonymous label="그림자" filter={`url(#lk-sil-${o.light})`}/></div>}
  {sq?<div style={{position:'absolute',inset:0,transformOrigin:`${X}px ${y}px`,transform:`scale(${1+sq*.3},${1-sq*.28})`}}>{g}</div>:g}
 </>;
};
