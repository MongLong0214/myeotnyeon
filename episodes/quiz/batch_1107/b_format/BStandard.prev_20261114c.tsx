// B-format Shorts frame: q013 v3 caption spec (72px/800/black 10px, centred, ≤2 lines), choice cards, answer header,
// opinion question, no sign-off. Episode films are looked up by qid.
import React,{useLayoutEffect,useRef} from 'react';
import {AbsoluteFill,continueRender,delayRender,staticFile,useCurrentFrame} from 'remotion';
import {ArticulatedGuy} from './FightRig';
import {standing} from './FightScene';
import {CourtBackground,type,INK,PAPER,GOLD,TEAL} from './CourtDynamic';
import {Who,Push,breathe,kf,Sweat,S,solve} from './Kit';
import {Q019Film,StompShot} from './Q019';
import {Q021Film,OpenCover} from './Q021';
import {Q023Film,CrashCover} from './Q023';
import {Q024Film,OpenCover as Q024Cover} from './Q024';
import {Q025Film,SpeedCover} from './Q025';
import {B3Film,Pops,SubGag,HookText,DealStage,KickStage,MotelStage,TaxiStage,FireStage,KettleStage,BBStage,FleeStage,ForgeStage,VaultStage,SojuStage,CabStage,BusStage,SaltStage,PrintStage,GlareStage,BusArgueStage,VoucherStage,BankStage,FactoryStage,PledgeStage,YardStage,HolidayStage,ScanStage,StreamStage,ShotsStage,CashStage,SpeedStage,LikeStage} from './B3Kit';

export type Line={id:string;mode:string;tts:string;shown:string|null;from_frame:number;dur:number;onset:number;offset:number};
export type Cue={start_s:number;end_s:number;text:string;emphasis?:string};
export type Case={qid:string;number_label:string;choices:string[];correct:number;answer:string;answer_label:string;opinion:string;utterances:Line[];subtitles:Cue[];n:number;choice_frame:number;options_frame:number;answer_frame:number;opinion_frame:number;option_onsets:number[];cover_text:string;defendant:string};

import {FONTS,localeOf,str,captionSize,em,LocaleCtx,type Locale} from './i18n';
const fontsDone:Partial<Record<Locale,Promise<void>>>={};
const loadFonts=(L:Locale)=>fontsDone[L]??=Promise.all(FONTS[L].map(async([family,file,weight])=>{const font=await new FontFace(family,`url(${staticFile('fonts/'+file)})`,{weight}).load();document.fonts.add(font);})).then(()=>undefined);
const useFonts=(c:unknown)=>{const [h]=React.useState(()=>typeof document==='undefined'?null:delayRender('b-format fonts'));
 React.useEffect(()=>{if(h!==null)loadFonts(localeOf(c)).then(()=>continueRender(h));},[h]);};

const captionStyle:React.CSSProperties={...type,fontFamily:'Quiet Sans',position:'absolute',left:90,top:1192,width:900,height:150,display:'flex',alignItems:'center',justifyContent:'center',fontSize:72,fontWeight:800,lineHeight:1.04,WebkitTextStroke:'10px #000',color:'#FFF',textShadow:'0 3px 4px rgba(0,0,0,.65)',whiteSpace:'pre',zIndex:30};
const Caption:React.FC<{s:Cue;c:Case}>=({s,c})=><div data-narration style={{...captionStyle,fontSize:captionSize(c,s.text)}}><div style={{width:'100%'}}>{s.text.split('\n').map((line,i)=>{const at=s.emphasis?line.indexOf(s.emphasis):-1;return <div key={i} data-caption-line>{at<0?line:<>{line.slice(0,at)}<span style={{color:'#FFD400'}}>{s.emphasis}</span>{line.slice(at+s.emphasis!.length)}</>}</div>;})}</div></div>;

