"""Analyze recorded distances to repeated reference settings; empty inputs produce no curve."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
AXES=['brightness','contrast','volume'];BOUNDS=[(45,100),(65,110),(0,70)]
CONTEXT=['clip_id','segment_start','segment_end','playback_rate']

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return [r for r in csv.DictReader(f) if any(v.strip() for v in r.values() if v)]

def values(row):
    array=np.array([float(row[k]) for k in AXES])
    if not np.isfinite(array).all() or any(v<lo or v>hi for v,(lo,hi) in zip(array,BOUNDS)):raise ValueError('Missing or out-of-range setting')
    return array

def context(row):
    return (row['clip_id'],*[float(row[k]) for k in CONTEXT[1:]])

def main():
    p=argparse.ArgumentParser();p.add_argument('--trials',type=Path,default=HERE/'human-trials-template.csv')
    p.add_argument('--references',type=Path,default=HERE/'human-reference-template.csv')
    p.add_argument('--out',type=Path,default=HERE/'private'/'analysis');args=p.parse_args()
    trials=read(args.trials);refs=read(args.references);args.out.mkdir(parents=True,exist_ok=True)
    if not trials and not refs:
        status={'observed_n':0,'complete_paired_n':0,'data_rows':0,'curve_created':False,'state':'empty_provided_templates'}
        (args.out/'status.json').write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status));return
    participants=sorted({r['participant_id'] for r in trials+refs});groups=defaultdict(list);reference=defaultdict(list)
    for row in trials:
        values(row);context(row);r=int(row['round'])
        if row['condition'] not in ['adaptive','fixed'] or not 0<=r<=5:raise ValueError('Primary analysis accepts adaptive/fixed rounds0–5 only')
        if r and (row['axis'] not in AXES or row['outcome'] not in ['a','b','equal','unsure','skip']):raise ValueError('Record actual axis and outcome')
        groups[row['participant_id'],row['condition']].append(row)
    for row in refs:values(row);context(row);reference[row['participant_id']].append(row)
    included=[];incomplete=[];distances={k:[] for k in ['adaptive','fixed']};reference_spread=[]
    widths=np.array([hi-lo for lo,hi in BOUNDS])
    for pid in participants:
        rr=reference[pid];conditions=[groups[pid,k] for k in ['adaptive','fixed']]
        if len(rr)!=3 or {int(r['replicate']) for r in rr}!={1,2,3} or any(len(rows)!=6 or {int(r['round']) for r in rows}!=set(range(6)) for rows in conditions):
            incomplete.append(pid);continue
        if len({context(r) for r in rr+conditions[0]+conditions[1]})!=1:raise ValueError('Each paired case must share a clip/segment/playback rate')
        reference_values=np.array([values(r) for r in rr]);center=np.median(reference_values,axis=0)
        reference_spread.append(((reference_values.max(axis=0)-reference_values.min(axis=0))/widths).tolist())
        for method,rows in zip(['adaptive','fixed'],conditions):
            settings=np.array([values(r) for r in sorted(rows,key=lambda r:int(r['round']))])
            distances[method].append(np.mean(np.abs(settings-center)/widths,axis=1).tolist())
        included.append(pid)
    result={'observed_n':len(participants),'complete_paired_n':len(included),'incomplete_n':len(incomplete),
            'metric':'Normalized distance to the component-wise median of three independent reference adjustments, not a known human true preference',
            'mean_distances':{k:np.mean(v,axis=0).tolist() if v else [] for k,v in distances.items()},
            'reference_within_person_range_mean':np.mean(reference_spread,axis=0).tolist() if reference_spread else [],'curve_created':bool(included)}
    (args.out/'status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if included:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(7,4.5),layout='constrained')
        for method,color in [('adaptive','#284abd'),('fixed','#bd4e65')]:
            for trace in distances[method]:ax.plot(range(6),trace,color=color,alpha=.16,lw=.8)
            ax.plot(range(6),result['mean_distances'][method],marker='o',label=method,color=color,lw=2)
        ax.set(xlabel='Recorded comparison responses',ylabel='Normalized distance to repeated reference settings',
               title=f'Recorded paired cases: n={len(included)}',xticks=range(6),ylim=(0,1));ax.legend();ax.grid(alpha=.2)
        fig.savefig(args.out/'recorded-reference-distance.pdf');plt.close(fig)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
