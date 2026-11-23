"""Check the episode's attribution destination. The CLI retains its historical arguments."""
import json
import sys
from pathlib import Path

from description_gate import check_description

episode = Path(sys.argv[2])
config = json.loads((episode / 'episode.json').read_text())
description_ok, detail = check_description(episode / 'description.txt')
ok = description_ok and not config.get('credits')
print(json.dumps({'ok': bool(ok), 'in_video_credit': bool(config.get('credits')), 'description': detail}))
sys.exit(0 if ok else 1)
