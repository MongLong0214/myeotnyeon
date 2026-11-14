// Look-dev sets: the same flat ink style as Kit/CourtDynamic sets, split into depth planes for parallax.
//   *Out  = what is seen through windows (depth ~.3)       *Wall = back wall plane with props (depth ~.9)
//   *Near = out-of-focus foreground at the frame edges (depth ~1.35). Floors live on the wall plane.
// Coordinates match the original sets (court floor y1040, alley 1180, home 1240, cell 1260). Overscan ±160 px.
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {S,INK,PAPER,GOLD} from '../Kit';
import {BlurSvg} from './BLook';
type P=[number,number];
const T:React.FC<{x:number;y:number;s:number;fill?:string;children:string;anchor?:'middle'|'start'|'end';font?:string;rot?:number}>=({x,y,s,fill=INK,children,anchor='middle',font='Quiet Sans',rot=0})=>
 <text x={x} y={y} fontSize={s} fill={fill} stroke="none" fontFamily={font} fontWeight={800} textAnchor={anchor} transform={rot?`rotate(${rot} ${x} ${y})`:undefined}>{children}</text>;
const box=(x:number,y:number,w:number,h:number)=>`M${x} ${y}h${w}v${h}h${-w}Z`;
const SVG:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style})=><BlurSvg style={style} svgProps={S as any}>{children}</BlurSvg>;

// ================= COURT (day, cool daylight from the tall windows on the left) =================
export const CourtOut:React.FC=()=><SVG>
 <defs><linearGradient id="co-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#CFE3F2"/><stop offset="1" stopColor="#EEF4F2"/></linearGradient></defs>
 <path d="M-200 -100H1280V1100H-200Z" fill="url(#co-sky)" stroke="none"/>
 <path d="M-200 520Q-60 430 60 500Q150 400 260 480Q330 430 400 520V1100H-200Z" fill="#A9C3B8" strokeWidth={6}/>
 <path d="M700 300H1000V1100H700Z" fill="#C4CCD4" strokeWidth={6}/>{[360,460,560,660].map(y=><path key={y} d={`M730 ${y}h240`} stroke="#A9B3BD" strokeWidth={8}/>)}
 <path d="M-200 640Q-80 560 40 620Q130 560 240 640V1100H-200Z" fill="#8FAE9E" strokeWidth={6}/>
