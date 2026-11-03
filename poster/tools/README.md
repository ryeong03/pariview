# poster/tools

- `adaptive_chart.py` — 적응형 피팅 평가 그래프를 포스터 색·글꼴(형광 플랫, 글로 없음)로 SVG 생성. 입력 `research/adaptive-fitting/simulation-results.json`(합성 데이터·조건별 500), 출력 `poster/assets/adaptive-chart.svg`와 인라인용 fragment
- `autofit.py` — 포스터 블록(header, #s1~#s4, #s5가 있으면 포함) 높이를 잠시 풀어 실측하고, A1 예산 안이면 남는 높이를 #s2에 몰아 고정해요. 넘치면 `OVER by N`만 출력하고 파일은 안 바꿔요. 로컬 서버 `python3 -m http.server 4195`를 저장소 루트에서 띄운 뒤 실행해요
