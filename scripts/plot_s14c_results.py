#!/usr/bin/env python3
"""Plot every S14C query from verified output without fitting or perturbation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'work/S14C_reporting/figures'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    verification = ROOT/'results/S14C_independent_verification/verification.json'
    rows_path = ROOT/'results/S14C_exploratory_association/joined_rows.json'
    stats_path = ROOT/'results/S14C_exploratory_association/associations.json'
    inputs = {str(p):sha(p) for p in [verification,rows_path,stats_path]}
    assert json.loads(verification.read_text())['status']=='PASS'
    rows = json.loads(rows_path.read_text())['rows']
    stats = json.loads(stats_path.read_text())['rows']
    OUTPUT.mkdir(exist_ok=False)
    plt.rcParams.update({'font.size':10,'axes.labelsize':10,'axes.titlesize':12,
                         'svg.fonttype':'none','pdf.fonttype':42})
    fig,axes = plt.subplots(1,2,figsize=(9,4.5),sharex=True,sharey=True)
    colors=['#0072B2','#E69F00','#009E73']
    markers=['o','s','^']
    plotted=[]
    for axis,scene in zip(axes,['S7','S8']):
        for block in range(3):
            subset=[r for r in rows if r['stage']==scene and r['block']==block
                    and r['disagreement_g_minus_p'] is not None]
            axis.scatter([r['disagreement_g_minus_p'] for r in subset],
                         [r['y_pose_minus_geometry_pp'] for r in subset],
                         s=58,color=colors[block],marker=markers[block],
                         edgecolors='white',linewidths=.65,label=f'Block {block}',zorder=3)
            plotted.extend([r['stage'],r['block'],r['query']] for r in subset)
        rho=next(r['rho'] for r in stats if r['stage']==scene and r['block'] is None
                 and r['metric']=='disagreement_g_minus_p')
        axis.set_title(f'{scene}  |  12 previously seen queries\nSpearman = {rho:+.4f}',pad=12)
        axis.axhline(0,color='#657080',lw=.8,zorder=1)
        axis.axvline(0,color='#657080',lw=.8,zorder=1)
        axis.grid(color='#e5e8eb',linewidth=.55)
        axis.set_axisbelow(True)
        axis.set_xlabel('Predicted disagreement difference (G - P)')
        axis.spines[['top','right']].set_visible(False)
    axes[0].set_ylabel('Support loss of G versus P (percentage points)')
    xs=[r['disagreement_g_minus_p'] for r in rows if r['disagreement_g_minus_p'] is not None]+[0]
    ys=[r['y_pose_minus_geometry_pp'] for r in rows]+[0]
    xspan=max(xs)-min(xs);yspan=max(ys)-min(ys)
    axes[0].set_xlim(min(xs)-max(xspan*.1,.01),max(xs)+max(xspan*.1,.01))
    axes[0].set_ylim(min(ys)-max(yspan*.1,.1),max(ys)+max(yspan*.1,.1))
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.10),ncol=3,frameon=False)
    fig.suptitle('The coarse disagreement proxy fails the two-scene sign check',fontsize=13,y=.98)
    fig.text(.5,.035,'24 related queries; repeated/overlapping points retained. No jitter, fitted line, or pooled correlation.',
             ha='center',fontsize=9,color='#394351')
    fig.subplots_adjust(left=.10,right=.98,bottom=.30,top=.78,wspace=.15)
    assert sorted(plotted)==sorted([r['stage'],r['block'],r['query']] for r in rows)
    for extension in ['svg','png']:
        fig.savefig(OUTPUT/f's14c_all_queries.{extension}',dpi=180,facecolor='white')
    plt.close(fig)
    assert all(sha(Path(p))==h for p,h in inputs.items())
    receipt=dict(completed_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(Path(__file__)),
                 input_sha256=inputs,plotted_query_ids=plotted,all_24_plotted=True,
                 geometric_or_statistical_recomputation=False,jitter=False,regression_fit=False,
                 shared_axes=True,matplotlib_version=matplotlib.__version__,
                 output_sha256={p.name:sha(p) for p in OUTPUT.iterdir()})
    (OUTPUT/'figure_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(OUTPUT/'s14c_all_queries.png')

if __name__=='__main__':
    main()
