# PariView

화면과 소리, 내가 정하면 안 되나요?

감각 프로필을 선택하고 실제 영화 장면을 비교해 시청 설정을 고르는 캡스톤 프로토타입

## 실행

Python 3가 설치된 환경에서 다음 명령을 실행한 뒤 http://127.0.0.1:4178 을 연다

```sh
python web/serve.py
```

`web/serve.py`는 동영상 구간 이동을 위한 HTTP Range 요청을 지원한다
정적 웹 소스는 `web/dist`에 있으며 설치나 빌드가 필요하지 않다

## 구성

- `web/dist`: 사용자 웹, Three.js·Anime.js 입체 로고, GSAP 전환
- `research/literature-review.txt`: 논문 결과와 설계 추론, 적용 한계
- `research/sources.json`: 서지 및 확인 기록
- `PariView_A1.html`: 편집 가능한 포스터 소스
- `render.py`: A1 PDF 출력 및 규격 확인

PariView의 임상 효과나 감각 역치를 검증한 결과가 아니다
반복 비교는 현재의 선호를 찾는 과정이며 설정은 브라우저에만 저장된다
영화는 Blender Foundation의 CC BY 3.0 작품 Tears of Steel의 공식 제공 파일을 발췌한 것이다
소재와 라이브러리 출처는 웹의 credits.html에 기록한다
