import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {pose,Kind,PoseName} from './Beasts';
import {Animal,GEO} from './Rig';
const PS:PoseName[]=['idle','roar','charge','hit','dodge','win','tired'];
export const ModelSheet:React.FC<{kind:Kind}>=({kind})=>{const f=useCurrentFrame();const sc=380/Math.max(GEO[kind].top,(GEO[kind].reach+GEO[kind].back)*.75);
 return <AbsoluteFill style={{background:'#BFD8E8'}}><svg width={1080} height={1920}>
 {PS.map((p,i)=>{const x=i%2?800:270,y=400+Math.floor(i/2)*470;return <g key={p}><path d={`M${x-260} ${y}H${x+260}`} stroke="#7A8C99" strokeWidth={4}/><Animal kind={kind} x={x} y={y} s={sc} p={pose(p)} t={f+10}/><text x={x} y={y+44} textAnchor="middle" fontSize={36} fontFamily="sans-serif">{p}</text></g>;})}
 <g><path d="M540 1840H1060" stroke="#7A8C99" strokeWidth={4}/><Animal kind={kind} x={800} y={1840} s={sc} flip p={{...pose('roar'),rear:1,swipe:f/60} as never} t={f}/><text x={800} y={1884} textAnchor="middle" fontSize={36} fontFamily="sans-serif">rear+swipe (flip)</text></g>
 </svg></AbsoluteFill>;};
