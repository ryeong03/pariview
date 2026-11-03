"""Build the sourced award-case review, not the A1 poster or application."""
import html
import json
from pathlib import Path
import fitz

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = json.loads((HERE / 'sources.json').read_text())
CASES = {s['id']: s for s in DATA['cases']}
PDF = Path(DATA['local_materials'][0]['path'])
ASSETS = HERE / 'assets'
ASSETS.mkdir(exist_ok=True)
if PDF.exists():
    with fitz.open(PDF) as doc:
        for pno in (11, 12, 13):
            image = max(doc[pno - 1].get_images(full=True), key=lambda x: x[2] * x[3])
            extracted = doc.extract_image(image[0])
            (ASSETS / f'guide-p{pno}.{extracted["ext"]}').write_bytes(extracted['image'])

def e(value):
    return html.escape(str(value), quote=True)

def link(label, url):
    return f'<a href="{e(url)}">{e(label)}</a>'

def cite(*ids):
    return '<span class="citations">' + ' '.join(link(f'[{i}]', f'#source-{i}') for i in ids) + '</span>'

def table(headings, rows, cls=''):
    return f'<table class="{cls}"><thead><tr>' + ''.join(f'<th>{h}</th>' for h in headings) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join(f'<td>{c}</td>' for c in row)+'</tr>' for row in rows) + '</tbody></table>'

def card(title, body, cls=''):
    return f'<article class="card {cls}"><h3>{title}</h3>{body}</article>'

def refimage(pno, cls=''):
    images = sorted(ASSETS.glob(f'guide-p{pno}.*'))
    if not images:
        raise FileNotFoundError(f'Provide original course PDF or extracted image for page {pno}')
    return f'<img class="reference-image {cls}" src="assets/{images[0].name}" alt="사용자가 제공한 강의 자료 {pno}쪽 포스터">'

PAGES = []
def page(title, eyebrow, body, cls=''):
    n = len(PAGES) + 1
    PAGES.append(f'<section class="page {cls}" id="page-{n}"><header><span>PariView / AWARD CASE REVIEW</span><span>2026.11.04 · 조사·제안 자료</span></header><main><div class="eyebrow">{eyebrow}</div><h1>{title}</h1>{body}</main><footer><span>100점 심사표 우선 · 수상 사례에서 관찰한 내용과 PariView 적용 제안을 구분</span><span>{n} / TOTAL</span></footer></section>')

page('대상을 목표로,<br>심사 근거가 바로 보이는 포스터', '01 / 조사 결론', f'''
<p class="lead">PariView의 중심은 <strong>의학·감각 연구에서 출발해<br>사용자가 자기 시청 설정을 찾아가는 흐름</strong>이에요</p>
<div class="statement">기존 기능 비교 → PariView의 차별점 → 이용자 가치</div>
<p>이 한 행을 먼저 읽고, 바로 아래 큰 실제 화면에서 같은 내용을 확인하게 구성해요 포스터에는 심사에 필요한 핵심만 남기고 상세 연구·기술·검증은 기존 웹 링크에서 이어 읽도록 해요</p>
<div class="numbers"><div><b>10</b><span>공개자료로 확인한 대상 사례</span></div><div><b>3</b><span>직접 살펴본 포스터 이미지</span></div><div><b>65점</b><span>차별성·다학제·사회기여/사업화</span></div></div>
<h2>이번 분석에서 제안하는 다섯 가지</h2>
<ol class="spaced"><li><strong>차별점은 ‘선호를 찾는 과정’으로</strong><br>같은 장면 비교, 설정 저장, 시청 중 재조절을 한 경험으로 연결해요</li>
<li><strong>연구는 기능으로 이어지는 화살표로</strong><br>개인차·환경 조절·사용자 통제가 각각 어느 조작에 반영됐는지 보여줘요</li>
<li><strong>작동 장면은 큰 화면 세 개로</strong><br>선호 비교 → 개인 설정 → 시청 중 재조절·지원 영상 적용 순서예요</li>
<li><strong>검증은 실제 확인한 항목으로</strong><br>작동 기록과 당사자 의견의 역할을 각각 보여주고, 측정값에는 이름과 조건을 붙여요</li>
<li><strong>도입 모델에는 비용을 내는 주체까지</strong><br>교육·기관용 시청 환경의 운영자와 플랫폼 사업자가 무엇을 도입할지 제안해요</li></ol>
<p class="note">대상 사례는 기관 공식 기록 8건, 참여자 직접 기록 1건, 제공 강의자료 1건이에요 추가 포스터 2점은 최우수·우수 사례로 따로 분석했어요 위 결론은 사례 관찰과 사용자 심사표를 함께 읽어 도출한 제안이에요 {cite('G1','G2')}</p>
''', 'cover')

case_rows = []
for s in DATA['cases']:
    source_type = {'institutional_primary':'기관 공식','participant_primary':'수상자 직접 기록','user_supplied_course_material':'제공 강의자료'}[s['source_type']]
    year = s['year_label'].replace('제공 PDF p11 / 수상 연도 미표기', '연도 미표기')
    case_rows.append([f'<b>{e(s["university"])}</b><br><small>{e(year)}</small>', f'<b>{e(s["team"])}</b><br>{e(s["project"] or "해당 작품명 미제공")}', f'{e(s["event"])}<br><b>{e(s["award"])}</b>', f'{source_type}<br>{cite(s["id"])}'])
