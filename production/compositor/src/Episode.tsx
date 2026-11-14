import React from 'react';
import { AbsoluteFill, Audio, Img, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { C, FONT, SERIF } from './theme';
import { loadFonts } from './fonts';
import {
  Card, Chain, Chapter, Columns, EndScreen, Fade, Floorplan, Hud, Labels, PeriodBar, Plate, Question, Stamp, Sub,
  Subtitles, Tag, Timeline, useEnter, Verdict, Vignette,
} from './components/gfx';

export type PlateSpec = { kind: 'video' | 'still'; src: string | null; startFrom?: number; dim?: number; ok: boolean } | null;
export type CueSpec = { cue_id: string; act: string; from_: number; dur: number; plate: PlateSpec; hud: string | null; gfx: Record<string, any>[] };
export type RenderDoc = { fps: number; durationInFrames: number; hud_case: string; cues: CueSpec[]; subtitles: { from_: number; to: number; text: string }[]; audio: string | null };

loadFonts();

// ------------------------------------------------------------------ small pieces used by the script
const StillPlate: React.FC<{ src: string; dim?: number }> = ({ src, dim = 0 }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const z = interpolate(f, [0, durationInFrames], [1.0, 1.06]);
  return (
    <AbsoluteFill style={{ backgroundColor: '#05080b' }}>
      <AbsoluteFill style={{ transform: `scale(${z})` }}>
        <Img src={staticFile(src)} style={{ width: '100%', height: '100%' }} />
      </AbsoluteFill>
      {dim > 0 && <AbsoluteFill style={{ backgroundColor: `rgba(4,8,12,${dim})` }} />}
    </AbsoluteFill>
  );
};

const MissingPlate: React.FC<{ label: string }> = ({ label }) => (
  <AbsoluteFill style={{ background: 'repeating-linear-gradient(45deg,#1a1010 0 20px,#120a0a 20px 40px)', alignItems: 'center', justifyContent: 'center' }}>
    <div style={{ fontFamily: FONT, fontSize: 40, color: '#ff8a7a' }}>PLATE MISSING · {label}</div>
  </AbsoluteFill>
);

const Chip: React.FC<{ text: string; sub?: string }> = ({ text, sub }) => {
  const e = useEnter(0, 12);
  return (
    <div style={{ position: 'absolute', left: 96, top: 140, opacity: e.opacity, transform: `translateY(${e.y}px)` }}>
      <div style={{ display: 'inline-block', fontFamily: FONT, fontSize: 34, fontWeight: 800, color: C.tealBright, background: 'rgba(5,10,14,0.72)', padding: '6px 16px', borderRadius: 8, borderLeft: `5px solid ${C.tealBright}` }}>{text}</div>
      {sub && <div style={{ fontFamily: FONT, fontSize: 32, fontWeight: 600, color: C.paper, marginTop: 10, background: 'rgba(5,10,14,0.6)', padding: '6px 14px', borderRadius: 8, display: 'inline-block', marginLeft: 0 }}>{sub}</div>}
    </div>
  );
};

const Omit: React.FC<{ text: string }> = ({ text }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const o = interpolate(f, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ backgroundColor: 'rgba(3,5,7,0.96)', alignItems: 'center', justifyContent: 'center', opacity: o }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ marginBottom: 22 }}><Tag kind="recon" size={26} /></div>
        <div style={{ fontFamily: SERIF, fontSize: 64, fontWeight: 700, color: C.paper }}>{text}</div>
        <div style={{ fontFamily: FONT, fontSize: 28, color: 'rgba(243,241,233,0.6)', marginTop: 16 }}>접촉·넘어지는 순간은 보여주지 않습니다</div>
      </div>
    </AbsoluteFill>
  );
};

