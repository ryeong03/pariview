# 확장 프로그램 v0.3.0 검증 기록

2026-11-04 KST · macOS · Playwright Chromium 148.0.7778.96 · 로그인하지 않은 임시 프로필

## 결과

- 기존 웹 연결·저장·다른 페이지 적용·초기화·켜기/끄기·재생 유지 6/6 통과
- 실제 Web Audio 신호·상태·영상 요소 교체·iframe·미지원 소리·원본 복원 16/16 통과
- 공개 PariView → 실제 YouTube 저장·필터·소리·SPA 이동·복원·초기화·미저장 미리보기 격리 10/10 통과
- 최종 ZIP을 새 폴더에 풀어 설치한 상태에서도 오디오·상태 16/16 재검증 통과
- 웹과 확장 normalize 기본값·범위·불리언·잘못된 입력 호환 확인
- JS 문법 검사와 git diff 공백 오류 검사 통과

## 실제 유튜브 확인

공개 앱: https://pariview-production.up.railway.app/

시작 영상: https://www.youtube.com/watch?v=R6MlUcmOul8

YouTube의 실제 추천 링크를 클릭해 다음 영상으로 SPA 이동: https://www.youtube.com/watch?v=41hv2tW5Lc4

- 웹 저장 버튼으로 밝기 60 · 대비 95 · 채도 75 · 따뜻함 20 · 음량 35 · 높은 소리 완화 45 · 말소리 강조 켜짐 전달
- 필터 `brightness(0.6) contrast(0.95) saturate(0.75) sepia(0.07)` 확인
- AudioContext running · gain 0.35 · lowpass 약 8767.67 Hz · peaking EQ 3000 Hz +4 dB · compressor threshold −25 / ratio 5 확인
- 실제 영상 오디오 입력 RMS 0.095648 · 처리 출력 RMS 0.047774로 비무음 확인
- SPA 전후 동일 document 유지 및 두 번째 영상에도 화면·소리 적용 확인
- 끈 뒤 오디오 입력/출력 RMS 모두 0.083577 · 출력/입력 비율 1.00 · CSS filter none 확인
- 재생 시간 계속 증가 · 재생 속도/플레이어 음량/음소거 유지
- 공개 웹 초기화 후 유튜브 밝기 85 · 대비 90 · gain 0.35 · EQ 0 dB로 복원
- 저장하지 않은 웹 미리보기는 확장과 유튜브에 전달되지 않음

440 Hz 제어 신호에서는 gain 0.35의 실제 RMS 비율 약 0.350012 · 끈 뒤 비율 1.00 확인
유튜브의 EQ·압축 동시 적용 시 최종 RMS 비율을 gain 값과 동일하다고 해석하지 않음

## 설치 패키지

두 ZIP 내용 동일 · 11개 파일 · 17313 bytes

`pariview-extension.zip` 및 `web/dist/pariview-extension.zip`

SHA-256 `98b305321f01f3bfcdf1a7ed24297bce30c5f99e9737637740d7fcd5bf142e6f`

사용자 안내: `install.html` · 소스 통합 명세: `INTEGRATION.md`

## 확인하지 않은 범위

- 사람의 귀로 듣는 청취 평가와 체감 편안함 평가는 수행하지 않음
- 개인 계정이 로그인된 사용자 Chrome에는 설치하거나 세션을 변경하지 않음
- 실제 유료 DRM 영상은 미검증 · encrypted 이벤트에 대한 비연결/새로고침 안내는 로컬 fixture로 검증
- 모든 유튜브 광고·Shorts·라이브·다른 브라우저를 전수 검증하지 않음
- 닫힌 Shadow DOM, 브라우저 내부 페이지, 영상 자막·요약·AI 분석은 지원 범위 밖

재현 스크립트와 실행법은 [../README.md](../README.md)에 있어요
