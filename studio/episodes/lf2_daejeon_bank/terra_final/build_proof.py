#!/usr/bin/env python3
"""Low-resolution 640×360 CEO proof only; modify three existing SVG scenes."""
from pathlib import Path
import json
import subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parent
W, H = 640, 360
FONT = "Apple SD Gothic Neo,Arial,sans-serif"
INK = "#17262b"; WALL = "#66767a"; FLOOR = "#2a393e"; LINE = "#9eadae"
BLACK = "#20262a"; VAN = "#dde4e0"; GLASS = "#91aeb7"; GOLD = "#eac66f"
MASK = "#273238"; CLOTH_A = "#344d59"; CLOTH_B = "#624c53"; STAFF = "#66818a"; SKIN = "#b98268"

def text(x, y, s, size=10, fill="#eef1eb", anchor="start", weight=700):
    return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{s}</text>'

def garage():
    return '''<rect width="426" height="240" fill="#58686d"/>
    <path d="M0 48H426M0 92L426 76M0 147L426 124" stroke="#9aa7a8" stroke-width="2" opacity=".72"/>
    <path d="M0 151L426 124V240H0Z" fill="#2a393e"/>
    <path d="M0 185L426 143M0 232L426 179" stroke="#718186" stroke-width="1.5"/>
    <g fill="#718085" stroke="#26373d" stroke-width="2"><path d="M36 22h29v132H36z"/><path d="M194 12h28v121h-28z"/><path d="M354 5h29v119h-29z"/></g>'''

def sedan(x, y, scale=1, angle=0):
    return f'''<g transform="translate({x} {y}) rotate({angle}) scale({scale})" stroke="{INK}" stroke-width="2" stroke-linejoin="round">
    <path d="M0 28L13 10H68L85 28L80 45H5Z" fill="{BLACK}"/>
    <path d="M20 11H57L69 27H12Z" fill="{GLASS}"/>
    <path d="M5 32H80" stroke="#3c484c"/><circle cx="20" cy="45" r="8" fill="#11191d"/><circle cx="69" cy="45" r="8" fill="#11191d"/>
    <circle cx="20" cy="45" r="3" fill="#aab5b5"/><circle cx="69" cy="45" r="3" fill="#aab5b5"/><path d="M3 31h7" stroke="{GOLD}" stroke-width="3"/></g>'''

def transport_van(x, y, scale=1, angle=0, rear_open=False):
    rear = '<path d="M72 8h19v43H72z" fill="#172329"/><path d="M75 8l13-15 16 14" fill="#dce4e1"/>' if rear_open else ''
    return f'''<g transform="translate({x} {y}) rotate({angle}) scale({scale})" stroke="{INK}" stroke-width="2" stroke-linejoin="round">
    <path d="M0 12H73L90 26V49H0Z" fill="{VAN}"/><path d="M56 15h17l10 12H56z" fill="{GLASS}"/>
    <path d="M4 25h48" stroke="{GOLD}" stroke-width="4"/><circle cx="18" cy="50" r="8" fill="#172025"/><circle cx="70" cy="50" r="8" fill="#172025"/>{rear}</g>'''

def bag(x, y, s=1):
    return f'''<g transform="translate({x} {y}) scale({s})" stroke="{INK}" stroke-width="2" stroke-linejoin="round"><rect x="4" y="14" width="44" height="28" rx="3" fill="#765a49"/><path d="M15 14V7q11-10 21 0v7" fill="none" stroke-width="3"/><path d="M7 21h37" stroke="#b09170"/></g>'''

