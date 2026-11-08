// Channel art for "몇년나옴": profile icon (800×800, shown as a circle down to ~40 px) and banner
// (2560×1440; every device shows the centre 1546×423, desktop shows the full-width 423 band).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { DISPLAY, FONT } from './theme';
import { loadFonts } from './fonts';
import { Guy } from './components/rm';
import { INK, PAPER, RED, TEAL, YELLOW } from './components/toon';

loadFonts();

const Bars: React.FC<{ n: number; x0: number; gap: number; w: number; color: string; top?: number; h?: number }> = ({ n, x0, gap, w, color, top = 0, h = 1440 }) => (
  <>
    {Array.from({ length: n }, (_, i) => (
      <div key={`bar${x0 + i * gap}`} style={{ position: 'absolute', left: x0 + i * gap, top, width: w, height: h, background: color, borderRadius: w / 2 }} />
    ))}
  </>
);

// Logo: the name as a tight two-line block that reads as the question itself ("몇년 / 나옴?"),
// readable as a circle at 32 px, with jail bars behind it — the channel is a sentencing quiz.
const Logo: React.FC<{ size: number }> = ({ size }) => (
  <div style={{ position: 'relative', width: size, height: size, background: YELLOW, overflow: 'hidden' }}>
    <div style={{ position: 'absolute', inset: 0, transform: `scale(${size / 800})`, transformOrigin: '0 0', width: 800, height: 800 }}>
      <Bars n={6} x0={95} gap={122} w={32} color="#E9BC1E" h={800} />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 168, textAlign: 'center', fontFamily: DISPLAY, fontSize: 236, lineHeight: 0.98, color: INK, letterSpacing: '-0.02em' }}>
        <div>몇년</div>
        <div>나옴<span style={{ color: RED, marginLeft: 6 }}>?</span></div>
      </div>
    </div>
  </div>
);

export const ChannelIcon: React.FC = () => <Logo size={800} />;

const CHOICES: [string, string, string][] = [['A', '벌금', '#8A93A6'], ['B', '집행유예', TEAL], ['C', '실형', RED]];

export const ChannelBanner: React.FC = () => (
  <AbsoluteFill style={{ background: INK }}>
    {/* desktop-only edges: courtroom wood and the cast, kept inside the 423 px band */}
    <AbsoluteFill style={{ background: 'linear-gradient(90deg, #5A3B22 0%, #3A2716 18%, #16181F 30%, #16181F 70%, #3A2716 82%, #5A3B22 100%)' }} />
    <Bars n={4} x0={30} gap={110} w={26} color="rgba(255,216,74,0.10)" />
    <Bars n={4} x0={2200} gap={110} w={26} color="rgba(255,216,74,0.10)" />
    <div style={{ position: 'absolute', left: 120, top: 425, width: 1000, height: 900, transform: 'scale(0.62)', transformOrigin: '0 0' }}>
      <Guy look="D" x={260} y={1000} scale={1} expr="smug" pose="shrug" wobble={0} seed={6} />
    </div>
    <div style={{ position: 'absolute', left: 1880, top: 425, width: 1000, height: 900, transform: 'scale(0.62)', transformOrigin: '0 0' }}>
      <Guy look="judge" x={500} y={1000} scale={1} expr="serious" pose="stand" wobble={0} seed={7} />
    </div>
    {/* Every device shows the centre 1546×423 (x 507–2053, y 509–932); phones also round its corners.
        Keep everything inside a 1300×340 box centred in it (≥120 px side margin) — owner 2026-10-26: the
        first version touched the safe-area edge and phones clipped "몇" and the chips. */}
    <div style={{ position: 'absolute', left: 630, top: 550, width: 1300, height: 340, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div>
        <div style={{ fontFamily: DISPLAY, fontSize: 168, lineHeight: 1, color: YELLOW, letterSpacing: '-0.02em', whiteSpace: 'nowrap' }}>몇년나옴<span style={{ color: RED }}>?</span></div>
        <div style={{ marginTop: 24, fontFamily: FONT, fontWeight: 800, fontSize: 54, color: PAPER, letterSpacing: '-0.03em', whiteSpace: 'nowrap' }}>실제 판결로 만든 <span style={{ color: YELLOW }}>형량 퀴즈</span></div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {CHOICES.map(([k, c, bg]) => (
          <div key={k} style={{ width: 380, height: 92, borderRadius: 22, background: bg, border: `6px solid ${PAPER}`, display: 'flex', alignItems: 'center', gap: 20, paddingLeft: 22, boxSizing: 'border-box' }}>
            <span style={{ width: 60, height: 60, borderRadius: 30, background: PAPER, color: INK, fontFamily: FONT, fontWeight: 800, fontSize: 44, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{k}</span>
            <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: 52, color: PAPER, letterSpacing: '-0.03em' }}>{c}</span>
          </div>
        ))}
      </div>
    </div>
  </AbsoluteFill>
);

// Proof sheet: the icon at the sizes YouTube shows it, cropped to a circle.
export const ChannelIconSizes: React.FC = () => (
  <AbsoluteFill style={{ background: '#F1F1F1', display: 'flex', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 60 }}>
    {[400, 176, 88, 48, 32].map((s) => (
      <div key={s} style={{ width: s, height: s, borderRadius: s / 2, overflow: 'hidden' }}><Logo size={s} /></div>
    ))}
    <div style={{ background: '#0F0F0F', padding: 30, display: 'flex', gap: 40, alignItems: 'center', borderRadius: 20 }}>
      {[88, 48, 32].map((s) => <div key={s} style={{ width: s, height: s, borderRadius: s / 2, overflow: 'hidden' }}><Logo size={s} /></div>)}
    </div>
  </AbsoluteFill>
);

// Proof: the banner as each surface crops it — phone (safe area, rounded), desktop (full-width 423 band), TV (all).
export const ChannelBannerCrops: React.FC = () => (
  <AbsoluteFill style={{ background: '#F1F1F1', padding: 40, display: 'flex', flexDirection: 'column', gap: 40 }}>
    {[['phone', 507, 1546, 0.62, 24], ['desktop', 0, 2560, 0.5, 12]].map(([name, x0, w, k, r]) => (
      <div key={String(name)} style={{ width: Number(w) * Number(k), height: 423 * Number(k), overflow: 'hidden', borderRadius: Number(r), position: 'relative', outline: '2px solid #999' }}>
        <div style={{ position: 'absolute', left: -Number(x0) * Number(k), top: -509 * Number(k), width: 2560, height: 1440, transform: `scale(${k})`, transformOrigin: '0 0' }}><ChannelBanner /></div>
      </div>
    ))}
    <div style={{ width: 2560 * 0.25, height: 1440 * 0.25, overflow: 'hidden', position: 'relative', outline: '2px solid #999' }}>
      <div style={{ position: 'absolute', inset: 0, width: 2560, height: 1440, transform: 'scale(0.25)', transformOrigin: '0 0' }}><ChannelBanner /></div>
    </div>
  </AbsoluteFill>
);
