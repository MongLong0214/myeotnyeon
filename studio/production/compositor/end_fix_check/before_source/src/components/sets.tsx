// Backgrounds for non-traffic cases, drawn in the same 1000×900 set space and ink style as NightLot.
// Readable content stays out of the Shorts action rail (set x ≥ 880, y ≥ 570).
import React from 'react';
import { useCurrentFrame } from 'remotion';
import { INK, PAPER, YELLOW } from './toon';

const W = 1000, H = 900;
const S = { stroke: INK, strokeWidth: 8, strokeLinejoin: 'round' as const };

export const OfficeSet: React.FC = () => (
  <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
    <rect x={0} y={0} width={W} height={H} fill="#DCE3EA" />
    <rect x={0} y={640} width={W} height={260} fill="#9AA6B5" {...S} />
    <g>
      <rect x={560} y={70} width={360} height={300} rx={10} fill="#8EC5E8" {...S} />
      {[[600, 210, 60, 160], [680, 170, 70, 200], [770, 230, 60, 140], [850, 190, 50, 180]].map(([x, y, w, h]) => (
        <rect key={`b${x}`} x={x} y={y} width={w} height={h} fill="#6C8DB0" stroke={INK} strokeWidth={4} />
      ))}
      <line x1={740} y1={70} x2={740} y2={370} stroke={INK} strokeWidth={6} />
    </g>
    <rect x={60} y={100} width={150} height={190} rx={8} fill={PAPER} {...S} />
    {[140, 175, 210, 245].map((y) => <line key={`l${y}`} x1={85} y1={y} x2={185} y2={y} stroke="#B7BFCB" strokeWidth={8} strokeLinecap="round" />)}
    <rect x={120} y={520} width={760} height={46} rx={10} fill="#B9844F" {...S} />
    <rect x={160} y={566} width={30} height={170} fill="#8C6239" {...S} />
    <rect x={810} y={566} width={30} height={170} fill="#8C6239" {...S} />
    <rect x={430} y={380} width={250} height={150} rx={12} fill="#2C3445" {...S} />
  </svg>
);

export const HallwaySet: React.FC = () => (
  <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
    <rect x={0} y={0} width={W} height={H} fill="#EFE6D2" />
    <polygon points="0,640 1000,640 1000,900 0,900" fill="#BFA98A" {...S} />
    {[60, 400, 740].map((x, i) => (
      <g key={`d${x}`}>
        <rect x={x} y={170} width={200} height={470} rx={8} fill={['#7B5A44', '#6E7F96', '#7B5A44'][i]} {...S} />
        <circle cx={x + 170} cy={420} r={12} fill={YELLOW} stroke={INK} strokeWidth={5} />
        <rect x={x + 55} y={200} width={90} height={44} rx={6} fill={PAPER} stroke={INK} strokeWidth={5} />
        <text x={x + 100} y={232} textAnchor="middle" fontFamily="Pretendard" fontWeight={800} fontSize={28} fill={INK}>{['1402', '1403', '1404'][i]}</text>
      </g>
    ))}
    {[200, 540, 880].map((x) => <rect key={`c${x}`} x={x - 50} y={20} width={100} height={22} rx={10} fill="#FFF6C8" stroke={INK} strokeWidth={5} />)}
  </svg>
);

export const StoreSet: React.FC = () => (
  <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
    <rect x={0} y={0} width={W} height={H} fill="#E9F0E8" />
    {[0, 1, 2].map((r) => (
      <g key={`s${r}`}>
        <rect x={40} y={90 + r * 140} width={920} height={20} fill="#C9CED6" {...S} />
        {Array.from({ length: 11 }, (_, i) => (
          <rect key={`p${r}-${i}`} x={60 + i * 82} y={30 + r * 140} width={60} height={60} rx={8} fill={['#F0433A', '#21B8B0', '#FFD84A', '#7A6CF0'][(i + r) % 4]} stroke={INK} strokeWidth={5} />
        ))}
      </g>
    ))}
    <rect x={0} y={560} width={W} height={340} fill="#D7C3A3" {...S} />
    <rect x={80} y={500} width={840} height={70} rx={10} fill="#5E7F6E" {...S} />
    <rect x={640} y={410} width={170} height={90} rx={10} fill="#2C3445" {...S} />
    <rect x={660} y={425} width={130} height={55} rx={6} fill="#8EE6C8" />
  </svg>
);

// Big amount with stacked bills: label like "700억", counts up from 0 between at and at + 30.
export const MoneySet: React.FC<{ label: string; at?: number }> = ({ label, at = 0 }) => {
  const f = useCurrentFrame();
  const k = Math.max(0, Math.min(1, (f - at) / 30));
  return (
    <>
      <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
        <rect x={0} y={0} width={W} height={H} fill="#1F3B2E" />
        {Array.from({ length: 9 }, (_, i) => {
          const h = Math.round((60 + (i % 3) * 40) * k);
          const x = 120 + (i % 5) * 150, base = i < 5 ? 780 : 640;
          return Array.from({ length: Math.max(0, Math.floor(h / 16)) }, (_, j) => (
            <rect key={`m${i}-${j}`} x={x} y={base - j * 16} width={130} height={14} rx={3} fill={j % 2 ? '#8CCB7E' : '#76B86A'} stroke={INK} strokeWidth={4} />
          ));
        })}
      </svg>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 120, textAlign: 'center', fontFamily: "'Black Han Sans', 'Pretendard', sans-serif", fontSize: 200, lineHeight: 1,
        color: YELLOW, WebkitTextStroke: `16px ${INK}`, paintOrder: 'stroke fill', transform: `scale(${0.6 + 0.4 * k})`, opacity: k }}>{label}</div>
    </>
  );
};

