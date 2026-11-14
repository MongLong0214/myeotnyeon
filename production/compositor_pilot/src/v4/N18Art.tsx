import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFonts} from '../fonts';

// Stage 2a: original SVG sets, uniform silhouettes and light. No image assets.
// Light belongs to space, shared by every role. No training is acted out.
// Owner direction supersedes Stage 1's neutral tokens and restricted red light.
loadFonts();
const C = {ink:'#03040b', blue:'#1a2cff', red:'#ff1e3c', pink:'#ff2a7a', white:'#edeff3', grey:'#a6adc3', yellow:'#f2d45c', green:'#b1e8bd'};
const ease = Easing.bezier(.33,0,.2,1);
type Kind = 'opening' | 'spatial' | 'verdict';
const progress = (seconds:number, from=0, to=5) => interpolate(seconds,[from,to],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:ease});
const useShot = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const seconds = frame/fps;
  return {frame,seconds,push:progress(seconds)};
};
// Eight head heights, distinct boot toes, knees, cuffs, collar, cap and pockets.
const body = 'M-14-236 Q-15-253 0-254 Q15-253 14-236 L14-226 Q13-218 7-215 L7-208 L28-202 Q37-199 40-188 L45-153 L49-119 Q50-111 44-110 Q38-109 36-117 L30-148 L25-176 L24-147 L23-128 L22-112 L21-72 L18-20 L22-10 Q23-5 17-4 L5-4 Q0-5 1-12 L1-65 L-2-109 L-6-65 L-8-12 Q-6-5-12-4 L-26-4 Q-31-5-28-11 L-23-22 L-23-70 L-22-115 L-24-145 L-25-176 L-31-148 L-37-116 Q-39-109-45-111 Q-51-113-48-121 L-43-155 L-39-188 Q-37-199-27-202 L-7-208 L-7-215 Q-14-219-14-226 Z';
const seams = 'M-7-208L0-198L7-208 M0-198V-137 M-26-194L-17-180 M25-194L17-180 M-19-184H-5V-166H-18Z M5-184H19L18-166H5Z M-22-140Q0-135 23-140 M-20-129L-7-120 M20-129L7-120 M-14-111L-15-74L-12-34 M11-111L13-74L10-34 M-23-72L-9-69 M4-70L20-72 M-44-127L-36-125 M36-125L46-127 M-24-20L-9-18 M3-18L18-20';

const ArtDefs: React.FC = () => <defs>
  <radialGradient id="n18-blue"><stop stopColor={C.blue}/><stop offset=".45" stopColor="#1128bd" stopOpacity=".7"/><stop offset="1" stopColor="#071047" stopOpacity="0"/></radialGradient>
  <radialGradient id="n18-red"><stop stopColor={C.pink}/><stop offset=".4" stopColor="#d50c4b" stopOpacity=".6"/><stop offset="1" stopColor="#34061b" stopOpacity="0"/></radialGradient>
  <linearGradient id="n18-ground" x2=".5" y2="1"><stop stopColor="#1822a4"/><stop offset=".35" stopColor="#111c5d"/><stop offset="1" stopColor="#04060e"/></linearGradient>
  <linearGradient id="n18-uniform"><stop stopColor="#555fff"/><stop offset=".06" stopColor="#1e2c9a"/><stop offset=".22" stopColor="#101735"/><stop offset=".54" stopColor="#04060d"/><stop offset=".82" stopColor="#1e0b26"/><stop offset=".96" stopColor="#641337"/><stop offset="1" stopColor="#ff5c9a"/></linearGradient>
  <linearGradient id="n18-edge"><stop stopColor="#8497ff"/><stop offset=".18" stopColor="#3447d0"/><stop offset=".49" stopColor="#162047"/><stop offset=".8" stopColor="#b92462"/><stop offset="1" stopColor="#ffb3cb"/></linearGradient>
  <linearGradient id="n18-beam" x2="0" y2="1"><stop stopColor="#7d8dff" stopOpacity=".2"/><stop offset="1" stopColor={C.blue} stopOpacity="0"/></linearGradient>
  <linearGradient id="n18-red-beam" x2="1" y2=".5"><stop stopColor={C.pink} stopOpacity="0"/><stop offset="1" stopColor={C.pink} stopOpacity=".2"/></linearGradient>
  <linearGradient id="n18-building" x2="1" y2=".8"><stop stopColor="#242ab3"/><stop offset=".46" stopColor="#111a65"/><stop offset="1" stopColor="#080c20"/></linearGradient>
  <linearGradient id="n18-plan-building" x2="1" y2=".6"><stop stopColor="#682050"/><stop offset=".48" stopColor="#261346"/><stop offset="1" stopColor="#121d69"/></linearGradient>
  <linearGradient id="n18-court-wall"><stop stopColor="#23091f"/><stop offset=".5" stopColor="#090a1c"/><stop offset="1" stopColor="#111f80"/></linearGradient>
  <linearGradient id="n18-court-floor" x2="0" y2="1"><stop stopColor="#0d1546"/><stop offset="1" stopColor="#04050c"/></linearGradient>
  <linearGradient id="n18-court-bench" x2="0" y2="1"><stop stopColor="#3446a3"/><stop offset=".08" stopColor="#101632"/><stop offset="1" stopColor="#080914"/></linearGradient>
  <filter id="n18-glow" x="-80%" y="-35%" width="260%" height="170%"><feGaussianBlur stdDeviation="3.2"/></filter>
  <filter id="n18-soft"><feGaussianBlur stdDeviation="22"/></filter>
  <filter id="n18-shadow" x="-50%" y="-60%" width="200%" height="220%"><feGaussianBlur stdDeviation="8"/></filter>
  <pattern id="n18-edge-texture" width="7" height="7" patternUnits="userSpaceOnUse"><path d="M0 7L7 0 M-2 2L2-2 M5 9L9 5" stroke="#9daeff" strokeWidth=".55" opacity=".6"/></pattern>
  <clipPath id="n18-body-clip"><path d={body}/></clipPath>
