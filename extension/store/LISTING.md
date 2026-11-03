# Chrome Web Store 제출 내용

상태: v0.3.1 업로드 및 등록 필수 항목 저장 완료 · 게시자 이메일 인증 대기 · 심사 제출/공개 전

2026-11-04 KST 최신 사용자 지시에 따라 배포 보류를 해제하고 기존 항목에서 등록을 계속함
실제 항목 ID: `iglphbdlmnpahdojacfkemhijagafjda`
2026-11-04 콘솔 재검사에서 남은 요건은 게시자 연락처 이메일 입력·인증뿐이었으며, 연락처 입력 후 인증 이메일 발송 완료를 확인함
인증은 수신 메일의 링크를 여는 방식이며 공개 설치 가능한 상태로 표기하지 않음
연락처와 인증 링크/코드는 이 문서나 패키지에 보관하지 않음

## 등록 파일

- 제출 ZIP: 저장소 루트 `pariview-webstore.zip` — 최상위 manifest · v0.3.1 · 13개 파일 · MIT LICENSE 포함 · 기존 항목에 업로드 완료
- 아이콘: `extension/icons/icon128.png`
- 스크린샷: `extension/store/screenshot-01.png`, `screenshot-02.png` — 실제 YouTube + 확장 팝업 켜기/끄기 화면 · 각 1280×800 · 24-bit RGB PNG · 알파 없음 · 2장 업로드/저장 완료
- capture.py는 실제 브라우저 화면을 캡처하여 배치함 영상은 Big Buck Bunny © Blender Foundation, CC BY 3.0이며 이미지 안에 출처 표기
- 언어: 한국어
- 카테고리: 접근성 — 콘솔 저장 확인
- 배포: 무료 · 공개 · 지역 제한 없음
- 홈페이지: https://pariview-production.up.railway.app/#chrome
- 지원: https://github.com/ryeong03/pariview/issues
- 개인정보 URL: https://pariview-production.up.railway.app/extension-privacy.html — 2026-11-04 HTTPS 200 확인, 배포 담당이 원본 바이트 일치 확인
- 사용자가 지정한 연락처만 콘솔에 입력 · 전화번호 입력 없음 · 인증 메일 수신 링크 확인은 계정 소유자가 진행

## 제목

PariView 시청 설정

## 짧은 설명

PariView에서 고른 소리·밝기·대비를 크롬의 다른 영상에도 적용해요

## 상세 소개 — 그대로 입력

화면과 소리를 내가 정한 기준으로 시청해요

PariView에서 저장한 시청 설정을 유튜브 등 웹 영상에서도 이어서 사용할 수 있어요
Mac과 Windows의 PC 크롬에서 같은 확장 프로그램을 사용해요

어떤 설정을 적용하나요
• 화면 밝기·대비·채도·따뜻함
• 지원되는 영상의 전체 음량·높은 소리 완화·음량 변화 완화·말소리 대역 강조
• 현재 탭의 실제 적용 상태 확인
• 한 번의 스위치로 효과 켜기·끄기

사용 방법
1 PariView 웹사이트에서 화면과 소리를 직접 조절하거나 추천을 비교해요
2 마음에 드는 설정을 저장해요 임시 미리보기는 다른 영상에 전달되지 않아요
3 유튜브 등 영상 탭을 새로고침하고 페이지를 한 번 누른 뒤 재생해요
4 도구 모음의 PariView 아이콘에서 적용 상태를 확인해요

재생 중에도 내 선택을 유지해요
영상의 재생 위치·재생 속도·플레이어 음량·음소거는 바꾸지 않아요
확장의 음량 35%는 플레이어의 원래 음량에 0.35를 곱하는 설정이에요
적용을 끄면 화면 필터와 소리 효과를 해제해요

지원 범위
HTML 영상과 지원되는 소리 소스에 적용돼요
보호된 영상이나 소리 접근을 허용하지 않는 영상에는 화면만 적용해요
재생 도중 영상의 보호 방식이 바뀌면 새로고침이 필요할 수 있어요
장면 안내·자막·요약·AI 분석·자동 밝기·배경음 분리는 확장에서 제공하지 않아요
모바일 크롬과 브라우저 내부 페이지는 지원하지 않아요
감각 진단이나 치료 효과를 제공하지 않아요

내 브라우저 안에서 처리해요
시청 설정은 현재 Chrome 프로필에 저장해요
영상과 소리는 브라우저 안에서 처리하며 개발자 서버로 보내지 않아요
시청 기록 수집·판매·광고 추적·마이크 녹음은 하지 않아요
권한과 데이터 처리 상세는 개인정보 처리 안내에서 확인할 수 있어요

PariView는 Google 또는 YouTube의 공식 제품이 아니에요

## 단일 목적 — Privacy practices

사용자가 PariView에서 저장한 화면·소리 설정을 웹의 HTML 영상에 적용하고 현재 탭의 적용 상태와 켜기·끄기를 제공함

## 권한 설명 — storage

사용자가 저장한 밝기·대비·채도·따뜻함·음량·소리 효과 설정, 저장 시각, 적용 스위치 상태, 설정 페이지로 돌아가기 위한 PariView origin/path를 chrome.storage.local에 보관함
이 정보는 같은 브라우저 프로필에서 설정을 다시 적용하는 데 사용하며 외부로 전송하거나 계정 간 동기화하지 않음

## 사이트 접근 설명 — HTTP / HTTPS content scripts, all_frames

