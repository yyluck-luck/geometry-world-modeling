"""Full frozen curves and explicitly post-score depth-tail inspection."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT/'work/S17C_environment/site-packages'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
from PIL import Image
from s23_geometry_diagnostic import nearest,BASES
OUT=ROOT/'work/S23_reporting';OUT.mkdir(exist_ok=False)
B=ROOT/'results/S23_geometry_diagnostic'
records={n:json.loads((B/(n+'_frames.json')).read_text())for n in BASES}
styles={'cut3r':('#0072B2','-','CUT3R'),'ttt3r':('#D55E00','--','TTT3R'),'filt3r':('#009E73','-.','FILT3R')}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
fig,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained')
for name,(color,ls,label)in styles.items():
    rows=records[name];x=np.arange(300)
    values=[[r.get('raw',{}).get('absrel',np.nan)*100 for r in rows],
            [r.get('raw',{}).get('rmse',np.nan)for r in rows],
            [r.get('oracle_scale',np.nan)for r in rows],
            [r['closure']['relative_median']*100 if r['closure']['relative_median'] is not None else np.nan for r in rows]]
    for ax,y in zip(axes.flat,values):ax.plot(x,y,color=color,ls=ls,lw=1.1,label=label)
labels=['Raw AbsRel (%)','Raw depth RMSE (m)','Per-frame GT median scale (oracle)','Within-frame head disagreement (%)']
for k,(ax,label)in enumerate(zip(axes.flat,labels)):
    ax.set_ylabel(label);ax.set_xlabel('Frame index');ax.grid(alpha=.15)
    if k!=2:ax.set_ylim(bottom=0)
axes[0,0].legend(frameon=False,ncol=3,fontsize=9)
axes[1,0].axhline(1,color='.5',lw=.8,ls=':')
fig.suptitle('One seen TUM sequence: geometry diagnostics of three existing methods\n278 depth-matched frames; 22 gaps retained. Head agreement uses all 300 frames.',fontsize=11)
for ext in ['png','pdf','svg']:fig.savefig(OUT/('s23_full_curves.'+ext),dpi=170)
plt.close(fig)

tail=json.loads((ROOT/'results/S23_depth_tail/metrics.json').read_text())
fig,axes=plt.subplots(2,1,figsize=(8,6),layout='constrained',sharex=True)
x=np.arange(4);axes[0].bar(x,[b['pixel_share']*100 for b in tail['methods']['cut3r']],color='.6')
axes[0].set_ylabel('Share of valid GT pixels (%)');axes[0].set_ylim(0,100)
for j,(name,(color,ls,label))in enumerate(styles.items()):
    axes[1].bar(x+(j-1)*.24,[b['sse_share']*100 for b in tail['methods'][name]],width=.24,color=color,label=label,hatch=['','//','..'][j])
axes[1].set_ylabel('Share of total squared error (%)');axes[1].set_ylim(0,100)
axes[1].set_xticks(x,['0 < Z <= 2','2 < Z <= 4','4 < Z <= 8','Z > 8']);axes[1].set_xlabel('Sensor depth band (m); all valid depths retained')
axes[1].legend(frameon=False,ncol=3)
fig.suptitle('Post-score explanation: a small far-depth tail dominates squared error\nSame GT bands and pixels for all methods; no change to primary scores',fontsize=11)
for ext in ['png','pdf','svg']:fig.savefig(OUT/('s23_depth_tail.'+ext),dpi=170)
plt.close(fig)

# One explicitly selected example, without editing the original photograph.
i=max((r for r in records['filt3r']if 'raw'in r),key=lambda r:r['raw']['rmse'])['index']
rgbmanifest=json.loads((ROOT/'work/S21_baseline_preparation/run_manifest.json').read_text())
dm=json.loads((ROOT/'work/S23_geometry_preparation/manifest.json').read_text())
p=Path(rgbmanifest['frames'][i]['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==rgbmanifest['frames'][i]['sha256']
rgb=np.asarray(Image.open(p));g=nearest(np.asarray(Image.open(dm['frames'][i]['depth_file']))).astype(float)/5000
depth={}
for name in ['ttt3r','filt3r']:
    with np.load(BASES[name]/f'frame_{i:04d}.npz')as a:depth[name]=a['pts3d_in_self_view'][0,:,:,2].astype(float)
valid=g>0;diff=(depth['filt3r']-g)**2-(depth['ttt3r']-g)**2
lim=max(float(abs(diff[valid]).max()),1e-6);vmax=float(np.ceil(max(g.max(),*(a.max()for a in depth.values()))))
fig,axes=plt.subplots(2,3,figsize=(12,7.7),layout='constrained')
axes[0,0].imshow(rgb);axes[0,0].set_title('Original real photograph')
cmap=plt.get_cmap('viridis').copy();cmap.set_bad('.85')
im=axes[0,1].imshow(np.where(valid,g,np.nan),vmin=0,vmax=vmax,cmap=cmap);axes[0,1].set_title('Sensor depth (m); grey = missing')
axes[0,2].imshow(np.where(valid,(g>8).astype(float),np.nan),vmin=0,vmax=1,cmap=cmap);axes[0,2].set_title('Yellow: sensor Z > 8 m')
for ax,name in [(axes[1,0],'ttt3r'),(axes[1,1],'filt3r')]:ax.imshow(depth[name],vmin=0,vmax=vmax,cmap=cmap);ax.set_title(name.upper()+' predicted depth (m)')
im2=axes[1,2].imshow(np.where(valid,diff,np.nan),cmap='coolwarm',norm=TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim));axes[1,2].set_title('Squared-error difference (m²)\nRed: FILT worse; blue: FILT better')
for ax in axes.flat:ax.axis('off')
fig.colorbar(im,ax=[axes[0,1],axes[1,0],axes[1,1]],shrink=.65,label='Depth (m)')
fig.colorbar(im2,ax=axes[1,2],shrink=.65)
fig.suptitle(f'Frame {i}: highest FILT depth RMSE, selected after scoring\nA single inspection image does not establish sensor reliability or a memory-failure mechanism.',fontsize=11)
fig.savefig(OUT/'s23_real_depth_example.png',dpi=150);plt.close(fig)
(OUT/'figure_recipe.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),scope='frozen full curves plus post-score depth-band explanation and one authentic RGB',example_index=i,example_selection='highest FILT raw RMSE after scoring',original_rgb_sha256=rgbmanifest['frames'][i]['sha256'],source_metrics_sha256=hashlib.sha256((B/'metrics.json').read_bytes()).hexdigest(),skill='figure-designer: full range, dual encodings, vector curve exports, explicit missingness, no invented error bars',font_pt=10),indent=2)+'\n')
print(OUT)
