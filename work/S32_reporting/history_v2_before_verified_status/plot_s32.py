#!/usr/bin/env python3
"""Plot only sealed S32 JSON/CSV. No NPZ, sensor files, inference or scoring."""
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,json,math,sys
from plot_utils import PALETTE,MARKERS,FIGSIZE,configure
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
INPUT=ROOT/'results/S32_consumer_scoring'
WINDOWS=['fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2']
ENDS=['initial_0step','corrected_getter_400','global_rescaled_400']
LABELS=['Zero step','400 steps\n(getter fix)','400 + global\nrescaling']
MANIFEST=ROOT/'work/S32_scoring_preparation/manifest.json'
MANIFEST_SHA='091ab3c69fd62c50a57d3ce12f7b404abff370d8fb229381e103a2db4fc2e722'
RECEIPT_SHA='834627965eaa4198e42a8a00c43951949bf45a15bbdd0e28f871e63d98017b37'
METRICS_SHA='975ad404667a24032ca3c3c5bcfa61fc70dc1f38ef3dd14391df9c4dd2b0bbbf'
CSV_SHA='1743010707fdb9dc1cdd7b6801b51b8f5eb8c8d99fcb10f95b32b5d906ca700d'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def main():
    started=utc();assert not (HERE/'receipt.json').exists(),'No overwrite of finished figure'
    ids={str(MANIFEST):MANIFEST_SHA,str(INPUT/'receipt.json'):RECEIPT_SHA,
         str(INPUT/'metrics.json'):METRICS_SHA,str(INPUT/'per_frame.csv'):CSV_SHA}
    for p,h in ids.items():assert sha(p)==h,p
    r=read(INPUT/'receipt.json');m=read(INPUT/'metrics.json')
    assert r['status']=='PASS' and r['scoring_manifest_sha256']==MANIFEST_SHA==m['scoring_manifest_sha256']
    assert r['output_sha256']['metrics.json']==METRICS_SHA and r['output_sha256']['per_frame.csv']==CSV_SHA
    assert (m['prespecified_windows'],m['prespecified_groups'],m['prespecified_rows'],m['scored_rows'],m['unavailable_rows'])==(4,12,48,36,12)
    rows=m['per_frame'];csvrows=list(csv.DictReader((INPUT/'per_frame.csv').open()))
    keyed={(x['window_id'],x['endpoint'],x['index']):x for x in rows}
    csvkeyed={(x['window_id'],x['endpoint'],int(x['index'])):x for x in csvrows}
    expected={(w,e,i) for w in WINDOWS for e in ENDS for i in range(4)}
    assert len(keyed)==len(rows)==len(csvrows)==48 and set(keyed)==set(csvkeyed)==expected
    for key,x in keyed.items():
        y=csvkeyed[key];assert x['row_status']==y['row_status']
        assert (y['absrel']=='' and x['absrel'] is None) or (x['absrel'] is not None and float(y['absrel'])==x['absrel'])
    points=[];means=[]
    for wi,w in enumerate(WINDOWS):
        for ei,e in enumerate(ENDS):
            g=m['window_groups'][w][e];assert g['frame_count']==4 and g['frame_indices']==[0,1,2,3]
            means.append(dict(window_id=w,endpoint=e,absrel=g['absrel'],percent=None if g['absrel'] is None else g['absrel']*100,
                panel_index=wi,x=ei,aggregation=g['aggregation']))
            for i in range(4):
                x=keyed[w,e,i];val=x['absrel'];assert val is None or math.isfinite(val) and val>=0
                points.append(dict(window_id=w,endpoint=e,index=i,absrel=val,percent=None if val is None else val*100,
                    panel_index=wi,x=ei+[-.15,-.05,.05,.15][i],marker=MARKERS[ei],color=PALETTE[ei],
                    row_status=x['row_status'],missing_reason=x['missing_reason']))
    assert sum(x['percent'] is not None for x in points)==36 and sum(x['percent'] is not None for x in means)==9
    assert all(x['percent'] is None for x in points if x['window_id']=='fr2_desk_j1')
    summaries=[]
    for e in ENDS:
        total=m['endpoint_summaries'][e]['all_four_prespecified'];eligible=m['endpoint_summaries'][e]['three_preselected_pose_eligible']
        assert total['absrel'] is None and total['prespecified_window_count']==4
        assert eligible['prespecified_window_count']==3
        summaries.append(dict(endpoint=e,all_four_absrel=None,three_pose_eligible_absrel=eligible['absrel'],
            three_pose_eligible_percent=100*eligible['absrel'],purpose='descriptive secondary; never replaces four-window NA'))
    maximum=max(x['percent'] for x in points if x['percent'] is not None)
    assert maximum<50 # Full common 0–50% axis includes every observed point, no clipping or broken axes.
    write(HERE/'plotted_data.json',dict(status='RECORDED_MAIN_SCORE_INDEPENDENT_NUMERIC_REVIEW_PENDING',created_utc=utc(),
        source_sha256=ids,points=points,window_means=means,endpoint_summaries_imported=summaries,
        complete_design=dict(windows=4,endpoint_groups=12,frame_rows=48,observed_points=36,observed_means=9,NA_rows=12,NA_means=3),
        axes=dict(type='linear',y_label='AbsRel (%)',common_y_min=0,common_y_max=50,observed_max_percent=maximum),
        transformations=['Read saved per-frame/group AbsRel; convert fractions to percent by multiplying by100',
            'Fixed endpoint/frame x offsets solely to separate all four correlated observations; no random jitter',
            'Means are imported from sealed scoring JSON, not recomputed from sensor files'],
        missing='fr2_desk_j1 all3 endpoints×4frames NA: missing given camera association',
        limitations=['Given GT optical camera poses as common input','Already exposed scenes; approximately0.10s windows',
            'Correlated adjacent frames; no independent-frame/pixel significance, CI or repeat-run variance',
            'Three ordinary controls; no new algorithm or generated-video gain','Independent numerical review pending at figure creation']))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    configure(plt)
    fig,axes=plt.subplots(2,2,figsize=FIGSIZE,sharey=True)
    fig.subplots_adjust(left=.09,right=.985,bottom=.27,top=.905,hspace=.46,wspace=.20)
    starts={'fr2_desk_j1':'987–990','fr2_desk_j2':'1974–1977','fr1_xyz_j1':'264–267','fr1_xyz_j2':'529–532'}
    for wi,(ax,w) in enumerate(zip(axes.flat,WINDOWS)):
        ax.set_ylim(0,50);ax.set_xlim(-.45,2.45);ax.set_yticks(range(0,51,10));ax.grid(axis='y',color='#E4E6E8',lw=.55,zorder=0)
        ax.set_xticks(range(3),LABELS);ax.tick_params(axis='x',length=0,pad=6)
        ax.set_title(f"({chr(97+wi)}) {w}  |  RGB {starts[w]}",loc='left',pad=7)
        if wi%2==0:ax.set_ylabel('AbsRel (%) ↓')
        if w=='fr2_desk_j1':
            ax.text(1,30,'NA',ha='center',va='center',fontsize=20,color='#60666D')
            ax.text(1,19,'Missing given-camera association\nAll 3 endpoints unavailable\n4 frames retained in the design',ha='center',va='center',fontsize=9,color='#60666D',linespacing=1.4)
            continue
        for ei,e in enumerate(ENDS):
            group=[x for x in points if x['window_id']==w and x['endpoint']==e]
            mean=next(x['percent'] for x in means if x['window_id']==w and x['endpoint']==e)
            ax.bar(ei,mean,width=.46,color=PALETTE[ei],alpha=.12,linewidth=0,zorder=1)
            ax.plot([ei-.22,ei+.22],[mean,mean],color='#24282D',linewidth=1.5,zorder=2)
            ax.scatter([x['x'] for x in group],[x['percent'] for x in group],s=28,marker=MARKERS[ei],
                facecolor='white',edgecolor=PALETTE[ei],linewidth=1.25,zorder=3)
            label_y=max(mean,max(x['percent'] for x in group))+1.8
            ax.text(ei,label_y,f'{mean:.2f}',ha='center',va='bottom',fontsize=9,color='#24282D')
    fig.text(.09,.969,'Recorded main scores · independent numerical review PENDING',fontsize=9.5,color='#7B3F10',va='top')
    fig.text(.09,.178,'Points: frames 0–3 from left to right per endpoint.  Black line / number: four-frame mean.',fontsize=8.5)
    fig.text(.09,.141,'Four-window average: NA for all endpoints (missing window retained).  No significance tests or CIs.',fontsize=8.5)
    fig.text(.09,.104,'Given GT camera poses · previously used scenes · short windows (~0.10 s) · ordinary controls.',fontsize=8.5)
    fig.text(.09,.067,'Depth only; no innovation/video claim.  Rescaling uses predictions, with no GT fit.',fontsize=8.5)
    outputs={}
    for ext in ['png','pdf','svg']:
        p=HERE/f's32_window_absrel.{ext}';fig.savefig(p,format=ext);outputs[p.name]=sha(p)
    plt.close(fig)
    table=['| 汇总口径 | 零步 | 修 getter 的400步 | 400步+公共比例恢复 |','|---|---:|---:|---:|',
        '| 原4预定窗口等权均值 | NA | NA | NA |',
        '| 另附3预定pose可用窗等权描述均值 | '+' | '.join(f"{x['three_pose_eligible_percent']:.5f}%" for x in summaries)+' |']
    (HERE/'descriptive_summary.md').write_text('# 汇总口径（仅导入现有主评分）\n\n'+'\n'.join(table)+'\n\n三窗均值不能替代原四窗NA；不得按局部帧或像素当独立样本作显著性。该图制作时独立数值复核尚未完成。\n')
    for p,h in ids.items():assert sha(p)==h,'Input changed during plotting'
    for name in ['plotted_data.json','descriptive_summary.md']:outputs[name]=sha(HERE/name)
    write(HERE/'receipt.json',dict(status='PASS_PLOTTING_FROM_SAVED_MAIN_SCORES_NOT_NUMERIC_REVIEW',started_utc=started,completed_utc=utc(),
        command=[sys.executable,str(Path(__file__))],python_version=sys.version,matplotlib_version=matplotlib.__version__,
        source_sha256=sha(__file__),style_sha256=sha(HERE/'plot_utils.py'),input_sha256_before_after=ids,outputs=outputs,
        integrity=dict(all48_records_retained=True,observed_points=36,observed_window_means=9,unavailable_groups=3,common_y_range=[0,50],
            no_clipped_data=maximum<50,CSV_absrel_matches_all48=True,means_imported=True),
        actual_access=dict(sensor_depth_PNG=0,prediction_NPZ=0,RGB_images=0,model_calls=0,GA_calls=0,new_metric_computation=0),
        visual_QA='PENDING_ACTUAL_VIEW_IMAGE; separate receipt will record actual view',
        independent_numeric_review='PENDING_AT_FIGURE_CREATION'))
    print(json.dumps(dict(status='PLOTTED_VISUAL_QA_PENDING',outputs=outputs),indent=2))
if __name__=='__main__':main()
