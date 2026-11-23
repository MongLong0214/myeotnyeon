"""Execute each registry fixture and verify the class-specific production review path."""
import sys, os, json, subprocess, yaml, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checks
K = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); F = K + '/gates/fixtures/'; B = K + '/blender/launch.py'
J = lambda p: json.load(open(p))
FIX = {   # check name -> function(fixture_dir) -> ok (True = the check PASSED, which is wrong for a fixture)
 'caption_truth': lambda d: checks.caption_truth(J(d + '/episode.json'), J(d + '/pose_dump.json'), J(d + '/scene_dump.json'), J(d + '/label_pos.json') if os.path.exists(d + '/label_pos.json') else None)[0],
 'subject_size': lambda d: checks.subject_size(d + '/frames', step=5)[0],
 'rigid_bend': lambda d: checks.rigid_bend(J(d + '/pose_dump.json'), [0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4])[0],
 'leaders_cross': lambda d: checks.leaders_cross({'beats': [], 'labels': [dict(l, dx=l['dx'], dy=l['dy']) for l in J(d + '/episode.json')['labels']]}, J(d + '/label_pos.json'), auto=False)[0],
 'text_size': lambda d: checks.text_size(J(d + '/episode.json'))[0],
 'dead_time': lambda d: checks.dead_time(d + '/frames', J(d + '/episode.json'))[0],
 'visibility_windows': lambda d: checks.visibility_windows(J(d + '/scene_dump.json'), {k: [(0, 135)] for k in J(d + '/scene_dump.json')}, nf=300)[0],
 'steady_glow': lambda d: checks.steady_glow(J(d + '/scene_dump.json'), 'MuscleGlow', (0, 99))[0],
 'pose_ratio': lambda d: checks.caption_truth({'beats': [{'cap': [1], 'evidence': [{'type': 'pose_ratio', 'joints': [0, 1, 2, 3, 4, 5], 'f_c': 380, 'f_rev': 510, 'min_ratio': 0.9}]}]}, J(d + '/pose_dump.json'), {})[0],
 'anchors_apart': lambda d: checks.caption_truth({'beats': [{'cap': [1], 'evidence': [{'type': 'anchors_apart', 'a': 'A_Ear', 'b': 'A_Acro', 'frames': [9], 'min_dy': 0.2}]}]}, {}, {}, J(d + '/label_pos.json'))[0],
 'red_contact': lambda d: checks.red_contact(d + '/frames', 0, 10, 150)[0],
 'labels_anchored': lambda d: checks.labels_anchored(J(d + '/episode.json'))[0],
 'label_beat_alignment': lambda d: checks.label_beat_alignment(J(d + '/episode.json'))[0],
 'audio_fit': lambda d: checks.audio_fit(J(d + '/sfx_report.json'))[0],
 'opening_event': lambda d: checks.opening_event(d + '/frames', at=12)[0],
 'establishing_person': lambda d: checks.establishing_person(J(d + '/scene_dump.json'))[0],
 'human_reads_as_human': lambda d: checks.human_reads_as_human(J(d + '/human_dump.json'))[0],
 'labels_clear_of_anchors': lambda d: checks.labels_clear_of_anchors(J(d + '/episode.json'), J(d + '/label_pos.json'), ['A_Contact', 'A_C56', 'A_Root'])[0],
 'marker_present': lambda d: checks.caption_truth({'beats': [{'cap': [1], 'evidence': [{'type': 'object_scale', 'object': 'EarMarker', 'f': 950, 'radius_mm': 11, 'min_mm': 8}]}]}, {}, J(d + '/scene_dump.json'))[0],
 'audio_balance': lambda d: checks.audio_balance(d + '/sfx.wav')[0],
 'layout_uses_height': lambda d: checks.layout_uses_height(J(d + '/episode.json'))[0],
 'anchors_aligned': lambda d: checks.caption_truth(J(d + '/episode.json'), {}, {}, J(d + '/label_pos.json'))[0],
 'dump_change': lambda d: checks.caption_truth(J(d + '/episode.json'), {}, J(d + '/scene_dump.json'))[0],
 'plumb_projected': lambda d: checks.plumb_projected(J(d + '/label_pos.json'), 900, 900)[0],
 'plumb_drawn': lambda d: checks.plumb_drawn(J(d + '/plumb_draw.json'), J(d + '/label_pos.json'), None, 900, 900)[0],
 'frame_cadence': lambda d: checks.cadence_ok(J(d + '/deltas.json'))[0],
 'narration_wer': lambda d: checks.narration_wer([tuple(x) for x in J(d + '/pairs.json')])[0],
 'narration_sync': lambda d: checks.narration_sync(J(d + '/lines.json'), J(d + '/beats.json'))[0],
 'labels_clear_of_dots': lambda d: checks.labels_clear_of_dots(J(d + '/episode.json'))[0],
 'audio_beat_balance': lambda d: checks.audio_beat_balance(d + '/sfx.wav', [(0, 3), (3, 6)])[0],
 'no_kg_on_screen': lambda d: checks.no_kg_on_screen(J(d + '/episode.json'))[0],
}
def penetration(d):
    out = str(Path(d) / 'measured.json')
    subprocess.run([B, '-b', d + '/scene.blend', '--python-exit-code', '1', '-P',
                    K+'/gates/penetration_gate.py', '--', out, d+'/pairs.json'], check=True, capture_output=True)
    return J(out)['ok']
