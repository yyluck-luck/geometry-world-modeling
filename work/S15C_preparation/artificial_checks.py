"""Artificial-only S15C boundary and mode checks; never read real data arrays."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import sys, json, hashlib, importlib.util, subprocess, tempfile
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/'scripts/s15c_observed_depth.py'
spec=importlib.util.spec_from_file_location('s15c',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
started=datetime.now(timezone.utc).isoformat();checks=[]
def check(name,condition,**details):
 checks.append(dict(name=name,passed=bool(condition),**details));assert condition,name
p=np.arange(1.,9.).reshape(4,1,2);g=np.ones_like(p)
c=m.calibration_values(p,g)
check('pooled even median is 4.5 not average of ratios or frame fitted scales',c['s_model_per_meter']==4.5)
# Pooled median must differ from median of per-frame medians.
p=np.array([[[1.,1.,1.]],[[2.,np.nan,np.nan]],[[9.,np.nan,np.nan]],[[10.,np.nan,np.nan]]]);g=np.ones_like(p)
c=m.calibration_values(p,g)
check('unequal valid frame counts still pool pixels',c['s_model_per_meter']==1.5 and c['ratio_count']==6)
p=np.ones((4,1,2));g=np.array([[[1.,9.]],[[1.,1.]],[[1.,1.]],[[1.,1.]]]);p[0,0,1]=np.nan
c=m.calibration_values(p,g);check('constant uses positive GT even where prediction missing',c['positive_gt_count']==8 and c['ratio_count']==7)
p[2]=np.nan
try:m.calibration_values(p,g);bad=False
except ValueError:bad=True
check('one calibration frame with zero valid pairs fails',bad)
gt=np.array([[1.,1.,1.,0.]]);pred=np.array([[[1.,1.25,np.nan,1.]],[[1.,1.,1.,1.]]])
rows,a=m.compute_metrics(gt,pred,4)
check('delta strict 1.25 equality fails and missing remains denominator',rows[0]['delta1_success_count']==1 and rows[0]['gt_valid_count']==3 and rows[0]['coverage']==2/3)
check('common domain excludes model missing',rows[0]['common_valid_count']==2 and rows[1]['common_valid_count']==2)
rows,a=m.compute_metrics(np.array([[27/5000.]]),np.array([[[.00675]],[[.00675]]]),4)
expected=(max(.00675/(27/5000.),(27/5000.)/.00675)<1.25)
check('quotient boundary follows declared floating calculation',rows[0]['delta1_success_count']==int(expected))
rows,a=m.compute_metrics(np.zeros((1,2)),np.ones((2,1,2)),4)
check('empty GT is explicit None not invented zero',rows[0]['delta1_all_gt'] is None and rows[0]['own_mae_m'] is None)
full=[]
for i in range(4,20):
 rr,_=m.compute_metrics(np.zeros((1,2)) if i==8 else np.ones((1,2)),np.ones((2,1,2)),i);full+=rr
means=m.equal_frame_means(full)
check('missing frame invalidates primary 16-frame mean',means[0]['means']['delta1_all_gt'] is None and means[0]['contributing_frame_counts']['delta1_all_gt']==15)
# A full artificial 640x480 PNG path validates routing, identity gates, and exact 20+2 array decodes.
base=Path(tempfile.mkdtemp(prefix='artificial_s15c_',dir=ROOT/'work/S15C_preparation'))
source=base/'history';source.mkdir();imgdir=base/'images';imgdir.mkdir();depthdir=base/'depth';depthdir.mkdir()
oldtime=datetime.now(timezone.utc)-timedelta(seconds=20)
samples=[];history=[];preds={}
for i in range(20):
 rgb=imgdir/f'{i}.png';rgb.write_bytes(f'ARTIFICIAL RGB HASH CANARY {i}'.encode())
 depth=depthdir/f'{i}.png';raw=np.full((480,640),10000+i*100,dtype=np.uint16);Image.fromarray(raw).save(depth)
 samples.append(dict(index=i,rgb_path=str(rgb),rgb_sha256=sha(rgb),rgb_timestamp=1000.+i*.4,depth_path=str(depth),depth_sha256=sha(depth),depth_timestamp=1000.+i*.4+.001))
 history.append(dict(index=i,path=str(rgb),sha256=sha(rgb)))
 xyz=np.zeros((1,224,224,3),dtype=np.float32);xyz[...,2]=2*((10000+i*100)/5000.)
 preds[f'frame{i}_pts3d_in_self_view']=xyz
preds['frame0_conf_self']=np.array(['DO NOT DECODE OTHER HEAD'],dtype=object)
np.savez_compressed(source/'predictions.npz',**preds)
original=base/'history_manifest.json';write(original,dict(schema='s15-history-manifest-v1',history_images=history))
write(source/'run_metadata.json',dict(schema='s15-history-run-v1',status='SUCCESS',completed_utc=oldtime.isoformat(),manifest_sha256=sha(original),output_sha256={'predictions.npz':sha(source/'predictions.npz')}))
ids={str(p):sha(p) for p in [source/'predictions.npz',source/'run_metadata.json',original,*imgdir.glob('*.png')]}
seal=base/'history_seal.json';write(seal,dict(schema='s15a-history-combined-seal-v1',sealed_utc=(oldtime+timedelta(seconds=1)).isoformat(),identities=ids,run_dir=str(source),manifest=str(original)))
control=base/'artificial_protocol.md';control.write_text('ARTIFICIAL SOFTWARE CHECK ONLY\n')
manifest=base/'stage_manifest.json'
newids={str(p):sha(p) for p in [SCRIPT,seal,control,*depthdir.glob('*.png')]}
write(manifest,dict(schema='s15c-observed-depth-manifest-v1',frozen_utc=(oldtime+timedelta(seconds=2)).isoformat(),runner=str(SCRIPT),python=sys.executable,history_seal=str(seal),history_seal_sha256=sha(seal),history_predictions=str(source/'predictions.npz'),history_metadata=str(source/'run_metadata.json'),controls=[str(control)],identities=newids,samples=samples,contract=m.EXPECTED_CONTRACT))
def run(mode,out,extra=()):
 cmd=[sys.executable,str(SCRIPT),mode,'--manifest',str(manifest),'--manifest-sha256',sha(manifest),'--output',str(out),*extra]
 proc=subprocess.run(cmd,capture_output=True,text=True,timeout=40)
 (base/(out.name+'_stdout.txt')).write_text(proc.stdout);(base/(out.name+'_stderr.txt')).write_text(proc.stderr)
 return proc,json.loads((out/'run_metadata.json').read_text())
caldir=base/'calibrate'
proc,meta=run('calibrate',caldir)
check('artificial full calibrate succeeds',proc.returncode==0,status=meta['status'],error=meta.get('error'))
check('calibrate decodes 20 self pointmaps and four depth, no RGB/model',meta['counters']['npz_arrays_decoded']==20 and meta['counters']['depths_decoded']==4 and meta['counters']['rgb_decodes']==0 and meta['counters']['model_calls']==0)
evalpaths={s['depth_path'] for s in samples[4:]}
check('calibrate does not hash or open any evaluation depth',not evalpaths & {x['path'] for x in meta['identity_hashes']+meta['reads']})
cal=json.loads((caldir/'calibration.json').read_text());check('artificial scale close to two',abs(cal['s_model_per_meter']-2)<1e-6)
pseal=base/'prediction_seal.json';pids={str(p):sha(p) for p in caldir.rglob('*') if p.is_file()}
write(pseal,dict(schema='s15c-calibrated-prediction-seal-v1',sealed_utc=datetime.now(timezone.utc).isoformat(),manifest=str(manifest),manifest_sha256=sha(manifest),calibration_dir=str(caldir),identities=pids))
proc,scoremeta=run('score',base/'score',['--prediction-seal',str(pseal),'--prediction-seal-sha256',sha(pseal)])
check('artificial full score succeeds',proc.returncode==0,status=scoremeta['status'],error=scoremeta.get('error'))
check('score decodes only two calibrated arrays and sixteen depth',scoremeta['counters']['npz_arrays_decoded']==2 and scoremeta['counters']['depths_decoded']==16)
sc=json.loads((base/'score/scores.json').read_text());check('all 32 rows present and artificial model delta1 perfect',len(sc['rows'])==32 and sc['means'][0]['means']['delta1_all_gt']==1.)
proc,badmeta=run('score',base/'bad_seal',['--prediction-seal',str(pseal),'--prediction-seal-sha256','0'*64])
check('bad external prediction seal fails before depth or NPZ decode',proc.returncode==1 and badmeta['counters']['depths_decoded']==0 and badmeta['counters']['npz_arrays_decoded']==0)
extra=base/'outside_answer_canary.txt';extra.write_text('ARTIFICIAL OUTSIDE IDENTITY MUST NOT BE READ')
malformed=json.loads(pseal.read_text());malformed['identities'][str(extra)]=sha(extra)
badseal=base/'extra_identity_seal.json';write(badseal,malformed)
proc,badmeta=run('score',base/'outside_identity',['--prediction-seal',str(badseal),'--prediction-seal-sha256',sha(badseal)])
check('outside prediction-seal identity rejected before its byte read',proc.returncode==1 and str(extra) not in {x['path'] for x in badmeta['identity_hashes']} and badmeta['counters']['depths_decoded']==0)
# A changed PNG remains unopened when its immutable checksum disagrees.
with (depthdir/'19.png').open('ab') as f:f.write(b'ARTIFICIAL TAMPER')
proc,badmeta=run('score',base/'changed_depth',['--prediction-seal',str(pseal),'--prediction-seal-sha256',sha(pseal)])
check('changed eval depth identity fails before decoding',proc.returncode==1 and badmeta['counters']['depths_decoded']==0)
# Source native dtype test executes only on a generated 8-bit PNG.
eight=base/'artificial_8bit.png';Image.fromarray(np.ones((480,640),dtype=np.uint8)).save(eight)
out=base/'dtype_only';out.mkdir();rec=m.Recorder(out,'calibrate')
try:rec.depth({'index':0,'depth_path':str(eight)});rejected=False
except ValueError:rejected=True
check('8-bit depth PNG rejected',rejected)
result=dict(schema='s15c-artificial-checks-v1',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),status='PASS',
    evidence_kind='ARTIFICIAL_CODE_TESTS_ONLY',real_png_decodes=0,real_npz_decodes=0,model_calls=0,
    checks=checks,check_count=len(checks),fixture=str(base),script_sha256=sha(SCRIPT),test_source_sha256=sha(__file__))
write(ROOT/'work/S15C_preparation/artificial_checks.json',result)
print(json.dumps({'status':'PASS','checks':len(checks),'fixture':str(base),'script_sha256':sha(SCRIPT)}))
