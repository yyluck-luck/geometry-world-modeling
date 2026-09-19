#!/usr/bin/env python3
"""Different numerical path for the seven sealed S15B consumers and four scored GTs.

The verifier author improved producer input guards but did not author the original
render/statistics core. This is an internal different-path recomputation, not an
external team replication. No producer functions are imported.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,math,resource,signal,sys,time,traceback
import numpy as np
from PIL import Image

METHODS=['never','all_new','half_blend','pool_new','split_new','matched_absolute_new','model_confidence']
SOURCE_IDS=[0,3,6,9]
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def need(ok,message):
    if not ok:raise ValueError(message)

def render_components(z,eligible,source,target,K,scale):
    """Component pinhole/pose math, then minimum.at z and separate identity reduction."""
    n,h,w=z.shape;rows,cols=np.indices((h,w),dtype=np.float64)
    normalized_x=(cols-float(K[0,2]))/float(K[0,0])
    normalized_y=(rows-float(K[1,2]))/float(K[1,1])
    worlds=[]
    for s in range(n):
        x=normalized_x*z[s];y=normalized_y*z[s];zz=z[s]
        world=np.stack([source[s,k,0]*x+source[s,k,1]*y+source[s,k,2]*zz+source[s,k,3] for k in range(3)],axis=-1)
        worlds.append(world)
    world=np.stack(worlds).reshape(-1,3)
    delta=[world[:,k]-target[k,3] for k in range(3)]
    camera=[target[0,k]*delta[0]+target[1,k]*delta[1]+target[2,k]*delta[2] for k in range(3)]
    with np.errstate(divide='ignore',invalid='ignore',over='ignore'):
        continuous_x=K[0,0]*(camera[0]/camera[2])+K[0,2]
        continuous_y=K[1,1]*(camera[1]/camera[2])+K[1,2]
        col=np.floor(continuous_x+.5);row=np.floor(continuous_y+.5)
    keep=eligible.ravel()&np.isfinite(np.stack(camera)).all(axis=0)&(camera[2]>0)&np.isfinite(col)&np.isfinite(row)&(col>=0)&(col<w)&(row>=0)&(row<h)
    identities=np.flatnonzero(keep);pixels=row[keep].astype(np.int64)*w+col[keep].astype(np.int64);depth=camera[2][keep]
    minimum=np.full(h*w,np.inf);np.minimum.at(minimum,pixels,depth)
    on_minimum=depth==minimum[pixels]
    missing_identity=n*h*w
    winner=np.full(h*w,missing_identity,dtype=np.int64)
    np.minimum.at(winner,pixels[on_minimum],identities[on_minimum])
    valid=np.isfinite(minimum)
    prediction=np.zeros(h*w);prediction[valid]=minimum[valid]/scale
    winner[~valid]=-1
    return prediction.reshape(h,w),winner.reshape(h,w),int(keep.sum())

def confidence_by_fsum(old,new):
    out=np.zeros((4,224,224),dtype=bool)
    for s in range(4):
        for r in range(0,224,16):
            for c in range(0,224,16):
                sl=(s,slice(r,r+16),slice(c,c+16))
                a=math.fsum(map(float,old[sl].ravel()))/256
                b=math.fsum(map(float,new[sl].ravel()))/256
                out[sl]=b>a
    return out

def statistics(p,g,valid):
    indices=np.flatnonzero(valid);a=p.ravel();b=g.ravel();n=len(indices)
    if not n:return dict(count=0,mae_m=None,abs_rel=None,rmse_m=None)
    differences=[float(a[i])-float(b[i]) for i in indices]
    return dict(count=n,mae_m=math.fsum(abs(x) for x in differences)/n,
        abs_rel=math.fsum(abs(d)/float(b[i]) for d,i in zip(differences,indices))/n,
        rmse_m=math.sqrt(math.fsum(d*d for d in differences)/n))

def score_fsum(predictions,gt):
    rows=[]
    for q in range(4):
        g=gt[q];valid_gt=np.isfinite(g)&(g>0);n=int(valid_gt.sum())
        valid_predictions=np.isfinite(predictions[:,q])&(predictions[:,q]>0)
        common=valid_gt.copy()
        for k in range(7):common&=valid_predictions[k]
        for k,name in enumerate(METHODS):
            p=predictions[k,q];own=valid_gt&valid_predictions[k];indices=np.flatnonzero(own)
            pp=p.ravel();gg=g.ravel()
            correct=sum(max(float(pp[i])/float(gg[i]),float(gg[i])/float(pp[i]))<1.25 for i in indices)
            rows.append(dict(method=name,target_index=20+q,gt_valid=n,prediction_valid_on_gt=len(indices),
                correct_delta1=correct,coverage=len(indices)/n if n else None,delta1_all_gt=correct/n if n else None,
                own=statistics(p,g,own),common=statistics(p,g,common)))
    summary={}
    def average(values):return None if any(v is None for v in values) else math.fsum(values)/4
    for name in METHODS:
        rr=[row for row in rows if row['method']==name]
        summary[name]={key:average([row[key] for row in rr]) for key in ['delta1_all_gt','coverage']}
        for domain in ['own','common']:
            for key in ['mae_m','abs_rel','rmse_m']:
                summary[name][domain+'_'+key]=average([row[domain][key] for row in rr])
        denominator=sum(row['gt_valid'] for row in rr)
        summary[name]['pixel_weighted_delta1']=sum(row['correct_delta1'] for row in rr)/denominator if denominator else None
    return rows,summary

def execute(a):
    out=Path(a.output);need(not out.exists(),'fresh verification output');out.mkdir(parents=True)
    started=time.monotonic();r=dict(schema='s15b-consumer-independent-verification-v1',status='RUNNING',started_utc=utc(),
        independence='Author improved producer input guards; original mathematical core by root. Internal different-path numeric recomputation, not external-team replication.',
        actual_model_calls=0,rgb_decodes=0,gt_depth_decodes=0,array_decodes=0,checks=[],tolerances=dict(atol=1e-10,rtol=1e-10,identity='exact'),
        python=sys.executable,numpy_version=np.__version__)
    frozen={}
    def check(name,ok,detail=None):
        r['checks'].append(dict(name=name,status='PASS' if ok else 'FAIL',detail=detail))
        write(out/'verification.json',r);need(ok,name)
    def bind(path,expected=None):
        path=str(Path(path).resolve());digest=sha(path)
        if expected is not None:check('SHA '+path,digest==expected)
        if path in frozen:check('repeated identity '+path,frozen[path]==digest)
        frozen[path]=digest;return Path(path)
    def load(path,keys):
        path=Path(path);need(str(path.resolve()) in frozen,'array input not frozen')
        values={}
        with np.load(path,allow_pickle=False) as z:
            for key in keys:values[key]=z[key];r['array_decodes']+=1
        return values
    def compare_tree(got,expected,path='statistics'):
        if isinstance(expected,dict):
            check(path+' keys',set(got)==set(expected))
            for key in expected:compare_tree(got[key],expected[key],path+'.'+key)
        elif isinstance(expected,list):
            check(path+' length',len(got)==len(expected))
            for index,(x,y) in enumerate(zip(got,expected)):compare_tree(x,y,path+f'[{index}]')
        elif isinstance(expected,float):check(path,math.isclose(float(got),expected,abs_tol=1e-10,rel_tol=1e-10),dict(got=got,expected=expected))
        else:check(path,got==expected)
    def timeout(*args):raise TimeoutError('600-second independent verification budget')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(600)
    try:
        manifest_path=bind(a.manifest,a.manifest_sha256);m=json.loads(manifest_path.read_text())
        check('manifest fixed schema/methods',m['schema']=='s15b-consumer-manifest-v1' and m['methods']==METHODS)
        seal_path=bind(a.prediction_seal,a.prediction_seal_sha256);seal=json.loads(seal_path.read_text())
        check('prediction seal schema/manifest',seal['schema']=='s15b-consumer-prediction-seal-v1' and seal['manifest_sha256']==a.manifest_sha256)
        prediction_dir=Path(seal['prediction_dir']).resolve();score_dir=Path(a.score_dir).resolve()
        check('exact sealed prediction directory',set(seal['identities'])=={str(p) for p in prediction_dir.iterdir() if p.is_file()})
        for path,digest in seal['identities'].items():bind(path,digest)
        for path in score_dir.iterdir():
            if path.is_file():bind(path)
        score_run=json.loads((score_dir/'run_metadata.json').read_text())
        prediction_run=json.loads((prediction_dir/'run_metadata.json').read_text())
        check('both real phases completed before any array/GT read',score_run['status']==prediction_run['status']=='PASS' and score_run['mode']=='score' and prediction_run['mode']=='predict')
        check('score manifest and prediction seal binding',score_run['manifest_sha256']==a.manifest_sha256 and score_run['prediction_seal_sha256']==a.prediction_seal_sha256)
        check('same prediction manifest',prediction_run['manifest_sha256']==a.manifest_sha256)
        check('exact scored four target order',[x['index'] for x in m['target_depths']]==[20,21,22,23])
        for directory in [prediction_dir,score_dir]:
            bind(directory/'frozen_manifest.json',a.manifest_sha256);bind(directory/'source_snapshot.py',m['runner_sha256'])
        for path,digest in m['predict_identities'].items():bind(path,digest)
        for sample in m['target_depths']:bind(sample['path'],sample['sha256'])
        bind(__file__)
        write(out/'input_snapshot.json',dict(frozen_utc=utc(),identities=frozen,arrays_decoded=0,gt_decoded=0))
        p=load(m['proposals'],['source_indices','source_poses','K','s_model_per_metric','old_self_z_model','new_self_z_model','old_conf_self','new_conf_self'])
        b=load(m['bridge'],['old_self_z','new_self_z','source_c2w','K','scale_model_per_meter'])
        t=load(m['target_cameras'],['target_c2w','K','scale_model_per_meter'])
        masks=load(m['rule_masks'],['pool_new','split_new','matched_absolute_new'])
        saved=load(prediction_dir/'target_predictions.npz',['depth_m','source_pixel_identity','source_valid','model_confidence_mask'])
        scale=float(p['s_model_per_metric']);K=p['K'][0];source=p['source_poses']
        old=p['old_self_z_model'].astype(np.float64);new=p['new_self_z_model'].astype(np.float64)
        check('source ordering and camera binding',np.array_equal(p['source_indices'],SOURCE_IDS) and np.array_equal(source,b['source_c2w']))
        check('source depth binding',np.array_equal(old,b['old_self_z'],equal_nan=True) and np.array_equal(new,b['new_self_z'],equal_nan=True))
        check('fixed K and common scale',np.array_equal(K,np.array([[245.2734375,0.,112.],[0.,245.,111.5],[0.,0.,1.]])) and np.array_equal(p['K'],np.repeat(K[None],4,axis=0)) and np.array_equal(K,b['K']) and np.array_equal(K,t['K']) and math.isfinite(scale) and scale>0 and scale==float(b['scale_model_per_meter'])==float(t['scale_model_per_meter']))
        eligible=np.isfinite(old)&np.isfinite(new)&(old>0)&(new>0)
        check('common source eligibility exact',np.array_equal(eligible,saved['source_valid']))
        confidence=confidence_by_fsum(p['old_conf_self'],p['new_conf_self'])
        check('confidence mean by fsum exact actions',np.array_equal(confidence,saved['model_confidence_mask']))
        choices=dict(masks,model_confidence=confidence);predictions=[];provenance=[];visits=[];changed={}
        for name in METHODS:
            if name=='never':depth=old.copy()
            elif name=='all_new':depth=new.copy()
            elif name=='half_blend':depth=(old+new)/2
            else:depth=old.copy();depth[choices[name]]=new[choices[name]]
            changed[name]=int(np.count_nonzero(depth[eligible]!=old[eligible]));dp=[];di=[];dv=[]
            for target in t['target_c2w']:
                x,y,z=render_components(depth,eligible,source,target,K,scale);dp.append(x);di.append(y);dv.append(z)
            predictions.append(dp);provenance.append(di);visits.append(dv)
        predictions=np.asarray(predictions);provenance=np.asarray(provenance)
        np.savez_compressed(out/'independent_predictions.npz',depth_m=predictions,source_pixel_identity=provenance)
        check('all 28 raster shapes',predictions.shape==saved['depth_m'].shape==(7,4,224,224) and provenance.shape==saved['source_pixel_identity'].shape)
        mismatched=provenance!=saved['source_pixel_identity']
        r['provenance_mismatch_count']=int(mismatched.sum())
        r['first_provenance_mismatches']=np.argwhere(mismatched)[:20].tolist()
        r['maximum_prediction_abs_error_m']=float(np.max(np.abs(predictions-saved['depth_m'])))
        check('all 28 source identity rasters exact',not mismatched.any(),dict(mismatch_count=r['provenance_mismatch_count']))
        check('all 28 depth rasters agree',np.allclose(predictions,saved['depth_m'],atol=1e-10,rtol=1e-10))
        description=json.loads((prediction_dir/'prediction_description.json').read_text())
        compare_tree(visits,description['projected_source_visits'],'projected source visits')
        compare_tree(changed,description['changed_source_pixels'],'changed source pixels')
        gt=[];ys=((2*np.arange(224,dtype=np.int64)+1)*480)//448;xs=((2*(np.arange(224,dtype=np.int64)+37)+1)*640)//598
        for sample in m['target_depths']:
            with Image.open(sample['path']) as image:
                raw=np.asarray(image)
                check('raw GT uint16 640x480 index '+str(sample['index']),raw.shape==(480,640) and raw.dtype==np.uint16)
                gt.append(raw[ys[:,None],xs[None,:]].astype(np.float64)/5000)
            r['gt_depth_decodes']+=1
        gt=np.asarray(gt)
        saved_gt=load(score_dir/'evaluation_gt.npz',['depth_m'])['depth_m']
        check('integer nearest GT mapping exactly matches saved scoring GT',np.array_equal(gt,saved_gt))
        rows,summary=score_fsum(predictions,gt)
        independent=dict(per_target=rows,equal_four_frame_means_and_auxiliary=summary)
        write(out/'independent_scores.json',independent)
        produced=json.loads((score_dir/'scores.json').read_text())
        compare_tree(rows,produced['per_target'],'28 per-target rows')
        compare_tree(summary,produced['equal_four_frame_means_and_auxiliary'],'seven equal-four means and auxiliary')
        for path,digest in frozen.items():check('post verification SHA '+path,sha(path)==digest)
        r.update(status='PASS',inputs_unchanged=True,input_identities=frozen)
    except BaseException as error:r.update(status='FAIL',error=repr(error),traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-started,peak_rss_bytes=rss,check_count=len(r['checks']))
        if r['elapsed_seconds']>600 or rss>8*1024**3:r.update(status='FAIL',budget_exceeded=True)
        write(out/'verification.json',r)
    print(json.dumps({k:r.get(k) for k in ['status','check_count','gt_depth_decodes','array_decodes','maximum_prediction_abs_error_m','provenance_mismatch_count','error']}))
    return int(r['status']!='PASS')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--prediction-seal',required=True);p.add_argument('--prediction-seal-sha256',required=True)
    p.add_argument('--score-dir',required=True);p.add_argument('--output',required=True)
    raise SystemExit(execute(p.parse_args()))
