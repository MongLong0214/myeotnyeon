"""Beast Clash caption timing: 1-3 word captions follow a per-word minimum (0.25 s per word, never under 0.35 s).
Every other format keeps the fixed 0.8 s minimum; the per-word rule is opt-in (--cue-rule per_word, passed only by
factory/shorts/bc.py and episodes/beastclash/finish.sh).
  .venv/bin/python -m pytest factory/tests/test_bc_cue_rule.py -q"""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from factory.qa import gate  # noqa: E402

BC = SimpleNamespace(min_cue=0.8, cue_rule='per_word')
QUIZ = SimpleNamespace(min_cue=0.8, cue_rule='fixed')


def test_per_word_minimums():
    assert gate.min_cue_for('BAM!', BC) == 0.35
    assert gate.min_cue_for('Orca vs', BC) == 0.5
    assert gate.min_cue_for('great white shark!', BC) == 0.75
    assert gate.min_cue_for('one two three four', BC) == 1.0


def test_other_formats_keep_the_fixed_minimum():
    for text in ('BAM!', 'Orca vs', 'great white shark!'):
        assert gate.min_cue_for(text, QUIZ) == 0.8
    assert gate.min_cue_for('BAM!', SimpleNamespace(min_cue=0.8)) == 0.8  # no cue_rule attribute -> fixed


def test_default_cli_rule_is_fixed_and_only_bc_opts_in():
    root = Path(__file__).resolve().parents[2]
    assert "default='fixed'" in (root / 'factory/qa/gate.py').read_text()
    users = [p for p in list((root / 'factory').rglob('*.py')) + list((root / 'episodes').rglob('*.sh'))
             if 'per_word' in p.read_text(errors='ignore') and p.name not in ('gate.py', 'test_bc_cue_rule.py')]
    assert sorted(p.name for p in users) == ['bc.py', 'finish.sh']
