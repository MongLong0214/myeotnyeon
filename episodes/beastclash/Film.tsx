// Beast Clash Shorts, engine v2 (2026-11-14). Same case.json contract as v1 (build.py from specs/<id>.json):
// face-off (frame 0, both animals already mid-charge) -> 3 stat reveals in the habitat (count-up + bars, animals react)
// -> "Who wins? A or B" -> clash (charge, rear, strike/dodge, impact, counter, finisher) -> verdict -> loop.
// Characters: Rig.tsx. Habitats: 3 parallax layers + foreground + weather. Impact frames last 4 frames and are
// >= 20 frames apart (flash screening: fewer than 3 flash pairs in any second). Previous engine: Film_v5keep.tsx.bak.
import React from 'react';
import {AbsoluteFill,continueRender,delayRender,staticFile,useCurrentFrame,spring} from 'remotion';
import {pose,Kind,P,INK,PAPER,GOLD,RED,TEAL} from './Beasts';
import {Animal,GEO,headPos,PX} from './Rig';
import CH from './choreo.json';

const loading=typeof document==='undefined'?null:delayRender('fonts');
if(loading!==null)Promise.all([['Lilita','LilitaOne-Regular.ttf'],['Quiet Sans','Pretendard-ExtraBold.woff2']].map(async([fam,file])=>{const f=await new FontFace(fam,`url(${staticFile('fonts/'+file)})`).load();document.fonts.add(f);})).then(()=>continueRender(loading));

type Side='a'|'b';type Pt=[number,number];
type Shot={s:string;who?:Side;tank?:boolean;pin?:boolean};
type Line={id:string;mode:string;k?:number;shots?:Shot[];from:number;dur:number;onset:number;offset:number;shown:string|null};
type Stat={label:string;a?:{big:string;small:string};b?:{big:string;small:string};win:Side;note?:string};
type Bg='ice'|'jungle'|'scrub'|'ocean'|'savanna'|'river';
export type Case={id:string;a:Kind;b:Kind;winner:Side;bg:Bg;title:[string,string];tag?:[string,string];stats:Stat[];verdict:{head:string;name:string;note:string;note2?:string;pop1?:string;pop2?:string};lines:Line[];subs:{s:number;e:number;text:string}[];n:number};

const clamp01=(u:number)=>Math.max(0,Math.min(1,u));
const ease=(u:number)=>{u=clamp01(u);return u<.5?4*u*u*u:1-Math.pow(-2*u+2,3)/2;};
const kf=(t:number,pts:[number,number][],lin=false)=>{if(t<=pts[0][0])return pts[0][1];for(let i=1;i<pts.length;i++){const [a,va]=pts[i-1],[b,vb]=pts[i];if(t<=b){const u=(t-a)/(b-a);return va+(vb-va)*(lin?u:ease(u));}}return pts[pts.length-1][1];};
const pop=(f:number)=>f<0?0:spring({frame:f,fps:30,config:{damping:12,stiffness:240,mass:.7}});
const rnd=(i:number)=>{const x=Math.sin(i*127.1+311.7)*43758.5453;return x-Math.floor(x);};
const GROUND=1240;
const R={strokeLinecap:'round' as const,strokeLinejoin:'round' as const};
const txt:React.CSSProperties={fontFamily:'Lilita',color:PAPER,WebkitTextStroke:`12px ${INK}`,paintOrder:'stroke fill',textAlign:'center',lineHeight:1,whiteSpace:'pre-line'};
const kindOf=(c:Case,r:Side)=>r==='a'?c.a:c.b;
const other=(r:Side):Side=>r==='a'?'b':'a';
const dirOf=(r:Side)=>r==='a'?1:-1;

// ---------------- habitats ----------------
type Hab={sky:string[];far:string;farLit:string;mid:string;midLit:string;g:string;g2:string;edge:string;line:string;dust:string;deb:string[];strip?:string;water?:boolean};
const HAB:Record<Bg,Hab>={
 ice:{sky:['#4F9FDD','#B5DEF6','#EAF7FD'],far:'#9BBCE0',farLit:'#EDF6FC',mid:'#A6CDE9',midLit:'#F4FBFF',g:'#EAF5FC',g2:'#A9CFE8',edge:'#A9D5EE',line:'#A3CBE2',dust:'#FFFFFF',deb:['#FFFFFF','#BFE3F7','#8EC9EE'],strip:'#2F7FB8'},
 jungle:{sky:['#6DBE9A','#C6E8B0','#F2F7C8'],far:'#5FA77A',farLit:'#7DBE8C',mid:'#2C7444',midLit:'#44995A',g:'#8C6A44',g2:'#644A2E',edge:'#6E5235',line:'#5D4429',dust:'#E8DCC0',deb:['#3F9154','#8C6A44','#C9D96A'],strip:'#4E8FA0'},
 scrub:{sky:['#EE8F54','#F8CF8A','#FBE9BE'],far:'#C4835A',farLit:'#DFA574',mid:'#6E5236',midLit:'#8E9A4C',g:'#D7AE6C',g2:'#B0854A',edge:'#BF9455',line:'#A07A40',dust:'#F3E2BC',deb:['#B48A55','#8A6A3C','#E8D29A']},
 savanna:{sky:['#5FAEE6','#C9E7F2','#F6EFC2'],far:'#96AE78',farLit:'#B4C790',mid:'#5E4B30',midLit:'#7C9A44',g:'#D9C26E',g2:'#AE9446',edge:'#C2A955',line:'#9C843C',dust:'#EFE2B0',deb:['#B79C4C','#8E7A3A','#F1E3A5']},
 river:{sky:['#7CC2E6','#D2ECDD','#EEF4C4'],far:'#6FA873',farLit:'#8EBF86',mid:'#3F7C4C',midLit:'#5B9A58',g:'#A1825A',g2:'#6F5336',edge:'#7E6140',line:'#6A5034',dust:'#CFEAF2',deb:['#7FC4D8','#9A7B55','#DFF3F7'],strip:'#3F93B4'},
 ocean:{sky:['#7FD8EA','#2A93C4','#0B3F6B'],far:'#1F79A8',farLit:'#3A97C2',mid:'#125882',midLit:'#1C6E9C',g:'#0D4470',g2:'#082C4C',edge:'#0A3558',line:'#1C6E9C',dust:'#E4F8FF',deb:['#E4F8FF','#A9E4F4','#FFFFFF'],water:true},
};
const ridge=(seed:number,x0:number,x1:number,base:number,amp:number,step:number,jag:boolean)=>{let d=`M${x0} ${base+900}L${x0} ${base}`,px=x0,py=base;
 for(let x=x0+step,i=0;x<=x1;x+=step,i++){const y=base-amp*(.3+.7*rnd(seed+i))*(i%2?1:.45);d+=jag?`L${x} ${y}`:`Q${(px+x)/2} ${Math.min(py,y)-amp*.25} ${x} ${y}`;px=x;py=y;}
 return d+`L${x1} ${base+900}Z`;};
