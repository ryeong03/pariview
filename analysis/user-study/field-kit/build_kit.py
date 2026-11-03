"""Build blank, printable study materials; never generate participant responses."""
from pathlib import Path
import csv, html, json, random
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).resolve().parent
SUS = [
 '이 서비스를 자주 사용하고 싶어요',
 '이 서비스는 쓸데없이 복잡해요',
 '이 서비스는 쓰기 쉬워요',
 '이 서비스를 쓰려면 기술을 잘 아는 사람의 도움이 필요할 것 같아요',
 '이 서비스의 여러 기능이 잘 어우러져 있어요',
 '이 서비스는 일관되지 않은 부분이 너무 많아요',
 '대부분의 사람이 이 서비스를 금방 배울 것 같아요',
 '이 서비스는 쓰기 번거로워요',
 '이 서비스를 쓰는 데 자신감이 있었어요',
 '이 서비스를 쓰기 전에 배워야 할 것이 많았어요',
]
RATINGS = [
 ('comfort','방금 본 장면을 전체적으로 얼마나 편안하게 시청했나요?','매우 불편했어요','매우 편안했어요'),
 ('visual','방금 본 장면의 화면을 보는 것이 얼마나 편안했나요?','매우 불편했어요','매우 편안했어요'),
 ('audio','방금 본 장면의 소리를 듣는 것이 얼마나 편안했나요?','매우 불편했어요','매우 편안했어요'),
 ('caption','방금 본 장면의 자막을 읽는 것이 얼마나 쉬웠나요?','매우 어려웠어요','매우 쉬웠어요'),
]
orders = ['AB']*5 + ['BA']*5
random.Random(20261104).shuffle(orders)
ALLOC = [{'id':f'U{i+1:02d}','planned_order':o} for i,o in enumerate(orders)]

CSS = '''
@font-face{font-family:PV;src:url('../../../web/dist/assets/Pretendard-Regular.woff2')}
@font-face{font-family:PV;src:url('../../../web/dist/assets/Pretendard-Bold.woff2');font-weight:700}
@page{size:A4;margin:0}*{box-sizing:border-box}body{margin:0;background:#e9edf1;color:#17202d;font-family:PV,sans-serif;font-size:11pt;line-height:1.5}
.page{width:210mm;min-height:297mm;height:297mm;padding:16mm 17mm 19mm;background:white;position:relative;margin:8mm auto;break-after:page}
.page:last-child{break-after:auto}.content{display:flow-root}h1{font-size:27pt;line-height:1.16;margin:4mm 0 5mm;letter-spacing:-.8px}h2{font-size:18pt;line-height:1.3;margin:3mm 0 5mm}h3{font-size:12pt;margin:5mm 0 2mm}p{margin:2mm 0}li{margin:1.5mm 0}ul,ol{padding-left:5mm;margin:2mm 0 4mm}.eyebrow{font-size:9pt;font-weight:700;letter-spacing:1px;color:#b51f45}.lead{font-size:13pt}.box{padding:4mm;border:1px solid #ced7e0;border-radius:3mm;margin:3mm 0}.tint{background:#f2f6fa}.small{font-size:9pt;color:#46505d}.tiny{font-size:8pt;color:#46505d}.grid{display:grid;grid-template-columns:1fr 1fr;gap:4mm}.rule{border-top:1px solid #d6dce3;margin:4mm 0}.blank{min-height:13mm;border-bottom:1px solid #aeb7c1}.write{min-height:30mm;border:1px solid #c8d1db;border-radius:2mm;margin:2mm 0 4mm}.footer{position:absolute;left:17mm;right:17mm;bottom:10mm;border-top:1px solid #d5dce3;padding-top:2mm;display:flex;justify-content:space-between;font-size:8pt;color:#57616d}table{border-collapse:collapse;width:100%;font-size:10pt;margin:3mm 0}th,td{border:1px solid #c6d0da;padding:2.4mm;text-align:left;vertical-align:top}th{background:#f0f4f8}.scale{display:flex;justify-content:space-between;margin:4mm 0 1mm}.scale span{border:1px solid #8793a1;width:12mm;height:12mm;border-radius:50%;display:grid;place-items:center;font-size:13pt}.anchors{display:flex;justify-content:space-between;font-size:10pt}.question{margin:7mm 0 9mm}.sus td:first-child{width:68%}.sus td:not(:first-child),.sus th:not(:first-child){text-align:center}.sus td{padding:2.5mm}.idline{display:flex;justify-content:space-between;border-bottom:2px solid #17202d;padding-bottom:3mm;margin-bottom:6mm}.check{line-height:1.9}a{color:#23569a;overflow-wrap:anywhere}.steps td:first-child{white-space:nowrap}.nowrap{white-space:nowrap}@media print{body{background:white}.page{margin:0}}
'''

CSS += '.steps td{padding:1.6mm;line-height:1.35;font-size:9.5pt}'

