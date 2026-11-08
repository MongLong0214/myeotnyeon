#!/usr/bin/env python3
"""N18 approval proof: vector source only; low-resolution review output."""
from pathlib import Path
import json, subprocess

ROOT = Path(__file__).parent
SVG = ROOT / "svg"
W,H = 1920,1080

# The drawings are intentionally anonymous, conceptual and non-medical.
# Each pose is a distinct 3/4 spatial composition, not a crop of one drawing.
COMMON = '''<defs>
 <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#b9d6df"/><stop offset="1" stop-color="#f3e7c7"/></linearGradient>
 <linearGradient id="ground" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#afb985"/><stop offset="1" stop-color="#647350"/></linearGradient>
 <linearGradient id="uniform" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#71836b"/><stop offset="1" stop-color="#394e44"/></linearGradient>
 <linearGradient id="pack" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#8a7251"/><stop offset="1" stop-color="#493c2e"/></linearGradient>
 <filter id="soft"><feGaussianBlur stdDeviation="10"/></filter>
</defs>
<style>.o{stroke:#26332f;stroke-width:13;stroke-linejoin:round;stroke-linecap:round}.thin{stroke:#26332f;stroke-width:8;stroke-linecap:round;fill:none}.sub{font-family:'Apple SD Gothic Neo','Noto Sans CJK KR',sans-serif;font-weight:700;fill:#fff}.note{font-family:'Apple SD Gothic Neo','Noto Sans CJK KR',sans-serif;fill:#27352f;font-weight:600}</style>'''

def field(extra):
 return f'''<rect width="1920" height="1080" fill="url(#sky)"/>
 <path d="M0 445 C300 375 540 410 760 448 C1120 500 1510 370 1920 438V690H0Z" fill="#90a475" opacity=".75"/>
 <path d="M0 560 L1920 520 L1920 1080 L0 1080Z" fill="url(#ground)"/>
 <path d="M0 710 L1920 625 M0 830 L1920 745 M0 965 L1920 875" stroke="#d4cea7" stroke-width="9" opacity=".58"/>
 <path d="M950 550 L180 1080 M950 550 L650 1080 M950 550 L1240 1080 M950 550 L1840 1080" stroke="#596a50" stroke-width="8" opacity=".65"/>
 <ellipse cx="955" cy="562" rx="760" ry="55" fill="#fff8dc" opacity=".28" filter="url(#soft)"/>{extra}'''

