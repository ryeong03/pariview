# PariView에 기여하기

PariView는 사람마다 다른 시청 선호에 맞춰 화면과 소리를 조절할 수 있도록 소스를 공개해요
현재 검증한 유튜브 연동을 출발점으로, 여러 OTT와 웹 영상에서 쓸 수 있도록 지원 범위를 함께 넓혀가요

## 시작하기

```sh
git clone https://github.com/ryeong03/pariview.git
cd pariview
HOST=127.0.0.1 PORT=4178 python3 ai/server.py
```

http://127.0.0.1:4178 에서 실행해요 Python 표준 라이브러리만 필요하고, API 키 없이도 기본 제안이 동작해요
확장 프로그램은 [설치·개발 안내](extension/README.md)를 따라 로컬에서 실행할 수 있어요

## 함께 넓혀갈 범위

- **영상 서비스 지원** 서비스별 플레이어 탐색, 영상 교체와 SPA 이동 대응, 지원 범위 표시
- **접근성** 키보드 조작, 화면 낭독, 큰 글자, 모션 줄이기, 다양한 화면 크기
- **비교 장면** 재배포 가능한 영상, 자막·쉬운 표현, 장면별 신호 측정과 정확한 출처
- **연구와 평가** 검토 가능한 출처, 사용자 평가 방법, 추천의 설명과 조절권

지원 서비스를 추가할 때는 정상 작동한 브라우저·공개 영상·기능과 제한을 함께 기록해 주세요
DRM·CORS 등 소리 처리가 지원되지 않는 경우에는 원래 재생을 유지하고 지원 상태를 보여줘요
새 서비스 지원은 실제 검증이 끝난 범위만 표시해요

## 변경 확인

```sh
python3 -m unittest ai.test_recommendation -v
uv run --with playwright python web/validate.py
uv run --with playwright python web/validate_recommendation.py --base-url http://127.0.0.1:4178
```

브라우저 검사에 쓰는 Chromium 경로와 포트는 각 스크립트 및 [배포 안내](deploy/README.md)를 참고해요
확장 기능을 고쳤다면 [확장 검증 기록과 재현 방법](extension/tests/VALIDATION.md)도 확인해 주세요
PR에는 바뀐 동작, 확인 방법, 화면 변경이 있을 때 전후 화면을 적어 주세요
키·토큰·개인 브라우저 프로필과 응답자 개인정보는 저장소에 넣지 않아요

## 라이선스와 출처

PariView가 작성한 소스 코드는 [MIT License](LICENSE)로 공개해요
동봉된 영화·글꼴·외부 라이브러리는 각각의 라이선스를 따르며 이 MIT 라이선스로 바뀌지 않아요
영상 출처는 [FILM-LICENSE.txt](web/dist/assets/FILM-LICENSE.txt), 글꼴은 [OFL.txt](web/dist/assets/OFL.txt), 라이브러리는 [vendor](web/dist/vendor)를 확인해 주세요
