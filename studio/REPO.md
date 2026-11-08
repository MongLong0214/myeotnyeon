# 로컬 제작 저장소

이 폴더의 `main` 브랜치에서 제작 코드와 기록을 관리한다. 원격 저장소는 없으며 push하지 않는다. 기존 파일은 수정·이동·삭제하지 않고 최초 상태 그대로 등록했다.

추적 대상은 `factory`·`tts`·`tts_lab`의 도구, `production`의 제작 소스, `episodes`·`research`·`references`의 대본·팩트·조사 기록, `upload`·`channel`의 메타데이터·원장, 최상위 결정·상태 문서다. `.gitignore`는 코드·텍스트·설정 확장자만 허용하며, 각 파일은 UTF-8 텍스트이고 1,000,000바이트 이하여야 한다.

별도 저장소 `research/tools/stickman-video-director/`·`tts_lab/engines/melotts/src/`와 실행 중인 전체 영상 작성기의 `production/lf_toon/`, `episodes/review_full/`는 통째로 제외한다. 해당 파일·브랜치·인덱스는 건드리지 않으며 스테이징·커밋하지 않는다.

미디어·모델·압축파일 등 바이너리, 의존성·가상환경, 캐시·모델 폴더, 임시·백업 폴더, 번들·렌더 결과 및 `review_runs/**/images`는 제외한다. `render_`로 시작하는 실행 소스는 추적할 수 있고 같은 접두사의 결과 디렉터리·데이터는 제외한다. 비밀정보·개인정보 검사에 걸린 파일은 내용 수정 없이 파일 전체를 제외한다. Naver 키와 `.env` 등 자격정보 파일은 계속 로컬에 둔다.

변경은 영역별로 등록한다. 먼저 아래 검사를 실행하면 패턴(API 키·토큰·쿠키·암호·개인키·이메일·전화번호)과 엔트로피로 검사하고, 발견 파일·대용량·바이너리를 `.gitignore`에 추가한다. 오탐 후보도 자동으로 다시 허용하지 않는다.

```sh
python3 repo_check.py screen
git add -- <검토한 파일 경로들>
git diff --cached --stat
git commit -m "area: summary"
```

영역은 `factory`, `production`, `episodes`, `upload`, `docs`를 쓴다. 로컬 pre-commit 훅이 실제 스테이징된 내용을 검사하며, 전체 추적 대상 검사는 `python3 repo_check.py check`로 실행한다. 강제 추가(`git add -f`)는 사용하지 않는다.

검사 상세는 `.git/repo-screen-report.json`, **발견 파일명만** 담은 목록은 `.git/secret-screen-hits.txt`, 최종 집계·커밋 목록은 `.git/repository-report.md`에 있다. 검사 결과의 개별 제외 경로는 `.gitignore`를 통해 이력에 남는다. 보고서는 원문이나 비밀 값을 저장하지 않는다.

CommitLore는 `commitlore init --mcp-scope none`으로 설정했다. `commitlore doctor` 로그는 `.git/commitlore-doctor.log`에 있다. init·doctor는 성공했으며 원격 미설정, 기존 MCP 중복 경로·실행 버전 차이 경고가 있었다. 결정 근거는 관련 문서와 같은 커밋에 남기고, CommitLore 캡처를 지원하는 도구에서는 세션 근거로 prepare → verify → stage 후 커밋한다. 비밀 값은 메시지·결정 기록에도 적지 않는다.
