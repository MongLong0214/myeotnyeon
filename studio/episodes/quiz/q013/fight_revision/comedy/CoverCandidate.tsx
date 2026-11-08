import React from 'react';
import {AbsoluteFill} from 'remotion';
import {DISPLAY,FONT} from '../../../../../production/compositor/src/theme';
import {Reenactment} from './FightScene';
export const CoverCandidate:React.FC=()=> <AbsoluteFill style={{background:'#0B0F1C',color:'#FFFDF6',fontFamily:FONT}}>
 <div style={{position:'absolute',left:120,top:210,width:810,fontWeight:900,fontSize:38,color:'#F2C14E'}}>몇년나옴? · 형량 퀴즈 #16</div>
 <div style={{position:'absolute',left:110,top:305,width:850,fontFamily:DISPLAY,fontSize:124,lineHeight:1.13,letterSpacing:'-.04em'}}>박치기 <span style={{color:'#FF4942'}}>22번</span></div>
 <div style={{position:'absolute',left:110,top:470,width:850,fontWeight:900,fontSize:76,letterSpacing:'-.04em',color:'#F2C14E'}}>공장 관리자의 최후</div>
 <div style={{position:'absolute',left:60,top:625,width:960,height:864,borderRadius:28,overflow:'hidden'}}><div style={{width:1000,height:900,transform:'scale(.96)',transformOrigin:'0 0'}}><Reenactment globalOffset={174}/></div></div>

</AbsoluteFill>;
