// Channel branding kits (profile picture, banner, watermark, preview board) in the B-format thick-outline toon style.
// Characters come from the b_format rig (Guy); animals are original drawings in the same outline language.
import React from 'react';
import {AbsoluteFill,Img,continueRender,delayRender,staticFile} from 'remotion';
import {Guy,OL} from '../../episodes/quiz/batch_1107/b_format/FightRig';

export type Ch='gts'|'nnd'|'bcl'|'chk';
const INK=OL,YEL='#FFC93C',RED='#E8412F',WHITE='#FFF8EC';
const SW=14;

let fontsP:Promise<void>|null=null;
const useFonts=()=>{const [h]=React.useState(()=>delayRender('fonts'));
 React.useEffect(()=>{fontsP??=Promise.all([['BrandEN','NotoSans-VF.ttf'],['BrandJP','NotoSansJP-VF.ttf']].map(async([fam,file])=>{
  const ff=await new FontFace(fam,`url(${staticFile('fonts/'+file)})`,{weight:'100 900'}).load();document.fonts.add(ff);})).then(()=>undefined);
  fontsP.then(()=>continueRender(h));},[h]);};
const EN="'BrandEN', sans-serif",JP="'BrandJP', sans-serif";

// outlined text drawn with SVG so the stroke sits behind the fill
const T:React.FC<{x:number;y:number;size:number;fill:string;stroke?:string;sw?:number;font?:string;weight?:number;anchor?:'start'|'middle'|'end';ls?:number;children:React.ReactNode;skew?:number}>=
 ({x,y,size,fill,stroke=INK,sw=0,font=EN,weight=900,anchor='middle',ls=0,children,skew=0})=>
 <text x={x} y={y} fontSize={size} fill={fill} stroke={stroke} strokeWidth={sw} strokeLinejoin="round" paintOrder="stroke" fontFamily={font} fontWeight={weight}
  textAnchor={anchor} letterSpacing={ls} transform={skew?`skewX(${skew})`:undefined} style={{transformBox:'fill-box',transformOrigin:'center'}}>{children}</text>;

// ---------- props ----------
// gavel lying along +x, head at origin; rot rotates around the head
export const Gavel:React.FC<{x:number;y:number;s:number;rot:number}>=({x,y,s,rot})=>
 <g transform={`translate(${x} ${y}) rotate(${rot}) scale(${s})`} stroke={INK} strokeWidth={SW/s*s} strokeLinejoin="round" strokeLinecap="round">
  <rect x={40} y={-16} width={250} height={32} rx={16} fill="#B5713A"/>
  <rect x={-90} y={-62} width={180} height={124} rx={26} fill="#8A4F25"/>
  <rect x={-112} y={-70} width={40} height={140} rx={14} fill="#C98A4E"/>
  <rect x={72} y={-70} width={40} height={140} rx={14} fill="#C98A4E"/>
  <path d="M-60 -40H50" stroke="#B5713A" strokeWidth={10} fill="none"/>
 </g>;
const Block:React.FC<{x:number;y:number;s:number}>=({x,y,s})=><g transform={`translate(${x} ${y}) scale(${s})`} stroke={INK} strokeWidth={SW} strokeLinejoin="round">
 <rect x={-130} y={-34} width={260} height={56} rx={18} fill="#8A4F25"/><rect x={-100} y={-62} width={200} height={34} rx={12} fill="#B5713A"/></g>;
const Spark:React.FC<{x:number;y:number;s:number;rot?:number;color?:string}>=({x,y,s,rot=0,color=WHITE})=><g transform={`translate(${x} ${y}) rotate(${rot}) scale(${s})`} stroke={INK} strokeWidth={10} strokeLinejoin="round">
 <path d="M0 -60L14 -14L60 0L14 14L0 60L-14 14L-60 0L-14 -14Z" fill={color}/></g>;

