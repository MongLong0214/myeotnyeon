#!/usr/bin/env python3
"""Opus grades a movie or composited preflight stills against the EBS=7 rubric.
Read-only evidence includes the reference, layout, close views and motion, audio
measurements and class-specific dispositions. --historical omits mutable sidecars
and review labels. Use --out outside the source episode when replaying an archive.
Exit 0 pass, 1 editorial fail, 2 grader error.
"""
import sys, os, json, subprocess, re, hashlib, math, time
import numpy as np
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import shutil
from PIL import Image, ImageDraw
from review_classes import MOVIE_ONLY, checklist, review_failures
from score_scale import predict

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thresholds import T

args = sys.argv[1:]
def opt(name, default=None):
    return args[args.index(name) + 1] if name in args else default
E = os.path.abspath(args[0]); TAG = args[1]
MODEL = opt('--model', 'opus'); MP4 = os.path.abspath(opt('--mp4', f'{E}/{TAG}.mp4'))
OUT = os.path.abspath(opt('--out', f'{E}/gates')); DRY = '--dry-run' in args
MODE = ('a DRAFT render (reduced resolution and samples): judge noise and softness only where they make a structure or text unreadable'
        if '--draft' in args else 'the FINAL render: judge everything')
MAT = f'{OUT}/review_{TAG}'; os.makedirs(MAT, exist_ok=True)
PYW = sys.executable
HISTORICAL = '--historical' in args
STILLS = opt('--stills')
FAMILY = 'fable' if 'fable' in MODEL else ('opus' if 'opus' in MODEL else MODEL)
cfg = T['review_gate'].get(FAMILY) or T['review_gate']['opus']

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def probe(p):
    s = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries',
                                   'stream=width,height,nb_read_packets,r_frame_rate', '-of', 'json', p], capture_output=True, text=True).stdout)['streams'][0]
    n, d = map(int, s['r_frame_rate'].split('/')); return s['width'], s['height'], int(s['nb_read_packets']), n / d

def grab(t, out, vf=None):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', MP4, '-frames:v', '1'] + (['-vf', vf] if vf else []) + [out], check=True)
    return out

def luma_profile():
    """Mean abs luma difference between consecutive frames of the whole file (at 1/4 size)."""
    w, h = 270, 480
    cmd = ['ffmpeg', '-v', 'error', '-i', MP4, '-vf', f'scale={w}:{h},format=gray', '-f', 'rawvideo', '-']
    deltas = []
    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as pipe:
        prev = None
        while raw := pipe.stdout.read(w * h):
            current = np.frombuffer(raw, np.uint8).astype(np.int16)
            if prev is not None:
                deltas.append(float(np.abs(current - prev).mean()))
            prev = current
        if pipe.wait() or not deltas:
            raise ValueError('could not measure video motion')
    return np.asarray(deltas)

def loudness():
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', MP4, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    g = lambda k: (re.findall(k + r':\s+(-?[\d.]+)', r) or ['nan'])[-1]
    return {'integrated_lufs': g('I'), 'lra_lu': g('LRA'), 'true_peak_dbfs': g('Peak')}

def transcript():
    wav = f'{MAT}/audio.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', MP4, '-ac', '1', '-ar', '16000', wav], check=True)
    code = ("import mlx_whisper,json,sys;r=mlx_whisper.transcribe(sys.argv[1],path_or_hf_repo='mlx-community/whisper-small-mlx',language='ko');"
            "print(json.dumps([[round(s['start'],1),round(s['end'],1),s['text'][:200]] for s in r['segments']],ensure_ascii=False))")
    r = subprocess.run([PYW, '-c', code, wav], capture_output=True, text=True, timeout=600)
    try: return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: return None

