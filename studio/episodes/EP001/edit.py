#!/usr/bin/env python3
"""v2 light cut: picture + overlay edit decision list → compositor/public/ep001/render.json.

Cuts are anchored to narration sentences (timing.json), and keyword overlays to the moment
the word is spoken (approximated by its character position in the sentence). One idea per
screen, 1–4 words, courtroom only for the charge, the court's answers and the verdict.
Also writes edit_fx.json (cut / pop times) for the sound design.
"""
import json, pathlib, re, subprocess

HERE = pathlib.Path(__file__).parent
PUB = HERE.parents[1] / 'production' / 'compositor' / 'public'
PLATES = PUB / 'plates'
OUT = PUB / 'ep001'
FPS = 30
AMBER, TEAL, GREY, RED = '#E6B061', '#3FB6C0', '#8A9399', '#E4685A'

script = json.load(open(HERE / 'script.json'))
timing = json.load(open(HERE / 'timing.json'))
CUE = {c['cue_id']: c for c in script['cues']}
SENT = {i['id']: i for i in timing['items']}
TOTAL = script['duration_frames']


def CI(c): return CUE[c]['in_frame']
def CO(c): return CUE[c]['out_frame_exclusive']
def S(c, k): return SENT[f'{c}_{k}']['start']
def E(c, k): return SENT[f'{c}_{k}']['end']


def W(c, k, word, after=False):
    """Frame at which `word` is spoken inside sentence k (character-position estimate)."""
    it = SENT[f'{c}_{k}']
    text = it['text']
    i = text.index(word) + (len(word) if after else 0)
    w = lambda s: len(re.sub(r'\s', '', s))
    return it['start'] + round((it['end'] - it['start']) * w(text[:i]) / max(1, w(text)))


cuts, ovs = [], []


def cut(f, shot=None, at=0.0, zoom=(1.0, 1.05), pan=None, dim=0.0, blur=0, bg=None, rate=1.0):
    cuts.append(dict(f=f, shot=shot, at=at, zoom=list(zoom), pan=pan, dim=dim, blur=blur, bg=bg, rate=rate))


def ov(otype, f0, f1, **p):
    ovs.append(dict(type=otype, from_=f0, to=f1, p=p))


def big(f0, f1, lines, **kw):
    ov('big', f0, f1, lines=[dict(l) for l in lines], **kw)


# ---------------------------------------------------------------- A: cold open
cut(CI('Q01'), 'L01_aerial', zoom=(1.0, 1.08))
ov('dateline', CI('Q01') + 8, S('Q01', 2), lines=['2022. 7. 28. 새벽 3시 30분경', '대구 수성구의 한 주차장 · 재구성'])
cut(S('Q01', 2) - 2, 'L02_hood', zoom=(1.0, 1.06))
ov('corner', S('Q01', 2), CO('Q02'), kind='recon')
cut(S('Q02', 1), 'L03_beams', at=0.6, zoom=(1.02, 1.08))   # after the hands are up (the raise smears under 2-step interpolation)
cut(S('Q02', 2), 'L04_push', at=1.2, zoom=(1.0, 1.05))
cut(S('Q02', 3), 'L05_wheel', zoom=(1.05, 1.12))
big(S('Q02', 3) + 2, CO('Q02'), [dict(t='여러 번', c=AMBER, s=160)], y=360)
cut(S('Q03', 1) - 3, 'SH21', at=2.0, zoom=(1.05, 1.12), dim=0.45)
big(S('Q03', 1) + 6, S('Q03', 2), [dict(t='“진지한 반성 없음”', s=96)], tag='court', y=380)
cut(S('Q03', 2), bg='radial-gradient(ellipse at 50% 45%, #1d2a33 0%, #05080b 70%)')
big(W('Q03', 2, '집행유예'), S('Q03', 3), [dict(t='집행유예', c=AMBER, s=190)], y=380)
ov('flash', W('Q03', 2, '집행유예'), W('Q03', 2, '집행유예') + 6, color='#E6B061', len=6)
big(S('Q03', 3), CO('Q03'), [dict(t='왜?', s=230)], y=330)

