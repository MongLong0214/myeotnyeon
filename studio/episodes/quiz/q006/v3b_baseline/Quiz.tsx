// "몇년나옴 · 형량 퀴즈" Shorts template (1080×1920), v3 (owner 2026-10-26: studio level, no layout shift).
// One JSON per episode (public/qNNN/render.json, built by episodes/quiz/make.py): header lines, choices,
// answer, and cues whose scenes react to narration anchors.
//
// Layout contract v4 (owner 2026-10-26: nothing may be cut on any phone; SafeAudit.tsx checks every frame):
//   phones can hide x < 110 and x > 970 (app fills taller screens), y < 190 (status bar, Dynamic Island, app
//   icons), y > 1540 (title and channel block), and x > 880 when y > 900 (action rail).
//   header 196–456 · scene panel 60..1020 × 468..1332 (1000×900 set at 0.96) · captions 1352–1520 in x 110–870
// Every episode uses the same boxes; only the words change.
export const PANEL = { x: 60, y: 468, k: 0.96 };
import React from 'react';
import { AbsoluteFill, Audio, interpolate, Sequence, spring, staticFile, useCurrentFrame } from 'remotion';
import { DISPLAY, FONT } from './theme';
import { loadFonts } from './fonts';
import { Burst, Car, Flash, INK, NightLot, PAPER, Paper, ramp, RED, Sfx, Shake, SpeedLines, Stamp, TEAL, usePop, YELLOW } from './components/toon';
import { Expr, Guy, Look, Pose } from './components/rm';
import { BarStreetSet, BigTextSet, CabinSet, CafeSet, DormSet, HallwaySet, MemorialSet, MoneySet, MotelSet, OfficeSet, OrchardSet, PhoneSet, Prop, PropKind, RecorderSet, StoreSet, WildfireSet } from './components/sets';

type P = Record<string, any>;
export type QuizCue = { id: string; scene: string; from: number; dur: number; a: Record<string, number>; p: P };
// hook (#11+, optional): the frame-0 header, kept apart so it can be swapped per episode. style picks the header
// renderer (HOOK_STYLES below); absent = the v3 house header, so q001–q010 render exactly as before.
export type Hook = { style?: string; lines?: string[]; ask?: string; narration?: string };
export type QuizDoc = {
  fps: number; durationInFrames: number; ep: { no: number; head: [string, string]; ask: string; answerHead: string; choices: string[]; answer: number; source: string; hook?: Hook };
  cues: QuizCue[]; subtitles: { from_: number; to: number; text: string }[]; audio: string | null;
};

loadFonts();
const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };
const CHOICE_BG = ['#8A93A6', TEAL, RED];

const Cam: React.FC<{ keys: [number, number, number, number][]; children: React.ReactNode }> = ({ keys, children }) => {
  const f = useCurrentFrame();
  let k = keys[0]; let prev = keys[0];
  for (const kk of keys) { if (f >= kk[0]) { prev = k; k = kk; } }
  const t = Math.min(1, (f - k[0]) / 12); const e = 1 - Math.pow(1 - t, 3);
  const cx = prev[1] + (k[1] - prev[1]) * e, cy = prev[2] + (k[2] - prev[2]) * e, z = prev[3] + (k[3] - prev[3]) * e;
  return <AbsoluteFill style={{ transform: `translate(${500 - cx * z}px, ${450 - cy * z}px) scale(${z})`, transformOrigin: '0 0' }}>{children}</AbsoluteFill>;
};

const Tag: React.FC<{ text: string; x: number; y: number; at: number; color: string; size?: number }> = ({ text, x, y, at, color, size = 42 }) => {
  const p = usePop(at, 11);
  return (
    <div style={{ position: 'absolute', left: x, top: y, transform: `translateX(-50%) scale(${0.5 + 0.5 * p})`, opacity: Math.min(1, p * 2), fontFamily: FONT, fontWeight: 800, fontSize: size,
      color: PAPER, background: color, border: `6px solid ${INK}`, borderRadius: 16, padding: '6px 20px', whiteSpace: 'nowrap', letterSpacing: '-0.03em' }}>{text}</div>
  );
};

const Road: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <>
      <NightLot glow={0.7} />
      <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
        <rect x={0} y={600} width={1000} height={300} fill="#3E3A4C" stroke={INK} strokeWidth={6} />
        {Array.from({ length: 8 }, (_, i) => {
          const x = ((i * 180 - f * 34) % 1440 + 1440) % 1440 - 220;
          return <rect key={`ln${i}`} x={x} y={760} width={110} height={16} rx={8} fill="#F2E9C9" />;
        })}
      </svg>
    </>
  );
};