def build_material():
    W, H, nf, fps = probe(MP4); dur = nf / fps; files = []
    for s in range(math.ceil(dur / 12)):   # 1 fps contact sheets, 12 frames each (6x2 at 360x640)
        o = f'{MAT}/sheet_{s:02d}.png'
        vf = f"select='between(t,{12*s},{12*s+11.99})*not(mod(n,{round(fps)}))',scale=360:640,tile=6x2"
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', MP4, '-vf', vf, '-fps_mode', 'vfr', '-frames:v', '1', o], check=True)
        files.append((o, f'1 fps contact sheet, seconds {12*s}-{min(int(dur), 12*s+11)} (left to right, top row first; frame = second x {round(fps)})'))
    for i in range(12):
        t = (i + 0.5) * dur / 12; f = round(t * fps)
        files.append((grab(t, f'{MAT}/still_f{f:04d}.png'), f'full frame {W}x{H}, frame {f}'))
    yb = round(H * 1500 / 1920); f = round(dur * 0.9 * fps)
    files.append((grab(dur * 0.9, f'{MAT}/bottom_f{f:04d}.png', f'crop={W}:{H - yb}:0:{yb}'), f'bottom of the full frame (y 1500-1920), frame {f}'))
    it = f'{E}/items.json'   # reviewer-cited boxes from the previous round, cut from THIS mp4: claimed fixes are judged on these
    if not HISTORICAL and os.path.exists(it):
        by = (json.load(open(E + '/episode.json')).get('layout', {}) if os.path.exists(E + '/episode.json') else {}).get('band_y', 470); sx = W / 1080
        for k, item in enumerate(json.load(open(it))):
            x0, y0, x1, y1 = item['box']; f = item['frame']
            o = grab(f / fps, f'{MAT}/item{k}_f{f:04d}.png', f'crop={int((x1-x0)*sx)}:{int((y1-y0)*sx)}:{int(x0*sx)}:{int((y0+by)*sx)},scale=iw*2:-1')
            files.append((o, f'reviewer crop "{item["id"]}" at frame {f}, band box {item["box"]}, enlarged 2x'))
    d = luma_profile(); runs, cur = [], []
    for i, v in enumerate(d):
        if v < 0.25: cur.append(i + 1); continue
        if len(cur) >= 10: runs.append([cur[0], cur[-1]])
        cur = []
    if len(cur) >= 10: runs.append([cur[0], cur[-1]])
    steps = sorted(((float(v), i + 1) for i, v in enumerate(d)), reverse=True)[:10]
    meas = {'frames': nf, 'fps': fps, 'duration_s': round(dur, 2), 'luma_diff_median': round(float(np.median(d)), 3),
            'largest_steps_[delta,frame]': [[round(v, 2), f] for v, f in steps],
            'near_still_runs_>=10_frames_(delta<0.25)': runs[:10],
            'per_second_mean_delta': [round(float(d[int(s*fps):int((s+1)*fps)].mean()), 2) for s in range(int(dur))],
            'loudness': loudness(), 'transcript_[start,end,text]': transcript()}
    json.dump(meas, open(f'{MAT}/measurements.json', 'w'), ensure_ascii=False, indent=1)
    ep = None
    if not HISTORICAL and os.path.exists(E + '/episode.json') and abs(json.load(open(E + '/episode.json')).get('duration', 0) - dur) < 0.2: ep = E + '/episode.json'
    # A one-second stride skips entire dissolves. Sample the band eight times/s
    # for those short-lived defects; the static full stills retain layout context.
    for start in range(0, math.ceil(dur), 4):
        image = f'{MAT}/motion_{start:03d}.jpg'
        vf = "fps=8,crop=iw:ih/2:0:ih/4,scale=240:-2,tile=8x4"
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(start),'-i',MP4,'-t','4','-vf',vf,
                        '-frames:v','1',image], check=True)
        if not os.path.isfile(image): raise ValueError(f'missing motion strip at {start}s')
        files.append((image, f'band motion strip, first frame at {start}s, 8 columns per second; black trailing cells are padding'))
    return files, meas, ep

