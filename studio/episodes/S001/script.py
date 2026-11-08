#!/usr/bin/env python3
"""S001 — "역대급 판결" Shorts #1 (55 s vertical, webtoon 2D) → script_text.json.

Owner decisions 2026-10-26: channel "역대급 판결", free AI voice (Supertonic), webtoon-style 2D,
Shorts first, reuse the EP001 case. Structure: strongest scene first, the verdict withheld
until a viewer vote, then the reasons. Facts link to claim ids in ../EP001/ledger.py
(same case, same sources). No invented dialogue: speech bubbles carry only reported wording.
"""
import json, pathlib

HERE = pathlib.Path(__file__).parent

# id, scene, narration sentences, claim ids, pad (s)
CUES = [
    ('C1', 'hook', ['음주운전 신고하겠다고 차 앞을 막았더니,', '운전자가 그대로 차로 밀어 버렸습니다.'], ['F003', 'F004', 'F005'], 0.2),
    ('C2', 'again', ['한 번이 아니라 여러 번.', '밀려 넘어진 뒤에도, 차를 뒤로 뺐다가 다시 와서 한 번 더 들이받았어요.'], ['F004', 'F008'], 0.2),
    ('C3', 'injury', ['피해자는 약 34일 치료가 필요한 어깨 부상을 입었습니다.'], ['F009'], 0.2),
    ('C4', 'claim', ['그런데 운전자 측 주장은 이랬어요.', '부주의한 운전 탓이다, 저 사람이 뛰어든 거다.'], ['A001', 'F005'], 0.2),
    ('C5', 'court', ['하지만 현장 CCTV에 다 찍혀 있었고, 법원은 고의라고 봤어요.', '진지한 반성도 없다고 했죠.'], ['F010', 'E001', 'J001', 'J002'], 0.3),
    ('C6', 'vote', ['자, 여러분이 판사라면?', '실형일까요, 집행유예일까요?'], ['J003'], 1.2),
    ('C7', 'verdict', ['판결은, 징역 8개월에 집행유예 2년.'], ['J003', 'S001'], 0.8),
    ('C8', 'why', ['반성은 없었지만, 초범이었고, 들이받은 건 인정했고, 신고가 두려워 그랬다고 본 거예요.'], ['J005', 'J007'], 0.4),
    ('C9', 'ask', ['이 판결, 여러분 생각은 어때요?'], ['BRAND'], 2.0),
]


def main():
    out = [dict(cue_id=i, act=scene, block_name=scene, narration=na, claim_ids=cl, pad_s=pad, note='') for i, scene, na, cl, pad in CUES]
    json.dump(dict(episode_id='S001', version='shorts-1', hud_case='대구지방법원 2023고단202', cues=out),
              open(HERE / 'script_text.json', 'w'), ensure_ascii=False, indent=1)
    n = sum(len(''.join(c['narration']).replace(' ', '')) for c in out)
    print('cues', len(out), 'narration chars (no space)', n)


if __name__ == '__main__':
    main()
