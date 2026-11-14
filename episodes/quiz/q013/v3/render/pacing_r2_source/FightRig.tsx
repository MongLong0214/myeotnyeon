// Original adult-animation style characters for the "역대급 판결" Shorts (owner: "릭앤모티 느낌"):
// huge heads, big round eyes with dot pupils, thick dark outlines, flat colours, hand-drawn line boil.
// All characters are original designs (no existing show's characters, props or logos).
import React from 'react';
import { useCurrentFrame } from 'remotion';

export const OL = '#1E1712';          // outline
const SKIN = '#F4CFA7';
const SKIN_SH = '#E2AE84';
const WORKER_SKIN = '#B9784A', WORKER_SHADE = '#A0643C';

const HEAD = 1.38;   // caricature: oversized head on a small, noodle-limbed body

export type Expr = 'pain' | 'concern' | 'normal' | 'angry' | 'shock' | 'scared' | 'tired' | 'smug' | 'talk' | 'serious' | 'dizzy';
export type Pose = 'stand' | 'point' | 'pushed' | 'sit' | 'bust' | 'shrug' | 'cling';
export type Look = 'B' | 'A' | 'judge' | 'cop' | 'D' | 'suit' | 'hoodie' | 'clerk' | 'granny' | 'doctor';

const LOOKS: Record<Look, { shirt: string; shirtSh: string; pants: string; shoe: string }> = {
  B: { shirt: '#3FB8A9', shirtSh: '#2E9285', pants: '#3E5FA8', shoe: '#F5F5F0' },
  A: { shirt: '#8E8F9B', shirtSh: '#72737E', pants: '#2F3340', shoe: '#E4E4E4' },
  judge: { shirt: '#22232B', shirtSh: '#15161C', pants: '#22232B', shoe: '#111' },
  cop: { shirt: '#2D3F73', shirtSh: '#22315C', pants: '#1F2A4A', shoe: '#111' },
  D: { shirt: '#C9503E', shirtSh: '#A43E2F', pants: '#4A4A52', shoe: '#2B2B2B' },
  suit: { shirt: '#3A3F4B', shirtSh: '#2B2F38', pants: '#2B2F38', shoe: '#111' },
  hoodie: { shirt: '#2E2E33', shirtSh: '#1F1F23', pants: '#4A5B7A', shoe: '#E4E4E4' },
  clerk: { shirt: '#2F8F5B', shirtSh: '#246F46', pants: '#2F3340', shoe: '#E4E4E4' },
  granny: { shirt: '#8C5BA8', shirtSh: '#6F4787', pants: '#5A5A64', shoe: '#2B2B2B' },
  doctor: { shirt: '#F4F4F2', shirtSh: '#D8D8D4', pants: '#3E7FA8', shoe: '#F5F5F0' },
};

const boil = (f: number, seed: number, amp = 0.6) => {
  const k = Math.floor(f / 4) + seed * 13;
  return [Math.sin(k * 12.9898) * amp, Math.cos(k * 78.233) * amp, Math.sin(k * 3.7) * 0.6];
};

// arm: shoulder at (sx, sy), angles in degrees (0 = straight down, positive = towards +x)
const Arm: React.FC<{ sx: number; sy: number; a1: number; a2: number; color: string; fingers?: boolean; skin?:string }> = ({ sx, sy, a1, a2, color, fingers, skin=SKIN }) => {
  const r1 = (a1 * Math.PI) / 180, r2 = ((a1 + a2) * Math.PI) / 180;
  const ex = sx + Math.sin(r1) * 78, ey = sy + Math.cos(r1) * 78;
  const hx = ex + Math.sin(r2) * 72, hy = ey + Math.cos(r2) * 72;
  return (
    <g>
      <path d={`M${sx},${sy} L${ex},${ey} L${hx},${hy}`} stroke={OL} strokeWidth={26} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d={`M${sx},${sy} L${ex},${ey}`} stroke={color} strokeWidth={15} fill="none" strokeLinecap="round" />
      <path d={`M${ex},${ey} L${hx},${hy}`} stroke={skin} strokeWidth={14} fill="none" strokeLinecap="round" />
      <circle cx={hx} cy={hy} r={15} fill={skin} stroke={OL} strokeWidth={6} />
      {fingers && <path d={`M${hx},${hy} l${Math.sin(r2) * 26},${Math.cos(r2) * 26}`} stroke={OL} strokeWidth={14} strokeLinecap="round" />}
      {fingers && <path d={`M${hx},${hy} l${Math.sin(r2) * 26},${Math.cos(r2) * 26}`} stroke={skin} strokeWidth={6} strokeLinecap="round" />}
    </g>
  );
};

