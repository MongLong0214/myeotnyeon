# 장편 후보 확장 — 2026-10-30

**잠정 TOP10·첫 제작 3편: 막가파 → 대전 국민은행 권총 강도살인 → 이태원 살인사건.** 연도 제한을 없애고 자극적인 실제 범행, 추적·수사의 전환, 확정판결까지 이어지는 장편성을 우선했다. Google Trends가 차단돼 아래는 검색 관심도까지 완성된 종합 순위가 아니다.

## 조사 상태와 기존 작업 보존

- 요청한 이름의 기존 두 파일은 작업폴더·인접 경로·/tmp에서 발견하지 못했다. 기존 `v3_candidates`, `viral_candidates`, `interest/2026-10-26`, Extol 분석은 변경하지 않았고, 이전 후보의 기록 전체를 JSON `carryover_candidates`에 보존했다. 파일 위치 확인은 비동기로 요청했다.
- Exa 검색 50회·요청 결과 250개 슬롯(중복 포함), 주요 페이지 6개 추가 본문 확인. 법원·법무부 자료와 확정 보도를 우선했다. 검색 인덱스·사건별 출처는 JSON에 있다.
- **Google Trends 미완료:** 직접 요청 HTTP429 후 브라우저 네트워크 접근이 권한 거부됐다. 거부 이후 우회하지 않았다. 2004-01-01~2026-10-30 / 2025-10-30~2026-10-30, KR의 평균·정점·최근값·시계열은 전부 `null`. 미측정은 0이 아니다. 최근 검색 수요나 장기 인기를 숫자로 주장하지 않는다.
- YouTube는 2026-10-30 검색 메타데이터 실측. 관련도·조회수 정렬 각 최대 40개 표본을 모아 제목·설명으로 사건을 대조한 뒤 조회수 상위 10개를 골랐다. **전 플랫폼 절대 TOP10이나 한국 내 시청량이 아닌 관측 표본 TOP10**이다. 개별 상세 조회수 재확인은 하지 않았으므로 응답 캐시·반올림 가능성이 있다.
- 아래 합계는 서로 다른 영상 ID의 누적 조회수 합으로 순시청자 수가 아니다. 같은 방송 재편집·합본도 포함된다. 8분 이상 영상 수는 표본 경쟁 구조 참고이며 제작 분량의 의무 기준이 아니다.
- 순위·포화도·서사 깊이는 편집 판단이다. 임의 가중 점수는 만들지 않았다. 성범죄·미성년 직접 피해·친밀관계/가정폭력·스토킹·살아 있는 공인 당사자 제외는 유지했다. 범죄로 유명해진 일반인 자체를 공인으로 분류하지 않았으며, 판사·검사·해설자의 등장도 가해·피해 당사자와 구분했다.

## TOP10