// ------------------------------------------------------------------ scenes
const Cling: React.FC<{ a: Record<string, number>; p: P }> = ({ a, p }) => {
  const f = useCurrentFrame();
  const dist = Math.round(interpolate(f, [a.s1 + 4, (a.e2 ?? a.e1) - 4], [0, p.dist], clamp));
  const bob = Math.sin(f / 3) * 4;
  return (
    <AbsoluteFill>
      {/* zoom 1.08 keeps the 1000×900 set covering the frame only for centres within ±37 px of (500, 450) */}
      <Cam keys={[[0, 500, 450, 1.0], [a.s1 + 40, 530, 475, 1.08]]}>
        <Road />
        <SpeedLines dir="right" opacity={0.6} />
        <Car x={520} y={760 + bob} />
        <Guy look={p.victim as Look} x={170} y={728 + bob} scale={0.62} expr="scared" pose="cling" rot={78 + Math.sin(f / 4) * 3} seed={3} />
      </Cam>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 40, textAlign: 'center' }}>
        <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 140, color: YELLOW, WebkitTextStroke: `14px ${INK}`, paintOrder: 'stroke fill', letterSpacing: '-0.04em' }}>{dist}m</span>
      </div>
      {p.tag && <Tag text={p.tag} x={500} y={230} at={a.s1 + 6} color={p.victim === 'cop' ? '#2D3F73' : TEAL} />}
    </AbsoluteFill>
  );
};

// Pushed three times, then reverse and a second hit. The bumper stays on the victim's legs while pushing.
const Push2: React.FC<{ a: Record<string, number>; p: P }> = ({ a }) => {
  const f = useCurrentFrame();
  const hit = a.e1 - 6;
  const n = [a.s1 + 4, a.s1 + 16, a.s1 + 28];
  const step = n.reduce((acc, t) => acc + ramp(f, t, t + 6), 0);
  const back = ramp(f, a.s1 + 40, a.s1 + 56);
  const again = ramp(f, a.s1 + 58, hit);
  const pushing = f < a.s1 + 36;
  const victimX = 600 + 30 * step;
  const front = pushing ? victimX - 10 : 680 - 260 * back + 260 * again; // car's front bumper x: on the legs while pushing
  const down = f >= hit;
  return (
    <Shake at={hit} len={8} amp={8}>
      <NightLot />
      <Car x={front - 268} y={740} reverse={!pushing && f < a.s1 + 56} />
      {pushing && <Guy look="B" x={victimX} y={850} scale={0.84} expr="shock" pose="pushed" flip rot={8} seed={2} />}
      {!pushing && !down && <Guy look="B" x={victimX} y={850} scale={0.84} expr="scared" pose="stand" flip seed={2} />}
      {down && <Guy look="B" x={victimX} y={860} scale={0.84} expr="dizzy" pose="pushed" flip rot={14} seed={2} />}
      {pushing && n.map((t, i) => (f >= t ? <Sfx key={`n${t}`} text={`${i + 1}`} x={260 + i * 150} y={190} size={110} at={t} color={YELLOW} rot={0} /> : null))}
      {!pushing && f < a.s1 + 58 && <Sfx text="후진" x={300} y={300} size={96} at={a.s1 + 40} color={PAPER} rot={0} />}
      {down && <Burst x={470} y={380} r={230} at={hit} text="쾅!" size={122} />}
      <Tag text="피해자 · 30대 남성" x={690} y={40} at={a.s1 + 2} color={TEAL} size={38} />
      <Tag text="가해자 · 20대 여성 운전자" x={330} y={560} at={a.s1 + 10} color={RED} size={36} />
    </Shake>
  );
};

const Hurt: React.FC<{ a: Record<string, number>; p: P }> = ({ a, p }) => (
  <AbsoluteFill>
    <Paper color="#F6E7D7" />
    <Guy look={p.victim as Look} x={250} y={860} scale={1.05} expr={p.expr ?? 'dizzy'} pose="sit" seed={4} />
    <Stamp lines={[p.stamp, ...(p.sub ? [p.sub] : [])]} at={a.s1 + 10} x={680} y={250} size={110} maxW={540} />
  </AbsoluteFill>
);

const Record: React.FC<{ a: Record<string, number>; p: P }> = ({ a, p }) => {
  const f = useCurrentFrame();
  const items: string[] = p.items;
  return (
    <AbsoluteFill>
      <Paper color="#E9E1F2" />
      <Guy look="D" x={220} y={1000} scale={1.15} expr={p.expr ?? 'smug'} pose={p.pose ?? 'stand'} seed={6} />
      {items.map((t, i) => {
        const at = a.s1 + 6 + i * Math.max(8, Math.round(((a.e1 - a.s1) * 0.6) / items.length));
        return f >= at ? <Stamp key={t} lines={[t]} at={at} x={630} y={items.length === 1 ? 300 : 170 + i * 170} size={78} maxW={500} rot={-6 + i * 5} color={p.color ?? RED} /> : null;
      })}
    </AbsoluteFill>
  );
};

