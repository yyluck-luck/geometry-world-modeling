"""Descriptive figure from the one recorded S67 result, with all 515 points."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent
E=D/'execution_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(E/'receipt.json')=='5ec04455ba9155913882155d36fd64b7e32c8022c8959e14bc6a5023f1d29f70'
assert sha(E/'fixed_geometry_and_projections.npz')=='985e9b235b4c0ea1a0bd2d193900961b2e7e6a5da1124ca89004efe0ca0d2a8d'
r=json.loads((E/'receipt.json').read_text())
assert r['status']=='COMPLETE_FIXED_PAIR_DIAGNOSTIC'
with np.load(E/'fixed_geometry_and_projections.npz',allow_pickle=False) as x:
    displacement=np.linalg.norm(x['query_projection_A']-x['query_projection_B'],axis=1)
assert displacement.shape==(515,) and np.isfinite(displacement).all()
with np.load(E/'A_context.npz',allow_pickle=False) as a,np.load(E/'B_context.npz',allow_pickle=False) as b:
    assert set(a.files)==set(b.files)
    assert all(a[k].dtype==b[k].dtype and a[k].shape==b[k].shape and a[k].tobytes()==b[k].tobytes() for k in a.files)
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(10.3,4.4),gridspec_kw={'width_ratios':[1,1.1]})
fig.subplots_adjust(left=.08,right=.98,bottom=.29,top=.77,wspace=.32)
fig.suptitle('Projection and weights changed; returned context did not',fontsize=15,y=.965)
fig.text(.5,.887,'S67 | One fixed query and saved scene | Artificial radial-depth intervention | No new video',ha='center',fontsize=9.5)
ax[0].step(np.sort(displacement),np.arange(1,516)/515*100,where='post',color='#263647',lw=1.8)
ax[0].set(xlim=(0,60),ylim=(0,100),xlabel='New-query point displacement (pixels)',ylabel='Points at or below displacement (%)',title='A. All 515 point projections')
ax[0].grid(axis='y',alpha=.18)
ax[0].text(.96,.22,f'Median: {np.median(displacement):.2f} px\nMaximum: {displacement.max():.2f} px',ha='right',va='top',transform=ax[0].transAxes,fontsize=9)
labels=np.arange(5);w=.34
for i,(c,color,fill) in enumerate(zip(r['conditions'],['#0072B2','#D55E00'],[True,False])):
    assert [x[0] for x in c['weights']]==labels.tolist()
    vals=[x[1] for x in c['weights']];xx=labels+(-w/2 if i==0 else w/2)
    ax[1].bar(xx,vals,w,color=color if fill else 'white',edgecolor=color,linewidth=1.5,label='A: stored' if i==0 else 'B: radial')
    for x,y in zip(xx,vals):ax[1].text(x,.008,'A' if i==0 else 'B',ha='center',va='bottom',color='white' if fill else color,fontsize=8)
ax[1].set(xticks=labels,xlabel='History source ID',ylabel='Normalized retrieval weight',ylim=(0,.36),title='B. All five source weights')
ax[1].legend(frameon=False,fontsize=9,loc='upper right')
fig.text(.5,.135,'Every source retained quota 1. Both arms selected [0, 2, 4, 1].',ha='center',fontsize=11)
fig.text(.5,.075,'All four returned context arrays and source IDs were byte-identical.',ha='center',fontsize=10)
fig.text(.5,.025,'Scope: this fixed selection path only; no correctness, video-quality, or novelty claim.',ha='center',fontsize=9,color='#44505c')
out=D/'figures';out.mkdir(exist_ok=False)
for ext in ('png','svg'):fig.savefig(out/('S67_projection_changes_context_unchanged.'+ext),dpi=180,facecolor='white')
plt.close(fig)
manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(Path(__file__)),
             evidence={str(E/n):sha(E/n) for n in ('receipt.json','fixed_geometry_and_projections.npz','A_context.npz','B_context.npz')},
             outputs={p.name:sha(p) for p in out.iterdir() if p.is_file()},points=515,scenes=1,
             purpose='All-data descriptive plot; a point is not an independent scene; no new experiment.')
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'out':str(out),'manifest_sha256':sha(out/'manifest.json')}))
