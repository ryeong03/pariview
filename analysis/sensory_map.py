"""Generate PariView's sensory map from the video signal itself.

Sound: EBU R128 momentary loudness (400 ms window, 100 ms hop) via ffmpeg ebur128.
Light: per-frame mean luma (YAVG, 0-255) via ffmpeg signalstats.

A "sound change" is a moment where loudness rises sharply above the recent level,
and a "light change" is a moment where mean brightness jumps quickly.
These are signal events, not predictions of anyone's discomfort.

Usage: python3 analysis/sensory_map.py web/dist/assets/scenes/tears-lab.mp4 web/dist/assets/scenes/tears-lab-map.json
Output: events (full map lanes) + noticeEvents (sparse advance-notice subset) + methods
"""
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

# Thresholds (documented in the output so the UI can show them)
SOUND_RISE_LU = 6.0        # loudness above the trailing median of the previous 1.5 s
SOUND_LOUD_LUFS = -16.0    # or simply loud in absolute terms
LIGHT_JUMP_Y = 18.0        # mean-luma change within 0.25 s (0-255 scale)
MERGE_GAP_S = 0.4
MIN_LEN_S = 0.2
LIGHT_HOLD_S = 0.8      # a cut is instantaneous, so keep the event visible for a moment after it
SILENCE_LUFS = -70.0

# Advance-notice subset ("확실히 변할 때만"): strong, sparse, demo-oriented thresholds — not medical risk levels
NOTICE_SOUND_RISE_LU = 18.0      # sharp rise above the trailing level ...
NOTICE_SOUND_ABOVE_MED_LU = 4.0  # ... that also ends up louder than the clip's typical level
NOTICE_SOUND_LOUD_OVER_MED = 12.0  # or simply much louder than the clip's typical level
NOTICE_LIGHT_JUMP_Y = 45.0       # big cut in mean brightness (0-255) ...
NOTICE_LIGHT_RANGE_RATIO = 0.30  # ... that is also a large share of the clip's own brightness range
NOTICE_COOLDOWN_S = 5.0          # at most one notice per 5 s; the stronger one wins
NOTICE_MERGE_S = 2.0             # sound + light within 2 s become one "빛·소리 변화" notice
NOTICE_SKIP_START_S = 1.0        # ignore the clip's first second (fade-in from silence)


def run_ffmpeg(video, filt, key, out):
    stream = '-af' if filt.startswith('ebur128') else '-vf'
    subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-loglevel', 'error', '-i', str(video), stream,
                    f'{filt},{"a" if stream == "-af" else ""}metadata=print:key={key}:file={out}', '-f', 'null', '-'],
                   check=True)
    times, values = [], []
    t = None
    for line in Path(out).read_text().splitlines():
        m = re.search(r'pts_time:([\d.]+)', line)
        if m:
            t = float(m.group(1))
            continue
        if line.startswith(key + '=') and t is not None:
            times.append(t)
            values.append(float(line.split('=', 1)[1]))
    return times, values


def segments(flags, times, step, min_len=None):
    segs, start = [], None
    for t, f in zip(times, flags):
        if f and start is None:
            start = t
        if not f and start is not None:
            segs.append([start, t])
            start = None
    if start is not None:
        segs.append([start, times[-1] + step])
    merged = []
    for s in segs:
        if merged and s[0] - merged[-1][1] <= MERGE_GAP_S:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    min_len = MIN_LEN_S if min_len is None else min_len
    return [s for s in merged if s[1] - s[0] >= min_len]


