# LF3 바이낸스 — 하이스트 장면표 (scene_heist.md)

Script: script_heist.md, beats B01–B45. This is a narration draft at about 7:12–7:35 (syllable estimate, not yet synthesized).
Owner instruction (11-08, uuid 4dd0d76d): show the preparation before the robbery like a film.
CEO boundaries (msg_569dce69):
- The target is the Binance hot wallets (F01).
- The rewind card reads "그해 6월". It does not say 5 or 6 months.
- Dramatization is not fact.
- Causality only where facts.md supports it.
- The cold open does not spend the method.
- The ending separates other cases' sentences from the hypothetical.

## Common rules
- **재연** marks staging: the hackers' lair, their gestures, the masks, the clock, the vault door and the pipe metaphors. Show a small "재연" tag at the bottom-left of each lair scene.
  - No invented dialogue, psychology, planning meetings or failed attempts presented as real. The hackers do not speak.
- **Hackers.** An anonymous crew in hoods, faces in shadow, with two glints for eyes and a simple mouth line (satisfies H7). No real people. "북한" appears only as the FBI attribution, alongside the denial.
- **Employees.** Engineer 1 and Engineer 2 are non-identifiable, generic characters. They are victims of deception, so they are never played for laughs.
- **Intrusion staging: concrete and cinematic, at the level the public reports describe.** Owner, 11-08: "침투 절차를 구체적으로 영화적으로 연출해". Each reported step is shown as an actual on-screen event:
  - the tampered installer;
  - the job-platform message;
  - the three video interviews;
  - the take-home repo download and install;
  - the endpoint alert that never fires;
  - the 10/20 spread to other wallet developers' machines through the internal AI tool;
  - the 10/29 combination of one developer's computer with another's stolen credentials;
  - the container/script launch;
  - the signing service signing transactions outside the normal flow;
  - the EIP-7702 delegation that outlives the withdrawal halt.
  Screens are stylized UI: progress bars, chat bubbles, video tiles, a terminal window with blurred or placeholder lines, and status lights. No real code, commands, exploit techniques or tool internals beyond what the reports state, both for factual accuracy and so nothing is instructional. Metaphors (vault door, keys, pipes) are used only as inserts on top of the concrete action.
- **Motifs:**
  - (M1) the countdown clock;
  - (M2) the video-call window;
  - (M3) the signing-service vault door;
  - (M4) the lair, which gains one more monitor or object on every return (1 → 2 → 3 → 4 → empty).
- **Pace.** The screen changes every 1.5–2 s, with an event every 10–15 s. No frontal presenter shots. Characters act.

## Beats (shot / action → change / camera / reads / SFX / F)

### COLD 0:00–0:19 — tease the result; keep the method and the ending hidden
- **B01** Hot-wallet vault corridor at night. Coin crates slide down the corridor and out through the exit on their own, at speed. Camera: a fast dolly following the crates. Reads: "something enormous is draining, fast". SFX: a whoosh per crate. Clock (M1): "05:05 KST". F01·F02·F04.
- **B02** Lair 0: a dark silhouette against a single monitor glow; only the glints of the eyes are visible (재연). Cut to the vault: an amount counter spins to "$6.3B ≈ 8조4000억원". Camera: punch-in from the glints to the counter. Reads: "a lot of money, an unknown culprit". F04·F05·F02.
- **B03** The rewind card: the clock hands spin backwards, the calendar flips back through months, and the card lands on "그해 6월". The hook question appears as text. Reads: "how did it get here?" SFX: tape rewind. F30.

### CH1 June — the bait, 0:19–0:51
- **B04** Engineer 1 at a desk downloads an "AI 코딩 도구" installer. The installer icon carries a tiny hidden hook (insert). The install wizard runs and a progress bar fills, while the lair's single monitor lights up in a split screen (재연). Reads: "an ordinary install, but the package was tampered". F08.
- **B05** Lair 1, one monitor (M4 = 1). A hooded figure turns its head toward a single blinking light. Text: "이름·얼굴·역할 비공개". Reads: "we don't know who". F31.
- **B06** The security team comes over, swaps the laptop and hands Engineer 1 a new key card. Engineer 1 relieved: shoulders drop. Camera: wide, then a close-up of the old laptop going into a bin. Reads: "seems handled". Beat hold 0.5 s. F08.
- **B07** Lair 1 cork board: a blank silhouette card labelled "직무·동료 정보" is pinned up (company claim, 재연 visual). A caption-chip: "6월 기기에 계속 붙어 있었다는 증거 없음". Reads: "information leaked; the access did not necessarily persist". F08 (the limit line).

