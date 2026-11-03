"""Before/after report and invariants for the advance-notice subset of each scene map.

Usage: python3 analysis/notice_report.py [web/dist/assets/scenes/*-map.json]
Exit 1 if any invariant fails (cooldown spacing, notices ⊆ events, bounds).
"""
import json, sys
from pathlib import Path

paths = [Path(p) for p in sys.argv[1:]] or sorted(Path('web/dist/assets/scenes').glob('*-map.json'))
ok = True
for p in paths:
    d = json.loads(p.read_text())
    ev, nt = d['events'], d.get('noticeEvents', [])
    before = Path('/tmp') / (p.stem + '.before.json')
    b = json.loads(before.read_text())['events'] if before.exists() else ev
    print(f"{p.stem:12s} 전체 변화 {len(ev):2d}개 · 예고 BEFORE {len(b):2d}개 → AFTER {len(nt):2d}개 · 중앙값 {d['noticeMethod']['clipLoudnessMedianLufs']} LUFS · 밝기 범위 {d['noticeMethod']['clipLumaRange']}")
    for e in nt:
        print(f"   {e['at']:5.1f}s  {e['type']:8s} 강도 {e['strength']:.2f}  {e['why']}")
    starts = sorted(e['at'] for e in ev)
    for i, e in enumerate(nt):
        if i and e['at'] - nt[i - 1]['at'] < 5.0: ok = False; print('   !! 5초 간격 위반', e)
        if not (0 <= e['at'] <= d['duration']): ok = False; print('   !! 범위 밖', e)
        if min(abs(e['at'] - s) for s in starts) > 0.001: ok = False; print('   !! events에 없는 예고', e)
print('OK' if ok else 'FAIL'); sys.exit(0 if ok else 1)
