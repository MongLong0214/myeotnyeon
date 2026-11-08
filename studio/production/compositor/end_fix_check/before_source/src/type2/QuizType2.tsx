import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import type {QuizDoc} from '../Quiz';
import {RecordGrid, Texture, ink, red, white} from './Type';

// Live adapter for the reviewed Type 02 stills. All wording comes from the quiz
// data or the existing premium labels. Frame anchors and audio remain in Quiz.
const text: React.CSSProperties = {position: 'absolute', left: 120, color: white};
export const Type2Ground: React.FC = () => <><RecordGrid/><Texture/></>;
export const Type2Header: React.FC<{ep: QuizDoc['ep']; revealAt: number}> = ({ep, revealAt}) => {
  const f = useCurrentFrame(), head = ep.hook?.lines ?? ep.head;
  const ask = ep.hook?.ask ?? (ep.hook?.style === 'outcome' ? '' : '몇 년 나왔을까?');
  return <>
    <div style={{...text, top: 196, fontFamily: 'T2 Coding', fontSize: 28}}>몇년나옴? <span style={{marginLeft: 18}}>형량 퀴즈 #{ep.no}</span></div>
    <div style={{...text, top: 246, width: 840, fontFamily: 'T2 Head', fontSize: 81, lineHeight: 1.08, letterSpacing: '-.045em'}}>
      {head.map((line, i) => <div key={i} style={{color: i ? red : white}}>{line}</div>)}
    </div>
    <div style={{...text, top: 424, width: 840, fontFamily: 'T2 Song', fontSize: 34, lineHeight: 1.2}}>{f >= revealAt ? ep.answerHead : ask}</div>
    <div style={{position: 'absolute', left: 120, top: 474, width: 840, height: 2, background: '#66675f'}}/>
  </>;
};
export const Type2Caption: React.FC<{subs: QuizDoc['subtitles']}> = ({subs}) => {
  const f = useCurrentFrame(), sub = subs.find(s => f >= s.from_ && f < s.to);
  return sub ? <div data-type2-caption={sub.from_} style={{...text, top: 1352, width: 750, textAlign: 'left', fontFamily: 'T2 Sans', fontWeight: 600, fontSize: 57, lineHeight: 1.25, letterSpacing: '-.045em', whiteSpace: 'pre-line', color: '#f2f1e9', WebkitTextStroke: '1.5px #111', paintOrder: 'stroke fill', textShadow: '1px 2px 0 #111'}}>{sub.text}</div> : null;
};
export const Type2Source: React.FC<{source: string}> = ({source}) => <div style={{...text, top: 1506, width: 750, fontFamily: 'T2 Coding', fontSize: 23, lineHeight: 1.3, letterSpacing: '-.03em', color: '#b2b2a9'}}>{source}</div>;
export const Type2Choices: React.FC<{choices: string[]}> = ({choices}) => <>
  <div style={{...text, top: 507, fontFamily: 'T2 Song', fontSize: 40}}>선고를 예상해 보세요</div>
  <div style={{position: 'absolute', left: 116, top: 590, width: 830, height: 585, boxSizing: 'border-box', background: '#d5d0bf', transform: 'rotate(-1deg)', padding: '37px 24px', color: ink}}>
    {choices.map((choice, i) => <div key={choice} style={{height: 163, display: 'flex', alignItems: 'center', borderBottom: i < 2 ? '2px solid #696a60' : undefined}}>
      <span style={{fontFamily: 'T2 Coding', fontSize: 38, width: 115, paddingLeft: 12, color: red}}>{'ABC'[i]}</span>
      <span style={{fontFamily: 'T2 Head', fontSize: 85, lineHeight: 1, color: '#10120e'}}>{choice}</span>
    </div>)}<Texture paper/>
  </div>
</>;
type Card = {text: string; tag: string};
export const Type2Evidence: React.FC<{cards: Card[]; at: number[]}> = ({cards, at}) => {
  const f = useCurrentFrame(), index = Math.max(0, at.reduce((last, t, i) => f >= t ? i : last, 0)), card = cards[index];
  return <>
    <div style={{...text, top: 510, fontFamily: 'T2 Myeongjo', fontSize: 36}}>판사가 본 사정</div>
    <div style={{...text, top: 592, fontFamily: 'T2 Coding', fontSize: 28}}>{String(index + 1).padStart(2, '0')} / {String(cards.length).padStart(2, '0')} · <span style={{fontFamily: 'T2 Myeongjo', fontSize: 65, fontWeight: 800}}>{card.tag}</span></div>
    <div style={{...text, top: 784, width: 740, fontFamily: 'T2 Myeongjo', fontWeight: 400, fontSize: 67, lineHeight: 1.5, letterSpacing: '-.04em'}}>{card.text}</div>
    <div style={{position: 'absolute', left: 120, top: 998, width: 360, height: 4, background: '#dedccc'}}/>
    <div style={{...text, top: 1180, fontFamily: 'T2 Myeongjo', fontSize: 32}}>재판부 판단 요지 · 보도 기반</div>
  </>;
};
export const Type2Verdict: React.FC<{lines: string[]; hit: number; legal?: string; secondaryLegal?: {at: number; text: string}}> = ({lines, hit, legal, secondaryLegal}) => {
  const f = useCurrentFrame(), second = secondaryLegal && f >= secondaryLegal.at;
  return <>
    <div style={{...text, top: 505, fontFamily: 'T2 Coding', fontSize: 31}}>선고 · 항소심</div>
    {legal && f >= hit + 34 && <div style={{...text, top: 580, width: 740, fontFamily: 'T2 Myeongjo', fontSize: 42, lineHeight: 1.6}}>{second ? secondaryLegal.text : legal}</div>}
    {f >= hit && lines.map((line, i) => <div key={line} style={{...text, top: 717 + i * 193, fontFamily: 'T2 Head', fontSize: i ? 91 : 88, letterSpacing: '-.04em', color: i ? red : white, whiteSpace: 'nowrap'}}>
      {line.split(/(\d+)/).map((part, j) => <span key={j} style={{fontSize: /^\d+$/.test(part) ? 144 : undefined}}>{part}</span>)}
    </div>)}
  </>;
};
