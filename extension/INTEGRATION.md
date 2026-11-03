# PariView 웹 ↔ 크롬 확장 프로그램 연결 명세

확장 프로그램 본체는 이 폴더(`~/Desktop/pariview/extension/`)에 완성돼 있고, 설치 파일은 `~/Desktop/pariview/pariview-extension.zip`이에요.
웹(`web/dist`)에는 아래 내용만 붙이면 돼요. 마침표는 쓰지 않아요.

## 1. 연결에 꼭 필요한 두 줄 (없으면 동기화 안 됨)

- `<head>`에 `<meta name="pariview-app" content="1">` 추가
  - 확장 프로그램은 이 태그로 PariView 페이지인지 알아보고, 이 페이지에서는 영상 필터를 적용하지 않아요
- 설정을 `localStorage['pariview-fit-v1']`에 저장한 직후 `document.dispatchEvent(new Event('pariview-saved'))` 실행
  - 저장 형식은 지금과 같아요: `{settings:{brightness,contrast,volume,compression,notices},updatedAt}`
  - 키 이름이나 형식을 바꾸면 `content.js`의 `KEY`, `normalize()`도 같이 바꿔야 해요

확장 프로그램은 연결되면 `document.documentElement.dataset.pariviewExtension`을 `connected`(설정 없음) 또는 `synced`(설정 넘어감)로 바꾸고 `pariview-extension-ready` 이벤트를 보내요

## 2. 메뉴

- 상단 메뉴의 "설계의 근거"를 빼고 그 자리에 **크롬에서 쓰기** 탭 추가
- "설계의 근거"는 페이지 맨 밑 푸터 링크로 옮김 (`<a href="#research" data-tab="research">설계의 근거</a>`)
- `#chrome` 해시로 들어오면 크롬 탭을 바로 열기

## 3. 크롬에서 쓰기 탭 문구

- 키커: 크롬 확장 프로그램
- 제목: 맞춘 설정, / 유튜브에서도 그대로
- 설명: 크롬 확장 프로그램을 설치하면 PariView에서 고른 소리·밝기·대비가 다른 영상에도 적용돼요
- 연결 상태 (dataset 값에 따라)
  - none: 아직 연결되지 않았어요 / 설치한 뒤 이 페이지를 새로고침하면 연결돼요
  - connected: 확장 프로그램이 연결됐어요 / 감각 피팅 결과를 저장하면 설정이 넘어가요
  - synced: 확장 프로그램에 설정이 들어갔어요 / 유튜브에서도 같은 밝기·대비·소리로 볼 수 있어요
- 1단계 확장 프로그램 설치하기: 파일을 받아 압축을 풀고, 크롬 주소창에 chrome://extensions를 입력해요 오른쪽 위 개발자 모드를 켜고 ‘압축해제된 확장 프로그램을 로드합니다’를 눌러 풀어둔 폴더를 골라요 → [설치 파일 받기 ↓] (`pariview-extension.zip`을 dist에 복사)
- 2단계 감각 피팅 결과 저장하기: 설치한 뒤 이 페이지를 새로고침하고 감각 피팅을 마치면 설정이 확장 프로그램으로 자동으로 넘어가요 → [감각 피팅 하기 →]
- 3단계 유튜브에서 확인하기: 아무 영상이나 틀면 고른 밝기와 대비가 바로 보여요 소리는 페이지를 한 번 누른 뒤부터 맞춰져요 툴바의 PariView 아이콘에서 켜고 끌 수 있어요 → [유튜브 열기 ↗]
- 하단 메모: 끄면 원래 화면과 소리로 돌아가요 DRM이 걸린 영상은 화면만 맞춰져요

```js
const extensionCopy={none:['아직 연결되지 않았어요','설치한 뒤 이 페이지를 새로고침하면 연결돼요'],connected:['확장 프로그램이 연결됐어요','감각 피팅 결과를 저장하면 설정이 넘어가요'],synced:['확장 프로그램에 설정이 들어갔어요','유튜브에서도 같은 밝기·대비·소리로 볼 수 있어요']};
function renderExtension(){const st=document.documentElement.dataset.pariviewExtension||'none';const [t,d]=extensionCopy[st]||extensionCopy.none;$('#extension-status').dataset.state=st;$('#extension-status-title').textContent=t;$('#extension-status-desc').textContent=d;}
document.addEventListener('pariview-extension-ready',renderExtension);renderExtension();
```

## 4. 첫 화면 서브카피 (사용자 지정 문구)

```
안경을 맞출 땐, 섬세하게 맞추면서
왜 화면에는 무심한가요?
같은 장면을 비교하며 내게 편안한 소리와 빛을 찾아요
```

## 5. 설계의 근거 → 연구 기반 시작 모드 추천

- 제목: 연구를 근거로 / 시작 모드를 추천해요
- 설명: 두 가지만 고르면 연구에서 확인된 개인차를 바탕으로 시작할 모드를 골라드려요 / 관찰된 연구 결과와 우리가 제안하는 경험은 구분해서 보여드려요
- 질문 1: 영화를 볼 때 더 신경 쓰이는 쪽을 골라주세요 → [큰 소리] [밝은 화면] [둘 다] [잘 모르겠어요]
- 질문 2: 갑자기 바뀌는 장면을 미리 알려드릴까요? → [미리 알려주세요] [알림 없이 볼게요]
- 결과: "추천 시작 모드" 배지 + 모드 이름·설명 + 고른 이유 + 근거 연구 카드 2~3개(설계 해석 문장 + 논문 링크) + [이 모드로 피팅 시작 →]
- 결과 하단: 추천은 진단이 아니라 비교를 시작할 지점이에요 장면을 비교하며 언제든 바꿀 수 있어요
- 피팅 모달의 모드 목록에서 추천된 모드에 "추천" 배지 표시, 그 모드를 미리 선택

규칙 (현재 `modes`/`research` 배열 인덱스 기준, 모드 구성이 바뀌면 id만 맞추면 됨)

| 질문 1 답 | 추천 모드 id | 근거 카드 |
|---|---|---|
| 큰 소리 | focus (이야기에 집중) | 0 개인차, 2 시청각 영화 연구 |
| 밝은 화면 | soft (부드럽게 시작) | 0 개인차, 2 시청각 영화 연구 |
| 둘 다 | gentle (자극을 편안하게) | 0 개인차, 4 국내 보조 근거 |
| 잘 모르겠어요 | everyday (평소처럼 편안하게) | 0 개인차, 1 통제권 |

질문 2에 답하면 근거 카드 3(예고 단서 개인차)을 추가하고 `settings.notices`를 그 답으로 맞춘 뒤 피팅을 열어요

이 추천은 규칙 기반이에요 화면에 "AI 추천", "맞춤 분석", "진단" 같은 말은 쓰지 않아요

## 6. 하단 프로토타입 문구

- 기존: 현재 웹은 A/B 선호 탐색, 화면·음량 조절, 설정 저장을 체험하는 프로토타입입니다 감각 진단이나 치료 효과를 제공하지 않습니다
- 변경 (사용자 확정): 현재 PariView 서비스는 같은 장면 비교, 화면·소리 조절, 설정 저장과 크롬 확장 프로그램 연동을 제공해요 감각 진단이나 치료를 대신하지 않아요
