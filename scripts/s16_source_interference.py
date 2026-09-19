#!/usr/bin/env python3
"""Saved-data factorial source interventions; oracle diagnosis, never a deployed policy."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,time,traceback,signal,resource,sys,os,threading
import numpy as np
POLICIES=['all_new','half_blend','pool_new','split_new','matched_absolute_new','model_confidence']
SUBSETS=[0,1,2,4,8,15,14,13,11,7]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def need(x,label):
    if not x:raise ValueError(label)
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def load(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def layer(z,valid,camera,target,K,source):
    y,x=np.indices((224,224),dtype=np.float64)
    ray=np.stack([x,y,np.ones_like(x)],axis=-1)@np.linalg.inv(K).T
    world=((ray*z[...,None])@camera[:3,:3].T+camera[:3,3]).reshape(-1,3)
    target_xyz=(world-target[:3,3])@target[:3,:3];uvz=target_xyz@K.T
    with np.errstate(divide='ignore',invalid='ignore'):
        u=np.floor(uvz[:,0]/uvz[:,2]+.5);v=np.floor(uvz[:,1]/uvz[:,2]+.5)
    ok=valid.ravel()&np.isfinite(target_xyz).all(axis=1)&(target_xyz[:,2]>0)&np.isfinite(u)&np.isfinite(v)&(u>=0)&(u<224)&(v>=0)&(v<224)
    ids=np.flatnonzero(ok)+source*224*224;pixel=v[ok].astype(np.int64)*224+u[ok].astype(np.int64);depth=target_xyz[ok,2]
    order=np.lexsort((ids,depth,pixel));p=pixel[order];first=np.r_[True,p[1:]!=p[:-1]] if len(order) else np.zeros(0,bool);chosen=order[first]
    zz=np.zeros(224*224);ii=np.full(224*224,-1,np.int64);zz[pixel[chosen]]=depth[chosen];ii[pixel[chosen]]=ids[chosen]
    return zz.reshape(224,224),ii.reshape(224,224)
def compose(z,ids,owner=None):
    # source axis first, then target/y/x. Earliest source wins exact cross-source ties.
    if owner is None:
        cost=np.where(z>0,z,np.inf);owner=np.argmin(cost,axis=0)
    out=np.take_along_axis(z,owner[None],axis=0)[0];which=np.take_along_axis(ids,owner[None],axis=0)[0]
    return out,which
def intervention(old,new,subset):
    select=np.array([bool(subset&(1<<i)) for i in range(4)])
    return np.where(select[:,None,None,None],new,old)
def classify(old,new,oldids,newids):
    oldvalid=old>0;newvalid=new>0
    coverage=np.any(oldvalid!=newvalid,axis=0)
    route=(~coverage)&np.any(oldids!=newids,axis=0)
    fixed=(~coverage)&(~route)
    need(np.all(fixed.astype(int)+route.astype(int)+coverage.astype(int)==1),'three disjoint exhaustive classes')
    return dict(fixed_candidates_depth_competition=fixed,source_pixel_routing=route,coverage_change=coverage)
def correct(z,s,gt):
    p=z/s;mask=(p>0)&np.isfinite(p)&(gt>0)&np.isfinite(gt);hit=np.zeros_like(mask)
    hit[mask]=np.maximum(p[mask]/gt[mask],gt[mask]/p[mask])<1.25
    return hit
def diagnose(old,new,oldids,newids,s,gt):
    basez,baseids=compose(old,oldids);owner=np.maximum(baseids,0)//(224*224)
    base_exists=baseids>=0;gv=(gt>0)&np.isfinite(gt);den=gv.sum(axis=(1,2));need((den>0).all(),'four GT denominators nonempty')
    classes=classify(old,new,oldids,newids);success={};frozen={};records=[];frozen_records=[]
    for subset in SUBSETS:
        zz=intervention(old,new,subset);ii=intervention(oldids,newids,subset)
        z,ident=compose(zz,ii);hit=correct(z,s,gt);success[subset]=hit.astype(np.int16)
        fz,_=compose(zz,ii,owner);fz=np.where(base_exists,fz,0);frozen[subset]=correct(fz,s,gt).astype(np.int16)
        records.append(dict(subset=subset,changed_sources=[i for i in range(4) if subset&(1<<i)],correct_counts=hit.sum(axis=(1,2)).tolist(),delta1_per_target=(hit.sum(axis=(1,2))/den).tolist(),equal_four_frame_delta1=float(np.mean(hit.sum(axis=(1,2))/den)),coverage_on_gt=((z>0)&gv).sum(axis=(1,2)).tolist()))
        frozen_counts=frozen[subset].sum(axis=(1,2));frozen_records.append(dict(subset=subset,correct_counts=frozen_counts.tolist(),delta1_per_target=(frozen_counts/den).tolist(),equal_four_frame_delta1=float(np.mean(frozen_counts/den))))
    interaction=success[15]-sum(success[1<<i] for i in range(4))+3*success[0]
    frozen_interaction=frozen[15]-sum(frozen[1<<i] for i in range(4))+3*frozen[0]
    need(not np.any(frozen_interaction),'fixed old-owner control must have exact zero interaction at every pixel')
    component=[]
    for name,mask in classes.items():
        contributions=(interaction*mask*gv).sum(axis=(1,2));component.append(dict(name=name,gt_pixel_counts=(mask&gv).sum(axis=(1,2)).tolist(),interaction_correct_count_contribution=contributions.tolist(),interaction_delta1_contribution=(contributions/den).tolist(),interaction_mean_delta1=float(np.mean(contributions/den))))
    total=(interaction*gv).sum(axis=(1,2));need(np.array_equal(sum(np.array(x['interaction_correct_count_contribution']) for x in component),total),'three integer contributions exactly sum to total')
    marginal=[]
    for i in range(4):
        single=((success[1<<i]-success[0])*gv).sum(axis=(1,2));joint=((success[15]-success[15^(1<<i)])*gv).sum(axis=(1,2))
        solo_old=correct(old[i],s,gt).sum(axis=(1,2));solo_new=correct(new[i],s,gt).sum(axis=(1,2));solo=solo_new-solo_old
        marginal.append(dict(source_ordinal=i,source_index=[0,3,6,9][i],single_correct_delta=single.tolist(),joint_marginal_correct_delta=joint.tolist(),single_mean_delta1=float(np.mean(single/den)),joint_marginal_mean_delta1=float(np.mean(joint/den)),target_sign_reversals=((single*joint)<0).tolist(),mean_sign_reversal=bool(float(np.mean(single/den))*float(np.mean(joint/den))<0),solo_old_correct_counts=solo_old.tolist(),solo_new_correct_counts=solo_new.tolist(),solo_correct_delta=solo.tolist(),solo_delta1_per_target=(solo/den).tolist(),solo_mean_delta1=float(np.mean(solo/den))))
    return dict(denominators=den.tolist(),subsets=records,frozen_owner_subsets=frozen_records,interaction_correct_counts=total.tolist(),interaction_delta1=(total/den).tolist(),interaction_mean_delta1=float(np.mean(total/den)),components=component,marginals=marginal,frozen_owner_exact_zero=True,scope='10 selected subsets, not full factorial; I aggregates interaction orders >=2; spatial accounting classes do not independently intervene on physical causes'),dict(interaction=interaction,**classes)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--manifest',required=True);ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);need(not out.exists(),'fresh output');out.mkdir(parents=True);start=time.monotonic();r=dict(started_utc=utc(),status='RUNNING',new_model_calls=0,new_rgb_decodes=0,new_sensor_png_decodes=0,kind='post-answer saved-data oracle intervention diagnosis')
    def alarm(*args):raise TimeoutError('600 seconds')
    def peak():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    def memory_alarm(*args):raise MemoryError('8 GiB process RSS high-water limit')
    done=threading.Event()
    def monitor():
        while not done.wait(.1):
            if peak()>8*1024**3:os.kill(os.getpid(),signal.SIGUSR1);return
    signal.signal(signal.SIGUSR1,memory_alarm);signal.signal(signal.SIGALRM,alarm);signal.alarm(600);threading.Thread(target=monitor,daemon=True).start()
    try:
        need(sha(a.manifest)==a.manifest_sha256,'manifest SHA');m=json.loads(Path(a.manifest).read_text());need(m['schema']=='s16-source-interference-v1' and m['policies']==POLICIES,'manifest schema and fixed policies');need(os.path.realpath(m['python'])==os.path.realpath(sys.executable),'frozen Python executable')
        for p,h in m['identities'].items():need(sha(p)==h,'input identity '+p)
        need(m['identities'][str(Path(__file__).resolve())]==sha(__file__),'runner identity');save(out/'frozen_manifest.json',m);(out/'source_snapshot.py').write_bytes(Path(__file__).read_bytes())
        b=load(m['bridge']);p=load(m['proposals']);t=load(m['target_cameras']);masks=load(m['rule_masks']);existing=load(m['consumer_predictions']);gt=load(m['scored_gt'])['depth_m'];valid=existing['source_valid'];s=float(b['scale_model_per_meter']);K=b['K']
        old=b['old_self_z'].astype(np.float64);new=b['new_self_z'].astype(np.float64);choices={**masks,'model_confidence':existing['model_confidence_mask']};layers={};layer_ids={}
        methods=['never',*POLICIES]
        for name in methods:
            z=old if name=='never' else new if name=='all_new' else (old+new)/2 if name=='half_blend' else np.where(choices[name],new,old)
            values=[];ident=[]
            for source in range(4):
                current=[layer(z[source],valid[source],b['source_c2w'][source],target,K,source) for target in t['target_c2w']];values.append([x[0] for x in current]);ident.append([x[1] for x in current])
            layers[name]=np.asarray(values);layer_ids[name]=np.asarray(ident)
            zz,ii=compose(layers[name],layer_ids[name]);idx=methods.index(name)
            need(np.array_equal(zz/s,existing['depth_m'][idx]),'exact S15B depth reconstruction '+name);need(np.array_equal(ii,existing['source_pixel_identity'][idx]),'exact S15B provenance reconstruction '+name)
        np.savez_compressed(out/'source_layers.npz',**{name+'_z_model':z for name,z in layers.items()},**{name+'_source_pixel':i for name,i in layer_ids.items()})
        results={};maps={}
        for name in POLICIES:
            result,arrays=diagnose(layers['never'],layers[name],layer_ids['never'],layer_ids[name],s,gt);results[name]=result;maps.update({name+'_'+k:v for k,v in arrays.items()})
        save(out/'interference.json',dict(schema='s16-source-interference-results-v1',policies=results,interpretation='Known nonlinear z-buffer decomposition on already-seen targets, not a novel algorithm, not causal evidence about physical scene occlusion',all_previous_predictions_reconstructed_exactly=True))
        np.savez_compressed(out/'interaction_maps.npz',**maps)
        for p,h in m['identities'].items():need(sha(p)==h,'post-run identity '+p)
        need(peak()<=8*1024**3 and time.monotonic()-start<=600,'resource completion bounds');r.update(status='PASS',all_28_prior_predictions_exact=True,frozen_owner_control_all_six_exact_zero=True)
    except BaseException as e:r.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
    finally:done.set();signal.alarm(0);r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-start,peak_rss_bytes=peak(),source_sha256=sha(__file__));save(out/'run_metadata.json',r)
    print(json.dumps(r));return int(r['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
