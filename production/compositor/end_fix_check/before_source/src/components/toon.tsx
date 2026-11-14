// Webtoon-style 2D pieces for the "역대급 판결" Shorts: flat night parking lot, line-art car,
// Open Peeps characters (CC0, via react-peeps MIT), comic effects. Stage space is 1000×900.
import React from 'react';
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import Peep from 'react-peeps';
import { FONT } from '../theme';

export const INK = '#141414';
export const PAPER = '#FFFDF6';
export const YELLOW = '#FFD84A';
export const RED = '#F0433A';
export const TEAL = '#21B8B0';
const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };
const ease = Easing.bezier(0.22, 1, 0.36, 1);

export const usePop = (delay = 0, damping = 12) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: f - delay, fps, config: { damping, mass: 0.5, stiffness: 180 } });
};

export const ramp = (f: number, a: number, b: number) => interpolate(f, [a, b], [0, 1], { ...clamp, easing: ease });

// ------------------------------------------------------------------ characters
type PeepPiece = React.ComponentProps<typeof Peep>;
export const Person: React.FC<{
  body: string; face: string; hair?: string; x: number; y: number; h: number; flip?: boolean; rot?: number; full?: boolean; tint?: string;
}> = ({ body, face, hair = 'ShortMessy', x, y, h, flip, rot = 0, full = true, tint = '#fff' }) => {
  const vb = full ? { x: '-100', y: '-50', width: '1600', height: '3150' } : { x: '-50', y: '-30', width: '1100', height: '1250' };
  const w = h * (Number(vb.width) / Number(vb.height));
  return (
    <div style={{ position: 'absolute', left: x - w / 2, top: y - h, width: w, height: h, transform: `rotate(${rot}deg) scaleX(${flip ? -1 : 1})`, transformOrigin: '50% 100%' }}>
      <Peep style={{ width: w, height: h }} viewBox={vb} body={body as PeepPiece['body']} face={face as PeepPiece['face']}
        hair={hair as PeepPiece['hair']} strokeColor={INK} backgroundColor={tint} />
    </div>
  );
};


// ------------------------------------------------------------------ caricature: tiny body, huge wobbling head
// Open Peeps draws the head at the same place for every pose (neck ≈ (450, 560) in peep units),
// so a second, head-only Peep can be laid over it at any scale.
const NECK = { x: 450, y: 560 };
const GROUND: Record<string, number> = { full: 2950, sit: 1980, bust: 1250 };
export const Toon: React.FC<{
  body: string; face: string; hair?: string; x: number; y: number; h: number; kind?: 'full' | 'sit' | 'bust';
  flip?: boolean; rot?: number; head?: number; wobble?: number; squash?: number; pop?: number; tint?: string; accessory?: string;
}> = ({ body, face, hair = 'ShortMessy', x, y, h, kind = 'full', flip, rot = 0, head = 2.3, wobble = 5, squash = 0, pop = 0, tint = '#fff', accessory }) => {
  const f = useCurrentFrame();
  const vb = kind === 'bust' ? { x: -150, y: -50, w: 1200, h: 1300 } : { x: -350, y: -50, w: 1600, h: 3150 };
  const s = h / vb.h;
  const bw = vb.w * s;
  const top = y - (GROUND[kind] - vb.y) * s;
  const neckY = top + (NECK.y - vb.y) * s;
  const K = head * (1 + 0.18 * pop);
  const hb = { x: 230, y: 20, w: 440, h: 560 };
  const hw = hb.w * s * K, hh = hb.h * s * K;
  const tilt = Math.sin(f / 6) * wobble + Math.sin(f / 2.3) * wobble * 0.25;
  const sq = Math.max(-0.4, Math.min(0.5, squash));
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 1000, height: 900, transform: `rotate(${rot}deg)`, transformOrigin: `${x}px ${y}px` }}>
      <div style={{ position: 'absolute', left: x - bw / 2, top, width: bw, height: h, transform: `scaleX(${(flip ? -1 : 1) * (1 + sq * 0.35)}) scaleY(${1 - sq * 0.3})`, transformOrigin: `50% ${((GROUND[kind] - vb.y) / vb.h) * 100}%` }}>
        <Peep style={{ width: bw, height: h }} viewBox={{ x: String(vb.x), y: String(vb.y), width: String(vb.w), height: String(vb.h) }}
          body={body as PeepPiece['body']} face={face as PeepPiece['face']} hair={hair as PeepPiece['hair']} strokeColor={INK} backgroundColor={tint} />
        <div style={{ position: 'absolute', left: (NECK.x - vb.x) * s - hw / 2, top: (NECK.y - vb.y) * s * (1) - (NECK.y - hb.y) * s * K, width: hw, height: hh,
          transform: `rotate(${tilt}deg) scaleY(${1 + sq * 0.25})`, transformOrigin: '50% 92%' }}>
          <Peep style={{ width: hw, height: hh }} viewBox={{ x: String(hb.x), y: String(hb.y), width: String(hb.w), height: String(hb.h) }}
            face={face as PeepPiece['face']} hair={hair as PeepPiece['hair']} accessory={accessory as PeepPiece['accessory']} strokeColor={INK} backgroundColor={tint} />
        </div>
      </div>
      <div style={{ display: 'none' }}>{neckY}</div>
    </div>
  );
};

