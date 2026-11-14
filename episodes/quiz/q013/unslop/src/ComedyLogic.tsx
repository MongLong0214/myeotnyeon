import React from 'react';
import {AbsoluteFill,useCurrentFrame} from 'remotion';
import {FONT} from '/Users/isaac/projects/verdict-kr/work/production/compositor/src/theme';
import {ArticulatedGuy} from './FightRig';
import {Reenactment,standing,k,smooth,label,Banner,ink,paper,red,teal} from './FightScene';
const CourtRoom:React.FC=()=> <svg data-environment width={1000} height={2400} viewBox="0 -430 1000 2400" style={{position:'absolute',top:-430}}>
 <rect y={-430} width={1000} height={2400} fill="#E7E0CD"/><rect y={300} width={1000} height={530} fill="#CDBB99"/>
 {[70,250,430,610,790,970].map(x=><path key={x} d={`M${x},300V820`} stroke="#BDA981" strokeWidth={6}/>)}
 <rect y={815} width={1000} height={1600} fill="#A78B68" stroke={ink} strokeWidth={7}/>
</svg>;
const Bench:React.FC=()=> <svg width={1000} height={900} style={{position:'absolute',pointerEvents:'none'}}>
 <rect x={85} y={658} width={370} height={175} rx={10} fill="#A27547" stroke={ink} strokeWidth={8}/>
 <path d="M70,650H470L450,620H90Z" fill="#FAF0CC" stroke={ink} strokeWidth={8}/><path d="M115,700H425" stroke="#6D4A2C" strokeWidth={8}/>
