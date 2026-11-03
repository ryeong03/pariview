"""Summarize a real-user fitting study for the poster.

Target = each participant's own manually found preference (pref_*), not a team-chosen value.
Usage: python3 analysis/user-study/user_study.py analysis/user-study/results.csv
"""
import csv
import statistics
import sys
from pathlib import Path

RANGES = {'brightness': (45, 100), 'contrast': (65, 110), 'volume': (0, 70)}
DEFAULT = {'brightness': 85, 'contrast': 90, 'volume': 35}


def err(vals, pref):
    return statistics.mean(abs(vals[k] - pref[k]) / (hi - lo) for k, (lo, hi) in RANGES.items())


def main(path):
    rows = [r for r in csv.DictReader(Path(path).open(encoding='utf-8')) if r.get('id', '').strip()]
    if not rows:
        raise SystemExit('results.csv에 참가자 행이 없어요')
    n = len(rows)
    before, after, improved, times, cb, ca, more_comfortable, sus = [], [], 0, [], [], [], 0, []
    groups = {}
    for r in rows:
        pref = {k: float(r[f'pref_{k}']) for k in RANGES}
        fit = {k: float(r[f'fit_{k}']) for k in RANGES}
        e0, e1 = err(DEFAULT, pref), err(fit, pref)
        before.append(e0); after.append(e1); improved += e1 < e0
        times.append(float(r['fit_seconds']))
        b, a = float(r['comfort_before']), float(r['comfort_after'])
        cb.append(b); ca.append(a); more_comfortable += a > b
        if r.get('sus', '').strip():
            sus.append(float(r['sus']))
        groups[r.get('group', '?')] = groups.get(r.get('group', '?'), 0) + 1
    mb, ma = statistics.mean(before), statistics.mean(after)
    t = statistics.mean(times)
    label = {'sensitive': '소리·빛에 민감한 편', 'typical': '그렇지 않은'}
    who = ' · '.join(f"{label.get(g, g)} {c}명" for g, c in groups.items())
    print(f'참가자 {n}명 ({who})')
    print(f'직접 찾은 선호값과의 정규화 오차: 기본값 {mb:.3f} → 피팅 후 {ma:.3f} ({(1 - ma / mb) * 100:+.0f}% 변화, 오차가 줄어든 사람 {improved}/{n})')
    print(f'편안함(1~5): 피팅 전 {statistics.mean(cb):.1f} → 후 {statistics.mean(ca):.1f}, {n}명 중 {more_comfortable}명이 피팅 후 더 편안하다고 답함')
    print(f'피팅 소요 평균 {int(t // 60)}분 {int(t % 60)}초')
    if sus:
        print(f'SUS 평균 {statistics.mean(sus):.0f}점 (n={len(sus)})')
    print('\n포스터 문장:')
    print(f'검증 · 실제 사용자 {n}명 피팅 실험 ({who}) · 직접 찾은 선호값과의 오차 {mb:.2f} → {ma:.2f} · {n}명 중 {more_comfortable}명이 피팅 후 더 편안하다고 응답 · 평균 {int(t // 60)}분 {int(t % 60)}초')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'analysis/user-study/results.csv')
