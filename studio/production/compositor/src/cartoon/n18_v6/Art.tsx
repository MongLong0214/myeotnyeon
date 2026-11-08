import React from 'react';
import {Puppet} from '../engine_v6/Puppet';

const ink='#17152b',green='#507e6c',white='#fff5db';
const smooth=(v:number)=>{v=Math.max(0,Math.min(1,v));return v*v*(3-2*v)};
export const Recruit:React.FC<{x:number;y:number;f:number;s?:number;seed?:number;action?:string;fall?:number;officer?:boolean;pack?:boolean;weapon?:boolean}>=({x,y,f,s=1,seed=0,action='march',fall=0,officer=false,pack=true,weapon=false})=>{
 if(action==='push'){
  const lift=Math.sin((f+seed*9)*.11)*14;
  return <g transform={`translate(${x} ${y}) scale(${s})`} stroke={ink} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round">
   <ellipse cx={-15} cy={5} rx={190} ry={11} fill={ink} opacity={.16} stroke="none"/>
   <path d={`M-69 ${-82+lift}L-140-21L-170-3M-34 ${-80+lift}L-114-22L-140-2`} fill="none" strokeWidth={29}/>
   <path d={`M-69 ${-82+lift}L-140-21M-34 ${-80+lift}L-114-22`} fill="none" stroke={green} strokeWidth={18}/>
   <path d={`M-95 ${-109+lift}L63 ${-108+lift}L77 ${-66+lift}L-75 ${-57+lift}Z`} fill={green}/>
   <path d={`M-70 ${-121+lift}Q-36 ${-174+lift} 12 ${-128+lift}L12 ${-106+lift}L-70 ${-103+lift}Z`} fill="#698c78"/>
   <path d={`M46 ${-84+lift}L83-39L102-4M69 ${-89+lift}L120-42L138-4`} fill="none" strokeWidth={27}/>
   <path d={`M46 ${-84+lift}L83-39L102-4M69 ${-89+lift}L120-42L138-4`} fill="none" stroke={green} strokeWidth={16}/>
   <ellipse cx={105} cy={-4} rx={18} ry={9} fill="#a7aa8a"/><ellipse cx={141} cy={-4} rx={18} ry={9} fill="#a7aa8a"/>
   <g transform={`translate(111 ${-99+lift})`}><ellipse rx={39} ry={37} fill="#8e8d76"/><path d="M-42-10Q-40-55 5-43Q46-36 40 0L5-6Z" fill="#598370"/></g>
  </g>;
 }
 const run=action==='run',t=f+seed*19,stride=(action==='rest'?0:Math.sin(t*(run?.52:.28)))*(1-fall),boil=fall>.98?0:Math.floor(f/3),b=fall>0?0:Math.sin(t*(run?.52:.28))*(run?8:3);
 const a=fall>0?fall*87:(run?11:0)+Math.sin(t*.12)*2,shade=officer?'#27373e':green;
 const leg=(side:number)=>{const knee=side*22+(action==='push'?0:stride*side*(run?35:18));return <g key={side}><path d={`M${side*22} -139L${knee} -75L${side*26-stride*side*(run?41:14)} -9`} fill="none" stroke={ink} strokeWidth={34} strokeLinecap="round"/><path d={`M${side*22} -139L${knee} -75L${side*26-stride*side*(run?41:14)} -9`} fill="none" stroke={shade} strokeWidth={22} strokeLinecap="round"/><path d={`M${side*26-stride*side*(run?41:14)-16} -14h43v17h-43Z`} fill={ink}/></g>};
 const body=<g transform={`translate(${Math.sin(boil*4+seed)*.7} ${Math.cos(boil*5+seed)*.7})`} stroke={ink} strokeWidth={6} strokeLinejoin="round">
  {[-1,1].map(leg)}<path d="M-43-260Q0-277 43-260L51-133Q0-119-51-133Z" fill={shade}/>
  {[-1,1].map(side=><g key={side} transform={`translate(${side*41} -245) rotate(${officer?side===1?-80+Math.sin(t*.23)*12:9:side*stride*(run?35:16)})`}><path d="M0 0L4 66L-4 116" stroke={ink} strokeWidth={28} fill="none" strokeLinecap="round"/><path d="M0 0L4 66L-4 116" stroke={shade} strokeWidth={17} fill="none" strokeLinecap="round"/><ellipse cx={-4} cy={120} rx={12} ry={15} fill={officer?'#283b3f':'#c7b99b'}/></g>)}
  <path d="M-14-286V-257H14V-286" fill={officer?'#26383c':'#998e79'}/><path d="M-52-319Q-52-376 2-374Q58-371 55-315L38-279Q0-262-36-282Z" fill={officer?'#26343c':'#8e8d76'}/><path d="M-59-322Q-68-385 0-387Q69-384 63-322L36-337H-35Z" fill={officer?'#263d3b':'#598370'}/><path d="M-49-323Q0-342 50-322" fill="none" stroke="#2a4f48" strokeWidth={10}/>
  {pack&&!officer&&<g><path d="M-44-256Q0-272 44-256L50-151Q0-137-50-151Z" fill="#54746b"/><path d="M-30-255V-146M30-255V-146" stroke="#203f3f" strokeWidth={12}/><path d="M-39-242L-29-212H31L41-242Z" fill="#81a08a"/><path d="M-37-167H38" stroke="#95aa8e" strokeWidth={5}/></g>}
 {weapon&&<g transform="translate(20 -205) rotate(-32)"><path d="M-8-102H8V75H-8Z" fill="#293a3b"/><path d="M-22 5H19V55H-22ZM-12 60H19V105H-12Z" fill="#59665c"/></g>}
 </g>;
 return <g transform={`translate(${x} ${y+b}) scale(${s})`}><ellipse rx={94+fall*60} ry={12} fill={ink} opacity={.15}/>{action==='push'?<g transform={`translate(80 ${-63+Math.sin(t*.19)*16}) rotate(-82) scale(.9)`}>{body}</g>:<g transform={`translate(${-fall*90} 0) rotate(${a})`}>{run&&!fall&&f%24<4&&[2,1].map(k=><g key={k} transform={`translate(${-k*27} ${k*2})`} opacity={.11/k}>{body}</g>)}{body}</g>}
 {run&&!fall&&[0,1].map(j=><path key={j} d={`M${-95-j*28} ${-170-j*35}h-50`} stroke={white} strokeWidth={5} opacity={.55}/>)}</g>;
};
const Cross=({x,y,s=1}:{x:number;y:number;s?:number})=><path d="M-12-36H12V-12H36V12H12V36H-12V12H-36V-12H-12Z" transform={`translate(${x} ${y}) scale(${s})`} fill="#47a78f" stroke={ink} strokeWidth={4}/>;
export const Medic=({x,y,f,s=1,reach=false,flip=false}:{x:number;y:number;f:number;s?:number;reach?:boolean;flip?:boolean})=><g transform={`translate(${x} ${y+Math.sin(f*.14)*2}) rotate(${Math.sin(f*.1)*.6}) scale(${flip?-s:s} ${s})`} stroke={ink} strokeWidth={6} strokeLinejoin="round"><ellipse rx={85} ry={12} opacity={.15} fill={ink}/><path d="M-26-146L-31-12M29-145L43-12" stroke={ink} strokeWidth={34} strokeLinecap="round"/><path d="M-26-146L-31-12M29-145L43-12" stroke="#4b7890" strokeWidth={22}/><path d="M-47-270Q0-288 48-269L57-143Q0-129-57-145Z" fill="#d4eee1"/><path d={`M-40-250L${reach?-72:-58} -185L${reach?-115:-48} ${reach?-170+Math.sin(f*.12)*12:-139}M44-251L${reach?78:70} -194L${reach?135+Math.sin(f*.12)*15:64} ${reach?-170+Math.sin(f*.12)*12:-139}`} fill="none" stroke={ink} strokeWidth={28} strokeLinecap="round"/><path d={`M-40-250L${reach?-72:-58} -185L${reach?-115:-48} ${reach?-170+Math.sin(f*.12)*12:-139}M44-251L${reach?78:70} -194L${reach?135+Math.sin(f*.12)*15:64} ${reach?-170+Math.sin(f*.12)*12:-139}`} fill="none" stroke="#d4eee1" strokeWidth={17} strokeLinecap="round"/><ellipse cx={reach?135+Math.sin(f*.12)*15:64} cy={reach?-167+Math.sin(f*.12)*12:-136} rx={13} ry={17} fill="#f0cdab"/><path d="M-18-292V-266H18V-292" fill="#cfad91"/><ellipse cy={-325} rx={44} ry={52} fill="#bead91"/><path d="M-48-328L-42-374Q0-394 46-367L50-326Z" fill="#e1f6e9"/><path d="M-39-306Q0-286 37-306V-285Q0-270-39-285Z" fill="#cce8df"/><Cross x={0} y={-352} s={.44}/><Cross x={1} y={-210} s={.45}/></g>;
const Bed=({x,y,f,transport=false}:{x:number;y:number;f:number;transport?:boolean})=><g transform={`translate(${x} ${y})`} stroke={ink} strokeWidth={7} strokeLinejoin="round"><path d="M-255-36H250V-12H-255Z" fill="#ccded3"/><path d="M-235-12L-210 62M220-12L204 62M-194-3H190" stroke="#869d9b" strokeWidth={13} fill="none"/>{[-207,204].map(k=><circle key={k} cx={k} cy={65} r={21} fill="#41495c"/>)}<ellipse cx={-178} cy={-87} rx={41} ry={33} fill="#8b9380"/><path d="M-219-91Q-200-138-164-122L-144-95" fill="#697c6f"/><path d="M-137-111Q-56-146 60-91L207-77L217-42H-147Z" fill="#708981"/><path d="M-125-120Q-10-139 112-95L209-78L214-43H-143Z" fill="#adc6ba"/><path d="M-235-33V-78M235-33V-71" fill="none" strokeWidth={10}/>{transport&&[0,1].map(j=><path key={j} d={`M${-320-j*45} ${j*28-32}h-65`} stroke="#e4edce" strokeWidth={6}/>)}</g>;
const flower=(x:number,y:number,i:number)=> <g key={i} transform={`translate(${x} ${y}) rotate(${i*9-20})`} stroke={ink} strokeWidth={3}><path d="M0 0L15 135M8 70Q-34 40-22 99M14 91Q55 58 45 112" fill="#63957c"/>{Array.from({length:8},(_,j)=><ellipse key={j} transform={`rotate(${j*45})`} cy={-18} rx={10} ry={23} fill={white}/>)}<circle r={11} fill="#c6ca9d"/></g>;
export const Backdrop=({kind,f}:{kind:string;f:number})=>{
 const t=Math.sin(f/70)*12;
 if(kind==='ground')return <g stroke={ink} strokeWidth={6}><rect width={1920} height={1080} fill="#c6e0c0"/><g transform={`translate(${t*.3} 0)`}><path d="M-80 440L120 140L360 322L590 85L840 440M620 420L1120 100L1350 309L1650 170L2040 440" fill="#87ac9a" stroke="none"/><path d="M-100 465V310L400 270L700 329V470Z" fill="#5d8371"/><path d="M-130 312L400 231L730 330" fill="#466459"/>{[30,160,290,420,550].map(x=><rect key={x} x={x} y={348} width={67} height={72} fill="#a7cab9"/>)}</g><path d="M0 453L1920 469V1080H0Z" fill="#c9996a"/><path d="M-100 1040Q240 602 800 591H2010M-160 1190Q340 704 850 704H2090" stroke="#ecd3a4" strokeWidth={17} fill="none"/><path d="M0 467L1920 484" stroke="#846c58" strokeWidth={13}/></g>;
 if(kind==='barracks')return <g stroke={ink} strokeWidth={8}><rect width={1920} height={1080} fill="#3d5865"/><path d="M0 700H1920V1080H0Z" fill="#526a73"/>{[100,730,1360].map(x=><g key={x} transform={`translate(${x+t*.2} 0)`}><path d="M0 300V850M480 300V850M-10 500H492M-10 775H492" fill="none" stroke="#a1b9b2" strokeWidth={18}/><path d="M8 442H471V493H8ZM8 716H471V767H8Z" fill="#a7a78e"/><path d="M36 414H149V441H36ZM36 688H149V715H36Z" fill="#c7c9b2"/></g>)}</g>;
 if(kind==='medical')return <g stroke={ink} strokeWidth={7}><rect width={1920} height={1080} fill="#b1d9cf"/><path d="M0 760H1920V1080H0Z" fill="#8eb1a8"/>{[110,1280].map(x=><g key={x}><path d={`M${x} 158h440v605h-440Z`} fill="#6d9891"/><path d={`M${x+35} 200h370v275h-370Z`} fill="#9ac9c1"/><path d={`M${x+216} 479v279`} fill="none" strokeWidth={11}/></g>)}<Cross x={960} y={190} s={1.3}/><path d="M0 550H1920" stroke="#d6ecdc" strokeWidth={18}/></g>;
 if(kind==='road')return <g stroke={ink} strokeWidth={7}><rect width={1920} height={1080} fill="#33485d"/><path d={`M-100 500L300 160L540 400L920 200L1350 490L1680 260L2050 480V860H-100Z`} fill="#405e69" stroke="none"/><path d="M0 765L1920 700V1080H0Z" fill="#35384e"/><path d={`M${-(f*26)%340} 959H${2180-(f*26)%340}`} stroke="#e1d6b6" strokeWidth={12} strokeDasharray="170 180"/></g>;
 if(kind==='court')return <g stroke={ink} strokeWidth={7}><rect width={1920} height={1080} fill="#625070"/>{[100,450,1470,1810].map(x=><path key={x} d={`M${x} 120v650h-65V120Z`} fill="#a28b9e"/>)}<path d="M580 140H1350V673H580Z" fill="#44354f"/><circle cx={960} cy={290} r={87} fill="#b6a074"/><path d="M930 230L990 230L1022 291L960 346L899 291Z" fill="#d5c39a"/><path d="M0 760H1920V1080H0Z" fill="#7c665d"/><path d="M0 897L960 742L1920 897" stroke="#b49b7f" fill="none"/></g>;
 if(kind==='memorial')return <g stroke={ink} strokeWidth={6}><rect width={1920} height={1080} fill="#a6b7ba"/><path d="M0 735H1920V1080H0Z" fill="#7e9494"/><path d="M700 345H1280V785H700Z" fill="#43535f"/><path d="M820 475H1160V745H820Z" fill="#c5cbb8"/><path d="M858 513H1123V698H858Z" fill="#e5e0c5"/><circle cx={990} cy={560} r={23} fill="#b7ae7d"/><path d="M903 616H1083M930 644H1052" stroke="#929b87" strokeWidth={9}/><path d="M580 758H1400V817H580Z" fill="#526969"/>{[0,1,2,3,4,5,6,7].map(i=>flower(660+i*93,736+Math.sin(i)*12,i))}</g>;
 return <g stroke={ink} strokeWidth={7}><rect width={1920} height={1080} fill="#b3a8cc"/><path d="M0 780H1920V1080H0Z" fill="#817c9c"/>{[180,1260].map(x=><g key={x}><path d={`M${x} 200h460v400h-460Z`} fill="#8e9db0"/><path d={`M${x+25} 230h410v340h-410Z`} fill="#d2d6c4"/></g>)}<path d="M560 770H1340V820H560Z" fill="#846f65"/><path d="M600 820V1010M1300 820V1010" strokeWidth={18}/></g>;
};

