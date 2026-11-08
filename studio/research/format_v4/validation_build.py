# -*- coding: utf-8 -*-
"""Calculate the requested research data from timestamped public observations."""
import datetime as dt
import json
import pathlib
import re
import statistics as st
import sys
import urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'tools'))
from subs import parse

R=pathlib.Path(__file__).resolve().parent
RAW=R/'validation_raw'; DEEP=R/'validation_deep'; DATES=R/'validation_dates'
KST=dt.timezone(dt.timedelta(hours=9))
def now():return dt.datetime.now(KST).isoformat(timespec='seconds')
def read(p,default=None):
    try:return json.loads(p.read_text())
    except Exception:return default
def rows(p):
    if not p.exists():return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def num(s):
    s=s.strip().replace(',','')
    try:return round(float(s.rstrip('KMB'))*({'K':1e3,'M':1e6,'B':1e9}.get(s[-1],1)))
    except:return None
def texts(v):
    if isinstance(v,dict):
        if v.get('type')=='text':yield v.get('text','')
        else:
            for x in v.values():yield from texts(x)
    elif isinstance(v,list):
        for x in v:yield from texts(x)
def time_kst(t):
    if not t:return None
    if t.endswith(' UTC'):return dt.datetime.strptime(t,'%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=dt.timezone.utc).astimezone(KST).isoformat()
    return t
def history_sources():
    result={}
    files=list(RAW.glob('history*.json'))+[RAW/'batch19_0.json']
    for p in files:
        d=read(p,{})
        text='\n'.join(texts(d))
        matches=list(re.finditer(r'URL: (https://socialblade.com/youtube/channel/(UC[\w-]+)(?:/monthly)?)\s*\n',text))
        for i,m in enumerate(matches):
            sec=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)]
            points=[]
            for line in sec.splitlines():
                parts=[s.strip() for s in line.strip().strip('|').split('|')]
                if not parts:continue
                dm=re.search(r'2026-\d\d-\d\d',parts[0])
                if dm and len(parts)>=7:
                    value=num(parts[2])
                    if value is not None:points.append(dict(date=dm.group(),subscribers=value,reported_label=parts[2],video_count=num(parts[6]),total_views=num(parts[4])))
            old=result.setdefault(m[2],[])
            old.append(dict(url=m[1],access_result='공개 일별 표 읽기 성공' if len(points)>1 else '페이지 접근 성공 / 단일 시점만 있음' if points else '페이지 접근 성공 / 구독자 시계열 미추출',observed_at_kst=time_kst(d.get('observed_at_kst')),source_file=str(p.relative_to(R)),daily_subscribers=points,quality='공개 통계 수집 사이트의 반올림 구독자 이력; YouTube 내부 분석 아님'))
    return result