| 순위 | 사건·연도 | 확인한 최종 형 | YT 표본10 합계 / 채널 / 8분↑ | 장편 판단 |
|---:|---|---|---|---|
| 1 | [막가파 납치·생매장 살인](https://www.hankookilbo.com/news/article/199712130034973418) (1996) | 두목 최정수 사형 확정 | 192.1만 / 8채널 / 9편 | 매우 깊음 |
| 2 | [대전 국민은행 권총 강도살인](https://www.yna.co.kr/view/AKR20231214069500004) (2001) | 이승만·이정학 각 무기징역 확정 | 461.8만 / 9채널 / 6편 | 매우 깊음 |
| 3 | [이태원 햄버거가게 살인사건](https://www.yna.co.kr/view/AKR20170125074051004) (1997) | 패터슨 징역 20년 확정 | 987.1만 / 8채널 / 10편 | 매우 깊음 |
| 4 | [정유정 과외앱 살인](https://www.scourt.go.kr/portal/news/NewsViewAction.work?gubun=2&seqnum=5365) (2023) | 무기징역 확정 | 1,911.3만 / 7채널 / 7편 | 깊음 |
| 5 | [권재찬 연쇄 강도살인](https://www.yna.co.kr/view/AKR20230921071500004) (2021) | 1심 사형→2심 무기징역→확정 | 473.2만 / 8채널 / 8편 | 매우 깊음 |
| 6 | [안양 환전소 살인·최세용 일당 필리핀 납치](https://www.moj.go.kr/bbs/moj/182/591466/artclView.do) (2007/2011) | 최세용 무기징역 확정; 김성곤 무기징역 및 별건 징역 7년 확정 | 1,507.8만 / 5채널 / 9편 | 매우 깊음 |
| 7 | [장대호 한강 몸통시신 사건](https://www.yna.co.kr/view/AKR20200729059651004) (2019) | 무기징역 확정 | 1,750.2만 / 9채널 / 6편 | 깊음 |
| 8 | [강서구 PC방 김성수 살인](https://www.donga.com/news/Society/article/all/20200217/99751234/1) (2018) | 징역 30년 확정(상고 취하) | 1,375.9만 / 8채널 / 2편 | 중간~깊음 |
| 9 | [신림역 조선 흉기난동](https://www.scourt.go.kr/supreme/news/NewsViewAction2.work?gubun=702&seqnum=1586) (2023) | 무기징역 확정 | 735.8만 / 6채널 / 2편 | 중간~깊음 |
| 10 | [탈옥수 신창원](https://www.joongang.co.kr/article/3880605) (1989/1997/1999) | 탈옥 전 강도치사 무기징역 확정; 탈옥 등 추가형은 항소심 22년 6개월 확인 | 3,345.6만 / 10채널 / 7편 | 매우 깊음 |

신창원은 **기존 강도치사 무기형의 확정**을 확인했다. 탈옥 추가형 22년 6개월은 항소심까지 확인했으며, 그 추가형의 최종 확정일은 미확보다. 안양·필리핀 사건은 최세용 2017-09 확정 보도와 김성곤의 법무부 확정 확인으로 판단했다. 장대호 2020-07-29는 확정 보도일이며 실제 선고일과 분리했다.

## 첫 제작 3편

1. **여성을 생매장한 20대들, 선고 직후 판사를 협박했다** — 납치→검문→검거→법정 난동까지 전환이 많고 표본 경쟁이 상대적으로 작음.
   구성: 조직 결성·모방 → 성인 피해자 납치 → 금품 강취와 살인 → 주유소 강도·검문 → 자백·법정 협박 → 사형 확정. 지존파 종합편 대신 막가파 1996년 사건의 수사와 재판으로 좁힘. 타 조직 성범죄는 가져오지 않음.

2. **21년 전 사라진 권총강도, 손수건이 범인을 가리켰다** — 총기 탈취·현금 강탈·미제·DNA·공범 진술 충돌·형량 역전이 모두 있음.
   구성: 2001 총성 → 권총 출처 → 남겨진 증거 → 21년의 공백 → DNA 검거 → 누가 쐈나 → 두 명 무기징역. 오래된 미제 소개 영상에 2023 확정판결과 공범 20년→무기 변화를 결합.

3. **화장실에 남은 두 남자, 서로를 지목한 20년** — 같은 현장 두 진술을 대비시키는 구조가 강하고 최종 판결로 결론을 낼 수 있음.
   구성: 1997 현장 → 상반된 진술 → 초기 오판·별건 유죄 → 출국 → 송환 → 2017 살인 유죄 확정. 범인이 누구인가를 무한히 미스터리화하지 않고 증거인멸 재판과 살인 재판의 차이·법정 최고형 20년을 설명.

## 제외·보류와 추가 후보

| 사건 | 판정 | 이유 |
|---|---|---|
| 서현역 최원종 차량돌진·흉기난동 | hold | 미성년 피해를 확인한 것이 아님. 전체 직접 피해자의 성인 여부 확인이 남아 있어 성인 한정 TOP10에는 보류. |
| 정두영 연쇄 강도살인 | hold | 사형 확정은 확인했으나 전체 직접 부상자 성인 여부 미확보. 영아 목격을 곧바로 살인 피해로 오기하지 않고 보류. |
| 은평구 일본도 이웃 살인 | reserve | 기존 후보 N17 유지. 단일 현장 사건이라 과거 수사극보다 전환점이 적고, 이번 최초 3편에서는 후순위. |
| 인천 노래주점 허민우 살인 | hold | 확정은 위키 보조 정보만 확보. 독립 언론·법원으로 최종 확정을 재확인하지 못해 TOP10에서 보류. |
| 유영철 연쇄살인 | excluded | 성인 20명 살인 본건을 미성년 살인으로 오기하지 않음. 다만 2004고합972 판결문에 별건 미성년자 강간 전력이 명시되고 혜화동 영아가 남아 있는 집의 방화도 포함됨. 전체 행적을 다루는 장편은 성범죄·미성년 관련 장면을 끌어들이므로 이번에는 편집상 제외. 성인 살인 부분만 분리하는 조건부 제작 가능성은 남김. |
| 지존파 | excluded | 납치·강간·살인이 하나의 연속 사건이며 탈출한 생존자도 성폭행 피해자. 성범죄를 제거하면 사건 핵심과 탈출 동기를 왜곡하게 되어 제외. |
| 우순경 우범곤 총기난사 | excluded | 미성년·영아 피해 포함, 동거녀도 피살되어 친밀관계 폭력 포함. 범인이 현장에서 사망해 확정판결 조건도 충족하지 못함. |
| 대구지하철 방화 | excluded | 공개 희생자 명단에 16·17세 등 미성년 피해가 포함됨. 성인 피해자만 따로 잘라 참사 전체를 다루는 방식은 채택하지 않음. |
| 김대두 연쇄살인 | excluded | 영아·어린이 살인과 강간이 범행군에 포함됨. 미성년 피해·성범죄 두 조건으로 제외. |
| 온보현 연쇄 납치살인 | excluded | 생존 피해자 성폭행과 성폭행에 저항한 피해자 살인이 결합됨. 살해된 두 명 모두 강간 기수 피해자였다고 쓰면 오보이며, 강간 미수·다른 생존자의 성폭행을 구분해도 성범죄 제외 조건에 해당. |
| 이춘재·화성 연쇄살인 | 제외 | 사용자 지정 제외: 성범죄 및 미성년 피해가 포함됨. 화성 사건을 이춘재의 별건 확정형과 혼동하지 않음. |
| 강호순 | 제외 | 사용자 지정 제외: 성범죄 포함. |
| 조두순 | 제외 | 사용자 지정 제외: 아동 성범죄. |
| 김길태 | 제외 | 사용자 지정 제외: 미성년 성범죄·살인. |
| 세월호 | 제외 | 사용자 지정 제외: 미성년 피해 다수. |
| 씨랜드 | 제외 | 사용자 지정 제외: 미성년 피해 다수. |
| 고유정 | 제외 | 사용자 지정 제외: 전 배우자에 대한 친밀관계·가정 내 폭력. |
| 이은해 계곡살인 | 제외 | 사용자 지정 제외: 배우자에 대한 친밀관계·가정 내 폭력. |
| 정남규 연쇄살인 | 제외 | 미성년자 성추행·살인이 포함되어 두 제외 조건에 해당. |
| 안인득 진주 아파트 방화살인 | 제외 | 12세 피해자 등 미성년 피해 포함. |
| 최신종 연쇄살인 | 제외 | 강간·강도살인 범행이 결합. |
| 김태현 세 모녀 살인·신당역 전주환 살인 | 제외 | 스토킹 범행과 연결되는 소재로 사용자 제외 범주 적용. 이번 확장 후보에는 편입하지 않음. |
| 이재명 피습 | 제외 | 살아 있는 공인이 직접 피해 당사자이므로 제외. |

유영철은 **살인 본건 20명이 모두 성인이라는 점과 별건 성범죄 전력을 구분**했다. 전체 행적형 장편은 제외했으며 성인 살인만의 조건부 범위는 JSON에 남겼다. 서현역은 미성년 피해가 확인돼 제외한 것이 아니라, 초기 차량 피해자 1명의 나이까지 확인하지 못해 보류했다. 구조에 나선 10대 목격자와 직접 피해자는 구분했다.

추가 제외 근거: [정남규](https://www.sisajournal.com/news/articleView.html?idxno=193324) · [안인득](https://www.sedaily.com/article/20107256) · [최신종](https://www.yna.co.kr/view/AKR20201105120351055). 사용자 지정 예시는 지시된 제외 이유를 그대로 적용했다.

## 사건별 평가·YouTube 표본 TOP10

모든 사건의 Google Trends 두 기간은 접근 차단으로 미측정이다. 정확한 요청 URL·기간·지역·null 지표는 JSON `google_trends`에 각각 보존했다. 아래 영상 제목은 플랫폼 표시값이고, 역사 사실·범인 발언의 진실성을 보증하지 않는다.

### 1. 막가파 납치·생매장 살인

- 판결: 두목 최정수 사형 확정. 1997-12-12
- 피해·범위: 피살 피해자 40세 여성. 지존파를 모방했으나 지존파의 성범죄 사실을 본건 범죄로 합치지 않음.
- 서사: **매우 깊음**. 조직 결성·모방 동기 → 40대 여성 납치와 금품 강취 → 생매장·주유소 강도 → 피해 차량 검문으로 검거 → 1·2심과 법정 협박 → 대법원 사형 확정
- 편집·경쟁: 부자 응징을 내세운 조직의 실제 표적과 검거의 허점을 시간순으로 재구성. 표본 내 상대적으로 낮음. 최대 영상은 사건의뢰, 방송 대형 요약물의 수백만 회 장벽이 비교적 작음.
- 관측 합계 1,920,786회, 중앙값 129,992회, 8채널, 8분 이상 9/10편.
- 근거: [한국일보·1997-12-13, 대법 확정 보도](https://www.hankookilbo.com/news/article/199712130034973418) · [문화일보·항소심 및 피해자 40세](https://www.munhwa.com/article/10051369) · [중앙일보·항소심 법정 협박](https://www.joongang.co.kr/article/3490473)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | 사건의뢰 | 943,123 | 70:50 | [[South Korean Murder Cases Episode 38] Makgapa](https://www.youtube.com/watch?v=ZPGDfU6tPdA) |
| 2 | 채널A News | 166,658 | 12:19 | [[Reconstruction of the Verdict] The 'Makga-pa' Gang That Refused Forgiveness · Crime Situation Room](https://www.youtube.com/watch?v=Au8cJCojPOg) |
| 3 | 현대사TV | 160,045 | 9:24 | [쓰레기들을 존경한 쓰레기들 [막가파의 이야기]](https://www.youtube.com/watch?v=efF1moiZoL0) |
| 4 | 고요한밤 | 155,446 | 61:28 | [🌙 [국내사건] 지존파·막가파·영웅파, 한국을 충격에 빠뜨린 조직 범죄 실화](https://www.youtube.com/watch?v=_TK0YnMtLec) |
| 5 | 범죄의 재구성 | 133,946 | 28:39 | [양은이파를 꿈꿨던 20살 청년들이 벌인 일](https://www.youtube.com/watch?v=vrh4NBVS9qk) |
| 6 | 현대사TV | 126,039 | 9:23 | ["지존파처럼 살고 싶다" 범죄집단 막가파의 충격실체 !](https://www.youtube.com/watch?v=-rC02Vgtq9w) |
| 7 | 현대사TV | 95,223 | 18:44 | [못 돼 처먹은 양아치집단 [지존파와 막가파]](https://www.youtube.com/watch?v=uLgp59x4awE) |
| 8 | 사건의뢰 뒷방 | 56,862 | 20:36 | [[대한민국 살인사건 압축] 세상을 막 살고파!!! - 막가파 그들의 이야기](https://www.youtube.com/watch?v=-96NHuUlpNM) |
| 9 | JTBC News | 52,613 | 12:30 | ["지존파·조양은처럼 하고 싶었다"…어긋난 동경, '막가파' 사건 / JTBC 사건반장](https://www.youtube.com/watch?v=zeHoeE0W7qo) |
| 10 | 3분역사 | 30,831 | 4:13 | [Choi Jeong-su, the leader of 'Makgapa' who dreamed of becoming Jo Yang-eun / The real-life Makgap...](https://www.youtube.com/watch?v=1BMyorxmveA) |

### 2. 대전 국민은행 권총 강도살인

- 판결: 이승만·이정학 각 무기징역 확정. 2023-12-14
- 피해·범위: 은행 출납과장 45세, 선행 권총 탈취 피해자는 성인 경찰관.
- 서사: **매우 깊음**. 경찰관 습격·권총 탈취 → 은행 지하주차장 현금수송차 습격 → 손수건·마스크 증거와 장기 미제 → 2022년 DNA 대조로 검거 → 누가 방아쇠를 당겼는가 진술 공방 → 공범 20년→무기로 가중·확정
- 편집·경쟁: 권총의 이동 경로와 21년 뒤 손수건 DNA가 연결되는 수사극. 2001→2022 검거는 21년, 2023 확정까지는 22년으로 구별. 중간. SBS·그알 인기 영상이 있으나 단순 범행 소개보다 검거 이후 공범 형량 역전을 붙일 여지.
- 관측 합계 4,617,554회, 중앙값 209,281회, 9채널, 8분 이상 6/10편.
- 근거: [연합뉴스·2023-12-14 확정](https://www.yna.co.kr/view/AKR20231214069500004) · [KBS·확정과 1·2심 차이](https://news.kbs.co.kr/news/view.do?ncd=7841754)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 1,879,747 | 21:53 | [[꼬꼬무 121회 요약] 영원한 도피는 없다, 21년만에 붙잡힌 진범들의 정체는?  · 꼬리에 꼬리를 무는 그날 이야기 (SBS방송)](https://www.youtube.com/watch?v=3OAyNcjz_nY) |
| 2 | 그것이 알고싶다 | 1,007,189 | 20:05 | [True Culprit Arrested After 21 Years! Are There More Uncovered Crimes? · Short Unanswered Questions](https://www.youtube.com/watch?v=fSjj7-QuQmo) |
| 3 | 사건의뢰 | 341,900 | 40:10 | [Cold Case Solved! - The Full Story of the Daejeon Bank Robbery and Murder Case](https://www.youtube.com/watch?v=cE8aKut7njw) |
| 4 | YTN | 308,569 | 1:43 | ['DNA에 덜미' 21년 미제 대전 은행 강도살인 용의자 붙잡혀 / YTN](https://www.youtube.com/watch?v=LE3qxAyF3dE) |
| 5 | kimwontv김원 | 215,721 | 30:08 | [【세 발의 총성, 준비된 차량, 그리고 얼굴】 대전 국민은행 강도 살인사건ㅣ토요사건팩트](https://www.youtube.com/watch?v=yucnHpo60Bk) |
| 6 | MBCNEWS | 202,841 | 2:15 | [Suspects in 2001 Daejeon Bank Armed Robbery and Murder Arrested After 21 Years (2022.08.27/Newsde...](https://www.youtube.com/watch?v=UetXXjQss9w) |
| 7 | 디바제시카DeevaJessica | 202,159 | 19:27 | [18년간 완벽한 미제로 남은 한국판 '종이의 집'? 대전 국민은행 강도살인](https://www.youtube.com/watch?v=DBu1pzB-p2k) |
| 8 | 뉴스1TV | 163,122 | 4:00 | [21년만에 붙잡은 대전 은행 강도...이제는 말 할 수 있다](https://www.youtube.com/watch?v=pPjOAHbEdCo) |
| 9 | 사건의뢰 뒷방 | 148,645 | 262:39 | [[사건의뢰 몰아보기] 대전은행강도 살인사건/ 무안 저수지 보험살인사건/ 대전 여대생 납치강도사건 / 대한민국 살인사건 201회](https://www.youtube.com/watch?v=dzPl6pazOOo) |
| 10 | 그것이 알고싶다 | 147,661 | 3:48 | [100% the Culprit! VS False Confession! The Daejeon Bank Robbery Case · Unanswered Questions Yeste...](https://www.youtube.com/watch?v=Wxm1vtjCtn8) |

### 3. 이태원 햄버거가게 살인사건

- 판결: 패터슨 징역 20년 확정. 2017-01-25
- 피해·범위: 피해자 22세. 범행 당시 피고인 17세는 미성년 피해자 조건에 해당하지 않음.
- 서사: **매우 깊음**. 화장실에서 대학생 피살 → 서로 상대를 지목하는 두 용의자 → 초기 기소·무죄와 증거인멸 별건 → 출국정지 누락·미국행 → 재수사·범죄인 인도 → 살인 유죄와 20년 확정
- 편집·경쟁: 같은 현장에 있던 두 사람의 진술을 병렬로 보여주고, 왜 20년이 걸렸는지를 판결로 회수. 높음. SBS 계열 비슷한 요약 영상이 여러 개. 송환과 두 재판의 차이를 중심축으로 잡아야 함.
- 관측 합계 9,870,666회, 중앙값 524,500회, 8채널, 8분 이상 10/10편.
- 근거: [연합뉴스·2017-01-25 확정](https://www.yna.co.kr/view/AKR20170125074051004) · [한겨레·증거인멸과 살인 재판 경과](https://www.hani.co.kr/arti/society/society_general/780148.html)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 5,469,543 | 21:30 | [[꼬꼬무2 15회 요약] 피로 물든 화장실, 20년 만에 밝혀진 살인자와 목격자 · 꼬리에 꼬리를 무는 그날 이야기 (SBS방송)](https://www.youtube.com/watch?v=jHYiB0EfpCI) |
| 2 | 궁금소 | 766,669 | 17:32 | [누가 그를 죽였나? 이태원 화장실 살인사건](https://www.youtube.com/watch?v=JhvXWlmH45k) |
| 3 | 디바제시카DeevaJessica | 571,635 | 28:42 | [The Unjust Itaewon Murder Case · Saturday Mystery · Deeva Jessica](https://www.youtube.com/watch?v=JKfkuHefo-o) |
| 4 | 샾잉 #ing | 542,025 | 14:27 | [[#알쓸범잡] 영화 "이태원 사건"으로 시작된 재수사, 21년 만에 인정된 과거의 잘못된 판결 · #갓잡은클립 #샾잉](https://www.youtube.com/watch?v=7LtZ76msX_I) |
| 5 | 그것이 알고싶다 | 525,618 | 24:25 | [The Truth Within the Conflicting Statements of the Two 'Itaewon Murder Case' Suspects, Analyzed b...](https://www.youtube.com/watch?v=rPAA8NSGyd8) |
| 6 | 그것이 알고싶다 | 523,383 | 15:05 | [[ENG] 왜 20년간 진범을 찾지 못했나? 이태원 살인사건 · 그알 캐비닛](https://www.youtube.com/watch?v=TWhO3Rs7I4Q) |
| 7 | SBS | 450,604 | 21:21 | [[꼬꼬무2] 요약 '범인 잡는데 20년, 이태원 살인사건 두 용의자의 거짓말'  · SBS NOW](https://www.youtube.com/watch?v=qmNpLuU3BlU) |
| 8 | 사건의뢰 | 385,617 | 83:07 | [[South Korean Murder Cases Episode 109] The Truth Behind the Itaewon Murder Case](https://www.youtube.com/watch?v=73lt6DIvjTk) |
| 9 | 디바제시카DeevaJessica | 371,750 | 19:39 | [[금사파] 20년간 미제였던 '이태원 살인사건' 범인은 바로.. · 금요사건파일 · 디바제시카](https://www.youtube.com/watch?v=WgvCUn0n_5s) |
| 10 | 디글 :Diggle | 263,822 | 23:28 | [[#사건의재구성] 교도소에 진범이 들어가기까지 걸린 시간 20년. 1997년 이태원 햄버거 가게에서 벌어진 외국인 범죄 · #알쓸범잡 #디글](https://www.youtube.com/watch?v=uE1zVKrshF4) |

### 4. 정유정 과외앱 살인

- 판결: 무기징역 확정. 2024-06-13
- 피해·범위: 피해자는 20대 성인 여성. 중학생으로 위장한 가해자와 피해자 나이를 혼동하지 않음.
- 서사: **깊음**. 과외앱으로 범행 대상 물색 → 학생 위장·피해자 방문 → CCTV 동선과 반복된 거짓말 → 택시기사 신고와 검거 → 계획성·교화 가능성 논쟁 → 무기징역 확정
- 편집·경쟁: 중학생 위장이 통했던 접근 과정과 수사에서 무너진 거짓말을 연결. 높음. 뉴스·그알 등 다수의 100만~400만 회 영상. 보도 요약만으로는 차별화 어려움.
- 관측 합계 19,113,421회, 중앙값 1,764,298회, 7채널, 8분 이상 7/10편.
- 근거: [대법원·2024도5087](https://www.scourt.go.kr/portal/news/NewsViewAction.work?gubun=2&seqnum=5365) · [연합뉴스·2024-06-13 확정](https://www.yna.co.kr/view/AKR20240613065751004)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | 그것이 알고싶다 | 3,960,738 | 20:39 | [반복된 거짓말 속에 숨겨진 성향? 정유정에 대한 오해와 진실｜짧은 그알](https://www.youtube.com/watch?v=6w16kBjtLFU) |
| 2 | 그것이 알고싶다 | 2,819,610 | 13:44 | [정유정이 범행 후 피해자 집에 3번 더 간 이유 · 그알 비하인드](https://www.youtube.com/watch?v=y7aNnXa0-d0) |
| 3 | JTBC News | 2,378,109 | 8:44 | [[1일1뉴스] 삼시세끼 챙겨 먹고 잠도 잘 자…보통 아닌 정유정과 '수싸움' 시작 / JTBC News](https://www.youtube.com/watch?v=FIaxOy0m83E) |
| 4 | MBCNEWS | 2,287,516 | 10:11 | ["내가 손녀를 잘못 키웠어"..넋이 나간 할아버지의 자책 [뉴스.zip/MBC뉴스]](https://www.youtube.com/watch?v=O4myeE11tx0) |
| 5 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 1,764,858 | 18:02 | [＂피해자 표정 아파보여＂ 피해자의 사인이 말하는 정유정 사건의 진실 · SBS스페셜[국과수2](SBS 방송)](https://www.youtube.com/watch?v=_pdZe2q5tb8) |
| 6 | JTBC News | 1,763,737 | 5:34 | [[1일1뉴스] 끔찍하면서도 허술했던 범행…'엽기 살인' 가해자는 23살 정유정 / JTBC News](https://www.youtube.com/watch?v=L4zaqu8HlbQ) |
| 7 | YTN | 1,291,960 | 1:48 | ['신상공개' 23살 정유정 "살인 충동 느껴"...계획적 범행 / YTN](https://www.youtube.com/watch?v=2veagTh4EzE) |
| 8 | 빨강도깨비 | 953,711 | 12:24 | [정유정이 범행을 계획하면서 여러 번 다시 봤다는 영화](https://www.youtube.com/watch?v=RBYO47BoKIA) |
| 9 | MBCNEWS | 947,056 | 2:31 | [[자막뉴스] "내가 안 죽였어..옮기기만 했어" "나만 불쌍" 정유정 육성 공개 (2023.09.26/MBC뉴스)](https://www.youtube.com/watch?v=rFSYaUZQ9h4) |
| 10 | 뷰인사이드 | 946,126 | 24:37 | [Watching prison life... Jung Yu-jeong is different from your average murderer.](https://www.youtube.com/watch?v=WHdcklolCMI) |

### 5. 권재찬 연쇄 강도살인

- 판결: 1심 사형→2심 무기징역→확정. 2023-09-21
- 피해·범위: 50대 여성 지인과 40대 남성 동료. 확인된 관계는 지인·동료로 교제살인으로 분류하지 않음.
- 서사: **매우 깊음**. 과거 살인 복역 후 출소 → 지인 살해·금품 강취 → 시신 유기를 도운 동료도 피살 → CCTV 시간표와 책임 전가 → 1심 사형 → 계획살인 인정 범위가 달라진 2심·확정
- 편집·경쟁: 도와준 공범이 다음 피해자가 되는 전환과 사형이 무기로 바뀐 법원 판단을 결말로. 미확인 암수살인은 사실화하지 않음. 중간. 장편 해설이 여러 채널에 있으나 사형 확정으로 오해시키는 오래된 제목을 최종 판결로 바로잡을 여지.
- 관측 합계 4,732,024회, 중앙값 337,632회, 8채널, 8분 이상 8/10편.
- 근거: [연합뉴스·2023-09-21 확정](https://www.yna.co.kr/view/AKR20230921071500004) · [뉴스핌·50대·40대 피해자 및 감형 이유](https://web3.newspim.com/news/view/20230921000411)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | E채널 | 1,199,647 | 28:01 | [🕵‍♂47회 요약 · 인천 연쇄 살인사건 · CCTV로 범인이 설계한 타임라인을 재구성하라 [용감한형사들4] 매주 (금) 밤 9시 50분 본방송](https://www.youtube.com/watch?v=tuu2BKN1Cio) |
| 2 | 디바제시카DeevaJessica | 727,746 | 52:59 | [최근 한국에서 유일하게 사형 판결받은 범인 권재찬을 아십니까](https://www.youtube.com/watch?v=bk8bruA6X5w) |
| 3 | 조은영화 | 565,809 | 45:23 | [🔥The Worst Murder Addict in History: Kwon Jae-chan, the Devil Who Spent Over Half His Life Behind...](https://www.youtube.com/watch?v=AwJsnQ6Mx9A) |
| 4 | MBC every1 | 545,087 | 39:56 | [[심층분석] 15년 복역 후 출소, 그리고 또 살인... 인천 강도 연쇄살인범 권재찬 사건 심층분석 · #히든아이 · #MBCevery1 · EP.89](https://www.youtube.com/watch?v=e7PGUoY3UCY) |
| 5 | kimwontv김원 | 343,775 | 47:48 | [【2022년 '사형선고' 연쇄살인마 권재찬】ㅣ공범을 살해하는 것이 '내가 사는 일이다'ㅣ당신이 몰랐던 사건](https://www.youtube.com/watch?v=PCX4yjrw9fg) |
| 6 | JTBC News | 331,490 | 1:35 | [권재찬 '계획 살해' 드러났다…피해자 몸에서 '약물' / JTBC 뉴스룸](https://www.youtube.com/watch?v=wMXlfm-_izI) |
| 7 | YTN | 323,153 | 0:52 | [[속보] 인천 연쇄살인범 신상 공개...만 52살 권재찬 / YTN](https://www.youtube.com/watch?v=yRYV4rEL3CU) |
| 8 | 사건의뢰 | 277,939 | 19:50 | [Serial killer Kwon Jae-chan commits another crime after being released from prison after 15 years.](https://www.youtube.com/watch?v=BryW4nQsL6Y) |
| 9 | 사건의뢰 | 267,204 | 53:52 | [[Case Request Live] June 27 - Serial killers Kwon Jae-chan in their 50s sentenced to death (Kim B...](https://www.youtube.com/watch?v=GaQlrU6W2ow) |
| 10 | kimwontv김원 | 150,174 | 22:09 | [【단독 '암수살인 의혹'】 연쇄살인마 권재찬 ,'성명불상'의 공범은 어디로?ㅣ당신이 몰랐던 사건ㅣ김원사건파일](https://www.youtube.com/watch?v=W_QyT8FESCM) |

### 6. 안양 환전소 살인·최세용 일당 필리핀 납치

- 판결: 최세용 무기징역 확정; 김성곤 무기징역 및 별건 징역 7년 확정.  — 최세용은 2017-09 확정 보도, 정확한 일자 미확보. 김성곤은 법무부 2025-01-24 자료에서 확정 확인. 2025-01-23은 최종 인도 결정 통보일이며 판결 확정일이 아님.
- 피해·범위: 환전소 여직원 26세와 성인 한국인 관광객 피해를 대상으로 평가. 다른 필리핀 한인 피살사건을 합치지 않음.
- 서사: **매우 깊음**. 안양 환전소 강도살인 → 해외 도주와 한국인 관광객 납치 → 가족의 신고와 유해 추적 → 동남아 검거 → 임시 인도와 국내 재판 → 무기징역 확정·2025년 김성곤 최종 인도
- 편집·경쟁: 국내 살인에서 해외 납치와 송환까지 확장되는 추적극. 영화 범죄도시2의 장면을 사실로 쓰지 않음. 높음. SBS 꼬꼬무·그알 중심. 동일 방송의 재편집이 겹쳐 합계가 실제 시청자 수를 뜻하지 않음.
- 관측 합계 15,078,125회, 중앙값 686,807회, 5채널, 8분 이상 9/10편.
- 근거: [법무부·2025-01-24 확정 및 최종 인도](https://www.moj.go.kr/bbs/moj/182/591466/artclView.do) · [법무부 보도자료 PDF·최세용도 무기 확정](https://www.corrections.go.kr/bbs/moj/182/476895/download.do) · [중앙일보·최세용 2017-09 확정 보도](https://www.joongang.co.kr/article/22065392) · [연합뉴스·본건 인정 사실](https://www.yna.co.kr/view/AKR20161104089300051)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | SBS | 4,338,824 | 21:08 | ["천만원에 뼈라도 찾아가세요" 필리핀으로 여행 간 아들이 시체로 돌아온 이유 #꼬꼬무2 · SBS NOW](https://www.youtube.com/watch?v=BqDUhE4pxiA) |
| 2 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 4,182,272 | 21:17 | [[꼬꼬무2 17회 요약] ＂아드님은 죽었습니다. 뼈라도 가져가세요＂ 필리핀 살인 기업의 실체 · 꼬리에 꼬리를 무는 그날 이야기 (SBS방송)](https://www.youtube.com/watch?v=5b81bcFVnIs) |
| 3 | 그것이 알고싶다 | 2,690,665 | 18:54 | [Motif for the movie ‘The Outlaws 2’! Philippines serial kidnapping case · The Unanswered Question...](https://www.youtube.com/watch?v=2SXBEcRWXgI) |
| 4 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 1,117,993 | 10:29 | [The Philippine Serial Kidnapping Case, A Mother's Journey to Find Her Son's Body · KkokkoPICK](https://www.youtube.com/watch?v=2ga40X6J_U4) |
| 5 | 사건의뢰 | 838,097 | 93:24 | [[South Korean Murder Cases Ep. 129] The People Who Disappeared in the Philippines](https://www.youtube.com/watch?v=2MCHJ2JNll0) |
| 6 | 그것이 알고싶다 | 535,517 | 14:36 | [The Philippine Serial Kidnapping Case, Someone Definitely Knows · Cabinet](https://www.youtube.com/watch?v=XuL5PUSS9ZE) |
| 7 | 그것이 알고싶다 | 516,852 | 14:44 | [Anyang Currency Exchange Murder Case · The Cabinet](https://www.youtube.com/watch?v=XSPUCBctPKM) |
| 8 | chang kyu Kim | 378,643 | 5:22 | [홍석동 납치 사건, 납치범과의 통화 - 딴지일보.wmv](https://www.youtube.com/watch?v=xWt3RyPwpDA) |
| 9 | 그것이 알고싶다 | 314,379 | 14:54 | ["We are devils": The Philippine serial kidnapping case, Murder Inc. CEO Choi Se-yong (Part 3) · T...](https://www.youtube.com/watch?v=sUTcbLFm1ao) |
| 10 | 그것이 알고싶다 | 164,883 | 14:54 | ["Find the bodies yourself," Choi Se-yong and his accomplices (Part 4) · The Time of the Monster](https://www.youtube.com/watch?v=4GpWpwl_pA0) |

### 7. 장대호 한강 몸통시신 사건

- 판결: 무기징역 확정.  — 2020-07-29 대법원 확정 보도. 기사 문구가 확정했다고 29일 밝혔다이므로 실제 선고일을 별도 확정하지 않음.
- 피해·범위: 피해자 30대 남성 모텔 투숙객.
- 서사: **깊음**. 한강에서 시신 발견 → 피해자 신원·모텔 동선 복원 → 자수와 초기 대응 → 자기정당화 진술 → 검찰 사형 구형·법원 무기 → 자수감경 부인·확정
- 편집·경쟁: 범인의 주장을 사실과 구분하며 시신 발견→신원 추적→자수 순서로 구성. 매우 높음. 비디오머그 발언 영상이 압도적이고 기존 애니메이션 회고록도 존재.
- 관측 합계 17,502,387회, 중앙값 1,040,999회, 9채널, 8분 이상 6/10편.
- 근거: [연합뉴스·2020-07-29 확정 보도](https://www.yna.co.kr/view/AKR20200729059651004) · [동아일보·피해자 30대](https://www.donga.com/news/Society/article/all/20200729/102205429/2)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | 비디오머그 - VIDEOMUG | 7,089,282 | 1:54 | [[풀영상] "흉악범이 양아치 죽인 것...유족에 미안하지 않다", '한강 몸통 시신' 피의자 장대호 얼굴 공개 / 비디오머그](https://www.youtube.com/watch?v=ab3tlsngBG8) |
| 2 | 비디오머그 - VIDEOMUG | 2,395,411 | 2:16 | [살인마의 미소와 유족의 통곡...'한강 몸통 시신' 장대호, 사형선고 안 된 이유 / 비디오머그](https://www.youtube.com/watch?v=8sNyez3Z5rg) |
| 3 | 샾잉 #ing | 2,119,065 | 13:52 | [[#알쓸범잡] 법원도 인정한 비겁하고 교활한 장대호의 범행! 잘못을 뉘우칠 바에야 사형을 받겠다는 뻔뻔함과 악랄함 · #갓잡은클립 #샾잉](https://www.youtube.com/watch?v=2BL2IJfONMQ) |
| 4 | 그것이 알고싶다 | 1,362,733 | 24:31 | [장대호는 언제나 '선제 공격'으로 상대를 제압했다? 장대호와 김성수의 심리 분석 · 그알 외전](https://www.youtube.com/watch?v=qXkJBq1ScyQ) |
| 5 | 실화 On | 1,073,050 | 17:09 | [[실화Pick] 한강 토막 살인 사건 장대호의 실체 #실화탐사대 #실화On MBC190828방송](https://www.youtube.com/watch?v=e0n8BR6YIzI) |
| 6 | 사건의뢰 | 1,008,948 | 88:46 | ['한강 몸통 시신' 장대호는 누구인가?](https://www.youtube.com/watch?v=1tFDS8j4iv8) |
| 7 | 악인전 - 인물소개 | 838,461 | 4:49 | [Jang Dae-ho: 12 Facts You Didn't Know](https://www.youtube.com/watch?v=iCaNFHxC0xk) |
| 8 | 엠뚜루마뚜루 : MBC 공식 종합 채널 | 582,223 | 12:39 | [[실화탐사대] 한강 몸통시신 사건 장대호는 왜 살인범이 되었나? 그의 평소 모습을 기억하는 사람들 #엠뚜루마뚜루 #엠트루​ ​MBC190825방송](https://www.youtube.com/watch?v=LSUMpeZFip4) |
| 9 | 태풍의 눈곱 | 579,344 | 6:00 | [Jang Dae-ho's Memoir (Animation) Part 1: Memories of Murder](https://www.youtube.com/watch?v=z1lD7FebQWU) |
| 10 | YTN | 453,870 | 8:53 | [유족 향해 윙크하고 웃었다는 장대호...왜? / YTN](https://www.youtube.com/watch?v=EAIKi5_Y7M8) |

### 8. 강서구 PC방 김성수 살인

- 판결: 징역 30년 확정(상고 취하). 2019-12-12
- 피해·범위: 피해자 20세 아르바이트생.
- 서사: **중간~깊음**. 다툼과 경찰 출동 → 범행 전후 CCTV 동선 → 동생 공범 논란 → 심신미약 주장 검증 → 동생 무죄·본인 30년 → 상고 취하로 확정
- 편집·경쟁: 인터넷에서 퍼진 공범 의혹과 법원이 인정한 사실을 대조. 동생을 살인 공범으로 단정하지 않음. 높음. 포토라인·뉴스가 대규모 조회를 차지. 장편의 승부는 공범 판단과 확정 경위.
- 관측 합계 13,759,417회, 중앙값 1,026,620회, 8채널, 8분 이상 2/10편.
- 근거: [동아일보·2019-12-12 상고 취하](https://www.donga.com/news/Society/article/all/20200217/99751234/1) · [KBS·상고 취하로 확정](https://news.kbs.co.kr/news/view.do?ncd=4383138)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | 비디오머그 - VIDEOMUG | 3,735,133 | 4:57 | ['강서 PC방 살인사건' 김성수 "화나고 억울…동생도 벌 받아야" / 비디오머그](https://www.youtube.com/watch?v=AVaSknPqRAA) |
| 2 | SBS 뉴스 | 1,821,064 | 1:49 | ['당시로 돌아간다면 다른 선택 하겠냐'는 질문에 김성수의 대답 (풀영상) / SBS](https://www.youtube.com/watch?v=TNJ1kmYIuG0) |
| 3 | KBS News | 1,543,562 | 6:04 | [[뉴스 따라잡기] ‘PC방 살인사건’ 일주일…커지는 국민 분노 / KBS뉴스(News)](https://www.youtube.com/watch?v=sOmLuRTRrSM) |
| 4 | 그것이 알고싶다 | 1,362,733 | 24:31 | [장대호는 언제나 '선제 공격'으로 상대를 제압했다? 장대호와 김성수의 심리 분석 · 그알 외전](https://www.youtube.com/watch?v=qXkJBq1ScyQ) |
| 5 | 킴킴변호사 | 1,058,692 | 7:41 | [강서구 PC방 살인사건 피해자 측 변호사로서 한 말씀드립니다.](https://www.youtube.com/watch?v=Ni3KgKRmzPM) |
| 6 | 악인전 - 인물소개 | 994,548 | 4:23 | [12 Facts You Didn't Know About Kim Sung-soo](https://www.youtube.com/watch?v=HHfWW8tLxtU) |
| 7 | kimwontv김원 | 901,620 | 33:07 | [[김원 사건 파일] 엘리베이터로 내려가 피해자를 기다린 범인들... 강서구 PC방 알바생 피살사건...](https://www.youtube.com/watch?v=40eZntEfS2I) |
| 8 | JTBC News | 798,109 | 1:47 | ['강서구 PC방 알바생' 흉기 살해사건…현장 CCTV에는](https://www.youtube.com/watch?v=5qEbije55FE) |
| 9 | JTBC News | 776,082 | 5:33 | [[소셜스토리] 강서구 PC방 살인사건 피해자 아버지의 '못 다한 말'](https://www.youtube.com/watch?v=cze757ku9fQ) |
| 10 | 비디오머그 - VIDEOMUG | 767,874 | 2:47 | [[풀영상] '강서구 PC방 살인' 피의자 김성수 신상공개…대중 앞에 선 그의 첫마디는? /  비디오머그](https://www.youtube.com/watch?v=o-FUET42t0I) |

### 9. 신림역 조선 흉기난동

- 판결: 무기징역 확정. 2024-09-12
- 피해·범위: 사망자 22세, 부상자 30대 남성 3명으로 모두 성인. 신림 등산로 성폭행 살인과 별개.
- 서사: **중간~깊음**. 범행 전 휴대전화 초기화 → 흉기 절도와 신림역 이동 → 무차별 공격과 검거 → 진술과 법정 주장 변화 → 심신미약 인정과 감경 여부 → 무기징역 확정
- 편집·경쟁: 열등감 진술과 망상 주장의 변화, 심신미약 인정이 곧 감형은 아니라는 판결을 회수. 중간~높음. 단신 뉴스가 상위 조회를 많이 차지해 긴 해설에는 여지가 있으나 사건 자체의 시간축은 짧음.
- 관측 합계 7,358,016회, 중앙값 623,492회, 6채널, 8분 이상 2/10편.
- 근거: [대법원·2024도10197 보도자료](https://www.scourt.go.kr/supreme/news/NewsViewAction2.work?gubun=702&seqnum=1586) · [연합뉴스·2024-09-12 확정](https://www.yna.co.kr/view/AKR20240912068851004) · [연합뉴스·20대 사망·30대 3명 부상](https://www.yna.co.kr/view/AKR20230726118900004)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | MBCNEWS | 1,192,220 | 1:40 | [[오늘 이 뉴스] 신림역 흉기난동범 '33세 조선' 'CCTV 포착' 사진까지 공개 (2023.07.26/MBC뉴스)](https://www.youtube.com/watch?v=-Tl-kza7t8s) |
| 2 | SBS 뉴스 | 1,132,476 | 2:16 | [1명 사망·3명 중상…대낮 서울 신림동서 흉기 난동 / SBS 8뉴스](https://www.youtube.com/watch?v=3xPpFcTL9wY) |
| 3 | 궁금한 Y | 980,961 | 13:26 | [[Y 647회 요약] 신림역 묻지마 칼부림, 피의자 조선 · 숏와이](https://www.youtube.com/watch?v=PNas0_wYWNg) |
| 4 | YTN | 702,546 | 2:11 | [서울 신림동 흉기 난동...2명 심정지·2명 중상 / YTN](https://www.youtube.com/watch?v=qJgnSHsG4r8) |
| 5 | JTBC News | 631,492 | 4:10 | [[1일1뉴스] 신림 칼부림 목격자 "그 사람이랑 눈이 마주쳤어요. 눈빛이…" / JTBC News](https://www.youtube.com/watch?v=UA8WwXs08u4) |
| 6 | JTBC News | 615,492 | 1:30 | [신림역 인근 대낮 공포의 칼부림…1명 사망·3명 부상 / JTBC 뉴스룸](https://www.youtube.com/watch?v=5VNgNC-CDpU) |
| 7 | MBCNEWS | 600,113 | 0:44 | ['Sillim-dong' stabbing video uploader booked... decision on suspect's identity disclosure coming ...](https://www.youtube.com/watch?v=fTn0anwVYdA) |
| 8 | SBS 뉴스 | 573,413 | 1:29 | ["보지마, 끔찍해" 잔혹한 범행 장면이 그대로…CCTV 무차별 확산 (자막뉴스) / SBS](https://www.youtube.com/watch?v=YZz2cNUt_F4) |
| 9 | YTN | 530,934 | 2:23 | [[Subtitled News] "They're stabbing people"… Eyewitness's 'shocking testimony' on Sillim-dong knif...](https://www.youtube.com/watch?v=pb5GtwaYOTs) |
| 10 | 조은영화 | 398,369 | 53:36 | [🔥대한민국을 공포에 떨게 만들었던 신림동 칼부림 사건, 범행 후 모든 걸 포기했던 그의 최후와 잔인하고 무자비했던 그날의 범죄현장 ≪히든아이≫ 60화 몰아보기 ㅎㄷㄷ](https://www.youtube.com/watch?v=MGwVWpPqCDI) |

### 10. 탈옥수 신창원

- 판결: 탈옥 전 강도치사 무기징역 확정; 탈옥 등 추가형은 항소심 22년 6개월 확인.  — 기존 무기형의 확정 사실은 동시대 보도로 확인했으나 일자 미확보. 추가형은 2000-09-25 항소심까지 교차확인; 추가형 최종 확정일·절차는 미확보로 명시. 이를 대법 확정으로 바꾸지 않음.
- 피해·범위: 1989년 성인 주택 강도치사와 경찰관 상해·도주를 대상으로 평가. 무죄인 강간 혐의를 범죄 사실로 쓰지 않음.
- 서사: **매우 깊음**. 기존 강도치사와 무기징역 → 부산교도소 탈옥 → 907일 도피와 반복된 검거 실패 → 주민 신고와 순천 검거 → 추가 범죄 재판 → 강간 혐의 무죄와 원래 무기형 유지
- 편집·경쟁: 영웅화 없이 추적 실패의 이유와 신고로 좁혀지는 수사망을 구성. 매우 높음. 엑스톨이 동일 소재 907일 체포 작전으로 이미 약 176만 회. 첫 제작보다 후순위.
- 관측 합계 33,456,398회, 중앙값 1,849,234회, 10채널, 8분 이상 7/10편.
- 근거: [중앙일보·원래 무기징역 확정 및 강간 무죄](https://www.joongang.co.kr/article/3880605) · [문화일보·2000-09-25 항소심과 강간 무죄 유지](https://www.munhwa.com/article/10263272) · [연합뉴스·탈옥~검거](https://www.yna.co.kr/view/AKR19990716005400063)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | SBS | 11,627,042 | 24:38 | [[꼬꼬무] 요약  '1997년 대한민국을 뒤흔든 사건! 탈옥수 신창원의 이야기' · SBS NOW](https://www.youtube.com/watch?v=1LYSSY-VLTU) |
| 2 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 6,825,781 | 24:38 | [[꼬꼬무 3회 요약] 탈옥 위해 20kg 감량? 희대의 탈옥수 신창원 · 꼬리에 꼬리를 무는 그날 이야기](https://www.youtube.com/watch?v=gJW3qLxDAg0) |
| 3 | 그것이 알고싶다 | 3,983,215 | 10:38 | [[ENG] 희대의 탈옥수 신창원! 사람들은 왜 그에게 열광했을까? · 그알로 보는 '1999'](https://www.youtube.com/watch?v=AS5QcTejvGk) |
| 4 | 타M머신 | 2,732,844 | 2:11 | [[신긔방긔~] 신창원 검거 당시 제보자 112신고 통화내용](https://www.youtube.com/watch?v=PeIAmYZFR3Y) |
| 5 | YTN | 1,855,117 | 1:58 | [[News & Issues] Shin Chang-won, the "Epic Escapee," Spent 30 Years in Prison / YTN](https://www.youtube.com/watch?v=O4ll3_iWh5s) |
| 6 | 사건의뢰 | 1,843,350 | 101:05 | [[The Infamous Escape Artist Shin Chang-won] A Record of 907 Days](https://www.youtube.com/watch?v=pS8BdcL4Ld4) |
| 7 | 엑스톨(Extol) | 1,758,492 | 8:55 | [907일 동안 경찰을 농락한 탈옥수 '신창원' 체포 작전](https://www.youtube.com/watch?v=w_LJ_GQObic) |
| 8 | 디바제시카DeevaJessica | 1,334,383 | 17:28 | [[금사파] 한국에서 제일 유명한 탈옥수 신창원 도대체 왜? · 금요사건파일 · 디바제시카](https://www.youtube.com/watch?v=g5Ix93lsoYQ) |
| 9 | tvN Joy | 959,479 | 12:21 | [[알쓸범잡 부록] 탈옥범 신창원, 우리가 몰랐던 검거 후 이야기 #알쓸범잡 EP.9](https://www.youtube.com/watch?v=6GnEkdzAEPg) |
| 10 | KBS부산 | 536,695 | 3:53 | [신창원의 정체를 알면서도 여성들은 왜 그를 숨겨줬을까?😶 · 사사클럽 · KBS 260901 방송](https://www.youtube.com/watch?v=TjTo1biCLoo) |

직접 형식 경쟁: [엑스톨 영상](https://www.youtube.com/watch?v=w_LJ_GQObic) 1,758,492회. 표본10 합계에 포함됐는지는 영상 ID로 구분.

### 별도. 서현역 최원종 차량돌진·흉기난동

- 판결: 무기징역 확정. 2024-11-20
- 피해·범위: 사망자 20세·65세. 흉기 부상 9명은 20~70대로 보도. 초기 차량 피해 5명 중 1명 신원·나이 미확보. 14명은 인원이지 14세 피해자가 아님.
- 서사: **깊음**. 차량돌진 → 백화점 흉기 공격 → 현장 구조와 검거 → 피해자 치료 경과 → 망상·치료 거부와 책임능력 → 무기징역 확정
- 편집·경쟁: 차량과 흉기 피해를 하나의 동선으로 복원. 중간~높음. 단신 뉴스 비중이 크지만 실화탐사대 등 장편도 존재.
- 관측 합계 6,318,867회, 중앙값 573,916회, 6채널, 8분 이상 4/10편.
- 근거: [대법원·2024도13614](https://www.scourt.go.kr/portal/news/NewsViewAction.work?gubun=2&seqnum=5538) · [KBS·2024-11-20 확정](https://news.kbs.co.kr/news/view.do?ncd=8111002) · [경향신문·피해자 연령별 집계 및 신원 미확인 1명](https://www.khan.co.kr/article/202308032208001) · [헤럴드경제·흉기 피해자 20~70대](https://biz.heraldcorp.com/article/3183946)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | MBCNEWS | 1,496,199 | 1:06 | [[오늘 이 뉴스] "사람을 막 찔러요!"..10여명 날벼락..이번엔 분당서 '묻지마 흉기난동' (2023.08.03/MBC뉴스)](https://www.youtube.com/watch?v=BMeKlO-_DTU) |
| 2 | 실화 On | 1,050,796 | 27:56 | [[True Story Pick] Who is Seohyeon Station stabbing suspect Choi Won-jong? #TrueStoryExploration #...](https://www.youtube.com/watch?v=UtdhGR2dMeg) |
| 3 | MBCNEWS | 714,703 | 715:00 | [[속보] 칼부림 난동범은 22살 최원종..서현역 흉기 난동범 신상 공개 - [핫이슈PLAY] MBC뉴스 2023년 8월 7일](https://www.youtube.com/watch?v=A2S_KdvbyZ8) |
| 4 | 크크조이 : KBS Joy 종합 예능 채널 | 625,971 | 11:33 | [Saved lives at the 'Seohyeon Station incident' scene, but... worried about the 'trauma' [Ask Anyt...](https://www.youtube.com/watch?v=U_nD2JHuOyI) |
| 5 | JTBC News | 592,444 | 3:01 | [서현역 흉기 난동범은 '01년생 최원종'…범행 전날도 흉기 들고 갔었다 / JTBC 뉴스룸](https://www.youtube.com/watch?v=8FkotmIrPIU) |
| 6 | JTBC News | 555,387 | 1:18 | [분당 서현역서 '무차별 흉기 난동', 사건 당시 영상 보니… / JTBC News](https://www.youtube.com/watch?v=oayE2T1SFWI) |
| 7 | MBCNEWS | 422,208 | 1:32 | [[Today's News] Seohyeon Station stabbing suspect identified as 22-year-old Choi Won-jong... Photo...](https://www.youtube.com/watch?v=WjiOdZ2AWLo) |
| 8 | MBN News | 313,052 | 1:30 | [[자막뉴스] ＂빨리 뛰어요!＂ 긴박했던 '서현역 흉기 난동' 당시 상황 · 이슈픽](https://www.youtube.com/watch?v=tFIC7236zrU) |
| 9 | MBN News | 309,996 | 24:40 | [＂꺄악!＂ ＂어서 도망쳐요!＂ 분당 서현역 '흉기 난동' 충격적인 당시 상황 · 이슈픽 zip](https://www.youtube.com/watch?v=MRJXfH-yjDo) |
| 10 | KBS News | 238,111 | 1:50 | [분당 서현역 인근 AK플라자서 '흉기 난동', 부상자 다수 발생…용의자 현장서 체포 / KBS  2023.08.03.](https://www.youtube.com/watch?v=SRoFLWI99v0) |

### 별도. 정두영 연쇄 강도살인

- 판결: 2000-12 항소심 사형 후 상고 포기로 확정. 
- 피해·범위: 노인·성인 여성·20대 남성 사망 확인. 전체 부상자 10명 연령표는 미확보; 17개월 영아가 현장에 있었으나 직접 상해 여부 확인 안 됨.
- 서사: **매우 깊음**. 출소 후 강도살인 연속 발생 → 부유층 주택 침입 → 천안 검거와 부산 사건 연결 → 결혼자금 명목의 축재 → 사형 확정 → 2016년 탈옥 시도
- 편집·경쟁: 성실한 예비 사위라는 외형과 연쇄강도 수사의 연결. 높음. 디글·그알·꼬꼬무 등 대형 장편 다수.
- 관측 합계 12,007,368회, 중앙값 861,406회, 7채널, 8분 이상 9/10편.
- 근거: [연합뉴스·2000-12 항소심 후 상고 포기 확인](https://www.yna.co.kr/view/AKR20160928148000063) · [문화일보·피해자 및 17개월 아기 현장 존재](https://www.munhwa.com/article/10239864)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | 디글 :Diggle | 3,754,542 | 24:17 | [[#사건의재구성] 천안 경찰이 부산의 미제까지 해결할 수 있었던 실화! 몽타주로 잡은 정두영 · #알쓸범잡 #디글](https://www.youtube.com/watch?v=-DiyzD3SIrw) |
| 2 | 그것이 알고싶다 | 2,547,305 | 12:55 | [[ENG] 유영철의 롤모델?! 맨손의 연쇄살인마 정두영 · 그알로 보는 '연쇄살인마'](https://www.youtube.com/watch?v=1e1Af0BTAYg) |
| 3 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 1,343,128 | 14:58 | [[꼬꼬무 167회 요약] 성실한 예비 사위의 정체는 연쇄살인마? 그가 끊임없이 살인을 저질렀던 이유 · 꼬리에 꼬리를 무는 그날 이야기 (SBS방송) #꼬리에꼬리를무는그날이야기](https://www.youtube.com/watch?v=4z0HV_zZJQU) |
| 4 | MBC every1 | 1,280,840 | 151:08 | [[사건모음 2시간] 희대의 연쇄살인마 유영철과 그의 롤모델 정두영, 그리고 장재진까지 · #히든아이 · #MBCevery1 · EP. 76외](https://www.youtube.com/watch?v=NZxjLSBWiI8) |
| 5 | 조은영화 | 911,628 | 51:44 | [🔥Jung Doo-young, South Korea's first serial killer admired by Yoo Young-chul: The heinous crimina...](https://www.youtube.com/watch?v=Xc-tK0tHn2I) |
| 6 | 디바제시카DeevaJessica | 811,184 | 18:21 | [3억짜리 아파트에 월천씩 번다던 예비사위 특기는 무차별 연쇄살인.. 정두영 사건전말 · 금요사건파일](https://www.youtube.com/watch?v=nSCzE5pAhtQ) |
| 7 | MBC every1 | 394,256 | 319:47 | [[사건모음] 사회에서 영원히 격리된 대한민국 최악의 사형수 6인 몰아보기(유영철, 정남규, 강호순, 박한상, 장재진, 정두영) l #히든아이 l #MBCevery1 l EP.76외](https://www.youtube.com/watch?v=aWnZhnD-ETg) |
| 8 | 괴인협회 | 369,911 | 5:42 | [Jeong Doo-young: 11 Facts You Didn't Know](https://www.youtube.com/watch?v=PffLc9qU18U) |
| 9 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 322,626 | 23:34 | [[🧾#달리포트] 착하고 성실하기만 했던 예비사위의 충격적인 실체...희대의 연쇄살X마 '정두영' #꼬꼬무 #달리 #DALI](https://www.youtube.com/watch?v=8KJoxaHq3zM) |
| 10 | MBC every1 | 271,948 | 43:45 | [[심층분석] 유영철의 롤모델? 9명 죽여 '신혼 자금' 1.3억 모은 '직업 살인마' 정두영 · #히든아이 · #MBCevery1 · EP.78](https://www.youtube.com/watch?v=ZDmu1a0a7SU) |

### 별도. 은평구 일본도 이웃 살인

- 판결: 무기징역 확정. 2025-09-25 — 기존 10-26 조사에는 2025-10-24를 확정일로 적었으나 재확인한 매일경제 기사는 실제 확정 09-25, 보도 10-24로 구분함. 원자료는 보존하고 여기서 정정.
- 피해·범위: 피해자 40대 남성. 2021년 아내 살해·2023년 주차시비 살인과 구분.
- 서사: **중간~깊음**. 도검 소지와 범행 준비 → 아파트에서 이웃 공격 → 도주로 추격 → 망상 주장 → 책임능력 판단 → 무기징역 확정
- 편집·경쟁: 아파트 내 짧은 추적 동선을 재구성하되 동명 별건을 합치지 않음. 중간~높음. 별건 일본도 사건이 검색에 다량 혼입.
- 관측 합계 7,134,156회, 중앙값 641,420회, 6채널, 8분 이상 3/10편.
- 근거: [매일경제·2025-09-25 확정, 10-24 보도](https://www.mk.co.kr/news/society/11450445)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | YTN | 1,528,270 | 1:45 | [[자막뉴스] 아파트 정문서 벌어진 끔찍한 사건...'일본도 살해' 30대 체포 / YTN](https://www.youtube.com/watch?v=065F3QLAZvI) |
| 2 | JTBC News | 955,345 | 4:00 | [[현장영상] "이X이 꼭 사형당하도록 노력"…'일본도' 피해자 아버지의 절규 / JTBC News](https://www.youtube.com/watch?v=QnPo_gTYhbs) |
| 3 | 실화 On | 903,261 | 23:06 | [[True Story Pick] The Japanese Sword Murder Case: The Truth of That Day #TrueStoryInvestigationTe...](https://www.youtube.com/watch?v=Wv89cG4suNo) |
| 4 | 실화 On | 823,993 | 18:34 | [[실화Pick] 일면식도 없는 이웃에게... 일본도 살인 사건의 전말 #실화탐사대 #실화On MBC240829방송](https://www.youtube.com/watch?v=2Qm_pfbVbH4) |
| 5 | JTBC News | 679,507 | 2:07 | ["한 가정이 완전히.." '일본도' 희생자는 두 아이 아빠였다 / JTBC 뉴스룸](https://www.youtube.com/watch?v=jGW8acyYvVo) |
| 6 | MBCNEWS | 603,332 | 1:58 | [[오늘 이 뉴스] 일본도 피의자 마스크 내리더니 "멀쩡한 정신으로 범행" 기겁 (2024.08.01/MBC뉴스)](https://www.youtube.com/watch?v=ZrJX2BdMgzg) |
| 7 | 채널A News | 460,209 | 0:47 | [[자막뉴스] '일본도' 휘두른 30대... “대기업 퇴사 후 무례해져” / 채널A](https://www.youtube.com/watch?v=gYEKbX9GF5A) |
| 8 | 채널A News | 436,885 | 0:55 | [[자막뉴스] '80cm 일본도' 휘둘러 살해 얼굴만 아는 사이였다 / 채널A](https://www.youtube.com/watch?v=Bly7KaDCsj4) |
| 9 | kimwontv김원 | 385,188 | 23:43 | [【충격 CCTV 공개】 일본도 살인사건 백씨와 조력자ㅣ김원사건파일](https://www.youtube.com/watch?v=VN2R3N_ztgQ) |
| 10 | MBCNEWS | 358,166 | 1:57 | [아파트 단지 앞 이웃 살해, 흉기는 '일본도' (2024.07.30/뉴스데스크/MBC)](https://www.youtube.com/watch?v=tkh12oL-438) |

### 별도. 인천 노래주점 허민우 살인

- 판결: 2021-12-23 항소심 징역 30년 확인; 상고하지 않아 확정됐다는 보조 정보. 
- 피해·범위: 피해자 40대 남성 손님.
- 서사: **깊음**. 술값 시비와 폭행 → 실종 신고 → CCTV 수사 → 시신 유기와 검거 → 집행유예 기간 범행 → 항소심 30년
- 편집·경쟁: 가게에 들어간 손님이 나오지 않은 동선을 추적. 상대적으로 낮음~중간. 사건의뢰 중심이며 대형 뉴스 조회는 상대적으로 작음.
- 관측 합계 2,420,019회, 중앙값 184,140회, 8채널, 8분 이상 7/10편.
- 근거: [연합뉴스·1심 30년](https://www.yna.co.kr/view/AKR20210910095851065) · [뉴스핌·2021-12-23 항소심 30년](https://www.newspim.com/news/view/20211223000839) · [위키·상고하지 않아 확정됐다는 보조 정보](https://thewiki.kr/w/허민우)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | 사건의뢰 | 822,476 | 50:47 | ["He had a criminal record, but he was a good person?" Heo Min-woo, a former member of the Incheon...](https://www.youtube.com/watch?v=8Odw_arg-5Y) |
| 2 | 디바제시카DeevaJessica | 314,061 | 41:16 | [인천 조폭 '꼴망파' 셔터내린 노래방에서 시신 7등분으로..](https://www.youtube.com/watch?v=78gWwVpTAOQ) |
| 3 | 사건의뢰 | 253,966 | 23:53 | [A Crime That Started with an 80,000 Won Drink Price: The Incheon Karaoke Bar Murder](https://www.youtube.com/watch?v=RfKMmeCDTdI) |
| 4 | SBS 뉴스 | 232,473 | 1:51 | ["범행 잔혹" 34살 허민우 공개…집행유예 중 살인 / SBS](https://www.youtube.com/watch?v=qi0aa8D7cGk) |
| 5 | kimwontv김원 | 205,392 | 31:20 | [【인천 노래방 살인사건】 "들어간 사람은 2명, 나온 사람은 1명?"ㅣ신상공개ㅣ김원사건파일](https://www.youtube.com/watch?v=Qe4OIBtUX_4) |
| 6 | YTN | 162,888 | 2:05 | [마스크 벗은 허민우 "유기 장소 찾아가 술 따라줬다" / YTN](https://www.youtube.com/watch?v=9jV3Eabmi3E) |
| 7 | 현대사TV | 144,937 | 8:54 | [정신 못차린 조폭XX ...[ 인천노래주점 살인사건 ]](https://www.youtube.com/watch?v=ZqY-xNfSdyA) |
| 8 | JTBC News | 107,295 | 9:01 | ['노래주점 살인' 허민우, 조폭 '꼴망파' 일원…보호관찰 대상자 / JTBC 사건반장](https://www.youtube.com/watch?v=Xm-7Re2RK58) |
| 9 | JTBC News | 103,509 | 1:33 | [[현장영상] 마스크 벗은 허민우 "시신 버린 곳 4번 가서 술 따랐다, 죄송" / JTBC News](https://www.youtube.com/watch?v=85ps65AL3lA) |
| 10 | MBN News | 73,022 | 9:39 | [MBN 뉴스파이터-스스로 마스크 벗은 허민우 "유기 장소 가서 술 따랐다"](https://www.youtube.com/watch?v=FbI2Ow2kbEg) |

### 별도. 유영철 연쇄살인

- 판결: 사형 확정; 2005-06-09 이문동 무죄 부분까지 재판 종결. 
- 피해·범위: 상세 제외 사유 참조
- 서사: **매우 깊음**. 성인 20명 살인 본건을 미성년 살인으로 오기하지 않음. 다만 2004고합972 판결문에 별건 미성년자 강간 전력이 명시되고 혜화동 영아가 남아 있는 집의 방화도 포함됨. 전체 행적을 다루는 장편은 성범죄·미성년 관련 장면을 끌어들이므로 이번에는 편집상 제외. 성인 살인 부분만 분리하는 조건부 제작 가능성은 남김.
- 편집·경쟁:  매우 높음. 기존 엑스톨 유영철 체포 작전도 존재.
- 관측 합계 23,763,925회, 중앙값 2,280,296회, 9채널, 8분 이상 9/10편.
- 근거: [서울중앙지법 2004고합972 등·별건 미성년 강간 전력과 영아 있는 혜화동 방화](https://casenote.kr/서울중앙지방법원/2004고합972) · [법률신문·20명 살인 유죄, 이문동 무죄 및 2005-06-09 재판 종결](https://www.lawtimes.co.kr/news/articleView.html?idxno=16241)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | 그것이 알고싶다 | 5,104,359 | 13:59 | [권일용 프로파일러의 유영철 면담 뒷이야기 · 그알 외전 3회_1부](https://www.youtube.com/watch?v=vAO2_Pzdr6M) |
| 2 | tvN Joy | 3,068,386 | 17:21 | [※분노주의※ 유영철 사건부터 그의 감옥생활까지😡 #highlight #알쓸범잡 EP.3](https://www.youtube.com/watch?v=DbJpZXj2lHw) |
| 3 | 그것이 알고싶다 | 2,545,711 | 11:18 | [[ENG] 영화 ‘추격자’ 실화! 희대의 연쇄살인마 유영철 · 그알로 보는 '연쇄살인마'](https://www.youtube.com/watch?v=QpBPEcFj3e8) |
| 4 | 디바제시카DeevaJessica | 2,401,075 | 22:06 | [#1 Psychopath Serial Killer Yoo Young-chul · Saturday Mystery · Diva Jessica](https://www.youtube.com/watch?v=z3S5vxY1rw4) |
| 5 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 2,286,535 | 21:00 | [[꼬꼬무 149회 요약] '이 친구가 정말 사이코패스구나' 교도관도 소름 끼치게 한 유영철의 이야기 · 꼬리에 꼬리를 무는 그날 이야기(SBS방송) #꼬리에꼬리를무는그날이야기](https://www.youtube.com/watch?v=4xmTtJNcfmE) |
| 6 | KBS 교양 | 2,274,058 | 38:49 | [[A Double Life Episode 10 Summary] "I killed people. 27 of them!" Serial Killer Yoo Young-chul! W...](https://www.youtube.com/watch?v=KHwEHmnkWIA) |
| 7 | 괴인협회 | 2,006,494 | 5:59 | [Yoo Young-chul: 15 Facts You Didn't Know](https://www.youtube.com/watch?v=piUkvveDNeU) |
| 8 | 엠빅뉴스 | 1,398,773 | 9:54 | [[이거 실화야?] 경찰을 꿈꿨던 유영철은 어떻게 살인중독이 되었나.. 스스로에게 취한 악마? "거긴 내가 너희들의 삶과 죽음을 결정하는 문턱이야..!"](https://www.youtube.com/watch?v=pESPBCEMTRg) |
| 9 | 사건의뢰 | 1,397,694 | 85:47 | [[대한민국 살인사건 22화] 드디어 유영철! 그가 스스로 말한 내용 입수!](https://www.youtube.com/watch?v=LhuG-beg0z4) |
| 10 | MBC every1 | 1,280,840 | 151:08 | [[사건모음 2시간] 희대의 연쇄살인마 유영철과 그의 롤모델 정두영, 그리고 장재진까지 · #히든아이 · #MBCevery1 · EP. 76외](https://www.youtube.com/watch?v=NZxjLSBWiI8) |

직접 형식 경쟁: [엑스톨 영상](https://www.youtube.com/watch?v=H_GaGKQp17k) 561,092회. 표본10 합계에 포함됐는지는 영상 ID로 구분.

### 별도. 지존파

- 판결: 1995년 사형 집행 확인. 
- 피해·범위: 상세 제외 사유 참조
- 서사: **매우 깊음**. 납치·강간·살인이 하나의 연속 사건이며 탈출한 생존자도 성폭행 피해자. 성범죄를 제거하면 사건 핵심과 탈출 동기를 왜곡하게 되어 제외.
- 편집·경쟁:  매우 높음
- 관측 합계 28,946,090회, 중앙값 1,677,589회, 9채널, 8분 이상 8/10편.
- 근거: [연합뉴스·첫 피해자 성폭행](https://www.yna.co.kr/view/AKR19940922003300063) · [MBC·탈출 생존자 성폭행 피해](https://imnews.imbc.com/replay/1994/nwdesk/article/1938820_30690.html)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | SBS | 8,918,042 | 27:22 | [[꼬꼬무] 요약 '악마들의 살인공장' 지존파 ＂이 세상 법이 X 같은 거야＂ · SBS NOW](https://www.youtube.com/watch?v=uSZQpqcvy2Q) |
| 2 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 8,442,115 | 27:31 | [[꼬꼬무 5회 요약] ＂더 죽이지 못해 한일 뿐＂ 살인공장 지존파, 그들은 누구? · 꼬리에 꼬리를 무는 그날 이야기](https://www.youtube.com/watch?v=DGt5LkiBwi8) |
| 3 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 2,303,847 | 14:51 | [[꼬꼬무 153회 요약] 사형 집행 교도관이 기억하는 '지존파'부터 '홍순영'까지 · 꼬리에 꼬리를 무는 그날 이야기(SBS방송) #꼬리에꼬리를무는그날이야기](https://www.youtube.com/watch?v=d41AMpOTqyA) |
| 4 | 현대사TV | 1,743,263 | 9:23 | [지존파중에서도 진짜 악마였던 [두목 김기환]](https://www.youtube.com/watch?v=zXXGB6jqF8c) |
| 5 | 사건의뢰 | 1,725,980 | 94:15 | [[ENG SUB][대한민국 살인사건 제4화]'지존파' 진짜 이야기-그들의 '아지트'에서는 무슨 일이 있었는가? 결성부터 검거까지](https://www.youtube.com/watch?v=emNs1riqGQk) |
| 6 | JY Lee | 1,629,198 | 7:01 | [지존파](https://www.youtube.com/watch?v=wkIsSk3IvCo) |
| 7 | 채널A WORLD | 1,099,197 | 68:30 | [[#밥친구] "전두환은 무죄인데 나는 왜 유죄냐" 살인공장까지 만든 희대의 살인 조직 지존파 · #블랙 악마를 보았다 10회](https://www.youtube.com/watch?v=3mt7rJlOg2Y) |
| 8 | 디바제시카DeevaJessica | 1,092,641 | 14:42 | [#1 실제 상황! 살인조직 지존파ㅣ토요미스테리ㅣ디바제시카(Deeva Jessica)](https://www.youtube.com/watch?v=TV18bfN7c_0) |
| 9 | TV 네영카 (네영카) | 1,003,324 | 2:05 | [지존파 사건일지 뉴스 비보도 미공개영상 단독 최초공개!](https://www.youtube.com/watch?v=as3NCqlDcWI) |
| 10 | 초신자의 시선 | 988,483 | 9:41 | [지존파 김현양 사형집행직전 고백 & 유언 & 간증](https://www.youtube.com/watch?v=Yvg5uiJQC80) |

### 별도. 우순경 우범곤 총기난사

- 판결: 범인 현장 자폭 사망; 본인에 대한 확정 유죄판결 없음. 
- 피해·범위: 상세 제외 사유 참조
- 서사: **매우 깊음**. 미성년·영아 피해 포함, 동거녀도 피살되어 친밀관계 폭력 포함. 범인이 현장에서 사망해 확정판결 조건도 충족하지 못함.
- 편집·경쟁:  매우 높음. 엑스톨 직접 경쟁 영상 존재.
- 관측 합계 14,659,790회, 중앙값 657,448회, 9채널, 8분 이상 9/10편.
- 근거: [중앙일보·미성년 피해·동거녀 사망·범인 자폭](https://www.joongang.co.kr/article/25244762)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | KBS 교양 | 5,305,495 | 24:11 | [마을 순경은 왜 하룻밤 사이에 62명을 살해한 것일까 · 우순경 총기난사 사건의 진실  KBS 180705 방송](https://www.youtube.com/watch?v=vfG2obptphE) |
| 2 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 4,599,659 | 20:35 | [[Kkokkomu Ep. 6 Summary] A 'Police Officer' Who Killed 56 People in 6 Hours? A Murderous Rampage ...](https://www.youtube.com/watch?v=EpAuJq_5n00) |
| 3 | 사건의뢰 | 1,381,628 | 67:07 | [[ENG SUB][대한민국 살인사건 제 11화] 우범곤 사건 - 왜 그는 그토록 분노했나](https://www.youtube.com/watch?v=_0_aq72pFn8) |
| 4 | 디바제시카DeevaJessica | 768,369 | 14:35 | [#2 최단살인 기네스북 기록 우순경 총기난사(우범곤)ㅣ토요미스테리ㅣ디바제시카](https://www.youtube.com/watch?v=TjRMx8ucB6c) |
| 5 | 괴인협회 | 707,959 | 6:18 | [우범곤, 당신이 몰랐던 14가지 사실](https://www.youtube.com/watch?v=Ne0Jf_vPfXo) |
| 6 | 익스트림한 | 606,937 | 16:59 | [The Worst Serial Killer in South Korean History Who Made the Guinness World Records](https://www.youtube.com/watch?v=xnkv0CLwMzo) |
| 7 | 사건의뢰 | 419,971 | 34:42 | [[스모킹건2] 기네스 세계 기록 등재된 최악의 사건. 당시 사건 현장에 있던 유가족이 들려주는 그날의 이야기(무편집본)](https://www.youtube.com/watch?v=WNdlbNH9LWo) |
| 8 | 올빼미TV | 401,886 | 8:16 | [우순경 사건후 마을에는 빈집만 남았다](https://www.youtube.com/watch?v=Gqu8qyeRK7M) |
| 9 | 엑스톨(Extol) | 248,989 | 8:42 | [8시간 만에 56명이 사망한 대한민국 최초 총기난사 사건](https://www.youtube.com/watch?v=OwQm8ZIZfiQ) |
| 10 | 공포라디오0.4MHz 쌈무이 | 218,897 | 38:28 | [[Ssammui Horror Radio Short] The Woo Sun-kyung Shooting Incident - The Woo Beom-gon Shooting Inci...](https://www.youtube.com/watch?v=PZRIVaPiu70) |

직접 형식 경쟁: [엑스톨 영상](https://www.youtube.com/watch?v=OwQm8ZIZfiQ) 248,989회. 표본10 합계에 포함됐는지는 영상 ID로 구분.

### 별도. 대구지하철 방화

- 판결: 김대한 1심 무기징역 확인; 제외 후 최종심 추가조사는 생략. 
- 피해·범위: 상세 제외 사유 참조
- 서사: **매우 깊음**. 공개 희생자 명단에 16·17세 등 미성년 피해가 포함됨. 성인 피해자만 따로 잘라 참사 전체를 다루는 방식은 채택하지 않음.
- 편집·경쟁:  매우 높음
- 관측 합계 14,734,642회, 중앙값 1,011,545회, 10채널, 8분 이상 8/10편.
- 근거: [대구일보·사망자 명단에 16·17세 등](https://www.idaegu.com/news/articleView.html?idxno=18056) · [연합뉴스·김대한 1심 무기징역](https://www.yna.co.kr/view/AKR20030806001300053)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 5,068,968 | 21:45 | [[Kkokkomu Ep. 27 Summary] The Worst Railway Disaster in History! The Daegu Subway Fire Was a Fore...](https://www.youtube.com/watch?v=0zD9L13J2p8) |
| 2 | 디바제시카DeevaJessica | 2,195,514 | 32:00 | [*대구 지하철 참사 비극의 현장ㅣ토요미스테리 ·ㅣ디바제시카](https://www.youtube.com/watch?v=aYkVHVTmgqA) |
| 3 | tvN D ENT | 1,596,839 | 18:38 | [[#유퀴즈온더블럭] 화재현장 베테랑 김명배 소방위님이 기억하는 대구 지하철 화재사건 · #갓구운클립 #Diggle](https://www.youtube.com/watch?v=tv_1-O5sfPY) |
| 4 | 디글 :Diggle | 1,537,363 | 19:50 | [[#사건의재구성] 세계 3대 지하철 사고로 알려진 2003년 2월의 대구. 자신의 우울을 핑계로 불을 내고 도망간 범인 김대한 · #알쓸범잡 #디글](https://www.youtube.com/watch?v=LykAvrjLDic) |
| 5 | tvN Joy | 1,092,990 | 15:31 | [[알쓸범잡 부록] 방화벽 옆엔 비상문이 있다! 대구 지하철 참사 그 후, 우리가 알아야 할 것들#알쓸범잡 · crimetrivia EP.5](https://www.youtube.com/watch?v=fWJ2Qy2fPs8) |
| 6 | 지식코리야 | 930,100 | 8:11 | [4 Shocking Reasons About the Daegu Subway Disaster That 99% of People Don't Know](https://www.youtube.com/watch?v=Qlmogk42Rb0) |
| 7 | 사건현대사 | 774,129 | 8:12 | ['대구지하철 화재사건'의 비밀.](https://www.youtube.com/watch?v=Le7fyp2FOd8) |
| 8 | 실화 On | 538,485 | 2:14 | [[Dark History of South Korea] Daegu Subway Disaster: Communication Recordings Revealed](https://www.youtube.com/watch?v=xRIrSLKP-u8) |
| 9 | KBS News | 517,152 | 1:41 | [[그때 그 뉴스] 대구지하철 방화참사](https://www.youtube.com/watch?v=ng5A5n2bzo8) |
| 10 | 조은영화 | 483,102 | 49:55 | [🔥 The shocking truth behind the Daegu subway disaster not reported in the news, the worst arson a...](https://www.youtube.com/watch?v=Fh5bTV6KZQ8) |

### 별도. 김대두 연쇄살인

- 판결: 1976-03 사형 확정·동년 집행. 
- 피해·범위: 상세 제외 사유 참조
- 서사: **매우 깊음**. 영아·어린이 살인과 강간이 범행군에 포함됨. 미성년 피해·성범죄 두 조건으로 제외.
- 편집·경쟁:  중간
- 관측 합계 3,102,338회, 중앙값 191,262회, 10채널, 8분 이상 10/10편.
- 근거: [중앙일보·아동 피해·강간·1976-03 사형 확정](https://www.joongang.co.kr/article/4336010) · [매일경제·강도살인·강간 1심](https://www.mk.co.kr/news/economy/304319)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | 디바제시카DeevaJessica | 1,232,287 | 15:33 | [구경꾼들에게 웃음을 날린다.. 한국최초 연쇄살인마 김대두 · 토요미스테리 · 디바제시카](https://www.youtube.com/watch?v=F9J79PFNNRY) |
| 2 | JTBC News | 495,772 | 21:03 | ['2개월 살인여행' 17명을 흉기로…대한민국 최초 연쇄살인범 김대두 / JTBC 사건반장](https://www.youtube.com/watch?v=ekmKd6sp2jM) |
| 3 | 사건의뢰 뒷방 | 385,448 | 27:37 | [[South Korean Murder Case Summary] Why Did He Become a Serial Killer? - Kim Dae-doo](https://www.youtube.com/watch?v=9I5fB7wJruQ) |
| 4 | 사건의뢰 | 295,542 | 41:40 | [10,000 Prisoners I Met - Death Row Inmates, Murderers, and Kim Dae-doo](https://www.youtube.com/watch?v=D7HPq2FSDwE) |
| 5 | 김복준의 사건속으로 | 228,119 | 52:55 | [[다시보는 대한민국살인사건 67화] - 국내 최초 연쇄살인마, 김대두](https://www.youtube.com/watch?v=MloLBqRtqm8) |
| 6 | 미스스한 이야기 | 154,405 | 8:23 | [그는 진짜 범인이었나? 한국 최초의 연쇄살인마 김대두](https://www.youtube.com/watch?v=yhnm21t2CyI) |
| 7 | kimwontv김원 | 140,122 | 31:32 | [【(19세)충격 주장, 연쇄살인마가 아니다?】 최초의 연쇄살인마 김대두, 그 주장은 진실일까?ㅣ김원사건파일](https://www.youtube.com/watch?v=y5BIIw65O2c) |
| 8 | Ope Duna | 95,691 | 47:42 | [Reconstruction of Crime E21 The First Serial Killer Kim Dae-du](https://www.youtube.com/watch?v=oP-aYR0VZLI) |
| 9 | 왓섭! 공포라디오 | 54,618 | 10:46 | [[사건파일] 한국 최초의 연쇄 살인마 ‘김대두’｜왓섭! 공포라디오](https://www.youtube.com/watch?v=NCQQqBRRY50) |
| 10 | 노트13 | 20,334 | 15:14 | [1975년 대한민국을 공포에 빠뜨린 연쇄살인범 김대두 · 55일간의 추적](https://www.youtube.com/watch?v=XS0GrbJIw6U) |

### 별도. 온보현 연쇄 납치살인

- 판결: 사형·1995-11-02 집행. 
- 피해·범위: 상세 제외 사유 참조
- 서사: **깊음**. 생존 피해자 성폭행과 성폭행에 저항한 피해자 살인이 결합됨. 살해된 두 명 모두 강간 기수 피해자였다고 쓰면 오보이며, 강간 미수·다른 생존자의 성폭행을 구분해도 성범죄 제외 조건에 해당.
- 편집·경쟁:  중간~높음
- 관측 합계 5,530,325회, 중앙값 279,148회, 10채널, 8분 이상 9/10편.
- 근거: [중앙일보·2명 살해·4명 성폭행](https://www.joongang.co.kr/article/2969942) · [한국일보·살해 피해자들은 성폭행에 저항, 다른 생존 성폭행 피해와 구별](https://www.hankookilbo.com/news/article/199511100072247630)

| # | 채널 | 관측 조회수 | 길이 | 영상 |
|---:|---|---:|---:|---|
| 1 | KBS 교양 | 1,844,516 | 36:31 | [[Face the Facts Ep. 8 Recap] "I will kill as many people as my age." Taxi serial killer 'On Bo-hy...](https://www.youtube.com/watch?v=5hp5hW3Rg9Q) |
| 2 | 사건의뢰 | 1,268,428 | 67:47 | [[South Korean Murder Cases Ep. 3] You're Comparing Me to the Jijon Clan? The Killer On Bo-hyun - ...](https://www.youtube.com/watch?v=UNTTZmkTO7o) |
| 3 | 달리 [SBS DALI] - SBS 공식 교양 채널 | 980,415 | 14:59 | [[꼬꼬무 174회 요약] 그 남자가 범죄 내용을 모두 기록해 둔 이유 · 꼬리에 꼬리를 무는 그날 이야기 (SBS방송) #꼬리에꼬리를무는그날이야기](https://www.youtube.com/watch?v=puLgRuMniKE) |
| 4 | 채널A News | 629,939 | 18:15 | [[판결의 재구성]사라진 여성들…‘살인 일기’ 온보현 사건  · 사건상황실](https://www.youtube.com/watch?v=fF99bSbqK8Y) |
| 5 | 디바제시카DeevaJessica | 457,137 | 44:19 | [너무 빨리 사형당해서 알려질 시간도 없었던 '죽음의 택시' 연쇄살인마 온보현](https://www.youtube.com/watch?v=x9wHu6kw2II) |
| 6 | JTBC News | 101,160 | 19:25 | [살인택시 공포로 몰아넣은 '온보현'…왜 여성 승객만 노렸나 / JTBC 사건반장](https://www.youtube.com/watch?v=LPX_7-ABdPc) |
| 7 | 뉴스공장 | 70,733 | 1:24 | [News of Kim Hyun-yang and On Bo-hyun's Executions (11/2/1995)](https://www.youtube.com/watch?v=GOCEsuARUk4) |
| 8 | 신지우 shinjiwoo | 63,220 | 26:50 | [[Mystery Crime] Taxi Crimes 3 - The On Bo-hyun Serial Murder Case](https://www.youtube.com/watch?v=g9pYRyO0XxU) |
| 9 | Ope Duna | 59,636 | 47:31 | [범죄의 재구성 E02 온보현 살인의 기록의 사본](https://www.youtube.com/watch?v=QFlRhXN65MI) |
| 10 | 디바제시카 국내사건모음 | 55,141 | 44:19 | ['Death Taxi' Serial Killer On Bo-hyun, Who Was Executed Too Quickly to Even Be Known · Diva Jessi...](https://www.youtube.com/watch?v=eEP_WrFCzD8) |

## 표본 오염을 제거한 예

막가파 비유를 쓴 커피배달 여성 별건(129만 회), 영화 리뷰(190만 회), 정치 뉴스는 제외했다. 신창원 원숭이(101만 회), 신창원보다 앞선 다른 탈주범, 정두영 교수·정유정 작가, 신림 등산로 성폭행, 2021년 배우자 일본도 살인, 필리핀 한인사업가 별건도 해당 사건 합계에 넣지 않았다. 혼합 프로그램이 실제 해당 사건을 포함하면 노출 표본에 남겼고, 같은 프로그램 재편집의 중복 도달 가능성을 인정했다. 상세 ID와 이유는 JSON에 있다.

## 기존 후보 유지 사항

N18 군기훈련 사망은 기존 제작 맥락과 조사값을 보존했다. N17 은평구 일본도는 유지하되 **실제 확정 2025-09-25 / 보도 10-24**로 구분을 정정했다. N16 시청역은 교통과실, N12 경남은행은 비폭력 횡령이라 이번 고의 강력범죄 수사극 TOP10의 후순위·별도 풀로 남겼다. N13 대리기사 폭행은 기존 기록이 상고 진행 단계이므로 확정 후보로 올리지 않았다. 원본 조사 파일은 모두 그대로이며 기존 지수를 10-30 새 관측값으로 바꾸지 않았다.

Google Trends 접근 권한 거부로 두 기간의 수요 측정이 남아 있다. 이 문서의 순위는 판결·성인 피해 확인, 실제 YouTube 표본과 서사 깊이에 근거한 잠정 제작 우선순위다.