// N18 v6 uses fixed blocking and a global acting clock. Camera cuts never restart
// the actors or apply a random zoom, roll, whip or alternating movement direction.
const Txt=({x,y,children,size=38,color=white,anchor='middle'}:any)=><text x={x} y={y} textAnchor={anchor} fontSize={size} fill={color} stroke="none" fontWeight={800}>{children}</text>;
const Panel=({x=960,y=510,lines=[],title='',w=610}:any)=><g transform={`translate(${x} ${y})`} stroke={ink} strokeWidth={6}><path d={`M${-w/2} -158h${w}v316h-${w}Z`} fill="#eee4c9"/><path d={`M${-w/2} -158h${w}v65h-${w}Z`} fill="#3e5f62"/><Txt x={0} y={-113} size={31}>{title}</Txt>{lines.map((l:string,i:number)=><Txt key={i} x={0} y={-29+i*51} size={30} color={ink}>{l}</Txt>)}</g>;
const Desk=({x,y=825,w=350}:any)=><g stroke={ink} strokeWidth={7}><path d={`M${x-w/2} ${y}h${w}v110h-${w}Z`} fill="#805d60"/><path d={`M${x-w/2-14} ${y-20}h${w+28}v31h-${w+28}Z`} fill="#bd8878"/></g>;
const Pack=({x=950,y=690,f=0,books=false}:any)=><g transform={`translate(${x} ${y})`} stroke={ink} strokeWidth={7}><path d="M-105-154Q0-184 105-154L118 122H-118Z" fill="#5a8071"/>{books&&[0,1,2,3,4].map(j=><g key={j} transform={`translate(${-82+j*34} ${-145-Math.max(0,1-smooth(f/35))*75})`}><path d="M0 0h29v128H0Z" fill={['#d9c28d','#8596af','#c2c296'][j%3]}/><path d="M6 8v108" stroke="#f0e5cb" strokeWidth={3}/></g>)}<path d="M-113-12H113L118 122H-118Z" fill="#789e87"/><path d="M-80-147V120M80-147V120" stroke="#314f4c" strokeWidth={12}/></g>;
const DocumentLines:Record<string,{title:string;lines:string[]}>= {
 judge:{title:'법원 판단',lines:['학대치사 · 유죄']},purpose:{title:'1심 양형 이유',lines:['교육 목적 참작','학대치사 유죄']},
 missing:{title:'빠진 절차',lines:['확인서 미작성','소명 기회 미부여']},rule:{title:'군기훈련 규정',lines:['절차 · 방법 위반']},
 unchecked:{title:'시행 전 확인 미흡',lines:['신체 상태','훈련장 온도지수']},basic:{title:'훈련 전 기본',lines:['사람 · 날씨 확인','응급상황 대비']},
 order:{title:'논평',lines:['확인보다 앞선 명령']},contrast:{title:'논평',lines:['비워진 안전 절차','채워진 군장']},
 record:{title:'병원 이송 기록',lines:['의무대 → 병원']},fever:{title:'이송 당시',lines:['40°C 초과 고열']},
 damage:{title:'속초의료원 관계자 설명',lines:['도착 때 검사','장기 손상 의심 · 중증']},
 transfer_interval:{title:'두 병원 사이 전체 경과',lines:['속초의료원 → 강릉아산병원','약 3시간']},not_drive:{title:'전체 경과 ≠ 주행시간',lines:['두 병원 사이 약 3시간','차로 달린 시간은 미확정']},
 cause:{title:'수사결과 보도 · 사인',lines:['열사병에 의한','다발성 장기부전']},
 letter:{title:'어머니 편지',lines:['첫 전화 시각 기록']},call_time:{title:'아들이 쓰러졌다는 전화',lines:['05-23','17:54']},
 book_testimony:{title:'동료의 법정 증언',lines:['책 약 40권','군장에 넣었다는 취지']},not_weight:{title:'증언 범위',lines:['책 약 40권','실제 무게 확정치 아님']},
 distress:{title:'동료 한 명의 법정 진술',lines:['외상 후 스트레스 장애','진단을 받았다고 밝힘']},regret:{title:'동료 증인의 아쉬움',lines:['처치가 더 빨랐다면…','의학적 확정 판단 아님']},
 investigate:{title:'검찰 판단',lines:['단순 과실로 보지 않음']},evidence:{title:'검찰의 종합 판단',lines:['방식 · 경과 · 신체조건','학대로 판단']},
 indict:{title:'두 지휘관 기소',lines:['학대치사','직권남용 가혹행위']},defense:{title:'중대장 측 변호인 주장',lines:['잘못된 행동 인정','학대치사 혐의 부인']},
 guilty:{title:'법원 판단',lines:['학대치사 · 유죄']},unfit:{title:'재판부 판단',lines:['신체조건에 맞지 않는 훈련','죄책이 무거움']},
 trust:{title:'재판부 판단',lines:['군 사기 · 전투력','국민 신뢰 훼손']},trust_comment:{title:'논평',lines:['군의 신뢰를 무너뜨린 책임']},
 no_forgiveness:{title:'재판부 지적',lines:['피해자 측 용서받지 못함']},turn_page:{title:'1심 판결 · 다음 이유',lines:['양형 이유']},
 remorse:{title:'1심 양형 이유',lines:['사실관계 인정','반성 태도 참작']},purpose_comment:{title:'논평',lines:['교육 목적을 고려한 판결','학대치사 유죄']},
 sentence_question:{title:'선고는 몇 년이었을까?',lines:['1심 판결']},not_acquittal:{title:'유죄 판단 유지',lines:['무죄라는 뜻이 아님']},
 distinguish:{title:'판결 해설',lines:['목적 참작 ≠ 행위 정당화','유죄 판단 / 양형 이유']},
 prosecutor_date:{title:'검찰 구형',lines:['2024-11-12']},request_a:{title:'검찰 구형 · 요청',lines:['중대장 징역 10년']},request_b:{title:'검찰 구형 · 요청',lines:['부중대장 징역 7년']},
 request_only:{title:'구형',lines:['검찰의 요청','선고가 아님']},trust_request:{title:'검찰 구형 이유',lines:['군 지도력 · 관리 체제','신뢰 훼손']},
 verdict_date:{title:'춘천지법 · 1심 선고',lines:['2025-01-07']},sentence_a:{title:'1심 선고',lines:['중대장 징역 5년']},sentence_b:{title:'1심 선고',lines:['부중대장 징역 3년']},
 compare:{title:'요청과 선고',lines:['중대장 10년 → 5년','부중대장 7년 → 3년']},not_final:{title:'중대장 1심',lines:['징역 5년','아직 최종 형량 아님']},
 appeal:{title:'항소심의 변경',lines:['하나의 행위인가?']},group:{title:'1심 · 상상적 경합',lines:['하나의 행위','여러 범죄']},separate:{title:'항소심 판단',lines:['같은 장소 · 기회만으로','하나로 묶을 수 없음']},
 individual:{title:'항소심 판단',lines:['피해자별 다른 양상','사람별 피해 구분']},plural:{title:'항소심 · 실체적 경합',lines:['여러 행위','여러 죄']},
 ungroup:{title:'논평 · 사람별 피해',lines:['여섯 사람을 나누어 보기']},not_six_crimes:{title:'설명 범위',lines:['정확히 죄 6개라는','계산은 아님']},
 appeal_date:{title:'항소심 선고',lines:['2025-06-18','중대장 징역 5년 6개월']},increase:{title:'중대장 항소심',lines:['5년 → 5년 6개월','1심보다 +6개월']},
 deputy_sentence:{title:'부중대장 항소심',lines:['징역 3년 유지']},separate_reason:{title:'판결 이유 구분',lines:['중대장 증형 이유를','부중대장에게 옮길 수 없음']},
 preventable:{title:'항소심의 지적',lines:['충분히 예방할 수 있었던','사망사고']},culture:{title:'항소심의 지적',lines:['후진적 병영문화 답습']},
 duty:{title:'항소심 판단',lines:['국가의 생명 · 신체 보호','사회 기본 기대 배반']},safe_return:{title:'논평',lines:['안전하게 돌려보낼 기대']},baseline:{title:'논평',lines:['생명과 안전 보호는 기본']},
 dismiss:{title:'대법원 · 중대장 상고 기각',lines:['2025-09-25']},final_a:{title:'중대장 · 확정',lines:['징역 5년 6개월']},final_b:{title:'부중대장 · 확정 상태',lines:['징역 3년','확정일 미채택']},
 not_same_day:{title:'확정 상태 구분',lines:['중대장 2025-09-25','부중대장 확정일 미채택']},
 policy:{title:'국방부 재발방지 대책',lines:['군기훈련 절차 보완']},exclude_exercise:{title:'2024-06-27 국방부 발표',lines:['훈련병 군기훈련','체력단련 종목 제외']},
 explain:{title:'절차 표준화',lines:['개인 소명 반드시 거침']},missing_explain:{title:'사건에서 빠진 단계',lines:['개인 소명']},authorize:{title:'육군 신병교육부대',lines:['승인권자','영관급 지휘관으로 상향']},
 health:{title:'훈련 전 · 중 확인',lines:['건강상태 수시 확인']},weather:{title:'기상에 따른 판단',lines:['장소 · 진행 여부']},emergency_plan:{title:'시행 전 준비',lines:['응급상황 대비책']},
 summer:{title:'혹서기 관리 기간 확대',lines:['07-01 시작 → 06-01 시작']},summer_end:{title:'혹서기 관리 종료',lines:['08-31 유지']},measure:{title:'온도지수 측정',lines:['하루 3회 이상']},
 implementation:{title:'논평',lines:['대책 발표 이후','현장 안전 확인 필요']},list:{title:'발표된 대책',lines:['소명 · 건강 · 기상','승인 · 응급상황 대비']},
 certificate:{title:'명예수료증',lines:['2024-06-19','인제체육관 수료식장']},mother_letter:{title:'어머니 편지',lines:['수료생 251명 가운데','아들만 부재']},
};

