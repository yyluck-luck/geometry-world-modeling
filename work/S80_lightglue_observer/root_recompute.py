"""Independent root arithmetic audit of saved S80 outputs; no model/image loading."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import math
import time
import numpy as np

BASE = Path(__file__).resolve().parent
RUN = BASE / 'execution_01'
ATOL, RTOL = 1e-8, 1e-12
began, tick = dt.datetime.now(dt.timezone.utc).isoformat(), time.monotonic()
checks, max_error, coordinate_pairs, bf_precision_disagreements = 0, 0., 0, 0

def load(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(condition, label):
    global checks
    checks += 1
    if not condition:
        raise AssertionError(label)

def close(a, b, label):
    global max_error
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    require(a.shape == b.shape, label+' shape')
    finite = np.isfinite(a) & np.isfinite(b)
    if finite.any():
        max_error = max(max_error, float(np.max(np.abs(a[finite]-b[finite]))))
    require(np.allclose(a, b, atol=ATOL, rtol=RTOL, equal_nan=True), label)

def verify_npz(meta):
    path = Path(meta['path'])
    require(sha(path) == meta['sha256'], 'npz file SHA')
    require(path.stat().st_size == meta['bytes'], 'npz bytes')
    a = dict(np.load(path, allow_pickle=False))
    require(set(a) == set(meta['arrays']), 'array fields')
    for k, v in a.items():
        expected = meta['arrays'][k]
        require(list(v.shape) == expected['shape'] and str(v.dtype) == expected['dtype'], k+' shape dtype')
        require(hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest() == expected['sha256'], k+' bytes')
    return a

def quant(values):
    a = sorted(float(x) for x in values)
    if not a:
        return None
    ans = []
    for p in [.25, .5, .75, .95]:
        h = (len(a)-1)*p
        i = math.floor(h)
        ans.append(a[i]*(1-(h-i)) + a[min(i+1,len(a)-1)]*(h-i))
    return ans

def cover(points):
    if not len(points):
        return {'occupied_4x4_cells':0, 'span_xy_fraction':None}
    cells = {(min(3,max(0,math.floor(float(x)/576*4))), min(3,max(0,math.floor(float(y)/576*4)))) for x,y in points}
    spans = []
    for k in [0,1]:
        high,low = max(float(v[k]) for v in points),min(float(v[k]) for v in points)
        # All-feature arrays in the original output retain FP32 subtraction/division.
        # Accepted-coordinate arrays are FP64. Preserve this dtype semantics rather
        # than relaxing the independently fixed geometric arithmetic tolerance.
        span = float(np.float32(np.float32(high-low)/np.float32(576))) if points.dtype == np.float32 else (high-low)/576
        spans.append(span)
    return {'occupied_4x4_cells':len(cells), 'span_xy_fraction':spans}

def distances(xs, ys, F):
    result, valid = [], []
    for x,y in zip(xs,ys):
        p,q = [float(x[0]),float(x[1]),1.], [float(y[0]),float(y[1]),1.]
        l = [math.fsum(float(F[i,j])*p[j] for j in range(3)) for i in range(3)]
        r = [math.fsum(float(F[j,i])*q[j] for j in range(3)) for i in range(3)]
        a = abs(math.fsum(q[i]*l[i] for i in range(3)))
        s,t = math.hypot(l[0],l[1]), math.hypot(r[0],r[1])
        ok = all(math.isfinite(z) for z in [a,s,t]) and s>1e-12 and t>1e-12
        valid.append(ok)
        result.append([a/s,a/t,(a/s+a/t)/2] if ok else [math.nan]*3)
    return np.asarray(result).reshape((-1,3)), np.asarray(valid,dtype=bool)

c = load(BASE/'RUN_CONTRACT.json')
receipt = load(RUN/'receipt.json')
external = load(RUN/'EXTERNAL_RECEIPT.json')
require(sha(BASE/'RUN_CONTRACT.json') == receipt['contract_sha256'], 'contract identity')
require(sha(BASE/'run_observer.py') == receipt['source_sha256'], 'runner identity')
require(external['returncode'] == 0 and external['stop_reason'] is None, 'external terminal')
require(external['elapsed_seconds'] <= 600 and external['peak_sampled_process_tree_rss_bytes'] <= 8589934592, 'sampled budget')
require(receipt['counts'] == {'image_read_attempts':13,'images_read_and_identity_verified':13,'sift_extract_attempts':13,'sift_extract_successes':13,'bf_pair_attempts':12,'lightglue_forward_attempts':12,'lightglue_forward_successes':12}, 'execution counts')
require(receipt['missing_rows'] == [] and receipt['actual_rows'] == 24, 'completion')
require(sha(Path(c['geometry_receipt']['path'])) == c['geometry_receipt']['sha256'], 'frozen geometry file')
Fs = {p['target_id']:np.array(p['Fraw']) for p in load(Path(c['geometry_receipt']['path']))['pairs']}
manifest = load(RUN/'FEATURE_MANIFEST.json')
features = {}
for spec in c['images']:
    f = manifest[spec['id']]
    require(f['input_sha256'] == spec['sha256'], 'input recorded identity')
    features[spec['id']] = verify_npz(f['saved'])
    require(f['N'] == len(features[spec['id']]['keypoints']) <= 1500, 'N')
    for arr in features[spec['id']].values():
        require(arr.dtype == np.float32 and np.isfinite(arr).all(), 'finite FP32 features')
rows = load(RUN/'ROWS.json')
require([r['row_id'] for r in rows] == [p['id']+'_'+m for p in c['pairs'] for m in ['BF','LG']], 'all ordered rows')
compact = []
for row in rows:
    rid = row['row_id']
    require(row == load(RUN/'pairs'/(rid+'.json')), rid+' row identity')
    a, raw = verify_npz(row['saved']), verify_npz(row['raw_matcher_saved'])
    for k in raw:
        require(np.array_equal(a[k],raw[k],equal_nan=True), rid+' unaltered matcher output')
    f0,f1 = features[row['source_id']],features[row['target_image_id']]
    n,m = len(f0['keypoints']),len(f1['keypoints'])
    require(n == row['N_source'] and m == row['N_target'], 'denominators')
    for label,key in [('source',row['source_id']),('target',row['target_image_id'])]:
        require(row[label+'_feature_file_sha256'] == manifest[key]['saved']['sha256'], 'shared features')
    a0,a1 = a['matches0'],a['matches1']
    require(a0.shape == (n,) and a1.shape == (m,), 'match shapes')
    require(((a0>=-1)&(a0<m)).all() and ((a1>=-1)&(a1<n)).all(), 'match range')
    pairs = [(i,int(j)) for i,j in enumerate(a0) if j>=0]
    require({(int(i),j) for j,i in enumerate(a1) if i>=0} == set(pairs), 'reciprocal full sets')
    require(len({j for i,j in pairs}) == len(pairs), 'target unique indices')
    require(np.array_equal(np.asarray(pairs).reshape((-1,2)),a['accepted_indices']), 'accepted indices')
    require(len(pairs) == row['M'], 'M')
    require(n-len(pairs) == row['unmatched_source'] and m-len(pairs) == row['unmatched_target'], 'unmatched')
    close([len(pairs)/n,len(pairs)/m],[row['matched_fraction_source'],row['matched_fraction_target']], 'match fractions')
    xs=np.array([f0['keypoints'][i] for i,j in pairs],dtype=np.float64).reshape((-1,2))
    ys=np.array([f1['keypoints'][j] for i,j in pairs],dtype=np.float64).reshape((-1,2))
    require(np.array_equal(xs,a['source_xy']) and np.array_equal(ys,a['target_xy']), 'exact coordinate provenance')
    coordinate_pairs += len(pairs)
    if row['matcher'] == 'BF':
        candidates=[]
        goods=[]
        for side in [0,1]:
            ids,d=a['knn_ids'+str(side)],a['knn_l2_distances'+str(side)]
            require((ids[:,0] != ids[:,1]).all() and (d>=0).all() and (d[:,0]<=d[:,1]).all(), 'BF ordered distinct neighbors')
            good=(ids[:,1]>=0)&(d[:,0] < np.float32(.75)*d[:,1])
            wide=d[:,0].astype(float) < .75*d[:,1].astype(float)
            bf_precision_disagreements += int(np.count_nonzero(good != wide))
            goods.append(good)
        for i in range(n):
            j=int(a['knn_ids0'][i,0])
            if goods[0][i] and goods[1][j] and a['knn_ids1'][j,0] == i:
                candidates.append((i,j))
        require(candidates == pairs, 'BF independent acceptance')
    else:
        require(np.array_equal(a['matches'],a['accepted_indices']), 'LG compact indices')
        require(row['stop_layer']==9 and (a['prune0']==9).all() and (a['prune1']==9).all(), 'LG no adaptation')
        selected=np.array([a['matching_scores0'][i] for i,j in pairs])
        require((selected > np.float32(.1)).all(), 'LG strict threshold')
        require(np.array_equal(selected,a['scores']), 'LG compact scores')
    recalculated={}
    for label,target in [('correct',row['target_id']),('wrong',row['wrong_target_id'])]:
        require(np.array_equal(Fs[target],a[label+'_F']), 'fixed F identity')
        e,v=distances(xs,ys,Fs[target])
        close(e,a[label+'_residuals'], 'scalar geometry')
        require(np.array_equal(v,a[label+'_valid']), 'valid mask')
        stat=row[label]; z=e[v,2]; recalculated[label]=(e,v)
        require(int(v.sum())==stat['valid_count'] and int((~v).sum())==stat['invalid_count'], 'valid denominator')
        close(quant(z),stat['quantiles_q25_q50_q75_q95_px'],'manual quantiles')
        close([min(z),max(z)],[stat['min_px'],stat['max_px']], 'extrema')
        for threshold in [2,5,10]:
            count=sum(float(x)<=threshold for x in z); key=str(threshold)
            require(count==stat['counts_le_px'][key], 'exact threshold counts')
            close([count/len(z),count/n],[stat['fraction_of_valid_le_px'][key],stat['fraction_of_all_anchor_le_px'][key]], 'threshold denominators')
    e0,v0=recalculated['correct']; e1,v1=recalculated['wrong']; joint=v0&v1
    diff=e1[joint,2]-e0[joint,2]
    require(np.array_equal(joint,a['joint_valid']) and int(joint.sum())==row['joint_valid_count'],'joint mask')
    close(diff,a['wrong_minus_correct_px'][joint], 'paired difference')
    close(quant(diff),row['paired_wrong_minus_correct_quantiles_px'],'paired quantiles')
    require([int(sum(diff>0)),int(sum(diff==0)),int(sum(diff<0))]==[row['paired_positive_count'],row['paired_zero_count'],row['paired_negative_count']], 'paired signs')
    for label,points in [('source',xs),('target',ys),('source_all_feature',f0['keypoints']),('target_all_feature',f1['keypoints'])]:
        cv=cover(points); recorded=row[label+'_coverage']
        require(cv['occupied_4x4_cells']==recorded['occupied_4x4_cells'],'grid coverage')
        close(cv['span_xy_fraction'],recorded['span_xy_fraction'],'coverage spans')
    compact.append({'row_id':rid,'M':len(pairs),'median_px':row['correct']['quantiles_q25_q50_q75_q95_px'][1],'le10':row['correct']['counts_le_px']['10']})
result={'status':'PASS_SAVED_OUTPUT_ARITHMETIC_AND_IDENTITIES_ONLY','started_utc':began,'completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-tick,'checks':checks,'coordinate_pairs':coordinate_pairs,'both_labels_evaluated':True,'absolute_tolerance_px':ATOL,'relative_tolerance':RTOL,'max_absolute_numeric_difference':max_error,'BF_FP32_FP64_acceptance_disagreements':bf_precision_disagreements,'rows':compact,'source_sha256':sha(Path(__file__)),'independence':'Root wrote separate scalar math.fsum/hypot geometry and manual sorted quantiles; did not import original scorer. Original author provided schema/formula checklist.','scope_limits':['No independent image decoding, SIFT extraction, nearest-neighbor distance search or neural forward rerun.','No correspondence physical ground truth or independent camera calibration established.','Checks count arithmetic assertions, not independent experiments or sample size.'],'new_method_validated':False}
with (BASE/'ROOT_RECOMPUTATION.json').open('x') as f:
    json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False))
