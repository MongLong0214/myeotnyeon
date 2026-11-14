# EVAL case pack ko-1 (2026-11-13) — raw facts only, no spec

Give this file, and nothing else, to each operator together with their id. Haiku id: `zzh049`, Sonnet id: `zzs049`.
Channel: `myeotnyeon` (ko). Packet line: "Follow factory/runbooks/RESEARCH.md, SPEC.md, BUILD.md, REVIEW.md in order.
Spec path: episodes/specs/<id>.json. Stop at REVIEW. Report the path of review.json."
The coordinator keeps the answer key outside the repo (operators must not be able to read it).

## Case
Two real-estate agents in Busan told an acquaintance that the money would go into a government project, and promised to
return double the money. They took 400 million won from her and were sentenced to prison. Topic radar rank 3 of
2026-11-13 (topic radar report of 2026-11-13 22:38 KST). The case is not grave: there are no deaths, no injuries, no
minors and no sexual offence.

## Raw facts (paraphrased; operators must find and copy the exact source sentences)
- Court: Busan District Court, criminal single judge division 11 (부산지법 형사11단독). Verdict announced 2026-11-10.
  Two defendants (A, B), each sentenced to 1 year 6 months in prison. The charge is fraud (사기). No source reports an appeal.
- The pitch: if she invested in a public project run by the land ministry and the industrial complex agency, she would get
  double her principal back.
- The victim and A attended the same Catholic church and had known each other for about 10 years. A introduced B as a
  real-estate agent.
- She sent a total of 400 million won in 6 transfers between 2022-03-21 and 2022-08-16.
- They had no funding. A land-purchase agreement had already expired at the end of 2021. A hospital had decided in
  January 2022 not to invest. They did not tell the victim.
- In February 2022, A messaged that they were short of money for an office move and asked her to help once more.
- The judge found intent (미필적 고의) and called the loss of 400 million won very large: nothing was repaid and there was no
  settlement. The judge also took into account that the defendants were first offenders and had not planned the harm.

## Sources
- S1 뉴스1 https://www.news1.kr/local/busan-gyeongnam/6349166 — the body is rendered by script, so a plain fetch returns only the
  headline and summary. Expect `validate` to say the quote is not found. Save the article text by hand, as RESEARCH.md step 4
  describes (Tavily extract works).
- S2 뉴시스 https://www.newsis.com/view/NISX20261110_0003862192 — a plain fetch returns the full text.
