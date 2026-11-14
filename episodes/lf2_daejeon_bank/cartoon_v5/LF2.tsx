import React from 'react';
import {AbsoluteFill,Composition,registerRoot,staticFile,useCurrentFrame} from 'remotion';
import {Stage,C,SceneShot,SpeechFrame} from '../../../production/compositor/src/cartoon/engine_v5';
import data from './episode_data.json';
const font=`@font-face{font-family:ToonPretendard;src:url('${staticFile('Pretendard-ExtraBold.woff2')}') format('woff2');font-weight:800 900;font-display:block}`;
const shotAt=Array.from({length:data.durationInFrames},(_,f)=>data.shots.find(s=>s.start<=f&&f<s.end)??data.shots[data.shots.length-1]);
const captionAt=Array.from({length:data.durationInFrames},(_,f)=>data.captions.find(c=>c.startMs<=f/30*1000&&f/30*1000<c.endMs));
const keywords=/(\d[\d,.]*(?:년|월|일|억|만|명|개|대|심)?|총|마스크|무기징역|DNA|공범|증거|기각|신원불명|아니다)/g;
export const LF2:React.FC=()=>{
 const f=useCurrentFrame(),sh=shotAt[f],c=captionAt[f];
 const pop=c?1+.055*Math.exp(-(f-c.startMs*.03)/2.3):1;
 return <AbsoluteFill style={{background:C.ink}}><svg width="100%" height="100%" viewBox="0 0 1920 1080"><style>{font}</style><Stage shot={sh as SceneShot} f={f} speech={data.speech[f] as SpeechFrame}/><defs><linearGradient id="subshade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={C.ink} stopOpacity="0"/><stop offset=".6" stopColor={C.ink} stopOpacity=".94"/></linearGradient></defs><path d="M0 907H1920V1080H0Z" fill="url(#subshade)"/>{(sh.serious||sh.action==='spa'||f<90)&&<text x={55} y={65} fontFamily="ToonPretendard" fontWeight={800} fontSize={26} fill={C.paper} stroke={C.ink} strokeWidth={5} paintOrder="stroke">사실에 따른 재구성 · 인물 비식별</text>}{c&&<g transform={`translate(960 1009) scale(${pop})`}><text textAnchor="middle" fontFamily="ToonPretendard" fontWeight={900} fontSize={Math.min(65,1550/Math.max(1,c.text.length))} fill={C.paper} stroke={C.ink} strokeWidth={7} paintOrder="stroke" strokeLinejoin="round">{c.text.split(keywords).map((s,i)=><tspan key={i} fill={i%2?C.yellow:C.paper}>{s}</tspan>)}</text></g>}</svg></AbsoluteFill>;
};
registerRoot(()=><Composition id="LF2CartoonV5" component={LF2} width={1920} height={1080} fps={30} durationInFrames={data.durationInFrames}/>);