유튜브를 포함한 사용자가 방문한 웹사이트의 HTML video 요소에 저장한 CSS 화면 필터와 지원되는 Web Audio 효과를 적용하기 위해 필요함
다른 웹사이트의 영상과 iframe 안의 플레이어도 지원하므로 사이트를 특정 도메인 한 곳으로 제한하지 않음
콘텐츠 스크립트는 영상 요소·소스의 출처·재생 상태와 PariView 저장값만 기능에 필요한 범위에서 사용함
브라우저 방문 기록 API·쿠키·마이크·카메라 권한은 사용하지 않음
사용자는 Chrome의 사이트 접근 설정에서 허용 사이트를 제한할 수 있음

## 원격 코드

No, I am not using remote code

All executable code is packaged inside the extension
The extension does not fetch, evaluate or execute server-provided code
Opening a normal link to the PariView website does not execute the website's code in the extension
The website's recommendation service is separate from the extension

## 데이터 사용 공개

로컬 처리도 공개 대상이므로 ‘아무 데이터도 처리하지 않음’으로 표시하지 않음
현재 대시보드의 항목 설명과 아래 실제 처리 범위를 맞춰 입력

- Website content: HTML video 요소, 미디어 소스 정보, 실시간 소리 신호, 웹에서 저장한 시청 설정을 기기에서만 처리
- Web history / browsing activity: 영상 소스 주소를 지원 가능 여부 확인에 일시적으로 사용하고, 돌아가기 기능을 위해 PariView origin/path 한 개를 로컬에 저장함 방문 사이트·영상 목록은 수집하거나 보관하지 않음
- User activity: 로컬에서 영상의 재생·일시정지·음소거 상태와 사용자 동작 발생 여부를 확인함 입력 내용·키 값·클릭 위치·행동 로그는 기록하지 않음
- 개인 식별·결제·건강·인증 정보·개인 통신·위치: 확장 기능이 수집하지 않음 시청 설정은 의학적 측정이나 진단 데이터가 아님
- 데이터 판매, 관련 없는 용도의 사용·전달, 신용/대출 판단 용도의 사용·전달 없음

## 심사자 테스트 안내 — Test instructions

No account, payment, API key or test credentials are required to use this extension

1 Install the submitted extension
2 Open https://pariview-production.up.railway.app/#studio and refresh once
3 Adjust 화면 밝기 (brightness), then click 이 설정 저장하기 (save settings)
4 Open https://www.youtube.com/watch?v=R6MlUcmOul8 and refresh once
5 Click the page and start playback to allow Web Audio
6 Open the extension popup to see the active tab status and saved values
7 Toggle 다른 영상에도 적용하기 off/on to compare with the original video
8 Reset using 기본값으로 초기화 on PariView and verify brightness 85 / contrast 90 / volume 35 in the extension

The extension only imports settings after the web app saves them
Temporary previews are not imported
On DRM or CORS-restricted media, visual filters may work while audio remains native
Audio filtering does not analyze or upload media, and no AI features execute inside the extension
The popup explicitly distinguishes no video, gesture needed, visual-only, applied, and reload-required states

## 콘솔에 저장한 심사 안내 — 398/500자

No login/payment needed. Install, open https://pariview-production.up.railway.app/#studio and refresh. Adjust brightness and click 이 설정 저장하기. Open https://www.youtube.com/watch?v=R6MlUcmOul8, refresh, click the page and play. The popup shows status; toggle 다른 영상에도 적용하기 off/on. 기본값으로 초기화 on PariView restores 85/90/35. Unsaved previews do not sync. Protected/CORS-restricted audio is not processed.

사용자 이름·비밀번호 칸은 비움 — 로그인이나 별도 테스트 계정이 필요하지 않음

## 2026-11-04 검증 및 등록 상태

- 최종 v0.3.1 제출 ZIP을 새 폴더에 풀고 새 Chromium 프로필로 검사 32/32 통과: [검증 기록](../tests/VALIDATION-0.3.1.md)
- 실제 사람의 청취 평가와 유료 DRM 영상 실증은 수행하지 않음
- v0.3.1은 기존 런타임에 홈페이지·설치 안내·개인정보 안내·MIT 라이선스·웹스토어 패키징을 추가함
- 설명 927자 · 접근성 · 한국어 · 아이콘 · 스크린샷 2장 · 홈페이지/지원 URL 저장 완료
- 단일 목적 · storage/호스트 권한 이유 · 원격 코드 없음 · 로컬 처리 3범주 · 데이터 정책 준수 3항목 · 개인정보 URL 저장 완료
- 무료 · 공개 · 전체 155개 지역 선택 상태 확인
- 콘솔의 ‘항목이 저장되었습니다’와 테스트 안내 저장 완료 표시를 확인함
- 심사 제출/실제 공개 여부는 따로 확인하며 항목 ID만으로 설치 가능한 공개 링크라고 표시하지 않음

제출 ZIP SHA-256 `5efded799b6c8a24fed772aef7ef216c4524aa3f57e67c466783154a0d4b933e` · 20724 bytes

일반 설치 ZIP 두 개 SHA-256 `b105e2a95f821714c47eebacba707025092fe0bd81e9c694507e67f4fd989ac0` · 각 21218 bytes · 바이트 동일

공식 절차: https://developer.chrome.com/docs/webstore/publish
ZIP 규칙: https://developer.chrome.com/docs/webstore/prepare
등록 화면 요구사항: https://developer.chrome.com/docs/webstore/cws-dashboard-listing
로컬 데이터 처리 공개: https://developer.chrome.com/docs/webstore/program-policies/user-data-faq
