import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Puppet,C,Role,Expression,View} from './Puppets_v2';
import {Parking,Court,Bench,Investigation,Desk} from './Sets';
import {fontCss} from './Pilot_v2';
const roles:Role[]=['host','employee','robberA','robberB','detective','judge'];
const names=['진행자 · 단추','은행 직원 · 익명','강도 A · 긴 후드','강도 B · 짧은 비니','형사 · 모서리','판사 · 쇼츠 기준'];
const cols=['정면','3/4','측면','후면','기본','의문 / 경계','놀람 / 긴장','단호 / 버팀'];
export const StyleSheet:React.FC=()=><AbsoluteFill style={{background:C.paper}}><svg width={3600} height={3360} viewBox="0 0 3600 3360"><style>{fontCss()}</style>
 <g fontFamily="Cartoon Pretendard" fill={C.ink}><text x={78} y={88} fontSize={62} fontWeight={700}>몇년나옴 · CARTOON LONG-FORM</text><text x={80} y={141} fontSize={30}>독창적 인물 / 2D SVG 리그 / 16:9 · 표정 없는 인물은 실루엣과 자세로 표현</text>
 {Object.values(C).slice(0,10).map((color,i)=><rect key={i} x={2460+i*100} y={58} width={73} height={73} rx={14} fill={color} stroke={C.line} strokeWidth={4}/>)}
 {cols.map((name,j)=><text key={name} x={570+j*398} y={206} fontSize={27} textAnchor="middle">{name}</text>)}
 {roles.map((role,i)=>{const top=237+i*385;return <g key={role}><path d={`M75 ${top+358}L3500 ${top+358}`} stroke="#D8CEB6" strokeWidth={3}/><text x={80} y={top+142} fontSize={32} fontWeight={700}>{names[i]}</text><text x={80} y={top+187} fontSize={23} fill="#766D59">{i===1?'동일 익명 리그 × 3':i===2||i===3?'얼굴·피부 노출 없음':'머리 / 눈 / 입 / 팔 분리'}</text>
 {Array.from({length:8},(_,j)=>{const view:View=j<4?(['front','three-quarter','profile','back'] as View[])[j]:'front';const expr:Expression=j<4?'neutral':(['neutral','skeptic','alarm','resolve'] as Expression[])[j-4];return <Puppet key={j} role={role} x={570+j*398} y={top+313} scale={.42} f={0} still seed={i+1} view={view} expr={expr} gesture={j===5?'shrug':j===7?'point':'rest'}/>;})}</g>;})}
 <text x={80} y={2672} fontSize={35} fontWeight={700}>배경 3종 · 그림자는 1단계 / 촬영 텍스트는 자막만</text>
 {[0,1,2].map((s)=><g key={s} transform={`translate(${80+s*1170} 2720)`}><svg width={1100} height={619} viewBox="0 0 1920 1080">{s===0?<Parking f={0}/>:s===1?<><Investigation f={0}/><Desk f={0}/></>:<><Court f={0}/><Bench/></>}</svg><rect width={1100} height={619} fill="none" stroke={C.line} strokeWidth={5}/><rect y={545} width={1100} height={74} fill={C.paper} opacity={.94}/><text x={25} y={595} fontSize={31} fontWeight={700}>{['은행 지하주차장 · 비식별 재구성','수사실 · 가상 공간 / 자료는 무문자','법정 · 쇼츠 나무 패널 확장'][s]}</text></g>)}
 </g></svg></AbsoluteFill>;