ANALYSIS={
'엑스톨(Extol)':dict(archetype='공간 재구성 사건 다큐',role='owner_visual_reference_and_conditional_model',title_pattern='기간·숫자 + 실명 사건 + 체포/암살의 방법',thumbnail_pattern='한 사건의 3D 공간·인물 대치, 인물/역할 라벨; 최신작은 실제 인물 사진도 혼용',visual_style='입체 공간, 인물 실루엣, 고대비 색 조명, 위치·거리 주석과 하단 자막. 사진도 일부 혼용. 원본의 장면/그래픽은 사용하지 않는다.',hook='범행 또는 현장의 시공간을 먼저 제시하고 작전의 원인과 경로를 설명한다.',structure='현장 진입 → 배경/인물 → 동선·행동의 연쇄 → 체포/사후 결과. 장 구분과 공간 설명을 사용한다.',topic='한국 실존 범죄·탈옥·암살 및 범죄 공간 설명; 형량 전문 채널은 아님',limitations=['장편 공개 표본 9편으로 최근 10편 기준 미달','초기 구독자 이력과 기존 외부 관객 유입 미확인','상위3·최근3의 중복 때문에 심층 고유 영상은 4편','완전한 3D 재연의 품질·제작비를 Remotion 템플릿으로 동일하게 재현한다고 주장할 수 없음'],cost=dict(label='추정',hours_first_episode=[40,100],hours_later_episode=[30,80],incremental_tools_krw=[0,50000],assumptions='3D 신규 장면과 수작업이 필요한 수준의 범위 추정; 인건비·하드웨어 제외')),
'다큐스토리 844':dict(archetype='공간 재구성 사건 다큐',role='conditional_model',title_pattern='짧은 치명적 결과 + 숫자·시간·금지 공간 / 원인 궁금증',thumbnail_pattern='검정/어두운 배경, 빨간 사람 실루엣, 지도·단면과 화살표, 1~2개 큰 문구',visual_style='지도·동굴 단면·위치 표시와 붉은 실루엣, 일부 입체 재구성, 실제 참고영상/사진, 하단 1줄 자막.',hook='이미 위기에 빠진 현장 또는 평범한 출발에 불길한 결과를 덧붙여 왜 그렇게 됐는지 남긴다.',structure='위기/평범한 출발 → 인물·공간·규칙 → 선택과 구조 실패의 인과 → 사고 원인/사후 변화. 최신 항공편은 설명란에 7개 장이 있다.',topic='동굴·다이빙·항공 등 공간과 잘못된 선택이 결과를 바꾸는 실화 사고. 한국 형사판결 수요와 차이 있음',limitations=['참고영상/사진 혼용이므로 전부 코드 애니메이션으로 대체하는 효과는 미검증','초기 작은 채널 구간은 미확인','사건 제목과 내용의 사실 정확성 자체는 이번 형식 조사에서 검증하지 않음'],cost=dict(label='추정',hours_first_episode=[24,40],hours_later_episode=[12,24],incremental_tools_krw=[0,30000],assumptions='우리의 도식·실루엣으로 8분을 제작할 경우; 원본 영상 비용 아님; 인건비·하드웨어 제외')),
'붉은실':dict(archetype='자료 중심 수사 내레이션',role='conditional_model',title_pattern='[사건 분류] + 일상/여행/실종 + 반전·해결 단서',thumbnail_pattern='실제 인물/장면 사진 + 검정 하단 띠, 흰색 핵심어와 빨강 범죄어, 노란 보조 문구',visual_style='사진·자료 장면을 연속 배치하고 날짜·장소 카드, 하단 흰 자막. 전문 진행자의 얼굴 출연은 표본에서 보이지 않음.',hook='사건 당시 인물의 평범한 사정이나 발견 장면부터 짚는다.',structure='배경/발견 → 실종·범죄 진행 → 수사 단서/증거 → 재판 또는 미해결 상태와 피해자 사후. 최신 모자 사건 설명란에 재판 장 포함.',topic='해외 실화 범죄와 미제사건, 한국 관련 실종·범죄도 포함',limitations=['자료 사진/참고영상과 직접 녹음이라는 제작자 설명이 있어 TTS·전면 도식 전환의 성과는 미검증','최근 14일 반올림 구독자 수는 정체; 작은 채널 출발 경로 미확인','2026-10-14 누적 조회수 감소가 있으나 삭제/비공개/정정 중 원인은 미확인'],cost=dict(label='추정',hours_first_episode=[16,28],hours_later_episode=[10,18],incremental_tools_krw=[0,30000],assumptions='사진 장면을 우리 도식으로 치환한 8분 연구·대본·TTS·편집; 인건비 제외')),
'버그아카데미아':dict(archetype='만화 사연·사건',role='format_reference_existing_ip_limitation',title_pattern='【실화/실재/만화】 + 인물에게 벌어진 극단적 결과',thumbnail_pattern='좌우 2장 만화 대비, 큰 표정, 노란 바탕 검정 문구와 붉은 실화 태그',visual_style='채색 만화 컷, 세로 내레이션 상자·말풍선, 표정과 컷 구도가 바뀐다.',hook='1인칭 인물 소개 또는 피해 순간으로 들어가 대사로 상황을 진행한다.',structure='인물 소개/위기 → 대화·선택 → 결과/대가 → 설명·마무리. 최근 표본에 84분대 묶음 영상도 있어 단편과 혼재.',topic='범죄뿐 아니라 사고·직업·극단적 실화에 상상을 더한 만화; 판결문 기반 실화와 구분 필요',limitations=['설명란에서 일본 「バグアカデミア-漆黒の漫画-」와 계약하여 대사/목소리를 한국어로 바꾼다고 명시','기존 원작·제작 자산/IP의 이점; 신규 1인 채널의 재현 가능한 비용/성장 근거로 쓰지 않음','최근 14일 249000명 표기 유지; 2026-10-20 공개 영상 수 -1, 이유 미확인'],cost=dict(label='추정',hours_first_episode=[30,60],hours_later_episode=[20,40],incremental_tools_krw=[0,30000],assumptions='신규 원화·대사 연기형 TTS를 포함한 5~8분; 기존 일본 원작 자산 활용 비용이 아님')),
'재훍 영상툰':dict(archetype='만화 사연·사건',role='high_performance_but_broadcast_ip',title_pattern='인물 관계 + 웃긴 행동/신경전; Shorts 제목은 짧다',thumbnail_pattern='세로 첫 화면과 같은 만화 컷, 상단 흰 바탕 검정 상황 문장',visual_style='9:16 흰 상하 영역, 상단 상황 제목, 가운데 채색 만화 컷, 하단 대사와 브랜드 표기.',hook='생활 속 관계와 갈등을 바로 설명하고 대사로 오해를 쌓는다.',structure='관계/사연 설정 → 오해/대사 반복 → 끝의 웃긴 반전. 법적 결말 중심과는 다른 보상 구조.',topic='컬투쇼 계열 생활·연애·식당·가족 사연; 실제 한국 판결과 직접 동일 수요 아님',limitations=['화면·태그에 컬투쇼 브랜드가 반복됨; 방송 사연/IP의 기존 인지도가 비교를 제한','오디오를 듣지 않았으므로 방송 음원 사용 여부·성우 특성은 미확인','최근 14일 111만명 표기 유지; 작은 채널 성장 구간 미확인'],cost=dict(label='추정',hours_first_episode=[8,16],hours_later_episode=[4,8],incremental_tools_krw=[0,10000],assumptions='60~100초 신규 만화 컷과 TTS 제작; 방송 자산/음원 재사용 없음')),
'미지의 미스터리수첩':dict(archetype='자료 중심 수사 내레이션',role='smaller_current_scale_comparator',title_pattern='수사 기간/경찰 인원 + 대조되는 작은 단서 + 이유/결말',thumbnail_pattern='실제 인물 2~3명, 빨강 테두리·띠, 흰/노란 큰 문구',visual_style='인물/현장 사진과 참고 장면, 하단 흰 자막, 우상단 채널 표시.',hook='오랜 미제 또는 역설적인 수사 상황을 제시해 해답을 약속한다.',structure='미제/범인 예고 → 피해자·배경 → 수사 실패·새 증거 → 해결·형량/피해자 회복. 2시간 묶음 영상도 혼재.',topic='해외 범죄·미제·반전 수사와 장시간 몰아보기',limitations=['실제 자료 중심이므로 코드 렌더/TTS 치환은 미검증','직접 녹음한다는 제작자 설명만 확인; 음성 특성은 미확인','2026-10-22 영상 수 -1; 삭제/비공개/분류 정정 원인 미확인'],cost=dict(label='추정',hours_first_episode=[18,30],hours_later_episode=[12,24],incremental_tools_krw=[0,30000],assumptions='자료 조사와 도식 치환을 포함한 8~12분; 원본 2시간 묶음을 그대로 제작하는 비용 아님')),
'사건 창고':dict(archetype='자료 중심 수사 내레이션',role='low_performing_control',title_pattern='[충격 실화] + 연도/장소/사건명 + 숨겨진 진실',thumbnail_pattern='인물+증거/현장 2분할, 노랑 보조 문구, 흰/빨강 큰 범죄어',visual_style='사진풍 재연 이미지·자료사진·검정 글 카드, 굵은 노란 하단 자막. 생성 방식은 화면만으로 단정하지 않음.',hook='발견/경찰 대화/충격 장면을 먼저 놓는다.',structure='장면형 시작 → 배경과 긴 대화·수사 → 체포·재판 → 교훈·구독 유도. 최다 조회 73분 편이 나머지와 크게 다름.',topic='국내 실화 범죄·가족·보험금·재심; 영상의 주장 자체는 판결문 대조 미실시',limitations=['최신 장편 2026-01-29로 활동 중단과 노출 기간이 비교를 교란','장편 15편 중 1편 23만대, 나머지 중앙값은 수백 회','사건 사실성과 재연 대사의 근거 미확인; 이를 우리 실제 사건 대본의 출처로 삼지 않음'],cost=dict(label='추정',hours_first_episode=[16,30],hours_later_episode=[10,20],incremental_tools_krw=[0,30000],assumptions='우리 8분 도식 버전; 원본의 30~77분 길이 재현 비용 아님')),
'수다르 미스테리':dict(archetype='만화 사연·사건',role='low_performing_control',title_pattern='충격/공포 태그 + 금기 행동·물건·일본 사건',thumbnail_pattern='사진/만화와 큰 흰/빨강 문구, 일부 잔혹 묘사',visual_style='이전 사건은 사진·만화·캐릭터 혼합; 최근 괴담은 검정 배경의 촛불·정적 텍스트 카드가 중심.',hook='캐릭터 소개/사건 소개 또는 괴담의 발견으로 들어간다.',structure='소개 → 일본 사건/괴담의 연쇄 → 범죄 결과 또는 공포 여운. 최근에는 사건 만화에서 글 카드 괴담으로 바뀜.',topic='일본 실제 범죄와 2ch/5ch 괴담의 혼합',limitations=['최신 장편 2023-01-02로 약 3년9개월 휴면; 동일 시기/주제 대조가 아님','상위 1편은 연령 로그인 요구로 자막·스토리보드 접근 불가; 인증 우회하지 않음','과거 성공 편과 최근 영상의 시각 형식 자체도 달라 원인을 한 요소에 귀속할 수 없음'],cost=dict(label='추정',hours_first_episode=[12,24],hours_later_episode=[8,16],incremental_tools_krw=[0,20000],assumptions='신규 6~8분 간단한 만화/도식; 인건비 제외')),
'형량계산기':dict(archetype='형량·최후 Shorts',role='low_performing_control',title_pattern='행위·피해 기간/금액 + 그런데 형량은 X',thumbnail_pattern='어두운 세로 첫 화면, 흰 글씨 속 빨강 숫자·형량',visual_style='9:16 어두운 법정·사건 상징 이미지, 중앙 짧은 자막과 빨강 강조, 고정 채널 표기.',hook='가해 행위와 기대와 다른 형량을 첫 문장부터 대비한다.',structure='형량 역설 → 사건 입력 → 가중/감경 사정 또는 법률 이유 → 형량 → 댓글 질문. 45~62초 표본.',topic='실제 형사사건의 낮아 보이는 형량·감형·사법 불만',limitations=['현재 28명, 최근20 중앙값608.5회; 탐색 신호를 성장 검증으로 쓰지 않음','통계 사이트는 단일 시점만 있어 성장 경로 미확인','최신 Shorts 2026-08-11로 휴면 기간이 있음','피해액/형량의 단순 산술 대비는 사건별 사정 차이를 가릴 수 있음'],cost=dict(label='추정',hours_first_episode=[3,6],hours_later_episode=[2,4],incremental_tools_krw=[0,5000],assumptions='45~60초, 기존 템플릿·TTS; 사실 확인 포함, 인건비 제외')),
'결국 이렇게':dict(archetype='형량·최후 Shorts',role='exploratory_short_case_candidate',title_pattern='인물의 도발적 말 + 차종/나이/행동 + 결말/최후',thumbnail_pattern='남색 세로 화면 상단 상황 제목, 중앙 장면과 하단 자막',visual_style='9:16 남색 상하 여백, 중앙 사진/만화 인물/법정 이미지 전환, 숫자·결과를 자막으로 강조.',hook='일상 분쟁의 행동을 보여 주고 도발 대사를 붙인다.',structure='행동/갈등 → 법정의 변명 → 증거/법원의 판단 → 벌금·형량 또는 무죄의 반전 → 최근 3편 끝에 선택형 좋아요/댓글 유도 화면. 40~51초 표본.',topic='주차·보복·보험사기 등 일상 분쟁의 재판 결말',limitations=['현재66명; 최근20 중앙값2250회와 상위9.8만 편의 격차','통계 사이트는 단일 시점만 있어 성장 경로 미확인','원본 음성·음악·효과음 미확인; 대사 사실성도 별도 확인 필요'],cost=dict(label='추정',hours_first_episode=[4,8],hours_later_episode=[2,5],incremental_tools_krw=[0,5000],assumptions='40~60초 신규 도식/인물·TTS; 인건비 제외'))
}

