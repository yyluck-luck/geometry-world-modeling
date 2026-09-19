#!/usr/bin/env python3
"""Describe all frozen S7 outcomes without selecting/tuning experiments."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/'results/S7_event_replay'
OUT = ROOT/'results/S7_analysis'
font = FontProperties(fname='/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
plt.rcParams.update({'font.family': font.get_name(), 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False, 'svg.fonttype': 'none'})


def read(p): return json.loads(p.read_text())
def mean(values): return float(np.mean(values))


def effect(rows, a, b, ra='official', rb='official'):
    pairs = [(r['readouts'][a][ra], r['readouts'][b][rb]) for r in rows]
    changes = [set(x['selected']) != set(y['selected']) for x,y in pairs]
    delta = [100*(y['support']-x['support']) for x,y in pairs]
    return dict(n=len(rows), changed=sum(changes), order_changed=sum(x['selected'] != y['selected'] for x,y in pairs),
                mean_delta_pp=mean(delta), min_delta_pp=min(delta), max_delta_pp=max(delta),
                positive=sum(d>1e-12 for d in delta), negative=sum(d< -1e-12 for d in delta),
                zero=sum(abs(d)<=1e-12 for d in delta), delta_pp=delta)


def run():
    meta = read(RAW/'run_metadata.json')
    if meta['status'] != 'completed': raise ValueError('S7 not complete')
    rows = read(RAW/'records.json')
    OUT.mkdir(exist_ok=True)
    groups = {}
    labels = ('A0P0','A0P1','A1P0','A1P1')
    readouts = ('official','candidate_no_nms','all20_nms','all20_no_nms')
    for split in ('development','test'):
        for stride in (8,12):
            selected = [r for r in rows if r['split']==split and r['stride']==stride]
            if not selected: raise ValueError('Expected frozen split is missing: '+split)
            g = dict(n=len(selected), support_percent={}, effects={},
                     common_four_coverage_percent=mean([100*r['common_four_pixels']/r['valid_pixels'] for r in selected]),
                     common_four_pixel_range=[min(r['common_four_pixels'] for r in selected),max(r['common_four_pixels'] for r in selected)],
                     geometry={}, all20_percent=mean([100*r['all20_support'] for r in selected]))
            for a in labels:
                g['support_percent'][a] = {rule: mean([100*r['readouts'][a][rule]['support'] for r in selected]) for rule in readouts}
                geo = [r['geometry'][a] for r in selected]
                g['geometry'][a] = dict(coverage_percent=mean([100*x['coverage'] for x in geo]),
                    common_four_mae_mm=mean([x['common_four']['mae_mm'] for x in geo]) if all(x['common_four']['n'] for x in geo) else None,
                    common_four_median_mm=mean([x['common_four']['median_abs_mm'] for x in geo]) if all(x['common_four']['n'] for x in geo) else None)
            for name,a,b in [('position_A0','A0P0','A0P1'),('position_A1','A1P0','A1P1'),
                             ('trajectory_P0','A0P0','A1P0'),('trajectory_P1','A0P1','A1P1'),
                             ('diagonal_total','A0P0','A1P1')]:
                g['effects'][name] = effect(selected,a,b)
            g['interaction_pp'] = g['effects']['position_A1']['mean_delta_pp']-g['effects']['position_A0']['mean_delta_pp']
            for a in labels:
                g['effects'][f'remove_nms_{a}'] = effect(selected,a,a,'official','candidate_no_nms')
                g['effects'][f'expand_pool_{a}'] = effect(selected,a,a,'official','all20_nms')
            groups[f'{split}_stride{stride}'] = g
    summary = dict(created_utc=datetime.now(timezone.utc).isoformat(),
        source_records_sha256=hashlib.sha256((RAW/'records.json').read_bytes()).hexdigest(), groups=groups)
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    with (OUT/'all_query_readouts.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['block','split','stride','query','map','readout','selected_ids','support_percent'])
        for r in rows:
            for a in labels:
                for rule in readouts:
                    v=r['readouts'][a][rule]
                    writer.writerow([r['block'],r['split'],r['stride'],r['frame'],a,rule,' '.join(map(str,v['selected'])),100*v['support']])
    fig,axes=plt.subplots(1,2,figsize=(12,4.8),sharey=True)
    colors=['#566675','#368a9c','#d17b41','#86579b']
    for ax,stride in zip(axes,(8,12)):
        g=groups[f'test_stride{stride}']; x=np.arange(4)
        for i,(rule,title) in enumerate(zip(readouts,('原候选＋NMS','原候选，无NMS','全20图＋NMS','全20图，无NMS'))):
            ax.bar(x+(i-1.5)*.19,[g['support_percent'][a][rule] for a in labels],width=.18,color=colors[i],label=title)
        ax.set(xticks=x,xticklabels=labels,ylim=(0,100),title=f'采样步长 {stride} · 同一8张测试查询',ylabel='参考支持（%）')
        ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    handles,names=axes[0].get_legend_handles_labels();fig.legend(handles,names,ncol=4,loc='lower center',frameon=False)
    fig.suptitle('位置、关联轨迹和选图规则：同预算比较')
    fig.subplots_adjust(bottom=.2,top=.87,wspace=.12)
    for ext in ('png','svg'):fig.savefig(OUT/f'four_map_readouts.{ext}',dpi=180)
    plt.close(fig)
    names=['position_A0','position_A1','trajectory_P0','trajectory_P1','diagonal_total']
    display=['固定A0：改位置','固定A1：改位置','固定P0：改轨迹','固定P1：改轨迹','原两臂总变化']
    data=[]
    for stride in (8,12):data.append(np.array([groups[f'test_stride{stride}']['effects'][n]['delta_pp'] for n in names]))
    maximum=max(float(np.abs(d).max()) for d in data) or 1.
    fig,axes=plt.subplots(2,1,figsize=(10.5,7.2))
    for ax,stride,d in zip(axes,(8,12),data):
        im=ax.imshow(d,cmap='RdBu',vmin=-maximum,vmax=maximum,aspect='auto')
        ax.set(yticks=np.arange(5),yticklabels=display,xticks=np.arange(8),
               xticklabels=[f'B{b}/Q{q}' for b in (1,2) for q in range(20,24)],title=f'采样步长 {stride} · 支持变化（百分点）')
        for iy in range(5):
            for ix in range(8):ax.text(ix,iy,f'{d[iy,ix]:+.2f}',ha='center',va='center',fontsize=10,color='white' if abs(d[iy,ix])>maximum*.5 else '#222')
    fig.subplots_adjust(left=.2,right=.87,hspace=.4,top=.94,bottom=.07)
    fig.colorbar(im,ax=axes,fraction=.025,pad=.04,label='正数为后者支持较高；不是视频质量')
    for ext in ('png','svg'):fig.savefig(OUT/f'paired_mechanism_effects.{ext}',dpi=180)
    plt.close(fig)
    (OUT/'captions.md').write_text('图1：四地图×四种读出的同预算支持，均为同一8测试查询均值。纵轴从0开始。A=关联轨迹，P=最终位置规则；跨A同时改变点数/分区/出生属性和来源。\n\n图2：全部8测试查询逐项差值，未挑例。两档密度使用同一色标；改变ID但支持相同的情况需与CSV/summary中的changed字段合读。所有格子属于同一环境，不能作为独立样本进行显著性检验。\n')
    print(json.dumps(groups,indent=2))


if __name__=='__main__':run()
