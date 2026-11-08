import React from 'react';
import {registerRoot, AbsoluteFill, Audio, Composition, Still, staticFile, useCurrentFrame} from 'remotion';
import {Quiz, QuizDoc} from './QuizPanels';
import {HookV52} from '../v52_candidates/HookRevised';
import {Cover} from '../Cover';
import {SafeAudit} from '../SafeAudit';
import {HookAudit51} from '../HookAudit51';
import {ZoomAudit} from '../v52/ZoomAudit';
import data from '../../../../episodes/quiz/q013/v52_n16/render_n16.json';
const doc = data as unknown as QuizDoc;
// Series number is text; asset identity and lighting animation retain original q013 seed.
const heroDoc = {...doc, ep: {...doc.ep, no: 13}};
const V52 = () => useCurrentFrame() <= 60 ? <AbsoluteFill><HookV52 doc={heroDoc}/>{doc.audio && <Audio src={staticFile(doc.audio)}/>}</AbsoluteFill> : <Quiz doc={doc} hookStyle="v51"/>;
const Audit = () => <SafeAudit label="q013"><HookAudit51 doc={doc}><ZoomAudit><V52/></ZoomAudit></HookAudit51></SafeAudit>;
registerRoot(() => <><Composition id="V52-Q013-N16" component={V52} width={1080} height={1920} fps={30} durationInFrames={doc.durationInFrames}/><Composition id="AUDIT-Q013-N16" component={Audit} width={1080} height={1920} fps={30} durationInFrames={doc.durationInFrames}/><Still id="COVER-Q013-N16" component={() => <Cover doc={doc}/>} width={1080} height={1920}/></>);
