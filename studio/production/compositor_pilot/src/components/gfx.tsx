import React from 'react';
import {
  AbsoluteFill, Easing, interpolate, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';
import { C, FONT, SERIF, TAGS } from '../theme';

const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const useEnter = (delay = 0, dur = 14) => {
  const f = useCurrentFrame();
  const t = interpolate(f - delay, [0, dur], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease });
  return { opacity: t, y: (1 - t) * 18, t };
};
const useExit = (outAt?: number, dur = 10) => {
  const f = useCurrentFrame();
  if (outAt === undefined) return 1;
  return interpolate(f, [outAt - dur, outAt], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
};

// ------------------------------------------------------------------ plate
export const Plate: React.FC<{ src: string; startFrom?: number; dim?: number; blur?: number; zoom?: [number, number]; playbackRate?: number }> = ({ src, startFrom = 0, dim = 0, blur = 0, zoom, playbackRate = 1 }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const z = zoom ? interpolate(f, [0, durationInFrames], zoom) : 1;
  return (
    <AbsoluteFill style={{ backgroundColor: '#05080b' }}>
      <AbsoluteFill style={{ transform: `scale(${z})`, filter: blur ? `blur(${blur}px)` : undefined }}>
        <OffthreadVideo src={staticFile(src)} startFrom={startFrom} muted playbackRate={playbackRate} style={{ width: '100%', height: '100%' }} />
      </AbsoluteFill>
      {dim > 0 && <AbsoluteFill style={{ backgroundColor: `rgba(4,8,12,${dim})` }} />}
    </AbsoluteFill>
  );
};

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.55 }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,${strength}) 100%)` }} />
);

export const Fade: React.FC<{ inF?: number; outF?: number; color?: string }> = ({ inF = 0, outF = 0, color = '#000' }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  let o = 0;
  if (inF > 0) o = Math.max(o, interpolate(f, [0, inF], [1, 0], { extrapolateRight: 'clamp' }));
  if (outF > 0) o = Math.max(o, interpolate(f, [durationInFrames - outF, durationInFrames], [0, 1], { extrapolateLeft: 'clamp' }));
  return <AbsoluteFill style={{ backgroundColor: color, opacity: o }} />;
};

// ------------------------------------------------------------------ tags / hud
export const Tag: React.FC<{ kind: keyof typeof TAGS | string; size?: number; style?: React.CSSProperties }> = ({ kind, size = 26, style }) => {
  const t = TAGS[kind] ?? { label: kind, color: C.paper };
  return (
    <span style={{
      fontFamily: FONT, fontSize: size, fontWeight: 600, color: t.color, letterSpacing: '-0.01em',
      border: `2px ${t.dashed ? 'dashed' : 'solid'} ${t.color}`, borderRadius: 6, padding: '3px 12px',
      background: 'rgba(5,10,14,0.62)', whiteSpace: 'nowrap', ...style,
    }}>[{t.label}]</span>
  );
};

export const Hud: React.FC<{ left?: string; tag?: string; right?: string }> = ({ left, tag, right }) => {
  const e = useEnter(4, 12);
  return (
    <div style={{ position: 'absolute', top: 58, left: 96, right: 96, display: 'flex', alignItems: 'center', gap: 16, opacity: e.opacity }}>
      {left && <span style={{ fontFamily: FONT, fontSize: 28, fontWeight: 500, color: 'rgba(243,241,233,0.86)', textShadow: '0 2px 8px rgba(0,0,0,0.8)' }}>{left}</span>}
      {tag && <Tag kind={tag} size={24} />}
      <span style={{ flex: 1 }} />
      {right && <span style={{ fontFamily: FONT, fontSize: 24, fontWeight: 500, color: 'rgba(243,241,233,0.7)' }}>{right}</span>}
    </div>
  );
};

// ------------------------------------------------------------------ subtitles
export type Sub = { from: number; to: number; text: string };
export const Subtitles: React.FC<{ subs: Sub[]; offset?: number }> = ({ subs, offset = 0 }) => {
  const f = useCurrentFrame() + offset;
  const s = subs.find((x) => f >= x.from && f < x.to);
  if (!s) return null;
  return (
    <div style={{ position: 'absolute', left: 96, right: 96, bottom: 1080 - 1000, display: 'flex', justifyContent: 'center' }}>
      <div style={{
        fontFamily: FONT, fontSize: 46, lineHeight: 1.38, fontWeight: 600, color: '#FAF8F2', textAlign: 'center',
        padding: '8px 22px', borderRadius: 8, background: 'rgba(4,8,12,0.55)', letterSpacing: '-0.015em',
        textShadow: '0 2px 6px rgba(0,0,0,0.9)', whiteSpace: 'pre-line', maxWidth: 1500,
      }}>{s.text}</div>
    </div>
  );
};

// ------------------------------------------------------------------ stamp (time/place)
export const Stamp: React.FC<{ lines: string[]; pos?: 'tl' | 'bl' | 'tc'; delay?: number }> = ({ lines, pos = 'bl', delay = 6 }) => {
  const f = useCurrentFrame();
  const style: React.CSSProperties = pos === 'bl' ? { left: 96, bottom: 230 } : pos === 'tl' ? { left: 96, top: 140 } : { left: 0, right: 0, top: 150, textAlign: 'center' };
  let acc = 0;
  return (
    <div style={{ position: 'absolute', ...style }}>
      {lines.map((ln, i) => {
        const start = delay + acc; acc += ln.length * 1.6 + 8;
        const n = Math.max(0, Math.min(ln.length, Math.floor((f - start) / 1.6)));
        return (
          <div key={i} style={{ fontFamily: SERIF, fontSize: i === 0 ? 40 : 30, fontWeight: i === 0 ? 600 : 400, color: i === 0 ? C.paper : 'rgba(243,241,233,0.75)', textShadow: '0 2px 10px rgba(0,0,0,0.9)', marginBottom: 6 }}>
            {ln.slice(0, n)}<span style={{ opacity: n < ln.length && f > start ? 1 : 0 }}>▍</span>
          </div>
        );
      })}
    </div>
  );
};

// ------------------------------------------------------------------ chapter card
export const Chapter: React.FC<{ no: string; title: string; sub?: string }> = ({ no, title, sub }) => {
  const e = useEnter(2, 16);
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const out = interpolate(f, [durationInFrames - 8, durationInFrames], [1, 0], { extrapolateLeft: 'clamp' });
  return (
    <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 45%, #13222c 0%, #070b0f 70%)', alignItems: 'center', justifyContent: 'center', opacity: out }}>
      <div style={{ textAlign: 'center', opacity: e.opacity, transform: `translateY(${e.y}px)` }}>
        <div style={{ fontFamily: FONT, fontSize: 34, fontWeight: 700, color: C.tealBright, letterSpacing: '0.3em', marginBottom: 18 }}>{no}</div>
        <div style={{ fontFamily: SERIF, fontSize: 92, fontWeight: 700, color: C.paper, letterSpacing: '-0.01em' }}>{title}</div>
        {sub && <div style={{ fontFamily: FONT, fontSize: 32, color: 'rgba(243,241,233,0.65)', marginTop: 20 }}>{sub}</div>}
        <div style={{ width: interpolate(e.t, [0, 1], [0, 220]), height: 2, background: C.amber, margin: '28px auto 0' }} />
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ cards
export type Row = { k?: string; v: string; state?: 'ok' | 'dispute' | 'unknown' | 'no' | 'hl'; delay?: number; small?: string };
const stateColor = (s?: Row['state']) => s === 'ok' ? C.tealBright : s === 'dispute' ? C.amberBright : s === 'unknown' ? C.grey : s === 'no' ? '#C9776A' : s === 'hl' ? C.amberBright : C.paper;
const stateMark = (s?: Row['state']) => s === 'ok' ? '●' : s === 'dispute' ? '◐' : s === 'unknown' ? '○' : s === 'no' ? '×' : '';

export const Card: React.FC<{
  x?: number; y?: number; w?: number; tag?: string; title?: string; rows?: Row[]; delay?: number; serif?: boolean;
  titleSize?: number; rowSize?: number; outAt?: number; footer?: string; center?: boolean;
}> = ({ x = 96, y = 170, w = 760, tag, title, rows = [], delay = 0, serif, titleSize = 50, rowSize = 36, outAt, footer, center }) => {
  const e = useEnter(delay);
  const f = useCurrentFrame();
  const out = useExit(outAt);
  return (
    <div style={{
      position: 'absolute', left: center ? (1920 - w) / 2 : x, top: y, width: w, opacity: e.opacity * out, transform: `translateY(${e.y}px)`,
      background: C.glass, border: `1px solid ${C.line}`, borderRadius: 14, padding: '26px 32px 28px', boxShadow: '0 20px 60px rgba(0,0,0,0.45)',
    }}>
      {tag && <div style={{ marginBottom: 16 }}><Tag kind={tag} size={24} /></div>}
      {title && <div style={{ fontFamily: serif ? SERIF : FONT, fontSize: titleSize, fontWeight: 700, color: C.paper, lineHeight: 1.25, letterSpacing: '-0.02em', marginBottom: rows.length ? 18 : 0, whiteSpace: 'pre-line' }}>{title}</div>}
      {rows.map((r, i) => {
        const d = (r.delay ?? delay + 8 + i * 8);
        const o = interpolate(f - d, [0, 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        return (
          <div key={i} style={{ display: 'flex', gap: 16, alignItems: 'baseline', opacity: o, padding: '9px 0', borderTop: i ? `1px solid ${C.line}` : undefined }}>
            {r.state && <span style={{ fontFamily: FONT, fontSize: rowSize * 0.75, color: stateColor(r.state), width: 26 }}>{stateMark(r.state)}</span>}
            {r.k && <span style={{ fontFamily: FONT, fontSize: rowSize * 0.78, fontWeight: 600, color: 'rgba(243,241,233,0.62)', minWidth: rowSize * 4.2 }}>{r.k}</span>}
            <span style={{ fontFamily: serif ? SERIF : FONT, fontSize: rowSize, fontWeight: 500, color: stateColor(r.state === 'ok' || r.state === 'unknown' || r.state === 'dispute' || r.state === 'no' ? undefined : r.state), lineHeight: 1.35, whiteSpace: 'pre-line' }}>
              {r.v}{r.small && <span style={{ fontSize: Math.max(27, rowSize * 0.72), color: 'rgba(243,241,233,0.66)', marginLeft: 10 }}>{r.small}</span>}
            </span>
          </div>
        );
      })}
      {footer && <div style={{ fontFamily: FONT, fontSize: 28, color: 'rgba(243,241,233,0.62)', marginTop: 14 }}>{footer}</div>}
    </div>
  );
};

export const Columns: React.FC<{ cols: { title: string; tag?: string; items: Row[] }[]; y?: number; delay?: number; gap?: number; rowSize?: number; outAt?: number }> = ({ cols, y = 170, delay = 0, gap = 40, rowSize = 34, outAt }) => {
  const w = (1920 - 192 - gap * (cols.length - 1)) / cols.length;
  return (
    <>
      {cols.map((c, i) => (
        <Card key={i} x={96 + i * (w + gap)} y={y} w={w} tag={c.tag} title={c.title} rows={c.items} delay={delay + i * 10} titleSize={42} rowSize={rowSize} outAt={outAt} />
      ))}
    </>
  );
};

// ------------------------------------------------------------------ big question / quote
export const Question: React.FC<{ kicker?: string; text: string; delay?: number; y?: number; size?: number; tag?: string; outAt?: number }> = ({ kicker, text, delay = 0, y = 360, size = 74, tag, outAt }) => {
  const e = useEnter(delay, 18);
  const out = useExit(outAt);
  return (
    <div style={{ position: 'absolute', left: 140, right: 140, top: y, textAlign: 'center', opacity: e.opacity * out, transform: `translateY(${e.y}px)` }}>
      {tag && <div style={{ marginBottom: 22 }}><Tag kind={tag} size={26} /></div>}
      {kicker && <div style={{ fontFamily: FONT, fontSize: 34, fontWeight: 600, color: C.amberBright, marginBottom: 18, letterSpacing: '0.02em' }}>{kicker}</div>}
      <div style={{ fontFamily: SERIF, fontSize: size, fontWeight: 700, color: C.paper, lineHeight: 1.3, letterSpacing: '-0.02em', textShadow: '0 4px 24px rgba(0,0,0,0.7)', whiteSpace: 'pre-line' }}>{text}</div>
    </div>
  );
};

// ------------------------------------------------------------------ timeline
export type Ev = { t: string; label: string; state: 'ok' | 'dispute' | 'unknown'; sub?: string };
export const Timeline: React.FC<{ events: Ev[]; y?: number; delay?: number; active?: number; outAt?: number; title?: string }> = ({ events, y = 420, delay = 0, active, outAt, title }) => {
  const f = useCurrentFrame();
  const out = useExit(outAt);
  const x0 = 150, x1 = 1770;
  const step = (x1 - x0) / Math.max(1, events.length - 1);
  const lineT = interpolate(f - delay, [0, 24], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease });
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: out }}>
      {title && <div style={{ position: 'absolute', left: 150, top: y - 190, fontFamily: FONT, fontSize: 40, fontWeight: 700, color: C.paper }}>{title}</div>}
      <div style={{ position: 'absolute', left: x0, top: y, height: 3, width: (x1 - x0) * lineT, background: 'rgba(243,241,233,0.5)' }} />
      {events.map((ev, i) => {
        const d = delay + 10 + i * 10;
        const o = interpolate(f - d, [0, 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        const col = ev.state === 'ok' ? C.tealBright : ev.state === 'dispute' ? C.amberBright : C.grey;
        const on = active === undefined || active === i;
        return (
          <div key={i} style={{ position: 'absolute', left: x0 + i * step - 170, top: y - 120, width: 340, textAlign: 'center', opacity: o * (on ? 1 : 0.4) }}>
            <div style={{ fontFamily: FONT, fontSize: 30, fontWeight: 700, color: col, marginBottom: 70 }}>{ev.t}</div>
            <div style={{ position: 'absolute', left: 170 - 13, top: 107, width: 26, height: 26, borderRadius: 13, border: `3px ${ev.state === 'ok' ? 'solid' : 'dashed'} ${col}`, background: ev.state === 'ok' ? col : 'rgba(5,10,14,0.9)' }} />
            <div style={{ fontFamily: FONT, fontSize: 32, fontWeight: 600, color: C.paper, lineHeight: 1.35, marginTop: 10, whiteSpace: 'pre-line' }}>{ev.label}</div>
            {ev.sub && <div style={{ fontFamily: FONT, fontSize: 28, color: 'rgba(243,241,233,0.68)', marginTop: 8, whiteSpace: 'pre-line' }}>{ev.sub}</div>}
          </div>
        );
      })}
    </div>
  );
};

// ------------------------------------------------------------------ chain
export const Chain: React.FC<{ nodes: { label: string; sub?: string; state?: Row['state'] }[]; y?: number; delay?: number; active?: number; outAt?: number; title?: string; tag?: string }> = ({ nodes, y = 420, delay = 0, active, outAt, title, tag }) => {
  const f = useCurrentFrame();
  const out = useExit(outAt);
  const gap = 56;
  const w = (1920 - 192 - gap * (nodes.length - 1)) / nodes.length;
  return (
    <div style={{ position: 'absolute', inset: 0, opacity: out }}>
      {(title || tag) && (
        <div style={{ position: 'absolute', left: 96, top: y - 150, display: 'flex', gap: 18, alignItems: 'center' }}>
          {tag && <Tag kind={tag} size={24} />}
          {title && <span style={{ fontFamily: FONT, fontSize: 40, fontWeight: 700, color: C.paper }}>{title}</span>}
        </div>
      )}
      {nodes.map((n, i) => {
        const d = delay + i * 14;
        const o = interpolate(f - d, [0, 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        const on = active === undefined || i <= active;
        const col = n.state === 'unknown' ? C.grey : n.state === 'hl' ? C.amberBright : i === active ? C.tealBright : C.paper;
        return (
          <React.Fragment key={i}>
            <div style={{
              position: 'absolute', left: 96 + i * (w + gap), top: y, width: w, minHeight: 150, opacity: o * (on ? 1 : 0.35),
              border: `2px ${n.state === 'unknown' ? 'dashed' : 'solid'} ${col}`, borderRadius: 12, background: C.glass, padding: '22px 18px', textAlign: 'center',
            }}>
              <div style={{ fontFamily: FONT, fontSize: 36, fontWeight: 700, color: col, lineHeight: 1.25, whiteSpace: 'pre-line' }}>{n.label}</div>
              {n.sub && <div style={{ fontFamily: FONT, fontSize: 30, color: 'rgba(243,241,233,0.76)', marginTop: 10, lineHeight: 1.32, whiteSpace: 'pre-line' }}>{n.sub}</div>}
            </div>
            {i < nodes.length - 1 && (
              <div style={{ position: 'absolute', left: 96 + i * (w + gap) + w + 8, top: y + 58, fontFamily: FONT, fontSize: 40, color: 'rgba(243,241,233,0.6)', opacity: o }}>›</div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

// ------------------------------------------------------------------ annotation labels over a plate
export const Labels: React.FC<{ items: { x: number; y: number; ax?: number; ay?: number; text: string; tag?: string; delay?: number; color?: string }[]; outAt?: number }> = ({ items, outAt }) => {
  const f = useCurrentFrame();
  const out = useExit(outAt);
  return (
    <AbsoluteFill style={{ opacity: out }}>
      <svg width={1920} height={1080} style={{ position: 'absolute' }}>
        {items.map((it, i) => it.ax !== undefined ? (
          <line key={i} x1={it.ax} y1={it.ay} x2={it.x} y2={it.y + 24} stroke={it.color ?? C.paper} strokeWidth={2} strokeDasharray={it.tag === 'party' || it.tag === 'defense' ? '8 6' : undefined}
            opacity={interpolate(f - (it.delay ?? 0), [0, 10], [0, 0.8], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })} />
        ) : null)}
        {items.map((it, i) => it.ax !== undefined ? (
          <circle key={'c' + i} cx={it.ax} cy={it.ay} r={7} fill={it.color ?? C.paper} opacity={interpolate(f - (it.delay ?? 0), [0, 8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })} />
        ) : null)}
      </svg>
      {items.map((it, i) => {
        const o = interpolate(f - (it.delay ?? 0), [0, 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        return (
          <div key={i} style={{ position: 'absolute', left: it.x, top: it.y, transform: 'translateX(-50%)', opacity: o, textAlign: 'center' }}>
            {it.tag && <div style={{ marginBottom: 8 }}><Tag kind={it.tag} size={22} /></div>}
            <div style={{ fontFamily: FONT, fontSize: 34, fontWeight: 700, color: it.color ?? C.paper, background: 'rgba(5,10,14,0.7)', padding: '6px 16px', borderRadius: 8, whiteSpace: 'pre-line', lineHeight: 1.3 }}>{it.text}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ concept floor plan (2D, labelled as concept)
export const Floorplan: React.FC<{ delay?: number; step?: number; outAt?: number }> = ({ delay = 0, step = 3, outAt }) => {
  const f = useCurrentFrame();
  const out = useExit(outAt);
  const a = (k: number) => interpolate(f - delay - k * 14, [0, 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const stalls = Array.from({ length: 9 }, (_, i) => i);
  return (
    <AbsoluteFill style={{ opacity: out }}>
      <svg width={1920} height={1080} viewBox="0 0 1920 1080">
        <rect x={250} y={200} width={1420} height={700} rx={16} fill="rgba(5,10,14,0.8)" stroke="rgba(243,241,233,0.18)" opacity={a(0)} />
        <text x={280} y={240} fill="rgba(243,241,233,0.55)" fontFamily="Pretendard" fontSize={24} opacity={a(0)}>개념도 · 실제 배치·거리 아님</text>
        <g opacity={a(0)} stroke="rgba(243,241,233,0.35)" strokeWidth={3} fill="none">
          {stalls.map((i) => <line key={'n' + i} x1={360 + i * 150} y1={250} x2={360 + i * 150} y2={400} />)}
          {stalls.map((i) => <line key={'s' + i} x1={360 + i * 150} y1={690} x2={360 + i * 150} y2={840} />)}
          <rect x={300} y={400} width={1320} height={290} strokeDasharray="14 10" stroke="rgba(243,241,233,0.25)" />
        </g>
        <text x={960} y={560} textAnchor="middle" fill="rgba(243,241,233,0.35)" fontFamily="Pretendard" fontSize={30} opacity={a(0)}>통로</text>
        {step >= 1 && (
          <g opacity={a(1)}>
            <rect x={640} y={505} width={250} height={84} rx={18} fill="rgba(23,125,135,0.25)" stroke={C.tealBright} strokeWidth={3} />
            <text x={765} y={559} textAnchor="middle" fill={C.paper} fontFamily="Pretendard" fontWeight={700} fontSize={30}>A씨 차량</text>
            <path d="M 905 547 L 960 547" stroke={C.tealBright} strokeWidth={4} markerEnd="url(#arr)" />
          </g>
        )}
        {step >= 2 && (
          <g opacity={a(2)}>
            <circle cx={1060} cy={547} r={26} fill="rgba(243,241,233,0.2)" stroke={C.paper} strokeWidth={3} />
            <text x={1060} y={620} textAnchor="middle" fill={C.paper} fontFamily="Pretendard" fontWeight={700} fontSize={30}>B씨</text>
          </g>
        )}
        {step >= 3 && (
          <g opacity={a(3)}>
            <text x={1060} y={480} textAnchor="middle" fill={C.amberBright} fontFamily="Pretendard" fontWeight={600} fontSize={28}>차량 앞을 막아섬</text>
          </g>
        )}
        <defs><marker id="arr" markerWidth="10" markerHeight="10" refX="6" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill={C.tealBright} /></marker></defs>
      </svg>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ verdict slate
export const Verdict: React.FC<{ lines: { text: string; size?: number; color?: string }[]; meta: string; delay?: number }> = ({ lines, meta, delay = 0 }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', marginTop: -60 }}>
        <div style={{ opacity: interpolate(f - delay, [0, 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }), marginBottom: 34 }}><Tag kind="court" size={30} /></div>
        {lines.map((l, i) => {
          const o = interpolate(f - delay - 10 - i * 12, [0, 14], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease });
          return <div key={i} style={{ fontFamily: SERIF, fontSize: l.size ?? 96, fontWeight: 700, color: l.color ?? C.paper, opacity: o, transform: `translateY(${(1 - o) * 14}px)`, lineHeight: 1.28, letterSpacing: '-0.015em', textShadow: '0 6px 30px rgba(0,0,0,0.8)' }}>{l.text}</div>;
        })}
        <div style={{ fontFamily: FONT, fontSize: 32, color: 'rgba(243,241,233,0.72)', marginTop: 34, opacity: interpolate(f - delay - 40, [0, 12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }}>{meta}</div>
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ treatment period bar
export const PeriodBar: React.FC<{ delay?: number; outAt?: number }> = ({ delay = 0, outAt }) => {
  const f = useCurrentFrame();
  const out = useExit(outAt);
  const a = (k: number) => interpolate(f - delay - k * 16, [0, 16], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease });
  const x0 = 220, xA = 700, xB = 1640, y = 520;
  return (
    <AbsoluteFill style={{ opacity: out }}>
      <svg width={1920} height={1080}>
        <line x1={x0} y1={y} x2={x0 + (xA - x0) * a(0)} y2={y} stroke={C.tealBright} strokeWidth={14} strokeLinecap="round" />
        <line x1={xA} y1={y} x2={xA + (xB - xA) * a(1)} y2={y} stroke={C.grey} strokeWidth={8} strokeDasharray="4 16" strokeLinecap="round" />
      </svg>
      <div style={{ position: 'absolute', left: x0 - 40, top: y + 30, fontFamily: FONT, fontSize: 30, color: C.paper, opacity: a(0) }}>2022. 7. 29.</div>
      <div style={{ position: 'absolute', left: xA - 80, top: y + 30, fontFamily: FONT, fontSize: 30, color: C.paper, opacity: a(0) }}>2022. 8. 31.</div>
      <div style={{ position: 'absolute', left: x0, top: y - 96, fontFamily: FONT, fontSize: 32, fontWeight: 700, color: C.tealBright, opacity: a(0) }}>치료 기간</div>
      <div style={{ position: 'absolute', left: xB - 140, top: y + 30, fontFamily: FONT, fontSize: 30, color: C.paper, opacity: a(1) }}>2023. 5.경</div>
      <div style={{ position: 'absolute', left: xA + 120, top: y - 96, fontFamily: FONT, fontSize: 30, fontWeight: 600, color: 'rgba(243,241,233,0.75)', opacity: a(1) }}>이후 약침(어깨관절)·추나요법(경추·요추) 치료</div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ end screen
export const EndScreen: React.FC = () => {
  const e = useEnter(0, 20);
  return (
    <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 40%, #11202a 0%, #05080b 75%)', opacity: e.opacity }}>
      <div style={{ position: 'absolute', left: 150, top: 300, width: 760, height: 428, border: '2px dashed rgba(243,241,233,0.25)', borderRadius: 12 }} />
      <div style={{ position: 'absolute', left: 1010, top: 300, width: 760, height: 428, border: '2px dashed rgba(243,241,233,0.25)', borderRadius: 12 }} />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 150, textAlign: 'center', fontFamily: SERIF, fontSize: 64, fontWeight: 700, color: C.paper }}>판결의 이유</div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 800, textAlign: 'center', fontFamily: FONT, fontSize: 34, color: 'rgba(243,241,233,0.7)' }}>다음 사건도, 판단의 근거부터.</div>
    </AbsoluteFill>
  );
};