const Remorse: React.FC<{ a: Record<string, number>; p: P }> = ({ a, p }) => (
  <AbsoluteFill>
    <Paper color="#DCE6F2" />
    <Guy look="A" x={280} y={1040} scale={1.2} expr="smug" pose="shrug" seed={5} />
    <Stamp lines={p.lines} at={a.s1 + 8} x={680} y={290} size={84} maxW={540} color={RED} />
  </AbsoluteFill>
);

const Choice: React.FC<{ c: string; i: number }> = ({ c, i }) => {
  const pp = usePop(i * 4, 12);
  return (
    <div style={{ position: 'absolute', left: 70, width: 780, top: 110 + i * 158, height: 136, borderRadius: 28, background: CHOICE_BG[i], border: `8px solid ${PAPER}`, boxSizing: 'border-box',
      display: 'flex', alignItems: 'center', gap: 28, paddingLeft: 30, transform: `scale(${0.7 + 0.3 * pp})`, opacity: Math.min(1, pp * 2) }}>
      <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 64, color: INK, background: PAPER, borderRadius: 50, width: 88, height: 88, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{'ABC'[i]}</span>
      <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 80, color: PAPER, letterSpacing: '-0.03em' }}>{c}</span>
    </div>
  );
};

const QuizScene: React.FC<{ a: Record<string, number>; choices: string[] }> = ({ a, choices }) => {
  const f = useCurrentFrame();
  const cd0 = a.e2 ?? a.e1;
  const left = Math.ceil(interpolate(f, [cd0, cd0 + 90], [3, 0], clamp));
  return (
    <AbsoluteFill style={{ background: '#16181F' }}>
      <div style={{ position: 'absolute', left: 70, top: 34, display: 'flex', alignItems: 'center', gap: 14, opacity: ramp(f, a.s1 + 6, a.s1 + 16) }}>
        <svg width={46} height={42} viewBox="0 0 46 42"><path d="M6 4h34a4 4 0 0 1 4 4v18a4 4 0 0 1-4 4H20l-10 9v-9H6a4 4 0 0 1-4-4V8a4 4 0 0 1 4-4z" fill={YELLOW} /></svg>
        <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 44, color: PAPER, letterSpacing: '-0.03em' }}>댓글로 먼저 찍고 보기</span>
      </div>
      {choices.map((c, i) => <Choice key={c} c={c} i={i} />)}
      {f >= cd0 && left > 0 && (
        <div style={{ position: 'absolute', left: 500 - 80, top: 640, width: 160, height: 160, borderRadius: 80, background: YELLOW, border: `8px solid ${PAPER}`, boxSizing: 'border-box',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT, fontWeight: 800, fontSize: 104, color: INK,
          transform: `scale(${1 + 0.15 * (1 - ((f - cd0) % 30) / 30)})` }}>{left}</div>
      )}
    </AbsoluteFill>
  );
};