def main(video, out_json):
    video = Path(video)
    lt, lv = run_ffmpeg(video, 'ebur128=metadata=1', 'lavfi.r128.M', '/tmp/pariview_loud.txt')
    yt, yv = run_ffmpeg(video, 'signalstats', 'lavfi.signalstats.YAVG', '/tmp/pariview_luma.txt')
    duration = max(lt[-1] if lt else 0, yt[-1] if yt else 0)

    # Sound: rise above trailing median, ignoring silence
    sound_flags, sound_peaks = [], []
    for i, (t, v) in enumerate(zip(lt, lv)):
        past = [x for x in lv[max(0, i - 15):i] if x > SILENCE_LUFS]
        base = statistics.median(past) if past else v
        rise = v - base
        sound_flags.append(v > SILENCE_LUFS and (rise >= SOUND_RISE_LU or v >= SOUND_LOUD_LUFS))
        sound_peaks.append(rise)
    sound = segments(sound_flags, lt, 0.1)

    # Light: luma change over ~0.25 s (6 frames at 24 fps)
    fps_step = (yt[1] - yt[0]) if len(yt) > 1 else 1 / 24
    lag = max(1, round(0.25 / fps_step))
    light_flags = [i >= lag and abs(yv[i] - yv[i - lag]) >= LIGHT_JUMP_Y for i in range(len(yv))]
    light = [[a, min(duration, b + LIGHT_HOLD_S)] for a, b in segments(light_flags, yt, fps_step, min_len=0)]

    def describe_sound(s):
        idx = [i for i, t in enumerate(lt) if s[0] <= t < s[1]]
        rise = max(sound_peaks[i] for i in idx)
        from_silence = all(x <= SILENCE_LUFS for x in lv[max(0, idx[0] - 15):idx[0]])
        return {'at': round(s[0], 2), 'end': round(s[1], 2), 'type': '소리 변화',
                'peakLufs': round(max(lv[i] for i in idx), 1),
                'riseLu': None if from_silence else round(rise, 1), 'fromSilence': from_silence}

    def describe_light(s):
        idx = [i for i, t in enumerate(yt) if s[0] <= t < s[1]]
        deltas = [yv[i] - yv[i - lag] for i in idx if i >= lag]
        jump = max(deltas, key=abs)
        return {'at': round(s[0], 2), 'end': round(s[1], 2), 'type': '빛 변화',
                'jumpY': round(jump, 1), 'direction': '밝아짐' if jump > 0 else '어두워짐'}

    events = sorted([describe_sound(s) for s in sound] + [describe_light(s) for s in light], key=lambda e: e['at'])

    # --- advance-notice subset ---
    loud_vals = [v for v in lv if v > SILENCE_LUFS]
    loud_med = statistics.median(loud_vals) if loud_vals else -70.0
    luma_range = (max(yv) - min(yv)) if yv else 0.0
    scored = []
    for e in events:
        if e['at'] < NOTICE_SKIP_START_S:
            continue
        if e['type'] == '소리 변화':
            if e.get('fromSilence'):
                continue
            over = e['peakLufs'] - loud_med
            sharp = (e['riseLu'] or 0) >= NOTICE_SOUND_RISE_LU and over >= NOTICE_SOUND_ABOVE_MED_LU
            loud = over >= NOTICE_SOUND_LOUD_OVER_MED
            if sharp or loud:
                scored.append({**e, 'strength': round(max((e['riseLu'] or 0) / NOTICE_SOUND_RISE_LU, over / NOTICE_SOUND_LOUD_OVER_MED), 2),
                               'why': f'중앙값 대비 +{over:.1f}LU' + (f', 상승 {e["riseLu"]}LU' if sharp else '')})
        else:
            jump = abs(e['jumpY'])
            if jump >= NOTICE_LIGHT_JUMP_Y and luma_range and jump >= NOTICE_LIGHT_RANGE_RATIO * luma_range:
                scored.append({**e, 'strength': round(jump / NOTICE_LIGHT_JUMP_Y, 2), 'why': f'밝기 {e["direction"]} {jump:.0f} (클립 범위의 {100 * jump / luma_range:.0f}%)'})
    # merge sound+light that land together, then enforce the cooldown keeping the stronger notice
    scored.sort(key=lambda e: e['at'])
    merged = []
    for e in scored:
        if merged and e['at'] - merged[-1]['at'] <= NOTICE_MERGE_S and merged[-1]['type'] != e['type']:
            m = merged[-1]
            m['type'] = '빛·소리 변화'
            m['end'] = max(m['end'], e['end'])
            m['strength'] = max(m['strength'], e['strength'])
            m['why'] = m['why'] + ' · ' + e['why']
        else:
            merged.append(dict(e))
    notices = []
    for e in merged:
        if notices and e['at'] - notices[-1]['at'] < NOTICE_COOLDOWN_S:
            if e['strength'] > notices[-1]['strength']:
                notices[-1] = e
            continue
        notices.append(e)
    notice_events = [{k: e[k] for k in ('at', 'end', 'type', 'strength', 'why')} for e in notices]

    def downsample(times, values, hz=10):
        out, nxt = [], 0.0
        for t, v in zip(times, values):
            if t >= nxt:
                out.append([round(t, 2), round(max(v, -70.0), 1)])
                nxt += 1 / hz
        return out

    data = {
        'source': video.name,
        'duration': round(duration, 2),
        'method': {
            'sound': f'EBU R128 순간 라우드니스(0.4초 창, 0.1초 간격)가 직전 1.5초 중앙값보다 {SOUND_RISE_LU:g}LU 이상 오르거나 {SOUND_LOUD_LUFS:g}LUFS 이상인 구간',
            'light': f'프레임 평균 밝기(0–255)가 0.25초 안에 {LIGHT_JUMP_Y:g} 이상 바뀐 순간부터 {LIGHT_HOLD_S:g}초',
            'note': '영상 신호에서 측정한 변화 구간이에요 누군가의 불편을 예측하거나 진단하지 않아요',
        },
        'events': events,
        'noticeEvents': notice_events,
        'noticeMethod': {
            'sound': f'소리: 직전 1.5초보다 {NOTICE_SOUND_RISE_LU:g}LU 이상 급상승하면서 클립 중앙값보다 {NOTICE_SOUND_ABOVE_MED_LU:g}LU 이상 크거나, 중앙값보다 {NOTICE_SOUND_LOUD_OVER_MED:g}LU 이상 큰 구간',
            'light': f'빛: 0.25초 안에 평균 밝기가 {NOTICE_LIGHT_JUMP_Y:g} 이상 바뀌고 그 변화가 클립 밝기 범위의 {NOTICE_LIGHT_RANGE_RATIO * 100:.0f}% 이상인 구간',
            'spacing': f'{NOTICE_MERGE_S:g}초 안의 빛·소리 변화는 하나로 합치고, {NOTICE_COOLDOWN_S:g}초 안에는 더 강한 변화 하나만 남김 · 첫 {NOTICE_SKIP_START_S:g}초 제외',
            'note': '시연용 예고 기준이며 의학적 위험 수준이나 사용자 불편을 추정한 값이 아니에요 조용한 클립은 예고가 0개일 수 있어요',
            'clipLoudnessMedianLufs': round(loud_med, 1), 'clipLumaRange': round(luma_range, 1),
        },
        'curves': {'loudness': downsample(lt, lv), 'luma': downsample(yt, yv)},
    }
    Path(out_json).write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(json.dumps({'source': video.name, 'duration': data['duration'], 'events': len(events), 'noticeEvents': notice_events}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
