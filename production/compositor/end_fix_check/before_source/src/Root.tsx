import React from 'react';
import { Composition, Still, staticFile } from 'remotion';
import { Episode2, RenderDoc } from './Episode2';
import { Thumbnail } from './Thumbnail';
import { Short, ShortDoc } from './Short';
import { Quiz, QuizDoc, QuizStyleProps } from './Quiz';
import { Cover, CoverShelf } from './Cover';
import { SafeAudit } from './SafeAudit';
import { HookAudit } from './HookAudit';
import { HookAudit51 } from './HookAudit51';
import { SetsProof } from './SetsProof';
import { ChannelBanner, ChannelBannerCrops, ChannelIcon, ChannelIconSizes } from './Channel';
import { PeepTest } from './PeepTest';
import { V4SpikeCompositions } from './v4spike/Compositions';
import { V4N18Compositions } from './v4/N18';
import { V4N18FullCompositions } from './v4/N18Full';

const fetchDoc = async (): Promise<RenderDoc> => {
  const r = await fetch(staticFile('ep001/render.json'));
  return r.json();
};

const fetchShort = async (): Promise<ShortDoc> => {
  const r = await fetch(staticFile('s001/render.json'));
  return r.json();
};

const ShortOrEmpty: React.FC<{ doc: ShortDoc | null }> = ({ doc }) => (doc ? <Short doc={doc} /> : null);

const QuizOrEmpty: React.FC<{ doc: QuizDoc | null } & QuizStyleProps> = ({ doc, ...style }) => (doc ? <Quiz doc={doc} {...style} /> : null);
const QUIZ_IDS = ['q001', 'q002', 'q003', 'q004', 'q005', 'q006', 'q007', 'q008', 'q009', 'q010', 'q011', 'q012', 'q013', 'q014', 'q015', 'q016', 'q017'];
const AuditOrEmpty: React.FC<{ doc: QuizDoc | null; label: string } & QuizStyleProps> = ({ doc, label, ...style }) => (doc ? <SafeAudit label={label}>{style.hookStyle === 'v51' ? <HookAudit51 doc={doc}><Quiz doc={doc} {...style} /></HookAudit51> : style.hookStyle === 'v5' ? <HookAudit doc={doc}><Quiz doc={doc} {...style} /></HookAudit> : <Quiz doc={doc} {...style} />}</SafeAudit> : null);
const CoverOrEmpty: React.FC<{ doc: QuizDoc | null }> = ({ doc }) => (doc ? <Cover doc={doc} /> : null);
const fetchQuiz = async (q: string, hookStyle?: 'v5' | 'v51'): Promise<QuizDoc> => (await fetch(staticFile(`${q}/${hookStyle === 'v51' ? 'v51/' : hookStyle === 'v5' ? 'v5/' : ''}render.json`))).json();

const EpisodeOrEmpty: React.FC<{ doc: RenderDoc | null }> = ({ doc }) => (doc ? <Episode2 doc={doc} /> : null);

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="EP001"
      component={EpisodeOrEmpty}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={14400}
      defaultProps={{ doc: null }}
      calculateMetadata={async () => {
        const doc = await fetchDoc();
        return { props: { doc }, durationInFrames: doc.durationInFrames };
      }}
    />
    <Composition
      id="S001"
      component={ShortOrEmpty}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={1200}
      defaultProps={{ doc: null }}
      calculateMetadata={async () => {
        const doc = await fetchShort();
        return { props: { doc }, durationInFrames: doc.durationInFrames };
      }}
    />
    {QUIZ_IDS.map((q) => (
      <Composition
        key={q}
        id={q.toUpperCase()}
        component={QuizOrEmpty}
        width={1080}
        height={1920}
        fps={30}
        durationInFrames={900}
        defaultProps={{ doc: null }}
        calculateMetadata={async ({props}) => {
          const r = await fetch(staticFile(`${q}/${props.hookStyle === 'v51' ? 'v51/' : props.hookStyle === 'v5' ? 'v5/' : ''}render.json`));
          const doc: QuizDoc = await r.json();
          return { props: { ...props, doc }, durationInFrames: doc.durationInFrames };
        }}
      />
    ))}
    {QUIZ_IDS.map((q) => (
      <Composition key={`a${q}`} id={`AUDIT-${q.toUpperCase()}`} component={AuditOrEmpty} width={1080} height={1920} fps={30} durationInFrames={900}
        defaultProps={{ doc: null, label: q }} calculateMetadata={async ({props}) => { const doc = await fetchQuiz(q, props.hookStyle); return { props: { ...props, doc, label: q }, durationInFrames: doc.durationInFrames }; }} />
    ))}
    {QUIZ_IDS.map((q) => (
      <Still key={`c${q}`} id={`COVER-${q.toUpperCase()}`} component={CoverOrEmpty} width={1080} height={1920} defaultProps={{ doc: null }}
        calculateMetadata={async () => ({ props: { doc: await fetchQuiz(q) } })} />
    ))}
    <Still id="COVER-SHELF" component={CoverShelf} width={1840} height={656} defaultProps={{ docs: [] as QuizDoc[] }}
      calculateMetadata={async () => ({ props: { docs: await Promise.all(QUIZ_IDS.map(q => fetchQuiz(q))) } })} />
    <Still id="SETS-PROOF" component={SetsProof} width={3000} height={4500} />
    <Still id="CH-ICON" component={ChannelIcon} width={800} height={800} />
    <Still id="CH-BANNER" component={ChannelBanner} width={2560} height={1440} />
    <Still id="CH-BANNER-CROPS" component={ChannelBannerCrops} width={1400} height={1060} />
    <Still id="CH-ICON-SIZES" component={ChannelIconSizes} width={1800} height={500} />
    <Still id="THUMB" component={Thumbnail} width={1280} height={720} />
    <Still id="PEEPTEST" component={PeepTest} width={1800} height={2040} />
    <V4SpikeCompositions />
    <V4N18Compositions />
    <V4N18FullCompositions />
  </>
);