</defs>;

const Person: React.FC<{x:number; y:number; scale:number; etched?:boolean; lean?:number}> = ({x,y,scale,etched=false,lean=0}) => <g transform={`translate(${x} ${y}) scale(${scale}) rotate(${lean})`}>
  <ellipse cx="2" cy="0" rx="41" ry="6" fill="#000" opacity=".85" filter="url(#n18-shadow)"/>
  <path d={body} fill="none" stroke={C.blue} strokeWidth="6" transform="translate(-2 0)" opacity=".9" filter="url(#n18-glow)"/>
  <path d={body} fill="none" stroke={C.pink} strokeWidth="5" transform="translate(2 0)" opacity=".85" filter="url(#n18-glow)"/>
  <path d={body} fill="url(#n18-uniform)" stroke="url(#n18-edge)" strokeWidth="1.1"/>
  {etched && <g clipPath="url(#n18-body-clip)">
    <path d={body} fill="url(#n18-edge-texture)" opacity=".28"/>
    <path d="M-21-196Q0-211 22-195 M-21-187Q0-202 22-186 M-23-156Q0-146 23-157 M-20-151Q0-141 21-152 M-20-146Q0-136 21-147 M-19-141Q0-131 20-142" fill="none" stroke="#c0ccff" strokeWidth=".6" opacity=".45"/>
  </g>}
  <path d={seams} fill="none" stroke="url(#n18-edge)" strokeWidth=".8" opacity=".85"/>
  <path d="M-18-239L-16-253Q0-262 16-253L19-239L23-235Q1-231-20-235Z" fill="url(#n18-uniform)" stroke="url(#n18-edge)" strokeWidth="1.1"/>
  <path d="M-15-247Q1-252 16-247 M-18-239Q1-243 18-239" fill="none" stroke="#7582f2" strokeWidth=".7" opacity=".7"/>
</g>;

