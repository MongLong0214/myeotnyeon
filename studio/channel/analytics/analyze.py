#!/usr/bin/env python3
"""Offline descriptive feature × performance analysis; no significance claims."""
import argparse
import datetime as dt
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def experiment_plan(day):
    def on(n):
        return (day + dt.timedelta(days=n)).isoformat()
    # One new case per video. These are matched sequential comparisons, not randomised A/B.
    arms = [
        ('hook', 'A: 첫 2초 사건 결과 자막 + 현재 hero', 'V2', 'H1', 9),
        ('hook', 'B: 같은 자막 + 사건 행위가 즉시 읽히는 그림/동작', 'V1', 'H1', 9),
        ('reenactment', 'A: q014식 comedy rig, 몸·팔·표정과 원인→반응', 'V4', 'H2', 11),
        ('reenactment', 'B: 같은 설명을 static panels로', 'V3', 'H2', 11),
        ('title_length_baseline', '제목 A: 질문형 / 길이 A: 필요한 설명을 모두 유지', 'V6 / V7', 'H4/H5', 14),
        ('title', '제목 B: 쟁점·결과 예고형 / 길이 A', 'V5', 'H4', 13),
        ('length', '제목 A / 길이 B: 중복 설명·대기만 줄임', 'V5', 'H5', 14),
    ]
    return [dict(slot=f'V{i}', proposed_publish_date=on(i), axis=axis, arm=arm,
                 comparison=comp, hypothesis=h, result_confirmation_date=on(confirm),
                 primary_metric='viewed_pct' if axis == 'hook' else
                    'views (first_7d)' if axis == 'title' else 'subscribers_net per 1,000 views',
                 secondary_metrics=['average_view_duration_seconds', 'average_percentage_viewed', 'viewed_pct', 'views', 'subscribers_net', 'traffic_sources'],
                 controls='유사 주제·정답 유형·공개 시각·CTA·다른 제작 요소 유지. 제목/길이 비교는 V5 공통 기준. 서로 다른 신규 사건이므로 주제 교란 남음.')
            for i, (axis, arm, comp, h, confirm) in enumerate(arms, 1)]


