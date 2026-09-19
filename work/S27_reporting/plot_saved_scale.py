#!/usr/bin/env python3
"""Render one S27 descriptive figure from completed JSON/CSV; no metric recomputation."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
BASE=ROOT/'results/S27_saved_scale_diagnostic'
NAME='s27_raw_self_vs_ga_absrel'
CONTRACT=ROOT/'work/S27_saved_scale_preparation/contract.json'
FONT=Path('/System/Library/Fonts/STHeiti Light.ttc')
GROUPS=[('common_old','old4','共同旧4帧\n原 CUT · 帧0–3'),
        ('cut3r','new4','CUT3R 新4帧\n帧4–7'),
        ('ttt3r','new4','TTT3R 新4帧\n帧4–7'),
        ('filt3r','new4','FILT3R 新4帧\n帧4–7')]
STAGES=('raw_self_z','ga_depth_z')


def utc(): return datetime.now(timezone.utc).isoformat()


def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    started=utc()
    for ext in ('png','pdf','svg'):
        assert not (OUT/f'{NAME}.{ext}').exists(),'Do not overwrite prior figure'
    assert not (OUT/'receipt.json').exists(),'Do not overwrite prior receipt'
    paths=[BASE/'receipt.json',BASE/'summary.json',BASE/'per_frame.csv',CONTRACT,Path(__file__).resolve(),FONT]
    inputs={str(p):sha(p) for p in paths}
    parent=json.loads((BASE/'receipt.json').read_text())
    assert parent['status']=='PASS' and parent['metric_rows']==56 and parent['aggregate_rows']==20
    assert inputs[str(CONTRACT)]==parent['contract_sha256']
    for name in ('summary.json','per_frame.csv'):
        assert inputs[str(BASE/name)]==parent['outputs'][name]
    summary=json.loads((BASE/'summary.json').read_text())
    rows=list(csv.DictReader((BASE/'per_frame.csv').open()))
    assert len(rows)==56 and len(summary['aggregates'])==20
    all_keys={(r['mode'],r['stage'],int(r['index'])) for r in rows}
    expected={(m,s,i) for m,n in [('common_old',4),('cut3r',8),('ttt3r',8),('filt3r',8)] for s in STAGES for i in range(n)}
    assert all_keys==expected and len(all_keys)==len(rows),'All parent rows must be present once'
    plotted=[]
    for mode,group,label in GROUPS:
        indices=list(range(4)) if group=='old4' else list(range(4,8))
        for stage in STAGES:
            agg=[a for a in summary['aggregates'] if (a['mode'],a['group'],a['stage'])==(mode,group,stage)]
            assert len(agg)==1
            a=agg[0]
            assert a['frame_indices']==indices and a['frame_count']==a['absrel_defined_frames']==4
            subset=[r for r in rows if r['mode']==mode and r['stage']==stage and int(r['index']) in indices]
            assert [int(r['index']) for r in subset]==indices
            assert all(r['metric_status']=='DEFINED' and r['absrel']!='' and r['scale_applied']=='False' for r in subset)
            values=[100*float(r['absrel']) for r in subset]
            average=100*a['absrel']  # Use existing aggregate; do not recompute scientific means.
            assert all(math.isfinite(x) and x>=0 for x in values+[average])
            plotted.append(dict(mode=mode,group=group,stage=stage,indices=indices,
                                displayed_percent=average,individual_percent=values,
                                gt_valid_pixel_sum_descriptive=a['gt_valid_pixel_sum_descriptive']))
    sys.path.append(str(ROOT/'work/S17C_environment/site-packages'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import fontManager,FontProperties
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    fontManager.addfont(str(FONT)); family=FontProperties(fname=str(FONT)).get_name()
    plt.rcParams.update({'font.family':family,'font.size':11,'axes.unicode_minus':False,
        'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'path',
        'text.color':'#252A30','axes.labelcolor':'#252A30','xtick.color':'#252A30','ytick.color':'#252A30'})
    fig=plt.figure(figsize=(9,6.4),facecolor='white')
    ax=fig.add_axes([.105,.34,.86,.47])
    positions=[0,1.35,2.45,3.55]
    offsets=(-.18,.18); jitter=(-.072,-.024,.024,.072)
    colors=('#0072B2','#D55E00')
    displayed=[]
    for g,(mode,group,_) in enumerate(GROUPS):
        for k,stage in enumerate(STAGES):
            d=next(r for r in plotted if (r['mode'],r['stage'])==(mode,stage))
            x=positions[g]+offsets[k]; h=d['displayed_percent']; c=colors[k]
            ax.bar(x,h,width=.30,facecolor='white' if k==0 else c,edgecolor=c,linewidth=1.7,zorder=2)
            for dx,y in zip(jitter,d['individual_percent']):
                ax.plot(x+dx,y,marker='s' if k==0 else 'o',ms=3.7,markeredgewidth=.8,
                        markerfacecolor='white' if k==0 else '#24282D',markeredgecolor='#24282D',ls='none',zorder=4)
            ax.text(x,max(d['individual_percent']+[h])+2.3,f'{h:.2f}',ha='center',va='bottom',fontsize=12,color=c)
            displayed+=d['individual_percent']+[h]
    maximum=max(displayed)
    ymax=20*math.ceil((maximum+12)/20)
    ax.set_ylim(0,ymax); ax.set_xlim(-.68,4.18)
    ax.set_yticks(list(range(0,int(ymax)+1,20)))
    ax.set_ylabel('平均相对深度误差 AbsRel（%，越低越好）',fontsize=12,labelpad=10)
    ax.set_xticks(positions,[g[2] for g in GROUPS],fontsize=11.5)
    ax.tick_params(axis='x',length=0,pad=11)
    ax.grid(axis='y',color='#D7DCE1',linewidth=.6,alpha=.65,zorder=0)
    ax.axvline(.68,color='#ADB5BC',linewidth=.8,ls=(0,(3,4)),zorder=1)
    handles=[Patch(facecolor='white',edgecolor=colors[0],linewidth=1.7,label='Raw self：逐帧自身深度'),
             Patch(facecolor=colors[1],edgecolor=colors[1],label='原 GA：保存的深度输出'),
             Line2D([],[],color='#24282D',marker='o',ms=4,ls='none',label='全部单帧值')]
    ax.legend(handles=handles,loc='lower left',bbox_to_anchor=(-.015,1.025),ncol=3,frameon=False,
              fontsize=11,handlelength=1.5,columnspacing=1.25)
    fig.text(.065,.955,'共同旧地图已经出现明显深度误差',fontsize=18,weight='bold',va='top')
    fig.text(.065,.902,'TUM fr2_desk · 已见8帧 / 0.236秒 · 保存量事后诊断',fontsize=12,color='#59636C',va='top')
    fig.text(.065,.233,'柱为4帧等权均值，点包含该组全部4帧；点不是多次独立运行的置信区间。',fontsize=11,va='top')
    fig.text(.065,.190,'Raw self 不是 GA 逐帧相同输入：GA 消费第0帧 self 与其余帧 other 头。',fontsize=11,va='top')
    fig.text(.065,.147,'三路8帧 GA 共用同一旧4帧深度；所有指标未做传感器尺度拟合或置信度筛选。',fontsize=11,va='top')
    fig.text(.065,.104,'这张图用于定位失败，不证明因果、创新改进或视频生成效果。GA = 全局几何对齐。',fontsize=11,va='top')
    assert all(0<=v<=ymax for v in displayed)
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer(); canvas=fig.bbox
    clipped_text=[]
    for text in fig.findobj(matplotlib.text.Text):
        if text.get_visible() and text.get_text():
            b=text.get_window_extent(renderer)
            if b.x0<-.5 or b.y0<-.5 or b.x1>canvas.x1+.5 or b.y1>canvas.y1+.5:
                clipped_text.append(text.get_text())
    assert not clipped_text,repr(clipped_text)
    for ext in ('png','pdf','svg'):
        fig.savefig(OUT/f'{NAME}.{ext}',dpi=200,facecolor='white')
    plt.close(fig)
    assert all(sha(p)==s for p,s in inputs.items()),'Source table changed during rendering'
    skill=Path('/Users/rocket/.codex/skills/figure-designer')
    receipt=dict(status='RENDERED_VISUAL_QA_PENDING',started_utc=started,completed_utc=utc(),
        source='Completed S27 JSON/CSV only; no raw predictions, sensor images, model, GA or scoring executed.',
        input_identities_before_after=inputs,inputs_unchanged=True,source_all_metric_rows=56,
        plotted_groups='All common old4 and all three methods new4; method old4 duplicates are outside this requested figure.',
        plotted_aggregate_count=8,plotted_frame_values=32,plotted_values=plotted,
        scientific_metric_recomputations=0,percentage_display_conversion=True,model_runs=0,ga_runs=0,sensor_depth_reads=0,
        axis_audit=dict(ymin=0,ymax=ymax,max_displayed_value=maximum,clipped_data_points=0,clipped_text=clipped_text),
        design=dict(type='experimental-results supporting failure diagnostic',paradigm='grouped bars plus all frame points',
            rationale='Compare two saved quantities across four fixed groups, with no temporal interpolation or inferred uncertainty.',
            dimensions_inches=[9,6.4],minimum_font_pt=11,minimum_insertion_width_for_8pt=9*8/11,
            palette='Okabe-Ito blue/vermillion',dual_encoding='raw unfilled bar/square; GA filled bar/circle',
            actual_font_file=str(FONT),vector_exports=['pdf','svg'],svg_fonts='paths for portable Chinese glyphs',
            method_claim='Four-frame exploratory failure localization only, not an improvement or causal effect.'),
        skill_identities={str(p):sha(p) for p in [skill/'SKILL.md',skill/'references/experimental-results.md',
                          skill/'references/design-rules.md',skill/'references/tools.md']},
        integrity_gate=dict(figure_type='PASS',concrete_layout='PASS',real_labels='PASS',tool_match='PASS',
            universal_rules='PENDING_VISUAL_INSPECTION',intro_running_example='NOT_APPLICABLE_SUPPORTING_RESULT',chart_type='PASS'),
        visual_qa='PENDING actual view_image before delivery',
        outputs={f'{NAME}.{ext}':sha(OUT/f'{NAME}.{ext}') for ext in ('png','pdf','svg')})
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({'status':receipt['status'],'png':str(OUT/f'{NAME}.png'),'axis':receipt['axis_audit']},ensure_ascii=False))


if __name__=='__main__': main()
