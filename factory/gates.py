"""Measurements on delivered v52 media; unknown factual semantics never pass."""
from pathlib import Path
import sys,json,re,hashlib,subprocess,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from short import W,S,load,save,sha
sys.path.insert(0,str(W/'episodes/quiz/out/v3'))
import qa as legacy
sys.path.insert(0,str(W/'episodes/quiz/v51_support'))
import align_v51
sys.path.insert(0,str(W/'episodes/quiz/v52_q013_q014_support'))
from alignment_word_clock import character_clock
align_v51.character_clock=character_clock

def gate(ok,evidence,review=False):return dict(status='PASS' if ok else 'FAIL',review_state='NEEDS_REVIEW' if review else 'DECIDED',evidence=evidence)
def cmd(args):
    p=subprocess.run(list(map(str,args)),capture_output=True,check=True)
    return p.stdout,p.stderr

def decode(v,start=0,end=None,width=270):
    filt=f'select=gte(n\\,{start})'+(f'*lt(n\\,{end})' if end is not None else '')+f',scale={width}:{width*16//9}'
    out,_=cmd(['ffmpeg','-v','error','-i',v,'-vf',filt,'-vsync','0','-pix_fmt','rgb24','-f','rawvideo','-'])
    return np.frombuffer(out,np.uint8).reshape(-1,width*16//9,width,3)

UNNUMBERED_LINE=re.compile(r'(?m)^번호 미배정(?:\.|\s*$)')
def unnumbered_ok(x,pkg=None):
    """A ledger record may lack `no` only for the deliberately unnumbered std format (q018/q020, 11-07):
    published/scheduled with a video_id, and its upload/pkg/<qid>_std/meta.txt has a line starting '번호 미배정'."""
    if not re.fullmatch(r'q\d{3}',str(x.get('qid',''))):return False,f'qid {x.get("qid")!r} is not qNNN'
    if x.get('state') not in ('published','scheduled') or not x.get('video_id'):return False,'unnumbered record needs state published/scheduled and a video_id'
    meta=(W/'upload/pkg' if pkg is None else Path(pkg))/f"{x['qid']}_std"/'meta.txt'
    if not meta.is_file() or not UNNUMBERED_LINE.search(meta.read_text()):return False,f'no {x["qid"]}_std/meta.txt line declaring 번호 미배정'
    return True,'unnumbered std package'

def number_gate(n,q,props,ledger=None,video_id=None,pkg=None):
    ledger=load(W/'upload/ledger.json') if ledger is None else ledger
    entries=ledger['entries'];malformed=[];unnumbered=[]
    for x in entries:
        if 'no' in x:
            if type(x['no']) is not int:malformed.append(dict(qid=x.get('qid'),no=x['no'],reason='no must be an integer'))
            continue
        ok,why=unnumbered_ok(x,pkg);row=dict(qid=x.get('qid'),video_id=x.get('video_id'),accepted=ok,reason=why)
        unnumbered.append(row)
        if not ok:malformed.append(row)
    for qid in sorted({u['qid'] for u in unnumbered if u['accepted']}):
        if sum(u['qid']==qid for u in unnumbered)>1:malformed.append(dict(qid=qid,reason='more than one unnumbered record for this qid'))
    if malformed:
        return gate(False,dict(requested=n,qid=q,reason='ledger has a missing/invalid number that is not one declared unnumbered std upload per qid',malformed=malformed))
    used=[x for x in ledger['entries'] if x.get('no')==n]
    conflicts=[x for x in used if not (
        x['state']=='reserved' and x['qid']==q or
        x['state'] in ('published','scheduled') and x['qid']==q and
        video_id is not None and x.get('video_id')==video_id)]
    equal=all(props.get(k)==n for k in ['badge','endCard','cover'])
    return gate(not conflicts and equal,dict(requested=n,qid=q,video_id=video_id,ledger_matches=used,conflicts=conflicts,unnumbered=unnumbered,rendered_props=props,method='Free or same-qid reservation; published/scheduled require identical known video_id. Read-only; no number consumed.'))
def title_gate(text):
    m=re.search(r'\[제목\]\s*\n([^\n]+)',text);title=m[1].strip() if m else ''
    ok=bool(title) and len(title)<=100 and not re.search(r'형량\s*퀴즈\s*#\d+\s*·',title) and bool(re.search(r'(?:#형량퀴즈\s+)?#몇년나옴$',title))
    return gate(ok,dict(title=title,chars=len(title),max_chars=100,series_suffix='[#형량퀴즈 ]#몇년나옴',forbidden_prefix='형량 퀴즈 #N ·'))

def empty_panel_gate(video,empty,doc):
    end=max(c['from']+c['dur'] for c in doc['cues'] if c['scene']=='incident')
    actual=decode(video,61,end);template=decode(empty)
    if len(actual)!=len(template):return gate(False,dict(error='Empty-template frame count mismatch',actual=len(actual),template=len(template)))
    # Same camera, paper, stamps, tags and punch animation; only set illustration,
    # props and actors removed in EMPTY composition. Ignore header/captions/badge.
    roi=(slice(126,324),slice(24,246))
    diff=np.max(np.abs(actual[:,roi[0],roi[1]].astype(np.int16)-template[:,roi[0],roi[1]].astype(np.int16)),axis=3)
    fractions=(diff>30).mean(axis=(1,2));rows=[]
    for c in doc['cues']:
        if c['scene']!='incident':continue
        a=max(61,c['from']);b=min(end,c['from']+c['dur']);values=fractions[a-61:b-61]
        rows.append(dict(scene=c['id'],set=c['p'].get('set'),interval=[a,b],frames=len(values),minimum_illustration_fraction=float(values.min()) if len(values) else 0,mean_illustration_fraction=float(values.mean()) if len(values) else 0,empty_frames=[a+i for i,v in enumerate(values) if v<.01]))
    return gate(bool(rows) and all(r['frames'] and not r['empty_frames'] for r in rows),dict(method='Every delivered story frame versus rendered empty-paper template with stamps/tags retained; RGB delta>30 on >=1% panel pixels.',roi_at_270=[24,126,246,324],template_sha256=sha(empty),scenes=rows))

def demand_gate(ep,doc,audio,q,facts_text=None):
    head=ep['answerHead'];rv=next(c for c in doc['cues'] if c['scene']=='reveal');answer=' '.join(i['text'] for i in audio['items'] if i['cue']==rv['id'])
    panel=json.dumps(rv['p'],ensure_ascii=False);facts=(W/'episodes/quiz'/q/'facts.md').read_text() if facts_text is None else facts_text
    match=re.search(r'정답:\s*(.*?)\s*[·→]',head)
    sentence=match[1] if match else head.replace('정답:','').strip()
    expected_reveal=next(c for c in ep['cues'] if c[1]=='reveal')
    ok=doc['ep']['answerHead']==head and all(rv['p'].get(k)==expected_reveal[5].get(k) for k in ['lines','steps']) and all(t in answer for t in expected_reveal[2])
    # Exact comparison of sentence/demand labeling against the source entry and facts.
    has_demand='구형' in head
    ok=ok and (not has_demand or ('구형' in answer and '구형' in panel and '구형' in facts)) and sentence in panel and sentence in facts
    return gate(ok,dict(answerHead=head,sentence=sentence,narration=answer,panel=rv['p'],facts_file=str((W/'episodes/quiz'/q/'facts.md').relative_to(W)) if facts_text is None else 'research.json archived sources (concatenated)',facts_sha256=hashlib.sha256(facts.encode()).hexdigest(),check='Exact reveal narration/panel match to episode answerHead/cues, plus sentence and 구형 in facts; source semantics separately held for facts review.'))

def source_snapshots(sources):
    hashes={};missing=[]
    for src in sources:
        name=src.get('file');sid=src.get('id') or (Path(name).stem if name else 'unknown')
        f=W/name if name else None
        if f is None or not f.is_file():missing.append(f'missing source snapshot: {sid}')
        hashes[name or sid]=sha(f) if f is not None and f.is_file() else None
    return dict(sorted(hashes.items())),sorted(set(missing))

def fact_gate(p,q):
    if load(p/'recipe.json').get('from_scratch'):
        research=load(p/'research.json')
        _,missing=source_snapshots(research['sources'])
        if missing:return gate(False,dict(sources=research['sources'],reason='; '.join(missing)))
        rows=[dict(**src,hash_verified=(W/src['file']).is_file() and sha(W/src['file'])==src['sha256'],cached_passages=(W/src['file']).read_text()) for src in research['sources']]
        return gate(False,dict(sources=rows,claims=[dict(cue=c[0],narration=c[2],visible=c[5]) for c in load(p/'episode.json')['cues']],reason='CTO must verify each claim, court/instance/date and publisher independence against archived sources.'),True)
    matrix_path=W/'episodes/quiz/v52_q013_q014_support'/f'{q}_fact_matrix.json'
    if not matrix_path.exists():return gate(False,dict(reason='No claim-to-publisher matrix'),True)
    matrix=load(matrix_path);rows=[];hard_fail=False
    sources=[src for claim in matrix['claims'] for src in claim['sources']]
    _,missing=source_snapshots(sources)
    if missing:return gate(False,dict(sources=sources,reason='; '.join(missing)))
    facts=(W/'episodes/quiz'/q/'facts.md').read_text()
    quotes={};claim_no=None
    for line in facts.splitlines():
        if not line.startswith('|'):continue
        cells=[x.strip() for x in line.split('|')[1:-1]]
        if len(cells)<5:continue
        if cells[0].isdigit():claim_no=int(cells[0])
        match=re.search(r'research/[^`]+\.txt',cells[2])
        if claim_no and match:quotes.setdefault((claim_no,match[0]),[]).append(cells[4])
    compact=lambda t:re.sub(r'[^가-힣0-9A-Za-z]','',t)
    # These identities are read from the local fact sheet, not inferred from two URLs.
    expected_instances=re.findall(r'(수원지법[^,，)\n]*|광주지법[^,，)\n]*|광주고법[^,，)\n]*)',facts[:facts.find('| #')])
    for claim in matrix['claims']:
        sources=[];publishers=set()
        for src in claim['sources']:
            f=W/src['file'];valid=f.is_file() and sha(f)==src['sha256'];text=f.read_text() if valid else ''
            if valid:publishers.add(src['publisher'])
            # Keep literal court/date/instance/demand/sentence passages for human review.
            passages=[line.strip() for line in text.splitlines() if re.search(r'(법원|지법|고법|형사\d|선고|구형|항소|2026[.년-])',line) and len(line.strip())>15]
            literal_quotes=quotes.get((claim['number'],src['file']),[])
            # Some archived quotes intentionally elide the judge's name. Match
            # every remaining fragment in order, never pretend it is a verbatim quote.
            checked=[]
            for quote in literal_quotes:
                fragments=[compact(t) for t in quote.split('[판사명 생략]') if compact(t)];hay=compact(text);pos=0;found=True
                for fragment in fragments:
                    at=hay.find(fragment,pos)
                    if at<0:found=False;break
                    pos=at+len(fragment)
                checked.append(dict(quote=quote,all_literal_fragments_in_cached_source=found))
            courts=sorted(set(re.findall(r'(?:수원|광주)(?:지법|고법)(?:\s*제?\d+형사부|\s*형사\d+(?:단독|부))?', '\n'.join(passages))))
            dates=sorted(set(re.findall(r'2026[.년-]\s*\d{1,2}[.월-]\s*\d{1,2}',text)))
            context=[line for line in passages if re.search(r'박치기|베트남|야차룰|A.?씨|A.?\(28\)|A 씨',line)]
            demand=[line for line in context if '구형' in line]
            sentence=[line for line in context if ('선고' in line or '유지' in line) and ('벌금' in line or '징역' in line)]
            instance_check=bool(courts and dates and context)
            sources.append(dict(**src,hash_verified=valid,literal_claim_quotes=checked,court_candidates=courts,date_candidates=dates,instance_identity_candidates_present=instance_check,case_context=context[:12],demand_passages=demand[:5],sentence_passages=sentence[:5],case_instance_passages=passages[:18],syndication_signals=[s for s in ['(뉴스1)','(뉴시스)','뉴스1 제공'] if s in text]))
        enough=len(publishers)>=2
        hard_fail|=not enough
        rows.append(dict(claim=claim['claim'],number=claim['number'],independent_publisher_candidates=sorted(publishers),at_least_two=enough,sources=sources,same_case_instance='NEEDS_REVIEW',claim_entailment='NEEDS_REVIEW',literal_quote_sources_verified=sum(any(z['all_literal_fragments_in_cached_source'] for z in source['literal_claim_quotes']) for source in sources)))
    ev=dict(matrix=str(matrix_path.relative_to(W)),matrix_sha256=sha(matrix_path),facts_sha256=hashlib.sha256(facts.encode()).hexdigest(),expected_instances_from_facts=expected_instances,claims=rows,coverage='Existing matrix covers narration/visible labels/meta, but semantic coverage and publisher independence require CTO verification.',reason='Source count/hash alone cannot establish same defendant, same case/instance/date, semantic entailment or newsroom independence. Check prosecution demand separately from sentence. No inherited pass_ accepted.')
    return gate(False,ev,not hard_fail)

def redline_gate(p,q,doc):
    ep=load(p/'episode.json');facts='' if load(p/'recipe.json').get('from_scratch') else (W/'episodes/quiz'/q/'facts.md').read_text();narration=' '.join(t for c in ep['cues'] for t in c[2]);visible=json.dumps(doc,ensure_ascii=False)
    # Positive matches in narration/props fail. The negative checklist in facts is evidence,
    # never scanned as if it were an assertion that these crimes happened.
    hits=re.findall(r'성폭행|강간|강제추행|미성년\s*피해|아동\s*피해|가정폭력|데이트폭력|스토킹',narration+visible)
    staging=[]
    for c in doc['cues']:
        for a in c['p'].get('actors',[]):
            if a.get('pose') in ['collapse','dead','fall','pushed']:staging.append(dict(scene=c['id'],actor=a))
    # Raster heroes and actual identity status cannot be proved by a token scan.
    return gate(False,dict(prohibited_topics=hits,prohibited_staging=staging,actors=[dict(scene=c['id'],actors=c['p'].get('actors',[])) for c in doc['cues']],hero_sha256=sha(p/'hero.png'),facts_redline_section=facts[facts.find('## 금지선'):facts.find('## 출처 URL')] if '## 금지선' in facts else '',reason='CTO must establish no living public figure, gore/collapse depiction and faceless/silhouette defendant in raster assets. Keyword absence is not proof.'),not hits and not staging)

def typecheck_gate(p):
    root=W/'production/compositor'
    config=dict(compilerOptions=dict(target='ES2020',module='ESNext',moduleResolution='Bundler',jsx='react-jsx',strict=True,esModuleInterop=True,skipLibCheck=True,noEmit=True,resolveJsonModule=True,baseUrl=str(root),paths={'react':['node_modules/@types/react'],'react/*':['node_modules/@types/react/*'],'remotion':['node_modules/remotion']},typeRoots=[str(root/'node_modules/@types')]),include=['*.tsx'])
    save(p/'tsconfig.json',config)
    proc=subprocess.run(['node',str(root/'node_modules/typescript/bin/tsc'),'-p',str(p/'tsconfig.json')],capture_output=True,text=True)
    (p/'typecheck.log').write_text(proc.stdout+proc.stderr)
    return gate(proc.returncode==0,dict(exit_code=proc.returncode,log='typecheck.log',sha256=sha(p/'typecheck.log')))

def evaluate(p):
    cfg=load(p/'recipe.json');q=cfg['qid'];doc=load(p/'render.json');ep=load(p/'episode.json');audio=load(p/'audio.json');tim=load(p/'timing.json');v=p/'video.mp4';n=doc['durationInFrames'];g={}
    g['typecheck']=typecheck_gate(p)
    fresh=cfg.get('from_scratch',False)
    if fresh:
        texts=[*ep['head'],ep['answerHead'],*[t for c in ep['cues'] for t in c[2]],json.dumps([c[5] for c in ep['cues']],ensure_ascii=False)]
        hits=[dict(text=t,issue=why) for t in texts for rx,why in legacy.SPELL if re.search(rx,t)]
        g['spelling']=gate(not hits,dict(issues=hits))
        facts_text='\n'.join((W/x['file']).read_text() for x in load(p/'research.json')['sources'] if (W/x['file']).is_file())
        # Check numeric facts in spec labels, not staging coordinates or test badge.
        shown=legacy.values(' '.join(legacy.textgate.labels(ep)+legacy.textgate.narration(ep)))
        missing=sorted(shown-legacy.values(facts_text))
        g['fact_numbers']=gate(not missing,dict(not_in_archived_sources=missing,screen_and_speech=sorted(shown)))
    else:
        facts_text=None
        spelling=legacy.spelling(q);g['spelling']=gate(spelling.pop('pass_'),spelling)
        numbers=legacy.numbers(q);g['fact_numbers']=gate(numbers.pop('pass_'),numbers)

    g['number']=number_gate(cfg['number'],q,load(p/'render_complete.json'),video_id=cfg.get('video_id'));g['title_format']=title_gate((p/'meta.txt').read_text())
    probe=legacy.probe(v);g['format']=gate(probe.pop('pass'),probe);g['duration']=gate(22<=probe['duration']<=40,dict(seconds=probe['duration'],frames=n,limit=[22,40]))
    count=int(cmd(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','csv=p=0',v])[0])
    g['frame_count']=gate(count==n,dict(decoded=count,render_props=n))
    print('QA decoded panels / loudness / freeze',flush=True)
    g['no_empty_panel']=empty_panel_gate(v,p/'empty.mp4',doc)
    loud=legacy.loud(v);g['loudness']=gate(loud.pop('pass_'),loud)
    fb=legacy.freeze_black(v);g['freeze_black']=gate(fb.pop('pass_'),fb)
    _,motion=cmd(['ffmpeg','-hide_banner','-nostats','-i',v,'-vf','freezedetect=n=0.001:d=1.5','-an','-f','null','-']);holds=re.findall(rb'freeze_start: ([\d.]+)',motion);g['motion']=gate(not holds,dict(freezes_over_1p5s=[float(x) for x in holds]))
    import soundfile as sf
    pace_rows=[]
    for item in audio['items']:
        source=W/item['file'];seconds=sf.info(source).duration;syllables=len(re.findall('[가-힣]',item['tts_text']))
        pace_rows.append(dict(id=item['id'],seconds=seconds,syllables=syllables,sps=syllables/seconds,source_sha256=sha(source),source_hash_matches=sha(source)==item['source_sha256']))
    sps=sum(r['syllables'] for r in pace_rows)/sum(r['seconds'] for r in pace_rows)
    g['pace']=gate(sps>=7.5 and pace_rows[0]['sps']>=7.5 and all(r['source_hash_matches'] and (not fresh or r['sps']>=7.5) for r in pace_rows),dict(syllables_per_second=sps,hook_syllables_per_second=pace_rows[0]['sps'],minimum=7.5,per_line=pace_rows,method='Hangul syllables / measured complete utterance WAV duration, using hashed source files; inter-line gaps excluded.'))
    # Actual delivered AAC, never trust a previous ASR report.
    out,_=cmd(['ffmpeg','-v','error','-i',v,'-ac','1','-ar','16000','-f','f32le','-']);y=np.frombuffer(out,np.float32)
    import soundfile as sf
    sf.write(p/'delivered16k.wav',y,16000,subtype='PCM_16')
    import mlx_whisper
    model=next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
    print('QA local Whisper ASR',flush=True)
    asr=mlx_whisper.transcribe(str(p/'delivered16k.wav'),path_or_hf_repo=str(model),language='ko',condition_on_previous_text=False,temperature=0,word_timestamps=True)
    save(p/'asr.json',asr)
    oldargv=sys.argv;sys.argv=[oldargv[0]]
    try:
        if fresh:
            from fresh import normalizer
            norm=normalizer(ep)
        else:norm=align_v51.normalizer(q)
    finally:sys.argv=oldargv
    acc=1-legacy.cer(norm(audio['reference']),norm(asr['text']))
    g['asr']=gate(acc>=.99,dict(accuracy=acc,reference=audio['reference'],transcript=asr['text'],backend='offline cached Whisper large-v3-turbo, delivered AAC, no prompt'))
    rows,subacc=align_v51.align(doc,audio,asr,norm)
    errors=[dict(text=s['text'],start_ms=abs(s['from_']/30-r['start_seconds'])*1000,end_ms=abs(s['to']/30-r['end_seconds'])*1000) for s,r in zip(doc['subtitles'],rows)]
    g['sync']=gate(len(errors)==len(doc['subtitles']) and subacc>=.99 and all(e['start_ms']<=200 and e['end_ms']<=200 for e in errors) and all(0<=s['from_']<s['to']<=n for s in doc['subtitles']),dict(tolerance_ms=200,per_caption=errors))
    win=80;rms=np.sqrt(np.mean(y[:len(y)//win*win].reshape(-1,win)**2,axis=1));voiced=rms>10**(-45/20);idx=np.where(voiced)[0];onset=float(idx[0]*.005) if len(idx) else 999;g['narration_onset']=gate(onset<=.15,dict(seconds=onset,limit=.15))
    gaps=[]
    for a,b in zip(tim['items'],tim['items'][1:]):
        left=max(0,round((a['end']/30-.35)/.005));right=min(len(voiced),round((b['start']/30+.35)/.005));z=voiced[left:right];edges=np.diff(np.r_[True,z,True].astype(int));mid=(a['end']+b['start'])/60
        vals=[(bb-aa)*.005 for aa,bb in zip(np.where(edges==-1)[0],np.where(edges==1)[0]) if (left+aa)*.005<=mid<=(left+bb)*.005];gaps.append(dict(after=a['id'],seconds=float(max(vals,default=0))))
    g['silences']=gate(all(x['seconds']<=.120001 for x in gaps),dict(threshold_dbfs=-45,window_ms=5,limit_seconds=.12,gaps=gaps))
    pcm=cmd(['ffmpeg','-v','error','-i',v,'-map','0:a:0','-c:a','pcm_s32le','-f','md5','-'])[0].decode().strip();cached=cmd(['ffmpeg','-v','error','-i',cfg['aac'],'-map','0:a:0','-c:a','pcm_s32le','-f','md5','-'])[0].decode().strip()
    if fresh:
        raw,sr=sf.read(p/'prepared/raw.wav',dtype='int32',always_2d=True);ident=[]
        for item in audio['items']:
            wave,wsr=sf.read(W/item['file'],dtype='int32');a=item['new_start_sample'];ln=item['samples']
            ident.append(dict(id=item['id'],identical=wsr==sr==48000 and bool(np.array_equal(raw[a:a+ln,0],wave)) and bool(np.array_equal(raw[a:a+ln,1],wave))))
        g['narration_integrity']=gate(all(x['identical'] for x in ident) and pcm==cached and audio['voice']=='M1' and audio['all_lines_resynthesized'],dict(lines=ident,voice=audio['voice'],all_lines_resynthesized=True,delivered_audio_md5=pcm,cached_aac_pcm_md5=cached,method='New M1 WAVs copied sample-identically to raw master before loudness normalization; delivered AAC equals the encoded new master. No v3 body exists to preserve.'))
    else:
        orig,sr=sf.read(W/'production/compositor/public'/q/'mix_master.wav',dtype='int32',always_2d=True);master,msr=sf.read(p/'mix_master.wav',dtype='int32',always_2d=True)
        ident=[]
        for e in audio['body_pcm_evidence']:
            a=e['source_start_sample'];b=e['delivery_start_sample'];ln=e['samples'];ident.append(dict(id=e['id'],samples=ln,identical=bool(np.array_equal(orig[a:a+ln],master[b:b+ln]))))
        g['body_pcm_unchanged']=gate(sr==msr==48000 and all(x['identical'] for x in ident) and pcm==cached,dict(lines=ident,delivered_audio_md5=pcm,cached_aac_pcm_md5=cached))
    log=(p/'render.log').read_text();hooks={};scales={}
    for tag,target in [('HOOKCHECK51',hooks),('HOOKCHECK52SCALE',scales)]:
        for raw in re.findall(tag+r' (\{.*?\}) END',log):
            z=json.loads(raw);target[z['frame']]=z
    audit={int(f):int(b) for f,b in re.findall(r'AUDIT '+q+r' f=(\d+) n=(\d+).*? END',log)}
    g['safe_area']=gate(set(audit)==set(range(n)) and not any(audit.values()),dict(frames=len(audit),expected=n,bad_frames=[f for f,b in audit.items() if b]))
    h4=hooks.get(4,{});g['hook_frame4']=gate(h4.get('hookVisible',False) and h4.get('minGlyphHeight',0)>=110,dict(frame4=h4,minimum_glyph_pixels=110))
    g['hook_branding']=gate(all(f in hooks and not hooks[f]['branding'] for f in range(60)),dict(early_frames=[hooks.get(f) for f in [0,4,59]]))
    g['push_in']=gate(all(abs(scales.get(f,{}).get('scale',0)-s)<.00001 for f,s in [(0,1),(30,1.06),(60,1.12)]),dict(frames={str(f):scales.get(f) for f in [0,30,60]}))
    first=decode(v,0,61,width=540);import cv2
    gray=cv2.cvtColor(first[0],cv2.COLOR_RGB2GRAY);edge=float((cv2.Canny(gray,50,150)>0).mean());mean=float(gray.mean());pairs=[float(np.abs(first[a].astype(float)-first[b]).astype(float).mean()) for a,b in [(0,15),(15,30),(30,45),(45,60)]]
    g['hook_frame0']=gate(mean>3 and edge>.002,dict(mean_luminance=mean,edge_density=edge));g['hook_motion']=gate(all(x>.2 for x in pairs),dict(adjacent_15frame_mae=pairs))
    # Exact legacy full-resolution flat-band threshold over every early frame.
    high=decode(v,0,61,1080);bands=[]
    for im in high:
        luma=np.dot(im,[.2126,.7152,.0722]);flat=luma.std(1)<1;best=cur=0;start=0
        for i,f in enumerate(flat):
            if f:
                if cur==0:start=i
                if abs(luma[i].mean()-luma[start].mean())>1:start=i;cur=0
                cur+=1;best=max(best,cur)
            else:cur=0
        bands.append(best)
    del high
    g['hook_no_empty_band']=gate(max(bands)<=96,dict(max_band_pixels=max(bands),limit=96,per_frame=bands))
    g['end_card']=gate(all(f in hooks and hooks[f]['cta'] and hooks[f]['ctaAreaRatio']>=.5 for f in range(n-45,n)),dict(frames=45,min_area_ratio=min((hooks.get(f,{}).get('ctaAreaRatio',0) for f in range(n-45,n)),default=0)))
    weigh=next(c for c in doc['cues'] if c['scene']=='weigh');rv=next(c for c in doc['cues'] if c['scene']=='reveal');ask=next(i for i in tim['items'] if i['cue']==weigh['id']);ans=next(i for i in tim['items'] if i['cue']==rv['id']);reveal=rv['from']+rv['a']['s1']+2
    timing=dict(choices_settled=weigh['from']+24,reveal_frame=reveal,reveal_ratio=reveal/n,answer_delta_seconds=abs(reveal-ans['start'])/30,preanswer_choice_seconds=(reveal-weigh['from']-24)/30)
    g['choice_answer_timing']=gate(weigh['from']<=ask['start'] and weigh['from']+24<ask['end'] and timing['preanswer_choice_seconds']>=3 and timing['reveal_ratio']>=.75 and timing['answer_delta_seconds']<=.2,timing)
    outro=next(c for c in doc['cues'] if c['scene']=='outro');start=outro['from']-1;tail=decode(v,start,n-44,360);reference=tail[0][175:485,35:325].astype(float);maes=[float(np.abs(x[175:485,35:325].astype(float)-reference).mean()) for x in tail[1:(n-45)-start]];cut=float(np.abs(tail[-1].astype(float)-tail[-2].astype(float)).mean())
    g['end_transition']=gate(all(x<8 for x in maes) and cut>10,dict(interval=[outro['from'],n-45],held_verdict_roi_mae=maes,card_cut_mae=cut,method='Every frame: held verdict until N-45, then full CTA; existing getEndTransition.'))
    g['demand_vs_sentence']=demand_gate(ep,doc,audio,q,facts_text);g['facts']=fact_gate(p,q);g['red_lines']=redline_gate(p,q,doc)
    source_changes=[path for path,h in cfg['source_hashes'].items() if not (W/path).is_file() or sha(W/path)!=h]
    g['source_preservation']=gate(not source_changes,dict(changed=source_changes,source_hashes=cfg['source_hashes']))
    # Review sheet samples every scene and ending, with frame numbers.
    allframes=decode(v);selected=sorted({0,4,30,60,61,n-46,n-45,n-1,*[min(n-1,c['from']+18) for c in doc['cues']]});sheet=Image.new('RGB',(270*5,520*math.ceil(len(selected)/5)),(15,18,25));draw=ImageDraw.Draw(sheet)
    for i,f in enumerate(selected):
        x=i%5*270;y=i//5*520;draw.text((x+5,y+6),f'{q} #{cfg["number"]} f{f} {f/30:.2f}s',fill='white');sheet.paste(Image.fromarray(allframes[f]),(x,y+30))
    sheet.save(p/'review_sheet.jpg',quality=95)
    # Shared checklist is additional to the legacy empty-panel/facts/media gates.
    from review_gates import shorts_review
    review,items=shorts_review(p,p/'review',doc,audio,asr,g['loudness']['evidence'],norm,acc)
    g.update(items)
    return finalize(p,g,review)

def finalize(p,g,review=None):
    """Bind reviews to delivered inputs and current local source bytes, without rendering."""
    for item in g.values():
        if item.get('review_state')=='CTO_SIGNED':
            item.update(status='NEEDS_REVIEW',review_state='NEEDS_REVIEW');item.pop('cto_signoff',None)
    cfg=load(p/'recipe.json');q=cfg['qid']
    evidence=g['facts']['evidence']
    sources=[*evidence.get('sources',[]),*[src for claim in evidence.get('claims',[]) for src in claim.get('sources',[])]]
    snapshots,missing=source_snapshots(sources)
    if missing:
        g['facts']=gate(False,dict(evidence,reason='; '.join(missing)))
    # The human can sign NEEDS_REVIEW gates, never deterministic failures. Bind signoffs
    # to all media/spec/source evidence, so an edit invalidates an old review.
    binding=dict(files={name:sha(p/name) for name in ['video.mp4','cover.jpg','meta.txt','render.json','episode.json','audio.json','timing.json','hero.png']},source_snapshots=snapshots,gates={k:v for k,v in g.items() if k in ['facts','red_lines','number']})
    if review is not None:
        from review_gates import ITEMS,apply_calibration
        apply_calibration(g,review)
        binding['review']=dict(files=review.inputs,evidence=review.artifacts,config=review.config,
                               gates={k:v for k,v in g.items() if k in ITEMS})
    digest=hashlib.sha256(json.dumps(binding,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    prior=load(p/'qa.json') if (p/'qa.json').exists() else {};signoffs=prior.get('cto_signoffs',{})
    apply_cto_signoffs(g,digest,signoffs)
    from review_gates import OPERATIONS,LIMIT
    ready=all(x['status']=='PASS' for k,x in g.items() if k not in OPERATIONS and not x.get('advisory')) and not cfg.get('dry_number',False)
    return dict(qid=q,number=cfg['number'],dry_number=cfg.get('dry_number',False),ready=ready,
                ceo_review_eligible=ready,owner_delivery_ready=False,limits=[LIMIT],
                input_sha256=digest,cto_signoffs=signoffs,gates=g,network=False,uploads=False)


def apply_cto_signoffs(g,digest,signoffs):
    """Shared extension of the original input-bound signoff protocol.

    Deterministic FAILs never become signable. D2 requires the reviewer to mark
    every shot; B4 requires a blind reads-as label for every represented object.
    """
    for name,item in g.items():
        if item.get('review_state')=='CTO_SIGNED':
            item['status']='NEEDS_REVIEW';item['review_state']='NEEDS_REVIEW';item.pop('cto_signoff',None)
        sign=signoffs.get(name,{})
        if not (item.get('review_state')=='NEEDS_REVIEW' and sign.get('role')=='CTO'
                and sign.get('name') and sign.get('reason') and sign.get('input_sha256')==digest):continue
        ev=item.get('evidence',{})
        if name=='D2' and not all(sign.get('matches',{}).get(s)=='MATCH' for s in ev.get('required_matches',[])):continue
        if name=='B4' and not all(sign.get('reads_as',{}).get(s)==label for s,label in ev.get('required_reads_as',{}).items()):continue
        if name=='E4':
            hands=sign.get('handedness',{})
            if not all(isinstance(hands.get(s),dict) and hands[s].get('hand')==hand
                       and hands[s].get('peak_frame') in ev.get('sample_frames',{}).get(s,[])
                       for s,hand in ev.get('required_handedness',{}).items()):continue
        item['status']='PASS';item['review_state']='CTO_SIGNED';item['cto_signoff']=sign
    return g


def finalize_review(c,g,prior=None):
    """Long-form uses the same CTO protocol; sources/evidence cannot drift."""
    from review_gates import SIGNED,OPERATIONS,LIMIT,apply_calibration
    apply_calibration(g,c)
    canonical={k:{key:value for key,value in v.items() if key!='cto_signoff'} for k,v in g.items()}
    for v in canonical.values():
        if v.get('review_state')=='CTO_SIGNED':v.update(status='NEEDS_REVIEW',review_state='NEEDS_REVIEW')
    # Rehash at the boundary too: an edited/missing evidence image or source can
    # never retain a previous approval, including a source changed during QA.
    from review_gates import digest as file_digest
    current_inputs={p:file_digest(p) if Path(p).is_file() else None for p in c.inputs}
    current_evidence={p:file_digest(p) if Path(p).is_file() else None for p in c.artifacts}
    changed=[p for p,h in c.inputs.items() if current_inputs[p]!=h]
    changed.extend(p for p,h in c.artifacts.items() if current_evidence[p]!=h)
    if changed:
        g['input_integrity']=gate(False,dict(changed=changed,reason='Input/evidence changed after measurement; rerun required'))
        canonical['input_integrity']=g['input_integrity']
    binding=dict(files=current_inputs,evidence=current_evidence,gates=canonical,format=c.format,
                 config=c.config,limits=[LIMIT])
    digest=hashlib.sha256(json.dumps(binding,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    signoffs=(prior or {}).get('cto_signoffs',{})
    apply_cto_signoffs(g,digest,signoffs)
    automatic={k:v for k,v in g.items() if k not in SIGNED|OPERATIONS and not v.get('advisory')}
    auto_ok=all(v['status']=='PASS' for v in automatic.values())
    signed_ok=all(g[k]['review_state']=='CTO_SIGNED' or
                  (k=='E4' and g[k]['status']=='PASS' and g[k]['evidence'].get('not_applicable'))
                  for k in SIGNED if not g[k].get('advisory'))
    return dict(format=c.format,video=str(c.video),ready=auto_ok and signed_ok,
                ceo_review_eligible=auto_ok and signed_ok,owner_delivery_ready=False,
                input_sha256=digest,cto_signoffs=signoffs,gates=g,limits=[LIMIT],
                inputs=c.inputs,evidence_sha256=c.artifacts,network=False,uploads=False,
                defects=[k for k,v in g.items() if v['status']=='FAIL' and v.get('review_state')=='DECIDED'],
                input_missing=[k for k,v in g.items() if v['status']=='INPUT_MISSING'],
                advisory_gates=[k for k,v in g.items() if v.get('advisory')],
                operational_blockers=[k for k in OPERATIONS if g[k]['status']!='PASS'])
