"""Convert a provided fit snapshot to local study rows; never fabricate responses."""
import argparse
import csv
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser();p.add_argument('snapshot',type=Path);p.add_argument('--participant-code',required=True)
    p.add_argument('--order',choices=['AF','FA'],required=True);p.add_argument('--out',type=Path,default=HERE/'private'/'trials.csv');args=p.parse_args()
    if not re.fullmatch(r'P[0-9]{2,4}',args.participant_code):raise SystemExit('Use an anonymous participant code such as P01')
    data=json.loads(args.snapshot.read_text());condition=data.get('policy')
    if condition not in ['adaptive','fixed']:raise SystemExit('Snapshot policy must be adaptive or fixed')
    context=data.get('context',{});segment=context.get('segment',{})
    required=[context.get('clipId'),segment.get('start'),segment.get('end'),context.get('playbackRate')]
    if any(v is None or v=='' for v in required):raise SystemExit('Record clipId, segment start/end and playbackRate before importing')
    fields=next(csv.reader((HERE/'human-trials-template.csv').open()))
    common={'participant_id':args.participant_code,'condition':condition,'clip_id':required[0],'segment_start':required[1],
            'segment_end':required[2],'playback_rate':required[3],'engine_version':data['version'],'order':args.order}
    rows=[]
    for i,item in enumerate([None]+data['history']):
        settings=data['initialSettings'] if item is None else item['settingsAfter']
        row={**common,'round':i,**{k:settings[k] for k in ['brightness','contrast','volume']}}
        if item:
            q=item['question'];row.update(axis=q['axis'],a=q['a'],b=q['b'],outcome=item['outcome'])
        rows.append(row)
    existing=[]
    if args.out.exists():
        with args.out.open(encoding='utf-8-sig',newline='') as f:existing=list(csv.DictReader(f))
        if any(r['participant_id']==args.participant_code and r['condition']==condition for r in existing):raise SystemExit('This participant/method already exists; inspect the local file instead of overwriting')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(existing+rows)
    print(json.dumps({'rows_added':len(rows),'condition':condition,'output':str(args.out)}))

if __name__=='__main__':main()
