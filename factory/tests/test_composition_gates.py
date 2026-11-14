"""H15/H16 behavior regressions. Existing media are decoded only, never rendered."""
from pathlib import Path
import copy
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import cv2
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import composition_gates as cg
import review_gates as r
from gates import apply_cto_signoffs, finalize_review


class SubtitleNumbers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)
        self.c = r.Review(self.out/'video.mp4', self.out, 'longform', [], [], [], '', '')

    def test_korean_word_numerals_and_counters_fail(self):
        for text in ['십이사단', '제십이사단에서', '세 명', '한개', '두 번', '네 분이',
                     '이십 분', '삼십초', '이천이십사년', '오월', '이십삼일', '일억 원',
                     '삼조', '구십 퍼센트', '스물두 명', '여덟 마리', '마흔한 살']:
            with self.subTest(text=text):
                self.c.subtitles = [dict(text=text)]
                self.assertEqual(r.h16(self.c)['status'], 'FAIL')
        match = cg.word_numerals('십이사단')[0]
        self.assertEqual((match['numeral'], match['unit']), ('십이', '사단'))

    def test_required_negatives_and_ordinary_word_inflections_pass(self):
        for text in ['12사단', '3명', '20분', '8조4천억 원', '2024년 5월 23일',
                     '일단', '이상', '삼촌', '사실', '오늘', '구조', '한번에',
                     '오늘은 사실이다', '구조를 바꿨다', '세대가 다르다', '이명박',
                     '이번 사건은 사회의 문제다', '이런 이유로', '이달에 이곳으로']:
            with self.subTest(text=text):
                self.c.subtitles = [dict(text=text)]
                self.assertEqual(r.h16(self.c)['status'], 'PASS')

    def test_allowlist_is_word_scoped(self):
        self.assertTrue(cg.word_numerals('오늘 구조를 살펴본 세 명'))
        self.assertTrue(cg.word_numerals('한 번에'))
        self.assertTrue(cg.word_numerals('세 대가 있다'))

    def test_narration_and_general_script_prose_are_not_subtitles(self):
        self.c.subtitles = [dict(text='12사단')]
        self.c.narration = [dict(text='십이사단')]
        self.c.script = 'N001: 십이사단\n연출: 세 명이 서 있다\n자막: 12사단'
        self.assertEqual(r.h16(self.c)['status'], 'PASS')
        self.c.script += '\n자막: 십이사단'
        self.assertEqual(r.h16(self.c)['status'], 'FAIL')

    def test_srt_timeline_and_script_table_are_scanned_and_bound(self):
        for name, text in [('subtitles.srt', '\ufeff1\n00:00:00,000 --> 00:00:01,000\n세\n명\n'),
                           ('timeline.json', json.dumps(dict(captions=[dict(text='이십 분')]), ensure_ascii=False)),
                           ('script.md', '| 시각 | narration | 자막 |\n|---|---|---|\n|0|세 명|십이사단|')]:
            with self.subTest(name=name):
                path = self.out/name
                path.write_text(text)
                self.c.config['subtitle_files'] = [str(path)]
                self.assertEqual(r.h16(self.c)['status'], 'FAIL')
                self.assertEqual(self.c.inputs[str(path.resolve())], r.digest(path))

    def test_adjacent_cues_split_numeral_and_counter(self):
        self.c.subtitles = [dict(text='세', start_s=0, end_s=1), dict(text='명', start_s=1, end_s=2)]
        self.assertEqual(r.h16(self.c)['status'], 'FAIL')
        self.c.subtitles[1]['start_s'] = 5
        self.assertEqual(r.h16(self.c)['status'], 'PASS')

    def test_ocr_backup_checks_subtitle_band_and_split_boxes(self):
        self.c.subtitles = [dict(text='12사단')]
        self.c.media['ocr'] = [dict(frame=1, boxes=[dict(text='세', x=.2, y=.8, h=.1),
                                                                 dict(text='명', x=.3, y=.8, h=.1)])]
        self.assertEqual(r.h16(self.c)['status'], 'FAIL')
        self.c.media['ocr'] = [dict(frame=1, boxes=[dict(text='세 명', x=.2, y=.2, h=.1)])]
        self.assertEqual(r.h16(self.c)['status'], 'PASS')

    def test_missing_subtitles_are_not_a_clean_pass(self):
        self.assertEqual(r.h16(self.c)['status'], 'INPUT_MISSING')

    def test_short_subtitle_frame_alias_is_normalized(self):
        self.assertEqual(r.sec(dict(from_=30, to=60), 'start', 30), 1)
        self.assertEqual(r.sec(dict(from_=30, to=60), 'end', 30), 2)

    def test_n18_real_subtitle_positive_control(self):
        script = r.ROOT/'production/lf_toon/v2/n18/script_v2.md'
        self.c.script = script.read_text()
        gate = r.h16(self.c)
        self.assertEqual(gate['status'], 'FAIL')
        self.assertTrue(any(h['text'] == '십이사단' for h in gate['evidence']['hits']))