const Eyes: React.FC<{ expr: Expr; look: [number, number]; f: number; skin?:string; worker?:boolean }> = ({ expr, look, f, skin=SKIN, worker=false }) => {
  const big = expr === 'shock' || expr === 'scared' ? 46 : 38;
  const pr = expr === 'shock' ? 3.5 : expr === 'scared' ? 4.5 : 6;
  const jitter = expr === 'scared' || expr === 'shock' ? Math.sin(f * 2.7) * 2 : 0;
  const lid = expr === 'tired' ? 0.55 : expr === 'smug' ? 0.4 : expr === 'serious' ? 0.25 : expr === 'pain' ? .30 : 0;
  const eyes = [-36, 36];
  return (
    <g>
      {eyes.map((ex, i) => (
        <g key={`e${ex}`}>
          <circle cx={ex} cy={-470} r={big} fill="#FFFFFF" stroke={OL} strokeWidth={6} />
          {expr === 'dizzy'
            ? <path d={`M${ex - 14},${-470} a14,14 0 1,1 14,14 a8,8 0 1,1 -8,-8`} stroke={OL} strokeWidth={4} fill="none" transform={`rotate(${f * 12 * (i ? -1 : 1)} ${ex} ${-470})`} />
            : <circle cx={ex + look[0] + jitter} cy={-470 + look[1]} r={pr} fill={OL} />}
          {lid > 0 && (() => {
            const yc = -big + 2 * big * lid;
            const dx = Math.sqrt(Math.max(0, big * big - yc * yc));
            return (
              <g>
                <path d={`M${ex - dx},${-470 + yc} A${big},${big} 0 0,1 ${ex + dx},${-470 + yc} Z`} fill={skin} stroke={OL} strokeWidth={5} />
                <line x1={ex - dx} y1={-470 + yc} x2={ex + dx} y2={-470 + yc} stroke={OL} strokeWidth={6} />
              </g>
            );
          })()}
        </g>
      ))}
      {!worker && expr === 'concern' && <g stroke={OL} strokeWidth={7} strokeLinecap="round"><path d="M-70,-519Q-45,-537 -18,-527M20,-523Q43,-516 68,-520" fill="none"/></g>}
      {worker && <g stroke={OL} strokeWidth={5} strokeLinecap="round"><path d={expr==='pain'?"M-66,-522Q-45,-510 -18,-518M18,-518Q43,-510 66,-522":"M-66,-522Q-45,-531 -18,-522M18,-522Q43,-527 66,-522"} fill="none"/></g>}
      {(expr === 'angry'  || expr === 'serious') && (
        <g stroke={OL} strokeWidth={10} strokeLinecap="round">
          <line x1={-74} y1={-528} x2={-14} y2={expr === 'angry' ? -505 : -515} />
          <line x1={74} y1={-528} x2={14} y2={expr === 'angry' ? -505 : -515} />
        </g>
      )}
      {!worker && (expr === 'scared' || expr === 'tired') && (
        <g stroke={OL} strokeWidth={8} strokeLinecap="round">
          <line x1={-70} y1={-512} x2={-18} y2={-528} />
          <line x1={70} y1={-512} x2={18} y2={-528} />
        </g>
      )}
    </g>
  );
};

