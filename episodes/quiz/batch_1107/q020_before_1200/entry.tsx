import React from 'react';
import {registerRoot,AbsoluteFill,Composition,Still,staticFile,useCurrentFrame} from 'remotion';
import {TrainFilm,trainShot} from './TrainFilm';
import {CaseFilm,caseBeat} from './CaseFilm';
const FONT="'Pretendard',sans-serif";
type Case={qid:string;kind:string;n:number;headline:string;question:string;answer:string;display:string[];label:string[];next_kind:string;next_headline:string;next_question:string;utterances:{id:string;mode:string;text:string;from_frame:number;dur:number}[];subtitles:{start_s:number;end_s:number;text:string}[]};
// Layout only: the stored subtitle wording and cue boundaries are never changed.
export const centeredLines=(text:string)=>{
 const tokens=text.split(' '),options:{lines:string[];score:number}[]=[];
 if(text.length<=14)return [text];
 for(let i=1;i<tokens.length;i++){
  const a=tokens.slice(0,i).join(' '),b=tokens.slice(i).join(' ');
  options.push({lines:[a,b],score:Math.max(a.length,b.length)*100+Math.abs(a.length-b.length)});
 }
 if(!options.length){const mid=Math.ceil(text.length/2);return [text.slice(0,mid),text.slice(mid)];}
 return options.sort((a,b)=>a.score-b.score)[0].lines;
};
const floor=(kind:string,legal:boolean,metaphor:boolean)=>metaphor?'#E1E6C9':legal?'#A47B57':kind==='train'?'#8E999D':kind==='rolls'?'#B9B7A7':kind==='blanket'?'#AA987D':'#929B9B';
const Video:React.FC<{c:Case;cover?:boolean}>=({c,cover})=>{
 const frame=useCurrentFrame(),f=cover?0:frame,t=f/30;
 const u=c.utterances.find(u=>f>=u.from_frame&&f<u.from_frame+u.dur)??c.utterances.at(-1)!;
 const next=u.mode==='next';
 const train=c.qid==='q020'&&!next,mode=train?trainShot(t)[2]:caseBeat(c,f).mode;
 const metaphor=['figures','scales','counter','consequence','deposit','camera'].includes(mode);
 const legal=['judge','defendant','verdict'].includes(mode);
 const kind=next?c.next_kind:c.kind;
 const nextCase={...c,kind:c.next_kind,utterances:[{mode:'action',from_frame:0,dur:90}]} as Case;
 const sub=c.subtitles.find(s=>s.start_s<=t&&t<s.end_s);
 const text=cover?c.question:sub?.text??'';
 const lines=centeredLines(text);
 const emphasis=c.qid==='q020'&&text.includes('징역 20년')?'징역 20년':u.mode==='answer'?text.match(/징역\s*(?:[0-9]+년(?:\s*[0-9]+개월)?|[0-9]+개월)|무기징역/)?.[0]:undefined;
 const colorLine=(line:string)=>{if(!emphasis||!line.includes(emphasis))return line;const [a,b]=line.split(emphasis);return <>{a}<span style={{color:'#FFD400'}}>{emphasis}</span>{b}</>;};
 return <AbsoluteFill style={{background:mode==='camera'?'#929B9B':mode==='consequence'?'#778C86':floor(kind,legal,metaphor),fontFamily:FONT,color:'#FFFDF6'}}>
  <style>{`@font-face{font-family:Pretendard;src:url('${staticFile('fonts/Pretendard-ExtraBold.woff2')}');font-weight:800}@font-face{font-family:Pretendard;src:url('${staticFile('fonts/Pretendard-Medium.woff2')}');font-weight:500}.stage svg{position:absolute;inset:0;overflow:visible}`}</style>
  <div style={{position:'absolute',left:0,top:0,width:1080,height:1188,overflow:'hidden'}}>
   <div className="stage" style={{position:'absolute',width:1000,height:1100,transform:'scale(1.08)',transformOrigin:'0 0'}}>
    {train?<TrainFilm time={t}/>:next&&kind==='train'?<TrainFilm time={(9+f-u.from_frame)/30}/>:<CaseFilm c={next?nextCase:c} frame={next?9+f-u.from_frame:f}/>}
   </div>
  </div>
  <div style={{position:'absolute',left:110,top:200,fontSize:30,fontWeight:500,WebkitTextStroke:'3px #000',paintOrder:'stroke fill',textShadow:'0 2px 3px rgba(0,0,0,.5)'}}>{metaphor?'보도 기반 재연·비유':'보도 기반 재연'} · 시간 축약</div>
  {(f<45||cover)&&<div style={{position:'absolute',left:110,right:110,top:282,textAlign:'center',fontSize:76,fontWeight:800,lineHeight:1.18,WebkitTextStroke:'8px #000',paintOrder:'stroke fill',textShadow:'0 2px 4px rgba(0,0,0,.5)'}}>{cover?c.headline:c.question}</div>}
  {((c.qid==='q020'&&t>=11.9667&&t<13.5667)||(c.qid==='q019'&&sub?.text.includes('검찰 구형'))||(c.qid==='q021'&&sub?.text.includes('구형')))&&<div style={{position:'absolute',left:110,top:246,fontSize:30,fontWeight:500,WebkitTextStroke:'3px #000',paintOrder:'stroke fill'}}>검찰 구형: 1심 · 선고와 다름</div>}
  {text&&<div data-subtitle="true" style={{position:'absolute',left:60,width:960,top:1190,height:154,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',textAlign:'center',fontSize:64,fontWeight:800,lineHeight:1.18,letterSpacing:0,WebkitTextStroke:'8px #000',paintOrder:'stroke fill',textShadow:'0 2px 4px rgba(0,0,0,.5)'}}>{lines.map((line,i)=><div key={i} style={{whiteSpace:'pre',width:'100%'}}>{colorLine(line)}</div>)}</div>}
  {next&&<div style={{position:'absolute',left:110,right:110,top:380,textAlign:'center',fontSize:64,fontWeight:800,lineHeight:1.2,WebkitTextStroke:'8px #000',paintOrder:'stroke fill',textShadow:'0 2px 4px rgba(0,0,0,.5)'}}>{c.next_headline}<br/>{c.next_question}</div>}
 </AbsoluteFill>;
};
const dummy={} as Case;
registerRoot(()=> <><Composition id="VIDEO" component={Video} width={1080} height={1920} fps={30} durationInFrames={750} defaultProps={{c:dummy}} calculateMetadata={({props})=>({durationInFrames:props.c.n})}/><Still id="COVER" component={Video} width={1080} height={1920} defaultProps={{c:dummy,cover:true}}/></>);
