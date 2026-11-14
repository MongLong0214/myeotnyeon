# LF3 바이낸스 — 하이스트 장면표 v2 (scene_heist.md)

Matches script_heist.md v2. v1 is kept as scene_heist_v1.md. Owner direction: concrete, cinematic intrusion staging. CEO correction applied (msg_b9fc85fa).

## Common rules
- **재연 marks staging.** Every 재연 scene shows a small "재연" tag at the bottom-left. 재연 is not a license to invent facts.
  - No invented hacker dialogue, psychology, team roles, persistence, escape or "success" beyond the sources.
- **Hackers.** An anonymous presence: a hooded silhouette, the face in shadow with two eye glints and a mouth line (H7). One generic lair set.
  - The lair does NOT grow across chapters. No accumulating monitors or boards suggest one team running a continuous op since June.
  - The lair appears only at the reported action moments: 6월 install, 9월 interviews and assignment, 10/20, 10/29.
- **Employees.** Engineer 1 and Engineer 2 are generic and non-identifiable. They are victims and never played for laughs.
- **Intrusion staging: concrete at report level.** Use stylized UI throughout: progress bars, chat bubbles, video tiles, terminal windows with blurred lines, and status lights.
  - No real code, commands or exploit internals.
  - No invented on-screen paths: in particular, no cursor jumping between machines, and no AI chat executing an intrusion.
  - Metaphor inserts (vault door, keys) sit only on top of reported actions.
- **Time labels.** COLD shows KST once, labelled "KST". Every D-day clock shows "UTC".
- **Editing.** Cut on cause → result (click → result, discovery → response). The viewer must have time to read each change. There is no fixed cut rate.
- **Motifs:**
  - M1, the clock (labelled UTC or KST);
  - M2, the video-call window;
  - M3, the signing-service vault door.

## Shots (line IDs → shot / action → change / camera / reads / F)

### COLD
- **H001–H002**
  - Shot: the hot-wallet vault corridor at night. Coin crates slide out through the exit.
  - Clock: "KST 10/30 05:05".
  - Camera: a fast dolly following the crates.
  - Reads: "something huge is draining". F01·F02.
- **H003–H004**
  - Shot: an amount counter spins to "$6.3B ≈ 8조4000억원", then a ring timer fills, labelled "탈취금 대부분이 움직인 약 20분 — TRM 분석".
  - Reads: "a lot, fast". F04·F05·F02.
- **H005**
  - Shot: a silhouette in a doorway, glints only (재연), and the question text.
  - Then the rewind card: the calendar flips back and lands on "그해 6월".
  - Reads: "who, and what happened to them?" F30.

### CH1 그해 6월
- **H006–H007** Engineer 1 downloads an "AI 코딩 도구" installer. Insert: the installer icon carries a tiny hidden hook. The install wizard's progress bar fills. Reads: "a tampered package". F08.
- **H009** A dark lair monitor lights faintly with no details (재연). Chip: "이름·얼굴·역할 비공개". F31.
- **H010–H011** The security team arrives, swaps the laptop and resets the badge. Engineer 1 exhales. Hold 0.5 s. Reads: "seems handled". F08.
- **H012–H013**
  - Shot: a sheet labelled "직무·동료 정보" fades onto the dark monitor (company claim).
  - Chip: "기기에 계속 붙어 있었다는 증거 없음".
  - Reads: "information was exposed; persistence is not shown". F08.

### CH2 9월
- **H014–H015** Engineer 2 at home. A job-platform message arrives from a "프로젝트 책임자". The calendar shows September. Engineer 2 leans in. F09.
- **H016–H017**
  - Shot: video-call window (M2) with a friendly interviewer tile. A phone scrolls an SNS profile with photos and videos.
  - Caption: "첫 화상 면접".
  - Confirmed order (S01): "1차 — 인사 담당자, 화상 면접 (SNS 신뢰)" in the video window, then "2차 — 대표, 채팅 앱" as a chat-app window, not video. No simultaneous three-tile meeting.
  - Reads: "trust is built step by step". F09.
- **H019**
  - TWIST: the three tiles (책임자, 인사 담당자, 대표) peel off like masks, one after another, onto three hooks in the lair (재연 metaphor).
  - SFX: three clicks.
  - Reads: "all fake". F09.
- **H020–H021**
  - Shot: the 2nd-round chat-app interview ends with a chat bubble carrying the "과제 저장소" link.
  - On the WORK laptop (company sticker), Engineer 2 clicks it. The download bar fills and a folder appears.
  - Camera: OTS, then an insert on the cursor. F10.
- **H022–H023** A terminal window opens for setup (lines blurred) and the install bar runs. Insert: the endpoint-protection tray icon stays green and silent. The lair monitor shows "연결됨" (재연). Reads: "malware ran on install; it wasn't caught". F10.
- **H024** Engineer 2 working earnestly, shown with sympathy. F10.

