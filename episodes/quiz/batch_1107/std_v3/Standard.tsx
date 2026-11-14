import React,{useLayoutEffect,useRef} from 'react';
import {AbsoluteFill,Freeze,continueRender,delayRender,staticFile,useCurrentFrame} from 'remotion';
import {Film,Case,Line,lineAt} from './Scenes';
import {type,INK,PAPER,GOLD,TEAL} from './CourtDynamic';

const loading=typeof document==='undefined'?null:delayRender('q013 v3 fonts');
if(loading!==null)Promise.all([['Do Hyeon','DoHyeon-Regular.ttf','400'],['Quiet Sans','Pretendard-ExtraBold.woff2','800']].map(async([family,file,weight])=>{const font=await new FontFace(family,`url(${staticFile('fonts/'+file)})`,{weight}).load();document.fonts.add(font);})).then(()=>continueRender(loading));
const captionStyle:React.CSSProperties={...type,fontFamily:'Quiet Sans',position:'absolute',left:90,top:1192,width:900,height:150,display:'flex',alignItems:'center',justifyContent:'center',fontSize:72,fontWeight:800,lineHeight:1.04,WebkitTextStroke:'10px #000',color:'#FFF',textShadow:'0 3px 4px rgba(0,0,0,.65)',whiteSpace:'pre',zIndex:30};
const Caption:React.FC<{s:any;audit:boolean}>=({s,audit})=>{
 const f=useCurrentFrame(),ref=useRef<HTMLDivElement>(null);
 useLayoutEffect(()=>{
  if(!audit||!ref.current)return;
  const el=ref.current,cs=getComputedStyle(el),canvas=el.closest('[data-owner-canvas]')!.getBoundingClientRect(),b=el.getBoundingClientRect();
  const lines=Array.from(el.querySelectorAll('[data-caption-line]')).map(line=>{const r=document.createRange();r.selectNodeContents(line);const box=r.getBoundingClientRect();return {text:line.textContent,characters:Array.from(line.textContent??'').length,centerX:box.x+box.width/2-canvas.x,top:box.top-canvas.y,bottom:box.bottom-canvas.y,width:box.width};});
  console.log('CAPTION_LAYOUT '+JSON.stringify({frame:f,fontSize:cs.fontSize,fontWeight:cs.fontWeight,outline:cs.webkitTextStrokeWidth,centerX:b.x+b.width/2-canvas.x,top:b.y-canvas.y,bottom:b.bottom-canvas.y,lines}));
 },[audit,f,s]);
 return <div ref={ref} data-narration style={captionStyle}><div style={{width:'100%'}}>{s.text.split('\n').map((line:string,i:number)=>{const at=s.emphasis?line.indexOf(s.emphasis):-1;return <div key={i} data-caption-line>{at<0?line:<>{line.slice(0,at)}<span style={{color:'#FFD400'}}>{s.emphasis}</span>{line.slice(at+s.emphasis.length)}</>}</div>;})}</div></div>;
};