const Reveal: React.FC<{ a: Record<string, number>; p: P; choices: string[]; answer: number }> = ({ a, p, choices, answer }) => {
  const f = useCurrentFrame();
  const hit = a.s1 + 2;
  const swing = interpolate(f, [0, hit - 4, hit], [-38, -40, 8], clamp);
  const jail = answer === 2;
  const bars = ramp(f, hit + 4, hit + 12);
  // steps (#11+): the stamp changes at later narration sentences, e.g. a two-stage 1심 → 2심 reveal
  const steps: { s: number; lines: string[]; size?: number }[] = p.steps ?? [];
  const stepAt = (i: number) => a[`s${steps[i].s}`] ?? 1e9;
  const step = steps.reduce((acc, _, i) => (f >= stepAt(i) ? i : acc), -1);
  return (
    <Shake at={hit} len={8} amp={7}>
      <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
        <rect x={0} y={0} width={1000} height={900} fill="#5A3B22" />
        {Array.from({ length: 22 }, (_, i) => <rect key={`p${i}`} x={i * 46} y={0} width={30} height={560} fill="#6E4A2B" stroke={INK} strokeWidth={3} />)}
        {/* the cell belongs to the defendant: bars drop behind the desk on the right, never over the judge */}
        {jail && Array.from({ length: 5 }, (_, i) => <rect key={`b${i}`} x={470 + i * 108} y={-600 + 600 * bars} width={30} height={600} rx={8} fill="#565A66" stroke={INK} strokeWidth={6} />)}
      </svg>
      <Guy look="judge" x={185} y={790} scale={0.85} expr="serious" pose="stand" seed={7} headPop={f >= hit && f < hit + 10 ? 1 - (f - hit) / 10 : 0} />
      <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
        <rect x={-10} y={560} width={1020} height={360} fill="#8A5A32" stroke={INK} strokeWidth={8} />
        <rect x={-10} y={540} width={1020} height={40} fill="#A06C3E" stroke={INK} strokeWidth={8} />
        <rect x={380} y={600} width={260} height={56} rx={14} fill="#3B2414" stroke={INK} strokeWidth={8} />
        <g transform={`translate(650 590) rotate(${swing})`}>
          <rect x={-18} y={-280} width={36} height={280} rx={12} fill="#A06C3E" stroke={INK} strokeWidth={8} />
          <rect x={-100} y={-345} width={200} height={100} rx={28} fill="#7A4A26" stroke={INK} strokeWidth={8} />
        </g>
      </svg>
      <Punch beats={p.punch} s1={a.s1}>
        <Tag text={`정답 ${'ABC'[answer]} · ${choices[answer]}`} x={500} y={30} at={hit} color={CHOICE_BG[answer]} size={52} />
        {step < 0
          ? <Stamp lines={p.lines} at={hit + 6} x={645} y={300} size={p.size ?? 100} maxW={570} color={jail ? RED : INK} rot={-4} />
          : <Stamp key={`rs${step}`} lines={steps[step].lines} at={stepAt(step)} x={645} y={300} size={steps[step].size ?? p.size ?? 100} maxW={570} color={jail ? RED : INK} rot={-4} />}
        {(p.tags ?? []).map((g: P, i: number) => <Tag key={`rt${i}`} text={g.text} x={g.x ?? 645} y={g.y ?? 440} at={a.s1 + (g.at ?? 30)} color={g.color ?? INK} size={g.size ?? 34} />)}
      </Punch>
      <Flash at={hit} len={6} />
    </Shake>
  );
};

// Generic incident scene for non-traffic cases, fully described in episodes.py. Every "at" is in frames after the
// first narration sentence starts (a.s1), so staging follows the voice.
type Actor = { look: Look; x: number; y?: number; scale?: number; expr?: Expr; pose?: Pose; flip?: boolean; rot?: number; at?: number; until?: number; lift?: number; liftAt?: [number, number] };
type TagSpec = { text: string; x: number; y: number; color?: string; at?: number; size?: number };
type PropSpec = { kind: PropKind; x: number; y: number; scale?: number; rot?: number; at?: number; until?: number; front?: boolean; lift?: number; liftAt?: [number, number] };
const SETS: Record<string, (p: P, s1: number) => React.ReactNode> = {
  office: () => <OfficeSet />, hallway: () => <HallwaySet />, store: () => <StoreSet />, night: () => <NightLot />,
  paper: (p) => <Paper color={p.paper ?? '#F2EBDC'} />, memorial: () => <MemorialSet />,
  money: (p, s1) => <MoneySet label={p.money} at={s1 + (p.moneyAt ?? 4)} />,
  cafe: (p) => <CafeSet rocks={p.rocks} />,
  bigtext: (p, s1) => <BigTextSet label={p.big} sub={p.bigSub} bg={p.bigBg} color={p.bigColor} at={s1 + (p.bigAt ?? 0)} />,
  phone: (p, s1) => <PhoneSet lines={p.chat ?? [{}, { me: true }, {}]} at={s1 + 4} step={p.chatStep ?? 10} />,
  cabin: (p, s1) => <CabinSet leverAt={s1 + (p.leverAt ?? -99)} handAt={p.handAt == null ? null : s1 + p.handAt} />,
  orchard: (p) => <OrchardSet smoke={p.smoke} wind={p.wind} />, wildfire: () => <WildfireSet />, dorm: () => <DormSet />, motel: () => <MotelSet />,
  barstreet: () => <BarStreetSet />, recorder: () => <RecorderSet />,
};

