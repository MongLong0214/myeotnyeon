import React from 'react';
import {AbsoluteFill,Audio,Composition,registerRoot,staticFile,useCurrentFrame,Still} from 'remotion';
import {Stage,Puppet,C,SceneShot,Glyph} from '../../../production/compositor/src/cartoon/engine_v4';
import data from './episode_data.json';
export const wrapCaption=(text:string)=>{
 if(text.length<=38)return [text];
 const words=text.split(' ');let best=1,cost=Infinity;
 for(let i=1;i<words.length;i++){const a=words.slice(0,i).join(' '),b=words.slice(i).join(' ');const d=Math.abs(a.length-b.length);if(d<cost){cost=d;best=i}}
 return [words.slice(0,best).join(' '),words.slice(best).join(' ')];
};
const font=`@font-face{font-family:ToonPretendard;src:url('${staticFile('Pretendard-Bold.woff2')}') format('woff2');font-weight:700;font-display:block}`;
export const LF2:React.FC=()=>{
 const f=useCurrentFrame();const shot=data.shots.find(s=>f>=s.start&&f<s.end)??data.shots[data.shots.length-1];
 const caption=data.captions.find(c=>f/30>=c.startMs/1000&&f/30<c.endMs/1000);const lines=caption?wrapCaption(caption.text):[];
 return <AbsoluteFill style={{background:C.ink}}><Audio src={staticFile('soundtrack.wav')}/><svg width="100%" height="100%" viewBox="0 0 1920 1080"><style>{font}</style><Stage shot={shot as SceneShot} f={f} speech={data.speech[f] as any}/>{((f<60)||(f>=240&&f<300))&&<g><rect x={54} y={46} width={441} height={48} rx={12} fill="#192631" opacity={.85}/><text x={76} y={79} fontFamily="ToonPretendard" fontSize={25} fontWeight={700} fill={C.paper}>재구성 · 인물과 공간은 가상</text></g>}{lines.map((text,i)=><text key={i} x={960} y={lines.length===1?1015:985+i*57} fontFamily="ToonPretendard" fontSize={43} fontWeight={700} fill={C.paper} textAnchor="middle" stroke="#192631" strokeWidth={3} paintOrder="stroke">{text}</text>)}</svg></AbsoluteFill>;
};
const Atlas:React.FC=()=>{
 const roles=['host','employee','analyst','detective','judge','robberA','defendantB','police'] as const;
 const views=['front','three-quarter','profile','back'] as const;
 return <AbsoluteFill style={{background:C.paper}}><svg viewBox="0 0 3200 3600"><style>{font}</style>{roles.map((role,row)=>views.map((view,col)=><g key={role+view}><rect x={col*800+10} y={row*450+10} width={780} height={430} rx={25} fill={row%2?'#d3dfcf':'#e5ddc3'} stroke={C.line} strokeWidth={3}/><Puppet role={role} view={view} x={col*800+398} y={row*450+410} scale={.72} f={71+row*13} expr={row%3===0?'alarm':row%3===1?'skeptic':'resolve'} gesture={col===0?'shrug':col===1?'point':col===2?'read':'rest'} mouth={.8} viseme={role==='host'?'A':'rest'} seed={row+1}/></g>))}</svg></AbsoluteFill>;
};
registerRoot(()=><><Composition id="LF2CartoonV4" component={LF2} width={1920} height={1080} fps={30} durationInFrames={data.durationInFrames}/><Still id="PuppetAtlasV4" component={Atlas} width={3200} height={3600}/></>);