// A phone with chat bubbles that stack by their own height. Bubbles carry only text that is in the archived
// articles; pass [] for blank bars.
export const PhoneSet: React.FC<{ lines: { me?: boolean; text?: string }[]; at?: number; step?: number }> = ({ lines, at = 0, step = 10 }) => {
  const f = useCurrentFrame();
  return (
    <>
      <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
        <rect x={0} y={0} width={W} height={H} fill="#E7E2F3" />
        <rect x={230} y={30} width={540} height={840} rx={64} fill="#22252E" {...S} />
        <rect x={256} y={100} width={488} height={730} rx={22} fill="#B9C7DB" />
        <rect x={440} y={52} width={120} height={22} rx={11} fill="#0E0F13" />
      </svg>
      <div style={{ position: 'absolute', left: 276, top: 124, width: 448, display: 'flex', flexDirection: 'column', gap: 22 }}>
        {lines.map((l, i) => {
          const k = Math.max(0, Math.min(1, (f - (at + i * step)) / 6));
          return (
            <div key={`c${i}`} style={{ alignSelf: l.me ? 'flex-end' : 'flex-start', maxWidth: 420, minWidth: 160, minHeight: 72, borderRadius: 24, background: l.me ? YELLOW : PAPER,
              border: `5px solid ${INK}`, padding: '14px 22px', fontFamily: 'Pretendard', fontWeight: 800, fontSize: 44, lineHeight: 1.25, color: INK, boxSizing: 'border-box', wordBreak: 'keep-all',
              opacity: k, transform: `translateY(${(1 - k) * 16}px)` }}>
              {l.text ?? <div style={{ height: 14, width: 160, background: '#C9CED6', borderRadius: 7, marginTop: 12 }} />}
            </div>
          );
        })}
      </div>
    </>
  );
};

// Serious tone for cases with a death: no faces, no gags — a chrysanthemum and a candle. The flame flickers and the
// view creeps in slowly so a long serious beat never reads as a frozen frame.
export const MemorialSet: React.FC = () => {
  const f = useCurrentFrame();
  const z = 1 + Math.min(f, 600) * 0.00012;
  const fl = 1 + Math.sin(f * 0.9) * 0.08 + Math.sin(f * 2.3) * 0.04;
  return (
    <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
      <rect x={0} y={0} width={W} height={H} fill="#1C1E26" />
      <g transform={`translate(500 560) scale(${z}) translate(-500 -560)`}>
        <rect x={-50} y={640} width={W + 100} height={300} fill="#2A2D38" />
        <defs><radialGradient id="candleGlow"><stop offset="0" stopColor="#FFC766" stopOpacity={0.32 + 0.06 * Math.sin(f * 0.7)} /><stop offset="1" stopColor="#FFC766" stopOpacity={0} /></radialGradient></defs>
        <circle cx={660} cy={440} r={190} fill="url(#candleGlow)" />
        <g transform="translate(330 520)">
          <path d="M0,0 Q-10,120 10,240" stroke="#3E6B3A" strokeWidth={14} fill="none" strokeLinecap="round" />
          {Array.from({ length: 18 }, (_, i) => (
            <ellipse key={`f${i}`} cx={0} cy={-40} rx={18} ry={62} fill="#F4F1E6" stroke={INK} strokeWidth={4} transform={`rotate(${i * 20} 0 0)`} />
          ))}
          <circle cx={0} cy={0} r={26} fill="#E9D98A" stroke={INK} strokeWidth={5} />
        </g>
        <g transform="translate(660 600)">
          <rect x={-40} y={-140} width={80} height={180} rx={10} fill="#F4F1E6" stroke={INK} strokeWidth={6} />
          <g transform={`translate(0 -150) scale(${1 / fl * 0.5 + 0.5} ${fl})`}>
            <path d="M0,-60 Q26,-20 0,0 Q-26,-20 0,-60 Z" fill="#FFB547" stroke={INK} strokeWidth={4} />
          </g>
        </g>
      </g>
    </svg>
  );
};

// ------------------------------------------------------------------ #11–#14 sets (2026-10-26)
const SKIN = '#F4CFA7';
const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

