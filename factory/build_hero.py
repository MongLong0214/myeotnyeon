"""Run the existing world2 hero builder with package-local output and a cabin set."""
from pathlib import Path
import sys
q,out=sys.argv[sys.argv.index('--')+1:sys.argv.index('--')+3]
out=Path(out);out.mkdir(exist_ok=False)
W=Path(__file__).resolve().parents[1]
source=W/'episodes/quiz/v52_q013_q014_support/build_hero.py'
code=source.read_text().replace("p=W/'research/hook_stills'",f'p=Path({str(out)!r})')
# Reuse the builder's world2 setup, lights, materials, camera, render and evidence.
# The q011 branch is an invented closed cabin: no airline, people or open door.
cabin='''elif q=='q011':
 bpy.data.objects['asphalt'].hide_render=True
 ivory=A.mat('cabin ivory',(.7,.74,.76),rough=.55)
 navy=A.mat('seat fabric',(.025,.06,.12),rough=.9)
 A.box('cabin floor',(7,22,.16),(0,8,-.1),navy,.02)
 A.box('closed cabin wall',(.25,24,5),(3.4,8,2.4),ivory,.08)
 A.box('closed exit panel',(.12,2.2,3.7),(3.22,3.8,1.95),wall,.14)
 A.box('closed exit inset',(.13,1.75,2.9),(3.13,3.8,2.05),ivory,.18)
 A.box('unmarked lever',(.2,.7,.13),(2.98,3.6,2.05),metal,.04)
 for y in [1,7.4,11.4,15.4]:
  A.box('oval window rim',(.13,1.3,1.25),(3.18,y,3.1),ivory,.3)
  A.box('blue window',(.14,.85,.85),(3.08,y,3.1),glass,.27)
 for y in [1,5,9,13,17]:
  for x in [-1.4,-.1]:
   A.box('empty seat back',(1.1,.35,1.65),(x,y,1.35),navy,.2)
   A.box('empty seat cushion',(1.1,1.1,.3),(x,y-.4,.58),navy,.1)
 A.box('ceiling',(7,24,.2),(0,8,4.9),ivory,.08)
 area('cabin soft light',(-1,1,4.5),(3,5,1.5),1700,(.58,.75,1),(4,9))
 area('window daylight',(2,10,3.8),(-1,5,1),1300,(.3,.55,1),(2,7))
 camera=(-2.5,-3,1.8);target=(3.15,4,2.4);lens=23
'''
code=code.replace("else:\n for side in [-1,1]:",cabin+"else:\n for side in [-1,1]:",1)
exec(compile(code,str(source),'exec'))
