"""Build the printable research companion from the shared evidence records."""
from pathlib import Path
from html import escape
import json
import subprocess

ROOT = Path(__file__).resolve().parent.parent
core = json.loads((ROOT / 'research/sources.json').read_text())
medical = json.loads((ROOT / 'research/medical-sensory-sources.json').read_text())
module_url = (ROOT / 'web/dist/research.js').as_uri()
js = f"import * as data from {json.dumps(module_url)}; process.stdout.write(JSON.stringify(data))"
ui = json.loads(subprocess.run(['node', '--input-type=module', '--eval', js], check=True, capture_output=True, text=True).stdout)
all_sources = core['sources'] + medical['sources']
assert len(all_sources) == 17
e = escape

def link(label, url):
    return f'<a href="{e(url, quote=True)}">{e(label)}</a>'

def source_link(source):
    if source.get('doi'):
        return link('DOI ' + source['doi'], 'https://doi.org/' + source['doi'])
    return link('기관·원문 출처', source['url'])

def page(title, eyebrow, content, extra=''):
    return f'<section class="page {extra}"><header class="page-header"><span>PariView / RESEARCH &amp; STRATEGY</span><span>Lucent · 2026.11.04</span></header><main class="page-content"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1>{content}</main><footer><span>의학의 평가 관점과 감각 경험 연구에서 출발한 시청 선호 피팅</span><span class="page-number"></span></footer></section>'

pages = []
pages.append(page('의학과 감각 연구가<br><em>설계의 출발점이에요</em>', '01 / 설계의 기반', '''
<p class="lead">평가 관점과 동료심사 연구에서 설계 원칙을 찾고,<br>사용자의 반복 비교와 선택으로 지금의 시청 설정을 맞춰요</p>
<div class="review-count"><div><b>11<span>편</span></b><p>학술논문</p></div><div><b>6<span>건</span></b><p>진료·평가 및 연구 전문자료</p></div><p>개인차 · 통제권 · 시각 평가 · 소리 내성<br>총 17건의 자료를 검토했어요</p></div>
<h2>검토 자료에서 가져온 네 가지 원칙</h2>
<div class="two-col principles"><article><h3>개인·상황별 감각 경험</h3><p>MacLennan 등의 자폐 성인 연구는 기분·피로와 개인별 감각 경험의 차이를 다뤘어요 [R1]</p><strong>→ 다시 맞출 수 있는 설정</strong></article><article><h3>사용자의 통제권</h3><p>Unwin 등의 아동 감각실 연구는 감각 변화를 직접 조절하는 조건을 비교했어요 [R2]</p><strong>→ 선택·건너뛰기·원본 복귀</strong></article><article><h3>시각 평가의 비교 절차</h3><p>자각적 굴절검사의 응답 기반 조정과 대비·눈부심 평가 관점을 살펴봤어요 [M1–M2]</p><strong>→ 같은 장면을 두 설정으로 비교</strong></article><article><h3>소리 내성의 구분</h3><p>전체 크기와 특정 소리의 패턴·의미에 대한 반응을 구분하는 관점을 참고했어요 [M3–M4]</p><strong>→ 필요한 조절 항목을 따로 선택</strong></article></div>
<h2>사용자 조사에서 출발한 필요</h2>
<p class="small">구글 폼 온라인 설문 · 76명 응답 · 신경다양성 당사자 20%</p>
<div class="survey"><div><b>11.8<small>%</small></b><p>기존 OTT 관련<br>기능 만족도</p></div><div><b>60.5<small>%</small></b><p>기존 OTT 관련<br>세부 조절 기능 부족</p></div><div><b>83<small>%</small></b><p>맞춤형 시청각 자극<br>최적화 기술 사용 의향</p></div></div>
<p class="note">문헌은 핵심 실증연구 5편과 배경 종설 1편을 먼저 선정하고, 의학·감각 평가 자료를 보완하는 표적 검토로 정리했어요 자료별 확인 범위와 설문 표기의 출처는 뒤쪽에 남겼어요</p>
<div class="demo"><img src="web/dist/assets/pariview-demo-qr.svg" alt="공개 데모 QR"><div><b>실제 화면에서 근거와 선택 흐름을 볼 수 있어요</b><p><a href="https://pariview-production.up.railway.app/#research">PariView 연구 근거 보기 ↗</a></p><small>pariview-production.up.railway.app</small></div></div>
''', 'cover'))