def human(x,y,s,pose,flip=False,pack=False,accent="#71836b"):
 # Self-contained articulated, three-quarter cartoon anatomy. Limbs are tapered polygons,
 # hands have palm + fingers; boots/shadows make the stance readable at 240p.
 F = -1 if flip else 1
 def X(v): return x+F*v*s
 out=[]
 out.append(f'<ellipse cx="{X(10)}" cy="{y+493*s}" rx="{135*s}" ry="{24*s}" fill="#344139" opacity=".42" filter="url(#soft)"/>')
 # rear leg and forward leg; knees visibly separate
 if pose=="ready":
  out += [f'<path class="o" fill="{accent}" d="M {X(-28)} {y+275*s} L {X(-95)} {y+390*s} L {X(-54)} {y+474*s} L {X(0)} {y+458*s} L {X(-14)} {y+382*s} L {X(44)} {y+300*s}Z"/>',
          f'<path class="o" fill="{accent}" d="M {X(48)} {y+280*s} L {X(123)} {y+368*s} L {X(184)} {y+468*s} L {X(126)} {y+487*s} L {X(56)} {y+394*s} L {X(-8)} {y+319*s}Z"/>']
 elif pose=="lean":
  out += [f'<path class="o" fill="{accent}" d="M {X(-42)} {y+296*s} L {X(-150)} {y+390*s} L {X(-190)} {y+471*s} L {X(-127)} {y+478*s} L {X(-80)} {y+410*s} L {X(9)} {y+337*s}Z"/>',
          f'<path class="o" fill="{accent}" d="M {X(20)} {y+298*s} L {X(87)} {y+395*s} L {X(165)} {y+441*s} L {X(137)} {y+488*s} L {X(28)} {y+442*s} L {X(-52)} {y+330*s}Z"/>']
 else: # grounded: hip folded, one shin planted and one knee tucked
  out += [f'<path class="o" fill="{accent}" d="M {X(-15)} {y+290*s} L {X(-136)} {y+362*s} L {X(-196)} {y+450*s} L {X(-136)} {y+470*s} L {X(-48)} {y+405*s} L {X(50)} {y+343*s}Z"/>',
          f'<path class="o" fill="{accent}" d="M {X(33)} {y+291*s} L {X(122)} {y+347*s} L {X(75)} {y+423*s} L {X(7)} {y+443*s} L {X(45)} {y+366*s} L {X(-45)} {y+329*s}Z"/>']
 # boots
 out += [f'<path class="o" fill="#252c2a" d="M {X(-197)} {y+448*s} Q {X(-221)} {y+478*s} {X(-166)} {y+482*s} L {X(-110)} {y+471*s} L {X(-130)} {y+448*s}Z"/>', f'<path class="o" fill="#252c2a" d="M {X(135)} {y+452*s} Q {X(111)} {y+487*s} {X(176)} {y+494*s} L {X(224)} {y+476*s} L {X(174)} {y+442*s}Z"/>']
 # torso, pelvis and neck
 torso = "M -80 92 L 79 66 L 126 260 L 45 314 L -92 276 Z" if pose!="ground" else "M -110 128 L 55 96 L 128 257 L 36 316 L -116 274 Z"
 pts=[]
 # reflect path numerics is awkward; group mirroring around x
 out.append(f'<g transform="translate({x} 0) scale({F} 1) translate({-x} 0)"><path class="o" fill="{accent}" d="{torso.replace(str(92),str(y+92*s)).replace(str(66),str(y+66*s)).replace(str(260),str(y+260*s)).replace(str(314),str(y+314*s)).replace(str(276),str(y+276*s)).replace(str(128),str(y+128*s)).replace(str(96),str(y+96*s)).replace(str(257),str(y+257*s)).replace(str(316),str(y+316*s)).replace(str(274),str(y+274*s))}" transform="translate({x} 0) scale({s} {s}) translate({-x} 0)"/></g>')
 # This replacement transform is not relied on for dimensions; torso overlay below is exact.
 out[-1] = f'<path class="o" fill="{accent}" d="M {X(-80)} {y+92*s} L {X(79)} {y+66*s} L {X(126)} {y+260*s} L {X(45)} {y+314*s} L {X(-92)} {y+276*s}Z"/>'
 # head / cap angled 3/4
 out += [f'<path class="o" fill="#d1a681" d="M {X(-38)} {y+36*s} L {X(30)} {y+28*s} L {X(42)} {y+92*s} L {X(-31)} {y+105*s}Z"/>',
 f'<path class="o" fill="#d9ad86" d="M {X(-75)} {y-72*s} Q {X(-3)} {y-125*s} {X(71)} {y-64*s} L {X(58)} {y+33*s} Q {X(2)} {y+76*s} {X(-64)} {y+25*s}Z"/>',
 f'<path class="o" fill="#425646" d="M {X(-84)} {y-65*s} Q {X(-8)} {y-132*s} {X(80)} {y-66*s} L {X(72)} {y-34*s} L {X(-93)} {y-20*s}Z"/>',
 f'<path class="thin" d="M {X(23)} {y-18*s} L {X(40)} {y-20*s}"/><path class="thin" d="M {X(18)} {y+27*s} Q {X(34)} {y+36*s} {X(48)} {y+25*s}"/>']
 # arms/hands: distinct shoulder-elbow-wrist geometry
 if pose=="ready": arms=[((-73,125),(-137,213),(-92,275)),((71,119),(147,176),(162,245))]
 elif pose=="lean": arms=[((-74,126),(-143,195),(-170,273)),((74,121),(137,187),(184,235))]
 else: arms=[((-83,145),(-137,267),(-177,365)),((73,138),(141,245),(198,308))]
 for a,b,c in arms:
  out.append(f'<path class="o" fill="{accent}" d="M {X(a[0]-14)} {y+a[1]*s} L {X(b[0]-13)} {y+b[1]*s} L {X(c[0]-11)} {y+c[1]*s} L {X(c[0]+16)} {y+c[1]*s} L {X(b[0]+18)} {y+b[1]*s} L {X(a[0]+15)} {y+a[1]*s}Z"/>')
  # palm + three fingers, no circular hands
  out.append(f'<path class="o" fill="#d9ad86" d="M {X(c[0]-16)} {y+(c[1]-8)*s} L {X(c[0]+20)} {y+(c[1]-7)*s} L {X(c[0]+29)} {y+(c[1]+18)*s} L {X(c[0]+12)} {y+(c[1]+29)*s} L {X(c[0]-10)} {y+(c[1]+17)*s}Z"/><path class="thin" d="M {X(c[0]+4)} {y+(c[1]+3)*s} L {X(c[0]+16)} {y+(c[1]+16)*s} M {X(c[0]-6)} {y+(c[1]+4)*s} L {X(c[0]+5)} {y+(c[1]+19)*s}"/>')
 if pack:
  out += [f'<path class="o" fill="url(#pack)" d="M {X(-150)} {y+88*s} Q {X(-205)} {y+160*s} {X(-166)} {y+271*s} L {X(-84)} {y+283*s} L {X(-68)} {y+105*s} Q {X(-109)} {y+75*s} {X(-150)} {y+88*s}Z"/>', f'<path class="thin" d="M {X(-133)} {y+122*s} L {X(-149)} {y+234*s} M {X(-191)} {y+165*s} L {X(-92)} {y+179*s}"/>', f'<path class="thin" d="M {X(-70)} {y+118*s} Q {X(-7)} {y+142*s} {X(46)} {y+266*s}"/>']
 return ''.join(out)

