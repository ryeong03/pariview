# 연구 기반 추천 연결

`python3 ai/server.py`로 API와 `web/dist` 정적 파일을 같은 origin에서 제공함
Python 표준 라이브러리만 사용하며 서버는 파일이나 사용자 응답을 디스크에 쓰지 않음

## Railway 환경변수

| 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | 사용자가 Railway 서버 환경에 직접 등록하는 Claude API 키 |
| `PARIVIEW_AI_ENABLED` | `1` |
| `PARIVIEW_AI_MODEL` | `claude-haiku-5-5` |
| `HOST` | 기본 `0.0.0.0` |
| `PORT` | Railway 제공값 또는 기본 `8080` |
| `PARIVIEW_AI_MAX_CALLS_PER_HOUR` | 선택 사항 · 기본 `60` |

모델은 환경변수로 명시하며 코드가 다른 모델을 자동 선택하지 않음
`claude-haiku-5-5`는 공식 문서에서 확인한 분류·선택 작업용 연결 예시이며 실제 계정의 접근 권한과 호출 성공은 배포 후 확인 필요
키는 프런트 코드·정적 파일·요청 본문·로그에 포함하지 않음

- [Claude 모델 공식 문서](https://platform.claude.com/docs/en/models/overview)
- [Claude Structured Outputs 공식 문서](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

## 동작과 근거 경계

1. 사용자가 고른 불편·환경·선호와 현재 설정, 세션 내 비교 응답을 정해진 선택지로 검증
2. `web/dist/recommendation-data.json`의 검토된 후보에서 해당하는 설정과 다음 비교 목록 구성
3. AI가 연결돼 있으면 서버에서만 Anthropic Messages API 호출 · 외부 도구와 웹 검색 없음
4. 모델은 후보 ID와 다음 비교 ID만 출력 · 임의 문장·논문·수치·추가 필드 거부
5. 설정값·설명·출처 ID는 로컬 카탈로그에서 재구성하고 사용자에게 미리보기·수정·취소 제공
6. 사용자가 적용 버튼을 누른 경우에만 기존 앱의 저장 hook 실행

Claude에는 `output_config.format`으로 JSON Schema를 전달하고 지원하지 않는 `maxItems`는 제거함
응답 완료 상태와 후보의 유효성, 중복 여부, 최대 3개 제한은 서버에서 다시 검사
`stop_reason`이 `refusal` 또는 `max_tokens` 등으로 끝난 응답은 기본 제안으로 전환

카탈로그의 R1·M1·M2·M3·M5는 기존 `research/sources.json`과 `research/medical-sensory-sources.json`에 존재하는 ID와 URL을 사용
연구는 개인차·환경 조절·비교 절차를 참고한 설계 근거이며 제안 수치와 조합, AI 추천 성능 또는 의료효과를 검증한 것이 아님
배경음 분리와 장면 전환 완화 등 현재 목업 기능은 추천 변경 대상에서 제외
기존 선택·무차이·건너뛰기는 해당 축의 자동 변경과 재질문에서 제외하고 판단 유보는 별도 취급

연결 미설정·실패·지연·한도 초과 시 준비된 규칙 결과로 이어지며 오류 팝업은 없음
기본 결과의 표시는 `연구 기반 기본 제안`이고 실제 공급자 응답이 검증된 경우만 `AI 추천`
`configured: true`는 환경변수 준비 여부이며 실제 인증 성공 판정이 아님

## HTTP 계약

- `GET /healthz` → 상태 200
- `GET /api/recommendation/status` → `configured`, `provider`, `evidenceVersion`, `defaultAvailable`
- `POST /api/recommendation` → `source`, `status`, `selection`, `settings`, `actions`, `nextComparison`, `sources`, `boundary`
- 요청 Content-Type은 `application/json` · 최대 16 KiB · 브라우저는 same-origin만 허용

요청 예시

```json
{
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
python3 -m unittest ai.test_recommendation -v
HOST=127.0.0.1 PORT=4189 python3 ai/server.py
uv run --with playwright python web/validate_recommendation.py
```

도메인·공급자 모의응답 13개 테스트와 프런트·서버 정책 61개 입력 일치 검사
브라우저는 기본 제안·수정·취소·저장·다음 비교·모의 AI 성공/실패와 390/768/1440 화면, 실제 app 통합 hook 검사
실제 Claude 호출과 실제 사용자 효과 평가는 이 테스트 결과에 포함되지 않음