export const Sweat: React.FC<{ x: number; y: number; at?: number }> = ({ x, y, at = 0 }) => {
  const f = useCurrentFrame();
  const t = ((f - at) % 24) / 24;
  if (f < at) return null;
  return (
    <svg width={1000} height={900} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
      {[0, 1].map((k) => {
        const tt = (t + k * 0.5) % 1;
        return <path key={`sw${k}`} d={`M${x + k * 46},${y + tt * 70} q-16,26 0,34 q16,-8 0,-34 z`} fill="#8FD3FF" stroke={INK} strokeWidth={5} opacity={1 - tt} />;
      })}
    </svg>
  );
};

// ------------------------------------------------------------------ backgrounds
export const NightLot: React.FC<{ glow?: number }> = ({ glow = 1 }) => (
  <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
    <defs>
      <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#1B1440" /><stop offset="1" stopColor="#35307A" /></linearGradient>
      <radialGradient id="lamp" cx="0.5" cy="0" r="1"><stop offset="0" stopColor="rgba(210,255,140,0.55)" /><stop offset="1" stopColor="rgba(210,255,140,0)" /></radialGradient>
    </defs>
    <rect width={1000} height={900} fill="url(#sky)" />
    {Array.from({ length: 26 }, (_, i) => <circle key={`st${i}`} cx={(i * 211) % 1000} cy={(i * 67) % 260 + 10} r={i % 4 === 0 ? 4 : 2} fill="#FFF6C8" opacity={0.8} />)}
    {[[40, 170, 150, 330], [210, 120, 170, 380], [400, 200, 130, 300], [560, 90, 190, 410], [770, 150, 200, 350]].map(([x, y, w, h], i) => (
      <g key={`b${i}`}>
        <rect x={x} y={y} width={w} height={h} fill="#2B2358" stroke={INK} strokeWidth={6} />
        {Array.from({ length: 12 }, (_, k) => (
          <rect key={`w${k}`} x={x + 18 + (k % 3) * (w - 36) / 3} y={y + 24 + Math.floor(k / 3) * 60} width={(w - 60) / 3} height={30}
            fill={(k * 7 + i * 3) % 5 === 0 ? '#FFD86B' : '#3D3577'} stroke={INK} strokeWidth={3} />
        ))}
      </g>
    ))}
    <rect x={0} y={480} width={1000} height={420} fill="#4A4458" stroke={INK} strokeWidth={6} />
    {[-2, -1, 0, 1, 2, 3].map((k) => (
      <line key={`l${k}`} x1={500 + k * 230} y1={480} x2={500 + k * 420} y2={900} stroke="#E9E6DA" strokeWidth={8} opacity={0.75} />
    ))}
    <line x1={0} y1={560} x2={1000} y2={560} stroke="#E9E6DA" strokeWidth={6} opacity={0.5} />
    <rect x={858} y={150} width={14} height={340} fill="#2A2F3A" stroke={INK} strokeWidth={4} />
    <path d="M865 160 Q865 130 830 130 L790 130" stroke={INK} strokeWidth={12} fill="none" />
    <ellipse cx={790} cy={138} rx={34} ry={12} fill="#FFE9A8" stroke={INK} strokeWidth={4} />
    <polygon points="760,140 820,140 980,560 600,560" fill="url(#lamp)" opacity={0.8 * glow} />
  </svg>
);

export const Paper: React.FC<{ color?: string }> = ({ color = '#F4EAD5' }) => (
  <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 40%, ${color} 0%, #E3D3B2 100%)` }}>
    <svg width={1000} height={900} style={{ position: 'absolute', opacity: 0.12 }}>
      {Array.from({ length: 60 }, (_, i) => <circle key={`d${i}`} cx={(i * 173) % 1000} cy={(i * 97) % 900} r={3} fill={INK} />)}
    </svg>
  </AbsoluteFill>
);

