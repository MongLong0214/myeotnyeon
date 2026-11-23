"""Regression coverage for class discovery, candidate activation, agreement and windowed metrics."""

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image
import improve
import improve_calibration
import improvement_log as log
import label_style
import promote
import improve_metrics


class ImprovementTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.classes = self.root / "defects.yaml"
        self.classes.write_text("[]\n")
        for module, name, value in [
            (log, "FACTORY", self.root),
            (log, "LOG", self.root / "findings.jsonl"),
            (improve, "REGISTRY", self.classes),
            (improve, "FIXTURES", self.root),
        ]:
            self.enterContext(patch.object(module, name, value))

    def test_new_fixture_and_recurrence(self):
        still = self.root / "f_0021.jpg"
        Image.new("RGB", (8, 8), "orange").save(still)

        def item(ep, ref):
            return log.finding(
                ep, "opus", "Orange seam on molar", "P1", "f21", ref, media=str(still)
            )

        first = item("jaw", "draft01")
        rows = [
            first,
            item("jaw", "draft02"),
            item("tooth", "draft01"),
            item("molar", "draft01"),
        ]
        log.append([*rows, first])
        self.assertEqual(len(log.records()), 4)
        registry = {}
        groups = improve.classify(rows, registry)
        key, entry = next(iter(registry.items()))
        improve.escalate({key: rows[:2]}, registry)
        self.assertEqual(entry["enforcement"], {"type": "unenforced"})
        self.assertNotIn("recurrence", entry)
        self.assertEqual(
            (self.root / entry["evidence"]["file"]).read_bytes(), still.read_bytes()
        )
        improve.escalate(groups, registry)
        self.assertEqual(entry["recurrence"]["episodes"], ["jaw", "tooth", "molar"])
        self.assertEqual(entry["recurrence"]["template_fix"], "required")

    def test_candidate_only_activates_after_every_comparison(self):
        # Exercise the real promotion decision using short stand-ins for expensive render and review calls.
        template = "neck_v3"
        style = {"note_transition": "fade_at_size"}
        defect = "label-pops-at-handoff"
        (self.root / "templates").symlink_to(log.KIT / "templates")
        self.classes.write_text(
            json.dumps(
                [
                    {
                        "id": defect,
                        "recurrence": {"template_fix": "required"},
                        "template_patch": {template: style},
                    }
                ]
            )
        )
        self.enterContext(patch.object(promote, "KIT", self.root))
        movie = self.root / "cut.mp4"
        movie.write_bytes(b"reviewed cut")
        candidate = self.root / "candidate.mp4"
        candidate.write_bytes(b"revised cut")
        refs = [(self.root, template, "cut", log.digest(movie), True)]
        self.enterContext(patch.object(promote, "references", return_value=refs))
        self.enterContext(
            patch.object(promote, "composite", return_value=(candidate, []))
        )
        self.enterContext(patch("builtins.print"))
        for i, passed in enumerate((False, True)):
            with patch.object(promote, "compare", return_value={"passed": passed}):
                self.assertEqual(
                    promote.promote(
                        template, None if passed else style, self.root / str(i), defect
                    ),
                    passed,
                )
            self.assertEqual("v2" in label_style.versions()[template], passed)
        self.assertEqual([r["status"] for r in log.records()], ["rejected", "promoted"])

    def test_anchor_and_agreement_use_only_matching_movie_bytes(self):
        import hashlib
        import subprocess

        folder = self.root / "new_episode"
        gates = folder / "gates"
        gates.mkdir(parents=True)
        movie = folder / "final.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=blue:s=32x64:d=0.5",
                movie,
            ],
            check=True,
        )
        sha = log.digest(movie)
        md5 = hashlib.md5(movie.read_bytes()).hexdigest()
        audit = dict(
            tag="final",
            movie_sha256=sha,
            status="reviewed",
            score=9,
            reviewed_at=10,
            **{"pass": False},
        )
        (gates / "final_fable_audit.json").write_text(json.dumps(audit))
        (gates / "final_review_fable.json").write_text(
            json.dumps(
                dict(_md5=md5, final=9, scores=dict(anatomy=9, motion=8.5, hook=8))
            )
        )
        (gates / "final_review_opus.json").write_text(
            json.dumps(dict(_md5=md5, final=6))
        )
        target = self.root / "finals.json"
        self.enterContext(patch.object(improve_calibration, "DYNAMIC", target))
        self.enterContext(patch.object(improve_calibration, "ARCHIVE", self.root))
        self.assertEqual(improve_calibration.update()[0], 1)
        self.assertEqual(improve_calibration.update()[0], 1)
        self.assertEqual(log.read(target)[0]["sha256"], sha)
        self.assertEqual(log.read(target)[0]["opus"], 6)
        (gates / "final_review_opus.json").write_text(
            json.dumps(dict(_md5="another-cut", final=10))
        )
        improve_calibration.update()
        self.assertIsNone(log.read(target)[0]["opus"])

    def test_missing_media_stays_unenforced(self):
        r = log.finding(
            "demo",
            "owner",
            "Torn cheek silhouette",
            "P1",
            "f21",
            "manual",
            media="absent.mp4",
        )
        rows = [r, dict(r, kind="directive", episode="untouched")]
        registry = {}
        groups = improve.classify(rows, registry)
        improve.escalate(groups, registry)
        entry = next(iter(registry.values()))
        self.assertNotIn("evidence", entry)
        self.assertNotIn("recurrence", entry)
        self.assertEqual(entry["enforcement"]["type"], "unenforced")

    def test_windowed_metrics_keep_studio_and_proxy_separate(self):
        row = dict(
            video_id="movie",
            start="2026-11-16",
            end="2026-11-17",
            views=1000,
            engagedViews=420,
            averageViewPercentage=78,
            subscribersGained=3,
            subscribersLost=1,
        )
        studio = self.root / "2026-11-18.json"
        observed = dict(video_id="movie", metric_period="lifetime", viewed_pct=69)
        studio.write_text(json.dumps({"videos": [observed]}))
        (self.root / "api_sample_anatomy_48h.json").write_text(
            json.dumps({"first_48h": [row]})
        )
        ledger = self.root / "ledger.json"
        video = dict(
            video_id="movie",
            channel="anatomy",
            state="published",
            qid="jaw",
            template_version="v1",
            template="wisdom",
            hook_type="jaw_touch",
        )
        ledger.write_text(json.dumps({"entries": [video]}))
        with patch.dict(
            os.environ, FACTORY_LEDGER=str(ledger), ANAT_ANALYTICS=str(self.root)
        ):
            (initial,) = improve_metrics.ingest()
            self.assertIsNone(initial["metrics"]["swipe_through_pct"])
            self.assertEqual(initial["metrics"]["subscriber_conversion_pct"], 0.2)
            observed.update(metric_period="first_48h", views=2000, subscribers_net=6)
            studio.write_text(json.dumps({"videos": [observed]}))
            (item,) = improve_metrics.ingest()
        self.assertEqual(initial["id"], item["id"])
        self.assertEqual(item["sources"]["subscriber_conversion_pct"], studio.name)
        self.assertEqual(
            item["metrics"],
            dict(
                avg_view_pct=78,
                subscriber_conversion_pct=0.3,
                engaged_share_pct=42,
                swipe_through_pct=69,
            ),
        )
        self.assertIn("jaw_touch", improve_metrics.experiment([item]))
        self.assertIn("69.0%", improve_metrics.experiment([item]))

    def test_capture_ignores_passing_stills_and_keeps_the_reviewed_frame(self):
        gates = self.root / "gates"
        stills = gates / "pf_stills"
        stills.mkdir(parents=True)
        frame = stills / "f_0021.jpg"
        Image.new("RGB", (8, 8), "orange").save(frame)
        (gates / "pf_stills_checks.json").write_text(json.dumps({"a": [True, {}]}))
        (gates / "pf_review_opus.json").write_text(
            json.dumps(
                {"stage": "stills", "p1": [{"frame": 21, "what": "Pill changed size"}]}
            )
        )
        log.capture_run(self.root, "pf")
        log.capture_run(self.root, "pf")
        (item,) = log.records()
        self.assertEqual(
            (item["source"], item["location"], item["media_sha256"]),
            ("opus", "f21", log.digest(frame)),
        )


if __name__ == "__main__":
    unittest.main()
