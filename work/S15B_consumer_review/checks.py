"""Independent artificial review of projection, provenance and score boundaries."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import s15b_memory_consumer as c
OUT=Path(__file__).resolve().parent
started=c.utc();checks=[]
def check(name,value):
    assert value,name
    checks.append(dict(name=name,status='PASS'))
def reject(name,fn,text):
    try:fn()
    except ValueError as e:check(name,text in str(e))
    else:raise AssertionError('expected rejection '+name)

def reference(z,valid,source,target,K,scale):
    n,h,w=z.shape;depth=np.zeros((h,w));ids=np.full((h,w),-1,dtype=np.int64);visits=0
    candidates={}
    for s in range(n):
        for row in range(h):
            for col in range(w):
                if not valid[s,row,col]:continue
                ray=np.linalg.solve(K,np.array([col,row,1.],dtype=float))
                world=source[s,:3,:3]@(ray*z[s,row,col])+source[s,:3,3]
                camera=target[:3,:3].T@(world-target[:3,3])
                if not np.isfinite(camera).all() or camera[2]<=0:continue
                projected=K@camera
                u=math.floor(projected[0]/projected[2]+.5);v=math.floor(projected[1]/projected[2]+.5)
                if not(0<=u<w and 0<=v<h):continue
                identity=s*h*w+row*w+col;visits+=1
                candidate=(float(camera[2]),identity)
                if (v,u) not in candidates or candidate<candidates[(v,u)]:candidates[(v,u)]=candidate
    for (v,u),(d,i) in candidates.items():depth[v,u]=d/scale;ids[v,u]=i
    return depth,ids,visits

source=np.tile(np.eye(4),(2,1,1));target=np.eye(4);K=np.eye(3)
z=np.ones((2,3,3));z[1]=.5;valid=np.ones_like(z,dtype=bool)
p,i,n=c.render(z,valid,source,target,K,2.)
check('nearer positive target z wins every collision',np.array_equal(p,np.full((3,3),.25)) and np.array_equal(i,np.arange(9,18).reshape(3,3)))
check('render counts all valid source visits before visibility',n==18)
z[:]=1;p,i,n=c.render(z,valid,source,target,K,1.)
check('equal z tie favors smaller source ordinal',np.array_equal(i,np.arange(9).reshape(3,3)))
# Shrink source x/y positions so multiple raster pixels round onto one target pixel.
source[0,:3,:3]=np.diag([.2,.2,1]);valid[1]=False
p,i,n=c.render(z,valid,source,target,K,1.)
check('same source equal z tie favors smaller row-major source pixel',i[0,0]==0 and n==9)
# This direct render fixture is intentionally a synthetic scaled source transform;
# actual input validation separately requires proper rotations.
source=np.tile(np.eye(4),(1,1,1));z=np.ones((1,1,1));valid=np.ones_like(z,dtype=bool)
for shift,expected in [(-.5,True),(.5,False),(-.5000001,False),(.4999999,True)]:
    source[0,0,3]=shift;p,i,n=c.render(z,valid,source,np.eye(4),np.eye(3),1.)
    check('floor(pixel+0.5) boundary '+str(shift),(n==1)==expected)
source[0,0,3]=0;source[0,2,3]=-1
p,i,n=c.render(z,valid,source,np.eye(4),np.eye(3),1.)
check('zero target z excluded',n==0 and p[0,0]==0 and i[0,0]==-1)
source[0,2,3]=-2;p,i,n=c.render(z,valid,source,np.eye(4),np.eye(3),1.)
check('negative target z excluded',n==0)
z=np.arange(1,33,dtype=float).reshape(2,4,4)/7+1
source=np.tile(np.eye(4),(2,1,1));source[0,:3,3]=[.2,-.1,0];source[1,:3,3]=[-.25,.15,.1]
theta=.08;target=np.eye(4);target[:3,:3]=[[np.cos(theta),0,np.sin(theta)],[0,1,0],[-np.sin(theta),0,np.cos(theta)]];target[:3,3]=[.05,-.07,.03]
K=np.array([[3.,0.,1.5],[0.,3.2,1.5],[0.,0.,1.]])
valid=np.ones_like(z,dtype=bool);valid[0,0,0]=False
a=c.render(z,valid,source,target,K,1.7);b=reference(z,valid,source,target,K,1.7)
check('different scalar projection/reduction agrees',np.allclose(a[0],b[0],atol=1e-12,rtol=1e-12) and np.array_equal(a[1],b[1]) and a[2]==b[2])

old=np.ones((4,224,224));new=np.full_like(old,2.);poses=np.tile(np.eye(4),(4,1,1))
bridge=dict(old_self_z=old,new_self_z=new,source_c2w=poses,K=c.K_FIXED,scale_model_per_meter=np.array(2.))
proposals=dict(old_self_z_model=old.copy(),new_self_z_model=new.copy(),source_indices=np.array([0,3,6,9]),source_poses=poses.copy(),K=np.repeat(c.K_FIXED[None],4,axis=0),s_model_per_metric=np.array(2.),old_conf_self=np.ones_like(old),new_conf_self=np.ones_like(old))
targets=dict(target_c2w=poses.copy(),K=c.K_FIXED.copy(),scale_model_per_meter=np.array(2.))
masks={k:np.zeros_like(old,dtype=bool) for k in ['pool_new','split_new','matched_absolute_new']}
check('all seven methods validate same source camera scale K',c.validate_inputs(bridge,proposals,targets,masks)[4].all())
bad=deepcopy(bridge);bad['source_c2w'][0,0,3]=.1
reject('changed source camera rejected',lambda:c.validate_inputs(bad,proposals,targets,masks),'camera binding')
bad=deepcopy(proposals);bad['s_model_per_metric']=3.
reject('proposal scale mismatch rejected',lambda:c.validate_inputs(bridge,bad,targets,masks),'same finite positive scale')
bad=deepcopy(proposals);bad['source_indices']=[0,6,3,9]
reject('source order mismatch rejected',lambda:c.validate_inputs(bridge,bad,targets,masks),'source order')
bad=deepcopy(masks);bad['pool_new'][0,0,0]=True
reject('partial pixel mask cannot masquerade as block action',lambda:c.validate_inputs(bridge,proposals,targets,bad),'entire 16x16')
bad=deepcopy(masks);bad['pool_new']=bad['pool_new'].astype(float)
reject('float mask rejected',lambda:c.validate_inputs(bridge,proposals,targets,bad),'bool source mask')
bad=deepcopy(targets);bad['target_c2w'][0,0,0]=-1
reject('reflected target pose rejected',lambda:c.validate_inputs(bridge,proposals,bad,masks),'proper optical rotation')
check('equal mean confidence ties retain entire old block',not c.confidence_blocks(proposals).any())
proposals['new_conf_self'][0,0,0]=257.
conf=c.confidence_blocks(proposals)
check('full 16x16 mean decides all block pixels',conf[0,:16,:16].all() and conf.sum()==256)
proposals['new_conf_self'][0,0,0]=-255.
check('negative difference mean keeps old block',not c.confidence_blocks(proposals).any())

pred=np.zeros((7,4,224,224));gt=np.zeros((4,224,224))
gt[:,:1,:4]=1.;pred[:,:,:1,:4]=1.
pred[0,:,0,0]=1.25;pred[0,:,0,1]=.8;pred[0,:,0,2]=0
pred[1,:,0,3]=0
rows,means=c.evaluate_predictions(pred,gt)
row=rows[0]
check('delta1 strict upper and reciprocal threshold both fail',row['correct_delta1']==1)
check('missing prediction remains in all-GT denominator',row['gt_valid']==4 and row['prediction_valid_on_gt']==3 and row['delta1_all_gt']==.25)
check('seven-method common domain keeps intersection only',all(r['common']['count']==2 for r in rows))
check('all seven methods share GT denominator',all(r['gt_valid']==4 for r in rows))
check('equal four-frame primary delta1',means['never']['delta1_all_gt']==.25)
pred[:]=0;gt[:]=0;gt[0,0,0]=.0054;pred[:,:,0,0]=.00675
rows,_=c.evaluate_predictions(pred,gt)
check('strict quotient edge preserved over multiplied inequalities',rows[0]['correct_delta1']==int(max(.00675/.0054,.0054/.00675)<1.25))
check('empty GT frame remains null not success',rows[7]['delta1_all_gt'] is None and rows[7]['gt_valid']==0)
pred[:]=0;gt[:]=0;gt[0,0,0]=1.;pred[:,0,0,0]=1.;gt[1,0,:3]=1.;gt[2,0,0]=1.;gt[3,0,0]=1.
rows,means=c.evaluate_predictions(pred,gt)
check('equal-frame and pixel-weighted summaries stay distinct',means['never']['delta1_all_gt']==.25 and means['never']['pixel_weighted_delta1']==1/6)

source=Path(c.__file__).read_text()
score_source=source[source.index('def score('):source.index('def main(')]
check('seal SHA and successful prediction verified before first Image.open',score_source.index('sealed successful prediction run')<score_source.index('with Image.open'))
check('sealed source snapshot hash verified before GT reads',score_source.index("ident(base/'source_snapshot.py'")<score_source.index('with Image.open'))
check('prediction stage contains no image decoder', 'Image.open' not in source[source.index('def predict('):source.index('def evaluate_predictions')])
check('GT resize and crop fixed without smoothing',"Image.Resampling.NEAREST).crop((37,0,261,224))" in score_source)

# Exercise all seven method selections and render calls with synthetic arrays.
# These are dictionary injections, not reads of any actual project prediction file.
synthetic_out=OUT/'synthetic_seven_methods';synthetic_out.mkdir(exist_ok=False)
new[:,0,0]=0.;proposals['new_self_z_model'][:,0,0]=0.
fake_inputs={'bridge':bridge,'proposals':proposals,'target_cameras':targets,'rule_masks':masks}
old_arrays,old_ident=c.arrays,c.ident
try:
    c.arrays=lambda path:fake_inputs[path]
    c.ident=lambda path,digest:None
    c.predict(dict(predict_identities={},bridge='bridge',proposals='proposals',target_cameras='target_cameras',rule_masks='rule_masks'),synthetic_out,{})
finally:
    c.arrays,c.ident=old_arrays,old_ident
with np.load(synthetic_out/'target_predictions.npz') as q:
    depth=q['depth_m'];provenance=q['source_pixel_identity']
    check('seven-method half blend is exact arithmetic midpoint depth',np.all(depth[2,:,1:,1:]==.75) and np.all(depth[0,:,1:,1:]==.5) and np.all(depth[1,:,1:,1:]==1.))
    check('all seven share old-new-positive source eligibility',not q['source_valid'][:,0,0].any() and np.all(depth[:,:,0,0]==0))
    check('same-source raster provenance retained across all seven methods',np.array_equal(provenance,np.broadcast_to(provenance[0,0],provenance.shape)))
receipt=dict(schema='s15b-consumer-independent-artificial-review-v1',status='PASS',started_utc=started,completed_utc=c.utc(),check_count=len(checks),checks=checks,
    scope='Different-author code review plus artificial numerical/reference checks; no real arrays/images/GT or model.',
    real_image_decodes=0,real_array_decodes=0,real_gt_reads=0,model_calls=0,
    runner_sha256=hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest(),
    original_runner_sha256=hashlib.sha256((OUT/'source_before_review.py').read_bytes()).hexdigest(),
    numpy_version=np.__version__,python=sys.executable)
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['status','check_count','runner_sha256','completed_utc']}))
