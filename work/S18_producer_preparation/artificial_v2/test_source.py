"""New S18 interface fixtures only: no S17C archive, image, checkpoint, GT or model read."""
import sys,importlib.util,json,hashlib
from pathlib import Path
import numpy as np
import torch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('s18',ROOT/'scripts/run_s18_memory_bridge.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
from src.s18_original_kernels import OriginalGeometryKernel
from src import vmem_memory_kernel as memory
OUT=ROOT/'work/S18_producer_preparation/artificial_v2';OUT.mkdir(exist_ok=False)
(OUT/'test_source.py').write_text(Path(__file__).read_text());(OUT/'runner_source.py').write_text((ROOT/'scripts/run_s18_memory_bridge.py').read_text())
torch.set_num_threads(8);torch.manual_seed(0);np.random.seed(0)
checks=[]
def ok(name,condition):
    if not condition:raise AssertionError(name)
    checks.append(dict(name=name,passed=True))
vm=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem')
args=dict(pipeline_source=str(vm/'modeling/pipeline.py'),util_source=str(vm/'utils/util.py'),kernels=str(ROOT/'src/s18_original_kernels.py'),memory_kernel=str(ROOT/'src/vmem_memory_kernel.py'),retrieval_kernel=str(ROOT/'src/vmem_retrieval_kernel.py'))
audit=M.ast_audit(args);ok('10 exact original AST gates',audit['count']==10)
k=OriginalGeometryKernel();k.device='cpu';k.surfels=[];k.surfel_to_timestep={};k.config=SimpleNamespace(surfel=SimpleNamespace(shrink_factor=.05,radius_scale=.5,conf_thresh=1,merge_normal_threshold=.6),model=SimpleNamespace(context_num_frames=4,target_num_frames=4))
y,x=torch.meshgrid(torch.arange(384,dtype=torch.float32),torch.arange(512,dtype=torch.float32),indexing='ij')
point=torch.stack([x,y,torch.ones_like(x)],dim=-1)[None].repeat(2,1,1,1)
depth=(x+2*y)[None].repeat(2,1,1);conf=(x-y)[None].repeat(2,1,1)
rp,rd,rc=k.resize_scene_inputs(point,depth,conf)
prov=M.bilinear_provenance(np)
ok('original scale .05 yields 19x25',list(rp.shape)==[2,19,25,3])
ok('first center input x/y9.5,9.5',np.array_equal(rp[0,0,0,:2].numpy(),[9.5,9.5]))
ok('last center input x489.5/y369.5, not recomputed ratio',np.array_equal(rp[0,-1,-1,:2].numpy(),[489.5,369.5]))
ok('three independent channels retain expected linear interpolation',float(rd[0,0,0])==28.5 and float(rc[0,-1,-1])==120.)
ok('bilinear provenance all four weights .25',np.array_equal(prov['weights'],np.full((19,25,4),.25)))
yy,xx=torch.meshgrid(torch.arange(4,dtype=torch.float32),torch.arange(4,dtype=torch.float32),indexing='ij')
toy=torch.stack([(xx-1.5)*.02,(yy-1.5)*.02,torch.ones_like(xx)],-1)
toy=torch.stack([toy,toy+torch.tensor([.002,0,0])]);d=torch.ones((2,4,4));c=torch.full((2,4,4),2.);c[:,1,1]=0
pose=np.tile(np.eye(4,dtype=np.float32),(2,1,1));f=np.full((2,1),20,np.float32)
r=dict(counters=dict(pointmap_calls=0,normal_calls=0,merge_calls=0,octree_root_queries=0,render_calls=0,process_calls=0))
obs=M.BridgeObserver(k,memory,torch,np,OUT,r,lambda x:None);obs.install();k.store_reduced_scene(toy,d,c,f,pose)
map_arrays,sources=obs.map_snapshot('map_after_frame1');obs.restore()
ok('two original pointmap calls',r['counters']['pointmap_calls']==2)
ok('original store performs default-tree merge once',r['counters']['merge_calls']==1)
ok('all nonmasked second-frame candidates get a root tree query',r['counters']['octree_root_queries']==15)
ok('map retains source lists and no colors',len(sources)==len(k.surfels)and all(s.color is None for s in k.surfels))
trace=json.loads((OUT/'merge_trace.json').read_text())
ok('actual merge break captured for at least one candidate',any(x['actual_matched_old_id']is not None for x in trace['records']))
ok('exact source query order retained without set conversion',all(len(x['normal_dots'])==len(x['neighbor_indices'])for x in trace['records']))
with np.load(OUT/'frame0_geometry.npz')as a:
    ok('normal border stays zero',not a['normal_map'][-1].any()and not a['normal_map'][:,-1].any())
    ok('confidence mask excludes only fixed bad cell',a['valid_mask'].sum()==15 and not a['valid_mask'][1,1])
    ok('actual candidate reduced cell IDs preserve C-order',np.array_equal(a['candidate_flat_ids'],np.delete(np.arange(16),5)))
    ok('full-grid diagnostic agrees selected original radius',np.array_equal(a['candidate_radii'],a['fullgrid_radius_diagnostic'].reshape(-1)[a['candidate_flat_ids']]))
status=M.consume_query(k,np,OUT,0,pose[0],np.array([[20.],[20.]],np.float32),r)
ok('original tiny memory render/process gives visible source',status=='SUCCESS')
votes=json.loads((OUT/'votes_query0.json').read_text());ok('at most two source candidates each count1',all(n==1 for _,n in votes['frame_count'])and len(votes['frame_count'])<=2)
pose2=pose[1].copy();pose2[:3,:3]=np.diag([-1,1,-1])
status=M.consume_query(k,np,OUT,1,pose2,np.array([[20.],[20.]],np.float32),r)
ok('no-visible-source preserved without padding',status=='NO_VISIBLE_SOURCE')
# Explicitly expose nonfinite normal failure from the original zero-difference rule.
k2=OriginalGeometryKernel();k2.device='cpu';k2.surfels=[];k2.surfel_to_timestep={};k2.config=k.config
failout=OUT/'nonfinite_original';failout.mkdir();r2=dict(counters=dict(pointmap_calls=0,normal_calls=0))
ob2=M.BridgeObserver(k2,memory,torch,np,failout,r2,lambda x:None);ob2.install()
try:
    k2.pointmap_to_surfels(torch.zeros((2,2,3)),np.array([20.],np.float32),torch.ones(2,2),torch.ones(2,2),np.eye(4,dtype=np.float32))
except ValueError:
    ok('zero-difference original nonfinite saved and refused', (failout/'frame0_geometry.npz').exists())
else:raise AssertionError('Nonfinite original not refused')
finally:ob2.restore()
ok('original Octree binding restored',memory.Octree is obs.original_octree)
M.write(OUT/'receipt.json',dict(status='PASS_ARTIFICIAL_ONLY',utc=M.utc(),checks=checks,check_count=len(checks),
  runner_sha256=M.sha(ROOT/'scripts/run_s18_memory_bridge.py'),kernel_sha256=M.sha(ROOT/'src/s18_original_kernels.py'),
  S17C_array_decodes=0,RGB_reads=0,checkpoint_reads=0,GT_reads=0,model_instances=0,
  description='Generated linear grids and 4x4 plane; original methods and observer; not actual S18 scene'))
print(json.dumps(dict(status='PASS_ARTIFICIAL_ONLY',checks=len(checks))))
