import React from 'react';
import {AbsoluteFill,useCurrentFrame,staticFile} from 'remotion';
import {StageV6Fix2} from './ArtV6Fix2';
import data from '../../../../../episodes/v4/n18/cartoon_v6/episode_data_v6fix2.json';
export const EpisodeV6Fix2=()=>{
 const f=useCurrentFrame();const shot=data.shots.find(s=>f>=s.start&&f<s.end)??data.shots.at(-1)!;
 const cue=data.captions.find(c=>f>=c.start&&f<c.end);
 const sf=shot.sourceStart+(f-shot.start);const staged={...shot,start:shot.sourceStart,end:shot.sourceEnd};
 return <AbsoluteFill style={{backgroundColor:'#17152b',fontFamily:'N18V6Fix2'}}>
  <style>{`@font-face{font-family:N18V6Fix2;src:url(${staticFile('Pretendard-Bold.woff2')}) format('woff2');font-weight:700 900;}`}</style>
  <svg viewBox="0 0 1920 1080" style={{width:'100%',height:'100%'}}><StageV6Fix2 shot={staged} f={sf}/><path d="M0 926H1920V1080H0Z" fill="#17152b"/></svg>
  {cue&&<div style={{position:'absolute',left:90,right:90,bottom:35,textAlign:'center',fontSize:51,lineHeight:1.22,fontWeight:800,color:'#fff4da',whiteSpace:'pre-wrap'}}>{cue.text}</div>}
 </AbsoluteFill>;
};
