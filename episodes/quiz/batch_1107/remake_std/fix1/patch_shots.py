from pathlib import Path
import json
D=Path(__file__).resolve().parent.parent;W=D.parents[3]

def main(q):
 p=W/f'upload/pkg/{q}_std';b=D/f'fix1/before/{q}';c=json.loads((p/'case.json').read_text());x=json.loads((b/'shots.json').read_text());snack=q=='q004'
 views={
 'first':('wide','low-bench','낮은 법대 구도. 판사가 기록 쪽으로 손을 뻗고, 1심 벌금 5만 원은 큰 물리적 기록 소품 안에만 표시.','judge_reach',200.6,119.8),
 'harm':('wide','low-bench-video','낮은 법대. 판사의 판단 동작과 보도된 촬영 영상의 카툰 재생을 실제 모니터 소품 안에 배치. CCTV·실제 법정 재생이라고 주장하지 않음.','judge_reach',200.6,119.8),
 'claim':('close-up','defendant-reaction','피고인의 얼굴·가슴 클로즈업. 옷깃을 당기는 반응. 법정 실제 행동이 아닌 각색.','collar_pull',195,117),
 'recovery':('close-up','defendant-reaction','피고인의 얼굴·가슴 클로즈업. 반성·합의·처벌불원을 듣는 반응, 피해자 희화화 없음.','collar_pull',195,117),
 'evidence':('close-up','witness-document-insert','진술서 소품을 내려놓는 손·문서 인서트. 판사 얼굴과 손의 연기가 함께 보임. 실제 문서 원본 복제가 아님.','document_placement',120,72),
 'factor':('medium','over-shoulder-judge','피고인의 어깨 일부를 전경에 둔 판사 시점. 판사가 지적하고 두 사정을 함께 놓은 저울이 움직임. 최종 판결·공식 산식을 먼저 보여주지 않음.','judge_point',136.7,81.1),
 }
 for s,u in zip(x['shots'],c['utterances']):
  mode=u['mode']
  if mode in views:
   size,framing,action,hero,amp,secondary=views[mode];s.update(shot_size=size,framing=framing,action=action,intended_label=action,camera='scene-only 1.00→1.02 push; ease-in-out-quart; no new snap zoom',screen_direction='left_to_right',axis_side='A',CTO_match=None)
   s['motion_numbers']=dict(from_frame=u['from_frame'],to_frame=u['from_frame']+u['dur'],hero=dict(target=hero,screen_px=amp,screen_px_basis='authored displacement at nominal scale, before 2% camera push and small ambient',anticipation_frames=4,anticipation_ratio=-.15,main_frames=14 if mode=='evidence' else 18,start_offset_frames=10 if mode=='evidence' else 0,follow_through_frames=10,curve='ease-in-out-cubic + analytic damped follow-through',mass=1,stiffness=100,damping=10,zeta=.5),secondary=dict(delay_frames=5,screen_px=secondary,ratio=secondary/amp),ambient=dict(clock='absolute frame / 30; never clamped at hero end',period_frames=120,hip_raw_px=2,hands_raw_px=1.6,head_deg=.24,torso_deg=.22,independent_phase_sin_cos=True,feet_fixed=True),camera=dict(from_scale=1,to_scale=1.02,curve='ease-in-out-quart',caption_and_choice_layers_outside_camera=True),props=dict(no_top_badges=True,readable_number='1심 / 벌금 / 5만 원' if mode=='first' else None,read_hold_frames=u['dur']-38 if mode=='evidence' else u['dur'],document_words=2 if mode=='evidence' else 4 if mode=='first' else 0),sound=dict(new_sfx=False,original_AAC_copy=True))
  elif mode=='choices':
   s['action']='기존 A/B/C 카드·문구·타이밍 그대로. 마지막 27프레임의 배경 판사만 가벨 예비동작→22f 가속 strike. 접촉은 기존 효과음 한 프레임 전.'
   s['motion_numbers']=dict(hero='background_judge_gavel',from_frame=c['answer_frame']-27,anticipation_frames=4,main_frames=22,curve='-15% ease-in-out anticipation, then accelerating cubic strike',contact_frame=c['answer_frame']-1,sfx_nominal_frame=c['answer_frame'],picture_lead_frames=1,follow_through='7f in the unchanged answer composition, then approved deadpan',cards_changed=False,ambient=dict(period_frames=120,hip_px=1.5,free_hand_px=1.5,head_deg=.24))
 x['revision']='CTO fix1 / courtroom framing + no top stamp labels; narration and captions immutable'
 (p/'shots.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
 print(q,[(s['id'],s.get('framing'),s['start_s'],s['end_s']) for s in x['shots']])
if __name__=='__main__':
 for q in ['q004','q005']:main(q)