const Twin: React.FC<{ left: string; right: string }> = ({ left, right }) => {
  const e = useEnter(0, 18);
  const st: React.CSSProperties = { fontFamily: SERIF, fontSize: 96, fontWeight: 700, color: C.paper, textShadow: '0 6px 30px rgba(0,0,0,0.8)' };
  return (
    <AbsoluteFill style={{ opacity: e.opacity }}>
      <div style={{ position: 'absolute', left: 0, width: 960, top: 380, textAlign: 'center', ...st }}>{left}</div>
      <div style={{ position: 'absolute', left: 960, width: 960, top: 380, textAlign: 'center', ...st }}>{right}</div>
      <div style={{ position: 'absolute', left: 959, top: 300, width: 2, height: 360, background: 'rgba(243,241,233,0.3)' }} />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 560, textAlign: 'center', fontFamily: FONT, fontSize: 30, color: 'rgba(243,241,233,0.7)' }}>징역형을 전제로 한, 형의 집행 여부</div>
    </AbsoluteFill>
  );
};

const Stat: React.FC<{ x: number; y: number; w: number; big: string; label: string; sub: string }> = ({ x, y, w, big, label, sub }) => {
  const e = useEnter(0, 16);
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: w, opacity: e.opacity, transform: `translateY(${e.y}px)`, background: C.glass, border: `1px solid ${C.line}`, borderRadius: 14, padding: '26px 32px' }}>
      <div style={{ marginBottom: 12 }}><Tag kind="material" size={24} /></div>
      <div style={{ fontFamily: FONT, fontSize: 30, color: 'rgba(243,241,233,0.8)', whiteSpace: 'pre-line', lineHeight: 1.35 }}>{label}</div>
      <div style={{ fontFamily: SERIF, fontSize: 120, fontWeight: 700, color: C.amberBright, lineHeight: 1.1, margin: '10px 0' }}>{big}</div>
      <div style={{ fontFamily: FONT, fontSize: 28, color: 'rgba(243,241,233,0.68)', whiteSpace: 'pre-line', lineHeight: 1.4 }}>{sub}</div>
    </div>
  );
};

const Note: React.FC<{ text: string }> = ({ text }) => {
  const e = useEnter(0, 12);
  return <div style={{ position: 'absolute', left: 96, right: 96, top: 640, textAlign: 'center', fontFamily: FONT, fontSize: 30, color: C.amberBright, opacity: e.opacity }}>※ {text}</div>;
};

const Sources: React.FC<{ lines: string[] }> = ({ lines }) => {
  const e = useEnter(0, 14);
  return (
    <div style={{ position: 'absolute', left: 140, right: 140, top: 520, opacity: e.opacity, textAlign: 'center' }}>
      <div style={{ marginBottom: 14 }}><Tag kind="material" size={22} /> <span style={{ fontFamily: FONT, fontSize: 26, color: 'rgba(243,241,233,0.75)', marginLeft: 8 }}>주요 출처</span></div>
      {lines.map((l, i) => <div key={i} style={{ fontFamily: FONT, fontSize: 28, color: 'rgba(243,241,233,0.84)', lineHeight: 1.55 }}>{l}</div>)}
    </div>
  );
};

const IdentEp: React.FC = () => {
  const e = useEnter(0, 14);
  return <div style={{ position: 'absolute', left: 0, right: 0, top: 700, textAlign: 'center', fontFamily: FONT, fontSize: 32, fontWeight: 600, letterSpacing: '0.35em', color: 'rgba(243,241,233,0.8)', opacity: e.opacity }}>EP.01</div>;
};

