import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {FONT} from './theme';

const WHITE = '#EDEFF3', MUTED = '#929BAE', BLUE = '#466FA9', RED = '#A73A55';
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const fade = (f: number, at = 0) => interpolate(f, [at, at + 7], [0, 1], clamp);

// The v3 panel stays 1000×900. Text lives in x=94..814, clear of the mobile action rail.
const Ground: React.FC<{verdict?: boolean; paced?: boolean; children: React.ReactNode}> = ({verdict = false, paced = true, children}) => {
  const f = useCurrentFrame();
  // A restrained reframing every 1.2 s, with a 0.4 s ease and no spring or bounce.
  const beat = Math.floor(f / 36), t = Math.min(1, (f % 36) / 12), ease = t * t * (3 - 2 * t);
  const zoom = paced ? 1 + 0.03 * (beat % 2 ? 1 - ease : ease) : 1;
  return <AbsoluteFill style={{background: '#05070D', color: WHITE, fontFamily: FONT}}>
    <AbsoluteFill style={{background: verdict
      ? 'radial-gradient(ellipse at 4% 48%, #5E183951, transparent 65%), radial-gradient(ellipse at 94% 36%, #123C9D75, transparent 70%)'
      : 'radial-gradient(ellipse at 100% 10%, #16356163, transparent 72%)'}} />
    <svg width={1000} height={900} style={{position: 'absolute', inset: 0}} aria-hidden="true">
      {Array.from({length: 5}, (_, i) => <g key={i} opacity={0.32 - i * 0.035}
        transform={`translate(${500 - 500 * (1 + f * 0.0002)} ${450 - 450 * (1 + f * 0.0002)}) scale(${1 + f * 0.0002})`}>
        <path d={`M${24 + i * 46} 900 V${30 + i * 38} H${976 - i * 46} V900`} fill="none" stroke={verdict ? '#345FAD' : '#223147'} strokeWidth={2} />
        {verdict && <path d={`M${27 + i * 46} 870 V${36 + i * 38}`} fill="none" stroke={RED} strokeWidth={2} />}
      </g>)}
      <defs><pattern id="premium-grain" width={83} height={79} patternUnits="userSpaceOnUse" patternTransform={`translate(${f % 7} ${f % 11})`}>
        {Array.from({length: 36}, (_, i) => <rect key={i} x={(i * 31) % 83} y={(i * 23) % 79} width={1} height={1} fill="#FFFFFF" opacity={0.16 + (i % 3) * 0.06} />)}
      </pattern></defs>
      <rect width={1000} height={900} fill="url(#premium-grain)" opacity={0.22} />
    </svg>
    <AbsoluteFill style={{transform: `scale(${zoom})`, transformOrigin: '450px 450px'}}>{children}</AbsoluteFill>
    <AbsoluteFill style={{pointerEvents: 'none', background: 'radial-gradient(ellipse at 46% 42%, transparent 40%, #02040A70 100%)'}} />
  </AbsoluteFill>;
};

export const PremiumChoices: React.FC<{choices: string[]; duration: number}> = ({choices, duration}) => {
  const f = useCurrentFrame();
  return <Ground paced={false}>
    <div style={{position: 'absolute', left: 94, top: 94, fontSize: 32, fontWeight: 500, letterSpacing: '0.04em', color: MUTED}}>선고를 예상해 보세요</div>
    <div style={{position: 'absolute', inset: 0, transform: `scale(${1 + f / duration * 0.025})`, transformOrigin: '450px 430px'}}>
      {choices.map((choice, i) => <div key={choice} style={{position: 'absolute', left: 110, top: 192 + i * 158, width: 680, height: 128,
        border: '1px solid #68738770', background: '#080D16C9', display: 'flex', alignItems: 'center', gap: 38, paddingLeft: 32, boxSizing: 'border-box'}}>
        <span style={{fontSize: 27, fontWeight: 500, color: BLUE, letterSpacing: '0.12em'}}>{'ABC'[i]}</span>
        <span style={{fontSize: 65, fontWeight: 600, letterSpacing: '-0.035em'}}>{choice}</span>
      </div>)}
    </div>
  </Ground>;
};