</SVG>;
const courtWin=(x:number)=>box(x,130,150,640);
export const CourtWall:React.FC<{t?:number}>=({t=0})=>{const f=useCurrentFrame();return <SVG>
 {/* wall with window holes (even-odd) */}
 <path d={`M-200 -100H1280V1040H-200Z ${courtWin(105)} ${courtWin(825)}`} fill="#D7CCB3" fillRule="evenodd" stroke="none"/>
 {/* window frames, mullions, half-down blinds */}
 {[105,825].map(x=><g key={x}>
  <path d={courtWin(x)} fill="none" strokeWidth={10}/><path d={`M${x+75} 130V770M${x} 450H${x+150}`} strokeWidth={7}/>
  <path d={box(x,130,150,170)} fill="#EFE8D6" strokeWidth={6}/>{[155,180,205,230,255,280].map(y=><path key={y} d={`M${x+6} ${y}H${x+144}`} stroke="#CFC4AA" strokeWidth={5}/>)}
  <path d={box(x-14,770,178,22)} fill="#C9B691" strokeWidth={6}/>
 </g>)}
 {/* pilasters (original positions) */}
 {[70,280,800,1010].map(x=><g key={x}><path d={`M${x-33} -100V1060H${x+33}V-100`} fill="#EDE2C9" strokeWidth={5}/><path d={`M${x-50} 1010H${x+50}V1060H${x-50}Z`} fill="#AE8F69" strokeWidth={5}/><path d={`M${x-20} 40V990`} stroke="#DCCFB2" strokeWidth={6}/></g>)}
 {/* centre: wood panelling, emblem, room plaque */}
 <path d="M318 120H762V1040H318Z" fill="#B48C62" strokeWidth={7}/>{[392,466,540,614,688].map(x=><path key={x} d={`M${x} 140V1030`} stroke="#9C7651" strokeWidth={6}/>)}
 <path d="M318 120H762V160H318Z" fill="#8E6A47" strokeWidth={6}/>
 <g transform="translate(540 330)"><circle r={92} fill="#E8C66A" strokeWidth={8}/><circle r={72} fill="none" stroke="#B9953E" strokeWidth={6}/>
  <path d="M0 -50V44M-40 44H40M-52 -26H52" fill="none" strokeWidth={7}/><path d="M-52 -26L-68 10H-36ZM52 -26L36 10H68Z" fill="#F5E2A6" strokeWidth={5}/></g>
 <path d="M410 470H670V540H410Z" fill="#2F2A2C" strokeWidth={6}/><T x={540} y={518} s={40} fill="#F0D488">제417호 법정</T>
 {/* wall clock, ticking */}
 <g transform="translate(540 640)"><circle r={50} fill={PAPER} strokeWidth={7}/>{Array.from({length:12}).map((_,i)=><path key={i} d={`M0 -40V-33`} transform={`rotate(${i*30})`} strokeWidth={4}/>)}
  <path d="M0 0V-26" strokeWidth={6} transform="rotate(-60)"/><path d="M0 0V-36" strokeWidth={5} transform="rotate(64)"/><path d="M0 6V-38" stroke="#C8372D" strokeWidth={3} transform={`rotate(${Math.floor(f/30)*6})`}/></g>
 {/* notice on the right pilaster gap */}
 <g transform="translate(905 860) rotate(1.5)"><path d={box(-62,-70,124,140)} fill={PAPER} strokeWidth={5}/><T x={0} y={-30} s={30}>정숙</T>{[-2,18,38].map(y=><path key={y} d={`M-42 ${y}H42`} stroke="#B4A58C" strokeWidth={5}/>)}</g>
 {/* floor: planks + window light patches */}
 <path d="M-200 1040H1280V2100H-200Z" fill="#A98B6A" stroke="none"/>
 {[0,180,360,540,720,900,1080].map(x=><path key={x} d={`M540 1040L${x*2-540} 1960`} stroke="#886C53" strokeWidth={4}/>)}
 {[1110,1210,1340,1520,1760].map(y=><path key={y} d={`M-200 ${y}H1280`} stroke="#977A5C" strokeWidth={3}/>)}
 <path d="M150 1060L330 1060L560 1300L300 1300Z" fill="#D9C29A" stroke="none" opacity={.6}/>
 <path d="M860 1060L1020 1060L1250 1300L1010 1300Z" fill="#D9C29A" stroke="none" opacity={.5}/>
 <path d="M-200 1040H1280" strokeWidth={9}/>
</SVG>;};
// Judges' dais behind the actors (same plane as the wall)
export const CourtDais:React.FC=()=><SVG>
 <path d="M300 880H780V1040H300Z" fill="#8A6040" strokeWidth={8}/><path d="M290 868H790V896H290Z" fill="#C59C6B" strokeWidth={7}/>
 {[380,540,700].map(x=><path key={x} d={`M${x} 910V1030`} stroke="#6E4A31" strokeWidth={8}/>)}
 <g transform="translate(540 940)"><path d={box(-70,-24,140,44)} fill="#2F2A2C" strokeWidth={5}/><T x={0} y={11} s={30} fill="#F0D488">재판장</T></g>
 <path d="M420 868L428 820M428 820Q440 800 452 812" fill="none" strokeWidth={6}/><circle cx={455} cy={814} r={9} fill="#3A3A40" strokeWidth={4}/>
 <path d="M630 868V826H690V868Z" fill="#E9E2D2" strokeWidth={5}/><path d="M636 838H684M636 850H676" stroke="#B4A58C" strokeWidth={4}/><path d="M640 826V814H680V826" fill="#F4EEDF" strokeWidth={5}/>
 <path d="M330 868V842H372V868Z" fill="#9FC2D6" strokeWidth={5}/><path d="M340 842V834H362V842" fill="#5C83A6" strokeWidth={4}/>
