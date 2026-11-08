"""Local additive q013 fix. Existing episodes.py stays byte-identical.
C2/C3 relied on actors over Paper; v52 input omitted actors without replacement.
Use object-only sets so removing people cannot erase the scene illustration.
"""
from copy import deepcopy
from episodes import EPISODES as BASE_EPISODES
EPISODES = deepcopy(BASE_EPISODES)
EPISODES['q013']['no'] = 16
SCENE_SETS = {'C2': 'custody_court', 'C3': 'probation_objects'}
for cue in EPISODES['q013']['cues']:
    if cue[0] in SCENE_SETS:
        cue[5]['set'] = SCENE_SETS[cue[0]]
        cue[5].pop('actors', None)

def patch_render(doc):
    result = deepcopy(doc)
    result['ep']['no'] = EPISODES['q013']['no']
    for cue in result['cues']:
        if cue['id'] in SCENE_SETS:
            cue['p']['set'] = SCENE_SETS[cue['id']]
    return result