ITEM = {"type": "object", "required": ["frame", "what", "box"], "properties": {"frame": {"type": "integer"}, "what": {"type": "string"}, "box": {"type": "array", "items": {"type": "number"}}}}
AREAS = ["anatomy", "cutaway", "motion", "labels", "hook", "facts", "audio"]
SCHEMA = {"type": "object", "required": ["scores", "final", "p0", "p1", "not_checked", "pass"], "properties": {
    "scores": {"type": "object", "required": AREAS, "properties": {k: {"type": "number"} for k in AREAS}},
    "final": {"type": "number"}, "p0": {"type": "array", "items": ITEM}, "p1": {"type": "array", "items": ITEM},
    "not_checked": {"type": "array", "items": {"type": "string"}}, "pass": {"type": "boolean"}}}

FINAL_ANCHOR = FAMILY == "fable" and "--single-audit" in args
if FINAL_ANCHOR:
    from anchored_review import SCHEMA as PICTURE_SCHEMA
    SCHEMA["required"].append("picture_axes")
    SCHEMA["properties"]["picture_axes"] = PICTURE_SCHEMA["properties"]["axes"]

def rubric_final(s):
    v = [float(s[k]) for k in AREAS]; return math.floor(((min(v) + sum(v) / len(v)) / 2) * 2) / 2

DISPOSITIONS = ('clear', 'absent', 'unseen', 'defects')
SCHEMA['properties']['inspection'] = {'type':'object', 'required':list(DISPOSITIONS), 'properties': {
    key: {'type':'array', 'items':{'type':'string'}} for key in DISPOSITIONS}}
SCHEMA['required'].append('inspection')
SCHEMA['properties']['final'].update(minimum=1, maximum=10, multipleOf=0.5)
for spec in SCHEMA['properties']['scores']['properties'].values():
    spec.update(minimum=1, maximum=10, multipleOf=0.5)

def claude(prompt, schema, cwd):
    cmd = ['claude', '-p', '--model', MODEL, '--output-format', 'json', '--no-session-persistence', '--strict-mcp-config',
           '--tools', 'Read', '--allowedTools', 'Read', '--disable-slash-commands', '--json-schema', json.dumps(schema),
           '--max-budget-usd', str(cfg.get('max_usd', 20))]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=cfg.get('timeout_s', 2400), cwd=cwd)
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout)[-1000:])
    env = json.loads(r.stdout)
    if env.get('is_error'): raise RuntimeError(env.get('result',env.get('subtype')))
    body = env.get('structured_output') or env.get('result', '')
    if isinstance(body, str): body = json.loads(re.search(r'\{.*\}', body, re.S).group(0))
    return dict(body, resolved_models=list(env.get('modelUsage', {}))), env.get('total_cost_usd') or 0

CONFIRM = {"type": "object", "required": ["items"], "properties": {"items": {"type": "array", "items": {"type": "object",
           "required": ["n", "visible", "why"], "properties": {"n": {"type": "integer"}, "visible": {"type": "boolean"}, "why": {"type": "string"}}}}}}

