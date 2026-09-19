"""Exploratory numeric schema checks on one camera JSON; no images/objects."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,time,math
import numpy as np

S=Path(__file__).parent
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    started=datetime.now(timezone.utc).isoformat();t=time.monotonic()
    source=S/'rtmv_range_02/07_json_quarantine.bin'
    raw=source.read_bytes()
    assert sha(raw)=='e51fd4f99d0fc45d4eb34d8dc448545e3e412c4a4e8621a8b55ffe9bdc953e76'
    data=json.loads(raw)['camera_data']
    A=np.asarray(data['cam2world'],dtype=np.float64)
    B=np.asarray(data['camera_view_matrix'],dtype=np.float64)
    C,V=A.T,B.T
    R=C[:3,:3];eye=np.asarray(data['camera_look_at']['eye'],dtype=np.float64)
    at=np.asarray(data['camera_look_at']['at'],dtype=np.float64)
    up=np.asarray(data['camera_look_at']['up'],dtype=np.float64)
    forward=(at-eye)/np.linalg.norm(at-eye)
    right=np.cross(forward,up);right/=np.linalg.norm(right)
    upward=np.cross(right,forward)
    look_R=np.column_stack([right,upward,-forward])
    x,y,z,w=map(float,data['quaternion_world_xyzw'])
    Q=np.asarray([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
        [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
        [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    k=data['intrinsics'];K=np.asarray([[k['fx'],0,k['cx']],[0,k['fy'],k['cy']],[0,0,1]],dtype=np.float64)
    D=np.diag([1.,-1.,-1.,1.]);Copt=C@D
    aim_opt=np.linalg.inv(Copt)@np.append(at,1.)
    pixel_h=K@aim_opt[:3];pixel=pixel_h[:2]/pixel_h[2]
    e=lambda v:float(np.max(np.abs(v)))
    vals=dict(c2w_last_row_error=e(C[3]-np.array([0,0,0,1])),view_last_row_error=e(V[3]-np.array([0,0,0,1])),inverse_product_error=e(V@C-np.eye(4)),rotation_orthogonality_error=e(R.T@R-np.eye(3)),rotation_determinant=float(np.linalg.det(R)),eye_translation_max_error=e(C[:3,3]-eye),look_at_basis_max_error=e(R-look_R),quaternion_norm=float(math.sqrt(x*x+y*y+z*z+w*w)),quaternion_rotation_max_error=e(R-Q),lookat_projection_pixels=pixel.tolist(),principal_point_max_error_px=e(pixel-np.array([k['cx'],k['cy']])),lookat_optical_z=float(aim_opt[2]),horizontal_fov_degrees=math.degrees(2*math.atan(data['width']/(2*k['fx']))),vertical_fov_degrees=math.degrees(2*math.atan(data['height']/(2*k['fy']))))
    checks=dict(shapes=A.shape==(4,4) and B.shape==(4,4),finite=bool(np.isfinite(A).all() and np.isfinite(B).all() and np.isfinite(K).all()),positive_dimensions=data['width']>0 and data['height']>0,positive_focal=k['fx']>0 and k['fy']>0,principal_in_image=0<=k['cx']<data['width'] and 0<=k['cy']<data['height'],proper_rotation=abs(vals['rotation_determinant']-1)<1e-5,axis_toward_aim=vals['lookat_optical_z']>0)
    for key in ['c2w_last_row_error','view_last_row_error','inverse_product_error','rotation_orthogonality_error','eye_translation_max_error','look_at_basis_max_error','quaternion_rotation_max_error']:
        checks[key]=vals[key]<1e-5
    checks['principal_projection']=vals['principal_point_max_error_px']<1e-3
    out=dict(status='PASS_METADATA_INTERNAL_CONSISTENCY' if all(checks.values()) else 'CHECK_FAILED',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-t,source=str(source),source_sha256=sha(raw),code_sha256=sha(Path(__file__).read_bytes()),numpy_version=np.__version__,image_size=[data['width'],data['height']],values=vals,checks=checks,scene_id='00000',view_id='00108',source_choice='first regular JSON in frozen bounded archive traversal; not chosen from image quality',exposure='Whole JSON bytes read and parsed, including objects; only camera_data examined. No objects analysis, image/depth payload or model.',limit='Source/schema exploration after camera fields inspected, not preregistered scientific hypothesis, independent scene qualification, EXR projection validation, metric world units or new method. Large scene bbox fields not used as scale.',new_model_runs=0,new_image_or_depth_decodes=0)
    p=S/'CAMERA_METADATA_CHECK.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
