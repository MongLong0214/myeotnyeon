from pathlib import Path
import json,csv,sys
O=Path('/Users/isaac/projects/verdict-kr/work/upload/inspect_v52/cards')
SEGS={'q015':[(0,85,'S01 hook'),(86,294,'S02 숫자·쟁점 카드'),(659,704,'S05 end card')],'q012':[(0,60,'S01 hook'),(61,181,'S02 산불 도해'),(182,367,'S03 과수원'),(368,438,'S04 확산 도해'),(439,541,'S05 추모 카드'),(917,966,'S08 종료')],'q016':[(0,81,'S01 hook'),(82,428,'S02 주장·판단 카드'),(841,889,'S05 종료')],'q017':[(0,60,'S01 hook'),(61,180,'S02 사건·주장 카드'),(181,267,'S03 구형 카드'),(623,671,'S06 종료')]}
N={'q015':705,'q012':967,'q016':890,'q017':672}
def runs(fs):
 r=[]
 for f in sorted(fs):
  if r and f==r[-1][1]+1:r[-1][1]=f
  else:r.append([f,f])
 return ', '.join(str(a) if a==b else f'{a}–{b}' for a,b in r) or '없음'
def write(q):
 p=O/q;s=set(json.loads((p/'sample_manifest.json').read_text())['frames']);t=set();e=set()
 for label in ['trans','extra','fill','end_context']:
  path=p/f'{label}_manifest.json'
  if path.exists():
   m=json.loads(path.read_text());t.update(m['frames'])
   if m['crop']==[0,0,1080,1920]:e.update(m['frames'])
 with (p/'coverage.csv').open('w') as o:
  w=csv.writer(o);w.writerow(['frame','time_seconds','segment','visual_status','scope'])
  for f in range(N[q]):
   seg=next((n for a,b,n in SEGS[q] if a<=f<=b),'EXCLUDED judge')
   status='INSPECTED' if f in s|t else 'NOT_INSPECTED'
   scope='full 1080x1920 CONSECUTIVE' if f in e else 'full 1080x1920 SAMPLE' if f in s else 'native crop x0:1080 y100:1700 CONSECUTIVE' if f in t else 'none'
   w.writerow([f,f'{f/30:.6f}',seg,status,scope])
 for a,b,name in SEGS[q]:
  print(name,'SAMPLE',len(s&set(range(a,b+1))),'CONSEC',runs(t&set(range(a,b+1))),'NOT',runs(set(range(a,b+1))-s-t))
if __name__=='__main__':write(sys.argv[1])
