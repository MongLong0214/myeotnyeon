from finalize import *
S=json.load(open(R/'summary.json'));K=['ref','ours','ours_fast'];names=['Extol','N18 기본','N18 fast'];rows=[]
def add(label,fn,fmt='.2f',status='측정'):
 vals=[fn(S[k]) for k in K];row={'metric':label,'status':status,**{k:vals[i] for i,k in enumerate(K)}};rows.append(row)
 return '| '+label+' | '+' | '.join(format(v,fmt) if isinstance(v,(float,int)) else str(v) for v in vals)+' | '+status+' |'
lines=[]
for label,fn,fmt,status in [
 ('영상 길이 (s)',lambda x:x['duration_s'],'.3f','측정'),('영상 fps',lambda x:x['fps'],'.0f','측정'),('숏 / 화면 단절 구간 수',lambda x:x['shot_count'],'.0f','측정·아래 정의'),('경계 수',lambda x:x['cut_count'],'.0f','측정'),('평균 숏 (s)',lambda x:x['mean_shot_s'],'.3f','측정'),('중앙값 숏 (s)',lambda x:x['median_shot_s'],'.3f','측정'),('P10 숏 (s)',lambda x:x['shot_percentiles_s']['p10'],'.3f','측정'),('P25 숏 (s)',lambda x:x['shot_percentiles_s']['p25'],'.3f','측정'),('P75 숏 (s)',lambda x:x['shot_percentiles_s']['p75'],'.3f','측정'),('P90 숏 (s)',lambda x:x['shot_percentiles_s']['p90'],'.3f','측정'),('P95 숏 (s)',lambda x:x['shot_percentiles_s']['p95'],'.3f','측정'),('최장 숏 (s)',lambda x:x['max_shot_s'],'.3f','측정'),('전체 컷/분',lambda x:x['cuts_per_minute'],'.2f','측정'),('첫 15s 경계 수',lambda x:x['sections'][0]['cut_count'],'.0f','측정'),('첫 15s 환산 컷/분',lambda x:x['sections'][0]['cuts_per_minute'],'.2f','측정'),('첫 60s 경계 수',lambda x:x['sections'][1]['cut_count'],'.0f','측정'),('실제 구도/주 화면 교체',lambda x:x['composition_change_count'],'.0f','시각 분류'),('동일 구도 리셋',lambda x:x['same_view_reset_count'],'.0f','시각 분류'),('광류 중앙값 (px/s, 폭320)',lambda x:x['flow_median_px_s_at_320w'],'.3f','측정'),('절대 scale 변화 중앙값 (%/s)',lambda x:x['abs_scale_change_pct_s_median'],'.3f','추정 affine'),('절 경계 컷 비중 (%)',lambda x:100*x['clause_boundary_estimate_share'],'.1f','ASR·문법 추정'),('±0.1s 온셋 일치 (%)',lambda x:100*x['onset_hit_proxy_share'],'.1f','효과음 대리지표'),('비단어 구간 온셋 일치 (%)',lambda x:100*x['nonword_onset_lower_proxy_share'],'.1f','비음성 온셋 대리지표'),('발화 구간 음절/s',lambda x:x['audio'].get('narrator_only_syllables_per_phrase_s',x['audio']['syllables_per_phrase_s']),'.3f','ASR·읽기 환산 추정'),('전체 타임라인 음절/s',lambda x:x['audio']['syllables_per_timeline_s'],'.3f','전체 ASR 발화 추정'),('0.2s 초과 ASR 쉼 수',lambda x:x['audio'].get('narrator_only_asr_pause_count',x['audio']['asr_pause_count_gt_0_2']),'.0f','어절 공백 추정'),('ASR 쉼 중앙값 (s)',lambda x:x['audio'].get('narrator_only_asr_pause_median_s',x['audio']['asr_pause_median_s']),'.3f','어절 공백 추정'),('VAD 비음성 구간 수 (>0.2s)',lambda x:x['audio']['vad_pause_count_gt_0_2'],'.0f','혼합 음원 VAD'),('VAD 비음성 중앙값 (s)',lambda x:x['audio']['vad_pause_median_s'],'.3f','혼합 음원 VAD'),('장 카드 중앙값 (s)',lambda x:x['chapter_card_median_s'],'.3f','관측 구간'),('음성 포함 혼합 RMS (dBFS)',lambda x:x['audio']['mixed_speech_rms_dbfs'],'.2f','측정'),('비단어 구간 혼합 RMS (dBFS)',lambda x:x['audio']['mixed_nonword_rms_dbfs'],'.2f','측정'),('비단어/음성 혼합 레벨 차 (dB)',lambda x:x['audio']['bed_to_speech_proxy_db'],'.2f','음악 분리값 아님'),('스테레오 Side RMS (dBFS)',lambda x:x['audio']['side_rms_dbfs'],'.2f','측정')]:lines.append(add(label,fn,fmt,status))
