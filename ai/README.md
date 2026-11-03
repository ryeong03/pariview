# 연구 기반 추천 연결

`python3 ai/server.py`로 API와 `web/dist` 정적 파일을 같은 origin에서 제공함
Python 표준 라이브러리만 사용하며 서버는 파일이나 사용자 응답을 디스크에 쓰지 않음

## Railway 환경변수

| 이름 | 값 |
|---|---|
| `ANTHROPIC_BASE_URL` | 선택 사항 · 학교 LiteLLM 사용 시 `<학교 게이트웨이 주소>` · 로컬 예시 `http://localhost:4000` · 없으면 Anthropic 직접 연결 |
| `ANTHROPIC_AUTH_TOKEN` | 선택 사항 · 학교 LiteLLM Virtual Key · 게이트웨이에서 이 값이 있으면 우선 사용 |
| `ANTHROPIC_API_KEY` | Anthropic 직접 연결용 API 키 · 게이트웨이에서는 기존 Railway 값을 Virtual Key 호환 입력으로 사용 가능 |
| `PARIVIEW_AI_ENABLED` | `1` |
| `PARIVIEW_AI_MODEL` | 공급자가 허용한 정확한 모델 이름 · 학교 권장 `claude-sonnet-4-6` · 가벼운 시험 `claude-haiku-4-5-20251001` |
| `HOST` | 기본 `0.0.0.0` |
| `PORT` | Railway 제공값 또는 기본 `8080` |
| `PARIVIEW_AI_MAX_CALLS_PER_HOUR` | 선택 사항 · 기본 `60` |
| `PARIVIEW_AI_DEBUG` | 선택 사항 · `1`이면 공급자 호출 실패 시 `provider_error <예외> status=<HTTP 코드> type=<Anthropic 오류 종류>` 한 줄만 로그에 남김 · 응답 본문·키·사용자 문장은 남기지 않음 · 원인 확인 후 끄기 |

모델은 환경변수로 명시하며 코드가 다른 모델을 자동 선택하지 않음
학교 연결은 LiteLLM이 제공하는 Anthropic Messages 호환 `/v1/messages`를 사용하고 Virtual Key를 `Authorization: Bearer`로 전달함
공급자 응답의 HTTP 리다이렉트는 거부하여 Bearer 토큰이나 API 키가 다른 URL로 자동 전달되지 않게 함
`ANTHROPIC_AUTH_TOKEN`이 비어 있으면 현재 `ANTHROPIC_API_KEY` 값을 학교 Virtual Key로 재사용하므로 기존 Railway 비밀값을 복사하거나 읽을 필요가 없음
`ANTHROPIC_BASE_URL`이 없으면 `https://api.anthropic.com/v1/messages`와 `x-api-key`를 사용하는 기존 Anthropic 직접 연결을 유지함
공급자 상태는 학교 게이트웨이면 `litellm`, 직접 연결이면 `anthropic`으로 표시하며 URL이나 인증값은 반환하지 않음
준비된 후보 ID만 고르는 작업이라 `output_config.effort`는 `low`, thinking 토큰을 포함해 `max_tokens`는 4000으로 둠
`output_config.format`의 JSON Schema와 `effort`는 Messages 요청 본문에 함께 보내며 최종 후보는 공급자와 무관하게 서버에서 다시 검증함
키는 프런트 코드·정적 파일·요청 본문·로그에 포함하지 않음 · 붙여넣을 때 들어간 앞뒤 공백·줄바꿈·따옴표는 서버가 제거함

