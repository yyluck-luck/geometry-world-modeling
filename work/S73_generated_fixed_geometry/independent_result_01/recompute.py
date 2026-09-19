"""S73 independent saved-coordinate arithmetic; no image/feature/model code."""
from pathlib import Path
from datetime import datetime, timezone
import math, json, hashlib, io, time, traceback, sys
O=Path(__file__).resolve().parent
D=O.parent
S72=D.parent/'S72_fixed_requested_geometry'
ATOL,RTOL=1e-8,1e-10
S72_HELPER_SOURCE_SHA='856e6f6295809415238bac520acddb8114fdcc0604cb5369c11feea4fdbe1eac'

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

def utc(): return datetime.now(timezone.utc).isoformat()

def run(r):
    import numpy as np
    r['numpy_version']=np.__version__
    def check(name,ok,detail=None):r['checks'].append(dict(name=name,pass_=bool(ok),detail=detail))
    def read(p,h=None,kind='metadata'):
        p=Path(p);b=p.read_bytes();digest=hashlib.sha256(b).hexdigest()
        r['reads'].append(dict(path=str(p),bytes=len(b),sha256=digest,kind=kind))
        if h:
            check('pin/'+str(p),digest==h)
            if digest!=h:raise ValueError('Pinned identity changed '+str(p))
        return b
    def js(p,h=None):return json.loads(read(p,h))
    def cmp(name,a,b,atol=ATOL,rtol=RTOL):
        if a is None or b is None:
            check(name,a is None and b is None);return
        aa,bb=flatten(a),flatten(b)
        bad=[i for i,(x,y) in enumerate(zip(aa,bb)) if not(math.isfinite(x) and math.isfinite(y) and math.isclose(x,y,abs_tol=atol,rel_tol=rtol))]
        check(name,len(aa)==len(bb) and not bad,dict(count=len(aa),saved_count=len(bb),mismatch_indices=bad,max_abs_difference=max((abs(x-y) for x,y in zip(aa,bb)),default=0),atol=atol,rtol=rtol))
    w=js(D/'execution_02/receipt.json','8a953c7a477ddbc84721be4fe6f9974e923a45cd6718c840a2dfb149b958ba01')
    c=js(D/'CONTRACT.json','45fd78cb09ec53704d35ca07d789b75477276c48adc0ef1919ef6105e513028a')
    e=js(D/'external_02/receipt.json','1a43c28cae56430ea1454237241835277751c31be543d98ec0892eb530b2a630')
    start=js(D/'external_02/started.json','76858a30a605cdd9f940ac4efc622b0b18fe0807c3e1b64fdccacfa125b652f1')
    logs=js(D/'external_02/stdout.txt');stderr=read(D/'external_02/stderr.txt')
    read(D/'measure_v2.py','eadff2d2628402ed474dd54a1179f8d73d6240439d4d8c67f610a82b5df4c65b','source_identity_only')
    accepted=js(c['real_acceptance']['path'],c['real_acceptance']['sha256'])
    old=js(c['real_receipt']['path'],c['real_receipt']['sha256'])
    c72=js(S72/'CONTRACT_v2.json','14e72eafa5131a3734fa9386f7ae073bb9ccf72b9be9223e9655c30099910940')
    check('actual_v2_terminal',e['returncode']==0 and not e['timed_out'] and w['status']=='COMPLETE_EXISTING_GENERATED_GEOMETRY_DIAGNOSTIC' and not stderr and logs['status']==w['status'] and logs['completed_utc']==w['completed_utc'])
    check('corrected_lexical_venv_argv',start['argv']==[str(D.parents[1]/'.venv-cut3r/bin/python'),'-B',str(D/'measure_v2.py'),w['contract_sha256']] and start['timeout_seconds']==60)
    check('time_order',e['started_utc']==start['started_utc'] and e['started_utc']<=w['started_utc']<=w['completed_utc']<=e['completed_utc'])
    check('source_contract',w['source_sha256']=='eadff2d2628402ed474dd54a1179f8d73d6240439d4d8c67f610a82b5df4c65b' and w['contract_sha256']=='45fd78cb09ec53704d35ca07d789b75477276c48adc0ef1919ef6105e513028a')
    check('scope',w['model_calls']==0 and w['weight_bytes']==0 and not w['new_method_validated'] and w['versions']==c['versions'])
    check('accepted_real_binding',accepted['status']=='ACCEPTED_S72_REAL_CONTROL_ARITHMETIC_ONLY' and accepted['files_sha256']['execution_01/receipt.json']==c['real_receipt']['sha256'])
    ar=c72['camera_archive']
    with np.load(io.BytesIO(read(ar['path'],ar['sha256'],'camera_NPZ')),allow_pickle=False) as z: ids,ca=z['ids'].copy(),z['c2ws'].copy()
    for name,arr in [('ids',ids),('c2ws',ca)]:
        d=ar['fields'][name]
        check('camera_descriptor/'+name,list(arr.shape)==d['shape'] and str(arr.dtype)==d['dtype'] and arr.nbytes==d['body_bytes'] and hashlib.sha256(arr.tobytes(order='C')).hexdigest()==d['body_sha256'])
        r['decoded_fields'].append(dict(path=ar['path'],field=name,bytes=arr.nbytes))
    poses=dict(zip(ids.tolist(),ca.tolist()));check('camera_ids',ids.tolist()==[12,13,14,18,19,20,21,22,23])
    kr=c72['anchor_K_cache']
    with np.load(io.BytesIO(read(kr['path'],kr['sha256'],'K_container_only')),allow_pickle=False) as z:ka=z['K_pixels_576'].copy()
    check('K_descriptor',ka.shape==(3,3) and str(ka.dtype)=='float32' and hashlib.sha256(ka.tobytes(order='C')).hexdigest()=='af06e3d3809815c458f03778db3349a6c907d83d5877a75cd8bbd0064122d582')
    r['decoded_fields'].append(dict(path=kr['path'],field='K_pixels_576',bytes=ka.nbytes))
    K=ka.tolist();check('K_finite',all(math.isfinite(x) for x in flatten(K)));Ki=inverse(K)
    C0=poses[19];Rs=[row[:3] for row in C0[:3]]
    source_bases=[[dot(row,col(Ki,j)) for row in Rs] for j in range(3)]
    Fs={}
    for j in c['target_ids']:
        Ct=poses[j];Rt=[row[:3] for row in Ct[:3]];baseline=[C0[i][3]-Ct[i][3] for i in range(3)]
        target_bases=[[dot(row,col(Ki,i)) for row in Rt] for i in range(3)]
        raw=[[dot(target_bases[i],cross(baseline,source_bases[k])) for k in range(3)] for i in range(3)]
        norm=math.sqrt(math.fsum(v*v for v in flatten(raw)));Fs[j]=[[v/norm for v in row] for row in raw]
        check(str(j)+'/baseline_defined',math.hypot(*baseline)>c72['baseline_insufficient_m'] and norm>0)
        r['derived_F'][str(j)]=dict(Fraw=raw,norm=norm,F_unit=Fs[j])
    N=w['anchor_count'];axy=w['anchor_xy'];oldreal={p['target_id']:p for p in old['pairs']}
    check('anchor_N_shape',N==old['anchor_keypoints']==len(axy) and N>0 and w['anchor_descriptor_shape']==[N,128])
    check('anchor_xy_finite_native',all(len(p)==2 and all(math.isfinite(v) and 0<=v<576 for v in p) for p in axy))
    check('anchor_saved_real_ids_exact',all(0<=idx<N and axy[idx]==xy for p in old['pairs'] for (idx,_),xy in zip(p['match_keypoint_ids'],p['source_xy'])) and w['all_observed_real_anchor_ids_xy_exact'])
    check('twelve_pair_order',[(p['target_id'],p['arm']) for p in w['pairs']]==[(j,'real') for j in c['target_ids']]+[(v['target_id'],v['arm']) for v in c['generated_images'].values()])
    by={}
    for p in w['pairs']:
        j,arm=p['target_id'],p['arm'];tag=f'{j}/{arm}/';n=p['match_count'];x,y,mids=p['source_xy'],p['target_xy'],p['match_keypoint_ids'];F=Fs[j]
        cmp(tag+'F_from_original_cameras',F,p['F_unit_frobenius'],1e-12,1e-10)
        check(tag+'count_lengths',n==len(x)==len(y)==len(mids)==len(p['residuals'])==len(p['valid_line_mask']))
        check(tag+'source_unique_IDs',len({a for a,b in mids})==n<=N and all(type(a) is int and type(b) is int and 0<=a<N and 0<=b<p['target_keypoints'] for a,b in mids))
        check(tag+'xy_shape_finite',all(len(a)==2 and all(math.isfinite(v) and 0<=v<576 for v in a) for a in x+y))
        check(tag+'anchor_xy_each_slot',all(a==axy[idx] for (idx,_),a in zip(mids,x)))
        if arm=='real':check(tag+'original_real_fields_exact',all(p[k]==v for k,v in oldreal[j].items()) and p['reused_from_S72'] is True)
        else:check(tag+'new_pair_mark',p['reused_from_S72'] is False)
        residuals=[];valid=[]
        for a,b in zip(x,y):
            xh,yh=a+[1.],b+[1.];lt=[dot(row,xh) for row in F];ls=[dot(col(F,k),yh) for k in range(3)]
            q=dot(yh,lt);nt,ns=math.hypot(*lt[:2]),math.hypot(*ls[:2])
            good=all(math.isfinite(v) for v in [q,nt,ns]) and min(nt,ns)>c['line_epsilon'];valid.append(good)
            if good:
                dt,ds=abs(q)/nt,abs(q)/ns;residuals.append([dt,ds,(dt+ds)/2])
            else:residuals.append(None)
        check(tag+'valid_mask',valid==p['valid_line_mask']);check(tag+'null_residual_positions',[z is None for z in residuals]==[z is None for z in p['residuals']])
        cmp(tag+'all_residual_columns',[z for z in residuals if z is not None],[z for z in p['residuals'] if z is not None])
        means=[v[2] for v in residuals if v is not None];V=len(means);qs=[quantile(means,q) for q in c['residual_quantiles']] if means else None
        cmp(tag+'quantiles',qs,p['residual_quantiles_px'])
        check(tag+'N_M_V_counts',p['anchor_population']==N and p['unmatched_count']==N-n and p['valid_count']==V and p['invalid_count']==n-V)
        cmp(tag+'availability',[n/N,(N-n)/N],[p['matched_fraction'],p['unmatched_fraction']],0,0)
        counts={str(q):sum(v<=q for v in means) for q in c['cutoffs_px']}
        check(tag+'threshold_counts',counts==p['threshold_counts'])
        check(tag+'threshold_denominators',p['agreement_fraction_of_anchor']=={k:v/N for k,v in counts.items()} and p['agreement_fraction_of_valid']=={k:v/V if V else None for k,v in counts.items()})
        for name,xy in [('source',x),('target',y)]:
            cov=coverage(xy);check(tag+name+'_gridcells',cov['occupied_4x4_cells']==p[name+'_coverage']['occupied_4x4_cells']);cmp(tag+name+'_span',cov['span_xy_fraction'],p[name+'_coverage']['span_xy_fraction'])
        row=dict(target_id=j,arm=arm,match_count=n,valid_count=V,invalid_count=n-V,matched_fraction=n/N,threshold_counts=counts,agreement_fraction_of_anchor={k:v/N for k,v in counts.items()},residual_quantiles_px=qs,residuals=residuals)
        r['pairs'].append(row);by[j,arm]={idx:residuals[k] for k,(idx,_) in enumerate(mids)}
    check('four_shared_targets',[p['target_id'] for p in w['shared_support']]==c['target_ids'])
    medians={arm:[] for arm in c['arms']}
    for saved in w['shared_support']:
        j=saved['target_id'];tag=f'{j}/shared/'
        inter=[i for i in range(N) if all(i in by[j,arm] for arm in ['real','A0','B'])]
        good=[i for i in inter if all(by[j,arm][i] is not None for arm in ['real','A0','B'])]
        check(tag+'ID_joins',inter==saved['raw_intersection_ids'] and good==saved['common_valid_ids'])
        check(tag+'counts',len(inter)==saved['raw_intersection_count'] and len(good)==saved['common_valid_count'] and len(inter)-len(good)==saved['invalid_in_any_count'])
        cmp(tag+'anchor_denominator',len(good)/N,saved['common_valid_anchor_fraction'],0,0)
        for name,idxs in [('raw_intersection',inter),('common_valid',good)]:
            cov=coverage([axy[i] for i in idxs]);check(tag+name+'_gridcells',cov['occupied_4x4_cells']==saved[name+'_coverage']['occupied_4x4_cells']);cmp(tag+name+'_span',cov['span_xy_fraction'],saved[name+'_coverage']['span_xy_fraction'])
        result=dict(target_id=j,raw_intersection_ids=inter,common_valid_ids=good,arms={})
        for arm in c['arms']:
            delta=[by[j,arm][i][2]-by[j,'real'][i][2] for i in good]
            qs=[quantile(delta,q) for q in c['residual_quantiles']] if delta else None
            sr=saved['arms'][arm];cmp(tag+arm+'/deltas',delta,sr['delta_generated_minus_real_px']);cmp(tag+arm+'/quantiles',qs,sr['quantiles_px'])
            signs=[sum(x>0 for x in delta),sum(x<0 for x in delta),sum(x==0 for x in delta)]
            check(tag+arm+'/strict_sign_counts',signs==[sr['positive_count'],sr['negative_count'],sr['zero_count']])
            medians[arm].append(qs[1] if qs else None);result['arms'][arm]=dict(deltas=delta,quantiles=qs,sign_counts=signs)
        r['shared_support'].append(result)
    for arm,ms in medians.items():
        event=None if None in ms else min(ms)>0
        actual=w['predefined_exploratory_events'][arm]
        check('event/'+arm,event is actual['all4_positive_paired_median'])
        for i,(a,b) in enumerate(zip(ms,actual['target_medians_px'])):cmp(f'event/{arm}/median/{i}',a,b)
        r['events'][arm]=dict(all4_positive_paired_median=event,target_medians_px=ms)
    expected=[(c['real_acceptance']['path'],c['real_acceptance']['sha256'],'accepted_real_metadata'),(c['real_receipt']['path'],c['real_receipt']['sha256'],'real_saved_coordinates_and_F')]
    expected += [(it['path'],it['sha256'],'RGB_PNG') for it in [c['anchor']]+list(c['generated_images'].values())]
    check('upstream_readlist_exact',[(a['path'],a['sha256'],a['kind']) for a in w['reads']]==expected)
    r['upstream_image_bytes_claimed']=sum(a['bytes'] for a in w['reads'] if a['kind']=='RGB_PNG')
    r['anchor_descriptor_boundary']='Current descriptor shape/hash metadata checked, descriptor bytes not stored/read; no historical descriptor replay or SIFT truth claim.'