def analyze(daily, features, source, history_path):
    by_id = {v['video_id']: v for v in features['videos']}
    if len(by_id) != len(features['videos']):
        raise ValueError('features에 중복 video_id')
    rows, unmatched = [], []
    for p in daily['videos']:
        if p['video_id'] not in by_id:
            unmatched.append(p['video_id'])
            continue
        f = by_id[p['video_id']]
        rows.append(dict(**p, features=f))
    if not rows:
        raise ValueError('연결되는 영상 없음')
    def label(r):
        return f"{r['features']['qid']} ({r['video_id']})"
    def comparisons(rs, keys):
        return [dict(video=label(r), values={k: r.get(k) for k in keys},
                     source={k:r['sources'][k] for k in keys if k in r['sources']},
                     feature_reference=f"features.json: video_id={r['video_id']}, sources") for r in rs]
    def summary(rs):
        out = dict(n=len(rs), videos=[label(r) for r in rs])
        for key in ['views', 'average_view_duration_seconds', 'average_percentage_viewed', 'viewed_pct', 'subscribers_net']:
            vals = [r[key] for r in rs if r[key] is not None]
            out[key] = dict(n=len(vals), median=round(median(vals), 6) if vals else None)
        return out
    # Never pool metric windows. Unknown is descriptive only, not a comparable exposure window.
    groups = {}
    length_mid = median(r['features']['length_seconds'] for r in rows)
    for r in rows:
        f = r['features']
        dimensions = dict(topic=f['topics'], hook=[f['hook_first_2s']['format']],
                          reenactment=[f['reenactment']['type']], title=[f['title_pattern']],
                          answer=[f['answer_type']],
                          length=['<= sample median' if f['length_seconds'] <= length_mid else '> sample median'])
        for axis, values in dimensions.items():
            for value in values:
                groups.setdefault((axis, value, r['metric_period']), []).append(r)
    group_results = [dict(axis=a, value=v, metric_period=p, **summary(rs)) for (a,v,p),rs in sorted(groups.items())]
    day = dt.date.fromisoformat(daily['collection_date'])
    confirm = lambda n: (day + dt.timedelta(days=n)).isoformat()
    viewed = [r for r in rows if r['viewed_pct'] is not None]
    ranked = sorted(viewed, key=lambda r:r['viewed_pct'])
    low, high = (ranked[0], ranked[-1]) if ranked else (None, None)
    gap = round(high['viewed_pct'] - low['viewed_pct'], 3) if ranked else None
    comedy = [r for r in rows if r['features']['reenactment']['type'] == 'comedy_rig']
    reference = [r for r in rows if r['features']['qid'] == 'q006']
    channel = daily['channel']
    views, subs, total = channel.get('views'), channel.get('subscribers_net'), channel.get('subscribers_total')
    rate = subs/views if views and subs is not None else None
    gap_subs = max(0, 1000-total) if total is not None else None
    remaining_views = gap_subs*views/subs if rate and rate > 0 and gap_subs is not None else None
    hypotheses = [
        dict(id='H1', claim='첫 2초의 즉시 이해 가능한 사실·그림이 진입률을 높일 수 있다', direction='viewed_pct ↑',
             strength='중간: 진입 병목 관측은 높음, 훅 변경의 인과 신뢰는 낮음',
             evidence=f'현재 viewed 관측 {len(viewed)}/{len(rows)}개; 최대−최소 {gap}pp. 나머지는 결측.',
             comparisons=comparisons(ranked, ['viewed_pct','average_percentage_viewed']),
             caveat='주제·공개일·포맷 동시 변경. 10-30 memo의 원인 단정은 재사용하지 않음.', result_confirmation_date=confirm(9)),
        dict(id='H2', claim='q014식 원인→반응 코미디 재연이 본문 몰입과 구독을 돕는다', direction='구독/1,000조회 ↑, 시청 지속 ↑',
             strength='낮음: owner 선호는 명확; 성과 인과 근거 부족',
             evidence='q014와 유사 폭행 사망 주제 q006 비교; q014 유지율/viewed 결측. 훅은 코미디 변경 범위 밖.',
             comparisons=comparisons(comedy+reference, ['views','subscribers_net','average_percentage_viewed','viewed_pct']),
             caveat='q014의 +1만으로 승자 선언 불가; 노출기간 다름. q006은 static 대조군도 아님.', result_confirmation_date=confirm(11)),
        dict(id='H3', claim='현재 구독 전환으로는 조회·전환을 함께 늘려야 1,000명에 접근한다', direction='조회 × 순구독 전환 ↑',
             strength='운영 진단 높음 / 개선 수단의 효과 미검증',
             evidence=f'채널 같은 기간 순구독/조회 = {subs}/{views}; live 구독 {total}. 이는 순구독 대용 지표.',
             comparisons=comparisons(comedy, ['views','subscribers_net']), channel_source=channel.get('sources'),
             caveat='채널 28일 값과 live 총구독·48시간 조회는 서로 다른 창. 구독 획득률·예측으로 해석 금지.', result_confirmation_date=confirm(14)),
        dict(id='H4', claim='질문형 대 쟁점 예고형 제목은 신규 영상으로 비교해야 한다', direction='미정 (first_7d 조회·유입별 성과)',
             strength='판단 보류', evidence='현재 제목은 대부분 질문형; Studio 제목은 축약, 로컬 metadata는 후보.',
             comparisons=comparisons(rows, ['views']), caveat='Shorts feed의 viewed는 제목 단독 효과 지표가 아님.', result_confirmation_date=confirm(13)),
        dict(id='H5', claim='중복 설명을 줄인 길이가 절대 시청시간을 지키며 평균 시청 비율을 높일 수 있다', direction='비율 ↑; 절대 시간·구독 동반 확인',
             strength='낮음', evidence=f'길이는 로컬 MP4 측정; 표본 중앙값 {length_mid:.3f}s로 기술적 분할.',
             comparisons=comparisons([r for r in rows if r['average_percentage_viewed'] is not None], ['views','average_view_duration_seconds','average_percentage_viewed']),
             caveat='100% 초과를 자르지 않음. 루프/재시청 가능성과 분모 길이의 기계적 효과; 원인 미확인.', result_confirmation_date=confirm(14)),
        dict(id='H6', claim='사망·폭력 등 주제 자체만으로 분배 확대를 설명할 수 없다', direction='주제 가중치 보류',
             strength='운영 진단 중간 / 주제 효과 낮음', evidence='topic별 실제 비교는 아래 group_results. 다중 태그는 집단이 겹침.',
             comparisons=comparisons(rows, ['views','average_percentage_viewed']),
             caveat='저조회 q004/q005를 약한 주제의 증거로 쓰지 않음. 재업로드 억제는 10-30의 미확인 가설.', result_confirmation_date=confirm(14)),
    ]
    history = read(history_path) if history_path.exists() else None
    return dict(as_of=day.isoformat(), sources=[str(source),str(HERE/'features.json'),str(history_path)],
                sample_size=len(rows), unmatched_video_ids=unmatched,
                limitations=['통계적 유의성·인과 추정·회귀를 주장하지 않음. 서로 다른 영상 연령·관측 창·노출량.',
                             'identity inferred 및 local candidate와 공개본의 일치 확인 필요. 결측≠0. 그룹 median은 비가중 기술 통계.',
                             '표본이 늘어도 이 스크립트는 가설 갱신 보조. RULES/REPORT의 자동 덮어쓰기·공장 수정·공개 없음.'],
                missing_metrics={k:sum(r[k] is None for r in rows) for k in ['views','average_view_duration_seconds','average_percentage_viewed','viewed_pct','subscribers_net','traffic_sources']},
                historical_context=dict(source=str(history_path), data=history, usage='별도 과거 창; 현재 행에 결측 보간하지 않음'),
                length_split_seconds=length_mid, group_results=group_results, hypotheses=hypotheses,
                experiments=experiment_plan(day),
                kpi=dict(source=channel.get('sources'), subscribers_goal=1000, subscribers_current=total,
                         subscribers_remaining=gap_subs, net_subscribers_per_view=rate,
                         net_subscribers_per_1000_views=rate*1000 if rate is not None else None,
                         additional_views_at_unchanged_proxy=remaining_views,
                         meaning='목표 산술 시나리오; 순구독/조회 대용값 유지 가정. 달성 날짜 예측 아님.'))