def masked(x, ground, scale, flip=1, arm="down"):
    # Full hood + lower-face covering: no white-eye-band shorthand.
    if arm == "approach":
        arm_path = [(0,-90),(25,-70),(38,-51)]
    elif arm == "aim":
        arm_path = [(0,-91),(24,-98),(46,-93)]
    else:
        arm_path = [(0,-90),(23,-70),(29,-48)]
    def p(pt): return (x + flip*pt[0]*scale, ground + pt[1]*scale)
    points = lambda pts: ' '.join(f'{a},{b}' for a,b in map(p, pts))
    hx, hy = p(arm_path[-1])
    return f'''<g stroke="{INK}" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="{x}" cy="{ground+3*scale}" rx="{27*scale}" ry="{4*scale}" fill="#17252a" opacity=".58" stroke="none"/>
      <path d="M{points([(0,-47),(-15,-22),(-22,0)])}" fill="none" stroke="{CLOTH_A if arm=='aim' else CLOTH_B}" stroke-width="{13*scale}"/>
      <path d="M{points([(0,-47),(17,-23),(25,0)])}" fill="none" stroke="{CLOTH_A if arm=='aim' else CLOTH_B}" stroke-width="{13*scale}"/>
      <path d="M{points([(-24,-106),(25,-106),(16,-54),(-15,-54)])}" fill="{CLOTH_A if arm=='aim' else CLOTH_B}" stroke-width="{2*scale}"/>
      <path d="M{points([(0,-103)]+arm_path[1:])}" fill="none" stroke="{CLOTH_A if arm=='aim' else CLOTH_B}" stroke-width="{10*scale}"/>
      <path d="M{points([(0,-103),(-22,-76),(-27,-54)])}" fill="none" stroke="{CLOTH_A if arm=='aim' else CLOTH_B}" stroke-width="{10*scale}"/>
      <ellipse cx="{x}" cy="{ground-132*scale}" rx="{20*scale}" ry="{22*scale}" fill="{MASK}" stroke-width="{2*scale}"/>
      <ellipse cx="{x}" cy="{ground-128*scale}" rx="{14*scale}" ry="{10*scale}" fill="#151d21" stroke="none"/>
      <circle cx="{x-6*scale}" cy="{ground-130*scale}" r="{2.2*scale}" fill="#b6c0bd" stroke="none"/>
      <circle cx="{x+6*scale}" cy="{ground-130*scale}" r="{2.2*scale}" fill="#b6c0bd" stroke="none"/>
      <path d="M{x-10*scale},{ground-117*scale}q10*scale,4*scale 20*scale,0" fill="none" stroke="#778488" stroke-width="{2*scale}"/>
      <circle cx="{hx}" cy="{hy}" r="{4*scale}" fill="{SKIN}" stroke="{INK}"/></g>''', (hx,hy)

def staff_unloading(x, ground, scale):
    # One staff member, intentionally dominant; hand lands on the bag handle.
    hand = (x + 31*scale, ground - 68*scale)
    return f'''<g stroke="{INK}" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="{x}" cy="{ground+3*scale}" rx="{27*scale}" ry="{4*scale}" fill="#17252a" opacity=".55" stroke="none"/>
      <path d="M{x},{ground-49*scale}l{-16*scale},{27*scale}m16*scale,-27l18*scale,27*scale" fill="none" stroke="{STAFF}" stroke-width="{13*scale}"/>
      <path d="M{x-23*scale},{ground-106*scale}h46*scalel{-7*scale},{54*scale}h{-31*scale}z" fill="{STAFF}" stroke-width="{2*scale}"/>
      <path d="M{x},{ground-101*scale}l{20*scale},{ground-79*scale} {31*scale},{ground-68*scale}" fill="none" stroke="{STAFF}" stroke-width="{10*scale}"/>
      <path d="M{x},{ground-101*scale}l{-19*scale},{ground-80*scale} {-27*scale},{ground-60*scale}" fill="none" stroke="{STAFF}" stroke-width="{10*scale}"/>
      <path d="M{x-16*scale},{ground-143*scale}q16*scale,-12*scale 32*scale,0v24*scaleq-16*scale,12*scale -32*scale,0z" fill="{SKIN}" stroke-width="{2*scale}"/>
      <path d="M{x+27*scale},{ground-70*scale}l8*scale,2*scale" stroke="{SKIN}" stroke-width="{5*scale}"/>
      <path d="M{x+6*scale},{ground-135*scale}l4*scale,0" stroke="{INK}" stroke-width="{2*scale}"/></g>''', hand

def top_vehicle(x, y, length, width, fill, angle, label=None):
    # Single top-down camera for S01; each vehicle has a readable front, rear, and ground separation.
    lbl = text(0,4,label,7,INK,'middle') if label else ''
    return f'''<g transform="translate({x} {y}) rotate({angle})" stroke="{INK}" stroke-width="2" stroke-linejoin="round">
      <rect x="{-length/2}" y="{-width/2}" width="{length}" height="{width}" rx="7" fill="{fill}"/>
      <path d="M{-length/2+12},{-width/2+5}h{length-38}v{width-10}h{-length+38}z" fill="{GLASS}"/>
      <path d="M{length/2-6},{-width/2+8}v{width-16}" stroke="#d63f39" stroke-width="4"/>
      <path d="M{-length/2+6},{-width/2+8}v{width-16}" stroke="#f6f2cf" stroke-width="4"/>
      <path d="M{-length/2+16},{-width/2+5}h{length-32}" stroke="#b8c6c5" stroke-width="2"/>{lbl}</g>'''