### CH2 September — the fake interview, 0:51–1:41
- **B08** Engineer 2's home office, a laptop notification "채용 제안". Neutral link line: "그리고 석 달 뒤". The calendar flips to September (M1). Engineer 2 leans in, interested. Reads: "a new target, a legitimate-looking channel". F09.
- **B09** Split screen. Left: video-call window (M2) with the friendly "recruiter". Right: lair 2 (M4 = 2), the same character face as a mask on a stand (재연 metaphor). A phone shows SNS photos scrolling. Reads: "trust is being built". F09.
- **B10** The video window adds a third tile: the "CEO". Engineer 2 straightens up, impressed. Camera: slow push on Engineer 2's face. Reads: "it feels big and real". F09.
- **B11** TWIST. Lair 2: three masks hang on hooks. A hooded hand hangs the third one: project lead, recruiter, CEO. The camera tilts down the row of masks. SFX: three hook clicks. Reads: "all three were fake". F09.
- **B12** End of interview 2: the "PM" tile says goodbye. A chat bubble with a link reads "과제 저장소". On the WORK laptop (company sticker visible), Engineer 2 clicks it; the download bar fills, and a folder icon appears on the desktop. Camera: OTS, then an insert on the cursor. Reads: "a test task, on the work computer". F10.
- **B13** Engineer 2 opens a terminal window to set up the task (lines blurred) and an install progress bar runs. Split screen: in lair 2, a dark monitor wakes with a single "연결됨" light (재연). The endpoint-protection shield icon in the laptop's tray stays green and silent; insert on the green shield. A crack of light opens under a door labelled "회사 내부" (insert). Reads: "the install ran the hidden malware; the protection didn't catch it". F10.
- **B14** Engineer 2 typing earnestly, unaware (sympathetic, not mocked). Cut to lair 2: the mask stand turns away. Chip: "무기 = 채용 면접 + 과제". Reads: "the victim was deceived; the weapon was the hiring process". F10.

### CH3 October 20 — inside, 1:41–2:09
- **B15** A company corridor at night, the calendar "10월 20일" (M1). The shadow from B13 walks the corridor. Chip: "9월~10월 20일 사이 움직임: 확인 자료 없음". Reads: "a gap we don't fill". F11 (the limit line).
- **B16** On the infected laptop, a stylized "내부 AI 도구" chat panel opens. From it, cursor trails jump to the screens of other wallet developers' desks across a dark office; each monitor flickers and gets a small red dot. Cut to lair 3 (M4 = 3): a network map gains red nodes and string lines. Reads: "the company's own tool became the path into other developers' systems". F11.
- **B17** Lair 3: the lantern sits under a "?" spotlight. Chip: "어떤 AI 도구가 어떻게 쓰였는지 비공개". Reads: "we don't know the details". F11.
- **B18** Calendar countdown: the pages tear off from 20 to 29 (M1). SFX: ticks speeding up. Reads: "it's coming". F12.

### CH4 October 29 — D-day, 2:09–3:11 (metaphor only, no method)
- **B19** Lair 4, the operations room (M4 = 4 monitors, all lit), clock "UTC 10/29". Split screen:
  - left, Developer A's desk at night, empty chair, screen lit;
  - right, a login card for Developer B fills in by itself.
  Both screens slide into the lair's center monitor, and two key cards merge into one (insert). Reads: "one developer's computer plus another's stolen credentials". F12·F01, company claim.
- **B20** The lair's center monitor shows a stylized "컨테이너 실행" panel: a box icon spins up and a script window opens (lines blurred). A route line draws across a company network map to a node labelled "내부 지갑 서명 서비스" (M3), which turns red. Reads: "they reached the service that signs withdrawals". F06·F12.
- **B21** TWIST. Inside the signing service (stylized server room): transaction slips arrive from a side chute, not from the normal "출금 요청" counter. The signer stamps them VALID one by one. Vault-door insert (M3) swinging open. Camera: crane up. Reads: "valid signatures on transactions made outside the normal process". F06, company claim plus Elliptic.
- **B22** The clock snaps to 20:05 (M1). The corridor from B01 returns, now from inside the vault looking out: crates leave, the first XRP crate, until 20:09. Reads: "the cold open, explained by the build-up". F01·F03.
- **B23** Four-panel chain screens, each a different chain pipe pouring. A 20-minute timer and a "10 chains" chip. A big number pops: "1초에 약 70억원". Reads: "speed". F02·F04·F40.
- **B23a** Scale-gag montage, split screen; the gag is about scale, not the victims:
  - a calendar flipping 230 years for "하루 1억원";
  - a crowd map of Korea with a "16만원" chip per person;
  - a ribbon of 5만원 notes wrapping half the globe.
  F36–F39 (comparison).
- **B24** TWIST. Binance's response room: someone slams the big "출금 중단" shutter down. Beat hold 0.5 s. Cut: crates keep leaving anyway. SFX: shutter slam, then silence, then a whoosh. Reads: "stopping didn't stop it". F07·F03.
- **B25** The clock's tail runs on to 23:56 (M1). The last crate, which had been waiting in a queue, leaves. Chip: "대부분 20분 / 끝까지 약 4시간". Reads: "precise timing". F02·F03.