def markdown(result):
    lines = [f"# 가설 분석 {result['as_of']}", '',
             f"표본 {result['sample_size']}개. 통계적 유의성 없음. 출처: " + ', '.join(result['sources']), '',
             '결측: ' + json.dumps(result['missing_metrics'], ensure_ascii=False), '',
             '| 가설 | 방향 | 근거 강도 | 비교 영상·관측 | 결과 확인일 |', '|---|---|---|---|---|']
    for h in result['hypotheses']:
        evidence = '; '.join(f"{c['video']}: " + ', '.join(f'{k}={v}' for k,v in c['values'].items() if v is not None) for c in h['comparisons'])
        lines.append(f"| {h['id']} {h['claim']} | {h['direction']} | {h['strength']} | {h['evidence']}<br>{evidence}<br>제약: {h['caveat']} | {h['result_confirmation_date']} |")
    lines += ['', '## 특징 × 성과 (기간별 분리, 비가중 중앙값)', '',
              '| 특징 | 값 | 기간 | n | 조회 중앙값 (관측 n) | 평균 시청 비율 중앙값 (관측 n) | 비교 영상 |', '|---|---|---|---|---|---|---|']
    for g in result['group_results']:
        lines.append(f"| {g['axis']} | {g['value']} | {g['metric_period']} | {g['n']} | {g['views']['median']} ({g['views']['n']}) | {g['average_percentage_viewed']['median']} ({g['average_percentage_viewed']['n']}) | {', '.join(g['videos'])} |")
    lines += ['', '## 다음 7편 제안 (계획값)', '', '| 슬롯·공개 예정일 | 축·처치 | 비교 | 확인일 |', '|---|---|---|---|']
    for e in result['experiments']:
        lines.append(f"| {e['slot']} {e['proposed_publish_date']} | {e['axis']}: {e['arm']} | {e['comparison']} | {e['result_confirmation_date']} |")
    lines += ['', '각 신규 영상 48시간·7일 같은 경과 창을 CTO가 수집. 주제·정답·공개 시각·CTA와 변경하지 않는 축을 맞춘다. V5를 제목·길이 공통 기준으로 사용하며 상호작용은 판정하지 않는다. 재업로드 없음. 비교는 순차 관찰이며 무작위 A/B 실험이 아니다.', '',
              '주 지표: 훅=viewed%; 재연=순구독/1,000조회 및 시청 지속; 제목=7일 조회와 유입; 길이=절대 시청시간·비율·순구독. 결과가 섞이거나 결측이면 보류, 같은 방향 반복 시만 잠정 채택. 자료 부족이면 확인일에 보류와 다음 수집일 기록.', '',
              'KPI 산술 (예측 아님, 채널 원문 출처는 JSON의 kpi.source): ' + json.dumps({k:v for k,v in result['kpi'].items() if k != 'source'},ensure_ascii=False), '',
              *result['limitations']]
    return '\n'.join(lines)+'\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--daily', type=Path)
    ap.add_argument('--features', type=Path, default=HERE/'features.json')
    ap.add_argument('--history', type=Path, default=W/'research/metrics/2026-10-30.json')
    ap.add_argument('--output-dir', type=Path, default=HERE)
    args = ap.parse_args()
    if args.daily is None:
        files = sorted((HERE/'daily').glob('????-??-??.json'))
        if not files:
            ap.error('daily 없음: collect_parse.py 먼저 실행')
        args.daily = files[-1]
    result = analyze(read(args.daily), read(args.features), args.daily, args.history)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.output_dir/f"analysis_{result['as_of']}"
    stem.with_suffix('.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n',encoding='utf-8')
    stem.with_suffix('.md').write_text(markdown(result),encoding='utf-8')
    print(stem.with_suffix('.md'))


if __name__ == '__main__':
    main()
