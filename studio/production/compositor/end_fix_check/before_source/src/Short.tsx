// "역대급 판결" Shorts #1 (1080×1920): webtoon-style retelling of 대구지법 2023고단202.
// Scenes react to anchors computed from the narration (episodes/S001/build.py → public/s001/render.json).
import React from 'react';
import { AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame } from 'remotion';
import { FONT } from './theme';
import { loadFonts } from './fonts';
import {
  Bubble, Burst, Car, Flash, INK, NightLot, PAPER, Paper, ramp, RED, Sfx, Shake, SpeedLines, Stamp, Sweat, TEAL, usePop, YELLOW,
} from './components/toon';
import { Guy } from './components/rm';

export type ShortCue = { id: string; scene: string; from: number; dur: number; a: Record<string, number> };
export type ShortDoc = { fps: number; durationInFrames: number; cues: ShortCue[]; subtitles: { from_: number; to: number; text: string }[]; audio: string | null };

loadFonts();

const STAGE = { x: 0, y: 452, w: 1080, h: 972, k: 1.08 };

// ------------------------------------------------------------------ camera: snap zooms on the beats
type Key = [number, number, number, number];   // frame, centre x, centre y, zoom
const Cam: React.FC<{ keys: Key[]; children: React.ReactNode }> = ({ keys, children }) => {
  const f = useCurrentFrame();
  let k: Key = keys[0];
  let prev: Key = keys[0];
  for (const kk of keys) {
    if (f >= kk[0]) { prev = k; k = kk; }
  }
  const t = Math.min(1, (f - k[0]) / 12);
  const e = 1 - Math.pow(1 - t, 3);
  const cx = prev[1] + (k[1] - prev[1]) * e, cy = prev[2] + (k[2] - prev[2]) * e, z = prev[3] + (k[3] - prev[3]) * e;
  return <AbsoluteFill style={{ transform: `translate(${500 - cx * z}px, ${450 - cy * z}px) scale(${z})`, transformOrigin: '0 0' }}>{children}</AbsoluteFill>;
};

const Tag: React.FC<{ text: string; x: number; y: number; at: number; color: string }> = ({ text, x, y, at, color }) => {
  const p = usePop(at, 11);
  return (
    <div style={{ position: 'absolute', left: x, top: y, transform: `translateX(-50%) scale(${0.4 + 0.6 * p})`, opacity: Math.min(1, p * 2), fontFamily: FONT, fontWeight: 900, fontSize: 42,
      color: PAPER, background: color, border: `6px solid ${INK}`, borderRadius: 16, padding: '6px 20px', whiteSpace: 'nowrap', letterSpacing: '-0.03em' }}>{text}</div>
  );
};

// ------------------------------------------------------------------ scenes
const Hook: React.FC<{ a: Record<string, number> }> = ({ a }) => {
  const f = useCurrentFrame();
  const hit = a.s2 + 6;
  const lunge = ramp(f, a.s2 + 2, hit);
  const pushed = f >= hit;
  return (
    <Shake at={hit} len={10} amp={8}>
      <Cam keys={[[0, 540, 500, 1.12], [a.s1 + 30, 520, 470, 1.0], [hit, 760, 440, 1.3], [hit + 30, 560, 470, 1.0]]}>
        <NightLot />
        {f >= a.s2 && f < hit + 20 && <SpeedLines dir="right" />}
        <Car x={250 + 190 * lunge} y={740} />
        {!pushed
          ? <Guy look="B" x={700} y={850} scale={0.86} expr="angry" pose="point" flip talk={f > a.s1 && f < a.e1} seed={2} />
          : <Guy look="B" x={700 + 90 * ramp(f, hit, hit + 8)} y={850} scale={0.86} expr="shock" pose="pushed" flip rot={16 * ramp(f, hit, hit + 8)}
              squash={0.4 * (1 - ramp(f, hit, hit + 12))} seed={2} headPop={1 - ramp(f, hit, hit + 16)} />}
        {f < a.s2 && <Sfx text="📱" x={830} y={300} size={90} at={a.s1 + 8} rot={0} />}
      </Cam>
      <Tag text="피해자 · 30대 남성" x={700} y={60} at={a.s1 + 4} color={TEAL} />
      <Tag text="가해자 · 20대 여성 운전자" x={260} y={560} at={a.s1 + 14} color={RED} />
      {pushed && <Sfx text="부웅!" x={300} y={250} size={120} at={hit} color={YELLOW} />}
      <Flash at={hit} len={5} />
    </Shake>
  );
};

