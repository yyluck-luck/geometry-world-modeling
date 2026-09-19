#!/usr/bin/env python3
"""S33 four-condition plot from sealed JSON/CSV only; no scientific rerun."""
from pathlib import Path
from datetime import datetime,timezone
import csv,hashlib,io,json,math,sys
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE=Path(__file__).resolve().parent
BASE=ROOT/'results/S33_pair_scale_scoring'
WINDOWS=['fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2']
ENDS=['initial_0step','corrected_getter_400','global_rescaled_400','common_pair_scale_400']
LABELS=['0 step\nS32','400 steps\nS32','400 + k\nS32','Pair-scale\nS33']
PALETTE=['#0072B2','#D55E00','#009E73','#CC79A7']
MARKERS=['o','s','D','^']
IDS={str(BASE/'receipt.json'):'30976ca99eaf1b9e107aaa2001b3c60537f456d19073eaec3420d9bda37ef1f6',
     str(BASE/'metrics.json'):'349aab3c275c2a35da921c8fbd734ddf8cddf8e4d5e98dffca56655db668ef63',
     str(BASE/'per_frame.csv'):'ce5520c7d167db04db0d8b3dbeec8bf475a94b576e41ca626cd36eb959c757eb',
     str(BASE/'imported_s32_metrics.json'):'975ad404667a24032ca3c3c5bcfa61fc70dc1f38ef3dd14391df9c4dd2b0bbbf',
     str(BASE/'imported_s32_per_frame.csv'):'1743010707fdb9dc1cdd7b6801b51b8f5eb8c8d99fcb10f95b32b5d906ca700d',
     str(ROOT/'work/S33_scoring_preparation/manifest.json'):'83be08e12d3102487cf31f902c396db49567cfdbc63cbfeba12b02d3ab1665ab'}
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
REVIEW=ROOT/'work/S33_independent_numeric_review/receipt.json'
REVIEW_SHA='057b369b82e6b16af640222c16ada5536f67851b06dee7d248ce61eee6d21b0e'
PLOTTED_SHA='a0ec1d980dcd7fc98616902bf5dacdbeb380785b21eeff03ba9f48d126c34a35'
def main():
    started=utc();assert not (HERE/'receipt.json').exists(),'Never overwrite a finished figure without preserving prior version'
    for p,h in IDS.items():assert sha(p)==h,p
    assert sha(REVIEW)==REVIEW_SHA
    review=read(REVIEW);assert review['status']=='PASS_INDEPENDENT_S33_SAVED_REVIEW' and review['full_rows']==64 and review['new_scored_rows']==12 and review['new_NA_rows']==4
    assert sha(HERE/'plotted_data.json')==PLOTTED_SHA
    r=read(BASE/'receipt.json');m=read(BASE/'metrics.json');old=read(BASE/'imported_s32_metrics.json')
    assert r['status']=='PASS' and r['scoring_manifest_sha256']==m['scoring_manifest_sha256']==IDS[str(ROOT/'work/S33_scoring_preparation/manifest.json')]
    assert r['output_sha256']['metrics.json']==IDS[str(BASE/'metrics.json')]
    assert (m['prespecified_windows'],m['prespecified_groups'],m['prespecified_rows'],m['scored_rows'],m['unavailable_rows'])==(4,16,64,48,16)
    assert m['per_frame'][:48]==old['per_frame']
    assert all(m['window_groups'][w][e]==old['window_groups'][w][e] for w in WINDOWS for e in ENDS[:3])
    oldcsv=(BASE/'imported_s32_per_frame.csv').read_bytes();newcsv=(BASE/'per_frame.csv').read_bytes();assert newcsv[:len(oldcsv)]==oldcsv
    csvrows=list(csv.DictReader(io.StringIO(newcsv.decode())));rows=m['per_frame']
    keyed={(x['window_id'],x['endpoint'],x['index']):x for x in rows}
    csvkey={(x['window_id'],x['endpoint'],int(x['index'])):x for x in csvrows}
    domain={(w,e,i) for w in WINDOWS for e in ENDS for i in range(4)}
    assert len(rows)==len(csvrows)==64 and set(keyed)==set(csvkey)==domain
    points=[];means=[]
    for wi,w in enumerate(WINDOWS):
        for ei,e in enumerate(ENDS):
            g=m['window_groups'][w][e];mean=g['absrel'];assert g['frame_indices']==[0,1,2,3]
            origin='S32_imported_unchanged' if ei<3 else 'S33_new_constrained400'
            means.append(dict(window_id=w,endpoint=e,origin=origin,absrel=mean,percent=None if mean is None else 100*mean,x=ei,panel=wi))
            for i in range(4):
                x=keyed[w,e,i];y=csvkey[w,e,i];v=x['absrel']
                assert x['row_status']==y['row_status'] and ((v is None and y['absrel']=='') or (v is not None and float(y['absrel'])==v))
                assert v is None or math.isfinite(v) and 0<=100*v<50
                points.append(dict(window_id=w,endpoint=e,index=i,origin=origin,absrel=v,percent=None if v is None else 100*v,
                    x=ei+[-.21,-.07,.07,.21][i],panel=wi,marker=MARKERS[ei],color=PALETTE[ei],row_status=x['row_status'],missing_reason=x['missing_reason']))
    assert sum(p['percent'] is not None for p in points)==48 and sum(p['percent'] is not None for p in means)==12
    assert all(m['endpoint_summaries'][e]['all_four_prespecified']['absrel'] is None for e in ENDS)
    proposed_data=dict(status='MAIN_S33_SCORES_INDEPENDENT_REVIEW_PENDING',created_utc=utc(),source_sha256=IDS,
        points=points,window_means=means,endpoint_summaries_imported=m['endpoint_summaries'],complete_domain=dict(rows=64,actual_frame_points=48,NA_rows=16,actual_means=12,NA_means=4),
        axes=dict(scale='linear',unit='percent',shared_min=0,shared_max=50),old48_JSON_rows_and_CSV_prefix_identical=True,
        transformations=['Saved AbsRel multiplied by100 for percent','Window means imported from existing scorer, no new sensor metric computation','Fixed deterministic frame offsets0to3; no sampling, random jitter, mask or threshold'],
        limitations=['All3legacy controls imported fromS32; only fourth condition newS33','Previously scored shortwindows and givenGTcamera','Correlated frames, no independence/CI/significance claim','Ordinary scale constraint, no novelty or fullvideo proof','Independent new-score arithmetic review pending at first rendering'])
    preserved=read(HERE/'plotted_data.json')
    for key in proposed_data:
        if key!='created_utc':assert preserved[key]==proposed_data[key],key
    # Retain original creation/status provenance and every plotted value byte-for-byte.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':9,'axes.titlesize':10,'axes.labelsize':9,
        'xtick.labelsize':8.5,'ytick.labelsize':8.5,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
        'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'savefig.dpi':300,'path.simplify':False})
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.9),sharey=True)
    fig.subplots_adjust(left=.09,right=.985,bottom=.27,top=.905,hspace=.46,wspace=.20)
    starts=['987–990','1974–1977','264–267','529–532']
    for wi,(ax,w) in enumerate(zip(axes.flat,WINDOWS)):
        ax.set_xlim(-.5,3.5);ax.set_ylim(0,50);ax.set_yticks(range(0,51,10));ax.set_xticks(range(4),LABELS)
        ax.grid(axis='y',color='#E4E6E8',lw=.55,zorder=0);ax.tick_params(axis='x',length=0,pad=6)
        ax.set_title(f'({chr(97+wi)}) {w}  |  RGB {starts[wi]}',loc='left',pad=7)
        if wi%2==0:ax.set_ylabel('AbsRel (%) ↓')
        if wi==0:
            ax.text(1.5,31,'NA',ha='center',fontsize=20,color='#60666D')
            ax.text(1.5,20,'Missing given-camera association\nAll 4 conditions unavailable\n4 frames retained in the design',ha='center',va='center',fontsize=9,color='#60666D',linespacing=1.4)
            continue
        for ei,e in enumerate(ENDS):
            group=[p for p in points if p['window_id']==w and p['endpoint']==e];mean=next(x['percent'] for x in means if x['window_id']==w and x['endpoint']==e)
            ax.bar(ei,mean,width=.57,color=PALETTE[ei],alpha=.12,linewidth=0,zorder=1)
            ax.plot([ei-.27,ei+.27],[mean,mean],color='#24282D',linewidth=1.5,zorder=2)
            ax.scatter([x['x'] for x in group],[x['percent'] for x in group],s=25,marker=MARKERS[ei],facecolor='white',edgecolor=PALETTE[ei],linewidth=1.2,zorder=3)
            ax.text(ei,max(mean,max(x['percent'] for x in group))+1.8,f'{mean:.2f}',ha='center',va='bottom',fontsize=9)
    fig.text(.09,.969,'S33 saved-output arithmetic independently verified',fontsize=9.5,color='#256344',va='top')
    fig.text(.09,.178,'Markers: frames 0–3, left to right per condition.  Black line / number: four-frame mean.',fontsize=8.5)
    fig.text(.09,.141,'First 3 controls: imported S32.  Last: new S33 with fixed geometric mean of pair scales.',fontsize=8.5)
    fig.text(.09,.104,'Given GT camera poses · already seen short windows (~0.10 s) · all four-window averages: NA.',fontsize=8.5)
    fig.text(.09,.067,'Ordinary controls, no innovation/video claim.  Correlated frames; no significance tests or CIs.',fontsize=8.5)
    outputs={}
    for ext in ['png','pdf','svg']:
        p=HERE/f's33_four_conditions.{ext}';fig.savefig(p,format=ext);outputs[p.name]=sha(p)
    plt.close(fig)
    outputs['plotted_data.json']=sha(HERE/'plotted_data.json')
    for p,h in IDS.items():assert sha(p)==h,'Changed plotting source'
    write(HERE/'receipt.json',dict(status='PASS_PLOTTING_ONLY_VISUAL_QA_PENDING',started_utc=started,completed_utc=utc(),command=[sys.executable,str(Path(__file__))],
        python_version=sys.version,matplotlib_version=matplotlib.__version__,source_sha256=sha(__file__),input_sha256_before_after=IDS,outputs=outputs,
        counts=dict(rows=64,actual_frame_points=48,window_means=12,NA_rows=16),actual_access=dict(NPZ=0,sensor_PNG=0,RGB_images=0,new_score=0,model_GA=0),
        independent_numeric_review=dict(status=review['status'],path=str(REVIEW),sha256=REVIEW_SHA,started_utc=review['started_utc'],completed_utc=review['completed_utc']),original_plotted_data_unchanged=sha(HERE/'plotted_data.json')==PLOTTED_SHA,visual_QA='Separate receipt after actualviewPNG'))
    print(json.dumps(outputs,indent=2))
if __name__=='__main__':main()