export const N18Stage=({shot:s,f,shots}:any)=>{
 const loc=s.location,a=s.action;const pf=f;const local=f-s.performanceStart;
 const all=shots as any[];
 const first=(nid:string)=>all.find(x=>x.narrationId===nid)?.performanceStart??s.performanceStart;
 const heading=/court|appeal/.test(loc)?'법정':loc==='supreme'?'대법원':loc==='sokcho'?'속초의료원':loc==='gangneung'?'강릉아산병원':loc==='infirmary'?'의무대':loc==='icu'?'중환자실':loc==='memorial'?'인제체육관 · 수료식장':loc==='yongsan'?'용산역 · 분향소':loc==='policy'?'재발방지 대책':loc==='command'?'지휘관 보고·승인':loc==='barracks'?'취침점호 뒤 · 생활관':loc==='packing'?'군장 결속':loc==='family'?'어머니의 편지':loc==='entrance_memory'?'편지 속 입영 날 기억':loc==='prosecution'?'검찰 수사 자료':loc==='record'?'수사결과 보도':'강원 인제 · 육군 12사단 신병교육대';
 const dates:Record<string,string>={date:'2024-05-23',clock:'16:26경',collapse:s.narrationId==='N015'?'17:11경':'',elapsed:'약 45분 경과',delay:'경찰 수사결과',call_time:'05-23 · 17:54',arrival_time:'21:40경',loss:'2024-05-25',witness_date:'2024-08-27',prosecutor_date:'2024-11-12',verdict_date:'2025-01-07',appeal_date:'2025-06-18',dismiss:'2025-09-25',exclude_exercise:'2024-06-27',certificate:'2024-06-19',book_testimony:'약 40권 · 증언',not_weight:'실제 무게 미확정',summer:'07-01 → 06-01',summer_end:'08-31'};
 const stamp=dates[a]??'';
 const kind=/ground|entrance/.test(loc)?'ground':loc==='barracks'?'barracks':/infirmary|sokcho|gangneung|icu/.test(loc)?'medical':/court|appeal|supreme/.test(loc)?'court':/memorial|yongsan/.test(loc)?'memorial':'office';
 const panel=s.narrationId==='N037'&&a==='guilty'?{title:'1심 법원 판단',lines:['두 사람 유죄','훈련과 사망 인과관계 인정']}:DocumentLines[a];
 const doc=(x=960,y=480)=>(panel&&!(s.subject==='rucksack'||(s.size==='close'&&!['judgment','legal_diagram','medical_record','policy_document','records','mother_letter','documents','health_weather'].includes(s.subject))))?<Panel x={x} y={y} {...panel}/>:null;
 const court=/court|appeal|supreme/.test(loc);
 const witnessScene=/^N0(27|28|29|32|33)$/.test(s.narrationId);
 const officer=(x:number,label:string,flip=false)=><g><Puppet role="instructor" x={x} y={880} scale={.94} f={pf} view="profile" flip={flip} gesture="point" anonymous take={0}/><Txt x={x} y={923} size={28}>{label}</Txt></g>;
 const recruits=(act='rest',pack=true)=>[0,1,2,3,4,5].map(j=><Recruit key={j} x={350+j*242+(/march|run/.test(act)&&/^N01[123]$/.test(s.narrationId)?Math.min(120,Math.max(0,f-first('N011'))*.22):0)} y={j%2?874:801} f={pf} s={j%2?.91:.74} seed={j} action={act} pack={pack} weapon={act==='march'||act==='run'}/>);
 let focus={x:960,y:510};
 if(s.subject==='commander')focus={x:court?650:1290,y:635};
 else if(s.subject==='deputy')focus={x:court?825:540,y:635};
 else if(s.subject==='defense')focus={x:420,y:620};
 else if(s.subject==='judge')focus={x:1460,y:560};
 else if(s.subject==='witness')focus={x:830,y:645};
 else if(s.subject==='witnesses')focus={x:960,y:650};
 else if(s.subject==='prosecutor')focus={x:420,y:610};
 else if(s.subject==='recruit'||s.subject==='officers_patient')focus={x:1030,y:745};
 else if(s.subject==='rucksack')focus={x:witnessScene?1120:960,y:650};
 else if(s.subject==='medical_record')focus={x:960,y:/infirmary|sokcho|gangneung|icu/.test(loc)?340:490};
 else if(s.subject==='patient')focus={x:960,y:650};
 else if(s.subject==='mother'||s.subject==='parents'||s.subject==='family')focus={x:950,y:650};
 else if(s.subject==='empty_chair')focus={x:620,y:690};
 else if(s.subject==='mourners')focus={x:760,y:700};
 else if(s.subject==='mother_letter'&&loc==='memorial')focus={x:980,y:390};
 else if(/memorial|certificate/.test(s.subject))focus={x:980,y:600};
 else if(s.subject==='recruits'||s.subject==='six_recruits')focus={x:960,y:655};
 if(a==='collapse'&&s.size!=='wide')focus={x:1030,y:610+smooth((f-s.fallStart)/Math.max(1,s.fallEnd-s.fallStart))*125};
 const z=s.size==='wide'?1:s.size==='medium'?1.38:1.88;
 if(s.size==='wide')focus={x:960,y:540};
 const world=()=>{
  if(court)return <>
   <Puppet role="judge" x={1460} y={790} scale={.88} f={pf} view="profile" flip gesture="read" expr="resolve" take={0}/><Desk x={1460} y={725} w={370}/>
   <Puppet role="lawyer" x={420} y={870} scale={.9} f={pf} view="profile" gesture="read" expr="resolve" take={0}/><Desk x={420}/>
   {!witnessScene&&<><Puppet role="defendantA" x={650} y={920} scale={.75} f={pf} view="back" gesture="hold" take={0}/><Puppet role="defendantB" x={825} y={920} scale={.72} f={pf} view="back" gesture="hold" take={0}/><g><rect x={578} y={750} width={144} height={42} rx={6} fill={ink}/><Txt x={650} y={780} size={25}>중대장</Txt><rect x={745} y={750} width={160} height={42} rx={6} fill={ink}/><Txt x={825} y={780} size={25}>부중대장</Txt></g></>}
   {witnessScene&&<>{[0,1,2,3].map(j=><Recruit key={j} x={600+j*230} y={905} f={0} s={j===1?.92:.65} action="rest" pack={false}/>)}<Desk x={830} y={860} w={290}/>{(a==='four_witnesses'||a==='witness_date'||a==='witness_wide')&&s.size!=='close'?<Panel x={970} y={310} title="동료 증인 4명" lines={a==='witness_date'?['2024-08-27 공판']:['그날 출석한 증인 수']}/>:null}</>}
   {/book_testimony|not_weight/.test(a)&&<Pack x={1120} y={760} books f={99}/>}
   {/individual|ungroup/.test(a)&&<g>{[0,1,2,3,4,5].map(j=><g key={j}><rect x={475+j*170} y={570} width={145} height={260} rx={12} stroke="#b2d9be" fill="#314951" strokeWidth={5}/><Recruit x={548+j*170} y={815} f={0} s={.47} action="rest" pack={false}/></g>)}</g>}
   {/group|plural|separate|not_six_crimes/.test(a)&&<g stroke={ink} strokeWidth={6}>{[0,1,2].map(j=><g key={j}><path d={`M${700+j*210} 735v-56`} stroke="#e8d891"/><rect x={620+j*210} y={730} width={160} height={65} fill="#aac5af"/><Txt x={700+j*210} y={775} size={25} color={ink}>{a==='group'?'범죄':'행위·죄'}</Txt></g>)}</g>}
   {doc(1000,/individual|ungroup/.test(a)?345:475)}
  </>;
  if(/ground/.test(loc)){
   const collapse=a==='collapse',hold=/elapsed|stopped|emergency|delay|patient|rebuke/.test(a);
   let fall=hold?1:collapse?smooth((f-s.fallStart)/Math.max(1,s.fallEnd-s.fallStart)):0;
   if(collapse||hold)return <>
    <Recruit x={860} y={835} f={fall>.01?0:pf} s={1} action={fall>.01?'rest':'run'} fall={fall}/>
    <Recruit x={400} y={810} f={0} s={.8} action="rest"/><Recruit x={1580} y={850} f={0} s={.86} action="rest"/>
    {officer(1370,'중대장',true)}{officer(570,'부중대장')}
    {a==='emergency'&&<Txt x={970} y={350} size={35}>논평 · 응급조치가 필요했던 상황</Txt>}
    {(a==='elapsed'||s.narrationId==='N015')&&s.size==='wide'&&<Panel x={960} y={305} title={a==='elapsed'?'약 45분 경과':'훈련병 쓰러짐'} lines={a==='elapsed'?['16:26 → 17:11']:['17:11경']}/>}
    
    {a==='delay'&&s.size==='wide'&&<Panel x={960} y={300} title="경찰 수사결과" lines={['열사병 위급함 인지 미흡','응급처치 지체']}/>}
   </>;
   const act=a==='push'?'push':/run|race/.test(a)?'run':a==='march'?'march':'rest';
   return <>{recruits(act)}{a==='pack_detail'&&<Pack x={960} y={670} books f={99}/>} {a==='clock'&&<Panel title="훈련 시작" lines={['16:26경']}/>} {a==='date'&&<Panel title="사건 날짜" lines={['2024-05-23']}/>} {a==='establish'&&<Panel title="육군 12사단 신병교육대" lines={['강원 인제']}/>} {a==='order'&&officer(1320,'중대장',true)}{a==='race'&&officer(1710,'중대장',true)}{doc()}{a==='march'&&s.narrationId==='N012'&&<Panel x={960} y={335} title="연병장 걷기" lines={['두 바퀴']}/>} {a==='run'&&<Panel x={960} y={335} title="완전군장 뜀걸음" lines={['세 바퀴']}/>}</>;
  }
  if(loc==='command')return <>{officer(540,'부중대장')}{officer(1290,'중대장',true)}<Desk x={940} y={825} w={400}/>{doc(960,440)}</>;
  if(loc==='barracks')return <>{recruits('rest',false)}{officer(1730,'간부',true)}<Panel x={960} y={305} title="경찰 수사결과" lines={['취침점호 뒤 대화 · 적발']}/></>;
  if(loc==='packing')return <>
   {recruits('rest',false)}
   <Pack x={960} y={730} f={a==='books'?f-s.start:99} books={a==='books'||a==='pack'||a==='contrast'}/>
   <g stroke={ink} strokeWidth={7}><path d="M1320 430h370v350h-370Z" fill="#718d80"/><path d="M1320 550h370M1320 670h370"/></g>
   {a==='six'&&<Panel x={960} y={250} title="군기훈련 대상" lines={['훈련병 6명']}/>}
   {a==='contrast'&&<g transform="translate(1310 630)" stroke={ink} strokeWidth={5}><rect x={-80} y={-90} width={160} height={210} fill="#eee4c9"/>{[0,1,2].map(j=><g key={j}><rect x={-54} y={-50+j*47} width={23} height={23} fill="none"/><path d={`M-17 ${-38+j*47}H54`}/></g>)}</g>}
   {a==='incomplete'&&<Txt x={960} y={410} size={34}>보급품 미수령</Txt>}
  </>;
  if(/infirmary|sokcho|gangneung|icu/.test(loc)){
   const moving=a==='arrival',dx=moving?Math.min(190,Math.max(0,local)*2.2):0;
   return <>
    {moving&&(loc==='gangneung'?<g stroke={ink} strokeWidth={7}>
     <path d="M90 225H1830V820H90Z" fill="#88a8bd"/><path d="M130 260H560V790H130ZM1360 260H1790V790H1360Z" fill="#456d88"/>
     {[0,1,2].map(j=><g key={j}><path d={`M170 ${305+j*125}h350v85H170ZM1400 ${305+j*125}h350v85H1400Z`} fill="#b8d3df"/><path d={`M340 ${305+j*125}v85M1570 ${305+j*125}v85`} fill="none" stroke="#6b8ca1"/></g>)}
     <path d="M610 380H1310V820H610Z" fill="#bed3dd"/><path d="M720 465H1200V820H720Z" fill="#365466"/><path d="M960 465V820M650 420H1270" fill="none" stroke="#e2e5d9" strokeWidth={11}/>
     <Txt x={960} y={315} size={49} color={ink}>강릉아산병원</Txt>
    </g>:<g stroke={ink} strokeWidth={7}><path d="M120 220H1800V800H120Z" fill="#accabc"/><path d="M700 380h500v420H700Z" fill="#3d6770"/><path d="M940 380v420" fill="none" stroke="#a7c7bc"/><Txt x={960} y={315} size={48} color={ink}>{heading}</Txt></g>)}

    <g transform={`translate(${dx} 0)`}><Bed x={860} y={735} f={pf} transport={moving}/><Medic x={540} y={855} f={a==='loss'?0:pf} s={1.02} reach={a!=='loss'} /><Medic x={1240} y={855} f={a==='loss'?0:pf} s={1.02} reach={a!=='loss'} flip/></g>
    {a==='arrival_time'&&<Panel x={960} y={345} title="강릉아산병원 도착" lines={['21:40경']}/>}
    {a==='loss'&&<Panel x={960} y={345} title="쓰러진 이틀 뒤 사망" lines={['2024-05-25']}/>}
    {doc(960,340)}
   </>;
  }
  if(loc==='family')return <><Puppet role="employee" x={620} y={900} scale={1.1} f={0} view="back" gesture="think" anonymous still take={0}/><Desk x={1050} y={810} w={520}/><g transform="translate(1120 690) rotate(-8)" stroke={ink} strokeWidth={6}><rect x={-120} y={-120} width={240} height={210} fill="#f2e6c9"/><path d="M-80-65H80M-80-25H80M-80 15H60" stroke="#81918a" strokeWidth={7}/></g><path d="M720 650q20-80 58-7l-10 110q-40 20-48-103Z" fill="#26394a" stroke={ink} strokeWidth={7}/>{doc(1100,365)}</>;
  if(loc==='prosecution')return <><Puppet role="lawyer" x={470} y={890} scale={1.05} f={pf} gesture="read" expr="thinking" take={0}/><Desk x={1000} y={800} w={700}/>{doc(1030,450)}</>;
  if(loc==='record')return <><Puppet role="detective" x={470} y={895} scale={1} f={pf} gesture="read" expr="sad" take={0}/>{doc(1040,490)}</>;
  if(loc==='policy')return <><Puppet role="clerk" x={440} y={885} scale={1} f={pf} gesture="point" expr="resolve" take={0}/><Recruit x={1530} y={875} f={0} s={.92} action="rest" pack={false}/>{doc(1000,480)}{/summer/.test(a)&&<g transform="translate(1000 740)" stroke={ink} strokeWidth={4}><rect x={-110} y={-53} width={220} height={100} fill="#e0d2b8"/>{[0,1,2,3].map(j=><path key={j} d={`M${-75+j*50} -53v100`}/>)}<path d="M-110-12H110M-110 20H110"/></g>}{a==='health'&&<Cross x={1000} y={725}/>} {a==='weather'||a==='measure'?<g stroke={ink} strokeWidth={6}><path d="M974 660v86a38 38 0 1 0 52 0v-86Z" fill="#d2ebe1"/><path d="M1000 680v92" stroke="#db765a" strokeWidth={12}/></g>:null}{a==='emergency_plan'&&<g><rect x={920} y={670} width={160} height={100} rx={15} fill="#d7e6d8" stroke={ink} strokeWidth={7}/><Cross x={1000} y={720} s={.55}/></g>}</>;
  if(loc==='entrance_memory')return <>
   <Puppet role="employee" x={670} y={885} scale={.96} f={0} view="back" gesture="hold" anonymous still/><Puppet role="clerk" x={1190} y={885} scale={.96} f={0} view="back" gesture="hold" anonymous still/>
   <Recruit x={950} y={875} f={0} s={.93} action="rest" pack={false}/><path d={`M905 660Q${805} ${620+Math.sin(local*.05)*7} 765 650M996 690L1125 730`} stroke={ink} strokeWidth={24} fill="none" strokeLinecap="round"/>
  </>;
  if(/memorial|yongsan/.test(loc))return <>
   {loc==='yongsan'&&<g stroke={ink} strokeWidth={6}><rect x={780} y={400} width={420} height={335} fill="#34414c"/><path d="M870 460L1000 590L1080 500M930 440L1070 580" fill="none" stroke="#aaaeb0" strokeWidth={22}/><Txt x={990} y={685} size={32}>추모</Txt></g>}
   {a==='empty'&&<g stroke={ink} strokeWidth={7}><path d="M540 600h180v140H540ZM530 755h200M555 756v119M705 756v119" fill="#b2bdaf"/></g>}
   <Puppet role="employee" x={400} y={900} scale={.94} f={0} view="back" gesture="hold" anonymous still hideRightArm={a==='flowers'} lean={0} take={0}/><Puppet role="clerk" x={1530} y={900} scale={.94} f={0} view="back" gesture="hold" anonymous still lean={0} take={0}/>
   {loc==='memorial'&&f<first('N074')&&flower(470,740,2)}
   {a==='flowers'&&(()=>{const placed=smooth(local/35),reach=placed*(1-smooth((local-55)/25)),handX=461+reach*190;return <g><path d={`M445 650Q490 710 ${handX} 770`} fill="none" stroke={ink} strokeWidth={31} strokeLinecap="round"/><path d={`M445 650Q490 710 ${handX} 770`} fill="none" stroke="#56e4c1" strokeWidth={20} strokeLinecap="round"/><ellipse cx={handX} cy={770} rx={16} ry={17} fill="#444354" stroke={ink} strokeWidth={5}/>{flower(470+placed*190,740,2)}</g>})()}

   {a==='mourners'||a==='bow'?<Puppet role="lawyer" x={1280} y={930} scale={.84} f={0} view="profile" flip anonymous still lean={3} take={0}/>:null}
   {a==='guilty'?doc(980,390):a==='mother_letter'?doc(980,390):a==='certificate'?<Panel x={980} y={420} {...DocumentLines.certificate}/>:null}
  </>;
  return doc();
 };
 return <g data-shot={s.id} data-location={loc} data-size={s.size} data-focus={`${focus.x},${focus.y},${z}`}>
  <Backdrop kind={kind} f={0}/>
  <g transform={`translate(960 540) scale(${z}) translate(${-focus.x} ${-focus.y})`}><Backdrop kind={kind} f={0}/>{world()}</g>
  <path d="M0 0H1920V100H0ZM0 935H1920V1080H0Z" fill={ink}/>
  <Txt x={70} y={65} anchor="start" size={30}>{heading}{stamp?'  |  '+stamp:''}</Txt>
  <Txt x={1850} y={65} anchor="end" size={23} color="#c1c8be">{loc==='ground_testimony'?'법정 증언 재구성':'보도 내용의 개념적 재구성 · 인물 비식별'}</Txt>
 </g>;
};