page('어떤 대상 사례를 확인했나요', '02 / 5개 대학 관련 수상 사례', table(['대학·시점','팀·작품','행사·수상 범위','확인 출처'], case_rows, 'case-table') + '''
<div class="two"><div class="callout"><h3>대학과 행사의 관계</h3><p>대부분은 그 대학 학생·팀의 수상 사례예요 절대감자는 서울대 개최 행사 사례이며 팀의 대학 소속은 본문에 없어요</p></div><div class="callout"><h3>확인한 범위</h3><p>작품 설명과 심사 방식이 충분한 사례를 중심으로 해석했어요 연세드론·Ku쿠하세요는 공개 글만으로 작품의 상세 기술까지 평가하지 않았어요</p></div></div>
<p class="note">조사 기간이나 대회 목록을 고정한 전수조사가 아니라 공개자료를 바탕으로 한 표적 사례 검토예요 수상작의 개별 심사 점수와 비수상작 대조 자료는 확보하지 않았어요</p>
''')

page('공개 심사 기준에서 읽히는 것', '03 / 관찰과 적용 제안', table(['공식 자료에 공개된 평가','PariView에 가져올 준비'], [
    [f'<b>Scamper 수상 대회</b><br>창의성·사회기여·완성도·기술력·발표력<br><small>서면 → 면접 발표 → 종합 심사</small> {cite("A04")}', '기능 차별성과 사회적 사용 장면을 함께 설명하고, 작동하는 산출물로 뒷받침해요'],
    [f'<b>2025 세종 DX 해커톤</b><br>완성도·사업화·기술성·독창성·적합성·전달력<br><small>부스 시연 → 상위 팀 발표</small> {cite("A07")}', '한 번에 이해되는 시연과 도입 제안을 동시에 준비해요'],
    [f'<b>제3회 보조기기 끝장 개발대회</b><br>필요성·적합성·시작품·기대효과 등<br><small>대상 이해 교육·전문가 멘토링 포함</small> {cite("A06")}', '누구의 어느 불편을 해결하는지, 그 이해가 어떤 기능 선택으로 이어졌는지 보여줘요']
], 'criteria-table') + f'''
<h2>작품 설명에서 뽑은 네 가지 관찰</h2>
<div class="two">
{card('① 문제의 대상과 순간이 구체적이에요', '<p>회로 초보자의 측정 순서, 시청각 장애인의 정보 접근, 학내 의견 전달 통로처럼 사용 상황이 드러나요</p>'+cite('A01','A06','A09'))}
{card('② 기술의 결과가 다음 행동으로 이어져요', '<p>측정 결과는 다음 측정 위치로, 교통 분석은 휴게소 위치 제안으로 이어져요</p>'+cite('A01','A08'))}
{card('③ 기능과 사용 흐름을 함께 보여줘요', '<p>공 모양 장치의 알림·조종이나 GOGO GOLEM!의 세 가지 놀이처럼 사용자가 무엇을 하는지 보이게 해요</p>'+cite('A04','A10'))}
{card('④ 발표 뒤 질문까지 준비할 여지가 커요', '<p>시흥 행사에서는 발표 7분 뒤 질문 8분을 배정했어요 구현과 도입 조건을 별도 자료로 준비할 이유예요</p>'+cite('A02'))}
</div>
<div class="callout"><b>이번 분석의 결론</b><p>포스터·시연·답변 자료에서 같은 주장이 같은 근거로 연결되도록 만들어요 이 연결을 PariView의 심사 대응 전략으로 제안해요</p></div>
''')

page('GOGO GOLEM!에서 가져올 한 행', '04 / 대상 포스터 상세 읽기', f'''
<div class="poster-analysis"><figure>{refimage(11)}<figcaption>제공 강의자료 p11 · 트리오링고<br>대상 / 산학 {cite('A10','G1')}</figcaption></figure><div>
<h2>상단에서 한 번에 답해요</h2><p>기존 아동 콘텐츠와의 비교, 핵심 차별점, 이용자에게 기대하는 변화가 수평으로 이어져요 화살표의 출발과 끝이 명확해요</p>
<h2>체험 장면이 중심이에요</h2><p>말하기·손동작·편지라는 세 행동을 큰 화면으로 보여줘요 사용자 행동을 먼저 보고 아래의 처리 흐름을 읽을 수 있어요</p>
<h2>기술 설명의 위치가 좋아요</h2><p>각 행동에 대응하는 구현 질문과 흐름이 가까이 있어요 여러 기술이 어느 체험을 만드는지 쉽게 연결돼요</p>
<h2>PariView에 적용하면</h2><p>같은 장면을 비교하는 화면, 고른 설정이 적용된 화면, 영상 아래에서 다시 조절하는 화면을 같은 크기로 배치해요</p>
</div></div>
<h2>요청하신 한 행을 PariView 문장으로</h2>
<div class="flow"><div><small>기존 기능</small><b>대사 강조 · 섬광 완화<br>밝기·음량 조절</b></div><span>→</span><div><small>PariView의 접근</small><b>같은 장면을 비교해<br>나의 시청 설정 찾기</b></div><span>→</span><div><small>이용자 가치</small><b>직접 고르고 저장해<br>필요할 때 다시 조절</b></div></div>
<div class="callout"><b>최신 편집 방향 · 핵심 솔루션에 공간을 줘요</b><p>상단 장식 영상·캐릭터, 다섯 프로필 나열, GitHub QR 카드를 빼고 비교·적용·재조절 화면을 크게 배치해요 긴 설명은 웹으로 옮기고 각 화면에는 행동과 결과를 설명하는 한 문장만 남겨요</p></div>
<p class="note">이 행은 PariView의 선택 과정을 선명하게 보여주기 위한 제안이에요 GOGO GOLEM!에 실린 기대효과는 그 팀의 주장과 해당 맥락으로 읽었어요</p>
''')