const BG:React.FC<{bg:Bg;cx:number;f:number}>=({bg,cx,f})=>{
 const H=HAB[bg],hz=GROUND-170,p=(k:number)=>`translate(${-cx*k} 0)`,X0=-1500,X1=2600,S7={stroke:INK,strokeWidth:7,...R};
 const tree=(x:number,i:number,sc=1)=><g key={x} transform={`translate(${x} ${hz+30}) scale(${sc})`}><path d={`M-14 0C-8 -120 -30 -200 -50 -270M-6 -150C20 -200 50 -230 80 -250`} fill="none" stroke={INK} strokeWidth={34} {...R}/><path d={`M-14 0C-8 -120 -30 -200 -50 -270M-6 -150C20 -200 50 -230 80 -250`} fill="none" stroke={H.mid} strokeWidth={20} {...R}/>
  <path d={`M-260 -270C-240 -350 -120 -380 -20 -360C80 -390 200 -350 230 -280C150 -262 -160 -250 -260 -270Z`} fill={H.midLit} {...S7}/><path d={`M-230 -282C-120 -296 110 -300 210 -288C150 -266 -160 -256 -230 -282Z`} fill={H.mid} opacity={.45}/></g>;
 return <svg width={1080} height={1920} style={{position:'absolute',overflow:'visible'}}>
  <defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={H.sky[0]}/><stop offset=".6" stopColor={H.sky[1]}/><stop offset="1" stopColor={H.sky[2]}/></linearGradient>
   <linearGradient id="gr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={H.g}/><stop offset="1" stopColor={H.g2}/></linearGradient></defs>
  <rect x={X0} y={-1400} width={X1-X0} height={H.water?4400:hz+1420} fill="url(#sky)"/>
  {H.water?<>
   <g transform={p(.06)} opacity={.5}>{[0,1,2,3,4,5,6].map(i=><path key={i} d={`M${-300+i*300+40*Math.sin(f*.02+i)} -300L${-520+i*330+60*Math.sin(f*.017+i*2)} 1700h${150+i%3*50}L${-180+i*300+40*Math.sin(f*.02+i)} -300Z`} fill="#D9F6FF" opacity={.16+.06*(i%2)}/>)}</g>
   <g transform={p(.12)}><path d={ridge(3,X0,X1,GROUND+150,420,210,true)} fill={H.far}/><path d={ridge(9,X0,X1,GROUND+200,280,150,true)} fill={H.farLit} opacity={.5}/></g>
   <g transform={p(.4)}><path d={ridge(21,X0,X1,GROUND+210,230,150,false)} fill={H.mid} {...S7}/><path d={ridge(21,X0+30,X1,GROUND+250,170,150,false)} fill={H.midLit} opacity={.5}/></g>
   <g transform={p(.7)}>{[-1300,-860,-430,10,450,890,1320,1760,2200].map((x,i)=><g key={x}>{[0,1,2].map(j=>{const bx=x+j*70-70,hh=330+((i+j)%3)*120,sw=26*Math.sin(f*.05+i+j);return <g key={j}>
     <path d={`M${bx} ${GROUND+420}C${bx-30+sw} ${GROUND+420-hh*.4} ${bx+40+sw} ${GROUND+420-hh*.7} ${bx+sw} ${GROUND+420-hh}`} fill="none" stroke={INK} strokeWidth={26} {...R}/><path d={`M${bx} ${GROUND+420}C${bx-30+sw} ${GROUND+420-hh*.4} ${bx+40+sw} ${GROUND+420-hh*.7} ${bx+sw} ${GROUND+420-hh}`} fill="none" stroke={j%2?'#2E8C6A':'#1F7458'} strokeWidth={14} {...R}/>
     {[.3,.5,.7,.9].map((u,q)=><ellipse key={q} cx={bx+sw*u+(q%2?34:-34)} cy={GROUND+420-hh*u} rx={38} ry={13} fill={q%2?'#3DA57C':'#2E8C6A'} stroke={INK} strokeWidth={6} transform={`rotate(${q%2?-28:28} ${bx+sw*u+(q%2?34:-34)} ${GROUND+420-hh*u})`}/>)}</g>;})}</g>)}</g>
   <g transform={p(1)}><path d={ridge(40,X0,X1,GROUND+330,110,170,false)} fill="url(#gr)" {...S7}/>{Array.from({length:14}).map((_,i)=>{const x=X0+i*300+rnd(i)*120,y=GROUND+330-20*rnd(i+3);return <g key={i}>{i%2?<path d={`M${x} ${y}q-34 -100 10 -170q34 56 24 170M${x+56} ${y+8}q34 -80 0 -136q-34 44 -24 136M${x-50} ${y+6}q-10 -70 20 -100q20 40 10 100`} fill={i%4===1?'#E8776C':'#F2B24E'} {...S7}/>:<><path d={`M${x-90} ${y+20}q20 -110 100 -120q90 -6 110 120Z`} fill={H.midLit} {...S7}/><path d={`M${x+10} ${y+16}q30 -70 90 -40q14 20 20 44Z`} fill={H.mid}/></>}</g>;})}</g>
  </>:<>
   <g transform={p(.05)}><circle cx={790} cy={hz-560} r={210} fill="#FFF8DC" opacity={.3}/><circle cx={790} cy={hz-560} r={118} fill="#FFF8DC"/>
    {[[-200,hz-640,1.2],[420,hz-470,.9],[1150,hz-700,1.4],[1700,hz-520,1]].map(([x,y,s],i)=><g key={i} transform={`translate(${x+f*.25} ${y}) scale(${s})`} fill="#FFFFFF" opacity={.75}><ellipse cx={0} cy={0} rx={150} ry={34}/><ellipse cx={-50} cy={-26} rx={70} ry={36}/><ellipse cx={46} cy={-34} rx={86} ry={46}/></g>)}</g>
   <g transform={p(.12)}><path d={ridge(3,X0,X1,hz,bg==='ice'?360:bg==='scrub'?260:230,bg==='ice'?170:260,bg==='ice'||bg==='scrub')} fill={H.far}/><path d={ridge(3,X0+26,X1,hz,bg==='ice'?360:bg==='scrub'?260:230,bg==='ice'?170:260,bg==='ice'||bg==='scrub')} fill={H.farLit} opacity={bg==='ice'?.85:.45} transform="translate(0 44)"/><path d={ridge(11,X0,X1,hz,120,140,false)} fill={H.far} opacity={.7}/></g>
   {H.strip&&<g><rect x={X0} y={hz-16} width={X1-X0} height={90} fill={H.strip} {...S7}/>{Array.from({length:22}).map((_,i)=><path key={i} d={`M${X0+i*190+((f*1.4)%190)} ${hz+10+(i%3)*20}h${60+(i%2)*40}`} stroke="#FFFFFF" strokeWidth={6} opacity={.55} {...R}/>)}</g>}
   <g transform={p(.38)}>{bg==='ice'?[-1100,-640,-150,330,830,1300,1800].map((x,i)=>{const w=300+(i%3)*90,h=250+(i%2)*150,y=hz+34;return <g key={x}><path d={`M${x} ${y}L${x+w*.18} ${y-h*.7}L${x+w*.42} ${y-h}L${x+w*.62} ${y-h*.78}L${x+w*.8} ${y-h*.9}L${x+w} ${y}Z`} fill={H.midLit} {...S7}/><path d={`M${x+w*.42} ${y-h}L${x+w*.62} ${y-h*.78}L${x+w*.8} ${y-h*.9}L${x+w} ${y}L${x+w*.5} ${y}Z`} fill={H.mid}/><path d={`M${x+w*.42} ${y-h}L${x+w*.5} ${y}`} stroke={INK} strokeWidth={5} opacity={.5}/><path d={`M${x} ${y}L${x+w*.18} ${y-h*.7}L${x+w*.42} ${y-h}L${x+w*.62} ${y-h*.78}L${x+w*.8} ${y-h*.9}L${x+w} ${y}Z`} fill="none" {...S7}/></g>;})
    :bg==='jungle'||bg==='river'?[-1200,-800,-380,60,470,900,1330,1760,2150].map((x,i)=><g key={x}><path d={`M${x} ${hz+40}C${x+20} ${hz-300} ${x-20} ${hz-520} ${x+10} ${hz-760}`} stroke={INK} strokeWidth={bg==='river'?40:64} fill="none" {...R}/><path d={`M${x} ${hz+40}C${x+20} ${hz-300} ${x-20} ${hz-520} ${x+10} ${hz-760}`} stroke="#5B4A33" strokeWidth={bg==='river'?26:50} fill="none" {...R}/>
      {[0,1,2].map(j=><ellipse key={j} cx={x+(j-1)*150} cy={hz-(bg==='river'?520:700)-j%2*90+8*Math.sin(f*.04+i+j)} rx={190} ry={130} fill={j%2?H.mid:H.midLit} {...S7}/>)}
      {bg==='river'&&[0,1,2,3].map(j=><path key={'r'+j} d={`M${x+180+j*34} ${hz+40}q${10*Math.sin(f*.05+j+i)} -90 ${-6+j*6} -${150+j%2*50}`} stroke={H.mid} strokeWidth={12} fill="none" {...R}/>)}</g>)
    :[-1150,-560,40,610,1220,1840].map((x,i)=>tree(x,i,.9+(i%2)*.35))}</g>
   <g transform={p(1)}>
    <path d={`M${X0} ${hz+52}${Array.from({length:28}).map((_,i)=>`L${X0+i*150+60} ${hz+52+(i%2?10:-8)*rnd(i+5)}`).join('')}L${X1} ${hz+52}V3400H${X0}Z`} fill="url(#gr)" {...S7}/>
    <path d={`M${X0} ${hz+52}H${X1}`} stroke={H.edge} strokeWidth={26} opacity={.6}/>
    {Array.from({length:11}).map((_,i)=>{const x=X0+i*380+rnd(i+90)*160,y=hz+330+rnd(i+95)*300,s=.8+rnd(i+97)*.7;return bg==='ice'?<g key={'b'+i} transform={`translate(${x} ${y}) scale(${s})`}><path d="M-130 0L-100 -90L-20 -130L70 -100L140 0Z" fill={H.midLit} {...S7}/><path d="M-20 -130L70 -100L140 0L10 0Z" fill={H.mid}/><path d="M-130 0H140" stroke={H.g2} strokeWidth={14} opacity={.8}/></g>:<g key={'b'+i} transform={`translate(${x} ${y}) scale(${s})`}><path d="M-110 0q10 -90 100 -96q100 -2 116 96Z" fill={H.edge} {...S7}/><path d="M10 -4q30 -60 80 -40q20 16 24 40Z" fill={H.g2} opacity={.7}/></g>;})}
    {Array.from({length:12}).map((_,i)=><ellipse key={'s'+i} cx={X0+i*350+rnd(i+70)*200} cy={hz+260+rnd(i+80)*520} rx={300+rnd(i)*160} ry={34+rnd(i+3)*24} fill={H.g2} opacity={.45}/>)}
    {Array.from({length:60}).map((_,i)=>{const x=X0+i*70+rnd(i)*90,y=hz+120+rnd(i+40)*640,k=[0,1,0,2,1,0,3,1][i%8];
     return bg==='ice'?(k<2?<path key={i} d={`M${x} ${y}l${90+rnd(i)*80} ${22}l${50} -18l${110} ${30}`} fill="none" stroke={H.line} strokeWidth={7} {...R}/>:k===2?<g key={i}><path d={`M${x} ${y}q70 -64 150 0Z`} fill="#FFFFFF" {...S7}/><path d={`M${x+60} ${y-4}q50 -30 84 2Z`} fill={H.g2}/></g>:<g key={i}><path d={`M${x} ${y}l26 -110l34 60l24 -84l40 134Z`} fill={H.midLit} {...S7}/><path d={`M${x+60} ${y-50}l24 -84l40 134Z`} fill={H.mid}/></g>)
      :bg==='jungle'||bg==='river'?(k<2?<path key={i} d={`M${x} ${y}q-34 -70 -70 -70M${x} ${y}q0 -90 10 -100M${x} ${y}q40 -64 76 -60`} fill="none" stroke={H.midLit} strokeWidth={14} {...R}/>:k===2?<ellipse key={i} cx={x} cy={y} rx={70} ry={26} fill={H.edge} {...S7}/>:<path key={i} d={`M${x} ${y}h150`} stroke={H.line} strokeWidth={8} {...R}/>)
      :(k<2?<path key={i} d={`M${x} ${y}l-16 -46M${x} ${y}l4 -58M${x} ${y}l22 -44`} stroke={H.line} strokeWidth={8} {...R}/>:k===2?<path key={i} d={`M${x} ${y}q10 -44 60 -40q50 -6 56 40Z`} fill={H.edge} {...S7}/>:<path key={i} d={`M${x} ${y}h120`} stroke={H.line} strokeWidth={7} opacity={.7} {...R}/>);})}
   </g>
  </>}
 </svg>;
};
const Weather:React.FC<{bg:Bg;f:number;near?:boolean}>=({bg,f,near})=>{const n=near?10:34,H=HAB[bg];
 return <svg width={1080} height={1920} style={{position:'absolute',filter:near?'blur(5px)':undefined}}>{Array.from({length:n}).map((_,i)=>{const k=near?2.4:1,sp=(2+(i%4))*k;
  const x=((i*157+f*(bg==='ice'?2.2:1.1)*(i%2?1:-.5)*k)%1240+1240)%1240-80,dn=bg==='ice'||bg==='jungle',y0=((i*263+f*sp*(dn?1:-.6))%2000+2000)%2000-40,r=(near?16:5)+(i%3)*(near?8:3);
  return bg==='ocean'?<circle key={i} cx={x+10*Math.sin(f*.1+i)} cy={y0} r={r*.9} fill="none" stroke="#E4F8FF" strokeWidth={near?6:3} opacity={.7}/>
   :bg==='ice'?<circle key={i} cx={x} cy={y0} r={r} fill="#FFFFFF" opacity={.92}/>
   :bg==='jungle'?<path key={i} d={`M${x} ${y0}q${r*2} ${-r*2} ${r*4} 0q${-r*2} ${r*2} ${-r*4} 0Z`} fill={i%2?'#C9D96A':'#5DAA5E'} opacity={.85} transform={`rotate(${f*3+i*40} ${x} ${y0})`}/>
   :<circle key={i} cx={x} cy={y0} r={r*.8} fill={H.dust} opacity={.6}/>;})}
  {bg==='ice'&&!near&&[0,1,2,3].map(i=><path key={'w'+i} d={`M${((f*26+i*420)%1700)-400} ${380+i*310}h${220+i*40}`} stroke="#FFFFFF" strokeWidth={7} opacity={.5} {...R}/>)}
 </svg>;};
