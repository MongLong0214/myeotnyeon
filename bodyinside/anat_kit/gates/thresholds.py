#!/usr/bin/env python3
"""Locked gate thresholds (defect class gate-threshold-moved-to-pass).
All thresholds of the gates added for review 10-13 and the review gate live in gates/thresholds.json. The file is locked by
gates/thresholds_changes.yaml: an append-only list of {date, keys, reason, sha256}. The sha256 of the CURRENT thresholds.json must
equal the sha256 of the LAST entry, every entry needs a reason of >= 25 characters that names why (never "to pass"), and lists the
keys it changed. Importing this module (`from thresholds import T`) raises SystemExit if the lock does not hold, so every gate that
reads a threshold fails when someone moved one without a reason entry.
usage:
  python thresholds.py check [THRESHOLDS_JSON CHANGES_YAML]   -> exit 1 if the lock is broken
  python thresholds.py record "reason" --human-approved key1 [key2 ...]           -> append an entry for the current file (after you edited it)"""
import sys, os, json, hashlib, datetime
import yaml

D = os.path.dirname(os.path.abspath(__file__))
TJ, TC = D + '/thresholds.json', D + '/thresholds_changes.yaml'
BANNED = ('to pass', 'so it passes', 'make it pass', 'fixture passes', 'loosen')

# Last digest in the historical reason log before approval flags were introduced.
LEGACY_DIGEST = "c562f2efe4d53b8068e2ede04232eafceed4e797ee62a54926067835678cd424"

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def lock_errors(tj=TJ, tc=TC):
    errs = []
    log = yaml.safe_load(open(tc)) if os.path.exists(tc) else None
    if not log: return ['no change log ' + tc]
    baseline = next((i for i,e in enumerate(log) if e.get('sha256') == LEGACY_DIGEST), -1)
    for i, e in enumerate(log):
        if i > baseline and e.get('human_approved') is not True:
            errs.append(f'entry {i}: missing human approval')
        r = str(e.get('reason', ''))
        if len(r) < 25: errs.append(f'entry {i}: reason shorter than 25 characters')
        if any(b in r.lower() for b in BANNED): errs.append(f'entry {i}: reason says the change was made to pass a gate')
        if not e.get('keys'): errs.append(f'entry {i}: no keys listed')
    if sha(tj) != LEGACY_DIGEST:
        change = json.load(open(tj)).get('_change', {})
        if change.get('human_approved') is not True or change.get('reason') != log[-1].get('reason'):
            errs.append('thresholds.json requires _change.human_approved=true and the logged reason')
    if log[-1].get('sha256') != sha(tj): errs.append('thresholds.json changed without a reason entry (sha256 differs from the last entry in thresholds_changes.yaml)')
    return errs

def load():
    errs = lock_errors()
    if errs: raise SystemExit('THRESHOLD LOCK BROKEN: ' + '; '.join(errs))
    return json.load(open(TJ))

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if cmd == 'check':
        e = lock_errors(*(sys.argv[2:4] if len(sys.argv) >= 4 else (TJ, TC))); print(json.dumps({'ok': not e, 'errors': e})); sys.exit(1 if e else 0)
    if cmd == 'record':
        log = (yaml.safe_load(open(TC)) if os.path.exists(TC) else None) or []
        change = json.load(open(TJ)).get('_change', {})
        if change.get('human_approved') is not True or change.get('reason') != sys.argv[2] or '--human-approved' not in sys.argv[3:]:
            sys.exit('a human must set _change.reason and _change.human_approved in thresholds.json and pass --human-approved')
        log.append({'human_approved':True,'date': datetime.date.today().isoformat(), 'keys': [k for k in sys.argv[3:] if k != '--human-approved'], 'reason': sys.argv[2], 'sha256': sha(TJ)})
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w",dir=D,delete=False) as staged:
            yaml.safe_dump(log, staged, allow_unicode=True, sort_keys=False, width=200)
        try:
            e = lock_errors(TJ, staged.name)
            if not e:
                os.replace(staged.name, TC)
        finally:
            if os.path.exists(staged.name):
                os.unlink(staged.name)
        print(json.dumps({'ok': not e, 'errors': e})); sys.exit(1 if e else 0)
else:
    T = load()


def episode_gap(folder):
    """An episode can use only its owner's recorded, episode-specific exception."""
    from pathlib import Path
    override = Path(folder) / 'thresholds.json'
    if not override.exists():
        return T['human']['payoff_ear_offset_m']
    approved = Path(D).parent / 'templates/neck_v3/thresholds.json'
    data = json.loads(override.read_text())
    if Path(folder).name != 'anat_neck_v3' or data != json.loads(approved.read_text()):
        raise ValueError('unregistered episode threshold override')
    gap = data['human_reads_as_human']
    historical = hashlib.sha256(approved.read_bytes()).hexdigest() == "9c55f8cbb123ffcbff592338a82f231873b93225f8b4a3235e5c3bda0fd71838"
    if not historical and (gap.get('human_approved') is not True or not str(gap.get('reason','')).strip()):
        raise ValueError('episode threshold override requires a reason and explicit human approval')
    return gap['gap']
