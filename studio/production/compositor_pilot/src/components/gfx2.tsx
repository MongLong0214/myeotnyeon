// v2 "light cut" overlays: one idea per screen, 1–4 words, big type, quick pop-in.
// Owner direction 2026-10-26: no wall-of-text cards, fast rhythm, easy to follow.
import React from 'react';
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { C, FONT, SERIF } from '../theme';
import { Tag } from './gfx';

const ease = Easing.bezier(0.22, 1, 0.36, 1);
const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };
const AMBER = C.amberBright;
const TEAL = C.tealBright;
const RED = '#E4685A';
const SHADOW = '0 4px 18px rgba(0,0,0,0.85), 0 0 2px rgba(0,0,0,0.9)';

const usePop = (delay = 0, damping = 13) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: f - delay, fps, config: { damping, mass: 0.55, stiffness: 170 } });
};

const useFadeIn = (delay = 0, dur = 8) => {
  const f = useCurrentFrame();
  return interpolate(f - delay, [0, dur], [0, 1], { ...clamp, easing: ease });
};

// ------------------------------------------------------------------ big kinetic words
export type Line = { t: string; c?: string; s?: number; at?: number; serif?: boolean };
export const BigText: React.FC<{ lines: Line[]; y?: number; box?: boolean; kicker?: string; tag?: string }> = ({ lines, y = 400, box, kicker, tag }) => {
  const k = useFadeIn(0, 8);
  return (
    <AbsoluteFill>
      <div style={{ position: 'absolute', left: 0, right: 0, top: y, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
        {tag && <div style={{ opacity: k, marginBottom: 14 }}><Tag kind={tag} size={28} /></div>}
        {kicker && <div style={{ fontFamily: FONT, fontSize: 40, fontWeight: 700, color: AMBER, opacity: k, textShadow: SHADOW, marginBottom: 6 }}>{kicker}</div>}
        {lines.map((l, i) => <PopLine key={i} l={l} i={i} box={box} />)}
      </div>
    </AbsoluteFill>
  );
};

const PopLine: React.FC<{ l: Line; i: number; box?: boolean }> = ({ l, i, box }) => {
  const p = usePop(l.at ?? i * 5);
  return (
    <div style={{
      fontFamily: l.serif ? SERIF : FONT, fontSize: l.s ?? 110, fontWeight: 800, color: l.c ?? C.paper, letterSpacing: '-0.03em',
      lineHeight: 1.12, textShadow: SHADOW, transform: `scale(${0.6 + 0.4 * p})`, opacity: Math.min(1, p * 1.4), whiteSpace: 'pre-line', textAlign: 'center',
      background: box ? 'rgba(6,10,14,0.72)' : undefined, padding: box ? '6px 30px' : undefined, borderRadius: box ? 14 : undefined,
    }}>{l.t}</div>
  );
};

// ------------------------------------------------------------------ count-up number
export const Counter: React.FC<{ to: number; label: string; note?: string; y?: number; at?: number }> = ({ to, label, note, y = 600, at = 0 }) => {
  const f = useCurrentFrame();
  const v = Math.round(interpolate(f - at, [0, 26], [0, to], { ...clamp, easing: ease }));
  const o = useFadeIn(at, 8);
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, top: y, textAlign: 'center', opacity: o }}>
      <span style={{ fontFamily: FONT, fontSize: 44, fontWeight: 600, color: 'rgba(243,241,233,0.8)', textShadow: SHADOW }}>{label} </span>
      <span style={{ fontFamily: FONT, fontSize: 76, fontWeight: 800, color: AMBER, textShadow: SHADOW }}>{v.toLocaleString('ko-KR')}</span>
      {note && <div style={{ fontFamily: FONT, fontSize: 28, color: 'rgba(243,241,233,0.62)', marginTop: 8 }}>{note}</div>}
    </div>
  );
};

