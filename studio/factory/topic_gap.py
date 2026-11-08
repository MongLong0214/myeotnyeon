"""Supplementary sentence comparisons; observations and editorial order stay separate."""
import hashlib
import html
import re
import time
import urllib.parse

ANGER_TERMS = ('솜방망이', '유전무죄', '무전유죄', '봐주기', '너무 가볍', '형량이 낮', '형량이 적')
NEUTRAL_TERMS = ('감형', '집행유예', '무죄')


def demand_gap(outcome, demand):
    """Acquittal/fine is never coerced to zero custodial months."""
    a = demand.get('custody_months')
    b = outcome.get('custody_months')
    delta = a-b if a is not None and b is not None and not outcome.get('acquittal') else None
    return dict(custody_term_difference_months=delta,
                comparison=demand.get('comparison'),
                note='Nominal terms only. Suspension, changed guilty counts and prosecution demands are not equivalent conditions; this difference does not prove an unjust judgment.')


def headline_reaction(d, t):
    news = d.get('naver', {}).get('search', {}).get('news', {})
    data = news.get('data')
    if data is None:
        return dict(sample_n=None, anger_headlines=None, share=None, reason='No accessible news search result sample.')
    kept = {}; rows = []
    for item in data.get('items', []):
        title = html.unescape(re.sub('<[^>]+>', '', item['title']))
        if not t.matches(title, d['candidate']):
            continue
        url = item.get('originallink') or item['link']
        canonical = urllib.parse.urlsplit(url)._replace(query='', fragment='').geturl()
        if canonical in kept:
            continue
        kept[canonical] = True
        rows.append(dict(url=url, title=title, published=item.get('pubDate'),
                         anger_terms=[x for x in ANGER_TERMS if x in title],
                         outcome_terms=[x for x in NEUTRAL_TERMS if x in title]))
    n = len(rows); count = sum(bool(x['anger_terms']) for x in rows) if n else None
    return dict(source_url=news.get('url'), query=news.get('query'), observed_at=news.get('observed_at'),
                sample_n=n, anger_headlines=count, share=count/n if n else None, articles=rows,
                lexicon=list(ANGER_TERMS),
                scope='Literal words in case-title-matched first ≤100 search headlines, not comments or public opinion. Some headlines may precede the compared judgment; these are not necessarily reactions to that outcome. Neutral outcome terms are counted separately. Syndicated reports can share wording.',
                reason=None if n else 'No matching headlines; anger frequency missing, not zero.')


def sample_comments(d, t, limit=40):
    """One post-judgment original per case; retain counts and hashes, not insults/names."""
    gap = d.get('sentence_outrage_gap', {})
    date = (gap.get('outcome') or {}).get('judgment_date')
    possible = []
    for v in (d.get('youtube') or {}).get('videos', []):
        posted = v.get('upload_date')
        if date and posted and posted >= date.replace('-', '') and re.search('선고|징역|확정|집행유예|무죄|감형|벌금', v.get('title', '')):
            possible.append(v)
    if not possible:
        return dict(sample_n=None, anger_comments=None, share=None,
                    reason='No retained original with a verified posting date on/after the compared judgment and a judgment-related title. Pre-judgment comments not attributed to the sentence.')
    v = max(possible, key=lambda x: x.get('view_count') or 0)
    cache = t.OUT/'comment_samples'/(v['id']+'.json')
    if cache.exists():
        return t.read(cache)
    args = [v['url'], '--skip-download', '--ignore-no-formats-error', '--write-comments',
            '--extractor-args', 'youtube:player_skip=js,configs;player_client=web;comment_sort=top;max_comments='+str(limit)+','+str(limit)+',0,0', '-J']
    raw = t.yt(args, timeout=100)
    data = raw.get('data') or {}; comments = data.get('comments')
    rows = []
    if comments:
        for c in comments[:limit]:
            body = c.get('text') or ''
            rows.append(dict(url=v['url']+'&lc='+str(c.get('id', '')),
                             text_sha256=hashlib.sha256(body.encode()).hexdigest(),
                             anger_terms=[x for x in ANGER_TERMS if x in body]))
    n = len(rows) if rows else None
    result = dict(url=v['url'], query=d['candidate']['query'], observed_at=raw['observed_at'],
                  command=raw['command'], requested_limit=limit, sort='top', sample_n=n,
                  total_comment_count=v.get('comment_count'),
                  anger_comments=sum(bool(x['anger_terms']) for x in rows) if n is not None else None,
                  share=sum(bool(x['anger_terms']) for x in rows)/n if n else None,
                  comments=rows or None, lexicon=list(ANGER_TERMS),
                  reason=None if n else 'No public comments returned; possibly disabled or extractor blocked. No count or sentiment inferred.',
                  scope='Non-random top-level top-comment sample; one original after the judgment, not population opinion or proof of severity. Text/authors not retained.')
    t.write(cache, result)
    time.sleep(2)
    return result


