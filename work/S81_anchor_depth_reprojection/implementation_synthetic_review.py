#!/usr/bin/env python3
"""Import only guarded pure helpers and test with artificial inputs; never call main."""
from pathlib import Path
import datetime, hashlib, importlib.util, json
import numpy as np

P = Path(__file__).resolve().parent
START = datetime.datetime.now(datetime.timezone.utc).isoformat()
expected_source = 'ce9f929e2d106b831144a262ff9f616e4e45d5ba8d82f733fc1af70524cd8d73'
expected_contract = 'ae317145a909f12fe94cd0ad221fa54da1a032855f585b73bc996b3ec0cc57a4'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'run_reprojection.py') == expected_source
assert sha(P/'CONTRACT.json') == expected_contract
spec = importlib.util.spec_from_file_location('s81_helpers_under_review', P/'run_reprojection.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
checks=[]

def test(name, actual, expected, tol=0):
    a=np.asarray(actual); e=np.asarray(expected)
    ok=bool(np.allclose(a,e,atol=tol,rtol=0,equal_nan=True)) if a.dtype.kind in 'fiu' and e.dtype.kind in 'fiu' else bool(np.array_equal(a,e))
    checks.append({'case':name,'passed':ok,'atol':tol,'actual':repr(actual),'expected':repr(expected)})

# Caller supplies exact-contract boundaries, not the older broader reference domain.
depth=np.full((480,640),10000,dtype=np.uint16)
native=np.array([[639.,100.],[639.2,100.],[200.,479.],[200.,479.2],
                 [100.5,20.],[100.499,20.],[100.501,20.],[-.1,20.],[100.,0.]])
x=native*np.array([1.2,1.2])-np.array([96.,0.])
n,idx,raw,z,v,reason=m.sample(x,depth)
test('contract_native_inverse_map',n,native,2e-13)
test('native_639_and_479_valid_639point2_and_479point2_invalid',v,[True,False,True,False,True,True,True,False,True])
test('half_up_100point5_and_neighbors',idx[4:7,0],[101,100,101])
test('outside_never_clipped_to_zero_or_edge',raw[[1,3,7]],[-1,-1,-1])
test('positive_raw_to_Z_metres',z[v],np.full(v.sum(),2.))
test('invalid_sample_z_is_nan',np.isnan(z[~v]),np.ones((~v).sum(),dtype=bool))
test('outside_reasons',reason[[1,3,7]],['SOURCE_OUTSIDE']*3)
# Contract's conservative boundary rejects v576=575 -> native=479+1/6.
a=m.sample(np.array([[575.,575.]]),depth)
test('final_576_corner_rejected_by_conservative_native_domain',a[4],[False])
test('final_576_corner_address_preserved',a[1],[[559,479]])
# Zero depth and nonfinite coordinates.
depth[20,100]=0
zcase=m.sample(np.array([[100*1.2-96,20*1.2],[np.nan,0.]]),depth)
test('zero_depth_and_nan_source_invalid',zcase[4],[False,False])
test('zero_and_nan_status',zcase[5],['ZERO_DEPTH','SOURCE_OUTSIDE'])
test('invalid_depth_not_zero_error',np.isnan(zcase[3]),[True,True])

I=np.eye(4); K=np.array([[100.,0.,50.],[0.,100.,40.],[0.,0.,1.]])
p=m.project(np.array([[60.25,40.75]]),np.array([2.]),K,I,I,1e-9)
test('zero_motion_subpixel',p[0],[[60.25,40.75]],1e-12)
test('zero_motion_valid_and_fov',[p[2][0],p[3][0]],[True,True])
Ct=I.copy();Ct[0,3]=.5
p=m.project(np.array([[50.,40.]]),np.array([2.]),K,I,Ct,1e-9)
test('known_right_camera_translation_left_pixel',p[0],[[25.,40.]],1e-12)
test('known_translation_depth',p[1],[2.])
# Correct Z=8 for a 10 m range on ray(3/4,0,1). Helper is a Z consumer.
Ct=I.copy();Ct[0,3]=2.
p=m.project(np.array([[.75,0.],[.75,0.]]),np.array([8.,10.]),np.eye(3),I,Ct,1e-9)
test('Z_not_range_consumer',p[0],[[.5,0.],[.55,0.]],1e-15)
# Rotation transpose direction independent of the translation example.
R90=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
Cs=I.copy();Cs[:3,:3]=R90
p=m.project(np.array([[.5,0.]]),np.array([2.]),np.eye(3),Cs,I,1e-9)
test('source_rotation_direction',p[0],[[0.,.5]])
Ct=I.copy();Ct[:3,:3]=R90
p=m.project(np.array([[.5,0.]]),np.array([2.]),np.eye(3),I,Ct,1e-9)
test('target_rotation_inverse',p[0],[[0.,-.5]])
# Finite out-of-view projections preserved; FOV domain is <=575 exactly.
p=m.project(np.array([[575.,100.],[575.2,100.],[100.,575.],[100.,575.2]]),np.ones(4),np.eye(3),I,I,1e-9)
test('target_continuous_575_boundary',p[3],[True,False,True,False])
test('out_of_view_stays_projection_valid',p[2],[True]*4)
test('out_of_view_xy_not_clipped',p[0],[[575.,100.],[575.2,100.],[100.,575.],[100.,575.2]])
Ct=I.copy();Ct[2,3]=3.
p=m.project(np.array([[0.,0.]]),np.array([2.]),np.eye(3),I,Ct,1e-9)
test('behind_camera_negative_z',p[1],[-1.])
test('behind_camera_invalid',p[2],[False])
test('behind_camera_expected_nan',np.isnan(p[0]),[[True,True]])
p=m.project(np.zeros((4,2)),np.array([0.,1e-9,2e-9,np.nan]),np.eye(3),I,I,1e-9)
test('strict_epsilon_and_nonfinite',p[2],[False,False,True,False])
# A point displaced along epiline can have positive point error and zero line distance.
expected=m.project(np.array([[50.,40.]]),np.array([2.]),K,I,np.array([[1,0,0,.5],[0,1,0,0],[0,0,1,0],[0,0,0,1.]]),1e-9)[0][0]
matched=np.array([55.,40.]);target_line_distance=abs(matched[1]-40.)
test('known_target_epiline_identity',expected[1],40.,1e-12)
test('point_error_30_while_target_line_zero',[np.linalg.norm(matched-expected),target_line_distance],[30.,0.],1e-12)

result={'schema':'S81_IMPLEMENTATION_SYNTHETIC_REVIEW_V1','started_at_utc':START,
 'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewed_source_sha256':expected_source,'reviewed_contract_sha256':expected_contract,
 'test_source_sha256':sha(Path(__file__).resolve()),'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL',
 'checks_count':len(checks),'checks_passed':sum(c['passed'] for c in checks),'checks':checks,
 'scope':{'imported_guarded_module':True,'called_functions':['sample','project'],'called_main':False,
 'real_rgb_reads':0,'real_depth_reads':0,'real_npz_reads':0,'model_calls':0,'network_calls':0},
 'boundary_difference':'Earlier independent reference uses [0,width); frozen S81 uses <=last pixel centre. Both preserved. These tests specifically cover639/639.2/479/479.2 and575/575.2.',
 'limits':'Only helper implementation on artificial arrays; does not validate real depth synchronization, registration, measurements, or physical matching truth.'}
with (P/'IMPLEMENTATION_SYNTHETIC_REVIEW.json').open('x') as f:
 json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['status','checks_count','checks_passed']}))
raise SystemExit(0 if result['status']=='PASS' else 1)