export const Choices:React.FC<{c:Case;answer?:boolean}>=({c,answer=false})=>{
 const f=useCurrentFrame(),colors=[GOLD,TEAL,'#929BEA'],wide=!answer;
 return <div data-choice-group style={{position:'absolute',left:110,top:wide?440:1430,width:wide?860:760,display:'flex',flexDirection:wide?'column':'row',gap:wide?25:20,zIndex:20}}>
  {c.choices.map((text,i)=>{const at=c.choice_frame+i*4,d=f-at,lit=answer&&c.correct===i,beat=!answer&&d>=0&&d<12;
   if(!answer&&d<0)return null;
   const val=text.replace('징역 ',''),ink=answer&&!lit?'#D0D5DC':INK;
   return <div data-choice={'ABC'[i]} data-answer-lit={lit} key={text} style={{width:wide?860:240,height:wide?165:164,background:answer&&!lit?'#40505D':colors[i],border:`${lit||beat?9:7}px solid ${lit||beat?'#FFF8C3':INK}`,borderRadius:9,display:'flex',flexDirection:wide?'row':'column',alignItems:'center',justifyContent:'center',gap:wide?45:0,boxSizing:'border-box',opacity:answer&&!lit?.28:1,boxShadow:lit||beat?'0 0 42px rgba(255,212,90,.8)':`7px 9px 0 ${INK}`,transform:!answer&&d<4?`translateY(${(4-d)*7}px)`:'none'}}>
    <span style={{fontFamily:'Quiet Sans',fontWeight:800,fontSize:wide?70:36,color:ink}}>{'ABC'[i]}{!wide?' · 징역':''}</span>
    <span style={{fontFamily:'Quiet Sans',fontWeight:800,fontSize:wide?84:72,letterSpacing:'-.04em',color:ink}}>{wide?text:val}{lit&&wide?' ✓':''}</span>
   </div>;
  })}
 </div>;
};

const Teaser:React.FC<{c:Case;t:number}>=({c,t})=>{
 const kind=c.next==='q020'?'train':c.next==='q018'?'parking':'kick',mode=kind==='train'?'pour':kind==='parking'?'assault':'trip';
 const next={...c,qid:c.next,kind},u={id:'TEASER',mode,text:'',shown:'',from_frame:0,dur:90,start_s:0,end_s:3};
 const headline=kind==='train'?'달리는 지하철에 불':kind==='parking'?'차 빼달랬더니 폭행':'대리기사에게 사커킥';
 return <AbsoluteFill><Film c={next} u={u} t={40+t}/><div style={{...type,position:'absolute',left:65,top:255,width:950,fontSize:85}}>{headline}</div></AbsoluteFill>;
};

export const Standard:React.FC<{c:Case;audit?:boolean;cover?:boolean}>=({c,audit=false,cover=false})=>{
 const f=useCurrentFrame(),u=lineAt(c,f),t=f-u.from_frame,answer=f>=c.answer_frame&&f<c.cta_frame;
 const cue=c.subtitles.find(s=>f/30>=s.start_s&&f/30<s.end_s);
 return <AbsoluteFill data-owner-canvas style={{background:'#D7CCB3',overflow:'hidden'}}>
  <style>{`svg path[stroke="#9FD8FF"]{display:none}`}</style>
  {u.mode==='next'?<Teaser c={c} t={t}/>:<Film c={c} u={u} t={t}/>}
  {(f<c.utterances[0].dur||cover)&&<div style={{...type,position:'absolute',left:65,top:235,width:950,fontSize:cover?91:88,zIndex:19}}>{cover?c.headline+'\n'+c.question:c.kind==='kick'?'남편 징역 몇 개월?':'징역 몇 년?'}</div>}
  {u.mode==='choices'&&<><Choices c={c}/><div style={{...type,position:'absolute',left:90,top:1040,width:900,fontSize:56,zIndex:20}}>댓글로 골라보세요</div></>}
  {answer&&<>
   <div style={{...type,position:'absolute',left:65,top:210,width:950,zIndex:21,color:GOLD}}><div style={{fontFamily:'Quiet Sans',fontSize:50,color:PAPER,WebkitTextStroke:`5px ${INK}`,marginBottom:24}}>정답 {'ABC'[c.correct]} · 항소심 선고</div><div style={{fontSize:c.qid==='q022'?110:124,letterSpacing:'-.03em'}}>{c.answer.replace('항소심 ','')}</div><div style={{fontFamily:'Quiet Sans',fontSize:58,color:PAPER,WebkitTextStroke:`5px ${INK}`,marginTop:25}}>{u.mode==='wife'?'아내 4개월 · 집행유예 1년':c.answer_detail}</div></div>
   <Choices c={c} answer/>
  </>}
  {cue&&!cover&&<Caption s={cue} audit={audit}/>}
 </AbsoluteFill>;
};
