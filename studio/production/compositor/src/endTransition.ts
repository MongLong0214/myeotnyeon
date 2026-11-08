import {spring} from 'remotion';
import type {QuizDoc, QuizStyleProps} from './Quiz';

// Cue frames are narration-local. Display ranges may retain the preceding panel
// while the outro is still transparent, or until a full-screen CTA takes over.
export const getEndTransition = (doc: QuizDoc, hookStyle?: QuizStyleProps['hookStyle']) => {
  const outro = doc.cues.find(c => c.scene === 'outro');
  const fullEndFrom = hookStyle ? doc.durationInFrames - 45 : null;
  let ready = 0;
  if (outro) {
    while (ready < outro.dur && spring({frame: ready - outro.a.s1, fps: doc.fps,
      config: {damping: 11, mass: 0.5, stiffness: 180}}) < 1) ready++;
  }
  const cardReadyFrom = fullEndFrom ?? (outro ? outro.from + ready : doc.durationInFrames);
  const outroIndex = doc.cues.indexOf(outro!);
  const ranges = doc.cues.map((c, i) => ({
    cue: c,
    // The incoming scene and outgoing panel share one handoff. Keep cue-local
    // animation/narration anchors unchanged; only their display lifetime changes.
    from: i === outroIndex ? cardReadyFrom : c.from,
    end: i === outroIndex - 1 ? cardReadyFrom : c.from + c.dur,
  }));
  return {fullEndFrom, cardReadyFrom, ranges};
};
