#!/usr/bin/env python3
"""Render immutable completed S15B JSON scores; no model/data/image reads."""
from pathlib import Path
import json, hashlib, csv, math, datetime, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
START=datetime.datetime.now(datetime.timezone.utc).isoformat()
T0=time.monotonic()
METHODS=['never','all_new','half_blend','pool_new','split_new','matched_absolute_new','model_confidence']
LABELS=['Never','All new','Half blend','Pooled cost','Split agreement','Matched new cost','Model confidence']
TARGETS=[20,21,22,23]
READS=[]
def read(rel):
    p=ROOT/rel; b=p.read_bytes()
    READS.append({'path':rel,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'format':'json','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    return json.loads(b)
for rel in ['results/S15B_prefix_proposals/run_metadata.json','results/S15B_witness_costs/run_metadata.json','results/S15B_consumer_predictions/run_metadata.json','results/S15B_consumer_scores/run_metadata.json']:
    assert read(rel)['status'] in ('PASS','SUCCESS'), rel
iv1=read('results/S15B_prefix_independent/attempt_2/verification.json')
iv2=read('results/S15B_consumer_independent/verification.json')
assert iv1['status']==iv2['status']=='PASS'
scores=read('results/S15B_consumer_scores/scores.json')
desc=read('results/S15B_consumer_predictions/prediction_description.json')
assert desc['methods']==METHODS and desc['target_indices']==TARGETS
assert scores['independent_sequences']==1 and scores['exploratory_previously_seen_targets'] is True
rows=scores['per_target']; lookup={(r['method'],r['target_index']):r for r in rows}
assert len(rows)==len(lookup)==28
means=scores['equal_four_frame_means_and_auxiliary']
for m in METHODS:
    for mk, rk in [('delta1_all_gt','delta1_all_gt'),('coverage','coverage')]:
        calc=math.fsum(lookup[m,t][rk] for t in TARGETS)/4
        assert math.isclose(calc,means[m][mk],rel_tol=0,abs_tol=1e-14)
    assert math.isclose(math.fsum(lookup[m,t]['common']['mae_m'] for t in TARGETS)/4,means[m]['common_mae_m'],rel_tol=0,abs_tol=1e-14)
with (OUT/'plotted_values.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['method','target_or_equal_frame_mean','delta1_percent','coverage_percent','common_mae_cm','changed_source_pixels'])
    for m in METHODS:
        for t in TARGETS:
            r=lookup[m,t]; w.writerow([m,t,100*r['delta1_all_gt'],100*r['coverage'],100*r['common']['mae_m'],desc['changed_source_pixels'][m]])
        r=means[m];w.writerow([m,'equal_four_frame_mean',100*r['delta1_all_gt'],100*r['coverage'],100*r['common_mae_m'],desc['changed_source_pixels'][m]])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,'axes.titlesize':10,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':9,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
fig,axes=plt.subplots(1,2,figsize=(7.6,5.4),sharey=True)
fig.subplots_adjust(left=.23,right=.985,bottom=.165,top=.76,wspace=.20)
colors=['#0072B2','#D55E00','#009E73','#CC79A7']
markers=['o','s','^','v']
offsets=[-.26,-.13,0,.13]
for ai,ax in enumerate(axes):
    ax.set_axisbelow(True)
    ax.grid(axis='x',color='#e1e5e9',linewidth=.6)
    for i,m in enumerate(METHODS):
        if i%2==0: ax.axhspan(i-.40,i+.40,color='#f4f6f8',zorder=-1)
        for j,t in enumerate(TARGETS):
            r=lookup[m,t]
            val=100*(r['delta1_all_gt'] if ai==0 else r['common']['mae_m'])
            ax.scatter(val,i+offsets[j],s=20,marker=markers[j],color=colors[j],linewidth=.5,edgecolor=colors[j],zorder=3)
        mean=100*(means[m]['delta1_all_gt'] if ai==0 else means[m]['common_mae_m'])
        ax.scatter(mean,i+.27,s=24,marker='D',color='#151c26',zorder=4)
        ax.text(73.6 if ai==0 else 22.55,i+.27,f'{mean:.2f}',ha='right',va='center',fontsize=9,color='#151c26')
    ax.set_ylim(6.48,-.5)
    ax.spines[['top','right','left']].set_visible(False)
    ax.spines['bottom'].set_color('#84909c')
    ax.tick_params(axis='y',length=0,pad=10)
axes[0].set_yticks(range(7),LABELS)
axes[0].set_xlim(60,74);axes[0].set_xticks([60,64,68,72])
axes[1].set_xlim(8,23);axes[1].set_xticks([8,12,16,20])
axes[0].set_title('(a) Depth accuracy',loc='left',pad=9)
axes[1].set_title('(b) Error on shared pixels',loc='left',pad=9)
axes[0].set_xlabel(r'$\delta_1$ (%)  —  higher is better',labelpad=7)
axes[1].set_xlabel('Common MAE (cm)  —  lower is better',labelpad=7)
fig.suptitle('S15B | Seven methods, four previously seen targets',x=.035,y=.976,ha='left',fontsize=11,fontweight='bold')
fig.text(.035,.924,'TUM fr2_desk block 0; 12-frame CUT3R prefix; fixed sources 0 / 3 / 6 / 9.',fontsize=9)
handles=[Line2D([],[],color=c,marker=m,linestyle='none',markersize=5,label=f'Target {t}') for c,m,t in zip(colors,markers,TARGETS)]
handles.append(Line2D([],[],color='#151c26',marker='D',linestyle='none',markersize=5,label='Equal-frame mean'))
fig.legend(handles=handles,loc='upper left',bbox_to_anchor=(.028,.886),ncol=5,frameon=False,columnspacing=1.25,handletextpad=.45)
fig.text(.035,.060,'All 28 target scores shown; numbers label means. Points are observations, not confidence intervals.',fontsize=9)
fig.text(.035,.024,'Enlarged axes. Missing predictions fail δ₁; common MAE uses the seven-method valid intersection.',fontsize=9)
for ext in ['png','pdf','svg']:
    fig.savefig(OUT/f's15b_seven_method_comparison.{ext}',dpi=220,facecolor='white')
plt.close(fig)
receipt={'schema':'s15b-reporting-plot-run-v1','status':'PASS','started_utc':START,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-T0,'method_order':METHODS,'target_indices':TARGETS,'read_receipts':READS,'source_json_mean_checks':21,'actual_model_calls':0,'rgb_decodes':0,'gt_depth_decodes':0,'experiment_npz_decodes':0,'new_network_requests':0,'matplotlib_version':matplotlib.__version__,'figure_size_inches':[7.6,5.4],'minimum_font_pt':9,'confidence_intervals':False,'figure_design':'Two aligned horizontal categorical point panels, all four fixed target observations and separate equal-frame mean for each of seven methods. No connecting line implies independent time process. Enlarged explicitly labelled axes, no truncated bars.'}
(OUT/'plot_run.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['status','started_utc','completed_utc','elapsed_seconds','rgb_decodes','gt_depth_decodes','experiment_npz_decodes','actual_model_calls']},ensure_ascii=False))
