"""Summarize both full gate runs. Sparse rows preserve every measured pair."""
import collections
import itertools
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def ranges(frames):
    return [[a[0],a[-1]] for _,g in itertools.groupby(enumerate(sorted(set(frames))),lambda p:p[1]-p[0])
            if (a:=[n for _,n in g])]

def summarize(run):
    events=collections.defaultdict(list)
    failures=[];onsite=[];counts=0;max_depth=0
    for fr in run['frames']:
        counts+=len(fr['tools'])*len(fr['targets'])
        for i,j,d,c in fr['hits']:
            max_depth=max(max_depth,d)
            if d<=run['threshold_mm']:continue
            failures.append(fr['f'])
            if (fr['shot']=='specimen')==run['tools'][i].startswith('Specimen forceps'):
                onsite.append(fr['f'])
            events[i,j].append((fr['f'],d))
    return dict(frames=len(run['frames']),tested_pairs_across_frames=counts,
                max_depth_mm=max_depth,over_limit_frames=len(set(failures)),
                over_limit_frame_ranges=ranges(failures),over_limit_on_active_set_frames=len(set(onsite)),
                over_limit_on_active_set_ranges=ranges(onsite),
                violations_by_pair=[dict(tool=run['tools'][i],target=run['targets'][j],
                    peak_mm=max(d for _,d in rows),ranges=ranges(f for f,_ in rows))
                    for (i,j),rows in sorted(events.items(),key=lambda item:-max(d for _,d in item[1]))])

def main():
    before,after=[json.loads(Path(p).read_text()) for p in sys.argv[1:3]]
    if any([r['f'] for r in run['frames']]!=list(range(1,1054)) for run in (before,after)):
        raise ValueError('Missing edited frame')
    if not after['ok']:raise ValueError('Unresolved penetration')
    if before['tools']!=after['tools'] or before['targets']!=after['targets']:raise ValueError('Different audit populations')
    summary={'threshold_mm':.2,'units':'millimetres','frame_numbering':'1-based inclusive, on the 20 fps edited timeline',
        'method':'At every output pose, evaluate render-visible instruments and hard tissue, including loose debris and the separate specimen set. Broad-phase world bounds, evaluated triangle BVH overlap, and shell containment. Mesh depth is the maximum sampled interior distance to the opposing surface across vertices, crossing triangle centroids, edge midpoints and clipped faces. The open alveolar bed is tested on its material side with upward rays.',
        'groove_policy':'The evaluated Boolean removes the actual cutter sweep before measuring contact. All pairs, including cutting lands, use the same numerical threshold.',
        'encoding':'tools and targets give zero-based name indices. Every Cartesian pair in the frame tools and targets lists was tested. Unlisted hit rows have zero depth and zero crossing triangles. Each hit is [tool_index,target_index,depth_mm,crossing_triangle_pairs].',
        'draft4':summarize(before),'draft5':summarize(after),'ok':after['ok'],
        'tools':after['tools'],'targets':after['targets'],
        'contact_checks':json.loads((HERE/'contact_checks.json').read_text()),'frames':[]}
    for a,b in zip(before['frames'],after['frames']):
        if a['tools']!=b['tools'] or a['targets']!=b['targets']:raise ValueError(('Visibility changed',b['f']))
        summary['frames'].append(dict(frame=b['f'],shot=b['shot'],source_frame=b['source_frame'],
            tools=b['tools'],targets=b['targets'],draft4_hits=a['hits'],draft5_hits=b['hits']))
        if a.get('empty_meshes'):summary['frames'][-1]['draft4_fully_removed']=a['empty_meshes']
        if b.get('empty_meshes'):summary['frames'][-1]['draft5_fully_removed']=b['empty_meshes']
    # One edited frame per line keeps the complete run practical to inspect.
    frames=summary.pop('frames')
    header=json.dumps(summary,ensure_ascii=False,indent=2)
    text=header[:-2]+',\n  "frames": [\n'+',\n'.join('    '+json.dumps(fr,separators=(',',':')) for fr in frames)+'\n  ]\n}\n'
    (HERE.parents[1]/'penetration_report.json').write_text(text)
if __name__=='__main__':main()
