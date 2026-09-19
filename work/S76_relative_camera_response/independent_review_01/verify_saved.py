"""Independent saved S76 arithmetic. No imports of author code, Torch, PIL or OpenCV."""
import argparse, datetime, hashlib, io, json, math, os, resource, time, traceback
from pathlib import Path
D=Path(__file__).absolute().parents[1]
CONTRACT='7b0216596bd3c8859d5a0c3a864c47efa28c1c37b9fbf2beef3a50ee2de23d54'
TOL={'scalar_atol':1e-8,'scalar_rtol':1e-10,'H_atol':1e-12,'yaw_atol':2e-7,'ray_atol':2e-5,'ray_rtol':2e-5}
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return sha(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def quant(a):
    if not a:return None
    s=sorted(a);out=[]
    for q in [.25,.5,.75,.95]:
        z=(len(s)-1)*q;i=int(z);f=z-i
        out.append(s[i] if i==len(s)-1 else s[i]*(1-f)+s[i+1]*f)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['generation','score'])
    for k in ['worker-sha','external-sha']:ap.add_argument('--'+k,required=True)
    for k in ['score-sha','score-external','score-external-sha']:ap.add_argument('--'+k)
    a=ap.parse_args();out=D/'independent_review_01'/(a.phase+'_01');out.mkdir(exist_ok=False)
    t=time.monotonic();r=dict(schema='s76-independent-saved-review-v1',phase=a.phase,status='RUNNING',
        reviewer_role='/root/c2_v9_source_primary',started_utc=utc(),source_sha256=sha(Path(__file__).read_bytes()),
        tolerances=TOL,reads=[],checks=[],blockers=[],diagnostics={},new_method_validated=False)
    def budget():
        if time.monotonic()-t>110:raise RuntimeError('110-second inner budget')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>2*1024**3:raise RuntimeError('2GiB self sampled peak budget')
    def check(ok,label,detail=None):
        ok=bool(ok);r['checks'].append(dict(name=label,pass_=ok,detail=detail))
        if not ok:r['blockers'].append(label)
    def require(ok,label):
        check(ok,label)
        if not ok:raise RuntimeError(label)
    def read(p,h=None,kind='metadata'):
        budget();p=Path(p);b=p.read_bytes();actual=sha(b)
        r['reads'].append(dict(path=str(p),sha256=actual,bytes=len(b),kind=kind))
        if h is not None:require(h==actual,'identity:'+str(p))
        return b
    def js(p,h=None):return json.loads(read(p,h))
    def compare(got,want,label,atol=1e-8,rtol=1e-10):
        if isinstance(want,dict):
            check(set(got)==set(want),label+':keys')
            for k in set(got)&set(want):compare(got[k],want[k],label+'/'+k,atol,rtol)
        elif isinstance(want,(list,tuple)):
            check(len(got)==len(want),label+':length')
            for i,(x,y) in enumerate(zip(got,want)):compare(x,y,label+'/'+str(i),atol,rtol)
        elif isinstance(want,float):check(isinstance(got,(int,float)) and math.isclose(got,want,abs_tol=atol,rel_tol=rtol),label,dict(got=got,expected=want))
        else:check(got==want,label)
    try:
        import numpy as np
        require(np.__version__=='1.26.4','NumPy version')
        c=js(D/'RUN_CONTRACT.json',CONTRACT);bind=js(D/'ROOT_RUN_BINDING.json')
        for p,h in bind['reviewed_files_sha256'].items():read(p,h,'reviewed source or accepted metadata')
        worker=js(D/'execution_01/receipt.json',a.worker_sha);ext=js(D/'external_01/receipt.json',a.external_sha)
        require(ext['returncode']==0 and ext['stop_reason'] is None and ext['observer_error'] is None,'external success')
        check(ext['binding_sha256']==canonical(bind) or ext['binding_sha256']==sha((D/'ROOT_RUN_BINDING.json').read_bytes()),'external root binding')
        require(worker['status']=='COMPLETE_SINGLE_YAW_FIXED_STREAM','worker complete')
        check(worker['contract_sha256']==CONTRACT,'worker contract')
        check(worker['source_sha256']==bind['reviewed_files_sha256'][str(D/'run_single_yaw.py')],'worker source')
        old=js(c['old_worker_receipt']['path'],c['old_worker_receipt']['sha256']);a0=old['arms']['A0']
        manifest=js(c['s70_manifest']['path'],c['s70_manifest']['sha256'])
        def descriptor(x,z,label):
            check(list(x.shape)==z['shape'] and str(x.dtype)==z['dtype'] and x.nbytes==z['body_bytes'],label+':layout')
            check(sha(np.ascontiguousarray(x).tobytes())==z['body_sha256'],label+':body')
            check(np.isfinite(x).all(),label+':finite')
        def npz(z,label):
            b=read(z['path'],z['sha256'],label)
            with np.load(io.BytesIO(b),allow_pickle=False) as f:data={k:f[k] for k in f.files}
            require(set(data)==set(z['fields']),label+':fields')
            for k,x in data.items():descriptor(x,z['fields'][k],label+'/'+k)
            return data
        def arr(z,label):
            x=np.load(io.BytesIO(read(z['path'],z['file_sha256'],label)),allow_pickle=False);descriptor(x,z,label);return x
        g=npz(worker['prescribed_geometry'],'saved prescribed numeric geometry')
        oldC=g['old_optical'].astype(float);newC=g['new_optical'].astype(float);Ks=g['K_pixels_576'].astype(float)
        # Independent scalar expansion of local yaw column mixing.
        co=float(np.float32(math.cos(math.pi/36)));si=float(np.float32(math.sin(math.pi/36)))
        expected=oldC.copy()
        for s in range(4,8):
            for j in range(3):
                expected[s,j,0]=oldC[s,j,0]*co-oldC[s,j,2]*si
                expected[s,j,2]=oldC[s,j,0]*si+oldC[s,j,2]*co
        check(np.allclose(newC,expected,rtol=0,atol=TOL['yaw_atol']),'scalar local yaw',float(np.max(np.abs(newC-expected))))
        check(np.array_equal(newC[:4],oldC[:4]) and np.array_equal(newC[:,:,3],oldC[:,:,3]),'old history/centers byte values')
        check(g['ordered_ids'].tolist()==[19,18,13,12,20,21,22,23],'ordered eight cameras')
        expectedQ=np.array([[co,0,si],[0,1,0],[-si,0,co]],dtype=np.float32)
        check(g['local_yaw_Q'].tobytes()==expectedQ.tobytes(),'saved yaw Q bytes')
        Hs=[];inverseHs=[]
        def mm(A,B):return np.array([[math.fsum(float(A[i,k])*float(B[k,j]) for k in range(3)) for j in range(3)] for i in range(3)])
        def proj(x,y,H):
            v=[math.fsum([float(H[j,0])*x,float(H[j,1])*y,float(H[j,2])]) for j in range(3)]
            return None if not all(map(math.isfinite,v)) or v[2]<=1e-12 else (v[0]/v[2],v[1]/v[2])
        def inside(p):return p is not None and all(math.isfinite(z) and 0<=z<=575 for z in p)
        def grid(H):
            yy,xx=np.indices((576,576),dtype=float)
            v=[H[j,0]*xx+H[j,1]*yy+H[j,2] for j in range(3)];valid=np.isfinite(v).all(axis=0)&(v[2]>1e-12)
            with np.errstate(divide='ignore',invalid='ignore'):x=v[0]/v[2];y=v[1]/v[2]
            return valid&(x>=0)&(x<=575)&(y>=0)&(y<=575),x,y
        for s in range(4,8):
            H=mm(mm(Ks[s],mm(newC[s,:3,:3].T,oldC[s,:3,:3])),np.linalg.inv(Ks[s]));Hs.append(H);Hi=np.linalg.inv(H);inverseHs.append(Hi)
            check(np.allclose(H,g['H_old_to_new'][s-4],atol=TOL['H_atol'],rtol=0),'scalar H target'+str(s+16))
            ma,x,y=grid(H);mb,_,_=grid(Hi)
            check(np.array_equal(ma,g['old_common_fov_masks'][s-4]) and np.array_equal(mb,g['new_common_fov_masks'][s-4]),'all integer FOV mask target'+str(s+16))
            # True inverse is diagnostic only; never substitutes the prescribed H.
            Htrue=mm(mm(Ks[s],mm(np.linalg.inv(newC[s,:3,:3]),oldC[s,:3,:3])),np.linalg.inv(Ks[s]))
            mt,u,v=grid(Htrue);mask=ma&mt;err=np.hypot(x[mask]-u[mask],y[mask]-v[mask])
            r['diagnostics']['transpose_vs_inverse_target'+str(s+16)]=dict(H_maxabs=float(np.max(np.abs(H-Htrue))),
                positive_common_inframe_count=int(mask.sum()),pixel_max=float(err.max()) if len(err) else None,
                pixel_mean=float(err.mean()) if len(err) else None,old_rotation_orthogonality_max=float(np.max(np.abs(oldC[s,:3,:3].T@oldC[s,:3,:3]-np.eye(3)))))
        if a.phase=='generation':
            prior=npz(manifest['conditions']['geometry'],'accepted geometry condition arrays');new=npz(worker['new_conditions'],'new condition arrays')
            check(g['old_optical'].tobytes()==prior['optical_c2ws_fp32'].tobytes(),'original camera exact accepted bytes')
            check(g['K_pixels_576'].tobytes()==prior['K_pixels_576'].tobytes(),'K exact accepted bytes')
            for k in ['K_pixels_576','input_masks','c__crossattn','uc__crossattn','c__replace','uc__replace']:
                check(new[k].tobytes()==prior[k].tobytes(),'unchanged field bytes:'+k)
            for k in ['c__concat','uc__concat','c__dense_vector','uc__dense_vector']:
                check(new[k][:4].tobytes()==prior[k][:4].tobytes(),'history ray bytes:'+k)
            check(new['c__dense_vector'].tobytes()==new['uc__dense_vector'].tobytes(),'c/uc full rays identical')
            for q in ['c','uc']:
                check(new[q+'__concat'][:,1:].tobytes()==new[q+'__dense_vector'].tobytes(),q+' concat ray channels')
                check(new[q+'__concat'][:,0].tobytes()==prior[q+'__concat'][:,0].tobytes(),q+' mask channel unchanged')
            check(np.array_equal(new['post_cond_optical_c2ws'][:,:3,3],prior['post_cond_optical_c2ws'][:,:3,3]),'normalized centers unchanged')
            check(np.allclose(new['post_cond_optical_c2ws'][:,:3,:3],newC[:,:3,:3],rtol=0,atol=0),'post-cond optical axes')
            # Independent world-camera rays and cross products; original optical camera, no get_cond.
            scale=float(prior['scale'][0])
            centers=oldC[:,:3,3];med=np.array([sorted(centers[:,j])[3] for j in range(3)])
            dist=[math.sqrt(math.fsum(float(z*z) for z in row-med)) for row in centers]
            sd=sorted(dist);position=7*.97;q97=sd[int(position)]*(1-position%1)+sd[int(position)+1]*(position%1)
            keep=[row for row,z in zip(centers,dist) if z<=min(q97*10,1e6)]
            center=np.array([math.fsum(float(row[j]) for row in keep)/len(keep) for j in range(3)])
            norm=math.sqrt(math.fsum(float(z*z) for z in centers[0]-center));derived_scale=2. if norm<=1e-5 else 2/norm+.01
            check(math.isclose(scale,derived_scale,abs_tol=2e-5,rel_tol=2e-5),'independent median center scale',dict(saved=scale,derived=derived_scale))
            check(np.allclose(new['post_cond_optical_c2ws'][:,:3,3],(centers-center)*scale,atol=2e-5,rtol=2e-5),'independent normalized centers')
            yy,xx=np.indices((72,72),dtype=float)
            for s in range(8):
                K=Ks[s].copy();K[:2]/=8
                rays=np.linalg.solve(K,np.stack([xx.ravel()+.5,yy.ravel()+.5,np.ones(5184)]))
                direction=np.linalg.solve(newC[0,:3,:3],newC[s,:3,:3]@rays);direction/=np.linalg.norm(direction,axis=0)
                origin=scale*np.linalg.solve(newC[0,:3,:3],newC[s,:3,3]-newC[0,:3,3]);moment=np.cross(origin,direction.T).T
                pred=np.concatenate([direction,moment]).reshape(6,72,72);saved=new['c__dense_vector'][s]
                check(np.allclose(saved,pred,atol=TOL['ray_atol'],rtol=TOL['ray_rtol']),'independent optical ray slot'+str(s),float(np.max(np.abs(saved-pred))))
            require(len(worker['steps'])==50,'50 recorded steps')
            for i,(x,y) in enumerate(zip(worker['steps'],a0['steps'])):
                check(x['step']==i+1 and x['finite'] and x['rng_before']==y['rng_before'] and x['rng_after']==y['rng_after'],'step/RNG '+str(i+1))
            trace=[json.loads(x) for x in read(D/'execution_01/steps.jsonl',kind='step trace').splitlines() if x]
            check(trace==worker['steps'],'step trace same worker')
            for k in ['sampler_entry_rng_state_sha256','terminal_rng_state_sha256']:check(worker[k]==a0[k],k)
            check(worker['restored_common_rng_state_sha256']==old['common_rng_state_sha256'],'restored common RNG')
            for path,h in [(D/'execution_01/sampler_entry_rng.json',worker['sampler_entry_rng_state_sha256']),(D/'execution_01/terminal_rng.json',worker['terminal_rng_state_sha256'])]:check(canonical(js(path))==h,'saved canonical RNG '+path.name)
            common=js(old['common_rng']['path'],old['common_rng']['sha256']);check(canonical(common)==old['common_rng_state_sha256'],'common RNG body')
            check(worker['model_before']==worker['model_after'],'same process model identity/value/modes')
            for k in ['value_sha256','modes_sha256']:check(worker['model_before'][k]==a0['model_before'][k],'cross-process model '+k)
            snap=js(worker['model_baseline']['path'],worker['model_baseline']['sha256'])
            for key in ['values','identity','modes']:check(canonical(snap[key])==snap[{'values':'value_sha256','identity':'identity_sha256','modes':'modes_sha256'}[key]],'model snapshot '+key)
            for k in ['value_sha256','identity_sha256','modes_sha256']:check(snap[k]==worker['model_before'][k],'snapshot receipt binding '+k)
            progress=[json.loads(x) for x in read(D/'execution_01/progress.jsonl',kind='generation progress').splitlines() if x]
            check([x['step'] for x in progress if x['phase']=='step']==list(range(1,51)),'50 completed progress steps')
            check(progress[-1]['phase']=='complete','terminal complete progress')
            for z in worker['reads']:
                if z['path'] in bind['reviewed_files_sha256']:check(z['sha256']==bind['reviewed_files_sha256'][z['path']],'consumed source binding:'+z['path'])
            # Consumed model hashes are receipt evidence; never re-read weight bodies.
            for z in old['reads']:
                if 'weight' in z['kind'].lower():check(any(x['path']==z['path'] and x['sha256']==z['sha256'] and x['bytes']==z['bytes'] for x in worker['reads']),'recorded consumed weight:'+z['path'])
            noise=arr(worker['noise'],'initial noise');oldnoise=arr(a0['noise'],'accepted initial noise')
            check(noise.tobytes()==oldnoise.tobytes(),'initial noise byte equality')
            arrays={k:arr(v,'new '+k) for k,v in worker['arrays'].items()}
            check(set(arrays)=={'all8_latents','targets_fp32','targets_uint8'},'complete saved array fields')
            for k,shape,dtype in [('all8_latents',(8,4,72,72),'float32'),('targets_fp32',(4,3,576,576),'float32'),('targets_uint8',(4,576,576,3),'uint8')]:check(arrays[k].shape==shape and str(arrays[k].dtype)==dtype,k+' expected shape/type')
            r['diagnostics']['quantization']=[]
            for i,raw in enumerate(arrays['targets_fp32']):
                x=raw.transpose(1,2,0);branch=bool(x.min()<-.1);mapped=(x+1)/2 if branch else x
                q=(np.clip(mapped,0,1)*255).astype(np.uint8)
                check(q.tobytes()==arrays['targets_uint8'][i].tobytes(),'original NumPy quantizer target'+str(20+i))
                r['diagnostics']['quantization'].append(dict(target_id=20+i,numpy_branch=branch,raw_min=float(raw.min()),raw_max=float(raw.max()),advisory=worker['quantizer'][i]))
            check(worker['target_ids']==[20,21,22,23] and worker['no_new_baseline'] and worker['stream_identity_pass'] and worker['all4_targets_preserved'],'complete intervention flags')
            read(D/'external_01/stdout.txt',kind='external stdout');read(D/'external_01/stderr.txt',kind='external stderr')
        else:
            require(all([a.score_sha,a.score_external,a.score_external_sha]),'actual score binding arguments')
            score=js(D/'scoring_01/receipt.json',a.score_sha);sex=js(a.score_external,a.score_external_sha)
            check(sex.get('returncode')==0 and not sex.get('timeout',sex.get('timed_out',False)),'score external return')
            require(score['status']=='COMPLETE_SAVED_YAW_DIRECTION_DIAGNOSTIC','score complete')
            check(score['generation_receipt_sha256']==a.worker_sha and score['external_receipt_sha256']==a.external_sha,'score generation bindings')
            check(score['source_sha256']==bind['reviewed_files_sha256'][str(D/'score_single_yaw.py')] and score['contract_sha256']==CONTRACT,'score source contract')
            require([x['target_id'] for x in score['targets']]==[20,21,22,23],'all four score rows')
            events={k:[] for k in ['all_valid_matches','common_fov_matches']}
            for ix,row in enumerate(score['targets']):
                ident=row['target_id'];compare(js(D/f'scoring_01/target_{ident}.json'),row,'saved row'+str(ident))
                H,Hi=Hs[ix],inverseHs[ix];pairs=row['same_match_scores']['rows'];N=row['source_feature_count'];M=len(pairs);Nc=row['common_fov_source_feature_count']
                check(M==row['match_count']==len(row['match_keypoint_ids']) and M<=N,'matching count '+str(ident))
                ids=row['match_keypoint_ids'];check(len({x[0] for x in ids})==M and len({x[1] for x in ids})==M and all(0<=x<N and 0<=y<row['new_feature_count'] for x,y in ids),'mutual IDs '+str(ident))
                sets={k:[] for k in events};invalid=0;outside=0
                for j,z in enumerate(pairs):
                    x,y=z['source_xy'],z['new_xy'];validxy=all(v is not None and math.isfinite(v) for v in x+y)
                    p=proj(*x,H) if validxy else None;b=proj(*y,Hi) if validxy else None;valid=p is not None;common=valid and inside(x) and inside(y) and inside(p) and inside(b)
                    e=math.hypot(y[0]-x[0],y[1]-x[1]) if valid else None;f=math.hypot(y[0]-p[0],y[1]-p[1]) if valid else None;delta=e-f if valid else None
                    compare(z,dict(index=j,source_xy=x,new_xy=y,valid=valid,common_fov=common,identity_error_px=e,H_error_px=f,paired_identity_minus_H_px=delta),'pair'+str(ident)+'/'+str(j))
                    invalid+=not valid;outside+=valid and not common
                    if valid:sets['all_valid_matches'].append((e,f,delta))
                    if common:sets['common_fov_matches'].append((e,f,delta))
                computed=dict(match_count=M,invalid_count=invalid,outside_common_fov_count=outside)
                for fam,v in sets.items():
                    cols=list(zip(*v)) if v else [[],[],[]];desc=dict(count=len(v))
                    for k,values in zip(['identity','H','paired_identity_minus_H'],cols):desc[k+'_quantiles_px']=quant(list(values));desc[k+'_maximum_px']=max(values) if values else None
                    desc.update(positive_count=sum(z[2]>0 for z in v),negative_count=sum(z[2]<0 for z in v),zero_count=sum(z[2]==0 for z in v))
                    compare(row['same_match_scores'][fam],desc,'statistics'+str(ident)+'/'+fam)
                    event=None if not v else quant(list(cols[2]))[1]>0;events[fam].append(event);check(row[fam+'_median_direction_positive']==event,'event '+str(ident)+'/'+fam)
                for k,v in computed.items():check(row['same_match_scores'][k]==v,k+str(ident))
                C=len(sets['common_fov_matches']);check(C<=Nc<=N and row['common_fov_matched_count']==C,'recorded common denominator '+str(ident))
                for k,v in dict(unmatched_count=N-M,matched_fraction=M/N if N else None,unmatched_fraction=(N-M)/N if N else None,common_fov_matched_fraction_of_source=C/N if N else None,common_fov_matched_fraction_of_common_source=C/Nc if Nc else None).items():compare(row[k],v,k+str(ident))
                for label,key in [('source_coverage','source_xy'),('new_coverage','new_xy')]:
                    xy=[v[key] for v in pairs];span=[(max(v[j] for v in xy)-min(v[j] for v in xy))/575 for j in range(2)] if xy else None
                    cells={(max(0,min(3,math.floor(v[0]/144))),max(0,min(3,math.floor(v[1]/144)))) for v in xy}
                    compare(row[label],dict(span_xy_fraction=span,occupied_4x4_cells=len(cells)),label+str(ident))
                check(row['old_common_fov_pixels']==int(g['old_common_fov_masks'][ix].sum()) and row['new_common_fov_pixels']==int(g['new_common_fov_masks'][ix].sum()),'row FOV counts'+str(ident))
            expected={k:None if any(v is None for v in vals) else all(vals) for k,vals in events.items()}
            compare(score['descriptive_all4_positive_median_events'],expected,'unknown-first all-four events')
            r['diagnostics']['feature_count_boundary']='N and Nc are recorded SIFT feature counts; unmatched keypoints were not saved, so their extraction/FOV membership cannot be independently rederived. Fractions and consistency are independently checked using these recorded denominators.'
        budget();r['status']='PASS_S76_INDEPENDENT_SAVED_'+a.phase.upper() if not r['blockers'] else 'DISCREPANCIES_PRESERVED'
    except Exception as e:
        r['status']='FAILED_PRESERVED';r['blockers'].append(str(e));r['error']=traceback.format_exc()
    finally:
        r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-t,peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        unique={x['path']:x for x in r['reads']};r['read_totals']=dict(calls=len(r['reads']),unique_files=len(unique),unique_file_bytes=sum(x['bytes'] for x in unique.values()))
        r['limits']='110 seconds internal; caller must enforce 120-second subprocess timeout; sampled self ru_maxrss 2GiB, no hard memory guarantee.'
        r['claim_boundary']='Team independent saved arithmetic, no live model identity observation, model/renderer/SIFT rerun, matching truth validation, camera calibration or exact noise equivariance. Negative/unknown results retained.'
        p=out/'receipt.json'
        with p.open('x') as f:json.dump(r,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
        p.chmod(0o444)
    print(json.dumps(dict(status=r['status'],receipt=str(p),sha256=sha(p.read_bytes()),blockers=r['blockers'])))
    return 0 if r['status'].startswith('PASS_') else 1
if __name__=='__main__':raise SystemExit(main())
