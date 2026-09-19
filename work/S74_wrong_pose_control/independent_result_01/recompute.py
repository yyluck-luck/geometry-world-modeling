"""Independent S74 scalar world-ray verification; no feature/model execution."""
from pathlib import Path
from datetime import datetime,timezone
import math,json,hashlib,io,time,traceback,sys
O=Path(__file__).resolve().parent
D=O.parent
S72=D.parent/'S72_fixed_requested_geometry'
ATOL,RTOL=1e-8,1e-10
S72_HELPER_SHA='856e6f6295809415238bac520acddb8114fdcc0604cb5369c11feea4fdbe1eac'

def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b))

def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]

def col(a, j):
    return [row[j] for row in a]

def inverse(a):
    # Scalar Gauss-Jordan with pivoting, independent of NumPy inverse.
    work = [list(row) + [float(i == j) for j in range(3)] for i, row in enumerate(a)]
    for j in range(3):
        k = max(range(j, 3), key=lambda i: abs(work[i][j]))
        work[k], work[j] = work[j], work[k]
        pivot = work[j][j]
        if pivot == 0:
            raise ValueError('Singular K')
        work[j] = [v/pivot for v in work[j]]
        for i in range(3):
            if i != j:
                factor = work[i][j]
                work[i] = [v-factor*u for v, u in zip(work[i], work[j])]
    return [row[3:] for row in work]

def quantile(values, q):
    v = sorted(values)
    at = q*(len(v)-1)
    lo, hi = math.floor(at), math.ceil(at)
    return v[lo]*(hi-at) + v[hi]*(at-lo) if hi != lo else v[lo]

def flatten(v):
    return [x for item in v for x in flatten(item)] if isinstance(v, list) else [v]

def coverage(points):
    return {'span_xy_fraction': [(max(p[j] for p in points)-min(p[j] for p in points))/575
                                 for j in range(2)] if points else None,
            'occupied_4x4_cells': len({tuple(max(0, min(3, math.floor(v/144))) for v in p)
                                      for p in points})}

