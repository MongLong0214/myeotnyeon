"""Regression checks for the source and template boundaries used by preflight."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

KIT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(KIT), str(KIT / "gates")]
from episode_template import initialize, read, validate
from clinical import claims, spoken_conditions
from checks import no_kg_on_screen
from thresholds import episode_gap
from final_audit import audit
from anchored_review import band_box
from solo import changed_windows


class TemplateTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name) / "neighbour"
        initialize(self.folder, "neck_v3")
        self.ep = read(self.folder / "episode.json")

    def test_narrated_conditions(self):
        self.assertEqual(spoken_conditions(self.ep), [])
        self.ep["narration"][1]["text"] = "숙이면 무게가 27킬로예요."
        self.assertTrue(spoken_conditions(self.ep))
        self.ep["narration"][2]["text"] = "목 각도가 달라요."
        self.ep["narration"][3]["text"] = "누구에게나 그래요."
        self.assertIn(
            "texting radiograph comparison lacks spoken population",
            spoken_conditions(self.ep),
        )

    def test_cervical_template_passes_the_owner_screen_rule(self):
        self.assertEqual(no_kg_on_screen(self.ep), (True, {"on_screen": []}))
        arrows = [l for l in self.ep["labels"] if l["kind"] == "arrow_load"]
        self.assertEqual([(l["anchor"], l["anchor2"]) for l in arrows], [("A_Head", "A_C7")])

    def test_unregistered_study_graphic_and_disclaimer_are_rejected(self):
        for field, value in [("kind", "angle_arc"), ("text", "컴퓨터 모델 추정")]:
            edited = copy.deepcopy(self.ep)
            edited["labels"][-1][field] = value
            with self.assertRaises(ValueError):
                validate(self.folder, edited)
        self.ep["claims"][-1]["condition"] = (
            "long-term follow-up of patients with neck pain"
        )
        with self.assertRaises(ValueError):
            validate(self.folder, self.ep)

    def test_every_spoken_line_has_its_beat_source(self):
        self.ep["narration"][2]["claim"] = "L"
        with self.assertRaises(ValueError):
            claims(self.ep)

    def test_empty_multi_segment_caption_is_rejected(self):
        self.ep["beats"][0]["cap"] = [[" ", [255, 255, 255]], ["", [200, 0, 0]]]
        with self.assertRaises(ValueError):
            validate(self.folder, self.ep)

    def test_published_source_must_match_the_registered_record(self):
        (self.folder / "SOURCES.md").write_text("| X | invented result |")
        with self.assertRaises(ValueError):
            validate(self.folder, self.ep)

    def test_v3_exception_cannot_travel_with_the_scene(self):
        (self.folder / "thresholds.json").write_bytes(
            (KIT / "templates/neck_v3/thresholds.json").read_bytes()
        )
        with self.assertRaises(ValueError):
            episode_gap(self.folder)


class RevisionTest(unittest.TestCase):
    def test_changed_label_uses_only_its_display_window(self):
        ep = read(KIT / "templates/wisdom/episode.json")
        edited = copy.deepcopy(ep)
        label = edited["labels"][-1]
        label["dx"] += 5
        self.assertEqual(changed_windows(ep, edited), [[label["f0"], label["f1"]]])

    def test_normalized_finding_uses_native_verification_pixels(self):
        self.assertEqual(band_box([0, 0, 1, 1], 470, 880), [0, 0, 1080, 880])
        self.assertEqual(
            band_box([0.25, 0.25, 0.75, 0.75], 470, 880), [270, 221, 810, 682]
        )
        with self.assertRaises(ValueError):
            band_box([0.8, 0, 0.2, 1], 470, 880)


class AuditTest(unittest.TestCase):
    def test_only_one_call_on_the_same_final(self):
        import hashlib

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            gates = folder / "gates"
            gates.mkdir()
            movie = folder / "final.mp4"
            movie.write_bytes(b"test media identity")
            sha = hashlib.sha256(movie.read_bytes()).hexdigest()
            (gates / "final_submission.json").write_text(
                json.dumps({"pass": True, "movie_sha256": sha})
            )
            (gates / "final_render.json").write_text('{"mode":"final-fast"}')

            def fake(*args, **kwargs):
                (gates / "final_review_fable.json").write_text(
                    json.dumps(
                        {
                            "final": 9,
                            "p0": [],
                            "pass": False,
                            "_md5": hashlib.md5(movie.read_bytes()).hexdigest(),
                        }
                    )
                )
                return mock.Mock(returncode=1)

            with mock.patch("improvement_log.LOG", folder/"findings.jsonl"), mock.patch("final_audit.subprocess.run", side_effect=fake) as call:
                first = audit(folder, "final")
                self.assertEqual(first["score"], 9)
                self.assertFalse(first["pass"])
                self.assertEqual(audit(folder, "final"), first)
                self.assertEqual(call.call_count, 1)


if __name__ == "__main__":
    unittest.main()
