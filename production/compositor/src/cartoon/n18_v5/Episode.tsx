import React from 'react';
import {AbsoluteFill,Audio,staticFile,useCurrentFrame} from 'remotion';
import {N18Stage} from './Art';
import data from '../../../../../episodes/v4/n18/cartoon_v5/episode_data.json';
const marks=/(학대치사|교육 목적|쓰러졌습니다|규정 위반|예방할 수|징역 [0-9]+년(?: [0-9]+개월)?|확정)/g;
export const Episode:React.FC=()=>{
 const f=useCurrentFrame();const shot=data.shots.find(s=>f>=s.start&&f<s.end)??data.shots[data.shots.length-1];
 const cue=data.captions.find(c=>f>=c.start&&f<c.end);
 const pop=cue?Math.min(1,(f-cue.start)/3):1;
 return <AbsoluteFill style={{backgroundColor:'#17152b',fontFamily:'N18V5'}}>
  <style>{`@font-face{font-family:N18V5;src:url(${staticFile('Pretendard-Bold.woff2')}) format('woff2');font-weight:700 900;}`}</style>
  <svg viewBox="0 0 1920 1080" style={{width:'100%',height:'100%'}}><N18Stage shot={shot} f={f} speech={data.speech[f]??{amplitude:0,viseme:'rest'}}/></svg>
  <div style={{position:'absolute',left:65,top:34,fontSize:26,color:'#fff5db',textShadow:'0 2px 5px #17152b'}}>보도 내용의 개념적 재구성 · 인물 비식별</div>
  {cue&&<div style={{position:'absolute',left:90,right:90,bottom:37,minHeight:89,display:'flex',justifyContent:'center',alignItems:'center',textAlign:'center'}}><div style={{fontSize:62,lineHeight:1.19,fontWeight:900,color:'#fff7e4',padding:'14px 28px 17px',borderRadius:12,background:'rgba(19,18,35,.93)',textShadow:'0 3px 2px #080811',transform:`scale(${.99+pop*.01})`}}>{cue.text.split(marks).map((t,i)=><span key={i} style={{color:/학대치사|교육 목적|쓰러졌습니다|규정 위반|예방할 수|징역 \d|확정/.test(t)?'#edff65':undefined}}>{t}</span>)}</div></div>}
  <Audio src={staticFile('mix.wav')}/>
 </AbsoluteFill>;
};