// ---------- animals (original designs), drawn facing +x ----------
const spikes=(n:number,r1:number,r2:number,cx=0,cy=0)=>Array.from({length:n*2},(_,i)=>{const a=Math.PI*i/n,r=i%2?r2:r1;return `${i?'L':'M'}${(cx+r*Math.cos(a)).toFixed(1)} ${(cy+r*Math.sin(a)).toFixed(1)}`;}).join('')+'Z';
export const Lion:React.FC<{x:number;y:number;s:number;flip?:boolean;body?:boolean}>=({x,y,s,flip,body})=>
 <g transform={`translate(${x} ${y}) scale(${flip?-s:s} ${s})`} stroke={INK} strokeWidth={SW} strokeLinejoin="round" strokeLinecap="round">
  {body&&<path d="M-150 120Q-170 260 -190 420H170Q150 250 110 130Z" fill="#E9A13B"/>}
  {body&&<path d="M-40 200Q0 300 60 420" fill="none" stroke="#C47A22" strokeWidth={10}/>}
  <path d={spikes(13,175,140,-25,0)} fill="#B8521C"/>
  <ellipse cx={-10} cy={-120} rx={36} ry={34} fill="#E9A13B"/><ellipse cx={-10} cy={-118} rx={16} ry={15} fill="#C47A22" strokeWidth={0}/>
  <ellipse cx={20} cy={5} rx={112} ry={118} fill="#F2B33D"/>
  <ellipse cx={95} cy={52} rx={68} ry={50} fill="#FCE6B5"/>
  <path d="M120 10Q150 0 168 18Q160 44 134 48Q112 40 120 10Z" fill="#3A2418"/>
  <path d="M136 50V72M100 92Q136 106 166 84" fill="none"/>
  <path d="M104 98L112 122L122 100Z" fill="#FFFFFF" strokeWidth={8}/>
  <ellipse cx={60} cy={-30} rx={30} ry={34} fill="#FFFFFF"/><circle cx={74} cy={-26} r={11} fill={INK} stroke="none"/>
  <path d="M20 -78L98 -58" fill="none" strokeWidth={18}/>
 </g>;
export const Rhino:React.FC<{x:number;y:number;s:number;flip?:boolean;body?:boolean}>=({x,y,s,flip,body})=>
 <g transform={`translate(${x} ${y}) scale(${flip?-s:s} ${s})`} stroke={INK} strokeWidth={SW} strokeLinejoin="round" strokeLinecap="round">
  {body&&<path d="M-200 40Q-230 250 -230 420H160Q150 250 80 110Z" fill="#7F8A9C"/>}
  {body&&<path d="M-150 160Q-110 220 -120 300M-60 220Q-40 300 -60 380" fill="none" stroke="#66707F" strokeWidth={10}/>}
  <path d="M-150 -40Q-140 -120 -40 -120Q70 -120 150 -40Q200 0 196 60Q190 120 120 130Q20 140 -80 130Q-170 110 -170 40Z" fill="#949FB1"/>
  <path d="M150 -26Q170 -120 150 -210Q200 -140 214 -20Z" fill="#EFE5CF"/>
  <path d="M70 -96Q80 -140 70 -172Q104 -130 112 -86Z" fill="#EFE5CF"/>
  <path d="M-110 -100Q-150 -190 -96 -200Q-70 -150 -66 -110Z" fill="#949FB1"/><path d="M-100 -130Q-110 -170 -96 -182" fill="none" strokeWidth={8}/>
  <path d="M182 50Q190 64 176 72" fill="none" strokeWidth={10}/>
  <path d="M110 108Q150 100 172 90" fill="none" strokeWidth={10}/>
  <path d="M-40 10Q-30 60 -60 90M-90 -20Q-80 40 -110 70" fill="none" stroke="#748094" strokeWidth={10}/>
  <ellipse cx={40} cy={-30} rx={27} ry={30} fill="#FFFFFF"/><circle cx={53} cy={-27} r={10} fill={INK} stroke="none"/>
  <path d="M6 -70L80 -52" fill="none" strokeWidth={18}/>
 </g>;

// ---------- characters from the rig ----------
const Char:React.FC<{look:any;x:number;y:number;s:number;expr:any;pose?:any;flip?:boolean;eye?:[number,number]}>=(p)=>
 <Guy look={p.look} x={p.x} y={p.y} scale={p.s} expr={p.expr} pose={p.pose??'stand'} flip={p.flip} eye={p.eye??[0,0]} wobble={0}/>;

