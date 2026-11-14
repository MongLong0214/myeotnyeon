import React,{useLayoutEffect,useRef} from 'react';
import {AbsoluteFill,Freeze,continueRender,delayRender,interpolate,staticFile,useCurrentFrame} from 'remotion';
import {Reenactment} from './FightScene';
import {Guy} from './FightRig';
import {Actor,CourtBackground,CourtDynamic,INK,PAPER,GOLD,TEAL,RED,type,pop} from './CourtDynamic';
import data from './render.json';
import captions from './captions.json';

const loadFonts=typeof document==='undefined'?null:delayRender('q013 v3 local fonts');
if(loadFonts!==null)Promise.all([
 ['Do Hyeon','DoHyeon-Regular.ttf','400'],['Quiet Sans','Pretendard-ExtraBold.woff2','800']
].map(async([family,file,weight])=>{const font=await new FontFace(family,`url(${staticFile('fonts/'+file)})`,{weight}).load();document.fonts.add(font);})).then(()=>continueRender(loadFonts));
const clamp={extrapolateLeft:'clamp' as const,extrapolateRight:'clamp' as const};

const captionStyle:React.CSSProperties={...type,fontFamily:'Quiet Sans',position:'absolute',left:90,top:1192,width:900,height:150,display:'flex',alignItems:'center',justifyContent:'center',fontSize:72,fontWeight:800,lineHeight:1.04,WebkitTextStroke:'10px #000',color:'#FFF',textShadow:'0 3px 4px rgba(0,0,0,.65)',whiteSpace:'pre',zIndex:30};
const Narration:React.FC<{text:string;from:number;to:number;audit?:boolean;emphasis?:string}>=({text,from,to,audit=false,emphasis})=>{
 const f=useCurrentFrame(),ref=useRef<HTMLDivElement>(null);
 useLayoutEffect(()=>{
  if(!audit||!ref.current)return;
  const el=ref.current,cs=getComputedStyle(el),canvas=el.closest('[data-owner-canvas]')!.getBoundingClientRect(),b=el.getBoundingClientRect();
  const lines=Array.from(el.querySelectorAll('[data-caption-line]')).map(line=>{const range=document.createRange();range.selectNodeContents(line);const r=range.getBoundingClientRect();return {text:line.textContent,characters:Array.from(line.textContent??'').length,centerX:r.x+r.width/2-canvas.x,top:r.top-canvas.y,bottom:r.bottom-canvas.y,width:r.width};});
  console.log('CAPTION_LAYOUT '+JSON.stringify({frame:f,from,to,font:cs.fontFamily,fontSize:cs.fontSize,fontWeight:cs.fontWeight,outline:cs.webkitTextStrokeWidth,textAlign:cs.textAlign,box:{centerX:b.x+b.width/2-canvas.x,top:b.y-canvas.y,bottom:b.bottom-canvas.y},lines}));
 },[audit,f,from,to,text]);
 return <div ref={ref} data-narration data-caption-from={from} data-caption-to={to} style={captionStyle}><div style={{width:'100%'}}>{text.split('\n').map((line,i)=>{const at=emphasis?line.indexOf(emphasis):-1;return <div data-caption-line key={i}>{at<0?line:<>{line.slice(0,at)}<span style={{color:'#FFD400'}}>{emphasis}</span>{line.slice(at+emphasis!.length)}</>}</div>;})}</div></div>;
};

const Captions:React.FC<{audit?:boolean}>=({audit=false})=>{
 const f=useCurrentFrame();
 // Preserve the base's actual caption visibility, including opening/end boundaries.
 if(f<61)return null;
 if(f>=755)return <Narration text="다음 사건도 맞혀 보세요." from={755} to={800} audit={audit}/>;
 const index=captions.findIndex(c=>f*1000/30>=c.startMs&&f*1000/30<c.endMs),s=data.subtitles[index];
 if(!s)return null;
 const breaks:Record<number,string>={286:'집행유예\n기간 중이었어요.',334:'벌금, 집행유예, 실형 중\n무엇이었을까요?',486:'다만 범행을\n모두 인정했고'};
 return <Narration text={s.from_===754?s.text.replace('\n',' '):breaks[s.from_]??s.text} from={s.from_} to={s.to} audit={audit} emphasis={s.from_===668?'벌금 400만 원':undefined}/>;
};