// Airliner cabin beside an over-wing emergency exit. The lever (yellow, in a red housing) lifts at leverAt; an arm in a
// plain sleeve reaches it from below at handAt. Only the arm is drawn, so the passenger has no visible age or sex.
export const CabinSet: React.FC<{ leverAt?: number; handAt?: number | null }> = ({ leverAt = 1e9, handAt = null }) => {
  const f = useCurrentFrame();
  const k = clamp01((f - leverAt) / 8);
  const ang = 62 * (1 - Math.pow(1 - k, 3));
  const r = (ang * Math.PI) / 180;
  const px = 690, py = 520, L = 150;
  const tx = px - L * Math.cos(r), ty = py - L * Math.sin(r);
  const slide = handAt == null ? 0 : 1 - Math.pow(1 - clamp01((f - handAt) / 10), 3);
  const hy = ty + (1 - slide) * 420;
  const sh = [430, 980], el = [(sh[0] + tx) / 2 - 70, (sh[1] + hy) / 2 + 30];
  const cloud = (dx: number) => ((f * 2 + dx) % 360) - 60;
  return (
    <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
      <defs>
        <clipPath id="cabWin"><rect x={96} y={230} width={160} height={190} rx={70} /></clipPath>
        <clipPath id="doorWin"><rect x={528} y={214} width={124} height={140} rx={50} /></clipPath>
      </defs>
      <rect x={0} y={0} width={W} height={H} fill="#E8E4DA" />
      <rect x={-10} y={-10} width={W + 20} height={84} fill="#F4F1E6" {...S} />
      {[0, 1, 2, 3].map((i) => <line key={`bin${i}`} x1={i * 260 + 120} y1={8} x2={i * 260 + 120} y2={70} stroke={INK} strokeWidth={5} />)}
      <rect x={400} y={140} width={380} height={580} rx={44} fill="#D7D2C6" {...S} />
      <rect x={430} y={170} width={320} height={520} rx={30} fill="none" stroke="#B9B3A5" strokeWidth={6} />
      {([['cabWin', 96, 230, 160, 190, 70], ['doorWin', 528, 214, 124, 140, 50]] as const).map(([id, x, y, w, h, rx]) => (
        <g key={`w${id}`}>
          <rect x={x - 10} y={y - 10} width={w + 20} height={h + 20} rx={rx + 8} fill="#C9C4B7" {...S} />
          <g clipPath={`url(#${id})`}>
            <rect x={x} y={y} width={w} height={h} fill="#8EC5E8" />
            {[0, 150, 260].map((dx) => <ellipse key={`cl${dx}`} cx={x + cloud(dx)} cy={y + h * 0.62 + (dx % 3) * 8} rx={46} ry={16} fill="#FFFFFF" opacity={0.9} />)}
          </g>
        </g>
      ))}
      <rect x={470} y={84} width={240} height={50} rx={10} fill="#2F8F5B" {...S} />
      <text x={590} y={122} textAnchor="middle" fontFamily="Pretendard" fontWeight={800} fontSize={36} fill="#FFFDF6">비상구</text>
      <rect x={520} y={452} width={226} height={136} rx={16} fill="#C9503E" {...S} />
      <g transform={`translate(${px} ${py}) rotate(${ang})`}>
        <rect x={-L - 14} y={-17} width={L + 30} height={34} rx={14} fill="#F2B705" stroke={INK} strokeWidth={7} />
      </g>
      <circle cx={px} cy={py} r={16} fill="#5B5F6B" stroke={INK} strokeWidth={6} />
      <rect x={-20} y={720} width={W + 40} height={200} fill="#4F5D73" {...S} />
      {[[40, 470], [230, 470]].map(([sx, sy]) => (
        <g key={`seat${sx}`}>
          <rect x={sx} y={sy} width={170} height={330} rx={34} fill="#3E5FA8" {...S} />
          <rect x={sx + 20} y={sy + 16} width={130} height={60} rx={14} fill="#F4F1E6" stroke={INK} strokeWidth={5} />
        </g>
      ))}
      <rect x={830} y={470} width={190} height={330} rx={34} fill="#3E5FA8" {...S} />
      {handAt != null && f >= handAt && (
        <g>
          <path d={`M${sh[0]},${sh[1]} L${el[0]},${el[1]} L${tx},${hy + 26}`} stroke={INK} strokeWidth={66} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          <path d={`M${sh[0]},${sh[1]} L${el[0]},${el[1]} L${tx},${hy + 26}`} stroke="#7A8796" strokeWidth={50} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx={tx} cy={hy} r={30} fill={SKIN} stroke={INK} strokeWidth={7} />
          <path d={`M${tx - 26},${hy - 8} q-14,-22 4,-30`} stroke={INK} strokeWidth={16} fill="none" strokeLinecap="round" />
          <path d={`M${tx - 26},${hy - 8} q-14,-22 4,-30`} stroke={SKIN} strokeWidth={7} fill="none" strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};

// Smoke puffs that rise from (x, y) and drift with the wind; muted grey so a serious beat stays calm.
const Smoke: React.FC<{ x: number; y: number; n?: number; size?: number; drift?: number; color?: string; f: number }> = ({ x, y, n = 6, size = 40, drift = 0.5, color = '#9A958C', f }) => (
  <g>
    {Array.from({ length: n }, (_, i) => {
      const t = ((f * 1.4 + i * (240 / n)) % 240) / 240;
      return <circle key={`sm${i}`} cx={x + t * 200 * drift + Math.sin(i * 1.7 + f / 20) * 10} cy={y - t * 300} r={size * (0.6 + t * 1.2)} fill={color} opacity={0.55 * (1 - t)} />;
    })}
  </g>
);

const WindLines: React.FC<{ f: number; y0?: number }> = ({ f, y0 = 160 }) => (
  <g>
    {Array.from({ length: 6 }, (_, i) => {
      const x0 = ((i * 230 + f * 9) % 1300) - 200, y = y0 + (i % 3) * 120;
      return <path key={`wd${i}`} d={`M${x0},${y} q60,-24 120,0 t120,0`} stroke="#FFFDF6" strokeWidth={6} fill="none" strokeLinecap="round" opacity={0.7} />;
    })}
  </g>
);

// Orchard in early spring: bare fruit trees, a low pile of farm waste. smoke = the pile still smoulders; wind = gusts.
export const OrchardSet: React.FC<{ smoke?: boolean; wind?: boolean }> = ({ smoke, wind }) => {
  const f = useCurrentFrame();
  return (
    <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
      <defs><linearGradient id="orSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#D9D3C6" /><stop offset="1" stopColor="#C2B9A6" /></linearGradient></defs>
      <rect x={0} y={0} width={W} height={H} fill="url(#orSky)" />
      <path d="M-20,470 Q180,360 380,440 Q600,330 820,420 Q920,380 1020,410 L1020,620 L-20,620 Z" fill="#9AA184" {...S} />
      <rect x={-20} y={600} width={W + 40} height={320} fill="#A8936E" {...S} />
      {[[110, 640, 1], [300, 610, 0.85], [760, 615, 0.9], [930, 650, 1.05]].map(([x, y, s]) => (
        <g key={`tr${x}`} transform={`translate(${x} ${y}) scale(${s})`}>
          <path d="M0,0 L0,-170 M0,-120 L-70,-200 M0,-140 L60,-230 M0,-170 L-10,-260 M-40,-170 L-80,-150 M30,-190 L90,-180" stroke={INK} strokeWidth={22} strokeLinecap="round" fill="none" />
          <path d="M0,0 L0,-170 M0,-120 L-70,-200 M0,-140 L60,-230 M0,-170 L-10,-260 M-40,-170 L-80,-150 M30,-190 L90,-180" stroke="#6B4A2E" strokeWidth={12} strokeLinecap="round" fill="none" />
          {[[-70, -200], [60, -230], [-10, -260], [90, -180]].map(([bx, by]) => <circle key={`bud${bx}`} cx={bx} cy={by} r={9} fill="#B7C48A" stroke={INK} strokeWidth={4} />)}
        </g>
      ))}
      <g transform="translate(520 720)">
        <ellipse cx={0} cy={0} rx={150} ry={34} fill="#5E4A36" stroke={INK} strokeWidth={7} />
        {[[-120, -10, 90, -40], [-80, -30, 110, -10], [-110, -40, 60, -60], [-40, -60, 120, -30], [-100, -20, 20, -70]].map(([x1, y1, x2, y2]) => (
          <line key={`st${x1}${y1}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#7A5A3A" strokeWidth={12} strokeLinecap="round" />
        ))}
        {smoke && [[-40, -36], [10, -50], [56, -30]].map(([ex, ey], i) => <circle key={`em${ex}`} cx={ex} cy={ey} r={9 + 3 * Math.sin(f * 0.5 + i)} fill="#FF8A3D" opacity={0.85} />)}
      </g>
      {smoke && <Smoke x={520} y={660} f={f} drift={wind ? 1.4 : 0.4} />}
      {wind && <WindLines f={f} y0={150} />}
    </svg>
  );
};

// Wildfire on distant ridges at dusk: a glow, a flickering fire line and smoke. No buildings, no people.
export const WildfireSet: React.FC = () => {
  const f = useCurrentFrame();
  const fl = (i: number) => 1 + 0.18 * Math.sin(f * 0.7 + i * 1.9) + 0.08 * Math.sin(f * 1.9 + i);
  return (
    <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
      <defs>
        <linearGradient id="wfSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#241A1C" /><stop offset="1" stopColor="#5C2F20" /></linearGradient>
        <radialGradient id="wfGlow" cx="0.5" cy="0.6" r="0.6"><stop offset="0" stopColor="#FF8A3D" stopOpacity={0.55 + 0.05 * Math.sin(f * 0.4)} /><stop offset="1" stopColor="#FF8A3D" stopOpacity={0} /></radialGradient>
      </defs>
      <rect x={0} y={0} width={W} height={H} fill="url(#wfSky)" />
      <ellipse cx={500} cy={520} rx={620} ry={300} fill="url(#wfGlow)" />
      <Smoke x={260} y={480} f={f} n={7} size={70} drift={1.2} color="#4A403C" />
      <Smoke x={680} y={460} f={f + 90} n={7} size={80} drift={1.0} color="#4A403C" />
      <path d="M-20,560 Q120,430 260,500 Q400,400 560,480 Q700,410 840,470 Q930,440 1020,470 L1020,700 L-20,700 Z" fill="#3A2723" {...S} />
      {Array.from({ length: 13 }, (_, i) => {
        const x = 20 + i * 78, y = 520 - 46 * Math.sin((i / 12) * Math.PI) + (i % 3) * 8;
        return <path key={`fl${i}`} d="M0,0 Q-22,-30 -6,-62 Q4,-40 14,-70 Q30,-36 0,0 Z" transform={`translate(${x} ${y}) scale(${fl(i)} ${fl(i + 3)})`} fill={i % 2 ? '#FFB547' : '#FF7A2F'} stroke={INK} strokeWidth={4} />;
      })}
      <path d="M-20,700 Q200,590 420,660 Q640,580 860,650 Q950,630 1020,640 L1020,920 L-20,920 Z" fill="#1E1615" {...S} />
    </svg>
  );
};

// Factory dormitory room: bunk bed, window, plank floor.
export const DormSet: React.FC = () => (
  <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
    <rect x={0} y={0} width={W} height={H} fill="#E9DFCB" />
    <rect x={-20} y={640} width={W + 40} height={280} fill="#B8996F" {...S} />
    {[160, 360, 560, 760].map((x) => <line key={`pl${x}`} x1={x} y1={640} x2={x - 40} y2={900} stroke="#9C7F58" strokeWidth={5} />)}
    <rect x={640} y={90} width={260} height={200} rx={10} fill="#BFD8E8" {...S} />
    <line x1={770} y1={90} x2={770} y2={290} stroke={INK} strokeWidth={6} />
    <rect x={630} y={286} width={280} height={18} rx={6} fill="#D7CBB4" stroke={INK} strokeWidth={5} />
    <g>
      {[40, 300].map((x) => <rect key={`post${x}`} x={x} y={120} width={22} height={540} rx={6} fill="#7B8796" stroke={INK} strokeWidth={6} />)}
      {[300, 560].map((y) => (
        <g key={`bunk${y}`}>
          <rect x={40} y={y} width={282} height={40} rx={8} fill="#F4F1E6" stroke={INK} strokeWidth={6} />
          <rect x={110} y={y - 24} width={200} height={30} rx={12} fill="#7A9CC6" stroke={INK} strokeWidth={5} />
        </g>
      ))}
      {[180, 230, 280].map((y) => <line key={`rung${y}`} x1={300} y1={y} x2={322} y2={y} stroke={INK} strokeWidth={5} />)}
    </g>
  </svg>
);

// Motel room: wallpaper, a bed on the right, a low table on the left where the relay phones sit.
export const MotelSet: React.FC = () => (
  <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
    <rect x={0} y={0} width={W} height={H} fill="#B9A6C9" />
    {Array.from({ length: 9 }, (_, i) => <path key={`wp${i}`} d={`M${i * 125 - 60},0 L${i * 125 + 60},640`} stroke="#A994BC" strokeWidth={6} />)}
    <rect x={-20} y={650} width={W + 40} height={270} fill="#6D5A4E" {...S} />
    <rect x={610} y={380} width={380} height={150} rx={18} fill="#5A3E5E" {...S} />
    <rect x={580} y={520} width={440} height={130} rx={18} fill="#F4F1E6" {...S} />
    <rect x={620} y={560} width={400} height={110} rx={18} fill="#C9503E" {...S} />
    <rect x={40} y={600} width={500} height={34} rx={8} fill="#8C6239" {...S} />
    {[70, 490].map((x) => <rect key={`tl${x}`} x={x} y={634} width={24} height={150} fill="#6E4A2B" stroke={INK} strokeWidth={6} />)}
    <g transform="translate(560 190)">
      <rect x={-14} y={0} width={28} height={70} fill="#3C3F48" stroke={INK} strokeWidth={5} />
      <path d="M-50,0 L50,0 L30,-60 L-30,-60 Z" fill="#FFE9A8" stroke={INK} strokeWidth={6} strokeLinejoin="round" />
    </g>
  </svg>
);

// Night street outside a bar (q014 V3-03): warm door and window, a camera over the door, a dark gap beside the
// building. No people and no signage text.
export const BarStreetSet: React.FC = () => {
  const f = useCurrentFrame();
  const glow = 0.85 + 0.08 * Math.sin(f * 0.21);
  return (
    <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
      <defs><linearGradient id="bsSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#141A33" /><stop offset="1" stopColor="#2A2F55" /></linearGradient></defs>
      <rect x={0} y={0} width={W} height={H} fill="url(#bsSky)" />
      {Array.from({ length: 14 }, (_, i) => <circle key={`bst${i}`} cx={(i * 263) % 1000} cy={(i * 71) % 180 + 20} r={i % 3 ? 2 : 3} fill="#FFF6C8" opacity={0.7} />)}
      <rect x={40} y={170} width={640} height={540} fill="#4E4058" {...S} />
      {Array.from({ length: 6 }, (_, r) => <line key={`br${r}`} x1={40} y1={240 + r * 80} x2={680} y2={240 + r * 80} stroke="#433650" strokeWidth={5} />)}
      <rect x={110} y={300} width={250} height={170} rx={10} fill="#FFC766" opacity={glow} {...S} />
      <line x1={235} y1={300} x2={235} y2={470} stroke={INK} strokeWidth={6} />
      <rect x={430} y={360} width={170} height={350} rx={8} fill="#FFB547" opacity={glow} {...S} />
      <circle cx={580} cy={540} r={9} fill={INK} />
      <g transform="translate(470 230)">
        <rect x={0} y={0} width={110} height={80} rx={14} fill="#F2C14E" stroke={INK} strokeWidth={6} />
        <rect x={22} y={18} width={46} height={46} rx={6} fill="#FFFDF6" stroke={INK} strokeWidth={5} />
        <path d="M68,28 q20,0 20,14 q0,14 -20,14" fill="none" stroke={INK} strokeWidth={5} />
        <rect x={22} y={14} width={46} height={12} rx={5} fill="#FFFDF6" stroke={INK} strokeWidth={4} />
      </g>
      <g transform="translate(610 330)">
        <rect x={-6} y={-30} width={12} height={30} fill="#5B5F6B" stroke={INK} strokeWidth={4} />
        <rect x={-46} y={-10} width={64} height={34} rx={8} fill="#D7DCE3" stroke={INK} strokeWidth={5} />
        <circle cx={-46} cy={7} r={9} fill="#2C3445" stroke={INK} strokeWidth={4} />
      </g>
      <rect x={680} y={250} width={120} height={460} fill="#0E1120" stroke={INK} strokeWidth={6} />
      <rect x={800} y={210} width={220} height={500} fill="#3B3247" {...S} />
      <rect x={-20} y={700} width={W + 40} height={220} fill="#5A5A66" {...S} />
      <line x1={-20} y1={760} x2={1020} y2={760} stroke="#6E6E7A" strokeWidth={6} />
      <g transform="translate(900 700)">
        <rect x={-8} y={-420} width={16} height={420} fill="#2A2F3A" stroke={INK} strokeWidth={4} />
        <ellipse cx={0} cy={-424} rx={40} ry={14} fill="#FFE9A8" stroke={INK} strokeWidth={4} />
      </g>
    </svg>
  );
};

// A phone recording a voice memo (q014 V3-03): pulsing record dot, running timer, moving level bars.
export const RecorderSet: React.FC = () => {
  const f = useCurrentFrame();
  const sec = Math.floor(f / 30) + 12;
  const t = `00:${String(sec % 60).padStart(2, '0')}`;
  return (
    <>
      <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
        <rect x={0} y={0} width={W} height={H} fill="#1C2030" />
        <rect x={300} y={70} width={400} height={800} rx={60} fill="#22252E" {...S} />
        <rect x={322} y={130} width={356} height={700} rx={20} fill="#0F1218" />
        <rect x={450} y={92} width={100} height={20} rx={10} fill="#0E0F13" />
        <circle cx={500} cy={420} r={46 + 6 * Math.sin(f * 0.3)} fill="#F0433A" opacity={0.25} />
        <circle cx={500} cy={420} r={34} fill="#F0433A" stroke={INK} strokeWidth={6} />
        {Array.from({ length: 13 }, (_, i) => {
          const h = 14 + Math.abs(Math.sin(f * 0.37 + i * 1.3)) * 70 * (0.5 + 0.5 * Math.sin(i * 0.9 + f * 0.05));
          return <rect key={`lv${i}`} x={356 + i * 23} y={540 - h / 2} width={13} height={h} rx={6} fill="#8EE6C8" />;
        })}
      </svg>
      <div style={{ position: 'absolute', left: 322, width: 356, top: 170, textAlign: 'center', fontFamily: 'Pretendard', fontWeight: 800, fontSize: 40, color: '#FFFDF6' }}>녹음 중</div>
      <div style={{ position: 'absolute', left: 322, width: 356, top: 236, textAlign: 'center', fontFamily: 'Pretendard', fontWeight: 700, fontSize: 64, color: '#FFFDF6', letterSpacing: '0.02em' }}>{t}</div>
    </>
  );
};

// Relay rig: a row of handsets on a stand, wired to a power strip; screens light up in turn (calls being relayed).
const Phones: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <g>
      <rect x={-230} y={-26} width={460} height={26} rx={8} fill="#3C3F48" stroke={INK} strokeWidth={6} />
      {Array.from({ length: 7 }, (_, i) => {
        const x = -210 + i * 62, on = Math.floor(f / 6 + i * 3) % 7 < 3;
        return (
          <g key={`ph${i}`}>
            <path d={`M${x + 22},-26 Q${x + 22},20 ${x + 40},40`} stroke={INK} strokeWidth={5} fill="none" />
            <rect x={x} y={-150} width={46} height={120} rx={9} fill="#22252E" stroke={INK} strokeWidth={5} />
            <rect x={x + 6} y={-140} width={34} height={92} rx={4} fill={on ? '#8EE6C8' : '#3C4A55'} />
          </g>
        );
      })}
      <rect x={-140} y={34} width={280} height={30} rx={8} fill="#F4F1E6" stroke={INK} strokeWidth={6} />
      {Array.from({ length: 6 }, (_, i) => <circle key={`ps${i}`} cx={-110 + i * 44} cy={49} r={7} fill={i % 2 ? '#F0433A' : '#5B5F6B'} />)}
    </g>
  );
};

// ------------------------------------------------------------------ props (set space, origin at the prop's base centre)
export type PropKind = 'diaper' | 'fridge' | 'fridgeOpen' | 'forklift' | 'bricks' | 'wrap' | 'tiles' | 'memo' | 'delivery' | 'phones';
export const Prop: React.FC<{ kind: PropKind; x: number; y: number; scale?: number; rot?: number; lift?: number }> = ({ kind, x, y, scale = 1, rot = 0, lift = 0 }) => (
  <svg width={W} height={H} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
    <g transform={`translate(${x} ${y}) rotate(${rot}) scale(${scale})`}>
      {kind === 'delivery' && (
        <g>
          <path d="M-90,0 L-100,-130 L100,-130 L90,0 Z" fill="#FFFDF6" stroke={INK} strokeWidth={8} strokeLinejoin="round" />
          <path d="M-60,-130 Q-60,-190 -20,-190 Q0,-190 0,-150 M60,-130 Q60,-190 20,-190 Q0,-190 0,-150" stroke={INK} strokeWidth={8} fill="none" strokeLinecap="round" />
          <rect x={-70} y={-110} width={140} height={46} rx={8} fill="#E05A3A" stroke={INK} strokeWidth={6} />
          <rect x={-70} y={-64} width={140} height={44} rx={6} fill="#F2C14E" stroke={INK} strokeWidth={6} />
        </g>
      )}
      {kind === 'phones' && <Phones />}
      {kind === 'diaper' && (
        <g>
          <path d="M-90,-120 L90,-120 Q80,-40 40,-10 Q0,6 -40,-10 Q-80,-40 -90,-120 Z" fill="#FBFBF6" stroke={INK} strokeWidth={8} strokeLinejoin="round" />
          <rect x={-110} y={-136} width={50} height={30} rx={8} fill="#8EC5E8" stroke={INK} strokeWidth={6} />
          <rect x={60} y={-136} width={50} height={30} rx={8} fill="#8EC5E8" stroke={INK} strokeWidth={6} />
          <path d="M-36,-70 Q-10,-96 22,-74 Q44,-56 18,-40 Q-12,-26 -30,-46 Z" fill="#8A5A2B" stroke={INK} strokeWidth={4} />
        </g>
      )}
      {(kind === 'fridge' || kind === 'fridgeOpen') && (
        <g>
          <rect x={-110} y={-470} width={220} height={470} rx={18} fill="#F2F4F6" stroke={INK} strokeWidth={8} />
          <line x1={-110} y1={-300} x2={110} y2={-300} stroke={INK} strokeWidth={6} />
          {kind === 'fridge' && <rect x={74} y={-440} width={12} height={90} rx={6} fill="#B7BFCB" stroke={INK} strokeWidth={4} />}
          {kind === 'fridgeOpen' && (
            <g>
              <rect x={-96} y={-288} width={192} height={274} rx={8} fill="#FFF9DD" stroke={INK} strokeWidth={5} />
              {[-200, -120].map((sy) => <line key={`sh${sy}`} x1={-96} y1={sy} x2={96} y2={sy} stroke="#C9CED6" strokeWidth={6} />)}
              {[-70, -10, 50].map((bx) => <rect key={`pie${bx}`} x={bx - 26} y={-246} width={52} height={40} rx={6} fill="#D9342B" stroke={INK} strokeWidth={4} />)}
              <rect x={-60} y={-166} width={60} height={40} rx={6} fill="#F2C14E" stroke={INK} strokeWidth={4} />
              <path d="M110,-300 L210,-270 L210,-10 L110,0 Z" fill="#E4E8EC" stroke={INK} strokeWidth={8} strokeLinejoin="round" />
            </g>
          )}
        </g>
      )}
      {kind === 'forklift' && (
        <g>
          {/* mast and forks on the left; lift raises the carriage */}
          <rect x={-250} y={-520} width={22} height={520} fill="#5B5F6B" stroke={INK} strokeWidth={6} />
          <rect x={-206} y={-520} width={22} height={520} fill="#5B5F6B" stroke={INK} strokeWidth={6} />
          <rect x={-380} y={-40 - lift} width={200} height={18} rx={4} fill="#3C3F48" stroke={INK} strokeWidth={6} />
          <rect x={-196} y={-150 - lift} width={18} height={128} fill="#3C3F48" stroke={INK} strokeWidth={6} />
          <path d="M-180,-170 L150,-170 L170,-60 L-180,-60 Z" fill="#F2B705" stroke={INK} strokeWidth={8} strokeLinejoin="round" />
          <path d="M-120,-170 L-120,-400 L90,-400 L120,-170" fill="none" stroke={INK} strokeWidth={14} strokeLinejoin="round" />
          <path d="M-120,-170 L-120,-400 L90,-400 L120,-170" fill="none" stroke="#3C3F48" strokeWidth={6} strokeLinejoin="round" />
          <rect x={60} y={-250} width={110} height={90} rx={10} fill="#D99A00" stroke={INK} strokeWidth={8} />
          {[-110, 90].map((wx) => (
            <g key={`fw${wx}`}><circle cx={wx} cy={-40} r={48} fill="#151821" stroke={INK} strokeWidth={8} /><circle cx={wx} cy={-40} r={20} fill="#9AA3B2" stroke={INK} strokeWidth={5} /></g>
          ))}
        </g>
      )}
      {kind === 'bricks' && (
        <g>
          <rect x={-110} y={-24} width={220} height={24} fill="#8C6239" stroke={INK} strokeWidth={6} />
          {Array.from({ length: 4 }, (_, r) => Array.from({ length: 3 }, (_, c) => (
            <rect key={`br${r}-${c}`} x={-104 + c * 70 + (r % 2) * 10} y={-24 - (r + 1) * 40} width={64} height={36} rx={4} fill="#B8553A" stroke={INK} strokeWidth={5} />
          )))}
        </g>
      )}
      {kind === 'wrap' && (
        <g opacity={0.82}>
          {[-60, -130, -200].map((wy) => <rect key={`wr${wy}`} x={-130} y={wy} width={260} height={30} rx={10} fill="#E9F6FF" stroke="#7FB8D9" strokeWidth={5} />)}
        </g>
      )}
      {kind === 'memo' && (
        <g>
          <rect x={-120} y={-300} width={240} height={300} rx={10} fill="#FFFDF6" stroke={INK} strokeWidth={8} />
          <text x={0} y={-236} textAnchor="middle" fontFamily="Pretendard" fontWeight={800} fontSize={54} fill={INK}>각서</text>
          {[-180, -140, -100, -60].map((ly) => <line key={`ml${ly}`} x1={-84} y1={ly} x2={84} y2={ly} stroke="#B7BFCB" strokeWidth={8} strokeLinecap="round" />)}
          <circle cx={60} cy={-34} r={20} fill="none" stroke="#D9342B" strokeWidth={6} />
        </g>
      )}
      {kind === 'tiles' && (
        <g>
          <rect x={-500} y={-900} width={1000} height={900} fill="#D7E8EE" />
          {Array.from({ length: 12 }, (_, i) => <line key={`tv${i}`} x1={-500 + i * 90} y1={-900} x2={-500 + i * 90} y2={0} stroke="#B9D0D9" strokeWidth={4} />)}
          {Array.from({ length: 11 }, (_, i) => <line key={`th${i}`} x1={-500} y1={-900 + i * 90} x2={500} y2={-900 + i * 90} stroke="#B9D0D9" strokeWidth={4} />)}
        </g>
      )}
    </g>
  </svg>
);

// One huge word or number on a flat colour (a duration, a count) — counts in with a small pop.
export const BigTextSet: React.FC<{ label: string; sub?: string; bg?: string; color?: string; at?: number }> = ({ label, sub, bg = '#1C1E26', color = YELLOW, at = 0 }) => {
  const f = useCurrentFrame();
  const k = Math.max(0, Math.min(1, (f - at) / 10));
  return (
    <>
      <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}><rect x={0} y={0} width={W} height={H} fill={bg} /></svg>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 150, textAlign: 'center', fontFamily: "'Black Han Sans', 'Pretendard', sans-serif", fontSize: 230, lineHeight: 1,
        color, WebkitTextStroke: `18px ${INK}`, paintOrder: 'stroke fill', transform: `scale(${0.7 + 0.3 * k})`, opacity: k }}>{label}</div>
      {/* sub stays ≤ 700 px wide around x 500 so it clears the Shorts action rail (set x ≥ 854 below set y 450) */}
      {sub && <div style={{ position: 'absolute', left: 150, width: 700, top: 440, textAlign: 'center', fontFamily: 'Pretendard', fontWeight: 800, fontSize: 52, lineHeight: 1.2, color: PAPER, opacity: k }}>{sub}</div>}
    </>
  );
};

// Cafe front (outside): awning, glass door and window; optional boulders blocking the entrance.
export const CafeSet: React.FC<{ rocks?: boolean }> = ({ rocks }) => (
  <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
    <rect x={0} y={0} width={W} height={H} fill="#CFE3EE" />
    <rect x={0} y={660} width={W} height={240} fill="#B9B2A6" stroke={INK} strokeWidth={6} />
    <rect x={300} y={120} width={660} height={540} fill="#F2E3C8" stroke={INK} strokeWidth={8} />
    <path d="M280,120 L980,120 L960,210 L300,210 Z" fill="#2F8F5B" stroke={INK} strokeWidth={8} strokeLinejoin="round" />
    {[0, 1, 2, 3, 4, 5].map((i) => <path key={`aw${i}`} d={`M${300 + i * 110},210 q55,40 110,0`} fill="#F4F1E6" stroke={INK} strokeWidth={6} />)}
    <text x={630} y={182} textAnchor="middle" fontFamily="'Black Han Sans', Pretendard" fontSize={60} fill="#FFFDF6">CAFE</text>
    <rect x={340} y={290} width={300} height={250} rx={10} fill="#9CCBE3" stroke={INK} strokeWidth={8} />
    <path d="M380,500 q40,-60 80,0 M470,500 q30,-50 60,0" stroke="#FFFDF6" strokeWidth={8} fill="none" opacity={0.8} />
    <rect x={690} y={290} width={210} height={370} rx={8} fill="#7FB8D9" stroke={INK} strokeWidth={8} />
    <circle cx={720} cy={480} r={10} fill={YELLOW} stroke={INK} strokeWidth={4} />
    {rocks && [[560, 700, 90, 60], [700, 712, 110, 70], [840, 702, 85, 58]].map(([cx, cy, rx, ry]) => (
      <g key={`rk${cx}`}>
        <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="#8D8F99" stroke={INK} strokeWidth={8} />
        <path d={`M${cx - rx * 0.5},${cy - ry * 0.2} q${rx * 0.3},${-ry * 0.4} ${rx * 0.7},${-ry * 0.1}`} stroke="#B3B5BE" strokeWidth={8} fill="none" strokeLinecap="round" />
      </g>
    ))}
  </svg>
);
