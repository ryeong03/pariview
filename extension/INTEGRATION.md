# PariView 웹 ↔ 크롬 확장 연결 명세

## 저장 계약

- 웹의 `<head>`: `<meta name="pariview-app" content="1">`
- 저장 키: `localStorage['pariview-fit-v1']`
- 저장 형식: `{settings, updatedAt}`
- 실제 저장 직후: `document.dispatchEvent(new Event('pariview-saved'))`
- 직접 조절·AI 추천의 임시 미리보기는 저장하거나 이 이벤트를 보내지 않아요
- 초기화는 웹 기본값을 저장하고 같은 이벤트를 보내요
- 확장은 최초 진입 때 저장값을 읽고 이후 저장 이벤트와 같은 origin의 storage 이벤트를 받아요
- PariView 페이지에는 확장 필터·오디오 처리를 중복 적용하지 않아요

## 연결 상태와 실제 적용 상태 구분

`document.documentElement.dataset.pariviewExtension`

- `connected`: 웹과 연결됨, 이 페이지에 저장된 설정 없음
- `synced`: 저장된 설정이 `chrome.storage.local.profile`에 전달됨
- `error`: 확장 저장 실패

갱신 후 `pariview-extension-ready` 이벤트를 보내요
`synced`는 저장 확인이며 유튜브의 실제 오디오 적용이나 재생 성공을 뜻하지 않아요
실제 적용 상태는 확장 팝업에서 현재 탭의 각 프레임에 질의해 확인해요

팝업 구분: 설정 없음 / 꺼짐 / PariView 페이지 / 연결 불가 / 영상 없음 / 로딩 / 영상 오류 / 클릭 필요 / 화면만 적용 / 일부 적용 / 화면·소리 적용 / 소스 변경 후 새로고침 필요

## 설정 호환

`extension/settings.js`의 `normalize()`는 `web/dist/settings.js`와 같은 기본값·범위를 사용해요
숫자는 유한한 number만 사용하고 범위를 벗어나면 제한해요 잘못된 형식은 기본값으로 복원해요

| 설정 | 기본값 | 범위 또는 처리 |
|---|---|---|
| brightness | 85 | 45–100 |
| contrast | 90 | 65–110 |
| saturation | 100 | 40–110 |
| warmth | 0 | 0–60, sepia에 ×0.35 |
| volume | 35 | 0–70, gain = 선택값 / 100 |
| highCut | 0 | 0–100, cutoff = 20000 × 0.16^(선택값 / 100) |
| compression | true | threshold −25, knee 22, ratio 5, attack 0.008, release 0.25 |
| dialogueBoost | false | 3000 Hz peaking EQ, Q 1, +4 dB |
| notices | true | 호환 저장만 유지, 유튜브 장면 예고는 제공하지 않음 |

그 외 웹 설정도 원본 profile에 보관하지만 확장에서 실행하지 않아요

## 소리 처리와 복원

- 실행 중인 AudioContext를 확보한 뒤에만 MediaElementAudioSource를 연결해 자동재생 제한으로 인한 무음을 피함
- 같은 origin·같은 origin의 MSE blob·data 또는 CORS가 허용된 재생 가능한 미디어에만 적용
- DRM·srcObject·미허용 외부 미디어에는 소리 그래프를 만들지 않음
- 켜짐: source → lowpass → speech EQ → 선택 compressor → gain → destination
- 꺼짐: source → destination, 화면 CSS 제거, 플레이어 volume/muted/currentTime/playbackRate를 변경하지 않음
- 새 영상 요소·YouTube SPA 탐색·loadeddata·encrypted 이벤트에 재평가
- 이미 연결한 요소가 보호/비허용 소스로 바뀌면 복원을 보장할 수 없어 새로고침 안내
- 기술 배경: [Web Audio의 cross-origin 보안 제약](https://www.w3.org/TR/webaudio-1.1/#MediaElementAudioSourceNode-security), [Chrome content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts)

## 패키지

`python3 extension/package.py`는 설치에 필요한 파일과 사용자 안내만 담은 두 동일한 zip을 만들어요

- `pariview-extension.zip`
- `web/dist/pariview-extension.zip`

개발용 테스트·인수인계 자료는 설치 패키지에 포함하지 않아요