for group,types in [('transition',['hard','dissolve','fade-black','fade-white','flash','whip-pan','zoom-through','match-cut','push-in-cut','glitch','other']),('camera_move',['static','push-in','pull-out','pan','tilt','parallax']),('content_type',['archival photo','news footage','illustration','3D render','map','document or record card','text card','timeline','character art','other'])]:
 for t in types:lines.append(add(group+' / '+t+' (%)',lambda x,g=group,t=t:100*x[g+'_shares'].get(t,0),'.1f','시각 분류' if group!='camera_move' else '광류 추정'))
csvwrite(R/'comparison.csv',rows)
sectionlines=[]
for k in K:
 for s in S[k]['sections'][2:]:sectionlines.append(f"| {names[K.index(k)]} | {s['section']} | {s['start_s']:.3f}–{s['end_s']:.3f} | {s['cut_count']} | {s['cuts_per_minute']:.2f} | {s['clipped_duration_median_s']:.3f} |")
windowlines=[]
windows={k:readcsv(R/k/'narration_30s.csv') for k in K}
for i in range(max(map(len,windows.values()))):
 vals=[]
 for k in K:
  if i<len(windows[k]):v=windows[k][i];vals.append(f"{float(v['narrator_syllables_per_timeline_s']):.2f}")
  else:vals.append('—')
 windowlines.append('| '+str(i*30)+'–'+str((i+1)*30)+' | '+' | '.join(vals)+' |')
# Proposed line retiming is explicit recommendation; no media/edit project is changed.
source=json.load(open(W/'production/compositor_pilot/src/v4/n18-film.json'));groups={}
for c in source['subtitles']:groups.setdefault(c['narration'],[]).append(c)
visuals={
'N001':'0.000 영상 시작은 연병장 전경. 0.200 발화, 2.0%/s 접근; 날짜는 0.000부터 작은 라벨. 기존 1.6s 전면 장 카드는 제거.',
'N002':'4.100 평면도로 하드컷. 6.300은 컷 없이 여섯 표식을 순서대로 밝힘(각 3f); 1.5%/s 회전 없는 접근.',
'N003':'8.600 지시 내용 기록 카드 → 10.900 규정 위반 부분 매크로로 하드컷. 같은 배경 위 문구 리셋 대신 실제 프레이밍 교체.',
'N004':'13.400 중대장·부중대장 역할 비교 구도. 15.300 역할 콜아웃만 추가; 이 지점에서 배경/scale 리셋 금지.',
'N005':'17.300 비어 있는 연병장으로 하드컷 → 20.100 적절한 조치 미실시 혐의 기록 카드로 하드컷. 피해자 신체 동작·고통 재현 없음.',
'N006':'22.567 이틀 뒤 날짜/기록 클로즈업으로 하드컷. 음악 히트·충격음 0개. 문장 끝 여백은 표의 0.2s.',
'N007':'24.300 군기훈련–사망 인과관계 2노드 도식. 26.500 연결선/쟁점 콜아웃 추가는 같은 숏 안에서 진행.',
'N008':'28.500 피해자별 행위 와이드 도식 → 30.900 행위 분리 도식 매크로. 33.467–34.467 장 카드 총 30f(아래 별도 행).',
'N009':'34.467 학대치사 카드 → 37.000 직권남용 가혹행위 카드로 하드컷. 말하는 혐의명과 같은 순간 강조.',
'N010':'39.600 검찰의 기소 판단 카드 → 42.300 과실/학대치사 판단 부분 가까운 구도. 검찰 주장임을 유지.',
'N011':'45.200 사건 경위·방식·경과·신체조건을 4항목으로 배치. 48.000은 같은 숏에서 측면 이동과 항목 강조; 배경 컷 리셋 없음.',
'N012':'50.933 부중대장 기소 혐의 카드. 53.000 두 번째 혐의 추가는 같은 숏 안에서 진행.',
'N013':'55.133 공소사실 카드 → 57.700 적절한 조치 부분 매크로. 60.000에서 자르지 않고 문장을 60.833까지 이어감.'}
plan=[];cursor=6
for j,(nid,caps) in enumerate(groups.items()):
 if j>12:break
 if j==8:cursor+=30
 txt=' '.join(c['text'] for c in caps);count=syll(txt);nframes=round(count/6.5*30);a=cursor/30;b=(cursor+nframes)/30
 plan.append({'line':nid,'before_caption_start_s':caps[0]['from_']/30,'before_caption_end_s':caps[-1]['to']/30,'recommended_voice_start_s':a,'recommended_voice_end_s':b,'recommended_start_frame_30fps':cursor,'recommended_end_frame_30fps':cursor+nframes,'text_unchanged':txt,'planned_syllables':count,'visual_plan':visuals[nid]});cursor+=nframes+6