# ---------------------------------------------------------------- B: ident + record
cut(CI('Q04'), 'SH04', zoom=(1.0, 1.0))
ov('ident', CI('Q04'), CO('Q04'))
cut(CI('Q05'))
big(CI('Q05') + 2, S('Q05', 2), [dict(t="‘역대급 판결’", s=140)], kicker='2023년 8월 · 커뮤니티 반응', y=300)
ov('counter', CI('Q05') + 2, S('Q05', 2), to=259028, label='한 게시글 조회수', note='보배드림 원글 · 확인일 2026. 10. 25.', y=620, at=16)
cut(S('Q05', 2), 'SH05', zoom=(1.0, 1.12))
ov('dateline', S('Q05', 2) + 4, CO('Q05'), lines=['대구지방법원 · 1심', '2023. 8. 16. 선고 · 2023고단202 특수상해'])
ov('corner', S('Q05', 2) + 4, CO('Q05'), kind='material', text='판결을 전한 보도로 재구성 · 판결문 원문 미확보')

# ---------------------------------------------------------------- C: who
cut(CI('Q06'), 'L04_push', at=0.0, zoom=(1.0, 1.04))
big(CI('Q06') + 4, S('Q06', 2), [dict(t='등장인물 2명', s=110)], y=150)
cut(S('Q06', 2), 'L08_driver', zoom=(1.0, 1.06))
big(S('Q06', 2) + 2, W('Q06', 2, '그리고'), [dict(t='A씨 · 운전자', s=86)], box=True, y=150)
cut(W('Q06', 2, '그리고'), 'L03_beams', at=1.5, zoom=(1.0, 1.05))
big(W('Q06', 2, '그리고') + 2, S('Q06', 3), [dict(t='B씨 · 막아선 사람', s=86)], box=True, y=150)
cut(S('Q06', 3), 'L01_aerial', at=2.5, dim=0.62)
big(S('Q06', 3) + 2, CO('Q06'), [dict(t='두 사람의 관계', s=72), dict(t='보도에 없음', s=110, c='#C9D1D6')], y=330, tag='unknown', box=True)

# ---------------------------------------------------------------- D: the night
ov('corner', CI('Q07'), CO('Q09'), kind='recon')
cut(CI('Q07'), 'L04_push', at=1.2, zoom=(1.0, 1.06))
cut(S('Q07', 2), 'L05_wheel', at=1.0, zoom=(1.08, 1.14))
big(S('Q07', 2) + 2, E('Q07', 2) + 6, [dict(t='여러 번', c=AMBER, s=160)], y=360)
cut(S('Q07', 3), 'L06_ground', zoom=(1.0, 1.05))
big(S('Q07', 3) + 4, CO('Q07'), [dict(t='넘어지는 순간은 보여주지 않습니다', s=38)], y=120, box=True)
cut(CI('Q08'), 'L07_reverse', zoom=(1.0, 1.05))
big(W('Q08', 1, '뒤로'), W('Q08', 1, '다시'), [dict(t='후진', s=110)], y=200)
big(W('Q08', 1, '다시'), W('Q08', 1, '한 번 더'), [dict(t='다시 전진', s=110)], y=200)
big(W('Q08', 1, '한 번 더'), CO('Q08'), [dict(t='한 번 더', c=AMBER, s=160)], y=330)
cut(CI('Q09'), 'L06_ground', at=1.5, zoom=(1.06, 1.16))
big(CI('Q09') + 4, CO('Q09'), [dict(t='약 34일 치료', c=AMBER, s=120), dict(t='어깨 관절 염좌·긴장', s=52)], y=70)
cut(CI('Q10'), 'L08_driver', at=1.5, zoom=(1.04, 1.1))
ov('corner', CI('Q10'), CO('Q10'), kind='defense')
cut(S('Q10', 2), 'L09_ghost', zoom=(1.0, 1.06))
ov('quote', S('Q10', 2), CO('Q10'), tag='defense', y=250, lines=[dict(t='부주의한 운전 탓', at=0), dict(t='B씨가 뛰어들었다', at=W('Q10', 2, 'B씨') - S('Q10', 2))])
cut(CI('Q11'), 'L04_push', at=3.0, dim=0.55)
ov('checks', CI('Q11'), S('Q11', 2), tag='defense', y=380, items=[dict(t='들이받은 건 인정', ok=True, at=6)])
cut(S('Q11', 2))
big(S('Q11', 2), CO('Q11'), [dict(t='쟁점은 두 가지', s=64, c=GREY, at=0), dict(t='① 일부러?', s=120, at=S('Q11', 3) - S('Q11', 2)),
                               dict(t='② 그래서 다쳤나?', s=120, at=W('Q11', 3, '그리고') - S('Q11', 2))], y=300)

