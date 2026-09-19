#!/usr/bin/env python3
"""Independent source-layer and selected-intervention accounting on already-scored data.

No new RGB, PNG, network or model is accessed. Reuses the previously verified
different-path component projector, never imports S16 producer functions.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,math,resource,signal,sys,time,traceback
import numpy as np
from verify_s15b_consumer import render_components,confidence_by_fsum

POLICIES=['all_new','half_blend','pool_new','split_new','matched_absolute_new','model_confidence']
METHODS=['never',*POLICIES]
SUBSETS=[0,1,2,4,8,15,14,13,11,7]
PIXELS=224*224
HELPER_SHA='184ecc344be8bf58741ee9c7d6182909fcdd6786f3bb877a43ab21e2990beee5'
SCOPE='10 selected subsets, not full factorial; I aggregates interaction orders >=2; spatial accounting classes do not independently intervene on physical causes'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def combine(z,ids):
    available=np.isfinite(z)&(z>0)&(ids>=0)
    smallest=np.minimum.reduce(np.where(available,z,np.inf),axis=0)
    at_minimum=available&(z==smallest[None])
    winner=np.minimum.reduce(np.where(at_minimum,ids,4*PIXELS),axis=0)
    exists=np.isfinite(smallest)
    return np.where(exists,smallest,0.),np.where(exists,winner,-1)
def hits(z,scale,gt):
    valid=np.isfinite(z)&(z>0)&np.isfinite(gt)&(gt>0)
    answer=np.zeros(z.shape,dtype=bool);p=z[valid]/scale;g=gt[valid]
    answer[valid]=(p/g<1.25)&(g/p<1.25)
    return answer
def normalized(counts,den):return [int(n)/int(d) for n,d in zip(counts,den)]
def mean(values):return math.fsum(map(float,values))/4

def diagnose_independent(old,new,old_ids,new_ids,scale,gt):
    gt_valid=np.isfinite(gt)&(gt>0)
    den=np.count_nonzero(gt_valid,axis=(1,2));need((den>0).all(),'four nonempty known GT denominators')
    _,base_ids=combine(old,old_ids)
    base_exists=base_ids>=0;owner=np.where(base_exists,base_ids//PIXELS,-1)
    availability_changed=np.zeros(gt.shape,dtype=bool)
    routing_changed=np.zeros(gt.shape,dtype=bool)
    for s in range(4):
        availability_changed|=(old[s]>0)!=(new[s]>0)
        routing_changed|=old_ids[s]!=new_ids[s]
    routing_changed&=~availability_changed
    fixed=~(availability_changed|routing_changed)
    classes={'fixed_candidates_depth_competition':fixed,'source_pixel_routing':routing_changed,'coverage_change':availability_changed}
    need(np.all(sum(x.astype(np.int8) for x in classes.values())==1),'exhaustive disjoint spatial classes')
    success={};frozen_success={};records=[];frozen_records=[]
    for subset in SUBSETS:
        z=old.copy();ids=old_ids.copy()
        for s in range(4):
            if (subset>>s)&1:z[s]=new[s];ids[s]=new_ids[s]
        combined,_=combine(z,ids);success[subset]=hits(combined,scale,gt).astype(np.int32)
        frozen_depth=np.zeros(gt.shape,dtype=np.float64)
        for s in range(4):
            selection=base_exists&(owner==s);frozen_depth[selection]=z[s][selection]
        frozen_success[subset]=hits(frozen_depth,scale,gt).astype(np.int32)
        counts=success[subset].sum(axis=(1,2),dtype=np.int64);fractions=normalized(counts,den)
        records.append(dict(subset=subset,changed_sources=[s for s in range(4) if (subset>>s)&1],correct_counts=counts.tolist(),
            delta1_per_target=fractions,equal_four_frame_delta1=mean(fractions),coverage_on_gt=np.count_nonzero((combined>0)&gt_valid,axis=(1,2)).tolist()))
        frozen_counts=frozen_success[subset].sum(axis=(1,2),dtype=np.int64);fractions=normalized(frozen_counts,den)
        frozen_records.append(dict(subset=subset,correct_counts=frozen_counts.tolist(),delta1_per_target=fractions,equal_four_frame_delta1=mean(fractions)))
    interaction=success[15].copy()+3*success[0]
    frozen_interaction=frozen_success[15].copy()+3*frozen_success[0]
    for s in range(4):interaction-=success[1<<s];frozen_interaction-=frozen_success[1<<s]
    need(np.count_nonzero(frozen_interaction)==0,'frozen old-owner interaction exact zero, all pixels')
    total=np.sum(interaction*gt_valid,axis=(1,2),dtype=np.int64);components=[]
    for name,mask in classes.items():
        contribution=np.array([sum(map(int,interaction[q][mask[q]&gt_valid[q]])) for q in range(4)],dtype=np.int64)
        fractions=normalized(contribution,den)
        components.append(dict(name=name,gt_pixel_counts=np.count_nonzero(mask&gt_valid,axis=(1,2)).tolist(),
            interaction_correct_count_contribution=contribution.tolist(),interaction_delta1_contribution=fractions,interaction_mean_delta1=mean(fractions)))
    need(np.array_equal(np.sum([x['interaction_correct_count_contribution'] for x in components],axis=0),total),'integer class contributions sum exactly')
    marginals=[];pixel_reversals=[]
    for s in range(4):
        single_map=success[1<<s]-success[0];joint_map=success[15]-success[15^(1<<s)]
        single=single_map.sum(axis=(1,2),dtype=np.int64);joint=joint_map.sum(axis=(1,2),dtype=np.int64)
        a=mean(normalized(single,den));b=mean(normalized(joint,den))
        solo_old=hits(old[s],scale,gt).sum(axis=(1,2),dtype=np.int64);solo_new=hits(new[s],scale,gt).sum(axis=(1,2),dtype=np.int64)
        solo=solo_new-solo_old;fractions=normalized(solo,den)
        marginals.append(dict(source_ordinal=s,source_index=[0,3,6,9][s],single_correct_delta=single.tolist(),joint_marginal_correct_delta=joint.tolist(),
            single_mean_delta1=a,joint_marginal_mean_delta1=b,target_sign_reversals=[(int(x)>0 and int(y)<0) or (int(x)<0 and int(y)>0) for x,y in zip(single,joint)],
            mean_sign_reversal=(a>0 and b<0) or (a<0 and b>0),solo_old_correct_counts=solo_old.tolist(),solo_new_correct_counts=solo_new.tolist(),
            solo_correct_delta=solo.tolist(),solo_delta1_per_target=fractions,solo_mean_delta1=mean(fractions)))
        pixel_reversals.append(int(np.count_nonzero(single_map*joint_map<0)))
    fractions=normalized(total,den)
    result=dict(denominators=den.tolist(),subsets=records,frozen_owner_subsets=frozen_records,interaction_correct_counts=total.tolist(),
        interaction_delta1=fractions,interaction_mean_delta1=mean(fractions),components=components,marginals=marginals,frozen_owner_exact_zero=True,scope=SCOPE)
    return result,dict(interaction=interaction,**classes),dict(frozen_interaction_nonzero=int(np.count_nonzero(frozen_interaction)),pixel_marginal_sign_reversals=pixel_reversals)

def execute(a):
    out=Path(a.output);need(not out.exists(),'fresh independent output');out.mkdir(parents=True)
    started=time.monotonic();r=dict(schema='s16-independent-verification-v1',status='RUNNING',started_utc=utc(),checks=[],array_decodes=0,
        rgb_decodes=0,png_decodes=0,model_calls=0,kind='already-known-GT saved-data independent numerical recomputation',
        independence='Internal different mathematical path; author reviewed producer input guards at S15B, not an external replication team.',
        tolerances=dict(model_z_atol=1e-10,model_z_rtol=1e-10,winner_id='exact',integers='exact'),python=sys.executable,numpy_version=np.__version__)
    frozen={}
    def check(name,ok,detail=None):
        r['checks'].append(dict(name=name,status='PASS' if ok else 'FAIL',detail=detail))
        if not ok or len(r['checks'])%100==0:write(out/'verification.json',r)
        need(ok,name)
    def bind(path,expected=None):
        p=Path(path).resolve();need(p.suffix.lower() not in ['.png','.jpg','.jpeg','.pth','.pt'],'no PNG/RGB/model byte reads')
        digest=sha(p)
        if expected is not None:check('SHA '+str(p),digest==expected)
        if str(p) in frozen:check('stable repeated identity '+str(p),frozen[str(p)]==digest)
        frozen[str(p)]=digest;return p
    def arrays(path,keys):
        need(str(Path(path).resolve()) in frozen,'only frozen NPZ inputs')
        with np.load(path,allow_pickle=False) as z:
            ans={}
            for key in keys:ans[key]=z[key];r['array_decodes']+=1
            return ans
    def compare(got,expected,name):
        if isinstance(expected,dict):
            check(name+' keys',set(got)==set(expected))
            for k in expected:compare(got[k],expected[k],name+'.'+k)
        elif isinstance(expected,list):
            check(name+' length',len(got)==len(expected))
            for i,(x,y) in enumerate(zip(got,expected)):compare(x,y,name+f'[{i}]')
        elif isinstance(expected,float):check(name,math.isclose(float(got),expected,rel_tol=1e-10,abs_tol=1e-10),dict(got=got,expected=expected))
        else:check(name,got==expected)
    def alarm(*args):raise TimeoutError('600-second S16 verification budget')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(600)
    try:
        mp=bind(a.manifest,a.manifest_sha256);m=json.loads(mp.read_text())
        check('manifest fixed scope',m['schema']=='s16-source-interference-v1' and m['policies']==POLICIES)
        producer=Path(a.producer_dir).resolve();run_path=bind(producer/'run_metadata.json');run=json.loads(run_path.read_text())
        check('producer PASS before actual NPZ access',run['status']=='PASS' and run['all_28_prior_predictions_exact'] and run['frozen_owner_control_all_six_exact_zero'])
        for path,digest in m['identities'].items():bind(path,digest)
        for path in producer.iterdir():
            if path.is_file():bind(path)
        check('producer frozen manifest values',json.loads((producer/'frozen_manifest.json').read_text())==m)
        check('producer source snapshot identity',sha(producer/'source_snapshot.py')==run['source_sha256']==m['identities'][str(Path(__file__).with_name('s16_source_interference.py').resolve())])
        bind(Path(__file__).with_name('verify_s15b_consumer.py'),HELPER_SHA);bind(__file__)
        write(out/'input_snapshot.json',dict(frozen_utc=utc(),identities=frozen,array_decodes=0,png_decodes=0))
        b=arrays(m['bridge'],['old_self_z','new_self_z','source_c2w','K','scale_model_per_meter'])
        p=arrays(m['proposals'],['old_self_z_model','new_self_z_model','source_indices','source_poses','K','s_model_per_metric','old_conf_self','new_conf_self'])
        t=arrays(m['target_cameras'],['target_c2w','K','scale_model_per_meter'])
        masks=arrays(m['rule_masks'],['pool_new','split_new','matched_absolute_new'])
        existing=arrays(m['consumer_predictions'],['depth_m','source_pixel_identity','source_valid','model_confidence_mask'])
        gt=arrays(m['scored_gt'],['depth_m'])['depth_m']
        saved=arrays(producer/'source_layers.npz',[n+s for n in METHODS for s in ['_z_model','_source_pixel']])
        map_keys=[n+'_'+s for n in POLICIES for s in ['interaction','fixed_candidates_depth_competition','source_pixel_routing','coverage_change']]
        saved_maps=arrays(producer/'interaction_maps.npz',map_keys)
        original=json.loads((producer/'interference.json').read_text())
        check('result schema and six policy domain',original['schema']=='s16-source-interference-results-v1' and set(original['policies'])==set(POLICIES))
        old=p['old_self_z_model'].astype(np.float64);new=p['new_self_z_model'].astype(np.float64);source=p['source_poses'];K=p['K'][0];scale=float(p['s_model_per_metric'])
        check('original proposal and bridge depth binding',np.array_equal(old,b['old_self_z'],equal_nan=True) and np.array_equal(new,b['new_self_z'],equal_nan=True))
        check('source ordering/cameras/scale',np.array_equal(p['source_indices'],[0,3,6,9]) and np.array_equal(source,b['source_c2w']) and scale==float(b['scale_model_per_meter'])==float(t['scale_model_per_meter']) and scale>0 and math.isfinite(scale))
        check('common fixed intrinsics',np.array_equal(K,b['K']) and np.array_equal(K,t['K']) and np.array_equal(p['K'],np.repeat(K[None],4,axis=0)))
        eligible=np.isfinite(old)&np.isfinite(new)&(old>0)&(new>0)
        check('shared valid source domain',np.array_equal(eligible,existing['source_valid']))
        confidence=confidence_by_fsum(p['old_conf_self'],p['new_conf_self'])
        check('independent confidence means',np.array_equal(confidence,existing['model_confidence_mask']))
        choices=dict(masks,model_confidence=confidence);layers={};layer_ids={};differences={}
        for k,name in enumerate(METHODS):
            if name=='never':z=old.copy()
            elif name=='all_new':z=new.copy()
            elif name=='half_blend':z=(old+new)/2
            else:z=old.copy();z[choices[name]]=new[choices[name]]
            values=[];ids=[]
            for s in range(4):
                ds=[];ii=[]
                for target in t['target_c2w']:
                    d,i,_=render_components(z[s:s+1],eligible[s:s+1],source[s:s+1],target,K,1.)
                    i=np.where(i>=0,i+s*PIXELS,-1);ds.append(d);ii.append(i)
                values.append(ds);ids.append(ii)
            layers[name]=np.asarray(values);layer_ids[name]=np.asarray(ids)
            differences[name]=float(np.max(np.abs(layers[name]-saved[name+'_z_model'])))
            np.savez_compressed(out/(name+'_independent_layers.npz'),z_model=layers[name],source_pixel=layer_ids[name])
            check(name+' all 16 layer winner identities exact',np.array_equal(layer_ids[name],saved[name+'_source_pixel']))
            check(name+' all 16 model-z layers within tolerance',np.allclose(layers[name],saved[name+'_z_model'],atol=1e-10,rtol=1e-10),dict(max_abs_model_z_error=differences[name]))
            merged,which=combine(layers[name],layer_ids[name])
            check(name+' four merged identities equal S15B',np.array_equal(which,existing['source_pixel_identity'][k]))
            check(name+' four merged depths equal S15B',np.allclose(merged/scale,existing['depth_m'][k],atol=1e-10,rtol=1e-10))
        independent={};maps={};invariants={}
        for name in POLICIES:
            result,map_values,invariant=diagnose_independent(layers['never'],layers[name],layer_ids['never'],layer_ids[name],scale,gt)
            independent[name]=result;invariants[name]=invariant
            write(out/(name+'_independent_diagnosis.json'),result)
            for key,value in map_values.items():
                maps[name+'_'+key]=value
                check(name+' exact '+key+' map',np.array_equal(value,saved_maps[name+'_'+key]))
            compare(result,original['policies'][name],name+' 10-subset/component/frozen/solo/marginal accounting')
            check(name+' no pointwise marginal sign reversal',not any(invariant['pixel_marginal_sign_reversals']))
        np.savez_compressed(out/'independent_interaction_maps.npz',**maps)
        write(out/'independent_interference.json',dict(policies=independent,extra_invariants=invariants))
        for path,digest in frozen.items():check('post verification SHA '+path,sha(path)==digest)
        r.update(status='PASS',input_identities=frozen,inputs_unchanged=True,model_z_max_abs_errors=differences,extra_invariants=invariants,
            all_112_layers_verified=True,all_28_S15B_predictions_verified=True,subsets_per_policy=10,policies_verified=6)
    except BaseException as error:r.update(status='FAIL',error=repr(error),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-started,peak_rss_bytes=rss,check_count=len(r['checks']))
        if r['elapsed_seconds']>600 or rss>8*1024**3:r.update(status='FAIL',budget_exceeded=True)
        write(out/'verification.json',r)
    print(json.dumps({k:r.get(k) for k in ['status','check_count','array_decodes','all_112_layers_verified','policies_verified','error']}))
    return int(r['status']!='PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--manifest',required=True);parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--producer-dir',required=True);parser.add_argument('--output',required=True)
    raise SystemExit(execute(parser.parse_args()))
