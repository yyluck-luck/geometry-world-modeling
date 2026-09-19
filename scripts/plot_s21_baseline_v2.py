"""Render every scored S21 frame, plus explicitly selected residual photographs."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT/'work/S17C_environment/site-packages'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
B=ROOT/'results/S21_baseline/scoring'
OUT=ROOT/'work/S21_reporting_v2'
OUT.mkdir(parents=True,exist_ok=False)
metrics=json.loads((B/'metrics.json').read_text());assert metrics['passed']
manifest=json.loads((ROOT/'work/S21_baseline_preparation/run_manifest.json').read_text())
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
style={'cut3r':('#0072B2','-','CUT3R (TTT3R code)'), 'ttt3r':('#D55E00','--','TTT3R')}
fig,axes=plt.subplots(3,1,figsize=(8,7.2),sharex=True,layout='constrained')
fields=[('ate_m','Position error (m)'),('rpe_translation_m','Local translation error (m)'),('rpe_rotation_deg','Local rotation error (deg)')]
data={name:dict(np.load(B/(name+'_aligned.npz')))for name in style}
for name,(color,linestyle,label)in style.items():
    for ax,(field,ylabel)in zip(axes,fields):
        v=data[name][field];ax.plot(np.arange(len(v)),v,color=color,ls=linestyle,lw=1.2,label=label);ax.set_ylabel(ylabel);ax.set_ylim(bottom=0);ax.grid(alpha=.15)
axes[0].legend(frameon=False,ncol=2);axes[-1].set_xlabel('Frame index (all 300 associated RGB frames; local errors use 299 pairs)')
cut_cm=metrics['methods']['cut3r']['official'][0]*100
ttt_cm=metrics['methods']['ttt3r']['official'][0]*100
fig.suptitle(f'Position RMSE: CUT3R {cut_cm:.2f} cm | TTT3R {ttt_cm:.2f} cm\nTUM fr2_desk; shared 512 DPT weights; original internal precision; one seen scene',fontsize=11)
for ext in ['png','pdf','svg']:fig.savefig(OUT/('s21_all_frame_errors.'+ext),dpi=180)
plt.close(fig)
# Two largest TTT3R residuals with a neighboring real photo on each side.
worst=metrics['methods']['ttt3r']['worst_indices_descending'][:2]
indices=[min(299,max(0,i+d))for i in worst for d in [-1,0,1]]
fig,axes=plt.subplots(2,3,figsize=(7.2,5.2),layout='constrained')
for ax,i in zip(axes.flat,indices):
    e=manifest['frames'][i];p=Path(e['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256']
    ax.imshow(Image.open(p));ax.set_title(f"Real RGB frame {i}\nCUT3R {data['cut3r']['ate_m'][i]*100:.2f} cm | TTT3R {data['ttt3r']['ate_m'][i]*100:.2f} cm",fontsize=10);ax.axis('off')
fig.suptitle('Exploratory residual inspection: two highest TTT3R position errors and neighbors\nSelected after scoring; images alone do not establish the cause',fontsize=11)
fig.savefig(OUT/'s21_real_residual_photos.png',dpi=160)
plt.close(fig)
(OUT/'figure_recipe.json').write_text(json.dumps(dict(type='actual scored baseline figures, not new-method evidence',all_time_series=300,local_pairs=299,photo_selection='two highest TTT3R ATE indices and immediate neighbors, post-score exploratory',photo_indices=indices,skill='figure-designer; experimental-results line plots; dual color/line coding; no invented uncertainty intervals; vector exports',font_min_pt=10),indent=2)+'\n')
print(OUT)
