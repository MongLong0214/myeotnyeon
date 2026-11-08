import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import type {QuizDoc} from './Quiz';
import {DISPLAY, FONT} from './theme';

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
// Existing hook copy, broken at spaces only. No factual text is authored here.
export const headline51 = (doc: QuizDoc): string[] => {
  const text = (doc.ep.hook?.lines ?? doc.ep.head)[0];
  const words = text.split(' ');
  const rows: string[] = [];
  let row = '';
  for (const word of words) {
    if (row && (row + ' ' + word).length > 7) {rows.push(row); row = word;}
    else row = row ? row + ' ' + word : word;
  }
  if (row) rows.push(row);
  return rows;
};
const HERO_IDS: Record<number, string> = {13: 'q013_clouds', 14: 'q014'};
const Hero: React.FC<{doc: QuizDoc; end?: boolean}> = ({doc, end = false}) => {
  const frame = useCurrentFrame();
  const f = end ? frame - (doc.durationInFrames - 45) : frame;
  const zoom = interpolate(f, [0, end ? 44 : 75], [end ? 1.04 : 1, 1.10], clamp);
  const pulse = .5 + .5 * Math.sin(f * .31 + doc.ep.no);
  return <AbsoluteFill style={{overflow: 'hidden'}}>
    <Img data-v51-hero src={staticFile(`hook_v51/${HERO_IDS[doc.ep.no]}.png`)}
      style={{width: 1080, height: 1920, objectFit: 'cover', transform: `scale(${zoom})`, transformOrigin: '50% 68%', filter: `brightness(${end ? .36 : .99 + pulse * .045})`}} />
    <AbsoluteFill style={{background: `radial-gradient(ellipse at ${20 + f * .18}% 90%, rgba(12,70,150,${.02 + pulse * .055}), transparent 58%)`, mixBlendMode: 'screen', transform: `translateY(${-f * .3}px) scale(1.03)`}} />
    <AbsoluteFill style={{background: 'linear-gradient(180deg, #02070b00 12%, #02070b10 45%, #02070b00 70%, #02070b42 100%)'}} />
  </AbsoluteFill>;
};

export const HookV51: React.FC<{doc: QuizDoc}> = ({doc}) => {
  const f = useCurrentFrame();
  const rows = headline51(doc);
  const slam = interpolate(f, [0, 2, 4], [.96, 1.025, 1], clamp);
  return <AbsoluteFill data-v51-hook>
    <Hero doc={doc} />
    <div data-v51-headline style={{position: 'absolute', left: 120, top: 435, width: 830, fontFamily: DISPLAY, fontWeight: 400, fontSize: 156, lineHeight: 1.12, letterSpacing: '-.055em', transform: `scale(${slam})`, transformOrigin: '50% 50%'}}>
      {rows.map((row, i) => <div key={i} style={{height: 184, display: 'flex', justifyContent: 'center', alignItems: 'center', background: '#030405f5', marginBottom: 3, boxShadow: '0 8px 25px #0004'}}>
        <span data-v51-headline-row style={{display: 'block', whiteSpace: 'nowrap', color: i === 0 ? '#fffdf6' : '#ff302a', transform: `scaleX(${row.replace(/\s/g, '').length > 5 ? .87 : 1})`, textShadow: '0 3px 0 #000'}}>{row.split(/(\d+)/g).map((part, j) => /^\d+$/.test(part) ? <span key={j} style={{color: '#ff302a', fontSize: 184, lineHeight: 1}}>{part}</span> : <React.Fragment key={j}>{part}</React.Fragment>)}</span>
      </div>)}
    </div>
    <div data-v51-ask style={{position: 'absolute', left: 140, top: rows.length > 2 ? 1080 : 950, width: 720, color: '#fffdf6', fontFamily: FONT, fontWeight: 800, fontSize: 60, lineHeight: 1.25, letterSpacing: '-.045em', textShadow: '0 3px 8px #000, 0 0 24px #000', WebkitTextStroke: '2px #090b10', paintOrder: 'stroke fill'}}>{doc.ep.hook?.ask ?? doc.ep.ask}</div>
  </AbsoluteFill>;
};

export const EndV51: React.FC<{doc: QuizDoc}> = ({doc}) => {
  const f = useCurrentFrame() - (doc.durationInFrames - 45);
  return <AbsoluteFill data-v51-cta style={{color: '#fffdf6', fontFamily: DISPLAY}}>
    <Hero doc={doc} end />
    {/* This continuous CTA card occupies 51.9% of the portrait, with all glyphs in phone-safe zones. */}
    <div data-v51-cta-card style={{position: 'absolute', left: 110, top: 210, width: 860, height: 1250, background: 'linear-gradient(160deg,#050b12ef,#0d1824cf)', border: '3px solid #f7f4e63a', borderRadius: 36, boxSizing: 'border-box', boxShadow: '0 24px 100px #0009'}}>
      <div style={{position: 'absolute', left: 26, top: 160, width: 800, fontSize: 144, lineHeight: 1.25, letterSpacing: '-.06em'}}>다음 판결도</div>
      <div style={{position: 'absolute', left: 26, top: 360, width: 800, fontSize: 144, lineHeight: 1.25, letterSpacing: '-.06em'}}>맞혀보세요</div>
      <div data-v51-subscribe style={{position: 'absolute', left: 30, top: 690, width: 710, height: 255, borderRadius: 36, background: '#f12d2b', boxShadow: `0 10px 35px #ef292b${f % 20 < 10 ? '50' : '28'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 45}}>
        <svg width={82} height={94} viewBox="0 0 40 44" aria-hidden="true"><path d="M5 3 L36 22 L5 41 Z" fill="#fffdf6" /></svg>
        <span style={{fontSize: 165, lineHeight: 1}}>구독</span>
      </div>
      <div style={{position: 'absolute', left: 36, top: 1090, fontFamily: FONT, fontWeight: 700, fontSize: 34}}>몇년나옴? · 형량 퀴즈 #{doc.ep.no}</div>
    </div>
  </AbsoluteFill>;
};