def scene1():
    # Same overhead camera: transport van advances down, black sedan lies across its front with a deliberate gap.
    lane = '<path d="M257 23V202" stroke="#829296" stroke-width="50" opacity=".36"/><path d="M257 24V174" stroke="#dce5de" stroke-width="2.5" stroke-dasharray="8 7"/>'
    van = top_vehicle(257,91,94,43,VAN,-90,'현금 수송')
    sedan_top = top_vehicle(257,175,105,42,BLACK,0,None)
    arrows = '<path d="M257 25v21m0 0l-7-9m7 9l7-9" stroke="#e8eee9" stroke-width="3" fill="none"/>'
    return garage()+lane+arrows+van+sedan_top+text(14,20,'은행 건물 지하주차장 · 공간 재구성',10)+text(213,231,'검은 승용차가 현금수송차 앞을 막습니다',11,anchor='middle')

def scene2():
    # Bag is fully outside the vehicle.  An oversized, separated sleeve/wrist/fingers closes the hand-to-handle ambiguity at proof scale.
    m1,_ = masked(78,194,.70,1,'approach')
    m2,_ = masked(137,185,.56,1,'approach')
    van = transport_van(305,142,.76,0,False)
    staff = f'''<g stroke="{INK}" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="278" cy="211" rx="26" ry="4" fill="#17252a" opacity=".55" stroke="none"/>
      <path d="M278,164l-15,43m15,-43l18,43" fill="none" stroke="{STAFF}" stroke-width="12"/>
      <path d="M254,105h48l-8,63h-33z" fill="{STAFF}" stroke-width="2"/>
      <path d="M276,105l-12,28 -19,27" fill="none" stroke="{STAFF}" stroke-width="10"/>
      <path d="M278,106l17,22 8,24" fill="none" stroke="{STAFF}" stroke-width="10"/>
      <path d="M262,82q16,-13 32,0v24q-16,12 -32,0z" fill="{SKIN}" stroke-width="2"/>
      <path d="M271,91l5,0" stroke="{INK}" stroke-width="2"/>
      <path d="M244,160q6,-9 15,-1l5,10 -8,8 -15,-5z" fill="{SKIN}" stroke-width="2"/>
      <path d="M246,164l12,4m-13,0l11,4m-12,0l9,4" stroke="{INK}" stroke-width="1.4"/></g>'''
    # Handle centre is under the visible fingers: bag is neither in nor touching the vehicle.
    cash_bag = bag(218,157,1.0)
    return garage()+van+m1+m2+staff+cash_bag+text(14,20,'은행 건물 지하주차장 · 공간 재구성',10)+text(213,231,'돈가방을 내리던 순간 복면을 쓴 두 사람이 나타납니다',10,anchor='middle')

def scene3():
    # Anonymous figure only. The explicit fist/grip and muzzle star establish firing without depicting a target or harm.
    shooter,_ = masked(100,210,1.03,1,'aim')
    wrist_x,wrist_y=147,114
    arm_overlay=f'<path d="M100,107L130,101 147,108" fill="none" stroke="{CLOTH_A}" stroke-width="11" stroke-linecap="round"/>'
    hand=f'<path d="M142,104q8,-8 15,1l4,8 -6,8 -12,-3z" fill="{SKIN}" stroke="{INK}" stroke-width="2"/><path d="M148,108l8,3m-9,3l8,3m-9,3l7,3" stroke="{INK}" stroke-width="1.4"/>'
    gun=f'<g stroke="{INK}" stroke-linejoin="round"><path d="M153,102h43v10h-43z" fill="#192328" stroke-width="2"/><path d="M164,110h12l-5,17h-10z" fill="#192328" stroke-width="2"/><path d="M196,101h6v12h-6z" fill="#11191d" stroke-width="2"/><path d="M203,107l7,-8 3,6 7,2 -7,4 -3,7z" fill="{GOLD}" stroke="{GOLD}" stroke-width="1"/></g>'
    cover = '<path d="M246 61h57v126h-57z" fill="#526367" stroke="#26373d" stroke-width="3"/><path d="M258 79h32M258 98h32" stroke="#91a0a1" stroke-width="2"/>'
    return garage()+cover+transport_van(286,153,.73,0,False)+shooter+arm_overlay+hand+gun+text(14,20,'은행 건물 지하주차장 · 공간 재구성',10)+text(213,231,'권총이 발사됩니다 · 피격·상처 묘사 없음',10,anchor='middle')

