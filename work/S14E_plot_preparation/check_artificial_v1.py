#!/usr/bin/env python3
"""Prepare-only synthetic figure and gate checks. No real photos or scoring data."""
from pathlib import Path
import importlib.util,sys,subprocess,json,csv
from datetime import datetime,timezone
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('plotter',ROOT/'scripts/plot_s14e_depth.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
OUT=Path(__file__).resolve().parent/'artificial_v1'
if OUT.exists():raise ValueError('Use fresh artificial directory')
OUT.mkdir();fixture=OUT/'fixture';fixture.mkdir();score=fixture/'score';score.mkdir();dataset=fixture/'fabricated_dataset';(dataset/'rgb').mkdir(parents=True)
checks=[]
def check(name,ok):
 if not ok:raise AssertionError(name)
 checks.append(dict(name=name,passed=True))
y,x=np.indices((224,224));gt=np.stack([.5+.002*x+.003*y+i*.25 for i in range(4)]).astype(np.float64)
pred=np.stack([gt*1.1,gt*.95,np.broadcast_to(np.median(gt),(4,224,224))],axis=1).copy()
pred[:,1,50:90,30:130]=np.nan
r=p.full_depth_range(gt,pred)
check('all16 maps and full values included',len(r['per_map'])==16 and r['all_depth_values']==16*224*224)
check('range finite positive exact',r['data_range_m']==[float(np.nanmin(np.r_[gt.ravel(),pred.ravel()])),float(np.nanmax(np.r_[gt.ravel(),pred.ravel()]))])
extreme=pred.copy();extreme[2,0,0,0]=1000
check('large depth cannot be clipped',p.full_depth_range(gt,extreme)['data_range_m'][1]==1000)
constant=p.full_depth_range(np.ones_like(gt),np.ones_like(pred))
check('singular range transparently expanded',constant['data_range_m']==[1,1] and constant['display_range_m']==[0,2] and constant['singular_range_expanded'])
rows=[]
for q in p.QUERIES:
 for i,m in enumerate(p.METHODS):rows.append(dict(query_index=q,target_index=q-20,model_call=q-19,method=m,gt_valid_count=50176,own_valid_count=50176 if i!=1 else 46176,delta1_all_gt=.7-.1*i,coverage=1. if i!=1 else 46176/50176,own_mae_m=.1+i*.03,common_mae_m=.12+i*.01))
metrics=dict(schema='s14e-depth-metrics-v1',query_order=p.QUERIES,method_order=p.METHODS,rows=rows,source_seal_sha256='0'*64)
p.write(score/'metrics.json',metrics);np.savez_compressed(score/'arrays.npz',gt_depth_m=gt,prediction_depth_m=pred,not_read_object=np.array([{'not_decoded':True}],dtype=object))
frames=[];targets=[];rgbtargets=[]
for i in range(24):
 rgbrel=f'rgb/{i}.png';depthrel=f'depth/{i}.png';rgbsha='f'*64
 if i>=20:
  yy,xx=np.indices((480,640));pixels=np.stack([(xx+i*30)%256,(yy+80)%256,((xx//50+yy//50)%2)*180+40],axis=-1).astype(np.uint8)
  Image.fromarray(pixels).save(dataset/rgbrel);rgbsha=p.sha(dataset/rgbrel)
  targets.append(dict(query_index=i,depth_path=str(dataset/depthrel),depth_sha256='a'*64))
  rgbtargets.append(dict(query_index=i,rgb_path=str(dataset/rgbrel),rgb_sha256=rgbsha))
 frames.append(dict(frame=i,rgb=dict(timestamp=float(i),path=rgbrel),depth=dict(timestamp=float(i)+.01,path=depthrel),rgb_sha256=rgbsha,depth_sha256='a'*64))
frozen=fixture/'frozen_inputs.json';p.write(frozen,dict(schema='s8-inputs-v1',blocks=[dict(block=0,frames=frames)]))
sm=fixture/'score_manifest.json';p.write(sm,dict(schema='s14e-score-manifest-v1',targets=targets))
(score/'frozen_manifest.json').write_bytes(sm.read_bytes())
meta=dict(schema='s14e-depth-score-run-v1',status='SUCCESS',result_rows=12,counters=dict(depths_decoded=4,target_rgb_decoded=0),before_after_identity_pass=True,completed_utc='2026-01-01T00:00:00+00:00',prediction_seal_sha256='0'*64,manifest_sha256=p.sha(sm),output_sha256={name:p.sha(score/name) for name in ['arrays.npz','metrics.json','frozen_manifest.json']})
meta_path=score/'run_metadata.json';p.write(meta_path,meta)
rm=fixture/'rgb_manifest.json';p.write(rm,dict(schema='s14e-report-rgb-manifest-v1',scope='artificial_layout_only',frozen_inputs=str(frozen),frozen_inputs_sha256=p.sha(frozen),dataset_root=str(dataset),targets=rgbtargets))
command=[sys.executable,str(ROOT/'scripts/plot_s14e_depth.py'),'--score-dir',str(score),'--score-manifest',str(sm),'--score-metadata-sha256',p.sha(meta_path),'--rgb-manifest',str(rm),'--output',str(OUT/'layout')]
proc=subprocess.run(command,capture_output=True,text=True);(OUT/'layout_stdout.txt').write_text(proc.stdout);(OUT/'layout_stderr.txt').write_text(proc.stderr)
if proc.returncode:raise RuntimeError(proc.stderr)
receipt=json.loads((OUT/'layout/figure_receipt.json').read_text())
check('full artificial report success',receipt['status']=='SUCCESS')
check('only two score arrays decoded',receipt['counters']['npz_arrays_decoded']==2)
check('four artificial RGB decoded',receipt['counters']['rgb_decoded']==4)
check('all12 exact CSV rows',list(csv.DictReader((OUT/'layout/all_12_scores.csv').open()))==[{k:str(v) for k,v in row.items()} for row in rows])
check('SVG and PNG exist',all((OUT/f'layout/s14e_all_four_targets.{ext}').exists() for ext in ['svg','png']))
check('receipt payload hashes',all(p.sha(OUT/'layout'/name)==digest for name,digest in receipt['output_sha256'].items()))
# Successful-looking payloads must not bypass a FAILED score status.
meta['status']='FAILED';p.write(meta_path,meta)
command[command.index('--score-metadata-sha256')+1]=p.sha(meta_path)
command[command.index('--output')+1]=str(OUT/'failed_score_gate')
proc=subprocess.run(command,capture_output=True,text=True);(OUT/'failed_score_stdout.txt').write_text(proc.stdout);(OUT/'failed_score_stderr.txt').write_text(proc.stderr)
failed=json.loads((OUT/'failed_score_gate/figure_receipt.json').read_text())
check('FAILED score blocks report',proc.returncode==1 and failed['status']=='FAILED')
check('FAILED score no photo hash/open/decode',failed['counters']['rgb_open_attempts']==failed['counters']['rgb_decoded']==0 and not any(h['role']=='post-score reference RGB' for h in failed['hashes']))
check('FAILED score no array decode',failed['counters']['npz_arrays_decoded']==0)
p.write(OUT/'receipt.json',dict(schema='s14e-plot-artificial-v1',status='PASS',completed_utc=datetime.now(timezone.utc).isoformat(),check_count=len(checks),checks=checks,real_score_array_reads=0,real_target_photo_reads=0,real_depth_reads=0,model_calls=0,production_source_sha256=p.sha(ROOT/'scripts/plot_s14e_depth.py')))
print(json.dumps(dict(status='PASS',check_count=len(checks),preview=str(OUT/'layout/s14e_all_four_targets.png'))))