const Finish: React.FC = () => {
  const {frame} = useShot();
  return <>
    <AbsoluteFill style={{background:'radial-gradient(ellipse at 52% 46%,transparent 24%,rgba(0,0,5,.16) 60%,rgba(0,0,5,.6) 100%)'}}/>
    <AbsoluteFill style={{background:'linear-gradient(180deg,rgba(3,4,11,.72),transparent 20%,transparent 74%,rgba(3,4,11,.92) 94%)'}}/>
    <svg width={1920} height={1080} style={{position:'absolute',inset:0,opacity:.075,mixBlendMode:'soft-light'}}>
      <filter id="n18-grain"><feTurbulence type="fractalNoise" baseFrequency=".82" numOctaves="1" seed={frame+31}/><feColorMatrix type="saturate" values="0"/></filter>
      <rect width={1920} height={1080} filter="url(#n18-grain)"/>
    </svg>
  </>;
};
const Opening: React.FC<{empty?:boolean}> = ({empty=false}) => {
  const {seconds,push} = useShot();
  return <>
    <svg width={1920} height={1080} viewBox="0 0 1920 1080">
      <ArtDefs/>
      <rect width={1920} height={1080} fill={C.ink}/>
      <g transform={`translate(1120 520) scale(${1+.025*push}) translate(-1120 -520)`}>
        <ellipse cx="1130" cy="410" rx="1090" ry="610" fill="url(#n18-blue)" opacity={1+.02*Math.sin(seconds*1.3)}/>
        <ellipse cx="1770" cy="465" rx="730" ry="610" fill="url(#n18-red)"/>
        <path d="M0 495L1130 405L1920 465V1080H0Z" fill="url(#n18-ground)"/>
        {/* Anonymous architecture has no real site dimensions or weather. */}
        <path d="M0 405L735 408L935 455H0Z" fill="#0e154b" stroke="#3d44bb" strokeWidth="2"/>
        <path d="M0 405L735 408V500L0 535Z" fill="#0b1038"/>
        {Array.from({length:13},(_,i) => <path key={i} d={`M${i*62} 430v37h30v-36Z`} fill="#182895" stroke="#3546bc" strokeWidth="1"/>)}
        <path d="M1515 348L1920 255V505L1515 463Z" fill="#270a35" stroke="#a41855" strokeWidth="2"/>
        {[0,1,2,3,4,5].map(i => <path key={i} d={`M${1560+i*72} ${361-i*17}v62l35-2v-69Z`} fill="#710d48" opacity=".55"/>)}
        <path d="M760 0L1055 0L1510 750L870 760Z" fill="url(#n18-beam)" filter="url(#n18-soft)"/>
        <path d="M1920 235L1490 390L1030 810L1920 690Z" fill="url(#n18-red-beam)" filter="url(#n18-soft)"/>
        <ellipse cx="1160" cy="565" rx="700" ry="72" fill="#4a3fff" opacity=".23" filter="url(#n18-soft)"/>
        <ellipse cx="1660" cy="611" rx="340" ry="50" fill={C.pink} opacity=".24" filter="url(#n18-soft)"/>
      </g>
      {!empty && <g transform={`translate(1110 650) scale(${1+.055*push}) translate(-1110 -650)`}>
        {[830,995,1160,1325,1490,1655].map((x,i) => <g key={x}>
          <path d={`M${x-12} 697L${x-105} 842L${x-66} 842L${x+13} 697Z`} fill="#03050f" opacity=".62"/>
          <Person x={x} y={698+Math.abs(i-2.5)*2} scale={.91} etched={i===1||i===4} lean={i%2?.5:-.5}/>
        </g>)}
        <path d="M755 730L1920 768" stroke="#9a236d" strokeWidth="2" opacity=".5"/>
      </g>
      }
      {/* Foreground tracks faster than people and architecture behind it. */}
      {!empty && <g transform={`translate(${-25*push} ${6*push})`}><Person x={360} y={1050} scale={3.3+.12*push} etched/></g>}
    </svg>
    <Finish/>
  </>;
};

// Overhead shoulders, sleeves, cap visor and boot toes, not circular tokens.
// The static red location dot is on empty ground, never attached to a person.
const OverheadPerson: React.FC<{x:number; y:number; angle:number}> = ({x,y,angle}) => <g transform={`translate(${x} ${y}) rotate(${angle})`}>
  <path d="M-27-11L-54 98L-26 119L16 25Z" fill="#01020b" opacity=".65"/>
  <path d="M-16 17L-16 40Q-10 48-4 40L-2 19 M6 18L8 42Q15 48 21 40L19 16" fill="#101531" stroke="#6878cd" strokeWidth="1.4"/>
  <path d="M-30-19Q-18-29 0-28Q18-29 30-19L40 4L37 23Q30 30 27 20L23 5L18 17Q0 26-18 17L-23 5L-27 22Q-32 29-38 22L-40 3Z" fill="none" stroke={C.pink} strokeWidth="6" filter="url(#n18-glow)"/>
  <path d="M-30-19Q-18-29 0-28Q18-29 30-19L40 4L37 23Q30 30 27 20L23 5L18 17Q0 26-18 17L-23 5L-27 22Q-32 29-38 22L-40 3Z" fill="url(#n18-uniform)" stroke="url(#n18-edge)" strokeWidth="2"/>
  <path d="M-24-12L-12-3 M24-12L12-3 M-17 9Q0 19 17 9" stroke="#a3a9e7" strokeWidth="1.1" fill="none"/>
  <ellipse cy="-15" rx="16" ry="19" fill="#090c1b" stroke="#b7bdec" strokeWidth="1.6"/>
  <path d="M-17-15Q-16-36 0-37Q16-36 17-15L19-7Q0-1-19-7Z" fill="url(#n18-building)" stroke="#a1a8fa" strokeWidth="1.8"/>
  <path d="M-15-15Q0-20 15-15" stroke="#ff89ba" fill="none" strokeWidth="1.6"/>