def compact_meta(vid):
    d=read(DATES/(vid+'.json'),{})
    if d.get('data'):return d['data'],d.get('observed_at_kst'),'compact'
    d=rows(RAW/('video_'+vid+'.jsonl'))
    if d:return d[0],read(RAW/('video_'+vid+'.status.json'),{}).get('finished_at_kst'),'channel_sample'
    p=DEEP/vid/'metadata.txt';d=read(p)
    if d:return d,read(DEEP/vid/'metadata.status.json',{}).get('finished_at_kst'),'deep'
    return {},None,None
def entry(r):
    return {k:r.get(k) for k in ['id','url','title','view_count','duration','timestamp','upload_date','availability','live_status']}
def tab_summary(c,tab):
    key=c['channel_id']+'_'+tab;p=RAW/(key+'.jsonl');rs=rows(p);s=read(RAW/(key+'.status.json'),{})
    allp=RAW/(key+'_all.jsonl');full=rows(allp) if allp.exists() else None
    absent='does not have a '+tab+' tab' in s.get('error','')
    exact=len(full) if full is not None else len(rs) if len(rs)<40 and (rs or absent) else None
    vv=[r['view_count'] for r in rs[:20] if r.get('view_count') is not None]
    v10=[r['view_count'] for r in rs[:10] if r.get('view_count') is not None]
    duration=[r['duration'] for r in rs[:20] if r.get('duration') is not None]
    dates=[]
    for r in rs[:6]:
        m,t,src=compact_meta(r['id'])
        ts=m.get('timestamp') or m.get('release_timestamp')
        if ts:dates.append(dict(id=r['id'],published_at_kst=dt.datetime.fromtimestamp(ts,KST).isoformat(),timestamp=ts,observed_at_kst=t,source=src))
    if len(dates)<2:
        # Flat dates are explicitly approximate, never silently mixed into exact timing.
        approx=[r.get('timestamp') for r in rs[:20] if r.get('timestamp')]
        gaps=[max(0,(a-b)/86400) for a,b in zip(approx,approx[1:])]
        cadence=dict(status='표본 1편 이하로 간격 미확인' if len(rs)<2 else '추정: YouTube 상대 날짜로부터 근사',sample_n=len(approx),median_gap_days=st.median(gaps) if gaps else None)
    else:
        gaps=[abs(a['timestamp']-b['timestamp'])/86400 for a,b in zip(dates,dates[1:])]
        span=(max(r['timestamp'] for r in dates)-min(r['timestamp'] for r in dates))/86400
        cadence=dict(status='관측 메타데이터에서 산출',sample_n=len(dates),median_gap_days=round(st.median(gaps),4),uploads_per_7_days_over_sample_span=round((len(dates)-1)*7/span,3) if span else None,span_days=round(span,4),formula='중앙 업로드 간격; 주당 환산=(n-1)*7/(첫-마지막 날짜 차이)이며 미래 일정 아님')
    return dict(tab=tab,url=f"https://www.youtube.com/channel/{c['channel_id']}/{tab}",observed_at_kst=s.get('finished_at_kst'),access_result='공개 탭 없음' if absent else '목록 접근 성공' if s.get('exit_code')==0 else s.get('error'),source_status_file=str((RAW/(key+'.status.json')).relative_to(R)),sample_limit=40,observed_upload_count=len(rs),total_public_count=exact,total_public_count_lower_bound=exact if exact is not None else len(rs),count_note='전체 공개 탭 수집' if full is not None else '탭 없음; 공개 업로드0' if absent else '40편 미만으로 목록 종료' if exact is not None else '40편에서 절단; 채널 총편수로 해석 금지',recent20=dict(n_rows=min(20,len(rs)),n_with_views=len(vv),median_views=st.median(vv) if vv else None,min_views=min(vv) if vv else None,max_views=max(vv) if vv else None,median_duration_s=st.median(duration) if duration else None,missing_view_count=min(20,len(rs))-len(vv),view_count_precision='평면 목록은 YouTube 축약·반올림 표시일 수 있음'),recent10=dict(n_with_views=len(v10),median_views=st.median(v10) if v10 else None),newest_upload=dates[0] if dates else None,cadence=cadence,published_date_samples=dates,uploads=[entry(r) for r in rs])