const Fore:React.FC<{bg:Bg;cx:number}>=({bg,cx})=>{const H=HAB[bg],o=-cx*1.5;
 return <svg width={1080} height={1920} style={{position:'absolute',overflow:'visible',filter:'blur(4px)'}}><g transform={`translate(${o} 0)`}>
  {[-1400,-700,0,700,1400,2100].map((x,i)=>bg==='jungle'||bg==='river'?<path key={x} d={`M${x} 1960C${x+60} 1760 ${x+200} 1700 ${x+330} 1690C${x+280} 1790 ${x+240} 1880 ${x+260} 1960Z`} fill="#1E5233" opacity={.9}/>
   :bg==='ocean'?<path key={x} d={`M${x} 1960C${x+20} 1800 ${x+110} 1730 ${x+90} 1640C${x+170} 1740 ${x+190} 1850 ${x+210} 1960Z`} fill="#062640" opacity={.85}/>
   :<path key={x} d={`M${x} 1960C${x+90} 1790 ${x+330} 1760 ${x+520} 1960Z`} fill={bg==='ice'?'#FFFFFF':H.g2} opacity={.95}/>)}</g></svg>;};

// ---------------- camera + world ----------------
type Cam={cx:number;fy:number;sy:number;z:number};
const at=(P:readonly [number,number],px:number,py:number,z:number):Cam=>({cx:P[0]-540-(px-540)/z,fy:P[1],sy:py,z});
type Imp={k:number;x:number;y:number;sil?:boolean}|null;   // impact frame: k 0,1 = ink silhouettes on white; 2,3 = colour burst
const World:React.FC<{c:Case;cam:Cam;sh?:number;imp?:Imp;whip?:number;over?:React.ReactNode;burst?:string;children:React.ReactNode}>=({c,cam,sh=0,imp=null,whip=0,over,burst,children})=>{
 const f=useCurrentFrame(),dx=sh*Math.sin(f*2.3)*(f%2?1:-1)+6*Math.sin(f*.09),dy=sh*.7*Math.cos(f*1.7)+4*Math.cos(f*.07),rz=.4*Math.sin(f*.05)+sh*.06*Math.sin(f*3.1),wb=Math.abs(whip);
 const sil=!!imp&&!!imp.sil;
 return <AbsoluteFill style={{overflow:'hidden',background:INK}}>
  <AbsoluteFill style={{transform:`translate(${dx+whip*40}px,${dy+cam.sy-cam.fy}px) rotate(${rz}deg) scale(${cam.z*1.03})`,transformOrigin:`540px ${cam.fy}px`,filter:wb>.05?`blur(${wb*7}px)`:undefined}}>
   {imp?<svg width={1080} height={1920} style={{position:'absolute',overflow:'visible'}}><rect x={-3000} y={-3000} width={7000} height={8000} fill={sil?'#FFFFFF':GOLD}/>
     <g transform={`translate(${imp.x-cam.cx} ${imp.y})`}>{Array.from({length:26}).map((_,i)=>{const a=i*13.85*Math.PI/180,r0=sil?230+rnd(i)*160:120,w=.035+.05*rnd(i+9);return <path key={i} d={`M${Math.cos(a)*r0} ${Math.sin(a)*r0}L${Math.cos(a-w)*3600} ${Math.sin(a-w)*3600}L${Math.cos(a+w)*3600} ${Math.sin(a+w)*3600}Z`} fill={sil?INK:(i%2?RED:'#FFFFFF')}/>;})}</g></svg>
    :<><BG bg={c.bg} cx={cam.cx} f={f}/><Weather bg={c.bg} f={f}/>{burst&&<svg width={1080} height={1920} style={{position:'absolute',overflow:'visible'}}><rect x={-3000} y={-3000} width={7000} height={8000} fill={burst} opacity={.86}/><g transform={`translate(540 ${cam.fy})`} opacity={.22}>{Array.from({length:18}).map((_,i)=>{const a=(i*20+f*.8)*Math.PI/180;return <path key={i} d={`M0 0L${Math.cos(a)*3200} ${Math.sin(a)*3200}L${Math.cos(a+.17)*3200} ${Math.sin(a+.17)*3200}Z`} fill="#FFFFFF"/>;})}</g></svg>}</>}
   <svg width={1080} height={1920} style={{position:'absolute',overflow:'visible',filter:sil?'brightness(0)':undefined}}><g transform={`translate(${-cam.cx} 0)`}>{children}</g></svg>
   {!imp&&<Fore bg={c.bg} cx={cam.cx}/>}
  </AbsoluteFill>
  {!imp&&<Weather bg={c.bg} f={f} near/>}
  {over}
  {wb>.05&&<svg width={1080} height={1920} style={{position:'absolute'}}>{Array.from({length:16}).map((_,i)=><path key={i} d={`M-50 ${120*i+40}H1130`} stroke="#FFFFFF" strokeWidth={14} opacity={.35*wb}/>)}</svg>}
 </AbsoluteFill>;
};
// one animal on stage: x = body-centre ground x, y = lift above the ground line
const B:React.FC<{c:Case;r:Side;x:number;p:PX;t:number;y?:number;sq?:number;ghost?:Pt;face?:Side;tilt?:number;s?:number}>=({c,r,x,p,t,y=0,sq,ghost,face,tilt,s=1})=>{
 const k=kindOf(c,r),G=GEO[k],flip=(face??r)==='b',w=HAB[c.bg].water,fl=w?70+16*Math.sin(t*.09+(r==='a'?0:2)):0;
 return <g>{!w&&<ellipse cx={x+(flip?-1:1)*G.cx*G.sc*s} cy={GROUND+10} rx={(G.reach+G.back)*.42*G.sc*s*(1-Math.min(.5,y/500))} ry={26*s} fill="#0B1E33" opacity={.2*(1-Math.min(.6,y/400))}/>}
  <Animal kind={k} x={x} y={GROUND-y-fl} s={G.sc*s} flip={flip} p={p} t={t} sq={sq} ghost={ghost} tilt={tilt}/></g>;};
const headAt=(c:Case,r:Side,x:number,p:PX,t:number,face?:Side,y=0):Pt=>{const k=kindOf(c,r),d=(face??r)==='a'?1:-1,h=headPos(k,p,t),fl=HAB[c.bg].water?70:0;return [x+d*h[0]*GEO[k].sc,GROUND-y-fl+h[1]*GEO[k].sc];};
// snouts meet at x=540 when both back-off distances are 0; idle keeps 120 each
const X0=(c:Case,r:Side)=>{const G=GEO[kindOf(c,r)];return r==='a'?540-G.reach*G.sc+10:540+G.reach*G.sc-10;};
const posOf=(c:Case,r:Side,d:number)=>X0(c,r)-dirOf(r)*d;
const IDLE=120;

