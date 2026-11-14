import React,{useEffect,useLayoutEffect,useMemo,useState} from 'react';
import {AbsoluteFill,useCurrentFrame,useVideoConfig,delayRender,continueRender,staticFile} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';
import * as THREE from 'three';
import {Beast,loadBeast,pose,gradientMap,INK} from './toon';
import {polarTint,crocTint} from './Lineup';

const fontHold=typeof document==='undefined'?null:delayRender('font');
if(fontHold!==null) new FontFace('Lilita',`url(${staticFile('fonts/LilitaOne-Regular.ttf')})`).load().then(f=>{document.fonts.add(f);continueRender(fontHold);});

const W=1080,H=1920,HIT=78,STOP=5;
const cl=(x:number,a=0,b=1)=>Math.min(b,Math.max(a,x));
const sm=(a:number,b:number,x:number)=>{const t=cl((x-a)/(b-a));return t*t*(3-2*t);};
const eo=(t:number)=>1-Math.pow(1-cl(t),3);
const lerp=(a:number,b:number,t:number)=>a+(b-a)*t;
const rnd=(i:number)=>{const x=Math.sin(i*127.1+311.7)*43758.5453;return x-Math.floor(x);};
const simFrame=(f:number)=>f<HIT?f:f<HIT+STOP?HIT:f-STOP;

type Actor={x:number;y:number;pitch:number;roll:number;yawAdd:number;sx:number;sy:number;phase:number};
type State={sf:number;u:number;bear:Actor;croc:Actor;cam:{pos:THREE.Vector3;tgt:THREE.Vector3;fov:number};shot:number};
const RE=92;
const adv=(re:number)=>re<=0?0:4.6*(re<18?re*re/36:re-9)/30; // u at which both charge again
export const stateAt=(f:number):State=>{
  const sf=simFrame(f),u=sf-HIT;
  const bear:Actor={x:0,y:0,pitch:0,roll:0,yawAdd:0,sx:1,sy:1,phase:0},croc:Actor={...bear};
  if(u<0){
    bear.x=-1.6-6.5*(-u)/30; croc.x=2.0+5.5*(-u)/30;
    bear.phase=sf/30/.80; croc.phase=sf/30/.85;
    const a=sm(-14,-5,u),d=sm(-4,0,u);               // leap up, then slam down
    bear.y=1.0*Math.sin(Math.PI*cl((u+14)/14)); bear.pitch=.55*a-.85*d;
    croc.pitch=.28*sm(-8,0,u); croc.y=.25*sm(-8,0,u);
  } else {
    // bear: rebound, rear up and roar, drop, charge again
    const rear=sm(2,14,u)*(1-sm(70,84,u));
    const back=eo(u/16);
    const re=Math.max(0,u-RE);
    bear.x=-1.6-1.1*back+ adv(re);
    bear.pitch=-.3*(1-sm(0,6,u))+1.05*rear+.05*rear*Math.sin(u*.9);
    bear.y=.35*rear; bear.sy=1+.06*rear*Math.sin(u*.9); bear.sx=1/bear.sy;
    bear.phase=HIT/30/.80+(re>0?re/30/.80:0)+.02*rear*Math.sin(u*.5);
    // croc: launched, barrel roll, lands, slides, shakes it off, charges again
    const air=cl(u/22),slide=eo((u-22)/20);
    croc.x=2.0+3.6*eo(u/22)+ (u>22?1.2*slide:0) - adv(re);
    croc.y=1.9*Math.sin(Math.PI*air)+(u<22?.25*(1-air):0);
    croc.roll=u<22?Math.PI*2*eo(u/22):0; croc.pitch=u<22?.28*(1-air)+.5*Math.sin(Math.PI*air):0;
    const land=u>=22?Math.exp(-(u-22)/5):0; croc.sy=1-.4*land; croc.sx=1+.3*land;
    const shake=sm(40,46,u)*(1-sm(66,74,u)); croc.yawAdd=.35*shake*Math.sin(u*1.3);
    croc.phase=HIT/30/.85+(u<22?u/30/.3:22/30/.3)+(re>0?re/30/.85:0);
  }
  // camera
  let pos=new THREE.Vector3(),tgt=new THREE.Vector3(),fov=40,shot=0;
  if(f<28){shot=1;const k=f/28; pos.set(bear.x+lerp(4.4,3.0,k),.55,lerp(2.6,1.9,k)); tgt.set(bear.x+.4,.95,0); fov=42;}
  else if(f<60){shot=2;const k=(f-28)/32; pos.set(croc.x-lerp(4.6,3.2,k),.35,lerp(2.4,1.7,k)); tgt.set(croc.x-.5,.55,0); fov=40;}
  else if(f<128){shot=3;const k=eo((f-60)/18),k2=sm(HIT+2,120,f); pos.set(lerp(-6.3,-5.5,k)+1.5*k2,lerp(1.5,1.2,k)+.3*k2,lerp(6.1,5.5,k)-.5*k2); tgt.set(k2*2.4,1.75,.4); fov=45;}
  else if(f<168){shot=4;const k=(f-128)/40; pos.set(croc.x-lerp(3.6,3.0,k),.5,lerp(2.9,2.3,k)); tgt.set(croc.x-.3,.6,0); fov=40;}
  else {shot=5;const mid=(bear.x+croc.x)/2; pos.set(croc.x+3.3,2.3,3.1); tgt.set(mid-.4,.7,0); fov=46;}
  const shake=(f>=HIT?.42*Math.exp(-(f-HIT)/8):0)+(f>=HIT+STOP+22?.2*Math.exp(-(f-HIT-STOP-22)/5):0);
  const sx=shake*Math.sin(f*17.3),sy=shake*Math.cos(f*23.1);
  pos.x+=sx*.6;pos.y+=sy;tgt.x+=sx*.8;tgt.y+=sy*.8;
  return {sf,u,bear,croc,cam:{pos,tgt,fov},shot};
};

