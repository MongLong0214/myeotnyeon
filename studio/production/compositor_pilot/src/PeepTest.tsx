import React from 'react';
import { AbsoluteFill } from 'remotion';
import { Expr, Guy, Look, Pose } from './components/rm';

const cells: { look: Look; expr: Expr; pose: Pose; label: string }[] = [
  { look: 'B', expr: 'angry', pose: 'point', label: 'B angry point' },
  { look: 'B', expr: 'shock', pose: 'pushed', label: 'B shock pushed' },
  { look: 'B', expr: 'dizzy', pose: 'sit', label: 'B dizzy sit' },
  { look: 'B', expr: 'tired', pose: 'stand', label: 'B tired' },
  { look: 'A', expr: 'smug', pose: 'shrug', label: 'A smug shrug' },
  { look: 'A', expr: 'scared', pose: 'stand', label: 'A scared' },
  { look: 'judge', expr: 'serious', pose: 'stand', label: 'judge serious' },
  { look: 'judge', expr: 'angry', pose: 'point', label: 'judge angry' },
  { look: 'B', expr: 'talk', pose: 'stand', label: 'B talk' },
];
export const PeepTest: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: '#7FD1C7', display: 'flex', flexWrap: 'wrap' }}>
    {cells.map((c) => (
      <div key={c.label} style={{ width: 600, height: 680, position: 'relative', border: '2px solid #333', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', left: -200, top: -60, width: 1000, height: 900, transform: 'scale(0.75)', transformOrigin: '500px 450px' }}>
          <Guy look={c.look} x={500} y={820} scale={1} expr={c.expr} pose={c.pose} talk={c.expr === 'talk'} />
        </div>
        <div style={{ position: 'absolute', left: 8, top: 4, fontSize: 30, fontFamily: 'sans-serif', background: '#ff0' }}>{c.label}</div>
      </div>
    ))}
  </AbsoluteFill>
);
