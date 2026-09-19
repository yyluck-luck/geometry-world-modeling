"""S15 calibration algebra only. No real RGB, depth, GT, or model is read."""
from pathlib import Path
import datetime, hashlib, json
import cv2
import numpy as np

start=datetime.datetime.now(datetime.timezone.utc).isoformat()
K=np.array([[542.822841,0,315.593520],[0,542.576870,237.756098],[0,0,1]],np.float64)
d=np.array([.039903,-.099343,-.000730,-.000144,0.],np.float64)
h,w=480,640
y,x=np.indices((h,w),dtype=np.float64)
xn=(x-K[0,2])/K[0,0];yn=(y-K[1,2])/K[1,1];r2=xn*xn+yn*yn
rad=1+d[0]*r2+d[1]*r2*r2+d[4]*r2*r2*r2
mx=K[0,0]*(xn*rad+2*d[2]*xn*yn+d[3]*(r2+2*xn*xn))+K[0,2]
my=K[1,1]*(yn*rad+d[2]*(r2+2*yn*yn)+2*d[3]*xn*yn)+K[1,2]
a,b=cv2.initUndistortRectifyMap(K,d,np.eye(3),K,(w,h),cv2.CV_32FC1)
checks=[]
def ck(name,passed,**details):
 checks.append(dict(name=name,passed=bool(passed),**details))
 if not passed: raise AssertionError(name)
err=max(np.max(abs(a-mx)),np.max(abs(b-my)))
ck('Brown forward-map agrees OpenCV FP32 maps',err<4e-5,max_pixel_error=float(err),fixed_tolerance=4e-5)
z1,z2=cv2.initUndistortRectifyMap(K,np.zeros(5),np.eye(3),K,(w,h),cv2.CV_32FC1)
e=max(np.max(abs(z1-x)),np.max(abs(z2-y)))
ck('zero distortion identity',e<1e-5,max_pixel_error=float(e),fixed_tolerance=1e-5)
label=(np.arange(h*w,dtype=np.int32).reshape(h,w)+1).astype(np.float32)
label[:,w//2]=0
remapped=cv2.remap(label,a,b,cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
ck('nearest remap preserves discrete depth labels and zeros',np.all(remapped==np.floor(remapped)) and np.isin(remapped,label).all(),zero_count=int((remapped==0).sum()))
plane=np.full((h,w),12500,np.uint16)
plane_out=cv2.remap(plane,a,b,cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
valid=plane_out>0
z=plane_out.astype(np.float64)/5000
pts=np.stack((xn*z,yn*z,z),axis=-1)
ck('frontoparallel plane z retained without range normalization',np.all(z[valid]==2.5) and np.all(pts[...,2][valid]==2.5),depth_m=2.5,range_off_axis_m=float(np.linalg.norm(pts[0,0])))
Kc=K.copy();Kc[0,0]*=299/640;Kc[1,1]*=224/480;Kc[0,2]=(K[0,2]+.5)*299/640-.5-37;Kc[1,2]=(K[1,2]+.5)*224/480-.5
u=np.array([0.,315.593520,639.]);v=np.array([0.,237.756098,479.]);up=(u+.5)*299/640-.5-37;vp=(v+.5)*224/480-.5
ke=max(np.max(abs((u-K[0,2])/K[0,0]-(up-Kc[0,2])/Kc[0,0])),np.max(abs((v-K[1,2])/K[1,1]-(vp-Kc[1,2])/Kc[1,1])))
ck('half pixel resize and center crop preserve pinhole rays',ke<1e-12,max_error=float(ke),fixed_tolerance=1e-12)
M=np.array([[1.0157,.1828,-.2389],[.0009,-.8431,-.6413],[-.3009,.6147,-.8085]])
sv=np.linalg.svd(M)[1];ortho=np.max(abs(M.T@M-np.eye(3)))
ck('official Tm rejected as rigid rotation',ortho>1e-4,singular_values=sv.tolist(),determinant=float(np.linalg.det(M)),max_orthogonality_error=float(ortho),SO3_gate=1e-4)
Tros=np.array([[-1,0,0],[0,0,1],[0,1,0]])
ck('Tros is invertible rotation and self inverse',np.array_equal(Tros@Tros,np.eye(3)) and np.linalg.det(Tros)==1,determinant=float(np.linalg.det(Tros)))
res={'schema':'s15-artificial-calibration-checks-v1','started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'numpy_version':np.__version__,'opencv_version':cv2.__version__,'evidence_kind':'ARTIFICIAL_ALGEBRA_ONLY','real_image_reads':0,'real_depth_reads':0,'real_trajectory_reads':0,'model_calls':0,'K_native':K.tolist(),'distortion_opencv_k1_k2_p1_p2_k3':d.tolist(),'K_224':Kc.tolist(),'max_native_displacement_pixels':float(np.max(np.hypot(mx-x,my-y))),'checks':checks,'status':'PASS'}
Path(__file__).with_name('artificial_checks.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res,indent=2))
