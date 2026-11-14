"""Build delivery narration WAVs from the locked source snapshot, offline only."""
import hashlib
import json
import os
import shutil
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
import numpy as np
import soundfile as sf
from supertonic import TTS

ROOT = Path("/Users/isaac/projects/verdict-kr/work")
OUT = ROOT / "production/astra_12min/audio_edit"
SOURCE = ROOT / "production/astra_preserved/active_full_narration_source.json"
LF_CUES = ROOT / "episodes/lf2_daejeon_bank/astra_12min/lf2_full_cues.json"
N18_CUES = ROOT / "episodes/v4/n18/astra_12min/n18_full_cues.json"
SR = 44100
GAP_SECONDS = 0.17

# Cut duplicated production caveats from N18 while retaining the factual chronology,
# medical/safety boundary, trial holdings, and final outcome.
N18_DELETE = set("""
T02_04 T02_05
T04_04 T04_05 T04_06
T05_03 T05_04 T05_05
T06_03 T06_04 T06_05 T06_06
T07_03 T07_04 T07_05
T08_03 T08_04
T09_03 T09_04 T09_05
T10_03 T10_04
T11_03 T11_04 T11_05 T11_06
T12_04 T12_05
T16_01 T16_02 T16_03 T16_04 T16_05 T16_06
T17_04
""".split())

