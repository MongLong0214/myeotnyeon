from pathlib import Path
import subprocess,os,time
W=Path(__file__).resolve().parents[3]
for q in ['q015','q012','q016','q017']:
 p=W/'episodes/quiz'/q/'v5'
 while not all(f.exists() and f'DONE {mode} {q}' in f.read_text() for mode,f in [('render',p/'render_r4.log'),('audit',p/'audit_r4.log')]):time.sleep(5)
 with (p/'qa_r4.log').open('w') as log:
  r=subprocess.run([str(W/'.venv/bin/python'),str(W/'episodes/quiz/v5_support/qa_v5.py'),q],cwd=W,stdout=log,stderr=subprocess.STDOUT)
 print(q,'QA exit',r.returncode,flush=True)
 if r.returncode:print((p/'qa_r4.log').read_text()[-2000:],flush=True)
