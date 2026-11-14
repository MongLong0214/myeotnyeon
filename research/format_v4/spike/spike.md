# 몇년나옴 v4 렌더 경로 스파이크

2026-10-26 · Apple M4 Pro, 12스레드, 48GiB · React 18.3.1 / Remotion 4.0.538.
공통: 얼굴 없는 지휘관·정지 표식 6명, 파랑 공간광·빨강 림(강도 ≤0.6), 수치·날짜·자막·제목, 그레인·비네트. 2.5초간 6% 전진 후 0.5초 유지.
A: ThreeCanvas 캡슐·실제 원근·프레넬 림·Bloom·듀오톤 Effect 구현. 입체 표면은 보이나 분절된 마네킹과 약한 빨강 림이 게임처럼 보일 위험.
B: SVG 투시·실루엣·오프셋 블러 림·feColorMatrix/feComponentTransfer·프레임별 feTurbulence 구현. 림이 또렷하나 평면 일러스트 인상이 강함.

| 경로·조건 | 프레임 | 렌더 구간(s) | ms/프레임 | 명령 전체(s) |
|---|---:|---:|---:|---:|
| A · concurrency 1 | 75 | 19.488 | 259.84 | 21.684 |
| B · concurrency 1 | 75 | 20.226 | 269.68 | 22.625 |
| A · 기본값 6 | 75 | 21.446 | 285.95 | 23.265 |
| B · 기본값 6 | 75 | 3.947 | 52.63 | 37.731 |
| A · 납품 클립, 1 | 90 | 28.930 | 321.44 | 31.251 |
| B · 납품 클립, 1 | 90 | 25.683 | 285.37 | 28.142 |
시간은 CLI 로그의 `Rendering frames done in` ÷ 프레임 수. 명령 전체에는 번들·브라우저·인코딩·정리가 포함됨([원시 로그/수치](logs/metrics.json)).
기존 gl=angle 유지. Mac 권한/IOSurface 오류 때문에 스파이크 전용 래퍼로 단일 프로세스·ANGLE SwiftShader·소프트웨어 합성을 사용함. 하드웨어 GPU 결과가 아님.
단회 측정이라 캐시·시스템 부하·시작 지연에 민감함. 특히 B 기본값은 전체 37.7초 중 프레임 렌더가 3.95초임.
최대 메모리: 로그에 미노출. sysctl 권한 거부로 표시된 available memory는 여유 메모리이며 피크 사용량이 아님.
39초(1,170프레임) 단순 외삽, 렌더 구간만: concurrency 1 A 약5.1분/B 약5.3분, 기본값 A 약5.6분/B 약1.0분. 전체 제작시간 보장은 아님.
납품: [A.png](A.png)·[B.png](B.png) 1080×1920, [A.mp4](A.mp4)·[B.mp4](B.mp4) H.264/BT.709/30fps/90프레임/정확히3초, 무음.
폰: [A-phone.png](A-phone.png)·[B-phone.png](B-phone.png) 393×698에서 자막·수치·역할을 눈으로 읽음. 실제 휴대폰 실기기 평가는 미수행.
폰트 CSS: 자막62px, 측정50px, 역할·날짜·보조문구46px. 69번 프레임 실제 채움 픽셀 높이: 55/45/41/41/41px, 모두40px 이상([픽셀 측정](logs/qa.json)).
글자 박스는 전 구간 x≥130, y≥210·끝≤1458; y>900인 글자는 x≤870. 채널운영 §4의 좌우·상하·버튼 가림 영역을 피함.
실제 PNG 배경 픽셀 대비: 자막≥17.27:1, 수치≥13.52:1, 역할≥17.21:1. 40번 프레임 독립 재렌더 A/B 모두 차이0픽셀.
압축: qa/*-8Mbps.mp4(H.264 목표8Mbps), *-8Mbps-f69.png. 원본 클립 대비 PSNR A54.61/B61.55dB; 69번 화면에서 추가 밴딩·빨강 번짐은 두드러지지 않음. A의 미세 그레인은 첫 인코딩부터 약해짐.
16:9: [A-landscape.png](A-landscape.png)·[B-landscape.png](B-landscape.png), 1920×1080. 별도 카메라·FOV·카드 좌표로 재구도, 크롭 아님. 여섯 표식이 모두 보임.
룩 미달: 지휘관 몸통 ROI(80,880–185,1030)의 평균 선형 휘도 A0.0275/B0.0134로 §4.3의0.35 하한 미달. 본편 전 피사체 노출 조정 필요.
제목 강조색은 스펙의 #FF3B4E를 유지했으나 잉크 바탕 대비 약5.74:1로7:1 미달. 자막·측정·역할과 별도로 밝은 빨강 재조정 필요.
새 의존성(정확 버전): @remotion/three 4.0.538 MIT, three 0.186.1 MIT, @react-three/fiber 8.18.0 MIT, postprocessing 6.39.5 Zlib. 각각 `npm view PACKAGE license` 확인([기록](logs/licenses.log)); B 추가0개.
기존 OFL Pretendard만 사용. 새 폰트·외부 이미지·모델 없음. MPFB/GLB는 외부 모델 금지에 따라 제외하고 코드 캡슐로 한정. React postprocessing 래퍼·transitions 미사용.
회귀: 기존52개 컴포지션 메타데이터 동일, 추가 ID는 V4SPIKE-A/B뿐. COVER-Q012 변경 전후 차이0픽셀. Quiz/fonts/theme/렌더 설정 원본 해시 유지, Root는 import·등록만 추가. tsc 통과.
비용: 작업 약25분, 신규 코드334줄(장면 A115/B56줄 포함), 유료 도구·자산0원. 측정 로그와 패키지 잠금파일을 함께 보존함.
추천: B. 림과 역할이 더 빨리 읽히고 추가 의존성이 없으며 기본6동시성의 렌더 구간이 짧음. 1동시성은 동급이며 밝기 미달을 해결한 뒤 본편에 적용하는 편이 좋음.
오너 선택은 아직 없음. [X/Y 무작위 폰 비교표](comparison-phone.png)에 0.2/1.2/2.3초를 배치했고 키는 logs/blind-key.json에 보관. 실기기 룩 선택이 추천보다 우선함.
재현(work 디렉터리): `python3 production/compositor/src/v4spike/render_spike.py` — 모든 CLI 호출에 `npx --no-install` 사용, 로그에 전체 명령 보존.
API 참고: [Remotion ThreeCanvas](https://www.remotion.dev/docs/three-canvas), [postprocessing EffectComposer](https://pmndrs.github.io/postprocessing/public/docs/class/src/core/EffectComposer.js~EffectComposer.html).