page('SINGCHRONIZE의 전체 흐름도 가져와요', '05 / 최우수·우수 포스터 비교', f'''
<div class="poster-analysis"><figure>{refimage(12)}<figcaption>제공 PDF p12 · All Day Project<br>최우수상 / 산학 {cite('P12','G1')}</figcaption></figure><div>
<h2>위에서 아래로 질문이 바뀌어요</h2><ol class="spaced compact"><li><b>왜 필요한가</b><br>배경·문제·차별점을 세 칸으로 제시</li><li><b>어떻게 쓰는가</b><br>녹음 → 추천 리포트 → 버스킹의 큰 화면</li><li><b>어떻게 만드는가</b><br>특징 추출과 추천 파이프라인을 분리</li><li><b>어디로 이어지는가</b><br>시스템·기대효과·확장 방향·체험 QR</li></ol>
<p>PariView는 상단을 GOGO GOLEM!의 한 행으로 바꾸고, 그 아래를 이 수직 흐름으로 연결하면 돼요</p>
</div></div>
<div class="two bottom-example"><figure>{refimage(13, 'small-ref')}<figcaption>PDF p13 · OptimusPrime<br>우수상 / 연구 {cite('P13')}</figcaption></figure><div><h2>연구형 포스터의 장점도 보완해요</h2><p>OptimusPrime은 측정 방법과 결과 그래프를 가까이 놓았어요 PariView 감각 지도에도 <b>시간축·영상 구간·측정량·단위</b>를 붙여 기술 근거로 읽히게 해요</p><p class="note">두 사례의 상격은 각각 최우수·우수예요 사례에 실린 설문 수치·가중치·오차 수치는 PariView의 결과와 별개예요</p></div></div>
''')

rubric_rows = [
    ['창의·융합성<br><b>25점</b>', '기존 기능을 넘어 어떤 경험을 제안하나요', '실제 기존 기능과 비교 → 같은 장면 비교·저장·재조절의 연결', '상단 한 행 + 실제 A/B 화면'],
    ['기획성<br><b>10점</b>', '처음 보는 사람이 순서대로 이해하나요', '하나의 제목, 세 단계 체험, 읽을 근거와 체험 QR', '상단에서 15초 개요 / 시연 진입'],
    ['기술성·완성도<br><b>15점</b>', '왜 그렇게 설계했고 실제로 어떻게 작동하나요', '사용자 설정 → CSS·Web Audio → 출력 / 영상 측정 → 지도·예고', '간단한 처리도·측정 단위·작동 기록'],
    ['다학제적 접근성<br><b>20점</b>', '각 분야가 어느 설계 결정을 바꿨나요', '감각 연구 → 조절 필요 / HCI → 비교·복귀 / 신호처리 → 변화 표시', '연구 → 설계 → 기능의 연결 표'],
    ['성실도·홍보효과<br><b>5점</b>', '어떤 과정과 역할로 완성했나요', '문제 파악 → 문헌 검토 → 구현 → 당사자 의견·기능 점검', '실제 구성원별 역할과 수정 이력'],
    ['사회기여·사업화<br><b>20점</b>', '누가 도움을 받고 누가 도입·구매하나요', '이용자–기관 운영자–플랫폼을 구분 / 제공 범위와 도입 단위', '도입 모델·수익 구조 제안'],
    ['미래 신산업<br><b>5점</b>', '행사 공고의 어느 분야와 연결되나요', '디지털 미디어 접근성·개인화 SW의 실제 역할을 기술', '공고의 5대 분야명 확인 후 정합성 표시']
]
page('100점 심사표를 이렇게 채워요', '06 / 평가 항목과 증거의 연결', table(['항목·배점','심사 질문으로 읽기','PariView의 답','보여줄 자료'], rubric_rows, 'rubric-table')+'''
<div class="callout"><b>우선 보강할 65점</b><p>차별성 25점, 다학제 20점, 사회기여·사업화 20점에 집중해요 같은 기능을 세 번 반복하기보다, 각각 <b>무엇이 다른지 / 왜 그렇게 설계했는지 / 누가 도입할지</b>로 답을 나눠요</p></div>
<p class="note">배점은 사용자 제공 심사표 그대로예요 점수 예측이나 임의의 합격선을 제시하지 않았어요 PDF p9의 수업용 40점 기준은 구성 점검에 참고하고 합산하지 않아요</p>
''')

