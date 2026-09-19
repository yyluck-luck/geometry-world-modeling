"""Plot only sealed existing S28 JSON/JSONL; no sensor/image/NPZ/model reads."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, math, csv, sys, time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT/'results/S28_gradient_scale_control'
ARMS = ('original','gradient_only')
def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def main():
    assert not (HERE/'plot_receipt.json').exists(), 'Preserve plotting attempts'
    start=utc();tick=time.perf_counter()
    inputs=[BASE/a/f for a in ARMS for f in ('receipt.json','gradient_depth_trace.jsonl')]+[BASE/'scoring'/f for f in ('receipt.json','metrics.json')]
    identities={str(p):sha(p) for p in inputs};source_sha=sha(Path(__file__))
    write(HERE/'plot_attempt.json',dict(started_utc=start,command=[sys.executable,str(Path(__file__))],source_sha256=source_sha,inputs=identities))
    receipts={a:json.loads((BASE/a/'receipt.json').read_text()) for a in ARMS}
    score_receipt=json.loads((BASE/'scoring/receipt.json').read_text())
    metrics=json.loads((BASE/'scoring/metrics.json').read_text())
    assert score_receipt['status']=='PASS'
    assert sha(BASE/'scoring/metrics.json')==score_receipt['outputs']['metrics.json']
    traces={a:[json.loads(l) for l in (BASE/a/'gradient_depth_trace.jsonl').read_text().splitlines()] for a in ARMS}
    contract=score_receipt['s28_contract_sha256']
    plotted={}
    for a in ARMS:
        r=receipts[a];t=traces[a]
        assert r['status']=='PASS' and r['iterations']==r['adam_steps']==400
        assert r['s28_contract_sha256']==metrics['s28_contract_sha256']==contract
        assert sha(BASE/a/'receipt.json')==score_receipt['input_sha256_before_after'][str(BASE/a/'receipt.json')]
        assert sha(BASE/a/'gradient_depth_trace.jsonl')==r['outputs']['gradient_depth_trace.jsonl']
        assert [q['iteration'] for q in t]==list(range(400))
        assert [q['actual_adam_steps'] for q in t]==list(range(1,401))
        losses=[q['loss_before_step'] for q in t]+[r['observer']['postfinal_objective']]
        assert all(math.isfinite(v) and v>0 for v in losses)
        ratios=[]
        for i in range(4):
            for q in t:
                assert [v['index'] for v in q['statistics_before_step']['frames']]==list(range(4))
                assert [v['index'] for v in q['statistics_after_step']['frames']]==list(range(4))
            v=[t[0]['statistics_before_step']['frames'][i]['depth_initial_ratio_mean']]+[q['statistics_after_step']['frames'][i]['depth_initial_ratio_mean'] for q in t]
            assert all(math.isfinite(x) and x>0 for x in v)
            if a=='original':assert all(x==1.0 for x in v)
            ratios.append(v)
        rows=[q for q in metrics['per_frame'] if q['mode']==a]
        assert [q['index'] for q in rows]==list(range(4))
        absrel=[q['absrel']*100 for q in rows]+[metrics['primary_common4'][a]['absrel']*100]
        assert all(math.isfinite(v) for v in absrel)
        plotted[a]=dict(completed_steps=list(range(401)),objective=losses,
                       objective_source='indices 0..399: saved pre-next-update values; 400: saved postfinal receipt value',
                       mean_pixelwise_depth_ratio=ratios,
                       ratio_definition='mean over all 384x512 pixels of depth_t(pixel)/depth_initial(pixel), separately for each frame; NOT ratio of frame means',
                       absrel_percent_final_frames_0_1_2_3_equal_frame_mean=absrel)
    write(HERE/'plotted_data.json',plotted)
    with (HERE/'plot_data_long.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['arm','completed_steps','original_objective','objective_position','frame','mean_pixelwise_depth_to_initial_ratio'])
        for a in ARMS:
            for step in range(401):
                for frame in range(4):w.writerow([a,step,plotted[a]['objective'][step],'postfinal' if step==400 else 'pre_next_step',frame,plotted[a]['mean_pixelwise_depth_ratio'][frame][step]])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':8.2,'axes.labelsize':8.6,'axes.titlesize':9,
        'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'pdf.fonttype':42,'ps.fonttype':42,
        'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.6,
        'lines.linewidth':1.35,'savefig.dpi':300,'path.simplify':False})
    fig,axes=plt.subplots(1,3,figsize=(7.5,3.2),gridspec_kw={'width_ratios':[1,1,1.15]})
    fig.subplots_adjust(left=.082,right=.985,bottom=.20,top=.86,wspace=.40)
    blue='#0072B2';orange='#D55E00';styles=['-','--',':','-.'];markers=['o','s','^','D']
    ax=axes[0]
    for a,label,color,style,marker in [('original','Original',blue,'--','o'),('gradient_only','Gradient-only repair',orange,'-','s')]:
        vals=plotted[a]['objective'];ax.plot(range(400),vals[:400],color=color,linestyle=style,marker=marker,markersize=3,markevery=[0,100,200,300],label=label)
        ax.plot([399,400],vals[399:],color=color,linestyle=style)
        ax.plot(400,vals[400],marker='D',color=color,markersize=4)
        ax.annotate(f'{vals[-1]:.5f}',(400,vals[-1]),xytext=(-5,7),textcoords='offset points',ha='right',color=color,fontsize=8)
    ax.set_yscale('log');ax.set_ylim(.003,2);ax.set_xlim(0,410);ax.set_xticks([0,200,400])
    ax.set_xlabel('Completed Adam steps');ax.set_ylabel('Original objective (log scale)')
    ax.set_title('(a) Optimization objective',loc='left',pad=11)
    ax.legend(loc='upper right',frameon=False,handlelength=2.1,borderaxespad=.25)
    ax.grid(axis='y',which='major',color='#DADADA',linewidth=.5)
    ax=axes[1]
    # All four original curves are deliberately retained; they overlap exactly.
    for i in range(4):
        ax.plot(range(401),plotted['original']['mean_pixelwise_depth_ratio'][i],color=blue,linestyle='--',marker=markers[i],markevery=[55+80*i],markersize=3,zorder=3)
    ax.text(18,1.022,'Original F0–F3: 1.0',color=blue,fontsize=8)
    for i in range(4):
        ax.plot(range(401),plotted['gradient_only']['mean_pixelwise_depth_ratio'][i],color=orange,linestyle=styles[i],marker=markers[i],markevery=[40+12*i,140+12*i,240+12*i,340+12*i],markersize=3,label=f'F{i}')
    ax.set_title('(b) Depth vs. initialization',loc='left',pad=11)
    ax.set_xlabel('Completed Adam steps');ax.set_ylabel(r'Mean pixelwise ratio $d_t / d_0$')
    ax.set_xlim(0,410);ax.set_xticks([0,200,400]);ax.set_ylim(.60,1.10);ax.set_yticks([.6,.8,1.0])
    ax.legend(loc='lower left',ncol=2,title='Repair frames',title_fontsize=8,frameon=False,columnspacing=1.0,handlelength=2.0,borderaxespad=.25)
    ax.grid(axis='y',color='#DADADA',linewidth=.5)
    ax=axes[2]
    ys=[4,3,2,1,-.2]
    for i,y in enumerate(ys):
        va=plotted['original']['absrel_percent_final_frames_0_1_2_3_equal_frame_mean'][i]
        vb=plotted['gradient_only']['absrel_percent_final_frames_0_1_2_3_equal_frame_mean'][i]
        ax.plot([va,vb],[y,y],color='#BBBBBB',linewidth=.8,zorder=1)
        ax.plot(va,y,'o',color=blue,markersize=4.4 if i<4 else 5.2)
        ax.plot(vb,y,'s',color=orange,markersize=4.4 if i<4 else 5.2)
        for v,color in [(va,blue),(vb,orange)]:ax.text(v,y+.22,f'{v:.2f}',color=color,ha='center',va='bottom',fontsize=8)
    ax.axhline(.35,color='#C7C7C7',linewidth=.6,linestyle=':')
    ax.set_ylim(-.7,4.75);ax.set_xlim(75,95);ax.set_xticks([75,85,95])
    ax.set_yticks(ys,['F0','F1','F2','F3','Mean']);ax.tick_params(axis='y',length=0)
    ax.set_xlabel('Final AbsRel (%) · lower is better');ax.set_ylabel('Frame / equal-frame mean')
    ax.set_title('(c) Final sensor-depth error',loc='left',pad=11)
    ax.grid(axis='x',color='#E2E2E2',linewidth=.5)
    fig.text(.5,.042,'S28 · Four previously seen frames · Matched initialization · 400 steps per arm · No scale fitting',ha='center',fontsize=8)
    fig.canvas.draw()
    # Full vector originals plus display-only PNG preview. No rasterized data artists.
    for ext in ['pdf','svg','png']:fig.savefig(HERE/f's28_gradient_control.{ext}',metadata={'Creator':'S28 saved-log plotting only'} if ext=='pdf' else None)
    font_sizes=sorted({float(t.get_fontsize()) for t in fig.findobj(matplotlib.text.Text) if t.get_text()})
    plt.close(fig)
    assert all(sha(Path(q))==v for q,v in identities.items()) and sha(Path(__file__))==source_sha
    outputs={q.name:sha(q) for q in HERE.iterdir() if q.is_file() and q.name not in ('plot_receipt.json','plot_attempt.json')}
    write(HERE/'plot_receipt.json',dict(status='PASS_PLOT_GENERATION_PENDING_VISUAL_QA',started_utc=start,completed_utc=utc(),wall_seconds=time.perf_counter()-tick,
        command=[sys.executable,str(Path(__file__))],source_sha256=source_sha,input_sha256_before_after=identities,outputs=outputs,
        inputs_unchanged=True,s28_contract_sha256=contract,matplotlib_version=matplotlib.__version__,canvas_inches=[7.5,3.2],minimum_font_pt=min(font_sizes),
        source_rows_per_arm=400,objective_points_per_arm=401,depth_curves_per_arm=4,depth_points_per_curve=401,scored_rows_reused=8,group_means_reused=2,
        sensor_gt_reads=0,NPZ_reads=0,new_model_forwards=0,new_GA_steps=0,new_sensor_score_runs=0,
        scope='Existing sealed log and metric visualization; not an independent numeric experiment audit. Raw depth metric values reused, not recomputed.'))
    print(json.dumps({'status':'PLOT_GENERATED','files':['s28_gradient_control.pdf','s28_gradient_control.svg','s28_gradient_control.png'],'minimum_font_pt':min(font_sizes)},indent=2))

if __name__=='__main__':main()