// Zoom beats (#11+, owner H3 2026-10-26: a visual change at least every 1.5 s). Each beat at s1 + t toggles the zoom
// between 1 and 1 + amp about the set centre over 8 frames, so it never drifts and edge text stays in frame.
// No beats = no wrapper, so older episodes render unchanged.
const Punch: React.FC<{ beats?: number[]; s1: number; amp?: number; children: React.ReactNode }> = ({ beats, s1, amp = 0.04, children }) => {
  const f = useCurrentFrame();
  if (!beats || !beats.length) return <>{children}</>;
  let z = 1;
  beats.forEach((b, i) => {
    if (f < s1 + b) return;
    const k = ramp(f, s1 + b, s1 + b + 8);
    z = i % 2 ? 1 + amp * (1 - k) : 1 + amp * k;
  });
  return <AbsoluteFill style={{ transform: `scale(${z})`, transformOrigin: '500px 450px' }}>{children}</AbsoluteFill>;
};
// A prop appears at s1 + at; lift animates from liftAt[0] to liftAt[1] frames (forklift carriage, raised objects).
const PropAt: React.FC<{ q: PropSpec; f: number; s1: number }> = ({ q, f, s1 }) => {
  if (f < s1 + (q.at ?? -99) || f >= s1 + (q.until ?? 1e9)) return null;
  const k = q.liftAt ? ramp(f, s1 + q.liftAt[0], s1 + q.liftAt[1]) : 1;
  const lift = (q.lift ?? 0) * k;
  return q.kind === 'forklift' ? <Prop kind={q.kind} x={q.x} y={q.y} scale={q.scale} rot={q.rot} lift={lift} />
    : <Prop kind={q.kind} x={q.x} y={q.y - lift} scale={q.scale} rot={q.rot} />;
};

const Creep: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{ transform: `scale(${1 + Math.min(f, 240) * 0.00015})`, transformOrigin: '500px 450px' }}>{children}</AbsoluteFill>;
};

export const Incident: React.FC<{ a: Record<string, number>; p: P }> = ({ a, p }) => {
  const f = useCurrentFrame();
  const s1 = a.s1;
  const actors: Actor[] = p.actors ?? [];
  const tags: TagSpec[] = p.tags ?? [];
  const props: PropSpec[] = p.props ?? [];
  // stamps (#11+): several stamp cards in turn, each shown from at until `until` (frames after s1)
  const stamps: P[] = p.stamps ?? [];
  return (
    <Shake at={p.burst ? s1 + p.burst.at : -99} len={8} amp={8}>
      <Creep>
      <Punch beats={p.punch} s1={s1}>
      {SETS[p.set ?? 'paper'](p, s1)}
      {props.filter((q) => !q.front).map((q, i) => <PropAt key={`pb${i}`} q={q} f={f} s1={s1} />)}
      {actors.map((c, i) => (f >= s1 + (c.at ?? -99) && f < s1 + (c.until ?? 1e9) ? (
        <Guy key={`act${i}`} look={c.look} x={c.x} y={(c.y ?? 880) - (c.lift ?? 0) * (c.liftAt ? ramp(f, s1 + c.liftAt[0], s1 + c.liftAt[1]) : 1)} scale={c.scale ?? 0.9}
          expr={c.expr ?? 'normal'} pose={c.pose ?? 'stand'} flip={c.flip} rot={c.rot ?? 0} seed={i + 2} />
      ) : null))}
      {props.filter((q) => q.front).map((q, i) => <PropAt key={`pf${i}`} q={q} f={f} s1={s1} />)}
      {(p.sfx ?? []).map((s: TagSpec, i: number) => (f >= s1 + (s.at ?? 0) ? <Sfx key={`sfx${i}`} text={s.text} x={s.x} y={s.y} size={s.size ?? 96} at={s1 + (s.at ?? 0)} color={s.color ?? YELLOW} rot={0} /> : null))}
      {p.burst && f >= s1 + p.burst.at && <Burst x={p.burst.x} y={p.burst.y} r={p.burst.r ?? 220} at={s1 + p.burst.at} text={p.burst.text} size={p.burst.size ?? 110} />}
      {tags.map((g, i) => <Tag key={`tag${i}`} text={g.text} x={g.x} y={g.y} at={s1 + (g.at ?? 2)} color={g.color ?? RED} size={g.size ?? 40} />)}
      {p.stamp && f >= s1 + (p.stamp.at ?? 10) && <Stamp lines={p.stamp.lines} at={s1 + (p.stamp.at ?? 10)} x={p.stamp.x ?? 660} y={p.stamp.y ?? 260} size={p.stamp.size ?? 100} maxW={p.stamp.maxW ?? 560} color={p.stamp.color ?? RED} rot={p.stamp.rot ?? -8} />}
      {stamps.map((q, i) => (f >= s1 + (q.at ?? 10) && f < s1 + (q.until ?? 1e9)
        ? <Stamp key={`stp${i}`} lines={q.lines} at={s1 + (q.at ?? 10)} x={q.x ?? 660} y={q.y ?? 260} size={q.size ?? 100} maxW={q.maxW ?? 560} color={q.color ?? RED} rot={q.rot ?? -8} /> : null))}
      </Punch>
      </Creep>
    </Shake>
  );
};