const fitc=(c:Case,t:string,size:number)=>localeOf(c)==='ko'?size:Math.min(size,Math.floor(980/Math.max(1,...t.split('\n').map(l=>em(localeOf(c),l)))));
export const lineAt=(c:Case,f:number)=>c.utterances.find(u=>f>=u.from_frame&&f<u.from_frame+u.dur)??c.utterances[c.utterances.length-1];
const COLORS=[GOLD,TEAL,'#929BEA'];
const Cards:React.FC<{c:Case;answer?:boolean}>=({c,answer=false})=>{
 const f=useCurrentFrame(),wide=!answer;
 return <div data-choice-group style={{position:'absolute',left:wide?110:110,top:wide?440:1430,width:wide?860:860,display:'flex',flexDirection:wide?'column':'row',gap:wide?25:20,zIndex:20}}>
  {c.choices.map((text,i)=>{const at=c.choice_frame+3+i*5,read=Math.round(c.option_onsets[i]*30)-1,d=f-at,lit=answer&&c.correct===i,beat=!answer&&(d>=0&&d<8||f>=read&&f<read+10);
   if(!answer&&d<0)return <div key={text} style={{height:165}}/>;
   const ink=answer&&!lit?'#D0D5DC':INK;
   return <div data-choice={'ABC'[i]} data-answer-lit={lit} key={text} style={{width:wide?860:273,height:wide?165:150,background:answer&&!lit?'#40505D':COLORS[i],border:`${lit||beat?9:7}px solid ${lit||beat?'#FFF8C3':INK}`,borderRadius:9,display:'flex',flexDirection:wide?'row':'column',alignItems:'center',justifyContent:'center',gap:wide?45:0,boxSizing:'border-box',opacity:answer&&!lit?.3:1,boxShadow:`7px 9px 0 ${INK}`,transform:!answer&&d<4?`translateY(${(4-d)*7}px) scale(${1+.04*(4-d)})`:'none'}}>
    <span style={{fontFamily:'Quiet Sans',fontWeight:800,fontSize:wide?70:34,color:ink}}>{'ABC'[i]}</span>
    <span style={{fontFamily:'Quiet Sans',fontWeight:800,fontSize:localeOf(c)==='ko'?(wide?84:text.length>6?40:46):Math.min(wide?84:46,Math.floor((wide?660:250)/Math.max(1,em(localeOf(c),text)))),letterSpacing:'-.04em',color:ink}}>{text}</span>
   </div>;})}
 </div>;
};
const GAVEL=<g stroke="#1E1712" strokeWidth={6} strokeLinejoin="round"><path d="M-8 10V-103H8V10Z" fill="#A17442"/><rect x={-61} y={-135} width={122} height={45} rx={6} fill="#AD7944"/><path d="M-44 -135V-90M44 -135V-90" fill="none" stroke="#D1AE78" strokeWidth={5}/></g>;
// Judge holds the gavel through the choice hold: rest -> slow raise -> strike that lands 1f before the answer cut.
const GavelJudge:React.FC<{x:number;y:number;s:number;impact:number}>=({x,y,s,impact})=>{
 const f=useCurrentFrame(),d=impact-f,r=standing();
 const raise=kf(-d,[[-52,0],[-14,1]]),strike=kf(-d,[[-13,0],[-9,-.12],[-1,1]]);
 let h:[number,number]=[90+180*raise,-260-210*raise],rot=-20+50*raise;
 if(d<=13){h=[270-40*strike,-470+30*strike];rot=30+115*strike;}
 r.hands=[[-70,-250+1.5*breathe(f,1.8)],h];r.head=.3*breathe(f,.6)+3*strike;r.hip[1]+=1.5*breathe(f,.2);
 r.handProps=[{pose:'relaxed'},{pose:'grip',anchor:'wrist',side:'left',rot,object:GAVEL}];
 solve(r,{elbow:[[-1,.6],[1,.2]]});
 return <ArticulatedGuy look="judge" x={x} y={y} scale={s} rig={r} expr="serious" eye={[8,2]}/>;
};
const GX=470;
const ChoiceShot:React.FC<{c:Case}>=({c})=>{
 const f=useCurrentFrame(),t=f-c.choice_frame;
 const read=c.option_onsets.map(o=>Math.round(o*30)),cur=read.filter(r=>f>=r).length-1;
 const eyeX=cur<0?-4:[-10,-2,8][cur];
 return <AbsoluteFill><CourtBackground dark/>
  <Push t={t} dur={c.answer_frame-c.choice_frame} amt={.03} origin="50% 30%"><AbsoluteFill style={{transform:`scale(${1+.05*Math.max(0,...read.map(r=>f>=r-1&&f<r+12?1-Math.abs(f-r-2)/10:0))})`,transformOrigin:'50% 40%'}}>
  <GavelJudge x={290} y={930} s={1.0} impact={c.answer_frame-1}/>
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d="M-20 540H600V640H-20Z" fill="#80573F"/><path d="M-20 525H600V550H-20Z" fill="#CFAB76"/><ellipse cx={GX} cy={532} rx={70} ry={14} fill="#5D3A30" strokeWidth={6}/></svg>
  <Who look={c.defendant as never} x={830} y={930} s={1.0} expr={t<70?'concern':'scared'} talk={false} phase={1.3} eye={[eyeX,10]} pose={(r)=>{
   // fidget cycle (every ~1.3 s a different big arm action) so the choice hold never reads as a still frame
   const k=Math.floor(t/40)%3,u=(t%40)/40,a=Math.sin(Math.PI*Math.min(1,u*1.25));r.hip[0]+=26*Math.sin(t*.16);r.hip[1]+=10*Math.abs(Math.sin(t*.32));
   if(k===0){r.hands=[[-40,-250],[60+40*a,-260-300*a]];r.handProps=[{pose:'relaxed'},{pose:a>.5?'open':'relaxed'}];r.head=-4*a;}
   else if(k===1){r.hands=[[-30-10*a,-250-60*a],[30+10*a,-250-60*a]];r.handProps=[{pose:a>.4?'fist':'relaxed'},{pose:a>.4?'fist':'relaxed'}];r.head=4*a;r.torso=-4*a;}
   else{r.hands=[[-60-60*a,-250-260*a],[30,-260]];r.handProps=[{pose:a>.5?'open':'relaxed'},{pose:'relaxed'}];r.head=5*a;}}}/>
  {t>=70&&<Sweat x={900} y={290} t={t-70} s={1.1}/>}
  </AbsoluteFill></Push>
  <div style={{position:'absolute',left:0,top:190,width:1080,height:1}}/>
  <div style={{position:'absolute',left:0,top:0,width:1080,height:1920,transform:'translateY(170px)'}}><Cards c={c}/></div>
 </AbsoluteFill>;
};
const AnswerJudge:React.FC<{t:number}>=({t})=>{
 const f=useCurrentFrame(),r=standing(),lift=kf(t,[[0,0],[10,0],[30,.35]]);
 r.hands=[[-85,-210],[65+60*lift,-336-110*lift]];r.elbows=[[-90,-262],[106,-330+20*lift]];r.head=.3*breathe(f,.6);r.hip[1]+=1.5*breathe(f,.2);
 r.handProps=[{pose:'relaxed'},{pose:'grip',anchor:'wrist',side:'left',rot:145-40*lift,object:<g stroke="#1E1712" strokeWidth={6} strokeLinejoin="round"><path d="M-8 10V-103H8V10Z" fill="#A17442"/><rect x={-61} y={-135} width={122} height={45} rx={6} fill="#AD7944"/><path d="M-44 -135V-90M44 -135V-90" fill="none" stroke="#D1AE78" strokeWidth={5}/></g>}];
 return <ArticulatedGuy look="judge" x={235} y={1230} scale={1.15} rig={r} expr="serious" eye={[8,1]}/>;
};
const AnswerShot:React.FC<{c:Case;t:number}>=({c,t})=>{
 const zoom=1+.08*(1-Math.min(1,t/4));
 return <AbsoluteFill><CourtBackground dark/><AbsoluteFill style={{transform:`scale(${zoom})`,transformOrigin:'50% 55%'}}>
  <AnswerJudge t={t}/>
  <svg width={1080} height={1920} style={{position:'absolute'}} {...S}><path d="M20 930H570V1160H20Z" fill="#80573F"/><path d="M20 930H570V970H20Z" fill="#CFAB76"/><ellipse cx={385} cy={950} rx={85} ry={17} fill="#5D3A30" strokeWidth={7}/></svg>
  <Who look={c.defendant as never} x={815} y={1260} s={1.08} expr={t<16?'shock':'scared'} phase={.6} eye={[-9,2]} pose={(r)=>{const b=kf(t,[[0,0],[8,1],[24,1],[40,.5]]);r.hands=[[-90-20*b,-180-120*b],[90+20*b,-180-120*b]];r.handProps=[{pose:'open'},{pose:'open'}];r.head=-6*b;r.hip[1]+=16*b;}}/>
  {t>=6&&<Sweat x={930} y={650} t={t} s={1.1}/>}
 </AbsoluteFill>{t<4&&<AbsoluteFill style={{background:'#FFF5CC',opacity:.65*(1-t/4)}}/>}</AbsoluteFill>;
};
// B3 result: whip-in push on the judge + gavel, the sentence pops big with a burst, then settles while the camera keeps drifting
const AnswerB3:React.FC<{c:Case;t:number}>=({c,t})=>{
 const f=useCurrentFrame(),whip=t<6?(6-t)/6:0,pop=t<8?.55+.45*Math.min(1,t/5)+.18*Math.sin(t*1.3)*(1-t/8):1,cam=1.02+.10*Math.min(1,t/40);
 return <AbsoluteFill style={{overflow:'hidden'}}>
  <AbsoluteFill style={{transform:`translate(${-260*whip*whip+16*Math.sin(f*.11)}px,${10*Math.sin(f*.08)}px) scale(${cam}) rotate(${-2*whip+.6*Math.sin(f*.07)}deg)`,transformOrigin:'40% 55%',filter:whip>0?`blur(${whip*6}px)`:undefined}}>
   <AnswerShot c={c} t={t}/>
  </AbsoluteFill>
  {t>=1&&t<10&&<svg width={1080} height={1920} style={{position:'absolute'}}><g transform={`translate(540 430) scale(${1+.15*t})`} opacity={1-t/10}>{Array.from({length:16}).map((_,k)=><path key={k} d="M0 -60L-14 -260H14Z" fill={GOLD} transform={`rotate(${k*22.5})`}/>)}</g></svg>}
  <div style={{...type,position:'absolute',left:30,top:190,width:1020,zIndex:22,transform:`scale(${pop})`,transformOrigin:'50% 40%'}}>
   <div style={{fontFamily:'Quiet Sans',fontSize:50,color:PAPER,WebkitTextStroke:`5px ${INK}`,marginBottom:14}}>{str(c).answer('ABC'[c.correct],c.answer_label)}</div>
   <div style={{fontSize:localeOf(c)==='ko'?(c.answer.length>8?118:150):fitc(c,c.answer,150),color:GOLD,letterSpacing:'-.03em'}}>{c.answer}</div>
  </div>
 </AbsoluteFill>;
};
const AnswerHeader:React.FC<{c:Case}>=({c})=><div style={{...type,position:'absolute',left:65,top:200,width:950,zIndex:21,color:GOLD}}>
 <div style={{fontFamily:'Quiet Sans',fontSize:50,color:PAPER,WebkitTextStroke:`5px ${INK}`,marginBottom:20}}>{str(c).answer('ABC'[c.correct],c.answer_label)}</div>
 <div style={{fontSize:fitc(c,c.answer,118),letterSpacing:'-.03em'}}>{c.answer}</div>