csvwrite(R/'n18_first60_edit_plan.csv',plan)
planlines=[f"| {p['line']} | {p['before_caption_start_s']:.3f}–{p['before_caption_end_s']:.3f} | {p['recommended_voice_start_s']:.3f}–{p['recommended_voice_end_s']:.3f} | {p['text_unchanged']} | {p['visual_plan']} |" for p in plan]
ref=S['ref'];ours=S['ours'];fast=S['ours_fast']
text=f'''# cut grammar v5 — Extol 신창원 실프레임 분석과 N18 수정 사양

2026-10-30. 분석 대상은 지정 레퍼런스 1편과 N18 기본/fast 저해상도 2편이다. 이 문서는 편집 지시안이며 파일럿 영상/프로젝트를 수정하지 않았다.

**결론과 증거 수준**

[측정] 레퍼런스는 **162숏/161경계**, 평균 **3.300s**, 중앙값 **2.783s**다. 기본 파일럿은 **121구간/120경계**, fast는 **204구간/203경계**다. 기존 문서의 156컷은 재사용하지 않았다. 중앙값 2.77s와 비슷한 결과가 나왔어도 이번 2.783s는 독립 검출·시각 검토에서 다시 계산한 값이다.

[시각 분류] 기본판 120경계 중 90개, fast 203경계 중 176개는 같은 구도에서 카메라/배경 애니메이션이 되돌아가는 리셋이다. 주 화면·구도 교체는 각각 30개와 27개로 분류했다. 따라서 ‘많이 자른다’와 ‘이야기가 진행되는 새 구도를 보여준다’는 별도로 읽어야 한다. 기준 프레임은 모든 채택 경계의 `final_boundaries_*.jpg`, 기각 포함 전수 기록은 `candidate_review.csv`다.

[측정] 첫 60s 경계는 레퍼런스 15, 기본판 20, fast 45다. 광류 중앙값은 폭 320px 기준 각각 {ref['flow_median_px_s_at_320w']:.2f}/{ours['flow_median_px_s_at_320w']:.2f}/{fast['flow_median_px_s_at_320w']:.2f}px/s다. fast는 말과 리셋 횟수가 빨라졌지만, 공간 이동과 구도 다양성은 여전히 작다.

[측정에 기반한 추정] 내레이터 발화 구간 속도는 **6.85 / 4.86 / 6.44음절/s**다. 숫자·소수점·cm/m/kg/km/IMF를 한국어 읽기로 환산했다. 레퍼런스 전화 녹취 418.600–457.133s는 내레이터 속도에서 제외했다. 전체 ASR 발화 기준 레퍼런스는 6.844음절/s다. ASR 인식 오류·숫자 읽기 변형·단어 시작 오차 때문에 ‘정답 음절수’로 해석하지 않는다. 기존 4.96과 우리 재측정 4.86은 분모(원본 발화 길이/ASR 공백 제외 시간)가 다르다. fast 제작 타임라인의 독립 원본 발화 측정 6.411과 이번 ASR 6.438은 근접한다.

**측정 방법과 한계**

- 다운로드: yt-dlp, format 399(1080p AV1)+251(Opus), 로그인/쿠키/업로드 없음. 원본 1920×1080, 30fps, 16,038프레임, 영상 길이 534.600s. 535s 표기는 반올림. 원본 SHA256 `{ref['sha256']}`. 파일 크기 96,309,635 bytes.
- 기본/fast 저해상도는 5fps, 각각 1,877/1,360프레임이다. 관측 길이 375.400/272.000s이며 제작 타임라인 375.300/271.900s와 끝 프레임 양자화 차이가 있다. 경계 위치는 실제 네이티브 프레임의 시작 시각이며, 원래 30fps 편집점은 0–0.2s 앞설 수 있다. 5fps를 30fps로 보간하여 정확도를 꾸미지 않았다. fast 제작상 205숏 중 일부가 동일한 5fps 경계로 양자화되어 관측 204구간이 된다.
- 프레임 번호는 0부터, 구간은 `[start,end)`다. `cuts.csv`의 한 행은 한 숏/연속 화면 구간이며 `transition_type`은 그 구간으로 **들어오는** 전환이다. 첫 행 `other`는 시작 표시이고 전환 비중에서 제외한다. 리셋도 화면의 불연속이므로 경계 수에는 포함하고 `boundary_kind`로 분리했다. 자막 교체, 연속 카메라 이동, 와이어프레임 변형만으로는 레퍼런스 경계를 추가하지 않았다.
- 분석용 480×270 Intra 프록시는 네이티브 프레임 수/fps를 보존했다. 컷 검토용 크롭은 이 프록시에서 뽑았으므로 픽셀 압축은 원본과 다르다. PySceneDetect 0.7.2 ContentDetector threshold=20, AdaptiveDetector threshold=2.5/min_content=9. 레퍼런스 최소 간격 4f. ffmpeg `scale=480:-2,scdet=threshold=5` 독립 대조. 1차 후보는 ref 396, ours 114, fast 173개였다.
- 레퍼런스 원시 차이 피크 13개, 기본판 저작 이벤트 보완 6개를 별도 시트로 검토했다. 5fps에 4f 최소 간격/3f 군집을 그대로 적용하면 짧은 카드가 합쳐지므로, 네이티브 프레임 전수 차이 스캔(기본 8개/fast 32개 추가)과 최소 간격 1f PySceneDetect 재검출로 보완했다. 단순 검출기 투표 다수결을 최종 컷 수로 사용하지 않았다.
- 각 후보의 −3…+2 **연속 네이티브 프레임**과 ±0.5s 맥락을 시각 검토했다. 채택 위치를 바로잡은 정규 6프레임 시트를 추가로 생성했다. 시각 검토자는 이 세션의 에이전트이며, 독립 인간 검수/통계적 정확도 보증은 없다. confidence는 관찰에 대한 판단값이다.
- 원시 luma MAD/histogram 차이는 전 프레임에서 계산했다. `frame_diff_0_5s.csv`는 시간축을 10ms로 선형 재표본화한 **곡선**의 정확한 0.5s 이동 평균이다. 이는 프레임을 새로 만든 것이 아니며 파일럿의 0.2s 경계 해상도는 그대로다. 1차 후보 스캔은 정수 프레임 창(레퍼런스 15f, 파일럿 3f)을 썼다.
- 광류: 폭 320px, 상단 150px 범위에서 Farnebäck, 약 0.2s 간격, 숏당 최대 12쌍. LK 특징점+RANSAC 부분 affine으로 scale/s 추정. 화면 속 인물 동작·패럴랙스·문자·저텍스처가 카메라 추정에 섞인다. static은 ‘완전 정지’가 아니라 낮은 움직임 분류다. scale 누적값은 affine 속도의 외삽이므로 물리적 카메라 거리로 읽지 않는다. 방향은 영상 좌표(오른쪽 +x, 아래 +y)다.
- mlx_whisper large-v3-turbo는 기존 로컬 캐시를 오프라인으로 읽었다. 원시 `whisper_words.json`과 `words.csv`를 보존했다. 첫 단어가 초기 효과음/침묵까지 길게 잡히는 정렬 오류가 있다. 전화 녹취 앞부분 인식도 불완전하다. 말/음절 수와 절 위치는 자동 추정이다.
- 절 위치: 단어 끝 ±0.2s에 한국어 종결/연결 어미·구두점이 있거나, 0.2s 초과 어절 공백 안인 경우. 그 외 mid-clause. 전화 녹취의 5개 경계는 unknown으로 두었다. ref {ref['clause_boundary_estimate_count']}/{ref['clause_boundary_estimate_known_denominator']}, ours {ours['clause_boundary_estimate_count']}/120, fast {fast['clause_boundary_estimate_count']}/203이다. 완전한 수동 절 문법 분석으로 주장하지 않는다.
- 소리 히트 대리: 25ms STFT/10ms hop, 양의 spectral flux, 0.5s 지역 중앙값/MAD 대비 score≥6, peak 간격≥0.1s. 컷 ±0.1s에서 일치 여부. 이 기준은 자음·강세도 잡는다. **실제 효과음/음악 히트 비율과 음악/내레이션 분리 loudness는 미측정**이다. `sfx_or_music_hit=unconfirmed`는 이를 숨기지 않은 표기다. 비단어 구간 온셋 비중도 확정 효과음 비중이나 엄밀한 하한이 아니다(음성 정렬 누락/동시 효과음 가능).
- 쉼은 ASR 단어 간 >0.2s 공백과 WebRTC VAD(mode2, 20ms)의 비음성 구간을 병기했다. 혼합 음원의 VAD는 음악/효과음을 말로 오인한다. 배경층 상대값은 비단어 구간 혼합 RMS−단어 구간 혼합 RMS이며, **실제 음악 대 내레이션 dB가 아니다**. ref Side RMS −29.81dBFS는 스테레오 배경층의 존재를 보여주지만 음악과 환경음을 분리하지 못한다. 기본/fast Side 약 −72.8/−72.9dBFS는 거의 모노다. 파일럿 제작 자료의 `music:false`와 −17.96dB 이하 환경음 설정은 별도의 제작 근거이며 레퍼런스 음악 측정의 대용이 아니다.

**비교표 — 측정과 추정을 함께 표시**

| 지표 | Extol | N18 기본 | N18 fast | 근거 수준 |
|---|---:|---:|---:|---|
'''+ '\n'.join(lines)+'''

카메라/콘텐츠는 숏 수 비중이며, 콘텐츠의 시간 가중 비중은 각 `summary.json`의 `content_time_shares`에 있다. 혼합 화면은 주된 시각 유형 하나를 부여했다(예: 3D 인물+사진 합성은 3D render, 문서가 중심인 카드만 document). 파일럿 SVG 재구성은 illustration이며 3D render로 세지 않았다. 순수 비장(非章) 텍스트 전면 카드는 따로 관찰되지 않았고, 장 카드는 text card에 포함한다. 따옴표 없는 요약 콜아웃을 quote로 과장하지 않았다.

**장별 컷 속도**

구간 첫 경계는 중복 집계하지 않는다. 숏이 장 구간에 걸치면 길이는 구간 안으로 잘라 계산했다. 장 진입의 중간 프레임을 사용하는 숏 목록과, 전환 시작부터 쓰는 장 구간의 차이도 보존했다.

| 영상 | 장 | 범위 s | 컷 | 컷/분 | 잘린 숏 중앙값 s |
|---|---|---|---:|---:|---:|
'''+ '\n'.join(sectionlines)+'''

레퍼런스의 낮은 P10은 89.400–93.233s 예고 몽타주와 뉴스 내부의 짧은 컷에 크게 좌우된다. 0.2–0.4s를 장편 전체의 목표로 삼으면 잘못된 재현이다. 반대로 188.000–209.133s는 약 21.13s의 연속 이동이다. 긴 숏에서도 테이블→인물→환풍구로 화면 정보가 진행한다.

**발화·쉼·배경층의 시간 변화**

아래는 30s 창의 내레이터 음절/타임라인 초다. 마지막 창은 남은 길이만 분모로 사용한다. 전체 발화 구간 속도(6.85/4.86/6.44)와 다른 지표다. 레퍼런스 녹취 시간은 내레이터 열에서 제외했다.

| 창 s | Extol | N18 기본 | N18 fast |
|---|---:|---:|---:|
'''+ '\n'.join(windowlines)+'''

`narration_30s.csv`에는 창별 원시 환산 음절 수, 전체 발화/내레이터 열, ASR 공백 시간이 있다. `pauses.csv`와 `acoustic_pauses.csv`는 >0.2s 쉼의 전 분포다. 레퍼런스의 음악이 실제로 몇 초 켜져 있는지, 내레이션보다 몇 LU 낮은지는 혼합 음원만으로 이 분석에서 확정하지 못했다. 이를 −4.00dB라는 ‘음악 레벨’로 잘못 보고하지 않는다. 배경층이 훨씬 약한 파일럿의 −19.51/−15.59dB 역시 혼합 구간 비교치다.

**장 카드·기록 카드와 첫 60초**

[측정] 레퍼런스 장 카드 진입은 세로 막대 분할/밀기 `other` 4회다. 시각상 효과 시작→정착 구간은 f2843–2850(7f), f4425–4436(11f), f6541–6553(12f), f11990–12003(13f), 끝 프레임 제외. 텍스트 회전 정착까지 포함한다. 숏 경계는 이 구간 중간 f2847/4431/6547/11997로 두었다. 효과 자체와 카드 전체 체류 시간을 구분한다.

[측정] 중간 경계 기준 장 카드 숏은 55/53/60/59f = 1.833/1.767/2.000/1.967s. 정착 이후 다음 컷까지는 각각 52/48/54/53f이다. 기본판 장 카드 관측 길이는 1.6/1.6/1.6/1.4/1.4s, fast는 0.6/0.4/0.4/0.4/0.4s. 5fps에서 30fps 기준의 미세한 효과 길이는 확정할 수 없다.

[측정] 레퍼런스 첫 기록 카드는 96.733–109.133s(12.400s), 이감 타임라인은 128.433–134.233s(5.800s)다. 글이 누적되며 머물기 때문에 같은 카드의 반복 리셋과 다르다. 전체 카드별 시간은 `ref/cards.csv`, `ours/cards.csv`, `ours_fast/cards.csv`에 있다.

[관찰] 레퍼런스 첫 60s는 전경→감방→인물/실제 사진→화장실→쇠창살→치수→몸/다리→바깥→지도→벽 높이→손/물체→땅/이동→담벼락으로 진행한다. 첫 15s는 3숏뿐이다. 49.933–56.033s의 변형/이동은 여러 하드컷이 아니다. 파일럿의 기존 첫 60s는 전면 장 카드→같은 연병장·평면도 반복→빈 연병장→법정 배경→같은 도식→다음 장 카드→같은 기록 카드 반복이다.

초별 화면과 말은 **60행씩 전수 기록**했다: `ref/first60_log.csv`, `ours/first60_log.csv`, `ours_fast/first60_log.csv`. raw ASR와 명백한 인식 오류를 기존 로컬 자막으로 바로잡은 said_corrected를 함께 싣는다. 1초 창과 겹치는 어절을 싣기 때문에 창 경계의 어절은 중복될 수 있다. 이것은 자막 큐 타임라인과 다르다. 근거 이미지: `ref_first60_2fps.jpg`, `ref_transitions.jpg`, `ours_first60_2fps.jpg`, `ours_transitions.jpg`, `ours_fast_first60_2fps.jpg`, `ref_vs_ours_first60.jpg`. 5fps의 0.5s 표본은 가장 가까운 네이티브 프레임(최대 0.1s 차이)이며 그림에 실제 f번호를 썼다.

**장편 편집 사양 — 아래 수치는 전부 [권고], 관측값이 아님**

마스터는 30fps. 같은 구도에서 줌·조명 위상을 0으로 되돌리는 컷은 **0개**로 만든다. 원래 같은 숏으로 이어지는 카메라/광원은 연속 시간으로 계산한다. 새 컷은 다른 거리·방향·물체·지도·기록으로 바뀔 때 넣는다. 동일한 컷 수를 채우기 위한 배경 리셋을 목표에 포함하지 않는다.

| 구간 | <1s | 1–2s | 2–4s | 4–6s | 6–9s | 길이/구도 목표 |
|---|---:|---:|---:|---:|---:|---|
| 첫 15s | 0% | 25% | 50% | 25% | 0% | 약 4–5숏, 중앙 3.5s. 전경→핵심 수치/관계로 진행 |
| 15–60s | 0% | 15% | 55% | 25% | 5% | 첫 60s 전체 18–22개의 구도 구간, 중앙 약 2.8–3.2s |
| 사건 동선/행위 | 5% | 20% | 45% | 20% | 10% | 중앙 2.6–3.2s, P90 6–8s |
| 법리/기록 설명 | 0% | 10% | 45% | 35% | 10% | 중앙 3.2–4.2s, P90 7–8s. 같은 카드 누적은 6–8s 허용 |
| 선고/정리 | 0% | 10% | 40% | 40% | 10% | 중앙 3.5–4.5s. 숫자 읽는 중에는 추가 컷 없음 |

빈도는 장/구간 안의 숏 수 기준이고 소수 숏 구간에서는 가까운 정수로 적용한다. 첫 15s와 첫 60s의 목표는 레퍼런스보다 조금 빠르게 잡은 오너 요구 반영이다. 최장 9s 이상은 동선·새 증거가 실제로 진행될 때만 1회/분 이하로 허용한다. 레퍼런스의 21s 이동을 현재 파일럿의 빈 배경으로 재현하지 않는다. 화면 변화는 컷 외에도 연속 카메라, 새 표식, 수치 전개로 **2s 이내마다** 한 번 만든다.

| 전환 태그 | 정확한 효과 길이(30fps) | 권고 사용량 |
|---|---:|---|
| hard | 0f 블렌드, 다음 프레임 즉시 교체 | 전체 경계 약 97%; 구도와 대상 교체에 사용 |
| other: 자체 세로/패널 전환 | 진입 12f, 이탈 hard 0f | 약 3%; 장 진입에만, 장당 1회. Extol 막대 디자인 복제 대신 자체 패널 형태 |
| dissolve | 기본 0회; 예외 설계 시 12f | 기본판 0% |
| fade-black | 끝내기 12f | 영상 마지막 1회; 새 숏으로 세지 않음 |
| fade-white / flash / whip-pan / glitch | 0f, 0회 | N18에서 0% |
| zoom-through | 컷 효과로 0회 | 필요한 공간 연결은 24–36f의 실제 연속 이동, 최대 1회/60s |
| match-cut | 별도 블렌드 0f | 기본 할당 0%; 도형/움직임 대응이 실제로 있을 때 hard 안의 관계로 표시 |
| push-in-cut | 별도 블렌드 0f | 반복 구도 리셋 0회. 필요하면 12% 이상 크기 차와 새 정보가 있는 명시적 가까운 구도로 1회/30s 이하 |

97:3은 전체 리듬 가이드이고 장 수 때문에 정확한 백분율을 강제로 채우지 않는다. 장 이동 외에는 효과 길이를 덧붙여 문장 호흡을 늦추지 않는다. 레퍼런스에서 별도 컷으로 확인되지 않은 돌리/와이어프레임 애니메이션을 ‘전환 프리셋’으로 대체하지 않는다.

| 콘텐츠 | 카메라/화면 이동 규칙 [권고] |
|---|---|
| archival photo | scale 100→106%/3s(약 2%/s). 팬은 화면 폭 1–2%/s. 얼굴/증거 핵심이 잘리지 않게 종료점 먼저 지정 |
| news footage | 원래 동작 유지. 추가 줌 0–1%/s; 외곽 박스를 매 컷 확대/축소로 리셋하지 않음 |
| illustration | 전경/중경/배경 분리. 전경 2%폭/s, 배경 0.5%폭/s로 패럴랙스; 한 숏은 한 진행 방향 |
| 3D render/공간 재구성 | 기본 push-in 2–4% scale/s 또는 수평 2–4%폭/s. 동선 이동은 4–8%폭/s를 0.6–1.2s만. 방향이 바뀌면 6f ease; 컷마다 거리/높이 변화 |
| map | 이동 지점을 말할 때 100→112%/3s 또는 2–3%폭/s 이동. 경로·표식은 6f 이내 순차 노출 |
| document/record card | 읽는 동안 0–0.8% scale/s. 새 줄 누적 6f, 핵심 줄 강조 4f. 3초마다 같은 카드 첫 줄을 다시 타이핑하지 않음 |
| text card | 글자 정착 후 카메라 0%. 글자 이동과 배경 이동을 동시에 하지 않음 |
| timeline | 축 진행 2–4%폭/s. 사건 하나마다 6f로 점·날짜가 추가되고 이전 사건은 유지 |
| character art | 얼굴 없는 역할 구도: push 1.5–2.5%/s, 근경·중경의 속도 비 2:1. 피해자 고통/신체 동작 재현에 쓰지 않음 |
| other/빈 화면 | 의도한 쉼 6f(0.2s). 장간 15f(0.5s) 이내. 빈 배경을 새 컷으로 세지 않음 |

위 속도는 화면 좌표/scale 기준이다. 기존 optical-flow px/s를 물리 카메라 이동량으로 직접 환산하지 않는다. 이동이 있는 숏은 화면 광류 중앙값 **폭320 기준 3–10px/s**를 작업용 범위로 삼되, 텍스트 읽기·정지 증거 카드에 강제로 적용하지 않는다. 레퍼런스의 단일 push-in 비중을 복제하기보다 pull-out·pan·parallax를 실제 동선에 배정한다. 전체 숏의 static 10–20%, push-in 35–45%, pull-out 15–20%, pan/tilt 10–15%, parallax 15–20%를 합계 100%에 가깝게 조정한다(예시 15/40/15/10/20).

절 경계 컷 목표는 **60–70%**, 문장 내부 의미 단위 컷은 **30–40%**다. 레퍼런스의 ASR 추정 38.5%를 그대로 복제하는 값이 아니라 우리 법리 설명의 이해도를 위한 권고다. 문장 내부에서는 주어→행위, 물체→치수, 주장→증거가 바뀌는 명사구 끝에 놓는다. 숫자·혐의명·부정어 한가운데 컷은 0회. 새 음원의 단어 타임스탬프 확정 후 절 끝 ±3f 안으로 제안 편집점을 이동한다. 시각 내용이 바뀌면 문장을 가로지르는 연속 음성/J-cut 3–6f는 허용한다.

효과음은 N18 장편 **2–4회/분 이하**, 문서·지도·장 변경 중 정보가 새로 확정되는 지점에만 쓴다. 컷마다 넣지 않는다. 히트를 쓰는 컷은 전체의 **10–20% 이하**를 목표로, 피크는 컷 ±2f 안에 놓는다. 효과음 3–6f attack, 잔향 포함 9–18f, 내레이션 단기 RMS보다 10–16dB 낮게 시작한다. 사망 문장·피해자 언급·선고 숫자에 충격음 0개. 음성 시작을 히트로 센 온셋 비율 42.9/70.8/65.5%를 효과음 목표로 쓰지 않는다.

N18은 기존 음악 없는 방향을 유지하고 환경층을 내레이션보다 **18–24dB** 낮게 둔다. 다른 주제에서 음악을 허용할 경우 음악 스템은 내레이션보다 **20–26LU 낮게** 시작하고 발화 중 3–5dB duck을 3f attack/12f release로 준다. 이는 레퍼런스 음악 레벨 측정값이 아니다. 스템을 분리해서 실제 믹스로 확인할 권고 값이다.

내레이션은 새 발화 기준 **6.4–6.8음절/s**, 숫자·법리 정의 구간 **6.0–6.4**, 짧은 연결 구간 **6.6–7.0**으로 둔다. 문장 간 기본 쉼 **6f=0.2s**, 절 사이 **3f=0.1s**, 장 사이 비발화 여백 **최대15f=0.5s**다. 이미 완성된 fast의 ASR 6.44와 제작 측정 6.41은 이 범위의 하단이다. 더 빨라 보이게 만들려면 같은 구도 리셋을 추가하기보다 정보와 시점을 진행시킨다.

장 카드 총 길이는 **30f=1.0s**(12f 진입+18f 정착+0f hard 이탈), 그 위에 다음 문장의 첫 3–6f를 J-cut할 수 있다. 첫 장 카드는 전면 화면 대신 첫 사건 구도의 작은 장 라벨로 시작한다. 날짜 카드 18–30f, 8–14음절 핵심 문구 카드 45–75f, 20–30음절 기록/인용 카드 90–150f. 실제 필요한 읽기 시간은 `ceil((음절수/6.5+0.25)*30)`f를 최소값으로, 문구의 음절 수가 많으면 범위를 늘린다. 선고 숫자와 피고인/심급은 같은 화면에서 60–90f 함께 유지한다. 자막은 단어 진행에 맞추되 의미 단위 0.8–2.0s, 최대 18–24한글 음절/화면을 기본으로 한다.

**N18 첫 60초 전후 수정안 — 모든 새 시간은 [권고]**

기존 열은 원본 자막/저작 타임라인이며 5fps 관측 경계와 최대 0.2s 차이가 있다. 새 열은 30fps, 6.5음절/s 환산에서 만든 구체 초안이다. 말은 바꾸지 않았으며 TTS를 재생성한 실측 타이밍은 아니다. 발화 끝 후 6f를 두고, N008 다음에 30f 장 카드를 배치했다. 첫 장 전면 카드 제거. `n18_first60_edit_plan.csv`에 프레임 번호도 있다. 장 카드 행은 33.467–34.467s이며 33.467–33.867 진입, 33.867–34.467 정착, 34.467 hard 이탈이다.

| 줄 | 기존 자막 범위 s | 새 발화 범위 s | 그대로 유지할 말 | 새 화면/컷 |
|---|---|---|---|---|
'''+ '\n'.join(planlines)+'''

새 첫 60s는 약 **20개 구도 구간/19회 화면 교체**다. 6.300/15.300/26.500/48.000/53.000은 새 컷이 아니라 같은 숏 안의 표식·카메라·정보 진행이다. N013은 60.000s를 지나 이어지므로 60초를 맞추려고 문장 중간을 자르지 않는다. 효과음은 4.100 지도 진입, 34.467 기소 카드 진입 두 곳만 우선 배치하고 나머지 첫 60s는 무효과음으로 시작한다. 새 타임코드에서 실제 단어 끝이 다르면 위 ±3f 규칙으로 미세 조정한다.

**Shorts 적응안 — [권고], 레퍼런스 장편에서 직접 측정한 Shorts 수치 아님**

30fps/9:16, 40–55s. 0–2s 사건/수치, 2–12s 배경, 12–30s 핵심 행위·쟁점, 30–45s 판단·선고, 마지막 3–5s 근거/심급을 한 흐름으로 잇는다. 긴 장편 전체를 단순 배속하지 않고 사건 하나·법리 쟁점 하나를 선택한다. 혐의·구형·선고·확정은 각 상태를 지운 채 한 숫자로 합치지 않는다.

숏 수 비중은 0.25–1s 10%, 1–2s 45%, 2–3.5s 40%, 3.5–5s 5%; 중앙값 약 1.8s, 구도 교체 30–40회/분. 숫자 카드와 최종 선고는 60–90f까지 유지한다. 같은 구도 리셋은 0개다. 하드컷 98%, 자체 패널 2%(6f, 최대 1회/편), 다른 전환 0%. 장 전면 카드는 0회; 작은 장/쟁점 라벨은 12–18f. 카메라 push 2–4%/s, pan 2–4%폭/s, 글 읽기 중 scale≤0.8%/s. 9:16에서는 증거와 피고인/심급 라벨을 같은 시야에 남긴다.

말은 6.4–6.8음절/s, 문장 간 쉼 3–6f, 절 사이 0–3f. 절 경계 컷 60% 이상, 히트는 한 편 2–3개 이하/±2f, 사망 문장 충격음 0개. 텍스트는 한 화면 8–16음절, 최소 `ceil((음절수/6.5+0.2)*30)`f. 30초 안에 정답 숫자를 감추기 위한 불필요한 카드/반복 컷은 넣지 않는다.

**산출물과 재현 범위**

- `ref_extol/cuts.csv`, `shots.csv`: 레퍼런스 정규 데이터. `ours_cuts.csv`, `ours_shots.csv`, `ours_fast_cuts.csv`, `ours_fast_shots.csv`: 동일 스키마 비교 파일.
- 각 영상 하위 폴더의 `boundaries.csv`, `flow.csv`, `words.csv`, `pauses.csv`, `acoustic_pauses.csv`, `narration_30s.csv`, `sections.csv`, `cuts_per_30s.csv`, `cards.csv`, `first60_log.csv`, `summary.json`: 세부 근거.
- `candidate_review.csv`와 후보/추가/정규 경계 JPG: 채택·기각 모두 추적 가능. `comparison.csv`, 최상위 `summary.json`, `n18_first60_edit_plan.csv`는 편집자가 직접 사용할 요약 데이터.
- `analyze.py`, `measure.py`, `supplement.py`, `native_review.py`, `compile_review.py`, `jumps.py`, `finalize.py`, `evidence.py`, `contacts.py`, `write_report.py`: 이 분석에서 쓴 로컬 코드. `within_shot_events.csv`에는 532.300–534.600s의 말미 fade-black(관측 가능한 시작 기준 약69f)과 연속 환풍구 통과/와이어프레임 이동을 별도 기록했다. 이들은 새 숏 수에 더하지 않았다. `audio_windows_30s.csv`에는 배경층 RMS 대리값과 미확정 음악 상태를 창별로 보존했다. 음원/프록시를 삭제한 뒤에도 도출 데이터와 결과 문서는 남는다. 원본이 없으면 원시 영상 분석을 다시 실행할 수 없고, 남은 CSV로 집계/문서 재생성만 가능하다.
- 원본/임시 미디어 삭제와 최종 입력 SHA 재확인은 `cleanup_manifest.json`을 기준으로 한다. 다운로드 영상·분리 오디오·분석 WAV·프록시는 모두 삭제 대상이며, 기존 파일럿과 기존 프로젝트 오디오는 삭제하지 않는다.
'''
(R.parent/'cut_grammar_v5.md').write_text(text)
print('REPORT',len(text),'chars',len(text.splitlines()),'lines')