// "판사가 본 사정" (#11+, owner H2 2026-10-26): replaces the long options card and countdown. A thin strip keeps the three
// choices on screen while 2–3 cards — what the court weighed, for and against — land one per narration sentence
// (card i at sentence cardFrom + i). Each card's badge stamps a beat later and the judge's face changes per card.
const TONE: Record<string, string> = { bad: RED, good: TEAL, info: '#2D3F73' };
const Weigh: React.FC<{ a: Record<string, number>; p: P; choices: string[] }> = ({ a, p, choices }) => {
  const f = useCurrentFrame();
  const cards: { text: string; tag: string; tone?: string }[] = p.cards;
  const from = p.cardFrom ?? 2;
  const at = (i: number) => a[`s${from + i}`] ?? a.s1 + 12 + i * 40;
  const shown = cards.filter((_, i) => f >= at(i)).length;
  const faces: Expr[] = p.faces ?? ['serious', 'tired', 'serious', 'tired'];
  return (
    <Punch beats={p.punch} s1={a.s1}>
      <Paper color={p.paper ?? '#F2EBDC'} />
      <div style={{ position: 'absolute', left: 70, width: 860, top: 22, height: 88, display: 'flex', gap: 14 }}>
        {choices.map((c, i) => {
          const pp = usePopAt(f, i * 3);
          return (
            <div key={c} style={{ flex: 1, borderRadius: 20, background: CHOICE_BG[i], border: `6px solid ${INK}`, boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
              transform: `scale(${0.7 + 0.3 * pp})`, opacity: Math.min(1, pp * 2) }}>
              <span style={{ width: 50, height: 50, borderRadius: 25, background: PAPER, color: INK, fontFamily: FONT, fontWeight: 800, fontSize: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{'ABC'[i]}</span>
              <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: c.length > 4 ? 38 : 44, color: PAPER, letterSpacing: '-0.04em', whiteSpace: 'nowrap' }}>{c}</span>
            </div>
          );
        })}
      </div>
      <div style={{ position: 'absolute', left: 80, top: 136, fontFamily: DISPLAY, fontSize: 64, lineHeight: 1, color: INK, opacity: ramp(f, 2, 8) }}>{p.title ?? '판사가 본 사정'}</div>
      {cards.map((c, i) => {
        const t = at(i);
        const pp = f >= t ? Math.min(1, (f - t) / 6) : 0;
        const bp = f >= t + 14 ? usePopAt(f, t + 14) : 0;
        return (
          <div key={c.text} style={{ position: 'absolute', left: 80, width: 700, top: 230 + i * 150, height: 128, boxSizing: 'border-box', opacity: pp, transform: `translateX(${(1 - pp) * -24}px)`,
            background: PAPER, border: `7px solid ${INK}`, borderRadius: 24, padding: '10px 28px 0', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <span style={{ alignSelf: 'flex-start', fontFamily: FONT, fontWeight: 800, fontSize: 26, lineHeight: '34px', color: PAPER, background: TONE[c.tone ?? 'info'], borderRadius: 10, padding: '0 12px',
              transform: `scale(${0.6 + 0.4 * bp})`, transformOrigin: '0 50%', opacity: Math.min(1, bp * 2) }}>{c.tag}</span>
            <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 48, lineHeight: '62px', color: INK, letterSpacing: '-0.03em', whiteSpace: 'nowrap' }}>{c.text}</span>
          </div>
        );
      })}
      <Guy look="judge" x={860} y={1000} scale={0.5} expr={faces[Math.min(shown, faces.length - 1)]} pose="stand" seed={7} />
    </Punch>
  );
};

// usePop's spring as a plain function of the frame, so it can run inside loops.
const usePopAt = (f: number, at: number, damping = 12) => spring({ frame: f - at, fps: 30, config: { damping, mass: 0.5, stiffness: 180 } });

const Confiscate: React.FC<{ a: Record<string, number> }> = ({ a }) => {
  const f = useCurrentFrame();
  const tow = ramp(f, a.s1 + 24, a.e1);
  return (
    <AbsoluteFill>
      <NightLot glow={0.6} />
      <Car x={520 + 520 * tow} y={760} lights={false} driver={false} />
      <Stamp lines={['몰수']} at={a.s1 + 8} x={500} y={320} size={170} color={RED} rot={-8} />
    </AbsoluteFill>
  );
};