def utc():return datetime.now(timezone.utc).isoformat()
def run(r):
    import numpy as np
    r['numpy_version']=np.__version__
    def check(name,ok,detail=None):r['checks'].append({'name':name,'pass':bool(ok),'detail':detail})
    def read(p,h=None,kind='metadata'):
        p=Path(p);b=p.read_bytes();digest=hashlib.sha256(b).hexdigest();r['reads'].append(dict(path=str(p),bytes=len(b),sha256=digest,kind=kind))
        if h:
            check('pin/'+str(p),digest==h)
            if digest!=h:raise ValueError('Changed pin '+str(p))
        return b
    def js(p,h=None):return json.loads(read(p,h))
    def cmp(name,a,b,atol=ATOL,rtol=RTOL):
        if a is None or b is None:check(name,a is None and b is None);return
        av,bv=flatten(a),flatten(b);bad=[i for i,(x,y) in enumerate(zip(av,bv)) if not(math.isfinite(x) and math.isfinite(y) and math.isclose(x,y,abs_tol=atol,rel_tol=rtol))]
        check(name,len(av)==len(bv) and not bad,dict(count=len(av),saved_count=len(bv),mismatch_indices=bad,max_abs_difference=max((abs(x-y) for x,y in zip(av,bv)),default=0),atol=atol,rtol=rtol))
    c=js(D/'CONTRACT.json','3912bf3317b36b0c57274e931cebb77f65b4aafeab305d4b1c9462bb0ced25ce')
    w=js(D/'execution_01/receipt.json','3e7c878265a7ff124a15f15db378ab2e71e2648a9d769bc424cfae5d09503c37')
    sep=js(D/'execution_01/geometry_separation.json','a1def36bdf29d136a5182633e5a39d7c98c2705d3a5e7d81e03176e853483caa')
    e=js(D/'external_01/receipt.json','fc2916cd5a21b92d50fef320a28765c142f110f80f2e7edef0914700f9d42124')
    st=js(D/'external_01/started.json','03c9319b5a4c7d5e79273c7a1cb6771203f0a07133a898cb87b7064fdae61310')
    out=js(D/'external_01/stdout.txt');err=read(D/'external_01/stderr.txt')
    read(D/'measure.py','e41c8e5e79c2ddac70ee6e93559e83f89805d14bff7526f429e5be256cc2865c','source_identity_only')
    ac=js(c['real_acceptance']['path'],c['real_acceptance']['sha256']);old=js(c['real_receipt']['path'],c['real_receipt']['sha256'])
    c72=js(S72/'CONTRACT_v2.json','14e72eafa5131a3734fa9386f7ae073bb9ccf72b9be9223e9655c30099910940')
    check('terminal_and_logs',e['returncode']==0 and not e['timed_out'] and not err and w['status']=='COMPLETE_FIXED_WRONG_LABEL_DIAGNOSTIC' and out['status']==w['status'] and out['completed_utc']==w['completed_utc'])
    check('actual_lexical_argv',st['argv']==[str(D.parents[1]/'.venv-cut3r/bin/python'),'-B',str(D/'measure.py'),w['contract_sha256']] and st['timeout_seconds']==c['budget']['external_seconds']==30)
    check('source_contract_scope',w['source_sha256']=='e41c8e5e79c2ddac70ee6e93559e83f89805d14bff7526f429e5be256cc2865c' and w['contract_sha256']=='3912bf3317b36b0c57274e931cebb77f65b4aafeab305d4b1c9462bb0ced25ce' and w['model_calls']==0 and w['weight_bytes']==0 and w['new_method_validated'] is False)
    check('accepted_S72',ac['status']=='ACCEPTED_S72_REAL_CONTROL_ARITHMETIC_ONLY' and ac['files_sha256']['execution_01/receipt.json']==c['real_receipt']['sha256'])
    check('fixed_swap_and_order',c['swap']=={'20':23,'21':22,'22':21,'23':20} and [p['target_id'] for p in w['pairs']]==[20,21,22,23])
    check('separation_file_consistency',sep['pairs']==w['separations'] and sep['contract_sha256']==w['contract_sha256'])
    check('separation_timestamp_order',e['started_utc']==st['started_utc'] and e['started_utc']<=w['started_utc']<=sep['recorded_before_residuals_utc']<=w['completed_utc']<=e['completed_utc'])
    ar=c72['camera_archive']
    with np.load(io.BytesIO(read(ar['path'],ar['sha256'],'camera_NPZ')),allow_pickle=False) as z:ids,ca=z['ids'].copy(),z['c2ws'].copy()
    for name,a in [('ids',ids),('c2ws',ca)]:
        d=ar['fields'][name];check('camera_descriptor/'+name,list(a.shape)==d['shape'] and str(a.dtype)==d['dtype'] and a.nbytes==d['body_bytes'] and hashlib.sha256(a.tobytes(order='C')).hexdigest()==d['body_sha256']);r['decoded_fields'].append(dict(field=name,bytes=a.nbytes))
    poses=dict(zip(ids.tolist(),ca.tolist()));check('camera_IDs',ids.tolist()==[12,13,14,18,19,20,21,22,23])
    kr=c72['anchor_K_cache']
    with np.load(io.BytesIO(read(kr['path'],kr['sha256'],'K_container_only')),allow_pickle=False) as z:ka=z['K_pixels_576'].copy()
    check('K_descriptor',ka.shape==(3,3) and str(ka.dtype)=='float32' and hashlib.sha256(ka.tobytes(order='C')).hexdigest()=='af06e3d3809815c458f03778db3349a6c907d83d5877a75cd8bbd0064122d582');r['decoded_fields'].append(dict(field='K_pixels_576',bytes=ka.nbytes))
    K=ka.tolist();Ki=inverse(K);C0=poses[19];Rs=[x[:3] for x in C0[:3]]
    source_bases=[[dot(row,col(Ki,j)) for row in Rs] for j in range(3)];Fs={}
    for j in c['target_ids']:
        Ct=poses[j];Rt=[x[:3] for x in Ct[:3]];baseline=[C0[i][3]-Ct[i][3] for i in range(3)]
        target_bases=[[dot(row,col(Ki,i)) for row in Rt] for i in range(3)]
        raw=[[dot(target_bases[i],cross(baseline,source_bases[k])) for k in range(3)] for i in range(3)]
        norm=math.sqrt(math.fsum(v*v for v in flatten(raw)));Fs[j]=[[v/norm for v in row] for row in raw]
        check(str(j)+'/geometry_defined',norm>0 and math.hypot(*baseline)>c72['baseline_insufficient_m']);r['derived_F'][str(j)]=dict(Fraw=raw,F_unit=Fs[j],baseline_m=math.hypot(*baseline))
    for saved in sep['pairs']:
        j,k=saved['target_id'],saved['wrong_pose_label'];check(f'{j}/wrong_label',k==c['swap'][str(j)])
        A,B=Fs[j],Fs[k]
        minus=math.sqrt(math.fsum((a-b)**2 for a,b in zip(flatten(A),flatten(B))))
        plus=math.sqrt(math.fsum((a+b)**2 for a,b in zip(flatten(A),flatten(B))))
        distance=min(minus,plus)
        cmp(f'{j}/correct_F',A,saved['normalized_F_correct'],1e-12,1e-10);cmp(f'{j}/wrong_F',B,saved['normalized_F_wrong'],1e-12,1e-10)
        cmp(f'{j}/separation_norms',[minus,plus,distance],[saved['difference_norm'],saved['sum_norm'],saved['separation']],1e-12,1e-10)
        check(f'{j}/exact_zero_flag',(distance==0)==saved['float_exact_zero'])
        r['separations'].append(dict(target_id=j,wrong_pose_label=k,difference_norm=minus,sum_norm=plus,separation=distance))
    def residuals(F,x,y):
        result=[]
        for a,b in zip(x,y):
            xh,yh=a+[1.],b+[1.];lt=[dot(row,xh) for row in F];ls=[dot(col(F,i),yh) for i in range(3)]
            q=dot(yh,lt);nt,ns=math.hypot(*lt[:2]),math.hypot(*ls[:2])
            if all(math.isfinite(v) for v in [q,nt,ns]) and min(nt,ns)>c['line_epsilon']:
                dt,ds=abs(q)/nt,abs(q)/ns;result.append([dt,ds,(dt+ds)/2])
            else:result.append(None)
        return result
    def statistics(values):
        means=[v[2] for v in values if v is not None];M,V=len(values),len(means)
        counts={str(q):sum(v<=q for v in means) for q in c['cutoffs_px']}
        return dict(valid_count=V,invalid_count=M-V,quantiles_px=[quantile(means,q) for q in c['quantiles']] if means else None,maximum_px=max(means) if means else None,threshold_counts=counts,fractions_of_matches={k:v/M if M else None for k,v in counts.items()},fractions_of_valid={k:v/V if V else None for k,v in counts.items()})
    by={p['target_id']:p for p in old['pairs']};N=old['anchor_keypoints'];check('anchor_population',N==w['anchor_population'])
    check('all638_preserved',sum(p['match_count'] for p in w['pairs'])==sum(p['match_count'] for p in old['pairs'])==638)
    medians=[]
    for p in w['pairs']:
        j,k=p['target_id'],c['swap'][str(p['target_id'])];tag=f'{j}/';ref=by[j];x,y=p['source_xy'],p['target_xy'];M=p['match_count']
        check(tag+'unchanged_IDs_xy_count',p['wrong_pose_label']==k and all(p[key]==ref[key] for key in ['match_count','match_keypoint_ids','source_xy','target_xy','source_coverage','target_coverage']) and len(x)==len(y)==len(p['match_keypoint_ids'])==M)
        check(tag+'correct_residuals_exact_reuse',p['correct_residuals_reused']==ref['residuals'])
        check(tag+'xy_valid',all(len(a)==2 and all(math.isfinite(v) and 0<=v<576 for v in a) for a in x+y))
        cmp(tag+'availability_M_over_N',M/N,p['matched_anchor_fraction'],0,0)
        correct,wrong=residuals(Fs[j],x,y),residuals(Fs[k],x,y)
        for name,values,saved in [('correct',correct,p['correct_residuals_reused']),('wrong',wrong,p['wrong_residuals'])]:
            check(tag+name+'_null_mask',[v is None for v in values]==[v is None for v in saved])
            cmp(tag+name+'_every_distance',[v for v in values if v is not None],[v for v in saved if v is not None])
            stat=statistics(values);oldstat=p[name]
            check(tag+name+'_counts_and_denominators',all(stat[key]==oldstat[key] for key in ['valid_count','invalid_count','threshold_counts','fractions_of_matches','fractions_of_valid']))
            cmp(tag+name+'_quantiles',stat['quantiles_px'],oldstat['quantiles_px']);cmp(tag+name+'_max',stat['maximum_px'],oldstat['maximum_px'])
        common=[i for i in range(M) if correct[i] is not None and wrong[i] is not None]
        check(tag+'common_indices_counts',common==p['common_valid_indices'] and len(common)==p['common_valid_count'] and M-len(common)==p['invalid_in_either_count'])
        for name,points in [('source',x),('target',y)]:
            cov=coverage(points);cmp(tag+name+'_span',cov['span_xy_fraction'],p[name+'_coverage']['span_xy_fraction']);check(tag+name+'_cells',cov['occupied_4x4_cells']==p[name+'_coverage']['occupied_4x4_cells'])
        check(tag+'common_source_cells',coverage([x[i] for i in common])['occupied_4x4_cells']==p['common_source_cells'])
        delta=[wrong[i][2]-correct[i][2] for i in common];qs=[quantile(delta,q) for q in c['quantiles']] if delta else None
        cmp(tag+'all_paired_deltas',delta,p['deltas_wrong_minus_correct_px']);cmp(tag+'paired_quantiles',qs,p['delta_quantiles_px'])
        signs=[sum(v>0 for v in delta),sum(v<0 for v in delta),sum(v==0 for v in delta)]
        check(tag+'strict_signs',signs==[p['positive_count'],p['negative_count'],p['zero_count']])
        medians.append(qs[1] if qs else None);r['pairs'].append(dict(target_id=j,wrong_pose_label=k,match_count=M,correct_residuals=correct,wrong_residuals=wrong,correct=statistics(correct),wrong=statistics(wrong),common_valid_indices=common,delta=delta,delta_quantiles=qs,sign_counts=signs))
    event=None if None in medians else min(medians)>0
    check('event_unknown_precedence_and_strict_sign',event is w['event']['all4_paired_medians_positive'])
    for i,(a,b) in enumerate(zip(medians,w['event']['paired_medians_px'])):cmp(f'event_median/{i}',a,b)
    r['event']=dict(all4_paired_medians_positive=event,paired_medians_px=medians)
    check('actual_worker_readlist',[(p['path'],p['sha256']) for p in w['reads']]==[(c[n]['path'],c[n]['sha256']) for n in ['real_acceptance','real_receipt']])

