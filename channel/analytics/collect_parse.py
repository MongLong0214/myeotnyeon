#!/usr/bin/env python3
"""Parse local CTO Studio notes. Standard library only; no browser/network access."""
import argparse
import configparser
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

METRICS = ('views', 'average_view_duration_seconds', 'average_percentage_viewed',
           'viewed_pct', 'swiped_away_pct', 'subscribers_net')
MISSING = {'', '-', '—', 'null', 'unknown', '미확인', '없음'}


def number(value, integer=False, percent=False, signed=False):
    if value.strip().lower() in MISSING:
        return None
    value = value.strip().replace(',', '')
    if percent:
        value = value.removesuffix('%')
    if not re.fullmatch(r'[+-]?\d+(?:\.\d+)?', value):
        raise ValueError(f'정확한 수치 필요 (축약값 불가): {value!r}')
    x = float(value)
    if not signed and x < 0:
        raise ValueError('음수 불가')
    if integer and not x.is_integer():
        raise ValueError('정수 필요')
    return int(x) if integer else x


def duration(value):
    if value.strip().lower() in MISSING:
        return None
    if ':' not in value:
        return number(value)
    if not re.fullmatch(r'\d+:\d{2}(?::\d{2})?', value):
        raise ValueError(f'기간 형식 오류: {value}')
    parts = list(map(int, value.split(':')))
    if any(x >= 60 for x in parts[1:]):
        raise ValueError('초/분은 60 미만')
    result = 0
    for p in parts:
        result = result * 60 + p
    return result


def date(value):
    return dt.date.fromisoformat(value).isoformat()


def blank_video(vid):
    return dict(video_id=vid, title=None, publish_date=None,
                metric_period='unknown', observed_at=None,
                **{k: None for k in METRICS}, traffic_sources=None, sources={})