### CH5 the chase, 3:11–5:26
- **B26** Response room: staff stare at the locked shutter, puzzled. Question line. Reads: "why?" F07.
- **B27** A stylized blockchain ledger wall shows a stamped "위임 권한 (EIP-7702) → 공격자 코드" entry that is already on-chain. The company's withdrawal console switches OFF, but the ledger entry stays lit, and crates keep moving through a side door. Insert: a key hanging outside the door. Reads: "the permission was already on the blockchain; switching off the company system didn't revoke it". F07.
- **B28** A pipe junction. At one branch, a stablecoin issuer pulls a freeze lever: the pipe ices over. Reads: "some coins can be frozen". F16.
- **B29** Lair 5 conveyor (재연): crates are repainted from stablecoin to ETH/BTC before the ice reaches them. The icicles cannot grip the BTC/ETH pipes. Reads: "swap before freeze; no issuer to freeze BTC/ETH". F16.
- **B30** A pipe maze that branches into a dense web, with a counter of "2만+ 지갑" and a "$124M → BTC" chip. Camera: pull out to reveal the size of the maze. Reads: "laundering spreads wide". F16 and related analysis F IDs per the script.
- **B30a** The pipe ends at an OTC counter with its shutter closed. Chip: "주소에 약 $3.11B 잔존 · 현금화 극히 적었을 수". Reads: "much is still sitting there". (Script F IDs.)
- **B31** An ice warehouse: frozen crates stacked with a "$2.85B (동결+차단 합산, 회사)" label. Cut: an empty refund counter. Reads: "frozen ≠ returned". F17·F18.
- **B32** A queue of legal papers in front of the ice warehouse. Chip: "실제 반환 최종액: 확인 자료 없음". F18.
- **B32a** Market board: BTC drops below $80k on 10/30 (correlation, not cause). Then Binance's own vault refilling the gap, with a "98% 보충 (회사, 10/31 기준)" chip and a red-stamped "≠ 도난금 회수". F23·F19·F20.
- **B32b** The withdrawal counters reopen in sequence on 11/1. A long customer queue flows out. Chip: "첫 9시간 30분 순유출 약 $3.64B (회사)". F21·F22.
- **B33** Analyst tracking room: an analyst pins two coin trails (the Bitget September crates and the Binance crates) and they mix in one pipe (TraderTraitor assessment). Reads: "evidence of a link". F14.
- **B34** FBI briefing room: a podium and agency seals, generic. An arrow from "FBI 발표 10/31" points to a "북한 책임" card. Secret Service and IRS-CI badges sit beside it. Reads: "an official attribution". F13.
- **B35** A statement paper (11/2, denial) slaps over the card. Lair 6 empties: monitors switch off one by one, hoods gone (M4 = empty). Chip: "기관의 지목 ≠ 법원의 유죄 판단". F15.

### END the question and other cases, 5:26–7:12
- **B36** Lair 6, the empty room. The quiz choices fly in: A 징역 20년 이상, B 징역 5년, C 처벌 못 함. A 3-second answer timer. F30.
- **B37–B39** Washington D.C. courtroom 1, another case: Lichtenstein (generic, non-identifiable figure), Bitfinex 2016, a 120k BTC chip.
  - Judge's sentence card: "징역 5년, 2024-11-14, 돈세탁 공모"; cooperation noted.
  - Courtroom 2: Morgan, "1년 6개월, 2024-11-18". The court separated her from the hacking.
  - The defendant reacts by lowering their head. No faces of real people.
  F24·F25·F26.
- **B40** The two courtrooms cross-fade back to the Binance clock (M1). Chip: "별개 사건 — 이번 해커 형량 아님". Reads: "don't confuse them".
- **B41–B43** Empty dock 1 (Park Jin Hyok, 2018 complaint, Sony and other separate cases) and empty dock 2 (Rim Jong Hyok, 2024-07 indictment, hospital ransomware, separate case). A wanted flyer with no photo: subtitle text only, with the amount and the issuing body. Chip: "이번 사건 가담 주장 아님". F28 and related.
- **B44** The choices reappear and C is highlighted, with the qualifier line "아직 처벌할 단계에도 오지 못했습니다" and "11/7 기준 체포·기소 확인 자료 없음". The extradition-treaty line is a chip. F30 and related. This states the hypothetical's limits; it is not a confirmed sentence.
- **B45** The closing montage of motifs: the clock (6월 → 20분), the vault door closing, the empty video-call window going dark. The last line: "형량을 매길 법정은, 아직 열리지 않았습니다." An optional loop cut to B01's corridor.

## Open fact gaps (kept as gaps)
- June → September: no causal link in facts.md. The two are shown in sequence only.
- Device ownership on 10/20, the 10/29 access window and the 00:10 revocation exist only in S01, so they are not used.
- "C" as the correct answer: facts_trace notes that the logic isn't fully sourced, hence the qualifier line in B44.