class Composition(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)

    def image(self, color='navy', subtitle='white', prop=True):
        image = Image.new('RGB', (320, 180), color)
        draw = ImageDraw.Draw(image)
        draw.ellipse((35, 40, 70, 75), fill='tan', outline='black', width=2)
        draw.rectangle((40, 75, 65, 135), fill='orange', outline='black', width=2)
        if prop:
            draw.rectangle((190, 40, 260, 100), fill='red', outline='black', width=2)
        draw.rectangle((0, 126, 319, 179), fill=subtitle)
        return image

    def samples(self, entries):
        signatures = {name: cg.signature(self.image(color)) for name, color in [('A', 'navy'), ('B', 'green'), ('C', 'red')]}
        return [dict(start_s=a, end_s=b, signature=signatures[name]) for name, a, b in entries]

    def test_subtitle_area_has_no_effect_on_signature(self):
        self.assertEqual(cg.distance(cg.signature(self.image(subtitle='white')),
                                     cg.signature(self.image(subtitle='black'))), (0, 0))

    def test_color_layout_distinguishes_same_shape_different_set(self):
        a, b = cg.signature(self.image('navy')), cg.signature(self.image('green'))
        self.assertGreater(cg.distance(a, b)[1], cg.COLOR_LIMIT)
        moved = self.image()
        moved.paste(self.image().crop((190, 40, 260, 100)), (100, 40))
        self.assertGreater(cg.distance(a, cg.signature(moved))[1], cg.COLOR_LIMIT)

    def test_small_encode_noise_does_not_split_composition(self):
        image = self.image()
        array = np.array(image).astype(np.int16)
        rng = np.random.default_rng(1)
        noisy = Image.fromarray(np.clip(array+rng.integers(-2, 3, array.shape), 0, 255).astype(np.uint8))
        h, color = cg.distance(cg.signature(image), cg.signature(noisy))
        self.assertLessEqual(h, cg.HASH_LIMIT)
        self.assertLessEqual(color, cg.COLOR_LIMIT)

    def test_continuous_hold_is_one_segment_even_over_sixty_seconds(self):
        clusters = cg.cluster_samples(self.samples([('A', i, i+1) for i in range(120)]))
        self.assertEqual(clusters[0]['segment_count'], 1)
        self.assertFalse(clusters[0]['fail'])

    def test_recurrence_uses_film_time_after_a_break(self):
        for gap, expected in [(59.9, True), (60, True), (60.1, False)]:
            with self.subTest(gap=gap):
                samples = self.samples([('A', 0, 2), ('B', 2, 2+gap), ('A', 2+gap, 4+gap)])
                self.assertEqual(cg.cluster_samples(samples)[0]['fail'], expected)

    def test_four_separate_segments_fail_even_if_far_apart(self):
        entries = [('A', 0, 1), ('B', 1, 100), ('A', 100, 101), ('B', 101, 200),
                   ('A', 200, 201), ('B', 201, 300), ('A', 300, 301)]
        cluster = cg.cluster_samples(self.samples(entries))[0]
        self.assertEqual(cluster['segment_count'], 4)
        self.assertFalse(cluster['recurrences_within_60s'])
        self.assertTrue(cluster['fail'])
        self.assertFalse(cg.cluster_samples(self.samples(entries[:-2]))[0]['fail'])

    def test_presenter_candidate_requires_figure_prop_and_low_motion(self):
        frames = []
        for i in range(3):
            path = self.out/f'{i}.png'
            self.image().save(path)
            frames.append(path)
        # Isolate the geometry/motion heuristic from silhouette model recall.
        box = dict(x=.10, y=.20, w=.15, h=.50)
        with patch('figure_shapes.silhouettes', return_value=[box, dict(x=.12, y=.21, w=.10, h=.40)]):
            candidate = cg.presenter_regions(frames)
            self.assertIsNotNone(candidate)
            self.assertEqual(candidate['status'], 'NEEDS_REVIEW')
            self.image(prop=False).save(frames[0])
            self.image(prop=False).save(frames[1])
            self.image(prop=False).save(frames[2])
            self.assertIsNone(cg.presenter_regions(frames))
            self.image().save(frames[1])
            self.assertIsNone(cg.presenter_regions(frames))

    def test_camera_motion_does_not_hide_static_presenter(self):
        frames = []
        for i, shift in enumerate([-3, 0, 3]):
            array = cv2.warpAffine(np.array(self.image()), np.float32([[1, 0, shift], [0, 1, 0]]), (320, 180), borderMode=cv2.BORDER_REFLECT)
            path = self.out/f'camera_{i}.png'
            Image.fromarray(array).save(path)
            frames.append(path)
        with patch('figure_shapes.silhouettes', return_value=[dict(x=.1, y=.2, w=.15, h=.5)]):
            candidate = cg.presenter_regions(frames)
        self.assertIsNotNone(candidate)
        self.assertTrue(all(candidate['camera_transforms']))

    def test_gate_builds_overview_and_automatic_fail_is_not_signable(self):
        video = self.out/'video.mp4'; video.write_bytes(b'input')
        c = r.Review(video, self.out, 'longform', [], [], [], '', '')
        c.duration=21; c.fps=30; c.frames=630; c.width=320; c.height=180
        frame = self.out/'frame.png'; self.image().save(frame)
        c.frame = lambda t: frame
        evidence = dict(samples=[], clusters=[], presenter_candidates=[], repetition_fail=False, complete=True)
        with patch.object(cg, 'composition_evidence', return_value=copy.deepcopy(evidence)):
            gate = r.h15(c)
            self.assertEqual(gate['status'], 'NEEDS_REVIEW')
            self.assertEqual(gate['evidence']['overview_interval_s'], 10)
            self.assertTrue(gate['evidence']['overview_pages'])
            self.assertTrue(c.artifacts)
        evidence['repetition_fail'] = True
        with patch.object(cg, 'composition_evidence', return_value=evidence):
            gate = r.h15(c)
        apply_cto_signoffs({'H15': gate}, 'digest', {'H15': dict(role='CTO', name='test', reason='reviewed', input_sha256='digest')})
        self.assertEqual(gate['status'], 'FAIL')

    def test_new_gates_cannot_be_demoted_by_calibration(self):
        gates = {name: r.result(False, {}) for name in ['H15', 'H16', 'B6', 'E4']}
        with patch.object(r, 'read_json', return_value=dict(false_fail_counts={name: 5 for name in gates})):
            r.apply_calibration(gates)
        self.assertTrue(all(not gate['advisory'] for gate in gates.values()))

    def test_gate_registration_and_signoff_invalidate_on_evidence_change(self):
        self.assertTrue({'H15', 'H16'} <= r.ITEMS.keys())
        self.assertIn('H15', r.SIGNED)
        video = self.out/'video.mp4'; video.write_bytes(b'input')
        c = r.Review(video, self.out, 'shorts', [], [], [], '', '')
        proof = self.out/'overview.jpg'; proof.write_bytes(b'overview')
        c.artifacts[str(proof)] = r.digest(proof)
        baseline = {name: r.pending({}) if name in r.SIGNED else r.result(True, {}) for name in r.ITEMS}
        first = finalize_review(c, copy.deepcopy(baseline))
        prior = dict(cto_signoffs={name: dict(role='CTO', name='test', reason='reviewed overview', input_sha256=first['input_sha256']) for name in r.SIGNED})
        self.assertTrue(finalize_review(c, copy.deepcopy(baseline), prior)['ready'])
        proof.write_bytes(b'changed overview')
        after = finalize_review(c, copy.deepcopy(baseline), prior)
        self.assertFalse(after['ready'])
        self.assertEqual(after['gates']['H15']['status'], 'NEEDS_REVIEW')


