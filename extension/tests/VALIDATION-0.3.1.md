# 확장 프로그램 v0.3.1 제출 패키지 검증

2026-11-04 KST · macOS · Playwright Chromium 148.0.7778.96 · 로그인하지 않은 새 임시 프로필

## 결과

실제 제출 파일 `pariview-webstore.zip`을 임시 폴더에 풀어 설치한 상태로 검사함
사용자의 개인 Chrome 프로필에는 확장을 설치하지 않음

- `e2e.py` 6/6 통과 — 웹 연결, 저장, 다른 페이지 적용, 초기화, 켜기/끄기, 재생 유지
- `audio_and_status.py` 16/16 통과 — 실제 디지털 신호, 상태 안내, 영상 교체, iframe, 지원하지 않는 소리, 원본 복원
- `youtube.py` 10/10 통과 — 공개 PariView에서 실제 YouTube로 저장 전달, 화면/소리 적용, SPA 이동, 복원, 초기화, 미저장 미리보기 격리
- 총 32/32 통과

## 실제 YouTube 측정

공개 앱: https://pariview-production.up.railway.app/

시작 영상: https://www.youtube.com/watch?v=R6MlUcmOul8

YouTube 추천 링크를 직접 클릭하여 다음 영상으로 SPA 이동: https://www.youtube.com/watch?v=41hv2tW5Lc4

- 저장한 밝기 60 / 대비 95 / 채도 75 / 따뜻함 20의 CSS 필터 적용
- Web Audio running · gain 0.35 · lowpass 약 8767.67 Hz · 말소리 EQ 3000 Hz +4 dB · compressor threshold −25 / ratio 5
- 실제 오디오 입력 RMS 0.0979233 / 처리 출력 RMS 0.0488442로 비무음 확인
- SPA 이동 뒤 다음 영상에도 화면과 소리 효과 적용
- 효과 끄기 뒤 입력/출력 RMS 모두 0.0820335 · 비율 1.00 · 화면 filter none
- 재생 위치 진행, 재생 속도, 플레이어 음량, 음소거 상태 유지
- 공개 앱 초기화가 실제 YouTube에 전달되어 밝기 85 / 대비 90 / gain 0.35로 복원
- 저장하지 않은 웹 미리보기는 확장과 YouTube에 전달되지 않음

440 Hz 제어 신호에서 gain 0.35의 출력/입력 RMS 비율 약 0.3500108, 효과를 끈 뒤 1.00 확인
YouTube에서 EQ와 압축을 함께 적용한 RMS 비율을 gain 값과 같다고 해석하지 않음

## 패키지

각 ZIP은 13개 파일을 포함하며 루트 저장소의 MIT LICENSE도 포함함
각 멤버를 소스와 바이트 단위로 대조했으며 테스트와 스토어 등록 자료는 패키지에서 제외함

| 파일 | 크기 | SHA-256 |
| --- | ---: | --- |
| `pariview-webstore.zip` | 20724 bytes | `5efded799b6c8a24fed772aef7ef216c4524aa3f57e67c466783154a0d4b933e` |
| `pariview-extension.zip` | 21218 bytes | `b105e2a95f821714c47eebacba707025092fe0bd81e9c694507e67f4fd989ac0` |
| `web/dist/pariview-extension.zip` | 21218 bytes | `b105e2a95f821714c47eebacba707025092fe0bd81e9c694507e67f4fd989ac0` |

제출 ZIP은 `manifest.json`이 최상위에 있으며 일반 설치 ZIP 두 개는 바이트 단위로 동일함
이 기록은 설치·기능 검증이며 Chrome Web Store 심사 통과를 뜻하지 않음

## 스토어 이미지

`extension/store/screenshot-01.png` 및 `screenshot-02.png`

- 각각 1280×800, 8-bit RGB / 24-bit PNG, 알파 없음
- 실제 YouTube 영상과 실제 확장 팝업을 같은 임시 프로필에서 캡처한 켜기/끄기 화면
- 영상: Big Buck Bunny © Blender Foundation, CC BY 3.0 · 화면 안 출처 표기
- 비교용 배치를 명시했으며 미구현 기능을 합성하지 않음

## 확인하지 않은 범위

- 사람의 귀로 듣는 청취 평가와 체감 편안함 평가
- Windows 기기에서의 직접 실행과 개인 Chrome 프로필 설치
- 실제 유료 DRM 영상 — encrypted 이벤트의 비연결/새로고침 안내는 로컬 fixture로 검사
- 모든 YouTube 광고, Shorts, 라이브 및 다른 웹사이트의 전수 검사

실제 콘솔의 등록·심사 상태는 [스토어 등록 기록](../store/LISTING.md)에서 따로 관리함