</g>;
const Roof: React.FC<{x:number; y:number; w:number; h:number}> = ({x,y,w,h}) => <g transform={`translate(${x} ${y})`}>
  <path d={`M0 0H${w}L${w+18} 20V${h+20}H18L0 ${h}Z`} fill="#030612"/>
  <rect width={w} height={h} fill="url(#n18-plan-building)" stroke="#5a48b6" strokeWidth="2"/>
  <path d={`M0 ${h/2}H${w} M0 0L18 20 M${w} 0L${w+18} 20 M${w} ${h}L${w+18} ${h+20}`} stroke="#5866f2" fill="none" opacity=".7"/>
  {Array.from({length:Math.floor(w/48)},(_,i) => <path key={i} d={`M${24+i*48} 5V${h-5}`} stroke="#5666de" opacity=".25"/>)}
</g>;

const Spatial: React.FC = () => {
  const {seconds,push} = useShot();
  return <>
    <svg width={1920} height={1080} viewBox="0 0 1920 1080">
      <ArtDefs/><rect width={1920} height={1080} fill={C.ink}/>
      <ellipse cx="600" cy="430" rx="1150" ry="750" fill="url(#n18-red)" opacity=".8"/>
      <ellipse cx="1580" cy="490" rx="1000" ry="800" fill="url(#n18-blue)"/>
      <g transform={`translate(1035 500) scale(${1+.06*push}) rotate(${-8+1.2*push}) translate(-1035 -500)`}>
        <path d="M190 180H1650L1780 260V930H190Z" fill="#080b20" stroke="#21318c" strokeWidth="3"/>
        <path d="M380 330H1470V785H380Z" fill="#141347" stroke="#4d3a83" strokeWidth="2"/>
        <path d="M407 357H1443V758H407Z" fill="#0c1032" stroke="#6a57a0" opacity=".7"/>
        <path d="M380 560H1470" stroke="#493756" strokeWidth="1.5"/>
        <ellipse cx="700" cy="535" rx="650" ry="390" fill="url(#n18-red)" opacity=".65"/>
        <ellipse cx="1350" cy="580" rx="550" ry="370" fill="url(#n18-blue)" opacity=".32"/>
        <Roof x={260} y={185} w={1130} h={105}/><Roof x={1530} y={330} w={170} h={370}/>
        <Roof x={260} y={825} w={570} h={110}/><Roof x={980} y={825} w={440} h={110}/>
        <path d="M218 324V785 M1730 312V785" stroke="#4c55b0" strokeWidth="3"/>
        {[0,1,2,3,4,5].map(i => <OverheadPerson key={i} x={530+i*156} y={535} angle={(i%3-1)*3}/>)}
        <circle cx="1420" cy="730" r="25" fill={C.red} opacity=".4" filter="url(#n18-glow)"/>
        <circle cx="1420" cy="730" r="9" fill={C.red}/><circle cx="1420" cy="730" r="15" fill="none" stroke="#ff8eab" strokeWidth="1.5"/>
      </g>
      <path d="M1630-60L1920 100L1470 1080L1250 1080Z" fill="url(#n18-beam)" opacity=".6" filter="url(#n18-soft)"/>
      <ellipse cx="1660" cy="820" rx="430" ry="110" fill="#414bff" opacity=".1" filter="url(#n18-soft)"/>
    </svg>
    <Finish/>
  </>;
};