const Reason: React.FC<{ a: Record<string, number>; p: P; subs: number[] }> = ({ a, p, subs }) => {
  const f = useCurrentFrame();
  const chips: string[] = p.chips;
  return (
    <Creep>
      <Paper color="#F2EBDC" />
      <div style={{ position: 'absolute', left: 80, top: 56, fontFamily: DISPLAY, fontSize: 76, lineHeight: 1, color: INK }}>{p.title ?? '왜냐하면'}</div>
      {chips.map((c, i) => {
        const at = subs.length >= chips.length ? subs[i] + 2 : a.s1 + 4 + i * Math.max(10, Math.round(((a.e1 - a.s1) * 0.7) / chips.length));
        const pp = f >= at ? Math.min(1, (f - at) / 6) : 0;
        return (
          <div key={c} style={{ position: 'absolute', left: 80, width: 760, top: 186 + i * 150, height: 116, boxSizing: 'border-box', opacity: pp, transform: `translateX(${(1 - pp) * -24}px)`,
            display: 'flex', alignItems: 'center', fontFamily: FONT, fontWeight: 800, fontSize: 58, color: PAPER, background: p.colors?.[i] ?? (i === 0 ? RED : TEAL),
            border: `7px solid ${INK}`, borderRadius: 24, padding: '0 30px', letterSpacing: '-0.03em', whiteSpace: 'nowrap' }}>{c}</div>
        );
      })}
    </Creep>
  );
};

// p.staged (#11+, owner H3: no static end card): the logo pops a beat after the card and the view keeps moving.
const Outro: React.FC<{ a: Record<string, number>; p?: P }> = ({ a, p }) => {
  const f = useCurrentFrame();
  const pp = usePop(a.s1, 11);
  const staged = !!p?.staged;
  const lp = staged ? usePopAt(f, a.s1 + (p?.logoAt ?? 14), 9) : 1;
  const body = (
    <>
      <NightLot glow={0.5} />
      <AbsoluteFill style={{ background: 'rgba(10,14,30,0.5)' }} />
      <div style={{ position: 'absolute', left: 60, right: 140, top: 200, textAlign: 'center', transform: `scale(${0.6 + 0.4 * pp})`, opacity: pp }}>
        <div style={{ background: PAPER, border: `8px solid ${INK}`, borderRadius: 50, padding: '34px 20px', fontFamily: FONT, fontWeight: 800, fontSize: 76, color: INK, letterSpacing: '-0.04em' }}>다음 사건도 맞혀 보세요</div>
        <div style={{ marginTop: 40, transform: `scale(${0.5 + 0.5 * lp})`, opacity: Math.min(1, lp * 2) }}><span style={{ fontFamily: DISPLAY, fontSize: 92, lineHeight: 1, color: INK, background: YELLOW, border: `8px solid ${INK}`, borderRadius: 24, padding: '14px 40px', display: 'inline-block' }}>몇년나옴<span style={{ color: RED }}>?</span></span></div>
      </div>
    </>
  );
  return staged ? <Punch beats={p?.punch ?? []} s1={a.s1}>{body}</Punch> : <AbsoluteFill>{body}</AbsoluteFill>;
};

// ------------------------------------------------------------------ frame
const HL = /(\d+미터|\d+m|\d+주|\d+일|\d+개월|\d+년|집행유예|실형|벌금|법정구속|몰수|가석방|전과|세 번|두 번|반성|초범)/g;
const Caption: React.FC<{ subs: QuizDoc['subtitles'] }> = ({ subs }) => {
  const f = useCurrentFrame();
  const s = subs.find((x) => f >= x.from_ && f < x.to);
  if (!s) return null;
  const parts = s.text.split(HL);
  return (
    <div style={{ position: 'absolute', left: 110, width: 760, top: 1352, textAlign: 'center' }}>
      <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 70, lineHeight: 1.2, color: PAPER, WebkitTextStroke: `12px ${INK}`, paintOrder: 'stroke fill', letterSpacing: '-0.03em', whiteSpace: 'pre-line', wordBreak: 'keep-all' }}>
        {parts.map((pt, i) => <span key={`${s.from_}-${i}`} style={{ color: HL.test(pt) ? YELLOW : PAPER }}>{pt}</span>)}
      </div>
    </div>
  );
};

