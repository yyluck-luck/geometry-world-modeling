"""Finite numerical checks without any new photo or generated-pixel reads."""
from pathlib import Path
import json
import numpy as np
from observer import PAIRS, classify, normalized_K_to_index, requested_homography, rotation_y, sha, write_json

D=Path(__file__).resolve().parent
Knorm=np.array([[.9,0,.5],[0,1.1,.5],[0,0,1.]])
K=normalized_K_to_index(Knorm,576,576)
assert K[0,2]==K[1,2]==287.5
p1=np.eye(4);p2=np.eye(4);p1[:3,:3]=rotation_y(-1.25);p2[:3,:3]=rotation_y(5.)
H=requested_homography(K,K,p1,p2)
points=np.array([[35.,29.],[180.,210.],[287.5,287.5],[480.,502.],[566.,559.]])
direct=[]
for x,y in points:
    ray=np.linalg.solve(K,np.array([x,y,1.]))
    world=p1[:3,:3]@ray
    second=np.linalg.solve(p2[:3,:3],world)
    pixel=K@second
    direct.append(pixel[:2]/pixel[2])
hp=np.column_stack([points,np.ones(len(points))])@H.T
homogeneous=hp[:,:2]/hp[:,2:]
error=float(np.max(np.abs(np.array(direct)-homogeneous)))
assert error<1e-10
inverse=requested_homography(K,K,p2,p1)
product=H@inverse;product/=product[2,2]
assert np.max(np.abs(product-np.eye(3)))<1e-10
assert len(PAIRS)==15 and len(set(PAIRS))==15
assert all((i,i+1) in PAIRS for i in range(8)) and all((0,j) in PAIRS for j in range(1,9))
calibration=json.loads((D/'CALIBRATION.json').read_text())
cases=json.loads((D/'controls/ALL_16_CONTROL_CASES.json').read_text())
assert len(cases)==16
for case in cases:
    verdict=classify(case['measurement'],calibration)
    assert verdict==case['verdict']
    assert (verdict=='CONSISTENT_WITH_RECORDED_NOMINAL_REQUEST')==(case['kind']=='correct')
assert classify({'status':'UNKNOWN'},calibration)=='UNKNOWN_MATCHING'
receipt=dict(status='PASS_FINITE_MATH_AND_SAVED_CONTROL_SCOPE_CHECKS',
             independent_direct_ray_vs_H_max_abs_px=error,inverse_H_composition_pass=True,
             pixel_center_mapping_pass=True,unique_pair_count=15,saved_control_cases_checked=16,
             photo_body_reads=0,generated_pixel_body_reads=0,model_calls=0,
             source_sha256=sha(Path(__file__)),observer_sha256=sha(D/'observer.py'))
write_json(D/'MATH_AND_SCOPE_CHECK_RECEIPT.json',receipt)
print(json.dumps(receipt,indent=2))
