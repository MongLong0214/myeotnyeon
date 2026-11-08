import React from 'react';
import {AbsoluteFill,useCurrentFrame,staticFile} from 'remotion';
import {StageV6Fix} from './ArtV6Fix';
import data from '../../../../../episodes/v4/n18/cartoon_v6/episode_data_v6fix.json';
export const EpisodeV6Fix=()=>{
 const f=useCurrentFrame();const shot=data.shots.find(s=>f>=s.start&&f<s.end)??data.shots.at(-1)!;
 const cue=data.captions.find(c=>f>=c.start&&f<c.end);
 return <AbsoluteFill style={{backgroundColor:'#17152b',fontFamily:'N18V6Fix'}}>
  <style>{`@font-face{font-family:N18V6Fix;src:url(${staticFile('Pretendard-Bold.woff2')}) format('woff2');font-weight:700 900;}`}</style>
  <svg viewBox="0 0 1920 1080" style={{width:'100%',height:'100%'}}><StageV6Fix shot={shot} f={f}/></svg>
  {cue&&<div style={{position:'absolute',left:90,right:90,bottom:35,textAlign:'center',fontSize:51,lineHeight:1.22,fontWeight:800,color:'#fff4da',whiteSpace:'pre-wrap'}}>{cue.text}</div>}
 </AbsoluteFill>;
};