if __name__=='__main__':
    started=utc();timer=time.perf_counter()
    r=dict(schema='s73-independent-existing-geometry-arithmetic-v1',status='RUNNING',reviewer_role='/root/c2_v9_source_primary',started_utc=started,python=sys.version,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),reused_own_S72_helper_source_sha256=S72_HELPER_SOURCE_SHA,reads=[],decoded_fields=[],checks=[],pairs=[],derived_F={},shared_support=[],events={},blockers=[],new_method_validated=False,scope='Original bound camera/K NPZ fields plus saved coordinates/metadata only. NumPy NPZ I/O; scalar world-ray F, distances, statistics, joins. No images/SIFT/Torch/models/weights or author-function import.')
    with (O/'receipt.json').open('x') as f:
        try:
            run(r);r['blockers']=[c['name'] for c in r['checks'] if not c['pass_']];r['status']='PASS_S73_INDEPENDENT_ARITHMETIC' if not r['blockers'] else 'DISCREPANCY_PRESERVED'
        except BaseException:r['status']='FAILED_PRESERVED';r['exception']=traceback.format_exc();r['blockers'].append('exception')
        r.update(completed_utc=utc(),elapsed_seconds=time.perf_counter()-timer,checks_passed=sum(c['pass_'] for c in r['checks']),input_file_count=len(r['reads']),input_bytes=sum(p['bytes'] for p in r['reads']),decoded_array_bytes=sum(p['bytes'] for p in r['decoded_fields']))
        json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
    (O/'receipt.json').chmod(0o444)
    print(json.dumps({k:r[k] for k in ['status','checks_passed','blockers','elapsed_seconds','input_file_count','input_bytes','decoded_array_bytes']}))
    raise SystemExit(0 if not r['blockers'] else 1)