// ---------- dust ----------
type Puff={b:number;x:number;y:number;z:number;vx:number;vy:number;vz:number;life:number;s:number};
const PUFFS:Puff[]=(()=>{const P:Puff[]=[];let n=0;const add=(b:number,x:number,z:number,vx:number,vy:number,vz:number,life:number,s:number)=>P.push({b,x,y:.1,z,vx,vy,vz,life,s});
  for(let sf=0;sf<210;sf+=2){const u=sf-HIT;const run=u<-6||u>RE+6; if(run){const st=stateAt(sf<HIT?sf:sf+STOP); for(const [a,dir] of [[st.bear,-1],[st.croc,1]] as [Actor,number][]){n++;add(sf,a.x+dir*(.8+rnd(n)*.6),(rnd(n+9)-.5)*.9,dir*1.2,.6+rnd(n+3)*.5,(rnd(n+5)-.5),16,.22+rnd(n+7)*.18);}}
    if(u>=22&&u<40){const st=stateAt(sf+STOP);n++;add(sf,st.croc.x+rnd(n)*1.6-.2,(rnd(n+2)-.5)*1.2,1.5,.5+rnd(n+1),(rnd(n+4)-.5)*1.5,18,.3+rnd(n+6)*.25);}}
  for(let i=0;i<18;i++){const a=i/18*Math.PI*2;add(HIT,.3,0,Math.cos(a)*(3+rnd(i)*2),1.2+rnd(i+20)*2.2,Math.sin(a)*(3+rnd(i+40)*2),20,.34+rnd(i+60)*.3);}
  for(let i=0;i<12;i++){const a=i/12*Math.PI*2;add(HIT+22,5.6,0,Math.cos(a)*2.6,.8+rnd(i+80)*1.4,Math.sin(a)*2.6,18,.3+rnd(i+90)*.25);}
  return P;})();


