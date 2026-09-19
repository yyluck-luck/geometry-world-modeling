#!/usr/bin/env python3
"""Plot already-scored S34 numbers and three already-rendered depth grids only."""
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,io,json,math,sys
from plot_utils import COLORS,LABELS,FRAME_MARKERS,UNOBSERVED,configure
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE=Path(__file__).resolve().parent
SCORE=ROOT/'results/S34_depth_scoring'
CONSUMER=ROOT/'results/S34_original_consumer'
ENDS=['old_fixed_zero','old_fixed_free_400','old_fixed_common_scale_400']
IDS={
str(SCORE/'receipt.json'):'4189323ed3715844033c2b13b1c754011f85261dc0df25cb9d31bfbb02bcb9b5',
str(SCORE/'metrics.json'):'1f69fbe1675321ec96d9d08543a0cf0a8bace683590abb382217789ce3ab844b',
str(SCORE/'per_frame.csv'):'3b19fd9360b2858031560134def8cd16601da4b4689b994ea0cf1331a2817fdc',
str(CONSUMER/'receipt.json'):'65dc7fe03f9b259c8678b1ffde1284cf45d42ec14b8c120a95a45937cdbe0a56',
str(ROOT/'work/S34_independent_numeric_review/receipt.json'):'2885ee548926e8bf2bea65e157604428228c70d109e5316b8819c1b908512afa',
str(ROOT/'work/S34_consumer_numeric_review/executed/receipt.json'):'59d688e7c15ce6e0e374f1e41c98b3922d7e8d17ba0c644e08ea72779f726316'}
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
    started=utc();assert not (HERE/'receipt.json').exists(),'Keep completed figures intact'
    for p,h in IDS.items():assert sha(p)==h,p
    sr=read(SCORE/'receipt.json');m=read(SCORE/'metrics.json');cr=read(CONSUMER/'receipt.json')
    ir=read(ROOT/'work/S34_independent_numeric_review/receipt.json');vr=read(ROOT/'work/S34_consumer_numeric_review/executed/receipt.json')
    assert sr['status']=='PASS' and cr['status']=='PASS_ORIGINAL_CONSUMER_COMPONENTS'
    assert ir['status']=='PASS_INDEPENDENT_S34_GEOMETRY_SCORE_REVIEW' and (ir['rows'],ir['groups'])==(12,3)
    assert vr['status']=='PASS_INDEPENDENT_SAVED_CONSUMER_REVIEW'
    for name in ('metrics.json','per_frame.csv'):assert sr['outputs'][name]==IDS[str(SCORE/name)]
    assert ir['input_sha256'][str(SCORE/'metrics.json')]==IDS[str(SCORE/'metrics.json')]
    assert cr['final_context_ids_status']=='NOT_RUN_MISSING_NMS_AND_LATENT_HISTORY'
    rows=m['per_frame'];csvrows=list(csv.DictReader(io.StringIO((SCORE/'per_frame.csv').read_text())))
    assert len(rows)==len(csvrows)==12
    points=[];means=[]
    for i,e in enumerate(ENDS):
        subset=[r for r in rows if r['endpoint']==e];assert [r['index'] for r in subset]==[4,5,6,7]
        means.append(dict(endpoint=e,label=LABELS[i],x=i,absrel=m['primary_new4'][e]['absrel'],percent=100*m['primary_new4'][e]['absrel']))
        for j,r in enumerate(subset):
            q=csvrows[i*4+j];assert q['endpoint']==e and int(q['index'])==r['index'] and float(q['absrel'])==r['absrel']
            assert math.isfinite(r['absrel']) and r['metric_status']=='DEFINED'
            points.append(dict(endpoint=e,index=r['index'],absrel=r['absrel'],percent=100*r['absrel'],x=i+[-.24,-.08,.08,.24][j],marker=FRAME_MARKERS[j]))
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.colors import Normalize
    configure(plt)
    renderdata=[];depths=[]
    for e in ENDS:
        rp=CONSUMER/e/'render.npz';vp=CONSUMER/e/'votes.json'
        for p in (rp,vp):
            expected=cr['outputs'][str(p.relative_to(CONSUMER))];assert sha(p)==expected;IDS[str(p)]=expected
        with np.load(io.BytesIO(rp.read_bytes()),allow_pickle=False) as z:
            d=z['depth'].copy();idx=z['surfel_index_map']
            assert d.dtype==np.float32 and d.shape==(288,512) and np.isfinite(d).all() and (d>=0).all()
            assert np.array_equal(d==0,idx<0)
        votes=read(vp);assert votes['expanded_candidate_source_ids']==list(range(8)) and votes['final_context_ids'] is None
        assert votes['visible_pixels']==int(np.count_nonzero(d)) and votes['total_pixels']==d.size
        assert hashlib.sha256(d.tobytes()).hexdigest()==cr['array_schemas'][f'{e}/render.npz']['depth']['sha256']
        renderdata.append(dict(endpoint=e,path=str(rp),npz_sha256=IDS[str(rp)],depth_array_sha256=hashlib.sha256(d.tobytes()).hexdigest(),
            shape=list(d.shape),dtype=str(d.dtype),minimum_m=float(d.min()),maximum_m=float(d.max()),
            zero_uncovered_count=int(np.count_nonzero(d==0)),positive_covered_count=int(np.count_nonzero(d)),
            depth_values_m=d.tolist(),candidate_ids_imported=votes['expanded_candidate_source_ids']))
        depths.append(d)
    ymax=float(math.ceil(max(p['percent'] for p in points)+1));vmax=max(r['maximum_m'] for r in renderdata)
    write(HERE/'plotted_data.json',dict(status='ACTUAL_MAIN_AND_DIFFERENT_AUTHOR_SAVED_REVIEWS_PASS',created_utc=utc(),source_sha256=IDS,
        score_points=points,score_means=means,render_grids=renderdata,
        axes=dict(absrel_percent_min=0,absrel_percent_max=ymax,depth_color_min_m=0,depth_color_max_m=vmax,depth_scale='linear',zero_uncovered_color=UNOBSERVED),
        transformations=['AbsRel multiplied by100; means imported without sensor rescoring','All3 saved renderer depth grids shown, exact zeros masked only for separate uncovered color','Shared linear depth range includes every maximum; no clipping, percentiles, log scaling or spatial crop'],
        limitations=['Known8 photos with given GT cameras and fixed old4 depth','No RGB generation; renderer grids are not sensor ground truth or visibility accuracy','All3 eight-candidate lists identical; final context IDs NOT RUN','Ordinary control, no innovation or fullvideo conclusion','Correlated frames; no CI or significance claim']))
    fig,ax=plt.subplots(figsize=(7.2,3.65));fig.subplots_adjust(left=.10,right=.985,bottom=.26,top=.86)
    for i,e in enumerate(ENDS):
        mean=means[i]['percent'];ax.bar(i,mean,width=.66,color=COLORS[i],alpha=.13,edgecolor=COLORS[i],linewidth=1,zorder=2)
        for p in points[i*4:i*4+4]:ax.scatter(p['x'],p['percent'],s=39,marker=p['marker'],c=COLORS[i],edgecolors='white',linewidth=.5,zorder=4)
        ax.plot([i-.31,i+.31],[mean,mean],c='black',lw=1.8,zorder=5)
        ax.text(i,ymax-.39,f"Mean {mean:.4f}%",ha='center',va='top',fontsize=9)
    ax.set(xlim=(-.6,2.6),ylim=(0,ymax),ylabel='AbsRel (%)  |  lower is better',xticks=range(3),xticklabels=LABELS)
    ax.yaxis.grid(True,color='#E7E9ED',lw=.65);ax.set_axisbelow(True)
    legends=[Line2D([0],[0],marker=FRAME_MARKERS[i],color='#4B5563',linestyle='None',markersize=5,label=f'Frame {i+4}') for i in range(4)]
    legends.append(Line2D([0],[0],color='black',lw=1.8,label='4-frame mean'))
    fig.legend(handles=legends,loc='lower center',bbox_to_anchor=(.55,.085),ncol=5,frameon=False,columnspacing=1.35)
    fig.text(.10,.96,'S34  |  Fixed old depth, three ordinary controls',fontsize=10.5,weight='bold',va='top')
    fig.text(.10,.885,'12 frame values + 3 means; saved score arithmetic independently verified',fontsize=8.5)
    fig.text(.10,.025,'Given GT cameras; already-seen short sequence. Correlated frames; no significance claim.',fontsize=8.5)
    for ext in ('png','pdf','svg'):fig.savefig(HERE/f's34_depth_scores.{ext}',dpi=300)
    plt.close(fig)
    cmap=plt.get_cmap('viridis').copy();cmap.set_bad(UNOBSERVED);norm=Normalize(vmin=0,vmax=vmax,clip=False)
    fig,axes=plt.subplots(1,3,figsize=(7.2,3.5));fig.subplots_adjust(left=.035,right=.985,bottom=.34,top=.80,wspace=.10)
    for i,(ax,d) in enumerate(zip(axes,depths)):
        im=ax.imshow(np.ma.masked_equal(d,0),cmap=cmap,norm=norm,interpolation='nearest',aspect='equal')
        ax.set_axis_off();ax.set_title(LABELS[i],fontsize=9.3,pad=5)
        r=renderdata[i];ax.text(.5,-.095,f"{r['positive_covered_count']:,} / 147,456 covered pixels",transform=ax.transAxes,ha='center',fontsize=8.2)
    cax=fig.add_axes([.245,.21,.70,.047]);cb=fig.colorbar(im,cax=cax,orientation='horizontal');cb.set_label(f'Saved renderer depth (m), shared linear 0–{vmax:.3f}',fontsize=8.5,labelpad=3)
    cb.ax.tick_params(labelsize=8.5)
    fig.legend(handles=[Patch(facecolor=UNOBSERVED,edgecolor='#9CA3AF',label='0: uncovered')],loc='lower left',bbox_to_anchor=(.03,.175),frameon=False,fontsize=8.5)
    fig.text(.035,.96,'S34  |  Actual original-kernel depth renders at input camera 7',fontsize=10.5,weight='bold',va='top')
    fig.text(.035,.875,'All maxima retained; 512 × 288 grid per condition; saved quantities independently checked',fontsize=8.5)
    fig.text(.035,.058,'Depth visualizations, not RGB photos, sensor-GT agreement or visibility accuracy.',fontsize=8.5)
    fig.text(.035,.015,'Candidate IDs remain 0–7 in all conditions; final context IDs were not run.',fontsize=8.5)
    for ext in ('png','pdf','svg'):fig.savefig(HERE/f's34_renderer_depths.{ext}',dpi=300)
    plt.close(fig)
    for p,h in IDS.items():assert sha(p)==h,'Plot source changed'
    outputs={p.name:sha(p) for p in HERE.iterdir() if p.is_file()}
    write(HERE/'receipt.json',dict(status='RENDERED_AWAITING_ACTUAL_VISUAL_QA',started_utc=started,completed_utc=utc(),
        command=f'{sys.executable} {Path(__file__).resolve()}',python=sys.version,numpy=np.__version__,matplotlib=matplotlib.__version__,
        source_sha256=IDS,outputs=outputs,score_points=12,score_means=3,renderer_grids=3,GT_reads=0,new_model=0,new_GA=0,new_renderer=0,
        scope='Plotting existing saved scores and three saved render grids; no rescore, raw depth optimizer decode, or regeneration',
        vector_scope='Score PDF/SVG vector. Renderer pixel grids intrinsically raster, labels/colorbar vector; not falsely claimed all-vector.'))
    print(json.dumps(dict(status='RENDERED_AWAITING_ACTUAL_VISUAL_QA',depth_vmax=vmax,score_ymax=ymax,render_shape=[288,512])))
if __name__=='__main__':main()
