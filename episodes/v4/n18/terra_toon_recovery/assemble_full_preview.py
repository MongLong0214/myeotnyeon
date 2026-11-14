#!/usr/bin/env python3
"""Assemble the N18 low-res review cut from Blender-rendered tableaux and actual cue timing."""
from pathlib import Path
import json, subprocess

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'shots.json'
AUDIO=ROOT.parent/'audio/mix_master.wav'
RENDERS=ROOT/'full_renders'
FPS=30
LEAD=1.5

def esc_ass(s):
    return s.replace('\\','\\\\').replace('{','\\{').replace('}','\\}').replace('\n','\\N')

def pick(shot, n):
    facts=set(shot.get('fact_ids',[])); text=' '.join(shot.get('on_screen_text',[]))+' '+shot.get('visual','')+' '+n.get('text','')
    if facts & {'F25','F23','F01','F27'} or any(w in text for w in ('어머니','부모','편지','입영')): return 'family'
    if facts & {'F29','F30','F31'} or any(w in text for w in ('추모','분향','국화','명예수료')): return 'memorial'
    if facts & {'F38','F39','F40','F41','F42','F43'} or any(w in text for w in ('국방부','대책','혹서기','소명 절차','승인권자')): return 'policy'
    if facts & {'F16','F18','F19','F20','F21','F22','F14'} or any(w in text for w in ('병원','의료','이송','중환자','고열')): return 'hospital'
    if facts & {'E04','E05','F11','F12','F13'} or any(w in text for w in ('의식','쓰러','응급')): return 'training_grounded'
    if facts & {'C01','C03','C04','C05','C06','C07','C09','C10','D01','D03','D04','D05','D06','D08','J01','J02','J03','J04','J05','J06','J07','J08','J09','J10','J11','J12','J13'} or any(w in text for w in ('법원','검찰','판결','재판','구형','선고','항소','대법원','기소')):
        return ['court_wide','court_prosecutor','court_defendants','court_witness','court_records','court_judgeclose'][shot['frame_start'] % 6]
    if facts & {'F06','F07'} or any(w in text for w in ('책','보급품','군장')): return 'training_pack'
    if facts & {'E02'} or '여섯' in text or '6명' in text: return 'training_six'
    return 'training_kit'

D=json.loads(SOURCE.read_text())
narr={x['id']:x for x in D['narration']}
shots=[]
for s in D['shots']:
    ids=s.get('narration_ids',[])
    n=narr.get(ids[0], {'id':'', 'text':''}) if ids else {'id':'', 'text':''}
    shots.append({'shot_id':s['id'],'start_s':round(LEAD+s['t_start'],3),'end_s':round(LEAD+s['t_end'],3),'narration_id':n.get('id',''),'spoken_text':n.get('text',''),'facts':s.get('fact_ids',[]),'screen':pick(s,n)})
# Real output includes intentional 1.5s leader and existing 10s tail in mix_master.
end_audio=385.933333
entries=[('training_kit.png',LEAD)] + [(x['screen']+'.png',max(.05,x['end_s']-x['start_s'])) for x in shots] + [('memorial.png',max(.1,end_audio-shots[-1]['end_s']))]
concat=ROOT/'full_preview_concat.txt'
concat.write_text(''.join(f"file '{(RENDERS/f).as_posix()}'\nduration {d:.6f}\n" for f,d in entries)+f"file '{(RENDERS/entries[-1][0]).as_posix()}'\n")
# Actual spoken cue text, not synthetic equal intervals.
ass=['[Script Info]','ScriptType: v4.00+','PlayResX: 426','PlayResY: 240','ScaledBorderAndShadow: yes','','[V4+ Styles]','Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding','Style: Default,Noto Sans CJK KR,17,&H00FFFFFF,&H00101010,&H70000000,1,0,0,0,100,100,0,0,1,1.8,0.8,2,10,10,8,1','','[Events]','Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text']
def tm(t):
    h=int(t//3600); m=int((t%3600)//60); s=t%60
    return f'{h}:{m:02}:{s:05.2f}'
def wrap_ko(text, width=23):
    chunks=[]; cur=''
    for word in text.split(' '):
        if cur and len(cur)+1+len(word)>width: chunks.append(cur); cur=word
        else: cur=(cur+' '+word).strip()
    if cur: chunks.append(cur)
    return '\\N'.join(chunks[:2])
for n in D['narration']:
    ass.append(f"Dialogue: 0,{tm(LEAD+n['t_start'])},{tm(LEAD+n['t_end'])},Default,,0,0,0,,{esc_ass(wrap_ko(n['text']))}")
(ROOT/'n18_full_preview.ass').write_text('\n'.join(ass),encoding='utf-8')
(ROOT/'n18_full_preview_shots.json').write_text(json.dumps({'source_audio':str(AUDIO),'source_audio_duration_s':end_audio,'lead_s':LEAD,'timing_basis':'shots.json actual t_start/t_end; each cue is shifted by the 1.5 s audio leader; no equal-time assignment.','shots':shots},ensure_ascii=False,indent=2),encoding='utf-8')
out=ROOT/'n18_terra_full_preview.mp4'
cmd=['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-i',str(AUDIO),'-vf',f"subtitles={ROOT/'n18_full_preview.ass'}",'-r',str(FPS),'-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest',str(out)]
subprocess.run(cmd,check=True)
print(out)
print('shots',len(shots),'unique_screens',sorted(set(x['screen'] for x in shots)))
