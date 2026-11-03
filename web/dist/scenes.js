// Licensed excerpts, authored Korean captions and scene notes
// Signal maps are measured separately by analysis/sensory_map.py
export const scenes = [
  {
    id: 'tears-lab', film: 'Tears of Steel', title: '홀로그램과 도시',
    description: '빛이 바뀌는 연구실과 어두운 도시를 비교해요',
    duration: 45, ratio: 1280 / 534, previewAt: 3,
    src: 'assets/scenes/tears-lab.mp4', poster: 'assets/scenes/tears-lab.jpg',
    map: 'assets/scenes/tears-lab-map.json',
    original: 'https://www.youtube.com/watch?v=R6MlUcmOul8',
    originalLabel: '공식 YouTube 원본 ↗',
    attribution: 'Tears of Steel · © Blender Foundation | mango.blender.org · CC BY 3.0',
    excerpt: '원본 00:47–01:32 발췌',
    captions: [
      {start: 3, end: 6.5, text: '로봇의 기억 동기화와 잠금이 완료됐어요', easy: '로봇의 기억을 맞추고 잠갔어요'},
      {start: 14, end: 16, text: '이거 꽤 으스스한데', easy: '조금 무서운데'}
    ],
    chapters: [
      {at: 0, title: '홀로그램이 켜진 연구실', recap: '홀로그램이 켜진 연구실이에요 주변 장치와 화면이 보이고 있어요'},
      {at: 3, title: '로봇의 기억을 확인하는 대사', recap: '로봇의 기억을 맞추고 잠갔다는 말이 들려요'},
      {at: 23, title: '도시의 전경', recap: '화면이 연구실에서 어두운 도시의 풍경으로 바뀌어요'},
      {at: 31, title: '도시를 살피는 사람', recap: '신문을 든 사람이 관측 장비로 도시를 살펴보고 있어요'}
    ]
  },
  {
    id: 'sintel', film: 'Sintel', title: '대화에서 골목으로',
    description: '어두운 실내의 대사와 햇빛이 드는 골목을 살펴봐요',
    duration: 45, ratio: 1280 / 546, previewAt: 8.8,
    src: 'assets/scenes/sintel.mp4', poster: 'assets/scenes/sintel.jpg',
    map: 'assets/scenes/sintel-map.json',
    original: 'https://durian.blender.org/download/', originalLabel: '공식 작품 보기 ↗',
    attribution: 'Sintel · © Blender Foundation | durian.blender.org · CC BY 3.0',
    excerpt: '원본 02:20–03:05 발췌',
    captions: [
      {start: 0, end: 2.2, text: '아주 소중한 것인가 보군 가까운 친구인가?', easy: '소중한 친구를 찾고 있나?'},
      {start: 3.4, end: 5, text: '용이요', easy: '용을 찾고 있어요'},
      {start: 8.85, end: 11.75, text: '홀로 다니는 사냥꾼에게는 위험한 일이군', easy: '혼자 찾으러 다니면 위험하네'},
      {start: 12.95, end: 15.87, text: '저는 언제나 외톨이였어요', easy: '저는 늘 혼자였어요'}
    ],
    chapters: [
      {at: 0, title: '찾고 있는 상대에 관한 대화', recap: '어두운 실내에서 찾고 있는 상대에 관해 이야기하고 있어요'},
      {at: 3.4, title: '찾고 있는 것은 용', recap: '주인공은 용을 찾고 있다고 말해요'},
      {at: 12.95, title: '혼자였다는 이야기', recap: '혼자 다니면 위험하다는 말에 주인공은 늘 혼자였다고 답해요'},
      {at: 18, title: '도시와 골목의 풍경', recap: '실내 대화에서 햇빛이 비치는 도시와 골목으로 화면이 바뀌어요'}
    ]
  },
  {
    id: 'bunny', film: 'Big Buck Bunny', title: '햇살이 드는 풀밭',
    description: '밝은 자연 풍경과 음악을 보며 화면과 소리를 맞춰요',
    duration: 45, ratio: 1280 / 720, previewAt: 8,
    src: 'assets/scenes/bunny.mp4', poster: 'assets/scenes/bunny.jpg',
    map: 'assets/scenes/bunny-map.json',
    original: 'https://peach.blender.org/download/', originalLabel: '공식 작품 보기 ↗',
    attribution: 'Big Buck Bunny · © 2008 Blender Foundation | www.bigbuckbunny.org · CC BY 3.0',
    excerpt: '원본 00:50–01:35 발췌',
    captions: [],
    chapters: [
      {at: 0, title: '밖으로 나온 토끼', recap: '큰 토끼가 밝은 풀밭으로 나와 주변을 살펴요 이 장면에는 대사가 없어요'},
      {at: 9, title: '풀밭과 꽃', recap: '햇빛 아래 풀밭과 꽃 사이로 토끼가 움직여요'},
      {at: 23, title: '나비를 바라보는 토끼', recap: '꽃 근처에서 토끼가 나비를 바라보고 있어요'},
      {at: 32, title: '열매를 집어 든 토끼', recap: '토끼가 풀밭에서 빨간 열매를 집어 들어요'}
    ]
  }
];