// ------------------------------------------------------------------ gfx registry (type → renderer)
type G = Record<string, any>;
const GFX: Record<string, (g: G, from: number) => React.ReactNode> = {
  stamp: (g) => <Stamp lines={g.lines} pos={g.pos} delay={0} />,
  question: (g) => <Question kicker={g.kicker} text={g.text} size={g.size} y={g.y} tag={g.tag} />,
  ident: () => <IdentEp />,
  card: (g) => <Card x={g.x} y={g.y} w={g.w} tag={g.tag} title={g.title} rows={g.rows} serif={g.serif} titleSize={g.titleSize} rowSize={g.rowSize} footer={g.footer} center={g.center} />,
  labels: (g, from) => <Labels items={g.items.map((it: G) => ({ ...it, delay: Math.max(0, (it.delay ?? 0) - from) }))} />,
  floorplan: (g) => <Floorplan step={g.step} />,
  chip: (g) => <Chip text={g.text} sub={g.sub} />,
  omit: (g) => <Omit text={g.text} />,
  timeline: (g) => <Timeline events={g.events} />,
  chain: (g) => <Chain nodes={g.nodes} active={g.active} title={g.title} tag={g.tag} />,
  chapter: (g) => <Chapter no={g.no} title={g.title} />,
  columns: (g, from) => <Columns cols={g.cols} y={g.y} rowSize={g.rowSize} outAt={g.outAt !== undefined ? g.outAt - from : undefined} />,
  period: () => <PeriodBar />,
  twin: (g) => <Twin left={g.left} right={g.right} />,
  verdict: (g) => <Verdict lines={g.lines} meta={g.meta} />,
  stat: (g) => <Stat x={g.x} y={g.y} w={g.w} big={g.big} label={g.label} sub={g.sub} />,
  note: (g) => <Note text={g.text} />,
  sources: (g) => <Sources lines={g.lines} />,
  endscreen: () => <EndScreen />,
};

// ------------------------------------------------------------------ gfx dispatcher
const Gfx: React.FC<{ g: G; cueDur: number }> = ({ g, cueDur }) => {
  const from = g.at_frac !== undefined ? Math.round(g.at_frac * cueDur) : (g.at ?? 0);
  const to = g.to_frac !== undefined ? Math.round(g.to_frac * cueDur) : g.dur !== undefined ? from + g.dur : cueDur;
  const dur = Math.max(1, to - from);
  const render = GFX[g.type];
  const el = render ? render(g, from) : null;
  return <Sequence from={from} durationInFrames={dur} layout="none">{el}</Sequence>;
};

// ------------------------------------------------------------------ cue
const Cue: React.FC<{ c: CueSpec; hudCase: string }> = ({ c, hudCase }) => {
  const p = c.plate;
  const chapterFirst = c.gfx.some((g) => g.type === 'chapter' && (g.at ?? 0) === 0);
  return (
    <AbsoluteFill>
      {p === null ? <AbsoluteFill style={{ backgroundColor: '#05080b' }} /> : !p.ok || !p.src ? <MissingPlate label={c.cue_id} /> :
        p.kind === 'video' ? <Plate src={p.src} startFrom={p.startFrom ?? 0} dim={p.dim ?? 0} /> : <StillPlate src={p.src} dim={p.dim ?? 0} />}
      {p !== null && <Vignette strength={0.5} />}
      {c.hud && !chapterFirst && <Hud left={hudCase} tag={c.hud} />}
      {c.hud && chapterFirst && <Sequence from={60} layout="none"><Hud left={hudCase} tag={c.hud} /></Sequence>}
      {c.gfx.map((g, i) => <Gfx key={i} g={g} cueDur={c.dur} />)}
    </AbsoluteFill>
  );
};

export const Episode: React.FC<{ doc: RenderDoc }> = ({ doc }) => (
  <AbsoluteFill style={{ backgroundColor: '#05080b' }}>
    {doc.cues.map((c) => (
      <Sequence key={c.cue_id} from={c.from_} durationInFrames={c.dur} name={c.cue_id}>
        <Cue c={c} hudCase={doc.hud_case} />
      </Sequence>
    ))}
    <Subtitles subs={doc.subtitles.map((s) => ({ from: s.from_, to: s.to, text: s.text }))} />
    <Sequence from={0} durationInFrames={12}><Fade inF={12} /></Sequence>
    {doc.audio && <Audio src={staticFile(doc.audio)} />}
  </AbsoluteFill>
);
