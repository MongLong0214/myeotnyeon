import React from 'react';
import {AbsoluteFill,Audio,staticFile,useCurrentFrame} from 'remotion';
import {N18Stage} from './Art';
import {Captions} from './Captions';
import data from '../../../../../episodes/v4/n18/cartoon_v6/episode_data.json';
export const Episode=()=>{
 const f=useCurrentFrame();const shot=data.shots.find(s=>f>=s.start&&f<s.end)??data.shots.at(-1)!;
 const cue=data.captions.find(c=>f>=c.start&&f<c.end);
 return <AbsoluteFill style={{backgroundColor:'#17152b',fontFamily:'N18V6'}}>
  <style>{`@font-face{font-family:N18V6;src:url(${staticFile('Pretendard-Bold.woff2')}) format('woff2');font-weight:700 900;}`}</style>
  <svg viewBox="0 0 1920 1080" style={{width:'100%',height:'100%'}}><N18Stage shot={shot} f={f} shots={data.shots}/></svg>
  <Captions cue={cue}/><Audio src={staticFile('mix.wav')}/>
 </AbsoluteFill>;
};
