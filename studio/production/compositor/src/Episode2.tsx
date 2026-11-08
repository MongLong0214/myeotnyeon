// v2 light cut: a flat list of short picture segments (3D plates with a slow zoom/pan, stills,
// or plain backdrops) plus timed overlays. Built by episodes/EP001/edit.py → public/ep001/render.json.
import React from 'react';
import { AbsoluteFill, Audio, Img, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { FONT } from './theme';
import { loadFonts } from './fonts';
import { EndScreen, Labels, Subtitles, Verdict } from './components/gfx';
import {
  BigStamp, BigText, Checks, Compare, Corner, Counter, Dateline, Defer, Myth, NumberLine, Persons, Quote, Scale, Split, Tip112,
} from './components/gfx2';

export type Seg = {
  from: number; dur: number; src?: string; still?: string; startFrom?: number; rate?: number;
  zoom?: [number, number]; pan?: [number, number, number, number]; dim?: number; blur?: number; bg?: string; ok?: boolean; label?: string;
};
type P = Record<string, any>;
export type Ov = { type: string; from: number; dur: number; p: P };
export type RenderDoc = {
  fps: number; durationInFrames: number; hud_case: string; segments: Seg[]; overlays: Ov[];
  subtitles: { from_: number; to: number; text: string }[]; audio: string | null;
};

loadFonts();

const Backdrop: React.FC<{ bg?: string }> = ({ bg }) => (
  <AbsoluteFill style={{ background: bg ?? 'radial-gradient(ellipse at 50% 42%, #142632 0%, #070b0f 72%)' }} />
);

const Missing: React.FC<{ label: string }> = ({ label }) => (
  <AbsoluteFill style={{ background: '#1a0d0d', alignItems: 'center', justifyContent: 'center' }}>
    <div style={{ fontFamily: FONT, fontSize: 40, color: '#ff8a7a' }}>PLATE MISSING · {label}</div>
  </AbsoluteFill>
);

const Shot: React.FC<{ s: Seg }> = ({ s }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t = interpolate(f, [0, Math.max(1, durationInFrames - 1)], [0, 1]);
  const [z0, z1] = s.zoom ?? [1.0, 1.05];
  const [x0, y0, x1, y1] = s.pan ?? [0, 0, 0, 0];
  const z = z0 + (z1 - z0) * t;
  const tx = x0 + (x1 - x0) * t;
  const ty = y0 + (y1 - y0) * t;
  const inner = s.ok === false ? <Missing label={s.label ?? '?'} />
    : s.src ? <OffthreadVideo src={staticFile(s.src)} startFrom={s.startFrom ?? 0} playbackRate={s.rate ?? 1} muted style={{ width: '100%', height: '100%' }} />
      : s.still ? <Img src={staticFile(s.still)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        : <Backdrop bg={s.bg} />;
  return (
    <AbsoluteFill style={{ backgroundColor: '#05080b', overflow: 'hidden' }}>
      <AbsoluteFill style={{ transform: `translate(${tx}px, ${ty}px) scale(${z})`, filter: s.blur ? `blur(${s.blur}px)` : undefined }}>{inner}</AbsoluteFill>
      {(s.dim ?? 0) > 0 && <AbsoluteFill style={{ backgroundColor: `rgba(4,8,12,${s.dim})` }} />}
      {(s.src || s.still) && <AbsoluteFill style={{ background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.5) 100%)' }} />}
    </AbsoluteFill>
  );
};

const Flash: React.FC<{ color?: string; len?: number }> = ({ color = '#fff', len = 6 }) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{ backgroundColor: color, opacity: interpolate(f, [0, len], [0.55, 0], { extrapolateRight: 'clamp' }) }} />;
};

const Ident: React.FC = () => {
  const f = useCurrentFrame();
  const o = interpolate(f, [8, 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return <div style={{ position: 'absolute', left: 0, right: 0, top: 700, textAlign: 'center', fontFamily: FONT, fontSize: 32, fontWeight: 600, letterSpacing: '0.35em', color: 'rgba(243,241,233,0.8)', opacity: o }}>EP.01</div>;
};

const OV: Record<string, (p: P) => React.ReactNode> = {
  big: (p) => <BigText lines={p.lines} y={p.y} box={p.box} kicker={p.kicker} tag={p.tag} />,
  counter: (p) => <Counter to={p.to} label={p.label} note={p.note} y={p.y} at={p.at} />,
  myth: (p) => <Myth rumor={p.rumor} facts={p.facts} src={p.src} />,
  scale: (p) => <Scale left={p.left} right={p.right} leftLabel={p.leftLabel} rightLabel={p.rightLabel} />,
  persons: (p) => <Persons pct={p.pct} big={p.big} label={p.label} note={p.note} />,
  compare: (p) => <Compare tiles={p.tiles} />,
  numberline: (p) => <NumberLine rangeAt={p.rangeAt} markAt={p.markAt} zoneAt={p.zoneAt} />,
  defer: (p) => <Defer voidAt={p.voidAt} />,
  checks: (p) => <Checks items={p.items} y={p.y} tag={p.tag} />,
  split: (p) => <Split left={p.left} right={p.right} q={p.q} qAt={p.qAt} />,
  quote: (p) => <Quote lines={p.lines} tag={p.tag} y={p.y} />,
  tip112: (p) => <Tip112 chipsAt={p.chipsAt} />,
  corner: (p) => <Corner kind={p.kind} text={p.text} />,
  dateline: (p) => <Dateline lines={p.lines} />,
  stamp: (p) => <BigStamp t={p.t} color={p.color} sub={p.sub} />,
  verdict: (p) => <Verdict lines={p.lines} meta={p.meta} />,
  labels: (p) => <Labels items={p.items} />,
  flash: (p) => <Flash color={p.color} len={p.len} />,
  ident: () => <Ident />,
  endscreen: () => <EndScreen />,
  shade: (p) => <AbsoluteFill style={{ backgroundColor: `rgba(4,8,12,${p.a ?? 0.5})` }} />,
};

export const Episode2: React.FC<{ doc: RenderDoc }> = ({ doc }) => (
  <AbsoluteFill style={{ backgroundColor: '#05080b' }}>
    {doc.segments.map((s, i) => (
      <Sequence key={`s${i}`} from={s.from} durationInFrames={s.dur} name={`seg ${s.label ?? s.src ?? s.still ?? 'bg'}`}>
        <Shot s={s} />
      </Sequence>
    ))}
    {doc.overlays.map((o, i) => {
      const render = OV[o.type];
      return render ? (
        <Sequence key={`o${i}`} from={o.from} durationInFrames={o.dur} name={`ov ${o.type}`} layout="none">
          <AbsoluteFill>{render(o.p)}</AbsoluteFill>
        </Sequence>
      ) : null;
    })}
    <Subtitles subs={doc.subtitles.map((s) => ({ from: s.from_, to: s.to, text: s.text }))} />
    {doc.audio && <Audio src={staticFile(doc.audio)} />}
  </AbsoluteFill>
);
