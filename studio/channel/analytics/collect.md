# Studio 수집 → 로컬 분석

이 폴더의 Python은 표준 라이브러리만 사용하며 브라우저·Aside·네트워크·업로드를 호출하지 않는다. Studio 수집은 **CTO가 Aside repl로 읽기 전용 수행**한다. 실제 수집을 이 lane에서 수행하지 않았다.

## CTO 수집 절차

1. Studio 채널 분석의 기간·조회수·시청시간·순구독자 증감, 실시간 총구독자·최근 48시간 조회수를 표시된 그대로 복사한다. 채널 날짜 범위와 수집 시각(KST)을 함께 적는다.
2. 콘텐츠 목록에서 Shorts 각각의 **11자 video_id, 현재 제목, 실제 공개일**을 기록한다. 예약일·업로드일과 공개일을 구별한다. 공개/예약/비공개를 구별하며 비공개 원본과 교체 공개본을 합치지 않는다.
3. 각 영상 분석에서 같은 기간으로 조회수, 평균 시청 지속 시간, 평균 시청 비율, 계속 시청(viewed)·스와이프(swiped away), 순구독 증감을 복사한다. 구독 획득만 보이면 순증으로 옮기지 말고 null로 남긴 뒤 note에 원문을 적는다. 기간을 화면에서 확인 못 하면 `unknown`.
4. 도달범위/트래픽 소스의 소스명·조회·비율을 복사한다. 소스명이 같은데 서로 다른 기간이면 섞지 않는다. 표시된 소스만 기록하고, 생략된 소스·비율을 역산하지 않는다. 정확한 수치가 아닌 `1.3천` 같은 축약이면 상세 수치를 읽거나 null을 기록한다.
5. 아래 텍스트 형식으로 `raw/YYYY-MM-DD.txt`에 저장한다. 화면 원문/캡처 경로와 선택한 기간은 `note`에 적는다. 이름·수치·제목을 추정해서 채우지 않는다. `traffic.` 뒤 소스명은 Studio 원문 그대로 쓴다.
6. 신규 영상은 공개 후 48시간과 7일에 해당 경과 창(`first_48h`, `first_7d`)으로 수집한다. 매일 lifetime 수집도 가능하나 같은 연령 실험 비교를 대체하지 않는다. 한 daily는 영상당 하나의 기간만 담는다. 같은 날 재수집하면 raw 원본을 보관한 뒤 daily를 재생성한다.
7. 아래 명령을 실행하고 `analysis_날짜.md`를 읽어 확인일에 가설을 유지/수정/보류한다. RULES의 잠정 규칙은 결과 확인 후 사람이 갱신한다. 자동 공장 변경·자동 업로드·스케줄 설치는 포함하지 않는다.

```sh
cd .
python3 channel/analytics/collect_parse.py channel/analytics/raw/YYYY-MM-DD.txt
python3 channel/analytics/analyze.py --daily channel/analytics/daily/YYYY-MM-DD.json
# 제공된 11-06 스냅샷도 원문 그대로 파싱 가능
python3 channel/analytics/collect_parse.py channel/analytics/snapshot_2026-11-06.md
```

## 입력 형식 (아래 수치는 예시로 만들지 않고 결측으로 표시)

`[video VIDEO_ID]`의 VIDEO_ID는 실제 ID로 교체한다. 영상 섹션을 반복한다. 값 앞뒤 공백은 허용하며 구분자는 `=`이다. 숫자는 쉼표 허용, 축약값 불가. `null`, `—`, `-`, `미확인`, 빈 문자열은 결측이다. 0은 관측된 0에만 쓴다. 텍스트에 `=`가 들어가도 값 안에서는 허용한다.

```ini
[collection]
date = 2026-11-06
observed_at = null
note = CTO 수집 시각·원문/캡처 경로·기간·누락 이유를 여기에 기록

[channel]
period_label = null
period_start = null
period_end = null
views = null
watch_hours = null
subscribers_net = null
subscribers_total = null
views_48h = null

[video VIDEO_ID]
title = null
publish_date = null
metric_period = unknown
observed_at = null
views = null
average_view_duration_seconds = null
average_percentage_viewed = null
viewed_pct = null
swiped_away_pct = null
subscribers_net = null
traffic.Shorts 피드 = null | null
```

`observed_at`은 정확한 시각이 있을 때만 ISO 8601 UTC offset 포함 문자열로 입력한다. `~10:00` 같은 근삿값은 null + note. 시간은 숫자 초 또는 `M:SS`/`H:MM:SS`, 비율은 % 단위(퍼센트 기호 생략 가능). `traffic.소스명 = 조회수 | 비율`이다. 유입 데이터 전체가 미수집이면 traffic 행 자체를 생략한다. 위 null 행은 소스명만 확인한 경우에 해당한다.

## daily JSON 정확한 필드 계약 (schema_version=1)

필드 이름·단위는 아래와 같다. 별도 표기 없으면 항상 존재한다. 결측은 JSON `null`; 관측값을 보간하거나 100−viewed로 swiped를 채우지 않는다.

