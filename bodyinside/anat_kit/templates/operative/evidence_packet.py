"""Summarize the evaluated geometry used by the cut for its independent reviewer."""
from pathlib import Path

from recipe import DB, LIB, RECORDINGS, WISDOM, digest, options, read, save


def recording_licences(ids):
    source=WISDOM/'LICENCE_AUDIT.md'
    if digest(source)!=LIB['archive']['LICENCE_AUDIT.md']:
        raise ValueError('Original recording audit changed')
    recording_rows=[]
    for ident in sorted(set(map(str,ids))):
        item=LIB['audio'][ident]
        lines=[line for line in source.read_text().splitlines() if line.startswith('|')
               and item['source'] in line.split('|')[1] and 'CC0' in line.split('|')[2]]
        if len(lines)!=1 or item['licence']!='CC0-1.0' or digest(RECORDINGS/(ident+'.mp3'))!=item['sha256']:
            raise ValueError('Unverified edition recording '+ident)
        recording_rows.append(lines[0])
    return recording_rows


def preflight_recipe(folder,case,rows,manifest):
    choices=options(case)
    if len(rows)!=len(choices) or any(row not in stage for row,stage in zip(rows,choices)):
        raise ValueError('Unregistered step, caption, target, thumbnail or clinical source')
    claims=[]
    for row in rows:
        source=LIB['sources'][row['pmid']]
        if not source['claim'] or source['url']!=f'https://pubmed.ncbi.nlm.nih.gov/{row["pmid"]}/':
            raise ValueError('Missing scope or primary source for '+row['step'])
        claims.append({'step':row['step'],'caption':row['caption'],**source})
    licences=recording_licences(cue[0] for row in rows for cue in LIB['steps'][row['step']]['sfx'])
    save(folder/'gates/recipe_preflight.json',dict(claims=claims,recorded_licences=licences,
         inputs=manifest,author_sha256=digest(folder/'author.json')))


def edition_sources(folder,tag):
    """Bind the claims and licence rows for the assets actually used by this cut."""
    episode=read(folder/'episode.json')
    mix=read(folder/'audio.json')
    source=WISDOM/'LICENCE_AUDIT.md'
    recording_rows=recording_licences(row['recording'] for row in mix['cues'])
    credits=read(folder/'assets.json')
    used=credits.get('attribution') or credits['derivations']
    if 'proof' in credits:
        archived=WISDOM/'SOURCES.md'
        if digest(archived)!='f9161e35afda1e962cca30d79d7a3c2069377ffb8974153c57414b9d0abd98d4':
            raise ValueError('The source edition of the surgery material credits changed')
        names=('Periosteal elevator and cheek retractor','Mucosal colour and stippling',
               'Tissue and cut hard surfaces','Steel and reflections','Clot')
        listed=archived.read_text().splitlines()
        for name in names:
            row,=[line for line in listed if line.startswith('| '+name+' |')]
            used+='\n'+row
    (folder/'LICENCE_AUDIT.md').write_text(
        'Licences for this edition\n\n'+used+'\nContinuous original Earshot score. '
        'https://github.com/Leonxlnx/earshot#licence\nThe following recorded cues appear in this mix. '
        'CC0 1.0. https://creativecommons.org/publicdomain/zero/1.0/\n'
        'Publisher audit SHA-256 '+digest(source)+'\n\n'+ '\n'.join(recording_rows)+'\n')
    if episode['id'] in LIB['cases']:
        claims=[dict(caption=row['caption'],shot=row['step'],target=row['target'],pmid=row['pmid'],
                     scope=LIB['sources'][row['pmid']]['claim']) for row in episode['steps']]
        provenance=dict(anatomy=credits['anatomy_source'],instrument_source=credits['instruments'],
                        inputs=credits['inputs'],scene_import=credits['scene_import'])
    else:
        claims=[]
        for shot,_,_,caption,_ in episode['steps']:
            spec=(LIB['surgery_ranges']|LIB['surgery_root_insertions'])[shot]
            claims.append(dict(shot=shot,caption=caption,target=spec['target'],pmid=spec['pmid'],
                          url=f'https://pubmed.ncbi.nlm.nih.gov/{spec["pmid"]}/',
                          scope='One illustrated sectioned, impacted mandibular third molar.'))
        jaw_ids=('FJ1257','FJ1254','FJ1256','FJ1253')
        directory=DB/'obj/isa_BP3D_4.0_obj_99'
        provenance=dict(anatomy='Adjacent lower teeth and gingiva traced to the DBCLS 4.0 source records.',
            archive_source_sha256=digest(WISDOM/'SOURCES.md'),
            registered_objects={name:digest(directory/(name+'.obj')) for name in jaw_ids},
            rendered_exclusions=credits['excluded_geometry'],derivations=used,
            geometry_evidence='Per-pose visibility mask and evaluated hard surfaces in the geometry receipt.')
    sha=read(folder/'gates'/(tag+'_assembly.json'))['sha256']
    save(folder/'gates'/(tag+'_facts.json'),dict(movie_sha256=sha,claims=claims))
    save(folder/'gates'/(tag+'_provenance.json'),dict(movie_sha256=sha,**provenance))