// ---------------- effects ----------------
const Dust:React.FC<{c:Case;x:number;y?:number;t:number;n?:number;s?:number;dir?:number;life?:number}>=({c,x,y=GROUND,t,n=5,s=1,dir=-1,life=24})=>{if(t<0||t>life)return null;const u=t/life,H=HAB[c.bg];
 return <g>{Array.from({length:n}).map((_,i)=>{const a=(i/Math.max(1,n-1)-.5)*1.9,up=H.water?-180*u*rnd(i+3):0;return <circle key={i} cx={x+dir*Math.cos(a)*190*Math.sqrt(u)*s+i*12} cy={y-Math.abs(Math.sin(a))*110*Math.sqrt(u)*s-14+up} r={(26+46*u)*s*(.65+.35*(i%2))*(H.water?.5:1)} fill={H.water?'none':H.dust} stroke={H.water?H.dust:INK} strokeWidth={H.water?6:5} opacity={.95*(1-u*u)}/>;})}
  {Array.from({length:Math.ceil(n/2)}).map((_,i)=>{const a=(i/Math.max(1,Math.ceil(n/2)-1)-.5)*1.5;return <circle key={'n'+i} cx={x+dir*Math.cos(a)*330*Math.sqrt(u)*s+i*30} cy={y+46-Math.abs(Math.sin(a))*70*Math.sqrt(u)*s} r={(48+84*u)*s*(H.water?.28:1)} fill={H.water?'none':H.dust} stroke={H.water?H.dust:INK} strokeWidth={H.water?8:6} opacity={.85*(1-u)}/>;})}</g>;};
const Debris:React.FC<{c:Case;x:number;y?:number;t:number;n?:number;s?:number}>=({c,x,y=GROUND,t,n=12,s=1})=>{if(t<0||t>30)return null;const H=HAB[c.bg],g=H.water?-.4:2.1;
 return <g>{Array.from({length:n}).map((_,i)=>{const a=-Math.PI*(.12+.76*rnd(i+1)),v=(17+20*rnd(i+7))*s,px=x+Math.cos(a)*v*t,py=y+Math.sin(a)*v*t+g*t*t*.5,r=(12+20*rnd(i+13))*s;
  return py>GROUND+30&&!H.water?null:H.water?<circle key={i} cx={px} cy={py} r={r*.7} fill="none" stroke={H.deb[i%3]} strokeWidth={5} opacity={1-t/30}/>:<path key={i} d={`M${px} ${py-r}L${px+r*.8} ${py+r*.3}L${px-r*.2} ${py+r}L${px-r} ${py}Z`} fill={H.deb[i%3]} stroke={INK} strokeWidth={5} transform={`rotate(${t*(14+i*5)} ${px} ${py})`} {...R}/>;})}</g>;};
const Ring:React.FC<{x:number;y?:number;t:number;s?:number}>=({x,y=GROUND,t,s=1})=>{if(t<0||t>14)return null;const u=t/14;return <ellipse cx={x} cy={y} rx={(80+620*u)*s} ry={(22+150*u)*s} fill="none" stroke="#FFFFFF" strokeWidth={26*(1-u)+4} opacity={1-u}/>;};
const Speed:React.FC<{t:number;dir:number;x0:number;y0:number;y1:number}>=({t,dir,x0,y0,y1})=><g>{Array.from({length:16}).map((_,i)=>{const y=y0+(i*97)%(y1-y0),len=200+(i*53)%220,x=x0+((i*211-t*90*dir)%1900+1900)%1900-400;return <path key={i} d={`M${x} ${y}h${len}`} stroke="#FFFFFF" strokeWidth={8+(i%3)*5} opacity={.8} {...R}/>;})}</g>;
const Star:React.FC<{x:number;y:number;t:number;s?:number}>=({x,y,t,s=1})=>{if(t<0||t>9)return null;const g=1-t/10;return <g transform={`translate(${x} ${y}) scale(${s*Math.min(1.4,.3+.3*t)}) rotate(${t*6})`} opacity={g}><path d="M0 -120L28 -40L110 -66L54 0L120 50L36 50L40 130L-8 60L-76 116L-60 32L-136 8L-60 -22L-88 -98L-18 -52Z" fill={GOLD} stroke={INK} strokeWidth={9} {...R}/></g>;};
// hand-lettered impact word in the channel's lettering: every letter has its own tilt, size and baseline; lands on the hit frame
const Word:React.FC<{t:number;text:string;y?:number;color?:string;size?:number}>=({t,text,y=470,color=GOLD,size=200})=>{if(t<0||t>24)return null;const sc=Math.min(1,.3+.24*t)*(1+(t>=3?.08*Math.exp(-(t-3)/3):0)),o=t>18?1-(t-18)/6:1,fs=Math.min(size,1500/text.length);
 return <div style={{position:'absolute',left:0,top:y-size/2,width:1080,display:'flex',justifyContent:'center',alignItems:'center',transform:`scale(${sc}) rotate(${-7+2*Math.sin(t*1.3)}deg)`,opacity:o,zIndex:20}}>
  {text.split('').map((ch,i)=><span key={i} style={{...txt,display:'inline-block',fontSize:fs*(1+.22*(rnd(i+text.length)-.4)),color:i%2?color:'#FFFFFF',WebkitTextStroke:`18px ${INK}`,textShadow:`10px 12px 0 ${INK}`,transform:`translateY(${(rnd(i*3+1)-.5)*fs*.22}px) rotate(${(rnd(i*7+2)-.5)*22}deg)`,margin:`0 ${-fs*.02}px`}}>{ch}</span>)}</div>;};

// ---------------- face-off (frame 0 = both already charging in, title up) ----------------
const twoCam=(ha:Pt,hb:Pt,sy:number,zmax:number,pad=640,push=1):Cam=>{const span=Math.abs(hb[0]-ha[0]),z=Math.max(.62,Math.min(zmax,1080/(span+pad)))*push;return at([(ha[0]+hb[0])/2,(ha[1]+hb[1])/2+40],540,sy,z);};
// framing rule: a solo shot shows the main animal at >= 40% of frame height; a two-shot fills the frame width with both bodies
const fitCam=(c:Case,xa:number,xb:number,ha:Pt,hb:Pt,sy:number,zmax=1.3,push=1,bk=.55):Cam=>{const A=GEO[c.a],Bk=GEO[c.b],l=xa-A.back*A.sc*bk,r=xb+Bk.back*Bk.sc*bk,z=Math.min(zmax,1080/Math.max(400,r-l))*push;return at([(l+r)/2,(ha[1]+hb[1])/2+60],540,sy,z);};
const soloZ=(k:Kind)=>Math.max(1.15,Math.min(2.4,820/(GEO[k].top*GEO[k].sc)));
const soloCam=(c:Case,r:Side,h:Pt,fd:number,sy:number,k=1):Cam=>{const G=GEO[kindOf(c,r)];return at([h[0]-fd*G.reach*G.sc*.22,h[1]+G.top*G.sc*.16],540,sy,soloZ(kindOf(c,r))*k);};
const scr=(cam:Cam,p:Pt):Pt=>[540+(p[0]-cam.cx-540)*cam.z*1.03,cam.sy+(p[1]-cam.fy)*cam.z*1.03];
const Bang:React.FC<{x:number;y:number;t:number;s?:number}>=({x,y,t,s=1})=>{if(t<0||t>16)return null;const k=pop(t);return <g transform={`translate(${x} ${y}) scale(${s*(.4+.6*k)}) rotate(${10*Math.sin(t)})`}><path d="M-22 -150L26 -150L12 -36L-10 -36Z" fill={RED} stroke={INK} strokeWidth={12} {...R}/><circle cx={0} cy={6} r={22} fill={RED} stroke={INK} strokeWidth={12}/></g>;};
const Dizzy:React.FC<{x:number;y:number;t:number;s?:number}>=({x,y,t,s=1})=>{if(t<0)return null;return <g>{[0,1,2].map(i=>{const a=t*.5+i*2.094;return <path key={i} d="M0 -26L8 -8L26 0L8 8L0 26L-8 8L-26 0L-8 -8Z" fill={GOLD} stroke={INK} strokeWidth={6} transform={`translate(${x+Math.cos(a)*110*s} ${y+Math.sin(a)*34*s}) scale(${s*(1+.3*Math.sin(a))})`} {...R}/>;})}</g>;};
// frame 0: both animals large and already lunging; they collide at frame 5 (impact frame), recoil and roar. The title is a small top label.
const FaceOff:React.FC<{c:Case;t:number;title:number;big?:boolean}>=({c,t,title,big})=>{
 const hit=5,d=t<0?70+(-t)*3:t<hit?70*(1-t/hit):kf(t,[[hit,0],[hit+10,64]]),W=HAB[c.bg].water;
 const mk=(t0:number):PX=>{const roar=kf(t,[[t0,0],[t0+5,1],[t0+14,1],[t0+20,0]]);return t<hit?pose('charge',undefined,0,{jaw:.8,grit:0}):t<hit+8?pose('hit','roar',(t-hit)/8):pose('idle','roar',Math.max(roar,.2),{rear:.15*roar,head:-6});};
 const pa=mk(13),pb=mk(26),xa=posOf(c,'a',d),xb=posOf(c,'b',d),ha=headAt(c,'a',xa,pose('idle'),0),hb=headAt(c,'b',xb,pose('idle'),0),iy=(ha[1]+hb[1])/2;
 const cam=fitCam(c,xa,xb,ha,hb,1060,1.4,(1+.03*clamp01(t/44))*(1+(t>=hit?.07*Math.exp(-(t-hit)/4):0)),.3);
 const imp:Imp=null;
 return <AbsoluteFill><World c={c} cam={cam} imp={imp} sh={t>=hit&&t<hit+12?16*(1-(t-hit)/12):t>14&&t<40?3:0}>
  {t<hit&&!imp&&<Speed t={t} dir={1} x0={-600} y0={GROUND-620} y1={GROUND-30}/>}
  <B c={c} r="a" x={xa} p={pa} t={t+100} ghost={t<hit?[60,0]:undefined} sq={t>=hit?-.1*Math.exp(-(t-hit)/4):.06}/><B c={c} r="b" x={xb} p={pb} t={t+117} ghost={t<hit?[-60,0]:undefined} sq={t>=hit?-.1*Math.exp(-(t-hit)/4):.06}/>
  {!imp&&<><Ring x={540} y={W?iy:GROUND} t={t-hit} s={.9}/><Debris c={c} x={540} y={W?iy:GROUND} t={t-hit} n={12}/><Dust c={c} x={xa-60} t={t-hit-2} n={5} dir={-1}/><Dust c={c} x={xb+60} t={t-hit-2} n={5} dir={1}/></>}
 </World>
 {title>0&&(big?<TitleCard c={c} o={title} t={t}/>:<div style={{position:'absolute',left:0,top:118,width:1080,display:'flex',justifyContent:'center',opacity:title,zIndex:22}}><div style={{background:INK,borderRadius:50,padding:'14px 36px',border:`6px solid ${PAPER}`,transform:`scale(${t>=0?1+.1*Math.exp(-t/3):1})`}}>
   <span style={{fontFamily:'Lilita',fontSize:Math.min(66,1500/(c.title[0].length+c.title[1].length+4)),color:PAPER,whiteSpace:'nowrap'}}>{c.title[0]} <span style={{color:RED}}>VS</span> <span style={{color:GOLD}}>{c.title[1]}</span></span></div></div>)}
 </AbsoluteFill>;
};
const fit=(s:string,max=160)=>Math.min(max,1700/Math.max(1,s.length));
const TitleCard:React.FC<{c:Case;o:number;t:number}>=({c,o,t})=>{const k=t>=0?1+.12*Math.exp(-t/3):1;return <div style={{position:'absolute',left:0,top:130,width:1080,opacity:o,zIndex:22,transform:`scale(${k})`,transformOrigin:'50% 40%'}}>
 <div style={{...txt,fontSize:fit(c.title[0]),color:PAPER,transform:'rotate(-2deg)'}}>{c.title[0]}</div>
 <div style={{...txt,fontSize:130,color:RED,margin:'2px 0'}}>VS</div>
 <div style={{...txt,fontSize:fit(c.title[1]),color:GOLD,transform:'rotate(2deg)'}}>{c.title[1]}</div>
</div>;};

