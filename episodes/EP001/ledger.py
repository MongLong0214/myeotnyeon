#!/usr/bin/env python3
"""Source log + claim log for EP001.

Every source points at an archived copy (research/raw/<id>.*) with its sha256.
Claim status: VERIFIED_OFFICIAL (statute / guideline / official statistics text),
VERIFIED_SECONDARY (judgment content as quoted in press — the judgment itself was not
obtained), UNKNOWN (reported on screen as not established). Writes source_log.csv,
claim_log.csv and ledger.json.
"""
import json, csv, pathlib, hashlib

HERE = pathlib.Path(__file__).parent
RAW = HERE.parents[1] / 'research' / 'raw'
VERIFIED_AT = '2026-10-25'

# id: (archive id, title, url, date, type, official, note)
SOURCES = {
    "SRC01": ("LAWISSUE", "로이슈: 대구지법, 음주운전 신고하겠다는 피해자 차량으로 들이받아 집유·사회봉사", "http://www.lawissue.co.kr/view.php?ud=202308250944539749a8c8bf58f_12", "2023-08-25", "legal_media", False, "판결 내용을 가장 자세히 옮긴 보도 (사건번호·선고일·범죄사실·주장·판단·양형)"),
    "SRC02": ("YNA", "연합뉴스: 음주운전 신고하겠다고 막아서자 차로 친 20대 집유", "https://www.yna.co.kr/view/AKR20230818120600053", "2023-08-20", "news", False, "1보"),
    "SRC03": ("KYONGBUK", "경북일보: 음주운전 신고하겠다는 남성 차량으로 들이받은 20대 집유", "http://www.kyongbuk.co.kr/news/articleView.html?idxno=2139684", "2023-08-16", "news", False, "선고 당일 보도: 34일, 사회봉사, 공탁"),
    "SRC04": ("MBC", "MBC: 음주운전 막자 차로 쾅! 20대女, 법원 죄질 안 좋지만 초범이라", "https://imnews.imbc.com/news/2023/society/article/6516532_36126.html", "2023-08-21", "broadcast", False, "지하주차장·전치 약 5주로 표기"),
    "SRC05": ("A1-018", "로톡뉴스 (대구지방법원 2023고단202 판결문 참고 표기)", "https://lawtalknews.co.kr/article/G943M22VHU43", "2025-10-16", "legal_media", False, "약 34일 치료 일치"),
    "SRC06": ("SEGYE24", "세계일보: 두려운 마음에 범행한 점 참작… 집유에 시끌", "http://www.segye.com/newsView/20230824504605", "2023-08-24", "news", False, "논란 보도"),
    "SRC07": ("A2-002", "형법 제258조의2(특수상해)", "https://www.law.go.kr/LSW//lsSideInfoP.do?lsiSeq=290185&joNo=0258&joBrNo=02&docCls=jo", "2016-01-06", "statute", True, "본조신설 2016.1.6. 이후 변경 없음"),
    "SRC08": ("A2-005", "형법 제53조(정상참작감경)", "https://www.law.go.kr/LSW//lsSideInfoP.do?lsiSeq=290185&joNo=0053&joBrNo=00&docCls=jo", "2020-12-08", "statute", True, ""),
    "SRC09": ("A2-006", "형법 제55조(법률상의 감경)", "https://www.law.go.kr/LSW//lsSideInfoP.do?lsiSeq=290185&joNo=0055&joBrNo=00&docCls=jo", "2010-04-15", "statute", True, ""),
    "SRC10": ("A2-008", "형법 제62조(집행유예의 요건)", "https://www.law.go.kr/LSW//lsSideInfoP.do?lsiSeq=290185&joNo=0062&joBrNo=00&docCls=jo", "2016-01-06", "statute", True, ""),
    "SRC11": ("A2-009", "형법 제62조의2(보호관찰, 사회봉사·수강명령)", "https://www.law.go.kr/LSW//lsSideInfoP.do?lsiSeq=290185&joNo=0062&joBrNo=02&docCls=jo", "1995-12-29", "statute", True, ""),
    "SRC12": ("A2-010", "형법 제63조(집행유예의 실효)", "https://www.law.go.kr/LSW//lsSideInfoP.do?lsiSeq=290185&joNo=0063&joBrNo=00&docCls=jo", "2005-07-29", "statute", True, ""),
    "SRC13": ("A2-004", "형법 제51조(양형의 조건)", "https://www.law.go.kr/LSW//lsSideInfoP.do?lsiSeq=290185&joNo=0051&joBrNo=00&docCls=jo", "", "statute", True, ""),
    "SRC14": ("A2-088", "대법원 1984. 10. 23. 선고 84도2001 판결 (케이스노트 게재)", "https://casenote.kr/대법원/84도2001", "1984-10-23", "supreme_court", True, "자동차를 위험한 물건의 예로 듦"),
    "SRC15": ("A2-040", "양형위원회 폭력범죄 양형기준 (2022.6.1. 시행)", "https://sc.scourt.go.kr/sc/krsc/pdf/F18.Crimes_of_Violence(2022).pdf", "2022-06-01", "sentencing_guideline", True, "특수상해 유형1 형량범위·집행유예 기준"),
    "SRC16": ("A2-110", "양형위원회 2023 연간보고서", "https://sc.scourt.go.kr (2023 연간보고서 PDF, raw/A2-110.pdf)", "2024-04-26", "statistics", True, "2023.1.1.~12.31. 1심 선고 양형기준 적용사건 전수조사"),
    "SRC17": ("A2-016", "공탁법 제5조의2(형사공탁의 특례)", "https://www.law.go.kr/LSW//lsSideInfoP.do?lsiSeq=290669&joNo=0005&joBrNo=02&docCls=jo", "2022-12-09", "statute", True, "시행 2022.12.9."),
    "SRC18": ("A2-019", "법무부 보도자료: 형사소송법 일부개정법률 공포·시행 알림", "https://www.moj.go.kr/bbs/moj/159/588549/artclView.do", "2024-10-16", "official_guide", True, "제294조의5 신설, 공포 후 3개월 시행"),
    "SRC19": ("A2-050", "법무부: 형사소송법 일부개정법률안 입법예고 (기습공탁 정의)", "https://moj.go.kr/bbs/moj/157/583320/artclView.do", "2024-05-16", "official_guide", True, ""),
    "SRC20": ("A1-027", "보배드림 게시글: 커뮤니티를 뜨겁게 달구고있는 역대급 판결", "http://www.bobaedream.co.kr/view?code=strange&No=5859526", "2023-08-21", "community", False, "확산 경로 확인용, 사실 근거 아님"),
    "SRC22": ("A2-018", "로톡: 형사공탁 특례 제도 해설 (시행일 보강)", "https://www.lawtalk.co.kr/posts/68014", "", "commentary", False, "시행일 2022.12.9. 보강 자료"),
    "SRC23": ("A3-039", "이데일리: 아파트 주차장 입구 막고 항의한 주민 차로 친 50대…징역형 (대구지법 형사합의12부)", "https://n.news.naver.com/mnews/article/018/0005313822?sid=102", "2022-09-09", "news", False, "비교 사건: 신고 후 차를 가로막은 주민을 후진해 침, 전치 2주, 징역 8월·집유 2년"),
    "SRC24": ("A2-114", "네이트 자동차: 자동차 위법행위 신고하면 벌점 줄까? 포상은 받을까?", "https://view.nate.com/auto/view/311604/", "", "commentary", False, "음주운전 의심 차량 112 신고 요령"),
    "SRC25": ("A1-002", "위키트리: 음주운전 신고한 남자를 차로 들이받은 20대 여자… 그런데 판결이 좀 이상하다", "https://www.wikitree.co.kr/articles/879791", "2023-08-21", "portal", False, "커뮤니티 요약 재인용 — 소문 확인용, 사실 근거 아님"),
    "SRC26": ("A1-028", "클리앙 게시글: 각종 커뮤니티를 뜨겁게 달구고 있다는 역대급 판결.jpg", "https://www.clien.net/service/board/park/18263138", "2023-08-23", "community", False, "소문 확인용, 사실 근거 아님"),
    "SRC21": ("A1-017", "피앤피뉴스(고시위크) 변호사 칼럼", "https://www.gosiweek.com/article/1065577962958295", "2023-12-27", "legal_media", False, "항소 여부를 가정형으로 서술"),
}