const Mouth: React.FC<{ expr: Expr; talk: boolean; f: number }> = ({ expr, talk, f }) => {
  const open = talk ? (Math.sin(f * 1.3) + 1) / 2 : 0;
  if (expr === 'shock' || expr === 'scared') {
    return <ellipse cx={0} cy={-392} rx={expr === 'shock' ? 26 : 34} ry={expr === 'shock' ? 34 : 18 + open * 10} fill="#5A1E1E" stroke={OL} strokeWidth={6} />;
  }
  if (expr === 'pain') return <path d="M-29,-386Q0,-408 29,-386" stroke={OL} strokeWidth={6} fill="none" strokeLinecap="round"/>;
  if (expr === 'angry') {
    return (
      <g>
        <rect x={-46} y={-410} width={92} height={36 + open * 10} rx={12} fill="#FFFFFF" stroke={OL} strokeWidth={6} />
        <line x1={-46} y1={-392 + open * 5} x2={46} y2={-392 + open * 5} stroke={OL} strokeWidth={4} />
        {[-23, 0, 23].map((x) => <line key={`t${x}`} x1={x} y1={-410} x2={x} y2={-374 + open * 10} stroke={OL} strokeWidth={3} />)}
      </g>
    );
  }
  if (expr === 'smug') return <path d="M-40,-396 Q0,-372 44,-404" stroke={OL} strokeWidth={7} fill="none" strokeLinecap="round" />;
  if (expr === 'tired' || expr === 'serious' || expr === 'concern') return <path d={`M-34,-390 Q0,${-398 - open * 8} 34,-390`} stroke={OL} strokeWidth={7} fill={talk ? '#5A1E1E' : 'none'} strokeLinecap="round" />;
  if (expr === 'dizzy') return <path d="M-38,-392 q10,-12 19,0 t19,0 t19,0 t19,0" stroke={OL} strokeWidth={6} fill="none" strokeLinecap="round" />;
  if (talk) return <ellipse cx={0} cy={-392} rx={30} ry={6 + open * 16} fill="#5A1E1E" stroke={OL} strokeWidth={6} />;
  return <path d="M-36,-394 Q0,-378 36,-394" stroke={OL} strokeWidth={7} fill="none" strokeLinecap="round" />;
};

