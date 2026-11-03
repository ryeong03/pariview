"""Paired evaluation and exportable figures for declared SYNTHETIC cases."""
import argparse
import gzip
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE=Path(__file__).resolve().parent
LABELS={'deterministic':'일관된 선택','matched':'모델과 일치하는 응답','noisy':'큰 응답 변동','nonresponse':'판단 보류 포함','asymmetric':'비대칭 선호'}
COLORS={'adaptive':'#284abd','fixed':'#bd4e65'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,default=HERE);args=parser.parse_args();out=args.directory
    metadata=json.loads((out/'simulation-metadata.json').read_text())
    with gzip.open(out/'synthetic-records.jsonl.gz','rt') as file:rows=[json.loads(line) for line in file]
    assert all(row['data_kind']=='synthetic' for row in rows)
    rng=np.random.default_rng(20261104)
    summaries={}
    for scenario in metadata['scenarios']:
        sid=scenario['id'];group=sorted((r for r in rows if r['scenario']==sid),key=lambda r:r['case_id']);n=len(group)
        assert n==metadata['n_per_condition'] and len({r['case_id'] for r in group})==n
        idx=rng.integers(0,n,size=(2000,n));policies={};arrays={}
        for policy in ['adaptive','fixed']:
            array=np.array([[p['nmae'] for p in r['policies'][policy]['points']] for r in group]);arrays[policy]=array
            assert array.shape==(n,6) and np.isfinite(array).all() and (array>=0).all() and (array<=1).all()
            boots=array[idx].mean(axis=1);low,high=np.quantile(boots,[.025,.975],axis=0)
            coverage=np.array([[p['contains'] for p in r['policies'][policy]['points'][-1]['intervals'].values()] for r in group],dtype=float)
            policies[policy]={'mean_nmae':array.mean(axis=0).tolist(),'ci95_low':low.tolist(),'ci95_high':high.tolist(),
                              'fraction_nmae_at_most_point10':float((array[:,-1]<=.10).mean()),
                              'posterior80_coverage_at_round5':float(coverage.mean()),
                              'mean_effective_answers':float(np.mean([r['policies'][policy]['counts']['effective'] for r in group]))}
        differences=arrays['adaptive'][:,-1]-arrays['fixed'][:,-1]
        dlo,dhi=np.quantile(differences[idx].mean(axis=1),[.025,.975])
        summaries[sid]={'n':n,'policies':policies,'paired_nmae_difference_adaptive_minus_fixed':float(differences.mean()),
                        'paired_difference_ci95':[float(dlo),float(dhi)],
                        'legacy_reference_round5_nmae':float(np.mean([r['legacy_reference']['points'][-1]['nmae'] for r in group]))}
    result={'data_kind':'synthetic','n_per_condition':metadata['n_per_condition'],'bootstrap_resamples':2000,
            'metric':'Mean of absolute setting errors divided by each of the 3 parameter ranges',
            'uncertainty_scope':'Case bootstrap for this synthetic distribution, not a population CI for human viewers',
            'conditions':summaries,'actual_participant_records':0,'engine_sha256':metadata['engine_sha256']}
    (out/'simulation-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    fonts=font_manager.findSystemFonts()
    chosen=next((f for f in fonts if 'AppleSDGothicNeo' in f),None) or next((f for f in fonts if 'NanumGothic' in f),None)
    if chosen:font_manager.fontManager.addfont(chosen);plt.rcParams['font.family']=font_manager.FontProperties(fname=chosen).get_name()
    plt.rcParams.update({'axes.unicode_minus':False,'font.size':11,'pdf.fonttype':42,'svg.fonttype':'none'})
    x=np.arange(6)
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),gridspec_kw={'width_ratios':[1.05,1]},layout='constrained')
    match=summaries['matched']
    for policy,label in [('adaptive','적응형 비교'),('fixed','고정 비교')]:
        p=match['policies'][policy];axes[0].plot(x,p['mean_nmae'],marker='o',color=COLORS[policy],label=label,lw=2.2)
        axes[0].fill_between(x,p['ci95_low'],p['ci95_high'],color=COLORS[policy],alpha=.12)
    axes[0].set(xlabel='A/B 비교 횟수',ylabel='설정값의 정규화 평균 절대오차',xticks=x,title='같은 5회 예산에서 추정 오차 비교')
    axes[0].legend(frameon=False);axes[0].grid(alpha=.2);axes[0].set_ylim(bottom=0)
    sids=list(summaries)
    for y,sid in enumerate(sids):
        s=summaries[sid];v=s['paired_nmae_difference_adaptive_minus_fixed'];lo,hi=s['paired_difference_ci95']
        axes[1].errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt='o',color='#284abd',capsize=4,ms=6)
    axes[1].axvline(0,color='#7b8493',ls='--',lw=1)
    axes[1].set(yticks=np.arange(len(sids)),yticklabels=[LABELS[s] for s in sids],xlabel='5회 오차 차이: 적응형 - 고정',title='다섯 가지 응답 조건을 모두 확인')
    axes[1].invert_yaxis();axes[1].grid(axis='x',alpha=.2)
    fig.suptitle(f'합성 데이터 시뮬레이션 · 조건별 {metadata["n_per_condition"]}개 선호점',fontweight='bold',fontsize=14)
    fig.supxlabel('띠·오차막대: 합성 사례 재표집 95% 구간 · 왼쪽은 모델 일치 조건 · 오른쪽 음수는 적응형 오차가 더 작음',fontsize=9)
    for ext in ['png','pdf','svg']:fig.savefig(out/f'comparison-overview.{ext}',dpi=220)
    svg_path=out/'comparison-overview.svg'
    svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text().splitlines())+'\n')
    plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(12,7),layout='constrained')
    for ax,(sid,s) in zip(axes.flat,summaries.items()):
        for policy,label in [('adaptive','적응형'),('fixed','고정')]:
            p=s['policies'][policy];ax.plot(x,p['mean_nmae'],'o-',label=label,color=COLORS[policy]);ax.fill_between(x,p['ci95_low'],p['ci95_high'],alpha=.12,color=COLORS[policy])
        ax.set(title=LABELS[sid],xticks=x,xlabel='비교 횟수',ylabel='정규화 MAE',ylim=(0,.35));ax.grid(alpha=.2)
    axes.flat[-1].axis('off');axes.flat[0].legend(frameon=False)
    fig.suptitle('모든 평가 조건 · 합성 데이터',fontweight='bold')
    fig.savefig(out/'all-conditions.png',dpi=170);plt.close(fig)
    lines=['합성 데이터 평가 결과 — 실제 참여자 결과와 별도',f'조건별 {metadata["n_per_condition"]}개 · seed {metadata["seed"]}',
           '동일 5회·3축·likelihood·prior·추정기 / 다음 비교 선택 정책만 다름',
           '조건 | 적응형 5회 NMAE | 고정 5회 NMAE | 짝 차이 [95% 합성 CI]']
    for sid,s in summaries.items():
        a=s['policies']['adaptive']['mean_nmae'][5];f=s['policies']['fixed']['mean_nmae'][5];lo,hi=s['paired_difference_ci95']
        lines.append(f'{LABELS[sid]} | {a:.4f} | {f:.4f} | {a-f:+.4f} [{lo:+.4f}, {hi:+.4f}]')
    lines+=['','해석: 주어진 모델에서의 설정값 오차이며, 편안함·SUS·의료 효과 수치가 아님',
            '5회 예산 이후에도 오차와 불확실성이 남으므로 ‘5회 수렴 보장’으로 표현하지 않음',
            'posterior 포함률은 simulation-results.json에서 확인; 실제 사람에게 보장되는 확률이 아님']
    (out/'RESULTS.txt').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))

if __name__=='__main__':main()