// ---------- rig shared by the 3D scene and the 2D face overlay ----------
type Part={P:THREE.Group;F:THREE.Group;face:number;b:Beast;clip:string;nose:number;top:number};
type Rig={bear:Part;croc:Part};
const makeRig=(bear:Beast,croc:Beast):Rig=>{ const mk=(b:Beast,face:number,suffix:string,headFrac:number):Part=>{const P=new THREE.Group(),F=new THREE.Group(); F.add(b.root); P.add(F);
    // head anchors from the base mesh (model faces +z before yaw): nose = max z, top = highest vertex in the head zone
    const p=b.meshes[0].geometry.attributes.position as THREE.BufferAttribute; let nose=0,top=-1,zmin=Infinity;
    for(let i=0;i<p.count;i++){ if(p.getZ(i)>p.getZ(nose)) nose=i; zmin=Math.min(zmin,p.getZ(i)); }
    const zc=p.getZ(nose)-headFrac*(p.getZ(nose)-zmin);
    for(let i=0;i<p.count;i++) if(p.getZ(i)>zc&&(top<0||p.getY(i)>p.getY(top))) top=i;
    return {P,F,face,b,clip:Object.keys(b.clips).find(k=>k.endsWith(suffix))||Object.keys(b.clips)[0],nose,top}; };
  return {bear:mk(bear,1,'B',.2),croc:mk(croc,-1,'runB',.3)}; };
const applyState=(rig:Rig,st:State)=>{ for(const [r,a] of [[rig.bear,st.bear],[rig.croc,st.croc]] as [Part,Actor][]){
    pose(r.b,r.clip,a.phase);
    r.P.position.set(a.x,a.y,0); r.P.rotation.y=(r.face<0?Math.PI:0)+a.yawAdd;
    r.F.position.y=r.b.size.y*.45; r.b.root.position.y=-r.b.size.y*.45;      // rotate about body centre
    r.F.rotation.set(a.roll,0,a.pitch); r.F.scale.set(a.sx,a.sy,a.sx);
    r.P.updateMatrixWorld(true); } };

const dustGeo=new THREE.IcosahedronGeometry(1,1);
const World:React.FC<{rig:Rig}> = ({rig})=>{
  const f=useCurrentFrame(); const {camera}=useThree(); const st=stateAt(f);
  useLayoutEffect(()=>{ applyState(rig,st);
    const c=camera as THREE.PerspectiveCamera; c.position.copy(st.cam.pos); c.fov=st.cam.fov; c.lookAt(st.cam.tgt); c.updateProjectionMatrix();
  });
  const scenery=useMemo(()=>{const o:React.ReactNode[]=[];
    for(let i=0;i<110;i++){const x=-30+rnd(i)*55,z=-9+rnd(i+200)*18,s=.4+rnd(i+400)*1.3; o.push(<mesh key={'p'+i} position={[x,.01+i*1e-4,z]} rotation={[-Math.PI/2,0,rnd(i+7)*3]} scale={[s*1.8,s*.7,1]}><circleGeometry args={[1,14]}/><meshBasicMaterial color={i%3?'#c79a52':'#ecd08f'}/></mesh>);}
    for(let i=0;i<46;i++){const side=i%2?1:-1,x=-30+rnd(i+900)*55,z=side>0?9+rnd(i+950)*5:-(2.6+rnd(i+950)*7),s=.25+rnd(i+970)*.7; o.push(<group key={'r'+i} position={[x,s*.35,z]} rotation={[rnd(i)*3,rnd(i+1)*3,0]} scale={[s*1.3,s*.8,s]}><mesh><dodecahedronGeometry args={[1,0]}/><meshToonMaterial color={i%4?'#8d8f9c':'#6f9a4d'} gradientMap={gradientMap()}/></mesh><mesh scale={1.07}><dodecahedronGeometry args={[1,0]}/><meshBasicMaterial color={INK} side={THREE.BackSide}/></mesh></group>);}
    for(let i=0;i<44;i++){const a=i/44*Math.PI*2,r=60+rnd(i+30)*14,h=7+rnd(i+60)*13; o.push(<mesh key={'h'+i} position={[Math.cos(a)*r,h/2-.5,Math.sin(a)*r]} ><coneGeometry args={[10+rnd(i+5)*9,h,5]}/><meshBasicMaterial color={i%2?'#7fae9c':'#5f958c'}/></mesh>);}
    for(let i=0;i<26;i++){const a=i/26*Math.PI*2+.1,r=95; o.push(<mesh key={'c'+i} position={[Math.cos(a)*r,24+rnd(i+11)*26,Math.sin(a)*r]} rotation={[0,-a+Math.PI/2+Math.PI,0]} scale={[9+rnd(i)*8,2.4+rnd(i+3)*1.6,1]}><circleGeometry args={[1,20]}/><meshBasicMaterial color="#fff7e6" side={THREE.DoubleSide}/></mesh>);}
    return o;},[]);
  const blob=(a:Actor,len:number)=><mesh position={[a.x,.03,0]} rotation={[-Math.PI/2,0,0]} scale={[len*.55/(1+a.y*.5),.6/(1+a.y*.5),1]}><circleGeometry args={[1,24]}/><meshBasicMaterial color="#5a3f1e" transparent opacity={.38}/></mesh>;
  return <>
    <color attach="background" args={['#8fd3e8']}/>
    <ambientLight intensity={1.35}/><directionalLight position={[-4,9,7]} intensity={2.4}/>
    <mesh rotation={[-Math.PI/2,0,0]}><planeGeometry args={[400,400]}/><meshBasicMaterial color="#dcb46c"/></mesh>
    {scenery}{blob(st.bear,2.6)}{blob(st.croc,3.6)}
    <primitive object={rig.bear.P}/><primitive object={rig.croc.P}/>
    {PUFFS.map((p,i)=>{const t=(st.sf-p.b)/p.life; if(t<0||t>=1||(st.sf===HIT&&f>HIT&&p.b>HIT)) return null; const d=(st.sf-p.b)/30,k=eo(t);
      return <mesh key={i} geometry={dustGeo} position={[p.x+p.vx*d*(1-.4*t),p.y+p.vy*d*(1-.5*t),p.z+p.vz*d*(1-.4*t)]} scale={p.s*(.5+1.6*k)}><meshBasicMaterial color="#f6e3b4" transparent opacity={.9*(1-t*t)}/></mesh>;})}
  </>;
};