// ------------------------------------------------------------------ car (side view, facing +x)
export const Car: React.FC<{ x: number; y: number; scale?: number; lights?: boolean; reverse?: boolean; shake?: number; driver?: boolean }> = ({ x, y, scale = 1, lights = true, reverse, shake = 0, driver = true }) => {
  const f = useCurrentFrame();
  const jy = shake ? Math.sin(f * 2.1) * shake : 0;
  return (
    <svg width={1000} height={900} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
      <g transform={`translate(${x} ${y + jy}) scale(${scale})`}>
        {lights && <polygon points="250,-62 760,-150 760,40 250,-34" fill="rgba(255,236,150,0.42)" />}
        {reverse && <polygon points="-262,-58 -620,-120 -620,30 -262,-30" fill="rgba(255,255,255,0.35)" />}
        <path d="M-262,-20 L-262,-70 Q-255,-95 -205,-102 L-120,-110 L-60,-168 Q-40,-185 0,-186 L110,-186 Q150,-184 175,-160 L225,-112 L240,-108 Q268,-100 268,-70 L268,-22 Q268,-6 250,-6 L-246,-6 Q-262,-6 -262,-20 Z"
          fill="#5B3F8C" stroke={INK} strokeWidth={9} strokeLinejoin="round" />
        <path d="M-95,-112 L-48,-160 Q-34,-172 -10,-172 L40,-172 L40,-112 Z" fill={driver ? '#5B6B86' : '#6F84A6'} stroke={INK} strokeWidth={6} />
        <path d="M56,-112 L56,-172 L104,-172 Q134,-170 150,-152 L188,-112 Z" fill="#6F84A6" stroke={INK} strokeWidth={6} />
        {driver && <g><circle cx={8} cy={-136} r={17} fill="#2C3445" stroke={INK} strokeWidth={4} /><rect x={-8} y={-121} width={34} height={12} rx={6} fill="#2C3445" /></g>}
        <line x1={-20} y1={-104} x2={-20} y2={-14} stroke={INK} strokeWidth={4} />
        <line x1={56} y1={-104} x2={56} y2={-14} stroke={INK} strokeWidth={4} />
        <path d="M232,-86 L266,-80 L266,-62 L236,-64 Z" fill={lights ? '#FFF3B0' : '#BFC5CF'} stroke={INK} strokeWidth={5} />
        <path d="M-262,-86 L-240,-86 L-240,-62 L-262,-62 Z" fill={reverse ? '#FFFFFF' : RED} stroke={INK} strokeWidth={5} />
        {[-160, 160].map((wx) => (
          <g key={`w${wx}`}>
            <circle cx={wx} cy={-6} r={50} fill="#151821" stroke={INK} strokeWidth={8} />
            <circle cx={wx} cy={-6} r={24} fill="#9AA3B2" stroke={INK} strokeWidth={5} />
          </g>
        ))}
      </g>
    </svg>
  );
};

// ------------------------------------------------------------------ effects
export const SpeedLines: React.FC<{ dir?: 'left' | 'right'; opacity?: number }> = ({ dir = 'right', opacity = 1 }) => {
  const f = useCurrentFrame();
  return (
    <svg width={1000} height={900} style={{ position: 'absolute', inset: 0, opacity }}>
      {Array.from({ length: 16 }, (_, i) => {
        const y = 60 + ((i * 131 + f * 23) % 800);
        const len = 160 + (i * 53) % 220;
        const x0 = dir === 'right' ? -40 + ((i * 97 + f * 60) % 600) : 1040 - ((i * 97 + f * 60) % 600);
        return <line key={`s${i}`} x1={x0} y1={y} x2={dir === 'right' ? x0 - len : x0 + len} y2={y} stroke={PAPER} strokeWidth={5} strokeLinecap="round" opacity={0.7} />;
      })}
    </svg>
  );
};

export const Burst: React.FC<{ x: number; y: number; r: number; at?: number; color?: string; text?: string; size?: number }> = ({ x, y, r, at = 0, color = YELLOW, text, size = 110 }) => {
  const p = usePop(at, 9);
  const pts = Array.from({ length: 28 }, (_, i) => {
    const a = (i / 28) * Math.PI * 2;
    const rr = (i % 2 ? 0.62 : 1) * r * p;
    return `${x + Math.cos(a) * rr},${y + Math.sin(a) * rr}`;
  }).join(' ');
  return (
    <>
      <svg width={1000} height={900} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
        <polygon points={pts} fill={color} stroke={INK} strokeWidth={8} strokeLinejoin="round" />
      </svg>
      {text && <Sfx text={text} x={x} y={y} size={size} at={at} rot={-8} />}
    </>
  );
};

export const Sfx: React.FC<{ text: string; x: number; y: number; size?: number; at?: number; color?: string; rot?: number }> = ({ text, x, y, size = 120, at = 0, color = PAPER, rot = -10 }) => {
  const p = usePop(at, 8);
  return (
    <div style={{
      position: 'absolute', left: x, top: y, transform: `translate(-50%, -50%) rotate(${rot}deg) scale(${0.7 + 0.3 * p})`, opacity: Math.min(1, p * 2),
      fontFamily: FONT, fontWeight: 900, fontSize: size, color, WebkitTextStroke: `${Math.round(size / 9)}px ${INK}`, paintOrder: 'stroke fill', whiteSpace: 'nowrap', letterSpacing: '-0.04em',
    }}>{text}</div>
  );
};

