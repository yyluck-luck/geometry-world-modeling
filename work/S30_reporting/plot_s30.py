"""Render sealed S30 JSON/JSONL only. No NPZ, sensor, model or optimizer access."""
from pathlib import Path
from datetime import datetime,timezone
import csv
import hashlib
import json
import math
import os
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/'results/S30_scale_optimization'
ARMS=('C2t','C2a')
os.environ['MPLCONFIGDIR']=str(HERE/'.mplconfig')
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,value):Path(p).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def main():
    assert not (HERE/'plot_receipt.json').exists(),'Preserve completed plot attempts'
    started=utc();tick=time.perf_counter()
    sources=[BASE/a/name for a in ARMS for name in ['receipt.json','gradient_depth_trace.jsonl']]
    sources += [BASE/'scoring/receipt.json',BASE/'scoring/metrics.json',ROOT/'work/S30_scale_optimization_preparation/contract.json']
    ids={str(p):sha(p) for p in sources}
    write(HERE/'input_seal.json',dict(utc=started,source_sha256=sha(__file__),inputs=ids,
        source_domain='Existing saved JSON/JSONL only; no NPZ, RGB, sensor or new scientific computation'))
    receipts={a:read(BASE/a/'receipt.json') for a in ARMS};score=read(BASE/'scoring/receipt.json');metrics=read(BASE/'scoring/metrics.json')
    assert score['status']=='PASS' and score['contract_sha256']==metrics['contract_sha256']
    assert sha(BASE/'scoring/metrics.json')==score['outputs']['metrics.json']
    assert sha(ROOT/'work/S30_scale_optimization_preparation/contract.json')==score['contract_sha256']
    rows=metrics['per_frame'];assert len(rows)==16
    expected=[(a,e,i) for a in ARMS for e in ['initial','final'] for i in range(4)]
    assert [(r['mode'],r['endpoint'],r['index']) for r in rows]==expected
    assert all(r['metric_status']=='DEFINED' and math.isfinite(r['absrel']) for r in rows)
    plotted=dict(endpoint_source='S30 saved scoring metrics; initial=S29 saved zero-step depth, final=S30 fixed step400 depth',
        mean_definition='Equal mean of four per-frame scores, not a pooled-pixel mean or independent repetitions',
        per_frame=rows,group_means=metrics['common4'],trajectories={})
    for arm in ARMS:
        r=receipts[arm];trace=[json.loads(v) for v in (BASE/arm/'gradient_depth_trace.jsonl').read_text().splitlines()]
        assert r['status']=='PASS' and r['iterations']==r['adam_steps']==400
        assert r['s30_contract_sha256']==score['contract_sha256']
        assert sha(BASE/arm/'receipt.json')==score['input_sha256'][str(BASE/arm/'receipt.json')]
        assert sha(BASE/arm/'gradient_depth_trace.jsonl')==r['outputs']['gradient_depth_trace.jsonl']
        assert [v['iteration'] for v in trace]==list(range(400))
        assert [v['actual_adam_steps'] for v in trace]==list(range(1,401))
        loss=[v['loss_before_step'] for v in trace]+[r['observer']['postfinal_objective']]
        assert len(loss)==401 and all(math.isfinite(v) and v>0 for v in loss)
        ratios=[]
        for frame in range(4):
            assert all([v['index'] for v in row[phase]['frames']]==list(range(4)) for row in trace for phase in ['statistics_before_step','statistics_after_step'])
            ratio=[trace[0]['statistics_before_step']['frames'][frame]['depth_initial_ratio_mean']]+[v['statistics_after_step']['frames'][frame]['depth_initial_ratio_mean'] for v in trace]
            assert len(ratio)==401 and all(math.isfinite(v) and v>0 for v in ratio)
            ratios.append(ratio)
        for endpoint in ['initial','final']:
            assert metrics['common4'][arm][endpoint]['absrel_defined_frames']==4
        plotted['trajectories'][arm]=dict(completed_steps=list(range(401)),original_objective=loss,
            objective_position='0..399 saved before next step; 400 saved postfinal objective',depth_ratio_per_frame=ratios,
            depth_ratio_definition='Saved mean over all 384x512 pixels of d_at_step(pixel)/d_at_initialization(pixel), separately for each frame; not ratio of frame means')
    write(HERE/'plotted_data.json',plotted)
    with (HERE/'endpoint_data.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['arm','endpoint','frame_or_mean','absrel_percent'])
        for arm,endpoint,index in expected:
            row=next(v for v in rows if (v['mode'],v['endpoint'],v['index'])==(arm,endpoint,index))
            w.writerow([arm,endpoint,index,row['absrel']*100])
        for arm in ARMS:
            for endpoint in ['initial','final']:w.writerow([arm,endpoint,'equal_frame_mean',metrics['common4'][arm][endpoint]['absrel']*100])
    with (HERE/'trajectory_data.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['arm','completed_steps','objective','objective_position','frame','mean_pixelwise_depth_ratio'])
        for arm in ARMS:
            data=plotted['trajectories'][arm]
            for step in range(401):
                for frame in range(4):w.writerow([arm,step,data['original_objective'][step],'postfinal' if step==400 else 'before_next_step',frame,data['depth_ratio_per_frame'][frame][step]])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':9,'axes.labelsize':9.5,'axes.titlesize':10,
        'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':8.5,'pdf.fonttype':42,'ps.fonttype':42,
        'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,
        'lines.linewidth':1.45,'savefig.dpi':300,'path.simplify':False})
    colors={'C2t':'#0072B2','C2a':'#D55E00'};markers=['o','s','^','D'];styles=['-','--',':','-.']
    figures=[]
    fig,ax=plt.subplots(figsize=(7.5,3.6));fig.subplots_adjust(left=.105,right=.98,bottom=.24,top=.82)
    positions=[0,1,2.6,3.6]
    groups=[(a,e) for a in ARMS for e in ['initial','final']]
    for x,(arm,endpoint) in zip(positions,groups):
        mean=metrics['common4'][arm][endpoint]['absrel']*100
        ax.bar(x,mean,width=.7,color=colors[arm],alpha=.18,edgecolor=colors[arm],linewidth=1)
        ax.hlines(mean,x-.35,x+.35,color=colors[arm],lw=1.6)
        vals=[v['absrel']*100 for v in rows if v['mode']==arm and v['endpoint']==endpoint]
        for i,(value,offset) in enumerate(zip(vals,[-.225,-.075,.075,.225])):
            ax.scatter(x+offset,value,marker=markers[i],s=27,facecolor='white',edgecolor='#202020',linewidth=.8,zorder=4)
        ax.text(x,max([mean,*vals])+3.5,f'{mean:.6f}%',ha='center',color=colors[arm],fontsize=9.3)
    ax.set_ylim(0,102);ax.set_xlim(-.65,4.25);ax.set_yticks([0,20,40,60,80,100])
    ax.set_ylabel('AbsRel (%) — lower is better')
    ax.set_xticks(positions,['Initial\n(saved S29)','After 400 steps\n(S30)','Initial\n(saved S29)','After 400 steps\n(S30)'])
    ax.grid(axis='y',color='#DADADA',lw=.5);ax.set_axisbelow(True)
    ax.text(.5,1.07,'C2t: fitted initial scale',transform=ax.get_xaxis_transform(),ha='center',color=colors['C2t'],fontsize=10)
    ax.text(3.1,1.07,'C2a: unit initial scale',transform=ax.get_xaxis_transform(),ha='center',color=colors['C2a'],fontsize=10)
    handles=[Line2D([0],[0],ls='',marker=markers[i],mfc='white',mec='#202020',ms=4,label=f'Frame {i}') for i in range(4)]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,.995),ncol=4,frameon=False,handletextpad=.35,columnspacing=1.3)
    fig.text(.105,.055,'Bars: 4 equal-frame means. Points: all 16 frame scores; no independent-run error bars.',fontsize=8.3)
    fig.text(.105,.012,'Known common4  |  Given GT cameras  |  Same raw-scale metric  |  No video measurement',fontsize=8.3,color='#454545')
    figures.append(('s30_endpoint_accuracy',fig))
    fig,axes=plt.subplots(1,2,figsize=(7.5,3.65));fig.subplots_adjust(left=.10,right=.98,bottom=.235,top=.84,wspace=.36)
    ax=axes[0];all_loss=[]
    for arm,line,marker in [('C2t','--','o'),('C2a','-','s')]:
        vals=plotted['trajectories'][arm]['original_objective'];all_loss+=vals
        ax.plot(range(401),vals,color=colors[arm],ls=line,marker=marker,markevery=[0,100,200,300],ms=3,label=arm)
        ax.scatter(400,vals[-1],marker='D',color=colors[arm],s=21,zorder=4)
        ax.annotate(f'{vals[-1]:.6f}',(400,vals[-1]),xytext=(-4,-12 if arm=='C2t' else 7),textcoords='offset points',ha='right',color=colors[arm],fontsize=8.3)
    lo=10**math.floor(math.log10(min(all_loss)));hi=10**math.ceil(math.log10(max(all_loss)))
    ax.set_yscale('log');ax.set_ylim(lo,hi);ax.set_xlim(0,410);ax.set_xticks([0,100,200,300,400])
    ax.set_xlabel('Completed Adam steps');ax.set_ylabel('Original objective (log scale)')
    ax.set_title('(a) Saved optimization objective',loc='left',pad=10);ax.legend(frameon=False,loc='upper right')
    ax.grid(axis='y',which='major',color='#DADADA',lw=.5)
    ax=axes[1]
    for arm in ARMS:
        for frame in range(4):
            values=plotted['trajectories'][arm]['depth_ratio_per_frame'][frame]
            ax.plot(range(401),values,color=colors[arm],ls=styles[frame],marker=markers[frame],ms=3,
                markevery=[45+12*frame,145+12*frame,245+12*frame,345+12*frame])
        terminal=plotted['trajectories'][arm]['depth_ratio_per_frame']
        low=min(v[-1] for v in terminal)
        ax.text(305,low-.018,arm,color=colors[arm],fontsize=8.7)
    ax.axhline(1,color='#666666',lw=.7,zorder=0)
    ax.set_xlim(0,410);ax.set_ylim(.5,1.035);ax.set_xticks([0,100,200,300,400]);ax.set_yticks([.5,.6,.7,.8,.9,1.])
    ax.set_xlabel('Completed Adam steps');ax.set_ylabel(r'Mean pixelwise ratio $d_k / d_0$')
    ax.set_title('(b) Every frame: depth / initial depth',loc='left',pad=10)
    frame_handles=[Line2D([0],[0],color='#353535',ls=styles[i],marker=markers[i],ms=3,label=f'F{i}') for i in range(4)]
    ax.legend(handles=frame_handles,ncol=2,frameon=False,loc='upper right',columnspacing=.7,handlelength=2.2)
    ax.grid(axis='y',color='#DADADA',lw=.5)
    fig.text(.10,.065,'All 800 saved iterations + 2 postfinal objective values (diamonds); no per-step GT scores.',fontsize=8.3)
    fig.text(.10,.018,'Depth: all 4 frames per arm, 401 points each; pixelwise ratios over all 384 × 512 pixels.',fontsize=8.3,color='#454545')
    figures.append(('s30_optimization_trajectories',fig))
    for name,fig in figures:
        for extension in ['png','pdf','svg']:fig.savefig(HERE/(name+'.'+extension),format=extension)
        plt.close(fig)
    assert all(sha(path)==h for path,h in ids.items()),'Bound input changed while rendering'
    outputs={p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.name not in ['plot_receipt.json','manifest.json']}
    write(HERE/'plot_receipt.json',dict(status='PASS_RENDERED_PENDING_VISUAL_QA',started_utc=started,completed_utc=utc(),
        wall_seconds=time.perf_counter()-tick,command=[sys.executable,str(Path(__file__).resolve())],python_version=sys.version,
        matplotlib_version=matplotlib.__version__,source_sha256=sha(__file__),inputs_sha256_before_after=ids,outputs=outputs,
        contract_sha256=score['contract_sha256'],minimum_font_pt=8.3,canvas_inches={'endpoints':[7.5,3.6],'trajectories':[7.5,3.65]},
        frame_endpoint_points=16,endpoint_means=4,saved_iteration_records=800,objective_points=802,
        depth_curves=8,points_per_depth_curve=401,GT_reads=0,NPZ_reads=0,new_model=0,new_optimization=0,new_GT_score=0,
        scope='Visualization of sealed saved values with schema/identity checks; not an independent numeric experiment audit'))


if __name__=='__main__':main()
