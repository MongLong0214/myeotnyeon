"""local VOICEVOX engine (127.0.0.1:50121) synth: vv.py <style_id> <speed> <out.wav> <text>; prints accent phrases."""
import sys, json, urllib.request, urllib.parse
sid, sp, out, text = sys.argv[1:5]; B = 'http://127.0.0.1:50121'
q = json.load(urllib.request.urlopen(urllib.request.Request(f'{B}/audio_query?speaker={sid}&text={urllib.parse.quote(text)}', method='POST')))
q['speedScale'] = float(sp); q['prePhonemeLength'] = .05; q['postPhonemeLength'] = .05; q['outputSamplingRate'] = 24000
for ph in q['accent_phrases']:
    k = ''.join(m['text'] for m in ph['moras']); print(f"{k}[{ph['accent']}]", end=' ')
print()
w = urllib.request.urlopen(urllib.request.Request(f'{B}/synthesis?speaker={sid}', data=json.dumps(q).encode(), headers={'Content-Type': 'application/json'})).read()
open(out, 'wb').write(w)