if __name__=='__main__':
    start=utc();timer=time.perf_counter();r=dict(schema='s74-independent-wrong-label-arithmetic-v1',status='RUNNING',reviewer_role='/root/c2_v9_source_primary',started_utc=start,python=sys.version,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),reused_own_S72_helper_source_sha256=S72_HELPER_SHA,reads=[],decoded_fields=[],checks=[],derived_F={},separations=[],pairs=[],event=None,blockers=[],new_method_validated=False,scope='Scalar world-ray original-camera/K rederivation and saved-coordinate arithmetic only; NumPy NPZ I/O. No images, SIFT, model/weight reads, author-function import or alternative permutation.')
    with (O/'receipt.json').open('x') as f:
        try:
            run(r);r['blockers']=[x['name'] for x in r['checks'] if not x['pass']];r['status']='PASS_S74_INDEPENDENT_ARITHMETIC' if not r['blockers'] else 'DISCREPANCY_PRESERVED'
        except BaseException:r['status']='FAILED_PRESERVED';r['exception']=traceback.format_exc();r['blockers'].append('exception')
        r.update(completed_utc=utc(),elapsed_seconds=time.perf_counter()-timer,checks_passed=sum(x['pass'] for x in r['checks']),input_file_count=len(r['reads']),input_bytes=sum(x['bytes'] for x in r['reads']),decoded_array_bytes=sum(x['bytes'] for x in r['decoded_fields']))
        json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
    (O/'receipt.json').chmod(0o444)
    print(json.dumps({k:r[k] for k in ['status','checks_passed','blockers','elapsed_seconds','input_file_count','input_bytes','decoded_array_bytes']}))
    raise SystemExit(0 if not r['blockers'] else 1)
