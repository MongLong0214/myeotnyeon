import React from 'react';
import {AbsoluteFill,Audio,Composition,Sequence,Still,staticFile,useCurrentFrame} from 'remotion';
import {N18Art,ArtDefs,Person,Finish,C} from './N18Art';
import film from './n18-film-fast.json';
import {ChapterCard,Date,Caption,Note,Record,EvidenceLabel,MeasurementLabel} from './PilotType';
import {white,red,Texture} from '../type2/Type';

type Shot = (typeof film.shots)[number];
const font='T2 Myeongjo';
const Dossier:React.FC<{variant:number}> = ({variant}) => {
 const f=useCurrentFrame(),p=f/150;
 return <><svg width="1920" height="1080"><ArtDefs/><rect width="1920" height="1080" fill={C.ink}/>
 <ellipse cx="300" cy="400" rx="1000" ry="700" fill="url(#n18-red)" opacity=".65"/><ellipse cx="1530" cy="520" rx="950" ry="700" fill="url(#n18-blue)"/>
 <g transform={`translate(${variant%2?45:-35} ${-p*12}) rotate(${variant%2?2:-2} 960 540)`}>
 {[0,1,2,3].map(i=><g key={i} transform={`translate(${200+i*19} ${200+i*17})`}><path d="M0 0H1250L1380 110V650H0Z" fill={i===3?'#090d26':'#080a18'} stroke={i===3?'#5e5fc1':'#292959'} strokeWidth="2"/>{i===3&&<><path d="M1250 0V110H1380 M65 170H1260 M65 510H1260" fill="none" stroke="#5260c1" opacity=".6"/><path d="M65 230H510M65 270H430M65 310H550" stroke="#303f88" strokeWidth="4"/></>}</g>)}
 </g><path d="M1350 0L1700 0L1060 1080H740Z" fill="url(#n18-beam)" filter="url(#n18-soft)"/></svg><Finish/></>;
};
const Relationship:React.FC<{multiple:boolean;close:boolean}> = ({multiple,close}) => {
 const f=useCurrentFrame();const p=Math.min(1,f/120);
 return <svg width="1920" height="1080" style={{position:'absolute',inset:0}}><ArtDefs/>
 <g transform={`translate(960 545) scale(${(close?1.09:1)+p*.025}) translate(-960 -545)`}>
 <rect x="365" y="310" width="1190" height="420" rx="2" fill="#03040b" opacity=".92"/>
 {[0,1,2,3,4,5].map(i=><g key={i}><Person x={540+i*166} y={620} scale={.66}/><path d={multiple?`M${540+i*166} 640v42`:`M${540+i*166} 640v18`} stroke="#a6adc3" strokeWidth="2" opacity=".6"/>{multiple&&<path d={`M${508+i*166} 690h64`} stroke="#a6adc3" strokeWidth="3"/>}</g>)}
 {!multiple&&<path d="M540 658H1370 M960 658v35 M880 698H1040" fill="none" stroke="#a6adc3" strokeWidth="3"/>}
 </g></svg>;
};
const ShotView:React.FC<{shot:Shot;index:number}> = ({shot,index}) => {
 const f=useCurrentFrame();const caption=film.subtitles.find(s=>s.from_<=shot.from+f&&s.to>shot.from+f);
 const local=f/Math.max(1,shot.dur), v=index%4;
 if(shot.kind==='silence')return <AbsoluteFill style={{background:shot.id==='S099'?'#000':'#03040b'}}/>;
 const isChapter=shot.kind==='chapter';
 const camera=`translate(${v===0?-22:v===1?18:v===2?-42:28}px,${-local*9}px) scale(${(v%2?1.105:1.015)+.025*local})`;
 return <AbsoluteFill style={{background:C.ink,fontFamily:font,color:C.white,overflow:'hidden'}}>
 <AbsoluteFill style={{transform:camera,transformOrigin:v%2?'63% 48%':'44% 50%'}}>
 {shot.art==='dossier'?<Dossier variant={index}/>:<N18Art kind={shot.art==='diagram'?'verdict':shot.art as 'opening'|'spatial'|'verdict'} empty={shot.empty}/>}
 </AbsoluteFill>
 {(isChapter||shot.kind==='credits')&&<AbsoluteFill style={{background:'rgba(3,4,11,.68)'}}/>}
 {isChapter?<ChapterCard revealFrames={9} number={shot.chapterTitle.slice(0,2)} title={shot.chapterTitle.slice(3)}/>: shot.kind==='credits'?<div style={{position:'absolute',left:190,top:255,width:1540}}><div data-safe style={{fontFamily:'T2 Song',fontSize:43,color:white,marginBottom:45}}>출처 · 보도 원문</div><div data-safe style={{fontFamily:'T2 Myeongjo',fontSize:47,fontWeight:400,lineHeight:1.9}}>{shot.lines.join(' · ')}</div><div data-safe style={{fontFamily:'T2 Coding',fontSize:25,marginTop:48,color:'#b2b2a9'}}>원문 URL과 발행일은 영상 설명에 수록했습니다.</div><div data-safe style={{fontFamily:'T2 Coding',fontSize:25,marginTop:30,color:'#b2b2a9'}}>화면은 직접 그린 재구성·개념도입니다. 실제 배치와 다릅니다.</div></div>:
 <>{shot.art==='diagram'&&<Relationship multiple={shot.multiple} close={index%2===1}/>}
 {shot.art==='diagram'?<div data-safe style={{position:'absolute',left:190,top:220,width:1540,textAlign:'center',fontFamily:'T2 Myeongjo',fontSize:49,fontWeight:400,letterSpacing:'-.045em',color:white}}>{shot.lines.join(' · ')}</div>:
 shot.art==='spatial'?<MeasurementLabel labelAt={8} revealFrames={9} text={shot.lines.join(' · ')}/>:shot.lines.length>0&&<Record lines={shot.lines} category={shot.category} numeric={shot.numeric}/>}
 <div data-safe style={{position:'absolute',left:108,top:64,fontFamily:'T2 Song',fontSize:23,color:white}}>{shot.chapterLabel}</div>
 {shot.date&&<Date text={shot.date}/>}
 {shot.art==='opening'&&!shot.empty&&shot.lines.length===0&&<EvidenceLabel text="중대장" x={570} y={275}/>}
 {shot.label&&<Note text={shot.label} top={845}/>}
 {shot.source&&<Note text={shot.source} top={1040}/>}
 {caption&&<Caption text={caption.text}/>}

 </>}
 </AbsoluteFill>;
};
export const N18Full:React.FC<{audio?:boolean;fastPreview?:boolean}> = ({audio=true,fastPreview=false}) => <AbsoluteFill>{fastPreview&&<style>{'[filter]{filter:none!important}'}</style>}{film.shots.map((shot,index)=><Sequence key={shot.id} from={shot.from} durationInFrames={shot.dur}><ShotView shot={shot} index={index}/></Sequence>)}{audio&&<Audio src={staticFile('pilot_n18/mix_master_fast.wav')}/>}</AbsoluteFill>;
export const N18Thumb:React.FC<{variant?:'a'|'b'}> = ({variant='a'}) => <AbsoluteFill style={{background:'#10110f',fontFamily:'T2 Black',color:white,overflow:'hidden'}}>
 <div style={{width:1920,height:1080,transform:'scale(.6666667)',transformOrigin:'0 0',filter:'saturate(.25) brightness(.7)'}}><N18Art kind={variant==='a'?'opening':'verdict'} empty={variant==='b'}/></div>
 <div style={{position:'absolute',inset:0,background:'linear-gradient(0deg,#10110f 0%,#10110fee 25%,transparent 85%)'}}/>
 <div data-safe style={{position:'absolute',left:70,top:55,fontFamily:'T2 Song',fontSize:31,letterSpacing:'-.04em'}}>훈련병 얼차려 사망</div>
 <div data-safe style={{position:'absolute',left:70,top:385,fontSize:variant==='a'?89:82,lineHeight:1.16,letterSpacing:'-4px',transform:'skewX(-5deg)',textShadow:'2px 3px #10110f'}}>{variant==='a'?<>중대장 징역<br/><span style={{color:red}}>5년 6개월</span> 확정</>:<>중대장 1심 선고<br/>징역 <span style={{color:red}}>5년</span></>}</div>
 <Texture scan/>
 </AbsoluteFill>;
export const V4N18FullCompositions:React.FC = () => <><Composition id="V4N18-FULL" component={N18Full} width={1920} height={1080} fps={30} durationInFrames={film.durationInFrames}/><Still id="V4N18-THUMB" component={N18Thumb} width={1280} height={720}/></>;
