PariView 대상 수상 사례와 100점 심사 대응 전략
최종 조사 기준일 2026-11-04

읽을 자료
- PariView_Award_Strategy.pdf: A4 13쪽 상세 보고서
- strategy.html: 같은 내용을 목차·출처 링크로 읽는 보고서
- sources.json: 대상 사례 10건, 비교 포스터 2건, 공식 기존 기능, 100점 심사표의 확인 원장
- validation.json: 페이지 넘침·폰트·링크·PDF 규격 점검
- ../../handoff/POSTER_STRATEGY_100.txt: 포스터 편집자용 짧은 전달문

범위
서울대·KAIST·연세대·고려대·이화여대 관련 공개 수상 사례의 표적 검토
기관 공식 자료 8건 + 수상자 직접 기록 1건 + 사용자 제공 강의 자료 1건의 대상 사례
직접 살펴본 포스터는 제공 PDF의 대상·최우수·우수 3점
대학 전체 수상작 전수조사나 수상 원인의 통계 분석으로 부르지 않음
PariView 감각 연구 17건(학술논문 11편·전문자료 6건)과 별도 집계

사용자 우선순위
100점 심사표 우선 / 수업 PDF는 구성 참고
기존 비교 → 차별점 → 이용자 가치 한 행 유지
SINGCHRONIZE의 전체 수직 흐름 참고
상단 장식 영상·캐릭터 / 감각 프로필 나열 / GitHub QR 카드 제거 방향
큰 핵심 솔루션과 심사에 필요한 정보만 남기고 상세 근거는 기존 웹 링크로 연결
사업화는 도입·구매 주체와 제공 단위 중심으로 설명
앱·A1 포스터 파일은 이 조사에서 편집하지 않음

재생성
프로젝트 루트에서 다음 명령을 각각 실행
/opt/anaconda3/bin/python3.12 research/award-patterns/build_report.py
/opt/anaconda3/bin/python3.12 research/award-patterns/render_report.py

빌드 입력
sources.json, 기존 연구 원장 2개, web/dist/assets/Pretendard 폰트
원본 강의 PDF가 있으면 11–13쪽에 포함된 포스터 이미지를 그대로 추출
원본 PDF가 없으면 assets/의 추출 이미지를 사용
사진 편집·생성, 앱 빌드, 서버 배포, Git 커밋은 수행하지 않음

실험 자료와의 관계
analysis/user-study/field-kit은 별도 제공용 빈 설문·실험 서식
이 문서는 그 실험을 실시했다고 주장하거나 결과를 생성하지 않음
당사자 참여 검증 완료에 관한 사용자 확인은 research/sources.json의 별도 항목에 보관
