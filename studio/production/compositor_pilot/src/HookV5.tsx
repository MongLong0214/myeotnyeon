import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import type {QuizDoc} from './Quiz';
import {FONT} from './theme';
import {Paper} from './components/toon';
import {WildfireSet} from './components/sets';

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
// Break only at existing spaces. All headline glyphs come from the first hook line.
const headline = (doc: QuizDoc) => {
  const words = (doc.ep.hook?.lines ?? doc.ep.head)[0].split(' ');
  let split = 1, best = Infinity;
  for (let i = 1; i < words.length; i++) {
    const d = Math.abs(words.slice(0, i).join(' ').length - words.slice(i).join(' ').length);
    if (d < best) {best = d; split = i;}
  }
  return [words.slice(0, split).join(' '), words.slice(split).join(' ')];
};
const SeriesTag: React.FC<{no: number}> = ({no}) => <div data-v5-series style={{fontFamily: FONT, fontSize: 30, fontWeight: 700, color: '#E8EAF0', letterSpacing: '-0.02em'}}>몇년나옴? · 형량 퀴즈 #{no}</div>;

export const HookV5: React.FC<{doc: QuizDoc}> = ({doc}) => {
  const f = useCurrentFrame();
  const scene = doc.cues[0].p;
  const propLines: string[] = scene.stamps?.[0]?.lines ?? (scene.big ? [scene.big] : []);
  const zoom = interpolate(f, [0, 60], [1, 1.08], clamp);
  const slam = interpolate(f, [0, 2, 4], [0.94, 1.025, 1], clamp);
  return <AbsoluteFill data-v5-hook style={{background: scene.bigBg ?? scene.paper ?? '#DCE3E6'}}>
    {/* Enlarge the episode's existing set to cover the portrait: no letterbox or new incident imagery.
        Paper-only episodes keep their existing abstract paper art; wildfire keeps the existing empty landscape. */}
    <div data-v5-art style={{position: 'absolute', left: 540, top: scene.set === 'wildfire' ? 1200 : 960, width: 1000, height: 900, transform: `translate(-50%, -50%) scale(${1920 / 900 * zoom * (scene.set === 'wildfire' ? 1.5 : 1)})`}}>
      {scene.set === 'wildfire' ? <WildfireSet /> : <Paper color={scene.paper ?? scene.bigBg ?? '#DCE3E6'} />}
    </div>
    <AbsoluteFill style={{background: 'linear-gradient(180deg, #060A120D 0%, #060A1270 37%, #060A1299 70%, #060A124D 100%)', transform: `translateY(${-f * 2}px) scale(1.18)`}} />
    <div data-v5-headline style={{position: 'absolute', left: 130, width: 820, top: 430, fontFamily: FONT, fontSize: 136, WebkitTextStroke: '8px #101724', paintOrder: 'stroke fill', lineHeight: 1.25, fontWeight: 900, letterSpacing: '-0.055em', color: '#FFFDF6', textShadow: '0 5px 22px #0009', transform: `scale(${slam})`, transformOrigin: '50% 50%'}}>
      {headline(doc).map((line, i) => <div key={i} style={{whiteSpace: 'nowrap'}}>{line.split(/(\d+명|\d+|숨진|살인)/g).map((part, j) => <span key={j} style={{color: /^(\d+명|\d+|숨진|살인)$/.test(part) ? '#FF424A' : undefined}}>{part}</span>)}</div>)}
    </div>
    <div style={{position: 'absolute', left: 140, top: 1000, width: 720, fontFamily: FONT, fontSize: 64, WebkitTextStroke: '6px #101724', paintOrder: 'stroke fill', lineHeight: 1.2, fontWeight: 800, color: '#FFFDF6'}}>{doc.ep.hook?.ask || doc.ep.ask}</div>
    {propLines.length > 0 && <div data-v5-existing-prop style={{position: 'absolute', left: 140, top: 1150, width: 690, borderTop: '6px solid #FFFDF6', borderBottom: '6px solid #FFFDF6', padding: '18px 0', color: '#FFFDF6', fontFamily: FONT, fontWeight: 800, fontSize: 92, lineHeight: 1.2, letterSpacing: '-0.055em', textShadow: '0 3px 12px #000'}}>{propLines.join(' ')}</div>}
    {scene.set === 'wildfire' && <div data-v5-existing-prop style={{position: 'absolute', left: 140, top: 1150, width: 690, borderTop: '6px solid #FFFDF6', borderBottom: '6px solid #FFFDF6', padding: '16px 0', color: '#FFFDF6', fontFamily: FONT, fontWeight: 800, fontSize: 40, lineHeight: 1.5, letterSpacing: '-0.04em', textShadow: '0 3px 12px #000'}}>{(scene.tags ?? []).map((tag: {text: string}, i: number) => <div key={i}>{tag.text}</div>)}</div>}
    <div style={{position: 'absolute', left: 140, top: 1400, width: 720, fontFamily: FONT, fontSize: 34, fontWeight: 700, lineHeight: 1.25, color: '#FFFDF6', textShadow: '0 2px 8px #000'}}>{doc.ep.source}</div>
  </AbsoluteFill>;
};

export const EndV5: React.FC<{doc: QuizDoc}> = ({doc}) => {
  const f = useCurrentFrame() - (doc.durationInFrames - 45);
  const scale = interpolate(f, [0, 44], [1, 1.025], clamp);
  return <AbsoluteFill data-v5-cta style={{background: '#101724', color: '#FFFDF6', fontFamily: FONT}}>
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 45% 48%, #31425C 0%, #101724 75%)'}} />
    <div style={{position: 'absolute', left: 140, top: 490, width: 720, transform: `scale(${scale})`, transformOrigin: '50% 50%'}}>
      <div style={{fontSize: 68, fontWeight: 900, lineHeight: 1.3, letterSpacing: '-0.045em'}}>다음 판결도 맞혀보세요</div>
      <div style={{marginTop: 64, width: 320, height: 118, borderRadius: 24, background: '#E9313C', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 24, boxShadow: '0 12px 36px #0006'}}>
        <svg width={40} height={44} viewBox="0 0 40 44" aria-hidden="true"><path d="M5 3 L36 22 L5 41 Z" fill="#FFFDF6" /></svg>
        <span style={{fontSize: 66, fontWeight: 900}}>구독</span>
      </div>
      <div style={{marginTop: 64}}><SeriesTag no={doc.ep.no} /></div>
    </div>
  </AbsoluteFill>;
};
