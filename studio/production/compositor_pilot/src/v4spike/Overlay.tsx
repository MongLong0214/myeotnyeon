import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { loadFonts } from '../fonts';
import { commander, palette as C, project, recruits } from './scene';

loadFonts();
const font = "'Pretendard', sans-serif";
export const Overlay: React.FC = () => {
  const f = useCurrentFrame();
  const { width: w, height: h } = useVideoConfig();
  const wide = w > h;
  const a = project(recruits[0], f, w, h);
  const b = project(recruits[5], f, w, h);
  const head = project([commander[0], 2.5, commander[2]], f, w, h);
  const p = interpolate(f, [15, 31], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const label = interpolate(f, [37, 43], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const date = '2024년 5월 23일.';
  const shownDate = date.slice(0, Math.min(date.length, Math.floor(f / (30 * 0.022))));
  const tx = wide ? 1060 : 535;
  const ty = wide ? 240 : 650;
  return <AbsoluteFill style={{ fontFamily: font, color: C.white, fontVariantNumeric: 'tabular-nums', pointerEvents: 'none' }}>
    <AbsoluteFill style={{ background: wide
      ? 'linear-gradient(180deg,rgba(5,7,13,.75),transparent 36%,transparent 72%,rgba(5,7,13,.85))'
      : 'linear-gradient(180deg,rgba(5,7,13,.94),rgba(5,7,13,.8) 18%,transparent 32%,transparent 59%,rgba(5,7,13,.45) 70%,rgba(5,7,13,.94))' }} />
    {!wide && <div style={{ position: 'absolute', left: 130, top: 210, width: 820, fontSize: 60, fontWeight: 800, lineHeight: 1.25, letterSpacing: '-.035em' }}>
      <div>얼차려로 숨진 훈련병</div>
      <div style={{ color: '#FF3B4E' }}>2심에서 형이 늘어난 이유</div>
    </div>}
    <div style={{ position: 'absolute', left: wide ? 100 : 130, top: wide ? 76 : 411, fontSize: 46, fontWeight: 700, lineHeight: '62px', whiteSpace: 'pre' }}>{shownDate}</div>
    <svg width={w} height={h} style={{ position: 'absolute', inset: 0 }}>
      <path d={`M${a.x} ${a.y + 17}v32H${b.x}v-32 M${(a.x+b.x)/2} ${a.y+49}V${ty+98}H${tx+12}`}
        fill="none" stroke={C.yellow} strokeWidth={4} strokeDasharray="10 8"
        style={{ clipPath: `inset(0 ${100*(1-p)}% 0 0)` }} />
      <circle cx={a.x} cy={a.y+17} r={5} fill={C.yellow} opacity={p} />
      <circle cx={b.x} cy={b.y+17} r={5} fill={C.yellow} opacity={p} />
    </svg>
    <div style={{ position: 'absolute', left: tx, top: ty, opacity: label, padding: '12px 18px', background: 'rgba(5,7,13,.94)', borderLeft: `4px solid ${C.yellow}`, fontSize: 50, lineHeight: '66px', fontWeight: 600, color: C.yellow }}>
      훈련병 6명
    </div>
    <div style={{ position: 'absolute', left: Math.max(wide ? 110 : 130, head.x - 70), top: Math.min(wide ? 680 : 1070, head.y - 88),
      padding: '8px 20px', fontSize: 46, lineHeight: '60px', fontWeight: 600, border: `1px solid ${C.grey}`, borderRadius: 12, background: 'rgba(5,7,13,.94)' }}>중대장</div>
    <div style={{ position: 'absolute', left: wide ? 450 : 130, top: wide ? 914 : 1220, width: wide ? 1020 : 740, height: 88,
      display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 4, background: 'rgba(5,7,13,.94)',
      fontSize: 62, fontWeight: 600, lineHeight: 1.2, letterSpacing: '-.025em', whiteSpace: 'nowrap',
      textShadow: '0 0 16px rgba(0,0,0,.9),0 2px 2px rgba(0,0,0,.8)' }}>규정을 어긴 얼차려.</div>
    <div style={{ position: 'absolute', left: wide ? 100 : 130, top: wide ? 826 : 1400, fontSize: 46, fontWeight: 500, lineHeight: '58px', color: '#B8BFCD' }}>개념도 · 실제 배치 아님</div>
  </AbsoluteFill>;
};

// Shared grain is frame-seeded, monochrome, +/-3.5%; it never covers the text.
export const Texture: React.FC = () => {
  const f = useCurrentFrame();
  const {width, height} = useVideoConfig();
  return <AbsoluteFill style={{ pointerEvents: 'none' }}>
    <svg width={width} height={height} style={{ position: 'absolute', inset: 0, opacity: .07, mixBlendMode: 'soft-light' }}>
      <filter id="v4grain"><feTurbulence type="fractalNoise" baseFrequency=".88" numOctaves={1} seed={f+17} stitchTiles="stitch" />
        <feColorMatrix type="saturate" values="0" /></filter>
      <rect width="100%" height="100%" filter="url(#v4grain)" />
    </svg>
    <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 43%, transparent 28%, rgba(5,7,13,.35) 100%)' }} />
  </AbsoluteFill>;
};
