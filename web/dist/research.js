// Keep the first six entries ordered: existing start-mode rules reference their indices
export const research = [
  {
    id: 'individual', category: 'difference', tag: '개인차 · 상황에 따른 변화',
    title: '편안한 설정은 사람마다 달라요',
    method: '혼합방법 설문', sample: '자폐 성인 49명', reading: '원문 확인',
    text: '참여자들은 감각 경험의 개인차와 기분·피로에 따른 변화, 예측 가능성과 강도 조절의 중요성을 보고했어요',
    design: '소리와 빛을 각각 비교하고, 오늘의 상태에 맞춰 다시 피팅하는 흐름을 제안해요',
    limitation: '자발적으로 참여한 자폐 성인의 자기보고를 분석했어요 세부 자극의 선택형 응답은 40명, 전체 질적 설문 완료는 29명이에요',
    ref: 'MacLennan, O’Brien & Tavassoli (2022)',
    citation: 'In Our Own Words: The Complex Sensory Experiences of Autistic Adults · Journal of Autism and Developmental Disorders, 52(7), 3061–3075',
    doi: '10.1007/s10803-021-05186-3', url: 'https://doi.org/10.1007/s10803-021-05186-3'
  },
  {
    id: 'control', category: 'control', tag: '사용자의 통제권',
    title: '바꿀지 말지는 내가 정해요',
    method: '동일 참여자 조건 비교', sample: '자폐 아동 41명 · 4–12세', reading: '원문 확인',
    text: '감각실을 직접 조절한 조건에서 주의집중 증가가 관찰됐어요 불안·긍정정서·각성에는 유의한 조건 차이가 없었어요',
    design: '적용·건너뛰기·원본 복귀의 결정권을 사용자에게 둬요',
    limitation: '4–12세 아동이 두 감각실 조건을 경험했어요 직접 조절 조건은 감각 변화 횟수와 iPad 제공 여부도 달랐어요',
    ref: 'Unwin, Powell & Jones (2022)',
    citation: 'The use of Multi-Sensory Environments with autistic children: Exploring the effect of having control of sensory changes · Autism, 26(6), 1379–1394',
    doi: '10.1177/13623613211050176', url: 'https://doi.org/10.1177/13623613211050176'
  },
  {
    id: 'audiovisual', category: 'audiovisual', tag: '시청각 영화 연구',
    title: '소리와 화면을 함께 살펴요',
    method: '영화 시청 · 뇌자도 측정', sample: '남아 46명 · 7–14세', reading: '초록·서지 확인',
    text: '시각 단독·시청각 영화 과제에서 감각 특성이 다른 자폐 하위집단의 신경반응 차이가 관찰됐어요',
    design: '소리와 빛의 변화 정보를 같은 시간축에서 보는 감각 지도를 제안해요',
    limitation: '감각 특이 자폐 집단 13명, 비특이 자폐 집단 10명, 비교군 23명이 참여했어요 시각 단독·시청각 영화 과제의 뇌자도 반응을 측정했어요',
    ref: 'Matsuzaki et al. (2022)',
    citation: 'Abnormal cortical responses elicited by audiovisual movies in patients with autism spectrum disorder with atypical sensory behavior: A magnetoencephalographic study · Brain and Development, 44(2), 81–94',
    doi: '10.1016/j.braindev.2021.08.007', url: 'https://doi.org/10.1016/j.braindev.2021.08.007'
  },
  {
    id: 'prediction', category: 'prediction', tag: '예고 단서에도 개인차',
    title: '미리 알려주는 것도 선택이에요',
    method: '청각·촉각 과제 · fMRI', sample: '자폐 55명 · 비교군 28명', reading: '원문 확인',
    text: '시각 단서로 자극을 예고했을 때의 신경반응이 감각 과반응 정도와 관련됐어요 예고에 대한 반응이 모두 같지는 않았어요',
    design: '사전 안내는 강제하지 않고, 켜거나 끌 수 있게 설계해요',
    limitation: '소리와 촉각 자극을 시각 단서로 예고하고 fMRI로 반응을 살펴봤어요 2026년 5월 공개된 연구를 사전 안내 설계에 참고했어요',
    ref: 'Yosef et al. (2026)',
    citation: 'Atypical Predictive Processing Is Associated With Sensory Over-Responsivity in Autism · Autism Research, 19(7), e70283',
    doi: '10.1002/aur.70283', url: 'https://doi.org/10.1002/aur.70283'
  },
  {
    id: 'white-noise', category: 'difference', tag: '국내 보조 근거 · KCI',
    title: '자극이 적을수록 좋은 걸까요?',
    method: 'ABAB 반전설계', sample: 'ADHD 아동 5명 · 10–12세', reading: '원문 확인',
    text: '자연음을 사용한 백색소음 제공기에 주의집중 지속시간과 암산 과제 정답률의 향상이 보고됐어요',
    design: '원본 유지와 자극 조절을 개인의 선호에 맞춰 선택하게 해요',
    limitation: '약물치료 경험이 없는 아동 5명의 교실 과제 연구예요 자연음을 스피커로 제공하고, 총 30회기에 걸쳐 주의집중과 암산 과제 수행을 관찰했어요',
    ref: '김경민 (2010)',
    citation: '백색소음이 ADHD 아동의 주의집중과 과제수행에 미치는 영향 · 정서·행동장애연구, 26(3), 113–126',
    sourceNote: 'KCI 원문 확인 · DOI 미기재', url: 'https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART001481865'
  },
  {
    id: 'background', category: 'difference', tag: '배경 종설',
    title: '진단명보다 나의 경험을 물어요',
    method: '동료심사 종설', sample: '기존 감각처리 연구 검토', reading: '초록·주요 논점 확인',
    text: '자폐의 감각처리 특성을 여러 감각 양식과 신경생물학 관점에서 다룬 종설이에요 감각 차이를 고려할 학술적 배경을 제공해요',
    design: '개인의 시청 선호를 묻고 직접 설정하게 해요',
    limitation: '기존 자폐 감각처리 연구를 여러 감각 양식과 신경생물학 관점에서 정리한 종설이에요 개인의 시청 경험을 묻는 설계의 배경으로 참고했어요',
    ref: 'Robertson & Baron-Cohen (2017)',
    citation: 'Sensory perception in autism · Nature Reviews Neuroscience, 18(11), 671–684',
    doi: '10.1038/nrn.2017.112', url: 'https://doi.org/10.1038/nrn.2017.112'
  }
];