type EvidenceCard = {text: string; tag: string};
export const PremiumEvidence: React.FC<{cards: EvidenceCard[]; at: number[]; duration: number}> = ({cards, at, duration}) => {
  const f = useCurrentFrame();
  const index = Math.max(0, at.reduce((last, t, i) => f >= t ? i : last, 0));
  const local = f - at[index], end = at[index + 1] ?? duration;
  const card = cards[index];
  return <Ground>
    <div style={{position: 'absolute', left: 94, top: 118, fontFamily: 'Noto Serif KR', fontSize: 56, fontWeight: 600}}>판사가 본 사정</div>
    <div style={{position: 'absolute', left: 94, top: 212, color: '#B8C2D4', fontSize: 28, letterSpacing: '0.08em'}}>{String(index + 1).padStart(2, '0')} / {String(cards.length).padStart(2, '0')} · {card.tag}</div>
    <div style={{position: 'absolute', left: 86, top: 292, width: 748, height: 340, boxSizing: 'border-box', background: '#101827E8', borderTop: '1px solid #69748B', borderBottom: '1px solid #353E50',
      boxShadow: '0 28px 80px #0009', opacity: fade(local), transform: `translateY(${(1 - fade(local)) * 8}px) scale(${1 + Math.max(0, local) / Math.max(1, end - at[index]) * 0.018})`, transformOrigin: '374px 170px'}}>
      <div style={{position: 'absolute', left: 28, top: 30, width: 34, height: 3, background: RED, transform: 'rotate(-22deg)'}} />
      <div style={{position: 'absolute', left: 24, right: 24, top: 0, height: '100%', display: 'flex', alignItems: 'center', fontFamily: 'Noto Serif KR', fontWeight: 700, fontSize: 84, lineHeight: 1, color: '#FAFAF7', letterSpacing: '-0.055em', whiteSpace: 'nowrap'}}>{card.text}</div>
      <div style={{position: 'absolute', left: 28, bottom: 28, height: 1, width: 90 * fade(local, 20), background: RED, opacity: 0.8}} />
    </div>
    <div style={{position: 'absolute', left: 94, top: 696, fontSize: 26, color: MUTED}}>재판부 판단 요지 · 보도 기반</div>
  </Ground>;
};

export const PremiumVerdict: React.FC<{lines: string[]; hit: number; duration: number; legal?: string; secondaryLegal?: {at: number; text: string}}> = ({lines, hit, duration, legal, secondaryLegal}) => {
  const f = useCurrentFrame();
  const second = secondaryLegal && f >= secondaryLegal.at;
  const legalAt = second ? secondaryLegal.at : hit + 34;
  return <Ground verdict>
    <div style={{position: 'absolute', left: 94, top: 94, fontSize: 31, fontWeight: 500, letterSpacing: '0.08em', color: MUTED}}>선고 · 항소심</div>
    {f >= hit && <div style={{position: 'absolute', left: 94, top: 238, width: 720, height: 382, boxSizing: 'border-box', border: '1px solid #77829A80',
      background: '#05070DEF', boxShadow: '-28px 0 90px #A51D4B21, 28px 0 90px #1653D03D', opacity: fade(f, hit),
      transform: `scale(${1 + (f - hit) / duration * 0.026})`, transformOrigin: '360px 190px'}}>
      {lines.map((line, i) => <div key={line} style={{position: 'absolute', left: 30, top: 34 + i * 164, height: 148, display: 'flex', alignItems: 'baseline', gap: 6, whiteSpace: 'nowrap'}}>
        {line.split(/(\d+)/).map((part, j) => <span key={j} style={{fontSize: /^\d+$/.test(part) ? 128 : 50, fontWeight: /^\d+$/.test(part) ? 700 : 600, letterSpacing: '-0.055em', color: WHITE}}>{part}</span>)}
      </div>)}
      <div style={{position: 'absolute', left: -1, top: 0, height: 62, width: 2, background: RED}} />
      <div style={{position: 'absolute', right: -1, bottom: 0, height: 62, width: 2, background: BLUE}} />
    </div>}
    {legal && f >= hit + 34 && <div style={{position: 'absolute', left: 94, top: 688, fontFamily: 'Noto Serif KR', fontSize: 34, fontWeight: 600, opacity: fade(f, legalAt)}}>{second ? secondaryLegal.text : legal}</div>}
    <div style={{position: 'absolute', left: 94, top: 788, width: 720 * fade(f, hit + 70), height: 1, background: '#8A93A644'}} />
  </Ground>;
};