const Verdict: React.FC = () => {
  const {seconds,push} = useShot();
  return <>
    <svg width={1920} height={1080} viewBox="0 0 1920 1080">
      <ArtDefs/><rect width={1920} height={1080} fill={C.ink}/>
      {/* Symmetric invented court: no judge, insignia or national emblem. */}
      <g transform={`translate(960 530) scale(${1+.08*push}) translate(-960 -530)`}>
        <path d="M0 0H1920L1250 325H670Z" fill="#0a0b24"/>
        <path d="M0 0L670 325V670L0 1080Z" fill="url(#n18-court-wall)"/>
        <path d="M1920 0L1250 325V670L1920 1080Z" fill="url(#n18-court-wall)"/>
        <rect x="670" y="325" width="580" height="345" fill="#080b1d" stroke="#3b4585" strokeWidth="2"/>
        <path d="M0 1080L670 670H1250L1920 1080Z" fill="url(#n18-court-floor)"/>
        <ellipse cx="470" cy="430" rx="720" ry="580" fill="url(#n18-red)" opacity=".65"/>
        <ellipse cx="1490" cy="450" rx="700" ry="630" fill="url(#n18-blue)" opacity=".9"/>
        {[.08,.23,.42,.63,.81].map((p,i) => {
          const lx=670*p, rx=1920-lx, top=325*p, bottom=1080-410*p;
          return <g key={i}>
            <path d={`M${lx} ${top}V${bottom} M${rx} ${top}V${bottom}`} fill="none" stroke="#303681" strokeWidth={7-p*5}/>
            <path d={`M${lx+7} ${top+18}V${bottom-12}`} stroke={C.pink} strokeWidth={3-p*2} opacity=".65"/>
            <path d={`M${rx-7} ${top+18}V${bottom-12}`} stroke="#6773ff" strokeWidth={3-p*2} opacity=".9"/>
            <path d={`M${lx+12} ${top+5}H${rx-12}`} stroke="#303660" strokeWidth="3"/>
          </g>;
        })}
        {[.12,.34,.55,.72].map(p => <path key={p} d={`M${670*p+120} ${325*p+23}H${1800-670*p}`} stroke="#7182e4" strokeWidth={6-p*4} opacity=".75"/>)}
        <path d="M830 318H1090L1410 850H510Z" fill="url(#n18-beam)" filter="url(#n18-soft)"/>
        <path d="M0 460L570 390L1050 870L0 920Z" fill="url(#n18-red-beam)" opacity=".7" filter="url(#n18-soft)"/>
        <ellipse cx="960" cy="675" rx="465" ry="58" fill="#3543ea" opacity=".2" filter="url(#n18-soft)"/>
        <path d="M733 619H1187L1255 651H665Z" fill="#4d5ba0" stroke="#7b88ce" strokeWidth="2"/>
        <path d="M665 651H1255V754H665Z" fill="url(#n18-court-bench)" stroke="#293367" strokeWidth="2"/>
        <path d="M680 661H1240 M704 680V735 M1216 680V735" fill="none" stroke="#5966a1" opacity=".5"/>
        <path d="M665 754H1255L1310 785H610Z" fill="#0a0f29" stroke="#333d77"/>
        <path d="M610 785H1310L1375 825H545Z" fill="#080d21" stroke="#232d57"/>
        <path d="M0 975L610 785 M1920 975L1310 785" stroke="#2c3471" strokeWidth="2"/>
      </g>
      <g transform={`translate(960 820) scale(${1+.14*push}) translate(-960 -820)`}>
        <path d="M0 727L445 801V1060H0Z" fill="#090918" stroke="#631337" strokeWidth="3"/>
        <path d="M1920 727L1475 801V1060H1920Z" fill="#070b20" stroke="#293cce" strokeWidth="3"/>
        <path d="M0 738L445 812 M1920 738L1475 812" stroke="#a5a5c0" opacity=".35" strokeWidth="3"/>
      </g>
    </svg>
    <Finish/>
  </>;
};

export const N18Art: React.FC<{kind:Kind;empty?:boolean}> = ({kind,empty}) => <AbsoluteFill style={{background:C.ink,fontVariantNumeric:'tabular-nums'}}>
 {kind==='opening' ? <Opening empty={empty}/> : kind==='spatial' ? <Spatial/> : <Verdict/>}
</AbsoluteFill>;
export {ArtDefs, Person, Finish, C};