def scene1():
 extra=f'''<g opacity=".72">{human(430,360,.62,'ready',pack=True)}{human(730,395,.62,'ready',pack=True)}{human(1310,405,.59,'ready',flip=True,pack=True)}{human(1590,380,.67,'ready',flip=True,pack=True)}</g>
 {human(1020,215,1.12,'ready',pack=True)}
 <path d="M1770 370 L1830 366 L1838 617 L1783 621Z" fill="#475c48" class="o"/><path d="M1745 369 L1870 358 L1850 404 L1760 416Z" fill="#52694f" class="o"/>
 <rect x="65" y="38" width="590" height="70" rx="14" fill="#f8efd5" opacity=".90"/><text x="92" y="84" class="note" font-size="46">개념 장면 · 실제 배치 아님</text>
 <rect x="80" y="875" width="1760" height="145" rx="24" fill="#1d2928" opacity=".94"/><text x="960" y="938" text-anchor="middle" class="sub" font-size="53">절차와 방법을 위반한 군기훈련,</text><text x="960" y="1002" text-anchor="middle" class="sub" font-size="53">이른바 얼차려였다.</text>'''
 return field(extra)
def scene2():
 extra=f'''<g opacity=".55">{human(370,390,.64,'ready',pack=True)}{human(1515,415,.62,'ready',flip=True,pack=True)}</g>
 {human(990,215,1.18,'lean',pack=True)}
 <path d="M1115 530 Q1260 547 1370 594" class="thin" stroke="#d9cc9d" stroke-width="16" opacity=".85"/>
 <path d="M1525 595 Q1590 560 1670 574" class="thin" stroke="#384b3e" stroke-width="24"/>
 <rect x="65" y="38" width="590" height="70" rx="14" fill="#f8efd5" opacity=".90"/><text x="92" y="84" class="note" font-size="46">개념 장면 · 실제 배치 아님</text>
 <rect x="80" y="875" width="1760" height="145" rx="24" fill="#1d2928" opacity=".94"/><text x="960" y="938" text-anchor="middle" class="sub" font-size="51">훈련 도중 의식을 잃은 훈련병에게</text><text x="960" y="1002" text-anchor="middle" class="sub" font-size="51">적절한 조치를 하지 않았다는 혐의도 포함된다.</text>'''
 return field(extra)
