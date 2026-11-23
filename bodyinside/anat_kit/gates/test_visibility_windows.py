import sys, os; sys.path.insert(0, os.path.dirname(__file__)); from checks import visibility_windows
def dump(n, vis): return {'arc': {str(f): (1.0 if f in vis else 0.0) for f in range(n)}}
def test_short_episode_924_frames_passes():
    ok, _ = visibility_windows(dump(924, range(10, 20)), {'arc': [(10, 19)]}); assert ok
def test_window_end_past_last_frame_is_tolerated():
    ok, _ = visibility_windows(dump(924, range(900, 924)), {'arc': [(900, 990)]}); assert ok
def test_visible_outside_window_still_fails_on_short_clip():
    ok, d = visibility_windows(dump(924, range(10, 30)), {'arc': [(10, 19)]}); assert not ok and d['visible_outside_window'][0][1] == 20
if __name__ == '__main__':
    for k, v in list(globals().items()):
        if k.startswith('test_'): v(); print('ok', k)
