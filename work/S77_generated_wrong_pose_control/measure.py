"""S77 saved-match, depth-free fixed wrong-target-camera-label control."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, sys, time, traceback
D=Path(__file__).resolve().parent
IDS=[20,21,22,23]; ARMS=['real','A0','B']; SWAP={'20':23,'21':22,'22':21,'23':20}
def sha(b):return hashlib.sha256(b).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def canon(x):return sha(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
    p.chmod(0o444)
def quant(values):
    if not values:return None
    a=sorted(values);out=[]
    for q in [.25,.5,.75,.95]:
        z=(len(a)-1)*q;i=int(z);f=z-i
        out.append(a[i] if i==len(a)-1 else a[i]*(1-f)+a[i+1]*f)
    return out
def delta_stats(v):
    return dict(count=len(v),quantiles_px=quant(v),minimum_px=min(v) if v else None,
                maximum_px=max(v) if v else None,positive_count=sum(x>0 for x in v),
                negative_count=sum(x<0 for x in v),zero_count=sum(x==0 for x in v))
def event(rows):
    med=[z['quantiles_px'][1] if z['quantiles_px'] is not None else None for z in rows]
    return dict(target_ids=IDS,paired_medians_px=med,
                all4_paired_medians_positive=None if any(v is None for v in med) else all(v>0 for v in med))
def coverage(x):
    if not x:return dict(span_xy_fraction=None,occupied_4x4_cells=0)
    return dict(span_xy_fraction=[(max(v[j] for v in x)-min(v[j] for v in x))/575 for j in range(2)],
                occupied_4x4_cells=len({tuple(max(0,min(3,math.floor(v/144))) for v in row) for row in x}))
def main():
    if sys.argv[1:]==['--compile-only']:
        compile(Path(__file__).read_bytes(),__file__,'exec');print('COMPILE_ONLY_NO_RESULT_READ');return 0
    cb=(D/'CONTRACT.json').read_bytes();need(len(sys.argv)==2 and sha(cb)==sys.argv[1],'Exact contract SHA required')
    c=json.loads(cb);out=D/'execution_01';out.mkdir(exist_ok=False);begin=time.monotonic()
    r=dict(status='RUNNING',started_utc=utc(),source_sha256=sha(Path(__file__).read_bytes()),contract_sha256=sha(cb),
           reads=[],pairs=[],shared_support=[],events={},new_images=0,new_features=0,new_models=0,depth_reads=0,new_method_validated=False)
    def budget():need(time.monotonic()-begin<25,'25-second inner boundary exceeded')
    def read(item):
        budget();p=Path(item['path']);b=p.read_bytes();need(sha(b)==item['sha256'],'Identity changed: '+str(p))
        r['reads'].append(dict(path=str(p),bytes=len(b),sha256=sha(b)));return json.loads(b)
    try:
        need(c['target_ids']==IDS and c['swap']==SWAP and c['generated_arms']==['A0','B'],'Frozen design changed')
        a73=read(c['s73_acceptance']);a74=read(c['s74_acceptance']);a72=read(c['s72_acceptance'])
        need(a73['status']=='ACCEPTED_S73_EXISTING_IMAGE_ARITHMETIC_ONLY' and a74['status']=='ACCEPTED_S74_FIXED_WRONG_LABEL_ARITHMETIC_ONLY','Accepted parent stages required')
        need(a72['status']=='ACCEPTED_S72_REAL_CONTROL_ARITHMETIC_ONLY' and a72['files_sha256']['execution_01/receipt.json']==c['s72_receipt_identity']['sha256'],'S72 fixed source-camera identity differs')
        need(a73['files_sha256']['execution_02/receipt.json']==c['s73_receipt']['sha256'] and a74['files_sha256']['execution_01/receipt.json']==c['s74_receipt']['sha256'],'Parent result binding changed')
        need(a74['files_sha256']['execution_01/geometry_separation.json']==c['s74_separation']['sha256'],'S74 geometry binding differs')
        c73=read(c['s73_contract']);c74=read(c['s74_contract'])
        need(c73['real_receipt']==c74['real_receipt']==c['s72_receipt_identity'] and c74['swap']==SWAP,'Same S72 geometry route required')
        old=read(c['s73_receipt']);control=read(c['s74_receipt']);sep=read(c['s74_separation'])
        need(old['status']=='COMPLETE_EXISTING_GENERATED_GEOMETRY_DIAGNOSTIC' and control['status']=='COMPLETE_FIXED_WRONG_LABEL_DIAGNOSTIC','Parent results incomplete')
        pairs={(z['arm'],z['target_id']):z for z in old['pairs']}
        need(len(pairs)==len(old['pairs'])==12 and set(pairs)=={(a,j) for a in ARMS for j in IDS},'All12 source rows required')
        real_control={z['target_id']:z for z in control['pairs']};separations={z['target_id']:z for z in sep['pairs']}
        need(set(real_control)==set(separations)==set(IDS),'All4 real controls/geometries required')
        N=old['anchor_count'];need(N==control['anchor_population'] and N>0 and len(old['anchor_xy'])==N,'Shared source19 feature denominator differs')
        r.update(anchor_frame_id=19,anchor_population=N,original_shared_support=old['shared_support'],
                 source_geometry_separation_reused=sep,scope=c['scope'],limits=c['limits'])
        save(out/'geometry_separation.json',dict(recorded_before_generated_residuals_utc=utc(),
             source_sha256=c['s74_separation']['sha256'],pairs=sep['pairs'],interpretation='Reused S74 fixed F separation; not new calibration or a pixel-distance threshold'))
        def stats(res):
            values=[v[2] for v in res if v is not None];M=len(res);V=len(values)
            counts={str(k):sum(x<=k for x in values) for k in [2,5,10]}
            return dict(valid_count=V,invalid_count=M-V,quantiles_px=quant(values),maximum_px=max(values) if values else None,
                        threshold_counts=counts,fractions_of_matches={k:v/M if M else None for k,v in counts.items()},
                        fractions_of_valid={k:v/V if V else None for k,v in counts.items()},fractions_of_anchor={k:v/N for k,v in counts.items()})
        def wrong_residual(x,y,F):
            a=x+[1.];b=y+[1.]
            lt=[math.fsum(F[i][k]*a[k] for k in range(3)) for i in range(3)]
            ls=[math.fsum(F[k][i]*b[k] for k in range(3)) for i in range(3)]
            num=math.fsum(b[i]*lt[i] for i in range(3));nt=math.hypot(*lt[:2]);ns=math.hypot(*ls[:2])
            if not all(math.isfinite(v) for v in [num,nt,ns]) or min(nt,ns)<=1e-12:return None
            dt=abs(num)/nt;ds=abs(num)/ns;return [dt,ds,(dt+ds)/2]
        by={}
        for arm in ARMS:
            for j in IDS:
                budget();z=pairs[arm,j];M=z['match_count'];xy=z['source_xy'];uv=z['target_xy'];correct=z['residuals'];ids=z['match_keypoint_ids'];k=SWAP[str(j)]
                need(len(xy)==len(uv)==len(correct)==len(ids)==M and M<=N and len({x[0] for x in ids})==M,'Coordinate/count identity fails')
                need(all(0<=a<N and old['anchor_xy'][a]==x for (a,b),x in zip(ids,xy)),'Source anchor coordinates changed')
                need(all(len(x)==len(y)==2 and all(math.isfinite(v) for v in x+y) for x,y in zip(xy,uv)),'Nonfinite recorded image coordinate')
                need(all(v is None or len(v)==3 and all(math.isfinite(t) and t>=0 for t in v) for v in correct),'Invalid correct residual schema')
                F=separations[j]['normalized_F_wrong'];need(separations[j]['wrong_pose_label']==k,'Fixed swap differs')
                need(all(len(m)==3 and all(len(row)==3 and all(math.isfinite(v) for v in row) for row in m) for m in [F,z['F_unit_frobenius'],separations[j]['normalized_F_correct']]),'Finite 3x3 F required')
                norm=math.sqrt(math.fsum(v*v for row in z['F_unit_frobenius'] for v in row));need(norm>0,'Degenerate originalF')
                need(max(abs(z['F_unit_frobenius'][a][b]/norm-separations[j]['normalized_F_correct'][a][b]) for a in range(3) for b in range(3))<=1e-12,'Correct geometry differs from S74')
                if arm=='real':
                    prior=real_control[j]
                    need(all(prior[key]==z[key] for key in ['match_keypoint_ids','source_xy','target_xy']), 'Real-control correspondence differs')
                    need(prior['correct_residuals_reused']==correct,'Real-control correct values differ');wrong=prior['wrong_residuals']
                else:wrong=[wrong_residual(x,y,F) for x,y in zip(xy,uv)]
                need(len(wrong)==M and all(v is None or len(v)==3 and all(math.isfinite(t) and t>=0 for t in v) for v in wrong),'Wrong residual rows incomplete/nonfinite')
                common=[i for i in range(M) if correct[i] is not None and wrong[i] is not None]
                common_set=set(common);raw_delta=[wrong[i][2]-correct[i][2] if i in common_set else None for i in range(M)]
                delta=[raw_delta[i] for i in common]
                row=dict(arm=arm,target_id=j,wrong_pose_label=k,real_wrong_residuals_reused=arm=='real',
                    source_frame_id=19,anchor_population=N,match_count=M,matched_anchor_fraction=M/N,unmatched_anchor_count=N-M,
                    target_keypoints=z.get('target_keypoints'),matching_status_reused=z['status'],match_keypoint_ids=ids,
                    source_xy=xy,target_xy=uv,coordinates_ids_sha256=canon(dict(ids=ids,source_xy=xy,target_xy=uv)),
                    source_coverage=z['source_coverage'],target_coverage=z['target_coverage'],
                    source_image_domain_count=sum(all(0<=v<576 for v in p) for p in xy),
                    target_image_domain_count=sum(all(0<=v<576 for v in p) for p in uv),
                    correct_residuals_reused=correct,wrong_residuals=wrong,correct=stats(correct),wrong=stats(wrong),
                    correct_invalid_indices=[i for i,v in enumerate(correct) if v is None],wrong_invalid_indices=[i for i,v in enumerate(wrong) if v is None],
                    common_valid_indices=common,common_valid_count=len(common),invalid_in_either_count=M-len(common),
                    common_valid_anchor_fraction=len(common)/N,common_source_coverage=coverage([xy[i] for i in common]),
                    raw_deltas_wrong_minus_correct_px=raw_delta,paired_delta=delta_stats(delta))
                by[arm,j]=row;r['pairs'].append(row)
        for original in old['shared_support']:
            j=original['target_id'];maps={a:{aid:i for i,(aid,bid) in enumerate(by[a,j]['match_keypoint_ids'])} for a in ARMS}
            raw=sorted(set(maps['real'])&set(maps['A0'])&set(maps['B']))
            correct_ids=[a for a in raw if all(by[arm,j]['correct_residuals_reused'][maps[arm][a]] is not None for arm in ARMS)]
            need(raw==original['raw_intersection_ids'] and correct_ids==original['common_valid_ids'],'Original three-arm support changed')
            both=[a for a in correct_ids if all(by[arm,j]['wrong_residuals'][maps[arm][a]] is not None for arm in ARMS)]
            row=dict(target_id=j,original_raw_intersection_ids=raw,original_correct_common_valid_ids=correct_ids,
                     original_correct_common_valid_count=len(correct_ids),new_all_six_valid_ids=both,new_all_six_valid_count=len(both),
                     new_wrong_invalid_on_original_correct_ids=sorted(set(correct_ids)-set(both)),
                     all_six_valid_anchor_fraction=len(both)/N,all_six_source_coverage=coverage([old['anchor_xy'][a] for a in both]),arms={})
            for arm in ARMS:
                z=by[arm,j];positions=[maps[arm][a] for a in correct_ids];valid=[i for i in positions if z['wrong_residuals'][i] is not None]
                v=[z['raw_deltas_wrong_minus_correct_px'][i] for i in valid];w=[z['raw_deltas_wrong_minus_correct_px'][maps[arm][a]] for a in both]
                row['arms'][arm]=dict(original_common_source_ids=correct_ids,valid_on_original_common_ids=[z['match_keypoint_ids'][i][0] for i in valid],
                    wrong_invalid_count_on_original_common=len(positions)-len(valid),on_original_common=delta_stats(v),on_all_six_valid=delta_stats(w))
            r['shared_support'].append(row)
        need([z['target_id'] for z in r['shared_support']]==IDS,'All4 shared-support rows required')
        for arm in ARMS:
            r['events'][arm]=dict(primary_same_matches=event([by[arm,j]['paired_delta'] for j in IDS]),
                secondary_original_three_arm_support=event([z['arms'][arm]['on_original_common'] for z in r['shared_support']]),
                secondary_all_six_valid=event([z['arms'][arm]['on_all_six_valid'] for z in r['shared_support']]))
        budget();r['status']='COMPLETE_S77_FIXED_GENERATED_WRONG_LABEL_DIAGNOSTIC'
    except Exception as e:r.update(status='FAILED_PRESERVED',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
    finally:
        r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-begin)
        save(out/'receipt.json',r)
    print(json.dumps(dict(status=r['status'],output=str(out))))
    return 0 if r['status']=='COMPLETE_S77_FIXED_GENERATED_WRONG_LABEL_DIAGNOSTIC' else 1
if __name__=='__main__':raise SystemExit(main())