const Again: React.FC<{ a: Record<string, number> }> = ({ a }) => {
  const f = useCurrentFrame();
  const n1 = a.s1 + 2, n2 = a.s1 + 12, n3 = a.s1 + 22;
  const last = [n1, n2, n3].filter((n) => f >= n).pop() ?? -99;
  const step = ramp(f, n1, n1 + 6) + ramp(f, n2, n2 + 6) + ramp(f, n3, n3 + 6);
  const back = ramp(f, a.back, a.back + 18);
  const again = ramp(f, a.again + 6, a.hit);
  const phase = f < a.s2 ? 'push' : f < a.back ? 'down' : 'again';
  const carX = phase === 'push' ? 230 + 70 * step : 440 - 300 * back + 360 * again;
  const keys: [number, number, number, number][] = [[0, 520, 470, 1.0], [a.s2, 640, 600, 1.35], [a.back, 500, 470, 1.0]];
  return (
    <Shake at={phase === 'push' ? last : a.hit} len={phase === 'push' ? 5 : 10} amp={phase === 'push' ? 4 : 10}>
      <Cam keys={keys}>
        <NightLot />
        <Car x={carX} y={740} reverse={phase === 'again' && f < a.again + 4} />
        {phase === 'push' && <Guy look="B" x={690 + 50 * step} y={850} scale={0.84} expr="shock" pose="pushed" flip rot={10}
          squash={0.35 * Math.max(0, 1 - (f - last) / 6)} headPop={Math.max(0, 1 - (f - last) / 6)} seed={2} />}
        {phase === 'down' && <Guy look="B" x={700} y={860} scale={0.84} expr="dizzy" pose="sit" flip seed={2} />}
        {phase === 'again' && f < a.hit + 2 && <Guy look="B" x={790} y={850} scale={0.84} expr="scared" pose="stand" flip seed={2} />}
        {phase === 'again' && f < a.again && <Sfx text="후진~" x={260} y={360} size={110} at={a.back} color={PAPER} rot={4} />}
      </Cam>
      {phase === 'push' && [n1, n2, n3].map((n, i) => (f >= n ? <Sfx key={`n${n}`} text={`${i + 1}`} x={260 + i * 200} y={190} size={120} at={n} color={YELLOW} rot={0} /> : null))}
      {phase === 'again' && f >= a.hit && <Burst x={620} y={430} r={300} at={a.hit} text="쾅!" size={150} />}
      <Flash at={a.hit} len={7} />
    </Shake>
  );
};

const Injury: React.FC<{ a: Record<string, number> }> = ({ a }) => {
  const f = useCurrentFrame();
  const day = Math.max(1, Math.round(interpolate(f, [a.s1 + 6, a.s1 + 50], [1, 34], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })));
  const p = usePop(a.s1, 12);
  return (
    <AbsoluteFill>
      <Paper color="#F6E7D7" />
      <Guy look="B" x={270} y={1010} scale={1.3} expr="tired" pose="stand" seed={3} wobble={2} />
      <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
        <path d="M168,640 l26,-26 l10,22 l26,-30 l8,26 l30,-24" stroke={RED} strokeWidth={10} fill="none" strokeLinecap="round" strokeLinejoin="round" opacity={ramp(f, 4, 10)} />
        <rect x={150} y={650} width={90} height={34} rx={8} fill="#FFFFFF" stroke={INK} strokeWidth={6} transform="rotate(-24 195 667)" opacity={ramp(f, 8, 14)} />
      </svg>
      <div style={{ position: 'absolute', left: 560, top: 150, width: 380, transform: `scale(${0.6 + 0.4 * p})`, opacity: p }}>
        <div style={{ background: RED, border: `6px solid ${INK}`, borderBottom: 'none', borderRadius: '24px 24px 0 0', padding: '14px 0', textAlign: 'center', fontFamily: FONT, fontWeight: 900, fontSize: 44, color: PAPER }}>치료 기간</div>
        <div style={{ background: PAPER, border: `6px solid ${INK}`, borderRadius: '0 0 24px 24px', padding: '24px 0', textAlign: 'center' }}>
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 190, color: INK, letterSpacing: '-0.05em' }}>{day}</span>
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 80, color: INK }}>일</span>
        </div>
      </div>
      {f >= a.s1 + 52 && <Stamp lines={['어깨 부상', '약 34일 치료']} at={a.s1 + 52} x={740} y={720} size={84} />}
    </AbsoluteFill>
  );
};

