import assert from 'node:assert/strict';
import {readFileSync, readdirSync} from 'node:fs';
import {test} from 'node:test';
import {getEndTransition} from '../src/endTransition.ts';
import type {QuizDoc, QuizStyleProps} from '../src/Quiz';

const read = (file: string): QuizDoc => JSON.parse(readFileSync(new URL(`../public/${file}`, import.meta.url), 'utf8'));
const check = (doc: QuizDoc, style?: QuizStyleProps['hookStyle']) => {
  const outro = doc.cues.find(c => c.scene === 'outro')!;
  const {ranges, fullEndFrom, cardReadyFrom} = getEndTransition(doc, style);
  for (let f = outro.from - 1; f < doc.durationInFrames; f++) {
    const fullEnd = fullEndFrom !== null && f >= fullEndFrom;
    const visible = fullEnd ? [] : ranges.filter(r => f >= r.from && f < r.end);
    assert.ok(fullEnd || visible.length > 0, `f${f}: uncovered panel`);
    assert.ok(!visible.some(r => r.cue.scene === 'outro') ||
      (fullEndFrom === null && f >= cardReadyFrom),
      `f${f}: legacy outro background precedes ready CTA f${cardReadyFrom}`);
  }
};
for (const q of readdirSync(new URL('../public/', import.meta.url)).filter(q => /^q\d{3}$/.test(q)).sort()) {
  test(`v3 ${q}: outgoing panel covers CTA pre-roll`, () => check(read(`${q}/render.json`)));
}
for (const q of ['q003', 'q012', 'q015', 'q016', 'q017']) {
  if (q === 'q003') continue;
  for (const version of ['v5', 'v51', 'v52']) {
    test(`${version} ${q}: no intermediate legacy outro`, () =>
      check(read(`${q}/${version}/render${version === 'v52' ? '_final' : ''}.json`), version === 'v5' ? 'v5' : 'v51'));
  }
}
test('already aligned full-screen transitions retain their display ranges', () => {
  for (const q of ['q012', 'q017']) {
    const doc = read(`${q}/v52/render_final.json`);
    const outro = doc.cues.at(-1)!;
    // Clean timing fixture; not evidence that an archived video was clean.
    doc.durationInFrames = outro.from + 45;
    outro.dur = 45;
    const t = getEndTransition(doc, 'v51');
    check(doc, 'v51');
    assert.deepEqual(t.ranges.filter(r => r.from < t.fullEndFrom!),
      doc.cues.filter(c => c.from < t.fullEndFrom!).map(c => ({cue: c, from: c.from, end: c.from + c.dur})));
  }
});
