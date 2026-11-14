from analyze import *
cuts=list(csv.DictReader((R/'cuts.csv').open()));shots=list(csv.DictReader((R/'shots.csv').open()));words=list(csv.DictReader((R/'ref/words.csv').open()));aud=list(csv.DictReader((R/'reference_audio_1s.csv').open()));onsets=list(csv.DictReader((R/'reference_side_onsets.csv').open()))
# One-second screen annotations, read from first60 images plus all reviewed boundaries.
shown=[
'날아오는 파리 전면; 배경의 집·인물은 심도 밖; 날짜 타이핑 시작',
'파리 추적; 1982년 4월 26일 날짜가 타이핑됨',
'파리 전면 초점; 낮 12시경·장소 두 줄 표시',
'파리 비행; 뒤에 붉게 발광하는 잠든 남자 흐릿함',
'파리를 따라 카메라가 남자 쪽으로 연속 이동; 초점·화면 크기 변화',
'붉은 남자 전신→5.633s 가슴·파리 클로즈업',
'가슴 위 작은 파리; 큰 밝은 피부 형태·붉은 그림자',
'파리에 접근; 가슴 표면의 붉은 점상 질감',
'파리 확대; 화면 하단에 흰 한 줄 자막',
'파리를 더 가깝게 보여줌; 발화 뒤 0.38s 간격',
'10.067s 총 조준 인물→10.533s 피격 집단; 결과 예고 몽타주 시작',
'11.033s 창문 안 집단→11.533s 문 앞 사수; 56명 자막 유지',
'12.033s 아기 전경→12.567s 방 안 쓰러진 인물·붉은 구체',
'13.100s 집 외부→13.633s 넓은 상갓집/피해 구체 장면',
'피해를 넓게 보임→14.867s 가슴 위 파리로 복귀',
'파리 정면에 지속 접근; 거대한 결과와 작은 원인 대비',
'파리 클로즈업 마무리; 하단에 시작됩니다 자막',
'17.000s 잠든 붉은 인물과 집 와이드',
'잠든 인물 위에 우범곤 실사 얼굴 사진·붉은 프레임 등장',
'사진 오른쪽 경찰 로고와 인적사항 라벨 타이핑',
'얼굴 사진·궁류지서·우범곤 순경 27세 정보 유지',
'같은 와이드에서 약한 카메라 이동; 사진 라벨 유지',
'신분 소개 자막과 잠든 전신·얼굴 사진을 함께 보임',
'밤 근무 설명 자막으로 전환; 기존 구도 유지',
'잠든 전신과 낮잠 맥락 유지; 다음 행동 전의 정지감',
'사진 라벨과 인물 유지; 카메라가 조금 이동',
'신분 사진 합성 유지; 동거녀 소개 발화로 넘어감',
'27.100s 노란 동거녀가 누운 남자를 내려다보는 시점',
'노란 인물의 상체와 붉은 남자의 가슴을 함께 보임',
'같은 장면에서 동거녀 쪽으로 접근',
'노란 손이 남자의 가슴 쪽으로 움직임',
'가슴을 때리는 동작; 파리잡기 설명 자막',
'노란 동거녀·붉은 남자; 타격 동작 마무리',
'33.767s 붉은 남자의 눈·얼굴 극단 클로즈업',
'놀라서 뜬 눈·눈썹을 과장한 붉은 얼굴',
'눈 클로즈업 유지; 다음 행동을 짧게 유예',
'36.400s 원형 문 안에서 붉은 인물이 노란 인물을 폭행하는 와이드',
'문·벽의 큰 원형 프레임으로 두 사람의 행동을 보임',
'38.600s 가해자 손·상체의 낮은 시점 클로즈업',
'붉은 가해자 팔 동작; 노란 인물은 전경 일부로 남음',
'손의 동작과 얼굴 강조; 배경은 심도 밖',
'41.067s 노란 여성의 비명을 짓는 얼굴 클로즈업',
'노란 얼굴 앞 붉은 입자; 해부학적 상처를 상세히 그리지 않음',
'노란 얼굴·코 주변 붉은 구체; 폭행 결과를 색으로 표시',
'같은 얼굴 전면·흰 윤곽·붉은 입자 유지',
'노란 인물의 반응을 유지; 친척 언니의 개입을 말함',
'46.400s 새 노란 인물이 붉은 남자를 말리는 두 인물 구도',
'노란 손·붉은 상체 접촉; 말리기와 폭행의 방향을 시각화',
'같은 공간에서 카메라가 옆으로 돌아감',
'두 인물의 손·상체를 가까이 보임; 친척도 폭행한다는 자막',
'연속 카메라 이동으로 두 얼굴의 거리와 힘 관계를 강조',
'노란 인물 뒤쪽 시점; 붉은 인물이 팔을 뻗음',
'붉은 인물·노란 인물 대비 유지; 장면 내부 동작',
'붉은 인물의 얼굴을 향해 접근; 별명 설명 시작',
'주변 사람들이 아는 별명 자막; 얼굴은 아직 인간형',
'인간 얼굴이 붉은 조각으로 분해되기 시작',
'같은 샷에서 얼굴이 호랑이 머리로 변형; 컷으로 세지 않음',
'붉은 호랑이 머리의 가해자와 노란 피해자 클로즈업',
'58.533s 술상 주변 여러 인물 와이드로 시간 전환',
'붉은 경찰 인물이 술잔을 듦; 저녁 7시30분 시간 라벨 타이핑'
]
assert len(shown)==60
rows=[]
for t in range(60):
 ss=[s for s in shots if float(s['end_s'])>t and float(s['start_s'])<t+1];ww=[w for w in words if float(w['end'])>t and float(w['start'])<t+1];line=' '.join(w['word'].strip() for w in ww)
 for a,b in [('국류','궁류'),('우범군','우범곤'),('오늘은 있다 있을','오늘은 이따 있을')]:line=line.replace(a,b)
 ons=[float(o['time_s']) for o in onsets if t<=float(o['time_s'])<t+1];a=aud[t];sound=f"내레이션(ASR) + 스테레오 비음성 성분; mix {float(a['mix_dbfs']):.1f}, side {float(a['side_dbfs']):.1f} dBFS"
 if ons:sound+='; 비음성 트랜지언트 후보 '+', '.join(f'{x:.2f}s' for x in ons)
 rows.append({'start_s':t,'end_s':t+1,'shot_ids':';'.join(s['shot_id'] for s in ss),'shown_visual_check':shown[t],'said_asr_overlap':line,'heard_measurement_proxy':sound,'cut_times_s':';'.join(f"{float(c['time_s']):.3f}" for c in cuts if t<=float(c['time_s'])<t+1),'note':'Words overlap seconds and may repeat. Audio: no direct listening; cannot name SFX/track from proxy.'})
csvwrite(R/'first60_second_by_second.csv',rows)
out=['# 첫 60초: 초별 화면·발화·음향 측정','', 'MEASURED: 1초 행마다 겹치는 ASR 단어를 표시하므로 경계의 단어는 반복된다. 화면은 실제 프레임과 컷 스트립을 확인했다. 음향은 청취 대신 혼합/side RMS와 트랜지언트를 측정한 것으로, 음악·효과음 정체를 확정하지 않는다. 원 수치는 CSV 및 reference_audio_1s.csv.', '', '| 초 | 화면 | 발화(단어 타임스탬프) | 음향 측정 |','|---|---|---|---|']
for r in rows:out.append(f"| {r['start_s']:02}–{r['end_s']:02} | {r['shown_visual_check']} | {r['said_asr_overlap']} | {r['heard_measurement_proxy']} |")
(R/'first60_second_by_second.md').write_text('\n'.join(out)+'\n')
