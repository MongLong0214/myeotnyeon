"""Beast Clash caption breaks (episodes/beastclash/captions.py): sentence punctuation first, names / number+unit /
verb+particle never split, no lone word from the next sentence, 1-3 words and one font size (<= MAX_CHARS) per caption.
  .venv/bin/python factory/tests/test_bc_captions.py"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location('bc_captions', ROOT / 'episodes/beastclash/captions.py')
C = importlib.util.module_from_spec(_s)
_s.loader.exec_module(C)
KEEP = ['orca', 'white shark', 'great white shark', 'killer whale']


def test_sentence_first_and_no_lone_word_from_next_sentence():
    assert C.split('Who wins? Take your pick!', KEEP) == ['Who wins?', 'Take your pick!']
    assert C.split('The orca rears up. Jaws first!', KEEP) == ['The orca', 'rears up.', 'Jaws first!']


def test_particles_stay_with_their_verb():
    assert C.split('The shark closes in!', KEEP) == ['The shark', 'closes in!']
    assert C.split('The shark backs away!', KEEP) == ['The shark', 'backs away!']


def test_names_and_numbers_with_units_stay_whole():
    assert C.split('Orca vs great white shark!', KEEP) == ['Orca vs', 'great white shark!']
    assert C.split('22,000 lbs vs 4,500 pounds!', KEEP) == ['22,000 lbs vs', '4,500 pounds!']
    assert C.split('Orca teeth: 3 in. long!', KEEP) == ['Orca teeth:', '3 in. long!']   # "in." is not a sentence end
    assert 'white sharks.' in C.split('In a study, orca visits displaced white sharks.', KEEP)   # plural of a kept name


def test_one_word_exclamation_may_lead_the_next_sentence():
    assert C.split('BAM! The shark takes the hit!', KEEP) == ['BAM! The shark', 'takes the hit!']


def test_every_caption_fits_one_size():
    lines = ['Orca vs great white shark!', 'In a study, orca visits displaced white sharks.', 'Rematch? Round 2!',
             'Experts say a healthy adult male walrus can more than match most polar bears.']
    for ln in lines:
        for cap in C.split(ln, KEEP + ['polar bear']):
            assert 1 <= len(cap.split()) <= C.MAX_WORDS and len(cap) <= C.MAX_CHARS, cap


def test_need_s():
    assert C.need_s('BAM!') == .4 and C.need_s('Orca vs') == .5 and C.need_s('great white shark!') == .75


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f()
    print('OK')