const Claim: React.FC<{ a: Record<string, number> }> = ({ a }) => {
  const f = useCurrentFrame();
  const p = usePop(-4, 12);   // on screen from the cut, no empty frames
  return (
    <AbsoluteFill>
      <Paper color="#DCE6F2" />
      <Cam keys={[[0, 500, 450, 1.0], [a.b2, 480, 420, 1.1]]}>
        <div style={{ opacity: p, transform: `translateY(${(1 - p) * 60}px)` }}>
          <Guy look="A" x={260} y={1040} scale={1.25} expr={f < a.b2 ? 'smug' : 'scared'} pose="shrug" talk={f >= a.s2 && f < a.e2} seed={5} eye={f < a.b2 ? [10, -2] : [-8, 4]} />
          <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
            <circle cx={260} cy={900} r={170} fill="none" stroke={INK} strokeWidth={22} />
            <circle cx={260} cy={900} r={40} fill={INK} />
          </svg>
          <Sweat x={410} y={230} at={a.b2} />
        </div>
      </Cam>
      <div style={{ position: 'absolute', left: 40, top: 40, opacity: p }}>
        <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 40, color: PAPER, background: RED, padding: '8px 20px', borderRadius: 10, border: `5px solid ${INK}` }}>가해자(20대 여성) 측 주장</span>
      </div>
      <Bubble text="부주의한 운전 탓" x={480} y={150} w={480} at={a.b1} tail="left" dashed size={56} />
      <Bubble text={'저 사람이\n뛰어들었다'} x={560} y={440} w={400} at={a.b2} tail="left" dashed size={56} />
    </AbsoluteFill>
  );
};

const Bench: React.FC = () => (
  <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
    <rect x={0} y={0} width={1000} height={900} fill="#5A3B22" />
    {Array.from({ length: 22 }, (_, i) => <rect key={`p${i}`} x={i * 46} y={0} width={30} height={560} fill="#6E4A2B" stroke={INK} strokeWidth={3} />)}
    <rect x={-10} y={560} width={1020} height={360} fill="#8A5A32" stroke={INK} strokeWidth={8} />
    <rect x={-10} y={540} width={1020} height={40} fill="#A06C3E" stroke={INK} strokeWidth={8} />
  </svg>
);

const Court: React.FC<{ a: Record<string, number> }> = ({ a }) => {
  const f = useCurrentFrame();
  const rec = Math.floor(f / 12) % 2 === 0;
  if (f < a.court) {
    return (
      <AbsoluteFill>
        <NightLot glow={0.6} />
        <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
          <rect x={470} y={120} width={30} height={300} fill="#2A2F3A" stroke={INK} strokeWidth={6} />
          <g transform={`translate(500 160) rotate(${-14 + Math.sin(f / 10) * 4})`}>
            <rect x={-300} y={-70} width={330} height={140} rx={18} fill="#E9EBEE" stroke={INK} strokeWidth={8} />
            <circle cx={-300} cy={0} r={52} fill="#20252E" stroke={INK} strokeWidth={8} />
            <circle cx={-300} cy={0} r={22} fill="#6FA8FF" />
          </g>
        </svg>
        <div style={{ position: 'absolute', left: 120, top: 380, display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 34, height: 34, borderRadius: 17, background: rec ? RED : '#5a1d1a', border: `5px solid ${INK}` }} />
          <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 64, color: PAPER, WebkitTextStroke: `6px ${INK}`, paintOrder: 'stroke fill' }}>REC</span>
        </div>
        <Sfx text="현장 CCTV" x={500} y={640} size={110} at={a.s1 + 6} color={YELLOW} rot={-4} />
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill>
      <Cam keys={[[0, 500, 450, 1.0], [a.s2, 500, 400, 1.12]]}>
        <Bench />
        <Guy look="judge" x={500} y={760} scale={0.95} expr={f >= a.s2 ? 'angry' : 'serious'} pose="stand" talk={f >= a.s2 && f < a.e2} seed={7} headPop={f >= a.court && f < a.court + 8 ? 1 - (f - a.court) / 8 : 0} />
        <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
          <rect x={-10} y={560} width={1020} height={360} fill="#8A5A32" stroke={INK} strokeWidth={8} />
          <rect x={-10} y={540} width={1020} height={40} fill="#A06C3E" stroke={INK} strokeWidth={8} />
        </svg>
      </Cam>
      <Stamp lines={['고의 인정']} at={a.court + 4} x={500} y={760} size={110} color={TEAL} rot={-6} />
      {f >= a.s2 && <Bubble text={'진지한 반성을 하고 있다고\n평가할 수 없다'} x={60} y={70} w={880} at={a.s2} tail="down" label="판결 이유 · 보도 인용" size={54} />}
    </AbsoluteFill>
  );
};