def confirm_p0(res, run_id):
    """Calibration rule (thresholds.json review_gate.opus.confirm_p0): every P0 is re-checked on a native-resolution crop of the cited
    frame and box (plus the neighbouring frames for pops). Opus misjudged sizes and noise on downscaled stills in calibration;
    a P0 stands only if the second look confirms it. Rejected P0s are kept in p0_rejected for the builder to see."""
    W, H, nf, fps = probe(MP4); items = []
    for n, p in enumerate(res.get('p0', [])):
        f = max(0, min(nf - 1, int(p.get('frame', 0)))); b = p.get('box') or [0, 0, 1080, 880]
        if len(b)!=4: b=[0,0,1080,880]
        sx = W/1080
        band_y = 470
        if not HISTORICAL and (Path(E)/'episode.json').is_file():
            band_y = json.loads((Path(E)/'episode.json').read_text())['layout']['band_y']
        x0,x1=sorted((int(b[0]),int(b[2]))); y0,y1=sorted((int(b[1]),int(b[3])))
        x0=max(0,min(W-2,int((x0-60)*sx))); x1=max(x0+2,min(W,int((x1+60)*sx)))
        y0=max(0,min(H-2,int((y0+band_y-60)*sx))); y1=max(y0+2,min(H,int((y1+band_y+60)*sx)))
        crops = []
        for g in ([f - 1, f, f + 1] if any(k in p['what'].lower() for k in ('pop', 'flash', 'strobe', 'single-frame', 'jump')) else [f]):
            g = max(0, min(nf - 1, g)); o = f'{MAT}/r{run_id}_p0_{n}_f{g:04d}.png'
            crops.append(grab(g / fps, o, f'crop={x1-x0}:{y1-y0}:{x0}:{y0}'))
        items.append((n, p, crops))
    if not items: return res, 0
    txt = '\n'.join(f'{n}. frame {p["frame"]}: "{p["what"]}"\n   crops (native resolution, 1:1): {", ".join(c)}' for n, p, c in items)
    prompt = f"""You are checking another reviewer's P0 findings on a 3D medical short ({MODE}). For each numbered finding, open its crop(s)
with the Read tool. They are at native resolution (1:1 pixels of the {W}x{H} file), so measure sizes here, not on downscaled sheets.
Picture defects (geometry, noise, text size, pops, occlusion): visible=true only if the defect as described is clearly present in the crop;
false only if this crop disproves the finding. Keep any multi-frame, view-dependent or compound finding unless all of it is disproved. A single crop cannot disprove a motion finding. A label caught mid scale-in/out fade is not 'unreadable' unless it stays small for >= 8 frames.
Facts, wording, rights and narration findings: the crop only shows the wording; judge the claim against {MAT}/sources.md and the
measurements file {MAT}/measurements.json (transcript) and answer true if the finding holds there.
{txt}
Answer with JSON only: {{"items":[{{"n":0,"visible":true,"why":"..."}}]}}"""
    try: ans, cost = claude(prompt, CONFIRM, MAT)
    except Exception as ex: res['confirm_error'] = repr(ex); return res, 0
    v = {a['n']: a for a in ans.get('items', [])}
    keep, rej = [], []
    for n, p, _ in items:
        (keep if v.get(n, {}).get('visible', True) else rej).append(dict(p, confirm=v.get(n, {}).get('why', 'no answer: kept')))
    res['p0'], res['p0_rejected'] = keep, rej
    return res, cost

