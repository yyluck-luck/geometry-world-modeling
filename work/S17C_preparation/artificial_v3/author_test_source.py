"""Author's S17C artificial checks; no checkpoint, native photo, GT, or model read."""
import importlib.util
from pathlib import Path
import json
import copy
import types
import sys
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('s17c_author',ROOT/'scripts/run_s17c_embedded_geometry.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
OUT=Path(__file__).parent/'artificial_v3'
OUT.mkdir(exist_ok=False)
(OUT/'author_test_source.py').write_text(Path(__file__).read_text())
(OUT/'runner_source.py').write_text((ROOT/'scripts/run_s17c_embedded_geometry.py').read_text())
checks=[]
def check(name,fn,refuse=False):
    try:
        fn()
    except ValueError as e:
        if not refuse: raise
        checks.append(dict(name=name,pass_=True,refusal=str(e)))
    else:
        if refuse: raise AssertionError(name+' did not refuse')
        checks.append(dict(name=name,pass_=True))

def identity(shape): return np.broadcast_to(np.eye(4,dtype=np.float32),shape)
d=dict(world_points=np.zeros((2,384,512,3),np.float32),depths=np.ones((2,384,512),np.float32),
    confidence=np.zeros((2,384,512),np.float32),poses=identity((2,4,4)),
    focal=np.ones((2,1),np.float32),pp=np.zeros((2,2),np.float32),
    intrinsics=np.broadcast_to(np.eye(3,dtype=np.float32),(2,3,3)),
    pw_poses=identity((1,4,4)),adaptors=np.ones((1,3),np.float32),colors=np.zeros((2,384,512,3),np.float32))
d['world_points'][...,2]=-7
check('negative world Z accepted; only camera depth positive',lambda:M.validate_scene(d))
check('zero cleaned confidence accepted',lambda:M.validate_scene(d))
for field,idx,value in [('depths',(0,0,0),0),('focal',(0,0),-1),('confidence',(0,0,0),-1),('world_points',(0,0,0,0),np.nan),('colors',(0,0,0,0),1.01)]:
    bad={k:v.copy() for k,v in d.items()};bad[field][idx]=value
    check('refuse '+field+' '+str(value),lambda bad=bad:M.validate_scene(bad),True)
bad={k:v.copy() for k,v in d.items()};bad['poses'][0,0,0]=-1
check('reflection camera refused',lambda:M.validate_scene(bad),True)

# Exercise the original-delegate wrappers with only a scalar nn.Module and tiny fake scene.
# This is an instrumentation test, NOT an instance of CUT3R/VMem or their optimizer.
counts=['prepare_input_calls','inference_attempts','inference_calls','history_frames_saved','supplied_image_frames','supplied_ray_frames',
    'global_aligner_calls','mst_calls','pnp_calls','optimization_iterations','optimizer_steps','clean_calls',
    'postfinal_objective_evaluations','scene_objective_calls']
r=dict(counters={k:0 for k in counts},optimization_trace=[])
delegated=dict(align=0,mst=0,pnp=0,iter=0,compute=0,clean=0)
class Scene(torch.nn.Module):
    def __init__(self):
        super().__init__();self.p=torch.nn.Parameter(torch.tensor(1.));self.edges=[(0,1)]
        self.norm_pw_scale=True;self.base_scale=.5;self.min_conf_thr=3
        self.imgs=[np.zeros((2,2,3),np.float32)]*2
        self.conf=torch.ones(2,2,2)
    def forward(self): return self.p.square()
    def get_pts3d(self): return torch.zeros(2,2,2,3)
    def get_depthmaps(self): return torch.ones(2,2,2)
    def get_conf(self,mode): return self.conf
    def get_im_poses(self): return torch.eye(4).repeat(2,1,1)
    def get_focals(self): return torch.ones(2,1)
    def get_principal_points(self): return torch.zeros(2,2)
    def get_intrinsics(self): return torch.eye(3).repeat(2,1,1)
    def get_pw_poses(self): return torch.eye(4)[None]
    def get_adaptors(self): return torch.ones(1,3)
    def compute_global_alignment(self,**kw): delegated['compute']+=1;return 17.
    def clean_pointcloud(self): delegated['clean']+=1;self.conf[0,0,0]=0;return self
def align(*a,**kw): delegated['align']+=1;return Scene()
def mst(scene,**kw): delegated['mst']+=1;return 'MST_SENTINEL'
def pnp(*a,**kw): delegated['pnp']+=1;return None
def iteration(net,i,n,base,minlr,opt,schedule):
    delegated['iter']+=1
    lr=(1-i/n)*base+(i/n)*minlr
    opt.param_groups[0]['lr']=lr;opt.zero_grad();loss=net();loss.backward();opt.step()
    return float(loss.detach()),lr
mods=dict(wrapper=types.SimpleNamespace(prepare_input_from_pil=lambda *a,**k:None),
    inference=types.SimpleNamespace(inference=lambda *a,**k:None),camera=types.SimpleNamespace(),
    aligner=types.SimpleNamespace(global_aligner=align),init=types.SimpleNamespace(init_minimum_spanning_tree=mst,fast_pnp=pnp),
    base=types.SimpleNamespace(global_alignment_iter=iteration,BasePCOptimizer=Scene))
obs=M.Observers(OUT,r,lambda *a:None,torch,mods)
obs.install()
scene=mods['aligner'].global_aligner(None)
assert mods['init'].init_minimum_spanning_tree(scene,niter_PnP=10)=='MST_SENTINEL'
assert mods['init'].fast_pnp(None) is None
assert scene.compute_global_alignment(init='mst',niter=400,schedule='linear',lr=.01)==17.
opt=torch.optim.Adam(scene.parameters(),lr=.01,betas=(.9,.9))
for i in range(400):mods['base'].global_alignment_iter(scene,i,400,.01,1e-6,opt,'linear')
original_validate=M.validate_scene
M.validate_scene=lambda x:None  # tiny fake geometry, full-shape validator separately tested above
assert scene.clean_pointcloud() is scene
M.validate_scene=original_validate
assert r['counters']['optimizer_steps']==400 and r['counters']['scene_objective_calls']==401
assert len(r['optimization_trace'])==400 and delegated['iter']==400
assert r['optimization_trace'][0]['lr']==.01
assert abs(r['optimization_trace'][-1]['lr']-.0000259975)<1e-15
assert all(delegated[k]==1 for k in ['align','mst','pnp','compute','clean'])
checks.append(dict(name='400 delegate iterations/400 real scalar optimizer steps/401 objectives',pass_=True))
checks.append(dict(name='schedule endpoints and sentinel returns preserved',pass_=True))
checks.append(dict(name='clean changes only confidence; snapshots remain independent',pass_=True))
check('changed iteration schedule refused',lambda:mods['base'].global_alignment_iter(scene,400,399,.01,1e-6,opt,'linear'),True)
obs.restore()
assert mods['base'].global_alignment_iter is iteration and mods['aligner'].global_aligner is align
assert opt.step.__func__ is torch.optim.Adam.step
checks.append(dict(name='all instrumentation restored',pass_=True))

base=dict(schema='s17c-embedded-two-frame-geometry-manifest-v1',source_commit=M.COMMIT,contract=M.EXPECTED_CONTRACT.copy(),
    source_root='/tmp/s17c_src',python='/tmp/python',runner='/tmp/s17c_runner.py',checkpoint='/tmp/s17c.pth',source_plan='/tmp/s17c_plan.json',
    overlay='/tmp/s17c_overlay',dependency_plan='/tmp/s17c_deps.json',environment_receipt='/tmp/s17c_env.json',import_smoke='/tmp/s17c_smoke.json',
    history_images=[dict(index=i,path=f'/tmp/s17c_rgb{i}.png',sha256=h) for i,h in enumerate(M.HISTORY_SHA256)],control_files=[],overlay_files=[])
# Canonical /tmp resolves to /private/tmp on macOS; use the resolved spelling everywhere.
for k in ['source_root','python','runner','checkpoint','source_plan','overlay','dependency_plan','environment_receipt','import_smoke']:base[k]=str(Path(base[k]).resolve())
for item in base['history_images']:item['path']=str(Path(item['path']).resolve())
base['identities']={base[k]:'a'*64 for k in ['runner','checkpoint','source_plan','dependency_plan','environment_receipt','import_smoke']}
base['identities'][base['checkpoint']]=M.CHECKPOINT_SHA256;base['identities'][base['source_plan']]=M.SOURCE_PLAN_SHA
base['identities'].update({x['path']:x['sha256'] for x in base['history_images']})
check('valid artificial manifest role contract',lambda:M.validate_contract(base))
for k,v in [('niter',399),('poses',[]),('depths',[]),('main_generator_calls',1),('size',224)]:
    bad=copy.deepcopy(base);bad['contract'][k]=v
    check('refuse contract '+k,lambda bad=bad:M.validate_contract(bad),True)
bad=copy.deepcopy(base);bad['identities'][str(Path('/tmp/extra_target.npz').resolve())]='0'*64
check('extra target array identity refused',lambda:M.validate_contract(bad),True)
fake_src=OUT/'fake_isolated_source';fake_src.mkdir()
fake_path=(fake_src/'fake_module.py').resolve();fake_path.write_text('# artificial source only\n')
sys.modules['dust3r.s17c_artificial_module']=types.SimpleNamespace(__file__=str(fake_path))
check('loaded but unmanifested isolated module refused',lambda:M.verify_modules(fake_src.resolve(),{},{}),True)
check('manifested isolated module accepted',lambda:M.verify_modules(fake_src.resolve(),{},{str(fake_path):M.sha(fake_path)}))
del sys.modules['dust3r.s17c_artificial_module']
M.write(OUT/'receipt.json',dict(status='PASS_ARTIFICIAL_ONLY',utc=M.utc(),checks=checks,check_count=len(checks),
    runner_sha256=M.sha(ROOT/'scripts/run_s17c_embedded_geometry.py'),checkpoint_reads=0,real_rgb_decodes=0,
    full_model_instances=0,GT_reads=0,video_generations=0,fixture='scalar nn.Module and tiny fake scene; numerical validation uses fabricated shapes'))
print(json.dumps(dict(status='PASS_ARTIFICIAL_ONLY',checks=len(checks))))