class MediaControls(unittest.TestCase):
    def test_existing_positive_and_negative_composition_controls(self):
        controls = [
            ('production/lf_toon/v2/n18/n18_v2_1080p.mp4', 'production/lf_toon/v2/n18/shots_v2.json', True),
            ('production/lf_toon/v2/lf2/lf2_v2_1080p.mp4', 'production/lf_toon/v2/lf2/shots_v2.json', True),
            ('episodes/review_full/lf3_binance/lf3_binance_animatic_360p.mp4', 'production/lf_toon/lf3_binance/shots.json', True),
            ('upload/v52_q013_n16_v3.mp4', None, False),
        ]
        for video, shots, expected_fail in controls:
            with self.subTest(video=video):
                path = r.ROOT/video
                if not path.exists() or shots and not (r.ROOT/shots).exists():
                    self.skipTest('Local control media unavailable: '+video)
                capture = cv2.VideoCapture(str(path))
                try:
                    self.assertTrue(capture.isOpened())
                    fps = capture.get(cv2.CAP_PROP_FPS)
                    duration = capture.get(cv2.CAP_PROP_FRAME_COUNT)/fps
                    if shots:
                        obj = json.loads((r.ROOT/shots).read_text())
                        spans = [(r.sec(s, 'start', fps), r.sec(s, 'end', fps)) for s in obj['shots']]
                    else:
                        spans = [(float(i), min(i+1., duration)) for i in range(int(np.ceil(duration)))]
                    samples = []
                    for start, end in spans:
                        capture.set(cv2.CAP_PROP_POS_FRAMES, round((start+end)/2*fps))
                        ok, frame = capture.read()
                        self.assertTrue(ok)
                        image = Image.fromarray(cv2.cvtColor(cv2.resize(frame, (640, round(frame.shape[0]*640/frame.shape[1]))), cv2.COLOR_BGR2RGB))
                        samples.append(dict(start_s=start, end_s=end, signature=cg.signature(image)))
                    self.assertEqual(any(c['fail'] for c in cg.cluster_samples(samples)), expected_fail)
                finally:
                    capture.release()


if __name__ == '__main__':
    unittest.main()