// ------------------------------------------------------------------ rumour vs fact
export const Myth: React.FC<{ rumor: string; facts: { t: string; at: number }[]; src?: string }> = ({ rumor, facts, src }) => {
  const f = useCurrentFrame();
  const p = usePop(0);
  const strikeAt = facts.length ? facts[0].at : 9999;
  const strike = interpolate(f - strikeAt, [0, 10], [0, 1], { ...clamp, easing: ease });
  return (
    <AbsoluteFill>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 250, textAlign: 'center' }}>
        <div style={{ display: 'inline-block', fontFamily: FONT, fontSize: 34, fontWeight: 800, color: '#0b0f12', background: C.grey, padding: '4px 18px', borderRadius: 8, opacity: p }}>커뮤니티 소문</div>
        <div style={{ position: 'relative', display: 'block', marginTop: 18 }}>
          <span style={{ position: 'relative', display: 'inline-block', fontFamily: FONT, fontSize: 92, fontWeight: 800, color: C.paper, textShadow: SHADOW, transform: `scale(${0.7 + 0.3 * p})`, opacity: 1 - 0.45 * strike }}>
            {rumor}
            <span style={{ position: 'absolute', left: -10, top: '52%', height: 10, width: `${strike * 104}%`, background: RED, borderRadius: 5 }} />
          </span>
        </div>
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 560, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 22 }}>
        {facts.map((x, i) => <FactRow key={i} t={x.t} at={x.at} />)}
      </div>
      {src && <div style={{ position: 'absolute', right: 96, bottom: 150, fontFamily: FONT, fontSize: 26, color: 'rgba(243,241,233,0.55)' }}>{src}</div>}
    </AbsoluteFill>
  );
};

const FactRow: React.FC<{ t: string; at: number }> = ({ t, at }) => {
  const p = usePop(at, 11);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 20, opacity: Math.min(1, p * 1.5), transform: `translateY(${(1 - p) * 30}px)` }}>
      <span style={{ fontFamily: FONT, fontSize: 34, fontWeight: 800, color: '#0b0f12', background: TEAL, padding: '4px 16px', borderRadius: 8 }}>보도 확인</span>
      <span style={{ fontFamily: FONT, fontSize: 64, fontWeight: 800, color: C.paper, textShadow: SHADOW }}>{t}</span>
    </div>
  );
};

// ------------------------------------------------------------------ the court's scales
export type Weight = { t: string; at: number };
export const Scale: React.FC<{ left: Weight[]; right: Weight[]; leftLabel: string; rightLabel: string }> = ({ left, right, leftLabel, rightLabel }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const shown = (ws: Weight[]) => ws.reduce((n, w) => n + spring({ frame: f - w.at, fps, config: { damping: 14 } }), 0);
  const tilt = Math.max(-9, Math.min(9, (shown(left) - shown(right)) * 3.2));
  const intro = usePop(0, 16);
  const cx = 960, top = 300, arm = 520;
  const rad = (tilt * Math.PI) / 180;
  const ly = top + Math.sin(rad) * arm, ry = top - Math.sin(rad) * arm;
  return (
    <AbsoluteFill style={{ opacity: intro }}>
      <svg width={1920} height={1080} style={{ position: 'absolute' }}>
        <line x1={cx} y1={top - 10} x2={cx} y2={900} stroke="rgba(243,241,233,0.8)" strokeWidth={10} strokeLinecap="round" />
        <polygon points={`${cx - 120},905 ${cx + 120},905 ${cx},860`} fill="rgba(243,241,233,0.8)" />
        <line x1={cx - Math.cos(rad) * arm} y1={ly} x2={cx + Math.cos(rad) * arm} y2={ry} stroke={C.paper} strokeWidth={12} strokeLinecap="round" />
        <circle cx={cx} cy={top} r={18} fill={AMBER} />
        <line x1={cx - Math.cos(rad) * arm} y1={ly} x2={cx - Math.cos(rad) * arm} y2={ly + 70} stroke="rgba(243,241,233,0.6)" strokeWidth={4} />
        <line x1={cx + Math.cos(rad) * arm} y1={ry} x2={cx + Math.cos(rad) * arm} y2={ry + 70} stroke="rgba(243,241,233,0.6)" strokeWidth={4} />
      </svg>
      <Pan x={cx - Math.cos(rad) * arm} y={ly + 70} label={leftLabel} color={RED} items={left} />
      <Pan x={cx + Math.cos(rad) * arm} y={ry + 70} label={rightLabel} color={TEAL} items={right} />
    </AbsoluteFill>
  );
};

const Pan: React.FC<{ x: number; y: number; label: string; color: string; items: Weight[] }> = ({ x, y, label, color, items }) => (
  <div style={{ position: 'absolute', left: x - 280, top: y, width: 560, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
    <div style={{ width: 460, height: 14, borderRadius: 7, background: color }} />
    <div style={{ fontFamily: FONT, fontSize: 40, fontWeight: 800, color, marginTop: 10, textShadow: SHADOW }}>{label}</div>
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, marginTop: 12 }}>
      {items.map((w, i) => <WeightChip key={i} w={w} color={color} />)}
    </div>
  </div>
);

