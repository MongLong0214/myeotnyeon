"""Shared bake-off helpers: test lines, Korean number reading, trimming."""
import re, numpy as np
LINES = ["20분, 63억 달러. 어떻게 털렸을까요?",
         "보안팀이 이상을 잡아냅니다. 컴퓨터를 통째로 바꾸고, 로그인 정보도 바꿔요.",
         "그런데 책임자도, 인사 담당자도, 대표도, 전부 가짜였습니다."]
# same spoken form production uses (lf3_heist/synth.py spoken(): sino-Korean digits)
SPOKEN = ["이십분, 육십삼억 달러. 어떻게 털렸을까요?", LINES[1], LINES[2]]
def syl(t): return len(re.sub('[^가-힣]', '', t))
def trim(x, sr, db=-45):
    win = int(sr * .005); n = len(x) // win
    if n == 0: return x
    rms = np.sqrt(np.mean(x[:n*win].reshape(-1, win)**2, 1)); idx = np.where(rms > 10**(db/20))[0]
    if not len(idx): return x
    return x[max(0, (idx[0]-2)*win):min(len(x), (idx[-1]+4)*win)]