// ---------------- stats ride on action: no card, no band. The number counts up as a big caption while the animals act:
// first two-sided stat = shove (the bigger number drives the other back), later two-sided = the winner towers up,
// one-sided = that animal shows the weapon (two chomps/strikes) in close-up. One reaction cut inside each stat.
const numOf=(s:string)=>{const m=s.match(/[\d,]*\.?\d+/);return m?parseFloat(m[0].replace(/,/g,'')):NaN;};
const countUp=(big:string,_u:number)=>big;   // the number is shown at its sourced value from its first frame (a paused frame must never show a wrong figure); it pops in by scale
const BigNum:React.FC<{v:{big:string;small:string};name:string;win:boolean;t:number;x:number;y:number;size:number;al:'left'|'right'|'center'}>=({v,name,win,t,x,y,size,al})=>{if(t<0)return null;const s=pop(t),fs=Math.min(size,(al==='center'?1500:1150)/v.big.length);
 return <div style={{position:'absolute',left:al==='left'?x:al==='right'?undefined:0,right:al==='right'?1080-x:undefined,width:al==='center'?1080:undefined,top:y,zIndex:14,textAlign:al,transform:`scale(${.5+.5*s}) rotate(${al==='right'?3:-3}deg)`,transformOrigin:al==='left'?'0% 100%':al==='right'?'100% 100%':'50% 100%'}}>
  <div style={{fontFamily:'Lilita',fontSize:44,color:PAPER,WebkitTextStroke:`9px ${INK}`,paintOrder:'stroke fill',lineHeight:1}}>{name}</div>
  <div style={{...txt,textAlign:al,fontSize:fs,color:win?GOLD:PAPER,WebkitTextStroke:`${fs>130?16:13}px ${INK}`,whiteSpace:'nowrap',textShadow:`8px 10px 0 ${INK}`}}>{countUp(v.big,clamp01(t/11))}</div>
  {v.small&&<div style={{fontFamily:'Quiet Sans',fontWeight:800,fontSize:36,color:PAPER,WebkitTextStroke:`7px ${INK}`,paintOrder:'stroke fill'}}>{v.small}</div>}</div>;};
const StatScene:React.FC<{c:Case;k:number;t:number;dur:number}>=({c,k,t,dur})=>{
 const st=c.stats[k],both=!!(st.a&&st.b),w=st.win,l=other(w),f=useCurrentFrame(),only:Side=st.a?'a':'b',lab=pop(t);
 const mode=!both?'weapon':c.stats.findIndex(s=>s.a&&s.b)===k?'shove':'rise',hit=9,cutT=Math.max(hit+12,Math.round(dur*.6));
 const lock=clamp01(t/hit),push=kf(t,[[hit,0],[hit+16,1]]),up=kf(t,[[3,0],[6,-.2],[14,1]]),ch=Math.abs(Math.sin(Math.max(0,t-3)*.3)),d:Dist={a:60,b:60};
 let pw:PX,pl:PX,sqw=0,sql=0;
 if(mode==='shove'){d[w]=60-60*lock*lock-140*push;d[l]=60-60*lock*lock+140*push;pw=t<hit?pose('charge'):pose('charge',undefined,0,{stride:push<1?1:0,jaw:.05});pl=t<hit?pose('charge'):pose('hit','tired',push,{sweat:1,stride:.3});sqw=t<hit?.06:0;sql=t>=hit?-.1*Math.exp(-(t-hit)/5):.06;}
 else if(mode==='rise'){const r=Math.max(0,up);d[l]=60+70*r;pw=pose('idle','roar',r,{rear:r,crouch:up<0?.5:0});pl=pose('idle','dodge',r,{sweat:r>.6?1:0});sqw=up<0?up*.4:.08*Math.exp(-(t-14)/5)*(t>=14?1:0);sql=-.06*r;}
 else{pw=pose('roar',undefined,0,{jaw:ch,strike:.35*ch,rear:.12,head:-8+10*ch});pl=pose('idle');}
 const P=(r:Side)=>both?(r===w?pw:pl):pw,x={a:posOf(c,'a',d.a),b:posOf(c,'b',d.b)},H=(r:Side)=>headAt(c,r,x[r],P(r),f);
 const react=both&&mode==='shove'&&t>=cutT,foc:Side=mode==='shove'?l:w;
 const cam=!both?at([H(only)[0]+dirOf(only)*10,H(only)[1]+40],540,930,Math.min(2.4,soloZ(kindOf(c,only))*1.15)*(1+.05*t/dur)*(1+.06*ch))
  :react?soloCam(c,foc,H(foc),dirOf(foc),960,1+.04*(t-cutT)/Math.max(1,dur-cutT))
  :fitCam(c,x.a,x.b,H('a'),H('b'),1060,1.3,(1+.03*t/dur)*(1+(t>=hit?.05*Math.exp(-(t-hit)/4):0)),.4);
 const ho=H(only),hw=H(w),ix=(x.a+x.b)/2+ (GEO[c.a].reach*GEO[c.a].sc-GEO[c.b].reach*GEO[c.b].sc)/2;
 return <AbsoluteFill><World c={c} cam={cam} burst={react||!both?CARD[k%3]:undefined} sh={mode==='shove'?(t>=hit&&t<hit+18?8:0):mode==='rise'?(t>=14&&t<22?9:0):4*ch}>
  {(both||only==='a')&&<B c={c} r="a" x={x.a} p={P('a')} t={f} sq={'a'===w||!both?sqw:sql} ghost={mode==='shove'&&t<hit?[50,0]:undefined}/>}{(both||only==='b')&&<B c={c} r="b" x={x.b} p={P('b')} t={f+17} sq={'b'===w||!both?sqw:sql} ghost={mode==='shove'&&t<hit?[-50,0]:undefined}/>}
  {mode==='shove'&&<><Star x={ix} y={hw[1]+40} t={t-hit} s={.9}/>{[0,5,10].map(q=><Dust key={q} c={c} x={x[l]} t={t-hit-q} n={4} s={.9} dir={-dirOf(l)} life={16}/>)}</>}
  {mode==='rise'&&<><Dust c={c} x={x[w]} t={t-14} n={6} s={1.2} dir={-dirOf(w)}/><Bang x={H(l)[0]} y={H(l)[1]-150} t={t-12} s={1.1}/></>}
  {!both&&[0,1,2,3,4].map(i=>{const tt=(t+i*7)%24,a=-Math.PI*(.1+.8*rnd(i+k));return <path key={i} d="M0 -22L7 -7L22 0L7 7L0 22L-7 7L-22 0L-7 -7Z" fill={i%2?GOLD:'#FFFFFF'} stroke={INK} strokeWidth={4} transform={`translate(${ho[0]+dirOf(only)*70+Math.cos(a)*(80+tt*6)} ${ho[1]+50+Math.sin(a)*(80+tt*6)}) scale(${1.5-tt/24})`} opacity={1-tt/24}/>;})}
 </World>
 <div style={{position:'absolute',left:0,top:112,width:1080,display:'flex',justifyContent:'center',zIndex:14}}><div style={{background:CARD[k%3],border:`8px solid ${INK}`,borderRadius:50,padding:'8px 40px',transform:`scale(${.5+.5*lab}) rotate(-2deg)`,boxShadow:`0 8px 0 ${INK}`}}><span style={{fontFamily:'Lilita',fontSize:64,color:INK,whiteSpace:'nowrap'}}>{st.label}</span></div></div>
 {both?<><BigNum v={st.a!} name={c.title[0]} win={w==='a'} t={t-2} x={50} y={236} size={w==='a'?170:120} al="left"/><BigNum v={st.b!} name={c.title[1]} win={w==='b'} t={t-7} x={1030} y={452} size={w==='b'?170:120} al="right"/></>
  :<BigNum v={(st.a??st.b)!} name={c.title[only==='a'?0:1]} win t={t-2} x={540} y={250} size={230} al="center"/>}
 </AbsoluteFill>;
};
const CARD=['#F2A51E','#22A58A','#DE5B4B'];

