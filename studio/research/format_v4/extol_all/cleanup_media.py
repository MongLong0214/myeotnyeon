import json,shutil,datetime
from pathlib import Path
R=Path(__file__).resolve().parent
media_ext={'.mp4','.wav','.m4a','.mp3','.opus','.webm','.aac','.flac','.mov','.mkv','.part','.ytdl'}
deleted=[]
for p in sorted(R.rglob('*'),key=lambda p:len(p.parts),reverse=True):
 if p.suffix.lower() in media_ext and (p.is_file() or p.is_symlink()):
  size=0 if p.is_symlink() else p.stat().st_size
  deleted.append({'path':str(p.relative_to(R)),'bytes':size,'symlink':p.is_symlink()});p.unlink()
# Working transcripts and full-size OCR frames were intermediate analysis inputs.
intermediate=[]
for p in list(R.rglob('*.internal.json')):
 intermediate.append(str(p.relative_to(R)));p.unlink()
for d in list(R.glob('*/ocr_frames.internal')):
 intermediate.append(str(d.relative_to(R)));shutil.rmtree(d)
for d in list(R.glob('*/prior')):
 intermediate.append(str(d.relative_to(R)));shutil.rmtree(d)
for pattern in ['*/words.csv','*/media.info.json','*/stats_raw.json','*/stats_probe.json','*/media.jpg']:
 for p in R.glob(pattern):intermediate.append(str(p.relative_to(R)));p.unlink()
for name in ['swift_cache','link_probe','tmp']:
 p=R/name
 if p.exists():intermediate.append(name);shutil.rmtree(p)
for name in ['measure_sample.txt','sample.log','available_tasks.py','probe_related.py']:
 p=R/name
 if p.exists():p.unlink()
remaining=[str(p.relative_to(R)) for p in R.rglob('*') if p.suffix.lower() in media_ext and (p.is_file() or p.is_symlink())]
prior=[]
for folder in ['ref_extol','ref_extol2','ref_extol_story']:
 d=R.parent/folder
 for p in d.rglob('*'):
  if p.suffix.lower() in media_ext and (p.is_file() or p.is_symlink()) and 'ours' not in str(p.relative_to(d)):
   prior.append(str(p.relative_to(R.parent)))
out={'completed_at':datetime.datetime.now().astimezone().isoformat(),'scope':'All source downloads/copies, proxies, analysis audio and media symlinks made under extol_all; prior reference jobs checked read-only','source_media_downloads_or_copies_deleted':sum(x['path'].endswith('/media.mp4') for x in deleted),'media_files_or_symlinks_deleted':len(deleted),'media_bytes_deleted':sum(x['bytes'] for x in deleted),'deleted_media':deleted,'removed_intermediate_files_or_folders':intermediate,'remaining_media_under_extol_all':remaining,'prior_reference_media_remaining_readonly_check':prior,'retained':'metadata, comments, thumbnails, small key/type/boundary crops, CSV/JSON/NPZ derived measurements and analysis scripts'}
(R/'media_cleanup.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
p=R.parent/'extol_formula_all.md';text=p.read_text().replace('원본 미디어·프록시·분석 WAV·임시 전사문·OCR 원본 프레임은 최종 정리에서 제거한다. 삭제 결과는 extol_all/media_cleanup.json에 기록한다.','이번 작업의 원본 미디어·프록시·분석 WAV·임시 전사문·OCR 원본 프레임을 삭제했다. 삭제 결과는 extol_all/media_cleanup.json에 기록했다.');text+='\n최종 삭제 확인: 본 작업의 원본/복사 미디어 '+str(out['source_media_downloads_or_copies_deleted'])+'개 삭제, extol_all 잔존 미디어 '+str(len(remaining))+'개. 선행 3개 폴더의 Extol 원본/분석 미디어도 읽기 확인에서 '+str(len(prior))+'개였다. 남은 CSV/NPZ로 수치 검토는 가능하며 ASR 재실행에는 원본 재다운로드가 필요하다.\n';p.write_text(text)
print(json.dumps({k:v for k,v in out.items() if k not in ['deleted_media','removed_intermediate_files_or_folders']},ensure_ascii=False,indent=2))
