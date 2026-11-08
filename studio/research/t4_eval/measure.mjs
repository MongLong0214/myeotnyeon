// T4 measurement per prereg.md. usage: node measure.mjs <repo checkout> <out.json>
// Labels never reach the scorer; the repo's own harness is run separately on a labelled copy.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [repo, out] = process.argv.slice(2);
const here = new URL('.', import.meta.url);
const read = name => JSON.parse(readFileSync(new URL(name, here), 'utf8'));
const digest = name => 'sha256:' + createHash('sha256').update(readFileSync(new URL(name, here))).digest('hex');
const { rankClusters } = await import(pathToFileURL(join(repo, 'factory/score/index.js')));
const { assertLabelledRanking } = await import(pathToFileURL(join(repo, 'factory/score/evaluate-ranking.js')));
const labels = new Map(read('labels.json').map(label => [label.id, label.used]));
const keyMap = read('key_map.json');

async function measure(file) {
  const clusters = read(file);
  const { ranked, rejected, held } = await rankClusters(clusters, { expectationGap: async () => null });
  const used = [...labels].filter(([, isUsed]) => isUsed).map(([id]) => id);
  const cases = used.map(id => {
    const row = ranked.find(result => result.id === id);
    if (!row) return { id, case: keyMap[id], inTop7: false, status: held.some(r => r.id === id) ? 'held' : 'rejected',
      reasons: [...held, ...rejected].find(r => r.id === id)?.reasons ?? [] };
    const atLeast = ranked.filter(other => other.id !== id && other.score >= row.score).length;
    return { id, case: keyMap[id], inTop7: atLeast < 7, score: row.score, othersScoringAtLeast: atLeast };
  });
  const repoHarness = await (async () => {
    const dir = mkdtempSync(join(tmpdir(), 't4-'));
    const fixture = join(dir, 'eval.json');
    writeFileSync(fixture, JSON.stringify({ clusters: clusters.map(c => ({ ...c, used: labels.get(c.id) })) }));
    try { await assertLabelledRanking(fixture); return { pass: true }; } catch (error) { return { pass: false, message: error.message }; }
  })();
  return {
    file, digest: digest(file), verdict: cases.every(c => c.inTop7) ? 'PASS' : 'FAIL', usedCases: cases, repoHarness,
    ranking: ranked.map((r, i) => ({ position: i + 1, id: r.id, case: keyMap[r.id], used: labels.get(r.id), score: r.score })),
    held: held.map(r => ({ id: r.id, case: keyMap[r.id], used: labels.get(r.id), reasons: r.reasons })),
    rejected: rejected.map(r => ({ id: r.id, case: keyMap[r.id], used: labels.get(r.id), reasons: r.reasons })),
  };
}

const result = {
  measuredAt: new Date().toISOString(),
  candidate: execFileSync('git', ['-C', repo, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
  manifest: digest('manifest.json'), prereg: digest('prereg.md'),
  primary: await measure('clusters.json'),
  sensitivitySymmetric: await measure('clusters_symmetric.json'),
};
writeFileSync(out, JSON.stringify(result, null, 1) + '\n');
console.log(JSON.stringify({ candidate: result.candidate, primary: result.primary.verdict,
  primaryRepoHarness: result.primary.repoHarness.pass, sensitivity: result.sensitivitySymmetric.verdict }));