research_notes = {
    'individual': '자발적 참여와 자기보고에 기반한 표본이에요 세부 선택형 문항은 40명, 전체 질적 설문 완료는 29명이에요',
    'control': '직접 조절 조건에는 변화 횟수와 iPad 제공의 차이도 포함돼요 불안·긍정정서·각성의 조건 차이는 유의하지 않았어요',
    'audiovisual': '감각 특이 자폐 13명·비특이 자폐 10명·비교군 23명으로 구성됐어요 결과 지표는 뇌자도 신경반응이에요',
    'prediction': '청각·촉각 자극을 시각 단서로 예고한 실험이에요 2026년 5월 공개된 자료를 후속 설계에 참고했어요',
    'white-noise': '교실의 암산 과제에서 자연음을 제공한 ABAB 30회기 연구예요 원문 표의 일부 평균값이 달라 이 검토에서는 효과크기 수치를 보류했어요',
    'background': '자폐 감각처리를 여러 감각 양식과 신경생물학 관점에서 정리한 종설이에요 개별 실험의 결과와 구분해 읽었어요',
}
cards = []
for index, study in enumerate(ui['research']):
    source = core['sources'][index]
    cards.append(f'''<article class="study"><div class="study-heading"><span>R{index+1}</span><h2>{e(study['title'])}</h2><small>{e(study['reading'])}</small></div><div class="study-meta">{e(study['ref'])} · {e(study['method'])} · {e(study['sample'])}</div><div class="study-columns"><div><h3>연구에서 확인</h3><p>{e(study['text'])}</p><h3>설계에 연결</h3><p>{e(study['design'])}</p></div><div><h3>연구를 읽을 때 함께 볼 정보</h3><p>{e(research_notes[study['id']])}</p><p class="citation">{e(source['title'])}</p>{source_link(source)}</div></div></article>''')
pages.append(page('개인차·통제권·시청각의 근거', '02 / 핵심 논문 1–3', ''.join(cards[:3]) + '<p class="note">관찰 결과에서 설계 원칙을 도출한 연결을 보여줘요 구체적인 버튼 구성과 A/B 비교 흐름은 PariView에서 정한 설계예요</p>'))
pages.append(page('예고·자극 선택·배경 이론의 근거', '03 / 핵심 논문 4–6', ''.join(cards[3:]) + '<p class="note">국내 보조 연구는 자극을 더한 조건의 결과도 함께 살피기 위해 선정했어요 자극 종류와 환경을 구체적으로 읽고, 개인의 선택으로 연결했어요</p>'))

clinical = []
clinical_copy = {
 'vision': ('사용자 응답으로 교정을 조정하는 자각적 굴절검사와 대비·눈부심 평가 관점을 참고했어요', '같은 장면을 비교하고, 편안함과 자막 가독성을 따로 확인하는 흐름을 제안해요'),
 'hearing': ('전체 소리의 크기와 특정 소리 패턴·의미에 대한 반응을 구분해 살펴봤어요', '음량·갑작스러운 변화·특정 소리·대사 식별을 서로 다른 필요로 물어요'),
 'context': ('NICE의 개인별 환경 조정 지침과 NIMH의 주의·정서·각성 연구 관점을 참고했어요', '오늘의 피로와 집중 상태를 선택적으로 묻고, 필요할 때 다시 맞추게 해요'),
}
for framework, keys in zip(ui['clinicalFrameworks'], ['M1–M2', 'M3–M4', 'M5–M6']):
    clinical.append(f'<article class="clinical"><h2>{e(framework["field"])} <small>{keys}</small></h2><div class="two-col"><div><h3>참고한 관점</h3><p>{e(clinical_copy[framework["id"]][0])}</p></div><div><h3>설계에 연결</h3><p>{e(clinical_copy[framework["id"]][1])}</p></div></div><div class="links">'+ ' · '.join(link(s['label'],s['url']) for s in framework['sources'])+'</div></article>')
