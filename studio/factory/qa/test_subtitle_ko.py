"""Owner-caught subtitle breaks must stay caught: .venv/bin/python factory/qa/test_subtitle_ko.py (or pytest)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from factory.qa.subtitle_ko import judge  # noqa: E402

BAD = [  # (line 1, line 2) — owner or audit caught these
    ('실제로 돈이 빠져나가기 시작한', '건, 10월 30일 새벽입니다.'),   # H23 owner 11-08, LF3 v7e 52 s
    ('방망이로 때렸다는', '증언은 아닙니다.'),                     # N18 audit r1 SRT #17
    ('관리 체제에 대한', '국민 신뢰를 해쳤다는 이유였어요.'),       # N18 audit r4 frame 7712
    ('그 컴퓨터에 계속 숨어', '있었다는 증거는 없어요.'),           # auxiliary verb split
    ('대부분이 약 20분', '안에 움직였죠.'),                        # positional noun start
    ('합쳐 약 28억5000만', '달러라고 밝혔습니다.'),                 # number | unit
]
GOOD = [
    ('한국 시각 10월 30일', '새벽 5시 5분,'),
    ('바이낸스 추정 약 63억 달러,', '국내 보도로 약 8조4000억원.'),
    ('그리고 이 해커들,', '지금 어떻게 됐을까요?'),
]


def test_bad_breaks_fail():
    for a, b in BAD:
        v = judge(a, b)
        assert v and v[0] == 'FAIL', (a, b, v)


def test_good_breaks_pass():
    for a, b in GOOD:
        v = judge(a, b)
        assert v is None or v[0] != 'FAIL', (a, b, v)


if __name__ == "__main__":
    test_bad_breaks_fail()
    test_good_breaks_pass()
    print("ok")