def parse(text, source_file):
    lines = text.splitlines()
    root = dict(schema_version=1, collection_date=None, observed_at=None,
                timezone='Asia/Seoul', source_file=source_file,
                source_sha256=hashlib.sha256(text.encode()).hexdigest(),
                channel={}, videos=[], warnings=[])

    def put(obj, key, value, line, raw, kind='observed'):
        obj[key] = value
        obj.setdefault('sources', {})[key] = dict(file=source_file, line=line, raw=raw, kind=kind)

    if text.lstrip().startswith('# Studio snapshot'):
        head = re.search(r'Studio snapshot (\d{4}-\d{2}-\d{2})([^\n]*)', text)
        root['collection_date'] = date(head[1])
        root['observed_at'] = None  # ~10:00 is approximate, retained verbatim below
        root['observation_note'] = head[0]
        year = root['collection_date'][:4]
        for ln, raw in enumerate(lines, 1):
            if raw.startswith('Channel:'):
                m = re.fullmatch(r'Channel: last 28 days \((\d{2}-\d{2}) to (\d{2}-\d{2})\) ([\d,]+) views, ([\d.]+) h watch time, ([+-]?\d+) subscribers\. Live: (\d+) subscribers, ([\d,]+) views in the last 48 h\.', raw)
                if not m:
                    raise ValueError(f'{ln}: 스냅샷 채널 행 형식 오류')
                c = root['channel']
                for key, val in dict(period_label='last 28 days (as reported)',
                                     period_start=date(f'{year}-{m[1]}'), period_end=date(f'{year}-{m[2]}'),
                                     views=number(m[3], True), watch_hours=number(m[4]),
                                     subscribers_net=number(m[5], True, signed=True),
                                     subscribers_total=number(m[6], True), views_48h=number(m[7], True)).items():
                    put(c, key, val, ln, raw)
            if not raw.startswith('- ') or ' | ' not in raw:
                continue
            parts = raw[2:].split(' | ')
            if len(parts) < 4:
                raise ValueError(f'{ln}: 영상 행 필드 부족')
            vid, title, published, views, *extras = parts
            v = blank_video(vid)
            for key, val in dict(title=title, publish_date=date(f'{year}-{published}'), views=number(views, True)).items():
                put(v, key, val, ln, raw)
            for extra in extras:
                m = re.fullmatch(r'(\d+:\d{2}) \(([\d.]+)%\)', extra)
                if m:
                    put(v, 'average_view_duration_seconds', duration(m[1]), ln, raw)
                    put(v, 'average_percentage_viewed', number(m[2]), ln, raw)
                elif re.search(r'viewed ([\d.]+)%', extra):
                    put(v, 'viewed_pct', number(re.search(r'viewed ([\d.]+)%', extra)[1]), ln, raw)
                elif re.fullmatch(r'subs [+-]?\d+(?: \(.*\))?', extra):
                    put(v, 'subscribers_net', number(re.search(r'subs ([+-]?\d+)', extra)[1], True, signed=True), ln, raw)
                else:
                    raise ValueError(f'{ln}: 인식 못한 지표: {extra}')
            root['videos'].append(v)
        root['warnings'] += ['영상별 지표 기간 미기재: unknown. 현재 조회수를 과거 구독자/유입 비율과 합치지 말 것.',
                             '채널 기간은 원문 그대로 보존. last 28 days와 명시 시작/종료일을 CTO가 재확인할 것.']
    else:
        cfg = configparser.ConfigParser(interpolation=None, delimiters=('=',), strict=True)
        cfg.optionxform = str
        cfg.read_string(text)
        if 'collection' not in cfg or 'channel' not in cfg:
            raise ValueError('[collection], [channel] 필수')
        root['collection_date'] = date(cfg['collection']['date'])
        observed = cfg['collection'].get('observed_at', '')
        root['observed_at'] = None if observed.lower() in MISSING else observed
        if root['observed_at'] and dt.datetime.fromisoformat(root['observed_at']).utcoffset() is None:
            raise ValueError('observed_at에 UTC offset 필수')
        root['observation_note'] = cfg['collection'].get('note', '')
        current = None
        locations = {}
        for ln, raw in enumerate(lines, 1):
            if raw.strip().startswith('['):
                current = raw.strip()[1:-1]
            elif '=' in raw and not raw.lstrip().startswith(('#', ';')):
                locations[(current, raw.split('=', 1)[0].strip())] = (ln, raw)
        channel_keys = {'period_start', 'period_end', 'period_label', 'views', 'watch_hours',
                        'subscribers_net', 'subscribers_total', 'views_48h'}
        video_keys = set(METRICS) | {'title', 'publish_date', 'metric_period', 'observed_at'}
        for section in cfg.sections():
            if section == 'collection':
                if set(cfg[section]) - {'date', 'observed_at', 'note'}:
                    raise ValueError('알 수 없는 collection 필드')
                continue
            if section == 'channel':
                obj, allowed = root['channel'], channel_keys
            elif section.startswith('video '):
                obj, allowed = blank_video(section[6:]), video_keys
                root['videos'].append(obj)
            else:
                raise ValueError(f'알 수 없는 섹션 {section}')
            traffic = []
            for key, raw_value in cfg[section].items():
                ln, raw = locations[(section, key)]
                if key.startswith('traffic.') and section.startswith('video '):
                    bits = [x.strip() for x in raw_value.split('|')]
                    if len(bits) != 2:
                        raise ValueError('traffic.NAME = views | pct 형식 필요')
                    traffic.append(dict(name=key[8:], views=number(bits[0], True), pct=number(bits[1], percent=True),
                                        source=dict(file=source_file, line=ln, raw=raw, kind='observed')))
                    continue
                if key not in allowed:
                    raise ValueError(f'{section}: 알 수 없는 필드 {key}')
                if key in {'publish_date', 'period_start', 'period_end'}:
                    val = None if raw_value.lower() in MISSING else date(raw_value)
                elif key == 'average_view_duration_seconds':
                    val = duration(raw_value)
                elif key in {'views', 'subscribers_net', 'subscribers_total', 'views_48h'}:
                    val = number(raw_value, True, signed=key == 'subscribers_net')
                elif key in {'watch_hours', 'average_percentage_viewed', 'viewed_pct', 'swiped_away_pct'}:
                    val = number(raw_value, percent=key.endswith('pct') or key == 'average_percentage_viewed')
                elif key == 'metric_period':
                    val = raw_value
                else:
                    val = None if raw_value.lower() in MISSING else raw_value
                put(obj, key, val, ln, raw)
            if traffic:
                obj['traffic_sources'] = traffic
    if not root['channel'] or not root['videos']:
        raise ValueError('채널/영상 데이터 없음')
    for key in ['period_label', 'period_start', 'period_end', 'views', 'watch_hours',
                'subscribers_net', 'subscribers_total', 'views_48h']:
        root['channel'].setdefault(key, None)
    seen = set()
    for v in root['videos']:
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', v['video_id']) or v['video_id'] in seen:
            raise ValueError('영상 ID 형식 오류 또는 중복: ' + v['video_id'])
        seen.add(v['video_id'])
        if v['observed_at'] and dt.datetime.fromisoformat(v['observed_at']).utcoffset() is None:
            raise ValueError('영상 observed_at에 UTC offset 필수')
        if v['metric_period'] not in {'lifetime', 'first_48h', 'first_7d', 'last_28d', 'unknown'}:
            raise ValueError('metric_period 허용값 오류')
        for key in ['viewed_pct', 'swiped_away_pct']:
            if v[key] is not None and not 0 <= v[key] <= 100:
                raise ValueError(f'{key} 범위 오류')
        for item in v['traffic_sources'] or []:
            if item['pct'] is not None and not 0 <= item['pct'] <= 100:
                raise ValueError('traffic pct 범위 오류')
        if v['viewed_pct'] is not None and v['swiped_away_pct'] is not None:
            if abs(v['viewed_pct'] + v['swiped_away_pct'] - 100) > .2:
                root['warnings'].append(v['video_id'] + ': viewed+swiped가 100%와 다름 (반올림/기간 확인)')
    return root


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input', type=Path)
    ap.add_argument('--output-dir', type=Path, default=Path(__file__).parent / 'daily')
    args = ap.parse_args()
    try:
        result = parse(args.input.read_text(encoding='utf-8'), str(args.input))
    except (ValueError, KeyError, configparser.Error) as exc:
        ap.error(str(exc))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    target = args.output_dir / (result['collection_date'] + '.json')
    temp = target.with_suffix('.json.tmp')
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temp.replace(target)
    print(target)


if __name__ == '__main__':
    main()