// ---------------- "Who wins? Comment A or B" ----------------
const Prompt:React.FC<{c:Case;t:number;dur:number;line:Line}>=({c,t,line})=>{
 const f=useCurrentFrame(),bA=Math.round(line.onset*30)+24-line.from,bB=bA+12,lit=(r:Side)=>r==='a'?t>=bA&&t<bB:t>=bB&&t<bB+24;
 const x={a:posOf(c,'a',IDLE-60),b:posOf(c,'b',IDLE-60)},P=(r:Side):PX=>lit(r)?pose('roar',undefined,0,{rear:.6}):pose('idle','charge',.4+.3*Math.sin(t*.3+(r==='a'?0:2)),{stride:0});
 const H=(r:Side)=>headAt(c,r,x[r],P(r),f),foc=lit('a')?'a':lit('b')?'b':null;
 const cam=fitCam(c,x.a,x.b,H('a'),H('b'),1060,1.3,1+.05*t/40,.3);void foc;
 const badge=(r:Side)=>{const h=H(r),sx=540+(h[0]-cam.cx-540)*cam.z*1.03,on=lit(r),s=(.6+.4*pop(t-(r==='a'?2:6)))*(on?1.25:1);return <div key={r} style={{position:'absolute',left:r==='a'?120+0*sx:740,top:470,width:220,height:220,borderRadius:110,background:r==='a'?GOLD:TEAL,border:`12px solid ${on?'#FFFFFF':INK}`,boxShadow:`0 12px 0 ${INK}`,display:'flex',alignItems:'center',justifyContent:'center',transform:`scale(${s}) rotate(${r==='a'?-6:6}deg)`,zIndex:13}}><span style={{fontFamily:'Lilita',fontSize:170,color:INK}}>{r.toUpperCase()}</span></div>;};
 return <AbsoluteFill><World c={c} cam={cam} sh={foc?3:0}><B c={c} r="a" x={x.a} p={P('a')} t={f}/><B c={c} r="b" x={x.b} p={P('b')} t={f+17}/></World>
  <AbsoluteFill style={{background:'linear-gradient(rgba(45,42,58,.92) 0%,rgba(45,42,58,.75) 30%,rgba(45,42,58,0) 60%)'}}/>
  <div style={{...txt,position:'absolute',left:0,top:150,width:1080,fontSize:156,color:GOLD,transform:`scale(${.5+.5*pop(t)}) rotate(-3deg)`,zIndex:12}}>WHO WINS?</div>
  {badge('a')}{badge('b')}
 </AbsoluteFill>;
};

// ---------------- clash ----------------
type Dist={a:number;b:number};
type St={d:Dist;y?:Partial<Dist>;p:{a:PX;b:PX};sq?:Partial<Dist>;tilt?:Partial<Dist>;ghost?:{a?:Pt;b?:Pt};face?:{a?:Side;b?:Side};front:Side;fx?:React.ReactNode;word?:React.ReactNode;emote?:[string,Side];snap?:number;pre?:number;sh?:number;imp?:number;impAt?:Pt;big?:boolean;victim?:Side};
const endDist=(s:Shot,d0:Dist):Dist=>{const w=s.who??'a',o=other(w),d={...d0};
 if(s.s==='charge')d[w]=20;else if(s.s==='strike')d[o]=d0[o]+90;else if(s.s==='impact'){if(s.tank)d[w]=-d0[o]+170;else{d[w]=-d0[o];if(!s.pin)d[o]=d0[o]+220;}}else if(s.s==='retreat')d[w]=d0[w]+150;return d;};