scenes = [
    ('S01_setting', scene1(), 0.00, 2.42, '검은 승용차가 현금수송차 앞을 막습니다.', ['F01','F04']),
    ('S02_bag_take', scene2(), 2.42, 5.42, '돈가방을 내리던 순간 복면을 쓴 두 사람이 나타났죠.', ['F01','F02','F04']),
    ('S03_bag_load', scene3(), 5.42, 12.00, '은행 지하주차장에서 권총이 발사됩니다.', ['F01','F04','F06']),
]
svg_head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><g transform="scale({W/426} {H/240})">'
for name, body, *_ in scenes:
    (ROOT/f'{name}.svg').write_text(svg_head+body+'</g></svg>', encoding='utf-8')

scratch = Path('$HOME/.hermes/cache/scratch/lf2_terra_final_svg')
scratch.mkdir(parents=True, exist_ok=True)
for name, *_ in scenes:
    subprocess.run(['qlmanage','-t','-s',str(W),'-o',str(scratch),str(ROOT/f'{name}.svg')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    with Image.open(scratch/f'{name}.svg.png') as im:
        im.crop((0,0,W,H)).convert('RGB').save(ROOT/f'{name}.png')

# Original cue/subtitle boundaries: 0–2.23, 2.42–5.41, 5.42–7.81.  Short pauses retain the preceding image;
# S03 then holds rather than restarting after its utterance ends, while unchanged source audio runs to 12 seconds.
concat = ROOT/'proof_concat.txt'
concat.write_text("".join(f"file '{ROOT/(name+'.png')}'\nduration {end-start+(0.05 if name == 'S02_bag_take' else 0):.2f}\n" for name,_,start,end,*_ in scenes)+f"file '{ROOT/(scenes[-1][0]+'.png')}'\n", encoding='utf-8')
audio = 'episodes/lf2_daejeon_bank/audio/mix_first90_polished.wav'
out = ROOT/'lf2_core_action_proof_640x360.mp4'
subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-ss','0','-t','12','-i',audio,'-map','0:v:0','-map','1:a:0','-c:v','libx264','-pix_fmt','yuv420p','-r','24','-c:a','aac','-shortest',str(out)], check=True)

# Actual decoded MP4 frames at each utterance start/mid/end (not merely a per-shot thumbnail).
extracts = []
for idx, (name, _, start, end, spoken, facts) in enumerate(scenes, 1):
    spoken_end = [2.23, 5.41, 7.81][idx-1]
    for label, t in [('start',start), ('mid',(start+spoken_end)/2), ('end',max(start, spoken_end-0.02))]:
        p = ROOT/f'proof_extract_{idx:02d}_{name}_{label}.png'
        subprocess.run(['ffmpeg','-y','-v','error','-i',str(out),'-ss',f'{t:.3f}','-frames:v','1',str(p)], check=True)
        extracts.append(str(p))

alignment=[]
for idx,(name,_,start,end,spoken,facts) in enumerate(scenes,1):
    utterance_end=[2.23,5.41,7.81][idx-1]
    alignment.append({'shot_id':name,'proof_range_s':[round(start,2),round(end,2)],'narration_audio_range_s':[round(start,2),utterance_end],'spoken_line':spoken,'visual_facts':facts,'cue_source':'_work/full4/subtitles.ass (original N001 cue)','post_utterance_hold':'S03 holds through 12.00 seconds; no action reset.','source_svg':str(ROOT/f'{name}.svg'),'proof_png':str(ROOT/f'{name}.png'),'decoded_mp4_frames':extracts[(idx-1)*3:idx*3],'decoded_end_sample_s':round(max(start, utterance_end-0.02),2)})
(ROOT/'shot_audio_visual_reference.json').write_text(json.dumps(alignment,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'README.md').write_text('''# LF2 핵심 동작 시안 (CEO 검수용)\n\n- 640×360, 12초 proof만 갱신했다. 1080p 및 전편 렌더는 하지 않았다.\n- 음성은 기존 `audio/mix_first90_polished.wav`의 0–12초 그대로다. 원본 cue(`_work/full4/subtitles.ass`)의 세 문장 범위는 0.00–2.23, 2.42–5.41, 5.42–7.81초다.\n- S01은 차량 차단 관계, S02는 가방을 내리는 운송관계자와 뒤/옆에 나타난 두 복면인, S03은 익명 복면인의 손·팔에 연결된 권총 발사만 보인다. 피격·상처·발사자 신원은 묘사하지 않는다.\n- `proof_extract_*_start|mid|end.png`은 각 실제 발화의 시작·중간·끝에서 MP4를 디코드한 프레임이다. S03은 마지막 발화 뒤에도 같은 장면을 유지한다.\n''',encoding='utf-8')
print('created', len(scenes), 'SVG scenes, 640x360 12s proof, and', len(extracts), 'decoded narration frames')
