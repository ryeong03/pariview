# poster/tools

- `adaptive_chart.py` — 적응형 피팅 평가 그래프를 포스터 색·글꼴(형광 플랫, 글로 없음)로 SVG 생성. 입력 `research/adaptive-fitting/simulation-results.json`(합성 데이터·조건별 500), 출력 `poster/assets/adaptive-chart.svg`와 인라인용 fragment
- `apply_v10.py` — v10 초안 적용 스크립트(카드 01 적응형 문구, 3섹션 적응형 흐름 띠 + 그래프, 구조도 캡션, 카드 스택 130→126mm). **적응형 피팅 엔진이 공개 앱에 연결된 뒤에만 실행**하고, 실행 후 `poster/render.py`와 검사 스크립트를 돌려요
