#!/usr/bin/env python3
"""Describe frozen S6 outputs without tuning or rerunning the experiment."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
METHODS = ('first_write', 'frame_mean')
COLORS = ('#0072B2', '#D55E00', '#009E73', '#777777')


def mean(values):
    return float(np.mean(values))


def summarize(records, split, stride):
    rows = [r for r in records if r['split'] == split and r['stride'] == stride]
    return dict(split=split, stride=stride, actual_queries=len(rows),
        common_pixels_min=min(r['common_pixels'] for r in rows),
        common_pixels_max=max(r['common_pixels'] for r in rows),
        common_coverage_percent=mean([100*r['common_pixels']/r['valid_target_pixels'] for r in rows]),
        geometry={m:{k:mean([r['geometry'][m][k] for r in rows])
            for k in ('mae_mm','median_abs_mm','p90_abs_mm','within_30mm','coverage_of_valid_target')}
            for m in METHODS},
        retrieval={w:dict(changed_queries=sum(r['retrieval'][w]['selection_set_changed'] for r in rows),
            support_percent={m:mean([100*r['retrieval'][w][m]['support_coverage'] for r in rows]) for m in METHODS},
            delta_pp=mean([r['retrieval'][w]['coverage_delta_pp'] for r in rows])) for w in ('160','320')},
        controls_percent={m:mean([100*r['controls'][m]['support_coverage'] for r in rows]) for m in ('recent4','nearest_pose4')},
        all_history_percent=mean([100*r['all_history_support_coverage'] for r in rows]))


def dump_csv(path, rows):
    with path.open('w', newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)


def main(args):
    source=args.input/'records.json';records=json.loads(source.read_text())
    assert len(records)==24 and {(r['block'],r['stride'],r['frame']) for r in records}=={
        (b,s,q) for b in range(3) for s in (8,12) for q in range(20,24)}
    args.output.mkdir(parents=True,exist_ok=True)
    groups=[summarize(records,p,s) for p in ('development','test') for s in (8,12)]
    summary=dict(created_utc=datetime.now(timezone.utc).isoformat(),groups=groups,
        observations='12 distinct query frames from one TUM sequence; test subset has 8; repeated strides/widths are not independent samples',
        aggregate='Unweighted mean across query-level metrics, never a pooled median or pooled p90',
        records_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2))
    rows=[]
    for r in records:
        for w in ('160','320'):
            p=r['retrieval'][w]
            rows.append(dict(block=r['block'],split=r['split'],stride=r['stride'],frame=r['frame'],width=int(w),
                changed=p['selection_set_changed'],first_write_ids=' '.join(map(str,p['first_write']['selected'])),
                frame_mean_ids=' '.join(map(str,p['frame_mean']['selected'])),
                first_write_support_percent=100*p['first_write']['support_coverage'],
                frame_mean_support_percent=100*p['frame_mean']['support_coverage'],delta_pp=p['coverage_delta_pp'],
                recent4_percent=100*r['controls']['recent4']['support_coverage'],
                nearest_pose4_percent=100*r['controls']['nearest_pose4']['support_coverage'],
                all20_percent=100*r['all_history_support_coverage']))
    dump_csv(args.output/'query_retrieval.csv',rows)
    dump_csv(args.output/'query_geometry.csv',[dict(block=r['block'],split=r['split'],stride=r['stride'],frame=r['frame'],
        valid_target_pixels=r['valid_target_pixels'],common_pixels=r['common_pixels'],
        **{f'{m}_{k}':r['geometry'][m][k] for m in METHODS for k in
            ('mae_mm','median_abs_mm','p90_abs_mm','within_30mm','coverage_of_valid_target')}) for r in records])
    plt.rcParams.update({'font.size':10,'axes.titlesize':11,'axes.spines.top':False,'axes.spines.right':False,
        'svg.fonttype':'none','pdf.fonttype':42,'axes.labelsize':10})
    files=[]
    def save(fig,name):
        for ext in ('png','svg'):
            p=args.output/f'{name}.{ext}';fig.savefig(p,dpi=180,bbox_inches='tight');files.append(p.name)
        plt.close(fig)
    test=[g for g in groups if g['split']=='test']
    fig,axs=plt.subplots(1,2,figsize=(9,3.5),sharey=True)
    for ax,g in zip(axs,test):
        vals=[g['retrieval']['160']['support_percent'][m] for m in METHODS]+[
            g['controls_percent'][m] for m in ('nearest_pose4','recent4')]
        ax.bar(np.arange(4),vals,color=COLORS,edgecolor='black',linewidth=.6)
        for i,v in enumerate(vals):ax.text(i,v+1,f'{v:.2f}',ha='center',fontsize=9)
        ax.axhline(g['all_history_percent'],color='black',ls='--',lw=1,label=f"All 20: {g['all_history_percent']:.2f}%")
        ax.set_xticks(range(4),['First\nwrite','Frame\nmean','Nearest\npose 4','Recent\n4'])
        ax.set_ylim(0,108);ax.set_yticks(range(0,101,20));ax.set_title(f"Stride {g['stride']} · 8 test queries")
        ax.legend(loc='lower left',frameon=False,fontsize=9)
    axs[0].set_ylabel('Measured reference support (%)')
    fig.tight_layout();save(fig,'reference_support')
    fig,axs=plt.subplots(1,2,figsize=(9,3.5),sharey=True)
    for ax,stride in zip(axs,(8,12)):
        a=[r for r in records if r['split']=='test' and r['stride']==stride]
        for method,color,marker in zip(METHODS,COLORS,('o','s')):
            ax.plot(range(8),[r['retrieval']['160'][method]['support_coverage']*100 for r in a],
                color=color,marker=marker,ls='-' if method=='first_write' else '--',label=method.replace('_',' '))
        ax.plot(range(8),[r['controls']['nearest_pose4']['support_coverage']*100 for r in a],
            color=COLORS[2],marker='^',ls=':',label='nearest pose 4')
        ax.axvline(3.5,color='gray',lw=.6);ax.set_xticks(range(8),[f"B{r['block']}\n{r['frame']}" for r in a])
        ax.set_ylim(70,101);ax.set_title(f'Stride {stride} · per-query support')
        ax.legend(loc='lower right',fontsize=8,frameon=False)
    axs[0].set_ylabel('Measured reference support (%)\n(axis starts at 70%)')
    fig.tight_layout();save(fig,'paired_query_support')
    fig,axs=plt.subplots(1,3,figsize=(10,3.5))
    for ax,key,title,mult in zip(axs,('mae_mm','median_abs_mm','coverage_of_valid_target'),
            ('Common-pixel MAE (mm)','Mean query median (mm)','Own target coverage (%)'),(1,1,100)):
        for j,(m,c) in enumerate(zip(METHODS,COLORS)):
            vals=[g['geometry'][m][key]*mult for g in test]
            bars=ax.bar(np.arange(2)+(j-.5)*.32,vals,width=.32,color=c,edgecolor='black',linewidth=.5,label=m.replace('_',' '))
            ax.bar_label(bars,fmt='%.1f',padding=3,fontsize=9)
        ax.set_xticks((0,1),('Stride 8','Stride 12'));ax.set_title(title);ax.set_ylim(0,ax.get_ylim()[1]*1.18)
    axs[0].legend(frameon=False,fontsize=8,loc='upper left')
    fig.tight_layout();save(fig,'geometry_and_coverage')
    (args.output/'figure_manifest.json').write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(),
        files={f:hashlib.sha256((args.output/f).read_bytes()).hexdigest() for f in files},source_records_sha256=summary['records_sha256']),indent=2))
    print(json.dumps(dict(groups=len(groups),retrieval_rows=len(rows),figures=len(files)//2)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=ROOT/'results/S6_memory_bridge')
    p.add_argument('--output',type=Path,default=ROOT/'results/S6_memory_analysis')
    main(p.parse_args())
