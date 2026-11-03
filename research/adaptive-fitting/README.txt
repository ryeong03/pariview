PariView 적응형 선호 피팅 연구 패키지
2026-11-04

핵심 결과
실제 웹 엔진을 사용해 적응형 비교와 고정 비교를 같은 5회 예산에서 평가함
모델 일치 조건의 평균 정규화 절대오차: 고정0.1498 / 적응형0.1381
큰 응답 변동 조건에서는 짝 차이의 합성95%구간이0을 포함함
5회는 초기 탐색 예산이며 최적값 도달이나 사람의 편안함을 보장하는 횟수와 구분

보여줄 자료
comparison-overview.png / .pdf / .svg — 주 비교와 다섯 조건을 함께 보여주는 그림
all-conditions.png — 조건별0~5회 전체 곡선
RESULTS.txt / simulation-results.json — 평균·구간·오차기준 충족률·posterior 포함률
RESEARCH_BASIS.txt / sources.json — 직접 확인한 학술자료3편과 적용 범위
CONTRACT.txt — 수학 모델·질문 선택·무차이 처리·종료·평가 계약

데이터
synthetic-records.jsonl.gz — 합성 선호점, 제시쌍, 실제 배치, 선택, 단계별 추정·오차·구간
simulation-metadata.json — seed·생성 조건·엔진 및 설정 코드SHA256
500개의 동일 합성 선호점을 다섯 조건에서 재사용, 총2500개의 조건별 사례
각 사례에서 adaptive와 fixed를 함께 실행해 짝 비교
실제 참여자 자료는0건이며 기존 사용자 확인 참여 검증의 수치로 해석하지 않음

주 비교의 공정성
두 방식은 범위·prior·반응 likelihood·5회 예산·posterior 추정기를 공유
adaptive는 이후 질문을 선택에 따라 정함; fixed는 미리 정한 질문 순서·수치 사용
질문 발급 순서가 다를 수 있으므로 횟수별 결과를 모두 보여줌
동일 합성 선호점과 응답 난수를 사용하되 A/B 좌우 배치 난수는 분리
밝기·대비·음량 세 축의 평균 정규화 절대오차(NMAE)를 계산
곡선의95%구간은 합성 사례 bootstrap2000회; 실제 이용자 모집단의 신뢰구간이 아님
기존 앱의 숫자3회+boolean2회는 원시 로그와 최종JSON의 별도 참고값으로만 보존
그 기준선은 정보량과 추정기가 달라 주 비교 그래프에 함께 올리지 않음

재생성 (저장소 루트)
node research/adaptive-fitting/simulate.mjs
/opt/anaconda3/bin/python3.12 research/adaptive-fitting/analyze_simulation.py
엔진은 ../../web/dist/adaptive-fit.js를 직접 import; 별도 복제 구현으로 성능을 계산하지 않음
시뮬 도중 엔진 파일이 바뀌면 종료하고 같은 버전으로 다시 실행

새 실제 기록의 분석 경로
HUMAN_RECORDING.txt — 같은 장면·조건·순서 교차·독립 참조값 기록 방법
human-trials-template.csv / human-reference-template.csv — 헤더만 있는 빈 양식
import_snapshot.py — 실제 엔진 snapshot을 익명 참여코드와 함께 CSV로 변환
analyze_human.py — 반복 참조값과의 거리 분석, 빈 양식에서는 그래프를 생성하지 않음

예: 실제 수집 후 사용
python3 research/adaptive-fitting/import_snapshot.py private/P01-adaptive.json --participant-code P01 --order AF
python3 research/adaptive-fitting/analyze_human.py --trials research/adaptive-fitting/private/trials.csv --references research/adaptive-fitting/private/references.csv
실제 자료는 연구 디렉터리의 private/에 보관하며 Git에서 제외

포스터에 쓸 수 있는 문구
이전 선택으로 선호 범위를 갱신하고, 다음 A/B 비교를 고르는 적응형 피팅
5회로 시작하고, 더 맞추고 싶으면 5회 추가
그래프 표제: 합성 데이터 시뮬레이션 · 조건별500개 선호점
기술 자체의 최초 발명, 5회 수렴 보장, 임상효과 또는 수집하지 않은 당사자 오차로 표현하지 않음
