"""Shared-splitter wiring in the production prepare scripts; needs production/lf_toon (outside git)."""
from pathlib import Path
import unittest


class ProductionPrepareScripts(unittest.TestCase):
    def test_prepare_scripts_use_shared_splitter_with_legacy_escape(self):
        root=Path(__file__).resolve().parents[2]
        for f,call in [(root/'factory'/'prepare_v52.py','shorts_from_subtitles'),(root/'production/lf_toon/prepare_lf2_full.py','longform_from_sentences')]:
            src=f.read_text();self.assertIn(call,src);self.assertIn("CAPTION_SPLITTER','shared')!='legacy'",src)
        # prepare_v52 never writes into an existing output (packaged Shorts stay byte-identical).
        self.assertIn('mkdir(exist_ok=False)',(root/'factory'/'prepare_v52.py').read_text())


if __name__=='__main__':unittest.main()