def update(t, comments=False):
    catalog = t.read(t.OUT/'sentence_gap_facts.json')
    facts = catalog['cases']
    manifest = t.read(t.OUT/'candidates.json')
    for c in manifest:
        p = t.OUT/(c['slug']+'.json')
        if not p.exists():
            continue
        d = t.read(p); f = facts.get(c['slug']); previous = d.get('sentence_outrage_gap', {})
        gap = dict(reference_date=catalog['reference_date'], observed_at=t.now(),
                   evidence_status='reviewed_reported_judgment' if f else 'not_yet_extracted',
                   severity=dict(deaths=None, injuries=None, damage_krw=None, damage_text=None,
                                 cruelty=None, repeat_offending=None, sources=None),
                   outcome=dict(judgment_date=None, stage=c.get('trial_stage'), finality=None,
                                sentence_text=c.get('sentence'), custody_months=None, suspended_months=None,
                                fine_krw=None, acquittal=None, guilty_counts=None, acquitted_counts=None, sources=None),
                   demand=dict(custody_months=None, text=None, sources=None, comparison=None),
                   main_reasons=None, confirmed_key_facts=None, sources=None,
                   political_sensitive=None, public_figure=None, separate_review_reason=None,
                   supplementary_rank=None,
                   must_not_imply=None,
                   missing=['죄명별 인정 사실·양형 이유의 추가 추출', '사망·부상·피해액·잔혹성·재범 중 출처로 확인되지 않은 항목'])
        gap['must_not_imply']='판결로 확인하지 않은 동기·유착·매수·정치적 개입을 암시하지 않음. 기존 제외 사유도 유지.'
        if f:
            for k, v in f.items():
                if k in ('severity', 'outcome', 'demand'):
                    gap[k].update(v)
                else:
                    gap[k] = v
            for k in ('severity', 'outcome', 'demand'):
                gap[k]['sources'] = gap[k].get('sources') or f['sources']
        gap['demand_sentence_gap'] = demand_gap(gap['outcome'], gap['demand'])
        gap['reaction'] = dict(headlines=headline_reaction(d, t),
                               youtube_comment_totals=[dict(url=v['url'], count=v.get('comment_count'),
                                   observed_at=v.get('metadata_observed_at'), query=(d.get('youtube') or {}).get('query'),
                                   posted=v.get('upload_date')) for v in (d.get('youtube') or {}).get('videos', [])],
                               news_public_counters=d.get('independent_signals') or None,
                               youtube_comment_sample=(previous.get('reaction') or {}).get('youtube_comment_sample'))
        d['sentence_outrage_gap'] = gap
        if comments and f and not (gap['reaction'].get('youtube_comment_sample') or {}).get('sample_n'):
            gap['reaction']['youtube_comment_sample'] = sample_comments(d, t)
        if not gap['reaction'].get('youtube_comment_sample'):
            gap['reaction']['youtube_comment_sample']=dict(sample_n=None,anger_comments=None,share=None,reason='Comment sample not collected.')
        missing = gap.setdefault('missing', [])
        if gap['outcome']['finality'] is None:missing.append('확정 여부')
        if gap['demand']['custody_months'] is None:missing.append('검찰 구형의 동일 피고인·죄명별 수치')
        if gap['reaction']['youtube_comment_sample']['sample_n'] is None:missing.append('선고 후 원본 영상의 경벌 반응 댓글 표본')
        if not gap['reaction']['news_public_counters']:missing.append('뉴스 원문 공개 댓글·반응 수')
        gap['missing']=list(dict.fromkeys(missing))
        t.save_fields(p,dict(sentence_outrage_gap=gap))