# ---------------------------------------------------------------- E: the charge (+ rumour 1)
cut(CI('Q12'), 'SH13', at=6.0, zoom=(1.0, 1.06))
big(CI('Q12') + 4, S('Q12', 2), [dict(t='특수상해', s=170)], kicker='재판에 넘겨진 죄명', y=330)
cut(S('Q12', 2), 'L05_wheel', at=0.0, dim=0.4, zoom=(1.1, 1.16), rate=0.9)
big(S('Q12', 2) + 2, W('Q12', 2, '판례상'), [dict(t='위험한 물건 + 상해', s=110)], y=360, tag='law')
big(W('Q12', 2, '판례상'), CO('Q12'), [dict(t='자동차도', s=90), dict(t='위험한 물건', s=140, c=AMBER)], y=320, tag='law')
cut(CI('Q13'))
ov('numberline', CI('Q13'), CO('Q13'), rangeAt=4)
big(S('Q13', 2), CO('Q13'), [dict(t='벌금형 없음', s=80, c=RED)], y=170)
cut(CI('Q14'), 'L01_aerial', at=1.0, dim=0.65, blur=8)
ov('myth', CI('Q14'), CO('Q14'), rumor='음주운전 확정?', src='사건 보도 34건 검토 기준',
   facts=[dict(t='죄명은 특수상해 1개', at=S('Q14', 2) - CI('Q14')), dict(t='음주 측정 결과: 보도 없음', at=S('Q14', 3) - CI('Q14'))])

# ---------------------------------------------------------------- F: today's question
cut(CI('Q15'), 'L02_hood', at=1.0, dim=0.72, blur=4, rate=0.7)
ov('stamp', CI('Q15') + 4, S('Q15', 2), t='유죄', color=TEAL)
big(S('Q15', 2), CO('Q15'), [dict(t='오늘의 질문', s=60, c=GREY, at=0), dict(t='반성은 없다면서', s=96, at=S('Q15', 3) - S('Q15', 2)),
                               dict(t='왜 실형이 아니었을까?', s=110, c=AMBER, at=W('Q15', 3, '왜') - S('Q15', 2))], y=280)

# ---------------------------------------------------------------- G: evidence
cut(CI('Q16'))
big(CI('Q16') + 2, S('Q16', 2), [dict(t='유죄일까?', s=150)], y=360)
cut(S('Q16', 2), 'SH15', zoom=(1.0, 1.1))
big(S('Q16', 2) + 2, S('Q16', 3), [dict(t='현장 CCTV', s=140, c=AMBER)], y=360)
ov('corner', S('Q16', 3), CO('Q16'), kind='report', text='판결을 전한 보도 기준')
big(W('Q16', 3, '범행'), CO('Q16'), [dict(t='범행 장면 녹화', s=110)], y=400, box=True)
cut(CI('Q17'), 'L08_driver', at=0.5, dim=0.5, rate=0.7)
ov('quote', CI('Q17'), CO('Q17'), tag='defense', y=260, lines=[dict(t='들이받은 건 맞다', at=2), dict(t='다치지 않았다 · 그 때문이 아니다', at=W('Q17', 1, 'B씨가') - CI('Q17'))])
cut(CI('Q18'), 'SH17', zoom=(1.0, 1.08))
big(CI('Q18') + 4, S('Q18', 2), [dict(t='진료기록', s=150, c=AMBER)], y=360)
cut(S('Q18', 2), 'SH17', at=5.0, dim=0.55, zoom=(1.1, 1.14))
big(S('Q18', 2), CO('Q18'), [dict(t='다음 날 ~ 8월 말', s=96, at=0), dict(t='+ 이듬해 5월쯤까지', s=96, c=AMBER, at=W('Q18', 2, '그리고') - S('Q18', 2))],
    y=330, tag='report')

