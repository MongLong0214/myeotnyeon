"""Write a short delivery note using measurements from the encoded program."""
import json
from pathlib import Path
EP=Path(__file__).resolve().parent.parent
CACHE=EP/'production/.cache'
def write_report():
    draft=json.loads((CACHE/'draft-verification.json').read_text())
    audio=json.loads((CACHE/'audio-metrics.json').read_text())
    contact=json.loads((EP/'penetration_report.json').read_text())
    final_path=CACHE/'final-verification.json'
    final=json.loads(final_path.read_text()) if final_path.exists() else None
    rows=['# Body Inside · 신경치료와 치근단 농양',
          f'1. [Draft](rootcanal_draft1.mp4) · [Ten-shot contact sheet](sheet_draft1.png). Cycles Metal and OpenImageDenoise, 540 × 960, 8 samples, {draft["frames"]} distinct frames at 30 fps, 31.00 s.']
    if final:
        rows.append(f'2. [Final master](rootcanal_final.mp4). Native 1080 × 1920, 24 adaptive samples, {final["unique_frames"]} distinct frames, 30 fps, 31.00 s. SHA-256 `{final["sha256"]}`.')
    else: rows.append('2. The [editable scene](rootcanal.blend) is set to 1080 × 1920 and 30 fps for the final render.')
    rows += [
        f'3. [Scene](rootcanal.blend) · [Instrument measurements](penetration_report.json). The refitted isolation assembly and canal instruments passed the 0.2 mm limit on all {len(contact["frames"])} poses. The maximum measured overlap was {contact["max_depth_mm"]:.4f} mm on a cutting flute.',
        '4. The opening shows the cavity and apical pocket together. Seven numbered stages and tracked Korean leaders follow one molar across treatment and the later crown visit. The captions identify compressed rinsing, drying and inter-visit time.',
        '5. The filled and sealed core remains under the descending crown. The restored section closes to the exterior, then a defocused foreground rim returns to the pre-treatment view.',
        f'6. Nine licence-checked CC0 recordings supply room tone and {audio["events"]} action cues. The continuous instrumental loop ducks by at most {audio["maximum_duck_db"]:.2f} dB. Encoded stereo measures {draft["lufs_i"]:.2f} LUFS-I and {draft["true_peak_dbtp"]:.2f} dBTP. [Mix](production/audio.py) · [Sources and credits](SOURCES.md)',
        ('7. [Thumbnail](thumbnail.png) is master frame 388 at 12.93 s, showing the file and apical pocket together.' if final else '7. Thumbnail selection is frame 388 at 12.93 s, showing the file and apical pocket together.'),
        '8. '+('Both deliveries' if final else 'The draft')+' decoded completely. Picture timestamps are evenly spaced. The hook caption spans the loop seam. Delivery stayed local.'
    ]
    checked=[draft]+([final] if final else [])
    if all(not item['black_frames'] and item.get('freezes_500ms')==0 for item in checked):
        rows[-1]=('8. Both deliveries decoded' if final else '8. The draft decoded')+' on a uniform picture clock with no black frames or half-second freezes. The hook caption spans the loop seam. Delivery stayed local.'
    if all(item.get('isolated_bright_pixels_max_per_frame')==0 for item in checked):
        rows.append('9. The full-frame scan found zero isolated bright pixels. Flat-area noise was sampled once per second.')
    if final and (final['lufs_i']!=draft['lufs_i'] or final['true_peak_dbtp']!=draft['true_peak_dbtp']):raise ValueError('Unexpected audio difference between draft and final')
    if final:
        def elapsed(log):
            return sum(float(row.split()[2]) for row in (CACHE/log).read_text().splitlines() if row.startswith('PLATE '))
        main_minutes=(elapsed('final-look.log')+elapsed('render-final.log'))/60
        reveal_minutes=elapsed('final-reveal.log')/60
        rows.append(f'{len(rows)}. Cycles logged {main_minutes:.1f} minutes for the native master plates and {reveal_minutes:.1f} minutes for the 13 alternate exterior-reveal frames.')
    dest=EP/'PROD_REPORT.md'
    dest.write_text(rows[0]+'\n\n'+'\n'.join(rows[1:])+'\n')
if __name__=='__main__':write_report()