page('비교표는 실제 제공 기능에서 출발해요', '07 / 창의·융합성 25점', table(['확인한 예','실제 제공 기능','PariView에서 강조할 접근'], [
    [f'<b>Prime Video<br>Dialogue Boost</b> {cite("C1")}', '배경 음악·효과음 대비 대사를 강조해요 이용자가 제공된 단계를 선택해요', '같은 장면을 비교하며 소리와 화면의 시작 설정을 함께 찾아요'],
    [f'<b>Apple<br>Dim Flashing Lights</b> {cite("C2")}', '섬광 감지 시 영상을 어둡게 해요 지원 미디어의 재생 타임라인에 섬광 구간도 표시해요', '소리·빛 변화 정보를 조절 화면과 연결하고, 사용자가 예고와 설정을 선택해요'],
    ['<b>PariView 현재 구현</b>', '5단계 비교·직접 조절·저장·원본 비교·재피팅과 지원 영상용 확장 기능을 연결해요', '핵심 차별점은 지금의 선호를 찾고 유지·수정하는 사용 과정이에요']
], 'comparison-table')+'''
<p class="note">앞의 두 행은 공식 문서에 나온 기능 예시예요 해당 브랜드의 전체 접근성 기능을 평가한 표는 아니에요 기능 부재를 단정하는 ○·× 대신 실제 확인한 동작을 적어요</p>
<h2>포스터 한 행에 바로 넣을 문구</h2>
<div class="copy-flow"><article><h3>기존 기능 비교</h3><p>대사를 강조하고<br>섬광을 완화하는 기능이 있어요</p><small>Prime Video · Apple 공식 자료</small></article><span>→</span><article><h3>PariView의 차별점</h3><p>같은 장면을 비교하며<br>빛·소리·자막 설정을 골라요</p><small>선호 비교 → 적용 → 재조절</small></article><span>→</span><article><h3>이용자 가치</h3><p>내가 고른 설정으로 보고<br>필요할 때 바로 바꿔요</p><small>저장 · 원본 비교 · 재피팅</small></article></div>
<h2>제목과 설명의 역할</h2><div class="callout"><b>같은 이야기를, 나에게 맞는 시청 설정으로</b><p>의학·감각 연구를 바탕으로 같은 장면을 비교하고, 빛·소리·자막을 직접 조절하는 시청 선호 피팅 서비스</p></div>
<p>‘최초’나 ‘모든 서비스보다 우수’ 같은 범위 큰 표현 대신, 실제 시연으로 확인할 수 있는 차별점을 제목 가까이에 두는 제안이에요</p>
''')

page('17건의 근거가 설계를 바꾸는 지점', '08 / 다학제적 접근성 20점', '''
<div class="count-band"><b>학술논문 11편 + 전문자료 6건</b><span>의학·감각 평가 자료의 표적 검토 · 수상 사례 조사와 별도</span></div>
''' + table(['연구·평가 관점','설계 해석','현재 기능과 확인할 것'],[
    [f'<b>개인·상황별 감각 경험</b><br>MacLennan 등, 2022<br>자폐 성인 49명 자기보고 {cite("R1")}', '한 번 고른 값을 고정하기보다 지금의 선호를 다시 고를 수 있게 해요', 'A/B 비교·재피팅<br><small>다시 비교하려는 이유와 장면별 차이</small>'],
    [f'<b>개인별 환경 조정</b><br>NICE CG142<br>성인 자폐 지원 지침 {cite("M5")}', '빛·소리·휴식 조건을 개인의 필요에 맞춰 선택하게 해요', '화면·소리 항목별 조절<br><small>어떤 항목을 바꾸고 유지하는지</small>'],
    [f'<b>감각 변화의 직접 통제</b><br>Unwin 등, 2022<br>자폐 아동 41명 감각실 비교 {cite("R2")}', '사용자에게 선택·건너뛰기·되돌리기 권한을 줘요', '수정·원본 비교·복귀<br><small>원하는 상태로 스스로 돌아갈 수 있는지</small>'],
    [f'<b>시각 비교·소리 내성 구분</b><br>AAO·ASHA 자료 {cite("M1","M3")}', '가독성과 편안함, 전체 음량과 특정 소리의 반응을 나눠 살펴봐요', '같은 장면 비교·항목별 질문<br><small>선호 응답을 통한 설정 탐색</small>'],
    [f'<b>시청각 반응의 차이</b><br>Matsuzaki 등, 2022<br>7–14세 남아 46명 뇌자도 {cite("R3")}', '시청각 경험을 단일 평균값으로 다루지 않는 관점에 참고해요', '소리·빛을 구분한 정보 제공<br><small>측정 신호와 사용자 판단을 함께 살펴보기</small>']
], 'research-table')+'''
<h2>큰 글씨로 남길 세 원칙</h2>
<div class="principles"><p><b>개인차</b> 감각 경험은 개인과 상황에 따라 달라요</p><p><b>환경 조절</b> 빛과 소리를 개인의 필요에 맞춰 조절해요</p><p><b>사용자 선택</b> 설정의 선택과 변경은 사용자가 결정해요</p></div>
<p class="note">관찰·지침에서 설계 원칙으로 이어지는 해석이에요 구체적인 5단계·프로필 숫자는 팀의 제품 설계예요 ‘학술논문 17편’ 대신 ‘논문 11편·전문자료 6건을 검토한 설계’로 표기해요</p>
''')

