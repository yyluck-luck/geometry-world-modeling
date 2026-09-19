"""Independent fixed-camera arithmetic. NumPy is used only for NPZ I/O."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import sys
import time
import traceback

O = Path(__file__).resolve().parent
D = O.parent
ATOL, RTOL = 1e-8, 1e-10
PINS = {
    'execution_01/receipt.json': '7711703643cb03e447a05fcd452142912d727e659372561d1efe4b7903d13d53',
    'CONTRACT_v2.json': '14e72eafa5131a3734fa9386f7ae073bb9ccf72b9be9223e9655c30099910940',
    'measure_v2.py': '98c980295a65c2bf7ba9bb786ba1a724d0be2b7310526169bb062be35b402f20',
    'external_01/receipt.json': 'd15eb6485e458a18475ef98ead610eb47c19d70f312b6880a186049f43f5ab45',
}


def utc():
    return datetime.now(timezone.utc).isoformat()


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


def run(r):
    import numpy as np  # no NumPy scientific arithmetic is used below
    r['numpy_version'] = np.__version__

    def check(name, ok, detail=None):
        r['checks'].append({'name': name, 'pass': bool(ok), 'detail': detail})

    def read(path, digest=None, kind='evidence'):
        p = Path(path)
        b = p.read_bytes()
        h = hashlib.sha256(b).hexdigest()
        r['reads'].append({'path': str(p), 'bytes': len(b), 'sha256': h, 'kind': kind})
        if digest:
            check('pin:'+str(p), h == digest)
            if h != digest:
                raise ValueError('Input identity changed: '+str(p))
        return b

    def compare(name, actual, saved, atol=ATOL, rtol=RTOL):
        a, b = flatten(actual), flatten(saved)
        bad = [i for i, (x, y) in enumerate(zip(a, b))
               if not math.isfinite(x) or not math.isfinite(y)
               or not math.isclose(x, y, abs_tol=atol, rel_tol=rtol)]
        check(name, len(a) == len(b) and not bad,
              {'count': len(a), 'saved_count': len(b), 'mismatch_indices': bad,
               'max_abs_difference': max((abs(x-y) for x, y in zip(a, b)), default=0),
               'atol': atol, 'rtol': rtol})

    data = {rel: read(D/rel, h) for rel, h in PINS.items()}
    w, c, e = (json.loads(data[name]) for name in
               ('execution_01/receipt.json', 'CONTRACT_v2.json', 'external_01/receipt.json'))
    accept = json.loads(read(D/'ROOT_SOURCE_ACCEPTANCE.json'))
    logs = json.loads(read(D/'external_01/stdout.txt'))
    stderr = read(D/'external_01/stderr.txt')
    metadata = {}
    for p, h in c['source_metadata'].items():
        metadata[p] = json.loads(read(p, h, 'metadata'))
    m = next(iter(metadata.values()))
    anchor = next(a for a in m['appearances'] if a['history_id'] == 19)
    check('terminal/source/contract', e['returncode'] == 0 and e['timeout'] is False
          and e['worker_receipt_sha256'] == PINS['execution_01/receipt.json']
          and w['source_sha256'] == accept['pins']['measure_v2.py'] == PINS['measure_v2.py']
          and w['contract_sha256'] == accept['pins']['CONTRACT_v2.json'] == PINS['CONTRACT_v2.json'])
    check('logs', not stderr and e['stderr_bytes'] == 0 and logs['status'] == w['status']
          and logs['completed_utc'] == w['completed_utc'])
    check('time_order', accept['accepted_utc'] <= e['started_utc'] <= w['started_utc']
          <= w['completed_utc'] <= e['completed_utc'])
    check('completed_descriptive_scope', w['status'] == 'COMPLETE_REAL_CONTROL_DIAGNOSTIC'
          and w['new_method_validated'] is False and w['model_calls'] == 0 and w['weight_bytes'] == 0)
    check('versions', w['versions'] == c['versions'] and np.__version__ == '1.26.4')
    check('anchor_tensor_identity_claim', w['anchor_image_tensor_sha256'] ==
          c['anchor_image_tensor_sha256'] == anchor['image_tensor_sha256'])
    check('real_fr2_records', all('/rgbd_dataset_freiburg2_desk/rgb/' in x['rgb_path_metadata_only'] for x in m['records']))

    archive = c['camera_archive']
    with np.load(io.BytesIO(read(archive['path'], archive['sha256'], 'camera_npz')), allow_pickle=False) as z:
        camera_arrays = {name: z[name].copy() for name in ('ids', 'c2ws')}
    for name, arr in camera_arrays.items():
        desc = archive['fields'][name]
        check('camera_descriptor/'+name, list(arr.shape) == desc['shape'] and str(arr.dtype) == desc['dtype']
              and arr.nbytes == desc['body_bytes'] and hashlib.sha256(arr.tobytes(order='C')).hexdigest() == desc['body_sha256'])
        r['decoded_fields'].append({'container': archive['path'], 'field': name, 'body_bytes': arr.nbytes})
    ids, values = camera_arrays['ids'].tolist(), camera_arrays['c2ws'].tolist()
    check('camera_ids', ids == [12, 13, 14, 18, 19, 20, 21, 22, 23])
    poses = dict(zip(ids, values))
    kp = c['anchor_K_cache']
    with np.load(io.BytesIO(read(kp['path'], kp['sha256'], 'K_container_only')), allow_pickle=False) as z:
        ka = z[kp['field']].copy()
    kd = anchor['tensors']['K_pixels_576']
    check('K_descriptor', list(ka.shape) == kd['shape'] and str(ka.dtype) == kd['dtype']
          and ka.nbytes == kd['body_bytes'] and hashlib.sha256(ka.tobytes(order='C')).hexdigest() == kd['body_sha256'])
    r['decoded_fields'].append({'container': kp['path'], 'field': kp['field'], 'body_bytes': ka.nbytes})
    K = ka.tolist()
    check('K_exact_recorded', K == w['K_pixels_576'])
    check('camera_exact_recorded', all(poses[i] == w['optical_c2ws_used'][str(i)] for i in [19,20,21,22,23]))
    check('camera_K_finite', all(math.isfinite(x) for x in flatten(values)+flatten(K)))
    Ki = inverse(K)
    for i in [19,20,21,22,23]:
        C = poses[i]
        check(f'{i}/homogeneous_row', C[3] == [0.,0.,0.,1.])
        rot = [row[:3] for row in C[:3]]
        compare(f'{i}/rotation_orthogonal', [[dot(col(rot,j),col(rot,k)) for k in range(3)] for j in range(3)],
                [[float(j==k) for k in range(3)] for j in range(3)], 1e-10, 0)
    C0 = poses[19]
    Rs = [row[:3] for row in C0[:3]]
    world_source_bases = [[dot(row,col(Ki,j)) for row in Rs] for j in range(3)]
    check('four_pair_order', [p['target_id'] for p in w['pairs']] == [20,21,22,23])
    for p in w['pairs']:
        target = p['target_id']; tag = str(target)+'/'
        Ct = poses[target]; Rt = [row[:3] for row in Ct[:3]]
        world_baseline = [C0[i][3]-Ct[i][3] for i in range(3)]
        R = [[dot(col(Rt,i),col(Rs,j)) for j in range(3)] for i in range(3)]
        t = [dot(col(Rt,i),world_baseline) for i in range(3)]
        baseline = math.hypot(*world_baseline)
        world_target_bases = [[dot(row,col(Ki,i)) for row in Rt] for i in range(3)]
        # Each F entry is a world-ray scalar triple product; no E/matrix-multiply implementation reused.
        Fraw = [[dot(world_target_bases[i],cross(world_baseline,world_source_bases[j]))
                 for j in range(3)] for i in range(3)]
        norm = math.sqrt(math.fsum(v*v for v in flatten(Fraw)))
        for name, value, saved in [('R',R,p['R_target_from_source']),('t',t,p['t_target_from_source_m']),
                                    ('baseline',baseline,p['baseline_m']),('Fraw',Fraw,p['Fraw']),('Fraw_norm',norm,p['Fraw_norm'])]:
            compare(tag+name,value,saved,1e-12,1e-10)
        x, y = p['source_xy'], p['target_xy']; n = len(x)
        check(tag+'counts', n == len(y) == len(p['match_keypoint_ids']) == p['match_count'])
        check(tag+'xy_finite_shape_domain', all(len(a)==2 and all(math.isfinite(v) and 0<=v<576 for v in a) for a in x+y))
        mids = p['match_keypoint_ids']
        check(tag+'match_id_domain_unique', all(len(a)==2 and all(type(i) is int for i in a)
              and 0<=a[0]<w['anchor_keypoints'] and 0<=a[1]<p['target_keypoints'] for a in mids)
              and len({a[0] for a in mids})==n and len({a[1] for a in mids})==n)
        for name, a in [('source',x),('target',y)]:
            cov=coverage(a);check(tag+name+'_gridcells',cov['occupied_4x4_cells']==p[name+'_coverage']['occupied_4x4_cells'])
            if n: compare(tag+name+'_span',cov['span_xy_fraction'],p[name+'_coverage']['span_xy_fraction'])
        row={'target_id':target,'R':R,'t_m':t,'baseline_m':baseline,'Fraw_world_triple_product':Fraw,
             'source_coverage':coverage(x),'target_coverage':coverage(y),'match_count':n}
        if baseline<=c['baseline_insufficient_m'] or not math.isfinite(norm) or norm<=0:
            check(tag+'insufficient_baseline',p['status']=='INSUFFICIENT_BASELINE')
        elif n==0:
            check(tag+'no_matches',p['status']=='NO_MATCHES')
        else:
            F=[[a/norm for a in z] for z in Fraw]
            compare(tag+'unit_F',F,p['F_unit_frobenius'],1e-12,1e-10)
            valid=[];residuals=[];triples=[];normal_min=[]
            for a,b in zip(x,y):
                xh,yh=a+[1.],b+[1.]
                lt=[dot(fr,xh) for fr in F];ls=[dot(col(F,j),yh) for j in range(3)]
                nt,ns=math.hypot(*lt[:2]),math.hypot(*ls[:2])
                signed=dot(yh,lt)
                ws=[dot(row,[dot(kr,xh) for kr in Ki]) for row in Rs]
                wt=[dot(row,[dot(kr,yh) for kr in Ki]) for row in Rt]
                triples.append(abs(dot(wt,cross(world_baseline,ws))/norm-signed))
                good=all(math.isfinite(v) for v in (nt,ns,signed)) and min(nt,ns)>c['line_normal_epsilon']
                valid.append(good);normal_min.append(min(nt,ns))
                dt,ds=(abs(signed)/nt,abs(signed)/ns) if good else (None,None)
                residuals.append([dt,ds,(dt+ds)/2] if good else None)
            check(tag+'valid_mask',valid==p['valid_line_mask'])
            check(tag+'valid_invalid_counts',sum(valid)==p['valid_count'] and n-sum(valid)==p['invalid_count'])
            check(tag+'residual_column_order',p['residual_columns']==['to_target_px','to_source_px','symmetric_mean_px'])
            check(tag+'null_residual_positions',[a is None for a in residuals]==[a is None for a in p['residuals']])
            compare(tag+'all_three_residual_columns',[a for a in residuals if a is not None],[a for a in p['residuals'] if a is not None])
            means=[a[2] for a in residuals if a is not None]
            q=[quantile(means,v) for v in [.25,.5,.75,.95]] if means else None
            fractions={str(z):sum(v<=z for v in means)/len(means) for z in [2,5,10]} if means else None
            if means:
                compare(tag+'quantiles',q,p['residual_quantiles_px'])
                check(tag+'exact_fraction_counts',fractions==p['fractions_below_px'])
            check(tag+'denominator_disclosure',p['fraction_denominator']=='valid lines; invalid counts separately retained')
            check(tag+'status',p['status']==('COMPUTED_DESCRIPTIVE_ONLY' if means else 'INSUFFICIENT_VALID_LINES'))
            row.update(F_unit=F,residuals=residuals,valid_count=sum(valid),invalid_count=n-sum(valid),
                       quantiles_px=q,fractions_le_px=fractions,max_triple_product_constraint_difference=max(triples),
                       min_line_normal=min(normal_min),max_symmetric_error_px=max(means) if means else None)
            check(tag+'direct_ray_triple_product_identity',max(triples)<=1e-10,{'max_abs_difference':max(triples)})
        r['pairs'].append(row)
    expected=[(c['original_util']['path'],c['original_util']['sha256'],'original_preprocess_source')]
    expected += [(p,h,'metadata') for p,h in c['source_metadata'].items()]
    expected += [(archive['path'],archive['sha256'],'camera_archive'),(kp['path'],kp['sha256'],'saved_cache_K_only')]
    expected += [(item['path'],item['sha256'],'RGB_PNG') for item in [c['anchor']]+list(c['targets'].values())]
    check('upstream_readlist_exact',[(a['path'],a['sha256'],a['kind']) for a in w['reads']]==expected)
    r['upstream_image_read_metadata']={'files':5,'bytes':sum(a['bytes'] for a in w['reads'] if a['kind']=='RGB_PNG'),
                                      'anchor_tensor_sha256':w['anchor_image_tensor_sha256'],
                                      'anchor_export_sha256_claim_only':w['anchor_export_sha256'],
                                      'independently_read_image_bytes':0}


if __name__=='__main__':
    start=utc();timer=time.perf_counter()
    r={'schema':'s72-independent-known-geometry-arithmetic-v1','status':'RUNNING',
       'reviewer_role':'/root/c2_v9_source_primary','started_utc':start,'python':sys.version,
       'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'reads':[],'decoded_fields':[],'checks':[],'pairs':[],'blockers':[],
       'scope':'Scalar arithmetic from original bound cameras/K and saved matches. NumPy NPZ I/O only; no image, feature extraction, Torch, weights, model, or author-function import.',
       'limits':'Numerical consistency review, not correspondence truth, calibrated camera PASS, or a generated-image/memory claim.',
       'new_method_validated':False}
    with (O/'receipt.json').open('x') as out:
        try:
            run(r)
            r['blockers']=[x['name'] for x in r['checks'] if not x['pass']]
            r['status']='PASS_S72_INDEPENDENT_ARITHMETIC' if not r['blockers'] else 'DISCREPANCY_PRESERVED'
        except BaseException:
            r['status']='FAILED_PRESERVED';r['exception']=traceback.format_exc();r['blockers'].append('exception')
        r.update(completed_utc=utc(),elapsed_seconds=time.perf_counter()-timer,
                 checks_passed=sum(x['pass'] for x in r['checks']),input_file_count=len(r['reads']),
                 input_bytes=sum(x['bytes'] for x in r['reads']),decoded_array_bytes=sum(x['body_bytes'] for x in r['decoded_fields']))
        json.dump(r,out,indent=2,allow_nan=False);out.write('\n')
    (O/'receipt.json').chmod(0o444)
    print(json.dumps({k:r[k] for k in ['status','checks_passed','blockers','elapsed_seconds','input_file_count','input_bytes','decoded_array_bytes']}))
    raise SystemExit(0 if not r['blockers'] else 1)