const WeightChip: React.FC<{ w: Weight; color: string }> = ({ w, color }) => {
  const p = usePop(w.at, 12);
  return (
    <div style={{
      fontFamily: FONT, fontSize: 38, fontWeight: 700, color: C.paper, background: 'rgba(6,10,14,0.85)', border: `3px solid ${color}`,
      borderRadius: 12, padding: '6px 20px', opacity: Math.min(1, p * 1.5), transform: `translateY(${(1 - p) * -60}px)`, whiteSpace: 'nowrap',
    }}>{w.t}</div>
  );
};

// ------------------------------------------------------------------ 10 people, x% filled
export const Persons: React.FC<{ pct: number; big: string; label: string; note?: string }> = ({ pct, big, label, note }) => {
  const f = useCurrentFrame();
  const fill = interpolate(f, [6, 40], [0, pct], { ...clamp, easing: ease });   // pct = filled people out of 10
  const b = usePop(30);
  return (
    <AbsoluteFill>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 230, display: 'flex', justifyContent: 'center', gap: 34 }}>
        {Array.from({ length: 10 }, (_, i) => {
          const part = Math.max(0, Math.min(1, fill - i));
          return <Person key={`p${i}`} part={part} />;
        })}
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 560, textAlign: 'center' }}>
        <div style={{ fontFamily: FONT, fontSize: 150, fontWeight: 800, color: AMBER, textShadow: SHADOW, transform: `scale(${0.6 + 0.4 * b})`, opacity: b }}>{big}</div>
        <div style={{ fontFamily: FONT, fontSize: 46, fontWeight: 700, color: C.paper, textShadow: SHADOW, opacity: b }}>{label}</div>
        {note && <div style={{ fontFamily: FONT, fontSize: 28, color: 'rgba(243,241,233,0.6)', marginTop: 10, opacity: b }}>{note}</div>}
      </div>
    </AbsoluteFill>
  );
};

const Person: React.FC<{ part: number }> = ({ part }) => (
  <svg width={110} height={250} viewBox="0 0 110 250">
    <defs>
      <clipPath id={`clip${Math.round(part * 1000)}`}><rect x={0} y={0} width={110 * part} height={250} /></clipPath>
    </defs>
    <g fill="rgba(243,241,233,0.22)"><circle cx={55} cy={34} r={30} /><rect x={15} y={74} width={80} height={170} rx={30} /></g>
    <g fill={AMBER} clipPath={`url(#clip${Math.round(part * 1000)})`}><circle cx={55} cy={34} r={30} /><rect x={15} y={74} width={80} height={170} rx={30} /></g>
  </svg>
);

// ------------------------------------------------------------------ two cases side by side
export type Tile = { title: string; sub?: string; rows: { k: string; v: string; hl?: boolean }[]; tag?: string };
export const Compare: React.FC<{ tiles: Tile[] }> = ({ tiles }) => (
  <AbsoluteFill>
    <div style={{ position: 'absolute', left: 120, right: 120, top: 190, display: 'flex', gap: 60, justifyContent: 'center' }}>
      {tiles.map((t, i) => <CompareTile key={i} t={t} i={i} />)}
    </div>
  </AbsoluteFill>
);