FIX['penetration_gate'] = penetration
def tool_contact(d):
    fixture=Path(d)
    spec=fixture/'measurement.json'
    result=fixture/'measured.json'
    scene=fixture.parent/'interpenetration-jaw-neck/scene.blend'
    subprocess.run([B,'-b',str(scene),'--python-exit-code','1','-P',K+'/gates/geo_gate.py',
                    '--',str(spec),str(result)],check=True,capture_output=True)
    return J(result)['pass']
FIX['tool_contact'] = tool_contact


def media(d):
    """Fixture dirs from make_real_fixtures.py: check.json names a media_checks function (or threshold_lock) and its arguments."""
    import media_checks, thresholds
    j = J(d + '/check.json'); args = [os.path.join(d, a) if isinstance(a, str) and os.path.exists(os.path.join(d, a)) else a for a in j['args']]
    if j['fn'] == 'threshold_lock': return not thresholds.lock_errors(*args)
    if j['fn'] in ('rim_bevel', 'no_3d_text', 'caption_evidence', 'on_screen_wording', 'caption_reading_speed'): args = [J(args[0])]
    if j['fn'] == 'narration_gaps': args = [args[0], J(args[1])]
    return bool(getattr(media_checks, j['fn'])(*args, **j.get('kwargs', {}))[0])
FIX['media'] = media
import playback
FIX["phone_playback"] = lambda d: playback.checked(J(d+"/playback.json"),"b"*64)
import shot_checks
FIX['skin_clear'] = lambda d: shot_checks.skin_clear(J(d+'/measurement.json'))
FIX['on_landmark'] = lambda d: shot_checks.on_landmark(J(d+'/measurement.json'))
FIX['surface_exposed'] = lambda d: shot_checks.surface_exposed(J(d+'/measurement.json'))
FIX['transition_ok'] = lambda d: shot_checks.transition_ok(Path(os.environ.get('ANAT_EPISODES',(__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../episodes')))/J(d+'/measurement.json')['raw'])

def flash_fixture(d):
    from transients import scan
    data=J(d+'/measurement.json')
    movie=Path(os.environ.get('ANAT_EPISODES',(__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../episodes')))/data['movie']
    flags={item['frame'] for item in scan(movie)}
    if flags & {data['before'],data['after']}: raise ValueError('adjacent control frame flagged')
    return data['frame'] not in flags

FIX['visibility_pop'] = flash_fixture
FIX['cord_clipped'] = lambda d: shot_checks.cord_clipped(J(d+'/human_dump.json'))

from pathlib import Path
sys.path.insert(0, K + '/layout')
from note_layers import stable_notes
FIX['stable_notes'] = lambda d: stable_notes(J(d+'/episode.json'))[0]
from tempfile import TemporaryDirectory
from collections import Counter
from review_classes import checklist, review_failures

def main():
    registry = Path(K) / 'defects.yaml'
    rows = yaml.safe_load(registry.read_text())
    visual = checklist(registry)
    by_id = {row['id']: row for row in rows}
    errors = [] if len(rows) == len(by_id) else [('registry', 'duplicate ids')]
    with TemporaryDirectory(prefix='anat-fixtures-', dir=os.environ.get('TMPDIR')) as temp:
        root = Path(temp)
        source = Path(F)
        # Generate binary inputs privately. Restore the committed JSON overrides.
        for script in ('make_fixtures.py','make_penetration_fixture.py'):
            shutil.copy(source/script,root/script)
        subprocess.run([sys.executable,str(root/'make_fixtures.py')],check=True,stdout=subprocess.DEVNULL)
        shutil.copytree(source,root,dirs_exist_ok=True)
        archive = Path(os.environ.get('ANAT_FIXTURE_ARCHIVE',(__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../fixture_media/anat_kit')))
        if archive.is_dir():
            shutil.copytree(archive,root,dirs_exist_ok=True)
        else:
            subprocess.run([sys.executable,str(root/'make_real_fixtures.py')],check=True,stdout=subprocess.DEVNULL)
        subprocess.run([B,'-b','--factory-startup','--python-exit-code','1','-P',
                        str(root/'make_penetration_fixture.py')],check=True,capture_output=True)
        for row in rows:
            key = row['id']
            e = row.get('enforcement') or {}
            try:
                if e.get('type') == 'alias':
                    target = by_id.get(e.get('of'),{}).get('enforcement',{})
                    if target.get('type') not in ('review','gate'):
                        raise ValueError('missing or indirect alias target')
                elif e.get('type') == 'review':
                    if key not in visual or not row.get('description','').strip():
                        raise ValueError('no production review question')
                    if not review_failures([key], {'defects':[key]}):
                        raise ValueError('positive finding did not block')
                elif e.get('type') == 'gate':
                    directory = root/e['fixture']
                    if not directory.is_dir(): raise ValueError('missing fixture')
                    if FIX[e['check']](str(directory)):
                        raise ValueError('bad fixture passed the check')
                else:
                    raise ValueError('no executable enforcement')
            except (ValueError, KeyError, OSError, subprocess.SubprocessError) as ex:
                errors.append((key,str(ex)))
    print(json.dumps(dict(classes=len(rows),by_enforcement=Counter(
        (r.get('enforcement') or {}).get('type') for r in rows),errors=errors,ok=not errors)))
    return bool(errors)

if __name__ == '__main__':
    sys.exit(main())