page('작동을 설명하는 증거를 가까이 둬요', '09 / 기술성·완성도 15점', '''
<div class="flow wide"><div><small>사용자 입력</small><b>비교 응답·직접 조절</b></div><span>→</span><div><small>적용</small><b>화면 필터·소리 처리</b></div><span>→</span><div><small>출력과 선택</small><b>같은 영상·복귀·저장</b></div></div>
''' + table(['기술 경로','포스터에 남길 설명','상세 자료에서 확인할 것'],[
    ['화면', '밝기·대비·채도 등 선택 값을 화면 필터로 적용해요', 'CSS filter 적용값·원본 비교와 기본값 초기화의 차이'],
    ['소리', '고음 완화·말소리 EQ·음량 압축·출력을 조절해요', 'Web Audio 처리 순서·수치 범위·지원 영상 조건'],
    ['영상 신호', '소리 크기와 프레임 밝기 변화로 지도와 예고 구간을 만들어요', 'EBU R128 라우드니스·평균 Y값·시간축·구간 규칙'],
    ['확장 연결', '저장한 설정을 PC Chrome의 지원 영상에 적용해요', '상태 저장·적용·끄기·원상복귀·페이지 이동 기록'],
    ['추천 경로', '연구 카탈로그의 시작 후보와 이유를 제안하고 사용자가 확정해요', 'AI 응답 검증·기본 제안 전환·출처 표시 / 선택권 유지']
], 'technical-table')+'''
<h2>결과와 기록은 질문에 맞춰 꺼내요</h2>
<div class="two"><div class="callout"><h3>작동하나요</h3><p>현재 README와 확장 검증 기록에는 32개 항목 통과가 정리돼 있어요 영상 적용·상태·원상복귀 같은 실제 동작을 보여줘요</p><small>이 보고서에서는 해당 검사를 재실행하지 않고 기록과 구현을 확인했어요</small></div><div class="callout"><h3>당사자가 사용했나요</h3><p>사용자가 확인한 ‘신경다양성 당사자 참여 검증 완료’를 유지해요 인원·항목·점수는 원장에 제공된 정보 범위에 맞춰 관리해요</p><small>새 10명 field-kit은 별도 제공용 설문·실험 서식이에요</small></div></div>
<h2>부스 시연 제안 · 약 60초</h2><p><b>10초</b> 같은 장면 두 설정 보기 → <b>20초</b> 편한 쪽 선택·적용 → <b>20초</b> 보면서 한 항목 수정·원본 비교 → <b>10초</b> 저장·지원 영상 적용 확인</p>
<p class="note">지원 조건은 짧은 각주로, 긴 구현 설명과 검증 항목은 QR로 연결해요 지도·예고의 기준은 영상 신호 변화 규칙으로 이름 붙이고 개인의 의학적 역치처럼 표시하지 않아요</p>
''')

page('사회기여와 사업화를 한 모델로', '10 / 사회기여·사업화 가능성 20점', '''
<p class="lead">사용자는 자기 시청 설정을 고르고,<br>기관은 그 선택 환경을 제공하는 모델을 제안해요</p>
''' + table(['역할','1차 도입 가설','제공 가치'],[
    ['이용자', '영상 학습·교육을 이용하는 감각 민감 성인, 신경다양성 당사자', '같은 콘텐츠를 보며 자신의 화면·소리·자막 설정을 선택해요'],
    ['도입 담당자', '대학 학습지원·장애학생지원 담당자, 교육 영상 운영자, 성인 복지·평생교육 기관', '지원 가능한 영상과 설치 환경을 정하고 이용 안내·설정 사용을 지원해요'],
    ['구매·계약 주체', '교육기관 또는 영상 플랫폼 운영사', '기관 이용권, 플레이어 연동, 호환성 유지·지원 범위에 비용을 지급하는 구조를 검토해요']
], 'business-table')+'''
<h2>왜 이 순서로 제안하나요</h2><p>현재의 웹 플레이어와 지원 영상용 확장 기능에서 시작할 수 있고, 도입 기관이 관리하는 영상 환경에서 지원 범위를 구체화할 수 있어요 DRM을 포함한 대형 OTT 연동은 후속 파트너 협의·기술 검증 단계로 두는 제안이에요</p>
<h2>판매 단위를 이렇게 구분해요</h2>
<div class="three"><div class="card"><h3>기관 이용권</h3><p>기관·운영 규모별 연간 계약과 업데이트 지원</p></div><div class="card"><h3>초기 연동</h3><p>플레이어 연결·환경 설정·설치 안내 비용</p></div><div class="card"><h3>운영 지원</h3><p>브라우저·플레이어 변경 대응과 호환성 점검</p></div></div>
<p class="note">위 항목은 수익 구조 제안이에요 현재 계약·판매·연동 SDK 보유를 뜻하지 않아요 구체 가격은 설치·지원 시간과 구매 담당자의 도입 조건을 확인한 뒤 정해요</p>
<h2>경제성을 확인할 계산 틀</h2><div class="formula"><b>기관당 기여이익</b> = 연간 계약액 + 연동 매출 − 직접 연동·운영·지원 비용<br><b>도입 가능한 연간 매출</b> = 실제 지원 가능한 기관 수 × 확인한 기관당 계약액</div>
<p>이용 의향 83%는 관심을 보여주는 팀 설문 결과로 사용해요 유료 구매 의향·실제 계약 전환율은 구매 담당자 인터뷰에서 별도로 확인할 항목이에요</p>
''')

