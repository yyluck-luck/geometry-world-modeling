"""Read pinned source only; produce invented data in NumPy1.26/Torch CPU."""
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Union
import ast
import hashlib
import json
import math
import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem')
OUT = Path(__file__).resolve().parent / 'artificial_packet'
OUT.mkdir(exist_ok=False)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
report = dict(started_utc=datetime.now(timezone.utc).isoformat(), numpy=np.__version__, torch=torch.__version__,
              input_kind='INVENTED_ARRAYS_ONLY', real_archive_reads=0, gt_reads=0, model_calls=0,
              source_sha256=sha(Path(__file__)))
assert np.__version__ == '1.26.4' and torch.__version__ == '2.7.0'
torch.set_num_threads(8)
torch.manual_seed(0)
paths = {'modeling/pipeline.py':'90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e',
         'utils/util.py':'0b71dcf6d4a43109d785f49d9c6def37b1256c4d189ab9438bfb185f3099f013'}
for p, h in paths.items(): assert sha(ROOT/p) == h
pipeline = next(x for x in ast.parse((ROOT/'modeling/pipeline.py').read_text()).body if isinstance(x, ast.ClassDef) and x.name == 'VMemPipeline')
names = {'estimate_normal_from_pointmap','pointmap_to_surfels','merge_surfels','render_surfels_to_image','get_frame_distribution','process_retrieved_spatial_information'}
methods = [n for n in pipeline.body if isinstance(n, ast.FunctionDef) and n.name in names]
classes = [n for n in ast.parse((ROOT/'utils/util.py').read_text()).body if isinstance(n, ast.ClassDef) and n.name in {'Surfel','Octree'}]
module = ast.fix_missing_locations(ast.Module(body=classes+[ast.ClassDef(name='Isolated', bases=[], keywords=[], body=methods, decorator_list=[])], type_ignores=[]))
env = dict(np=np, torch=torch, F=F, math=math, Union=Union)
exec(compile(module, '<pinned isolated artificial methods>', 'exec'), env)
obj = env['Isolated'](); obj.device='cpu'
obj.config=SimpleNamespace(surfel=SimpleNamespace(conf_thresh=1), model=SimpleNamespace(context_num_frames=4))
y,x=np.mgrid[:384,:512].astype(np.float32)
z=np.float32(1.3)+np.float32(.0003)*x+np.float32(.0007)*y
point=np.stack(((x-np.float32(256))*np.float32(.002), (y-np.float32(192))*np.float32(.002),z),axis=-1)
point=np.stack((point,point+np.array([.004,0,.006],dtype=np.float32)))
depth=point[...,2].copy()
conf=np.full((2,384,512),2,dtype=np.float32);conf[:,50:90,100:160]=0
pose=np.tile(np.eye(4,dtype=np.float32),(2,1,1));pose[1,:3,3]=[.03,.01,.02]
focal=np.array([[19.5],[20.5]],dtype=np.float32)
def resize(a):
 t=torch.from_numpy(a)
 if a.ndim==4: return F.interpolate(t.permute(0,3,1,2),scale_factor=.05,mode='bilinear').permute(0,2,3,1).numpy()
 return F.interpolate(t[:,None],scale_factor=.05,mode='bilinear')[:,0].numpy()
rp,rd,rc=resize(point),resize(depth),resize(conf)
np.savez(OUT/'inputs.npz',pointcloud=point,depths=depth,confs=conf,c2ws=pose,scaled_focal=focal)
np.savez(OUT/'reduced.npz',pointcloud=rp,depths=rd,confs=rc)
for i in range(2):
 p,d,c=(torch.from_numpy(a[i]) for a in (rp,rd,rc))
 nm=obj.estimate_normal_from_pointmap(p)
 threshold=torch.quantile(d,.999)
 mask=(d<=threshold)&(c>=1)
 surfels=obj.pointmap_to_surfels(p,torch.from_numpy(focal[i]),d,c,torch.from_numpy(pose[i]))
 np.savez(OUT/f'geometry{i}.npz',normal_map=nm.numpy(),depth_threshold=threshold.numpy(),valid_mask=mask.numpy(),candidate_flat_ids=np.flatnonzero(mask.numpy()),candidate_positions=np.array([s.position for s in surfels]),candidate_normals=np.array([s.normal for s in surfels]),candidate_radii=np.array([s.radius for s in surfels]))
# Non-square output and quantile fractional rank edge.
odd=(np.mgrid[:41,:61][1]+2*np.mgrid[:41,:61][0]).astype(np.float32)[None]
np.savez(OUT/'small.npz',odd=odd,odd_reduced=resize(odd),quantile_input=np.array([1,2,3,4,5,6],dtype=np.float32),quantile=torch.quantile(torch.arange(1,7,dtype=torch.float32),.999).numpy())
# Actual Octree branching, inclusive overlap, raw traversal ordering.
old=np.array(list(__import__('itertools').product([-1,0,1],[-1,1],[-.1,.1])),dtype=np.float32)
queries=np.array([[0,0,0],[.99,1,.1],[0,1,.1]],dtype=np.float32)
tree=env['Octree'](old,max_points=10)
neighbors=[tree.query_ball_point(q,.21) for q in queries]
np.savez(OUT/'tree.npz',old=old,queries=queries)
report['tree_neighbors']=[[int(v) for v in row] for row in neighbors]
# Two identical FP32 surfels, oblique FP32 pose gives non-representable mean depth.
angle=np.float32(.31)
r=np.array([[np.cos(angle),0,np.sin(angle)],[0,1,0],[-np.sin(angle),0,np.cos(angle)]],dtype=np.float32)
pose_r=np.eye(4,dtype=np.float32);pose_r[:3,:3]=r;pose_r[:3,3]=[.01,0,.03]
p=np.array([[.1,0,1.3],[.1,0,1.3],[.5,0,1.4]],dtype=np.float32)
n=np.tile(np.array([0,0,1],dtype=np.float32),(3,1));rad=np.array([.2,.2,.11],dtype=np.float32)
surfels=[env['Surfel'](a,b,c) for a,b,c in zip(p,n,rad)]
render=obj.render_surfels_to_image(surfels,pose_r,np.array([[25.],[25.]],dtype=np.float32),np.array([20,15],dtype=np.float32),40,30)
np.savez(OUT/'render_inputs.npz',positions=p,normals=n,radii=rad,c2w=pose_r,focal=np.array([[25.],[25.]],dtype=np.float32),pp=np.array([20,15],dtype=np.float32))
np.savez(OUT/'render.npz',**render)
obj.surfel_to_timestep={0:[0],1:[1],2:[0,1]}
weights,counts=obj.process_retrieved_spatial_information(render)
report['votes']={'weights':weights,'counts':counts,'sources':[[0],[1],[0,1]]}
report['identities']={p.name:sha(p) for p in OUT.glob('*.npz')}
report['status']='PASS_ARTIFICIAL_ORIGINAL_PACKET';report['completed_utc']=datetime.now(timezone.utc).isoformat()
(OUT/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'files':len(report['identities']),'output':str(OUT)}))
