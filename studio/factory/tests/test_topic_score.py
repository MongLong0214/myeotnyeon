"""Offline checks for the research errors that would change topic selection."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('topic_score',Path(__file__).parents[1]/'topic_score.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
gap_spec=importlib.util.spec_from_file_location('topic_gap',Path(__file__).parents[1]/'topic_gap.py')
g=importlib.util.module_from_spec(gap_spec);gap_spec.loader.exec_module(g)

class TopicScoreTests(unittest.TestCase):
    def candidate(self):return dict(match_groups=[['야차룰'],['6년','광주']],negative_terms=[])
    def entry(self,id,title,channel='뉴스',views=100):
        return dict(id=id,title=title,channel=channel,view_count=views,url='https://www.youtube.com/watch?v='+id)

    def test_two_fight_death_cases_are_not_merged(self):
        self.assertTrue(t.matches('광주 야차룰 사망, 항소심도 6년',self.candidate()))
        self.assertFalse(t.matches('싸움 각서 야차룰 폭행치사 무죄',self.candidate()))

    def test_owned_video_and_sex_background_do_not_inflate_demand(self):
        entries=[self.entry('ozKvg2XFA0Y','야차룰 6년','타 채널',10000),
                 self.entry('sex','야차룰 6년 성폭력 전과',views=500),
                 self.entry('ok','야차룰 6년',views=30)]
        accepted,decisions=t.canonical_sample(entries,self.candidate())
        self.assertEqual([x['id'] for x in accepted],['ok'])
        self.assertEqual(decisions[0]['reason'],'own_channel')

    def test_same_broadcaster_subbrands_and_compilations_are_removed(self):
        entries=[self.entry('a','야차룰 6년','SBS 뉴스',300),
                 self.entry('b','야차룰 6년','VIDEOMUG',200),
                 self.entry('c','[에디터픽] 야차룰 6년','YTN',400)]
        accepted,_=t.canonical_sample(entries,self.candidate())
        self.assertEqual([x['id'] for x in accepted],['a'])

    def test_missing_is_not_zero_and_short_duration_is_not_short_format(self):
        s=t.summary([dict(view_count=None,duration=39)])
        self.assertIsNone(s['view_sum']);self.assertIsNone(s['contains_shorts'])
        self.assertEqual(t.summary([dict(view_count=0)])['view_sum'],0)

    def test_original_short_is_not_a_reupload_just_because_it_is_short(self):
        accepted,_=t.canonical_sample([self.entry('original','야차룰 6년 #shorts','KBS News')],self.candidate())
        self.assertEqual([x['id'] for x in accepted],['original'])

    def test_long_live_news_views_are_not_case_isolated_demand(self):
        e=self.entry('live','야차룰 6년 LIVE 풀영상','KBS News');e['duration']=4000
        accepted,rejected=t.canonical_sample([e],self.candidate())
        self.assertEqual(accepted,[])
        self.assertEqual(rejected[0]['reason'],'long_live_news_stream_case_viewing_not_isolated')

    def test_comment_character_limit_is_not_a_public_comment_count(self):
        count,_,_=t.public_counters('댓글 0 / 150 최신순 135 개의 댓글 전체보기')
        self.assertEqual(count,135)
        count,reactions,_=t.public_counters('댓글 보기 좋아요 0 화나요 3')
        self.assertIsNone(count);self.assertEqual(reactions,{'좋아요':0,'화나요':3})

    def test_tied_ranks_and_degenerate_correlation(self):
        self.assertEqual(t.rank_pct([1,2,2,4],2),0.5)
        self.assertIsNone(t.corr([1,1,1],[2,3,4]))
        self.assertAlmostEqual(t.corr([1,2,3],[2,4,6]),1)

    def test_unreadable_robots_fail_closed(self):
        h=t.PublicHTTP(delay=0);h.raw=lambda url:(503,b'unavailable',url)
        r=h.get('https://example.org/story')
        self.assertEqual(r['status'],'robots_disallowed_or_unavailable')
        self.assertIsNone(r['body'])

    def test_redirect_target_robots_are_checked(self):
        h=t.PublicHTTP(delay=0);calls=[]
        def raw(url):
            calls.append(url)
            if url=='https://a.example/robots.txt':return 200,b'User-agent: *\nAllow: /',url
            if url=='https://a.example/story':return 302,b'', 'https://b.example/private'
            if url=='https://b.example/robots.txt':return 200,b'User-agent: *\nDisallow: /private',url
            raise AssertionError('Disallowed target requested')
        h.raw=raw;r=h.get('https://a.example/story')
        self.assertEqual(r['status'],'robots_disallowed_or_unavailable')
        self.assertNotIn('https://b.example/private',calls)

class SentenceGapTests(unittest.TestCase):
    def test_acquittal_is_not_zero_custodial_months(self):
        r=g.demand_gap({'acquittal':True,'custody_months':None},{'custody_months':60})
        self.assertIsNone(r['custody_term_difference_months'])
        r=g.demand_gap({'acquittal':False,'custody_months':None,'fine_krw':10000000},{'custody_months':4})
        self.assertIsNone(r['custody_term_difference_months'])

    def test_missing_headlines_are_not_zero_anger(self):
        r=g.headline_reaction({'candidate':{}},t)
        self.assertIsNone(r['anger_headlines']);self.assertIsNone(r['sample_n'])
        r=g.headline_reaction({'candidate':{'match_groups':[['case']]},'naver':{'search':{'news':{'data':{'items':[]}}}}},t)
        self.assertIsNone(r['anger_headlines']);self.assertIsNone(r['share'])

    def test_neutral_outcomes_are_not_anger_and_duplicates_are_removed(self):
        news={'observed_at':'2026-11-06','query':'case','data':{'items':[
            {'title':'case 집행유예 감형','link':'https://a.example/1?ref=first'},
            {'title':'case 집행유예 감형','link':'https://a.example/1?ref=second'},
            {'title':'case 솜방망이 논란','link':'https://a.example/2'},
            {'title':'another 솜방망이','link':'https://a.example/3'}]}}
        r=g.headline_reaction({'candidate':{'match_groups':[['case']]},'naver':{'search':{'news':news}}},t)
        self.assertEqual(r['sample_n'],2);self.assertEqual(r['anger_headlines'],1)
        self.assertEqual(r['share'],0.5)

if __name__=='__main__':unittest.main()