def table(head, rows, cls=''):
 return '<table class="'+cls+'"><thead><tr>'+''.join('<th>'+str(x)+'</th>' for x in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table>'

def document(title,pages):
 body=''.join(f'<section class="page"><div class="content"><div class="eyebrow">PARIVIEW · FIELD KIT v1.0</div>{p}</div><div class="footer"><span>{title} · 2026.11.04 · 제공용 빈 서식</span><span>{i+1} / {len(pages)}</span></div></section>' for i,p in enumerate(pages))
 return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>'+title+'</title><style>'+CSS+'</style></head><body>'+body+'</body></html>'

protocol=[]
protocol.append('''<h1>당사자 10명과 살펴보는<br>PariView 시청 경험</h1><p class="lead">기본 설정과 개인 설정으로 같은 장면을 보고<br>편안함과 사용성을 각각 기록해요</p>
<div class="box tint"><b>이 자료의 용도</b><p>신경다양성 당사자 성인 10명에게 제공할 실험·설문 서식이에요<br>이미 진행했다고 사용자가 확인한 당사자 검증과는 별도의 문서예요<br>여기에는 실제 참여자의 응답이나 평가 결과를 넣지 않았어요</p></div>
<h3>확인할 질문</h3><ol><li>같은 장면에서 기본 설정과 개인 설정의 시청 편안함은 어떻게 다른가요?</li><li>참여자는 피팅을 직접 완료하고, 설정을 바꾸거나 되돌릴 수 있나요?</li><li>어느 화면이나 조작에서 개선이 필요한가요?</li></ol>
<h3>대상과 운영</h3><ul><li>만 19세 이상, 본인을 신경다양성 당사자로 설명하는 성인 10명</li><li>당사자 여부는 자기보고로 확인하고 진단명·진단서·복약 정보는 받지 않아요</li><li>한국어 안내와 문항에 본인의 의사를 표현할 수 있는 분을 모집해요<br>평소 쓰는 보조기기, 글로 답하기, 동행 지원을 사용할 수 있어요</li><li>1명씩 약 20–25분, 휴식은 필요에 따라 더해요</li><li>10명 모집은 이번 점검의 운영 규모예요 대상 전체의 효과를 추정하는 검정력 계산에서 정한 수가 아니에요</li></ul>
<h3>필요한 준비물</h3><p>같은 노트북·브라우저·음향기기, 분리된 Chrome 프로필 2개, 타이머<br>참여자 설문지 10부, 기록표, 조용하고 조명을 조절할 수 있는 자리</p>
<div class="box"><b>시작 전 기입</b><p>담당자·연락처 _________________________________</p><p>실시 날짜·장소 _________________________________</p><p>자료 보관 종료일 _______________________________</p><p class="small">학교 프로젝트의 모집·동의·자료 관리 절차를 확인하고 빈칸을 채워요</p></div>''')

protocol.append('''<h2>비교 조건을 먼저 고정해요</h2>'''+table(['구분','조건'],[
 ('A · 기본 설정','앱에서 <b>기본값으로 초기화</b>한 뒤 공통 통제를 적용해요<br>밝기 85 · 대비 90 · 소리 35 · 음량 변화 완화 ON · 쉬운 자막 OFF'),
 ('B · 개인 설정','<b>직접 설정하기</b>로 시작 모드와 5단계 A/B 비교를 완료한 결과예요<br>모드에 포함된 정적 화면·소리·자막 설정을 함께 반영해요'),
 ('양쪽 공통','장면 자동 맞춤 OFF · 어두운 장면 자동 보정 OFF · 빛·소리 예고 OFF · 휴식 알림 OFF · 자막 ON · 재생 속도 1배'),
 ('장면','피팅 연습: Tears of Steel 45초 발췌<br>평가: <b>Sintel 발췌 영상 00:00–00:45 전체</b>를 A와 B에서 동일하게 사용해요'),
 ('환경','같은 화면 크기·거리·실내 조명·OS 밝기·OS 음량·음향기기를 두 조건에서 유지해요')])+
'''<p class="small">A는 필터를 우회하는 ‘원본 비교’와 달라요 ‘원본 비교’를 A 조건으로 쓰지 않아요<br>이 비교는 고정된 개인 설정 묶음에 관한 점검이에요 자동 장면 보정·예고·AI 추천의 효과는 이 절차에서 측정하지 않아요</p>
<h3>두 설정이 섞이지 않게 준비해요</h3><ol><li>같은 Chrome 버전의 서로 다른 프로필 A·B를 열어요 일반 탭 두 개는 저장값을 공유하므로 쓰지 않아요</li><li>두 창에서 ‘장면 맞춤 → 장면마다 바꾸지 않기’를 선택해요 버튼이 없으면 아래 진행자용 방법으로 끄고 새로고침해요</li><li>A는 초기화한 뒤 공통 통제를 적용해요 B는 피팅 후 공통 통제를 다시 확인해요</li><li>두 창에서 평가 클립을 선택하고 00:00에 멈춰요 현재 설정과 클립이 맞는지 확인하고, 다른 창은 일시정지해요</li><li>실험 도중 새 탭을 열거나 버전을 바꾸지 않아요 각 참여자의 A·B 설정 파일을 ID로 보관해요</li></ol>
<div class="box small"><b>진행자용 예비 설정</b><p>현재 앱은 장면 자동 맞춤 해제를 탭의 sessionStorage에 저장해요<br>개발자 도구 Console에서 다음 한 줄을 실행하고 새로고침한 뒤 초기화해요</p><code>sessionStorage.setItem('pariview-scene-adapt-off','1')</code><p>앱 코드를 수정하는 절차는 아니에요 새 탭을 열면 다시 확인해요</p></div>
<p class="small">평가 도중 설정이나 OS 음량을 바꿔야 하면 즉시 중지할 수 있어요 변경 내용을 절차 이탈로 남기고, 정해진 조건의 비교 결과와 분리해요</p>''')

protocol.append('''<h2>5명은 A부터, 5명은 B부터 봐요</h2><p>모집 순서대로 ID를 배정해요 결과나 감각 특성을 보고 순서를 바꾸지 않아요<br>참여자에게는 ‘첫 번째 시청 / 두 번째 시청’으로 안내해요</p>'''+table(['참여자','미리 배정한 순서','참여자','미리 배정한 순서'],[(ALLOC[i]['id'],ALLOC[i]['planned_order'].replace('A','기본 → ',1).replace('B','개인') if ALLOC[i]['planned_order']=='AB' else '개인 → 기본',ALLOC[i+5]['id'],'기본 → 개인' if ALLOC[i+5]['planned_order']=='AB' else '개인 → 기본') for i in range(5)])+
'''<p class="small">5개의 AB와 5개의 BA를 고정 난수 seed 20261104로 섞어 미리 배정했어요<br>중단자가 생기면 실제 시행 인원과 순서를 그대로 남겨요</p>
<h3>한 사람의 진행 순서</h3>'''+table(['단계','진행'],[
 ('① 안내·동의<br>2–3분','설문지 1쪽을 읽고 동의를 받아요 편한 응답 방식과 오늘 상태를 확인해요'),
 ('② 준비<br>2분','연습 클립으로 본인이 편한 OS 소리 크기를 정해요 작은 소리부터 시작하고 두 조건에서 그 값을 유지해요'),
 ('③ 피팅<br>3–5분','B 창에서 직접 설정하기 → 모드 선택 → A/B 비교 → 설정 적용을 해요 첫 클릭부터 적용까지의 경과 시간과 휴식 시간을 따로 재요'),
 ('④ 첫 시청<br>약 2분','배정 순서의 첫 조건으로 Sintel 45초를 보고 설문지 2쪽에 답해요 재생 중 생각을 말하도록 요구하지 않아요'),
 ('⑤ 휴식<br>1분 이상','본인이 다음 시청을 시작할 준비가 됐을 때 진행해요 휴식 연장이나 중단을 선택할 수 있어요'),
 ('⑥ 둘째 시청<br>약 2분','나머지 조건으로 같은 45초 구간을 보고 설문지 3쪽에 답해요'),
 ('⑦ 사용성 과제<br>2분','B 창에서 원본 비교 후 나의 설정으로 돌아오기, 세부 설정 하나를 바꾸고 되돌리기를 해요'),
 ('⑧ 응답·마무리<br>4–5분','먼저 사용성 10문항, 다음 선호·자유 의견에 답해요 점수를 본 뒤 추가 시청으로 답을 바꾸도록 요청하지 않아요')], 'steps')+
'''<p class="small">피팅과 평가에 다른 클립을 써요 같은 평가 클립의 반복에 따른 익숙함은 순서 배정과 함께 기록해 해석해요 참가자와 진행자가 설정 차이를 알 수 있는 공개 조건 비교예요</p>''')

protocol.append('''<h2>진행자가 읽을 안내와 기록</h2>
<div class="box tint"><p>“화면과 소리를 직접 설정해 보고, 두 설정으로 같은 장면을 볼 거예요 어느 쪽이 더 편한지, 차이가 없는지 모두 알려주세요 정답은 없어요 불편하면 바로 멈추거나 쉬어도 돼요 원하지 않는 질문은 넘어갈 수 있어요”</p></div>
<h3>피팅 과제</h3><p>“직접 설정하기에서 오늘의 시작 모드를 고르고, 비교 화면을 따라 설정을 적용해 주세요 비슷해요와 건너뛰기도 사용할 수 있어요”</p>
<p>진행자는 답을 추천하지 않아요 도움을 요청하면 먼저 문장을 같은 뜻으로 다시 읽고, 버튼 위치를 알려주거나 대신 클릭했으면 도움 내용을 기록해요</p>
<h3>완료 상태를 이렇게 구분해요</h3>'''+table(['상태','기록 기준'],[
 ('unaided','단계나 버튼을 가리키는 도움 없이 본인이 설정 적용까지 완료했어요'),
 ('assisted','진행자의 조작 안내 또는 대리 클릭을 받고 완료했어요'),
 ('not_completed','시도했지만 설정 적용까지 완료하지 않았어요'),
 ('not_attempted','피팅을 시작하지 않았어요')])+
'''<p class="small">평소 쓰는 보조기기·읽기 지원은 사용할 수 있어요 사용한 지원을 기록하고, 피팅 조작 자체를 도운 경우와 구분해요 시간은 경쟁 기준으로 안내하지 않아요</p>
<h3>중단·휴식</h3><ul><li>참여자가 멈춤·휴식을 요청하거나 불편을 표현하면 영상을 바로 멈춰요 이유 설명을 요구하지 않아요</li><li>중단한 조건, 시청한 초, 이후 응답을 남길지 여부를 기록해요 중단 점수를 0점으로 채우지 않아요</li><li>두 조건의 같은 구간을 다 보지 못한 경우에는 완전한 A–B 점수 비교에서 제외하고 중단 사례로 별도 보고해요</li><li>현재 영상을 보기 어렵거나 의료진에게 시청을 제한하라는 안내를 받은 분은 영상 비교 대신 화면 조작 의견만 남길 수 있어요</li></ul>
<h3>연구 기록</h3><p>참여자 번호, 사용 버전·기기, 실제 순서, 도움 여부, 피팅 시간, A·B 설정 파일, 조건별 응답, 중단·절차 이탈을 기록해요<br>자동 보정이 켜졌거나 설정이 바뀌면 <b>protocol_deviation=yes</b>로 남겨요</p>
<div class="box small">기록은 이름 대신 ID를 사용해요 연락처가 필요하면 응답지와 분리해 보관해요 원응답·설정 파일·자유 의견은 field-kit/private/에 보관하고 공개 저장소에 올리지 않아요 공개 인용은 별도 동의를 받은 문장만 익명으로 사용해요</div>''')

protocol.append('''<h2>답을 모으기 전에 계산법을 정해요</h2>'''+table(['지표','계산·보고'],[
 ('주 지표<br>전체 시청 편안함','조건별 0–10점 단일 질문<br><b>각 사람의 차이 = B 점수 − A 점수</b><br>양쪽을 완료한 사람의 차이 평균·중앙값과 증가/같음/감소 인원을 함께 보고해요'),
 ('보조 지표','화면 편안함, 소리 편안함, 자막 읽기 쉬움은 각각 0–10점으로 보고해요 합쳐서 새로운 총점으로 만들지 않아요'),
 ('사용성','SUS 10문항 구조의 한국어 번역안이에요<br>홀수 답−1, 짝수 5−답을 합한 뒤 ×2.5<br>0–100점 범위의 점수이며 백분율로 쓰지 않아요'),
 ('수행','도움 없이 피팅을 완료한 인원 / 피팅 시도 인원<br>완료자 피팅 시간의 중앙값·범위와 도움 여부<br>휴식을 뺀 시간과 전체 경과 시간을 구분해요'),
 ('선호·의견','기본 / 개인 / 비슷 / 둘 다 불편 / 판단 어려움<br>응답 인원과 헷갈린 지점·개선 요청을 정리해요')])+
'''<h3>빈 답과 중단을 처리하는 기준</h3><ul><li>계산마다 유효 응답자 수 n을 함께 적어요 전체 10명을 자동으로 분모에 넣지 않아요</li><li>두 조건 완료 + 해당 문항 두 답 + 자료 사용 동의가 있는 기록을 짝지어 계산해요</li><li>주 분석은 사전 조건을 지킨 짝만 사용해요 절차 이탈·중단의 수와 이유를 따로 남겨요</li><li>SUS 문항 하나라도 비어 있으면 그 사람의 SUS 방식 총점은 비워요 평균값으로 대신 채우지 않아요</li><li>같은 점수·기본값 선호·불편 증가도 그대로 남겨요 결과를 보고 참여자를 고르거나 비교 항목을 바꾸지 않아요</li></ul>
<h3>보고 문장 틀</h3><div class="box"><p>“신경다양성 당사자 성인 __명 참여 · 동일 장면의 기본/개인 설정 비교<br>완전한 짝 __명 중 편안함 증가 __명 · 같음 __명 · 감소 __명<br>편안함 차이 중앙값 __점 · 사용성 점수 평균 __점(n=__)”</p></div>
<p class="small">0–10점 질문은 이 프로젝트의 즉시 시청 경험을 묻는 자체 문항이에요 감각과부하 진단 척도로 부르지 않아요 10명 결과는 참여자별 경험과 개선점을 보고하는 소규모 사용자 평가로 해석해요</p>''')

protocol.append('''<h2>문서 사용과 연구 근거</h2>
<h3>파일을 이렇게 써요</h3><ol><li><b>participant-form.pdf</b>를 참여자별로 인쇄하거나 questionnaire-copy.txt를 폼에 붙여 넣어요 문항·척도·순서를 참여자마다 바꾸지 않아요</li><li><b>record-sheet.xlsx</b>의 진행·시청·사용성 시트에 응답을 옮겨요 두 번 확인해 전사 오류를 줄여요 인원·총점은 실제로 입력한 값으로만 계산해요</li><li>작성한 파일은 <b>private/responses.xlsx</b>로 저장해요 공유용 템플릿은 빈 상태로 보존해요</li><li>집계에는 analysis/user-study/field-kit/analyze.py를 사용해요<br><code>python3 analyze.py private/responses.xlsx</code><br>미응답·범위 오류·중복 ID를 확인하고 유효 n과 개인별 차이를 출력해요</li></ol>
<h3>기존 자료와의 관계</h3><p>이 서식은 ‘정해 둔 목표 설정과의 오차’를 측정하지 않아요<br>상위 폴더의 기존 user_study.py와 CSV 열도 서로 달라요<br>팀의 76명 온라인 설문, 시뮬레이션, 자동 기능검사, 사용자가 완료했다고 확인한 당사자 검증은 각각 별도로 기록해요</p>
<h3>근거와 도구</h3>
<p class="small"><b>MacLennan, O’Brien &amp; Tavassoli (2022)</b><br>In Our Own Words: The Complex Sensory Experiences of Autistic Adults<br>자폐 성인 49명 자기보고에서 개인·상황에 따른 감각 경험을 다뤄요<br><a href="https://doi.org/10.1007/s10803-021-05186-3">10.1007/s10803-021-05186-3</a></p>
<p class="small"><b>NICE CG142, 1.1.8</b><br>개인의 필요에 따른 빛·소리 환경 조절과 휴식 고려를 참고했어요<br><a href="https://www.nice.org.uk/guidance/CG142/chapter/Recommendations">NICE 공식 권고</a></p>
<p class="small"><b>Brooke, J (1996)</b><br>SUS: A ‘quick and dirty’ usability scale, Usability Evaluation in Industry, pp 189–194<br>10문항 구조와 채점법을 사용해요 한국어 문항은 프로젝트 번역안이에요<br><a href="https://hci-studies.org/methods-and-measures/downloads/SUS_Brooke1996.pdf">Brooke 원문</a></p>
<p class="small"><b>Kim H, Lee SH, Cho NB, You H, Choi T, Kim J (2020)</b><br>User-Dependent Usability and Feasibility of a Swallowing Training mHealth App for Older Adults: Mixed Methods Pilot Study<br>JMIR mHealth and uHealth 8(7):e19585 · 한국어 사용성 조사 운영의 참고 자료<br><a href="https://doi.org/10.2196/19585">10.2196/19585</a></p>
<p class="tiny">이번 표본에서 번역 문항의 측정 특성을 검증했다고 표기하지 않아요 SUS 68점 등을 합격선으로 정하지 않아요 이 문서에 추가한 방법론 참고문헌은 기존 ‘논문 11편·전문자료 6건’ 제품 설계 검토 집계와 별개예요</p>''')

forms=[]
forms.append('''<h1>PariView<br>시청 경험 설문</h1><div class="idline"><span>참여자 번호 __________</span><span>날짜 ______________</span></div>
<p class="lead">화면과 소리를 직접 맞추고<br>두 설정으로 같은 짧은 장면을 볼 거예요</p>
<div class="box tint"><p>약 20–25분이 걸려요 쉬는 시간은 더 사용할 수 있어요<br>정답은 없어요 차이가 없거나 불편한 경험도 알려주세요<br>언제든 쉬거나 멈출 수 있고, 답하기 싫은 질문은 넘어가도 돼요</p></div>
<h3>참여 안내</h3><p>이름·진단명·진단서는 받지 않아요 참여자 번호로 답과 조작 기록을 남겨요<br>응답은 PariView의 사용자 경험 개선과 프로젝트 발표를 위해 사용해요<br>익명 처리된 집계와 의견만 발표에 사용해요 직접 인용은 별도로 여쭤봐요</p>
<p>담당자·연락처 _________________________________<br>자료 보관 종료일 _________________________________</p>
<div class="check"><p>□ 저는 만 19세 이상이에요</p><p>□ 저는 스스로를 신경다양성 당사자로 설명해요</p><p>□ 안내를 이해했고, 자발적으로 참여하며 응답을 위 목적에 사용하는 데 동의해요</p></div>
<div class="rule"></div><h3>시작 전</h3><p>지금 짧은 영상을 볼 준비가 됐나요?</p><p>□ 시작할 수 있어요　□ 먼저 쉬고 싶어요　□ 오늘은 시청하기 어려워요</p>
<p>PariView를 이전에 사용해 본 적이 있나요?　□ 있어요　□ 없어요</p>
<p>읽기·응답·조작에 원하는 지원이 있으면 적어주세요 <span class="small">선택</span></p><div class="blank"></div>''')
for idx in [1,2]:
 q=f'<h2>{"첫 번째" if idx==1 else "두 번째"} 시청 직후</h2><div class="idline"><span>참여자 번호 __________</span><span>진행자 기록 · 조건 □ A　□ B</span></div><p>방금 본 장면을 떠올리며 각 줄에서 숫자 하나를 골라주세요<br>판단하기 어려우면 숫자 대신 해당 선택지에 표시해 주세요</p>'
 for n,(_,title,lo,hi) in enumerate(RATINGS,1):
  q+=f'<div class="question"><b>{n}　{title}</b><div class="scale">'+''.join(f'<span>{i}</span>' for i in range(11))+f'</div><div class="anchors"><span>0 · {lo}</span><span>10 · {hi}</span></div><p class="small">□ 판단하기 어려워요'+('　□ 자막을 보지 않았어요' if n==4 else '')+'</p></div>'
 q+='<div class="box small">진행자 기록　□ 45초 구간 완료　□ 중간에 멈춤 · ______초<br>휴식·설정 변경 등 기록 __________________________________</div>'
 forms.append(q)
forms.append('''<h2>PariView를 사용해 본 느낌</h2><div class="idline"><span>참여자 번호 __________</span><span>각 문장에 하나씩 골라요</span></div><p>1 전혀 그렇지 않아요 · 2 그렇지 않아요 · 3 보통이에요<br>4 그래요 · 5 매우 그래요</p><p class="small">사용한 경험을 떠올리며 답해 주세요 답하기 어려운 문항은 비워도 돼요</p>'''+table(['문장','1','2','3','4','5'],[(f'{i+1}　{s}', '○','○','○','○','○') for i,s in enumerate(SUS)],'sus')+'''<p class="small">SUS 10문항 구조의 한국어 번역안 · Brooke (1996)<br>이 페이지는 화면·소리의 편안함이 아니라 서비스 사용 경험을 물어요</p>''')
forms.append('''<h2>선호와 개선 의견</h2><div class="idline"><span>참여자 번호 __________</span><span>편하게 답해 주세요</span></div>
<h3>1　어느 쪽으로 계속 시청하고 싶나요?</h3><div class="check">□ 첫 번째 설정　□ 두 번째 설정<br>□ 둘이 비슷해요　□ 둘 다 불편해요　□ 판단하기 어려워요</div>
<h3>2　그렇게 고른 이유는 무엇인가요? <span class="small">선택</span></h3><div class="write"></div>
<h3>3　사용하면서 가장 헷갈리거나 어려웠던 부분은 무엇인가요? <span class="small">선택</span></h3><div class="write"></div>
<h3>4　하나만 바꿀 수 있다면 무엇을 바꾸고 싶나요? <span class="small">선택</span></h3><div class="write"></div>
<div class="box"><b>익명 인용 동의 · 선택</b><p>적어주신 문장의 일부를 이름 없이 프로젝트 발표에 직접 인용해도 될까요?</p><p>□ 동의해요　□ 동의하지 않아요</p><p class="small">선택하지 않으면 직접 인용하지 않아요</p></div>
<p>참여해 주셔서 고마워요 마지막으로 남기고 싶은 말씀도 편하게 알려주세요</p>''')

(HERE/'protocol.html').write_text(document('진행자 실험 설계서',protocol),encoding='utf-8')
(HERE/'participant-form.html').write_text(document('참여자 설문지',forms),encoding='utf-8')
copy=['PariView 시청 경험 설문 · 폼 복사용 · 제공용 빈 서식','대상: 신경다양성 당사자 성인 10명 · 1인 약 20–25분','폼 운영: 이메일 자동 수집 해제, 이름 대신 ID, 선택 문항 강제 응답 해제, 결과 통계 참여자에게 노출하지 않기','참여자에게는 A/B 대신 첫 번째/두 번째 시청으로 표시하고 진행자가 실제 조건을 따로 기록해요','', '참여 안내','두 설정으로 같은 짧은 장면을 보고 편안함과 사용 경험을 알려주세요 정답은 없어요 언제든 쉬거나 멈출 수 있고, 원하지 않는 질문을 넘길 수 있어요','담당자·연락처: [진행 전에 입력] / 보관 종료일: [진행 전에 입력]','응답과 조작 기록은 번호로 보관하며 사용자 경험 개선과 프로젝트 발표에 사용해요','', '동의 및 시작 전','참여자 번호 [U01~U10]','만 19세 이상인가요 [예/아니요 → 종료]','스스로 신경다양성 당사자로 설명하나요 [예/아니요 → 이 서식의 모집 대상과 구분]','안내를 이해하고 자발적 참여와 응답 자료 사용에 동의하나요 [동의/동의하지 않음 → 종료]','지금 짧은 영상을 볼 준비가 됐나요 [시작 가능/먼저 휴식/오늘 시청 어려움]','PariView를 이전에 사용해 본 적이 있나요 [있음/없음]','읽기·응답·조작에 원하는 지원 [선택, 단답]']
for i in [1,2]:
 copy+=['',f'{i}번째 시청 직후 · 이 섹션은 해당 영상을 본 직후 응답']
 for _,t,lo,hi in RATINGS: copy += [t, f'0~10 정수 선택 (0={lo}, 10={hi}) / 판단 어려움'+(' / 자막 보지 않음' if '자막' in t else '')]
copy+=['','사용 후 설문 · SUS 10문항 구조 한국어 번역안','1 전혀 그렇지 않아요 / 2 그렇지 않아요 / 3 보통이에요 / 4 그래요 / 5 매우 그래요']+[f'{i+1}. {s}' for i,s in enumerate(SUS)]+['','선호와 의견','어느 쪽으로 계속 시청하고 싶나요 [첫 번째/두 번째/둘이 비슷/둘 다 불편/판단 어려움]','그렇게 고른 이유 [선택, 서술]','가장 헷갈리거나 어려웠던 부분 [선택, 서술]','하나만 바꿀 수 있다면 무엇을 바꾸고 싶나요 [선택, 서술]','작성한 문장을 익명으로 직접 인용해도 될까요 [동의/동의하지 않음/빈 답은 미동의]','','채점: 0~10 자체 문항은 각각 보고, 전체 편안함이 주 지표','SUS 구조 점수는 홀수 문항 답−1, 짝수 문항 5−답을 합산해 2.5배, 하나라도 미응답이면 총점 비움','출처: Brooke (1996) https://hci-studies.org/methods-and-measures/downloads/SUS_Brooke1996.pdf']
(HERE/'questionnaire-copy.txt').write_text('\n'.join(copy)+'\n',encoding='utf-8')

schema={
 '진행': [('id','참여자 번호'),('planned_order','배정 순서'),('actual_order','실제 순서 AB/BA'),('status','not_started/completed/partial/withdrawn'),('data_consent','자료 사용 yes/no'),('fit_status','unaided/assisted/not_completed/not_attempted'),('fit_elapsed_s','피팅 전체 경과 초'),('fit_pause_s','그중 휴식 초'),('device_version','기기·브라우저·앱 버전'),('protocol_deviation','조건 이탈 yes/no'),('stop_reason','중단·이탈 메모'),('task_restore','되돌리기 unaided/assisted/not_completed'),('task_adjust','세부 조정 unaided/assisted/not_completed'),('support','사용한 지원'),('quote_consent','익명 직접 인용 yes/no')],
 '시청': [('id','참여자 번호'),('A_complete','기본 설정 45초 완료 yes/no'),('B_complete','개인 설정 45초 완료 yes/no')]+[(f'{condition}_{key}',f'{"기본" if condition=="A" else "개인"} · {label} 0~10') for key,label in [('comfort','전체 편안함'),('visual','화면 편안함'),('audio','소리 편안함'),('caption','자막 읽기')] for condition in ['A','B']]+[('preference','A/B/same/neither/na'),('reason','선호 이유')],
 '사용성': [('id','참여자 번호')]+[(f'sus_{i+1}',s) for i,s in enumerate(SUS)]+[('difficulty','어려웠던 부분'),('improvement','개선 의견')],
}
wb=Workbook();guide=wb.active;guide.title='안내'
guide.append(['PariView 실제 응답 기록용 빈 서식'])
for line in ['제공용 설계 v1.0 · 실측 결과는 아직 입력되지 않은 파일', '신경다양성 당사자 성인 10명 서식 · 기존 76명 설문 및 완료했다고 확인된 별도 검증과 혼합하지 않기','진행·시청·사용성 시트에 기록 · 1행은 집계용 영문 열 이름, 2행은 설명','AB = 첫 시청 기본, 두 번째 개인 / BA = 첫 시청 개인, 두 번째 기본','조건별 응답을 A/B에 맞춰 옮기기 · 빈 답, 못 본 항목은 빈 셀 유지','status: not_started 시작 전 / completed 전체 완료 / partial 일부 참여 / withdrawn 철회','data_consent: 응답 자료 사용 동의 yes/no · 철회한 자료는 집계 제외','protocol_deviation: 절차를 지키면 no, 설정 변경·기기 변경 등 발생하면 yes','진행 중단을 실패나 0점으로 바꾸지 않기 · 중단 이유 기록','숫자 0은 실제 0점, 미응답은 빈 셀 · SUS 문항은 1~5','실제 응답 파일은 private/responses.xlsx로 저장 · 빈 템플릿과 분리','집계 명령: python3 analyze.py private/responses.xlsx','원래 사용자 선호값 오차를 계산하는 상위 폴더 user_study.py와 다른 서식','등록할 버전·날짜·담당자·보관 종료일은 실험 전에 결정']:
 guide.append([line])
guide.column_dimensions['A'].width=110
for title,cols in schema.items():
 ws=wb.create_sheet(title);ws.append([k for k,_ in cols]);ws.append([v for _,v in cols]);ws.freeze_panes='C3'
 for a in ALLOC:
  vals={'id':a['id'],'planned_order':a['planned_order'],'status':'not_started'} if title=='진행' else {'id':a['id']}
  ws.append([vals.get(k) for k,_ in cols])
 for ci,(k,label) in enumerate(cols,1):
  from openpyxl.utils import get_column_letter
  letter=get_column_letter(ci);ws.column_dimensions[letter].width=15 if k=='id' else (34 if any(t in k for t in ['reason','difficulty','improvement','support','device']) else 23)
  if k.startswith('sus_') or k in [f'{c}_{r[0]}' for c in ['A','B'] for r in RATINGS]:
   lo,hi=(1,5) if k.startswith('sus_') else (0,10)
   dv=DataValidation(type='whole',operator='between',formula1=lo,formula2=hi,allow_blank=True);dv.errorTitle='점수 범위 확인';dv.error=f'{lo}~{hi} 사이 정수로 기록해 주세요';dv.showErrorMessage=True;dv.errorStyle='stop';ws.add_data_validation(dv);dv.add(f'{letter}3:{letter}12')
  choices={'status':'not_started,completed,partial,withdrawn','actual_order':'AB,BA','data_consent':'yes,no','A_complete':'yes,no','B_complete':'yes,no','protocol_deviation':'yes,no','quote_consent':'yes,no','fit_status':'unaided,assisted,not_completed,not_attempted','task_restore':'unaided,assisted,not_completed','task_adjust':'unaided,assisted,not_completed','preference':'A,B,same,neither,na'}.get(k)
  if choices:
   dv=DataValidation(type='list',formula1='"'+choices+'"',allow_blank=True);dv.showErrorMessage=True;dv.errorStyle='stop';ws.add_data_validation(dv);dv.add(f'{letter}3:{letter}12')
 ws.auto_filter.ref=f'A2:{get_column_letter(len(cols))}12';ws.row_dimensions[2].height=44
for ws in wb:
 for row in ws:
  for cell in row:
   cell.font=Font(name='Arial',size=11,color='17202D');cell.alignment=Alignment(vertical='top',wrap_text=True)
 for cell in ws[1]:cell.fill=PatternFill('solid',fgColor='17202D');cell.font=Font(name='Arial',bold=True,color='FFFFFF',size=11)
 if ws.title!='안내':
  for cell in ws[2]:cell.fill=PatternFill('solid',fgColor='E8EEF5');cell.font=Font(name='Arial',bold=True,size=11)
 wb.calculation.fullCalcOnLoad=True
wb.save(HERE/'record-sheet.xlsx')
allcols=[]
for cols in schema.values():
 for k,_ in cols:
  if k not in allcols:allcols.append(k)
with (HERE/'responses-template.csv').open('w',newline='',encoding='utf-8-sig') as f:
 writer=csv.DictWriter(f,fieldnames=allcols);writer.writeheader()
 for a in ALLOC:writer.writerow({**a,'status':'not_started'})
spec={'version':'1.0','created':'2026-11-04','status':'blank_materials_for_use_not_a_record_of_completed_evaluation','planned_participants':10,'population':'성인 신경다양성 당사자 자기보고','primary':'paired B minus A overall comfort on project-authored 0–10 item','order_seed':20261104,'allocations':ALLOC,'rating_items':RATINGS,'sus_korean_project_translation':SUS,'sheets':{k:[a for a,_ in v] for k,v in schema.items()},'fixed_controls':['sceneAdapt=off','autoBrightness=false','notices=false','breakReminder=false','captions=true','playbackRate=1'],'evaluation_clip':'sintel 00:00–00:45','fitting_clip':'tears-lab','data_present':False}
(HERE/'study-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/'.gitignore').write_text('private/\nresponses.xlsx\nresponses.csv\nresults*.json\nresults*.txt\n__pycache__/\n',encoding='utf-8')
(HERE/'README.txt').write_text('PariView 제공용 실험·설문 서식 v1.0\n\n1 protocol.pdf: 진행자용 절차와 분석 기준\n2 participant-form.pdf: 참여자에게 줄 5쪽 설문지\n3 questionnaire-copy.txt: 온라인 폼 복사 문항\n4 record-sheet.xlsx: 10명용 빈 기록표\n5 responses-template.csv: 같은 기록의 CSV 템플릿\n6 analyze.py: 실제 응답 집계 (xlsx 또는 CSV)\n\n대상은 성인 신경다양성 당사자 자기보고 10명, 기본/개인 설정 순서를 5:5로 배정했어요\n실제 응답은 private/에 따로 저장하고 공개 저장소에는 올리지 않아요\n이 폴더는 제공용 설계로, 이미 실시한 당사자 검증의 수행 절차나 결과를 증명하는 자료가 아니에요\n팀의 76명 온라인 설문과도 별개예요\n',encoding='utf-8')
print('Built HTML, form text, workbook, blank CSV, study specification')