# id: (type, text, sources, locator quote, status)
CLAIMS = {
    "F001": ("court_finding", "2022. 7. 28. 오전 3시 30분경, 대구 수성구의 주차장", ["SRC01", "SRC02"], "2022년 7월 28일 오전 3시 30분경 대구 수성구 한 건물 지상주차장에서", "VERIFIED_SECONDARY"),
    "F002": ("analysis", "장소는 개념 세트로 재구성 (실제 배치 아님)", [], "제작진 표기", "VERIFIED_SECONDARY"),
    "F003": ("court_finding", "B씨가 A씨를 음주운전으로 신고하겠다며 차량을 막아섬", ["SRC01"], "피해자 A(30대·남)가 피고인을 음주운전으로 신고하겠다고 하면서 피고인의 차량을 막아서자", "VERIFIED_SECONDARY"),
    "F004": ("court_finding", "A씨가 승용차로 B씨를 수회 밀어 넘어뜨림", ["SRC01"], "위험한 물건인 외제승용차로 피해자를 수회 밀어 넘어뜨리고", "VERIFIED_SECONDARY"),
    "F005": ("fact", "A씨 보도 당시 28세, B씨 30대(39세)", ["SRC02", "SRC03"], "A(28·여)씨 / B씨(39)", "VERIFIED_SECONDARY"),
    "F006": ("unknown", "두 사람의 이전 관계는 보도로 확인되지 않음", [], "검토한 보도 34건에 관계 언급 없음", "UNKNOWN"),
    "F007": ("fact", "지상 주차장(판결 기반 보도) / 지하 주차장(일부 보도)", ["SRC01", "SRC02", "SRC03", "SRC04"], "건물 지상주차장 (로이슈) / 지하주차장 (MBC, 경북일보)", "VERIFIED_SECONDARY"),
    "F008": ("court_finding", "후진했다가 다시 진행하며 1회 받아 넘어지게 함", ["SRC01"], "계속해서 차를 후진했다가 다시 진행하며 피해자를 1회 받아 넘어지게 했다", "VERIFIED_SECONDARY"),
    "F009": ("court_finding", "약 34일간 치료를 요하는 어깨 관절의 염좌 및 긴장 (일부 보도는 전치 5주)", ["SRC01", "SRC03", "SRC05"], "약 34일간의 치료를 요하는 어깨 관절의 염좌 및 긴장 등 상해", "VERIFIED_SECONDARY"),
    "F010": ("court_finding", "범죄사실이 녹화된 현장 CCTV 영상", ["SRC01"], "범죄사실이 고스란히 녹화된 현장 CCTV영상에 의하면", "VERIFIED_SECONDARY"),
    "F011": ("court_finding", "2022.7.29.~8.31. 및 2023.5.경까지 약침(어깨관절)·추나요법(경추·요추) 치료", ["SRC01"], "2022. 7. 29.부터 2022. 8. 31.까지 및 그로부터 2023. 5.경까지 약침(어깨관절), 추나요법(경추, 요추) 등 치료", "VERIFIED_SECONDARY"),
    "A001": ("party_claim", "피고인: 부주의한 운전 탓 / 피해자가 차량에 뛰어듦", ["SRC01", "SRC02"], "부주의한 운전 탓이라거나, 피해자가 피고인의 차량에 뛰어드는 바람에 발생했다고 진술", "VERIFIED_SECONDARY"),
    "A002": ("party_claim", "피고인·변호인: 들이받아 폭행한 사실은 있으나 상해 미발생 또는 인과관계 없음", ["SRC01"], "피해자에게 상해가 발생하지 않았거나, 피고인의 특수폭행행위와 상해의 결과 사이에 인과관계가 없다", "VERIFIED_SECONDARY"),
    "A003": ("party_claim", "공소사실: 승용차를 이용한 특수상해", ["SRC01"], "특수상해 혐의로 기소된 피고인", "VERIFIED_SECONDARY"),
    "E001": ("court_finding", "CCTV 영상에 의하면 상해 결과 발생, 특수상해 고의 인정", ["SRC01"], "상해의 결과가 발생했고, 특수상해 고의 또한 인정된다", "VERIFIED_SECONDARY"),
    "E002": ("court_finding", "유형력 정도가 가볍지 않고 진료기록이 피해자 진술과 어느 정도 일치 → 상해 인정", ["SRC01"], "진료기록의 객관적인 내용이 피해자의 증언 등 진술과 어느 정도 들어맞는 점", "VERIFIED_SECONDARY"),
    "J001": ("court_finding", "피해자가 일부러 차량 앞으로 뛰어든 것으로 보이지 않음", ["SRC01"], "피해자가 일부러 피고인의 차량 앞으로 뛰어든 것으로는 보이지 않는다", "VERIFIED_SECONDARY"),
    "J002": ("court_finding", "고의가 비교적 분명한데도 부주의·피해자 탓 → 진지한 반성 평가 불가", ["SRC01", "SRC03"], "진지한 반성을 하고 있다고 평가 할 수 없고", "VERIFIED_SECONDARY"),
    "J003": ("court_finding", "주문: 징역 8개월, 집행유예 2년, 사회봉사 120시간 (2023. 8. 16. 선고, 제1심)", ["SRC01", "SRC03", "SRC04"], "징역 8개월에 집행유예 2년을 선고했다(2023고단202) / 120시간의 사회봉사를 명했다", "VERIFIED_SECONDARY"),
    "J004": ("court_finding", "변론종결 후 형사공탁 300만 원, 피해자는 유리한 정상 참작에 반대", ["SRC01", "SRC03"], "변론종결 후 피해자에 대해 형사공탁(300만 원)을 했으나, 피해자는 이를 피고인에게 유리한 정상으로 참작함에 반대", "VERIFIED_SECONDARY"),
    "J005": ("court_finding", "불리한 정상: 진지한 반성 없음", ["SRC01"], "진지한 반성을 하고 있다고 평가 할 수 없고", "VERIFIED_SECONDARY"),
    "J006": ("court_finding", "짧은 시간이나 행위 횟수 거듭 → 죄질 불량, 피해자 엄벌 탄원, 죄책 가볍지 않음", ["SRC01", "SRC03"], "비록 짧은 시간 내이기는 하나 행위의 횟수가 거듭된 점 등에 비추어 죄질이 좋지 않는 점", "VERIFIED_SECONDARY"),
    "J007": ("court_finding", "유리한 정상: 특수폭행행위 자체 시인, 음주운전 신고에 대한 두려운 마음, 초범", ["SRC01", "SRC04"], "특수폭행행위 자체는 시인한 점, 음주운전 신고에 대한 두려운 마음에 이 사건 범행에 이를 것으로 보이는 점, 초범인 점", "VERIFIED_SECONDARY"),
    "L001": ("law", "형법 제258조의2 제1항: 1년 이상 10년 이하의 징역", ["SRC07"], "위험한 물건을 휴대하여 제257조 제1항 또는 제2항의 죄를 범한 때에는 1년 이상 10년 이하의 징역에 처한다", "VERIFIED_OFFICIAL"),
    "L002": ("law", "자동차도 위험한 물건에 해당할 수 있음 (판례)", ["SRC14"], "다른 목적으로 만들어진 칼·가위·유리병·각종 공구·자동차등은 물론", "VERIFIED_OFFICIAL"),
    "L003": ("law", "정상참작감경(제53조), 유기징역 감경은 형기의 2분의 1(제55조 제1항 제3호)", ["SRC08", "SRC09"], "유기징역 또는 유기금고를 감경할 때에는 그 형기의 2분의 1로 한다", "VERIFIED_OFFICIAL"),
    "L004": ("law", "제62조 제1항: 3년 이하 징역 선고 시 제51조 참작, 1년 이상 5년 이하 집행유예", ["SRC10"], "3년 이하의 징역이나 금고 또는 500만원 이하의 벌금의 형을 선고할 경우에 제51조의 사항을 참작하여", "VERIFIED_OFFICIAL"),
    "L005": ("law", "제63조 실효 / 제62조의2 사회봉사", ["SRC12", "SRC11"], "유예기간 중 고의로 범한 죄로 금고 이상의 실형을 선고받아 그 판결이 확정된 때에는 집행유예의 선고는 효력을 잃는다", "VERIFIED_OFFICIAL"),
    "L006": ("law", "제51조 양형의 조건 4가지", ["SRC13"], "1. 범인의 연령, 성행, 지능과 환경 2. 피해자에 대한 관계 3. 범행의 동기, 수단과 결과 4. 범행 후의 정황", "VERIFIED_OFFICIAL"),
    "L007": ("law", "형사공탁 특례 시행 2022. 12. 9.", ["SRC17", "SRC22"], "2022년 12월 9일부로 형사공탁 특례 제도가 시행되면서", "VERIFIED_SECONDARY"),
    "L008": ("law", "2024. 10. 16. 형사소송법 개정 공포: 선고 임박 공탁 시 피해자 의견 청취 의무 (제294조의5 신설, 공포 후 3개월 시행)", ["SRC18", "SRC19"], "판결 선고가 임박한 시점에 형사공탁을 하였을 때, 법원이 피해자의 의견을 의무적으로 청취하는 규정 신설(제294조의5 신설)", "VERIFIED_OFFICIAL"),
    "P001": ("fact", "수사를 거쳐 특수상해로 기소", ["SRC01"], "특수상해 혐의로 기소된 피고인", "VERIFIED_SECONDARY"),
    "P002": ("fact", "보도된 기소 죄명은 특수상해 하나, 음주 측정 결과는 보도되지 않음", ["SRC01", "SRC02", "SRC03", "SRC04", "SRC05"], "검토한 사건 보도 34건 전부에서 음주 측정·음주운전 기소 언급 없음 (research/agent1_summary.md)", "VERIFIED_SECONDARY"),
    "P003": ("unknown", "항소·확정 여부는 공개 보도로 확인되지 않음 (확인일 2026-10-25)", ["SRC21"], "검색 20회 이상, 항소심 보도 0건. 익명 커뮤니티 댓글의 항소기각 주장은 근거 없음으로 제외", "UNKNOWN"),
    "S001": ("meta", "대구지방법원 형사3단독, 2023고단202 특수상해, 2023. 8. 16. 선고 제1심", ["SRC01", "SRC03"], "2023년 8월 16일 음주운전으로 신고하겠다는 피해자를 차량으로 들이받아 특수상해 혐의로 기소된", "VERIFIED_SECONDARY"),
    "S002": ("meta", "확인일 2026. 10. 25.", [], "제작진 확인일", "VERIFIED_SECONDARY"),
    "S003": ("fact", "2023년 1심 특수상해(제1유형, 양형기준 적용) 3,550명 중 2,659명(74.9%) 집행유예", ["SRC16"], "891 25.1 2,659 74.9 3,550", "VERIFIED_OFFICIAL"),
    "U001": ("unknown", "실제 음주 여부·혈중알코올농도는 보도되지 않음", [], "P002와 동일 근거", "UNKNOWN"),
    "U002": ("unknown", "체포·구속 여부는 보도되지 않음", [], "검토한 보도 34건에 체포·구속 언급 없음", "UNKNOWN"),
    "AN001": ("analysis", "직관의 질문과 형법 제51조가 묻는 사정의 대비", ["SRC13"], "제작진 해설", "VERIFIED_SECONDARY"),
    "AN002": ("analysis", "선고형 8개월이 법정형 하한 1년보다 낮으므로 감경 적용으로 볼 수 있음 (적용 조문은 보도에 없음)", ["SRC07", "SRC08", "SRC09"], "제작진 해설", "VERIFIED_SECONDARY"),
    "AN003": ("analysis", "집행유예는 무죄가 아님 / 두려움 참작은 정당화가 아님", ["SRC10", "SRC01"], "제작진 해설", "VERIFIED_SECONDARY"),
    "V001": ("viral", "커뮤니티에서 '역대급 판결'로 확산 (보배드림 원글 2023. 8. 21., 확인일 조회 259,028)", ["SRC20", "SRC26"], "커뮤니티를 뜨겁게 달구고있는 역대급 판결", "VERIFIED_SECONDARY"),
    "M001": ("rumor", "커뮤니티 요약이 음주운전을 확정 사실처럼 서술 (보도된 죄명은 특수상해 하나)", ["SRC25"], "아파트 주차장에서 20대 여성이 음주 운전을 함", "VERIFIED_SECONDARY"),
    "M002": ("rumor", "커뮤니티에서 판결 이유를 '무서워서 그랬다니 봐줬다'로 축약", ["SRC26"], "신고할까봐 무서워서 범행한거 이해함, 집유 줄께", "VERIFIED_SECONDARY"),
    "C001": ("comparable", "대구지법 형사합의12부(2022. 9. 보도): 경찰 신고 후 차를 가로막은 주민을 후진해 친 50대, 전치 2주, 특수상해 징역 8월·집행유예 2년", ["SRC23"], "징역 8월에 집행유예 2년을", "VERIFIED_SECONDARY"),
    "T001": ("guide", "음주운전 의심 차량은 112 전화 신고, 위치·진행 방향·차량 번호 전달", ["SRC24"], "음주운전이 의심되는 차량의 위치, 진행 방향, 차량 번호 등을 정확히 전달하면 된다", "VERIFIED_SECONDARY"),
    "META": ("meta", "판결 기반 보도로 재구성, 판결문 원문 미확보, 공간 단순화", [], "제작진 고지", "VERIFIED_SECONDARY"),
    "BRAND": ("meta", "시리즈 브랜딩", [], "", "VERIFIED_SECONDARY"),
}


