import React from 'react';
import {useCurrentFrame} from 'remotion';
import {loadType2Fonts} from '../type2/fonts';
import {white, ink} from '../type2/Type';
loadType2Fonts();
export {ChapterCard, EvidenceLabel, MeasurementLabel, SourceLine} from '../type2/Type';
export const Date:React.FC<{text:string}>=({text})=>{
 const f=useCurrentFrame();
 return <div data-safe style={{position:'absolute',left:480,top:58,width:960,textAlign:'center',fontFamily:'T2 Song',fontSize:43,lineHeight:1.1,letterSpacing:'-.04em',color:white,textShadow:'1px 2px #181813'}}>{text.slice(0,Math.floor(f*2.2))}</div>;
};
// Subtitle timing comes from the approved cue timeline, independently of scene cuts.
export const Caption:React.FC<{text:string}>=({text})=><div data-safe style={{position:'absolute',left:120,top:935,width:1680,textAlign:'center',fontFamily:'T2 Sans',fontWeight:600,fontSize:48,lineHeight:1.15,letterSpacing:'-.045em',whiteSpace:'nowrap',color:'#f2f1e9',WebkitTextStroke:'1px #111',paintOrder:'stroke fill',textShadow:'1px 2px 0 #111'}}>{text}</div>;
export const Note:React.FC<{text:string;top:number}>=({text,top})=><div data-safe style={{position:'absolute',left:108,top,fontFamily:'T2 Coding',fontSize:20,lineHeight:1.3,letterSpacing:'-.03em',color:'#b2b2a9'}}>{text}</div>;
export const Record:React.FC<{lines:string[];category?:string;numeric?:boolean}>=({lines,category,numeric=false})=>{
 const f=useCurrentFrame();
 return <div style={{position:'absolute',left:300,top:290,width:1320,fontFamily:'T2 Myeongjo',letterSpacing:'-.045em',color:white,textShadow:`1px 2px ${ink}`}}>
 {category&&<div data-safe style={{fontSize:46,fontWeight:800,lineHeight:1.3,marginBottom:34}}>{category}</div>}
 {lines.map((line,i)=><div data-safe key={i} style={{fontSize:numeric?68:line.length>35?40:line.length>25?44:52,fontWeight:numeric?800:400,lineHeight:1.45,minHeight:numeric?99:76,marginBottom:18,whiteSpace:'normal',overflowWrap:'normal'}}>{line.slice(0,Math.max(0,Math.floor((f-i*6)*4)))}</div>)}
 </div>;
};
