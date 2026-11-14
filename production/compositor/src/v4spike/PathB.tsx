import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { commander, palette as C, project, recruits, Vec3 } from './scene';
import { Overlay, Texture } from './Overlay';

// Neutral capsule anatomy, back view. No hair, face, uniform or gender cues.
const silhouette = 'M-13-196 C-13-215 13-215 13-196 L13-185 Q12-176 6-173 L6-168 Q32-167 36-150 L43-106 Q45-97 37-96 Q30-96 28-106 L23-139 L24-104 L22-94 L20-14 Q20-5 11-5 Q3-5 3-14 L0-82 L-3-14 Q-3-5-11-5 Q-20-5-20-14 L-22-94 L-24-104 L-23-139 L-28-106 Q-30-96-37-96 Q-45-97-43-106 L-36-150 Q-32-167-6-168 L-6-173 Q-12-176-13-185 Z';

export const PathB: React.FC = () => {
  const f = useCurrentFrame();
  const {width:w, height:h} = useVideoConfig();
  const pt = (v: Vec3) => { const p=project(v,f,w,h); return `${p.x},${p.y}`; };
  const person = (v: Vec3, scale: number, main: boolean, i: number) => {
    const foot = project(v,f,w,h);
    const head = project([v[0],2.1*scale,v[2]],f,w,h);
    const k=(foot.y-head.y)/210;
    return <g key={i} transform={`translate(${foot.x} ${foot.y}) scale(${k})`}>
      <ellipse cx={16} cy={2} rx={main?66:40} ry={12} fill="#000" opacity=".7" filter="url(#soft)" />
      <g filter="url(#duotone)">
        <path d={silhouette} fill="url(#body)" stroke="#587DB7" strokeWidth={main?1.8:2.6} />
      </g>
      {main && <>
        <path d={silhouette} transform="translate(2.2 -1)" fill="none" stroke={C.red} strokeWidth={4} opacity={.6} filter="url(#rimGlow)" clipPath="url(#rightHalf)" />
        <path d={silhouette} fill="none" stroke={C.pink} strokeWidth={1.5} opacity={.6} clipPath="url(#rightHalf)" />
        <path d="M-9-177Q-3-173 5-176 M-19-159Q-7-153 3-157 M-14-105Q0-100 16-106 M-1-90L-1-48" fill="none" stroke="#315C9E" strokeWidth={1.2} opacity={.6} />
      </>}
    </g>;
  };
  return <AbsoluteFill style={{background:C.ink}}>
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <defs>
        <radialGradient id="space"><stop stopColor="#184B9D" stopOpacity=".9"/><stop offset=".55" stopColor={C.deepBlue}/><stop offset="1" stopColor={C.ink}/></radialGradient>
        <radialGradient id="redPool"><stop stopColor={C.red} stopOpacity=".32"/><stop offset="1" stopColor={C.red} stopOpacity="0"/></radialGradient>
        <linearGradient id="body" x1="0" x2="1"><stop stopColor="#94B5DF"/><stop offset=".2" stopColor="#446A9E"/><stop offset=".65" stopColor="#182337"/><stop offset="1" stopColor="#5A6B8C"/></linearGradient>
        <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#1B4283"/><stop offset="1" stopColor="#060A16"/></linearGradient>
        <filter id="duotone" colorInterpolationFilters="sRGB"><feColorMatrix type="matrix" values=".2126 .7152 .0722 0 0 .2126 .7152 .0722 0 0 .2126 .7152 .0722 0 0 0 0 0 1 0"/>
          <feComponentTransfer><feFuncR type="table" tableValues=".0196 .043 .19 .965"/><feFuncG type="table" tableValues=".0275 .14 .36 .65"/><feFuncB type="table" tableValues=".051 .40 .70 .70"/></feComponentTransfer></filter>
        <filter id="rimGlow" x="-100%" y="-50%" width="300%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>
        <filter id="soft" x="-50%" y="-100%" width="200%" height="300%"><feGaussianBlur stdDeviation="7"/></filter>
        <clipPath id="rightHalf"><rect x="2" y="-230" width="80" height="250"/></clipPath>
      </defs>
      <rect width={w} height={h} fill={C.ink}/>
      <ellipse cx={w*.47} cy={h*.45} rx={w*.85} ry={h*.38} fill="url(#space)"/>
      <polygon points={[[-12,0,-16],[12,0,-16],[12,0,6.5],[-12,0,6.5]].map(v=>pt(v as Vec3)).join(' ')} fill="url(#floor)"/>
      <polygon points={[[-6,0,-12],[-6,1.8,-12],[6,1.8,-12],[6,0,-12]].map(v=>pt(v as Vec3)).join(' ')} fill="#101F3F" stroke="#294B7E" strokeWidth={2}/>
      {Array.from({length:13},(_,i)=>i-6).map(x=><line key={x} x1={project([x*1.6,0,-14],f,w,h).x} y1={project([x*1.6,0,-14],f,w,h).y} x2={project([x*1.6,0,6.5],f,w,h).x} y2={project([x*1.6,0,6.5],f,w,h).y} stroke="#416498" opacity={.25} strokeWidth={1.5}/>)}
      {[-10,-7,-4,-1,2,5,6.5].map(z=><polyline key={z} points={[[-12,0,z],[12,0,z]].map(v=>pt(v as Vec3)).join(' ')} stroke="#416498" opacity={.25} strokeWidth={1.5}/>)}
      <polyline points={[[-3,0,-15],[-3,0,6.5]].map(v=>pt(v as Vec3)).join(' ')} stroke="#6096DE" opacity={.5} strokeWidth={5}/>
      <ellipse cx={project([1,0,.5],f,w,h).x} cy={project([1,0,.5],f,w,h).y} rx={w*.6} ry={h*.15} fill="url(#redPool)"/>
      {recruits.map((v,i)=>person(v,.82,false,i))}
      {person(commander,1.25,true,6)}
      <polygon points={[[3,0,2.5],[3,1.5,2.5],[3.2,1.5,2.5],[3.2,0,2.5]].map(v=>pt(v as Vec3)).join(' ')} fill="#111624" stroke={C.red} strokeWidth={3} opacity={.6}/>
    </svg>
    <Texture/><Overlay/>
  </AbsoluteFill>;
};