page('도입 제안을 실행 과제로 바꿔요', '11 / 사업화·수행 과정·신산업', table(['단계','준비할 산출물','다음 단계로 넘어갈 근거'],[
    ['1 · 설치·시연', '지원 브라우저·영상 범위, 기관용 안내, 원상복귀 시연', '담당자가 환경을 설치하고 이용자에게 설명할 수 있는지'],
    ['2 · 기관 파일럿', '동의·평가 절차, 개인 설정 과제, 담당자 지원 기록', '이용자의 실제 사용 의견·반복 사용·운영 부담과 수정 사항'],
    ['3 · 플랫폼 연동', '플레이어 모듈 규격, 동기화·접근성·지원 조건, 운영 계약', '플랫폼별 재생·DRM·성능·복원 검증과 구매 조건']
], 'roadmap-table')+'''
<p class="note">세 단계는 제안한 사업 경로예요 현재 완료된 설치나 계약 건수로 표현하지 않아요</p>
<div class="two"><div><h2>수요 인터뷰의 핵심 질문</h2><ul class="spaced compact"><li>영상 시청 중 어떤 요청이나 불편 신고가 생기나요</li><li>지금은 어떤 도구·지원 인력으로 대응하나요</li><li>연동할 플레이어와 구매 결정자는 누구인가요</li><li>파일럿 성공 여부를 무엇으로 판단하나요</li><li>설치·보안·지원·예산 조건은 무엇인가요</li></ul></div><div><h2>사회기여를 확인할 항목</h2><ul class="spaced compact"><li>자기 설정을 찾고 되돌리는 과제 수행</li><li>시청 중 불편한 지점과 재조절 이유</li><li>설정 유지·반복 사용 경험</li><li>지원 담당자의 안내·대응 부담</li><li>영상·기기별로 다른 이용 경험</li></ul></div></div>
<h2>지식재산·차별화 검토</h2><p>같은 장면의 선호 비교, 설정 저장·이식, 영상 신호와 사용자 조절의 연결 중 무엇이 구체적인 독자 구성인지 정리해요 그다음 선행기술·공개 이력을 조사해 권리화 검토 항목을 좁혀요 현재 출원이나 독점 기술로 표기할 단계는 아니에요</p>
<h2>역할과 미래 분야를 표시할 때</h2><p>실제 팀원의 연구·UI·신호처리·확장·배포·검증 기여를 산출물 옆에 짧게 적어요 미래 분야는 우선 <b>디지털 미디어 접근성·개인화 소프트웨어</b>로 설명하고, 행사 공고에 정해진 5대 신산업의 명칭을 확인해 정확히 대응시켜요</p>
<p class="note">제공된 심사표에는 5대 분야의 구체 목록이 없어요 의료 효과나 미래 기능을 더해 분야를 맞추기보다, 현재 동작하는 제품의 연결 지점을 설명하는 제안이에요</p>
''')

page('발표와 질문도 같은 근거로 이어져요', '12 / 전시·발표 실행안', '''
<h2>6분 발표 배분 제안</h2>
''' + table(['시간','보여줄 곳','전할 내용'],[
    ['0:00–1:10','문제·설문', '같은 영상에서도 빛·소리에 대한 필요가 다름 → 팀 설문에서 나타난 관련 기능 수요'],
    ['1:10–2:10','상단 한 행', '기존 대사·섬광 기능을 인정하고, 선호를 찾는 비교·저장·재조절 과정을 설명'],
    ['2:10–3:10','연구 원칙·도입 모델', '개인차·환경 조절·선택권이 기능과 도입 환경으로 이어지는 이유'],
    ['3:10–4:40','큰 화면·시연', '선호 비교 → 적용 → 시청 중 수정·원본 비교·저장'],
    ['4:40–5:30','처리도·확인 기록', '출력 처리와 영상 신호 분석, 실제 기능 확인과 당사자 참여'],
    ['5:30–6:00','핵심 문장·QR', '나에게 맞는 설정을 스스로 찾고 이어 쓰는 접근성 경험']
], 'talk-table')+'''<p class="note">사용자 PDF의 권장 구성인 배경 3–4분, 시나리오 1–2분, 구조·결과 약 1분을 6분으로 배치한 안이에요 실제 행사 발표 제한 시간이 있으면 그 시간을 우선해요</p>
<h2>심사 질문에 답할 준비</h2>
''' + table(['예상 질문','답의 중심'],[
    ['기존 밝기 조절과 무엇이 달라요', '같은 장면 비교로 선택을 돕고, 여러 항목을 저장·재조절·지원 영상 적용으로 연결해요'],
    ['연구 17건이 무엇을 뒷받침하나요', '개인차·환경 조절·사용자 통제의 설계 원칙이에요 연구 대상·방법과 화면에 연결한 해석을 보여줘요'],
    ['어떻게 작동하나요', '설정값이 화면 필터·소리 처리에 반영되는 경로와 원본 복귀를 바로 시연해요'],
    ['누가 구매하나요', '교육기관·영상 플랫폼을 구매 주체로 제안해요 운영자 인터뷰와 파일럿으로 연동·지원 조건을 확인할 계획이에요'],
    ['참여자 평가 결과는요', '완료 확인과 실제 제공된 기록 범위로 답해요 세부 인원·항목·점수는 원자료 확인 뒤 자료에 추가해요']
], 'qa-table')+'''
<div class="callout"><b>포스터 담당자에게 넘길 우선순위</b><p>비교 한 행 → 큰 솔루션 화면 → 연구 원칙 → 검증·도입 모델 순서예요 상단 장식·프로필 나열·GitHub QR은 덜어내요 자세한 구조와 근거는 웹으로 연결하고, 포스터의 작은 설명은 줄여요</p></div>
''')

refs = []
for s in DATA['cases']:
    label = f'{s["id"]} · {s["university"]} · {s["team"]}'
    if s['url']:
        location = link(s['publisher']+' 원문 ↗', s['url'])
    else:
        location = '사용자 제공 강의 PDF p11 · 포스터 시각 확인'
    refs.append(f'<article class="reference" id="source-{s["id"]}"><b>{e(label)}</b><p>{e(s["event"])} · {e(s["award"])}</p><small>{location}</small></article>')
for s in DATA['competitors']:
    refs.append(f'<article class="reference" id="source-{s["id"]}"><b>{e(s["id"])} · {e(s["name"])}</b><p>{link("공식 기능 설명 ↗", s["url"])}</p></article>')
