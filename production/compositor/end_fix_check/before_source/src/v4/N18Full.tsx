import React from 'react';
import {AbsoluteFill,Audio,Composition,Sequence,Still,staticFile,useCurrentFrame} from 'remotion';
import {N18Art,ArtDefs,Person,Finish,C} from './N18Art';
import film from './n18-film.json';

type Shot = (typeof film.shots)[number];
const font='Pretendard';
const Panel:React.FC<{lines:string[];category?:string;numeric?:boolean}> = ({lines,category,numeric=false}) => {
 const f=useCurrentFrame(); const a=Math.min(1,f/8);
 return <div style={{position:'absolute',left:330,top:335,width:1260,minHeight:250,padding:'34px 50px',boxSizing:'border-box',background:'rgba(3,4,11,.92)',borderTop:'1px solid #7983bd',borderBottom:'1px solid #343961',textAlign:'center',opacity:a,transform:`translateY(${(1-a)*9}px)`}}>
 {category && <div data-safe style={{fontSize:29,fontWeight:500,color:C.green,marginBottom:25,letterSpacing:'.04em'}}>{category}</div>}
 {lines.map((line,i)=><div data-safe key={i} style={{fontSize:numeric?82:line.length>27?39:line.length>19?44:56,fontWeight:numeric?700:600,lineHeight:1.55,color:numeric&&i===lines.length-1?C.yellow:C.white,whiteSpace:'nowrap'}}>{line}</div>)}
 </div>;
};
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
 {isChapter?<><div data-safe style={{position:'absolute',left:180,top:350,fontSize:28,letterSpacing:'.15em',color:C.green}}>몇년나옴 · 판결 기록</div><div data-safe style={{position:'absolute',left:180,top:430,fontSize:84,fontWeight:700}}>{shot.chapterTitle}</div><div style={{position:'absolute',left:180,top:575,width:1560,height:2,background:'linear-gradient(90deg,#ff2a7a,#1a2cff)'}}/></>:
 shot.kind==='credits'?<div style={{position:'absolute',left:190,top:255,width:1540}}><div data-safe style={{fontSize:35,color:C.green,marginBottom:45}}>출처 · 보도 원문</div><div data-safe style={{fontSize:47,fontWeight:600,lineHeight:1.9}}>{shot.lines.join(' · ')}</div><div data-safe style={{fontSize:29,marginTop:48,color:C.grey}}>원문 URL과 발행일은 영상 설명에 수록했습니다.</div><div data-safe style={{fontSize:28,marginTop:30,color:C.grey}}>화면은 직접 그린 재구성·개념도입니다. 실제 배치와 다릅니다.</div></div>:
 <>{shot.art==='diagram'&&<Relationship multiple={shot.multiple} close={index%2===1}/>}
 {shot.art==='diagram'?<div data-safe style={{position:'absolute',left:190,top:220,width:1540,textAlign:'center',fontSize:49,fontWeight:600}}>{shot.lines.join(' · ')}</div>:
 shot.art==='spatial'?<div data-safe style={{position:'absolute',left:600,top:746,width:900,textAlign:'center',fontSize:38,fontWeight:600}}>{shot.lines.join(' · ')}</div>:shot.lines.length>0&&<Panel lines={shot.lines} category={shot.category} numeric={shot.numeric}/>}
 <div data-safe style={{position:'absolute',left:108,top:64,fontSize:23,letterSpacing:'.07em',color:C.green}}>{shot.chapterLabel}</div>
 {shot.date&&<div data-safe style={{position:'absolute',left:450,top:61,width:1020,textAlign:'center',fontSize:30,fontWeight:600}}>{shot.date}</div>}
 {shot.label&&<div data-safe style={{position:'absolute',left:108,top:833,fontSize:22,color:C.grey}}>{shot.label}</div>}
 {shot.source&&<div data-safe style={{position:'absolute',left:108,top:873,fontSize:20,color:C.grey}}>{shot.source}</div>}
 {caption&&<div data-safe style={{position:'absolute',left:112,top:926,width:1696,textAlign:'center',fontSize:44,fontWeight:600,lineHeight:'58px',whiteSpace:'nowrap',letterSpacing:'-.025em',textShadow:'0 0 16px #000,0 2px 2px #000'}}>{caption.text}</div>}
 </>}
 </AbsoluteFill>;
};
export const N18Full:React.FC<{audio?:boolean}> = ({audio=true}) => <AbsoluteFill>{film.shots.map((shot,index)=><Sequence key={shot.id} from={shot.from} durationInFrames={shot.dur}><ShotView shot={shot} index={index}/></Sequence>)}{audio&&<Audio src={staticFile('v4n18/mix_master.wav')}/>}</AbsoluteFill>;
export const N18Thumb:React.FC = () => <AbsoluteFill style={{background:C.ink,fontFamily:font,color:C.white,overflow:'hidden'}}><div style={{width:1920,height:1080,transform:'scale(.6666667)',transformOrigin:'0 0'}}><N18Art kind="verdict"/></div><div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,rgba(3,4,11,.95),rgba(3,4,11,.2))'}}/><div data-safe style={{position:'absolute',left:76,top:83,fontSize:24,color:C.green}}>실제 판결 · 대법원 확정</div><div data-safe style={{position:'absolute',left:76,top:225,fontSize:77,fontWeight:800,lineHeight:1.35}}>얼차려 사망<br/><span style={{color:'#ff668e'}}>항소심은 왜 달랐나</span></div><div data-safe style={{position:'absolute',left:80,top:580,fontSize:24,color:C.grey}}>법정 재구성 · 개념도</div></AbsoluteFill>;
export const V4N18FullCompositions:React.FC = () => <><Composition id="V4N18-FULL" component={N18Full} width={1920} height={1080} fps={30} durationInFrames={film.durationInFrames}/><Still id="V4N18-THUMB" component={N18Thumb} width={1280} height={720}/></>;
