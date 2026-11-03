"""v10 draft: adaptive fitting as the technical core — apply ONLY after the engine is live in the public app.
Run: python3 poster/tools/apply_v10.py [html-path]   (then autofit, render.py, orphans, arch audit)
Wording follows the research agent's guidance: flow over numbers, no convergence/guarantee claims, no human-curve reading.
Chart fragment comes from poster/tools/adaptive_chart.py (poster tokens, flat colors)."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else '/Users/ryeong/Desktop/pariview/poster/PariView_A1.html'
s = open(p, encoding='utf-8').read()
chart = open('/Users/ryeong/Desktop/pariview/poster/tools/adaptive-chart.fragment.html', encoding='utf-8').read()
def rep(o, n):
    global s
    assert s.count(o) == 1, (s.count(o), o[:70]); s = s.replace(o, n)

# card 01: adaptive wording (keeps the real screenshot)
rep('<p>같은 장면 A · B 중 지금 편한 쪽을 눌러요 · 비슷해요 · 건너뛰기</p>',
    '<p>A · B 중 편한 쪽을 누르면 <b>다음 비교가 바뀌어요</b> · 5회로 시작, 원하면 5회씩 추가</p>')
rep('<li><b>진단이 아니라 비교로</b><span>AI 추천 시작점 → 같은 장면 A/B → 저장 → 재조절</span></li>',
    '<li><b>진단이 아니라 비교로</b><span>AI 추천 시작점 → 적응형 A/B → 저장 → 재조절</span></li>')

# section 3: sub-flows + adaptive flow strip on the left, poster-styled chart on the right
old = '<div class="sub-flows"><p><b>🤖 AI 추천 · Claude</b>'
assert s.count(old) == 1
a = s.index(old); b = s.index('</div>', s.index('어두운 장면 보정</p>', a)) + len('</div>')
subflows = s[a:b]
adaptive = ('<div class="adaptive"><b>🎯 적응형 피팅</b><span class="step">A/B 선택<small>비슷해요 · 건너뛰기 가능</small></span><i>→</i><span class="step">선호 범위 갱신<small>축별 사후분포</small></span><i>→</i>'
            '<span class="step">다음 쌍 선택<small>기대 정보이득 최대</small></span><i>→</i><span class="step">5회 후 추정 설정<small>원하면 5회씩 추가 · 최대 20회</small></span></div>')
s = s[:a] + '<div class="under"><div class="under-l">' + subflows + adaptive + '</div>' + chart + '</div>' + s[b:]

# section 2: give 4mm of the screenshot stack to section 3
css_stack = [l for l in s.split('\n') if '.shot .stack' in l and 'height: 126mm' in l]
assert len(css_stack) == 1, css_stack
s = s.replace(css_stack[0], css_stack[0].replace('height: 126mm', 'height: 122mm'))

# card 01 screenshot: use the adaptive capture when the web agent has delivered it (keeps step2.png on disk)
import os
if os.path.exists(os.path.join(os.path.dirname(p), 'assets', 'step2-adaptive.png')):
    rep('<img src="assets/step2.png"', '<img src="assets/step2-adaptive.png"')
    print('card 01 → step2-adaptive.png')
else:
    print('WARNING: assets/step2-adaptive.png not found — card 01 keeps step2.png')

# section 4 diagram: 피팅 UI caption
rep('프로필 5 · A/B 5단계', '프로필 5 · 적응형 A/B 5+5')

css = '''
  .under { display: grid; grid-template-columns: minmax(0,1fr) 96mm; gap: 2mm 6mm; align-items: start; margin-top: 1.5mm; }
  .under .sub-flows { margin-top: 0; }
  .afit-chart { width: 100%; height: auto; display: block; }
  .adaptive { display: flex; align-items: center; flex-wrap: wrap; gap: 2mm; margin-top: 2mm; }
  .adaptive > b { font-size: 13pt; color: var(--lime); margin-right: 1mm; }
  .adaptive .step { display: inline-flex; flex-direction: column; padding: 1.2mm 2.8mm; border: .35mm solid var(--line); border-radius: 1.5mm; font-size: 12pt; font-weight: 700; line-height: 1.2; }
  .adaptive .step small { font-size: 9.5pt; color: var(--muted); font-weight: 400; }
  .adaptive i { font-style: normal; color: var(--muted); font-size: 13pt; }
'''
s = s.replace('</style>', css + '</style>', 1)
s = '\n'.join(l.rstrip() for l in s.split('\n'))
open(p, 'w', encoding='utf-8').write(s)
print('v10 draft applied to', p, '— now refit/render/audit')
