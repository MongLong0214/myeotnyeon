import React from 'react';
import {AbsoluteFill,Composition,registerRoot,staticFile,useCurrentFrame} from 'remotion';
import {Stage,C,CinematicShot,SpeechFrame} from '../../../production/compositor/src/cartoon/engine_v6';
import {ActedStage,Performance} from '../../../production/compositor/src/cartoon/engine_v6/ActedStage';
import data from './episode_data.json';
const font=`@font-face{font-family:ToonPretendard;src:url('${staticFile('Pretendard-ExtraBold.woff2')}') format('woff2');font-weight:800 900;font-display:block}`;
const shotAt=Array.from({length:data.durationInFrames},(_,f)=>data.shots.find(s=>s.start<=f&&f<s.end)??data.shots[data.shots.length-1]);
const captionAt=Array.from({length:data.durationInFrames},(_,f)=>data.captions.find(c=>Math.round(c.startMs*.03)<=f&&f<Math.ceil(c.endMs*.03)));
const keywords=/(\d[\d,.]*(?:년|월|일|억|만|명|개|대|심)?|총|마스크|무기징역|DNA|공범|증거|기각|신원불명|아니다)/g;
export const LF2:React.FC=()=>{
 const f=useCurrentFrame(),sh=shotAt[f],c=captionAt[f];
 return <AbsoluteFill style={{background:C.ink}}><svg width="100%" height="100%" viewBox="0 0 1920 1080"><style>{font}</style>{'performance' in sh?<ActedStage performance={sh.performance as unknown as Performance} f={f}/>:<Stage shot={sh as CinematicShot} f={f} speech={data.speech[f] as SpeechFrame}/>}<defs><linearGradient id="subshade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={C.ink} stopOpacity="0"/><stop offset=".5" stopColor={C.ink} stopOpacity=".97"/></linearGradient></defs><path d="M0 905H1920V1080H0Z" fill="url(#subshade)"/>{c&&<text x={960} y={1009} textAnchor="middle" fontFamily="ToonPretendard" fontWeight={900} fontSize={Math.min(64,1700/Math.max(1,c.text.length))} fill={C.paper} stroke={C.ink} strokeWidth={7} paintOrder="stroke" strokeLinejoin="round">{c.text.split(keywords).map((s,i)=><tspan key={i} fill={i%2?C.yellow:C.paper}>{s}</tspan>)}</text>}</svg></AbsoluteFill>;
};
registerRoot(()=><Composition id="LF2CartoonV6" component={LF2} width={1920} height={1080} fps={30} durationInFrames={data.durationInFrames}/>);
