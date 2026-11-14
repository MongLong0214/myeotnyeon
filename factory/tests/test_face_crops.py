"""post.face_crop_box: margin, clamp to frame, reject slivers.
  .venv/bin/python -m unittest factory.tests.test_face_crops"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from factory.shorts.post import face_crop_box  # noqa: E402


class FaceCropBox(unittest.TestCase):
    def test_margin_inside_frame(self):
        self.assertEqual(face_crop_box([100, 200, 300, 400], 1080, 1920, .1), (80, 180, 320, 420))

    def test_clamped_at_edges(self):
        self.assertEqual(face_crop_box([-39, 496, 585, 1128], 1080, 1920), (0, 382, 697, 1241))
        self.assertEqual(face_crop_box([1000, 1800, 1200, 2000], 1080, 1920, 0), (1000, 1800, 1080, 1920))

    def test_off_frame_box_rejected(self):
        self.assertIsNone(face_crop_box([1100, 100, 1300, 300], 1080, 1920, 0))


if __name__ == '__main__':
    unittest.main()