</div>;
const Opinion:React.FC<{c:Case;t:number}>=({c,t})=>{
 const [a,b]=c.opinion.split('\n'),words=b.split(' / '),cols=['#7FE0CF',GOLD,'#FF8A7A'];
 const pop=(i:number)=>{const d=t-2-i*7;return d<0?0:Math.min(1,.4+d/6);};
 return <div style={{...type,position:'absolute',left:40,top:215,width:1000,zIndex:22,fontSize:fitc(c,a,96)}}>
  <div style={{opacity:Math.min(1,t/3)}}>{a}</div>
  <div style={{fontSize:fitc(c,b,92),marginTop:14,whiteSpace:'pre'}}>{words.map((w,i)=><span key={w} style={{color:cols[i],display:'inline-block',opacity:pop(i),transform:`scale(${.8+.2*pop(i)})`}}>{w}{i<2?<span style={{color:PAPER}}> / </span>:''}</span>)}</div>
 </div>;
};
const FILMS:Record<string,React.FC<{c:Case;u:Line;t:number}>>={q019:Q019Film,q021:Q021Film,q023:Q023Film,q024:Q024Film,q025:Q025Film};
const COVER_SHOT:Record<string,React.FC<{t:number;dur:number}>>={q019:StompShot,q021:OpenCover,q023:CrashCover,q024:Q024Cover,q025:SpeedCover};
// look: opt-in look-dev layer (look/LOOKDEV.md). film replaces the episode film; post draws over the picture under the captions.
export type LookOpt={film?:React.FC<{c:Case;u:Line;t:number}>;post?:React.FC<{c:Case;u:Line;t:number}>};
export const BStandard:React.FC<{c:Case;cover?:boolean;look?:LookOpt}>=(p)=>{useFonts(p.c);return <LocaleCtx.Provider value={localeOf(p.c)}><BStandardIn {...p}/></LocaleCtx.Provider>;};
const BStandardIn:React.FC<{c:Case;cover?:boolean;look?:LookOpt}>=({c,cover=false,look})=>{
 const b3=!!(c as Case&{b3?:boolean}).b3,f=useCurrentFrame(),u=lineAt(c,f),t=f-u.from_frame,Film=look?.film??(b3?B3Film:FILMS[c.qid]),Post=look?.post;
 if(cover){const st=(c as Case&{stage?:string}).stage,Shot=b3?(()=> st==='kick'?<KickStage s={6}/>:st==='motel'?<MotelStage s={6}/>:st==='taxi'?<TaxiStage s={6}/>:st==='fire'?<FireStage s={20}/>:st==='kettle'?<KettleStage s={10}/>:st==='bb'?<BBStage s={10}/>:st==='flee'?<FleeStage s={10}/>:st==='forge'?<ForgeStage s={10}/>:st==='vault'?<VaultStage s={10}/>:st==='soju'?<SojuStage s={10}/>:st==='cab'?<CabStage s={10}/>:st==='bus'?<BusStage s={10}/>:st==='salt'?<SaltStage s={10}/>:st==='printshop'?<PrintStage s={10}/>:st==='glare'?<GlareStage s={10}/>:st==='busargue'?<BusArgueStage s={10}/>:st==='scan'?<ScanStage s={10}/>:st==='stream'?<StreamStage s={10}/>:st==='shots'?<ShotsStage s={10}/>:st==='cash'?<CashStage s={10}/>:st==='speed'?<SpeedStage s={10}/>:st==='like'?<LikeStage s={10}/>:st==='voucher'?<VoucherStage s={10}/>:st==='bank'?<BankStage s={10}/>:st==='factory'?<FactoryStage s={10}/>:st==='pledge'?<PledgeStage s={10}/>:st==='yard'?<YardStage s={10}/>:st==='holiday'?<HolidayStage s={10}/>:<DealStage s={20}/>) as React.FC<{t:number;dur:number}>:COVER_SHOT[c.qid];return <AbsoluteFill data-owner-canvas style={{background:'#1E2328',overflow:'hidden'}}>
  {(c as Case&{grave?:boolean}).grave&&<style>{'[data-anger-mark]{display:none}'}</style>}
  <AbsoluteFill style={{transform:'translateY(250px)'}}><Shot t={0} dur={30}/></AbsoluteFill>
  <AbsoluteFill style={{background:'linear-gradient(#1E2328 0,#1E2328 300px,rgba(30,35,40,0) 520px)'}}/>
  <div style={{...type,fontFamily:'Quiet Sans',fontWeight:800,letterSpacing:'-.03em',position:'absolute',left:40,top:70,width:1000,fontSize:fitc(c,c.cover_text,122),color:PAPER}}>{c.cover_text.split('\n').map((l,i)=><div key={i} style={{color:i===1?GOLD:PAPER}}>{l}</div>)}</div>
  {c.number_label&&<div style={{position:'absolute',right:46,bottom:60,fontFamily:'Quiet Sans',fontWeight:800,fontSize:44,color:PAPER,WebkitTextStroke:`4px ${INK}`,paintOrder:'stroke fill'}}>{c.number_label}</div>}
 </AbsoluteFill>;}
 const cue=c.subtitles.find(s=>f/30>=s.start_s&&f/30<s.end_s);
 const choice=u.mode==='choices'||u.mode==='options',answer=u.mode==='answer'||u.mode==='answer2';
 return <AbsoluteFill data-owner-canvas style={{background:'#D7CCB3',overflow:'hidden'}}>
  <style>{`svg path[stroke="#9FD8FF"]{display:none}${(c as Case&{grave?:boolean}).grave?' [data-anger-mark]{display:none}':''}`}</style>
  {b3&&choice?<AbsoluteFill style={{transform:`translate(${14*Math.sin(f*.09)}px,${8*Math.sin(f*.07)}px) scale(${1.03+.025*Math.sin(f*.05)}) rotate(${.5*Math.sin(f*.06)}deg)`,transformOrigin:'50% 40%'}}><ChoiceShot c={c}/></AbsoluteFill>
   :choice?<ChoiceShot c={c}/>
   :b3&&u.mode==='answer'?<AnswerB3 c={c} t={t}/>
   :u.mode==='answer'?<AnswerShot c={c} t={t}/>:<Film c={c} u={u} t={t}/>}
  {answer&&!(b3&&u.mode==='answer')&&<AnswerHeader c={c}/>}{u.mode==='answer'&&!b3&&<Cards c={c} answer/>}
  {Post&&<Post c={c} u={u} t={t}/>}
  {u.mode==='opinion'&&<Opinion c={c} t={t}/>}
  {b3&&<><Pops c={c}/><HookText c={c}/>{!(c as Case&{grave?:boolean}).grave&&<SubGag c={c}/>}</>}
  {cue&&<Caption s={cue} c={c}/>}
 </AbsoluteFill>;
};