| 경로 | 타입·뜻 |
|---|---|
| `schema_version` | integer, 1 |
| `collection_date` | string `YYYY-MM-DD`, 저장 파일명과 일치 |
| `observed_at` | ISO datetime with UTC offset 또는 null |
| `observation_note` | string, 원문 헤더/수집 메모 |
| `timezone` | string, `Asia/Seoul` |
| `source_file`, `source_sha256` | 원본 텍스트 경로, UTF-8로 읽은 텍스트 SHA-256 |
| `channel` | 아래 채널 객체 |
| `videos` | 영상 객체 배열; video_id 유일, ID 문법 검증 |
| `warnings` | string 배열; 확인할 기간·반올림 문제 |
| `channel.period_label` | string 또는 null, 화면의 기간명 |
| `channel.period_start`, `channel.period_end` | `YYYY-MM-DD` 또는 null, 화면의 명시 범위 |
| `channel.views`, `channel.views_48h` | nonnegative integer 또는 null; 전자는 지정 기간, 후자는 실시간 48시간 |
| `channel.watch_hours` | nonnegative number 또는 null, 시간 |
| `channel.subscribers_net` | signed integer 또는 null, 지정 기간 순증 |
| `channel.subscribers_total` | nonnegative integer 또는 null, 실시간 총구독자 |
| `channel.sources` | 관측된 각 필드 이름 → source 객체 |
| `videos[].video_id` | string, 11자 YouTube ID; qid/시리즈 번호와 다름 |
| `videos[].title` | string 또는 null, 수집된 제목(스냅샷은 축약명) |
| `videos[].publish_date` | `YYYY-MM-DD` 또는 null, 실제 공개일 |
| `videos[].metric_period` | enum `lifetime`, `first_48h`, `first_7d`, `last_28d`, `unknown` |
| `videos[].observed_at` | ISO datetime with offset 또는 null; null이면 collection 관측 메모 참조 |
| `videos[].views` | nonnegative integer 또는 null, 해당 영상 기간 조회 |
| `videos[].average_view_duration_seconds` | nonnegative number 또는 null, 초 |
| `videos[].average_percentage_viewed` | nonnegative number 또는 null, **% 단위; 100 초과 허용** |
| `videos[].viewed_pct`, `videos[].swiped_away_pct` | number 0–100 또는 null, Studio의 계속 시청/이탈 비율 |
| `videos[].subscribers_net` | signed integer 또는 null, 영상 지정 기간 순증 |
| `videos[].traffic_sources` | null 또는 아래 유입 객체 배열; 전체 100%를 요구하지 않음 |
| `videos[].sources` | title·날짜·관측 지표 → source 객체; 미수집 필드는 키 없음 |
| 유입 객체 | `{name: string, views: nonnegative integer\|null, pct: 0..100\|null, source: source객체}` |
| source 객체 | `{file: string, line: integer(1부터), raw: string(원문 행), kind: "observed"}` |

현재 스냅샷의 영상 지표 창은 미기재여서 `unknown`이다. 채널 `last 28 days (10-08 to 11-04)`는 날짜/레이블을 모두 원문대로 보존하고 재확인 경고를 남긴다. 2026년은 11-06 헤더에서 가져왔다. 스냅샷 `Observations` 문장의 추정치는 측정 필드로 읽지 않는다. 10-30 JSON은 별도 역사 자료로만 읽고 11-06 결측을 채우지 않는다.

## features와 분석 갱신

`features.json`은 video_id당 한 행이며 `sources`에서 특징별 파일·위치·측정/해석 방법을 붙였다. `topics`, `title_pattern`, `answer_type`, `reenactment.type`은 제작 기록을 분류한 편집 판단이다. `hook_first_2s`는 자막 시간구간·헤드라인·그림·움직임을 분리한다. `length_seconds`는 로컬 MP4의 영상 프레임 수/프레임률이다. 공개본 동일 해시가 확인된 길이라고 주장하지 않는다.

새 영상은 로컬 패키지 `episode.json`, `render.json`, `meta.txt`, 실제 MP4와 Studio ID를 대조해 행을 추가한다. qid와 번호를 같다고 가정하지 않는다. q014 공개 ID는 `upload/ledger.json`의 replacement ID를 사용했다. 나머지 제목·날짜 매칭 추론은 `identity_confidence`에 표시했다. q013은 예약 상태라 이번 성과 표본에서 제외했다.

`analyze.py`는 최신 daily 또는 명시한 daily를 features와 video_id로 연결하여 기간별 그룹 중앙값·결측 수·근거 영상·가설 표·다음 7편 제안을 `analysis_날짜.json/.md`로 생성한다. features에 없는 ID는 `unmatched_video_ids`로 노출한다. 7편 날짜는 분석 기준일 다음 날부터의 **제안**이며 기존 예약을 바꾸지 않는다. 계획 실행일이 달라지면 실제 공개일+7일로 결과 확인일을 다시 잡는다. 규칙·1페이지 보고서는 분석 JSON을 근거로 작성한 이번 판본이다.