</SVG>;
// The prosecutor's desk rail with readable papers (actor plane)
export const CourtRailPlus:React.FC<{y:number;papers?:boolean}>=({y,papers=true})=><SVG>
 <path d={`M-200 ${y}H1280V${y+40}H-200Z`} fill="#C5A06F"/><path d={`M-200 ${y+40}H1280V2100H-200Z`} fill="#80573F"/>
 {[90,330,570,810,1050].map(x=><path key={x} d={`M${x} ${y+60}V2000`} stroke="#684630" strokeWidth={14}/>)}
 <path d={`M-200 ${y+44}H1280`} stroke="#5E3F2B" strokeWidth={6}/>
 {papers&&<><g transform={`translate(250 ${y-10}) rotate(-4)`}><path d={box(-150,-20,300,40)} fill={PAPER} strokeWidth={6}/><path d={box(-140,-28,300,40)} fill="#F4ECD6" strokeWidth={5}/><T x={10} y={0} s={24}>공소장 · 사건 2023고합</T></g>
 <g transform={`translate(770 ${y-14}) rotate(3)`}><path d={box(-90,-26,180,44)} fill="#3C5C86" strokeWidth={6}/><path d={box(-80,-34,160,12)} fill="#F4ECD6" strokeWidth={4}/><T x={0} y={6} s={22} fill={PAPER}>증거기록 3권</T></g></>}
 <g transform={`translate(560 ${y-6})`}><path d="M-22 0V-58H22V0Z" fill="rgba(200,230,245,.55)" strokeWidth={5}/><path d="M-18 -26H18" stroke="#9FC9DE" strokeWidth={10}/></g>
</SVG>;
export const CourtNear:React.FC=()=><SVG>
 {/* out-of-focus microphone gooseneck at the right edge */}
 <path d="M1110 1960L1040 1500Q1020 1380 960 1330" fill="none" stroke={INK} strokeWidth={34}/><path d="M1110 1960L1040 1500Q1020 1380 960 1330" fill="none" stroke="#4A4A52" strokeWidth={20}/>
 <path d="M930 1300L990 1350L970 1372L912 1322Z" fill="#2D2D33" strokeWidth={8}/>
</SVG>;