const SpeedLines:React.FC<{impact?:boolean}>=({impact=false})=>{
 const f=useCurrentFrame();return <svg width={1080} height={1920} style={{position:'absolute',pointerEvents:'none'}}>
  {Array.from({length:18},(_,i)=>{const a=i*Math.PI*2/18,cx=540,cy=720,r=impact?240:410,outer=900;return <path key={i} d={`M${cx+Math.cos(a)*(r+(i%3)*50)} ${cy+Math.sin(a)*(r+(i%3)*50)}L${cx+Math.cos(a)*outer} ${cy+Math.sin(a)*outer}`} stroke={impact?GOLD:'#665149'} strokeWidth={impact?12:6} opacity={impact?.6:.18} transform={`rotate(${Math.sin(f*.1)*.5} 540 720)`}/>;})}
 </svg>;
};

const Opening:React.FC=()=>{
 const f=useCurrentFrame();
 return <AbsoluteFill>
  <AbsoluteFill style={{transform:`scale(${1+f*.0012})`,transformOrigin:'50% 45%'}}><Freeze frame={f<6?97:f<18?101:190}><Reenactment opening={f<6} hideCounter/></Freeze></AbsoluteFill>
  <div style={{...type,position:'absolute',left:70,top:245,width:940,fontSize:99}}>박치기 22번. 몇 년?</div>
 </AbsoluteFill>;
};
const Incident:React.FC=()=> <Reenactment/>;

// Question cards are the one explicit card treatment requested by the owner.
// All labels are readable from f329; pop accents follow the three spoken options.
export const Choices:React.FC<{answer?:boolean}>=({answer=false})=>{
 const f=useCurrentFrame(),wide=!answer,colors=[GOLD,TEAL,'#929BEA'],beats=[334,346,365];
 return <div data-choice-group style={{position:'absolute',left:wide?110:100,top:wide?440:1430,width:wide?860:880,display:'flex',flexDirection:wide?'column':'row',gap:wide?25:20,zIndex:20}}>
  {data.ep.choices.map((label,i)=>{const d=f-beats[i],active=answer&&i===0;
   const scale=answer?i===0?1+.06*Math.exp(-Math.max(0,f-669)/12)*Math.sin((f-669)*.4):.94:d>=0&&d<=14?(d<3?.96+.11*d/3:d<9?1.07:1.07-.07*(d-9)/5):1;
   return <div data-choice={'ABC'[i]} data-answer-lit={active} key={label} style={{width:wide?860:i===0?340:250,height:wide?165:150,background:answer&&!active?'#40505D':colors[i],border:`${active?9:7}px solid ${active?'#FFF8C3':INK}`,borderRadius:9,display:'flex',alignItems:'center',justifyContent:'center',gap:wide?45:15,boxSizing:'border-box',transform:`scale(${scale})`,opacity:answer&&!active?.36:1,boxShadow:active?'0 0 42px rgba(255,212,90,.8)':`7px 9px 0 ${INK}`}}>
    <span style={{fontFamily:'Quiet Sans',fontWeight:800,fontSize:wide?70:50,color:INK}}>{'ABC'[i]}</span>
    <span style={{fontFamily:'Quiet Sans',fontWeight:800,fontSize:wide?84:label==='집행유예'?42:60,letterSpacing:'-.04em',color:answer&&!active?'#D0D5DC':INK}}>{label}</span>
    {active&&<span style={{fontFamily:'Quiet Sans',fontSize:43,fontWeight:800,color:INK}}>✓</span>}
   </div>;
  })}
 </div>;
};

const ChoiceReminder:React.FC=()=> <div data-choice-reminder style={{position:'absolute',left:110,top:1465,width:860,display:'flex',justifyContent:'space-between',zIndex:20}}>
 {data.ep.choices.map((text,i)=><div key={text} style={{...type,fontFamily:'Quiet Sans',fontSize:48,color:[GOLD,TEAL,'#A9AFF6'][i],WebkitTextStroke:`4px ${INK}`}}>{'ABC'[i]} {text}</div>)}
</div>;