patterns = ''.join(f'<div><b>{e(p["name"])}</b><p>{e(p["description"])}</p></div>' for p in ui['sensoryPatterns'])
therapies = ''.join(f'<tr><th>{e(s["title"])}<br><small>{e(s["ref"])}</small></th><td>{e(s["sample"])}<br>{e(s["finding"])}</td></tr>' for s in ui['therapyStudies'])
pages.append(page('세 분야에서 가져온 평가 관점', '04 / 의학·감각 평가 자료', ''.join(clinical)+f'''
<h2 class="compact-title">감각 경험을 이해하는 네 가지 패턴 <small>[M7]</small></h2><p class="small">Dunn의 작업치료 모형은 감각민감·감각회피·감각추구·낮은등록을 제시해요 자극을 알아차리는 특성과 대응 방식을 함께 보는 관점이에요 다섯 시작 프로필은 직접 고쳐 쓸 수 있는 설정 묶음으로 구성했어요</p>
<h2 class="compact-title">함께 읽은 치료 연구 <small>[M8–M10]</small></h2><table class="therapy-table"><tbody>{therapies}</tbody></table>
<p class="note">렌즈와 전문가의 치료를 평가한 연구는 대상·절차·결과를 함께 읽었어요 NICE CG170에서는 자폐 아동·청소년 지원과 개별 중재의 적용 범위를 확인했어요 [M11]</p>
'''))

short_proposals = ['자막과 어두운 장면의 가독성을 한 번 더 확인해요', '큰 소리와 특정 소리의 불편을 따로 물어요', '이전 설정 유지와 다시 비교하기 중에서 골라요']
proposal_rows = ''.join(f'<tr><th>{e(p["title"])}</th><td>{e(short_proposals[int(p["number"])-1])}</td><td>{e(p["question"])}</td></tr>' for p in ui['designProposals'])
pages.append(page('근거를 사용자가 고르는 흐름으로', '05 / 제품 설계와 다음 검증', f'''
<div class="flow three"><div><small>STEP 01</small><b>시작 프로필</b><p>다섯 설정 중 지금과 가까운 것을 골라요</p></div><div><small>STEP 02</small><b>같은 장면 비교</b><p>밝기·대비·소리·쉬운 자막을 비교해요</p></div><div><small>STEP 03</small><b>시청하며 조절</b><p>설정 저장·원본 비교·재피팅으로 이어져요</p></div></div>
<p class="small">감각 지도는 영상 신호의 소리·밝기 변화 정보를 표시해요 장면 기록과 쉬운 자막은 시연 영상에 맞춰 작성했어요 시작 프로필의 숫자는 편집 가능한 초기설정이에요</p>
<h2>다음 설계 제안</h2><table class="proposal-table"><thead><tr><th>방향</th><th>다음 경험</th><th>사용자에게 물을 것</th></tr></thead><tbody>{proposal_rows}</tbody></table>
<h2>당사자 평가에서 확인할 것</h2>
<table><thead><tr><th>관점</th><th>확인 방법</th><th>함께 기록할 정보</th></tr></thead><tbody><tr><th>편안함</th><td>기본 설정과 개인 설정으로 같은 장면을 본 뒤 평가</td><td>사람별 차이 · 영상 · 기기 · 피로</td></tr><tr><th>정보 전달</th><td>화면·소리 편안함과 자막 읽기 쉬움 문항</td><td>잘 보이는지와 편안한지 각각 기록</td></tr><tr><th>통제와 사용성</th><td>비교·건너뛰기·원본 복귀·저장 과제</td><td>완료 여부 · 망설인 지점 · 재조절 이유</td></tr></tbody></table>
<p class="note">평가에서는 조건의 제시 순서를 균형 있게 배치하고 개인별 변화를 살펴봐요 참여자는 비교를 건너뛰거나 종료할 수 있어요 위 항목은 별도 제공용 평가 설계예요 사용자가 확인한 기존 당사자 참여 검증은 인원·항목·점수 미제공 상태로 구분해 기록했어요</p>
<div class="verification"><b>화면 동작 확인</b><p>연구 카드 6개, 주제 필터, 출처 펼치기, 키보드 이동, 시작 모드 추천 연결을 확인했어요 320–1440px 너비에서 가로 넘침과 JavaScript 오류 없이 동작했어요</p><small>로컬 실행 기록 · web/research-validation.json · 실제 당사자 검증 완료는 사용자 확인으로 별도 기록</small></div>
'''))