LF2_ADDITIONS = [
    {
        "id": "LF2_NEW_01",
        "after": "L11_06",
        "text": "두 DNA가 일치했다는 것은, 두 장소의 흔적이 같은 사람에게서 나왔다는 뜻입니다.",
        "facts": ["F21"],
        "source": "lf2 facts.md F21",
        "reason": "DNA 일치의 의미를 수사 단계에 한정해 설명",
    },
    {
        "id": "LF2_NEW_02",
        "after": "L11_06",
        "text": "그 비교는 범행 차량 안에 남은 마스크와 손수건에서 시작됐습니다.",
        "facts": ["F18", "F21"],
        "source": "lf2 facts.md F18, F21",
        "reason": "현장 증거와 비교 자료의 연결을 명시",
    },
    {
        "id": "LF2_NEW_03",
        "after": "L11_06",
        "text": "하지만 DNA 비교만으로 범행 당시 누가 어떤 역할을 했는지까지 바로 정해지지는 않습니다.",
        "facts": ["F18", "F37"],
        "source": "lf2 facts.md F18, F37",
        "reason": "동일성 증거와 법정의 역할 판단을 구분",
    },
    {
        "id": "LF2_NEW_04",
        "after": "L11_06",
        "text": "그래서 수사팀은 게임장 출입 가능성, 몽타주, 차량 절도 수법도 함께 대조했습니다.",
        "facts": ["F23", "F24"],
        "source": "lf2 facts.md F23, F24",
        "reason": "보강수사의 근거 결속",
    },
    {
        "id": "LF2_NEW_05",
        "after": "L11_06",
        "text": "비가 특정된 뒤에도 과거 행적과 주변인을 확인하는 보강수사가 이어졌습니다.",
        "facts": ["F23", "F24"],
        "source": "lf2 facts.md F23, F24",
        "reason": "특정 뒤 검증 단계를 명시",
    },
    {
        "id": "LF2_NEW_06",
        "after": "L11_06",
        "text": "그 확인이 끝난 뒤 검거와 진술, 그리고 별도의 법정 판단이 이어집니다.",
        "facts": ["F25", "F37"],
        "source": "lf2 facts.md F25, F37",
        "reason": "수사·진술·법정 판단의 단계 구분",
    },
    {
        "id": "LF2_NEW_07",
        "after": "L11_06",
        "text": "이 연결은 이름을 찾는 수사의 경로이고, 총격 책임을 곧바로 결론낸 증거는 아닙니다.",
        "facts": ["F18", "F21", "F37"],
        "source": "lf2 facts.md F18, F21, F37",
        "reason": "DNA 특정과 발사자 판단의 비약 방지",
    },
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synth_new(items):
    pending = [x for x in items if x.get("new")]
    if not pending:
        return
    tts = TTS(model_dir="/Users/isaac/.cache/supertonic3", auto_download=False,
              intra_op_num_threads=2, inter_op_num_threads=1)
    assert tts.sample_rate == SR
    style = tts.get_voice_style(voice_name="M1")
    for item in pending:
        a, _ = tts.synthesize(item["text"], voice_style=style, lang="ko", speed=1.1, total_steps=16)
        a = np.asarray(a).reshape(-1)
        nz = np.flatnonzero(np.abs(a) > .001)
        if len(nz):
            a = a[max(0, nz[0] - int(.05 * SR)):min(len(a), nz[-1] + int(.12 * SR))]
        sf.write(item["audio"], a, SR)


def build(name, source_clip, source_cues, additions=None, deleted=None):
    additions = additions or []
    deleted = deleted or set()
    source_by_id = {x["id"]: x for x in source_clip["items"]}
    cue_by_id = {x["id"]: x for x in source_cues["cues"]}
    if set(source_by_id) != set(cue_by_id):
        raise RuntimeError(f"{name}: snapshot/cue id mismatch")
    segdir = OUT / f"{name}_segments"
    segdir.mkdir(parents=True, exist_ok=True)
    selected = []
    edits = []
    for item in source_clip["items"]:
        if item["id"] in deleted:
            edits.append({"original_id": item["id"], "action": "delete", "original_text": item["text"],
                          "reason": "반복되는 제작 메타 설명·시각화 주의문을 삭제하고 사건 경과와 판결 이유를 중심으로 압축",
                          "fact_source": item["facts"]})
            continue
        cue = cue_by_id[item["id"]]
        if item["text"].encode("utf-8") != cue["text"].encode("utf-8"):
            raise RuntimeError(f"{name}: text byte mismatch: {item['id']}")
        src_audio = Path(cue["audio"])
        if not src_audio.exists():
            raise FileNotFoundError(src_audio)
        dst_audio = segdir / src_audio.name
        shutil.copy2(src_audio, dst_audio)
        selected.append({**item, "audio": dst_audio, "new": False})
        edits.append({"original_id": item["id"], "action": "keep", "original_text": item["text"],
                      "edited_text": item["text"], "reason": "원문 UTF-8 바이트 일치 확인 후 기존 음성 재사용",
                      "fact_source": item["facts"]})
        for add in additions:
            if add["after"] == item["id"]:
                a = {"id": add["id"], "text": add["text"], "facts": add["facts"],
                     "paragraph": "L11A", "audio": segdir / f"{add['id']}.wav", "new": True}
                selected.append(a)
                edits.append({"original_id": None, "action": "add", "edited_id": add["id"],
                              "edited_text": add["text"], "reason": add["reason"], "fact_source": add["source"]})
    synth_new(selected)
    audio_parts, cues, script_lines = [], [], []
    cursor = 0
    for index, item in enumerate(selected):
        a, sr = sf.read(item["audio"])
        if sr != SR:
            raise RuntimeError(f"{item['audio']}: {sr} Hz")
        a = np.asarray(a).reshape(-1)
        start, end = cursor / SR, (cursor + len(a)) / SR
        audio_parts.append(a)
        cues.append({"id": item["id"], "text": item["text"], "facts": item["facts"],
                     "paragraph": item["paragraph"], "start": start, "end": end,
                     "audio": str(item["audio"]), "sha256": sha(item["audio"]),
                     "reused_after_utf8_byte_check": not item["new"]})
        script_lines.append(f"[{start:08.3f}–{end:08.3f}] {item['id']} | {item['text']} | 출처: {', '.join(item['facts'])}")
        cursor += len(a)
        if index != len(selected) - 1:
            audio_parts.append(np.zeros(round(SR * GAP_SECONDS), dtype=np.float64))
            cursor += round(SR * GAP_SECONDS)
    final = OUT / ("LF2_narration.wav" if name == "lf2" else "N18_narration.wav")
    sf.write(final, np.concatenate(audio_parts), SR)
    cue_doc = {"episode": source_clip["episode"], "source_snapshot": str(SOURCE), "engine": "local Supertonic 3 M1",
               "offline": True, "sample_rate": SR, "speed": 1.1, "boundary_gap_seconds": GAP_SECONDS,
               "duration": cursor / SR, "transition_headroom": "문장 사이 0.17초 경계만 포함. 정확 720초 A/V 편집용 장면 전환 여유는 별도 편집에서 배정.",
               "cues": cues, "final_wav": str(final), "final_wav_sha256": sha(final)}
    (OUT / f"{name}_cues.json").write_text(json.dumps(cue_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / f"{name}_script.txt").write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    return edits, cue_doc


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    lf = json.loads(LF_CUES.read_text(encoding="utf-8"))
    n18 = json.loads(N18_CUES.read_text(encoding="utf-8"))
    lf_edits, lf_doc = build("lf2", source["lf2_full"], lf, additions=LF2_ADDITIONS)
    n18_edits, n18_doc = build("n18", source["n18_full"], n18, deleted=N18_DELETE)
    all_edits = {"source_snapshot": str(SOURCE), "lf2": lf_edits, "n18": n18_edits,
                 "summary": {"lf2_duration": lf_doc["duration"], "n18_duration": n18_doc["duration"],
                             "lf2_items": len(lf_doc["cues"]), "n18_items": len(n18_doc["cues"]),
                             "n18_deleted": len(N18_DELETE)}}
    (OUT / "edits.json").write_text(json.dumps(all_edits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(all_edits["summary"], ensure_ascii=False))

if __name__ == "__main__":
    main()
