#!/usr/bin/env python3
"""Render two fixed S17B real RGBs and self-z only after root-approved SUCCESS.
No new inference, GT, calibration, confidence filtering or other RGBs.
"""
from pathlib import Path
import argparse, hashlib, json, datetime, shutil
import numpy as np
from PIL import Image, ImageOps
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

EXPECTED_SHA=[
 '7caa6f1b9fd1ac5b6938812682c55e3d7926a1348c7554c23e1012b47759cc39',
 '77bebdb3ac737221ef05a4404a1124676bcff536dbffdbb6e197b59bcdf811ae',
]
DEPTH_UPPER_MODEL_UNITS=5.0

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def draw(raw,processed,zs,out):
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':9,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
 fig,axs=plt.subplots(2,3,figsize=(7.6,5.65))
 fig.subplots_adjust(left=.04,right=.985,top=.82,bottom=.21,wspace=.05,hspace=.12)
 cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#d5d8dd');cmap.set_over('#fde725')
 for i in range(2):
  axs[i,0].imshow(raw[i]);axs[i,1].imshow(processed[i])
  valid=np.isfinite(zs[i])&(zs[i]>0)
  heat=axs[i,2].imshow(np.ma.array(zs[i],mask=~valid),vmin=0,vmax=DEPTH_UPPER_MODEL_UNITS,cmap=cmap)
  axs[i,0].text(.025,.055,f'Frame {i}',transform=axs[i,0].transAxes,color='white',fontsize=9,bbox={'facecolor':'black','alpha':.65,'edgecolor':'none','pad':2})
  for ax in axs[i]:ax.set_xticks([]);ax.set_yticks([]);[sp.set_visible(False)for sp in ax.spines.values()]
 for ax,title in zip(axs[0],['Original RGB | 640 × 480','Model input | 512 × 384','512 DPT self-z | model units']):ax.set_title(title,pad=6)
 cbax=fig.add_axes([.66,.16,.30,.018]);cb=fig.colorbar(heat,cax=cbax,orientation='horizontal',extend='max',ticks=[0,1,2,3,4,5]);cb.ax.tick_params(labelsize=9,length=2)
 fig.suptitle('S17B | Two fixed real photos through the 512 DPT checkpoint',x=.04,y=.969,ha='left',fontsize=11,fontweight='bold')
 fig.text(.04,.912,'Bonn indices 0 / 1, already observed in S15A. Same full image extent; no 224 crop.',fontsize=9)
 fig.text(.04,.086,'Self-z uses one fixed 0–5 scale for both frames; upper triangle marks values above 5.',fontsize=9)
 fig.text(.04,.048,'No metric calibration or GT: this is predicted geometry, not a depth-error or video result.',fontsize=9)
 for ext in ['png','pdf','svg']:fig.savefig(out/f's17b_two_photos_dpt_depth.{ext}',dpi=220,facecolor='white')
 plt.close(fig)

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--run-dir',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 require(not args.output.exists(),'Fresh reporting output directory required');args.output.mkdir(parents=True)
 report={'schema':'s17b-reporting-run-v1','status':'RUNNING','started_utc':utc(),'rgb_decodes':0,'pointmap_array_decodes':0,'gt_depth_decodes':0,'model_calls':0,'other_rgb_decodes':0,'metric_scale_fit':False,'video_generated':False,'input_ids':[]}
 try:
  for path,role in [(args.manifest,'frozen_manifest'),(args.run_dir/'run_metadata.json','completed_run_metadata')]:
   report['input_ids'].append({'path':str(path.resolve()),'role':role,'sha256':sha(path)})
  m=json.loads(args.manifest.read_text());meta=json.loads((args.run_dir/'run_metadata.json').read_text())
  require(meta['status']=='SUCCESS' and meta['before_after_identity_pass'],'Real run must complete successfully before reading predictions or images')
  require(m['schema']=='s17b-dpt-two-frame-manifest-v1' and meta['manifest_sha256']==sha(args.manifest),'Manifest binding')
  require([x['index']for x in m['history_images']]==[0,1] and [x['sha256']for x in m['history_images']]==EXPECTED_SHA,'Only predeclared original frames 0/1')
  pred=args.run_dir/'predictions.npz';require(sha(pred)==meta['output_sha256']['predictions.npz'],'Sealed prediction identity')
  report['input_ids'].append({'path':str(pred.resolve()),'role':'completed_saved_pointmaps_only_self_z_consumed','sha256':sha(pred)})
  raw=[];processed=[];zs=[];stats=[]
  # PNGs are opened exactly once each. Resize/crop matches the known non-square official size512 transform.
  with np.load(pred,allow_pickle=False)as store:
   for i,item in enumerate(m['history_images']):
    p=Path(item['path']);require(sha(p)==item['sha256'],'RGB changed')
    with Image.open(p)as image:
     require(image.size==(640,480)and image.mode=='RGB','Original RGB identity/shape');image.load();report['rgb_decodes']+=1
     raw.append(np.array(image));image=ImageOps.exif_transpose(image).convert('RGB')
     # 640x480 -> 512x384, no further crop since both dimensions divide by16.
     processed.append(np.array(image.resize((512,384),Image.Resampling.LANCZOS)))
    a=store[f'frame{i}_pts3d_in_self_view'];report['pointmap_array_decodes']+=1
    require(a.shape==(1,384,512,3)and a.dtype==np.float32,'Frozen self-pointmap shape/dtype');z=a[0,:,:,2].copy();zs.append(z)
    valid=np.isfinite(z)&(z>0);v=z[valid]
    stats.append({'index':i,'original_w_h':[640,480],'processed_w_h':[512,384],'positive_finite_count':int(valid.sum()),'total_pixels':int(z.size),'minimum_positive_model_units':float(v.min())if len(v)else None,'maximum_positive_model_units':float(v.max())if len(v)else None,'above_fixed_display_upper_count':int((valid&(z>DEPTH_UPPER_MODEL_UNITS)).sum()),'display_range_model_units':[0,DEPTH_UPPER_MODEL_UNITS]})
    report['input_ids'].append({'path':str(p.resolve()),'role':'additional_visualization_decode_only','sha256':item['sha256']})
  report['depth_display_statistics']=stats;draw(raw,processed,zs,args.output)
  shutil.copy2(__file__,args.output/'plot_source_snapshot.py');report.update(status='SUCCESS_PLOT_AWAIT_VISUAL_QA',completed_utc=utc(),matplotlib_version=matplotlib.__version__)
  report['outputs']={p.name:sha(p)for p in args.output.iterdir()if p.is_file()}
 except BaseException as e:
  report.update(status='FAILED',completed_utc=utc(),error=repr(e));save(args.output/'plot_receipt.json',report);raise
 save(args.output/'plot_receipt.json',report)
 return 0
if __name__=='__main__':raise SystemExit(main())