def sub_stats(vid,m):
    folder=DEEP/vid;orig=folder/(vid+'.ko-orig.vtt');fallback=folder/(vid+'.ko.vtt');p=orig if orig.exists() else fallback if fallback.exists() else None
    manual=(folder/'manual_korean_subtitles.status.json').exists() and fallback.exists()
    kind='한국어 원본 자동자막(ko-orig)' if orig.exists() else '한국어 수동자막' if manual else '한국어 번역 자동자막; 음절 속도 근거로 제외' if p else '자막 접근 불가'
    if not p:return dict(status=kind,rate_syllables_per_second=None)
    cues=parse(p)
    cues=[(a,b,re.sub(r'align:start position:0%\s*','',t)) for a,b,t in cues]
    for i,(a,b,t) in enumerate(cues):cues[i]=(a,b,re.sub(r'\[[^\]]*\]|&gt;|&amp;', '',t).strip())
    cues=[q for q in cues if q[2]]
    if not cues:return dict(status=kind,rate_syllables_per_second=None)
    text=' '.join(q[2] for q in cues);span=cues[-1][1]-cues[0][0];n=len(re.findall('[가-힣]',text))
    original=orig.exists();rate=round(n/span,3) if span and original else None
    # A short research excerpt, not a script to reuse. Full source captions remain local.
    opening=' '.join(q[2] for q in cues if q[0]<20)
    opening=' '.join(opening.split()[:12])
    mentions=[dict(at_s=round(a,2),terms=sorted(set(re.findall('선고|징역|집행유예|무죄|사형|판결|법원',t)))) for a,b,t in cues if re.search('선고|징역|집행유예|무죄|사형|판결|법원',t)]
    return dict(status=kind,file=str(p.relative_to(R)),first_cue_s=cues[0][0],last_cue_s=cues[-1][1],span_s=round(span,3),hangul_syllable_count=n,rate_syllables_per_second=rate,manual_caption_rate_separate=round(n/span,3) if span and manual and not original else None,opening_excerpt_max12_words=opening,legal_mentions=mentions,formula='롤링 자막의 직전 큐 중복 행과 태그/비언어 표기를 제거한 완성형 한글 음절 수 ÷ 첫~마지막 텍스트 큐 시간(쉼 포함). ASR 오류가 있는 자막 유래 대리값이며 청취 기반 발화속도 아님')