const Verdict:React.FC=()=>{
 const f=useCurrentFrame(),p=pop(f-669),compare=f>=710;
 return <>
  <div data-verdict style={{...type,position:'absolute',left:65,top:210,width:950,zIndex:21,transform:`translateY(${(1-p)*-210}px) scale(${.7+.3*p})`,color:GOLD}}>
   <div style={{fontFamily:'Quiet Sans',fontSize:55,fontWeight:800,color:PAPER,WebkitTextStroke:`5px ${INK}`,marginBottom:28}}>정답 A · 법원 선고</div>
   <div style={{fontSize:132,whiteSpace:'nowrap',letterSpacing:'-.03em'}}>벌금 400만 원</div>
  </div>
  {compare&&<div data-demand-sentence style={{...type,position:'absolute',left:90,top:845,width:900,fontSize:64,zIndex:23,lineHeight:1.4}}><span style={{color:'#E5E8EB'}}>구형 징역 1년</span>{'\n→ '}<span style={{color:GOLD}}>선고 벌금 400만 원</span></div>}
  <Choices answer/>
 </>;
};

const Ending:React.FC=()=>{
 const f=useCurrentFrame(),t=f-755;
 // Tease the prepared q020 subway-arson story, without its answer or a generic end card.
 // The act is supported by batch_1107/specs.py / V2-14; the figure is a fictional passenger.
 return <AbsoluteFill style={{background:'#283B46'}}>
  <svg width={1080} height={1920} style={{position:'absolute'}}>
   <path d="M0 0H1080V1920H0Z" fill="#263942"/>
   <path d="M0 490H1080V1130H0Z" fill="#E0DDD0" stroke={INK} strokeWidth={12}/>
   <path d="M0 1030H1080V1100H0Z" fill="#4EAA9A" stroke={INK} strokeWidth={8}/>
   <g transform={`translate(${-t*1.6} 0)`}>
    {[140,530,920].map(x=><g key={x}><rect x={x} y={585} width={300} height={305} rx={24} fill="#354A54" stroke={INK} strokeWidth={12}/><path d={`M${x+35} 830H${x+265}V880H${x+35}Z`} fill="#7B8993" stroke={INK} strokeWidth={6}/><path d={`M${x+150} 585V890`} stroke="#8A999C" strokeWidth={12}/></g>)}
   </g>
   <path d="M0 1130H1080V1920H0Z" fill="#6E7B7D"/>
   <path d="M0 1190H1080" stroke="#E5CA76" strokeWidth={25}/>
   {[460,620,770,920].map((x,i)=>{const h=230+45*Math.sin(t*.25+i*2),dx=16*Math.sin(t*.16+i);return <g key={x} transform={`translate(${x} 1050)`}><path d={`M-100 0Q-160 -100 -55 -180Q-65 -${h} ${dx} -${h+100}Q70 -${h-55} 50 -130Q150 -180 100 0Z`} fill="#D96743" stroke={INK} strokeWidth={8}/><path d={`M-45 0Q-85 -65 -5 -${h*.72}Q75 -100 45 0Z`} fill={GOLD}/></g>;})}
   {[0,1,2].map(i=><path key={i} d={`M${600+i*160} ${550-t*2}q-65 -100 0 -190t-10 -150`} fill="none" stroke="#B1B6AD" strokeWidth={58-i*8} strokeLinecap="round" opacity={.25}/>) }
  </svg>
  <div style={{position:'absolute',top:310,left:20,transform:`translateX(${-t*1.5}px)`}}><Guy look="suit" x={265} y={1180} scale={1.22} expr="concern" pose="point" eye={[12,-4]} rot={-4}/></div>
  <div style={{...type,position:'absolute',left:65,top:280,width:950,fontSize:87}}>달리는 지하철에 불</div>
 </AbsoluteFill>;
};

export const V3:React.FC<{audit?:boolean}>=({audit=false})=>{
 const f=useCurrentFrame();
 return <AbsoluteFill data-owner-canvas style={{background:'#D7CCB3',overflow:'hidden'}}>
  {f<61?<Opening/>:f<197?<Incident/>:f<755?<CourtDynamic/>:<Ending/>}
  {f>=329&&f<405&&<><Choices/><div style={{...type,position:'absolute',left:90,top:1040,width:900,fontSize:51,zIndex:20}}>댓글로 골라보세요</div></>}
  {f>=405&&f<663&&<ChoiceReminder/>}
  {f>=669&&f<755&&(f>=676&&f<691?<Freeze frame={676}><Verdict/></Freeze>:<Verdict/>)}
  <Captions audit={audit}/>
 </AbsoluteFill>;
};
