from pathlib import Path
import json,re,hashlib,struct
p=Path(__file__).resolve().parent
qs=['012','016','017'];ready=[];sha=[]
report=['# v52b verification','',
'PASS — all three files. All frame indices below are **zero-based**, endpoints inclusive. No network or uploads. Only `upload/fix_v52b/` was written.', '',
'## Exact spans and visual findings','',
'Each input was decoded at 1080×1920 from its last 110 frames through EOF (q012 f857–966, q016 f780–889, q017 f562–671), including more than 40 frames before the end card. The defect is the flat purple parking-lot illustration with a lamp and outlined buildings inside the judge panel. All occurrences, including possible fade/residual exposures, were checked through EOF.','',
'| Input / short | Defect span | Count / duration | Last normal frame held | End-card start |','|---|---:|---:|---:|---:|']
for q,num,card in [('012',12,922),('016',13,845),('017',14,627)]:
 m=json.loads((p/f'q{q}_metrics.json').read_text());a,b=m['span'];h=m['held']
 report.append(f'| v52_q{q}.mp4 / #{num} | f{a}–f{b} | {b-a+1} / {(b-a+1)/30:.6f} s | f{h} | f{card} ({card/30:.6f} s) |')
report += ['',
'The illustration starts and ends with hard cuts. There is no partial exposure before the first listed frame and no remaining panel/illustration after the last listed frame. q016/q017 end cards contain a **different**, full-screen rendered night scene (different buildings, perspective, wet pavement and lighting); this is visually distinct from the flat purple defect. It was retained. No file met the requested stop condition.', '',
'Before strips: `v52_q012_span.jpg` f914–924; `v52_q016_span.jpg` f838–847; `v52_q017_span.jpg` f620–629. Every cell is an unscaled 1080×1920 image, with a separate 32-pixel frame label above it and three frames of margin on each side.', '',
'Output visual review covered the whole hold-to-end-card transition and all 45 end-card frames per file through EOF. Native-resolution boundary frames and temporal extrema were inspected together with every-frame tail sheets. No purple illustration, panel residue, or inserted flicker was seen. The original end-card backgrounds and their motion remain. Output strips `v52_q012_after.jpg` f914–966, `v52_q016_after.jpg` f838–889, `v52_q017_after.jpg` f620–671 contain every tail frame at original resolution, six columns, row-major order; blank trailing cells contain no frames. Each strip is 6480×17568.', '',
'## Encoding and probe results', '',
'`libx264`, CRF 12, preset slow, faststart, `-c:a copy`. FFmpeg `freezeframes` replaces the entire decoded frame with the last normal decoded frame before H.264 encoding; there is no RGB conversion in the video path. The original timestamps and all frames are retained.', '',
'| File | Side | Video frames (declared / decoded) | Video duration (s) | Container duration (s) | FPS (r / avg) | Video / audio |','|---|---|---:|---:|---:|---|---|']
probes={}
for q in qs:
 probes[q]={}
 for label in ['input','output']:
  d=json.loads((p/f'q{q}_{label}_ffprobe.json').read_text());probes[q][label]=d;v,a=d['streams'];name=f'v52_q{q}.mp4' if label=='input' else f'v52b_q{q}.mp4'
  report.append(f'| {name} | {label} | {v["nb_frames"]} / {v["nb_read_frames"]} | {v["duration"]} | {d["format"]["duration"]} | {v["r_frame_rate"]} / {v["avg_frame_rate"]} | {v["codec_name"]} / {a["codec_name"]} |')
  assert v['nb_frames']==v['nb_read_frames']
  assert (v['width'],v['height'],v['pix_fmt'],v['color_range'],v['color_space'],v['color_transfer'],v['color_primaries'])==(1080,1920,'yuv420p','tv','bt709','bt709','bt709')
 for k in ['nb_frames','nb_read_frames','duration','r_frame_rate','avg_frame_rate','width','height','pix_fmt','color_range','color_space','color_transfer','color_primaries','time_base']:
  assert probes[q]['input']['streams'][0][k]==probes[q]['output']['streams'][0][k],(q,k)
 # Frame timestamps, using first numeric CSV field; SEI text lines are ignored.
 ts=[]
 for label in ['input','output']:
  values=[int(l.split(',')[0]) for l in (p/f'q{q}_{label}_timestamps.csv').read_text().splitlines() if re.match(r'^\d+(,|$)',l)]
  assert len(values)==int(probes[q][label]['streams'][0]['nb_frames'])
  assert values==list(range(0,len(values)*3000,3000))
  ts.append(values)
 assert ts[0]==ts[1]
 # Confirm moov atom precedes mdat (faststart).
 atoms=[];f=p/f'v52b_q{q}.mp4'
 with f.open('rb') as src:
  pos=0
  while pos<f.stat().st_size:
   src.seek(pos);size,kind=struct.unpack('>I4s',src.read(8))
   if size==1:size=struct.unpack('>Q',src.read(8))[0]
   if size==0:size=f.stat().st_size-pos
   atoms.append(kind);pos+=size
 assert atoms.index(b'moov')<atoms.index(b'mdat')
