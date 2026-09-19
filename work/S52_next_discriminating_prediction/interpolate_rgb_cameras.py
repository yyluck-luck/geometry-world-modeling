"""Interpolate already identified RGB-time cameras from real TUM text metadata."""
from bisect import bisect_left
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
import scipy
from scipy.spatial.transform import Rotation, Slerp

R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D=Path(__file__).resolve().parent
evidence=R/'work/S50_heldout_reference_metadata/evidence.json'
assert hashlib.sha256(evidence.read_bytes()).hexdigest()=='31e028c93a47b8bf2b84b85420c9d7748b4a376012f95d10df1bfe8cb432141d'
source=json.loads(evidence.read_text())
gt=R/'data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk/groundtruth.txt'
body=gt.read_bytes()
assert hashlib.sha256(body).hexdigest()=='f19dc674dc43b6c4957038e1a22906122c19c60893e664dafb0e0abe537906ca'
def ns(t):return int(Decimal(t)*Decimal(10)**9)
rows=[line.split() for line in body.decode().splitlines() if line.strip() and not line.startswith('#')]
times=[ns(row[0]) for row in rows]
assert all(a<b for a,b in zip(times,times[1:]))
def qmatrix(q):
    x,y,z,w=q/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def custom_slerp(q0,q1,a):
    q0=q0/np.linalg.norm(q0);q1=q1/np.linalg.norm(q1)
    dot=float(np.dot(q0,q1))
    if dot<0:q1=-q1;dot=-dot
    dot=min(1.0,max(-1.0,dot))
    if dot>1-1e-12:q=(1-a)*q0+a*q1
    else:
        theta=np.arccos(dot)
        q=(np.sin((1-a)*theta)*q0+np.sin(a*theta)*q1)/np.sin(theta)
    return q/np.linalg.norm(q)
def interpolate(t):
    n=ns(t);i=bisect_left(times,n)
    assert 0<i<len(rows)
    before,after=rows[i-1],rows[i]
    a=(n-times[i-1])/(times[i]-times[i-1])
    assert 0<=a<=1
    p0=np.array(before[1:4],float);p1=np.array(after[1:4],float)
    q0=np.array(before[4:],float);q1=np.array(after[4:],float)
    q=custom_slerp(q0,q1,a);rotation=qmatrix(q)
    independent_rotation=Slerp([0,1],Rotation.from_quat([q0,q1]))([a]).as_matrix()[0]
    disagreement=float(np.max(np.abs(rotation-independent_rotation)))
    assert disagreement<1e-12
    assert np.max(np.abs(rotation.T@rotation-np.eye(3)))<1e-12
    assert abs(np.linalg.det(rotation)-1)<1e-12
    sign_rotation=qmatrix(custom_slerp(q0,-q1,a))
    assert np.max(np.abs(rotation-sign_rotation))<1e-12
    c2w=np.eye(4);c2w[:3,:3]=rotation;c2w[:3,3]=(1-a)*p0+a*p1
    return dict(timestamp=t,before=before,after=after,gap_ns=times[i]-times[i-1],fraction=a,
                quaternion_xyzw=q.tolist(),c2w=c2w.tolist(),
                maximum_input_quaternion_norm_error=float(max(abs(np.linalg.norm(q0)-1),abs(np.linalg.norm(q1)-1))),
                scipy_rotation_max_abs_difference=disagreement)
outputs=[]
for candidate in source['candidate_chain']:
    rgb=interpolate(candidate['rgb_capture_timestamp_text'])
    bracket=candidate['rgb_time_gt_bracket']
    assert rgb['before']==bracket['before_values_as_published_text']
    assert rgb['after']==bracket['after_values_as_published_text']
    depth=interpolate(candidate['associated_depth_timestamp_text'])
    c_rgb=np.array(rgb['c2w']);c_depth=np.array(depth['c2w'])
    relative=np.linalg.inv(c_depth)@c_rgb
    outputs.append(dict(role=candidate['role'],frame_index=candidate['existing_frame_index'],rgb_camera=rgb,associated_depth_time_camera=depth,
                        rgb_minus_depth_ns=ns(rgb['timestamp'])-ns(depth['timestamp']),
                        camera_center_distance_m=float(np.linalg.norm(c_rgb[:3,3]-c_depth[:3,3])),
                        rotation_difference_degrees=float(Rotation.from_matrix(relative[:3,:3]).magnitude()*180/np.pi),
                        camera_at_rgb_expressed_in_depth_camera=relative.tolist(),historically_model_exposed=True))
receipt=dict(schema='s52-rgb-time-camera-interpolation-v1',status='REAL_TEXT_METADATA_CAMERA_INTERPOLATION_ONLY',completed_utc=datetime.now(timezone.utc).isoformat(),
    source_evidence_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),groundtruth_path=str(gt),groundtruth_sha256=hashlib.sha256(body).hexdigest(),
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),python_version=platform.python_version(),numpy_version=np.__version__,scipy_version=scipy.__version__,
    coordinate_definition='TUM published groundtruth: RGB optical-center camera-to-world translation in metres and orientation quaternion xyzw.',
    source_url='https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats',
    interpolation='Piecewise linear translation and shortest-arc SLERP of normalized published quaternions; no extrapolation.',
    validation='Root custom quaternion implementation crosschecked against SciPy, rotation orthonormality/determinant and quaternion sign equivalence. Not an external independent review.',
    camera_results=outputs,image_bodies_read=0,image_decodes=0,model_runs=0,
    limitations=['Interpolation is an assumed motion model between recorded mocap poses, not exact measured pose at each RGB instant.',
                 'No camera intrinsics, distortion, future 576 preprocessing, visibility masks or new input exclusion manifest are certified here.',
                 'Measured camera displacement does not establish any pixel error or explain a generation failure.',
                 'Historical target exposure is retained; no unseen confirmation or generation authorization.'],new_method_validated=False)
with (D/'RGB_TIME_CAMERA_RECEIPT.json').open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({x['role']:{'translation_mm':x['camera_center_distance_m']*1000,'rotation_degrees':x['rotation_difference_degrees']} for x in outputs}))