// ---------- palettes ----------
const PAL:Record<Ch,{bg:string;disc:string;accent:string}>={
 gts:{bg:'#18203A',disc:YEL,accent:RED},
 nnd:{bg:'#2A1416',disc:'#D7263D',accent:YEL},
 bcl:{bg:'#14182A',disc:YEL,accent:RED},
 chk:{bg:'#14182A',disc:YEL,accent:RED},
};

// ---------- profile pictures (800x800, mark kept inside the circle crop) ----------
const Burst:React.FC<{cx:number;cy:number;r:number;color:string;n?:number}>=({cx,cy,r,color,n=18})=>
 <g>{Array.from({length:n},(_,i)=>{const a=2*Math.PI*i/n,b=a+Math.PI/n;return <path key={i} d={`M${cx} ${cy}L${cx+r*Math.cos(a)} ${cy+r*Math.sin(a)}L${cx+r*Math.cos(b)} ${cy+r*Math.sin(b)}Z`} fill={color}/>;})}</g>;
export const Mark:React.FC<{ch:Ch;size?:number}>=({ch,size=800})=>{
 const P=PAL[ch];
 return <svg width={size} height={size} viewBox="0 0 800 800">
  <rect width={800} height={800} fill={P.bg}/>
  {ch==='gts'&&<g>
   <Burst cx={400} cy={400} r={600} color="#202A4A"/>
   <circle cx={400} cy={400} r={330} fill={P.disc} stroke={INK} strokeWidth={18}/>
   <T x={430} y={590} size={560} fill={RED} sw={30}>?</T>
   <Gavel x={300} y={480} s={1.15} rot={-150}/>
  </g>}
  {ch==='nnd'&&<g>
   <Burst cx={400} cy={400} r={600} color="#3A1C1F"/>
   <circle cx={400} cy={400} r={340} fill={P.disc} stroke={INK} strokeWidth={18}/>
   <Gavel x={470} y={235} s={0.72} rot={-200}/>
   <T x={408} y={515} size={200} fill={WHITE} sw={24} font={JP} ls={-16}>何年？</T>
  </g>}
  {ch==='bcl'&&<g>
   <path d="M0 0H470L330 800H0Z" fill="#F07A1A"/><path d="M470 0H800V800H330Z" fill="#2E66E8"/>
   <path d="M470 0L330 800" stroke={INK} strokeWidth={16}/>
   <Lion x={205} y={380} s={0.95}/>
   <Rhino x={640} y={410} s={0.95} flip/>
   <g transform="rotate(-8 400 560)"><T x={400} y={650} size={250} fill={YEL} sw={30} skew={-10}>VS</T></g>
  </g>}
 </svg>;
};
export const PFP:React.FC<{ch:Ch}>=({ch})=>{useFonts();return <AbsoluteFill><Mark ch={ch}/></AbsoluteFill>;};

// ---------- watermark (150x150, transparent) ----------
export const WM:React.FC<{ch:Ch}>=({ch})=>{useFonts();
 return <AbsoluteFill>
  <div style={{position:'absolute',left:6,top:6,width:126,height:126,borderRadius:63,overflow:'hidden',border:`6px solid ${WHITE}`,boxSizing:'border-box'}}><Mark ch={ch} size={114}/></div>
  <svg width={150} height={150} style={{position:'absolute'}}><circle cx={114} cy={114} r={30} fill="#E62117" stroke={WHITE} strokeWidth={6}/>
   <path d="M114 99V129M99 114H129" stroke={WHITE} strokeWidth={9} strokeLinecap="round"/></svg>
 </AbsoluteFill>;};