def main():
    if '--single-audit' in args and (FAMILY != 'fable' or STILLS or '--draft' in args or opt('--runs') != '1'):
        raise ValueError('single audit is reserved for one Fable reading of a final movie')
    if STILLS:
        still_dir = Path(STILLS)
        files = [(str(p.resolve()), f"composited keyframe {p.stem}") for p in sorted(still_dir.glob('f_*.jpg'))]
        if not files: raise ValueError('no composited keyframes')
        fingerprint = lambda original=tuple(files): hashlib.sha256(''.join(md5(p) for p, _ in original).encode()).hexdigest()
        h0 = fingerprint()
        # Batch timestamped full-frame thumbnails. Every original 540x960
        # still stays in this packet for native inspection at a suspect frame.
        detail = Path(MAT)/'detail'
        detail.mkdir(exist_ok=True)
        native = list(files)
        for source,_ in native:
            shutil.copyfile(source,detail/Path(source).name)
        files = []
        for i in range(0,len(native),6):
            batch=native[i:i+6]
            page=Image.new('RGB',(960,592*math.ceil(len(batch)/3)),(18,18,18))
            draw=ImageDraw.Draw(page)
            for n,(source,_) in enumerate(batch):
                with Image.open(source) as im:
                    im.thumbnail((320,568))
                    x,y=n%3*320,n//3*592
                    page.paste(im,(x,y+22))
                draw.text((x+4,y+2),Path(source).stem,fill='white')
            path=Path(MAT)/f'keyframes_{i:03d}.jpg'
            page.save(path,quality=90)
            files.append((str(path),'labelled full-frame keyframes; native stills are at detail/f_FRAME.jpg'))
        ep = None if HISTORICAL else f'{E}/episode.json'
        mode = 'draft-resolution still preflight; assess picture, text and shot order. Audio and intervening frames are tested on the movie.'
    else:
        fingerprint = lambda: md5(MP4)
        h0 = fingerprint()
        files, meas, ep = build_material()
        mode = f"{MODE}. {meas['frames']} frames at {meas['fps']} fps. Read measurements.json for luma, loudness and speech recognition."
    if HISTORICAL and STILLS:
        mode = 'Partial archived native anatomy-band stills only. Score the visible anatomy and event. The original title, layout, later sequence and soundtrack are unavailable.'
    # Only hand the grader the evidence for this cut. Archived source notes,
    # episode files and filenames can disclose later fixes and review labels.
    reference = Path(os.environ.get('ANAT_SHARED_KIT',(__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../anat_kit'))) / 'refs/sheet.png'
    with Image.open(reference) as im:
        im.thumbnail((1500,1500)); im.convert('RGB').save(f'{MAT}/reference.jpg')
    inputs = ['reference.jpg (EBS reference level 7)']
    for path, desc in files:
        dst = Path(MAT) / Path(path).name
        if dst.resolve() != Path(path).resolve(): shutil.copyfile(path, dst)
        inputs.append(f'{dst.name} — {desc}')
    if STILLS and FAMILY == "opus" and not HISTORICAL:
        from anchors.build import examples, write_sheet
        for row in examples():
            write_sheet(row,Path(MAT)/row["sheet"])
            inputs.append(row["sheet"] + " — picture benchmark " + json.dumps(row["axes"],ensure_ascii=False) + row.get("scope",""))
    if not HISTORICAL and '--operative' in args and not STILLS and (Path(E)/'gates'/(TAG+'_assembly.json')).is_file():
        sys.path.insert(0,str(Path(KIT)/'templates/operative'))
        from evidence_packet import contact_receipt, edition_sources
        contact_receipt(Path(E),TAG)
        edition_sources(Path(E),TAG)
    if not HISTORICAL:
        for path, name in [(Path(E)/'SOURCES.md','sources.md'),(Path(E)/'description.txt','description.txt'),(Path(E)/'assets.json','assets.json'),(Path(E)/'bp3d_provenance.json','anatomy_objects.json'),(Path(KIT)/'ASSETS_RIGHTS.md','rights.md'),(Path(KIT)/'astra_human/SOURCES.md','character_rights.md')]:
            if path.is_file():
                shutil.copyfile(path,Path(MAT)/name); inputs.append(name)
    if ep:
        shutil.copyfile(ep,Path(MAT)/'shots.json'); inputs.append('shots.json')
    classes = checklist(historical=HISTORICAL)
    if STILLS and not HISTORICAL:
        import yaml
        for row in yaml.safe_load((Path(KIT)/"defects.yaml").read_text()):
            if row["id"] not in classes or not row.get("recurrence") or not row.get("evidence"):
                continue
            sample = Path(KIT)/"gates/fixtures"/row["evidence"]["file"]
            if hashlib.sha256(sample.read_bytes()).hexdigest() != row["evidence"]["sha256"]:
                raise ValueError("recurring defect fixture changed: " + str(sample))
            name = "failure_" + row["id"] + ".png"
            if sample.suffix in (".jpg", ".jpeg", ".png"):
                with Image.open(sample) as im:
                    im.save(Path(MAT)/name)
            else:
                preview = (["-lavfi", "showspectrumpic=s=640x320"] if sample.suffix == ".flac"
                           else ["-vf", "thumbnail,scale=-2:480"])
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", sample, *preview,
                                "-frames:v", "1", Path(MAT)/name],check=True)
            inputs.append(name + " — historical failure. Inspect today's stills for " + row["id"])
            classes[row["id"]] += " Compare the cited failing example against the candidate before assigning a disposition."
    if not HISTORICAL:
        # Signed-off phone playback belongs to final confirmation. A still has
        # no sound, and an automated grader cannot perform a human listen.
        for kind in ('provenance','facts','description','audio','narration','shots','geometry'):
            report=Path(E)/'gates'/f'{TAG}_{kind}.json'
            if report.is_file():
                name=f'{kind}_checks.json'
                shutil.copyfile(report,Path(MAT)/name)
                inputs.append(name)

    # Encode checklist keys compactly; the result is expanded before being saved.
    codes = {str(i): k for i,k in enumerate(classes,1)}
    prompt = (Path(KIT)/'rubric.md').read_text() + '\n' + mode + '\nRead only these files in this directory:\n' + '\n'.join(inputs)
    if '--operative' in args:
        prompt += ('\nThis is the operative edition. Its owner requires a procedure cold-open, '
                   'silent Korean captions, recorded SFX and a continuous music bed through the loop. '
                   'Apply these in place of the older requirements for a person opening and narration. '
                   'Check the clinically scoped captions and the visible instrument contact. '
                   'Report source, playback and provenance limits separately from the picture score.')
        for name in ('LICENCE_AUDIT.md', 'SOURCES_AUDIO.md'):
            src = Path(E) / name
            if src.is_file():
                shutil.copyfile(src, Path(MAT) / name)
                prompt += '\nRead ' + name
    prompt += '\nThe frame labels are source frame indices. Boxes are 1080-wide band pixels. Checklist (return the numeric IDs as strings):\n'
    prompt += '\n'.join(f"{code} {classes[key]}" for code,key in codes.items())
    if FINAL_ANCHOR:
        prompt += "\nFor future calibration, score the six additional picture_axes independently on the Fable scale with frame evidence."
    open(f'{MAT}/prompt.md', 'w').write(prompt)
    if DRY: print(prompt[:3000]); sys.exit(0)
    def grade_run(run_id):
        cost = 0.0
        try:
            r1, c1 = claude(prompt, SCHEMA, MAT); cost += c1
            if not STILLS and '--single-audit' not in args and cfg.get('confirm_p0'): r1, c2 = confirm_p0(r1, run_id); cost += c2
            r1['inspection'] = {state: [codes[v] for v in r1['inspection'][state]] for state in DISPOSITIONS}
            r1['class_failures'] = review_failures(classes, r1['inspection'])
            r1['area_floor'] = rubric_final(r1['scores'])
            if not 1 <= r1['final'] <= 10: raise ValueError('overall outside rubric')
            return r1, cost
        except Exception as ex:
            return {'error': 'grader call failed', 'exception': repr(ex)}, cost
    t0 = time.time()
    count = int(opt('--runs', 1 if STILLS else cfg.get('runs', 1)))
    with ThreadPoolExecutor(max_workers=min(2, count)) as pool:
        graded = list(pool.map(grade_run, range(count)))
    runs = [result for result, _ in graded]
    cost = sum(cost for _, cost in graded)
    h1 = fingerprint(); ok = [r for r in runs if 'scores' in r and 'error' not in r]
    res = {'runs': runs, '_model': MODEL, '_mp4': MP4, '_md5': h0, '_seconds': round(time.time() - t0), '_cost_usd': round(cost, 3)}
    if len(ok) < len(runs): res['error'] = 'a grader run failed'
    if h1 != h0: res['error'] = f'mp4 changed during review ({h0} -> {h1}); review is void'
    if ok and 'error' not in res:
        res['scores'] = {a: round(sum(r['scores'][a] for r in ok) / len(ok), 2) for a in AREAS}
        if FINAL_ANCHOR:
            res["picture_axes"] = ok[0]["picture_axes"]
        res['run_finals'] = [r['final'] for r in ok]
        res['raw_overall'] = sum(res['run_finals']) / len(ok)
        res['final'] = predict(res['raw_overall'], cfg.get('fable_scale',{}) if not STILLS else {},res['scores'])
        res['p0'] = [p for r in ok for p in r.get('p0', [])]; res['p1'] = [p for r in ok for p in r.get('p1', [])]
        res['p0_rejected'] = [p for r in ok for p in r.get('p0_rejected', [])]; res['threshold'] = cfg['pass_final']
        res['class_failures'] = {k:v for r in ok for k,v in r['class_failures'].items()}
        res['findings'] = [dict(priority=priority, **p) for priority in ('p0','p1') for p in res[priority]]
        res['not_checked'] = sorted({n for r in ok for n in r['not_checked']})
        res['area_composite'] = math.floor(sum(r['area_floor'] for r in ok)/len(ok)*2)/2
        # Temporal, audio and human playback evidence is unavailable on sparse stills.
        # Any observed recurrence still blocks, and the movie review checks the full list.
        blocking = {key:state for key,state in res['class_failures'].items()
                    if not STILLS or state=='defects' or key not in MOVIE_ONLY}
        if STILLS:
            # A sparse silent packet has no full-episode score. The estimated
            # still score is feedback; the finished movie owns the numeric bar.
            res['stage']='stills'
            res['pass']=not res['p0'] and not blocking
        else:
            res['stage']='movie'
            res['pass']=(res['final']>=cfg['pass_final'] and res['raw_overall']>=cfg['pass_final'] and not res['p0'] and not blocking
                         and res['area_composite']>=cfg.get('min_area_composite',1))

    else:
        res['pass'] = False
    if ok and 'error' not in res and not STILLS and '--single-audit' not in args:
        from close_review import attach, cached_audit
        try:
            if FAMILY == 'opus' and not HISTORICAL:
                from anchored_review import score, band_box
                picture = score(Path(MP4),Path(OUT)/('axes_'+h0),MODEL)
                res['anchored_picture'] = picture
                res['legacy_calibrated'] = res['final']
                res['final'] = picture['final']
                layout = json.loads((Path(E)/'episode.json').read_text())['layout']
                res['p0'].extend(dict(p,box=band_box(p['box'],layout['band_y'],layout['band_h']),source='anchored picture') for p in picture['p0'])
                res['_cost_usd'] += picture.get('cost_usd') or 0
                res['pass'] = res['pass'] and res['final'] >= cfg['pass_final'] and not res['p0']
            close=cached_audit(Path(MP4),Path(OUT)/('close_'+h0),MODEL)
            attach(res,close)
            from severity import rank_review
            band_y=470 if HISTORICAL else json.loads((Path(E)/'episode.json').read_text())['layout']['band_y']
            rank_review(Path(MP4),Path(OUT)/('severity_'+h0),res,band_y)
            from transients import apply as check_transients
            check_transients(Path(MP4),res,band_y)
            if fingerprint()!=h0: raise ValueError('movie changed during review')
        except Exception as exc:
            res.update(error=f'visual review failed: {exc}', **{'pass':False})
    res['_seconds']=round(time.time()-t0)
    out = f'{OUT}/{TAG}_review_{FAMILY}.json'
    json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
    if not HISTORICAL and Path(OUT).resolve() == (Path(E)/'gates').resolve():
        sys.path.insert(0, KIT)
        from improvement_log import capture_run
        capture_run(Path(E), TAG)
    print(json.dumps({k: res.get(k) for k in ['final', 'run_finals', 'threshold', 'pass', 'scores', 'error', '_cost_usd', '_seconds']}, ensure_ascii=False))
    print('p0:', len(res.get('p0', [])), 'p1:', len(res.get('p1', [])), '->', out)
    sys.exit(2 if 'error' in res else (0 if res['pass'] else 1))

if __name__ == '__main__':
    main()