core = json.loads((ROOT/'research/sources.json').read_text())
medical = json.loads((ROOT/'research/medical-sensory-sources.json').read_text())
for s in core['sources'] + medical['sources']:
    if s['id'] in {'R1','R2','R3','M1','M3','M5'}:
        refs.append(f'<article class="reference" id="source-{s["id"]}"><b>{e(s["id"])} · {e(s.get("year") or s.get("corporate_author") or "전문자료")}</b><p>{link(s["title"],s["url"])}</p></article>')
page('출처와 확인 범위', '13 / 원문 바로가기', '<div class="references">'+''.join(refs)+'</div>'+f'''
<div class="local-refs"><p id="source-G1"><b>G1 · 사용자 제공 강의 PDF</b> CapstoneDesign-Poster preparation (1).pdf, 13쪽<br>p5–8 구성·시연·발표 / p9 수업 평가 / p11–13 수상 포스터</p><p id="source-G2"><b>G2 · 사용자 제공 심사표 이미지</b> 25·10·15·20·5·20·5점, 총 100점</p><p id="source-P12"><b>P12</b> All Day Project / SINGCHRONIZE, 최우수·산학, G1 p12</p><p id="source-P13"><b>P13</b> OptimusPrime, 우수·연구, G1 p13</p></div>
<p class="note">A08의 2020년 표기는 {link('대회 자료 목록','https://github.com/molit-korea/main/blob/master/README.md')} 및 {link('DACON 운영자 인터뷰','https://dacon.io/competitions/official/235622/talkboard/409240')}로 교차 확인했어요 A09는 수상자 직접 기록이며 기관 공식 심사평으로 분류하지 않았어요</p>
<p class="note">원장: sources.json · 기존 감각 자료: ../sources.json, ../medical-sensory-sources.json<br>실험·설문 제공용 빈 서식: ../../analysis/user-study/field-kit/ · 편집 전달문: ../../handoff/POSTER_STRATEGY_100.txt</p>
''', 'reference-page')

