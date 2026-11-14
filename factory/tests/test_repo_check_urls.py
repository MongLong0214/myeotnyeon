"""repo_check: entropy/email/phone rules are off (owner 11-14); real credential formats still fail.
  .venv/bin/python factory/tests/test_repo_check_urls.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import repo_check as rc  # noqa: E402

# fixtures are assembled at runtime so this file itself carries no high-entropy literal
URL = 'https://www.usatoday.com/story/entertainment/tv-streaming/2026/10/23/' + 'laura-owens-clayton-echard-' + 'sentencing-pregnancy-fraud-bachelor/' + '92400353007'
TOK = 'Zx9qL2mV7tR4' + 'wB8nK3pD6sF1' + 'hJ5gC0yQ'
AT = chr(64)


def f(text, path):
    return rc.findings(text.encode(), path)


def test_spec_url_passes():
    assert 'entropy' not in f('{"url": "%s"}' % URL, 'episodes/specs/en001.json')
    assert 'entropy' not in f('url: %s\nbody text' % URL, 'episodes/specs/en001.sources/S1.txt')
    assert 'entropy' not in f('[Sources]\nUSA Today | %s\n' % URL, 'upload/pkg/en001_B/meta.txt')


def test_urls_and_hashes_pass_anywhere():
    # owner 11-14: the entropy rule is off, so citations and record hashes pass in any file
    assert f('see %s' % URL, 'factory/notes.md') == []
    assert f('sha256 ' + 'ab12' * 16, 'upload/ledger.json') == []


def test_real_credential_formats_still_fail():
    assert 'credential-url' in f('{"url": "https://user' + ':' + TOK + AT + 'example.com/x"}', 'episodes/specs/x.json')
    assert 'provider-token' in f('{"url": "https://example.com/' + 'AI' + 'za' + TOK + 'abcdef"}', 'episodes/specs/x.json')
    assert 'private-key' in f('-----BEGIN ' + 'PRIVATE KEY-----', 'notes.md')
    assert 'credential-assignment' in f('api_key = "' + TOK + '"', 'x.py')


if __name__ == '__main__':
    for n, fn in sorted(globals().items()):
        if n.startswith('test_'):
            fn()
            print('ok', n)