export const clinicalFrameworks = [
  {
    id: 'vision', number: '01', field: '안과 · 검안', title: '잘 보이는 것과 편안한 것을 나눠 살펴요',
    evidence: '자각적 굴절검사는 사용자 응답을 반영해 교정을 정밀하게 조정해요 시각 평가에서는 대비감도와 눈부심도 따로 살펴요',
    design: '같은 장면을 두 설정으로 비교하고, 화면의 편안함과 자막의 가독성을 각각 확인하는 방식을 제안해요',
    boundary: '안경을 맞추는 비교 절차를, 지금 편안한 화면을 고르는 선호 탐색에 응용했어요',
    sources: [
      {label: 'AAO 굴절교정 진료지침 · 2023', url: 'https://doi.org/10.1016/j.ophtha.2022.10.031'},
      {label: 'AOA 성인 시각검사 진료지침', url: 'https://www.aoa.org/AOA/Documents/Practice%20Management/Clinical%20Guidelines/EBO%20Guidelines/Comprehensive%20Adult%20Eye%20and%20Vision%20Examination%2C%20Second%20Edition.pdf'}
    ]
  },
  {
    id: 'hearing', number: '02', field: '이비인후과 · 청각학', title: '크기가 불편한지, 특정 소리가 불편한지',
    evidence: '소리 내성 평가에서는 청각과민과 특정 소리의 패턴·의미에 대한 반응인 미소포니아 등을 구분해 살펴요',
    design: '전체 음량, 갑작스러운 변화, 특정 소리, 대사 식별의 어려움을 서로 다른 요구로 묻는 방식을 제안해요',
    boundary: '피팅에서는 두 가지 소리 설정을 비교해 선호하는 쪽을 골라요 기기의 음량 비율을 설정값으로 사용해요',
    sources: [
      {label: 'ASHA 소리 내성 평가·관리 지침', url: 'https://www.asha.org/practice-portal/clinical-topics/tinnitus-and-hyperacusis/'},
      {label: 'Swedo et al. · 미소포니아 합의 정의 · 2022', url: 'https://doi.org/10.3389/fnins.2022.841816'}
    ]
  },
  {
    id: 'context', number: '03', field: '정신건강의학 · 임상심리', title: '자극만큼, 지금의 상태도 살펴요',
    evidence: 'NICE는 개인의 감각 필요에 맞춘 빛·소리 환경 조정과 휴식, 예측 가능성을 고려하도록 권고해요 NIMH의 RDoC는 주의·정서·각성을 나눠 보는 연구틀이에요',
    design: '오늘의 피로와 집중하기 어려운 상황을 선택적으로 묻고, 필요할 때 다시 맞출 수 있는 흐름을 제안해요',
    boundary: '주의·정서·각성을 나눠 살피는 연구 관점을, 오늘의 피로와 집중 상태를 묻는 질문에 연결했어요',
    sources: [
      {label: 'NICE CG142 · 1.1.8, 1.3.2', url: 'https://www.nice.org.uk/guidance/CG142/chapter/Recommendations'},
      {label: 'NIMH · RDoC 연구틀', url: 'https://www.nimh.nih.gov/research/research-funded-by-nimh/rdoc/about-rdoc'}
    ]
  }
];

