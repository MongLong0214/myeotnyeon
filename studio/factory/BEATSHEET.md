<!--
MIT License

Copyright (c) 2026 Mr omi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
-->
# 법정 사건 숏츠 비트시트

`claude-animated-shorts/templates/SCRIPT_example.md`의 비트 순서만 각색한다.
사건·인물·대사·그림은 우리의 사실표와 독창 캐릭터로 만든다.
기준은 [REVIEW_CHECKLIST.md H](REVIEW_CHECKLIST.md#h-원일-11-06-추가-지적-전부-불합격-조건이다-하나라도-걸리면-ceo와-원일에게-보내지-않는다)와
[STYLE_VIDEO.md](unslop/STYLE_VIDEO.md)다. 이 문서는 새 승인 절차가 아니다.

| 비트 | 작성할 내용 | 화면·연기 | H 연결 |
|---|---|---|---|
| Hook — 행위 | `[확인된 행위]를 한 피고인. 몇 년 받았을까?` 숫자 정답은 숨긴다. | **0초부터 행위 재현**. 제목·배지 오프닝 없이 카툰 행동으로 시작한다. 피해자 사망·부상은 웃음 소재로 삼지 않는다. | H2·H4·H7·H8 |
| Setup — 사건 맥락 | 누가 어떤 관계에서 무엇을 했는지, 이해에 필요한 사실만 쓴다. | 장소를 먼저 읽히게 하고 행위자→반응으로 바꾼다. 모든 얼굴에 눈·코·입, 실존 인물과 닮지 않는 디자인. | H2·H7 |
| Escalation — 증거와 대립 | `[증거] → [피고인 주장] → [그 주장과 충돌하는 확인 사실]`. 주장과 법원 판단을 구분한다. | 증거 몽타주, 피고인·재판부의 반응 교환. 같은 구도 정지 1.5초 초과 금지. 의미 없는 흔들기로 때우지 않는다. | H2·H6 |
| Snap — 쟁점 반전 | 형량을 밝히기 전에, 사건의 해석을 바꾸는 **확인된 쟁점** 한 줄. 반전이 없으면 꾸며내지 않는다. | 행동 절정에서 반응으로 smash cut → 2–4프레임 snap zoom → 짧은 deadpan. 표정·판단이 실제로 달라져야 한다. | H2·H6 |
| Analogy — 이해 보조 | `[사실표에서 확인한 판단 이유]`를 일상 비유 한 문장으로 설명한다. 비유는 증거·법률 인용으로 취급하지 않는다. | 독창 소품·배우 행동으로 보여준다. 설명 카드·메타 라벨·고지 자막을 덧붙이지 않는다. 피해자를 희화화하지 않는다. | H4·H6·H9 |
| Consequence — 선택과 선고 | A/B/C 선택 → 고를 시간 **2초 이상** → **마지막 구간에서만 정답**. `[심급/법원 판단] 선고 [확인 형량]`. 구형과 선고를 명확히 구별한다. | 큰 유색 선택지가 각각 다른 박자·소리·포즈로 등장. H10의 선택 카드는 허용하고 H4의 장식 카드와 구분한다. 선택 중 반응을 이어가며 정답 때 정답만 강조, 나머지는 흐리게. 판결은 망치·저울·배우 반응과 함께 떨어진다. | H2·H4·H6·H10 |
| Callback — 첫 행위 재해석 | 첫 행동/소품을 판결의 의미와 연결하는 한 줄. 피해자·죽음 대신 피고인의 태도나 제도적 모순에 초점을 둔다. | 마지막 판결 구간 안에서 첫 구도의 의미를 뒤집는다. 3D 엔딩·템플릿 CTA·정답보다 앞선 형량 노출 없음. | H2·H4·H8 |

원본의 snap을 그대로 ‘중간 판결 공개’로 옮기면 H2와 충돌한다.
여기서는 **snap=쟁점 반전**, **consequence=마지막 선고 공개**로 쓴다.
비트를 억지로 같은 길이로 나누지 말고 단어 타임스탬프에 행동과 컷을 맞춘다.
화면 변화는 H2의 1.5–2초 리듬을 따르되, 법정은 H6의 1.5초 정지 제한을 지킨다.

소재는 H3의 `research/topic_scores/RANKED.md` 상위와 YouTube·네이버 수요 근거를 먼저 확인한다.
대본 사실은 기존 사실표에 연결하며 비유로 사실을 만들어내지 않는다.
자막은 H5대로 가로 중앙, 숏츠 64px 이상(현행 72), 굵기 800, 외곽선 8px 이상,
최대 2줄·줄당 14자 이하. 구형/선고 구분은 남기고 화면 고지는 설명란으로 보낸다(H9).

H1·H11·H12는 보고·삭제·권한에 관한 운영 규칙이며 비트로 바꾸지 않는다.
H13대로 새 연출은 한 편에서 먼저 확인하고 전체 30fps 시트로 이탈 구간을 본다.
[프레임 QA](lib/frame_qa.py)는 보조 진단이며 흥미·사실성·H 규칙 통과를 대신 증명하지 않는다.