// ================= ALLEY / STREET near the station (day) =================
export const AlleyOut:React.FC<{night?:boolean}>=({night=false})=><SVG>
 <defs><linearGradient id={`ao-${night}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={night?'#141A38':'#BFDBF0'}/><stop offset="1" stopColor={night?'#3A2C4A':'#F4EEDC'}/></linearGradient></defs>
 <path d="M-200 -100H1280V500H-200Z" fill={`url(#ao-${night})`} stroke="none"/>
 <path d="M-200 200H60V60H220V150H340V20H520V160H700V80H880V180H1040V40H1280V500H-200Z" fill={night?'#2A2C48':'#B9C1C8'} strokeWidth={6}/>
 {[[90,90],[250,180],[380,60],[560,190],[740,110],[920,210],[1080,80]].map(([x,y],i)=><g key={i}>{[0,1,2].map(j=><path key={j} d={box(x+j*36,y+10,22,18)} fill={night?(i+j)%3?'#FFC66A':'#3A3C58':'#D8E2EA'} strokeWidth={3}/>)}</g>)}
</SVG>;
const shop=(x:number,name:string,awn:[string,string],deco:'food'|'pharm'|'phone')=><g key={x}>
 <path d={box(x,160,360,1020)} fill={x%720?'#D6CCB4':'#CFC3A8'}/>
 {/* upper floor: windows with an AC unit and a pipe */}
 <path d={box(x+40,40,120,100)} fill="#9FB5BE" strokeWidth={6}/><path d={box(x+200,40,120,100)} fill="#9FB5BE" strokeWidth={6}/>
 <path d={box(x+210,150,90,56)} fill="#E7E5DD" strokeWidth={5}/>{[164,176,188].map(y=><path key={y} d={`M${x+222} ${y}h66`} stroke="#B8B6AE" strokeWidth={4}/>)}
 <path d={`M${x+340} 40V1180`} stroke="#8F8A7E" strokeWidth={8}/>
 {/* sign board */}
 <path d={box(x+30,220,300,110)} fill="#F3EEDD" strokeWidth={7}/><path d={box(x+42,232,276,86)} fill="none" stroke={awn[0]} strokeWidth={6}/>
 <T x={x+180} y={298} s={name.length>4?50:60}>{name}</T>
 {/* striped scalloped awning */}
 <path d={`M${x+16} 400H${x+344}L${x+330} 500H${x+30}Z`} fill={awn[0]} strokeWidth={7}/>
 {[0,1,2,3,4,5].map(i=><path key={i} d={`M${x+30+i*50} 400h25l-2 100h-25Z`} fill={awn[1]} stroke="none"/>)}
 <path d={`M${x+30} 500`+[0,1,2,3,4,5].map(i=>`q25 30 50 0`).join('')} fill={awn[0]} strokeWidth={6}/>
 {/* shop window */}
 <path d={box(x+50,560,260,500)} fill="#A9C0C8"/><path d={`M${x+180} 560V1060`} strokeWidth={6}/>
 <path d={`M${x+60} 580L${x+150} 580L${x+90} 700L${x+60} 700Z`} fill="#E7F1F3" stroke="none" opacity={.6}/>
 {deco==='food'&&<g><path d={box(x+70,620,94,130)} fill={PAPER} strokeWidth={5}/><T x={x+117} y={660} s={24}>떡볶이</T><T x={x+117} y={696} s={22} fill="#C8372D">4,000</T><T x={x+117} y={732} s={22}>순대</T>
  <path d={box(x+196,860,98,60)} fill="#E36D4A" strokeWidth={5}/><path d={`M${x+196} 878h98`} stroke="#B84E32" strokeWidth={5}/></g>}
 {deco==='pharm'&&<g><path d={box(x+70,600,90,90)} fill="#3E9E6A" strokeWidth={5}/><T x={x+115} y={662} s={52} fill={PAPER}>약</T>
  {[0,1,2].map(i=><path key={i} d={`M${x+196} ${640+i*70}H${x+296}`} stroke="#E8E4D6" strokeWidth={12}/>)}{[0,1,2,3].map(i=><path key={i} d={box(x+200+i*24,600,16,32)} fill={['#F0B84A','#E36D4A','#7DB7D9','#F3EEDD'][i]} strokeWidth={3}/>)}</g>}
 {deco==='phone'&&<g><path d={box(x+66,600,100,160)} fill="#FFE27A" strokeWidth={5}/><T x={x+116} y={650} s={30} fill="#C8372D">할인</T><T x={x+116} y={690} s={22}>최신폰</T><T x={x+116} y={724} s={22}>공짜</T>
  {[0,1].map(i=><path key={i} d={box(x+206+i*50,640,36,64)} rx={6} fill="#2E3440" strokeWidth={4}/>)}</g>}
 <path d={box(x+50,560,260,500)} fill="none" strokeWidth={8}/>
 <path d={`M${x+40} 1060H${x+320}V1180H${x+40}Z`} fill="#BDB29A" strokeWidth={6}/>
</g>;
export const AlleyWall:React.FC<{night?:boolean}>=({night=false})=><SVG>
 <path d={`M-200 400H1280V1180H-200Z`} fill="#D6CCB4" stroke="none"/>
 <path d={box(-200,160,200,1020)} fill="#CBBEA2" strokeWidth={6}/><path d={box(1080,160,200,1020)} fill="#CBBEA2" strokeWidth={6}/>
 {shop(0,'골목분식',['#C98B5A','#E8C49A'],'food')}{shop(360,'새봄약국',['#4E8FAE','#9CCBE0'],'pharm')}{shop(720,'모두폰',['#9DAE4E','#D3DE9C'],'phone')}
 {/* wires and a pole across the top */}
 <path d="M-200 30Q300 110 1280 20M-200 60Q400 150 1280 70" fill="none" stroke={INK} strokeWidth={4}/>
 {/* clutter on the pavement line */}
 <g transform="translate(330 1180)"><path d="M-40 0L-30 -110H30L40 0Z" fill="#F3EEDD" strokeWidth={6}/><T x={0} y={-66} s={22}>오늘의</T><T x={0} y={-38} s={22} fill="#C8372D">메뉴</T></g>
 <g transform="translate(700 1180)">{[0,1].map(i=><path key={i} d={box(-50+i*8,-60-i*56,100,56)} fill="#3C7FB0" strokeWidth={6}/>)}<path d="M-38 -40H38M-30 -96H46" stroke="#2C628A" strokeWidth={5}/></g>
 <g transform="translate(1040 1180)"><path d="M-46 0Q-60 -60 -20 -78Q10 -96 40 -70Q62 -40 46 0Z" fill="#2E3138" strokeWidth={6}/><path d="M-10 -78L0 -96L12 -80" fill="none" strokeWidth={5}/></g>
 <g transform="translate(150 1180)"><path d="M-30 0L-24 -50H24L30 0Z" fill="#B0603C" strokeWidth={6}/><path d="M0 -50Q-40 -110 -10 -150Q10 -110 0 -50Q30 -120 50 -100Q30 -70 0 -50" fill="#5E9A4E" strokeWidth={5}/></g>
 <g transform="translate(560 1100)"><path d={box(-80,-70,160,60)} fill={PAPER} strokeWidth={5}/><T x={0} y={-30} s={26}>임대 문의</T></g>
 {/* sun: the building opposite throws a diagonal shadow over the lower fronts */}
 <path d="M-200 820L1280 1080V1180H-200Z" fill={night?'#000':'#4C3F78'} stroke="none" opacity={.16}/>
 {/* pavement */}
 <path d="M-200 1180H1280V2100H-200Z" fill="#A7A293" stroke="none"/>
 {[1250,1340,1460,1620,1830].map(y=><path key={y} d={`M-200 ${y}H1280`} stroke="#928D7F" strokeWidth={4}/>)}
 {[-120,60,240,420,600,780,960,1140].map(x=><path key={x} d={`M${540+(x-540)*.55} 1180L${540+(x-540)*2.4} 2000`} stroke="#928D7F" strokeWidth={4}/>)}
 <path d="M-200 1180H1280" strokeWidth={10}/>
</SVG>;
export const AlleyNear:React.FC=()=><SVG>
 {/* lamp post at the left edge and a bollard at the right: out of focus foreground */}
 <path d="M-40 -100H40V2100H-40Z" fill="#5F6B73" strokeWidth={12}/><path d="M10 -100V2100" stroke="#7F8C94" strokeWidth={10}/>
 <path d="M-30 760H60V840H-30Z" fill="#E9E2D2" strokeWidth={8}/><T x={15} y={812} s={26} rot={0}>3번</T>
 <path d="M980 1700Q980 1640 1030 1640Q1080 1640 1080 1700V2100H980Z" fill="#E6B33A" strokeWidth={12}/><path d="M980 1760H1080" stroke={INK} strokeWidth={22}/>
</SVG>;

// ================= HOME (apartment at night) =================
export const HomeOut:React.FC=()=>{const f=useCurrentFrame();return <SVG>
 <path d="M-200 -100H700V900H-200Z" fill="#1B2140" stroke="none"/>
 <circle cx={330} cy={380} r={40} fill="#F2EBCB" stroke="none"/><circle cx={330} cy={380} r={90} fill="#F2EBCB" stroke="none" opacity={.12}/>
 {[[-60,470,150],[100,520,120],[230,440,160],[380,500,140],[520,460,170]].map(([x,y,w],i)=><g key={i}><path d={box(x,y,w,500)} fill="#262C50" strokeWidth={5}/>
  {Array.from({length:12}).map((_,j)=><path key={j} d={box(x+14+(j%3)*(w/3-6),y+20+Math.floor(j/3)*40,w/3-22,20)} fill={(i*7+j*3)%5<2?'#FFCF7A':'#30375E'} stroke="none" opacity={(i+j+Math.floor(f/45))%11===0?.4:1}/>)}</g>)}
</SVG>;};
export const HomeWall:React.FC<{door?:number;dark?:boolean;spill?:number}>=({door=0,dark=true,spill=1})=>{const f=useCurrentFrame();return <SVG>
 <path d={`M-200 -100H1280V1240H-200Z ${box(60,300,360,380)}`} fill={dark?'#575566':'#CDBFA6'} fillRule="evenodd" stroke="none"/>
 {/* faint wallpaper stripes */}
 {Array.from({length:20}).map((_,i)=><path key={i} d={`M${-160+i*76} 0V1240`} stroke={dark?'#5E5C6E':'#D4C7AF'} strokeWidth={14}/>)}
 <path d={box(60,300,360,380)} fill="none" strokeWidth={9}/><path d="M60 490H420M240 300V680" strokeWidth={7}/>
 <path d="M30 680H450V706H30Z" fill="#B9AE9A" strokeWidth={6}/>
 {/* curtains */}
 <path d="M20 270Q40 480 30 720L90 720Q80 480 96 270Z" fill="#7F6A8E" strokeWidth={6}/><path d="M384 270Q400 480 390 720L450 720Q440 480 456 270Z" fill="#7F6A8E" strokeWidth={6}/>
 <path d="M10 262H470" strokeWidth={10}/>
 {/* family photo, calendar, clock, switch */}
 <g transform="translate(560 420) rotate(-2)"><path d={box(-60,-74,120,148)} fill="#2D2B33" strokeWidth={6}/><path d={box(-46,-60,92,120)} fill="#C9C3B4" strokeWidth={4}/><circle cx={-16} cy={-12} r={16} fill="#A79F8E" stroke="none"/><circle cx={18} cy={-8} r={14} fill="#A79F8E" stroke="none"/><path d="M-40 60Q-16 10 6 60Z M2 60Q22 16 42 60Z" fill="#A79F8E" stroke="none"/></g>
 <g transform="translate(560 640)"><path d={box(-62,-70,124,150)} fill={PAPER} strokeWidth={5}/><path d={box(-62,-70,124,40)} fill="#C8372D" strokeWidth={5}/><T x={0} y={-38} s={28} fill={PAPER}>11월</T>
  {Array.from({length:20}).map((_,i)=><path key={i} d={box(-52+(i%5)*22,-20+Math.floor(i/5)*22,14,12)} fill={i===13?'#C8372D':'#DCD3BE'} stroke="none"/>)}</g>
 <g transform="translate(540 180)"><circle r={46} fill={PAPER} strokeWidth={7}/><path d="M0 0V-24" strokeWidth={6} transform="rotate(-30)"/><path d="M0 0V-34" strokeWidth={5} transform={`rotate(${60+f*.2})`}/></g>
 <path d={box(640,700,30,46)} fill="#E9E2D2" strokeWidth={5}/>
 {/* door: frame, warm gap light, panel */}
 <path d="M680 370H1020V1240H680Z" fill="#6A5240" strokeWidth={9}/>
 <path d="M690 380H1010V1240H690Z" fill={door>.02?'#FFD58A':'#1E1D24'} stroke="none"/>
 {door>.02&&<path d="M690 380H1010V1240H690Z" fill="#FFB860" stroke="none" opacity={.4}/>}
 <path d={`M690 380H${1010-300*door}V1240H690Z`} fill="#8A6A4E" strokeWidth={6}/>
 <path d={`M${720-10*door} 430H${980-290*door}V760H${720-10*door}Z M${720-10*door} 820H${980-290*door}V1190H${720-10*door}Z`} fill="none" stroke="#715640" strokeWidth={7}/>
 {door<.5&&<g><circle cx={970-280*door} cy={820} r={14} fill={GOLD} strokeWidth={5}/><path d={`M${958-280*door} 834H${982-280*door}`} strokeWidth={5}/></g>}
 {/* floor: laminate + rug, warm wedge from the door gap */}
 <path d="M-200 1240H1280V2100H-200Z" fill={dark?'#4A4239':'#9C8366'} stroke="none"/>
 {[1340,1500,1720].map(y=><path key={y} d={`M-200 ${y}H1280`} stroke={dark?'#3E372F':'#866F55'} strokeWidth={5}/>)}
 {[-100,120,340,560,780,1000,1220].map(x=><path key={x} d={`M${540+(x-540)*.7} 1240L${540+(x-540)*2.2} 2000`} stroke={dark?'#41392F':'#8C755A'} strokeWidth={3}/>)}
 <path d="M110 1300H620L700 1520H40Z" fill={dark?'#5B3F46':'#B07A6A'} strokeWidth={7}/><path d="M140 1330H600L660 1490H80Z" fill="none" stroke={dark?'#6E4E56':'#C88C7A'} strokeWidth={6}/>
 {door>.02&&<path d={`M690 1240H${1010-300*door+20}L${1150} 1900H${520-100*door}Z`} fill="#FFC774" stroke="none" opacity={.38*spill}/>}
 <path d="M-200 1240H1280" strokeWidth={10}/>
 {/* slippers by the door */}
 <g transform="translate(600 1290)"><path d="M-40 0Q-44 -24 -14 -24Q8 -24 6 0Z M10 6Q6 -18 36 -18Q58 -18 56 6Z" fill="#8FB2C9" strokeWidth={5}/></g>
</SVG>;};

// ================= CELL (cold fluorescent + high window) =================
export const CellOut:React.FC=()=><SVG><path d="M300 0H780V420H300Z" fill="#C9DCE6" stroke="none"/><path d="M300 300Q420 250 540 300Q660 260 780 300V420H300Z" fill="#AFC4CF" stroke="none"/></SVG>;
export const CellWall:React.FC=()=>{const f=useCurrentFrame(),flick=f%97<2?.82:1;return <SVG>
 <path d={`M-200 -100H1280V1260H-200Z ${box(400,130,280,200)}`} fill="#6F7A82" fillRule="evenodd" stroke="none"/>
 {[200,340,480,620,760,900,1040,1180].map((y,i)=><g key={y}><path d={`M-200 ${y}H1280`} stroke="#66717A" strokeWidth={6}/>{Array.from({length:8}).map((_,j)=><path key={j} d={`M${-120+j*180+(i%2)*90} ${y}V${y-140}`} stroke="#68737C" strokeWidth={5}/>)}</g>)}
 {/* stains */}
 <path d="M120 700Q160 640 210 700Q260 780 200 860Q150 900 130 820Z" fill="#66707A" stroke="none" opacity={.7}/><path d="M860 520Q900 500 930 560Q950 640 900 650Q860 620 860 520Z" fill="#66707A" stroke="none" opacity={.6}/>
 {/* high window with bars */}
 <path d={box(400,130,280,200)} fill="none" strokeWidth={10}/>{[456,512,568,624].map(x=><path key={x} d={`M${x} 130V330`} stroke="#3F474D" strokeWidth={12}/>)}<path d="M388 330H692V352H388Z" fill="#59636B" strokeWidth={6}/>
 {/* rules notice */}
 <g transform="translate(160 470) rotate(-1.5)"><path d={box(-90,-110,180,220)} fill="#ECE6D2" strokeWidth={6}/><T x={0} y={-66} s={26}>수용자</T><T x={0} y={-36} s={26}>준수사항</T>{[0,24,48,72].map(y=><path key={y} d={`M-64 ${y}H${64-(y%48?20:0)}`} stroke="#9C9580" strokeWidth={5}/>)}</g>
 {/* shelf with cup and towel */}
 <path d="M800 760H1010V784H800Z" fill="#8C959C" strokeWidth={6}/><path d="M830 760V716H872V760Z" fill="#E9EEF0" strokeWidth={5}/><path d="M900 760V730H990V760Z" fill="#C9D7C4" strokeWidth={5}/><path d="M906 744H984" stroke="#A9B9A4" strokeWidth={4}/>
 {/* fluorescent tube in a cage */}
 <path d="M380 20H700V56H380Z" fill={`rgba(235,252,246,${flick})`} strokeWidth={7}/><path d="M380 38H700M440 20V56M540 20V56M640 20V56" stroke="#8C959C" strokeWidth={4}/>
 {/* floor */}
 <path d="M-200 1260H1280V2100H-200Z" fill="#4B535A" stroke="none"/>
 {[1360,1520,1760].map(y=><path key={y} d={`M-200 ${y}H1280`} stroke="#434A50" strokeWidth={5}/>)}
 <path d="M380 1270L700 1270L860 1720L260 1720Z" fill="#8FA9B2" stroke="none" opacity={.22}/>
 {/* folded mat and blanket on the floor at the right */}
 <path d="M820 1300H1180V1370H820Z" fill="#7C8C6E" strokeWidth={7}/><path d="M850 1250H1120V1302H850Z" fill="#9FA88A" strokeWidth={7}/><path d="M870 1276H1100" stroke="#87906F" strokeWidth={5}/>
 <path d="M-200 1260H1280" strokeWidth={9}/>
</SVG>;};