export const Bubble: React.FC<{ text: string; x: number; y: number; w?: number; at?: number; tail?: 'left' | 'right' | 'down'; label?: string; dashed?: boolean; size?: number }> = ({ text, x, y, w = 560, at = 0, tail = 'down', label, dashed, size = 52 }) => {
  const p = usePop(at, 11);
  const tailPath = tail === 'down' ? 'M60,100% l30,46 l26,-46' : tail === 'left' ? 'M0,60 l-50,30 l50,10' : 'M100%,60 l50,30 l-50,10';
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: w, transform: `scale(${0.5 + 0.5 * p})`, transformOrigin: tail === 'right' ? '100% 100%' : '0% 100%', opacity: Math.min(1, p * 2) }}>
      {label && <div style={{ display: 'inline-block', fontFamily: FONT, fontWeight: 800, fontSize: 28, color: PAPER, background: INK, padding: '4px 14px', borderRadius: 8, marginBottom: 8 }}>{label}</div>}
      <div style={{
        position: 'relative', background: PAPER, border: `6px ${dashed ? 'dashed' : 'solid'} ${INK}`, borderRadius: 40, padding: '22px 30px',
        fontFamily: FONT, fontWeight: 800, fontSize: size, color: INK, lineHeight: 1.25, letterSpacing: '-0.03em', whiteSpace: 'pre-line',
      }}>
        {text}
        <svg width={120} height={60} style={{ position: 'absolute', left: tail === 'right' ? undefined : 50, right: tail === 'right' ? 50 : undefined, bottom: -52, overflow: 'visible' }}>
          {tailPath && <path d="M10,0 L40,48 L62,0" fill={PAPER} stroke={INK} strokeWidth={6} strokeLinejoin="round" />}
          <rect x={4} y={-8} width={64} height={12} fill={PAPER} />
        </svg>
      </div>
    </div>
  );
};

// Rough Pretendard advance widths (em) — enough to keep a stamp inside its box without measuring the DOM.
const em = (ch: string) => (/[가-힣]/.test(ch) ? 0.93 : /[0-9]/.test(ch) ? 0.6 : ch === ' ' ? 0.26 : 0.55);
export const textEm = (s: string) => [...s].reduce((w, ch) => w + em(ch) - 0.03, 0);

// maxW: the stamp's outer width (border and padding included) never exceeds it; the font shrinks instead.
export const Stamp: React.FC<{ lines: string[]; at?: number; color?: string; x?: number; y?: number; size?: number; rot?: number; maxW?: number }> = ({ lines, at = 0, color = RED, x = 500, y = 450, size = 120, rot = -9, maxW = 860 }) => {
  const p = usePop(at, 9);
  const need = Math.max(...lines.map((l, i) => textEm(l) * (i === 0 ? 1 : 0.62)));
  const fs = Math.min(size, (maxW - 104) / need);
  return (
    <div style={{ position: 'absolute', left: x, top: y, transform: `translate(-50%, -50%) rotate(${rot}deg) scale(${1.12 - 0.12 * p})`, opacity: Math.min(1, p * 2), textAlign: 'center' }}>
      <div style={{ border: `12px solid ${color}`, borderRadius: 24, padding: '10px 40px', background: 'rgba(255,253,246,0.94)' }}>
        {lines.map((l, i) => (
          <div key={l} style={{ fontFamily: FONT, fontWeight: 800, fontSize: i === 0 ? fs : fs * 0.62, color, lineHeight: 1.12, letterSpacing: '-0.03em', whiteSpace: 'nowrap' }}>{l}</div>
        ))}
      </div>
    </div>
  );
};

export const Shake: React.FC<{ at: number; len?: number; amp?: number; children: React.ReactNode }> = ({ at, len = 10, amp = 14, children }) => {
  const f = useCurrentFrame();
  const k = f >= at && f < at + len ? (1 - (f - at) / len) * amp : 0;
  // zoom in with the shake so the set's edges never show behind it
  return <AbsoluteFill style={{ transform: `translate(${Math.sin(f * 3.1) * k}px, ${Math.cos(f * 2.3) * k}px) scale(${1 + (0.034 * k) / Math.max(1, amp)})` }}>{children}</AbsoluteFill>;
};

export const Flash: React.FC<{ at: number; color?: string; len?: number }> = ({ at, color = '#fff', len = 8 }) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{ backgroundColor: color, opacity: interpolate(f, [at, at + 1, at + len], [0, 0.45, 0], clamp), pointerEvents: 'none' }} />;
};