### CH3 10월 20일
- **H025a** A company corridor at night. The calendar jumps from September to "10월 20일". Chip: "그 사이 움직임 — 확인 자료 없음". F31.
- **H025–H026**
  - Shot: an office floor map. Starting from the infected laptop's desk, the desks of other wallet developers turn red one by one. This shows access scope widening (company claim).
  - A side panel shows a "내부 AI 도구" icon labelled "발판" only, with no chat activity and no cursor paths.
  - Reads: "control spread to other wallet developers' systems". F11.
- **H028** The AI-tool icon sits under a "?" spotlight. Chip: "작동 방식 비공개 · AI가 스스로 훔친 것 아님". F11·F31.

### CH4 10월 29일 (UTC)
- **H030** Clock M1: "UTC 10/29". The lair monitor wakes (재연). F01.
- **H031** Split screen: Developer A's computer (an empty desk, screen lit) and a login card in Developer B's name filled with stolen credentials. Both are used together. Insert: two key cards side by side, not fused. Reads: "one person's computer plus another's stolen credentials". F12, company claim.
- **H032** A stylized "컨테이너" box spins up and a script window opens (blurred). A route line on the network map ends at the "내부 지갑 서명 서비스" node (M3), which turns red. F12·F06.
- **H034–H035** TWIST. Inside the signing service: transaction slips arrive from a side chute, not from the "출금 요청" counter, and the signer stamps them VALID. Insert: the vault door (M3) swings open. Chip: "유효 서명 악용 경로: Elliptic 분석". F06.
- **H036–H037** Clock M1: "UTC 20:05". The B01 corridor returns, now seen from inside the vault: the first XRP crate leaves, through to "UTC 20:09". F01·F03.
- **H038–H039** Four chain pipes pour, a ring timer runs labelled "탈취금 대부분이 움직인 약 20분 — TRM 분석", and a chip reads "체인 10개". A big number pops: "1초에 약 70억원". F02·F04·F40.
- **H040** The response room: the "출금 중단" shutter slams down. Hold 0.5 s. F07.
- **H042–H043** Clock M1: "UTC 23:56". One last crate leaves from a "대기 중" queue that was already filled before; the queue sign reads "앞서 보낸 거래". No new crates are created. Chip: "첫 이체 후 약 4시간". F03.

### CH5
- **H045–H047**
  - Shot: the response room stares at the closed shutter.
  - Cut to a stylized blockchain ledger wall with an entry "위임 권한 (EIP-7702) → 공격자 코드" already written on-chain. The company console switches OFF, but the ledger entry stays lit.
  - This is shown separately from the H043 queue.
  - Reads: "the permission lived on the chain; turning off the company system alone didn't remove it". F07.
- **H049–H052**
  - Shot: analysts at tracking screens (Chainalysis and Elliptic generic badges).
  - At a pipe junction a stablecoin issuer pulls a freeze lever and that pipe ices over.
  - On another screen a trail shows stablecoin → ETH conversions. The BTC and ETH pipes carry no issuer lever.
  - No race and no "escape before the freeze".
  - F16.
- **H055–H057** An ice warehouse with a "$2.85B (동결+차단 합산, 회사)" label. Cut to an empty refund counter with a queue of legal papers. Reads: "frozen ≠ returned". F17·F18.
- **H058b–H058c** Binance's own vault pours funds into the user-balance tank, with a "98% 보충 (회사, 10/31 기준)" chip, then a red stamp: "≠ 도난금 회수". F19.
- **H059–H060a** An analyst pins two coin trails, the Bitget September trail and this one, and they merge in one pipe. Chip: "체이널리시스 평가". F14.
- **H061** An FBI briefing podium (generic). The "북한 · TraderTraitor" card appears with a "FBI 발표 10/31" label. F13.
- **H062–H063** A statement paper reading "11/2 부인" lands beside the card. Chip: "기관의 지목 ≠ 법원의 유죄 판단". The lair is not shown: no evacuation, no escape. F15·F13·F14.

### END
- **H064** The empty courtroom, lights off, the dock empty. The question text. F30.
- **H082–H082a** A docket board with three slots, 체포 · 재판 · 선고, all showing "— 확인한 공개 자료에서 기록 미확인" and the date chip "2026-11-07 기준"; the empty courtroom carries a "개념 이미지" tag. F30.
- **H083** A map showing the US and North Korea with an "인도조약 없음" line. Chip: "≠ 영원히 처벌 불가". F41.
- **H084–H085** The closing motifs: the calendar "그해 6월", the ring "탈취금 대부분이 움직인 약 20분 — TRM 분석", then the vault door closing and the empty "선고" slot. The last line. F02·F08·F30.

## v1 → v2 changes
- The lair no longer grows.
- The interviews are separate sessions; there is no three-tile simultaneous meeting.
- B16's cursor and AI-chat path is removed; it is now a scope map.
- The pending transaction (H043) and the delegation (H047) are split.
- The conversion race and the lair evacuation are removed.
- The quiz, the C answer timer, and the other-case courtrooms and wanted flyers are removed.
- UTC and KST labels were added, and the fixed cut-rate rule was removed.