CSS = r'''
@font-face{font-family:Pretendard;src:url('../../web/dist/assets/Pretendard-Regular.woff2');font-weight:400}
@font-face{font-family:Pretendard;src:url('../../web/dist/assets/Pretendard-SemiBold.woff2');font-weight:600}
@font-face{font-family:Pretendard;src:url('../../web/dist/assets/Pretendard-Bold.woff2');font-weight:700 900}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#e9edf2;color:#202330;font:14px/1.65 Pretendard,sans-serif;print-color-adjust:exact;-webkit-print-color-adjust:exact}a{color:#204ac9;text-decoration:none;overflow-wrap:anywhere}a:hover{text-decoration:underline}h1,h2,h3,p,figure{margin:0}h1{font-size:29px;line-height:1.35;letter-spacing:-.7px;margin:6px 0 18px;word-break:keep-all}h2{font-size:17px;line-height:1.5;margin:18px 0 8px;letter-spacing:-.3px}h3{font-size:14px;margin-bottom:6px}p,li,td{word-break:keep-all;overflow-wrap:anywhere}p+p{margin-top:10px}strong,b{font-weight:700}small,.note{font-size:11px;line-height:1.6;color:#5c6374}.note{margin-top:12px}small{display:inline-block}.page{width:210mm;height:297mm;padding:12mm 14mm 17mm;margin:18px auto;background:white;position:relative;break-after:page;overflow:hidden}.page:last-child{break-after:auto}.page>header{display:flex;justify-content:space-between;font-size:9px;color:#667083;border-bottom:1px solid #dce1ea;padding-bottom:9px;margin-bottom:20px}.page>footer{position:absolute;bottom:9mm;left:14mm;right:14mm;font-size:8.5px;display:flex;justify-content:space-between;border-top:1px solid #dce1ea;padding-top:8px;color:#667083}.eyebrow{font-size:11px;font-weight:600;letter-spacing:.7px;color:#3560bd}.lead{font-size:18px;line-height:1.65;letter-spacing:-.3px;color:#434b5b}.cover h1{font-size:34px}.statement{background:#19172b;color:white;padding:18px;border-radius:9px;margin:22px 0 16px;font-size:18px;font-weight:700;text-align:center}.numbers{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0}.numbers>div{border:1px solid #dce1ea;border-radius:8px;padding:14px}.numbers b{display:block;font-size:29px;line-height:1.4;color:#ef2456}.numbers span{font-size:11px;color:#5c6374}.spaced{padding-left:22px;margin:8px 0}.spaced li+li{margin-top:10px}.spaced li{font-size:14px;line-height:1.65}.compact li{font-size:13px}.two{display:grid;grid-template-columns:1fr 1fr;gap:15px}.three{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.card{padding:13px 15px;background:#f5f7fb;border-radius:8px;margin:0 0 12px}.card p{font-size:12.5px;line-height:1.7}.callout{background:#f4f6fb;border-left:3px solid #315ad2;padding:13px 16px;margin-top:14px}.callout p{font-size:13px;line-height:1.7;margin-top:4px}.citations{font-size:10.5px;white-space:nowrap;margin-left:3px}.citations a{margin-right:2px}.card .citations{display:block;margin:7px 0 0}.flow{display:grid;grid-template-columns:1fr 20px 1fr 20px 1fr;gap:5px;align-items:stretch;margin:15px 0}.flow>div{border:1px solid #d8deeb;border-radius:8px;padding:14px 12px}.flow>span{align-self:center;text-align:center;color:#4662ab}.flow small{display:block;margin-bottom:6px}.flow b{font-size:13px;line-height:1.6}.flow>div:nth-of-type(2){background:#f0f4ff;border-color:#c8d6fa}.flow>div:nth-of-type(3){background:#fff3f7;border-color:#f4d6e0}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:12px;line-height:1.65;margin:10px 0 15px}thead th{font-size:11px;background:#eef2f9;padding:9px 8px;text-align:left;vertical-align:top}td{padding:9px 8px;vertical-align:top;border-bottom:1px solid #dfe4ee}td:first-child{font-weight:600}td small{font-weight:400;font-size:10px}.case-table{font-size:11px;line-height:1.6}.case-table th:nth-child(1){width:15%}.case-table th:nth-child(2){width:32%}.case-table th:nth-child(3){width:36%}.case-table th:nth-child(4){width:17%}.case-table td{padding:9px 6px}.case-table small{font-size:9.5px}.criteria-table th:first-child{width:52%}.rubric-table{font-size:12px}.rubric-table th:nth-child(1){width:17%}.rubric-table th:nth-child(2){width:25%}.rubric-table th:nth-child(3){width:34%}.rubric-table th:nth-child(4){width:24%}.rubric-table td{padding:10px 7px}.poster-analysis{display:grid;grid-template-columns:43% 1fr;gap:21px;margin-top:8px}.reference-image{width:100%;display:block;border:1px solid #d8deeb}.poster-analysis h2:first-child{margin-top:0}.poster-analysis h2{font-size:16px;margin-top:14px}.poster-analysis p{font-size:13px}.poster-analysis li{font-size:13px}.poster-analysis .spaced{padding-left:18px}figcaption{font-size:10px;line-height:1.6;color:#6b7280;margin-top:6px}.bottom-example{grid-template-columns:28% 1fr;align-items:center;margin-top:18px;gap:22px}.small-ref{max-height:220px;width:auto;max-width:100%;margin:auto}.bottom-example h2{margin-top:0}.bottom-example p{font-size:13px}.comparison-table th:first-child{width:24%}.copy-flow{display:grid;grid-template-columns:1fr 18px 1fr 18px 1fr;gap:5px;align-items:center;margin:14px 0 19px}.copy-flow article{height:180px;background:#19172b;color:white;border-radius:9px;padding:14px 11px}.copy-flow article:nth-of-type(2){background:#244cb3}.copy-flow article:nth-of-type(3){background:#991b40}.copy-flow h3{font-size:13px;margin-bottom:13px}.copy-flow p{font-size:13px;line-height:1.8}.copy-flow small{display:block;color:#dce4ff;font-size:9px;margin-top:12px}.copy-flow>span{color:#556578}.count-band{display:flex;flex-direction:column;background:#19172b;color:white;border-radius:9px;padding:15px 18px;margin-bottom:16px}.count-band b{font-size:19px}.count-band span{font-size:11px;color:#dce3f5;margin-top:4px}.research-table th:nth-child(1){width:35%}.research-table th:nth-child(2){width:33%}.research-table th:nth-child(3){width:32%}.principles{border-top:1px solid #dfe4ee;margin-top:10px;padding-top:6px}.principles p{font-size:14px;padding:5px 0}.principles b{display:inline-block;width:90px;color:#284fbb}.technical-table th:first-child{width:15%}.technical-table th:nth-child(2){width:41%}.technical-table th:nth-child(3){width:44%}.business-table th:first-child{width:18%}.business-table th:nth-child(2){width:40%}.business-table th:nth-child(3){width:42%}.formula{padding:14px 16px;background:#f5f7fb;border:1px solid #dfe4ee;border-radius:8px;font-size:12px;line-height:1.9;margin:8px 0 13px}.roadmap-table th:first-child{width:21%}.talk-table th:first-child{width:17%}.talk-table th:nth-child(2){width:23%}.talk-table th:nth-child(3){width:60%}.qa-table{font-size:11.5px}.qa-table th:first-child{width:30%}.qa-table td{padding:7px 8px}.references{display:grid;grid-template-columns:1fr 1fr;gap:11px 20px}.reference{font-size:10.5px;line-height:1.5;break-inside:avoid}.reference p{font-size:10px;margin-top:3px;word-break:normal}.reference small{font-size:9.5px}.reference-page h1{margin-bottom:15px}.reference-page .note{font-size:10px;line-height:1.5}.local-refs{padding-top:11px;margin-top:13px;border-top:1px solid #dce1ea}.local-refs p{font-size:10px;line-height:1.5}.local-refs p+p{margin-top:4px}.report-nav{position:sticky;top:0;background:#19172b;color:white;text-align:center;z-index:10;padding:11px;font-size:12px}.report-nav a{color:#dbe6ff;margin:0 10px}.page main{padding-bottom:2px}
@page{size:A4;margin:0}@media print{body{background:white}.page{margin:0}.report-nav{display:none}}@media screen and (max-width:820px){.report-nav{min-width:210mm}.page{margin:0 0 12px}}
'''
nav = '<nav class="report-nav">'+''.join(link(label,f'#page-{n}') for n,label in [(1,'결론'),(2,'수상 사례'),(4,'포스터 분석'),(6,'100점 대응'),(10,'사업화'),(13,'출처')])+'</nav>'
output = '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PariView 대상 수상 사례와 100점 심사 대응 전략</title><style>'+CSS+'</style></head><body>'+nav+''.join(PAGES).replace('/ TOTAL',f'/ {len(PAGES)}')+'</body></html>'
(HERE/'strategy.html').write_text(output)
print(json.dumps({'pages':len(PAGES),'cases':len(DATA['cases']),'rubric_total':sum(x['points'] for x in DATA['rubric']),'output':str(HERE/'strategy.html')},ensure_ascii=False))
