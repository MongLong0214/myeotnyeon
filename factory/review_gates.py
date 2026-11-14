"""Offline REVIEW_CHECKLIST gates shared by Shorts and long-form.

Unknown measurements require review. Production MATCH/qa.json are never approvals.
Times are seconds, except legacy shot start/end/from/to (encoded frame numbers).
"""
from dataclasses import dataclass, field
from pathlib import Path
import difflib, hashlib, json, math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
try:
    from . import visual_gates as visual
    from . import composition_gates as composition
except ImportError:
    import visual_gates as visual
    import composition_gates as composition

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
LIMIT = '실시간 재생 미검수'
SIGNED = {'A1','A3','B1','B2','B4','B5','C2','C4','D1','D2','E2','E3','E4','F1','F4','H15'}
OPERATIONS = {'F3','G1','G2'}
FONT = '/System/Library/Fonts/AppleSDGothicNeo.ttc'

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def read_json(path): return json.loads(Path(path).read_text())
def write_json(path, value): Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def run(args): return subprocess.run(list(map(str,args)),capture_output=True,check=True)
def result(ok, evidence, review=False):
    return dict(status='NEEDS_REVIEW' if review else 'PASS' if ok else 'FAIL',
                review_state='NEEDS_REVIEW' if review else 'DECIDED', evidence=evidence)
def pending(evidence): return result(True,evidence,True)
def input_missing(evidence):
    return dict(status='INPUT_MISSING',review_state='INPUT_MISSING',evidence=evidence)
def plain(text): return re.sub(r'\s+','',re.sub(r'[^가-힣A-Za-z0-9]','',text))
def korean_number(number):
    number=int(number)
    if number==0:return '영'
    out=''
    for base,unit in [(10000,'만'),(1000,'천'),(100,'백'),(10,'십'),(1,'')]:
        q,number=divmod(number,base)
        if q:out+=('' if q==1 and base>1 else korean_number(q) if q>9 else '영일이삼사오육칠팔구'[q])+unit
    return out
def pronunciation(text,lexicon):
    for key,value in sorted(lexicon.items(),key=lambda x:-len(x[0])):text=text.replace(key,value)
    return re.sub(r'\d+',lambda m:korean_number(m[0])+' ',text)
def sec(row, edge, fps):
    for key, scale in [(edge+'_s',1),(edge+'Ms',.001),(edge+'_seconds',1)]:
        if key in row: return float(row[key])*scale
    # v2 stores start/end in seconds alongside explicit encoded-frame bounds.
    # Legacy start/end without a unit remain frame numbers.
    if edge+'_frame' in row:return float(row[edge+'_frame'])/fps
    if edge=='start' and 'from_' in row:return float(row['from_'])/fps
    key = edge if edge in row else ('from' if edge=='start' else 'to')
    if key in row: return float(row[key])/fps
    if edge=='end' and 'dur' in row: return sec(row,'start',fps)+row['dur']/fps
    raise ValueError('Missing '+edge+' time: '+str(row.get('id')))

def facts_rows(text):
    rows={}
    for line in text.splitlines():
        cells=[s.strip() for s in line.strip().strip('|').split('|')]
        if len(cells)>1 and re.fullmatch(r'[A-Z]\d+',cells[0]): rows[cells[0]]=cells[1]
        m=re.match(r'- ([A-Z]\d+): (.*)',line)
        if m: rows[m[1]]=m[2].split(' — ')[0]
    return rows

@dataclass
class Review:
    video: Path
    out: Path
    format: str
    shots: list
    subtitles: list
    narration: list
    script: str
    facts: str
    inputs: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)
    asr: dict = field(default_factory=dict)
    fps: float = 30
    duration: float = 0
    frames: int = 0
    width: int = 0
    height: int = 0
    media: dict = field(default_factory=dict)
    images: dict = field(default_factory=dict)
    words: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)

    def bind(self,path):
        path=Path(path).resolve()
        if path.is_file(): self.inputs[str(path)]=digest(path)
        else: self.inputs[str(path)]=None

    def normalize(self):
        self.out.mkdir(parents=True,exist_ok=True)
        self.video=self.video.resolve();self.bind(self.video)
        probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',self.video]).stdout)
        v=next(s for s in probe['streams'] if s['codec_type']=='video')
        a,b=map(float,v['avg_frame_rate'].split('/'));self.fps=a/b
        self.duration=float(v.get('duration',probe['format']['duration']))
        self.width=v['width'];self.height=v['height']
        self.frames=int(v.get('nb_frames') or round(self.duration*self.fps))
        self.shots=[dict(s,id=str(s.get('id',i)),start_s=sec(s,'start',self.fps),end_s=sec(s,'end',self.fps)) for i,s in enumerate(self.shots)]
        self.subtitles=[dict(s,start_s=sec(s,'start',self.fps),end_s=sec(s,'end',self.fps)) for s in self.subtitles]
        if self.asr:
            self.words=[dict(w,text=w.get('word',w.get('text','')).strip()) for seg in self.asr.get('segments',[]) for w in seg.get('words',[])]

    def subtitle(self,t): return ' / '.join(s.get('text','') for s in self.subtitles if s['start_s']<=t<s['end_s'])
    def narration_at(self,a,b):
        # Actual final-mix words, rather than the shot author's intended sentence.
        return ' '.join(w['text'] for w in self.words if w['end']>a and w['start']<b)
    def frame(self,t):
        n=max(0,min(self.frames-1,round(t*self.fps)))
        if n not in self.images:
            f=self.out/'frames'/f'{n:06}.jpg';f.parent.mkdir(exist_ok=True)
            # Input seeking is frame-accurate when transcoding. Seek a quarter
            # frame before the target to avoid decimal rounding to the next PTS.
            run(['ffmpeg','-v','error','-ss',f'{max(0,(n-.25)/self.fps):.9f}','-i',self.video,'-vf','scale=640:-2','-frames:v','1','-vsync','0','-y',f])
            if not f.exists(): raise ValueError(f'Cannot decode frame {n}')
            self.images[n]=f
        return self.images[n]
    def markdown(self,name,text):
        p=self.out/(name+'.md');p.write_text(text+'\n');self.artifacts[str(p.resolve())]=digest(p)
        return str(p.resolve())


def final_asr(c):
    """Only local weights; never ask HuggingFace to resolve or download a model."""
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',DO_NOT_TRACK='1')
    audio=c.out/'final16k.wav'
    run(['ffmpeg','-v','error','-i',c.video,'-map','0:a:0','-ar','16000','-ac','1','-y',audio])
    c.media['audio_sha256']=digest(audio)
    try:
        import mlx_whisper
        cache=Path.home()/'.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots'
        weights=next(cache.glob('*/weights.safetensors'))
        c.bind(weights);c.bind(weights.parent/'config.json')
        c.asr=mlx_whisper.transcribe(str(audio),path_or_hf_repo=str(weights.parent),language='ko',
                                   condition_on_previous_text=False,temperature=0,word_timestamps=True)
        write_json(c.out/'final_asr.json',dict(video_sha256=c.inputs[str(c.video)],audio_sha256=c.media['audio_sha256'],asr=c.asr))
        c.words=[dict(w,text=w.get('word','').strip()) for s in c.asr['segments'] for w in s.get('words',[])]
    except (ImportError,StopIteration,RuntimeError,ValueError) as e:
        c.errors.append('Local final-mix ASR unavailable: '+str(e));c.asr={};c.words=[]
    # Real encoded mix measurements, including silence and loudness, independent of ASR.
    p=run(['ffmpeg','-hide_banner','-nostats','-i',c.video,'-af','silencedetect=n=-40dB:d=0.02,ebur128=peak=true','-vn','-f','null','-'])
    log=p.stderr.decode();(c.out/'audio_measurements.log').write_text(log)
    starts=list(map(float,re.findall(r'silence_start: ([\d.]+)',log)))
    ends=list(map(float,re.findall(r'silence_end: ([\d.]+)',log)))
    c.media['silences']=[dict(start=a,end=b,duration=b-a) for a,b in zip(starts,ends)]
    c.media['loudness_log']=str(c.out/'audio_measurements.log')
    c.media['loudness']={name:float(values[-1]) if values else None for name,values in {
        'integrated_lufs':re.findall(r'\bI:\s*(-?[\d.]+) LUFS',log),
        'range_lu':re.findall(r'\bLRA:\s*([\d.]+) LU',log),
        'true_peak_dbfs':re.findall(r'Peak:\s*(-?[\d.]+) dBFS',log)}.items()}


def ssim(a,b):
    a=a.astype(float);b=b.astype(float)
    va=a.var();vb=b.var();cov=((a-a.mean())*(b-b.mean())).mean()
    return float((2*a.mean()*b.mean()+6.5025)*(2*cov+58.5225)/((a.mean()**2+b.mean()**2+6.5025)*(va+vb+58.5225)))


