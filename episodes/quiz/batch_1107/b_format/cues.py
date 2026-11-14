"""cues.py <qid> -> upload/pkg/<qid>_B/cues.md : narration timeline (silencedetect onsets), shots, subtitle cues with line breaks."""
import sys, json
from pathlib import Path
D = Path(__file__).resolve().parent; W = D.parents[3]
q = sys.argv[1]; P = W / 'upload/pkg' / f'{q}_B'; c = json.loads((P / 'case.json').read_text()); a = json.loads((P / 'audio.json').read_text())
o = [f'# {q} B-format cues ({c["variant"]})', '', f'길이 {c["n"]}프레임 = {c["duration"]:.3f}s · 30fps · 음성 {a["engine"]} / {a["voice"]} · 전체 {a["overall_sps"]:.2f}음절/s', '',
     '시각은 합본 내레이션의 ffmpeg silencedetect(-38dB, 0.08s) 음성 시작. 컷은 음성 시작 1프레임 전.', '',
     '| 줄 | 샷(mode) | 컷 프레임 | 음성 시작–끝 s | 음절/s | 대사 (TTS) | 자막 |', '|---|---|---|---|---|---|---|']
for u in c['utterances']:
    o.append(f"| {u['id']} | {u['mode']} | {u['from_frame']} ({u['from_frame']/30:.2f}s), {u['dur']}f | {u['onset']:.3f}–{u['offset']:.3f} | {u['sps']:.2f} | {u['tts']} | {(u['shown'] or '(자막 없음: 화면 카드가 같은 문구)').replace(chr(10), ' / ')} |")
o += ['', '## 자막 큐 (72px/800/검정 10px, x540 중앙, ≤2줄·줄당 ≤14자)', '', '| # | 시작–끝 s | 1줄 | 2줄 | 줄 글자수 |', '|---|---|---|---|---|']
for i, s in enumerate(c['subtitles'], 1):
    ls = s['text'].split('\n') + ['']
    o.append(f"| {i} | {s['start_s']:.3f}–{s['end_s']:.3f} | {ls[0]} | {ls[1]} | {'/'.join(str(len(x)) for x in s['text'].split(chr(10)))} |")
if c.get('choice_frame') is not None:
    o += ['', f"선택지 카드: 등장 {c['choice_frame']+3}f부터 5f 간격, 낭독 강조 {', '.join(f'{x:.2f}s' for x in c['option_onsets'])}; 정답 {c['answer_frame']}f ({c['answer_frame']/30:.2f}s), 선택 시간 {(c['answer_frame']-c['choice_frame']-13)/30:.2f}s(세 카드 모두 보인 뒤).",
          f"의견 질문 화면 문구(고정 댓글과 동일): {c['opinion'].replace(chr(10), ' ')} · {c['opinion_frame']}f ({c['opinion_frame']/30:.2f}s)부터 {c['utterances'][-1]['from_frame']/30:.2f}s까지."]
else:
    o += ['', '결과 선공개 포맷: 퀴즈·의견 카드 없음, 판결 공개 후 첫 프레임으로 루프.']
(P / 'cues.md').write_text('\n'.join(o) + '\n'); print('\n'.join(o))
