#!/usr/bin/env python3
"""Seven fixed geometric consumers, predictions sealed before four sensor labels."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,sys,time,resource,traceback,signal
import numpy as np
from PIL import Image
METHODS=['never','all_new','half_blend','pool_new','split_new','matched_absolute_new','model_confidence']
SOURCE_INDICES=[0,3,6,9]
K_FIXED=np.asarray([[245.2734375,0.,112.],[0.,245.,111.5],[0.,0.,1.]])
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def need(x,s):
    if not x:raise ValueError(s)
def ident(p,h):need(sha(p)==h,'SHA '+str(p))
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def validate_manifest(m):
    need(m['schema']=='s15b-consumer-manifest-v1','manifest schema')
    need(os.path.realpath(sys.executable)==os.path.realpath(m['python']),'frozen Python executable')
    need(m['methods']==METHODS and [x['index'] for x in m['target_depths']]==[20,21,22,23],'fixed methods and targets')
    roles=[m[k] for k in ['bridge','proposals','target_cameras','rule_masks']]
    ids=m['predict_identities'];targets=[x['path'] for x in m['target_depths']]
    need(len(set(roles))==4 and len(set(targets))==4,'distinct prediction roles and target depth paths')
    need(all(p in ids for p in roles),'all prediction roles frozen')
    need(ids.get(str(Path(__file__).resolve()))==m['runner_sha256'],'runner identity binding')
    need(not set(targets)&set(ids),'target depth bytes excluded from prediction identities')
    for p in list(ids)+targets:
        need(Path(p).is_absolute() and str(Path(p).resolve())==p,'canonical identity path')
    for p in ids:
        need((p in roles and Path(p).suffix=='.npz') or (p not in roles and Path(p).suffix in ['.md','.json','.py']),'prediction input domain excludes images and other arrays')
    need(all(Path(p).suffix=='.png' for p in targets),'fixed PNG target depth inputs')
def poses_ok(p,label):
    need(p.shape==(4,4,4) and np.isfinite(p).all(),label+' shape/finite')
    need(np.array_equal(p[:,3,:],np.tile([0.,0.,0.,1.],(4,1))),label+' bottom row')
    rot=p[:,:3,:3]
    need(np.allclose(rot@rot.transpose(0,2,1),np.eye(3),atol=1e-5,rtol=0) and np.allclose(np.linalg.det(rot),1,atol=1e-5,rtol=0),label+' proper optical rotation')
def validate_inputs(b,p,t,masks):
    old,new=b['old_self_z'].astype(np.float64),b['new_self_z'].astype(np.float64)
    need(old.shape==new.shape==(4,224,224),'four source grids')
    need(np.array_equal(old,p['old_self_z_model'],equal_nan=True) and np.array_equal(new,p['new_self_z_model'],equal_nan=True),'bridge proposal depth binding')
    need(np.array_equal(p['source_indices'],SOURCE_INDICES),'fixed proposal source order')
    poses_ok(b['source_c2w'],'source c2w');poses_ok(t['target_c2w'],'target c2w')
    need(np.array_equal(b['source_c2w'],p['source_poses']),'bridge proposal camera binding')
    K=b['K'];need(np.array_equal(K,K_FIXED) and np.array_equal(K,t['K']) and np.array_equal(p['K'],np.repeat(K[None],4,axis=0)),'same fixed K including proposals')
    s=float(b['scale_model_per_meter'])
    need(np.isfinite(s) and s>0 and s==float(t['scale_model_per_meter']) and s==float(p['s_model_per_metric']),'same finite positive scale including proposals')
    need(set(masks)=={'pool_new','split_new','matched_absolute_new'},'exact three witnessed rules')
    for name,mask in masks.items():
        need(mask.shape==(4,224,224) and mask.dtype==np.bool_,'bool source mask shape '+name)
        blocks=mask.reshape(4,14,16,14,16)
        need(np.array_equal(blocks,np.broadcast_to(blocks[:,:,0,:,0][:,:,None,:,None],blocks.shape)),'entire 16x16 blocks '+name)
    for name in ['old_conf_self','new_conf_self']:
        need(p[name].shape==(4,224,224) and np.isfinite(p[name]).all(),'finite source confidence shape '+name)
    return old,new,K,s,np.isfinite(old)&np.isfinite(new)&(old>0)&(new>0)
def confidence_blocks(p):
    conf=np.zeros((4,224,224),dtype=bool)
    for j in range(4):
        for row in range(14):
            for col in range(14):
                sl=(j,slice(row*16,(row+1)*16),slice(col*16,(col+1)*16))
                a=p['old_conf_self'][sl].astype(np.float64);c=p['new_conf_self'][sl].astype(np.float64)
                conf[sl]=float(c.mean())>float(a.mean())
    return conf
def render(z,valid,source,target,K,scale):
    n,h,w=z.shape;yy,xx=np.indices((h,w),dtype=np.float64)
    rays=np.stack([xx,yy,np.ones_like(xx)],axis=-1)@np.linalg.inv(K).T
    world=np.stack([(rays*z[j,...,None])@source[j,:3,:3].T+source[j,:3,3] for j in range(n)]).reshape(-1,3)
    camera=(world-target[:3,3])@target[:3,:3];proj=camera@K.T
    with np.errstate(invalid='ignore',divide='ignore',over='ignore'):
        u=np.floor(proj[:,0]/proj[:,2]+.5);v=np.floor(proj[:,1]/proj[:,2]+.5)
    keep=valid.ravel()&np.isfinite(camera).all(axis=1)&(camera[:,2]>0)&np.isfinite(u)&np.isfinite(v)&(u>=0)&(u<w)&(v>=0)&(v<h)
    ids=np.flatnonzero(keep);pix=v[keep].astype(np.int64)*w+u[keep].astype(np.int64);depth=camera[keep,2]
    order=np.lexsort((ids,depth,pix));ordered_pix=pix[order]
    first=np.r_[True,ordered_pix[1:]!=ordered_pix[:-1]] if len(order) else np.zeros(0,dtype=bool)
    chosen=order[first];pred=np.zeros(h*w,dtype=np.float64);provenance=np.full(h*w,-1,dtype=np.int64)
    pred[pix[chosen]]=depth[chosen]/scale;provenance[pix[chosen]]=ids[chosen]
    return pred.reshape(h,w),provenance.reshape(h,w),int(keep.sum())
def errors(p,g,valid):
    count=int(valid.sum())
    if not count:return {'count':0,'mae_m':None,'abs_rel':None,'rmse_m':None}
    d=p[valid]-g[valid]
    return dict(count=count,mae_m=float(np.mean(np.abs(d))),abs_rel=float(np.mean(np.abs(d)/g[valid])),rmse_m=float(np.sqrt(np.mean(d*d))))
def predict(m,out,r):
    for p,h in m['predict_identities'].items():ident(p,h)
    b=arrays(m['bridge']);p=arrays(m['proposals']);t=arrays(m['target_cameras']);masks=arrays(m['rule_masks'])
    old,new,K,s,valid=validate_inputs(b,p,t,masks)
    choices={k:masks[k] for k in ['pool_new','split_new','matched_absolute_new']}
    conf=confidence_blocks(p)
    choices['model_confidence']=conf
    allpred=[];allids=[];allcounts=[];changed={}
    for name in METHODS:
        z=old if name=='never' else new if name=='all_new' else (old+new)/2 if name=='half_blend' else np.where(choices[name],new,old)
        changed[name]=int((z[valid]!=old[valid]).sum());preds=[];ids=[];counts=[]
        for target in t['target_c2w']:
            pp,ii,cc=render(z,valid,b['source_c2w'],target,K,s);preds.append(pp);ids.append(ii);counts.append(cc)
        allpred.append(preds);allids.append(ids);allcounts.append(counts)
    np.savez_compressed(out/'target_predictions.npz',depth_m=np.asarray(allpred),source_pixel_identity=np.asarray(allids),source_valid=valid,model_confidence_mask=conf)
    save(out/'prediction_description.json',dict(methods=METHODS,target_indices=[20,21,22,23],source_indices=[0,3,6,9],scale_model_per_meter=s,changed_source_pixels=changed,eligible_source_pixels=int(valid.sum()),projected_source_visits=allcounts,source_identity='source ordinal*224*224 + row*224 + col',missing_value=0,prediction_kind='known-camera saved-proposal geometric consumer; no model invocation'))
    r.update(rgb_decodes=0,sensor_depth_decodes=0,model_calls=0,methods=METHODS)
def evaluate_predictions(pred,gt):
    rows=[]
    for j in range(4):
        g=gt[j];gv=np.isfinite(g)&(g>0);pv=np.isfinite(pred[:,j])&(pred[:,j]>0);common=gv&pv.all(axis=0);gn=int(gv.sum())
        for k,name in enumerate(METHODS):
            p=pred[k,j];own=gv&pv[k];correct=0
            if own.any():correct=int((np.maximum(p[own]/g[own],g[own]/p[own])<1.25).sum())
            rows.append(dict(method=name,target_index=20+j,gt_valid=gn,prediction_valid_on_gt=int(own.sum()),correct_delta1=correct,coverage=float(own.sum()/gn) if gn else None,delta1_all_gt=correct/gn if gn else None,own=errors(p,g,own),common=errors(p,g,common)))
    result={}
    for name in METHODS:
        rr=[x for x in rows if x['method']==name];gcount=sum(x['gt_valid'] for x in rr)
        result[name]={key:float(np.mean([x[key] for x in rr])) if all(x[key] is not None for x in rr) else None for key in ['delta1_all_gt','coverage']}
        result[name].update({dom+'_'+key:float(np.mean([x[dom][key] for x in rr])) if all(x[dom][key] is not None for x in rr) else None for dom in ['own','common'] for key in ['mae_m','abs_rel','rmse_m']})
        result[name]['pixel_weighted_delta1']=sum(x['correct_delta1'] for x in rr)/gcount if gcount else None
    return rows,result
def score(m,out,r,sealpath,sealsha):
    need(sealpath is not None and sealsha is not None,'score requires prior prediction seal path and SHA')
    ident(sealpath,sealsha);seal=json.loads(Path(sealpath).read_text());need(seal['schema']=='s15b-consumer-prediction-seal-v1','prediction seal')
    need(seal['manifest_sha256']==r['manifest_sha256'],'same manifest')
    base=Path(seal['prediction_dir']);need(base.is_absolute() and str(base.resolve())==str(base),'canonical prediction directory')
    need(set(seal['identities'])=={str(p) for p in base.iterdir() if p.is_file()},'exact prediction directory')
    required={'target_predictions.npz','prediction_description.json','run_metadata.json','frozen_manifest.json','source_snapshot.py'}
    need(required<={Path(p).name for p in seal['identities']},'required sealed prediction payloads')
    for p,h in seal['identities'].items():ident(p,h)
    prior=json.loads((base/'run_metadata.json').read_text())
    need(prior['status']=='PASS' and prior['mode']=='predict' and prior['manifest_sha256']==r['manifest_sha256'],'sealed successful prediction run for same manifest')
    need(prior['sensor_depth_decodes']==0 and prior['rgb_decodes']==0 and prior['model_calls']==0,'prediction stage used no target answers or model')
    ident(base/'frozen_manifest.json',r['manifest_sha256']);ident(base/'source_snapshot.py',m['runner_sha256'])
    description=json.loads((base/'prediction_description.json').read_text())
    need(description['methods']==METHODS and description['source_indices']==SOURCE_INDICES and description['target_indices']==[20,21,22,23],'sealed method/source/target order')
    payload=arrays(base/'target_predictions.npz');need(set(payload)=={'depth_m','source_pixel_identity','source_valid','model_confidence_mask'},'exact prediction array domain')
    pred=payload['depth_m'];provenance=payload['source_pixel_identity']
    need(pred.shape==(7,4,224,224) and pred.dtype==np.float64 and np.isfinite(pred).all() and (pred>=0).all(),'seven by four finite nonnegative predictions')
    need(provenance.shape==pred.shape and provenance.dtype==np.int64 and (provenance>=-1).all() and (provenance<4*224*224).all(),'source provenance domain')
    need(np.array_equal(pred>0,provenance>=0),'missing prediction and source provenance agree')
    for key in ['source_valid','model_confidence_mask']:
        need(payload[key].shape==(4,224,224) and payload[key].dtype==np.bool_,'source boolean metadata '+key)
    gt=[]
    for sample in m['target_depths']:
        ident(sample['path'],sample['sha256'])
        with Image.open(sample['path']) as image:
            need(image.size==(640,480),'native sensor dimensions')
            raw=np.asarray(image);need(raw.dtype==np.uint16,'native uint16 depth')
            g=np.asarray(image.resize((299,224),Image.Resampling.NEAREST).crop((37,0,261,224)),dtype=np.float64)/5000
        gt.append(g);r['sensor_depth_decodes']=len(gt)
    gt=np.asarray(gt);rows,result=evaluate_predictions(pred,gt)
    save(out/'scores.json',dict(schema='s15b-consumer-scores-v1',per_target=rows,equal_four_frame_means_and_auxiliary=result,independent_sequences=1,exploratory_previously_seen_targets=True))
    np.savez_compressed(out/'evaluation_gt.npz',depth_m=gt)
    for sample in m['target_depths']:ident(sample['path'],sample['sha256'])
    for p,h in seal['identities'].items():ident(p,h)
    ident(sealpath,sealsha)
    r.update(rgb_decodes=0,model_calls=0,prediction_seal_sha256=sealsha)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['predict','score']);ap.add_argument('--manifest',required=True);ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--output',required=True);ap.add_argument('--prediction-seal');ap.add_argument('--prediction-seal-sha256');a=ap.parse_args()
    out=Path(a.output);need(not out.exists(),'fresh output');out.mkdir(parents=True)
    r=dict(schema='s15b-consumer-run-v1',mode=a.mode,status='RUNNING',started_utc=utc(),sensor_depth_decodes=0,manifest_sha256=a.manifest_sha256)
    start=time.monotonic()
    def timeout(*args):raise TimeoutError('600 second budget')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(600)
    try:
        ident(a.manifest,a.manifest_sha256);m=json.loads(Path(a.manifest).read_text());validate_manifest(m);ident(__file__,m['runner_sha256'])
        (out/'frozen_manifest.json').write_bytes(Path(a.manifest).read_bytes());(out/'source_snapshot.py').write_bytes(Path(__file__).read_bytes())
        if a.mode=='predict':predict(m,out,r)
        else:score(m,out,r,a.prediction_seal,a.prediction_seal_sha256)
        if a.mode=='predict':
            for p,h in m['predict_identities'].items():ident(p,h)
        ident(a.manifest,a.manifest_sha256);ident(__file__,m['runner_sha256']);r['status']='PASS'
    except BaseException as e:r.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024);r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-start,peak_rss_bytes=rss)
        if r['elapsed_seconds']>600 or rss>8*1024**3:r.update(status='FAIL',budget_exceeded=True)
        save(out/'run_metadata.json',r)
    print(json.dumps(r));return int(r['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
