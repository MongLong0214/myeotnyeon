import React from 'react';
import {C} from './Puppets_v3';
const outline={stroke:C.line,strokeWidth:7,strokeLinejoin:'round' as const};
export const PaperGrain:React.FC=()=><g fill={C.line} opacity={.055}>{Array.from({length:210},(_,i)=><circle key={i} cx={(i*173+19)%1920} cy={(i*97+43)%1080} r={i%3===0?2:1}/>)}</g>;
export const Clock:React.FC<{x:number;y:number;midnight?:boolean}>=({x,y,midnight=false})=><g transform={`translate(${x} ${y})`}><circle r={66} fill={C.paper} {...outline}/>{Array.from({length:12},(_,i)=><path key={i} d="M0 -52L0 -43" transform={`rotate(${i*30})`} stroke={C.line} strokeWidth={5}/>)}<path d={midnight?'M0 -34L0 0L0 -47':'M-29 -17L0 0L0 -47'} fill="none" stroke={C.line} strokeWidth={8} strokeLinecap="round"/><circle r={6} fill={C.line}/></g>;
export const Parking:React.FC<{f:number;alternate?:boolean}>=({f,alternate=false})=><>
 <rect width={1920} height={1080} fill={alternate?'#D4CFBF':'#D9E0D5'}/><path d="M0 0L1920 0L1920 145L0 201Z" fill="#B2C1B8" {...outline}/>
 <path d="M0 611L1920 611L1920 1080L0 1080Z" fill="#87968D" {...outline}/><path d="M0 665L1920 665" stroke="#5A6B62" strokeWidth={8}/>
 {[95,625,1155,1745].map((x,i)=><g key={x}><path d={`M${x} 165L${x+135} 152L${x+135} 681L${x} 681Z`} fill={i%2?'#C4CBB8':'#BCC8BB'} {...outline}/><path d={`M${x} 515L${x+135} 515L${x+135} 682L${x} 682Z`} fill={C.yellow} {...outline}/><path d={`M${x+8} 590L${x+65} 519M${x+73} 674L${x+128} 603`} stroke={C.line} strokeWidth={22}/></g>)}
 <path d="M0 235L1920 235M0 273L1920 273" stroke="#677C73" strokeWidth={12}/><path d="M252 273L252 357L435 357" fill="none" stroke="#677C73" strokeWidth={14}/>
 {[350,1020,1610].map(x=><g key={x}><path d={`M${x-90} 75L${x+110} 65L${x+105} 90L${x-90} 100Z`} fill={C.paper} {...outline}/><path d={`M${x-100} 107L${x+125} 94`} stroke={C.yellow} strokeWidth={9} opacity={.6}/></g>)}
 {[200,700,1220,1750].map(x=><path key={x} d={`M${x} 741L${x-260} 1080M${x+160} 741L${x-100} 1080`} stroke="#E2E4CE" strokeWidth={10} fill="none"/>)}
 <path d="M15 446Q530 431 1895 447" stroke="#C8D3C6" strokeWidth={6} fill="none"/><path d="M1554 277L1653 277L1653 591L1554 591Z" fill="#667E73" {...outline}/><path d="M1580 304L1628 304L1628 405L1580 405Z" fill="#B2C9B7" stroke={C.line} strokeWidth={5}/>
 <g opacity={.22} fill={C.paper} transform={`translate(${Math.sin(f/100)*9} 0)`}><path d="M210 114L470 114L686 595L-20 595Z"/><path d="M941 105L1111 105L1310 595L710 595Z"/></g><PaperGrain/>
</>;
export const Car:React.FC<{x:number;y:number;scale?:number;white?:boolean;van?:boolean;f:number}>=({x,y,scale=1,white=false,van=false,f})=><g transform={`translate(${x} ${y}) scale(${scale})`} {...outline}>
 <ellipse cx={0} cy={30} rx={330} ry={34} fill={C.ink} opacity={.18} stroke="none"/>
 <path d={van?'M-300 0L-300 -256L101 -256L171 -161L278 -151L300 -114L300 0Z':'M-300 0L-300 -88Q-298 -120 -224 -128L-128 -215Q-79 -237 111 -219L198 -127L277 -112L300 -77L300 0Z'} fill={van?'#E4DCC3':white?'#EEEDE5':'#292D35'} strokeWidth={9}/>
 {van?<><path d="M112 -237L167 -157L265 -147L267 -83L111 -83Z" fill="#8FAEAE"/><path d="M-267 -224L74 -224L74 -20L-267 -20Z" fill="#789C91"/><path d="M-97 -223L-97 -22M-115 -104L-110 -104M-78 -104L-73 -104" stroke={C.line} strokeWidth={8}/><path d="M-247 -207L-119 -207L-119 -40L-247 -40Z" fill="#A8BCAF" strokeWidth={4}/></>:<><path d="M-198 -132L-108 -204L-22 -205L-22 -132Z" fill="#7F999B"/><path d="M0 -205L98 -200L166 -132L0 -132Z" fill="#7F999B"/><path d="M-5 -120L-5 -16M-130 -90L-96 -90M65 -90L96 -90" stroke={C.line} strokeWidth={5}/></>}
 <path d="M270 -93L300 -86L300 -60L270 -60Z" fill={C.paper}/><path d="M-300 -91L-270 -91L-270 -59L-300 -59Z" fill="#9C6253"/>
 {[-200,200].map(wx=><g key={wx} transform={`translate(${wx} 4)`}><circle r={55} fill="#242630" strokeWidth={9}/><circle r={29} fill="#AFB7AE" strokeWidth={5}/><g transform={`rotate(${f*2})`} strokeWidth={4}><path d="M-19 0L19 0M0 -19L0 19"/></g></g>)}
 <path d="M-270 -13L260 -13" fill="none" stroke={white?'#BEC3BA':van?'#BFBAA4':'#535860'} strokeWidth={10}/>
