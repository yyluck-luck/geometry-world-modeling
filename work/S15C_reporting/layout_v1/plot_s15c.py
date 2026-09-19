"""S15C completed-score scientific figures; fixed four real photos, no model call."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,math
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
SCORED=ROOT/'results/S15C_bonn_scores';FIXED=[4,9,14,19]
START=datetime.now(timezone.utc).isoformat()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(ok,msg):
 if not ok:raise ValueError(msg)
meta=json.loads((SCORED/'run_metadata.json').read_text());check(meta['status']=='SUCCESS','Completed scoring required')
manifest=json.loads((SCORED/'frozen_manifest.json').read_text())
check(sha(SCORED/'scores.json')==meta['output_sha256']['scores.json'],'Score JSON hash')
check(sha(SCORED/'arrays.npz')==meta['output_sha256']['arrays.npz'],'Scored arrays hash')
scores=json.loads((SCORED/'scores.json').read_text())
rows={method:{r['index']:r for r in scores['rows'] if r['method']==method} for method in ['model','constant']}
check(set(rows['model'])==set(rows['constant'])==set(range(4,20)),'Keep all sixteen frames')
with np.load(SCORED/'arrays.npz',allow_pickle=False) as z:
 gt=z['gt_depth_m'].copy();pred=z['prediction_depth_m'].copy()
check(gt.shape==(16,224,224) and pred.shape==(16,2,224,224),'Exact score arrays')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':9,'axes.labelsize':9,
                     'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'pdf.fonttype':42,'svg.fonttype':'none'})
depthcmap=plt.get_cmap('viridis').copy();depthcmap.set_bad('#dedede');depthcmap.set_over('#ffe66d')
errorcmap=plt.get_cmap('magma').copy();errorcmap.set_bad('#dedede');errorcmap.set_over('#5cc8ff')
reads=[];display_stats=[]
fig=plt.figure(figsize=(7.6,8.35))
gs=fig.add_gridspec(4,4,left=.057,right=.98,top=.922,bottom=.142,hspace=.17,wspace=.055)
for row,i in enumerate(FIXED):
 s=manifest['samples'][i];check(s['index']==i,'Source index binding');check(sha(s['rgb_path'])==s['rgb_sha256'],'Original real RGB SHA')
 entry={'index':i,'path':s['rgb_path'],'sha256':s['rgb_sha256'],'opened_utc':datetime.now(timezone.utc).isoformat(),'purpose':'POST_SCORE_VISUALIZATION_ONLY'}
 with Image.open(s['rgb_path']) as im:
  im.load();check(im.mode=='RGB' and im.size==(640,480),'Real native image schema')
  rgb=np.asarray(im.resize((299,224),Image.Resampling.LANCZOS).crop((37,0,261,224)))
 entry['decoded_utc']=datetime.now(timezone.utc).isoformat();reads.append(entry)
 k=i-4;g=gt[k];p=pred[k,0];goodg=np.isfinite(g)&(g>0);goodp=np.isfinite(p)&(p>0)
 error=np.full_like(g,np.nan);support=goodg&goodp;error[support]=np.abs(p[support]-g[support])
 panels=[rgb,np.ma.masked_where(~goodg,g),np.ma.masked_where(~goodp,p),np.ma.masked_invalid(error)]
 count=int(goodg.sum());titles=['Real RGB\n(model crop)','Sensor depth\n(valid GT only)','CUT3R depth\n(fixed history scale)','Absolute error\n(valid GT only)']
 for col in range(4):
  ax=fig.add_subplot(gs[row,col]);ax.set_xticks([]);ax.set_yticks([])
  for spine in ax.spines.values():spine.set_visible(False)
  if col==0:ax.imshow(panels[col],interpolation='nearest')
  elif col<3:im_depth=ax.imshow(panels[col],cmap=depthcmap,norm=Normalize(0,5),interpolation='nearest')
  else:im_error=ax.imshow(panels[col],cmap=errorcmap,norm=Normalize(0,1),interpolation='nearest')
  if row==0:ax.set_title(titles[col],pad=6)
  if col==0:ax.text(-.055,.5,f'Frame {i}',rotation=90,va='center',ha='right',transform=ax.transAxes,fontsize=9)
  if col==1:ax.text(.02,.035,f'GT: {count:,} / 50,176',ha='left',va='bottom',fontsize=7.5,color='black',transform=ax.transAxes,bbox={'facecolor':'white','alpha':.9,'edgecolor':'none','pad':1.8})
 display_stats.append({'index':i,'gt_valid_count':count,'depth_gt_over_5m':int(np.sum(g[goodg]>5)),
    'model_depth_over_5m':int(np.sum(p[goodp]>5)),'absolute_error_over_1m':int(np.sum(error[support]>1)),
    'gt_plot_range':[0,5],'model_plot_range':[0,5],'absolute_error_plot_range':[0,1]})
cb1=fig.colorbar(im_depth,cax=fig.add_axes([.283,.095,.427,.014]),orientation='horizontal',extend='max',ticks=[0,1,2,3,4,5])
cb1.set_label('Optical-axis depth z (m); values >5 use over-range color',fontsize=8,labelpad=3)
cb2=fig.colorbar(im_error,cax=fig.add_axes([.77,.095,.204,.014]),orientation='horizontal',extend='max',ticks=[0,.5,1])
cb2.set_label('Absolute error (m); >1 over-range',fontsize=8,labelpad=3)
fig.text(.057,.968,'S15C  |  Existing RGB-conditioned predictions versus real sensor depth',fontsize=11,fontweight='bold',ha='left')
fig.text(.057,.048,'Fixed frames 4 / 9 / 14 / 19; gray means unavailable measurement. No smoothing or selection by score.',fontsize=8)
fig.text(.057,.029,'RGB is real photography, shown at the fixed model crop. These are observed views; no new method or video generation.',fontsize=8)
for ext in ['png','pdf','svg']:fig.savefig(OUT/f's15c_fixed_four_depth.{ext}',dpi=240,facecolor='white')
plt.close(fig)
# All fixed evaluation frames; missing frame remains an explicit gap, never interpolated.
x=np.arange(4,20)
fig,(ax,lower)=plt.subplots(2,1,figsize=(7.6,5.6),sharex=True,gridspec_kw={'height_ratios':[2,1]},layout='constrained')
for method,color,marker,style,label in [('model','#0072B2','o','-','CUT3R (fixed history scale)'),('constant','#777777','s','--','Constant depth (1.853 m)')]:
 y=np.array([np.nan if rows[method][int(i)]['delta1_all_gt'] is None else 100*rows[method][int(i)]['delta1_all_gt'] for i in x])
 ax.plot(x,y,color=color,marker=marker,linestyle=style,markersize=4,linewidth=1.5,label=label)
ax.set_ylim(-3,103);ax.set_yticks([0,25,50,75,100]);ax.set_ylabel(r'$\delta_1$ on valid GT (%)')
ax.legend(loc='upper right',frameon=False);ax.grid(axis='y',color='#dddddd',linewidth=.6)
ax.axvspan(11.7,12.3,color='#dddddd',alpha=.8,zorder=0)
ax.text(12,51,'No GT\nNA',ha='center',va='center',fontsize=9,color='#4b4b4b')
ax.set_title('One empty GT frame prevents the complete 16-frame primary mean',loc='left',fontsize=11,fontweight='bold')
valid=np.array([rows['model'][int(i)]['gt_valid_count'] for i in x])
lower.bar(x,valid/50176*100,color='#56B4E9',width=.7,edgecolor='#335d70',linewidth=.5)
for i,n in zip(x,valid):lower.text(i,n/50176*100+2,f'{n:,}',ha='center',va='bottom',fontsize=6.6,rotation=60)
lower.set_ylim(0,125);lower.set_yticks([0,50,100]);lower.set_ylabel('Sensor GT available\n(% of image)');lower.set_xlabel('Fixed evaluation frame index (first four frames calibrate scale)')
lower.set_xticks(x);lower.grid(axis='y',color='#dddddd',linewidth=.6);lower.set_axisbelow(True)
for a in (ax,lower):
 a.spines['top'].set_visible(False);a.spines['right'].set_visible(False)
fig.get_layout_engine().set(h_pad=.05,hspace=.05)
for ext in ['png','pdf','svg']:fig.savefig(OUT/f's15c_all_sixteen_metrics.{ext}',dpi=240,facecolor='white')
plt.close(fig)
record={'schema':'s15c-reporting-figures-v1','started_utc':START,'completed_utc':datetime.now(timezone.utc).isoformat(),
    'status':'GENERATED_PENDING_VISUAL_INSPECTION','figure_type':'experimental-results','selection_rule':'fixed indices [4,9,14,19] from root before visualization; no best-case ranking',
    'reads':reads,'additional_real_rgb_visualization_decodes':4,'score_array_decodes':2,'sensor_png_decodes':0,'model_calls':0,
    'figures':{p.name:sha(p) for p in sorted(OUT.iterdir()) if p.suffix in ['.png','.pdf','.svg']},
    'input_identities':{str(SCORED/n):sha(SCORED/n) for n in ['run_metadata.json','frozen_manifest.json','scores.json','arrays.npz']},
    'fixed_display_limits':{'depth_m':[0,5],'absolute_error_m':[0,1],'overrange':'explicit extend=max, dedicated over color','missing':'gray','image_interpolation':'nearest for array display'},
    'display_stats':display_stats,'script_sha256':sha(__file__),
    'skill_paths':['/Users/rocket/.codex/skills/figure-designer/SKILL.md','/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md'],
    'evidence_limit':'Post-score visualization, not new model inference; pending root independent metric verification.'}
(OUT/'figure_receipt.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'GENERATED','fixed_frames':FIXED,'additional_rgb_decodes':4,'score_array_decodes':2,'output':str(OUT)},ensure_ascii=False))