// ---------- 2D overlay ----------
const camOf=(st:State)=>{const c=new THREE.PerspectiveCamera(st.cam.fov,W/H,.1,500); c.position.copy(st.cam.pos); c.lookAt(st.cam.tgt); c.updateMatrixWorld(); return c;};
const toPx=(c:THREE.Camera,v:THREE.Vector3)=>{const q=v.clone().project(c); return {x:(q.x+1)/2*W,y:(1-q.y)/2*H};};
// 2D eyes pinned to the morphed 3D head (hybrid test): expression is drawn, not modelled
type Mood='angry'|'dizzy'|'wide';
const Eyes:React.FC<{part:Part;st:State;mix:number;off:number;r:number;mood:Mood}> = ({part,st,mix,off,r,mood})=>{
  const m=part.b.meshes[0],c=camOf(st),N=new THREE.Vector3(),T=new THREE.Vector3();
  m.getVertexPosition(part.nose,N).applyMatrix4(m.matrixWorld); m.getVertexPosition(part.top,T).applyMatrix4(m.matrixWorld);
  const lat=new THREE.Vector3(1,0,0).transformDirection(m.matrixWorld),fwd=new THREE.Vector3(0,0,1).transformDirection(m.matrixWorld);
  const E=N.clone().lerp(T,mix),focal=(H/2)/Math.tan(st.cam.fov*Math.PI/360);
  const a=toPx(c,E),b2=toPx(c,E.clone().addScaledVector(fwd,.3)),flip=b2.x<a.x?-1:1;
  return <>{[1,-1].map(sgn=>{ const e=E.clone().addScaledVector(lat,sgn*off),toCam=c.position.clone().sub(e);
    if(lat.clone().multiplyScalar(sgn).addScaledVector(fwd,.25).dot(toCam)<=0) return null;
    const px=r*focal/toCam.length(),q=toPx(c,e),sw=Math.max(3,px*.22);
    return <g key={sgn} transform={`translate(${q.x},${q.y}) scale(${flip},1)`}>
      <ellipse rx={px} ry={px*(mood==='wide'?1.1:.9)} fill="#fffdf2" stroke="#1b1b26" strokeWidth={sw}/>
      {mood==='dizzy'?<path d={`M${-px*.55},${-px*.5}L${px*.55},${px*.5}M${-px*.55},${px*.5}L${px*.55},${-px*.5}`} stroke="#1b1b26" strokeWidth={sw*1.2} strokeLinecap="round"/>
        :<circle cx={px*.3} cy={px*.08} r={px*(mood==='wide'?.28:.45)} fill="#1b1b26"/>}
      {mood==='angry'&&<path d={`M${-px*1.25},${-px*1.25}L${px*1.2},${-px*.35}`} stroke="#1b1b26" strokeWidth={sw*1.9} strokeLinecap="round"/>}
    </g>; })}</>; };