</svg>;
export const CustodyScene:React.FC=()=>{
 const f=useCurrentFrame(),r=standing();r.hip=[0,-160];r.head=k(f,[[0,0],[75,0],[90,9],[114,9]]);r.hands=[[-55,-240],[55,-240]];r.elbows=[[-70,-285],[70,-285]];
 return f<65?<Reenactment globalOffset={139}/>:<AbsoluteFill>
  <CourtRoom/><Banner>시각비유 · 구속된 채 재판</Banner>
  <ArticulatedGuy look="hoodie" x={370} y={820} scale={.65} rig={r} anonymous/>
  <svg width={1000} height={900} style={{position:'absolute'}}>
   <rect x={223} y={300} width={300} height={530} rx={14} fill="none" stroke={ink} strokeWidth={10}/>
   {[260,315,370,425,480].map(x=><path key={x} d={`M${x},305V825`} stroke="#65707D" strokeWidth={12}/>)}
   <g transform={`translate(${710+70*(1-smooth((f-65)/15))} 510) rotate(-5)`}><rect x={-137} y={-160} width={274} height={330} rx={0} fill={paper} stroke={ink} strokeWidth={8}/><path d="M-95,-75H95M-95,-25H95M-95,25H35" stroke="#9DABAC" strokeWidth={10}/><text y={108} textAnchor="middle" fontFamily="Do Hyeon" fontWeight={900} fontSize={45} fill={red}>상해</text></g>
  </svg>
 </AbsoluteFill>;
};
export const ProbationScene:React.FC=()=>{
 const f=useCurrentFrame(),j=standing();j.head=k(f,[[0,0],[25,-10],[55,-10]]);j.hands=[[-65,-220],[140,-300]];
 return <AbsoluteFill>
  <CourtRoom/><Banner>시각비유 · 과거 전력과 범행 시점</Banner>
  <ArticulatedGuy look="judge" x={265} y={810} scale={.62} rig={j} expr="serious" eye={[8,0]}/><Bench/>
  <svg width={1000} height={900} style={{position:'absolute'}}>
   <g transform="translate(680 492)"><rect x={-185} y={-210} width={370} height={400} rx={0} fill={paper} stroke={ink} strokeWidth={9}/><rect x={-185} y={-210} width={370} height={72} rx={0} fill="#5C6078" stroke={ink} strokeWidth={8}/><path d="M-100,-240V-184M100,-240V-184" stroke={ink} strokeWidth={16} strokeLinecap="round"/>
    <text textAnchor="middle" y={-159} fill={paper} fontFamily="Do Hyeon" fontSize={34} fontWeight={900}>음주운전 전력</text>
    <text textAnchor="middle" y={-58} fill={ink} fontFamily="Do Hyeon" fontSize={45} fontWeight={900}>집행유예</text><text textAnchor="middle" y={8} fill={ink} fontFamily="Do Hyeon" fontSize={45} fontWeight={900}>기간 중</text>
    <g transform={`translate(0 ${35+40*(1-smooth((f-25)/12))}) rotate(-6)`} opacity={smooth((f-25)/6)}><text y={63} textAnchor="middle" fill={red} fontFamily="Do Hyeon" fontSize={58} fontWeight={900}>이번 범행</text></g>
   </g>
  </svg>
 </AbsoluteFill>;
};
const Scales:React.FC<{stage:number;progress:number}>=({stage,progress})=>{
 const angle=stage===0?0:stage===1?-12:stage===2?-2:7;
 return <svg width={1000} height={900} style={{position:'absolute'}}>
  <g transform="translate(662 568)">
   <path d="M0,-115V210M-100,210H100" stroke={ink} strokeWidth={15} strokeLinecap="round"/>
   <g transform={`rotate(${angle*progress})`}><path d="M-165,-60H165" stroke={ink} strokeWidth={13} strokeLinecap="round"/>
    {[-1,1].map(side=><g key={side} transform={`translate(${side*155} -60)`}>
     <path d="M0,0L-70,130H70ZM-70,130Q0,200 70,130" fill={side<0?'#E5B8A7':'#A9D1B9'} stroke={ink} strokeWidth={7}/>

    </g>)}
   </g><circle cy={-60} r={18} fill="#E8C14A" stroke={ink} strokeWidth={6}/>
  </g>
 </svg>;
};
export const CourtComedy:React.FC<{children:React.ReactNode;at:number[]}>=({children,at})=>{
 const f=useCurrentFrame(),stage=at.filter(n=>f>=n).length,start=at[stage-1]??0,progress=smooth((f-start)/18),j=standing();
 j.head=k(f-start,[[0,0],[10,stage===1?-9:6],[24,0],[40,stage===1?-5:0]]);
 j.hands=[[-60,-220],[110+35*progress,-290-25*progress]];j.elbows=[[-72,-260],[90,-310]];
 const text=['형량을 가른 사정은?','자숙하지 않고 범행','범행 인정 · 구금 중 반성','700만 원 합의 · 처벌불원'][stage];
 return <AbsoluteFill>
  <CourtRoom/><ArticulatedGuy look="judge" x={265} y={810} scale={.62} rig={j} expr="serious" eye={[8,0]}/><Bench/><Scales stage={stage} progress={progress}/>
  {children}
 </AbsoluteFill>;
};
export const Sentencing:React.FC<{hit:number;second:number;choices:string[];answer:number}>=({hit,second,choices,answer})=>{
 const f=useCurrentFrame(),j=standing();j.head=k(f,[[0,0],[hit,0],[hit+5,7],[hit+15,0]]);j.hands=[[-65,-220],[120,-290]];
 return <AbsoluteFill>
  <CourtRoom/><ArticulatedGuy look="judge" x={265} y={810} scale={.66} rig={j} expr="serious" eye={[9,0]}/><Bench/><Banner>판결 시각화 · 수원지법 1심</Banner>
  {f>=hit&&<>
   <svg width={1000} height={900} style={{position:'absolute',opacity:smooth((f-hit-6)/8)}}><g transform={`translate(675 ${465+35*(1-smooth((f-hit-6)/8))}) rotate(-5)`}>
    <rect x={-200} y={-180} width={400} height={355} rx={0} fill={paper} stroke={ink} strokeWidth={10}/><path d="M-145,-120H145" stroke="#C5BBA4" strokeWidth={8}/><text y={-38} textAnchor="middle" fontFamily="Do Hyeon" fontSize={50} fontWeight={900} fill={ink}>벌금</text><text y={58} textAnchor="middle" fontFamily="Do Hyeon" fontSize={67} fontWeight={900} fill={red}>400만 원</text><path d="M-120,110H120" stroke="#C5BBA4" strokeWidth={8}/>
   </g></svg>
  </>}
 </AbsoluteFill>;
};
