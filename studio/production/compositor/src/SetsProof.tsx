// Proof sheet for the non-traffic sets (dev only).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { loadFonts } from './fonts';
import { BarStreetSet, CabinSet, DormSet, HallwaySet, MemorialSet, MoneySet, MotelSet, OfficeSet, OrchardSet, PhoneSet, Prop, RecorderSet, StoreSet, WildfireSet } from './components/sets';
import { Guy } from './components/rm';

loadFonts();
const CELLS: React.ReactNode[] = [
  <><OfficeSet /><Guy look="D" x={300} y={900} scale={0.8} expr="angry" pose="point" seed={1} /></>,
  <><HallwaySet /><Guy look="B" x={520} y={900} scale={0.8} expr="tired" pose="stand" seed={2} /></>,
  <><StoreSet /><Guy look="A" x={720} y={900} scale={0.8} expr="shock" pose="stand" seed={3} /></>,
  <MoneySet label="700억" at={-40} />,
  <PhoneSet lines={[{}, { me: true }, {}]} at={-40} />,
  <MemorialSet />,
  <><OfficeSet />{(['suit', 'hoodie', 'clerk', 'granny', 'doctor'] as const).map((l, i) => <Guy key={l} look={l} x={110 + i * 195} y={880} scale={0.55} expr={(['angry', 'smug', 'shock', 'tired', 'serious'] as const)[i]} pose="stand" seed={i} wobble={0} />)}</>,
  // #11–#14 (2026-10-26)
  <CabinSet leverAt={-40} handAt={-60} />,
  <OrchardSet smoke wind />,
  <WildfireSet />,
  <><DormSet /><Prop kind="delivery" x={520} y={880} scale={0.8} /></>,
  <><MotelSet /><Prop kind="phones" x={290} y={600} /></>,
  <BarStreetSet />,
  <RecorderSet />,
];
export const SetsProof: React.FC = () => (
  <AbsoluteFill style={{ background: '#F1F1F1', display: 'flex', flexWrap: 'wrap', gap: 0 }}>
    {CELLS.map((c, i) => (
      <div key={`cell${i}`} style={{ width: 1000, height: 900, position: 'relative', overflow: 'hidden', outline: '4px solid #fff' }}>{c}</div>
    ))}
  </AbsoluteFill>
);