def scene3():
 extra=f'''<path d="M365 720 Q930 648 1485 736" stroke="#d1c691" stroke-width="20" opacity=".5" fill="none"/>
 {human(1050,215,1.08,'ground',pack=True)}
 {human(535,355,.80,'ground',flip=True,pack=False)}
 {human(1540,348,.78,'ready',flip=True,pack=True)}
 <path d="M1400 725 Q1488 752 1564 724" class="thin" stroke="#3b5140" stroke-width="20"/>
 <rect x="65" y="38" width="590" height="70" rx="14" fill="#f8efd5" opacity=".90"/><text x="92" y="84" class="note" font-size="46">개념 장면 · 실제 배치 아님</text>
 <rect x="80" y="900" width="1760" height="110" rx="24" fill="#1d2928" opacity=".94"/><text x="960" y="970" text-anchor="middle" class="sub" font-size="49">적절한 조치를 하지 않았다는 혐의도 포함된다.</text>'''
 return field(extra)

SCENES=[('01_preparation_wide.svg',scene1,'N003',0.00,6.06,'RM-0003'),('02_action_weight_shift.svg',scene2,'N004',6.40,11.23,'RM-0006'),('03_settled_grounded.svg',scene3,'N005',11.56,18.23,'RM-0003')]
def wrap(content): return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{COMMON}{content}</svg>'
def main():
 SVG.mkdir(exist_ok=True)
 rows=[]
 for name,fn,nid,start,end,ref in SCENES:
  (SVG/name).write_text(wrap(fn()),encoding='utf-8')
  rows.append({'shot_id':name[:2],'source_svg':'svg/'+name,'narration_id':nid,'source_audio_start_s':round(11.17+start,2),'proof_start_s':start,'proof_end_s':end,'facts':['E03','E04'] if name!='01_preparation_wide.svg' else ['E01','E02','E03'],'reference_ref_id':ref,'description':{'01':'3/4 setting wide: six anonymous trainees, attached packs and planted boots','02':'3/4 action: forward weight shift, bent knees, pack straps and separated reacting figures','03':'3/4 settled pose: forearm/hand, bent knee, boots and ground shadow visibly connect'}[name[:2]]})
 (ROOT/'proof_timing.json').write_text(json.dumps({'output_resolution':'426x240','source_audio':'../audio/mix_master.wav','source_audio_range_s':[11.17,29.40],'shots':rows},ensure_ascii=False,indent=2),encoding='utf-8')
 # 426x240 is intentional approval-only rasterization. SVG sources retain vector detail for later approved render.
 for name,*_ in SCENES:
  out=ROOT/(name.replace('.svg','.png'))
  # Chrome captures the vector source directly into the approval canvas; no high-resolution raster is emitted.
  wrapper=ROOT/'_approval_raster_wrapper.html'
  wrapper.write_text(f'<!doctype html><style>html,body{{margin:0;width:426px;height:240px;overflow:hidden;background:#000}}img{{display:block;width:426px;height:240px}}</style><img src="{SVG.joinpath(name).as_uri()}">',encoding='utf-8')
  subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless','--disable-gpu','--hide-scrollbars','--force-device-scale-factor=1','--window-size=426,240',f'--screenshot={out}',wrapper.as_uri()],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 concat=ROOT/'proof.ffconcat'
 concat.write_text('ffconcat version 1.0\n'+''.join(f"file '{(ROOT/name.replace('.svg','.png')).as_posix()}'\nduration {end-start:.3f}\n" for name,fn,nid,start,end,ref in SCENES)+f"file '{(ROOT/'03_settled_grounded.png').as_posix()}'\n",encoding='utf-8')
 subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-ss','11.17','-t','18.23','-i',str(ROOT.parent/'audio'/'mix_master.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','96k','-shortest',str(ROOT/'n18_terra_final_approval_proof_426x240.mp4')],check=True)
if __name__=='__main__': main()