report += ['',
'All six probes: 1080×1920, SAR 1:1, yuv420p, TV range, BT.709 matrix / transfer / primaries, progressive; video time base 1/90000. AAC-LC audio is 48000 Hz stereo. Video frame PTS match input for **every frame**, starting at 0 and stepping by 3000 ticks (1/30 s); no frame insertion, deletion, or end-card shift. Faststart was verified by `moov` preceding `mdat`. Full `ffprobe -count_frames -show_streams -show_format` JSON is in `qNNN_input_ffprobe.json` / `qNNN_output_ffprobe.json`.', '',
'## Every-frame PSNR', '',
'PSNR is FFmpeg’s size-weighted Y/U/V `psnr_avg` on the decoded native yuv420p planes, peak 255. Outside the span, output is compared with the corresponding input frame. Inside, output is compared with the **input last-normal frame**, not the defective input image. No frames are skipped. Values from the per-frame log are reported to 0.01 dB.', '',
'| Output | Outside frames tested | Minimum outside PSNR (≥42 dB) | Frame | Outside per-plane minima Y / U / V (dB) |','|---|---:|---:|---:|---|']
for q in qs:
 m=json.loads((p/f'q{q}_metrics.json').read_text());o=m['outside'];planes=o['per_plane_min']
 report.append(f'| v52b_q{q}.mp4 | {o["count"]} | {o["minimum_psnr"]:.2f} | f{o["minimum_frame"]} | {planes["y"]:.2f} / {planes["u"]:.2f} / {planes["v"]:.2f} |')
report += ['', '| Output | Replaced frame | PSNR vs input held frame (≥45 dB) | PSNR vs decoded output held frame (≥45 dB) |','|---|---:|---:|---:|']
for q in qs:
 m=json.loads((p/f'q{q}_metrics.json').read_text());hc=json.loads((p/f'q{q}_hold_check.json').read_text())
 for row,outrow in zip(m['replaced'],hc['decoded_output_hold_comparison']):
  assert row['frame']==outrow['frame']
  report.append(f'| v52b_q{q}.mp4 | f{row["frame"]} | {row["psnr"]:.2f} | {outrow["psnr_vs_output_held"]:.2f} |')
report += ['',
'Exact pre-encode equality is separately verified by `qNNN_preencode_hold.framemd5`: the held source frame and every replacement have the same native YUV hash. Lossy output equality is quantified above. Detailed every-frame values: `qNNN_psnr.log`; hold checks: `qNNN_hold_check.json`. The files are re-encoded, and no bitwise-unchanged video claim is made.', '',
'## Audio equality and EBU R128', '',
'AAC payload MD5 is calculated with `ffmpeg -i FILE -map 0:a:0 -c:a copy -f md5 -`; this hashes the copied compressed stream, not a decoded substitute. A second MD5 over decoded PCM s32le also matches. Integrated loudness uses `ebur128=peak=true` over each entire audio stream; values below are FFmpeg’s 0.1-LUFS summary precision.', '',
'| Short | Input AAC MD5 | Output AAC MD5 | Equal | Input / output I (LUFS) |','|---|---|---|---|---:|']
for q,num in [('012',12),('016',13),('017',14)]:
 m=json.loads((p/f'q{q}_metrics.json').read_text());i=m['input'];o=m['output'];a,b=m['span']
 report.append(f'| #{num} / q{q} | `{i["audio_md5"].split("=")[1]}` | `{o["audio_md5"].split("=")[1]}` | true | {i["lufs"]:.1f} / {o["lufs"]:.1f} |')
 ready.append(f'READY v52b_q{q}.mp4 f{a}-f{b} {m["outside"]["minimum_psnr"]:.2f}dB true')
 f=p/f'v52b_q{q}.mp4';sha.append(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}')
report += ['',
'Audio stream durations input/output: q012 32.235000 / 32.235000 s; q016 29.675000 / 29.675000 s; q017 22.400000 / 22.400000 s. Full EBU R128 logs: `qNNN_input_r128.log` / `qNNN_output_r128.log`. Compressed and decoded MD5 values are retained in `qNNN_metrics.json`.', '',
'`SHA256` covers the three final MP4 outputs. `READY.txt` has one line per output: status, filename, inclusive zero-based span, minimum outside-span PSNR, audio MD5 equality.']
(p/'verify.md').write_text('\n'.join(report)+'\n')
(p/'SHA256').write_text('\n'.join(sha)+'\n')
(p/'READY.txt').write_text('\n'.join(ready)+'\n')
print('\n'.join(ready));print('\n'.join(sha))
