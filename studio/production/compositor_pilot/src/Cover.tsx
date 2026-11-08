// "몇년나옴" Shorts cover (1080×1920). One fixed grid for every episode so the channel's Shorts shelf
// reads as a series: every block has a fixed box and a fixed font size, and only the words change.
// Owner 2026-10-26: "대표이미지들 레이아웃쉬프트 없어야돼".
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { FONT } from './theme';
import { loadFonts } from './fonts';
import { Burst, Car, INK, NightLot, PAPER, RED, SpeedLines, TEAL, YELLOW } from './components/toon';
import { Guy, Look } from './components/rm';
import { Header, Incident, PANEL, QuizDoc } from './Quiz';

loadFonts();

const ROAD_LINES = [0, 1, 2, 3, 4, 5];

const ClingSet: React.FC<{ victim: Look; dist: number }> = ({ victim, dist }) => (
  <>
    <NightLot glow={0.7} />
    <svg width={1000} height={900} style={{ position: 'absolute', inset: 0 }}>
      <rect x={0} y={600} width={1000} height={300} fill="#3E3A4C" stroke={INK} strokeWidth={6} />
      {ROAD_LINES.map((i) => <rect key={`ln${i}`} x={i * 180 - 60} y={760} width={110} height={16} rx={8} fill="#F2E9C9" />)}
    </svg>
    <SpeedLines dir="right" opacity={0.6} />
    <Car x={520} y={760} />
    <Guy look={victim} x={170} y={728} scale={0.62} expr="scared" pose="cling" rot={78} seed={3} wobble={0} />
    <div style={{ position: 'absolute', left: 0, right: 0, top: 40, textAlign: 'center', fontFamily: FONT, fontWeight: 800, fontSize: 140, color: YELLOW,
      WebkitTextStroke: `14px ${INK}`, paintOrder: 'stroke fill', letterSpacing: '-0.04em' }}>{dist}m</div>
  </>
);

const PushSet: React.FC = () => (
  <>
    <NightLot />
    <Car x={690 - 10 - 268} y={740} />
    <Guy look="B" x={690} y={850} scale={0.84} expr="shock" pose="pushed" flip rot={8} seed={2} wobble={0} />
    <Burst x={330} y={250} r={210} text="쾅!" size={110} at={-60} />
  </>
);

const CHIPS: [string, string, string][] = [['A', '벌금', '#8A93A6'], ['B', '집행유예', TEAL], ['C', '실형', RED]];

// The cover is the video's own first frame minus the caption: same header, same panel box. Whatever
// frame YouTube picks before the reveal then matches the cover too.
export const Cover: React.FC<{ doc: QuizDoc }> = ({ doc }) => {
  const first = doc.cues[0];
  return (
    <AbsoluteFill style={{ background: '#0B0F1C' }}>
      <Header ep={doc.ep} revealAt={1e9} />
      <div style={{ position: 'absolute', left: PANEL.x, top: PANEL.y, width: 1000 * PANEL.k, height: 900 * PANEL.k, overflow: 'hidden', borderRadius: 26, background: '#000' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, width: 1000, height: 900, transform: `scale(${PANEL.k})`, transformOrigin: '0 0' }}>
          {first.scene === 'push2' ? <PushSet /> : first.scene === 'incident' ? <Incident a={{ s1: -300 }} p={first.p} /> : <ClingSet victim={first.p.victim as Look} dist={first.p.dist} />}
        </div>
      </div>
      {/* the three answers, where the caption sits in the video; the grid's view count covers y ≥ 1720 */}
      <div style={{ position: 'absolute', left: 110, right: 110, top: 1360, height: 112, display: 'flex', gap: 14 }}>
        {doc.ep.choices.map((c, i) => (
          <div key={c} style={{ flex: 1, borderRadius: 26, background: CHIPS[i][2], border: `7px solid ${PAPER}`, boxSizing: 'border-box', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
            <span style={{ width: 58, height: 58, borderRadius: 29, background: PAPER, color: INK, fontFamily: FONT, fontWeight: 800, fontSize: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{CHIPS[i][0]}</span>
            <span style={{ fontFamily: FONT, fontWeight: 800, fontSize: c.length > 4 ? 38 : 44, color: PAPER, letterSpacing: '-0.04em', whiteSpace: 'nowrap' }}>{c}</span>
          </div>
        ))}
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 1486, textAlign: 'center', fontFamily: FONT, fontWeight: 700, fontSize: 34, color: 'rgba(255,253,246,0.72)', letterSpacing: '-0.02em' }}>
        실제 판결 · {doc.ep.source.replace('보도 기반 재구성 · ', '')}
      </div>
    </AbsoluteFill>
  );
};

// Proof: all five covers side by side, as the channel's Shorts shelf shows them.
export const CoverShelf: React.FC<{ docs: QuizDoc[] }> = ({ docs }) => (
  <AbsoluteFill style={{ background: '#0F0F0F', display: 'flex', flexDirection: 'row', gap: 24, padding: 40 }}>
    {docs.map((d) => (
      <div key={d.ep.no} style={{ width: 1080, height: 1920, transform: 'scale(0.3)', transformOrigin: '0 0', marginRight: 1080 * 0.3 - 1080, borderRadius: 40, overflow: 'hidden', flexShrink: 0 }}>
        <Cover doc={d} />
      </div>
    ))}
  </AbsoluteFill>
);