- [Claude 모델 공식 문서](https://platform.claude.com/docs/en/models/overview)
- [Claude Structured Outputs 공식 문서](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [LiteLLM Claude Code 연결 공식 문서](https://docs.litellm.ai/docs/proxy/client_setup/claude_code)
- [LiteLLM 게이트웨이 클라이언트 공식 문서](https://docs.litellm.ai/docs/proxy/client_setup/overview)
- [LiteLLM Messages `output_config` 공식 예시](https://docs.litellm.ai/docs/providers/bigmodel#anthropic-messages-api)
- [LiteLLM `output_config.format` 호환 변경 기록](https://docs.litellm.ai/release_notes/v1.107.0rc1/v1-107-0-rc-1)

## 동작과 근거 경계

1. 사용자가 고른 불편·환경·선호와 현재 설정, 세션 내 비교 응답을 정해진 선택지로 검증하고 선택 입력 `experience`를 양끝 공백 제거 후 최대 300자로 검증
2. `web/dist/recommendation-data.json`의 검토된 후보에서 해당하는 설정과 다음 비교 목록 구성 · 문장이 있으면 AI 경로에서만 선택지 매칭 조건을 풀고 기존 제외 조건과 비교 이력은 유지
3. AI가 연결돼 있으면 서버에서만 Anthropic Messages API 호출 · 문장은 사용자 역할 메시지의 `experience` 데이터로 전달 · 외부 도구와 웹 검색 없음
4. 모델은 후보 ID·다음 비교 ID·허용된 시작 모드 ID만 출력 · 임의 문장·논문·수치·추가 필드 거부
5. 설정값·설명·출처 ID는 로컬 카탈로그에서 재구성하고 사용자에게 미리보기·수정·취소 제공
6. 사용자가 적용 버튼을 누른 경우에만 기존 앱의 저장 hook 실행

Claude에는 `output_config.format`으로 JSON Schema를 전달하고 지원하지 않는 `maxItems`는 제거함
응답 완료 상태와 후보의 유효성, 중복 여부, 최대 3개 제한은 서버에서 다시 검사
`stop_reason`이 `refusal` 또는 `max_tokens` 등으로 끝난 응답은 기본 제안으로 전환
문장은 시스템 프롬프트에 삽입하지 않고 untrusted user data로 명시하며, 문장 안 명령·역할 변경·진단 요청을 따르지 않도록 지시함
서버는 모델 출력의 허용 목록을 별도로 검증하며 서로 다른 후보가 같은 설정을 다른 값으로 바꾸는 충돌도 거부함

시작 모드는 카탈로그 `startingModes`의 검증된 5개 ID와 현재 모드를 뜻하는 `keep`만 사용
문장이 비어 있거나 `goal: original` 또는 규칙 결과이면 `keep`만 허용
모드를 고르면 `profileId`와 선택된 action의 검증된 변경값만 병합하며 모드 프리셋 전체를 덮어쓰지 않음
예를 들어 `폭발 장면에서 깜짝 놀라요`에 대한 모의 Claude 응답 `gentle` + `sound_changes`는 음량 변화 완화와 시연 영상 사전 안내를 켜고 기존 음량·밝기·자막 색상은 유지함
시연 영상의 장면 안내는 기존 준비된 데이터를 사용하며 유튜브 사전 분석이나 새로운 영상 분석 기능을 뜻하지 않음

카탈로그의 R1·M1·M2·M3·M5는 기존 `research/sources.json`과 `research/medical-sensory-sources.json`에 존재하는 ID와 URL을 사용
연구는 개인차·환경 조절·비교 절차를 참고한 설계 근거이며 제안 수치와 조합, AI 추천 성능 또는 의료효과를 검증한 것이 아님
배경음 분리와 장면 전환 완화 등 현재 목업 기능은 추천 변경 대상에서 제외
기존 선택·무차이·건너뛰기는 해당 축의 자동 변경과 재질문에서 제외하고 판단 유보는 별도 취급
사용자가 선택한 `captionYellow`는 추천·미리보기·적용 과정에서 유지하며 색상은 AI 추천 대상에 포함하지 않음
이 값이 없는 이전 저장 설정은 기본 흰색으로 처리

연결 미설정·실패·지연·한도 초과 시 준비된 규칙 결과로 이어지며 오류 팝업은 없음
기본 결과의 표시는 `연구 기반 기본 제안`이고 실제 공급자 응답이 검증된 경우만 `AI 추천`
규칙 결과는 경험 문장을 해석하거나 키워드로 매핑하지 않으며 원래 선택 항목과 설정만 사용함
문장을 적었지만 기본 제안으로 돌아간 경우 프런트는 `적은 문장은 이번 제안에 반영되지 않았어요`로 안내함
`configured: true`는 환경변수 준비 여부이며 실제 인증 성공 판정이 아님

## HTTP 계약

- `GET /healthz` → 상태 200
- `GET /api/recommendation/status` → `configured`, `provider`, `evidenceVersion`, `defaultAvailable`
- `POST /api/recommendation` → `source`, `status`, `selection`, `settings`, `actions`, `nextComparison`, `startingMode`, `sources`, `boundary`
- 요청 Content-Type은 `application/json` · 최대 16 KiB · 브라우저는 same-origin만 허용

요청 예시

```json
{
  "experience": "폭발 장면에서 깜짝 놀라요",
  "currentSettings": {"brightness":85,"volume":35},
  "answers": {
    "concerns":["light","changes"],
    "goal":"softer",
    "room":"dim",
    "device":"headphones",
    "captionStyle":"keep"
  },
  "comparisons":[{"axis":"volume","outcome":"equal"}],
  "useAI":true
}
```

`experience`는 선택적 문자열이며 `{"experience":"폭발 장면에서 깜짝 놀라요"}`만 보내도 기존 선택 필드 기본값으로 처리함
문자 수는 Unicode code point 기준이고 양끝 공백 제거 뒤 300자까지 허용함
누락·빈 문자열은 기존 동작이며 `null`·배열·객체·숫자·300자 초과·잘못된 Unicode는 HTTP 400 `{"error":"invalid_request"}`로 응답함
서버는 입력 문장을 응답이나 로그·파일에 남기지 않으며 정상 AI 요청일 때만 Anthropic에 전달함

`selection`은 `actionIds`, `nextComparisonId`, `startingModeId`로 구성함
예전 두 필드 selection은 `startingModeId: keep`으로 정규화하지만 문장이 있는 AI 응답에서 모드가 빠지면 잘못된 응답으로 처리함
`startingMode`는 로컬 카탈로그의 `{id,title,en}` 객체이며 현재 모드 유지이면 `null`
`actions[].matched`는 문장 입력 AI 경로에서 기존 선택지에 매칭되는 후보인지 나타내는 서버 구성값이며 모델 설명문이 아님

`useAI: false`면 연결 여부와 무관하게 규칙 결과만 반환
운영 기본값은 단일 프로세스당 동시 AI 요청 1건과 시간당 최대 60건이며 재시작 시 초기화되는 PoC 제한
서버 요청 timeout 10초, 재시도 없음, 실패 후 30초 동안 기본 제안 사용
브라우저 대기 한도 12초 이후에도 준비된 기본 제안으로 진행
정적 서버는 `web/dist`만 공개하며 폴더 목록·상위 경로·심볼릭 링크 탈출을 차단하고 HEAD 및 영상 Range 요청을 지원

## UI 연결

```js
import {initRecommendation} from './recommendation.js';
initRecommendation({getSettings, getComparisons, onPreview, onCancelPreview, onApply, onCompare});
```

- `[data-action="ai-recommend"]` 또는 `[data-recommendation-entry]`에서 열림
- 모듈이 dialog와 전용 스타일을 생성
- `getSettings()` → 현재 설정 복사본
- `getComparisons()` → 최대 20개 `{axis,outcome}` · `a`, `b`, `equal`, `unsure`, `skip`
- `onPreview(next)` → 원래 상태를 한 번 보관하고 임시 반영 · 저장 금지
- `onCancelPreview()` → 원래 설정·원본 모드·음소거·재생 위치 복원
- `onApply(next, meta)` → 사용자가 확정한 경우에만 저장
- `onCompare(axis, next, meta)` → 저장 없이 추천 초안에서 기존 A/B 비교 시작
- `meta`에는 결과 방식·근거 버전·출처 ID·다음 비교·사용자 수정 여부 포함

## 검증

```sh
python3 -m unittest ai.test_recommendation ai.test_experience_http ai.test_static_gzip -v
HOST=127.0.0.1 PORT=4189 python3 ai/server.py
uv run --with playwright python web/validate_recommendation.py
```

도메인·공급자 모의응답·로컬 HTTP 계약 테스트와 프런트·서버 규칙 및 AI 정책 정합 검사
300자·Unicode·잘못된 타입·텍스트 단독 요청, 프롬프트 주입 문자열의 데이터 분리, 잘못된 모드/출처/수치/추가 문장, 후보 간 충돌, 공급자 거부·잘못된 JSON·시간 초과·미설정·한도·동시 요청을 검사
노란 자막 켜기·끄기·이전 저장 형식이 규칙 제안·모의 AI·공급자 실패에서도 유지되는지 검사
브라우저는 기본 제안·수정·취소·저장·다음 비교·모의 AI 성공/실패와 390/768/1440 화면, 실제 app 통합 hook 검사
실제 Claude 호출과 실제 사용자 효과 평가는 이 테스트 결과에 포함되지 않음