def scan_frames(c, exhaustive=True, write_frames=True):
    """Stream every encoded frame. Motion ignores the configured subtitle band."""
    import cv2
    w=640;h=round(c.height*w/c.width/2)*2
    band=c.config.get('subtitle_band',[.78,1.0]);c.media['subtitle_band']=band
    mask=np.ones((h,w),bool);mask[round(h*band[0]):round(h*band[1])]=False
    cut_frames={round(s['start_s']*c.fps) for s in c.shots[1:]}
    changes=[];static=[];detected=[];similarities={};moving=set();previous=None;still_start=None
    page=None;page_no=0;page_frames=0;pages=[]
    outframes=c.out/'frames';outframes.mkdir(exist_ok=True)
    # Preserve an exhaustive visual record without holding the movie in RAM.
    def finish_page():
        nonlocal page_no
        if page is not None:
            p=c.out/f'F1_frames_{page_no:04}.jpg';page.save(p,quality=90);pages.append(str(p));page_no+=1
    proc=subprocess.Popen(['ffmpeg','-v','error','-i',str(c.video),'-vf',f'scale={w}:{h}','-vsync','0','-pix_fmt','rgb24','-f','rawvideo','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    n=0
    try:
        while True:
            raw=proc.stdout.read(w*h*3)
            if not raw: break
            if len(raw)!=w*h*3: raise ValueError('Truncated decoded frame')
            rgb=np.frombuffer(raw,np.uint8).reshape(h,w,3);gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
            if previous is not None:
                diff=np.abs(gray.astype(np.int16)-previous.astype(np.int16));mae=float(diff[mask].mean())
                changes.append(mae)
                if mae<=.35:
                    if still_start is None: still_start=(n-1)/c.fps
                else:
                    if still_start is not None and (n-1)/c.fps-still_start>1.5: static.append([still_start,(n-1)/c.fps])
                    still_start=None
                    for i,s in enumerate(c.shots):
                        if s['start_s']<n/c.fps<s['end_s']:moving.add(i);break
                if mae>30:
                    detected.append(n/c.fps)
                if n in cut_frames:
                    similarities[str(n)]=ssim(previous[mask],gray[mask])
            # OCR gets EVERY encoded frame. A per-second or cut-only sample
            # misses one-frame date/paragraph overlays and must not pass E1/C3.
            f=outframes/f'{n:06}.jpg'
            if write_frames:Image.fromarray(rgb).save(f,quality=95);c.images[n]=f
            if exhaustive:
                tw=320;th=round(h*tw/w)
                if page_frames==0:
                    page=Image.new('RGB',(tw*5,(th+24)*12),(18,20,25))
                x=page_frames%5*tw;y=page_frames//5*(th+24)
                page.paste(Image.fromarray(rgb).resize((tw,th)),(x,y+24));ImageDraw.Draw(page).text((x+4,y+3),f'f{n}  {n/c.fps:.3f}s',fill='white')
                page_frames+=1
                if page_frames==60:finish_page();page_frames=0
            previous=gray;n+=1
        if page_frames:finish_page()
        stderr=proc.stderr.read();code=proc.wait()
        if code: raise RuntimeError(stderr.decode())
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
        proc.stdout.close();proc.stderr.close()
    if still_start is not None and n/c.fps-still_start>1.5:static.append([still_start,n/c.fps])
    coverage=bool(c.shots) and abs(c.shots[0]['start_s'])<=1/c.fps and abs(c.shots[-1]['end_s']-n/c.fps)<=1/c.fps and all(abs(a['end_s']-b['start_s'])<=1/c.fps for a,b in zip(c.shots,c.shots[1:]))
    c.media.update(decoded_frames=n,static_spans=static,moving_shots=sorted(moving),cut_ssim=similarities,
                   motion_frame_share=sum(v>.35 for v in changes)/max(1,len(changes)),
                   detected_cuts=detected,shot_coverage=coverage,frame_pages=pages or c.media.get('frame_pages',[]),
                   ocr_frame_numbers=sorted(c.images),
                   motion_method='Every encoded frame at 640px; outside subtitle band, luma MAE >0.35; scene candidate MAE >30; global SSIM >=0.95')
    c.markdown('F1', '# 전 프레임 검수\n\n'+f'Decoded {n} / expected {c.frames} frames. Full episode is the changed range.\n\n'+'\n'.join(f'![frames]({Path(p).name})' for p in pages))


def ocr_frames(c,coverage=None):
    """macOS Vision Korean OCR, falling back to installed Tesseract languages."""
    frames=[dict(frame=n,path=str(p.resolve())) for n,p in sorted(c.images.items())]
    payload='\n'.join(json.dumps(x) for x in frames)+'\n'
    engine='';rows=[]
    try:
        binary=HERE/'.ocr_vision'
        source=HERE/'ocr_vision.swift'
        if sys.platform=='darwin' and source.exists():
            if not binary.exists() or binary.stat().st_mtime<source.stat().st_mtime:
                run(['swiftc','-O',source,'-o',binary])
            raw=c.out/'ocr_frames.jsonl'
            with raw.open('w') as stream:
                subprocess.run([str(binary)],input=payload,text=True,stdout=stream,stderr=subprocess.PIPE,check=True)
            rows=sorted([json.loads(x) for x in raw.read_text().splitlines()],key=lambda x:x['frame']);engine='macOS Vision ko-KR/en-US'
            raw.write_text(''.join(json.dumps(x,sort_keys=True,ensure_ascii=False)+'\n' for x in rows))
            if any(x.get('error') for x in rows):raise RuntimeError('Vision OCR frame errors')
        else:raise RuntimeError('Vision unavailable')
    except (OSError,RuntimeError,subprocess.CalledProcessError) as e:
        try:
            langs=run(['tesseract','--list-langs']).stdout.decode();ko='kor' in langs.split()
            engine='tesseract '+('kor+eng' if ko else 'eng (Korean unavailable)')
            for row in frames:
                p=run(['tesseract',row['path'],'stdout','-l','kor+eng' if ko else 'eng','--psm','11','tsv'])
                boxes=[]
                im=Image.open(row['path']);w,h=im.size
                for line in p.stdout.decode().splitlines()[1:]:
                    z=line.split('\t')
                    if len(z)==12 and z[11].strip() and float(z[10])>=30:
                        x,y,bw,bh=map(int,z[6:10]);boxes.append(dict(text=z[11],x=x/w,y=y/h,w=bw/w,h=bh/h))
                rows.append(dict(frame=row['frame'],boxes=boxes))
            if not ko:c.errors.append('Korean OCR unavailable: '+str(e))
        except (OSError,subprocess.CalledProcessError) as e:
            c.errors.append('OCR unavailable: '+str(e));engine='unavailable'
    complete=len(rows)==c.media.get('decoded_frames') and {x['frame'] for x in rows}==set(range(c.media.get('decoded_frames',0)))
    c.media.update(ocr=rows,ocr_engine=engine,ocr_korean=('ko-KR' in engine or 'kor+' in engine),ocr_complete=complete,ocr_coverage=coverage or 'Every encoded frame at 640px; no temporal sampling. OCR can still miss small, stylized or low-contrast text.')
    write_json(c.out/'ocr.json',dict(engine=engine,coverage=c.media['ocr_coverage'],frames=rows))
    checks,engine=detect_figures(c,c.shots[::max(1,len(c.shots)//12)])
    c.media['figure_spot_checks']=checks;c.media['figure_detector']=engine


def detect_figures(c,shots):
    """Use an installed native model; never download detector weights."""
    if not shots:return [],'No shot metadata for figure spot checks'
    frames=[dict(frame=i,path=str(c.frame((s['start_s']+s['end_s'])/2)),only_people=True) for i,s in enumerate(shots)]
    if sys.platform=='darwin' and (HERE/'.ocr_vision').exists():
        try:
            p=subprocess.run([str(HERE/'.ocr_vision')],input='\n'.join(json.dumps(x) for x in frames)+'\n',text=True,capture_output=True,check=True)
            rows=sorted([json.loads(line) for line in p.stdout.splitlines()],key=lambda x:x['frame'])
            if len(rows)==len(frames) and all('people' in row and not row.get('error') for row in rows):
                return [dict(shot=s['id'],detections=row['people'],image=f['path']) for s,row,f in zip(shots,rows,frames)],'macOS Vision human rectangles; cartoon false negatives possible; metadata is not auto-promoted'
        except (OSError,ValueError,subprocess.CalledProcessError):pass
    try:
        import cv2
        hog=cv2.HOGDescriptor();hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector());checks=[]
        for s,f in zip(shots,frames):
            boxes,_=hog.detectMultiScale(cv2.imread(f['path']),winStride=(8,8),padding=(8,8),scale=1.1)
            checks.append(dict(shot=s['id'],detections=len(boxes),image=f['path']))
        return checks,'OpenCV HOG person model; cartoon false negatives possible; metadata is not auto-promoted'
    except (ImportError,AttributeError,RuntimeError) as e:return [],'unavailable: '+str(e)


def sheet(c,name,entries,columns=3):
    """Paginated visual evidence with readable Unicode labels and exact frame IDs."""
    font=ImageFont.truetype(FONT,17) if Path(FONT).exists() else ImageFont.load_default()
    pages=[];cw=480;ih=round(c.height*cw/c.width);ch=ih+150
    for start in range(0,len(entries),18):
        group=entries[start:start+18];im=Image.new('RGB',(cw*columns,ch*math.ceil(len(group)/columns)),(18,20,25));draw=ImageDraw.Draw(im)
        for j,(t,label) in enumerate(group):
            x=j%columns*cw;y=j//columns*ch
            f=c.frame(t);pic=Image.open(f).convert('RGB');pic.thumbnail((cw,ih));im.paste(pic,(x,y))
            text=f'{t:.3f}s / f{round(t*c.fps)}\n{label}\n자막: {c.subtitle(t)}'
            lines=[]
            for line in text.splitlines():
                while len(line)>43:lines.append(line[:43]);line=line[43:]
                lines.append(line)
            draw.multiline_text((x+6,y+ih+5),'\n'.join(lines[:8]),font=font,fill='white',spacing=2)
        p=c.out/f'{name}_{start//18:03}.jpg';im.save(p,quality=93);pages.append(p.name)
    return pages


def a1(c):
    text='\n'.join(facts_rows(c.facts).values()) or c.facts
    score={k:len(re.findall(rx,text)) for k,rx in {'사망':'사망|숨졌|살해|목숨','흉악':'총격|권총|강도|살인|학대','공분':'공분|가혹|은폐|피해','금융·기술 감점':'금융|기술|사기|해킹'}.items()}
    path=c.markdown('A1','# 소재 점수표\n\n'+json.dumps(score,ensure_ascii=False,indent=2)+'\n\nCTO: 소재 채택 근거와 기준 충족 여부를 기입. 카운트는 인기나 자극성의 판정이 아님.')
    ev=dict(sheet=path,signals=score,criteria=c.config.get('topic_criteria'))
    return pending(ev) if ev['criteria'] else input_missing(dict(ev,reason='Missing topic acceptance criteria'))

def a2(c):
    rows=c.config.get('interest_evidence',[]);types=set();verified=[]
    for r in rows:
        p=Path(r.get('file',''));ok=p.is_file() and r.get('kind') in ['search_volume','press_count','community'] and r.get('value') is not None
        if p.is_file():c.bind(p)
        verified.append(dict(r,local_evidence_present=ok))
        if ok:types.add(r['kind'])
    ev=dict(evidence=verified,distinct_types=sorted(types),minimum=2)
    return result(True,ev) if len(types)>=2 else input_missing(ev)

def references(c): return c.config.get('references',[])
def a3(c):
    rows=references(c);ok=bool(rows) and all(r.get('channel') and r.get('video') and r.get('metrics') and Path(r['video']).is_file() for r in rows)
    path=c.markdown('A3','# 포맷 실측 레퍼런스\n\n'+json.dumps(rows,ensure_ascii=False,indent=2))
    return pending(dict(sheet=path,references=rows)) if ok else input_missing(dict(sheet=path,reason='Local reference video, channel and measured metrics required'))

def b1(c):
    paths=[]
    for i,r in enumerate(references(c)):
        video=Path(r.get('video',''))
        if not video.is_file():continue
        c.bind(video);ref=c.out/f'B1_reference_{i}.jpg'
        run(['ffmpeg','-v','error','-ss',str(r.get('time_s',0)),'-i',video,'-frames:v','1','-vf','scale=640:-2','-y',ref])
        ours=c.frame(float(r.get('our_time_s',0)))
        canvas=Image.new('RGB',(1280,440),(18,20,25))
        for x,f in [(0,ref),(640,ours)]:
            im=Image.open(f);im.thumbnail((640,400));canvas.paste(im,(x,40))
        ImageDraw.Draw(canvas).text((8,8),'REFERENCE                                    OUR FINAL ENCODE',fill='white')
        p=c.out/f'B1_side_by_side_{i}.jpg';canvas.save(p,quality=95);paths.append(p.name)
    path=c.markdown('B1','# 레퍼런스 나란히 비교\n\n'+('\n'.join(f'![reference / ours]({p})' for p in paths) or 'MISSING: local reference frames')+'\n\nCTO: 열세 항목·수정 필요 사항을 기록하고 서명.')
    return pending(dict(sheet=path,pairs=len(paths))) if paths else input_missing(dict(sheet=path,reason='No local reference'))

def b2(c):
    pages=sheet(c,'B2',[(s['start_s'],s['id']) for s in c.shots])
    path=c.markdown('B2','# AI 티 체크\n\n과한 그라데이션 / 무의미한 장식 / 텍스트 과밀 / 균일한 생성 질감\n\n'+'\n'.join(f'![frames]({p})' for p in pages))
    return pending(dict(sheet=path))

def b3(c):
    if not any(Path(r.get('video','')).is_file() for r in references(c)):
        return input_missing(dict(reason='No local reference'))
    measured=[]
    for r in references(c):
        p=Path(r.get('video',''))
        if not p.is_file():continue
        c.bind(p)
        # All figures must come from decoding reference media with the same engine.
        d=c.out/('reference_'+str(len(measured)));ref=Review(p,d,c.format,[],[],[],'','',config=c.config);ref.normalize();scan_frames(ref,False)
        cuts=[0,*ref.media['detected_cuts'],ref.duration];lengths=np.diff(cuts).tolist()
        ref.shots=[dict(id=f'R{i:04}',start_s=a,end_s=b) for i,(a,b) in enumerate(zip(cuts,cuts[1:]))]
        ocr_frames(ref)
        detected,engine=detect_figures(ref,ref.shots)
        if not detected:return result(False,dict(reason='Reference character-cut measurement unavailable; cannot substitute quoted ratios',video=str(p),cut_lengths_s=lengths,motion_frame_share=ref.media['motion_frame_share']))
        measured.append(dict(video=str(p),sha256=digest(p),cut_lengths_s=lengths,
                             motion_frame_share=ref.media['motion_frame_share'],
                             character_cut_share=sum(x['detections']>0 for x in detected)/max(1,len(detected)),
                             character_cut_measurements=detected,
                             figure_detector=engine,
                             figure_spot_checks=ref.media.get('figure_spot_checks',[]),
                             text_boxes=sum(len(row['boxes']) for row in ref.media.get('ocr',[])),method='decoded reference file; no quoted/estimated numbers'))
    # The HOG ratio is measured, but has known cartoon false negatives; never
    # substitute the production lane's quoted/estimated reference percentages.
    return result(bool(measured) and all(m['cut_lengths_s'] for m in measured),dict(measurements=measured,limitation='HOG person-cut ratio can undercount cartoon characters; B1 CTO comparison is still required'))

def b4(c):
    rows=[];entries=[]
    for s in c.shots:
        intended=s.get('intended_label') or c.config.get('intended_labels',{}).get(s['id'])
        rows.append(dict(shot=s['id'],intended_label=intended,script=s.get('purpose',s.get('staging','')),metadata=s.get('action',s.get('view',s.get('p',{}).get('set')))))
        entries.append(((s['start_s']+s['end_s'])/2,f"{s['id']} 의도: {intended}"))
    pages=sheet(c,'B4',entries)
    path=c.markdown('B4','# 무엇으로 읽히는가\n\nCTO: 맥락 없이 먼저 명칭을 적고 아래 의도와 대조. 제작 MATCH 무시.\n\n'+'\n'.join(f'![reads-as]({p})' for p in pages)+'\n\n'+json.dumps(rows,ensure_ascii=False,indent=2))
    ev=dict(sheet=path,items=rows,required_reads_as={r['shot']:r['intended_label'] for r in rows})
    return pending(ev) if rows and all(r['intended_label'] for r in rows) else input_missing(dict(ev,reason='Missing intended label'))

def b5(c):
    bible=c.config.get('style_bible');p=Path(bible or '')
    renderer=json.dumps(c.config.get('renderers',[]),ensure_ascii=False)
    bad=bool(re.search(r'blender|\b3d\b',renderer,re.I))
    path=c.markdown('B5','# 스타일 바이블 준수\n\n'+(p.read_text() if p.is_file() else 'MISSING style bible')+'\n\n팔레트·선 굵기·캐릭터 세트·렌더 방식 혼용: CTO 확인.')
    if p.is_file():c.bind(p)
    return result(False,dict(sheet=path,forbidden_renderer=True)) if bad else pending(dict(sheet=path)) if p.is_file() else input_missing(dict(sheet=path,reason='Missing style bible'))


PACE_SOURCES = (HERE/'unslop/STYLE_VIDEO.md', HERE/'REVIEW_CHECKLIST.md')

def pace_policy(c):
    """Require the two owner sources to agree; shot duration is not speech rate."""
    sources=[];issues=[]
    for path in PACE_SOURCES:
        c.bind(path)
        text=path.read_text() if path.is_file() else ''
        scope='\n'.join(line for line in text.splitlines() if re.match(r'\|\s*H14\s*\|',line)) if path.name=='REVIEW_CHECKLIST.md' else text
        formats={}
        for fmt,names in [('shorts',r'숏츠|Shorts'),('longform',r'롱폼|long-form')]:
            specs=[]
            for m in re.finditer(rf'(?:{names})\s*[:：]?\s*([^\n|;]+)',scope,re.I):
                clause=re.split(r'숏츠|Shorts|롱폼|long-form',m[1],flags=re.I)[0]
                rate=re.search(r'(\d+(?:\.\d+)?)\s*(?:[–~-]\s*(\d+(?:\.\d+)?))?\s*(?:음절/s|syllables/s)\s*(이상)?',clause)
                if not rate:continue
                lo,hi,minimum=rate.groups()
                sentence=re.search(r'문장 끝 쉼\s*(\d+(?:\.\d+)?)\s*s\s*이하',clause)
                internal=re.search(r'문장 안 쉼\s*(\d+(?:\.\d+)?)\s*s\s*이하',clause)
                if (hi or minimum) and sentence and internal:
                    specs.append(dict(window=[float(lo),float(hi) if hi else None],sentence_pause_max_s=float(sentence[1]),internal_pause_max_s=float(internal[1])))
            if specs and all(s==specs[0] for s in specs):formats[fmt]=specs[0]
            else:issues.append(f'{path}: {fmt} speech window / pause limits missing or ambiguous')
        source=dict(path=str(path),scope='H14' if path.name=='REVIEW_CHECKLIST.md' else 'format speech clauses',formats=formats)
        if path.name=='REVIEW_CHECKLIST.md':
            source['H14']=scope
            source['legacy_C1']='\n'.join(line for line in text.splitlines() if re.match(r'\|\s*C1\s*\|',line))
        sources.append(source)
    for fmt in ('shorts','longform'):
        a,b=(s['formats'].get(fmt) for s in sources)
        if a is not None and b is not None and a!=b:issues.append(f'{fmt}: STYLE_VIDEO.md {a} != REVIEW_CHECKLIST.md H14 {b}')
    policy=sources[0]['formats'].get(c.format) if not issues else None
    return dict(policy=policy,sources=sources,issues=issues,
                note='H14 / STYLE base shot 2–3 s is editing rhythm, not syllables/s; legacy C1 is not a fallback')

def c1(c):
    policy_evidence=pace_policy(c);policy=policy_evidence['policy']
    words=c.words;asr_syllables=len(re.findall('[가-힣]',c.asr.get('text','')))
    delivered_span=(words[-1]['end']-words[0]['start']) if words else 0
    asr_rate=asr_syllables/delivered_span if delivered_span>0 else None
    reference=' '.join(n.get('text','') for n in c.narration)
    agreement=difflib.SequenceMatcher(None,plain(reference).lower(),plain(c.asr.get('text','')).lower(),autojunk=False).ratio() if reference else 0
    agreement=c.media.get('final_asr_reference_agreement',agreement)
    cues=c.config.get('tts_cues',c.narration)
    tts_count=sum(len(re.findall('[가-힣]',n.get('tts_text',n.get('tts','')))) for n in cues) if cues and all(n.get('tts_text',n.get('tts')) for n in cues) else None
    same_script=plain(' '.join(n.get('text','') for n in cues))==plain(reference)
    intervals=[(float(n.get('start_s',0)),float(n.get('end_s',c.duration))) for n in cues]
    timings_ok=bool(words and intervals) and all(0<=a<b<=c.duration+1/c.fps for a,b in intervals) and all(a[1]<=b[0]+1e-6 for a,b in zip(intervals,intervals[1:]))
    if timings_ok:
        timings_ok=abs(intervals[0][0]-words[0]['start'])<=.3 and abs(intervals[-1][1]-words[-1]['end'])<=.3
    # ASR spelling agreement is diagnostic: it must not discard the script's
    # spoken numbers just because Whisper writes the same number differently.
    use_tts=bool(tts_count and same_script and timings_ok)
    syllables=tts_count if use_tts else asr_syllables
    # Full utterance intervals in the delivered audio, including within-line
    # breaths, excluding inserted between-sentence pads and end-card padding.
    span=sum(b-a for a,b in intervals) if use_tts else delivered_span
    rate=syllables/span if span>0 else None;pauses=[]
    for left,right in zip(words,words[1:]):
        gap=max(0,float(right['start']-left['end']));sentence=bool(re.search(r'[.!?。！？]["”\']?$',left['text']))
        # Word timestamps have finite resolution. Real mix silence refines a pause
        # when present; music can mask silence, so absence never proves a clean gap.
        sil=[s for s in c.media.get('silences',[]) if s['start']>=left['end']-.12 and s['end']<=right['start']+.12]
        measured=max([gap,*[s['duration'] for s in sil]])
        if sentence or measured>0:
            limit=policy['sentence_pause_max_s' if sentence else 'internal_pause_max_s'] if policy else None
            ok=measured<=limit+1e-6 if limit is not None else None
            pauses.append(dict(after=left['text'],at=left['end'],seconds=measured,sentence_end=sentence,pass_=ok))
    window=policy['window'] if policy else None
    pace_ok=rate is not None and rate>=window[0] and (window[1] is None or rate<=window[1]) if window else None
    uncounted_tokens=bool(re.search('[0-9A-Za-z]',c.asr.get('text',''))) and not use_tts
    if uncounted_tokens:pace_ok=False
    pause_ok=bool(words) and all(p['pass_'] for p in pauses) if policy else None
    evidence=dict(syllables=syllables,seconds=span,syllables_per_second=rate,asr_written_syllables_per_second=asr_rate,tts_pronunciation_used=use_tts,uncounted_asr_numeric_or_acronym_tokens=uncounted_tokens,final_asr_reference_agreement=agreement,window=window,pace_pass=pace_ok,pause_pass=pause_ok,pauses=pauses,pace_policy=policy_evidence,delivered_speech_span_s=delivered_span,syllables_per_second_including_sentence_pauses=syllables/delivered_span if delivered_span else None,tts_intervals=intervals if use_tts else [],source='Script TTS pronunciation / delivered utterance intervals (between-sentence pads excluded); script identity and final-mix voice endpoints within 0.3s. ASR spelling agreement is diagnostic; ASR words measure pauses.',audio_sha256=c.media.get('audio_sha256'))
    return input_missing(evidence) if not policy else result(pace_ok and pause_ok,evidence)


def script_markers(c):
    found=[]
    # Native script headings (## N001 · 0.000–2.885s · COLD_OPEN etc.)
    # or standalone [COLD_OPEN @ 0.000] / [CENTRAL_QUESTION @ 2.940].
    cue_times={n.get('id'):float(n.get('start_s',0)) for n in c.narration}
    for line in c.script.splitlines():
        for kind in ['COLD_OPEN','CENTRAL_QUESTION','CLIFFHANGER']:
            if kind not in line:continue
            explicit=re.search(r'@\s*(\d+(?:\.\d+)?)',line)
            heading=re.search(r'(\d+(?:\.\d+)?)\s*[–-]\s*\d',line)
            cue=re.search(r'\bN\d+\b',line)
            t=float(explicit[1]) if explicit else float(heading[1]) if heading else cue_times.get(cue[0]) if cue else None
            if t is not None:found.append(dict(kind=kind,time=t,line=line))
    return found

def c2(c):
    markers=script_markers(c);cold=[x['time'] for x in markers if x['kind']=='COLD_OPEN'];question=[x['time'] for x in markers if x['kind']=='CENTRAL_QUESTION'];cliffs=sorted(x['time'] for x in markers if x['kind']=='CLIFFHANGER')
    intervals=[b-a for a,b in zip(cliffs,cliffs[1:])]
    cadence=(not cliffs and c.duration<30) or bool(cliffs) and cliffs[0]<=45 and all(30<=d<=45 for d in intervals) and c.duration-cliffs[-1]<=45
    marker_timing=all(0<=m['time']<c.duration and any(abs(m['time']-w['start'])<=.3 for w in c.words) for m in markers)
    pages=sheet(c,'C2_first60',[(float(t),f'{t}s') for t in range(math.ceil(min(60,c.duration)))],5)
    path=c.markdown('C2','# 첫 60초 · 1초 간격\n\n'+'\n'.join(f'![first60]({p})' for p in pages)+'\n\n'+json.dumps(markers,ensure_ascii=False,indent=2))
    ok=bool(cold and question) and min(cold)<=3 and min(question)<=10 and cadence and marker_timing and not c.media.get('static_spans') and bool(c.media.get('decoded_frames'))
    ev=dict(sheet=path,markers=markers,cold_open_pass=bool(cold) and min(cold)<=3,central_question_pass=bool(question) and min(question)<=10,cliffhanger_intervals=intervals,cadence_pass=cadence,marker_timing_pass=marker_timing,static_spans=c.media.get('static_spans'),production_assertions_ignored=True)
    return pending(ev) if ok else result(False,ev)

# Only concrete acting actions count; cameras/parallax and a 'narrator_visible'
# flag on a prop card cannot turn it into an acting shot. Explicit metadata is
# preferred; legacy native action/view vocabulary is supported conservatively.
ACTING={'shoot','block','approach','reaction','staff','judge','statement','testimony','policehit','policehurt','arrest','blame','host','hosttake','defendant','defendants','command','witness'}
INSERT={'insert','prop','graphic','card','prop-card','graphic-card'}
def metadata_label(value,*keys):
    """Read semantic fields; serializing a dict would hide missing metadata."""
    if isinstance(value,str):return value or None
    if isinstance(value,dict):
        return next((value[k] for k in keys if isinstance(value.get(k),str) and value[k]),None)
    return None

def acting(s):
    if 'character_acting' in s:return s['character_acting'] is True and bool(s.get('subject') or s.get('actors') or s.get('action'))
    staging=s.get('staging',{})
    if isinstance(staging,dict) and 'actors' in staging:return bool(staging['actors'])
    if 'actors' in s:return bool(s['actors'])
    if 'actors' in s.get('p',{}):return bool(s['p']['actors'])
    if metadata_label(s.get('type',s.get('shot_type')),'name') in INSERT:return False
    return None

def character_observations(c):
    from figure_shapes import silhouettes
    rows=[]
    for s in c.shots:
        present=acting(s);boxes=[];image=None;action=None
        source='character fields (staging.actors / actors / p.actors / character_acting) or explicit insert'
        if present is None:
            image=c.frame((s['start_s']+s['end_s'])/2)
            boxes=silhouettes(image)
            if boxes:present=True
            source='Local rounded head + torso + separated legs silhouette; no detection means unknown'
            # Action evidence is local foreground change, not a camera label.
            if boxes:
                import cv2
                a=np.asarray(Image.open(c.frame(s['start_s']+(s['end_s']-s['start_s'])*.25)).convert('L'),dtype=float)
                b=np.asarray(Image.open(c.frame(s['start_s']+(s['end_s']-s['start_s'])*.75)).convert('L'),dtype=float)
                shift=cv2.phaseCorrelate(a.astype(np.float32),b.astype(np.float32))[0]
                aligned=cv2.warpAffine(b,np.float32([[1,0,-shift[0]],[0,1,-shift[1]]]),(b.shape[1],b.shape[0]))
                diff=np.abs(a-aligned)
                scores=[float(diff[round(box['y']*a.shape[0]):round((box['y']+box['h'])*a.shape[0]),round(box['x']*a.shape[1]):round((box['x']+box['w'])*a.shape[1])].mean()) for box in boxes]
                action=True if any(v>.35 for v in scores) else None
        elif present:
            actors=s.get('staging',{}).get('actors',s.get('actors',s.get('p',{}).get('actors',[]))) if isinstance(s.get('staging',{}),dict) else []
            action=True if s.get('character_acting') or metadata_label(s.get('action'),'class','verb') in ACTING or any(a.get('gesture') or a.get('motion') for a in actors if isinstance(a,dict)) else None
        rows.append(dict(shot=s['id'],character_present=present,action_observed=action,source=source,boxes=boxes,image=str(image) if image else None))
    return rows

def c3(c):
    observations=character_observations(c)
    count=sum(r['character_present'] is True for r in observations);unknown=[r['shot'] for r in observations if r['character_present'] is None]
    share=count/len(c.shots) if c.shots and not unknown else None
    lower=count/max(1,len(c.shots));upper=(count+len(unknown))/max(1,len(c.shots))
    prop_views={'books','pack','calendar','clock','dossier','letter','medical-bag','certificate','shield','balance','range','timeline','gun','mask','bags','money','number','papers','records','dna'}
    inserts=[dict(shot=s['id'],seconds=s['end_s']-s['start_s']) for s in c.shots if metadata_label(s.get('type',s.get('shot_type')),'name') in INSERT or metadata_label(s.get('view',s.get('action')),'class','verb') in prop_views]
    long_inserts=[s for s in inserts if s['seconds']>1.5+1e-6]
    lo,hi=c.media.get('subtitle_band',[.78,1]);boxes=[]
    for row in c.media.get('ocr',[]):
        for box in row['boxes']:
            if not (lo<=box['y'] and box['y']+box['h']<=hi+.005):boxes.append(dict(frame=row['frame'],**box))
    motion=c.media.get('motion_shot_count',len(c.media.get('moving_shots',[])))/len(c.shots) if c.shots else 0
    char_ok=(lower>=.8 if lower>=.8 or upper<.8 else None) if c.format=='longform' else bool(c.shots)
    defects=char_ok is False or motion!=1 or bool(boxes or long_inserts)
    missing=not c.media.get('ocr_korean',False) or not c.media.get('ocr_complete',False) or not c.media.get('shot_coverage',False)
    review=not defects and (bool(unknown) or missing or any(r['character_present'] and r['action_observed'] is None for r in observations))
    return result(not defects,dict(character_share=share,character_share_bounds=[lower,upper],character_shots=count,unknown_character_shots=unknown,character_observations=observations,total_shots=len(c.shots),character_share_pass=char_ok,minimum=.8 if c.format=='longform' else None,acting_classifier='Existing actor fields, otherwise local silhouette and camera-compensated foreground motion; negative detector output is unknown',motion_share=motion,required_motion_share=1,non_subtitle_text=boxes,oversize_inserts=long_inserts,figure_detector=c.media.get('figure_detector'),figure_spot_checks=c.media.get('figure_spot_checks'),ocr_engine=c.media.get('ocr_engine'),shot_coverage=c.media.get('shot_coverage')),review=review)


def c4(c):
    rows=[dict(shot=s['id'],camera=s.get('camera'),energy=s.get('energy'),action=s.get('action',s.get('view'))) for s in c.shots]
    path=c.markdown('C4','# 연기 에너지·독창 캐릭터\n\n과장 표정·동작, 카메라 무브, 캐릭터 복제 여부를 B4/F1 프레임과 대조.\n\n'+json.dumps(rows,ensure_ascii=False,indent=2))
    return pending(dict(sheet=path,camera_move_share=sum(bool(r['camera']) for r in rows)/max(1,len(rows))))


def cut_sheet(c):
    if 'cut_sheet' in c.media:return c.media['cut_sheet']
    planned={round(s['start_s']*c.fps) for s in c.shots[1:]}
    detected={round(t*c.fps) for t in c.media.get('detected_cuts',[])}
    cuts=sorted(planned | detected)
    entries=[];lines=['# D1/D2 전 컷·샷 중간 정렬표','', '실제 최종 믹스 ASR 단어를 사용. 제작 쪽 MATCH는 서명이 아님.','']
    for n in cuts:
        for f,label in [(n-1,'LAST before cut'),(n,'FIRST after cut')]:
            t=max(0,f)/c.fps;shot=next((s for s in c.shots if s['start_s']<=t<s['end_s']),None)
            a=shot['start_s'] if shot else t;b=shot['end_s'] if shot else t+1/c.fps
            narration=c.narration_at(a,b);entries.append((t,f'{label} f{f}\n샷: {shot["id"] if shot else "UNLISTED"}\n실제 발화: {narration}'))
            lines.extend([f'## {label} · f{f} · {t:.6f}s',f'![frame]({c.frame(t).relative_to(c.out)})',f'자막: {c.subtitle(t)}',f'이 샷의 실제 발화: {narration}',f'화면 메타데이터: {json.dumps(shot,ensure_ascii=False)}',''])
    for s in c.shots:
        t=(s['start_s']+s['end_s'])/2;words=c.narration_at(s['start_s'],s['end_s'])
        intended=s.get('purpose',s.get('staging',s.get('action',s.get('view',''))))
        entries.append((t,f'MID {s["id"]}\n실제 발화: {words}'))
        lines.extend([f'## MID {s["id"]} · {s["start_s"]:.6f}–{s["end_s"]:.6f}s',f'![frame]({c.frame(t).relative_to(c.out)})',f'자막: {c.subtitle(t)}',f'이 샷의 실제 발화: {words}',f'화면 의도: {intended}','CTO MATCH: 미서명',''])
    pages=sheet(c,'D1_D2_cut',entries)
    path=c.markdown('D1_D2_cut_sheet','\n'.join(lines)+'\n\n'+'\n'.join(f'![cut sheet]({p})' for p in pages))
    c.media['cut_sheet']=dict(sheet=path,cuts=len(cuts),shots=len(c.shots),frames=len(entries),shot_cut_frames=sorted(planned),all_cut_frames=cuts,unlisted_cut_frames=sorted(detected-planned),required_matches=[s['id'] for s in c.shots])
    return c.media['cut_sheet']

def d1(c):return pending(cut_sheet(c))

def clause_boundaries(c):
    # Only observed final-mix word endings with clause punctuation / Korean
    # connective endings qualify. No interpolation inside a word or authored MATCH.
    bounds=[]
    for i,w in enumerate(c.words):
        if re.search(r'[,;:.!?。！？]$|(?:지만|는데|으며|면서|고|면|서|니|니까|는데요|죠|습니다|어요|했다|한다)$',w['text']):
            a=float(w['end']);b=max(a,float(c.words[i+1]['start'])) if i+1<len(c.words) else a
            bounds.append([a,b])
    return bounds

def d2(c):
    ev=dict(cut_sheet(c));bounds=clause_boundaries(c);rows=[]
    for f in ev['all_cut_frames']:
        t=f/c.fps;delta=min((max(a-t,0,t-b) for a,b in bounds),default=None)
        rows.append(dict(frame=f,time=t,nearest_clause_delta_s=delta,pass_=delta is not None and delta<=.12+1e-8))
    ok=bool(c.words) and bool(c.shots) and all(r['pass_'] for r in rows) and not ev.get('unlisted_cut_frames')
    ev.update(cuts=rows,clause_boundaries=bounds,tolerance_s=.12,alignment_file='Attached as evidence only; production MATCH ignored')
    return pending(ev) if ok else result(False,ev)

def d3(c):
    jumps=[];direction=[];establishing=[];unknown=[];seen=set()
    for i,s in enumerate(c.shots):
        location=metadata_label(s.get('location',s.get('set',s.get('p',{}).get('set'))),'id','name','description')
        size=s.get('shot_size',s.get('type',s.get('shot_type')))
        subject=s.get('subject');screen=s.get('screen_direction');axis=s.get('axis_side')
        if not location or not size:unknown.append(dict(shot=s['id'],missing='location/shot_size'))
        if location is not None and location not in seen:
            if size not in ['establishing','wide','extreme-wide']:establishing.append(s['id'])
            seen.add(location)
        if i:
            prev=c.shots[i-1];same_set=location is not None and location==metadata_label(prev.get('location',prev.get('set',prev.get('p',{}).get('set'))),'id','name','description')
            same_size=size==prev.get('shot_size',prev.get('type',prev.get('shot_type')))
            similarity=c.media.get('cut_ssim',{}).get(str(round(s['start_s']*c.fps)))
            if (subject and subject==prev.get('subject') and same_set and same_size) or (similarity is not None and similarity>=.95):
                jumps.append(dict(before=prev['id'],after=s['id'],ssim=similarity,same_subject=subject==prev.get('subject')))
            if same_set:
                if screen is None or axis is None or prev.get('screen_direction') is None or prev.get('axis_side') is None:
                    unknown.append(dict(shot=s['id'],missing='screen_direction/axis_side (camera_direction is not screen direction)'))
                elif screen!=prev['screen_direction'] or axis!=prev['axis_side']:direction.append(dict(before=prev['id'],after=s['id']))
                if not subject or not prev.get('subject'):unknown.append(dict(shot=s['id'],missing='subject'))
    return result(bool(c.shots) and not jumps and not direction and not establishing and not unknown and c.media.get('shot_coverage',False),dict(jump_cuts=jumps,screen_direction_violations=direction,missing_establishing=establishing,missing_metadata=unknown,ssim_threshold=.95,axis_change_requires_cto_visual_review=True))

# Word numerals only, allowing whitespace between numeral and unit. Avoid
# matching arbitrary Korean words (e.g. 월급, 매일) or numerical durations.
NUM='[영공일이삼사오육칠팔구십백천만]'
WORD_DATE=re.compile(rf'(?:{NUM}{{2,}}\s*년(?:\s*{NUM}+\s*월)?(?:\s*{NUM}+\s*일)?|{NUM}+\s*월(?:\s*{NUM}+\s*일)?|{NUM}{{2,}}\s*일)(?![가-힣])')
DIGIT_DATE=re.compile(r'(?<!\d)(?:(\d{4})\s*(?:년|[./-])\s*(\d{1,2})?\s*(?:월|[./-])?\s*(\d{1,2})?\s*일?|(\d{4})\s*년|(\d{1,2})\s*월(?:\s*(\d{1,2})\s*일)?)(?!\d)')
KOREAN_DATE=re.compile(rf'({NUM}{{2,}})\s*년(?:\s*({NUM}+)\s*월)?(?:\s*({NUM}+)\s*일)?|({NUM}+)\s*월(?:\s*({NUM}+)\s*일)?')
CODE_DATE=re.compile(r'(?<!\d)(?:\d{4}\s*[-./_]\s*\d{1,2}(?:\s*[-./_]\s*\d{1,2})?|(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))(?!\d)')

def korean_date_number(text):
    if text is None:return None
    total=0;digit=0
    for char in text:
        if char in '십백천만':
            total+=(digit or 1)*dict(십=10,백=100,천=1000,만=10000)[char];digit=0
        else:digit='영일이삼사오육칠팔구'.index(char) if char!='공' else 0
    return total+digit

def dates(text):
    out=[]
    for m in DIGIT_DATE.finditer(text):
        y,mo,d,y2,mo2,d2=m.groups();date=(int(y or y2) if y or y2 else None,int(mo or mo2) if mo or mo2 else None,int(d or d2) if d or d2 else None)
        if date[1] is not None and not 1<=date[1]<=12:continue
        if date[2] is not None and not 1<=date[2]<=31:continue
        out.append((m[0].strip(),date))
    for m in KOREAN_DATE.finditer(text):
        y,mo,d,mo2,d2=m.groups();date=tuple(korean_date_number(v) for v in (y,mo or mo2,d or d2))
        if date[1] is not None and not 1<=date[1]<=12:continue
        if date[2] is not None and not 1<=date[2]<=31:continue
        out.append((m[0].strip(),date))
    return out

def adopted_date_cells(text):
    """Fact tables have several layouts; source/publication columns never authorize dates."""
    columns=None;cells=[];in_fact=False
    for line in text.splitlines():
        if line.startswith('#'):
            in_fact=bool(re.fullmatch(r'###\s+(?:[\w-]+:)?[A-Z]\d+\s*',line))
            columns=None
            continue
        if in_fact:
            # The statement under ### E01 / ### enrich:F09 is adopted fact.
            # Attribution, linked sources and quotations below it are provenance.
            if re.match(r'\s*(?:귀속/범위:|사실표:|-\s|>)',line):in_fact=False
            elif line.strip():cells.append(line)
            continue
        row=[s.strip() for s in line.strip().strip('|').split('|')]
        if row[0]=='ID':
            columns=[i for i,label in enumerate(row) if label in ['채택 사실','날짜·법원','날짜']]
        elif len(row)>1 and re.fullmatch(r'[A-Z]\d+',row[0]):
            cells.extend(row[i] for i in (columns or [1]) if i<len(row))
        elif line.startswith('날짜 구분:'):
            # Explicit adopted-date clarification, not article metadata/URLs.
            cells.append(line.split(':',1)[1])
        elif re.match(r'- [A-Z]\d+: ',line):
            cells.append(line.split(': ',1)[1].split(' — ')[0])
    return cells or [text]

def e1(c):
    texts=[dict(source='subtitle',time=s['start_s'],text=s.get('text','')) for s in c.subtitles]
    for shot in c.shots:
        staging=shot.get('staging',{})
        if isinstance(staging,dict):
            displayed=[staging.get(k,'') for k in ['heading','date','location','note']]
            displayed.extend(prop.get(k,'') for prop in staging.get('props',[]) for k in ['text','subtext'])
            texts.extend(dict(source='graphic field',time=shot['start_s'],text=text) for text in displayed if isinstance(text,str) and text)
    lo,hi=c.media.get('subtitle_band',[.78,1])
    for row in c.media.get('ocr',[]):
        # Unknown box geometry is not evidence that an ISO date is off-subtitle.
        boxes=[b for b in row['boxes'] if 'y' not in b or (b['y']<hi and b['y']+b.get('h',0)>lo)]
        texts.append(dict(source='OCR',time=row['frame']/c.fps,text=' '.join(b['text'] for b in row['boxes']),subtitle_text=' '.join(b['text'] for b in boxes)))
    # Also scan joined neighboring subtitles: a year/month can be split at a cue.
    joined=' '.join(s.get('text','') for s in c.subtitles)
    texts.append(dict(source='joined subtitles',time=None,text=joined))
    # Keep fact IDs scoped to their source; different files can reuse an ID.
    fact_texts=c.config.get('fact_texts',[c.facts])
    allowed=[d for text in fact_texts for cell in adopted_date_cells(text) for _,d in dates(cell)]
    hits=[];invented=[];shown=[];code_dates=[]
    for row in texts:
        for m in WORD_DATE.finditer(row['text']):hits.append(dict(row,match=m[0]))
        code_text=row['text'] if row['source'] in ['subtitle','joined subtitles'] else row.get('subtitle_text','')
        for m in CODE_DATE.finditer(code_text):code_dates.append(dict(source=row['source'],time=row['time'],text=code_text,match=m[0]))
        for label,d in dates(row['text']):
            shown.append(dict(date=label,value=d,source=row['source'],time=row['time']))
            # Every component must exist together in one adopted factual date.
            if not any(all(v is None or v==a for v,a in zip(d,approved)) for approved in allowed):invented.append(dict(date=label,value=d,source=row['source'],time=row['time']))
    return result(bool(c.subtitles) and not hits and not invented and not code_dates and c.media.get('ocr_korean',False) and c.media.get('ocr_complete',False),dict(korean_word_dates=hits,code_like_subtitle_dates=code_dates,dates_not_in_facts=invented,displayed_dates=shown,adopted_dates=allowed,ocr_engine=c.media.get('ocr_engine'),ocr_coverage=c.media.get('ocr_coverage'),ocr_complete=c.media.get('ocr_complete',False),fact_scope='Adopted fact cells/statements only; publication dates/URLs and source quotations do not authorize a date'))

def e2(c):
    rows=facts_rows(c.facts);beats={k:v for k,v in rows.items() if re.search(r'발사|총격|숨졌|사망|살해|쓰러|들이받|폭행|가혹|학대|목숨',v)}
    entries=[];coverage=[]
    for fid,text in beats.items():
        shots=[s for s in c.shots if fid in s.get('facts',s.get('fact_ids',[]))]
        coverage.append(dict(fact=fid,text=text,timestamps=[(s['start_s']+s['end_s'])/2 for s in shots]))
        for s in shots:entries.append(((s['start_s']+s['end_s'])/2,f'{fid} {s["id"]}: {text}'))
    pages=sheet(c,'E2_violence',entries)
    path=c.markdown('E2','# 폭력·사망 비트\n\nCTO: 실제 묘사 확인. 고어 클로즈업·피해자 식별·사망 희화화는 FAIL.\n\n'+json.dumps(coverage,ensure_ascii=False,indent=2)+'\n\n'+'\n'.join(f'![violence]({p})' for p in pages))
    if any(not r['timestamps'] for r in coverage):return result(False,dict(sheet=path,beats=coverage,reason='Unmapped factual violence beat'))
    return pending(dict(sheet=path,beats=coverage))

def e3(c):
    # Existing Shorts facts/red_lines gates still execute independently. This
    # shared item binds every local archived source supplied for long-form too.
    sources=c.config.get('sources',[]);missing=[]
    for r in sources:
        p=Path(r.get('file',''));c.bind(p)
        if not p.is_file() or r.get('sha256')!=digest(p):missing.append(str(p))
    path=c.markdown('E3','# 사실·레드라인 검수\n\n구형·선고 / 동일 사건·심급 / 독립 출처 2곳 / 원문 근거 / 피해자 식별·고어·희화화\n\n'+c.facts+'\n\n'+json.dumps(sources,ensure_ascii=False,indent=2))
    families={r.get('publisher') for r in sources if r.get('publisher')}
    changed=[str(Path(r.get('file',''))) for r in sources if Path(r.get('file','')).is_file() and r.get('sha256')!=digest(Path(r['file']))]
    if changed:return result(False,dict(sheet=path,changed_snapshots=changed,reason='Source snapshot hash mismatch'))
    return pending(dict(sheet=path,sources=sources)) if not missing and len(families)>=2 else input_missing(dict(sheet=path,missing_or_changed=missing,reason='Two independent local source snapshots with hashes required; semantic coverage requires CTO'))

def f1(c):
    pages=c.media.get('frame_pages',[])
    ev=dict(sheet=str(c.out/'F1.md'),decoded_frames=c.media.get('decoded_frames'),expected_frames=c.frames,pages=pages,coverage='Every encoded frame of whole episode (no baseline supplied)')
    return pending(ev) if pages and c.media.get('decoded_frames')==c.frames else result(False,ev)

def f2(c):
    ev=dict(limit=LIMIT,continuous_frames=c.media.get('frame_pages',[]),asr=str(c.out/'final_asr.json'),sync='ASR word timestamps vs caption start/end',loudness=c.media.get('loudness'),loudness_log=c.media.get('loudness_log'),ocr_coverage=c.media.get('ocr_coverage'),errors=c.errors)
    sync=[]
    for s in c.subtitles:
        ws=[w for w in c.words if w['end']>s['start_s'] and w['start']<s['end_s']]
        sync.append(dict(text=s['text'],start_delta_s=abs(s['start_s']-ws[0]['start']) if ws else None,end_delta_s=abs(s['end_s']-ws[-1]['end']) if ws else None))
    ev['subtitle_sync']=sync
    return result(bool(c.words) and bool(c.media.get('frame_pages')) and bool(c.media.get('audio_sha256')) and bool(c.media.get('loudness')) and bool(c.media.get('loudness_log')),ev)

def f3(c):return dict(status='FAIL',review_state='OPERATIONAL',evidence=dict(reason='CTO 항목별 서명 → CEO 시각 검수 PASS → 원일 전달. CEO 시각 도구 불가 시 blocker. CTO 서명은 CEO 검수가 아님.'))
def f4(c):
    path=c.markdown('F4','# 전달 전 최종 레퍼런스 재확인\n\n[B1](B1.md), B3 실측 결과를 최종 인코딩과 다시 대조. CTO가 재확인 사유를 기록하고 서명.')
    return pending(dict(sheet=path,requires=['B1','B3']))
def b6(c):
    """2026-11-07, CEO caught; CTO missed: encoded edge-fill failure."""
    before=digest(c.video)
    evidence=visual.measure_edges(c.video)
    if digest(c.video)!=before:
        evidence.update(complete=False,error='Video changed during edge-fill measurement; rerun required')
    for hit in evidence['hits']:
        hit['shot']=next((s['id'] for s in c.shots if s['start_s']<=hit['time_s']<s['end_s']),None)
    evidence['intervals']=visual.edge_intervals(evidence['hits'])
    evidence['video_sha256']=before
    evidence['status']='PASS' if evidence['complete'] and not evidence['hits'] else 'FAIL'
    path=c.out/'B6_edge_fill.json';write_json(path,evidence)
    c.artifacts[str(path.resolve())]=digest(path)
    c.bind(Path(visual.__file__))
    return result(evidence['status']=='PASS',dict(report=str(path.resolve()),**evidence))


def e4(c):
    """2026-11-07, CEO caught; CTO missed: anatomical hand, signed per shot."""
    shots=visual.canonical_actions(c);entries=[];rows=[];static=[]
    for s in shots:
        samples=visual.hand_samples(s,c.fps)
        rows.append(dict(shot=s['id'],action='military salute',expected_hand='right',samples=samples))
        static.extend(visual.left_salute_calls(s))
        for sample in samples:
            entries.append((sample['time'],f"{s['id']} salute / expected anatomical RIGHT\n{sample['phase']}"))
    source=c.config.get('salute_source');rig=c.config.get('salute_geometry')
    if shots and source and rig:
        c.bind(source);c.bind(rig)
        geometry=Path(rig).read_text()
        # Index mapping is specific to the named, front-facing house ToonRig.
        if re.search(r'const shoulders:.*?\[u\(\[-50,-302\]\),u\(\[50,-302\]\)\]',geometry):
            static.extend(dict(source=source,geometry=rig,**h) for h in visual.toon_salute_calls(Path(source).read_text()))
    pages=sheet(c,'E4_handedness',entries,columns=2) if entries else []
    for page in pages:c.artifacts[str((c.out/page).resolve())]=digest(c.out/page)
    requirements={s['id']:'right' for s in shots}
    path=c.markdown('E4','# Canonical hand — CTO sign-off\n\n2026-11-07: CEO caught; CTO missed.\n\n'
        +'\n'.join(f'![Start / peak evidence]({p})' for p in pages)
        +'\n\nFollow shoulder → elbow → hand. Salute uses anatomical RIGHT, independent of screen side. '
        'Check mirroring and simultaneous hand contact. For every shot, record handedness[shot] '
        '= {hand: "right", peak_frame: <visible peak frame in this sheet>}. '
        'A candidate is not a confirmed peak: if absent, add action_peak_frame to the spec and regenerate.\n\n'
        +'```json\n'+json.dumps(rows,ensure_ascii=False,indent=2)+'\n```')
    ev=dict(sheet=path,pages=pages,shots=rows,required_handedness=requirements,static_left_arm_calls=static,
            sample_frames={row['shot']:[v['frame'] for v in row['samples'] if v['phase']!='start'] for row in rows})
    c.bind(Path(visual.__file__))
    if static:return result(False,ev)
    if not shots and visual.SALUTE.search(c.script):
        return result(False,dict(ev,reason='Canonical-hand action in script has no mapped shots; add shot/sentence IDs or timed script ranges'))
    return pending(ev) if shots else result(True,dict(ev,not_applicable=True,reason='No canonical-hand actions in shot specs or linked script'))


def g1(c):return dict(status='FAIL',review_state='OPERATIONAL',evidence=dict(checklist=str(HERE/'upload_precheck.md'),reason='사람이 업로드 직전 Studio의 KST 당일 업로드(교체 포함)를 세고 1 이상이면 중단.'))
def g2(c):return dict(status='FAIL',review_state='OPERATIONAL',evidence=dict(checklist=str(HERE/'upload_precheck.md'),reason='사람이 교체 비공개 잔존본 0 및 ledger–Studio 일치를 업로드 전후 확인.'))

def h15(c):
    evidence=composition.composition_evidence(c)
    overview=sheet(c,'H15_overview',[(float(t),'Whole-film overview / CTO review') for t in np.arange(0,c.duration,10)])
    candidates=evidence['presenter_candidates']
    presenter_pages=sheet(c,'H15_presenters',[(t,f"Presenter candidate / {s['shot'] or '1 s window'}")
                         for s in candidates for t in s['times_s']]) if candidates else []
    repeated=[cl for cl in evidence['clusters'] if cl['fail']]
    repeat_pages=sheet(c,'H15_repetition',[(evidence['samples'][s['sample_indices'][0]]['time_s'],
                       f"Cluster {cl['cluster']} / segment {i+1}")
                       for cl in repeated for i,s in enumerate(cl['segments'])]) if repeated else []
    evidence.update(overview_pages=overview,presenter_pages=presenter_pages,repetition_pages=repeat_pages,
                    overview_interval_s=10,requires_cto_signoff=True)
    report=c.out/'H15_composition.json';write_json(report,evidence)
    path=c.markdown('H15','# Composition repetition and presenter review\n\n'
        'CTO: inspect the whole-film 10 s overview, repeated clusters and presenter candidates. '
        'Reject idle standing presenters beside props/boards. Inspect action, reaction, inserts and camera variety '
        'against LONGFORM_ANIMATION_BIBLE.md; a clean heuristic is not a semantic approval.\n\n'
        +'\n'.join(f'![H15 evidence]({p})' for p in overview+repeat_pages+presenter_pages))
    for p in [report,*[c.out/p for p in overview+repeat_pages+presenter_pages]]:c.artifacts[str(p.resolve())]=digest(p)
    c.bind(Path(composition.__file__));c.bind(HERE/'figure_shapes.py');c.bind(ROOT/'production/lf_toon/LONGFORM_ANIMATION_BIBLE.md')
    ev=dict(report=str(report.resolve()),sheet=path,**evidence)
    return result(False,ev) if evidence['repetition_fail'] else pending(ev)

def h16(c):
    evidence=composition.numeral_evidence(c)
    report=c.out/'H16_subtitle_numbers.json';write_json(report,evidence)
    c.artifacts[str(report.resolve())]=digest(report);c.bind(Path(composition.__file__))
    evidence=dict(report=str(report.resolve()),**evidence)
    if evidence['hits']:return result(False,evidence)
    return result(True,evidence) if evidence['text_available'] else input_missing(dict(evidence,reason='No subtitle text or complete Korean OCR'))

ITEMS={f.__name__.upper():f for f in [a1,a2,a3,b1,b2,b3,b4,b5,b6,c1,c2,c3,c4,d1,d2,d3,e1,e2,e3,e4,f1,f2,f3,f4,g1,g2,h15,h16]}

def apply_calibration(g,c=None):
    path=HERE/'gate_calibration.json'
    counts=read_json(path).get('false_fail_counts',{}) if path.exists() else {}
    if c is not None and path.exists():c.bind(path)
    for name,item in g.items():
        item['false_fail_count']=counts.get(name)
        item['advisory']=name not in {'B6','E4','H15','H16'} and (name=='FRAME_QA' or counts.get(name,0)>0 or bool(item.get('report_only')))
    return g


def reuse_measurements(c,directory):
    """Reuse offline ASR/OCR only for the identical encoded video, remeasure frames."""
    directory=Path(directory).resolve();report=read_json(directory/'qa.json')
    video_hash=digest(c.video)
    if report['inputs'].get(str(c.video.resolve()))!=video_hash:
        raise ValueError('Measurement cache video hash differs')
    for name in ['final_asr.json','ocr.json']:
        path=directory/name
        if report['evidence_sha256'].get(str(path))!=digest(path):
            raise ValueError('Measurement cache evidence changed: '+name)
        c.bind(path)
    saved=read_json(directory/'final_asr.json')
    if saved['video_sha256']!=video_hash:raise ValueError('ASR video hash differs')
    c.asr=saved['asr'];c.normalize()
    audio=directory/'final16k.wav'
    if digest(audio)!=saved['audio_sha256']:raise ValueError('Cached audio hash differs')
    c.bind(audio);c.media['audio_sha256']=saved['audio_sha256']
    log_path=directory/'audio_measurements.log';c.bind(log_path);log=log_path.read_text()
    starts=list(map(float,re.findall(r'silence_start: ([\d.]+)',log)))
    ends=list(map(float,re.findall(r'silence_end: ([\d.]+)',log)))
    c.media['silences']=[dict(start=a,end=b,duration=b-a) for a,b in zip(starts,ends)]
    c.media['loudness']=report['gates']['F2']['evidence']['loudness']
    c.media['loudness_log']=str(log_path)
    write_json(c.out/'final_asr.json',saved)
    scan_frames(c)
    saved_ocr=read_json(directory/'ocr.json');rows=saved_ocr['frames']
    complete=len(rows)==c.frames and {r['frame'] for r in rows}==set(range(c.frames))
    c.media.update(ocr=rows,ocr_engine=saved_ocr['engine'],ocr_korean=report['gates']['E1']['evidence'].get('ocr_engine','').startswith('macOS Vision') or 'kor+' in saved_ocr['engine'],ocr_complete=complete,ocr_coverage=saved_ocr['coverage'],measurement_cache=str(directory))
    write_json(c.out/'ocr.json',saved_ocr)


def frame_qa_advisory(c):
    """Diagnostic only: no checklist entry, signoff or readiness decision changes."""
    try:
        try:
            from .lib.frame_qa import analyze
        except ImportError:
            from lib.frame_qa import analyze
        meta = dict(c.config.get('frame_qa', {}))
        meta['shots'] = c.shots
        report = analyze(c.video, c.out/'frame_qa', meta)
        advisory = dict(status='ADVISORY', advisory=True, evidence=report)
    except Exception as exc:
        advisory = dict(status='ADVISORY', advisory=True, evidence=dict(error=str(exc)))
    c.media['frame_qa'] = advisory
    return advisory


def code_lint_gate(c):
    """Measured picture lint (lib/code_lint.py). Blocks only on measured face cut, text on face and
    subtitle overflow; static/repeats/pops/subtitle-rule findings are report-only."""
    try:
        try:
            from .lib import code_lint
        except ImportError:
            from lib import code_lint
        faces=c.config.get('face_boxes')
        if faces is None and c.config.get('face_boxes_file'):faces=read_json(c.config['face_boxes_file'])
        geometry=c.config.get('caption_box')
        if geometry is None and c.format=='longform' and c.width*9==c.height*16:geometry=code_lint.LONGFORM_CAPTION
        g=code_lint.lint(c.video,c.width,c.height,c.fps,c.duration,c.shots,c.subtitles,faces,c.config.get('text_boxes',[]),
                         geometry,line_max=18 if c.format=='longform' else 16,measure_video=c.config.get('code_lint_video',True),
                         scene_loudness=c.config.get('scene_loudness',False),variety=c.config.get('variety',False))
        c.bind(Path(code_lint.__file__));c.bind(Path(code_lint.SCENE_CHECK))
        report=c.out/'CODE_LINT.json';write_json(report,g['evidence']);g['evidence']=dict(g['evidence'],report=str(report.resolve()))
        return g
    except Exception as e:
        return dict(status='ADVISORY',report_only=True,evidence=dict(error=str(e)))


def shorts_rules_gate(c):
    """Report-only Shorts format numbers (shorts_rules.py): setting change rate, first word, pauses, loop diff;
    plus spec timing issues when review_inputs carries `shorts_spec`."""
    try:
        try:
            from . import shorts_rules
        except ImportError:
            import shorts_rules
        g=shorts_rules.measure(c.video,[dict(text=w.get('text',''),start=float(w['start']),end=float(w['end'])) for w in c.words])
        if c.config.get('shorts_spec'):g['evidence']['spec_issues']=shorts_rules.check_spec(c.config['shorts_spec'])
        c.bind(Path(shorts_rules.__file__))
        report=c.out/'SHORTS_RULES.json';write_json(report,g['evidence']);g['evidence']['report']=str(report.resolve())
        return g
    except Exception as e:
        return dict(status='ADVISORY',report_only=True,evidence=dict(error=str(e)))


def evaluate(c,measure=True):
    c.normalize()
    if measure:
        print('Review: final-mix local ASR / audio',flush=True);final_asr(c)
        print('Review: every encoded frame / exhaustive sheets',flush=True);scan_frames(c)
        print('Review: local Korean OCR / figure spot checks',flush=True);ocr_frames(c)
    gates={'FRAME_QA':frame_qa_advisory(c),'CODE_LINT':code_lint_gate(c)}
    if c.format=='shorts':gates['SHORTS_RULES']=shorts_rules_gate(c)
    c.bind(HERE/'lib/frame_qa.py')
    for name,fn in ITEMS.items():
        print('Review:',name,flush=True)
        try:gates[name]=fn(c)
        except Exception as e:
            gates[name]=result(False,dict(error=str(e),reason='Evidence generation or measurement failed; cannot sign'))
    # Bind code and every generated image/markdown/report. QA/signature itself is
    # excluded to avoid a recursive digest. No producer QA file is trusted.
    for p in [Path(__file__),HERE/'gates.py',HERE/'figure_shapes.py',HERE/'ocr_vision.swift',HERE/'REVIEW_CHECKLIST.md',HERE/'upload_precheck.md']:c.bind(p)
    for p in sorted(c.out.rglob('*')):
        if p.is_file() and p.suffix!='.log' and p.name not in ['qa.json','READY','signoffs.json']:c.artifacts[str(p.resolve())]=digest(p)
    return gates


def load_review(video,out,shots,script,facts,alignment=None,review_inputs=None,format='longform'):
    shots=Path(shots).resolve();obj=read_json(shots)
    root=shots.parent;doc=obj if isinstance(obj,dict) else {}
    companions=[]
    if not doc.get('narration') and (root/'episode_data.json').exists():
        doc=read_json(root/'episode_data.json');companions.append(root/'episode_data.json')
    config={}
    if (root/'lexicon.json').is_file():
        config['pronunciation_lexicon']=read_json(root/'lexicon.json');companions.append(root/'lexicon.json')
    if review_inputs:
        review_inputs=Path(review_inputs).resolve();config.update(read_json(review_inputs));companions.append(review_inputs)
        for r in config.get('references',[]):r['video']=str((review_inputs.parent/r['video']).resolve())
        for r in [*config.get('sources',[]),*config.get('interest_evidence',[])]:r['file']=str((review_inputs.parent/r['file']).resolve())
        if config.get('style_bible'):config['style_bible']=str((review_inputs.parent/config['style_bible']).resolve())
        config['subtitle_files']=[str((review_inputs.parent/p).resolve()) for p in config.get('subtitle_files',[])]
    config['subtitle_files']=list(dict.fromkeys([*config.get('subtitle_files',[]),
        *[str(p.resolve()) for p in [root/'subtitles.srt',root/'timeline.json',root/'captions.json'] if p.is_file()]]))
    subs=doc.get('subtitles',doc.get('captions',doc.get('subtitle_cues',[])));narration=doc.get('narration',[])
    if not subs and (root/'subtitles.srt').exists():
        srt=root/'subtitles.srt';companions.append(srt)
        def timestamp(s):
            h,m,s=map(float,s.replace(',','.').split(':'));return h*3600+m*60+s
        for block in srt.read_text().strip().split('\n\n'):
            lines=block.splitlines()
            if len(lines)>=3 and '-->' in lines[1]:
                a,b=lines[1].split('-->');subs.append(dict(start_s=timestamp(a.strip()),end_s=timestamp(b.strip()),text=' '.join(lines[2:])))
    fact_paths=[Path(f).resolve() for f in (facts if isinstance(facts,(list,tuple)) else [facts])]
    config['fact_texts']=[f.read_text() for f in fact_paths]
    config['facts_files']=[str(f) for f in fact_paths]
    if doc.get('sentences'):
        config['tts_cues']=doc['sentences']
    elif narration and all(n.get('tts_text',n.get('tts')) for n in narration):
        config['tts_cues']=[dict(n,start_s=float(n.get('start_s',n.get('start',0))),end_s=float(n.get('end_s',n.get('end',0)))) for n in narration]
    c=Review(Path(video),Path(out),'longform' if format=='longform' else 'shorts',obj if isinstance(obj,list) else obj.get('shots',[]),subs,narration,Path(script).read_text(),'\n'.join(config['fact_texts']),config=config)
    source=root/'Animatic.tsx';geometry=ROOT/'production/lf_toon/src/ToonRig.tsx'
    named_rigs={s.get('puppet_style',{}).get('geometry_source') for s in c.shots}
    if source.is_file() and str(geometry.relative_to(ROOT)) in named_rigs:
        c.config.update(salute_source=str(source),salute_geometry=str(geometry))
    for f in [shots,Path(script),*fact_paths,*companions]:c.bind(f)
    if alignment:c.bind(alignment);c.config['alignment_file']=str(Path(alignment).resolve())
    return c


def shorts_review(p,out,doc,audio,asr,loudness=None,normalizer=None,asr_accuracy=None):
    """Adapt existing factory data; never replace existing legacy gates."""
    p=Path(p);cfg=read_json(p/'recipe.json');q=cfg['qid'];tim=read_json(p/'timing.json')
    facts_path=ROOT/'episodes/quiz'/q/'facts.md'
    facts=facts_path.read_text() if facts_path.is_file() else ''
    config_path=p/'review_inputs.json';config=read_json(config_path) if config_path.exists() else {}
    config['subtitle_files']=[str((p/f).resolve()) for f in config.get('subtitle_files',[])]
    config['subtitle_files']=list(dict.fromkeys([*config.get('subtitle_files',[]),
        *[str(f.resolve()) for f in [p/'subtitles.srt',p/'timeline.json',p/'captions.json'] if f.is_file()]]))
    research=p/'research.json'
    if research.exists():
        config.setdefault('sources',read_json(research).get('sources',[]))
    else:
        matrix=ROOT/'episodes/quiz/v52_q013_q014_support'/f'{q}_fact_matrix.json'
        if matrix.exists():config.setdefault('sources',[s for claim in read_json(matrix)['claims'] for s in claim['sources']])
    for s in config.get('sources',[]):s['file']=str((ROOT/s['file']).resolve())
    if not facts:facts='\n'.join(Path(s['file']).read_text() for s in config.get('sources',[]) if Path(s['file']).is_file())
    # Markers must be explicitly supplied by the script author, not inferred from
    # runtime or copied from a producer's QA assertion.
    script_path=p/'script.md';script=script_path.read_text() if script_path.exists() else '\n'.join(x['text'] for x in audio['items'])
    by_id={i['id']:i for i in audio['items']}
    narration=[{**by_id.get(i['id'],{}),**i,'start_s':sec(i,'start',doc['fps']),'end_s':sec(i,'end',doc['fps'])} for i in tim['items']]
    c=Review(p/'video.mp4',Path(out),'shorts',doc['cues'],doc['subtitles'],narration,script,facts,config=config,asr=asr)
    for f in [p/'recipe.json',p/'render.json',p/'episode.json',p/'audio.json',p/'timing.json',facts_path,config_path,script_path]:
        if f.exists():c.bind(f)
    if research.exists():c.bind(research)
    elif matrix.exists():c.bind(matrix)
    c.normalize();c.words=[dict(w,text=w.get('word','').strip()) for s in asr.get('segments',[]) for w in s.get('words',[])]
    # ASR supplied here was just generated by gates.evaluate from delivered AAC.
    write_json(c.out/'final_asr.json',dict(video_sha256=digest(c.video),asr=asr))
    c.media['audio_sha256']=digest(p/'delivered16k.wav')
    c.media['loudness_log']=str(p/'qa.json')
    c.media['loudness']=loudness
    if normalizer is not None:
        c.media['tts_pronunciation_verified']=normalizer(audio['reference'])==normalizer(' '.join(i.get('tts_text','') for i in audio['items']))
        if asr_accuracy is not None:c.media['final_asr_reference_agreement']=asr_accuracy
    scan_frames(c);ocr_frames(c)
    return c,evaluate(c,measure=False)