const Head: React.FC<{ look: Look; expr: Expr; talk: boolean; eye: [number, number]; f: number; anonymous?: boolean }> = ({ look, expr, talk, eye, f, anonymous }) => {const skin=look==='B'?WORKER_SKIN:SKIN,shade=look==='B'?WORKER_SHADE:SKIN_SH;return (
  <g>
    {look === 'A' && <path d="M-146,-392 Q-170,-566 0,-606 Q170,-566 146,-392 Q138,-360 116,-350 L-116,-350 Q-138,-360 -146,-392 Z" fill="#8E8F9B" stroke={OL} strokeWidth={8} />}
    {look === 'A' && (
      <g fill="#5A2E1A" stroke={OL} strokeWidth={7} strokeLinejoin="round">
        <path d="M-122,-520 Q-150,-420 -138,-300 Q-120,-262 -96,-300 Q-104,-400 -96,-500 Z" />
        <path d="M122,-520 Q150,-420 138,-300 Q120,-262 96,-300 Q104,-400 96,-500 Z" />
      </g>
    )}
    <path d={look==='B'?"M-104,-472Q-112,-561 -42,-581Q28,-596 85,-562Q114,-533 108,-468Q110,-402 78,-368Q40,-338 0,-339Q-44,-338 -78,-369Q-110,-405 -104,-472Z":"M-118,-470 Q-124,-570 -40,-584 Q30,-596 92,-566 Q132,-540 124,-470 Q130,-400 96,-366 Q50,-334 0,-336 Q-60,-334 -96,-364 Q-128,-400 -118,-470 Z"}
      fill={skin} stroke={OL} strokeWidth={8} strokeLinejoin="round" />
    <path d={look==='B'?"M55,-363Q83,-389 93,-432":"M70,-360 Q100,-380 110,-430"} stroke={shade} strokeWidth={12} fill="none" strokeLinecap="round" />
    <ellipse cx={look==='B'?-110:-124} cy={-452} rx={16} ry={26} fill={skin} stroke={OL} strokeWidth={6} />
    <ellipse cx={look==='B'?110:124} cy={-452} rx={16} ry={26} fill={skin} stroke={OL} strokeWidth={6} />
    {look === 'B' && <path d="M-104,-510Q-118,-586 -43,-606Q38,-624 93,-575L108,-514Q78,-553 43,-561Q10,-548 -23,-564Q-63,-551 -87,-538Z" fill="#242221" stroke={OL} strokeWidth={8} strokeLinejoin="round" />}
    {look === 'A' && <path d="M-104,-540 Q-60,-600 0,-588 Q60,-600 104,-540 Q70,-560 30,-548 Q0,-570 -30,-548 Q-70,-560 -104,-540 Z" fill="#5A2E1A" stroke={OL} strokeWidth={6} />}
    {look === 'suit' && <path d="M-114,-500 Q-116,-604 0,-608 Q104,-604 118,-512 Q96,-566 30,-566 Q-10,-588 -60,-560 Q-96,-548 -114,-500 Z" fill="#1E1E22" stroke={OL} strokeWidth={8} strokeLinejoin="round" />}
    {look === 'hoodie' && <path d="M-112,-506 Q-104,-598 0,-602 Q104,-598 112,-506 Q60,-546 0,-548 Q-60,-546 -112,-506 Z" fill="#3B302A" stroke={OL} strokeWidth={7} />}
    {look === 'clerk' && (
      <g fill="#2B1A12" stroke={OL} strokeWidth={7} strokeLinejoin="round">
        <path d="M104,-540 Q176,-520 156,-420 Q140,-380 120,-410 Q134,-470 100,-500 Z" />
        <path d="M-108,-520 Q-90,-606 0,-604 Q92,-606 110,-520 Q70,-562 0,-556 Q-60,-560 -108,-520 Z" />
      </g>
    )}
    {look === 'granny' && (
      <g fill="#C9C9D2" stroke={OL} strokeWidth={6}>
        {[[-100, -520], [-70, -572], [-26, -598], [22, -600], [66, -578], [100, -526], [-112, -470], [114, -476]].map(([cx, cy]) => <circle key={`curl${cx}`} cx={cx} cy={cy} r={34} />)}
      </g>
    )}
    {look === 'doctor' && <path d="M-110,-516 Q-100,-600 0,-604 Q100,-600 112,-516 Q80,-552 30,-548 Q0,-572 -40,-550 Q-80,-556 -110,-516 Z" fill="#3A2A20" stroke={OL} strokeWidth={7} />}
    {look === 'judge' && (
      <g>
        <path d="M-122,-470 Q-150,-500 -128,-534 Q-112,-500 -100,-516 Q-104,-480 -122,-470 Z" fill="#E8E8E8" stroke={OL} strokeWidth={6} />
        <path d="M122,-470 Q150,-500 128,-534 Q112,-500 100,-516 Q104,-480 122,-470 Z" fill="#E8E8E8" stroke={OL} strokeWidth={6} />
        <path d="M-60,-560 Q0,-596 60,-560" stroke={shade} strokeWidth={8} fill="none" />
      </g>
    )}
    {look === 'cop' && (
      <g>
        <path d="M-112,-520 Q-110,-610 0,-616 Q110,-610 112,-520 Z" fill="#22315C" stroke={OL} strokeWidth={8} />
        <path d="M-124,-520 Q0,-494 124,-520 Q130,-500 118,-492 Q0,-468 -118,-492 Q-130,-500 -124,-520 Z" fill="#141A2E" stroke={OL} strokeWidth={6} />
        <circle cx={0} cy={-566} r={18} fill="#E8C24A" stroke={OL} strokeWidth={5} />
      </g>
    )}
    {look === 'D' && (
      <g>
        <path d="M-118,-480 Q-128,-560 -80,-570 Q-100,-540 -96,-500 Z" fill="#9A9AA2" stroke={OL} strokeWidth={6} />
        <path d="M118,-480 Q128,-560 80,-570 Q100,-540 96,-500 Z" fill="#9A9AA2" stroke={OL} strokeWidth={6} />
        <ellipse cx={-70} cy={-414} rx={26} ry={14} fill="#F08C8C" opacity={0.75} />
        <ellipse cx={70} cy={-414} rx={26} ry={14} fill="#F08C8C" opacity={0.75} />
        <path d="M-30,-424 Q0,-410 30,-424 Q14,-406 0,-410 Q-14,-406 -30,-424 Z" fill="#6E6E76" stroke={OL} strokeWidth={4} />
      </g>
    )}
    {!anonymous && <Eyes expr={expr} look={eye} f={f} skin={skin} worker={look==='B'} />}
    {look === 'A' && (
      <g stroke={OL} strokeWidth={6} strokeLinecap="round">
        <line x1={-70} y1={-500} x2={-82} y2={-516} /><line x1={-58} y1={-508} x2={-64} y2={-526} />
        <line x1={70} y1={-500} x2={82} y2={-516} /><line x1={58} y1={-508} x2={64} y2={-526} />
      </g>
    )}
    {look === 'judge' && (
      <g fill="none" stroke={OL} strokeWidth={6}>
        <rect x={-74} y={-492} width={66} height={44} rx={10} />
        <rect x={8} y={-492} width={66} height={44} rx={10} />
        <line x1={-8} y1={-472} x2={8} y2={-472} />
      </g>
    )}
    {!anonymous && <path d={look==='B'?"M-5,-440Q-15,-421 0,-415":"M-6,-440 Q-22,-418 -2,-412"} stroke={OL} strokeWidth={6} fill="none" strokeLinecap="round" />}
    {!anonymous && <Mouth expr={expr} talk={talk} f={f} />}
    {expr === 'tired' && <path d="M70,-420 q8,24 0,40" stroke="#7CC8FF" strokeWidth={10} strokeLinecap="round" />}
    {expr === 'angry' && (
      <g stroke="#E0302A" strokeWidth={7} strokeLinecap="round" fill="none" transform="translate(78 -560)">
        <path d="M-14,-4 q10,6 0,16" /><path d="M14,-4 q-10,6 0,16" /><path d="M-4,-16 q6,10 16,0" /><path d="M-4,16 q6,-10 16,0" />
      </g>
    )}
    {(expr === 'shock' || expr === 'scared') && <path d="M-60,-372 q-6,30 2,52" stroke="#9FD8FF" strokeWidth={8} strokeLinecap="round" fill="none" />}
  </g>
);};