// ---------- banners (2560x1440; safe area 1546x423 at 507,508.5) ----------
const SX=507,SY=508,SWD=1546,SH=424,CX=1280;
const CourtBG:React.FC<{tint:string;wood:string;woodDark:string}>=({tint,wood,woodDark})=><svg width={2560} height={1440} style={{position:'absolute'}}>
 <defs><radialGradient id="spot" cx="50%" cy="50%" r="55%"><stop offset="0" stopColor={tint} stopOpacity={1}/><stop offset="1" stopColor="#0C0F1A" stopOpacity={1}/></radialGradient>
 <linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stopColor={wood}/><stop offset="1" stopColor={wood} stopOpacity={0}/></linearGradient>
 <linearGradient id="fadeR" x1="1" x2="0"><stop offset="0" stopColor={wood}/><stop offset="1" stopColor={wood} stopOpacity={0}/></linearGradient></defs>
 <rect width={2560} height={1440} fill="url(#spot)"/>
 <rect x={0} width={760} height={1440} fill="url(#fadeL)"/><rect x={1800} width={760} height={1440} fill="url(#fadeR)"/>
 {[60,190,320,450,2110,2240,2370,2500].map(x=><rect key={x} x={x-18} y={0} width={36} height={1440} fill={woodDark} opacity={.55}/>)}
 <rect x={0} y={1180} width={2560} height={260} fill={woodDark} opacity={.7}/><rect x={0} y={1172} width={2560} height={18} fill={INK} opacity={.6}/>
</svg>;
const Pill:React.FC<{x:number;y:number;w:number;h:number;fill:string;text:string;color:string;size:number;font?:string}>=({x,y,w,h,fill,text,color,size,font=EN})=>
 <g><rect x={x-w/2} y={y-h/2} width={w} height={h} rx={h/2} fill={fill} stroke={INK} strokeWidth={8}/>
  <T x={x} y={y+size*.36} size={size} fill={color} font={font} weight={900} ls={font===EN?2:0}>{text}</T></g>;
const Bench:React.FC<{x:number;y:number;w:number;wood:string;trim:string;label:string;font:string}>=({x,y,w,wood,trim,label,font})=><g stroke={INK} strokeWidth={10} strokeLinejoin="round">
 <rect x={x-w/2} y={y} width={w} height={1440-y+20} fill={wood}/><rect x={x-w/2-16} y={y-14} width={w+32} height={30} rx={8} fill={trim}/>
 <rect x={x-w/2+24} y={y+34} width={w-48} height={52} rx={8} fill="#F6EEDC"/>
 <T x={x} y={y+72} size={34} fill={INK} font={font} weight={900} ls={font===EN?3:2}>{label}</T></g>;
const Paper:React.FC<{x:number;y:number;rot:number;s?:number}>=({x,y,rot,s=1})=><g transform={`translate(${x} ${y}) rotate(${rot}) scale(${s})`} stroke={INK} strokeWidth={8}>
 <rect x={-60} y={-80} width={120} height={160} rx={8} fill="#F6EEDC"/><path d="M-36 -44H36M-36 -14H36M-36 16H20" stroke="#B9AE98" strokeWidth={8}/></g>;

