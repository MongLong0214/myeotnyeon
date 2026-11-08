import json,re,statistics,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
d=json.loads((R/'devices.json').read_text())
new=json.loads((R/'rewrite_timing.json').read_text())
def stamp(s):return f'{int(s)//60:02}:{s%60:05.2f}'
def cell(v):return str(v).replace('|','/')
def table(headers,rows):return ['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(cell(v) for v in row)+' |' for row in rows]
def c(k,n):x=d[k]['device_counts'][n];return f"{x['count']} / {x['per_minute']:.2f}"
o=['# 엑스톨 신창원: 서사·나레이션·사운드 측정과 N18 비교','',
 '측정 대상: 지정 URL의 오디오 534.613초(08:54.61), 지정 N18 fast 프리뷰 영상 272.00초(04:32.00; 오디오 271.915초). 대본 파일의 06:15.30과 다른 버전이다. 이하 “우리”의 시간·밀도는 실제 fast 프리뷰 기준이며, 나레이션 문구·어미는 script.md의 63행을 기준으로 확인했다. 원본 대본의 설계 수치 4.95음절/초를 fast 오디오의 속도로 오인하지 않는다.','',
 '네트워크는 yt-dlp -f bestaudio -x --audio-format wav로 지정 레퍼런스 오디오를 받는 데만 사용했다. 로그인·쿠키·업로드·동영상 다운로드·기사 조회·모델 다운로드 없음. 첫 1분 시각 내용과 장 카드는 이전 ref-cuts 작업이 W에 보관한 로컬 이미지·영상으로 확인했다. 새로 내려받은 것은 오디오뿐이다. 다운로드 로그는 download.log.','',
 '전사: mlx_whisper, 한국어, word_timestamps=True, 로컬 whisper-large-v3-turbo. large 계열의 turbo 모델이며 전체 large-v3와 동일한 모델이라고 부르지 않는다. HF_HUB_OFFLINE=1로 실행했다. 원시 전사는 reference_transcript.json/txt와 ours_fast_transcript.json/txt에 보존했다. 특히 06:58.30–07:37.02의 신고전화 ASR는 오류가 많다. 전화 내용의 정확한 대사·지명·직업을 전사만으로 인용하거나 사건 사실로 채택하지 않았다.','',
 '## 해석을 바꾼 결과','',
 '레퍼런스의 힘을 “-죠/-요, 짧은 문장, 질문이 많음”으로 설명하면 측정과 맞지 않는다. 기록 음성을 제외한 나레이션 85문장은 전부 -습니다 계열이며 직접 질문·시청자 호명은 0회다. 평균 문장도 우리보다 길다. 차이는 물리적 목표→장애물→시도→반전→다음 목표의 연쇄, 앞에서 보여준 의문을 뒤에서 푸는 순서, 배경음의 지속과 변화다.','',
 '흥미의 인과관계는 단일 영상 비교로 증명할 수 없다. 시청 유지율·이탈 지점은 제공받지 않았다. 아래는 새 대본의 편집 선택을 설명하는 관찰과 가설이다. 대화체·질문 도입은 이번에 허용된 새 창작 선택이며 레퍼런스의 어미 분포를 그대로 복제한 결과가 아니다.','',
 '## 같은 기준의 비교표','',
 '횟수 표기의 “개수 / 분당”은 전체 미디어 길이가 분모다. 어미·문장·속도에서는 레퍼런스의 38.72초 기록 음성 삽입을 제외한다. 의미 장치들은 중복 코딩될 수 있다.','']
metrics=[('목표·장애물로 시작하는 cold open','cold_open'),('열린 질문 / 회수 루프','open_loops'),('장 끝 cliffhanger','chapter_ending_cliffhangers'),('그런데·하지만만','그런데_하지만_only'),('넓은 역접 표지','reversal_markers'),('구체 디테일 표식','specific_details'),('위험·이해관계·대조','stakes_contrast'),('복선·앞일 예고','foreshadowing'),('의도적인 해법·결과 유예','reveal_withholding'),('유머·반어적 대비','humor_irony'),('인용 음성 블록','quotes'),('수사적 직접 질문','rhetorical_questions'),('시청자 직접 호명','direct_address')]
# Cold open is an editorial classification, not simply the existence of a first shot.
for k,count in [('reference',1),('ours_fast',0)]:
 d[k]['device_counts']['cold_open']={'count':count,'per_minute':round(count/(d[k]['duration_s']/60),3)}
 d[k]['device_events']['cold_open']=([{'start_s':0,'end_s':17.94,'description':'탈옥 실행 직전의 목표 제시; 본문 설명 이전'}] if count else [])
o+=table(['측정 항목','레퍼런스: 개수 / 분당','우리 fast: 개수 / 분당'],[(title,c('reference',key),c('ours_fast',key)) for title,key in metrics])
o+=['','구체 디테일은 전사에서 숫자·물건·장소·시간의 명시적 표식을 세었다. 같은 대상의 재등장도 다시 센다. 날짜의 년·월·일은 각각 숫자 표식이며 형량·심급 숫자도 포함한다. 숫자가 많다고 현장감이 강하다고 단정할 수 없다. 장소/시간/숫자 태그는 일부 중첩되므로 아래 합계는 전체 고유 표식 수와 일치하지 않을 수 있다. 숫자 없이 암시된 묘사까지 세었다는 뜻은 아니다.','']
o+=table(['디테일 태그','레퍼런스: 개수 / 분당','우리: 개수 / 분당'],[(tag,*[f"{sum(tag in e['tags'] for e in d[k]['device_events']['specific_details'])} / {sum(tag in e['tags'] for e in d[k]['device_events']['specific_details'])/(d[k]['duration_s']/60):.2f}" for k in ['reference','ours_fast']]) for tag in ['number','object','place','time']])
o+=['','레퍼런스의 물건 표식 48회는 환풍구·창살·파이프·밧줄·톱날·운동화 밑창·껌·가스총처럼 이후 행동을 바꾸는 대상이다. 우리 기존 나레이션은 같은 물건 사전에서 0회였다. 이 차이를 반영해 v2는 E03의 완전군장·선착순 뜀걸음·팔굽혀펴기를 앞에 배치했다. 출처 없는 체중·무게·입대일을 보충하지 않았다.','',
 '## 처음 15초와 60초','']
o+=table(['범위','레퍼런스: 보이는 것 / 말하는 내용','우리 fast: 보이는 것 / 말하는 내용'],[
 ('00:00–00:15','교도소 외곽→감방 안 기상→인물 소개. 구체적인 일시·방 위치·수감 상태·인물을 제시한다. 탈옥 준비 언급은 14.26초부터 시작하고 목표 문장은 17.94초에 끝난다. 첫 15초 안에 실행 목표를 다 말했다고 과장하지 않는다.','네온 인체와 훈련병 대열·날짜·혐의 자막. 날짜→부대→6명→절차·방법 위반→부중대장 혐의 설명. 직접 질문·실행 목표 없음.'),
 ('00:15–01:00','화장실→환풍구→쉽게 제거되는 창살→좁은 통로→밖으로 나옴→아직 탈출 아님→공사장 벽→땅 파기→파이프·밧줄. 왜 쉽게 제거됐는지, 좁은 통로를 어떻게 준비했는지는 뒤로 남김.','적절한 조치 미실시 혐의→22.62–24.20초 사망 설명→인과관계·행위 구별 쟁점→혐의 문서. 중대장 측 부인 문장은 60.40초 이후여서 첫 1분에 검찰·변호인의 충돌은 완성되지 않음.')])
o+=['','레퍼런스의 첫 1분은 “얼마나 좁은가/높은가/멀리 있는가”를 다음 행동의 조건으로 쓰는 구간이다. 우리 첫 1분은 사건의 분류·혐의를 설명하는 구간이다. v2는 사망을 숨기는 대신 행동의 구체성에서 시작하고 법원 판단을 열린 질문으로 삼았다.','',
 '## 비트 시트','']
for key,title in [('reference','레퍼런스'),('ours_fast','우리 fast')]:
 o += ['### '+title,'']
 o += table(['시간','비트 유형','내용(레퍼런스는 그 영상의 서술 요약)','루프'],[(f"{stamp(b['start_s'])}–{stamp(b['end_s'])}",b['type'],b['description'],b['loops']) for b in d[key]['beats']])
 o += ['']
o += ['## 열린 질문과 회수 시간','', '루프는 시청자가 답을 기다릴 수 있는 목표·수수께끼의 제기와 해소 한 쌍이다. 단순히 뒤에 숫자가 나온다는 이유만으로 모두 유예로 세지 않았다. 우리 2개는 설명형 쟁점 예고로 보수적으로 인정했다.','']
o+=table(['대상·ID','의문','제기','회수','대기'],[(('레퍼런스' if key=='reference' else '우리')+' '+l['id'],l['question'],stamp(l['raised_s']),stamp(l['closed_s']),f"{l['wait_s']:.2f}초") for key in ['reference','ours_fast'] for l in d[key]['open_loops']])
o+=['','## 모든 장 끝 cliffhanger','',
 '장 카드 시각은 로컬 정지화면 확인 지점(±약 0.5초)이다. 01 무기수, 02 탈옥 계획, 03 도주 생활, 04 체포 작전으로 진입한다. 엔딩에는 새 의문을 만들지 않는다. 세 번째는 강한 위기 중단보다 순환 연결에 가깝다.','']
o+=table(['직전 발화','장 진입','장치','열어 둔 것'],[(f"{stamp(x['lead_start_s'])}–{stamp(x['lead_end_s'])}",stamp(x['boundary_s']),x['type'],x['description']) for x in d['reference']['chapter_ending_cliffhangers']])
o+=['','우리의 장 전환은 00:33.35, 01:28.70, 02:38.60, 03:44.10 부근이다. 각각 쟁점 예고·구형 재확인·부중대장 1심 선고 비교·재판부의 국가 기대 설명 뒤에 넘어간다. 적극적인 위기·질문·결과 유예로 장을 끊는 cliffhanger는 0개로 코딩했다.','',
 '## 장치 코딩 정의와 전체 이벤트','',
 'counts만 남기지 않았다. devices.json의 각 device_events 항목에 시작·끝·표식 또는 의미 요약을 기록했다. 숫자·물건·장소·시간은 ASR segment_id와 문자 위치도 저장했다. 이벤트 시각은 발화 절의 범위이며 단어의 시작처럼 가장하지 않는다. sentence JSON과 원시 word timestamp로 다시 확인할 수 있다.','',
 '- 역접: 좁게는 그런데·하지만, 넓게는 그러나·그럼에도·-지만 계열. 표지가 있다고 모두 강한 반전은 아니다.\n- stakes/contrast: 성공·실패의 대가, 대립하는 기대·현실, 사건 규모를 비교하는 한 덩어리. 여러 숫자가 나와도 같은 대조라면 1개.\n- foreshadowing: 뒤의 준비·도주·재도전·신고 장면을 기대하게 하는 선행 정보.\n- withholding: 앞의 의문에 답할 수 있는 해법·결과를 별도 뒷구간으로 미룬 편집.\n- humor/irony: 웃음 효과음 횟수가 아니라 가스총 위력과 실패, 도주범과 경찰 인사, 체포와 팬덤의 반어적 대비. 피해자 조롱을 뜻하지 않는다.\n- quotes: 레퍼런스가 신고전화로 제시한 기록 음성 한 블록 38.72초. 신문 구독 위장은 간접화법이므로 직접 인용 횟수에 더하지 않았다. 전화 블록의 질문·-요를 나레이터 말투로 세지 않았다.\n- 질문: 나레이터가 청자를 향해 던지는 직접 의문문. 간접 의문 표현은 제외.\n- 직접 호명: 여러분·시청자·당신에게 명시적으로 말 거는 표현. 양쪽 모두 0회.','',
 '## 나레이터 목소리','']
o+=table(['지표','레퍼런스 나레이션','우리 대본 / fast 오디오'],[
 ('문장 수',d['reference']['voice']['sentence_count'],d['ours_fast']['voice']['sentence_count']),
 ('-습니다·-ㅂ니다·입니다',f"{d['reference']['voice']['ending_shares']['습니다_ㅂ니다_입니다']:.0%}",f"{d['ours_fast']['voice']['ending_shares']['습니다_ㅂ니다_입니다']:.0%}"),
 ('-죠 / -요 / 해라체 -다','0% / 0% / 0%','0% / 0% / 100%'),
 ('평균 문장 길이: 정규화 음절',d['reference']['voice']['average_sentence_hangul_syllables_normalized'],d['ours_fast']['voice']['average_sentence_hangul_syllables_normalized']),
 ('평균 문장 길이: 어절',d['reference']['voice']['average_sentence_eojeol'],d['ours_fast']['voice']['average_sentence_eojeol']),
 ('직접 의문문 비율','0%','0%'),
 ('발화 구간 근사 음절/초',f"{d['reference']['voice']['narration_syllables_per_phrase_s']:.2f}",f"{d['ours_fast']['voice']['narration_syllables_per_phrase_s']:.2f}"),
 ('전체 길이 대비 나레이션 음절/초',f"{d['reference']['voice']['narration_syllables_per_timeline_s']:.2f}",f"{d['ours_fast']['voice']['narration_syllables_per_timeline_s']:.2f}")])
o+=['','문장 경계는 종결형을 기준으로 병합했다. “다 끝났다”의 부사 ‘다’와 ‘집집마다’의 ‘다’를 문장 끝으로 오인하지 않도록 확인했다. 숫자는 한글 읽기로 정규화했으나 cm·kg 같은 외래 단위 발음은 추가하지 않아 레퍼런스 음절 수에는 근사 오차가 있다. 원전사 인명·지명의 오인식도 사건 사실 검증으로 취급하지 않았다. 운율·억양·성우의 감정은 이 지표로 측정했다고 주장하지 않는다.','',
 'fast 프리뷰는 이미 약 6.40음절/초다. 새 대본을 더 빠르게만 읽히는 처방은 근거가 약하다. 원래 script.md의 4.95음절/초 설계와 fast 파일을 분리해서 봐야 한다. v2의 6.2–6.6음절/초는 속도 과시보다 짧은 문장·질문·장면 전환을 위한 편집 목표다.','',
 '## 음악·소리: 측정한 것과 모르는 것','',
 '16kHz stereo로 오프라인 분석했다. mono=(L+R)/2, side=(L−R)/2. 가운데에 놓인 음성은 side에서 줄어든다. 1초 RMS, side의 20–180Hz / 180–4000Hz / 4000–8000Hz 에너지, 단어 정렬 밖의 에너지를 저장했다. side RMS가 −50dBFS보다 높은 상태가 5초 이상 이어지는 구간을 “스테레오 배경 지속 근사치”로 삼았다. 이 값은 음악 분리 결과나 확정 음악 점유율이 아니다. 음성 리버브·효과음·환경음도 남고 mono 음악은 놓칠 수 있다.','']
o+=table(['음향 지표','레퍼런스','우리 fast'],[
 ('지속 side 배경 근사 구간','00:00–08:54, 534초 / 99.89%','검출 구간 없음 / 0%'),
 ('전체 side RMS',f"{d['reference']['audio']['side_dbfs']:.2f} dBFS",f"{d['ours_fast']['audio']['side_dbfs']:.2f} dBFS"),
 ('단어 정렬 밖 mono RMS',f"{d['reference']['audio']['mixed_nonword_dbfs']:.2f} dBFS",f"{d['ours_fast']['audio']['mixed_nonword_dbfs']:.2f} dBFS"),
 ('0.12초 이상 비단어 시간이 있는 1초 창 중 side >−50','104 / 106','0 / 20'),
 ('0.35초 이상 나레이션 단어 간격',len(d['reference']['audio']['narration_gaps_ge_350ms']),len(d['ours_fast']['audio']['narration_gaps_ge_350ms'])),
 ('−60dBFS 아래 ≥0.18초 혼합음 침묵','03:40.02–03:40.26(0.24초), 08:54.30–08:54.60(0.30초)','04:27.90–04:31.90(4.00초; 출처 꼬리)')])
o+=['','레퍼런스는 말이 멎어도 소리가 남는 쪽이다. 01:34.42–01:36.86, 02:27.10–02:29.26, 03:37.78–03:39.88, 06:39.24–06:41.58의 장 진입 전후 발화 쉼은 각각 약 2.44/2.16/2.10/2.34초지만 완전 무음으로 측정되지 않았다. 장 카드의 호흡과 디지털 침묵을 구별해야 한다. 혼합음 무음의 의도는 파형만으로 확정할 수 없다. 우리 대본의 사망 전 0.6초·선고 전 0.8초 침묵 계획은 fast MP4에서 그 길이의 혼합음 완전 침묵으로 검출되지 않았다.','',
 '### 장 경계 큐 변화 후보','',
 '경계 전후 각 2초 side 스펙트럼의 Hellinger 거리 ≥0.35 또는 RMS 변화 절댓값 ≥6dB이고, 양쪽 중 하나가 −50dBFS보다 높을 때 후보로 표시했다. 우리처럼 거의 0인 side의 수치 잡음을 곡 전환으로 세지 않는다. “다른 곡”이나 실제 악기·감정의 이름은 분리·청취 검증 없이 단정하지 않는다.','']
o+=table(['대상·경계','side 변화','스펙트럼 거리','변화 후보'],[(('레퍼런스' if key=='reference' else '우리')+' '+stamp(x['boundary_s']),f"{x['side_delta_db']:+.2f}dB",f"{x['spectral_hellinger']:.3f}",'예' if x['cue_change_candidate'] else '아니오') for key in ['reference','ours_fast'] for x in d[key]['audio']['chapter_cue_candidates']])
o+=['','레퍼런스 4개 중 3개, 우리 4개 중 0개가 위 기준을 통과했다. 거리·에너지 변화가 컷과 함께 나타난다는 뜻이며 음악 트랙 교체 횟수는 아니다.','',
 '### 공개 순간의 히트 후보','',
 '단어 타임스탬프에서 결과·숫자가 실제 발음되는 지점을 잡고 ±0.75초 안의 spectral-flux 피크를 측정했다. side는 중심 음성 억제, mono는 중심 효과음을 놓치지 않기 위한 보조다. mono 피크는 자음일 수도 있다. 전체 side 후보가 360개로 조밀하므로, 공개 순간과 가까웠다는 이유만으로 연출용 히트라고 확정하지 않는다.','']
o+=table(['대상·공개 발화','발화 시각','side 피크 시각(초)','mono 피크 시각(초)'],[(('레퍼런스' if key=='reference' else '우리')+' '+x['event'],stamp(x['time_s']),', '.join(str(p['time_s']) for p in x['side_onset_candidates']) or '없음',', '.join(str(p['time_s']) for p in x['mono_onset_candidates']) or '없음') for key in ['reference','ours_fast'] for x in d[key]['audio']['reveal_hit_candidates']])
o+=['','이 표는 공개 장면과 사운드 변화의 동시성 측정이다. 효과음 종류·실제 히트 개수·음악의 감정은 미확정이다. 상세 1초 에너지 곡선은 reference_audio_1s.csv와 ours_fast_audio_1s.csv, 피크는 *_side_onsets.csv, 모든 발화 쉼·침묵·경계 값은 devices.json에 있다.','',
 '## v2에 반영한 선택','',
 f'오프닝 18초, {new["syllables"]:,}음절, 편집 예상 {stamp(new["planned_duration_s"])}. 새 음성·영상은 생성하지 않았다. 본문 계획 컷은 {new["shot_count"]-2}개, 컷 길이는 {new["shot_duration_min_s"]:.2f}–{new["shot_duration_max_s"]:.2f}초이고 출처 2컷은 각 4초다. 속도 범위 전체 러닝타임도 대본에 적었다.','',
 '사건의 결과는 초반에 밝힌다. 대신 왜 유죄가 되었는지, 1심 선고는 얼마인지, 항소심이 무엇을 바꾸었는지, 증가는 얼마인지 순서대로 묻고 회수한다. 검찰·중대장 측·법원의 목소리를 구별하며 재판을 대립하는 주장과 판단의 흐름으로 만든다. 여섯 기록 탭은 피해자 수이지 범죄 개수가 아니다. 장마다 베드 강도와 악기 층을 바꾸고, 피해 사실 대신 선고 숫자 공개에만 히트를 쓴다.','',
 '입대 후 경과일·그날의 분 단위 시간표·군장 무게·날씨·개별 현장 발언·유족의 직접 발언·개별 최후진술은 facts.md의 채택 행이 없어 제외했다. 로컬 기사에 더 구체적인 말이 있더라도 사실표 밖의 내용을 새 대본에 몰래 추가하지 않았다.','',
 '## 보존물과 삭제','',
 '원시 전사·문장 단위 자료·장치 이벤트·음향 통계·다운로드/전사 로그와 측정 스크립트를 이 폴더에 보존한다. 다운로드 오디오와 임시 분석 WAV는 측정 후 삭제한다. 실제 삭제 상태와 해시는 cleanup.json에서 확인한다. 이전 ref-cuts 작업의 영상·오디오 파일은 다른 작업 소유물이므로 수정·삭제하지 않는다.']
(R/'beats.md').write_text('\n'.join(o)+'\n')
# Planned v2 text statistics are explicitly not audio measurements.
texts=[s.strip() for x in new['items'] for s in re.split('[.!?]',x['narration']) if s.strip()]
endings={'습니다_ㅂ니다_입니다':0,'죠_지요':0,'요':0,'다':0,'other':0}
for s in texts:
 cat='습니다_ㅂ니다_입니다' if s.endswith('니다') else '죠_지요' if s.endswith(('죠','지요')) else '요' if s.endswith('요') else '다' if s.endswith('다') else 'other';endings[cat]+=1
d['rewrite_planned']={'status':'script-only, no generated audio','syllables':new['syllables'],'duration_at_6_4_with_planned_pauses_s':new['planned_duration_s'],'sentence_count':len(texts),'ending_counts':endings,'question_count':sum(x['narration'].count('?') for x in new['items']),'average_sentence_hangul_syllables':new['syllables']/len(texts),'shot_count':new['shot_count']}
(R/'devices.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
print('beats.md and devices.json updated')