# ---------------------------------------------------------------- H: the court's answers
ov('corner', CI('Q19'), CO('Q21'), kind='courtSummary')
cut(CI('Q19'), 'SH14', at=3.0, zoom=(1.0, 1.08), dim=0.35)
ov('checks', CI('Q19'), S('Q19', 2), y=380, items=[dict(t='일부러 한 것', ok=True, at=W('Q19', 1, '일부러') - CI('Q19'))])
cut(S('Q19', 2), 'L09_ghost', at=1.0, dim=0.45)
ov('checks', S('Q19', 2), CO('Q19'), y=300, items=[dict(t='CCTV로 고의 인정', ok=True, at=4), dict(t='일부러 뛰어들었다', ok=False, at=W('Q19', 2, 'B씨가') - S('Q19', 2))])
cut(CI('Q20'), 'L05_wheel', at=1.5, dim=0.35)
ov('checks', CI('Q20'), S('Q20', 2), y=380, items=[dict(t='다친 것도 맞다', ok=True, at=W('Q20', 1, '다친') - CI('Q20'))])
cut(S('Q20', 2), 'SH17', at=8.0, dim=0.5)
big(S('Q20', 2), CO('Q20'), [dict(t='힘이 가볍지 않았다', s=90, at=0), dict(t='진료기록 ≈ B씨 진술', s=90, c=AMBER, at=W('Q20', 2, '진료기록') - S('Q20', 2))], y=330)
cut(CI('Q21'), 'SH13', at=20.0, dim=0.5, zoom=(1.08, 1.14))
ov('stamp', CI('Q21') + 3, CO('Q21'), t='유죄', color=TEAL, sub='특수상해')

# ---------------------------------------------------------------- I + J: the verdict
cut(CI('Q22'))
big(CI('Q22') + 2, S('Q22', 2), [dict(t='남은 건 형량', s=120)], y=380)
ov('split', S('Q22', 2), CO('Q22'), left='실형', right='집행유예', q='여러분이라면?', qAt=S('Q22', 3) - S('Q22', 2))
cut(CI('Q23'), 'SH21', zoom=(1.0, 1.12))
ov('shade', S('Q23', 1) + 6, CO('Q23'), a=0.5)
ov('verdict', S('Q23', 1) + 6, CO('Q23'), lines=[dict(text='징역 8개월', size=120), dict(text='집행유예 2년', size=120, color=AMBER), dict(text='사회봉사 120시간', size=70)],
   meta='대구지방법원 · 2023. 8. 16. 선고 · 1심')
cut(CI('Q24'), 'SH21', at=10.0, dim=0.72, blur=8)
ov('defer', CI('Q24'), CO('Q24'), voidAt=S('Q24', 2) - CI('Q24'))
cut(CI('Q25'), 'L13_outro', dim=0.5)
big(CI('Q25') + 2, CO('Q25'), [dict(t='1심 판결', s=110), dict(t='항소·확정 여부는 보도로 확인 안 됨', s=58, c=GREY)], y=340, tag='unknown')