export const Banner:React.FC<{ch:Ch}>=({ch})=>{useFonts();
 if(ch==='bcl')return <BannerBeast/>;
 const jp=ch==='nnd';
 return <AbsoluteFill style={{background:'#0C0F1A'}}>
  <CourtBG tint={jp?'#3B1C22':'#22305A'} wood={jp?'#5A2A22':'#4A3020'} woodDark={jp?'#3A1812':'#2E1D12'}/>
  {/* TV / desktop-only decoration, outside the safe area */}
  <svg width={2560} height={1440} style={{position:'absolute'}}>
   <Paper x={330} y={300} rot={-14}/><Paper x={2250} y={260} rot={12}/><Paper x={2300} y={1100} rot={-8} s={.9}/>
   <Block x={360} y={1150} s={1.2}/><Gavel x={420} y={1040} s={1.3} rot={-160}/>
   <Spark x={260} y={720} s={.7} color={YEL}/><Spark x={2330} y={700} s={.8} color={YEL}/>
   <T x={2220} y={1060} size={420} fill={jp?'#D7263D':RED} sw={24} weight={900}>?</T>
  </svg>
  {/* safe area */}
  <Char look="judge" x={SX+150} y={SY+SH+100} s={0.7} expr="serious" pose="bust" eye={[3,0]}/>
  <Char look="D" x={SX+SWD-150} y={SY+SH+100} s={0.7} expr="scared" pose="bust" flip eye={[-3,0]}/>
  <svg width={2560} height={1440} style={{position:'absolute'}}>
   <Bench x={SX+150} y={SY+330} w={330} wood={jp?'#6A2E22':'#7A4A26'} trim={YEL} label={jp?'裁判官':'JUDGE'} font={jp?JP:EN}/>
   <Bench x={SX+SWD-150} y={SY+330} w={300} wood={jp?'#5A3A2E':'#5E4A3A'} trim="#B9AE98" label={jp?'被告人':'DEFENDANT'} font={jp?JP:EN}/>
  </svg>
  <svg width={2560} height={1440} style={{position:'absolute'}}>
   {!jp&&<>
    <T x={CX} y={SY+92} size={82} fill={WHITE} sw={14} ls={6}>GUESS THE</T>
    <T x={CX} y={SY+232} size={150} fill={YEL} sw={20} ls={2}>SENTENCE<tspan fill={RED}>?</tspan></T>
    <T x={CX} y={SY+300} size={37} fill={WHITE} sw={0} weight={700}>Real US cases. Guess the sentence. Then the twist.</T>
    <Pill x={CX} y={SY+370} w={560} h={68} fill={RED} text="NEW VERDICT QUIZ" color={WHITE} size={34}/>
   </>}
   {jp&&<>
    <Pill x={CX} y={SY+50} w={300} h={64} fill={YEL} text="判決クイズ" color={INK} size={38} font={JP}/>
    <T x={CX} y={SY+236} size={170} fill={WHITE} sw={22} font={JP} ls={4}>何年出る<tspan fill={YEL}>？</tspan></T>
    <T x={CX} y={SY+306} size={42} fill={WHITE} sw={0} font={JP} weight={700}>実際の事件、判決を当てろ！</T>
    <Pill x={CX} y={SY+372} w={420} h={66} fill="#D7263D" text="新作クイズ更新中" color={WHITE} size={36} font={JP}/>
   </>}
  </svg>
 </AbsoluteFill>;};

const BannerBeast:React.FC=()=><AbsoluteFill style={{background:'#14182A'}}>
 <svg width={2560} height={1440} style={{position:'absolute'}}>
  <path d="M0 0H1420L1140 1440H0Z" fill="#F07A1A"/><path d="M1420 0H2560V1440H1140Z" fill="#2E66E8"/>
  <Burst cx={1280} cy={720} r={1800} color="rgba(255,255,255,.07)" n={40}/>
  <path d="M1420 0L1140 1440" stroke={INK} strokeWidth={20}/>
  <rect x={SX+300} y={SY+20} width={SWD-600} height={SH-40} rx={40} fill="#14182A" stroke={INK} strokeWidth={12} opacity={.92}/>
  <Spark x={300} y={360} s={1} color={YEL}/><Spark x={2280} y={1080} s={1.1} color={YEL}/><Spark x={2200} y={320} s={.6}/><Spark x={380} y={1100} s={.6}/>
  {/* TV-only full bodies */}
  <Lion x={250} y={1150} s={1.1} body/><Rhino x={2340} y={1180} s={1.1} flip body/>
  {/* safe area: busts + title */}
  <Lion x={SX+205} y={SY+250} s={.88}/><Rhino x={SX+SWD-180} y={SY+270} s={.9} flip/>
  <g transform={`rotate(-3 ${CX} ${SY+200})`}><T x={CX} y={SY+170} size={140} fill={YEL} sw={22} skew={-10} ls={4}>BEAST CLASH</T></g>
  <T x={CX} y={SY+258} size={40} fill={WHITE} sw={0} weight={700}>Animal stats. Who wins? Watch the clash.</T>
  <Pill x={CX} y={SY+336} w={560} h={66} fill={RED} text="NEW ANIMAL SHOWDOWNS" color={WHITE} size={34}/>
 </svg>
</AbsoluteFill>;