const star=(n:number,r1:number,r2:number)=>Array.from({length:n*2},(_,i)=>{const a=i/(n*2)*Math.PI*2,r=i%2?r2:r1*(.85+.3*rnd(i));return `${Math.cos(a)*r},${Math.sin(a)*r}`;}).join(' ');
const Overlay:React.FC<{rig:Rig}> = ({rig})=>{ const f=useCurrentFrame(); const st=stateAt(f); const d=f-HIT; applyState(rig,st);
  const hit=toPx(camOf(st),new THREE.Vector3(.3,.9,0));
  const lines=(st.shot===1||st.shot===2||st.shot===5)?Array.from({length:22},(_,i)=>{const y=rnd(i+f*.0)*H,len=180+rnd(i+50)*420,ph=(rnd(i+90)+f*(.05+.03*rnd(i)))%1,dir=st.shot===2?-1:1; const x=dir>0?W+len-ph*(W+2*len):-len+ph*(W+2*len); return <rect key={i} x={x} y={y} width={len} height={5+rnd(i+3)*7} rx={4} fill="#fff" opacity={.55*(y<H*.3||y>H*.72?1:.25)}/>;}):null;
  return <AbsoluteFill>
    <svg width={W} height={H} style={{position:'absolute'}}>
      {lines}
      <Eyes part={rig.bear} st={st} mix={.62} off={.2} r={.085} mood={st.u>8&&st.u<70?'wide':'angry'}/>
      <Eyes part={rig.croc} st={st} mix={.92} off={.17} r={.085} mood={st.u>=0&&st.u<62?'dizzy':'angry'}/>
      {d>=0&&d<11&&<g transform={`translate(${hit.x},${hit.y}) rotate(${d*3}) scale(${.3+.55*eo(d/4)})`} opacity={1-sm(6,11,d)}>
        <polygon points={star(11,330,150)} fill="#ffd23c" stroke="#1b1b26" strokeWidth={14} strokeLinejoin="round"/>
        <polygon points={star(9,190,80)} fill="#fff8e0"/></g>}
    </svg>
    {d>=2&&d<34&&<div style={{position:'absolute',left:0,width:W,top:250,textAlign:'center',fontFamily:'Lilita',fontSize:210,color:'#ff4b3a',WebkitTextStroke:'22px #1b1b26',paintOrder:'stroke fill',transform:`rotate(-7deg) scale(${.4+.75*eo((d-2)/5)+.03*Math.sin(d)})`,opacity:1-sm(26,34,d)}}>CRUNCH!</div>}
    {/* single impact flash: one rise/fall, well under 3 flashes per second */}
    {d>=0&&d<4&&<AbsoluteFill style={{background:'#fff',opacity:[.7,.45,.22,.08][d]}}/>}
  </AbsoluteFill>; };

export const Shot:React.FC=()=>{ const {width,height}=useVideoConfig(); const [rig,set]=useState<Rig|null>(null); const [h]=useState(()=>delayRender('glb'));
  useEffect(()=>{ Promise.all([loadBeast('bear',{length:2.6,yaw:Math.PI/2,outline:.024,tint:polarTint}),loadBeast('alligator',{length:3.6,yaw:Math.PI/2,outline:.024,tint:crocTint})]).then(b=>{set(makeRig(b[0],b[1]));continueRender(h);}); },[h]);
  return <AbsoluteFill style={{background:'#8fd3e8'}}>
    {rig&&<ThreeCanvas width={width} height={height} flat camera={{fov:40,near:.1,far:500,position:[0,2,8]}}><World rig={rig}/></ThreeCanvas>}
    {rig&&<Overlay rig={rig}/>}
  </AbsoluteFill>; };