def contact_receipt(folder,tag):
    gates=folder/'gates'
    if not (folder/'assets.json').exists():
        return None
    assets=read(folder/'assets.json')
    if 'proof' in assets:
        paths=[Path(entry['geometry']) for entry in assets['proof']]
    else:
        draft=read(folder/'trial.json')['drafts'][-1]['tag'] if tag=='terminal' else tag.removesuffix('_hq')
        paths=[Path(path) for path in read(gates/(draft+'_preflight.json'))['geometry']]
    shots=[]
    for path in dict.fromkeys(paths):
        rows=read(path)['frames']
        audit=read(path.with_name('audit.json'))
        shot=audit.get('catalog_shot',audit['shot'])
        depths=[hit[-1] for row in rows for hit in row['depths']]
        gaps=[row['tissue_gap'] for row in rows if row['tissue_gap'] is not None]
        sampled=rows[-1:] if shot=='grasp' else rows
        jaws=[gap for row in sampled for gap in row['gaps']] if shot in (
            'grasp','luxate','deliver_whole','extraction_hook') else []
        shots.append(dict(shot=shot,poses=len(rows),maximum_penetration_mm=max(depths,default=0),
                     maximum_engaged_bur_gap_mm=max((r['bur_gap_mm'] for r in rows if 'bur_gap_mm' in r),default=None),
                     maximum_scalpel_gingiva_gap_mm=max(gaps,default=None),
                     maximum_forceps_tooth_gap_mm=max(jaws,default=None),
                     visible_enamel_leader_poses=sum(row['leader'] is not None for row in rows),
                     geometry_sha256=digest(path)))
    ledger=read(gates/(tag+'_assembly.json'))
    if sum(s['poses'] for s in shots)!=ledger['frames'] or digest(folder/(tag+'.mp4'))!=ledger['sha256']:
        raise ValueError('Geometry evidence does not match the assembled cut')
    path=gates/(tag+'_geometry.json')
    result=dict(movie_sha256=ledger['sha256'],frames=ledger['frames'],hard_tissue_limit_mm=.2,shots=shots)
    if 'proof' in assets:
        registered=LIB['archive_instrument_contacts']
        contact=WISDOM/registered['path']
        if digest(contact)!=registered['sha256']:
            raise ValueError('Archived instrument contact data changed')
        forceps=read(contact)['forceps']
        lo,hi=forceps['held_frames']
        shown={row['original'] for entry in assets['proof'] if entry['shot']=='specimen'
               for row in read(Path(entry['geometry']))['frames']}
        held=[v for v in forceps['samples'] if lo<=v[0]<=hi and v[0] in shown]
        if held:
            result['tray_forceps']=dict(registered_source_sha256=registered['sha256'],
                original_frames=[held[0][0],held[-1][0]],poses=len(held),
                maximum_left_gap_mm=max(v[1] for v in held),maximum_right_gap_mm=max(v[2] for v in held))
    save(path,result)
    return path
