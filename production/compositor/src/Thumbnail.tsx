import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { C, FONT } from './theme';
import { loadFonts } from './fonts';

loadFonts();

// One object (the car's lights and the person in front of it) + one contrast + a short question.
// v2 light cut: short hook in the video's own words ("반성 없는데 집행유예?"), no faces, no violence.
export const Thumbnail: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: '#05080b' }}>
    <Img src={staticFile('ep001/thumb_bg.png')} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
    <AbsoluteFill style={{ background: 'linear-gradient(90deg, rgba(3,6,9,0.92) 0%, rgba(3,6,9,0.75) 42%, rgba(3,6,9,0.0) 70%)' }} />
    <div style={{ position: 'absolute', left: 58, top: 110, width: 760 }}>
      <div style={{ fontFamily: FONT, fontSize: 38, fontWeight: 800, color: C.amberBright, marginBottom: 14 }}>음주운전 신고하겠다고 막았더니</div>
      <div style={{ fontFamily: FONT, fontSize: 118, fontWeight: 900, color: C.paper, lineHeight: 1.05, letterSpacing: '-0.04em', textShadow: '0 6px 24px rgba(0,0,0,0.8)' }}>
        반성 없는데<br /><span style={{ color: C.amberBright }}>집행유예?</span>
      </div>
      <div style={{ display: 'inline-block', fontFamily: FONT, fontSize: 34, fontWeight: 800, color: '#0b0f12', background: C.paper, borderRadius: 10, padding: '6px 18px', marginTop: 26 }}>법원 저울엔 뭐가 올라갔나</div>
    </div>
    <div style={{ position: 'absolute', left: 58, bottom: 40, fontFamily: FONT, fontSize: 24, color: 'rgba(243,241,233,0.65)' }}>판결의 이유 · 대구지법 2023고단202 · 기록 기반 재구성</div>
  </AbsoluteFill>
);