pages.append(page('설문과 근거를 기록하는 기준', '06 / 출처와 해석의 추적', '''
<h2>현재 포스터에 쓰는 조사 결과</h2>
<table><thead><tr><th>표기 비율</th><th>사용자가 제공한 문항 표제</th><th>현재 표기</th></tr></thead><tbody><tr><th>11.8%</th><td>기존 OTT 관련 기능 만족도</td><td rowspan="3">구글 폼 온라인 설문<br>76명 응답<br>당사자 비율 20%</td></tr><tr><th>60.5%</th><td>기존 OTT 관련 세부 조절 기능 부족</td></tr><tr><th>83%</th><td>맞춤형 시청각 자극 최적화 기술 사용 의향</td></tr></tbody></table>
<p>사용자가 실제 응답자 수 76명, 구글 폼 온라인 조사, 당사자 비율 20%를 확인했어요 세 비율은 76명 전체 기준이에요 모집 경로는 미제공이에요</p>
<div class="calculation"><b>반올림 기준으로 계산한 후보</b><p>9/76 × 100 = 11.8421% → 11.8%<br>46/76 × 100 = 60.5263% → 60.5%<br>63/76 × 100 = 82.8947% → 83%</p></div>
<p>처음에는 비율 반올림에서 76명을 역산했고 이후 사용자가 실제 응답자 수로 직접 확인했어요 9·46·63명은 계산 후보로 보존하며 원응답 개수와 구분해요</p>
<h2>이전 기획서의 조사 기록</h2>
<p>출품계획서의 자체 설문은 49명, 2026년 2월 22–26일, 명도 변화 불편 98%, 시청 중단 경험 57.1%로 기재돼 있어요 현재 초안과 별도로 기록했어요</p>
<p class="small">MacLennan 등의 자폐 성인 49명 연구도 별도 표본이에요</p>
<h2>검토한 자료의 역할</h2>
<div class="two-col roles"><article><h3>학술논문 11편</h3><p>실증연구 5편 · 종설 1편 · 합의 정의 1편 · 개념 모형 1편 · 치료 연구 3편이에요</p></article><article><h3>전문자료 6건</h3><p>AAO·AOA·ASHA 자료 · NICE 지침 2건 · NIMH RDoC예요 AAO 지침도 이 범주로 한 번만 집계했어요</p></article></div>
<p class="note">전체 저자·서지·확인 경로는 research/sources.json과 medical-sensory-sources.json에 있어요 포스터용 문구와 수치 변경 기록은 handoff/RESEARCH_FOR_POSTER.txt에서 이어서 관리해요</p>
'''))

references = []
for source in all_sources:
    names = source.get('authors')
    author = ', '.join(names[:3]) + (' et al' if len(names) > 3 else '') if names else source.get('corporate_author', '')
    pub = ' · '.join(str(source[key]) for key in ['journal', 'volume', 'issue', 'pages', 'article_number'] if source.get(key))
    references.append(f'<article class="reference"><b>[{e(source["id"])}] {e(author)}{(" ("+str(source["year"])+")") if source.get("year") else ""}</b><p>{e(source["title"])}</p><small>{e(pub)}</small>{source_link(source)}</article>')
pages.append(page('검토 자료 목록', '07 / 서지와 원문', '<p class="small">R1–R6 핵심 논문 · M1–M11 의학·감각 평가 보완 자료<br>긴 저자 목록은 처음 세 저자와 et al로 표시했어요 전체 목록은 원장에 있어요</p><div class="reference-columns"><div>'+''.join(references[:9])+'</div><div>'+''.join(references[9:])+'</div></div>', 'references-page'))