const arc=(u:number)=>Math.sin(Math.PI*clamp01(u));
const land=(t:number)=>t<0?0:-.1*Math.sin(Math.PI*clamp01(t/9));   // landing squash that eases in (an instant squash reads as a jump cut)
const shotState=(c:Case,s:Shot,T:number,D:number,d0:Dist):St=>{
 const w=s.who??'a',o=other(w),dw=dirOf(w),d={...d0},e=endDist(s,d0);
 const P2=(pw:PX,po:PX)=>(w==='a'?{a:pw,b:po}:{b:pw,a:po}) as St['p'];
 const one=<V,>(r:Side,v:V)=>({[r]:v}) as Partial<Record<Side,V>>;
 const xw=()=>posOf(c,w,d[w]),xo=()=>posOf(c,o,d[o]);
 if(s.s==='charge'){const L=CH.charge.launch,an=clamp01(T/L),go=clamp01((T-L)/(D-L));d[w]=d0[w]+40*ease(an)-(d0[w]+40-e[w])*go*go;
  const pw=T<L?pose('idle','dodge',an,{brow:1}):pose('charge'),ro=kf(T,[[D*.5,0],[D*.62,1]]);
  return {d,p:P2(pw,pose('idle','roar',ro,{rear:.3*ro})),sq:one(w,T<L?-.12*an:(.1*Math.min(1,(T-L)/3)-.12*Math.max(0,1-(T-L)/3))*Math.exp(-(T-L)/6)) as St['sq'],ghost:one(w,T>=L+2?[dw*Math.min(70,(T-L-2)*18),0] as Pt:undefined) as St['ghost'],front:w,sh:T>=L?3:0,victim:o,
   fx:<>{T>=L&&<g opacity={clamp01((T-L)/5)}><Speed t={T} dir={dw} x0={xw()-900} y0={GROUND-560} y1={GROUND-30}/></g>}{[0,6,12,18,24,30,36,42].map(k=><Dust key={k} c={c} x={posOf(c,w,d0[w]+40-(d0[w]+40-e[w])*clamp01((k)/(D-L))**2)-dw*170} t={T-L-k} n={3} s={.8} dir={-dw} life={18}/>)}<Debris c={c} x={xw()-dw*200} t={T-L} n={6} s={.6}/></>};}
 if(s.s==='rear'){const up=kf(T,[[0,0],[5,-.25],[CH.rear.up,1]]),r=Math.max(0,up),sk=clamp01(T/10);if(d0[o]<70)d[o]=d0[o]+(70-d0[o])*ease(sk);
  return {d,p:P2(pose('idle','roar',r,{rear:r,crouch:up<0?-up*1.6:0,swipe:0}),pose('charge','dodge',sk,{stride:1-sk})),sq:{[w]:up<0?up*.3:.1*Math.exp(-(T-CH.rear.up)/5)*(T>=CH.rear.up?1:0),[o]:-.08*arc(sk)} as St['sq'],front:w,sh:T>=CH.rear.up&&T<CH.rear.up+8?8:2,victim:o,
   fx:<><Dust c={c} x={xo()+dw*150} t={T-2} n={5} dir={dw}/><Dust c={c} x={xw()} t={T-CH.rear.up+2} n={4} s={.7} dir={-dw}/></>};}
 if(s.s==='strike'){const hit=CH.strike.hit,dn=kf(T,[[3,0],[hit,1]]),rec=kf(T,[[hit+10,0],[D,1]]),hop=clamp01((T-2)/(hit+1));
  d[w]=d0[w]-80*dn*(1-rec);d[o]=d0[o]+90*ease(hop);const ix=posOf(c,w,d0[w]-80-GEO[kindOf(c,w)].reach*GEO[kindOf(c,w)].sc*.9);
  const pw=pose('roar','idle',rec,{rear:(1-dn)*(1-rec),strike:dn*(1-rec),swipe:dn*(1-rec),jaw:1-rec});
  return {d,y:one(o,60*arc(hop)) as St['y'],p:P2(pw,pose('dodge',undefined,0,{squeeze:T>=hit&&T<hit+5?1:0})),sq:{[w]:T>=hit?-.1*Math.exp(-(T-hit)/4):.08*dn,[o]:hop<1?.1*arc(hop):land(T-hit-1)} as St['sq'],
   ghost:one(w,T>3&&T<hit?[dw*60,70] as Pt:undefined) as St['ghost'],front:w,sh:T>=hit&&T<hit+14?15*(1-(T-hit)/14):0,snap:T>=hit?Math.exp(-(T-hit)/5):0,pre:T<hit?dn:0,imp:T-hit,impAt:[ix,GROUND-40],victim:o,
   fx:<><Ring x={ix} t={T-hit}/><Debris c={c} x={ix} t={T-hit} n={14}/><Dust c={c} x={ix} t={T-hit} n={6} s={1.3} dir={1}/><Dust c={c} x={ix} t={T-hit} n={6} s={1.3} dir={-1}/><Dust c={c} x={xo()} t={T-hit-1} n={4} s={.7} dir={dw}/></>,
   word:<Word t={T-hit} text="MISS!" y={430} color={PAPER} size={170}/>};} // no 'bang' emote: its "!" landed on MISS! and clipped the top edge (bc004 v3 sheets f392-432)
 if(s.s==='impact'){const hit=CH.impact.hit,ct=Math.round(D*CH.impact.counter),ap=clamp01(T/hit),gapx=d0[w]+d0[o];d[w]=d0[w]-gapx*ap*ap;
  const kw=kindOf(c,w),ko=kindOf(c,o),ix=posOf(c,o,d0[o]-20),iy=GROUND-GEO[ko].top*GEO[ko].sc*.5;
  if(s.tank){const bo=kf(T,[[hit,0],[hit+10,1]]),fl=clamp01((T-ct)/11),an=kf(T,[[ct-9,0],[ct-2,1],[ct,0]]),lun=kf(T,[[ct-5,0],[ct,1],[ct+12,0]]);
   d[w]=T<hit?d[w]:-d0[o]+70*bo+100*(1-(1-fl)*(1-fl));d[o]=d0[o]+30*an-70*lun;
   const po=T<hit?pose('idle','charge',ap,{stride:0,grit:1}):T<ct-9?pose('charge','win',clamp01((T-hit-6)/8),{stride:0,rear:0}):pose('win','charge',Math.max(an,lun),{stride:0,crouch:.5*an,strike:lun,rear:.3*an});
   const pw=T<hit?pose('charge'):T<ct?pose('hit','tired',clamp01((T-hit-8)/10)):pose('tired','hit',clamp01((T-ct+1)/4),{sweat:1});
   return {d,y:one(w,T>=ct?80*arc(fl):30*arc(bo)) as St['y'],p:P2(pw,po),tilt:one(w,T>=ct?-22*arc(fl)*1:-8*arc(bo)) as St['tilt'],
    sq:{[o]:T>=hit&&T<ct-9?-.14*Math.exp(-(T-hit)/7)*Math.cos((T-hit)*.95):T>=ct?.08*Math.exp(-(T-ct)/4):-.1*an,[w]:T<hit?.08*ap:T>=ct&&fl>=1?land(T-ct-11):0} as St['sq'],
    ghost:{[w]:T>2&&T<hit?[dw*80,0]:T>=ct+2&&T<ct+7?[-dw*40,-10]:undefined} as St['ghost'],front:T<ct?o:w,
    sh:T>=ct&&T<ct+14?18*(1-(T-ct)/14):T>=hit&&T<hit+12?13*(1-(T-hit)/12):0,snap:T>=ct?Math.exp(-(T-ct)/5):T>=hit?Math.exp(-(T-hit)/5):0,pre:T<hit?ap:T<ct?an:0,imp:T>=ct?T-ct:T-hit,big:false,impAt:[ix,iy],victim:w,
    fx:<><Star x={ix} y={iy} t={T-hit} s={1}/><Dust c={c} x={ix} t={T-hit} n={6} s={1.2} dir={dw}/><Debris c={c} x={ix} t={T-hit} n={8} s={.8}/><Star x={ix-dw*40} y={iy} t={T-ct} s={1.1}/><Ring x={ix} y={iy} t={T-ct} s={.8}/><Debris c={c} x={ix} y={iy+100} t={T-ct} n={12}/><Dust c={c} x={posOf(c,w,d[w])} t={T-ct-11} n={4} s={.8} dir={-dw}/></>,
    word:<><Word t={T-hit} text={w==='a'?'BAM!':'WHAM!'} y={420}/><Word t={T-ct} text={w==='a'?'WHAM!':'BAM!'} y={420} color={RED}/></>,emote:T>=ct+11?['dizzy',w]:undefined};}
  const kb=clamp01((T-hit)/14);if(!s.pin)d[o]=d0[o]+220*(1-(1-kb)*(1-kb));
  const po=T<hit?pose('idle','roar',ap):pose('hit','tired',clamp01((T-hit-16)/14)),pw=T<hit?pose('charge'):s.pin?pose('charge','win',clamp01((T-hit)/8),{rear:.6,jaw:.7,grit:0}):pose('charge','roar',clamp01((T-hit)/10),{rear:.5*clamp01((T-hit)/10)});
  return {d,y:one(o,s.pin?0:70*arc(kb)) as St['y'],p:P2(pw,po),tilt:one(o,s.pin?0:-18*arc(kb)) as St['tilt'],sq:{[w]:T<hit?.08*ap:0,[o]:s.pin?-.15*clamp01((T-hit)/6):kb>=1?land(T-hit-14):0} as St['sq'],
   ghost:one(w,T>2&&T<hit?[dw*80,0] as Pt:undefined) as St['ghost'],front:w,sh:T>=hit&&T<hit+14?17*(1-(T-hit)/14):0,snap:T>=hit?Math.exp(-(T-hit)/5):0,pre:T<hit?ap:0,imp:T-hit,big:true,impAt:[ix,iy],victim:o,
   fx:<><Star x={ix} y={iy} t={T-hit} s={1.8}/><Ring x={ix} y={iy} t={T-hit} s={.8}/><Debris c={c} x={ix} y={iy+100} t={T-hit} n={12}/><Dust c={c} x={posOf(c,o,d[o])} t={T-hit-13} n={6} s={1.2} dir={dw}/></>,
   word:<Word t={T-hit} text={w==='a'?'BAM!':'WHAM!'} y={420}/>};}
 // retreat: the winner (o) lands a finisher ground slam, the loser (w) is blown back, then turns and trudges off
 const sl=CH.retreat.slam,ld=CH.retreat.land,an=kf(T,[[0,0],[5,1]]),up=kf(T,[[4,0],[sl-2,1],[sl,0]]),bl=clamp01((T-sl)/(ld-sl)),walk=clamp01((T-ld-4)/Math.max(1,D-ld-4));
 d[w]=d0[w]+90*(1-(1-bl)*(1-bl))+60*walk;const ix=posOf(c,o,d0[o]-GEO[kindOf(c,o)].reach*GEO[kindOf(c,o)].sc*.8);
 const po=T<sl?pose('idle','roar',up,{crouch:.5*an*(1-up),rear:up}):pose('roar','win',clamp01((T-sl-10)/10),{strike:Math.exp(-(T-sl)/6),jaw:.6+.4*Math.abs(Math.sin(T*.3)),rear:.5*clamp01((T-sl-8)/10)});
 const pw=T<sl?pose('tired','dodge',up):T<ld?pose('hit'):pose('tired',undefined,0,{stride:.4});
 return {d,y:one(w,90*arc(bl)) as St['y'],p:P2(pw,po),tilt:one(w,-20*arc(bl)) as St['tilt'],sq:{[o]:T<sl?.1*up-.1*an*(1-up):-.12*Math.exp(-(T-sl)/4),[w]:land(T-ld)} as St['sq'],
  ghost:one(w,T>=sl&&T<sl+6?[-dw*70,-20] as Pt:undefined) as St['ghost'],face:(T>=ld?{[w]:o}:{}) as St['face'],front:o,sh:T>=sl&&T<sl+16?20*(1-(T-sl)/16):0,snap:T>=sl?Math.exp(-(T-sl)/5):0,pre:T<sl?up:0,imp:T-sl,big:true,impAt:[ix,GROUND-40],victim:w,
  word:<Word t={T-sl} text="CRUNCH!" y={430} color={RED} size={190}/>,
  fx:<><Ring x={ix} t={T-sl} s={1.2}/><Ring x={ix} t={T-sl-4} s={.9}/><Debris c={c} x={ix} t={T-sl} n={16} s={1.2}/><Dust c={c} x={ix} t={T-sl} n={7} s={1.5} dir={1}/><Dust c={c} x={ix} t={T-sl} n={7} s={1.5} dir={-1}/><Dust c={c} x={posOf(c,w,d[w])} t={T-ld} n={3} s={.5} dir={-dw}/><Dust c={c} x={posOf(c,w,d[w])+dw*80} t={(T-ld-8)%20} n={3} s={.6} dir={dw} life={20}/></>};
};
// camera plan per shot: [start fraction, framing]; framings: two, close:<w|o|v>, low:<w|o>
// camera plan per shot, in frames: wind-up close on the attacker, two-shot on the hit, close on the reaction
const planOf=(s:Shot,D:number):[number,string][]=>{const h=CH.impact.hit,ct=Math.round(D*CH.impact.counter);
 return s.s==='charge'?[[0,'low:w']]:s.s==='rear'?[[0,'close:w']]:s.s==='strike'?[[0,'two'],[CH.strike.hit+5,'close:v']]
  :s.s==='impact'?(s.tank?(D>=48?[[0,'two'],[h+5,'close:o'],[ct-7,'two'],[ct+11,'close:v']]:[[0,'two'],[ct+11,'close:v']]):[[0,'two'],[h+5,'close:v']])
  :s.s==='retreat'?[[0,'two'],[CH.retreat.land,'close:v']]:[[0,'two']];};