def render(t):
    """Append at rank generation time, so rebuilding cannot silently remove the supplement."""
    catalog = t.read(t.OUT/'sentence_gap_facts.json')
    docs={c['slug']:t.read(t.OUT/(c['slug']+'.json')) for c in t.read(t.OUT/'candidates.json') if (t.OUT/(c['slug']+'.json')).exists()}
    esc=lambda s:str(s if s is not None else '미측정').replace('|','/').replace('\n',' ')
    lines=['','## Light-sentence outrage TOP 15','',
           '보충 Shorts 비교표 · 기준일 '+catalog['reference_date']+'. **경벌 여부를 판정한 점수표가 아니라, 인정된 피해·구형과 선고의 차이·선고 이유·수요 증거를 함께 놓은 편집 우선순위다.** 기존 수요 점수는 참고 열이며 아래 순서는 편집 판단이다. 피해와 죄명이 다른 사건의 형량은 직접 등가 비교할 수 없다. 분노 강도를 범죄 중대성으로 환산하지 않았다.','',
           '표의 날짜는 확인된 재판·보도 기준이다. 이후 심급을 확보하지 못한 경우 해당 심급까지만 답한다. 확정 여부 결측을 최종 결과로 바꾸지 않는다. 무죄는 0년형이 아니므로 형량 차이 계산과 경벌 TOP에서 분리한다.','',
           '|순위·후보 / 기준일·민감성|심급·유죄/무죄·인정 사실(중대성)|선고·구형 차이 / 주된 이유|수요·반응 증거|사실 경계: 암시 금지|결측|',
           '|---|---|---|---|---|---|']
    eligible=[]; pending=[]
    for slug in catalog['priority_order']:
        d=docs[slug];c=d['candidate'];g=d['sentence_outrage_gap']
        if c.get('used_as') or c.get('hard_exclusion') or g['outcome'].get('acquittal'):continue
        kinds=d.get('demand_signal_kinds',[])
        if len(kinds)>=2 and g.get('confirmed_key_facts') and c.get('channel_fit') and not g.get('separate_review_reason'):
            eligible.append(d)
        else:pending.append(d)
    def row(d, position):
        c=d['candidate'];g=d['sentence_outrage_gap'];o=g['outcome'];r=g['reaction'];h=r['headlines'];sample=r['youtube_comment_sample']
        yt=(d.get('youtube') or {}).get('summary') or {};di=d.get('demand_inputs') or {};ss=d.get('search_summary') or {}
        count=[x['count'] for x in r['youtube_comment_totals'] if x['count'] is not None]
        num=lambda x:f'{x:,.2f}' if isinstance(x,float) else f'{x:,}' if isinstance(x,int) else '미측정'
        kinds={'youtube_performance':'YouTube 성과','naver_search_volume':'네이버 검색량','public_community_or_news_reaction':'뉴스·커뮤니티 반응'}
        evid=f"기존 수요 점수 {num(d.get('score',{}).get('value'))}; 원본 표본 조회 합 {num(yt.get('view_sum'))}회; 채널 대비 중앙 {num(di.get('relative_performance_median'))}배; 검색 정점/기준 {num(ss.get('peak_over_anchor_median'))}배(반환 {ss.get('returned_days')}일); 수요 종류 {', '.join(kinds[x] for x in d.get('demand_signal_kinds',[]))}"
        evid+=f"; 영상 댓글수 표본 합 {sum(count) if count else None}(선고 이전 포함); 선고 후 댓글 경벌어 {sample.get('anger_comments')}/{sample.get('sample_n')}; 기사 제목 경벌어 {h.get('anger_headlines')}/{h.get('sample_n')}"
        source=' · '.join(f"[근거{j+1}]({s['url']})" for j,s in enumerate(g.get('sources') or []))
        label=f"{position}. [{c['name']}]({c['slug']}.json) · 자료기준 {g.get('evidence_through')} / 조사 {g['reference_date']}"
        if g.get('political_sensitive'):label+=' · **정치 민감**'
        elif g.get('public_figure'):label+=' · 공인 본인 사건'
        if c.get('running_lane'):label+=' · 제작 중 '+c['running_lane']
        label+='; 첫 장면·형량 질문: '+c.get('channel_fit','미추출')
        comparison=(g['demand'].get('text') or '구형 미확보')+' → '+(o.get('sentence_text') or '미확보')
        delta=g['demand_sentence_gap']['custody_term_difference_months']
        comparison+=f"; 명목 징역기간 차이 {delta}개월" if delta is not None else '; 개월 환산 차이 미측정'
        comparison+='; 비교조건 '+(g['demand'].get('comparison') or '구형·선고를 같은 죄명으로 비교할 자료 부족')
        comparison+='; 이유 '+(' / '.join(g.get('main_reasons') or []) or '미확보')
        finality='확정 확인' if o.get('finality') is True else '확정 미확인'
        facts=(o.get('stage') or '심급 미확보')+'; '+finality+'; 적용·유죄 '+str(o.get('guilty_counts'))+'; 무죄 '+str(o.get('acquitted_counts'))+'; '+' / '.join(g.get('confirmed_key_facts') or [])+' '+source
        miss=list(g['missing'])+list(d.get('missing',[]))
        if g.get('separate_review_reason'):miss.append('별도 검토: '+g['separate_review_reason'])
        return '|'+ '|'.join(esc(x) for x in [label,facts,comparison,evid,g['must_not_imply'],' / '.join(dict.fromkeys(miss)) or '없음'])+'|'
    for i,d in enumerate(eligible[:15],1):
        d['sentence_outrage_gap']['supplementary_rank']=i
        t.save_fields(t.OUT/(d['candidate']['slug']+'.json'),dict(sentence_outrage_gap=d['sentence_outrage_gap']))
        lines.append(row(d,i))
    lines+=['',f'독립 수요 2종과 사실 근거를 확인한 상대 후보 {len(eligible[:15])}건. 표본 댓글의 경벌 표현 수는 그 표본 안의 관측값이며 전체 국민의 태도나 재판의 부당성 증거가 아니다. 기사 제목의 경벌어 수도 기사 표현 빈도이며 선고 전 기사가 섞일 수 있다. 반응이 미측정이어도 피해를 약하다고 보지 않는다.','',
            '제목·썸네일·재연 공통 경계: 판결이 인정하지 않은 매수·유착·청탁을 질문으로도 암시하지 않는다. 특정 사건에 유전무죄를 원인으로 붙이지 않는다. 창작 대사, 돈 전달·밀실 거래 장면을 만들지 않는다. 피해자는 식별하지 않고 공인의 가족·직원·지인의 사생활을 끌어오지 않는다. 동일 기준을 모든 정당에 적용한다.','',
            '### 무죄·보강 후보: 형량 0년으로 취급하지 않음','',
            '|후보 / 기준일·민감성|심급·유죄/무죄·인정 사실|선고·비교 조건·이유|수요·반응|암시 금지|결측|','|---|---|---|---|---|---|']
    extras=list(dict.fromkeys(catalog.get('comparison_only',[])+[d['candidate']['slug'] for d in pending]))
    for slug in extras:
        if slug in docs:lines.append(row(docs[slug],'비교'))
    lines+=['','### 후보별 기준일·사실 경계 (전체 조사 목록)','',
            '미추출은 사실이 없다는 뜻이 아니다. 아래 결측 후보를 보충 TOP 선정으로 취급하지 않는다. 원본 기사·댓글에 등장하는 의혹도 법원 인정 사실로 승격하지 않는다. 각 JSON에는 사망·부상·피해액·반복성·선고·구형·이유·반응의 출처와 결측이 따로 있다.','',
            '|후보|기준일·심급|확인한 핵심 사실|암시하면 안 되는 주장·검토 사유|','|---|---|---|---|']
    for slug,d in docs.items():
        g=d.get('sentence_outrage_gap',{});c=d['candidate'];o=g.get('outcome',{})
        facts=' / '.join(g.get('confirmed_key_facts') or []) or '인정 사실 미추출; 기존 선고 정보는 원자료 참조'
        boundary=g.get('must_not_imply') or '미추출 사실·동기 추정 금지'
        if g.get('separate_review_reason'):boundary+='; 별도 검토: '+g['separate_review_reason']
        lines.append('|'+ '|'.join(esc(x) for x in [f"[{c['name']}]({slug}.json)",str(g.get('reference_date'))+'; '+str(o.get('stage')),facts,boundary])+'|')
    lines+=['','보충 재실행: `python3 factory/topic_score.py gap` (로컬 저장 증거 재계산), `python3 factory/topic_score.py gap --comments` (허용된 공개 댓글 최대 40개 표본 시도), 이후 `python3 factory/topic_score.py rank`. 새 보충 후보는 기존 TOP·교정 비교집단과 분리해 원래 순위를 유지한다. 각 영상의 경과일·현재 구독자·동일 채널 비교 표본·배수는 JSON `youtube.videos`에 보존한다.','']
    return lines
