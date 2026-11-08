import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import type {QuizDoc} from '../Quiz';
import {DISPLAY, FONT} from '../theme';
import {headline51} from '../HookV51Revised';

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const HERO_IDS: Record<number, string> = {13: 'q013_clouds', 14: 'q014'};
const Hero52: React.FC<{doc: QuizDoc}> = ({doc}) => {
  const f = useCurrentFrame();
  const zoom = interpolate(f, [0, 60], [1, 1.12], clamp);
  const pulse = .5 + .5 * Math.sin(f * .31 + doc.ep.no);
  return <AbsoluteFill style={{overflow: 'hidden'}}>
    <Img data-v51-hero data-v52-zoom={zoom} src={staticFile(`hook_v51/${HERO_IDS[doc.ep.no]}.png`)}
      style={{width: 1080, height: 1920, objectFit: 'cover', transform: `scale(${zoom})`, transformOrigin: '50% 68%', filter: `brightness(${.99 + pulse * .045})`}} />
    <AbsoluteFill style={{background: `radial-gradient(ellipse at ${20 + f * .18}% 90%, rgba(12,70,150,${.02 + pulse * .055}), transparent 58%)`, mixBlendMode: 'screen', transform: `translateY(${-f * .3}px) scale(1.03)`}} />
    <AbsoluteFill style={{background: 'linear-gradient(180deg, #02070b00 12%, #02070b10 45%, #02070b00 70%, #02070b42 100%)'}} />
  </AbsoluteFill>;
};

export const HookV52: React.FC<{doc: QuizDoc}> = ({doc}) => {
  const f = useCurrentFrame();
  const rows = headline51(doc);
  const slam = interpolate(f, [0, 2, 4], [.96, 1.025, 1], clamp);
  return <AbsoluteFill data-v51-hook>
    <Hero52 doc={doc} />
    <div data-v51-headline style={{position: 'absolute', left: 120, top: 435, width: 830, fontFamily: DISPLAY, fontWeight: 400, fontSize: 156, lineHeight: 1.12, letterSpacing: '-.055em', transform: `scale(${slam})`, transformOrigin: '50% 50%'}}>
      {rows.map((row, i) => <div key={i} style={{height: 184, display: 'flex', justifyContent: 'center', alignItems: 'center', background: '#030405f5', marginBottom: 3, boxShadow: '0 8px 25px #0004'}}>
        <span data-v51-headline-row style={{display: 'block', whiteSpace: 'nowrap', color: i === 0 ? '#fffdf6' : '#ff302a', transform: `scaleX(${row.replace(/\s/g, '').length > 5 ? .87 : 1})`, textShadow: '0 3px 0 #000'}}>{row.split(/(\d+)/g).map((part, j) => /^\d+$/.test(part) ? <span key={j} style={{color: '#ff302a', fontSize: 184, lineHeight: 1}}>{part}</span> : <React.Fragment key={j}>{part}</React.Fragment>)}</span>
      </div>)}
    </div>
    <div data-v51-ask style={{position: 'absolute', left: 140, top: rows.length > 2 ? 1080 : 950, width: 720, color: '#fffdf6', fontFamily: FONT, fontWeight: 800, fontSize: 60, lineHeight: 1.25, letterSpacing: '-.045em', textShadow: '0 3px 8px #000, 0 0 24px #000', WebkitTextStroke: '2px #090b10', paintOrder: 'stroke fill'}}>{doc.ep.hook?.ask ?? doc.ep.ask}</div>
  </AbsoluteFill>;
};