css = '''
@font-face{font-family:Pretendard;src:url('web/dist/assets/Pretendard-Regular.woff2');font-weight:400}
@font-face{font-family:Pretendard;src:url('web/dist/assets/Pretendard-SemiBold.woff2');font-weight:600}
@font-face{font-family:Pretendard;src:url('web/dist/assets/Pretendard-Bold.woff2');font-weight:700 900}
*{box-sizing:border-box}body{margin:0;background:#e8ebef;color:#191f28;font:14px/1.7 Pretendard,sans-serif;print-color-adjust:exact;-webkit-print-color-adjust:exact}a{color:#003cdc;text-decoration:none;overflow-wrap:anywhere}a:hover{text-decoration:underline}h1,h2,h3,p{margin:0}h1{font-size:30px;line-height:1.4;letter-spacing:-.7px;margin:7px 0 20px;word-break:keep-all}h1 em{color:#fa0030;font-style:normal}h2{font-size:18px;line-height:1.5;margin:20px 0 11px;letter-spacing:-.3px}h3{font-size:14px;line-height:1.6;margin-bottom:5px}p{word-break:keep-all;overflow-wrap:anywhere}p+p{margin-top:12px}small,.small{font-size:12px;line-height:1.65;color:#6b7684}.page{position:relative;width:210mm;height:297mm;background:white;padding:13mm 15mm 17mm;margin:16px auto;break-after:page;overflow:hidden}.page:last-child{break-after:auto}.page-header{display:flex;justify-content:space-between;color:#6b7684;font-size:10px;letter-spacing:.3px;border-bottom:1px solid #e5e8eb;padding-bottom:11px;margin-bottom:24px}.eyebrow{font-size:12px;font-weight:600;color:#6b7684}.page footer{position:absolute;left:15mm;right:15mm;bottom:9mm;display:flex;justify-content:space-between;border-top:1px solid #e5e8eb;padding-top:10px;font-size:9px;color:#6b7684}.cover h1{font-size:36px;margin-bottom:15px}.lead{font-size:17px;line-height:1.65;color:#4e5968}.review-count{display:flex;gap:28px;align-items:center;padding:20px 24px;background:#f5f6f8;border-radius:12px;margin-top:24px}.review-count>div{flex:none}.review-count b{font-size:34px;line-height:1.2;letter-spacing:-1px}.review-count b span{font-size:14px;letter-spacing:0;margin-left:5px}.review-count p{font-size:12px;color:#4e5968}.review-count>p{margin-left:auto}.flow{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0 22px}.flow>div{padding:13px 12px;background:#f5f6f8;border-radius:10px}.flow small{display:block;font-size:10px;color:#6b7684}.flow b{display:block;font-size:13px;margin:3px 0}.flow p{font-size:11.5px;line-height:1.65;color:#4e5968}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:18px}.principles{gap:18px 25px}.principles p{font-size:12.5px;line-height:1.75;color:#4e5968}.principles strong{display:block;color:#003cdc;font-size:12px;margin-top:7px}.survey{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-top:12px}.survey>div{padding:14px 18px;border:1px solid #e5e8eb;border-radius:10px}.survey b{font-size:32px;color:#fa0030;line-height:1.2}.survey b small{font-size:16px;color:inherit}.survey p{font-size:12px;color:#4e5968;margin-top:7px}.note{font-size:11.5px;line-height:1.75;color:#6b7684;margin-top:14px}.demo{display:flex;align-items:center;gap:16px;margin-top:16px}.demo img{width:66px;height:66px}.demo b{font-size:12px}.demo p{font-size:12px}.demo small{font-size:10px}.study{border-top:1px solid #e5e8eb;padding-top:17px;margin-top:22px}.study-heading{display:flex;align-items:center;gap:10px}.study-heading>span{color:#003cdc;font-size:12px;font-weight:600}.study-heading h2{font-size:19px;margin:0;flex:1}.study-heading small{font-size:10px;flex:none}.study-meta{font-size:11.5px;color:#6b7684;margin-top:7px}.study-columns{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:13px}.study-columns h3{font-size:12px;margin-top:10px;color:#333d4b}.study-columns h3:first-child{margin-top:0}.study-columns p{font-size:12.5px;line-height:1.7;color:#4e5968}.study-columns .citation{font-size:10.5px;line-height:1.6;word-break:normal;color:#6b7684;margin-top:12px}.study-columns a{display:block;font-size:10.5px;margin-top:5px}.clinical{border-top:1px solid #e5e8eb;padding-top:12px;margin-top:16px}.clinical h2{margin:0 0 9px;font-size:17px}.clinical h2 small{font-size:11px;margin-left:7px}.clinical h3{font-size:12px;color:#6b7684}.clinical p{font-size:12.5px;line-height:1.75;color:#4e5968}.links{font-size:10px;line-height:1.8;margin-top:9px}.compact-title{font-size:16px;margin-top:18px}.patterns{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px}.patterns>div{padding:10px;background:#f5f6f8;border-radius:8px}.patterns b{font-size:12px}.patterns p{font-size:10.5px;line-height:1.6;color:#4e5968;margin-top:3px}table{width:100%;border-collapse:collapse;font-size:12px;line-height:1.7;margin:10px 0 15px;table-layout:fixed}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #e5e8eb;padding:10px 9px;word-break:keep-all;overflow-wrap:anywhere}th{font-weight:600;color:#333d4b}thead th{background:#f5f6f8;font-size:11px}tbody th:first-child{width:24%}td{color:#4e5968}.therapy-table{font-size:11px;line-height:1.65}.therapy-table th{width:30%}.therapy-table td,.therapy-table th{padding:7px 8px}.therapy-table small{font-size:10px}.three{grid-template-columns:repeat(3,1fr);margin-bottom:20px}.implementation{display:grid;grid-template-columns:1fr 20px 1fr 20px 1fr;align-items:center;gap:10px;padding:15px 18px;border:1px solid #e5e8eb;border-radius:10px;margin-bottom:12px}.implementation b{font-size:13px}.implementation p{font-size:11.5px;color:#4e5968}.implementation>span{color:#6b7684}.proposal-table th:first-child{width:25%}.proposal-table td:last-child{width:25%;color:#191f28}.verification{background:#f5f6f8;border-radius:10px;padding:16px 18px;margin-top:20px}.verification b{font-size:13px}.verification p{font-size:12px;line-height:1.75;color:#4e5968;margin-top:6px}.verification small{display:block;font-size:10px;margin-top:7px}.calculation{background:#f5f6f8;border-radius:10px;padding:18px 22px;margin:17px 0}.calculation b{font-size:13px}.calculation p{font-size:13px;margin-top:8px;font-variant-numeric:tabular-nums}.roles{margin-top:12px}.roles p{font-size:12.5px;color:#4e5968}blockquote{font-size:18px;font-weight:600;line-height:1.7;border-left:3px solid #fa0030;margin:12px 0 0;padding:6px 18px;word-break:keep-all}.reference-columns{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:17px}.reference{margin-bottom:11px;font-size:10px;line-height:1.5;overflow-wrap:anywhere}.reference b{font-weight:600}.reference p{font-size:10px;word-break:normal;margin-top:3px}.reference small{display:block;font-size:9px;line-height:1.5;margin-top:2px}.reference a{display:block;font-size:9px;margin-top:3px}.references-page h1{margin-bottom:12px}
@page{size:A4;margin:0}@media print{body{background:white}.page{margin:0;box-shadow:none}}
'''
html = '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>PariView 연구 근거와 설계 전략</title><style>'+css+'</style></head><body>'+''.join(pages)+'</body></html>'
for index in range(len(pages)):
    html = html.replace('<span class="page-number"></span>', f'<span class="page-number">{index+1} / {len(pages)}</span>', 1)
(ROOT / 'research-and-strategy.html').write_text(html)
print(f'Created {len(pages)}-page research companion')
