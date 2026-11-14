#!/usr/bin/env python3
"""Generate cue_sheet.csv, narration.ko.md and episode.final.json (v1.0 contract) for EP001."""
import json, csv, pathlib, hashlib

HERE = pathlib.Path(__file__).parent
FPS = 30
script = json.load(open(HERE / 'script.json'))
timing = json.load(open(HERE / 'timing.json'))
ledger = json.load(open(HERE / 'ledger.json'))
render = json.load(open(HERE.parents[1] / 'production' / 'compositor' / 'public' / 'ep001' / 'render.json'))

def in_cue(c, items):
    return [x for x in items if c['in_frame'] <= x['from'] < c['out_frame_exclusive']]


def tc(f):
    s, fr = divmod(f, FPS)
    return f'{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}:{fr:02d}'


def main():
    na_by_cue = {}
    for it in timing['items']:
        na_by_cue.setdefault(it['cue'], []).append(it)
    with open(HERE / 'cue_sheet.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['cue_id', 'block', 'block_name', 'tc_in', 'tc_out_excl', 'in_frame', 'dur_frames', 'narration', 'na_in', 'na_out',
                    'shots', 'overlays', 'claim_ids'])
        for c in script['cues']:
            items = na_by_cue.get(c['cue_id'], [])
            shots = [f"{x.get('label', 'bg')}@{x.get('startFrom', 0)}" for x in in_cue(c, render['segments'])]
            ovs = [x['type'] for x in in_cue(c, render['overlays'])]
            w.writerow([c['cue_id'], c['act'], c['block_name'], tc(c['in_frame']), tc(c['out_frame_exclusive']), c['in_frame'], c['duration_frames'],
                        ' '.join(c['narration']) or '[NA 없음]', tc(items[0]['start']) if items else '', tc(items[-1]['end']) if items else '',
                        ' | '.join(shots), ' | '.join(ovs), ';'.join(c['claim_ids'])])
    # narration script
    lines = ['# EP001 내레이션 원고 (한국어, 낭독본)', '', 'v2 가벼운 편집본 · 음성: Supertonic 3 (M2, 속도 1.2) · 자막은 아래 문장과 같음. 숫자는 낭독용 한글 표기로 변환해 합성.', '']
    act = None
    for c in script['cues']:
        if c['act'] != act:
            act = c['act']; lines += ['', f"## {act} · {c['block_name']}", '']
        items = na_by_cue.get(c['cue_id'], [])
        if not items:
            lines.append(f"- **{c['cue_id']}** {tc(c['in_frame'])} · [NA 없음]")
            continue
        for it in items:
            lines.append(f"- **{c['cue_id']}** {tc(it['start'])}–{tc(it['end'])} · {it['text']}")
    (HERE / 'narration.ko.md').write_text('\n'.join(lines) + '\n')
    # episode.final.json per v1.0 template
    srcs = []
    for sid, (aid, t, u, d, ty, off, note) in ledger['sources'].items():
        fp = None
        for ext in ('pdf', 'html', 'txt'):
            q = HERE.parents[1] / 'research' / 'raw' / f'{aid}.{ext}'
            if q.exists():
                fp = q; break
        srcs.append(dict(source_id=sid, title=t, url=u, locator=f'archive:{aid}', verified_at='2026-10-25', official=off,
                         sha256=hashlib.sha256(fp.read_bytes()).hexdigest() if fp else ''))
    claims = []
    for cid, (ty, t, s_ids, loc, st) in ledger['claims'].items():
        typemap = {'court_finding': 'court_finding', 'party_claim': 'party_claim', 'fact': 'fact', 'analysis': 'analysis', 'unknown': 'unknown',
                   'law': 'fact', 'meta': 'fact', 'viral': 'fact', 'rumor': 'fact', 'comparable': 'fact', 'guide': 'fact'}
        claims.append(dict(claim_id=cid, type=typemap[ty], text=t, source_ids=s_ids, locator=loc, status=st,
                           reviewer='Claude (AI, 자동 대조) — 사람 검수 아님', reviewed_at='2026-10-25'))
    scenes = []
    for c in script['cues']:
        scenes.append(dict(cue_id=c['cue_id'], act=c['act'], block_name=c['block_name'], in_frame=c['in_frame'], duration_frames=c['duration_frames'],
                           out_frame_exclusive=c['out_frame_exclusive'], narration=' '.join(c['narration']) or '[NA 없음]',
                           shots=[x.get('label', 'bg') for x in in_cue(c, render['segments'])], overlays=[x['type'] for x in in_cue(c, render['overlays'])],
                           required_claim_ids=c['required_claim_ids'], claim_ids=c['claim_ids'], review_status='AI_CHECKED_NOT_HUMAN_VERIFIED'))
    doc = dict(schema_version='1.0.0', episode_id='EP001', status='PREVIEW_HOLD', story_mode='VERDICT_OPEN',
               format=dict(width=1920, height=1080, fps=30, duration_frames=script['duration_frames'], timecode='NDF', out_is_exclusive=True, cut='v2-light'),
               case=dict(title='음주운전 신고하겠다며 막아선 사람을 차로 친 사건의 1심 판결', country='대한민국', jurisdiction='대구지방법원',
                         court='대구지방법원 형사3단독', case_number='2023고단202', decision_date='2023-08-16', focus_stage='제1심',
                         decision_maker='단독판사', holding='징역 8개월, 집행유예 2년, 사회봉사 120시간 (특수상해)',
                         current_status='항소·확정 여부 공개 보도로 확인 안 됨', verified_at='2026-10-25',
                         privacy_decision='피고인·피해자 익명(A씨·B씨), 정확한 장소 비공개, 판사 실명 미사용'),
               sources=srcs, claims=claims, assets=[], approvals={k: dict(approved=False, reviewer='', at='', scope_hash='') for k in ('fact', 'risk_legal', 'rights', 'technical', 'release')},
               scenes=scenes)
    json.dump(doc, open(HERE / 'episode.final.json', 'w'), ensure_ascii=False, indent=1)
    print('cue_sheet rows', len(script['cues']), 'narration lines', len(timing['items']), 'sources', len(srcs), 'claims', len(claims))


if __name__ == '__main__':
    main()
