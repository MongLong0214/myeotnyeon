"""Run the local anatomy kit gates for the main episode. Drafts stay on this machine."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

MAIN=Path(__file__).resolve().parent
WORK=MAIN.parents[2]
KIT=WORK/"anat_kit/gates"
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
MLX=WORK/"research/tts_bakeoff/venvs/mlx/bin/python"
ap=argparse.ArgumentParser()
ap.add_argument("draft_number",type=int,choices=range(1,6))
ap.add_argument("--draft",required=True,action="store_true")
ap.add_argument("--skip-blender",action="store_true")
args=ap.parse_args()
tag=f"main_draft{args.draft_number}"
video=MAIN.parent/f"{tag}.mp4"
if not video.is_file():
    raise SystemExit(f"Missing {video}")
reports=MAIN/"gates"
env=dict(os.environ)
env["PYTHONPATH"]=str(WORK/".venv/lib/python3.12/site-packages")

def run(name,cmd):
    out=reports/f"{tag}_{name}.json"
    with out.open("w") as log, (reports/f"{tag}_{name}.log").open("w") as err:
        p=subprocess.run([str(s) for s in cmd],stdout=log,stderr=err,env=env,cwd=MAIN)
    print(name,p.returncode,flush=True)
    return out

def kit(name,*args):
    return run(name,[sys.executable,KIT/f"{name}_gate.py",*args])

run("video",[sys.executable,KIT/"video_gates.py",video,MAIN/f"frames_{tag}",reports/"layout.json","--draft"])
kit("facts",MAIN)
kit("description",MAIN)
kit("audio",MAIN,video)
run("credit_ui",[sys.executable,KIT/"credit_ui_check.py",video,MAIN,reports/f"{tag}_credit_ui.png"])
run("narration",["nice","-n","15",MLX,KIT/"narration_gate.py",MAIN,video])
kit_names=("subject_size","dead_time","frame_cadence",
           "text_size","labels_anchored","label_beat_alignment","layout_uses_height","audio_beat_balance")
sys.path.insert(0,str(KIT))
import checks
ep=json.loads((MAIN/"episode.json").read_text())
raw=MAIN/f"frames_{tag}_raw"
thresholds=json.loads((MAIN.parent/"thresholds.json").read_text())
rows={}
kwargs=(raw,ep)
calls=(
    (raw,), kwargs, (raw,),
    (ep,), (ep,), (ep,), (ep,),
    (MAIN/"audio/sfx.wav",[(b["t0"],b["t1"]) for b in ep["beats"]]),
)
for n,params in zip(kit_names,calls):
    ok,details=getattr(checks,n)(*params)
    rows[n]={"ok":bool(ok),**details}
for name,(ok,details) in checks.opening_checks(raw,{},thresholds).items():
    rows[name]={"ok":bool(ok),**details}
lines=json.loads((MAIN/"audio/narration.json").read_text())
gaps=[round(b["start"]-a["end"],3) for a,b in zip(lines,lines[1:])]
bookends=[round(lines[0]["start"],3),round(ep["duration"]-lines[-1]["end"],3)]
rows["brief_narration"]={"ok":all(6.2<=l["rate"]<=6.6 for l in lines) and max(gaps+bookends)<=.2,
    "syllables_per_second":[l["rate"] for l in lines],"interline_gaps_s":gaps,"bookends_s":bookends}
rows["pass"]=all(r["ok"] for r in rows.values())
(reports/f"{tag}_checks.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2,default=str)+"\n")
if not args.skip_blender:
    blender=["nice","-n","15",BLENDER,"-b","--factory-startup"]
    def run_blender(*cmd, **kwargs):
        while subprocess.run(["pgrep","-x","Blender"],stdout=subprocess.DEVNULL).returncode == 0:
            time.sleep(1)
        return subprocess.run([*blender,str(MAIN/"jaw.blend"),"--python-exit-code","1",*cmd],
                              check=True,**kwargs)

    out=reports/f"{tag}_provenance_jaw.json"
    with (reports/f"{tag}_provenance_jaw.log").open("w") as log:
        run_blender("-P",str(KIT/"provenance_gate.py"),"--",str(out),stdout=log,stderr=subprocess.STDOUT)
    result=run_blender("-P",str(KIT/"geo_gate.py"),"--",str(reports/"geometry.json"),
                       capture_output=True,text=True).stdout
    token=next(line.removeprefix("GATE_JSON ") for line in result.splitlines() if line.startswith("GATE_JSON "))
    (reports/f"{tag}_geometry.json").write_text(json.dumps(json.loads(token),indent=2)+"\n")
print("local reports:",reports,flush=True)