const TONES=['#F2A51E','#7C5CE0','#22A58A','#DE5B4B'];
const Clash:React.FC<{c:Case;s:Shot;t:number;dur:number;seed:number;d0:Dist}>=({c,s,t,dur,seed,d0})=>{
 const st=shotState(c,s,t,dur,d0),w=s.who??'a',o=other(w),plan=planOf(s,dur);let bi=0;const pf=(v:number)=>v;for(let i=0;i<plan.length;i++)if(t>=pf(plan[i][0]))bi=i;
 const b0=pf(plan[bi][0]),b1=bi+1<plan.length?pf(plan[bi+1][0]):dur,bt=t-b0,u=bt/Math.max(1,b1-b0),[k,who]=plan[bi][1].split(':');
 const r:Side=who==='w'?w:who==='o'?o:who==='v'?(st.victim??o):w,x=(q:Side)=>posOf(c,q,st.d[q]),tq=(q:Side)=>q===st.front?t*1.2:t+7;
 const H=(q:Side)=>headAt(c,q,x(q),st.p[q],tq(q),st.face?.[q],st.y?.[q]??0),push=(1+.06*u)*(1+.14*(st.pre??0)),sn=1+(st.big?.3:.1)*(st.snap??0);
 const G=GEO[kindOf(c,r)],fd=(st.face?.[r]??r)==='a'?1:-1;
 const cam=k==='close'?at([H(r)[0]+fd*20,H(r)[1]+50+0*G.cx],540,900,Math.min(2.6,soloZ(kindOf(c,r))*1.25)*push*Math.min(sn,1.1)):k==='low'?soloCam(c,r,H(r),fd,950,push*Math.min(sn,1.1)):fitCam(c,x('a'),x('b'),H('a'),H('b'),1040,1.55,push*sn,.12);
 const whip=0*seed,imp=st.big&&st.imp!==undefined&&st.imp>=0&&st.imp<4&&st.impAt?{k:st.imp,x:st.impAt[0],y:st.impAt[1],sil:st.big}:null,back=other(st.front);
 const one=(q:Side)=><B key={q} c={c} r={q} x={x(q)} p={st.p[q]} t={tq(q)} y={st.y?.[q]} sq={st.sq?.[q]} ghost={st.ghost?.[q]} face={st.face?.[q]} tilt={st.tilt?.[q]}/>;
 return <AbsoluteFill><World c={c} cam={cam} sh={st.sh} imp={imp} whip={whip} burst={k==='close'?TONES[(seed+bi)%4]:undefined}>{one(back)}{!imp&&st.fx}{one(st.front)}{!imp&&st.emote&&(st.emote[0]==='bang'?<Bang x={H(st.emote[1])[0]} y={H(st.emote[1])[1]-170} t={bt} s={1.2}/>:<Dizzy x={H(st.emote[1])[0]} y={H(st.emote[1])[1]-150} t={t}/>)}</World>{st.word}</AbsoluteFill>;
};

// ---------------- verdict: one line + one image (the winner's hero shot under the stamped heading), then the loop ----------------
const Verdict:React.FC<{c:Case;t:number;dur:number;k:number}>=({c,t,dur,k})=>{
 const w=c.winner,l=other(w),f=useCurrentFrame(),V=c.verdict,head=/HYPOTHETICAL/i.test(V.head)?V.head:'HYPOTHETICAL '+V.head;   // never a bare "WINNER"
 const T=k===0?t:t+90,beat=Math.floor(T/40),bt=T-beat*40,flex=kf(bt,[[0,0],[7,1],[26,1],[38,.3]]);
 const x={[w]:posOf(c,w,60),[l]:posOf(c,l,230+Math.min(140,T*1.2))} as Record<Side,number>;
 const pw=pose('win','roar',flex*.8,{rear:.5+.35*flex,swipe:.5+.5*Math.sin(T*.25)}),pl=pose('tired',undefined,0,{stride:.35});
 const hw=headAt(c,w,x[w],pw,T+5),cam=k===0?soloCam(c,w,hw,dirOf(w),1010,(1+.03*T/90)*(1+.1*Math.exp(-bt/3))):at([hw[0]+dirOf(w)*20,hw[1]+50],540,1040,Math.min(2.6,soloZ(kindOf(c,w))*1.25)*(1+.04*t/Math.max(1,dur)));   // a second verdict line gets its own image: close-up on a colour backdrop
 const txt2=k===0?null:(V.pop2??V.note2??null);
 return <AbsoluteFill><World c={c} cam={cam} sh={bt<8?10*(1-bt/8):0} burst={k===0?undefined:'#7C5CE0'}>
  <g opacity={.5}>{Array.from({length:14}).map((_,i)=>{const a=(i*25.7+f*1.2)*Math.PI/180;return <path key={i} d={`M${hw[0]} ${hw[1]+60}L${hw[0]+Math.cos(a)*1700} ${hw[1]+60+Math.sin(a)*1700}L${hw[0]+Math.cos(a+.16)*1700} ${hw[1]+60+Math.sin(a+.16)*1700}Z`} fill="#FFF3B0"/>;})}</g>
  <B c={c} r={l} x={x[l]} p={pl} t={T} face={w}/>
  <B c={c} r={w} x={x[w]} p={pw} t={T+5} sq={.06*flex}/>
  {bt<30&&<><Ring x={x[w]} t={bt-2} s={1.2}/><Debris c={c} x={x[w]+dirOf(w)*100} t={bt-2} n={12}/></>}
  {Array.from({length:16}).map((_,i)=>{const tt=(T+i*7)%46,a=-Math.PI*(.15+.7*rnd(i));return <path key={i} d="M0 -16L5 -5L16 0L5 5L0 16L-5 5L-16 0L-5 -5Z" fill={i%2?GOLD:'#FFFFFF'} stroke={INK} strokeWidth={3} transform={`translate(${hw[0]+Math.cos(a)*tt*13} ${hw[1]+Math.sin(a)*tt*13+tt*tt*.12}) scale(${1.6-tt/46}) rotate(${tt*9})`} opacity={1-tt/46}/>;})}
 </World>
 <div style={{position:'absolute',left:0,top:112,width:1080,zIndex:15,transform:`scale(${k===0?1.12-.12*pop(t):1}) rotate(-3deg)`}}>
  <div style={{...txt,fontSize:Math.min(96,950/(.62*head.length)),color:PAPER}}>{head}</div>
  <div style={{...txt,fontSize:fit(V.name,190),color:GOLD,marginTop:6,WebkitTextStroke:`16px ${INK}`,textShadow:`8px 10px 0 ${INK}`}}>{V.name}</div></div>
 <div style={{position:'absolute',left:0,top:468,width:1080,display:'flex',justifyContent:'center',zIndex:16}}><div style={{fontFamily:'Quiet Sans',fontWeight:800,fontSize:36,color:PAPER,background:INK,borderRadius:30,padding:'8px 26px',letterSpacing:1}}>{txt2??V.note}</div></div>
 </AbsoluteFill>;
};

// ---------------- frame ----------------
// one size for every caption: captions.py keeps each caption <= 18 characters, which fits 1020 px at CAP_FONT
const CAP_FONT=92;
const Caption:React.FC<{text:string}>=({text})=>{const s=text.replace(/\n/g,' '),fs=Math.min(CAP_FONT,1000/(.58*s.length));return <div data-narration style={{...txt,fontFamily:'Quiet Sans',fontWeight:800,position:'absolute',left:30,top:1330,width:1020,height:170,display:'flex',alignItems:'center',justifyContent:'center',fontSize:fs,lineHeight:1,WebkitTextStroke:`15px ${INK}`,zIndex:30,whiteSpace:'nowrap'}}>{s}</div>;};
export const Film:React.FC<{c:Case;cover?:boolean}>=({c,cover})=>{
 const f=useCurrentFrame();
 if(!c||!c.lines)return null;
 if(cover)return <AbsoluteFill><FaceOff c={c} t={22} title={1} big/><div style={{...txt,position:'absolute',left:0,top:1330,width:1080,fontSize:150,color:GOLD,transform:'rotate(-4deg)',zIndex:30}}>WHO WINS?</div></AbsoluteFill>;
 const L=c.lines,u=L.find(x=>f>=x.from&&f<x.from+x.dur)??L[L.length-1],t=f-u.from;
 let scene:React.ReactNode=null;
 if(u.mode==='face')scene=<FaceOff c={c} t={t} title={1}/>;
 else if(u.mode==='loop')scene=<FaceOff c={c} t={t-u.dur} title={clamp01((t-u.dur+16)/8)}/>;
 else if(u.mode==='stat')scene=<StatScene c={c} k={u.k??0} t={t} dur={u.dur}/>;
 else if(u.mode==='prompt')scene=<Prompt c={c} t={t} dur={u.dur} line={u}/>;
 else if(u.mode==='verdict')scene=<Verdict c={c} t={t} dur={u.dur} k={u.k??0}/>;
 else if(u.mode==='clash'){let d:Dist={a:IDLE,b:IDLE},hit:React.ReactNode=null;
  for(const ln of L){if(ln.mode!=='clash')continue;const sh=ln.shots??[{s:'charge'}],n=sh.length,seg=Math.floor(ln.dur/n);
   for(let i=0;i<n;i++){if(ln===u&&i===Math.min(n-1,Math.floor(t/seg))){hit=<Clash c={c} s={sh[i]} t={t-i*seg} dur={i===n-1?ln.dur-i*seg:seg} seed={L.indexOf(u)+i} d0={d}/>;break;}d=endDist(sh[i],d);}
   if(hit)break;}
  scene=hit;}
 const sec=f/30,cue=c.subs.find(s=>sec>=s.s&&sec<s.e);
 return <AbsoluteFill style={{background:INK}}>{scene}{cue&&<Caption text={cue.text}/>}</AbsoluteFill>;
};
