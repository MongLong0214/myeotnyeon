"""Vertical (1080x1920 Shorts) geometry of the gate's box checks: a correctly placed subtitle must PASS, a clipped
one must FAIL. Before the fix the 640x360 landscape analysis frame put every Shorts subtitle "below the frame".
  .venv/bin/python -m pytest factory/qa/test_gate_vertical.py -q"""
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from factory.qa import gate  # noqa: E402


def make(info):
    a = SimpleNamespace(out=tempfile.mkdtemp(), lang='ko', sub_min_px=48, format='shorts', line_max=None)
    g = gate.Gate(a)
    g.info = info
    gate.set_analysis_size(info)
    g.ocr_sub = {}
    return g


def cue(i, s, e):
    return dict(idx=i, start=s, end=e, text='자막', lines=['자막'])


def test_analysis_size_keeps_aspect():
    assert gate.set_analysis_size(dict(w=1080, h=1920)) == (360, 640)
    assert gate.set_analysis_size(dict(w=1920, h=1080)) == (640, 360)
    assert gate.px1080(72, dict(w=1080, h=1920)) == 72
    assert gate.px1080(72, dict(w=1920, h=1080)) == 72


def test_vertical_subtitle_box_passes_and_clipped_fails():
    info = dict(w=1080, h=1920, fps=30, duration=2.0)
    g = make(info)
    d = SimpleNamespace(n=60, glyph_box=[None] * 60)
    # B3 subtitle: 72 px Korean line centred at x540, baseline ~y1560 (source pixels, OCR box)
    g.ocr_sub = {1: [[330, 1500, 750, 1580]], 2: [[-20, 1500, 1100, 1580]], 3: [[330, 1500, 750, 1520]]}
    g.subtitle_boxes(d, [cue(1, 0.0, 0.6), cue(2, 0.7, 1.3), cue(3, 1.4, 2.0)], None)
    it = next(i for i in g.items if i['check'] == 'subtitle_drawn_size_clip')
    bad = {f['cue']: f['why'] for f in it['findings']}
    assert 1 not in bad, bad                      # was 'outside title-safe' before the fix
    assert 'title-safe' in bad[2]                 # touches the frame edge
    assert 'line height' in bad[3]                # 20 px tall line < 48 px@1080
    assert it['status'] == 'FAIL'


def test_landscape_unchanged():
    info = dict(w=1920, h=1080, fps=30, duration=1.0)
    g = make(info)
    d = SimpleNamespace(n=30, glyph_box=[None] * 30)
    g.ocr_sub = {1: [[700, 900, 1220, 980]]}
    g.subtitle_boxes(d, [cue(1, 0.0, 0.9)], None)
    it = next(i for i in g.items if i['check'] == 'subtitle_drawn_size_clip')
    assert it['status'] == 'PASS', it


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