export const sensoryPatterns = [
  {name: '감각민감', description: '자극을 쉽게 알아차리는 경향'},
  {name: '감각회피', description: '자극을 줄이거나 피하려는 경향'},
  {name: '감각추구', description: '자극을 더 찾아 나서는 경향'},
  {name: '낮은등록', description: '자극을 알아차리는 데 더 많은 단서가 필요한 경향'}
];

export const therapyStudies = [
  {
    title: '착색렌즈 연구', sample: '교차시험 · 1차 환자 30명, 2차 환자 26명·비교군 26명',
    finding: 'FL-41 렌즈의 빛 민감도와 눈깜박임 관련 결과를 평가했어요',
    boundary: '안검경련 환자에게 사용한 광학 렌즈를 다룬 연구예요 빛 민감도를 평가한 대상과 방법을 살펴봤어요',
    ref: 'Blackburn et al. (2009)', url: 'https://doi.org/10.1016/j.ophtha.2008.12.031'
  },
  {
    title: '청각과민 인지행동치료', sample: '환자 60명 · 대기군 비교 무작위시험',
    finding: '불쾌음량 수준 등에서 차이가 있었지만 불안 척도에는 유의한 집단 차이가 없었어요',
    boundary: '전문가가 제공한 인지행동치료와 대기 조건을 비교했어요 소리 내성과 생활의 영향을 함께 평가했어요',
    ref: 'Jüris et al. (2014)', url: 'https://doi.org/10.1016/j.brat.2014.01.001'
  },
  {
    title: '미소포니아 인지행동치료', sample: '환자 54명 · 3개월 집단치료 · 대기군 비교 무작위시험',
    finding: '주의집중·각성 조절 등 여러 요소를 묶은 치료에서 증상 개선을 보고했어요',
    boundary: '주의·각성·정서와 관련한 여러 요소를 함께 다룬 집단치료예요 3개월 치료와 후속 평가를 살펴봤어요',
    ref: 'Jager et al. (2021 · 온라인 2020)', url: 'https://doi.org/10.1002/da.23127'
  }
];

export const designProposals = [
  {
    number: '01', title: '편안함 다음에, 가독성 확인',
    text: 'A/B로 고른 화면에서 자막과 어두운 장면도 잘 보이는지 한 번 더 확인하는 단계를 제안해요',
    question: '보기 편한가요? 자막도 잘 보이나요?',
    basis: '응답을 반영하는 자각적 비교 절차',
    url: 'https://doi.org/10.1016/j.ophtha.2022.10.031', source: '안과 평가에서 참고한 절차'
  },
  {
    number: '02', title: '소리의 종류까지 묻기',
    text: '큰 소리와 특정 소리에 대한 불편을 나눠 묻고, 전체 음량만 줄이는 추천에서 선택 범위를 넓히는 방향을 제안해요',
    question: '소리가 큰가요, 특정 소리가 거슬리나요?',
    basis: '소리 내성 · 미소포니아 합의 정의',
    url: 'https://doi.org/10.3389/fnins.2022.841816', source: '소리 내성의 구분에서 참고'
  },
  {
    number: '03', title: '오늘의 상태로 다시 시작',
    text: '피팅 전에 피로와 집중 상태를 선택적으로 남기고, 이전 설정을 유지할지 다시 비교할지 고르는 흐름을 제안해요',
    question: '지난번 설정이 오늘도 편안한가요?',
    basis: '개인·상황별 감각 경험의 차이',
    url: 'https://doi.org/10.1007/s10803-021-05186-3', source: '자폐 성인의 경험 연구에서 참고'
  }
];
