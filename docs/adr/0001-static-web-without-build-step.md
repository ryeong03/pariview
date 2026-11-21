# ADR 0001 · 웹 앱은 빌드 단계 없이 `web/dist`를 소스로 직접 배포한다

- 상태: 채택
- 날짜: 2026-11-22

## 맥락

`web/dist`라는 이름 때문에 번들러 산출물을 커밋한 것처럼 보이지만, 이 폴더의 HTML·CSS·ES 모듈은 사람이 직접 작성한 **소스**예요 `package.json`이나 번들러가 없고, `ai/server.py`(파이썬 표준 라이브러리만 사용)가 이 폴더를 그대로 서빙해요

이 경로는 서버, 테스트(`web/test_adaptive_fit.mjs`, `ai/test_recommendation.py`), 시뮬레이션(`research/adaptive-fitting/simulate.mjs`), 그리고 파일 해시를 기록한 연구 검증 자료(`research/engineering-basis/validation.json`)가 함께 참조해요

## 계기

커밋돼 있던 ZIP이 소스와 어긋나 있었어요 브랜드 색을 민트로 바꾼 커밋(`9b69b6e`)이 `extension/popup.html`과 `extension/README.md`를 고쳤지만 ZIP은 다시 만들지 않아, 웹의 다운로드 링크가 옛 빨간색 팝업을 내려주고 있었어요 사람이 기억해서 다시 만들어야 하는 산출물은 언젠가 낡아요

## 결정

- 빌드 단계를 두지 않아요 브라우저가 ES 모듈을 그대로 불러오고, 서드파티 라이브러리는 라이선스와 함께 `web/dist/vendor/`에 고정 버전으로 둬요
- **진짜 빌드 산출물만** 저장소에서 빼요 크롬 확장 ZIP 3개는 `extension/package.py`로 재현 가능하게 만들고, CI 아티팩트와 Docker 빌드 단계에서 생성해요
- 폴더 이름 `web/dist` → `web/static` 변경은 하지 않아요 연구 검증 해시와 문서 경로가 함께 깨지기 때문이에요 캡스톤 결선 이후 경로를 한 번에 옮길 때 다시 검토해요

## 결과

- 장점: 의존성 설치 없이 `python3 ai/server.py` 하나로 실행돼요 공급망 공격면과 빌드 실패 지점이 없어요 CI는 문법 검사, 엔진 단위 테스트(node:test), API 테스트(unittest), Docker 헬스체크로 같은 파일을 검증해요
- 단점: 축소(minify)와 트리 셰이킹이 없어요 정적 파일은 서버가 gzip으로 압축해 전송량을 줄여요
- 남은 위생 과제: 장면 영상(mp4)과 포스터 PDF는 Git 기록에 남아 있어요 Git LFS나 Release 자산으로 옮기는 일은 기록 재작성(force push)이 필요하므로 별도로 결정해요
