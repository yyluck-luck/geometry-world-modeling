"""All prespecified new-frame scores and original RGB photos, after final PASS."""
from pathlib import Path
import sys, json, hashlib
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'work/S17C_environment/site-packages'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

OUT=Path(__file__).resolve().parent
BASE=ROOT/'results/S26B_consumer_baseline'
read=lambda p:json.loads(p.read_text())
assert read(BASE/'scoring/receipt.json')['status']=='PASS'
assert read(ROOT/'work/S26B_root_numeric_review/receipt.json')['status']=='PASS'
assert read(ROOT/'work/S26B_commit_diagnostic/results/receipt.json')['status']=='PASS'
assert not (OUT/'figure_receipt.json').exists()
metrics=read(BASE/'scoring/metrics.json')
methods=['cut3r','ttt3r','filt3r'];labels=['CUT3R','TTT3R','FILT3R'];colors=['#0072B2','#D55E00','#009E73'];markers=['o','s','^']
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
fig,axes=plt.subplots(1,2,figsize=(10,4.1),layout='constrained')
for ax,key,scale,title in zip(axes,['absrel','rmse_m'],[100,100],['Absolute relative depth error (%)','Per-frame depth RMSE (cm)']):
    upper=0
    for method,label,color,marker in zip(methods,labels,colors,markers):
        rows=[r for r in metrics['per_frame'] if r['mode']==method and r['index'] in [4,5,6,7]]
        assert [r['index'] for r in rows]==[4,5,6,7]
        values=[r[key]*scale for r in rows];upper=max(upper,*values)
        ax.plot([4,5,6,7],values,marker=marker,label=label,color=color)
    ax.set_ylim(0,upper*1.10);ax.set_xticks([4,5,6,7]);ax.set_xlabel('New frame index');ax.set_ylabel(title);ax.grid(alpha=.2)
axes[0].legend(frameon=False)
fig.suptitle('Original VMem geometry consumer | all four new real frames',fontsize=14)
for suffix in ['png','pdf','svg']:fig.savefig(OUT/('new4_depth_scores.'+suffix),dpi=180)
plt.close(fig)
candidate=read(ROOT/'work/S26_consumer_baseline_preparation/candidate_inputs.json')
fig,axes=plt.subplots(1,4,figsize=(12,3.1),layout='constrained')
photos=[]
for ax,i in zip(axes,[4,5,6,7]):
    row=candidate['frames'][i]
    p=Path(row['path'])
    raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();assert h==row['sha256']
    ax.imshow(Image.open(p));ax.axis('off');ax.set_title(f'Real RGB frame {i}')
    photos.append({'index':i,'path':str(p),'sha256':h})
fig.suptitle('All new input photos | previously seen TUM fr2_desk | no generated images',fontsize=13)
fig.savefig(OUT/'all_new4_real_photos.png',dpi=160);plt.close(fig)
(OUT/'figure_receipt.json').write_text(json.dumps(dict(status='GENERATED_PENDING_VISUAL_REVIEW',utc=datetime.now(timezone.utc).isoformat(),photos=photos,all_new_frames_shown=True,no_metric_change=True,files_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.suffix in ['.png','.pdf','.svg']}),indent=2)+'\n')