// ---------- preview board (raster assets downscaled by the browser) ----------
export const Board:React.FC<{ch:Ch;handle:string}>=({ch,handle})=>{useFonts();
 const a=(f:string)=>staticFile(`assets/${ch}_${f}.png`),k=0.5,bw=2560*k,bh=1440*k,ox=60,oy=1030;
 const rect=(w:number,h:number,c:string,label:string,ly:number)=><div style={{position:'absolute',left:ox+(bw-w*k)/2,top:oy+(bh-h*k)/2,width:w*k,height:h*k,border:`4px dashed ${c}`,boxSizing:'border-box'}}>
  <div style={{position:'absolute',left:6,top:h*k+4+ly,color:c,font:`700 22px ${EN}`,background:'rgba(0,0,0,.6)',padding:'2px 8px'}}>{label}</div></div>;
 const lab=(x:number,y:number,t:string)=><div style={{position:'absolute',left:x,top:y,font:`700 26px ${EN}`,color:'#333'}}>{t}</div>;
 return <AbsoluteFill style={{background:'#EEECE6'}}>
  <div style={{position:'absolute',left:60,top:30,font:`900 44px ${EN}`,color:'#111'}}>@{handle} — branding preview</div>
  {lab(60,110,'profile 800')}<Img src={a('pfp')} style={{position:'absolute',left:60,top:150,width:800,height:800,borderRadius:400}}/>
  {lab(920,110,'98 px')}<Img src={a('pfp')} style={{position:'absolute',left:920,top:150,width:98,height:98,borderRadius:49}}/>
  {lab(1060,110,'48 px')}<Img src={a('pfp')} style={{position:'absolute',left:1060,top:150,width:48,height:48,borderRadius:24}}/>
  <div style={{position:'absolute',left:920,top:280,width:420,height:120,background:'#0F0F0F',borderRadius:12}}>
   <Img src={a('pfp')} style={{position:'absolute',left:16,top:36,width:48,height:48,borderRadius:24}}/>
   <div style={{position:'absolute',left:76,top:34,font:`600 22px ${ch==='nnd'||ch==='chk'?JP:EN}`,color:'#fff'}}>{ch==='gts'?'Guess The Sentence':ch==='nnd'?'何年出る 判決クイズ':ch==='chk'?'철컹철컹':'Beast Clash'}</div>
   <div style={{position:'absolute',left:76,top:64,font:`400 18px ${EN}`,color:'#aaa'}}>@{handle} · dark mode 48 px</div></div>
  <div style={{position:'absolute',left:920,top:420,width:420,height:120,background:'#fff',borderRadius:12,border:'2px solid #ddd'}}>
   <Img src={a('pfp')} style={{position:'absolute',left:16,top:36,width:48,height:48,borderRadius:24}}/>
   <div style={{position:'absolute',left:76,top:44,font:`400 18px ${EN}`,color:'#555'}}>light mode 48 px</div></div>
  {lab(1400,110,'watermark 150 / 60')}<div style={{position:'absolute',left:1400,top:150,width:400,height:240,background:'#5C6B7A'}}>
   <Img src={a('wm')} style={{position:'absolute',left:20,top:40,width:150,height:150}}/><Img src={a('wm')} style={{position:'absolute',left:240,top:130,width:60,height:60}}/></div>
  {lab(1400,430,'mobile crop (safe area 1546×423) at 50%')}
  <div style={{position:'absolute',left:1400,top:470,width:1546*k,height:423*k,overflow:'hidden',border:'2px solid #999'}}>
   <Img src={a('banner')} style={{position:'absolute',left:-507*k,top:-508.5*k,width:bw,height:bh}}/></div>
  {lab(1400,700,'desktop crop (2560×423) at 25%')}
  <div style={{position:'absolute',left:1400,top:740,width:640,height:423/4,overflow:'hidden',border:'2px solid #999'}}>
   <Img src={a('banner')} style={{position:'absolute',left:0,top:-508.5/4,width:640,height:360}}/></div>
  {lab(ox,oy-40,'banner 2560×1440 (TV = full) at 50% with crop overlays')}
  <Img src={a('banner')} style={{position:'absolute',left:ox,top:oy,width:bw,height:bh}}/>
  {rect(2560,423,'#00C2FF','desktop 2560×423',0)}{rect(1855,423,'#FFD400','tablet 1855×423',36)}{rect(1546,423,'#FF2D55','safe / mobile 1546×423',72)}
 </AbsoluteFill>;};
