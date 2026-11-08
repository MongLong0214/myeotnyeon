import React from 'react';
import data from './pilot_data.json';
import {C} from './Puppets';
// The pilot's only text layer. The atlas has its own production labels.
export const Subtitles:React.FC<{f:number}>=({f})=>{
 const cue=data.subtitles.find(c=>f>=c.from&&f<c.to);if(!cue)return null;
 const lines=cue.text.split('\n');return <g data-subtitles="true" fontFamily="Cartoon Pretendard" fontSize={46} fontWeight={700} fill={C.paper} stroke={C.ink} strokeWidth={8} paintOrder="stroke" strokeLinejoin="round" textAnchor="middle">{lines.map((line,i)=><text key={i} x={960} y={lines.length===1?1015:968+i*57}>{line}</text>)}</g>;
};
