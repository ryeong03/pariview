# PariView 크롬 확장 프로그램

PC 크롬에서 PariView의 저장한 화면·소리 설정을 유튜브 등 HTML 영상에 적용해요

## 설치와 사용

웹스토어 설치 후에는 아래 3번부터 진행해요 ZIP 직접 설치는 개발·시연용이에요

1. `pariview-extension.zip`의 압축을 풀어요
2. `chrome://extensions` → 개발자 모드 → 압축해제된 확장 프로그램을 로드합니다 → `manifest.json`이 있는 폴더를 선택해요
3. [PariView](https://pariview-production.up.railway.app/)를 새로고침하고 설정을 저장해요
4. 유튜브 탭도 새로고침한 뒤 영상 페이지를 한 번 누르고 재생해요
5. 도구 모음의 PariView 아이콘에서 현재 탭의 적용 상태와 켜기·끄기를 확인해요

자세한 설치·문제 해결 안내는 함께 들어 있는 [install.html](install.html)을 열어주세요
업데이트할 때는 기존 설치 폴더를 덮어쓰고 크롬 확장 관리 화면과 영상 탭을 모두 새로고침해요

## 적용 범위

- 화면: 밝기·대비·채도·따뜻함
- 지원되는 영상의 소리: 원래 음량 × 선택값 / 100, 높은 소리 완화, 음량 변화 완화, 말소리 대역 강조
- 끄면 기존 화면 필터가 복원되고 Web Audio 효과 경로를 완전히 우회해요
- 재생 위치·재생 속도·플레이어의 음량·음소거는 바꾸지 않아요
- DRM·CORS 등 미지원 영상은 화면만 적용하고 원본 소리를 유지해요
- 이미 소리 효과를 적용한 영상 요소가 재생 중 DRM·비허용 외부 소스로 바뀌면 새로고침을 안내해요 Web Audio의 미디어 연결은 되돌릴 수 없기 때문이에요
- 장면 안내·자막·요약·AI 분석·자동 밝기·배경음 분리·장면 전환 보간은 확장에서 제공하지 않아요
- 닫힌 Shadow DOM 플레이어나 브라우저 내부 페이지는 지원하지 않아요
- 설정은 현재 크롬 프로필 안에만 저장돼요 별도 로그인이나 서버 전송은 없어요

## 배포 파일

- `pariview-webstore.zip`: Chrome Web Store 제출용, manifest.json이 ZIP 최상위에 있어요
- `pariview-extension.zip`: 개발·시연용, 압축을 풀면 설치 폴더가 생겨요
- 소스 코드는 MIT 라이선스이며 각 ZIP에 LICENSE가 포함돼요
- [개인정보 처리 안내](privacy.html)

## 검증 및 패키징

로컬 앱을 `python3 web/serve.py`로 실행한 다음 저장소 루트에서 실행해요

```sh
uv run --with playwright python extension/tests/e2e.py
uv run --with playwright python extension/tests/audio_and_status.py
uv run --with playwright python extension/tests/youtube.py
python3 extension/package.py
```

테스트는 매번 별도 임시 Chromium 프로필을 사용해요 개인 크롬 계정과 로그인 상태는 건드리지 않아요
유튜브 테스트는 네트워크와 공개 영상 재생 가능 여부에 영향을 받아요 오디오 신호 측정과 사람의 청취 평가는 구분해요
