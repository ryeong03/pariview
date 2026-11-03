"""Summarize entered observations only; blank templates never produce study results."""
import csv
import json
import statistics as st
import sys
from pathlib import Path

RATINGS = ('comfort', 'visual', 'audio', 'caption')

def load_rows(path):
    path = Path(path)
    if path.suffix.lower() == '.xlsx':
        from openpyxl import load_workbook
        book = load_workbook(path, data_only=True)
        merged = {}
        for name in ('진행', '시청', '사용성'):
            sheet = book[name]
            keys = [cell.value for cell in sheet[1]]
            seen = set()
            for values in sheet.iter_rows(min_row=3, values_only=True):
                row = dict(zip(keys, values))
                pid = row.get('id')
                if not pid:
                    continue
                if pid in seen:
                    raise ValueError(f'{name}: 중복 ID {pid}')
                seen.add(pid)
                merged.setdefault(str(pid), {}).update(row)
        return list(merged.values())
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def num(row, key, low, high, integer=True):
    raw = row.get(key)
    if raw is None or str(raw).strip() == '':
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f'{row.get("id")}: {key} 숫자가 아니에요')
    if not low <= value <= high or (integer and not value.is_integer()):
        raise ValueError(f'{row.get("id")}: {key} 범위를 확인해 주세요 ({low}~{high})')
    return value

def describe(values):
    if not values:
        return {'n': 0}
    return {'n': len(values), 'mean': round(st.mean(values), 3),
            'median': round(st.median(values), 3), 'min': min(values), 'max': max(values)}

def summarize(rows):
    ids = [str(r['id']) for r in rows if r.get('id')]
    if len(ids) != len(set(ids)):
        raise ValueError('중복 참여자 ID가 있어요')
    started = []
    for row in rows:
        status = str(row.get('status') or 'not_started').strip()
        if status not in ('not_started','completed','partial','withdrawn'):
            raise ValueError(f'{row.get("id")}: status 값을 확인해 주세요')
        if status == 'not_started':
            continue
        started.append(row)
        for key in [f'{c}_{r}' for c in ('A','B') for r in RATINGS]:
            num(row,key,0,10)
        for i in range(1,11):
            num(row,f'sus_{i}',1,5)
        elapsed = num(row,'fit_elapsed_s',0,86400,False)
        pause = num(row,'fit_pause_s',0,86400,False)
        if elapsed is not None and pause is not None and pause > elapsed:
            raise ValueError(f'{row.get("id")}: 휴식 시간이 전체 경과 시간보다 커요')
    if not started:
        return {'status':'no_observations','message':'실제 응답이 입력되지 않은 빈 서식이에요','observed_n':0}
    usable = [r for r in started if r.get('data_consent')=='yes' and r.get('status')!='withdrawn']
    eligible = [r for r in usable if r.get('A_complete')=='yes' and r.get('B_complete')=='yes'
                and r.get('protocol_deviation')=='no' and r.get('actual_order') in ('AB','BA')]
    comparisons = {}
    for key in RATINGS:
        pairs=[]
        for r in eligible:
            a,b = num(r,f'A_{key}',0,10), num(r,f'B_{key}',0,10)
            if a is not None and b is not None:
                pairs.append({'id':r['id'],'order':r['actual_order'],'A':a,'B':b,'delta':b-a})
        ds=[r['delta'] for r in pairs]
        comparisons[key] = {'A':describe([r['A'] for r in pairs]),'B':describe([r['B'] for r in pairs]),
            'difference_B_minus_A':describe(ds),'increased':sum(d>0 for d in ds),
            'unchanged':sum(d==0 for d in ds),'decreased':sum(d<0 for d in ds),'individual_pairs':pairs,
            'by_order':{order:describe([r['delta'] for r in pairs if r['order']==order]) for order in ('AB','BA')}}
    sus=[]
    for r in usable:
        values=[num(r,f'sus_{i}',1,5) for i in range(1,11)]
        if all(v is not None for v in values):
            score=sum((v-1 if i%2==0 else 5-v) for i,v in enumerate(values))*2.5
            sus.append({'id':r['id'],'score':score})
    attempted=[r for r in usable if r.get('fit_status') in ('unaided','assisted','not_completed')]
    completed=[r for r in attempted if r.get('fit_status') in ('unaided','assisted')]
    active_times=[]; elapsed_times=[]
    for r in completed:
        elapsed,pause=num(r,'fit_elapsed_s',0,86400,False),num(r,'fit_pause_s',0,86400,False)
        if elapsed is not None: elapsed_times.append(elapsed)
        if elapsed is not None and pause is not None: active_times.append(elapsed-pause)
    preferences={value:sum(r.get('preference')==value for r in usable) for value in ('A','B','same','neither','na')}
    return {'status':'observations_entered','observed_n':len(started),'data_use_n':len(usable),
        'partial_n':sum(r.get('status')=='partial' for r in started),'withdrawn_n':sum(r.get('status')=='withdrawn' for r in started),
        'recorded_deviations_n':sum(r.get('protocol_deviation')=='yes' for r in usable),
        'paired_ratings':comparisons,'sus_project_korean_translation':{'scores':sus,**describe([s['score'] for s in sus])},
        'fitting':{'attempted_n':len(attempted),'unaided_completed_n':sum(r.get('fit_status')=='unaided' for r in attempted),
        'assisted_completed_n':sum(r.get('fit_status')=='assisted' for r in attempted),
        'completed_elapsed_seconds':describe(elapsed_times),'completed_active_seconds':describe(active_times)},
        'preference_counts':preferences,
        'report_note':'유효 n과 개인별 결과를 함께 보고해요 자체 0–10점 질문과 SUS 방식 점수를 혼합하거나 퍼센트 개선율로 바꾸지 않아요'}

if __name__ == '__main__':
    if len(sys.argv)!=2:
        raise SystemExit('사용법: python3 analyze.py private/responses.xlsx (또는 .csv)')
    try:
        result=summarize(load_rows(sys.argv[1]))
    except (ValueError,KeyError) as e:
        raise SystemExit(str(e))
    print(json.dumps(result,ensure_ascii=False,indent=2))