def sha(aid):
    for ext in ('pdf', 'html', 'txt'):
        f = RAW / f'{aid}.{ext}'
        if f.exists():
            return hashlib.sha256(f.read_bytes()).hexdigest(), f'research/raw/{f.name}'
    return '', ''


def main():
    script = json.load(open(HERE / 'script.json'))
    used = {}
    for c in script['cues']:
        for cid in c['claim_ids']:
            used.setdefault(cid, []).append(c['cue_id'])
    missing = sorted(set(used) - set(CLAIMS))
    with open(HERE / 'source_log.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['source_id', 'archive_id', 'title', 'url', 'date', 'type', 'official', 'verified_at', 'archive_file', 'sha256', 'note'])
        for sid, (aid, t, u, d, ty, off, note) in SOURCES.items():
            h, fp = sha(aid)
            w.writerow([sid, aid, t, u, d, ty, off, VERIFIED_AT, fp, h, note])
    with open(HERE / 'claim_log.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['claim_id', 'type', 'text', 'source_ids', 'locator_quote', 'status', 'used_in_cues'])
        for cid, (ty, t, srcs, loc, st) in CLAIMS.items():
            w.writerow([cid, ty, t, ';'.join(srcs), loc, st, ';'.join(used.get(cid, []))])
    json.dump(dict(sources=SOURCES, claims=CLAIMS, used=used), open(HERE / 'ledger.json', 'w'), ensure_ascii=False, indent=1)
    print('sources', len(SOURCES), 'claims', len(CLAIMS), 'claims used', len(used), 'undefined claims used:', missing)


if __name__ == '__main__':
    main()