const POSES: Record<Pose, { l: [number, number]; r: [number, number]; legs: 'stand' | 'sit' | 'none' }> = {
  stand: { l: [-14, 6], r: [14, -6], legs: 'stand' },
  point: { l: [-12, 8], r: [100, -12], legs: 'stand' },
  pushed: { l: [-140, -30], r: [140, 30], legs: 'stand' },
  sit: { l: [-28, -30], r: [26, 34], legs: 'sit' },
  bust: { l: [-10, 30], r: [10, -30], legs: 'none' },
  shrug: { l: [-70, 110], r: [70, -110], legs: 'stand' },
  cling: { l: [-160, 10], r: [-150, -10], legs: 'stand' },
};

export const Guy: React.FC<{
  look: Look; x: number; y: number; scale?: number; expr?: Expr; pose?: Pose; flip?: boolean; rot?: number; squash?: number;
  talk?: boolean; eye?: [number, number]; wobble?: number; seed?: number; headPop?: number;
}> = ({ look, x, y, scale = 1, expr = 'normal', pose = 'stand', flip, rot = 0, squash = 0, talk = false, eye = [0, 0], wobble = 1.4, seed = 1, headPop = 0 }) => {
  const f = useCurrentFrame();
  const L = LOOKS[look],skin=look==='B'?WORKER_SKIN:SKIN;
  const P = POSES[pose];
  const [bx, by, br] = boil(f, seed);
  const tilt = Math.sin(f / 7 + seed) * wobble;
  const sq = Math.max(-0.4, Math.min(0.5, squash));
  const sit = P.legs === 'sit';
  const lift = sit ? 120 : 0;
  return (
    <svg width={1000} height={900} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
      <g transform={`translate(${x + bx} ${y + by}) rotate(${rot + br}) scale(${(flip ? -1 : 1) * scale * (1 + sq * 0.3)} ${scale * (1 - sq * 0.28)})`}>
        <ellipse cx={0} cy={6} rx={110} ry={18} fill="rgba(0,0,0,0.25)" />
        {P.legs === 'stand' && (
          <g>
            {[-30, 30].map((lx) => (
              <g key={`leg${lx}`}>
                <path d={`M${lx * 0.8},-175 L${lx * 0.95},-14`} stroke={OL} strokeWidth={36} strokeLinecap="round" />
                <path d={`M${lx * 0.8},-175 L${lx * 0.95},-14`} stroke={L.pants} strokeWidth={24} strokeLinecap="round" />
                <ellipse cx={lx * 0.95 + (lx > 0 ? 14 : -14)} cy={-8} rx={32} ry={16} fill={L.shoe} stroke={OL} strokeWidth={6} />
              </g>
            ))}
          </g>
        )}
        {sit && (
          <g>
            {[-1, 1].map((k) => (
              <g key={`sleg${k}`}>
                <path d={`M${k * 22},-60 L${k * 22 + 150},-40 L${k * 22 + 170},-8`} stroke={OL} strokeWidth={46} fill="none" strokeLinecap="round" strokeLinejoin="round" />
                <path d={`M${k * 22},-60 L${k * 22 + 150},-40 L${k * 22 + 170},-8`} stroke={L.pants} strokeWidth={34} fill="none" strokeLinecap="round" strokeLinejoin="round" />
                <ellipse cx={k * 22 + 190} cy={-6} rx={34} ry={17} fill={L.shoe} stroke={OL} strokeWidth={6} />
              </g>
            ))}
          </g>
        )}
        <g transform={`translate(0 ${lift})`}>
          <path d="M-58,-170 Q-66,-300 -48,-318 L48,-318 Q66,-300 58,-170 Q0,-158 -58,-170 Z" fill={L.shirt} stroke={OL} strokeWidth={8} strokeLinejoin="round"
            transform={P.legs === 'none' ? 'translate(0 0)' : undefined} />
          <path d="M32,-312 Q50,-260 44,-176" stroke={L.shirtSh} strokeWidth={14} fill="none" strokeLinecap="round" />
          {look === 'judge' && <path d="M-26,-318 L0,-270 L26,-318" fill="#FFFFFF" stroke={OL} strokeWidth={6} />}
          {look === 'suit' && (
            <g stroke={OL} strokeWidth={5} strokeLinejoin="round">
              <path d="M-26,-318 L0,-262 L26,-318 Z" fill="#FFFFFF" />
              <path d="M-7,-306 L7,-306 L11,-236 L0,-222 L-11,-236 Z" fill="#C8372D" />
            </g>
          )}
          {look === 'hoodie' && <path d="M-50,-318 Q0,-284 50,-318 Q30,-300 0,-298 Q-30,-300 -50,-318 Z" fill="#46464D" stroke={OL} strokeWidth={6} />}
          {look === 'hoodie' && <g stroke="#E4E4E4" strokeWidth={5} strokeLinecap="round"><line x1={-12} y1={-298} x2={-14} y2={-250} /><line x1={12} y1={-298} x2={14} y2={-250} /></g>}
          {look === 'clerk' && <path d="M-26,-318 L0,-280 L26,-318 Z" fill="#FFFFFF" stroke={OL} strokeWidth={5} />}
          {look === 'doctor' && (
            <g stroke={OL} strokeWidth={5} strokeLinejoin="round">
              <path d="M-24,-318 L0,-276 L24,-318 Z" fill="#7FB8D9" />
              <line x1={0} y1={-276} x2={0} y2={-172} />
            </g>
          )}
          <Arm sx={-50} sy={-302} a1={P.l[0]} a2={P.l[1]} color={L.shirt} skin={skin} />
          <Arm sx={50} sy={-302} a1={P.r[0]} a2={P.r[1]} color={L.shirt} skin={skin} fingers={pose === 'point'} />
          <g transform={`translate(0 ${-312}) rotate(${tilt}) scale(${HEAD * (1 + headPop * 0.2)}) translate(0 ${312})`}>
            <Head look={look} expr={expr} talk={talk} eye={eye} f={f} />
          </g>
        </g>
      </g>
    </svg>
  );
};