# ---------------------------------------------------------------- K: why
scale_from = CI('Q26')
cut(CI('Q26'), 'L01_aerial', at=2.0, dim=0.72, blur=10, rate=0.5)
ov('scale', scale_from, CO('Q27'), leftLabel='불리한 사정', rightLabel='유리한 사정',
   left=[dict(t='남 탓 · 반성 없음', at=W('Q26', 2, '고의가') - scale_from), dict(t='짧은 시간에 여러 번', at=W('Q26', 2, '짧은') - scale_from),
         dict(t='피해자 엄벌 탄원', at=W('Q26', 2, '피해자가') - scale_from)],
   right=[dict(t='들이받은 행동은 인정', at=W('Q27', 1, '들이받은') - scale_from), dict(t='신고가 두려웠던 동기', at=W('Q27', 1, '신고가') - scale_from),
          dict(t='초범', at=W('Q27', 1, '초범') - scale_from)])
cut(CI('Q28'), 'L01_aerial', at=4.0, dim=0.72, blur=10, rate=0.5)
ov('myth', CI('Q28'), S('Q28', 2), rumor='“무서워했다니 봐줬다”?', src='온라인 반응 요약',
   facts=[dict(t='유리한 사정 3개 중 1개', at=W('Q28', 1, '그건') - CI('Q28'))])
big(S('Q28', 2), CO('Q28'), [dict(t='형법은 반성만 보지 않는다', s=84, at=0),
                               dict(t='동기 · 결과 · 범행 후 태도', s=84, c=AMBER, at=W('Q28', 2, '동기') - S('Q28', 2))], y=330, tag='law')
cut(CI('Q29'))
ov('numberline', CI('Q29'), CO('Q29'), rangeAt=0, markAt=W('Q29', 2, '8개월') - CI('Q29'), zoneAt=W('Q29', 4, '3년') - CI('Q29'))
big(S('Q29', 3), S('Q29', 4), [dict(t='감경', s=90, c=AMBER)], y=150, tag='analysis')
cut(CI('Q30'), 'L13_outro', at=2.0, dim=0.7, blur=8)
big(CI('Q30') + 2, S('Q30', 2), [dict(t='이례적인 판결?', s=130)], y=380)
ov('persons', S('Q30', 2), CO('Q30'), pct=7.49, big='74.9%', label='2023년 1심 특수상해 집행유예 비율', note='양형기준 적용 3,550명 중 2,659명 · 양형위원회 연간보고서')
cut(CI('Q31'))
ov('compare', CI('Q31'), CO('Q31'), tiles=[
    dict(title='이 사건', sub='신고하겠다며 막아선 사람을\n차로 밀어 넘어뜨림', tag='courtSummary', rows=[dict(k='형', v='징역 8개월 · 집유 2년', hl=True), dict(k='상해', v='약 34일 치료')]),
    dict(title='대구지법 · 2022년 보도', sub='신고 후 차를 가로막은 주민을\n후진해 침', tag='report', rows=[dict(k='형', v='징역 8개월 · 집유 2년', hl=True), dict(k='상해', v='전치 2주')])])

# ---------------------------------------------------------------- L: status, takeaway, end
cut(CI('Q32'), 'SH17', at=2.0, dim=0.6, blur=4, rate=0.5)
big(CI('Q32') + 2, S('Q32', 2), [dict(t='공탁 300만 원', s=130, c=AMBER, at=0), dict(t='피해자: 유리하게 보는 데 반대', s=64, at=W('Q32', 1, '피해자') - CI('Q32'))], y=330, tag='report')
big(S('Q32', 2), CO('Q32'), [dict(t='2024년 법 개정', s=110, at=0), dict(t='선고 직전 공탁 → 피해자 의견 청취 의무', s=58, c=AMBER, at=W('Q32', 2, '선고') - S('Q32', 2))], y=330, tag='law')
cut(CI('Q33'), 'L13_outro', at=3.0, dim=0.55)
big(CI('Q33') + 2, S('Q33', 2), [dict(t='반성 하나가 아니라', s=84, at=0), dict(t='여러 사정의 무게', s=130, c=AMBER, at=W('Q33', 1, '여러') - CI('Q33'))], y=330)
cut(S('Q33', 2))
ov('tip112', S('Q33', 2), CO('Q33'), chipsAt=W('Q33', 2, '위치') - S('Q33', 2))
cut(CI('Q34'), 'L13_outro', at=5.0, dim=0.3)
big(CI('Q34') + 2, CO('Q34'), [dict(t='판결의 이유', s=110, serif=True)], y=400)
cut(CI('Q35'))
ov('endscreen', CI('Q35'), CO('Q35'))


