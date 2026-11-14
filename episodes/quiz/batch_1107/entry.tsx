import React from 'react';
import {registerRoot,AbsoluteFill,Composition,Still,staticFile,useCurrentFrame} from 'remotion';
import {TrainFilm,trainShot,isTrainCourt,isTrainMetaphor} from './TrainFilm';
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
 const metaphor=train?isTrainMetaphor(mode):['counter','consequence','deposit','camera'].includes(mode);
 const legal=train?isTrainCourt(mode):['judge','defendant','verdict'].includes(mode);
 const kind=next?c.next_kind:c.kind;
 const nextCase={...c,kind:c.next_kind,utterances:[{mode:'action',from_frame:0,dur:90}]} as Case;
 const sub=c.subtitles.find(s=>s.start_s<=t&&t<s.end_s);
 const text=cover?c.question:sub?.text??'';
 const lines=centeredLines(text);
 const emphasis=c.qid==='q020'&&text.includes('징역 20년')?'징역 20년':u.mode==='answer'?text.match(/징역\s*(?:[0-9]+년(?:\s*[0-9]+개월)?|[0-9]+개월)|무기징역/)?.[0]:undefined;
 const colorLine=(line:string)=>{if(!emphasis||!line.includes(emphasis))return line;const [a,b]=line.split(emphasis);return <>{a}<span style={{color:'#FFD400'}}>{emphasis}</span>{b}</>;};
 const choiceStart=c.utterances[4].from_frame,reveal=c.utterances[5].from_frame;
 const choices=c.qid==='q020'&&!next&&f>=choiceStart;
 const factor=text.includes('피해 회복')?'피해 회복 미진':text.includes('대중교통')||text.includes('신뢰까지')?'대중교통 신뢰 침해':'';
 const stampAge=sub?(t-sub.start_s)*30:0,stampScale=stampAge<5?1.6-.6*Math.min(1,stampAge/5):1;
 return <AbsoluteFill style={{background:train&&metaphor?'#E3E7CF':mode==='camera'?'#929B9B':mode==='consequence'?'#778C86':floor(kind,legal,metaphor),fontFamily:FONT,color:'#FFFDF6'}}>
  <style>{`@font-face{font-family:Pretendard;src:url('${staticFile('fonts/Pretendard-ExtraBold.woff2')}');font-weight:800}@font-face{font-family:Pretendard;src:url('${staticFile('fonts/Pretendard-Medium.woff2')}');font-weight:500}.stage svg{position:absolute;inset:0;overflow:visible}.stage svg path[stroke="#9FD8FF"]{display:none}`}</style>
  <div style={{position:'absolute',left:0,top:0,width:1080,height:1188,overflow:'hidden'}}>
   <div className="stage" style={{position:'absolute',width:1000,height:1100,transform:'scale(1.08)',transformOrigin:'0 0'}}>
    {train?<TrainFilm time={t}/>:next&&kind==='train'?<TrainFilm time={(9+f-u.from_frame)/30}/>:<CaseFilm c={next?nextCase:c} frame={next?9+f-u.from_frame:f}/>}
   </div>
  </div>
  {(f<45||cover)&&<div style={{position:'absolute',left:110,right:110,top:200,textAlign:'center',fontSize:76,fontWeight:800,lineHeight:1.18,WebkitTextStroke:'8px #000',paintOrder:'stroke fill',textShadow:'0 2px 4px rgba(0,0,0,.5)'}}>{cover?c.headline:c.qid==='q020'?'지하철 방화, 몇 년?':c.question}</div>}
  {c.qid==='q020'&&text.includes('검찰 구형')&&<div style={{position:'absolute',left:110,right:110,top:200,textAlign:'center',fontSize:48,fontWeight:800,WebkitTextStroke:'6px #000',paintOrder:'stroke fill'}}>1심 검찰 구형 · 선고와 다름</div>}
  {c.qid==='q020'&&factor&&<div style={{position:'absolute',left:110,right:110,top:990,textAlign:'center',fontSize:58,fontWeight:800,color:'#FFD400',WebkitTextStroke:'7px #000',paintOrder:'stroke fill',transform:`scale(${stampScale}) rotate(-4deg)`,opacity:Math.min(1,stampAge/2)}}>{factor}</div>}
  {text&&<div data-subtitle="true" style={{position:'absolute',left:60,width:960,top:1190,height:154,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',textAlign:'center',fontSize:64,fontWeight:800,lineHeight:1.18,letterSpacing:0,WebkitTextStroke:'8px #000',paintOrder:'stroke fill',textShadow:'0 2px 4px rgba(0,0,0,.5)'}}>{lines.map((line,i)=><div key={i} style={{whiteSpace:'pre',width:'100%'}}>{colorLine(line)}</div>)}</div>}
  {choices&&<>
   {f<reveal&&<div style={{position:'absolute',left:110,right:110,top:1100,textAlign:'center',fontSize:42,fontWeight:800,WebkitTextStroke:'6px #000',paintOrder:'stroke fill'}}>댓글로 A · B · C <span style={{color:'#FFD400'}}>{Math.max(1,Math.ceil((reveal-f)/30))}</span></div>}
   {['8년','12년','20년'].map((value,i)=>{const elapsed=f-choiceStart-i*12;if(elapsed<0)return null;const pop=Math.min(1,elapsed/3),pulse=elapsed<3?.78+.36*pop:elapsed<12?1.14-.14*(elapsed-3)/9:1,correct=i===1,revealed=f>=reveal;return <div key={i} style={{position:'absolute',left:110+i*260,top:1376,width:240,height:164,boxSizing:'border-box',border:`${revealed&&correct?10:5}px solid ${revealed&&correct?'#FFD400':'#1E1712'}`,background:['#286C9A','#A94F31','#655199'][i],opacity:revealed&&!correct?.24:1,transform:`scale(${revealed?1:pulse})`,boxShadow:revealed&&correct?'0 0 24px rgba(255,212,0,.7)':'none',textAlign:'center',fontWeight:800,lineHeight:1.12,color:'#FFFDF6'}}><div style={{fontSize:40,marginTop:8}}>{['A','B','C'][i]} · 징역</div><div style={{fontSize:72,marginTop:8}}>{value}</div></div>;})}
  </>}
  {next&&<div style={{position:'absolute',left:110,right:110,top:380,textAlign:'center',fontSize:64,fontWeight:800,lineHeight:1.2,WebkitTextStroke:'8px #000',paintOrder:'stroke fill',textShadow:'0 2px 4px rgba(0,0,0,.5)'}}>{c.next_headline}<br/>{c.next_question}</div>}
 </AbsoluteFill>;
};
const dummy={} as Case;
registerRoot(()=> <><Composition id="VIDEO" component={Video} width={1080} height={1920} fps={30} durationInFrames={750} defaultProps={{c:dummy}} calculateMetadata={({props})=>({durationInFrames:props.c.n})}/><Still id="COVER" component={Video} width={1080} height={1920} defaultProps={{c:dummy,cover:true}}/></>);
