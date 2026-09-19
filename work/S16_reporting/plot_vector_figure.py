#!/usr/bin/env python3
"""Pure-vector rerender after SVG image audit; only saved figure JSON is read."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

root=Path(__file__).resolve().parents[2]
source=root/'work/S16_reporting/actual_support_and_figure/figure_values.json'
out=root/'work/S16_reporting/vector_figure_v2';out.mkdir(exist_ok=False)
start=time.monotonic();started=datetime.now(timezone.utc).isoformat()
data=json.loads(source.read_text()); policies=data['policies']
names=['All new','Half blend','Photo pool','Time split','Matched absolute','Model confidence']
matrix=np.array(data['matrix_percentage_points'])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
                     'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,
                     'pdf.fonttype':42,'svg.fonttype':'none'})
fig=plt.figure(figsize=(10.4,9.2))
gs=fig.add_gridspec(3,3,height_ratios=[1.28,1,1],hspace=.67,wspace=.27)
ax=fig.add_subplot(gs[0,:])
im=ax.pcolormesh(np.arange(5)-.5,np.arange(7)-.5,matrix,cmap='RdBu',
                 norm=TwoSlopeNorm(vmin=-2.1,vcenter=0,vmax=2.1),rasterized=False)
ax.set_xlim(-.5,3.5);ax.set_ylim(5.5,-.5)
ax.set_yticks(range(6),names)
ax.set_xticks(range(4),['Total interaction I','Fixed candidate IDs','Source-pixel routing','Source coverage'])
ax.tick_params(top=False,bottom=False,left=False)
ax.set_title('(a) Interaction and its three additive spatial contributions',loc='left',pad=10)
for r in range(6):
 for c in range(4):
  value=f'{matrix[r,c]:+.3f}' if matrix[r,c] else '0.000'
  ax.text(c,r,value,ha='center',va='center',fontsize=9,color='white' if abs(matrix[r,c])>1.2 else '#202020')
cb=fig.colorbar(im,ax=ax,fraction=.025,pad=.025)
cb.set_label('Delta1 percentage points')
cb.solids.set_rasterized(False)
all_values=[100*m[key] for name in policies for m in data['marginals'][name]
            for key in ['single_mean_delta1','joint_marginal_mean_delta1']]
limit=max(abs(v) for v in all_values)*1.18
for index,(name,label) in enumerate(zip(policies,names)):
 current=fig.add_subplot(gs[1+index//3,index%3]); m=data['marginals'][name]
 single=np.array([x['single_mean_delta1'] for x in m])*100
 joint=np.array([x['joint_marginal_mean_delta1'] for x in m])*100
 x=np.arange(4)
 a=current.bar(x-.19,single,width=.36,color='#0072B2',edgecolor='#003A5E')
 b=current.bar(x+.19,joint,width=.36,color='#E69F00',edgecolor='#764D00')
 current.axhline(0,color='#333333',lw=.8);current.set_ylim(-limit,limit)
 current.set_yticks([-1,-.5,0,.5,1]);current.set_xticks(x,['0','3','6','9'])
 current.set_xlabel('Source frame')
 if index%3==0: current.set_ylabel('Delta1 gain (pp)')
 current.set_title(f'({chr(98+index)}) {label}',loc='left')
 current.grid(axis='y',color='#DADADA',linewidth=.5);current.set_axisbelow(True)
 current.spines[['top','right']].set_visible(False)
 for xi,si,ji in zip(x,single,joint):
  current.plot(xi-.19,si,'o',color='#003A5E',ms=3)
  current.plot(xi+.19,ji,'s',color='#764D00',ms=3)
fig.legend([a,b],['Single: others stay old (circle)','Joint marginal: others updated (square)'],
           loc='lower center',bbox_to_anchor=(.5,.05),ncol=2,frameon=False,fontsize=9)
fig.text(.5,.025,'Saved-data diagnosis | Four target frames, equal weight | Aggregate gains, not pixel-level sign reversals',ha='center',fontsize=9)
fig.subplots_adjust(left=.16,right=.95,top=.95,bottom=.15)
for suffix in ['pdf','svg','png']:
 fig.savefig(out/f's16_interaction_summary.{suffix}',dpi=180,facecolor='white')
plt.close(fig)
assert '<image' not in (out/'s16_interaction_summary.svg').read_text()
assert b'/Subtype /Image' not in (out/'s16_interaction_summary.pdf').read_bytes()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=dict(status='PASS',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),
       elapsed_seconds=time.monotonic()-start,reason='Replace imshow embedded raster with vector mesh; data unchanged.',
       source_sha256=sha(__file__),input_figure_values_sha256=sha(source),npz_reads=0,rgb_decodes=0,sensor_png_decodes=0,model_calls=0,
       svg_image_elements=0,pdf_image_subtypes=0,
       outputs={p.name:sha(p) for p in out.iterdir() if p.is_file()})
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
