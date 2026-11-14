# Demo: Kiwi POS tags -> candidate subtitle break points (break allowed only after a phrase-final morpheme).
from kiwipiepy import Kiwi
kiwi = Kiwi()
S = ["피고인은 새벽 세 시에 금은방 뒷문을 따고 들어가 진열장 유리를 깨뜨렸습니다",
     "법원은 반성하지 않는다며 징역 이 년을 선고했고 피해자는 합의를 거부했습니다",
     "그런데 결정적인 증거는 바로 그가 버린 영수증 한 장이었습니다"]
# phrase-final tags: particles(J*), endings(E*: EC connective, EF final, ETM adnominal is NOT a break)
for s in S:
    toks = kiwi.tokenize(s)
    eoj, out, cur, last = [], [], "", None
    for t in toks:
        if last is not None and t.start > last.end:  # new eojeol starts (space)
            out.append((cur, last.tag)); cur = ""
        cur += s[t.start:t.end] if not cur or t.start > (last.end if last else 0) else s[last.end:t.end]
        last = t
    out.append((cur, last.tag))
    line, lines = "", []
    for w, tag in out:
        line = (line + " " + w).strip()
        strong = tag in ("EC", "JKB", "JX") or tag.startswith("EF")
        weak_no = tag in ("ETM", "MM", "NNB", "XPN") or tag.startswith("SN")
        if len(line) >= 9 and strong and not weak_no:
            lines.append(line); line = ""
    if line: lines.append(line)
    print(" | ".join(f"{l}({len(l)})" for l in lines))
print(kiwi.split_into_sents("판결이 나왔다 그런데 피해자는 웃었다 왜일까")[0:3])
print(kiwi.space("법원은반성하지않는다며징역이년을선고했다"))
