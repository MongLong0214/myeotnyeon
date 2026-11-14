import React from 'react';
import {AbsoluteFill, Audio, Composition, staticFile, useCurrentFrame} from 'remotion';
import {RemotionRoot} from '../Root';
import {Quiz, QuizDoc} from '../QuizCandidates';
import {SafeAudit} from '../SafeAudit';
import {HookAudit51} from '../HookAudit51';
import {HookV52} from './Hook';
import {ZoomAudit} from '../v52/ZoomAudit';

const IDS = ['q013', 'q014'];
const V52: React.FC<{doc: QuizDoc | null}> = ({doc}) => {
  const f = useCurrentFrame();
  if (!doc) return null;
  // All later scenes and the large end card use the unchanged v51 renderer.
  return f <= 60 ? <AbsoluteFill><HookV52 doc={doc} />{doc.audio && <Audio src={staticFile(doc.audio)} />}</AbsoluteFill> : <Quiz doc={doc} hookStyle="v51" />;
};
const Audit52: React.FC<{doc: QuizDoc | null; label: string}> = ({doc, label}) => doc ? <SafeAudit label={label}><HookAudit51 doc={doc}><ZoomAudit><V52 doc={doc} /></ZoomAudit></HookAudit51></SafeAudit> : null;
export const RootV52: React.FC = () => <>
  <RemotionRoot />
  {IDS.map(q => <React.Fragment key={q}>
    <Composition id={`V52-${q.toUpperCase()}`} component={V52} width={1080} height={1920} fps={30} durationInFrames={900} defaultProps={{doc: null}}
      calculateMetadata={async () => {const doc: QuizDoc = await (await fetch(staticFile(`${q}/v52/render_final.json`))).json();return {props: {doc}, durationInFrames: doc.durationInFrames};}} />
    <Composition id={`V52-AUDIT-${q.toUpperCase()}`} component={Audit52} width={1080} height={1920} fps={30} durationInFrames={900} defaultProps={{doc: null, label: q}}
      calculateMetadata={async () => {const doc: QuizDoc = await (await fetch(staticFile(`${q}/v52/render_final.json`))).json();return {props: {doc, label: q}, durationInFrames: doc.durationInFrames};}} />
  </React.Fragment>)}
</>;