const CompareTile: React.FC<{ t: Tile; i: number }> = ({ t, i }) => {
  const p = usePop(i * 10);
  return (
    <div style={{ width: 760, background: 'rgba(6,10,14,0.86)', border: `3px solid ${i === 0 ? AMBER : 'rgba(243,241,233,0.35)'}`, borderRadius: 18, padding: '28px 36px', opacity: p, transform: `translateY(${(1 - p) * 40}px)` }}>
      {t.tag && <div style={{ marginBottom: 10 }}><Tag kind={t.tag} size={24} /></div>}
      <div style={{ fontFamily: FONT, fontSize: 48, fontWeight: 800, color: i === 0 ? AMBER : C.paper }}>{t.title}</div>
      {t.sub && <div style={{ fontFamily: FONT, fontSize: 30, color: 'rgba(243,241,233,0.7)', marginTop: 6, lineHeight: 1.35 }}>{t.sub}</div>}
      <div style={{ marginTop: 18 }}>
        {t.rows.map((r) => (
          <div key={r.k} style={{ display: 'flex', alignItems: 'baseline', gap: 18, padding: '10px 0', borderTop: '1px solid rgba(243,241,233,0.18)' }}>
            <span style={{ fontFamily: FONT, fontSize: 30, color: 'rgba(243,241,233,0.62)', minWidth: 120 }}>{r.k}</span>
            <span style={{ fontFamily: FONT, fontSize: 44, fontWeight: 800, color: r.hl ? AMBER : C.paper }}>{r.v}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ sentence on a 0–10 year axis
export const NumberLine: React.FC<{ rangeAt?: number; markAt?: number; zoneAt?: number }> = ({ rangeAt = 0, markAt = 9999, zoneAt = 9999 }) => {
  const f = useCurrentFrame();
  const x0 = 200, x1 = 1720, y = 560;
  const X = (yr: number) => x0 + (x1 - x0) * (yr / 10);
  const r = interpolate(f - rangeAt, [0, 18], [0, 1], { ...clamp, easing: ease });
  const m = usePop(markAt, 12);
  const z = interpolate(f - zoneAt, [0, 14], [0, 1], { ...clamp, easing: ease });
  const axis = useFadeIn(0, 8);
  return (
    <AbsoluteFill>
      <svg width={1920} height={1080} style={{ position: 'absolute', opacity: axis }}>
        <rect x={X(0)} y={y - 60} width={(X(3) - X(0)) * z} height={120} fill="rgba(63,182,192,0.22)" rx={10} />
        <line x1={x0} y1={y} x2={x1} y2={y} stroke="rgba(243,241,233,0.45)" strokeWidth={4} />
        {[0, 1, 3, 5, 10].map((v) => <line key={v} x1={X(v)} y1={y - 14} x2={X(v)} y2={y + 14} stroke="rgba(243,241,233,0.6)" strokeWidth={3} />)}
        <line x1={X(1)} y1={y} x2={X(1) + (X(10) - X(1)) * r} y2={y} stroke={RED} strokeWidth={22} strokeLinecap="round" />
        <line x1={X(8 / 12)} y1={y - 120 + (1 - m) * -40} x2={X(8 / 12)} y2={y - 6} stroke={AMBER} strokeWidth={6} opacity={m} />
        <circle cx={X(8 / 12)} cy={y} r={20 * m} fill={AMBER} />
      </svg>
      {[0, 1, 3, 5, 10].map((v) => (
        <div key={v} style={{ position: 'absolute', left: X(v) - 60, width: 120, top: y + 30, textAlign: 'center', fontFamily: FONT, fontSize: 32, color: 'rgba(243,241,233,0.8)', opacity: axis }}>{v === 0 ? '0' : `${v}년`}</div>
      ))}
      <div style={{ position: 'absolute', left: X(5.5) - 300, width: 600, top: y - 130, textAlign: 'center', fontFamily: FONT, fontSize: 52, fontWeight: 800, color: RED, textShadow: SHADOW, opacity: r }}>법정형 1~10년</div>
      <div style={{ position: 'absolute', left: X(8 / 12) - 160, width: 320, top: y - 230, textAlign: 'center', fontFamily: FONT, fontSize: 56, fontWeight: 800, color: AMBER, textShadow: SHADOW, opacity: m }}>선고 8개월</div>
      <div style={{ position: 'absolute', left: X(0), width: X(3) - X(0), top: y + 100, textAlign: 'center', fontFamily: FONT, fontSize: 40, fontWeight: 800, color: TEAL, textShadow: SHADOW, opacity: z }}>3년 이하 → 집행유예 가능</div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ 8 months, deferred for 2 years
export const Defer: React.FC<{ voidAt?: number }> = ({ voidAt = 9999 }) => {
  const f = useCurrentFrame();
  const a = usePop(0, 14);
  const bar = interpolate(f, [12, 40], [0, 1], { ...clamp, easing: ease });
  const v = usePop(voidAt, 12);
  return (
    <AbsoluteFill>
      <div style={{ position: 'absolute', left: 230, top: 330, display: 'flex', alignItems: 'center', gap: 40 }}>
        <div style={{ fontFamily: FONT, fontSize: 64, fontWeight: 800, color: '#0b0f12', background: AMBER, borderRadius: 16, padding: '14px 34px', transform: `scale(${0.6 + 0.4 * a})`, opacity: a }}>징역 8개월</div>
        <div style={{ fontFamily: FONT, fontSize: 56, fontWeight: 800, color: C.paper, opacity: bar, textShadow: SHADOW }}>➜ 2년 동안 보류</div>
      </div>
      <div style={{ position: 'absolute', left: 230, top: 520, width: 1460, height: 26, borderRadius: 13, background: 'rgba(243,241,233,0.15)' }}>
        <div style={{ width: `${bar * 100}%`, height: '100%', borderRadius: 13, background: TEAL }} />
      </div>
      <div style={{ position: 'absolute', left: 230, top: 560, fontFamily: FONT, fontSize: 34, color: 'rgba(243,241,233,0.75)', opacity: bar }}>집행유예 2년 · 사회봉사 120시간</div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 690, textAlign: 'center', opacity: v, transform: `translateY(${(1 - v) * 30}px)` }}>
        <span style={{ fontFamily: FONT, fontSize: 46, fontWeight: 800, color: C.paper, background: 'rgba(228,104,90,0.25)', border: `3px solid ${RED}`, borderRadius: 14, padding: '10px 28px' }}>
          그사이 고의 범죄로 실형 확정 → 유예 효력 상실
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ check / cross list
export const Checks: React.FC<{ items: { t: string; ok: boolean; at: number }[]; y?: number; tag?: string }> = ({ items, y = 360, tag }) => (
  <AbsoluteFill>
    <div style={{ position: 'absolute', left: 0, right: 0, top: y, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 26 }}>
      {tag && <Tag kind={tag} size={28} />}
      {items.map((it, i) => <CheckRow key={i} t={it.t} ok={it.ok} at={it.at} />)}
    </div>
  </AbsoluteFill>
);

const CheckRow: React.FC<{ t: string; ok: boolean; at: number }> = ({ t, ok, at }) => {
  const p = usePop(at, 11);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 26, opacity: Math.min(1, p * 1.5), transform: `scale(${0.7 + 0.3 * p})` }}>
      <span style={{ width: 96, height: 96, borderRadius: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', background: ok ? TEAL : RED, fontFamily: FONT, fontSize: 64, fontWeight: 900, color: '#0b0f12' }}>{ok ? '✓' : '✕'}</span>
      <span style={{ fontFamily: FONT, fontSize: 84, fontWeight: 800, color: C.paper, textShadow: SHADOW }}>{t}</span>
    </div>
  );
};

// ------------------------------------------------------------------ A vs B split
export const Split: React.FC<{ left: string; right: string; q?: string; qAt?: number }> = ({ left, right, q, qAt = 9999 }) => {
  const l = usePop(0);
  const r = usePop(8);
  const qq = usePop(qAt, 10);
  return (
    <AbsoluteFill>
      <div style={{ position: 'absolute', left: 0, width: 960, top: 380, textAlign: 'center', fontFamily: FONT, fontSize: 140, fontWeight: 900, color: RED, textShadow: SHADOW, transform: `translateX(${(1 - l) * -200}px)`, opacity: l }}>{left}</div>
      <div style={{ position: 'absolute', left: 960, width: 960, top: 380, textAlign: 'center', fontFamily: FONT, fontSize: 140, fontWeight: 900, color: TEAL, textShadow: SHADOW, transform: `translateX(${(1 - r) * 200}px)`, opacity: r }}>{right}</div>
      <div style={{ position: 'absolute', left: 955, top: 300, width: 10, height: 420, background: 'rgba(243,241,233,0.5)', borderRadius: 5, opacity: Math.min(l, r) }} />
      <div style={{ position: 'absolute', left: 900, width: 120, top: 455, textAlign: 'center', fontFamily: FONT, fontSize: 52, fontWeight: 900, color: C.paper, background: '#0b0f12', borderRadius: 60, padding: '10px 0', opacity: Math.min(l, r) }}>VS</div>
      {q && <div style={{ position: 'absolute', left: 0, right: 0, top: 700, textAlign: 'center', fontFamily: FONT, fontSize: 72, fontWeight: 800, color: AMBER, textShadow: SHADOW, opacity: qq, transform: `scale(${0.7 + 0.3 * qq})` }}>{q}</div>}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ claim bubble (party claims stay labelled)
export const Quote: React.FC<{ lines: { t: string; at: number }[]; tag: string; y?: number }> = ({ lines, tag, y = 300 }) => {
  const k = useFadeIn(0, 8);
  return (
    <AbsoluteFill>
      <div style={{ position: 'absolute', left: 0, right: 0, top: y, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24 }}>
        <div style={{ opacity: k }}><Tag kind={tag} size={30} /></div>
        {lines.map((l, i) => <QuoteLine key={i} t={l.t} at={l.at} />)}
      </div>
    </AbsoluteFill>
  );
};

const QuoteLine: React.FC<{ t: string; at: number }> = ({ t, at }) => {
  const p = usePop(at, 12);
  return (
    <div style={{
      fontFamily: FONT, fontSize: 64, fontWeight: 800, color: C.paper, background: 'rgba(6,10,14,0.82)', border: `3px dashed ${AMBER}`,
      borderRadius: 22, padding: '14px 36px', opacity: Math.min(1, p * 1.5), transform: `scale(${0.75 + 0.25 * p})`, textShadow: SHADOW,
    }}>“{t}”</div>
  );
};

// ------------------------------------------------------------------ 112 tip
export const Tip112: React.FC<{ chipsAt?: number }> = ({ chipsAt = 20 }) => {
  const p = usePop(0, 12);
  return (
    <AbsoluteFill>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 210, textAlign: 'center' }}>
        <div style={{ fontFamily: FONT, fontSize: 40, fontWeight: 700, color: 'rgba(243,241,233,0.82)', opacity: p }}>음주운전 의심 차량을 봤다면</div>
        <div style={{ fontFamily: FONT, fontSize: 220, fontWeight: 900, color: AMBER, lineHeight: 1.05, textShadow: SHADOW, transform: `scale(${0.6 + 0.4 * p})`, opacity: p }}>112</div>
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 620, display: 'flex', justifyContent: 'center', gap: 34 }}>
        {['위치', '진행 방향', '차량 번호'].map((t, i) => <TipChip key={t} t={t} at={chipsAt + i * 7} />)}
      </div>
    </AbsoluteFill>
  );
};

const TipChip: React.FC<{ t: string; at: number }> = ({ t, at }) => {
  const p = usePop(at, 12);
  return <div style={{ fontFamily: FONT, fontSize: 54, fontWeight: 800, color: '#0b0f12', background: C.paper, borderRadius: 16, padding: '12px 34px', opacity: Math.min(1, p * 1.5), transform: `translateY(${(1 - p) * 40}px)` }}>{t}</div>;
};

// ------------------------------------------------------------------ small corner label (epistemic tag + optional text)
export const Corner: React.FC<{ kind: string; text?: string }> = ({ kind, text }) => {
  const o = useFadeIn(0, 8);
  return (
    <div style={{ position: 'absolute', left: 80, top: 60, display: 'flex', alignItems: 'center', gap: 14, opacity: o }}>
      <Tag kind={kind} size={26} />
      {text && <span style={{ fontFamily: FONT, fontSize: 28, fontWeight: 600, color: 'rgba(243,241,233,0.85)', textShadow: SHADOW }}>{text}</span>}
    </div>
  );
};

// ------------------------------------------------------------------ bottom-left date/place stamp
export const Dateline: React.FC<{ lines: string[] }> = ({ lines }) => {
  const o = useFadeIn(0, 10);
  return (
    <div style={{ position: 'absolute', left: 80, top: 120, opacity: o }}>
      {lines.map((l, i) => (
        <div key={l} style={{ fontFamily: FONT, fontSize: i === 0 ? 46 : 32, fontWeight: i === 0 ? 800 : 600, color: i === 0 ? C.paper : 'rgba(243,241,233,0.8)', textShadow: SHADOW, marginTop: i ? 6 : 0 }}>{l}</div>
      ))}
    </div>
  );
};

// ------------------------------------------------------------------ big rotated stamp
export const BigStamp: React.FC<{ t: string; color?: string; sub?: string }> = ({ t, color = RED, sub }) => {
  const p = usePop(0, 9);
  return (
    <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ transform: `rotate(-8deg) scale(${2.2 - 1.2 * p})`, opacity: Math.min(1, p * 2), textAlign: 'center' }}>
        <div style={{ fontFamily: FONT, fontSize: 190, fontWeight: 900, color, border: `14px solid ${color}`, borderRadius: 28, padding: '0 60px', textShadow: SHADOW }}>{t}</div>
        {sub && <div style={{ fontFamily: FONT, fontSize: 44, fontWeight: 700, color: C.paper, marginTop: 24, textShadow: SHADOW }}>{sub}</div>}
      </div>
    </AbsoluteFill>
  );
};
