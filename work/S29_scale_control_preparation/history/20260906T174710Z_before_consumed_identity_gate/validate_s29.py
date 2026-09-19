"""S29 no-GT saved-output comparison. Both producers must be sealed first."""
from __future__ import annotations
import argparse
import io
from pathlib import Path
import run_s29 as r


def validate(c):
    out=Path(c['output_root'])/'validation';r.require(not out.exists(),'No repeat validation');out.mkdir(parents=True)
    receipt=dict(status='RUNNING',started_utc=r.utc(),contract_sha256=c['_sha'],GT=0,model=0,MST=0,backward=0,Adam=0)
    r.write(out/'receipt.json',receipt)
    try:
        identities=dict(c['identities']);buffers={};metas={}
        # No NPZ decoding, including the historical B, before this complete seal.
        for arm in c['arms']:
            directory=Path(c['output_root'])/arm;path=directory/'receipt.json';rec=r.read(path)
            r.require(rec['status']=='PASS_INITIALIZATION_EXECUTED' and rec['contract_sha256']==c['_sha'] and rec['arm']==arm,'Both controlled initializations sealed')
            r.require(rec['counts']==c['counts_per_arm'] and rec['getter_repair_active'] is True,'Exact zero-step producer contract')
            identities[str(path)]=r.sha(path);buffers[arm]={}
            for name,h in rec['outputs'].items():
                p=directory/name;raw=p.read_bytes();r.require(r.hashlib.sha256(raw).hexdigest()==h,'Changed producer artifact: '+str(p))
                identities[str(p)]=h
                if p.suffix=='.npz':buffers[arm][name]=raw
            metas[arm]=r.read(directory/'prefix_metadata.json')
        reference=c['reference_B'];rec=r.read(reference['receipt'])
        r.require(rec['status']=='PASS' and rec['s28_contract_sha256']==c['s28_contract_sha256'],'Historical B identity, not a newly replayed prefix')
        identities[reference['receipt']]=r.sha(reference['receipt']);buffers['B']={}
        for name,item in reference['files'].items():
            raw=Path(item['path']).read_bytes();r.require(r.hashlib.sha256(raw).hexdigest()==item['sha256']==rec['outputs'][name],'Sealed historical B initial state')
            identities[item['path']]=item['sha256'];buffers['B'][name]=raw
        r.write(out/'pre_decode_seal.json',dict(status='PASS',utc=r.utc(),input_sha256=identities,
            both_initializations_complete=True,arrays_decoded=False,sensor_GT_bytes_read=False))
        b=r.module(c['parent_runner'],'s29_validation_environment');np,_=b.numeric_setup()
        data={}
        for arm,files in buffers.items():
            data[arm]={}
            for name,raw in files.items():
                with np.load(io.BytesIO(raw),allow_pickle=False) as z:data[arm][name]={k:z[k].copy() for k in z.files}
        del buffers
        def exact(x,y):return x.shape==y.shape and x.dtype==y.dtype and x.tobytes()==y.tobytes()
        checks={};reports={}
        t,a=data['C2t'],data['C2a'];pt,pa=t['prefix_raw.npz'],a['prefix_raw.npz']
        checks['C2t_C2a_complete_prefix_metadata_exact']=metas['C2t']==metas['C2a']
        checks['C2t_C2a_complete_prefix_tensor_bytes_exact']=set(pt)==set(pa) and all(exact(pt[k],pa[k]) for k in pt)
        at,aa=t['alignment.npz'],a['alignment.npz']
        checks['same_original_alignment_inputs_and_returns']=all(exact(at[k],aa[k]) for k in ['source_c2w','target_c2w','raw_registered_scale','s0','R0','T0'])
        checks['R0_unmodified']=exact(at['R0'],at['R_used']) and exact(aa['R0'],aa['R_used'])
        checks['scale_conditions_exact']=exact(at['s0'],at['s_used']) and float(aa['s_used'])==1.0
        # A mismatched common prefix is an execution/input failure, not a result
        # supporting or rejecting the scale model. Persist it before rejecting.
        r.write(out/'prefix_identity_checks.json',checks)
        r.require(all(checks.values()),'Common prefix/original alignment identity mismatch')
        def compare(label,x,y):
            x,y=np.asarray(x,dtype=np.float64),np.asarray(y,dtype=np.float64)
            r.require(x.shape==y.shape,'Comparison shape: '+label)
            finite=np.isfinite(x)&np.isfinite(y);delta=np.abs(x-y)
            good=finite&(delta<=c['tolerance']['atol']+c['tolerance']['rtol']*np.abs(y))
            reports[label]=dict(shape=list(x.shape),pixels=int(x.size),nonfinite_pairs=int((~finite).sum()),
                outside_tolerance=int((~good).sum()),max_abs=float(delta[finite].max()) if finite.any() else None,
                mean_abs=float(delta[finite].mean()) if finite.any() else None,
                per_frame_max_abs=[float(v[np.isfinite(v)].max()) if np.isfinite(v).any() else None for v in delta] if delta.ndim==3 else None,
                tolerance=c['tolerance'],passed=bool(good.all()))
            checks[label]=reports[label]['passed']
        zpre=[]
        for i,pose in enumerate(pt['local::poses']):
            points=pt['local::points.'+str(i)].astype(np.float64)
            local=(points-pose[:3,3].astype(np.float64))@np.linalg.inv(pose[:3,:3].astype(np.float64)).T
            zpre.append(local[...,2])
        zpre=np.stack(zpre);dt,da=t['initial_decoded.npz'],a['initial_decoded.npz'];s0=float(at['s0'])
        compare('prelog_C2t_vs_s0_times_preSim3',dt['prelog_depth'],s0*zpre)
        compare('prelog_C2a_vs_preSim3',da['prelog_depth'],zpre)
        compare('prelog_C2a_vs_C2t_div_s0',da['prelog_depth'],dt['prelog_depth'].astype(np.float64)/s0)
        compare('stored_C2t_vs_historical_B',dt['depth'],data['B']['initial_decoded.npz']['depth'])
        compare('stored_C2a_vs_C2t_div_s0',da['depth'],dt['depth'].astype(np.float64)/s0)
        checks['focal_pose_pp_unchanged_vs_B']=all(exact(dt[k],da[k]) and exact(dt[k],data['B']['initial_decoded.npz'][k]) for k in ['focal','pp','c2w'])
        checks['normalization_factor_one']=float(dt['norm_scale'])==float(da['norm_scale'])==1.
        ref=r.module(c['objective_reference'],'s29_original_independent_objective')
        for arm,item in [('C2t',t),('C2a',a)]:
            d=item['initial_decoded.npz'];al=item['alignment.npz'];raw=item['initial_raw.npz']
            src=al['source_c2w'].astype(np.float64);target=al['target_c2w'].astype(np.float64)
            mapped=float(al['s_used'])*(src[:,:3,3]@al['R_used'].astype(np.float64).T)+al['T_used']
            compare(arm+'_center_mean_match',mapped.mean(0),target[:,:3,3].mean(0))
            center_error=np.linalg.norm(mapped-target[:,:3,3],axis=1)
            angles=[]
            for Q,G in zip(src[:,:3,:3],target[:,:3,:3]):
                relative=(al['R_used'].astype(np.float64)@Q)@G.T
                angles.append(float(np.degrees(np.arccos(np.clip((np.trace(relative)-1)/2,-1,1)))))
            reports[arm+'_mapped_camera_residuals']=dict(center_error_per_frame=center_error.tolist(),
                center_rmse=float(np.sqrt(np.mean(center_error**2))),orientation_deg_per_frame=angles,
                note='Approximate rotation angle from FP32 matrices; mean match does not imply complete camera agreement')
            checks[arm+'_positive_finite_prelog']=bool(np.isfinite(d['prelog_depth']).all() and (d['prelog_depth']>0).all())
            reports[arm+'_domains']={k:dict(nonfinite=int((~np.isfinite(d[k])).sum()),nonpositive=int((np.isfinite(d[k])&(d[k]<=0)).sum())) for k in ['prelog_depth','depth','focal']}
            yi,xi=np.indices(d['depth'].shape[1:],dtype=np.float64);world=[]
            for i,dep in enumerate(d['depth'].astype(np.float64)):
                f=float(d['focal'][i,0]);pp=d['pp'][i]
                cam=np.stack([(xi-pp[0])*dep/f,(yi-pp[1])*dep/f,dep],-1)
                world.append(cam@d['c2w'][i,:3,:3].astype(np.float64).T+d['c2w'][i,:3,3])
            compare(arm+'_independent_depth_to_world',np.stack(world),d['point_cloud'])
            objectives=[]
            for j in range(1,4):
                suffix='0_'+str(j)
                objectives.append(ref.pair_objective(d['point_cloud'][[0,j]],raw['parameter::pred_i.'+suffix],
                    raw['parameter::pred_j.'+suffix],raw['parameter::conf_i.'+suffix],raw['parameter::conf_j.'+suffix],
                    d['pw_poses'][j-1],d['adaptors'][j-1]))
            independent=float(np.mean(objectives));observed=float(d['objective'])
            ok=bool(np.isfinite([independent,observed]).all() and np.isclose(independent,observed,atol=1e-5,rtol=1e-4))
            checks[arm+'_independent_objective']=ok
            reports[arm+'_objective']=dict(independent=independent if np.isfinite(independent) else None,
                observed=observed if np.isfinite(observed) else None,atol=1e-5,rtol=1e-4,passed=ok)
        r.write(out/'comparisons.json',dict(checks=checks,reports=reports,
            historical_B_scope='Bound source/input and saved post-MST values only; historical pre-Sim3 prefix was not saved and is not claimed exact',
            sensor_GT_used=False,new_optimization_steps=0,
            hypothesis_passed=all(checks.values()),meaning='Algebra/control evidence only, no depth-accuracy or method-novelty measurement'))
        for p,h in identities.items():r.require(r.sha(p)==h,'Identity changed during comparison: '+p)
        receipt.update(status='PASS_VALIDATION_EXECUTED',completed_utc=r.utc(),hypothesis_passed=all(checks.values()),
            failed_checks=[k for k,v in checks.items() if not v],input_sha256=identities,
            pass_meaning='Saved-array validation ran; a false hypothesis_passed is a preserved negative result and forbids progression as a valid scale control',
            outputs={p.name:r.sha(p) for p in out.iterdir() if p.is_file() and p.name!='receipt.json'})
        r.write(out/'receipt.json',receipt)
    except BaseException as e:
        receipt.update(status='FAILED',failed_utc=r.utc(),error=repr(e));r.write(out/'receipt.json',receipt);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contract',required=True);p.add_argument('--sha256',required=True)
    args=p.parse_args();validate(r.load_contract(args.contract,args.sha256))