const Vote: React.FC<{ a: Record<string, number> }> = ({ a }) => {
  const f = useCurrentFrame();
  const l = usePop(0, 12);
  const r = usePop(5, 12);
  const end = f > a.e2 + 6;
  return (
    <AbsoluteFill style={{ background: INK }}>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 70, textAlign: 'center', fontFamily: FONT, fontWeight: 900, fontSize: 92, color: YELLOW, letterSpacing: '-0.04em' }}>
        여러분이 판사라면?
      </div>
      {[{ t: '실형', c: RED, p: l, x: 40 }, { t: '집행유예', c: TEAL, p: r, x: 520 }].map((b, i) => (
        <div key={b.t} style={{
          position: 'absolute', left: b.x, top: 260, width: 440, height: 440, borderRadius: 40, background: b.c, border: `10px solid ${PAPER}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${0.6 + 0.4 * b.p})`, opacity: Math.min(1, b.p * 2),
          fontFamily: FONT, fontWeight: 900, fontSize: i === 0 ? 140 : 100, color: PAPER, letterSpacing: '-0.04em',
        }}>{b.t}</div>
      ))}
      <div style={{ position: 'absolute', left: 430, top: 420, width: 140, height: 140, borderRadius: 70, background: PAPER, border: `8px solid ${INK}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT, fontWeight: 900, fontSize: 56 }}>VS</div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 760, textAlign: 'center', fontFamily: FONT, fontWeight: 800, fontSize: 52, color: PAPER, opacity: ramp(f, a.s2 + 14, a.s2 + 24) }}>
        👇 댓글로 먼저 골라 보세요
      </div>
      {end && <AbsoluteFill style={{ background: `rgba(0,0,0,${ramp(f, a.e2 + 6, a.e2 + 30) * 0.7})` }} />}
    </AbsoluteFill>
  );
};

const Verdict: React.FC<{ a: Record<string, number> }> = ({ a }) => {
  const f = useCurrentFrame();
  const hit = a.s1 + 2;
  const swing = interpolate(f, [0, hit - 4, hit], [-38, -40, 8], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <Shake at={hit} len={8} amp={7}>
      <Bench />
      <Guy look="judge" x={330} y={760} scale={0.85} expr="serious" pose="stand" seed={7} headPop={f >= hit && f < hit + 10 ? 1 - (f - hit) / 10 : 0} />
      <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
        <rect x={-10} y={560} width={1020} height={360} fill="#8A5A32" stroke={INK} strokeWidth={8} />
        <rect x={-10} y={540} width={1020} height={40} fill="#A06C3E" stroke={INK} strokeWidth={8} />
      </svg>
      <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
        <rect x={360} y={600} width={280} height={60} rx={14} fill="#3B2414" stroke={INK} strokeWidth={8} />
        <g transform={`translate(640 590) rotate(${swing})`}>
          <rect x={-20} y={-300} width={40} height={300} rx={14} fill="#A06C3E" stroke={INK} strokeWidth={8} />
          <rect x={-110} y={-370} width={220} height={110} rx={30} fill="#7A4A26" stroke={INK} strokeWidth={8} />
        </g>
      </svg>
      {f >= hit && <Sfx text="탕!" x={760} y={300} size={150} at={hit} color={YELLOW} />}
      {f >= a.jing && <Stamp lines={['징역 8개월']} at={a.jing} x={500} y={250} size={130} color={INK} rot={-5} />}
      {f >= a.yu && <Stamp lines={['집행유예 2년', '사회봉사 120시간']} at={a.yu} x={500} y={520} size={120} color={RED} rot={4} />}
      <Flash at={hit} len={6} />
    </Shake>
  );
};

const Why: React.FC<{ a: Record<string, number> }> = ({ a }) => {
  const f = useCurrentFrame();
  const w = [a.w2, a.w3, a.w4].map((t) => ramp(f, t, t + 10));
  const left = ramp(f, a.w1, a.w1 + 10);
  const tilt = (left * 1 - (w[0] + w[1] + w[2]) * 0.9) * 7;
  const cx = 500, top = 250, arm = 300;
  const rad = (tilt * Math.PI) / 180;
  const ly = top + Math.sin(rad) * arm, ry = top - Math.sin(rad) * arm;
  const Weight: React.FC<{ t: string; c: string; p: number; x: number; y: number; dy: number }> = ({ t, c, p, x, y, dy }) => (
    <div style={{
      position: 'absolute', left: x - 165, top: y + dy, width: 330, textAlign: 'center', opacity: p, transform: `translateY(${(1 - p) * -120}px)`,
      fontFamily: FONT, fontWeight: 900, fontSize: 40, color: PAPER, background: c, border: `6px solid ${INK}`, borderRadius: 20, padding: '8px 0',
    }}>{t}</div>
  );
  return (
    <AbsoluteFill>
      <Paper color="#F2EBDC" />
      <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
        <line x1={cx} y1={top} x2={cx} y2={820} stroke={INK} strokeWidth={16} />
        <polygon points={`${cx - 150},830 ${cx + 150},830 ${cx},770`} fill={INK} />
        <line x1={cx - Math.cos(rad) * arm} y1={ly} x2={cx + Math.cos(rad) * arm} y2={ry} stroke={INK} strokeWidth={16} strokeLinecap="round" />
        <circle cx={cx} cy={top} r={26} fill={YELLOW} stroke={INK} strokeWidth={6} />
        <line x1={cx - Math.cos(rad) * arm} y1={ly} x2={cx - Math.cos(rad) * arm} y2={ly + 90} stroke={INK} strokeWidth={6} />
        <line x1={cx + Math.cos(rad) * arm} y1={ry} x2={cx + Math.cos(rad) * arm} y2={ry + 90} stroke={INK} strokeWidth={6} />
      </svg>
      <div style={{ position: 'absolute', left: cx - Math.cos(rad) * arm - 170, top: ly + 30, width: 340, textAlign: 'center', fontFamily: FONT, fontWeight: 900, fontSize: 40, color: RED }}>불리</div>
      <div style={{ position: 'absolute', left: cx + Math.cos(rad) * arm - 170, top: ry + 30, width: 340, textAlign: 'center', fontFamily: FONT, fontWeight: 900, fontSize: 40, color: TEAL }}>유리</div>
      <Weight t="반성 없음" c={RED} p={left} x={cx - Math.cos(rad) * arm} y={ly} dy={100} />
      <Weight t="초범" c={TEAL} p={w[0]} x={cx + Math.cos(rad) * arm} y={ry} dy={100} />
      <Weight t="들이받은 건 인정" c={TEAL} p={w[1]} x={cx + Math.cos(rad) * arm} y={ry} dy={180} />
      <Weight t="신고가 두려웠음" c={TEAL} p={w[2]} x={cx + Math.cos(rad) * arm} y={ry} dy={260} />
    </AbsoluteFill>
  );
};

const Ask: React.FC<{ a: Record<string, number> }> = ({ a }) => {
  const f = useCurrentFrame();
  const p = usePop(a.s1, 11);
  const pulse = 1;
  return (
    <AbsoluteFill>
      <NightLot glow={0.5} />
      <AbsoluteFill style={{ background: 'rgba(10,14,30,0.45)' }} />
      <Guy look="B" x={760} y={980} scale={1.0} expr="talk" pose="point" flip talk={f >= a.s1 && f < a.e1} seed={2} />
      <div style={{ position: 'absolute', left: 90, top: 150, width: 820, transform: `scale(${(0.5 + 0.5 * p) * pulse})`, opacity: p, textAlign: 'center' }}>
        <div style={{ background: PAPER, border: `8px solid ${INK}`, borderRadius: 50, padding: '40px 20px', fontFamily: FONT, fontWeight: 900, fontSize: 92, color: INK, letterSpacing: '-0.04em' }}>
          💬 여러분 생각은?
        </div>
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 560, textAlign: 'center', opacity: ramp(f, a.s1 + 20, a.s1 + 30) }}>
        <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 60, color: PAPER, background: RED, border: `6px solid ${INK}`, borderRadius: 18, padding: '12px 36px' }}>역대급 판결</span>
      </div>
    </AbsoluteFill>
  );
};

const SCENES: Record<string, React.FC<{ a: Record<string, number> }>> = {
  hook: Hook, again: Again, injury: Injury, claim: Claim, court: Court, vote: Vote, verdict: Verdict, why: Why, ask: Ask,
};

// ------------------------------------------------------------------ frame
const HL = /(\d+일|\d+개월|\d+년|집행유예|실형|고의|반성|초범|CCTV|여러 번|한 번 더|판사)/g;
const Caption: React.FC<{ subs: ShortDoc['subtitles'] }> = ({ subs }) => {
  const f = useCurrentFrame();
  const s = subs.find((x) => f >= x.from_ && f < x.to);
  if (!s) return null;
  const pop = Math.min(1, (f - s.from_) / 4);
  const parts = s.text.split(HL);
  return (
    <div style={{ position: 'absolute', left: 50, right: 110, top: 1450, textAlign: 'center', transform: `scale(${0.9 + 0.1 * pop})` }}>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 74, lineHeight: 1.22, color: PAPER, WebkitTextStroke: `12px ${INK}`, paintOrder: 'stroke fill', letterSpacing: '-0.03em', whiteSpace: 'pre-line' }}>
        {parts.map((p, i) => <span key={`${s.from_}-${i}`} style={{ color: HL.test(p) ? YELLOW : PAPER }}>{p}</span>)}
      </div>
    </div>
  );
};

const Header: React.FC<{ revealAt: number }> = ({ revealAt }) => {
  const f = useCurrentFrame();
  const after = f >= revealAt;
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, top: 92, textAlign: 'center' }}>
      <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 38, color: PAPER, background: RED, borderRadius: 12, padding: '5px 22px' }}>역대급 판결</span>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 60, color: PAPER, marginTop: 18, letterSpacing: '-0.04em', lineHeight: 1.12 }}>음주운전 신고하려던 사람을</div>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 76, color: PAPER, letterSpacing: '-0.04em', lineHeight: 1.12 }}>차로 <span style={{ color: RED }}>2번</span> 박았다</div>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 70, color: YELLOW, letterSpacing: '-0.04em', lineHeight: 1.15 }}>{after ? '판결: 집행유예 2년' : '판결은?'}</div>
    </div>
  );
};

export const Short: React.FC<{ doc: ShortDoc }> = ({ doc }) => {
  const reveal = doc.cues.find((c) => c.scene === 'verdict');
  return (
    <AbsoluteFill style={{ background: '#0B0F1C' }}>
      <Header revealAt={reveal ? reveal.from + (reveal.a.yu ?? 0) : 1e9} />
      <div style={{ position: 'absolute', left: STAGE.x, top: STAGE.y, width: STAGE.w, height: STAGE.h, overflow: 'hidden', borderTop: `10px solid ${INK}`, borderBottom: `10px solid ${INK}`, background: '#000' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, width: 1000, height: 900, transform: `scale(${STAGE.k})`, transformOrigin: '0 0' }}>
        {doc.cues.map((c) => {
          const Scene = SCENES[c.scene];
          return Scene ? (
            <Sequence key={c.id} from={c.from} durationInFrames={c.dur} name={`${c.id} ${c.scene}`} layout="none">
              <AbsoluteFill><Scene a={c.a} /></AbsoluteFill>
            </Sequence>
          ) : null;
        })}
        </div>
        <div style={{ position: 'absolute', left: 20, bottom: 14, fontFamily: FONT, fontWeight: 700, fontSize: 24, color: 'rgba(255,253,246,0.85)', background: 'rgba(0,0,0,0.45)', padding: '4px 12px', borderRadius: 8 }}>
          판결 보도 기반 재구성 · 대구지법 2023고단202
        </div>
      </div>
      <Caption subs={doc.subtitles} />
      {doc.audio && <Audio src={staticFile(doc.audio)} />}
    </AbsoluteFill>
  );
};
