# PariView

**화면과 소리, 내가 정하면 안 되나요?**

- **문제** 영화의 밝기와 소리는 하나의 기본값으로 나오지만, 편한 빛과 소리는 사람마다, 보는 곳마다 달라요
- **해법** 같은 장면을 두 가지로 비교해 고른 밝기·대비·소리를 저장하고, 크롬 확장 프로그램으로 다른 영상에도 이어서 적용해요

2026 이화여대 공과대학 캡스톤디자인 사회기여형 · 팀 Lucent (정아윤, 박세령, 정서윤)
의학의 평가 관점과 감각 연구를 참고해, 사용자가 직접 비교하고 조절하는 시청 선호 피팅 서비스예요

## 데모

- 웹 데모: [PariView 바로 열기](https://pariview-production.up.railway.app/)
- 로컬 실행: `HOST=127.0.0.1 PORT=4178 python3 ai/server.py` → http://127.0.0.1:4178
- Claude 추천 연결: [Railway 환경변수 안내](ai/README.md) · 키를 설정하기 전에도 연구 기반 기본 제안을 이용할 수 있어요
- 크롬 확장 프로그램: [`pariview-extension.zip`](pariview-extension.zip)을 풀고 `chrome://extensions`에서 개발자 모드 → 압축해제된 확장 프로그램을 로드합니다

## 화면

| 첫 화면 | 시청 스튜디오 |
|:---:|:---:|
| ![첫 화면](docs/images/hero-desktop.png) | ![영상 아래 조절 dock](docs/images/studio-desktop.png) |
| **시작 프로필 고르기** | **같은 장면 A/B 비교** |
| ![다섯 가지 시작 프로필](docs/images/fit-profiles.png) | ![밝기 A/B 비교](docs/images/fit-compare.png) |
| **크롬에서 쓰기** | **모바일** |
| ![크롬 확장 프로그램 연결](docs/images/chrome-tab.png) | <img src="docs/images/hero-mobile.png" alt="모바일 첫 화면" width="260"> |

영상 신호로 측정한 감각 지도

![장면의 감각 지도](docs/images/sensory-map.png)

모든 이미지는 `web/dist`를 실제로 실행한 화면이에요 (1440×900, 390×844)

## 이용 흐름

1. **방법 고르기** ‘직접 설정하기’에서 다섯 가지 시작 프로필을 고르거나 ‘연구 기반 PariView-AI 추천받기’에서 오늘의 필요와 환경을 골라요 추천값은 이유와 출처를 확인하고 수정·미리보기할 수 있어요
2. **같은 장면 비교하기** 밝기, 대비, 소리 크기, 음량 변화 완화, 쉬운 자막을 A/B로 비교해요 화면은 같은 순간을 함께 재생하고 소리는 한쪽씩 들어요 비교 재생 속도는 0.75배이며 ‘비슷해요’, ‘잘 모르겠어요’, ‘건너뛰기’를 따로 기록해요
3. **맞춘 설정으로 보기** 고른 설정으로 영상을 보고 저장해요 크롬 확장 프로그램이 같은 설정을 다른 사이트 영상에도 적용해요 언제든 다시 맞추거나 원본과 비교하거나 기본값으로 돌아갈 수 있어요

| 시작 프로필 | 이럴 때 |
|---|---|
| 자극을 편안하게 | 소리와 빛에 민감한 날이라면 |
| 이야기에 집중 | 이야기의 흐름을 따라가고 싶다면 |
| 조금 더 또렷하게 | 또렷하게 듣고 크게 보고 싶다면 |
| 부드럽게 시작 | 부드러운 화면과 쉬운 말이 필요하다면 |
| 평소처럼 편안하게 | 평소 화면과 소리를 조금씩 맞추고 싶다면 |

시작 프로필은 고쳐 쓸 수 있는 출발점이에요 실제 값은 [`web/dist/settings.js`](web/dist/settings.js)에 있어요

**영상은 세 작품에서 45초씩, 총 2분 15초**를 제공해요 ‘장면 고르기’에서 Tears of Steel의 연구실, Sintel의 대화와 도시, Big Buck Bunny의 밝은 초원을 바꿔 볼 수 있어요 선택한 화면·소리 설정은 영상이 바뀌어도 유지돼요

Claude는 검토된 후보 중 시작 설정과 다음 비교 항목을 고르고, 설명과 출처는 검증한 카탈로그에서 가져와요 AI 연결이 없거나 응답을 검증하지 못하면 ‘연구 기반 기본 제안’으로 이어져요 실제 모델 응답이 검증된 결과에만 ‘AI 추천’을 표시하며 사용자가 확정할 때만 저장해요

## 기술 구조

```mermaid
flowchart LR
  subgraph Web["PariView 웹 (web/dist, 빌드 없는 정적 HTML·CSS·JS)"]
    UI["피팅 UI<br>시작 프로필 · A/B 비교 · 추천 규칙"]
    V["video 요소"]
    F["CSS filter<br>밝기 · 대비 · 채도 · 색온도"]
    A["Web Audio<br>lowpass → 말소리 EQ → compressor → gain"]
    M["클립별 감각 지도<br>assets/scenes/*-map.json"]
    S[("localStorage<br>pariview-fit-v1")]
    G["Three.js · Anime.js<br>3D 로고 · 마스코트"]
    UI --> F --> V
    UI --> A --> V
    UI -- 저장 --> S
    M --> UI
  end
  subgraph Ext["크롬 확장 프로그램 (extension/, MV3)"]
    CS["content script"]
    CST[("chrome.storage")]
    P["팝업 켜기 · 끄기"]
  end
  S -- "pariview-saved 이벤트" --> CS --> CST
  CST --> O["다른 사이트의 video<br>CSS filter + Web Audio"]
  P --> CST
  AN["analysis/sensory_map.py<br>ffmpeg EBU R128 · 프레임 밝기"] --> M
  UI --> API["Python 추천 API<br>검토된 후보 · 연구 출처"]
  API --> Claude["Claude<br>후보 ID · 다음 비교 선택"]
  API --> Default["연구 기반 기본 제안"]
  API --> UI
```

| 영역 | 사용 기술 |
|---|---|
| 화면 조절 | CSS filter (brightness, contrast, saturate, sepia), canvas 프레임 밝기 측정으로 어두운 장면 보정 |
| 소리 조절 | Web Audio API (BiquadFilter lowpass, 3kHz peaking EQ, DynamicsCompressor, Gain) |
| 감각 지도 | ffmpeg EBU R128 순간 라우드니스와 signalstats 프레임 평균 밝기로 변화 구간 측정 |
| 저장·연동 | localStorage, JSON 설정 내려받기, Chrome Extension Manifest V3 (content script, storage) |
| 그래픽 | Three.js 마스코트·로고, Anime.js 스프링 반응, GSAP, 모션 줄이기 지원 |
| 추천 | 검토된 설정·출처 카탈로그, Claude Messages API, 응답 검증, 규칙 기반 기본 제안 |
| 배포 | Docker + Python 표준라이브러리 정적·추천 API 서버 (Railway), 영상 HTTP Range 지원 |

## 검증

| 항목 | 방법 | 결과 |
|---|---|---|
| 화면 동작 | `uv run --with playwright python web/validate.py` (1440·1280·768·390 폭, 5프로필, 비교, 저장, 초기화, 재생, 모바일, 모션 줄이기) | 오류 0건, 리소스 실패 0건 |
| 추천 | `python3 -m unittest ai.test_recommendation -v`, `uv run --with playwright python web/validate_recommendation.py` | 13개 테스트, 정책 입력 61개 일치, 브라우저 9개 흐름 통과 · 실제 Claude 호출은 키 설정 후 확인 |
| 영상 비교 | 3편 길이·장면 전환·12초 이후 탐색·동시 재생·0.75배속 확인 | 각 45초, 화면 동기화 및 설정 유지 통과 |
| 확장 프로그램 | Chromium에 `--load-extension`으로 설치해 연결 → 저장 → 다른 페이지 적용 → 초기화 → 끄고 켜기 → 재생 유지 | 6개 항목 통과 |
| 피팅 흐름 | [AI 페르소나 10명 시뮬레이션](analysis/simulation/REPORT.md) 대상층별 페르소나가 실제 UI로 피팅을 끝까지 진행 | 원하는 값과의 평균 오차 0.189 → 0.077, 10명 모두 오차 감소, 켜기/끄기 항목 일치 70% → 100% |

시뮬레이션은 페르소나마다 정해둔 목표값에 피팅 흐름이 얼마나 다가가는지를 확인한 결과예요 고정된 두 값 중에서만 고르는 구조라 큰 소리가 필요한 페르소나는 최대 선택지에서 멈추는 한계도 함께 찾았어요

## 구현 범위와 한계

| 구분 | 내용 |
|---|---|
| 구현 | 직접 설정 / 연구 기반 추천 두 경로, 다섯 시작 프로필, 5단계 A/B 비교, 추천 수정·미리보기·취소·확정, 3편 영상 선택, 밝기·대비·채도·색온도, 음량·고음 완화·말소리 강조·음량 변화 완화, 자막·쉬운 자막·자막 크기, 놓친 내용 기록, 20분 휴식 안내, 원본 비교, 저장·초기화·설정 파일 내려받기, 크롬 확장 연동, 영상 신호 기반 감각 지도 |
| 시연용 예시 | 자막·쉬운 자막·요약·장면 사전 안내 문구는 현재 영상에 맞춰 미리 작성했어요 배경음 줄이기와 장면 전환 완화는 설정 화면만 있고 실제 음원 분리나 프레임 보간은 하지 않아요 |
| 구현하지 않음 | 대사 분리, 개인별 불편 예측, 영상의 실시간 AI 분석, 감각 역치 측정 |
| 한계 | 연구는 개인차·환경 조절·비교 절차의 설계 근거예요 설정 수치나 AI 추천 성능, 감각 진단·치료 효과를 검증한 것은 아니에요 45초 구간으로 작품 전체를 대표하지 않아요 확장 프로그램의 소리는 DRM·CORS 등 지원 조건에 따라 제한되며 자막·장면 기록·사전 안내는 웹 시연 영상에서 제공해요 |

## 연구 근거

- [`research/literature-review.txt`](research/literature-review.txt): 논문 결과, 설계 해석, 적용 한계
- [`research/sources.json`](research/sources.json), [`research/medical-sensory-sources.json`](research/medical-sensory-sources.json): 서지와 확인 기록
- 웹의 "설계의 근거" 화면은 관찰된 연구 결과와 우리가 제안하는 경험을 구분해서 보여줘요

## 폴더

| 경로 | 내용 |
|---|---|
| `web/dist` | 웹 데모 소스 (index.html, app.js, settings.js, research.js, CSS, vendor) |
| `web/serve.py` | 로컬 서버 (HTTP Range 지원) |
| `ai/` | Python 정적·추천 API 서버, Claude 연결, 후보 검증과 테스트 |
| `web/dist/scenes.js`, `assets/scenes/` | 45초 영상 3편, 자막·장면 정보와 클립별 감각 지도 |
| `web/dist/recommendation*` | 추천 입력·수정·미리보기 UI와 검증된 후보·연구 카탈로그 |
| `web/validate.py` | 화면 동작 검증 |
| `extension/` | 크롬 확장 프로그램 소스 |
| `analysis/sensory_map.py` | 감각 지도 측정 |
| `analysis/simulation/` | AI 페르소나 시뮬레이션, 실제 사용자 평가지 |
| `research/` | 문헌 정리와 출처 |
| `Dockerfile`, `deploy/` | Railway Python 서버 배포 설정과 운영 안내 |

## 출처와 라이선스

- 영화: Tears of Steel (00:47~01:32), Sintel (02:20~03:05), Big Buck Bunny (00:50~01:35) · Blender Foundation / 해당 작품 크레디트 · [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) · [클립별 출처와 변경 내역](web/dist/assets/FILM-LICENSE.txt)
- 글꼴: Pretendard, SIL Open Font License ([`OFL.txt`](web/dist/assets/OFL.txt))
- 라이브러리: Three.js, Anime.js, GSAP (라이선스는 `web/dist/vendor`)
- 전체 소재 출처는 웹의 [`credits.html`](web/dist/credits.html)에 있어요
