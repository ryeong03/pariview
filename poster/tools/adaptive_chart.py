"""Poster-styled adaptive-fitting chart (SVG) for poster v10. Reads research/adaptive-fitting/simulation-results.json (matched condition), writes
/Users/ryeong/Desktop/pariview/poster/assets/adaptive-chart.svg + a preview HTML on the poster surface. Colors/fonts = poster tokens; flat, no glow."""
import json
d = json.load(open('/Users/ryeong/Desktop/pariview/research/adaptive-fitting/simulation-results.json'))
c = d['conditions']['matched']['policies']
A, F = c['adaptive'], c['fixed']
W, H = 400, 150                       # viewBox; placed at ~105mm wide → 1mm ≈ 3.81u
L, R, T, B = 44, 58, 36, 30           # plot margins (left axis, right end-labels, title, x axis)
pw, ph = W - L - R, H - T - B
ymax = 0.30
def X(i): return L + pw * i / 5
def Y(v): return T + ph * (1 - v / ymax)
LIME, CYAN, SURF, LINE, TEXT, MUTED = '#cdff5f', '#4df3ff', '#1b1829', '#36314c', '#f3f2f8', '#c6c3d6'
FONT = "Pretendard, 'Apple SD Gothic Neo', sans-serif"
def path(vals): return 'M' + ' L'.join(f'{X(i):.1f} {Y(v):.1f}' for i, v in enumerate(vals))
def band(lo, hi):
    up = ' L'.join(f'{X(i):.1f} {Y(v):.1f}' for i, v in enumerate(hi))
    dn = ' L'.join(f'{X(i):.1f} {Y(v):.1f}' for i, v in reversed(list(enumerate(lo))))
    return f'M{up} L{dn} Z'
g = []
g.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="6" fill="{SURF}" stroke="{LINE}" stroke-width="1.2"/>')
# title + legend (text tokens; swatches carry identity)
g.append(f'<text x="12" y="17" font-size="16" font-weight="800" fill="{TEXT}">비교 횟수에 따른 설정값 오차</text>')
g.append(f'<text x="12" y="31" font-size="12.5" fill="{MUTED}">합성 데이터 · 조건별 500 · 띠 = 95% 구간</text>')
lx = W - 12
g.append(f'<text x="{lx}" y="17" text-anchor="end" font-size="13" fill="{TEXT}">적응형</text>')
g.append(f'<line x1="{lx-58}" y1="12.5" x2="{lx-44}" y2="12.5" stroke="{LIME}" stroke-width="3" stroke-linecap="round"/>')
g.append(f'<text x="{lx-66}" y="17" text-anchor="end" font-size="13" fill="{TEXT}">고정</text>')
g.append(f'<line x1="{lx-110}" y1="12.5" x2="{lx-96}" y2="12.5" stroke="{CYAN}" stroke-width="3" stroke-dasharray="4 3" stroke-linecap="round"/>')
# grid + axes (hairline, solid, recessive)
for v in (0.1, 0.2, 0.3):
    g.append(f'<line x1="{L}" y1="{Y(v):.1f}" x2="{L+pw}" y2="{Y(v):.1f}" stroke="{LINE}" stroke-width="1"/>')
    g.append(f'<text x="{L-6}" y="{Y(v)+3.5:.1f}" text-anchor="end" font-size="13" fill="{MUTED}">{v:.2f}</text>')
g.append(f'<text x="{L-6}" y="{Y(0)+3.5:.1f}" text-anchor="end" font-size="13" fill="{MUTED}">0</text>')
g.append(f'<line x1="{L}" y1="{Y(0):.1f}" x2="{L+pw}" y2="{Y(0):.1f}" stroke="{MUTED}" stroke-width="1" opacity=".6"/>')
for i in range(6):
    g.append(f'<text x="{X(i):.1f}" y="{Y(0)+15:.1f}" text-anchor="middle" font-size="13" fill="{MUTED}">{i}</text>')
g.append(f'<text x="{L+pw/2:.1f}" y="{H-5}" text-anchor="middle" font-size="13" fill="{MUTED}">A/B 비교 횟수</text>')
# bands → lines → dots (surface ring)
g.append(f'<path d="{band(F["ci95_low"], F["ci95_high"])}" fill="{CYAN}" opacity=".12"/>')
g.append(f'<path d="{band(A["ci95_low"], A["ci95_high"])}" fill="{LIME}" opacity=".14"/>')
g.append(f'<path d="{path(F["mean_nmae"])}" fill="none" stroke="{CYAN}" stroke-width="2.4" stroke-dasharray="5 4" stroke-linecap="round" stroke-linejoin="round"/>')
g.append(f'<path d="{path(A["mean_nmae"])}" fill="none" stroke="{LIME}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
for i, v in enumerate(F['mean_nmae']): g.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="4.2" fill="{CYAN}" stroke="{SURF}" stroke-width="1.6"/>')
for i, v in enumerate(A['mean_nmae']): g.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="4.4" fill="{LIME}" stroke="{SURF}" stroke-width="1.6"/>')
# direct end labels in text tokens (no numbers)
ya, yf = Y(A['mean_nmae'][5]), Y(F['mean_nmae'][5])
if ya - yf < 15: yf = ya - 15   # fixed line ends higher → its label sits above
g.append(f'<text x="{L+pw+8}" y="{ya+4.5:.1f}" font-size="14" font-weight="800" fill="{TEXT}">적응형</text>')
g.append(f'<text x="{L+pw+8}" y="{yf+4.5:.1f}" font-size="14" font-weight="700" fill="{MUTED}">고정</text>')
# annotation: residual error after 5 → why +5 is offered
svg = f'<svg class="afit-chart" viewBox="0 0 {W} {H}" role="img" aria-label="A/B 비교 횟수에 따른 설정값 추정 오차, 적응형과 고정 비교 (합성 데이터)" font-family="{FONT}">' + ''.join(g) + '</svg>'
open('/Users/ryeong/Desktop/pariview/poster/assets/adaptive-chart.svg', 'w').write(svg.replace('<svg class="afit-chart"', '<svg xmlns="http://www.w3.org/2000/svg" class="afit-chart"'))
open('/Users/ryeong/Desktop/pariview/poster/tools/adaptive-chart.fragment.html', 'w').write(svg)
html = f'''<!doctype html><meta charset="utf-8"><style>@font-face{{font-family:Pretendard;src:local("Pretendard")}} body{{margin:0;background:#15131f;padding:24px}} .sec{{background:#1b1829;padding:20px;border-radius:8px;width:min-content}} svg{{width:1200px;height:auto;display:block}}</style><div class="sec">{svg}</div>'''
open('/Users/ryeong/Desktop/pariview/poster/tools/adaptive-chart-preview.html', 'w').write(html)
print('wrote /Users/ryeong/Desktop/pariview/poster/assets/adaptive-chart.svg', len(svg), 'bytes; A5', [round(v,3) for v in A['mean_nmae']], 'F5', [round(v,3) for v in F['mean_nmae']])