# ---------------------------------------------------------------- assemble
def nframes(shot):
    f = PLATES / f'{shot}.mp4'
    if not f.exists():
        return None
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-count_packets', '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', str(f)],
                       capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


def main():
    cuts.sort(key=lambda c: c['f'])
    segs, missing, warn, lens = [], set(), [], {}
    for a, b in zip(cuts, cuts[1:] + [dict(f=TOTAL)]):
        dur = b['f'] - a['f']
        if dur <= 0:
            warn.append(f"zero-length cut at {a['f']} ({a.get('shot')})"); continue
        s = dict(from_=a['f'], dur=dur, zoom=a['zoom'], dim=a['dim'], blur=a['blur'])
        if a.get('pan'):
            s['pan'] = a['pan']
        if a['shot']:
            n = lens.setdefault(a['shot'], nframes(a['shot']))
            st = round(a['at'] * FPS)
            s.update(src=f"plates/{a['shot']}.mp4", startFrom=st, label=a['shot'], rate=a['rate'])
            if n is None:
                s['ok'] = False; missing.add(a['shot'])
            elif st + dur * a['rate'] > n:
                warn.append(f"{a['shot']} needs frames {st}..{st + round(dur * a['rate'])} but plate has {n} (cut at {a['f']})")
        elif a.get('bg'):
            s['bg'] = a['bg']
        segs.append(s)
    overlays = [dict(type=o['type'], from_=o['from_'], dur=max(1, o['to'] - o['from_']), p=o['p']) for o in ovs]
    for o in overlays:
        if o['dur'] < 12:
            warn.append(f"short overlay {o['type']} {o['dur']}f at {o['from_']}")
    OUT.mkdir(parents=True, exist_ok=True)
    mix = HERE / 'audio' / 'mix_master.wav'
    doc = dict(fps=FPS, durationInFrames=TOTAL, hud_case=script['hud_case'],
               segments=[dict({k: v for k, v in s.items() if k != 'from_'}, **{'from': s['from_']}) for s in segs],
               overlays=[dict({k: v for k, v in o.items() if k != 'from_'}, **{'from': o['from_']}) for o in overlays],
               subtitles=[dict(from_=s['from_'], to=s['to'], text=s['text']) for s in timing['subtitles']],
               audio='ep001/mix_master.wav' if (OUT / 'mix_master.wav').exists() else None)
    json.dump(doc, open(OUT / 'render.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(dict(cuts=[s['from_'] for s in segs], pops=[o['from_'] for o in overlays if o['type'] in ('big', 'stamp', 'checks', 'myth', 'split', 'verdict', 'counter', 'persons', 'compare', 'tip112', 'quote', 'numberline', 'defer', 'scale')],
                   types={str(o['from_']): o['type'] for o in overlays}, verdict=CI('Q23'), total=TOTAL), open(HERE / 'edit_fx.json', 'w'), indent=1)
    shots = sorted({s['label'] for s in segs if s.get('label')})
    avg = TOTAL / len(segs) / FPS
    print(f'segments {len(segs)} (avg {avg:.2f} s) overlays {len(overlays)} total {TOTAL} f = {TOTAL / FPS:.1f} s')
    print('shots used', shots)
    print('missing plates', sorted(missing))
    for w in warn:
        print('WARN', w)
    if mix.exists():
        print('note: mix_master.wav is copied by render_final.sh after synth2')


if __name__ == '__main__':
    main()