</g>;
export const Investigation:React.FC<{f:number}>=({f})=><>
 <rect width={1920} height={1080} fill="#E5DCC7"/><rect y={675} width={1920} height={405} fill="#ABA58E" {...outline}/><path d="M0 152L1920 152M0 680L1920 680" stroke="#C7BCA3" strokeWidth={11}/>
 <rect x={938} y={228} width={754} height={397} rx={9} fill="#8A9B8B" {...outline}/><rect x={962} y={250} width={705} height={349} fill="#BDCAAD" stroke="#4A6257" strokeWidth={5}/>
 {[[1010,300],[1250,280],[1470,345]].map(([x,y],i)=><g key={x} transform={`translate(${x} ${y}) rotate(${i*7-5})`}><path d="M0 0L131 0L131 181L0 181Z" fill={C.paper} {...outline}/><circle cx={65} cy={54} r={25} fill="#6F7C71" stroke={C.line} strokeWidth={4}/><path d="M29 128L35 98Q65 73 96 99L103 128Z" fill="#6F7C71" stroke={C.line} strokeWidth={4}/><path d="M24 147L105 147M24 163L83 163" stroke="#B7BDAD" strokeWidth={6}/></g>)}
 <path d="M1080 330L1320 310L1535 375L1080 330" fill="none" stroke="#BE9667" strokeWidth={5}/><Clock x={770} y={330} midnight/>
 <rect x={82} y={260} width={270} height={420} rx={7} fill="#82928A" {...outline}/>{[285,405,525].map(y=><g key={y}><rect x={104} y={y} width={225} height={102} fill="#A8B3A5" {...outline}/><path d={`M190 ${y+46}L240 ${y+46}`} stroke={C.line} strokeWidth={9}/></g>)}<PaperGrain/>
</>;
export const Desk:React.FC<{f:number}>=({f})=><g {...outline}><path d="M695 756L1742 756L1787 806L664 806Z" fill="#B58757"/><path d="M698 808L1737 808L1725 963L718 963Z" fill="#91643F"/><path d="M750 828L750 941M1689 828L1689 941" stroke="#704C31" strokeWidth={11}/><path d="M1380 747L1405 658L1495 641L1572 688" fill="none" stroke={C.line} strokeWidth={18}/><path d="M1518 666Q1580 636 1620 708L1510 741Z" fill={C.teal}/><path d={`M1510 747L1620 721L1710 ${790+Math.sin(f/40)*6}L1375 790Z`} fill={C.yellow} opacity={.13} stroke="none"/><path d="M1035 740L1048 714L1280 714L1302 740Z" fill="#A09276"/><path d="M1024 749L1043 732L1301 732L1316 749Z" fill={C.paper}/></g>;
export const Court:React.FC<{f:number}>=({f})=><>
 <rect width={1920} height={1080} fill="#B08C5F"/>{Array.from({length:31},(_,i)=><rect key={i} x={i*66} width={52} height={760} fill={i%2?'#775236':'#8D6441'} stroke={C.line} strokeWidth={4}/>)}<path d="M0 119L1920 119M0 690L1920 690" stroke="#BD9565" strokeWidth={24}/>
 <path d="M0 760L1920 760L1920 1080L0 1080Z" fill="#99816A" {...outline}/><rect x={718} y={204} width={484} height={455} rx={38} fill="#4C433A" {...outline}/><rect x={743} y={227} width={435} height={409} rx={25} fill="#6B5E4C" stroke="#88765D" strokeWidth={6}/>
 {/* Abstract joinery only: no state emblem, insignia, caption panel or real court seal. */}<path d="M415 324L497 324L497 680M1505 324L1423 324L1423 680" stroke="#BB966B" strokeWidth={8} fill="none"/><PaperGrain/>
</>;
export const Bench:React.FC=()=><g {...outline}><path d="M522 735L1398 735L1423 779L497 779Z" fill="#BE9161"/><path d="M516 779L1404 779L1404 959L516 959Z" fill="#91643F"/>{[568,858,1148].map(x=><path key={x} d={`M${x} 812L${x+235} 812L${x+235} 931L${x} 931Z`} fill="#805534" strokeWidth={5}/>)}<path d="M550 750L692 750M1198 750L1340 750" stroke={C.paper} strokeWidth={9}/></g>;
