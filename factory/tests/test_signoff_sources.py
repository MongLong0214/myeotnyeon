"""Source binding regressions on a copied existing package; no render or network."""
import copy
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import gates
from short import W,load,save


class SignoffSources(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.package=self.root/'package'
        self.package.mkdir()
        original=W/'upload/pkg/q013_n16_v4'
        for name in ['recipe.json','qa.json','video.mp4','cover.jpg','meta.txt',
                     'render.json','episode.json','audio.json','timing.json','hero.png']:
            shutil.copyfile(original/name,self.package/name)
        self.cached=load(self.package/'qa.json')['gates']
        self.sources={src['file'] for claim in self.cached['facts']['evidence']['claims']
                      for src in claim['sources']}
        for name in [*self.sources,'episodes/quiz/q013/facts.md',
                     'episodes/quiz/v52_q013_q014_support/q013_fact_matrix.json']:
            target=self.root/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(W/name,target)
        save(self.package/'qa.json',dict(cto_signoffs={}))
        self.addCleanup(patch.stopall)
        patch('gates.W',self.root).start()

    def check(self):
        # Reuse the preserved QA measurements: only source bytes may change.
        return gates.finalize(self.package,copy.deepcopy(self.cached))

    def sign(self,digest):
        save(self.package/'qa.json',dict(cto_signoffs={
            name:dict(role='CTO',name='test CTO',reason='reviewed local snapshots',
                      input_sha256=digest) for name in ['facts','red_lines']}))

    def test_changed_snapshot_invalidates_signoff(self):
        before=self.check()
        self.sign(before['input_sha256'])
        signed=self.check()
        self.assertEqual(signed['gates']['facts']['review_state'],'CTO_SIGNED')
        self.assertTrue(signed['ready'])
        snapshot=self.root/sorted(self.sources)[0]
        data=snapshot.read_bytes()
        snapshot.write_bytes(bytes([data[0]^1])+data[1:])
        after=self.check()
        self.assertNotEqual(before['input_sha256'],after['input_sha256'])
        self.assertEqual(after['gates']['facts']['review_state'],'NEEDS_REVIEW')
        self.assertEqual(after['gates']['facts']['status'],'FAIL')
        self.assertNotIn('cto_signoff',after['gates']['facts'])
        self.assertFalse(after['ready'])

    def test_missing_snapshot_is_not_signable(self):
        name=sorted(self.sources)[0]
        missing='research/missing/'+Path(name).name
        matrix_path=self.root/'episodes/quiz/v52_q013_q014_support/q013_fact_matrix.json'
        matrix=load(matrix_path)
        for claim in matrix['claims']:
            for source in claim['sources']:
                if source['file']==name:source['file']=missing
        save(matrix_path,matrix)
        facts=gates.fact_gate(self.package,'q013')
        self.assertEqual(facts['status'],'FAIL')
        self.assertEqual(facts['review_state'],'DECIDED')
        self.assertEqual(facts['evidence']['reason'],
                         'missing source snapshot: '+Path(name).stem)
        self.cached['facts']=facts
        self.sign(self.check()['input_sha256'])
        after=self.check()
        self.assertEqual(after['gates']['facts']['status'],'FAIL')
        self.assertEqual(after['gates']['facts']['review_state'],'DECIDED')
        self.assertNotIn('cto_signoff',after['gates']['facts'])
        self.assertFalse(after['ready'])


if __name__=='__main__':unittest.main()
