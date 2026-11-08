import React from 'react';
import {AbsoluteFill, Composition} from 'remotion';
import {N18Art} from '../v4/N18Art';
import {ChapterCard, DateLine, DossierCard, EvidenceLabel, MeasurementLabel, SourceLine, Subtitle} from './Type';
import {ShortTypeReview} from './ShortType';
export const DocumentaryReview:React.FC<{kind:'chapter'|'scene'|'dossier'|'measurement'|'verdict'}>=({kind})=>{
 if(kind==='chapter')return <ChapterCard number="01" title="군기훈련"/>;
 if(kind==='dossier'||kind==='verdict')return <DossierCard verdict={kind==='verdict'}/>;
 return <AbsoluteFill className="type2-scene"><style>{`.type2-scene [stroke-dasharray="6 10"] {visibility:hidden}`}</style><N18Art kind={kind==='scene'?'opening':'spatial'}/><DateLine text="2024년 5월 23일."/>{kind==='scene'?<EvidenceLabel text="중대장" x={590} y={275}/>:<MeasurementLabel text="훈련병 6명"/>}<Subtitle text={kind==='scene'?'강원 인제의 신병교육대.':'규정을 위반한 군기훈련의 대상은 훈련병 6명이었습니다.'}/><SourceLine text="재구성 · 개념도 · 실제 배치·거리·축척 아님 / 문화일보·한겨레"/></AbsoluteFill>;
};
// Separate entrypoint, never imported by src/Root.tsx. Opt in explicitly for CTO review.
export const Type2ReviewRoot:React.FC=()=> <>
 {(['chapter','scene','dossier','measurement','verdict'] as const).map(kind=><Composition key={kind} id={`TYPE2-N18-${kind}`} component={DocumentaryReview} width={1920} height={1080} fps={30} durationInFrames={150} defaultProps={{kind}}/>)}
 {(['header','choices','reason','verdict'] as const).map(kind=><Composition key={kind} id={`TYPE2-Q006-${kind}`} component={ShortTypeReview} width={1080} height={1920} fps={30} durationInFrames={150} defaultProps={{kind}}/>)}
 </>;