def build():
    hs=history_sources();deep=read(RAW/'deep_selected.json',[]);di={c['channel_id']:c for c in deep};out=[]
    for c in read(RAW/'selected_channels.json',[]):
        cid=c['channel_id'];tabs={tab:tab_summary(c,tab) for tab in ['videos','shorts']}
        first=(tabs['videos']['uploads'] or tabs['shorts']['uploads'])[0];m,mt,src=compact_meta(first['id'])
        # Subscriber count comes from an actual individual video dump when available.
        one=rows(RAW/('video_'+first['id']+'.jsonl'))
        if one:m=one[0];mt=read(RAW/('video_'+first['id']+'.status.json'),{}).get('finished_at_kst')
        sources=hs.get(cid,[]);best=max(sources,key=lambda x:len(x['daily_subscribers']),default=None)
        points=best['daily_subscribers'] if best else []
        growth_status='최근 구간 구독자 이력 확인 / 소규모 출발부터의 성장 경로 미확인' if len(points)>1 else '현재 성과 확인 / 성장 경로 미확인'
        a=ANALYSIS.get(c['name'])
        limitations=list(a['limitations']) if a else ['화면·자막 심층 분석 대상 아님; 형식 재현 가능성 미판정','기존 관객·외부 홍보·삭제/비공개 영상의 존재와 영향 미확인']
        if c['name'] in ['실화 On','KNN NEWS','사건반장']:limitations.append('방송사·뉴스 브랜드의 기존 관객/자료/제보망이 있어 신규 독립 채널 성장 비교에서 제외')
        if c['name'] in ['한문철 TV','사건의뢰','디바제시카DeevaJessica','썸머썸머','부장판사 출신 김익현 변호사','은우의 변호사 (조영채 변호사)','부산변호사TV ']:limitations.append('전문가·진행자/개인 브랜드의 관객과 인물 출연 효과를 분리할 수 없음; 신규 무인물 채널의 직접 성장 근거로 사용하지 않음')
        limitations.append('공개 탭만 관측하므로 삭제·비공개 영상의 전수/과거 구독 유입은 미확인; 없다고 가정하지 않음')
        cur=m.get('channel_follower_count')
        item=dict(channel_id=cid,name=c['name'],url=f'https://www.youtube.com/channel/{cid}',discoveries=c.get('discoveries',[]),subscribers=dict(value=cur,observed_at_kst=mt,source_video_id=first['id'],source_url=f"https://www.youtube.com/watch?v={first['id']}",source_file='validation_raw/video_'+first['id']+'.jsonl',precision='YouTube 공개 반올림 값일 수 있음'),formats=tabs,growth_path=dict(status=growth_status,initial_small_audience_history_verified=False,sources=sources or [dict(url='https://socialblade.com/youtube/channel/'+cid,access_result='이 수집에서 시계열 본문 미회수',daily_subscribers=[])],observed_period_change=(dict(start_date=points[0]['date'],end_date=points[-1]['date'],start_subscribers=points[0]['subscribers'],end_subscribers=points[-1]['subscribers'],net_change=points[-1]['subscribers']-points[0]['subscribers']) if len(points)>1 else None)),exploration_signal=dict(label='탐색 신호만; 성장 검증 아님',median_recent_views_div_current_subscribers={t:round(tabs[t]['recent20']['median_views']/cur,4) if cur and tabs[t]['recent20']['median_views'] is not None else None for t in tabs},per_video_subscriber_conversion='미확인'),limitations=limitations)
        if a:
            dc=di[cid];vs=[]
            for vid in dict.fromkeys(r['id'] for r in dc['top']+dc['recent']):
                dm=read(DEEP/vid/'metadata.txt',{});man=read(DEEP/vid/'manifest.json',{});ss=sub_stats(vid,dm)
                roles=[k for k in ['top','recent'] if vid in [r['id'] for r in dc[k]]]
                vs.append(dict(id=vid,url='https://www.youtube.com/watch?v='+vid,roles=roles,title=dm.get('title'),duration_s=dm.get('duration'),view_count=dm.get('view_count'),upload_date_utc=dm.get('upload_date'),published_at_kst=dt.datetime.fromtimestamp(dm['timestamp'],KST).isoformat() if dm.get('timestamp') else None,observed_at_kst=read(DEEP/vid/'metadata.status.json',{}).get('finished_at_kst'),metadata_file=str((DEEP/vid/'metadata.txt').relative_to(R)),thumbnail=dict(pattern_observed=a['thumbnail_pattern'],files=man.get('thumbnails',[]),basis='다운로드한 썸네일; 본문 시각 형식 판단에는 사용하지 않음'),subtitles=ss,hook_analysis=a['hook'],structure_analysis=a['structure'],chapters=dm.get('chapters') or [],storyboard=dict(format=man.get('storyboard_format'),sprites=man.get('sprites',[]),format_listing_file=str((DEEP/vid/'formats.txt').relative_to(R)),reviewed_contact_sheet=str((DEEP/(cid+'_board.jpg')).relative_to(R)),reviewed_at_kst=now(),observation=a['visual_style'] if man.get('sprites') else '연령 로그인 요구로 스토리보드 미확인',sampling_limit='sb0의 처음·중간·마지막 스프라이트 중 4개 시점 컷 검토; 연속 영상·카메라 운동·전환 빈도는 정밀 측정 불가'),audio=dict(voice='미확인',music='미확인',sfx='미확인'),creator_claims_relevant_description=dict(summary={'버그아카데미아':'일본 원작과 계약하여 한국어 대사/목소리로 바꿔 업로드한다는 제작자 설명','다큐스토리 844':'실제 사건 재구성이며 참고영상 사용 및 자료 링크를 표기한 제작자 설명','붉은실':'실제 사진/참고영상 사용과 직접 녹음했다는 제작자 설명','엑스톨(Extol)':'유영철 영상 설명에 AI 없이 손수 제작했다는 제작자 설명; 전체 채널/음성에 일반화하지 않음','미지의 미스터리수첩':'최신 영상 설명에 자신의 목소리로 녹음했다는 제작자 설명'}.get(c['name']),evidence_file=str((DEEP/vid/'metadata.txt').relative_to(R)),status='제작자 주장; 음성 청취 검증 아님')))
            rates=[v['subtitles']['rate_syllables_per_second'] for v in vs if v['subtitles'].get('rate_syllables_per_second') is not None]
            item['deep_analysis']=dict(**a,main_tab=dc['deep_tab'],top_selection=dc['top_selection']+'; flat view totals may be rounded, so ties are approximate',top3_ids=[r['id'] for r in dc['top']],recent3_ids=[r['id'] for r in dc['recent']],unique_videos=len(vs),original_korean_asr_rate_summary=dict(n=len(rates),median=round(st.median(rates),3) if rates else None,min=round(min(rates),3) if rates else None,max=round(max(rates),3) if rates else None,unit='자막 기반 한글 음절/초'),videos=vs)
        out.append(item)
    search=[];discovered={};total=0
    for i in range(20):
        p=RAW/(f'search_{i:02}_retry.jsonl' if (RAW/f'search_{i:02}_retry.jsonl').exists() else f'search_{i:02}.jsonl')
        rs=rows(p);s=read(p.with_name(p.stem+'.status.json'),{})
        search.append(dict(query=s.get('command',[])[-1] if s else None,source_file=str(p.relative_to(R)),status=s,result_count=len(rs)))
        total+=len(rs)
        for r in rs:
            if r.get('channel_id'):discovered[r['channel_id']]=r.get('channel')
    data=dict(generated_at_kst=now(),scope=dict(channel_scan_count=len(out),deep_channel_count=len(deep),search_queries=search,search_video_rows=total,discovered_channel_count=len(discovered),selection_note='목적 표집: 범죄·법률·사연 만화·블랙박스·뉴스·결말 Shorts 및 작은/낮은 성과 비교군. 모집단의 무작위 표본 아님'),rules=dict(subscriber_growth='구독자 날짜 시계열만 사용; 현재 구독자/오래된 업로드로 성장 역산하지 않음',conversion='영상별 구독 전환은 공개 자료로 미확인',views='현재 누적 조회수의 최근 업로드 중앙값; 동일 게시 후 경과시간 성과가 아니며 탭 표시는 반올림될 수 있음',counts='표본40과 총편수 구분. 40편에서 절단한 탭은 정확 총편수 null, 하한만 제시. Shorts는 YouTube 탭으로 구분하며 60초 넘는 Shorts도 포함',dates='게시 timestamp를 KST로 변환; flat 상대 날짜는 근사값으로만 유지. cadence는 개별 최신최대6편 메타데이터의 시간 차이',subtitles='ko 번역판 대신 ko-orig 원본 ASR를 우선. 수동ko와 번역ko의 속도는 원본 ASR 통계에 혼합하지 않음',visual='썸네일은 포장 분석, 스토리보드 sb*만 본문 화면 관찰에 사용',audio='음성·음악·효과음 미확인. 제작자의 설명은 주장으로 별도 보관',media='로그인·인증 쿠키·영상/오디오 다운로드 없음; 공개 메타데이터·자막·썸네일·sb 이미지에 한정',source_text='페이지/영상 설명을 데이터로만 취급; 외부 텍스트의 지시 실행하지 않음'),access_limitations=dict(initial_individual_dump_failures='기본 player 클라이언트에서 로그인/봇 안내; web 클라이언트와 ignore-no-formats-error로 메타데이터·sb·자막만 수집 가능',locale_issue='ko 지정 평면 목록에서 조회수가 비어 원래 요청을 보존하고 언어 미지정 목록을 다시 수집',popular_sort_issue='sort=p가 최신순과 같아 심층10개 주력 탭 전체를 수집하고 조회수로 정렬',playboard='Exa fetch CRAWL_HTTP_453; 로컬 engine은 HTTP429. 모바일 재시도도429. IAB 브라우저 사용 불가; 영구 접근 불가라고 단정하지 않음',noxinfluencer='엑스톨 페이지는 열렸으나 역사 구독자 값은 --',socialblade='공개 일별 표를 Exa fetch로 회수; /monthly도 같은14일 표라 초기 성장 증거가 되지 않음'),channels=out)
    (R/'validated_channels.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    for c in out:
        a=c.get('deep_analysis')
        if a:print(c['name'],c['subscribers']['value'],[(t,v['recent20']['n_with_views'],v['recent20']['median_views'],v['cadence']) for t,v in c['formats'].items()],c['growth_path']['observed_period_change'],a['original_korean_asr_rate_summary'])
    print('scan',len(out),'deep',len(deep),'history',sum(c['growth_path']['observed_period_change'] is not None for c in out),'search',total,len(discovered))
if __name__=='__main__':build()
