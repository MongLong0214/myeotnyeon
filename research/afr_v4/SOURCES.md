# 확인한 1차 자료와 적용 범위

확인일: 2026-11-09. 문서/코드는 읽었으나 원작을 이 환경에서 재렌더하지 못했다.

1. https://github.com/seeconever/todai
   - 공개 README/소스 구조/실제 수정 이력. 기존 캐릭터와 look kit 사용.
   - 고정 커밋: c9bd1b883bcda247962a4f79cca49fe627e6f3ab.
   - 원작의 성능 수치를 새 패키지의 속도로 인용하지 않음.
2. https://github.com/seeconever/todai/blob/c9bd1b883bcda247962a4f79cca49fe627e6f3ab/src/anime.js
   - createAnimeRenderer, createRig, toonMaterial, paintMaterial, outlineMaterial, AnimePost의 실제 API를 확인.
   - 셀/배경 마스크, 배경 회화 필터, 광선, bloom, grade, 자체 sRGB 변환.
3. https://github.com/seeconever/todai/blob/c9bd1b883bcda247962a4f79cca49fe627e6f3ab/src/todai.js
   - window.renderFrame(time,{fmt}), window.ready, window.__info의 인터페이스 확인.
   - 원작의 캐릭터/영화는 벤치마크에만 사용. 신작 모듈과 구분.
4. https://studio.blender.org/tools/pipeline-overview/pre-production/editorial
   - 보드/레이아웃/애니메이션/최종 렌더가 같은 편집본에서 발전하는 실무 구조.
5. https://studio.blender.org/blog/charge-previsualization/
   - 편집 중심의 previs/animatic. 공정 결과가 전체 영화에서 읽혀야 함.
6. https://threejs.org/manual/en/color-management.html
   - 선형 작업 공간과 sRGB 출력 구분, custom shader의 변환 책임. 원본 grade 뒤에 추가 tone-map을 하지 않음.
7. https://threejs.org/docs/pages/AnimationMixer
   - 향후 glTF clip 사용 시 absolute setTime 지원. 현재 코드가 임의 skeletal rig를 지원한다는 증거로 쓰지 않음.
8. https://playwright.dev/docs/browsers
   - 브라우저 실행/설치와 버전 호환성. 설치되지 않은 브라우저가 있다고 가정하지 않음.
9. https://huggingface.co/hexgrad/Kokoro-82M
   - 로컬 TTS 사용 예, Apache-2.0 표기. 이번 환경에서 가중치 다운로드/음성 생성은 미실행.
10. https://ffmpeg.org/ffmpeg-filters.html
   - 실제 인코딩과 오디오 시간 배치. 사용 환경 기능을 확인해야 함.

공식 기능 설명, 셰이더 코드 확인, unit test, 실제 렌더 결과, 인간의 미적 판단은 서로 다른 증거다. 하나를 다른 것으로 바꾸어 말하지 않는다.