// q014-only articulation extension. Same rm.tsx head, clothes, palette and stroke geometry.
// Full-body joints are authored in the character's original coordinate space.
export type Point = [number, number];
export type RigPose = {hip: Point; torso: number; head: number; feet: [Point,Point]; knees: [Point,Point]; hands: [Point,Point]; elbows?: [Point,Point];squash?:number};
const rad = (a:number) => a*Math.PI/180;
const rotateP = (p:Point,a:number):Point => [p[0]*Math.cos(rad(a))-p[1]*Math.sin(rad(a)),p[0]*Math.sin(rad(a))+p[1]*Math.cos(rad(a))];
const solveElbow=(a:Point,b:Point,side:number):Point=>{
  const dx=b[0]-a[0],dy=b[1]-a[1],d=Math.max(.001,Math.hypot(dx,dy)),l1=110,l2=100,q=Math.min(d,l1+l2-.001);
  const k=(l1*l1-l2*l2+q*q)/(2*q),h=Math.sqrt(Math.max(0,l1*l1-k*k));
  return [a[0]+dx/d*k-dy/d*h*side,a[1]+dy/d*k+dx/d*h*side];
};
export const ArticulatedGuy: React.FC<{look:'hoodie'|'B'|'judge';x:number;y:number;scale:number;rig:RigPose;expr?:Expr;eye?:[number,number];anonymous?:boolean;label?:string;talk?:boolean}> = ({look,x,y,scale,rig,expr='serious',eye=[0,0],anonymous=false,label,talk=false})=>{
 const f=useCurrentFrame(),L=LOOKS[look],skin=look==='B'?WORKER_SKIN:SKIN;
 const u=(p:Point):Point=>{const r=rotateP([p[0],p[1]+170],rig.torso);return [rig.hip[0]+r[0],rig.hip[1]+r[1]];};
 const shoulders:[Point,Point]=[u([-50,-302]),u([50,-302])];
 const neck=u([0,-318]);
 const arm=(i:number)=>{const s=shoulders[i],h=rig.hands[i],e=rig.elbows?.[i]??solveElbow(s,h,i===0?1:-1);return <g key={i}>
  <path d={`M${s} L${e} L${h}`} stroke={OL} strokeWidth={26} fill="none" strokeLinecap="round" strokeLinejoin="round"/>
  <path d={`M${s} L${e}`} stroke={L.shirt} strokeWidth={15} fill="none" strokeLinecap="round"/>
  <path d={`M${e} L${h}`} stroke={skin} strokeWidth={14} fill="none" strokeLinecap="round"/>
  <rect x={h[0]-17} y={h[1]-14} width={34} height={28} rx={10} fill={skin} stroke={OL} strokeWidth={6}/>
  <path d={`M${h[0]-5},${h[1]+2}h10`} stroke={OL} strokeWidth={3} strokeLinecap="round"/>
 </g>};
 return <svg width={1000} height={900} style={{position:'absolute',inset:0,overflow:'visible'}} aria-label={label??(look==='judge'?'판사 캐릭터 · 시각비유':look==='hoodie'?'공장 관리자 · 비식별 재구성':'노동자 · 비식별 재구성')}>
 <g transform={`translate(${x} ${y}) scale(${scale})`}>
  <ellipse cx={0} cy={8} rx={105} ry={17} fill="rgba(0,0,0,0.25)"/>
  {rig.feet.map((ft,i)=>{const hp:Point=[rig.hip[0]+(i?24:-24),rig.hip[1]],k=rig.knees[i];return <g key={i}>
   <path d={`M${hp} L${k} L${ft}`} fill="none" stroke={OL} strokeWidth={36} strokeLinecap="round" strokeLinejoin="round"/>
   <path d={`M${hp} L${k} L${ft}`} fill="none" stroke={L.pants} strokeWidth={24} strokeLinecap="round" strokeLinejoin="round"/>
   <ellipse cx={ft[0]+(i?14:-14)} cy={ft[1]-8} rx={32} ry={16} fill={L.shoe} stroke={OL} strokeWidth={6}/>
  </g>})}
  {arm(0)}
  <g transform={`translate(${rig.hip}) rotate(${rig.torso}) translate(0 170)`}>
   <path d="M-58,-170 Q-66,-300 -48,-318 L48,-318 Q66,-300 58,-170 Q0,-158 -58,-170 Z" fill={L.shirt} stroke={OL} strokeWidth={8} strokeLinejoin="round"/>
   <path d="M32,-312 Q50,-260 44,-176" stroke={L.shirtSh} strokeWidth={14} fill="none" strokeLinecap="round"/>
   {look==='hoodie'&&<><path d="M-50,-318 Q0,-284 50,-318 Q30,-300 0,-298 Q-30,-300 -50,-318 Z" fill="#46464D" stroke={OL} strokeWidth={6}/><path d="M-12,-298L-14,-250M12,-298L14,-250" fill="none" stroke="#E4E4E4" strokeWidth={5} strokeLinecap="round"/></>}
  </g>
  <path d={`M${neck[0]},${neck[1]+8}L${neck[0]},${neck[1]-32}`} stroke={OL} strokeWidth={30} strokeLinecap="round"/>
  <path d={`M${neck[0]},${neck[1]+6}L${neck[0]},${neck[1]-32}`} stroke={skin} strokeWidth={18} strokeLinecap="round"/>
  <g transform={`translate(${neck[0]} ${neck[1]}) rotate(${rig.head}) scale(${HEAD*(1+(rig.squash??0)*.11)} ${HEAD*(1-(rig.squash??0)*.09)}) translate(0 312)`}>
   <Head look={look} expr={expr} talk={talk} eye={eye} f={f} anonymous={anonymous}/>
  </g>
  {arm(1)}
 </g></svg>;
};