// Frame-0 header renderers, picked per episode by ep.hook.style (the hookStyle switch). Every style keeps the same
// boxes as the house header so covers and videos never shift; only which words fill them changes.
//   house   — brand · two headline lines · "몇 년 나왔을까?" (or hook.ask) — the v3 default (#1–#10, #12, #14)
//   outcome — the same, but the question row stays empty until the reveal: the headline states the outcome/tension
//             (#11, #13 — H1 arm "결과형")
type HeaderProps = { ep: QuizDoc['ep']; revealAt: number };
const HOOK_STYLES: Record<string, { ask: (ep: QuizDoc['ep']) => string }> = {
  house: { ask: (ep) => ep.hook?.ask ?? '몇 년 나왔을까?' },
  outcome: { ask: (ep) => ep.hook?.ask ?? '' },
};
export const Header: React.FC<HeaderProps> = ({ ep, revealAt }) => {
  const f = useCurrentFrame();
  const after = f >= revealAt;
  const style = HOOK_STYLES[ep.hook?.style ?? 'house'];
  if (!style) throw new Error(`unknown hook style "${ep.hook?.style}" in episode ${ep.no}`);
  const head = ep.hook?.lines ?? ep.head;
  const ask = style.ask(ep);
  const q = ask.endsWith('?') ? [ask.slice(0, -1), '?'] : [ask, ''];
  return (
    <>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 196, height: 46, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14 }}>
        <span style={{ fontFamily: DISPLAY, fontSize: 40, lineHeight: 1, color: YELLOW }}>몇년나옴<span style={{ color: RED }}>?</span></span>
        <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 30, color: PAPER, background: RED, borderRadius: 10, padding: '3px 14px', letterSpacing: '-0.02em' }}>형량 퀴즈 #{ep.no}</span>
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 246, height: 60, textAlign: 'center', fontFamily: FONT, fontWeight: 800, fontSize: 52, lineHeight: '60px', color: PAPER, letterSpacing: '-0.04em', whiteSpace: 'nowrap' }}>{head[0]}</div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 306, height: 96, textAlign: 'center', fontFamily: DISPLAY, fontSize: 88, lineHeight: '96px', color: YELLOW, whiteSpace: 'nowrap' }}>{head[1]}</div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 404, height: 52, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {after
          ? <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 38, color: PAPER, background: CHOICE_BG[ep.answer], borderRadius: 12, padding: '4px 20px', letterSpacing: '-0.03em', whiteSpace: 'nowrap' }}>{ep.answerHead}</span>
          : ask ? <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 44, color: PAPER, letterSpacing: '-0.04em' }}>{q[0]}<span style={{ color: RED }}>{q[1]}</span></span> : null}
      </div>
    </>
  );
};

export const Quiz: React.FC<{ doc: QuizDoc }> = ({ doc }) => {
  const ep = doc.ep;
  const reveal = doc.cues.find((c) => c.scene === 'reveal');
  const R: Record<string, (c: QuizCue) => React.ReactNode> = {
    cling: (c) => <Cling a={c.a} p={c.p} />, push2: (c) => <Push2 a={c.a} p={c.p} />, hurt: (c) => <Hurt a={c.a} p={c.p} />, record: (c) => <Record a={c.a} p={c.p} />,
    remorse: (c) => <Remorse a={c.a} p={c.p} />, quiz: (c) => <QuizScene a={c.a} choices={ep.choices} />,
    reveal: (c) => <Reveal a={c.a} p={c.p} choices={ep.choices} answer={ep.answer} />, confiscate: (c) => <Confiscate a={c.a} />,
    incident: (c) => <Incident a={c.a} p={c.p} />, weigh: (c) => <Weigh a={c.a} p={c.p} choices={ep.choices} />,
    reason: (c) => <Reason a={c.a} p={c.p} subs={doc.subtitles.filter((s) => s.from_ >= c.from && s.from_ < c.from + c.dur).map((s) => s.from_ - c.from)} />, outro: (c) => <Outro a={c.a} p={c.p} />,
  };
  return (
    <AbsoluteFill style={{ background: '#0B0F1C' }}>
      <Header ep={ep} revealAt={reveal ? reveal.from + (reveal.p.headAt ? reveal.a[`s${reveal.p.headAt}`] : reveal.a.s1 + 2) : 1e9} />
      <div style={{ position: 'absolute', left: PANEL.x, top: PANEL.y, width: 1000 * PANEL.k, height: 900 * PANEL.k, overflow: 'hidden', borderRadius: 26, background: '#000' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, width: 1000, height: 900, transform: `scale(${PANEL.k})`, transformOrigin: '0 0' }}>
          {doc.cues.map((c) => {
            const r = R[c.scene];
            return r ? (
              <Sequence key={c.id} from={c.from} durationInFrames={c.dur} name={`${c.id} ${c.scene}`} layout="none">
                <AbsoluteFill>{r(c)}</AbsoluteFill>
              </Sequence>
            ) : null;
          })}
        </div>
        <div style={{ position: 'absolute', left: 54, bottom: 14, fontFamily: FONT, fontWeight: 700, fontSize: 22, color: 'rgba(255,253,246,0.85)', background: 'rgba(0,0,0,0.45)', padding: '3px 10px', borderRadius: 8 }}>
          {ep.source}
        </div>
      </div>
      <Caption subs={doc.subtitles} />
      {doc.audio && <Audio src={staticFile(doc.audio)} />}
    </AbsoluteFill>
  );
};
