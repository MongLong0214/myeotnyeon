// Object-only sets, same 1000x900 space, 8px INK outlines and flat palette as components/sets.tsx.
// Generic symbols only: no real building, dates, person, injury, collision or asserted document wording.
import React from 'react';
import {Paper, INK, PAPER, YELLOW, TEAL} from '../../../production/compositor/src/components/toon';
const S = {stroke: INK, strokeWidth: 8, strokeLinejoin: 'round' as const, strokeLinecap: 'round' as const};
export const CustodyCourtSet: React.FC<{paper?: string}> = ({paper}) => <>
  <Paper color={paper ?? '#F6E7D7'}/>
  <svg width={1000} height={900} style={{position:'absolute',inset:0}} aria-label="법원과 구금의 상징">
    <path d="M0 780H1000V900H0Z" fill="#C7B392" {...S}/>
    <ellipse cx={450} cy={780} rx={370} ry={32} fill="#B6A081"/>
    <rect x={105} y={340} width={270} height={360} rx={12} fill="#D8C8A8" {...S}/>
    <path d="M80 340L240 180L400 340Z" fill="#2D3F73" {...S}/>
    <path d="M120 318L240 210L360 318Z" fill="#6E86A4" stroke={INK} strokeWidth={5}/>
    <circle cx={240} cy={280} r={30} fill={YELLOW} stroke={INK} strokeWidth={6}/>
    <path d="M240 259V293M218 276H262M218 276L208 294H228ZM262 276L252 294H272Z" fill="none" stroke={INK} strokeWidth={4} strokeLinejoin="round"/>
    {[130,220,310].map(x=><g key={x}><rect x={x} y={370} width={40} height={270} rx={7} fill={PAPER} {...S}/><rect x={x-9} y={354} width={58} height={24} rx={5} fill="#BDAA87" stroke={INK} strokeWidth={5}/></g>)}
    <rect x={95} y={645} width={290} height={35} rx={7} fill="#9EABBA" {...S}/>
    <rect x={80} y={680} width={320} height={42} rx={7} fill="#9EABBA" {...S}/>
    <rect x={65} y={722} width={350} height={42} rx={7} fill="#9EABBA" {...S}/>
    <rect x={485} y={520} width={275} height={240} rx={20} fill="#667B8D" {...S}/>
    <rect x={505} y={540} width={235} height={200} rx={12} fill="#283442" stroke={INK} strokeWidth={5}/>
    {[530,590,650,710].map(x=><rect key={x} x={x} y={535} width={16} height={210} rx={6} fill="#C2CDD4" stroke={INK} strokeWidth={5}/>)}
    <path d="M500 640H745" stroke={INK} strokeWidth={13}/>
  </svg>
</>;
export const ProbationObjectsSet: React.FC<{paper?: string}> = ({paper}) => <>
  <Paper color={paper ?? '#E9E1F2'}/>
  <svg width={1000} height={900} style={{position:'absolute',inset:0}} aria-label="자동차 열쇠와 날짜 없는 달력 및 서류">
    <path d="M0 785H1000V900H0Z" fill="#B9ABC4" {...S}/>
    <ellipse cx={435} cy={786} rx={355} ry={32} fill="#9E90AB"/>
    <g transform="translate(200 325) rotate(-18)">
      <circle cx={0} cy={0} r={88} fill="none" stroke={INK} strokeWidth={22}/>
      <circle cx={0} cy={0} r={88} fill="none" stroke="#A9BAC9" strokeWidth={12}/>
      <path d="M0 85V252H30V222H60V194H30V85Z" fill={YELLOW} {...S}/>
      <rect x={-68} y={-60} width={136} height={110} rx={30} fill="#2D3F73" {...S}/>
      <path d="M-45 8L-32-23H32L45 8V30H-45ZM-31 3H31M-32 28V40M32 28V40" fill="#BFD8E6" stroke={INK} strokeWidth={6} strokeLinejoin="round"/>
    </g>
    <g transform="rotate(6 655 640)">
      <path d="M545 485H700L750 535V770H545Z" fill={PAPER} {...S}/>
      <path d="M700 485V535H750" fill="#A5B2C8" {...S}/>
      {[580,617,654,691].map(y=><path key={y} d={`M575 ${y}H714`} stroke="#8290A8" strokeWidth={9} strokeLinecap="round"/>)}
      <circle cx={654} cy={726} r={22} fill={TEAL} stroke={INK} strokeWidth={5}/>
    </g>
    <rect x={120} y={530} width={370} height={245} rx={18} fill={PAPER} {...S}/>
    <path d="M120 590H490V548Q490 530 472 530H138Q120 530 120 548Z" fill="#2D3F73" {...S}/>
    {[180,290,400].map(x=><path key={x} d={`M${x} 510V548`} stroke={INK} strokeWidth={14} strokeLinecap="round"/>)}
    {[0,1,2].map(r=>[0,1,2,3].map(c=><rect key={`${r}-${c}`} x={154+c*80} y={620+r*44} width={42} height={24} rx={5} fill={(r+c)%3===0?'#C8D6E3':'#E7E0EB'}/>))}
  </svg>
</>;
