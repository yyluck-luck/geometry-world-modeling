"""S77 independent standard-library saved-coordinate arithmetic; no scientific imports."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,math,resource,statistics,time,traceback
D=Path(__file__).absolute().parents[1]
IDS=[20,21,22,23];ARMS=['real','A0','B'];SWAP={20:23,21:22,22:21,23:20}
CONTRACT='f38eff84ca92a71929d9613a4ca4a3250d76fd32923c37045e96fce77774a040'
SOURCE='b35ba1483d47d39093822bc715aed601522ec3b66ff192210bd56fb73098bacb'
ATOL,RTOL=1e-8,1e-10

def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return sha(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def utc():return datetime.now(timezone.utc).isoformat()
def dot(x,y):return math.fsum(a*b for a,b in zip(x,y))
def cross(x,y):return [x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0]]
def inverse(A):
    M=[list(row)+[float(i==j) for j in range(3)] for i,row in enumerate(A)]
    for j in range(3):
        pivot=max(range(j,3),key=lambda i:abs(M[i][j]));M[j],M[pivot]=M[pivot],M[j]
        scale=M[j][j]
        if scale==0:raise ValueError('Singular intrinsics')
        M[j]=[x/scale for x in M[j]]
        for i in range(3):
            if i!=j:
                scale=M[i][j];M[i]=[x-scale*y for x,y in zip(M[i],M[j])]
    return [x[3:] for x in M]
def quant(v):
    if not v:return None
    if len(v)==1:return v*4
    q=statistics.quantiles(v,n=20,method='inclusive');return [q[i] for i in [4,9,14,18]]
def ds(v):
    return dict(count=len(v),quantiles_px=quant(v),minimum_px=min(v) if v else None,maximum_px=max(v) if v else None,
                positive_count=sum(x>0 for x in v),negative_count=sum(x<0 for x in v),zero_count=sum(x==0 for x in v))
def cov(x):
    return dict(span_xy_fraction=[(max(p[i] for p in x)-min(p[i] for p in x))/575 for i in [0,1]] if x else None,
        occupied_4x4_cells=len({(max(0,min(3,int(math.floor(p[0]/144)))),max(0,min(3,int(math.floor(p[1]/144))))) for p in x}))
def event(v):
    med=[x['quantiles_px'][1] if x['quantiles_px'] is not None else None for x in v]
    return dict(target_ids=IDS,paired_medians_px=med,all4_paired_medians_positive=None if None in med else min(med)>0)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker-sha',required=True);ap.add_argument('--external',required=True);ap.add_argument('--external-sha',required=True);a=ap.parse_args()
    O=D/'independent_result_01'/'execution_01';O.mkdir(exist_ok=False);t=time.monotonic()
    r=dict(schema='s77-independent-stdlib-arithmetic-v1',status='RUNNING',started_utc=utc(),reviewer_role='/root/c2_v9_source_primary',source_sha256=sha(Path(__file__).read_bytes()),reads=[],checks=[],pairs=[],events={},shared_support=[],derived_F={},blockers=[],tolerances=dict(atol=ATOL,rtol=RTOL,F_atol=1e-12),new_method_validated=False)
    def check(ok,name,detail=None):
        r['checks'].append(dict(name=name,pass_=bool(ok),detail=detail))
        if not ok:r['blockers'].append(name)
    def need(ok,name):
        check(ok,name)
        if not ok:raise ValueError(name)
    def budget():
        if time.monotonic()-t>50:raise RuntimeError('50-second internal budget')
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>1024**3:raise RuntimeError('1GiB sampled self-peak budget')
    def read(p,h=None):
        budget();p=Path(p);b=p.read_bytes();actual=sha(b);r['reads'].append(dict(path=str(p),bytes=len(b),sha256=actual))
        if h:need(actual==h,'pin:'+str(p))
        return b
    def js(p,h=None):return json.loads(read(p,h))
    def cmp(x,y,name,atol=ATOL,rtol=RTOL):
        if isinstance(x,dict):
            need(isinstance(y,dict),name+' type');check(set(x)==set(y),name+' keys')
            for k in x.keys()&y.keys():cmp(x[k],y[k],name+'/'+k,atol,rtol)
        elif isinstance(x,list):
            need(isinstance(y,list),name+' type');check(len(x)==len(y),name+' length')
            for i,(u,v) in enumerate(zip(x,y)):cmp(u,v,name+'/'+str(i),atol,rtol)
        elif isinstance(x,float):check(isinstance(y,(int,float)) and math.isfinite(x) and math.isfinite(y) and math.isclose(x,y,abs_tol=atol,rel_tol=rtol),name,dict(derived=x,saved=y))
        else:check(x==y,name)
    try:
        c=js(D/'CONTRACT.json',CONTRACT);read(D/'measure.py',SOURCE)
        w=js(D/'execution_01/receipt.json',a.worker_sha);e=js(a.external,a.external_sha)
        need(e.get('returncode')==0 and not e.get('timeout',e.get('timed_out',False)),'external success')
        need(w['status']=='COMPLETE_S77_FIXED_GENERATED_WRONG_LABEL_DIAGNOSTIC','worker completed')
        check(w['source_sha256']==SOURCE and w['contract_sha256']==CONTRACT,'worker source/contract')
        check(all(w[k]==0 for k in ['new_images','new_features','new_models','depth_reads']) and w['new_method_validated'] is False,'no new scientific operations')
        parents={k:js(c[k]['path'],c[k]['sha256']) for k in ['s73_acceptance','s74_acceptance','s72_acceptance','s73_contract','s74_contract','s73_receipt','s74_receipt','s74_separation']}
        old=parents['s73_receipt'];real=parents['s74_receipt'];separation=parents['s74_separation']
        expected_reads=[dict(path=c[k]['path'],sha256=c[k]['sha256']) for k in ['s73_acceptance','s74_acceptance','s72_acceptance','s73_contract','s74_contract','s73_receipt','s74_receipt','s74_separation']]
        check([dict(path=x['path'],sha256=x['sha256']) for x in w['reads']]==expected_reads,'actual worker complete read order')
        for stage,pathkey,receiptkey in [('s73','execution_02/receipt.json','s73_receipt'),('s74','execution_01/receipt.json','s74_receipt')]:check(parents[stage+'_acceptance']['files_sha256'][pathkey]==c[receiptkey]['sha256'],'parent acceptance '+stage)
        check(parents['s74_acceptance']['files_sha256']['execution_01/geometry_separation.json']==c['s74_separation']['sha256'],'accepted separation')
        # Original camera/K values in accepted S72 JSON were independently bound to raw NPZ in S72.
        c72=c['s72_receipt_identity'];s72=js(c72['path'],c72['sha256']);a72=parents['s72_acceptance']
        check(a72['files_sha256']['execution_01/receipt.json']==c72['sha256'],'S72 camera JSON accepted')
        old_review=js(Path(c72['path']).parents[1]/'independent_result_01/receipt.json',a72['files_sha256']['independent_result_01/receipt.json'])
        need(old_review['status']=='PASS_S72_INDEPENDENT_ARITHMETIC' and not old_review['blockers'],'prior raw-NPZ camera binding accepted')
        K=s72['K_pixels_576'];poses={int(k):v for k,v in s72['optical_c2ws_used'].items()};Ki=inverse(K)
        Rs=[x[:3] for x in poses[19][:3]];source=[[dot(row,[Ki[k][j] for k in range(3)]) for row in Rs] for j in range(3)]
        Fs={}
        for j in IDS:
            Rt=[x[:3] for x in poses[j][:3]];base=[poses[19][k][3]-poses[j][k][3] for k in range(3)]
            target=[[dot(row,[Ki[k][i] for k in range(3)]) for row in Rt] for i in range(3)]
            raw=[[dot(target[i],cross(base,source[k])) for k in range(3)] for i in range(3)];norm=math.sqrt(math.fsum(v*v for row in raw for v in row))
            need(norm>0 and math.hypot(*base)>1e-9,'nonzero camera baseline '+str(j));Fs[j]=[[v/norm for v in row] for row in raw];r['derived_F'][str(j)]=Fs[j]
        sep={x['target_id']:x for x in separation['pairs']};saved_sep=js(D/'execution_01/geometry_separation.json')
        check(saved_sep['pairs']==separation['pairs']==w['source_geometry_separation_reused']['pairs'],'separation exact reuse')
        check(saved_sep['source_sha256']==c['s74_separation']['sha256'],'separation source binding')
        check(w['started_utc']<=saved_sep['recorded_before_generated_residuals_utc']<=w['completed_utc'],'pre-residual separation timestamp')
        for j in IDS:
            k=SWAP[j];S=sep[j];check(S['wrong_pose_label']==k,'swap '+str(j));cmp(Fs[j],S['normalized_F_correct'],'correctF '+str(j),1e-12);cmp(Fs[k],S['normalized_F_wrong'],'wrongF '+str(j),1e-12)
            minus=math.sqrt(math.fsum((Fs[j][u][v]-Fs[k][u][v])**2 for u in range(3) for v in range(3)));plus=math.sqrt(math.fsum((Fs[j][u][v]+Fs[k][u][v])**2 for u in range(3) for v in range(3)))
            cmp([minus,plus,min(minus,plus)],[S['difference_norm'],S['sum_norm'],S['separation']],'Fseparation '+str(j),1e-12)
        def distances(F,x,y):
            # Nine-term bilinear numerator, square-root sums for line lengths; no author function.
            X=x+[1.];Y=y+[1.];n=abs(math.fsum(F[i][j]*Y[i]*X[j] for i in range(3) for j in range(3)))
            lt=[dot(F[i],X) for i in range(2)];ls=[math.fsum(F[j][i]*Y[j] for j in range(3)) for i in range(2)]
            a=math.sqrt(lt[0]*lt[0]+lt[1]*lt[1]);b=math.sqrt(ls[0]*ls[0]+ls[1]*ls[1])
            if not all(map(math.isfinite,[n,a,b])) or a<=1e-12 or b<=1e-12:return None
            return [n/a,n/b,(n/a+n/b)/2]
        N=old['anchor_count'];check(N==w['anchor_population']==real['anchor_population'] and len(old['anchor_xy'])==N,'anchor population')
        oldrows={(x['arm'],x['target_id']):x for x in old['pairs']};rows={(x['arm'],x['target_id']):x for x in w['pairs']};rr={x['target_id']:x for x in real['pairs']}
        keys={(arm,j) for arm in ARMS for j in IDS};need(set(rows)==set(oldrows)==keys and len(w['pairs'])==len(old['pairs'])==12,'all12 rows')
        check([(x['arm'],x['target_id']) for x in w['pairs']]==[(arm,j) for arm in ARMS for j in IDS],'fixed row order')
        def stats(vals):
            v=[x[2] for x in vals if x is not None];M=len(vals);V=len(v);counts={str(q):sum(x<=q for x in v) for q in [2,5,10]}
            return dict(valid_count=V,invalid_count=M-V,quantiles_px=quant(v),maximum_px=max(v) if v else None,threshold_counts=counts,
                fractions_of_matches={k:n/M if M else None for k,n in counts.items()},fractions_of_valid={k:n/V if V else None for k,n in counts.items()},fractions_of_anchor={k:n/N for k,n in counts.items()})
        independent={}
        for arm in ARMS:
            for j in IDS:
                budget();z=rows[arm,j];before=oldrows[arm,j];tag=arm+str(j);M=before['match_count'];ids=before['match_keypoint_ids'];x=before['source_xy'];y=before['target_xy']
                for k in ['match_count','match_keypoint_ids','source_xy','target_xy','source_coverage','target_coverage']:check(z[k]==before[k],'exact original '+tag+'/'+k)
                check(z['correct_residuals_reused']==before['residuals'],'correct reuse '+tag);check(z['coordinates_ids_sha256']==canon(dict(ids=ids,source_xy=x,target_xy=y)),'coordinate identity '+tag)
                check(len(x)==len(y)==len(ids)==M and len({i for i,k in ids})==M and all(0<=i<N and old['anchor_xy'][i]==p for (i,k),p in zip(ids,x)),'match cardinality '+tag)
                correct=[distances(Fs[j],p,q) for p,q in zip(x,y)];wrong=[distances(Fs[SWAP[j]],p,q) for p,q in zip(x,y)]
                if arm=='real':check(z['wrong_residuals']==rr[j]['wrong_residuals'],'real wrong exact reuse '+tag)
                check(z['real_wrong_residuals_reused']==(arm=='real') and z['wrong_pose_label']==SWAP[j] and z['source_frame_id']==19,'row provenance '+tag)
                cmp(correct,z['correct_residuals_reused'],'all correct distances '+tag);cmp(wrong,z['wrong_residuals'],'all wrong distances '+tag)
                common=[i for i in range(M) if correct[i] is not None and wrong[i] is not None];S=set(common);raw=[wrong[i][2]-correct[i][2] if i in S else None for i in range(M)];v=[raw[i] for i in common]
                expect=dict(correct_invalid_indices=[i for i,a in enumerate(correct) if a is None],wrong_invalid_indices=[i for i,a in enumerate(wrong) if a is None],common_valid_indices=common,common_valid_count=len(common),invalid_in_either_count=M-len(common),common_valid_anchor_fraction=len(common)/N,
                    matched_anchor_fraction=M/N,unmatched_anchor_count=N-M,source_image_domain_count=sum(all(0<=a<576 for a in p) for p in x),target_image_domain_count=sum(all(0<=a<576 for a in p) for p in y),raw_deltas_wrong_minus_correct_px=raw,paired_delta=ds(v),correct=stats(correct),wrong=stats(wrong),common_source_coverage=cov([x[i] for i in common]))
                for k,a in expect.items():cmp(a,z[k],tag+'/'+k)
                cmp(cov(x),z['source_coverage'],tag+'/source coverage');cmp(cov(y),z['target_coverage'],tag+'/target coverage')
                independent[arm,j]=dict(correct=correct,wrong=wrong,raw=raw,paired_delta=ds(v));r['pairs'].append(dict(arm=arm,target_id=j,match_count=M,common_valid_count=len(common),correct=stats(correct),wrong=stats(wrong),paired_delta=ds(v)))
        check(w['original_shared_support']==old['shared_support'],'original shared-support entire object')
        shared=[]
        for original,saved in zip(old['shared_support'],w['shared_support']):
            j=original['target_id'];maps={arm:{i:k for k,(i,_) in enumerate(oldrows[arm,j]['match_keypoint_ids'])} for arm in ARMS};raw=sorted(set.intersection(*(set(z) for z in maps.values())))
            cids=[i for i in raw if all(independent[arm,j]['correct'][maps[arm][i]] is not None for arm in ARMS)]
            six=[i for i in cids if all(independent[arm,j]['wrong'][maps[arm][i]] is not None for arm in ARMS)]
            check(raw==original['raw_intersection_ids'] and cids==original['common_valid_ids'],'reconstructed original support '+str(j))
            row=dict(target_id=j,original_raw_intersection_ids=raw,original_correct_common_valid_ids=cids,original_correct_common_valid_count=len(cids),new_all_six_valid_ids=six,new_all_six_valid_count=len(six),new_wrong_invalid_on_original_correct_ids=sorted(set(cids)-set(six)),all_six_valid_anchor_fraction=len(six)/N,all_six_source_coverage=cov([old['anchor_xy'][i] for i in six]),arms={})
            for arm in ARMS:
                good=[i for i in cids if independent[arm,j]['wrong'][maps[arm][i]] is not None]
                row['arms'][arm]=dict(original_common_source_ids=cids,valid_on_original_common_ids=good,wrong_invalid_count_on_original_common=len(cids)-len(good),on_original_common=ds([independent[arm,j]['raw'][maps[arm][i]] for i in good]),on_all_six_valid=ds([independent[arm,j]['raw'][maps[arm][i]] for i in six]))
            cmp(row,saved,'secondary '+str(j));shared.append(row)
        need(len(shared)==4 and [x['target_id'] for x in w['shared_support']]==IDS,'all four secondary rows');r['shared_support']=shared
        for arm in ARMS:
            r['events'][arm]=dict(primary_same_matches=event([independent[arm,j]['paired_delta'] for j in IDS]),secondary_original_three_arm_support=event([x['arms'][arm]['on_original_common'] for x in shared]),secondary_all_six_valid=event([x['arms'][arm]['on_all_six_valid'] for x in shared]))
        cmp(r['events'],w['events'],'all nine null-first events')
        check(w['scope']==c['scope'] and w['limits']==c['limits'],'recorded claim boundaries')
        budget();r['status']='PASS_S77_INDEPENDENT_STDLIB_ARITHMETIC' if not r['blockers'] else 'DISCREPANCIES_PRESERVED'
    except Exception as ex:r.update(status='FAILED_PRESERVED',error_type=type(ex).__name__,error=str(ex),traceback=traceback.format_exc());r['blockers'].append(str(ex))
    finally:
        unique={x['path']:x for x in r['reads']};r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-t,peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checks_passed=sum(x['pass_'] for x in r['checks']),input_calls=len(r['reads']),unique_input_files=len(unique),unique_input_bytes=sum(x['bytes'] for x in unique.values()),scope='JSON-only; accepted original camera/K values in S72 JSON previously bound to original NPZ by S72 independent review. Scalar world-ray F reconstruction, same-coordinate residuals and all support/statistics/events; no original NPZ body re-read, image/model/SIFT/depth, author code imports or extra permutation. Team arithmetic verification, not match truth, calibration, causal mechanism or method validation.')
        p=O/'receipt.json'
        with p.open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
        p.chmod(0o444)
    print(json.dumps(dict(status=r['status'],receipt=str(p),sha256=sha(p.read_bytes()),blockers=r['blockers'],checks_passed=r['checks_passed'])))
    return 0 if r['status'].startswith('PASS_') else 1
if __name__=='__main__':raise SystemExit(main())
