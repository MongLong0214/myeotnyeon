import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Cut, EvidenceLabel, RecordGrid, SourceLine, Subtitle, Texture, red, white, useTypeTime} from './Type';
export const ShortHeader:React.FC=()=> <div style={{position:'absolute',left:62,top:164,width:910,fontFamily:'T2 Head',fontSize:81,lineHeight:1.08,letterSpacing:'-.045em',color:white}}><div>'싸움 각서' 쓰고</div><div style={{marginTop:3}}>몸싸움 · <span style={{color:red}}>1명 사망</span></div></div>;
const Rule:React.FC=()=> <div style={{position:'absolute',left:62,top:394,width:900,height:2,background:'#66675f'}}/>;
const CaseSource:React.FC=()=> <SourceLine portrait text={'보도 기반 재구성\n수원고법 2026년 항소심'}/>;
/** C17/19: paper object and scene-anchored names, no inset rounded stage. */
export const ShortIncident:React.FC=()=> <>
 <svg width="1080" height="1920" style={{position:'absolute',inset:0}}><rect x="0" y="455" width="1080" height="720" fill="#a5a397"/>
 <g transform="translate(540 800) rotate(-8)"><path d="M-500-240H500V240H-500Z" fill="#72746d" stroke="#353832" strokeWidth="8"/>{[-365,-120,125,370].map((x,i)=><g key={x}><path d={`M${x-70} -305h140v45h-140zM${x-70} 260h140v45h-140z`} fill="#babbb0" stroke="#494e43" strokeWidth="7"/><path d={`M${x-60} -293h120M${x-60} 290h120`} stroke="#272b24" strokeWidth="3"/></g>)}
 <path d="M-190-220L175-205L200 240L-195 225Z" fill="#e5e1d4" stroke="#47493e" strokeWidth="2"/><text x="0" y="-100" textAnchor="middle" fontFamily="T2 Song" fontSize="82" fill="#23261f">각서</text><path d="M-130-40H130M-130-15H120M-130 10H130M-130 35H90M-130 100h85m70 0h95" stroke="#55564d" strokeWidth="3"/><text x="0" y="185" textAnchor="middle" fontFamily="T2 Coding" fontSize="22" fill="#46483f">문서 재구성 · 원본 아님</text></g></svg>
 <EvidenceLabel x={82} y={505} text="40대 동대표"/><EvidenceLabel x={650} y={1030} text="50대 동대표"/>
 <ShortHeader/><Rule/><Subtitle portrait text={'아파트 동대표 회의에서\n다툰 두 동대표가,'}/><CaseSource/><Texture paper/>
 </>;
/** C17 black name strips, C24 compact red headline: three fixed paper rows. */
export const ChoicesBeat:React.FC=()=> <><ShortHeader/><Rule/><div style={{position:'absolute',left:65,top:475,fontFamily:'T2 Song',fontSize:45,color:white}}>몇 년 받았을까?</div>
 <div style={{position:'absolute',left:48,top:590,width:970,height:585,background:'#d5d0bf',transform:'rotate(-1deg)',color:'#12140f',padding:'37px 24px'}}>
 {['벌금','집행유예','실형'].map((label,i)=><Cut at={i*8+5} key={label}><div style={{height:163,display:'flex',alignItems:'center',borderBottom:i<2?'2px solid #696a60':'none'}}><span style={{fontFamily:'T2 Coding',fontSize:38,width:115,paddingLeft:12,color:red}}>0{i+1}</span><span style={{fontFamily:'T2 Head',fontSize:85,lineHeight:1,color:'#10120e'}}>{label}</span></div></Cut>)}<Texture paper/></div>
 <Subtitle portrait text="몇 년 받았을까요?"/><CaseSource/></>;
/** C05/07 record language: left-registered heading and two lines of serif. */
export const ReasonCard:React.FC=()=> <><RecordGrid/><ShortHeader/><Rule/><div style={{position:'absolute',left:65,top:485,color:white,fontFamily:'T2 Myeongjo'}}><div style={{fontSize:36,marginBottom:76}}>재판부 판단 요지 · 보도 기반</div><div style={{fontSize:65,fontWeight:800}}>예견 가능성</div><div style={{fontSize:67,lineHeight:1.5,marginTop:80,letterSpacing:'-.04em'}}>사망까지<br/>예견하긴 어려움</div><div style={{width:360,height:4,background:'#dedccc',marginTop:38}}/></div><Subtitle portrait text={'숨질 걸 예견하긴\n어려웠다고 봤습니다.'}/><CaseSource/><Texture/></>;
/** C06 appended sentence + C24/26 dense white/red headline hierarchy. */
export const ShortVerdict:React.FC=()=>{const {t}=useTypeTime();return <><RecordGrid/><ShortHeader/><Rule/><div style={{position:'absolute',left:65,top:480,color:white,fontFamily:'T2 Myeongjo',fontSize:42,lineHeight:1.6}}><div>폭행치사 무죄</div><div>폭행죄 인정</div></div><Cut at={18}><div style={{position:'absolute',left:62,top:717,color:white,fontFamily:'T2 Head',fontSize:88,letterSpacing:'-.04em'}}>징역 <span style={{fontSize:144}}>10</span>개월</div></Cut><Cut at={36}><div style={{position:'absolute',left:62,top:910,color:red,fontFamily:'T2 Head',fontSize:91,letterSpacing:'-.04em'}}>집행유예 <span style={{fontSize:144}}>2</span>년</div></Cut>{t>=54&&<div style={{position:'absolute',left:65,top:1150,color:white,fontFamily:'T2 Song',fontSize:37}}>2심도 같은 판단</div>}<Subtitle portrait text={'징역 10개월에\n집행유예 2년입니다.'}/><CaseSource/><Texture/></>;};
export const ShortTypeReview:React.FC<{kind:'header'|'choices'|'reason'|'verdict'}>=({kind})=><AbsoluteFill style={{background:'#10110f'}}>{kind==='header'?<ShortIncident/>:kind==='choices'?<ChoicesBeat/>:kind==='reason'?<ReasonCard/>:<ShortVerdict/>}</AbsoluteFill>;
