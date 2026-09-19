"""New S35 wiring/archive checks, exclusively synthetic and externally bounded.

Prepared source, not evidence of executed tests. Never imports modeling.pipeline
or constructs the real VMem class. Original AST bodies execute only with the
explicit tiny substitutes below. This is not the old S20 codec test suite.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import shutil
import struct
import sys
import traceback
from types import MethodType, ModuleType, SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT/'work/S20_environment/isolated_vmem_source'
PIPELINE = SOURCE/'modeling/pipeline.py'
NAVIGATION = SOURCE/'navigation.py'
UTIL = SOURCE/'utils/util.py'
MISSING = object()
PIPELINE_METHODS = {'reset','initialize','geodesic_distance','get_context_info',
    'get_transformed_c2ws','get_translation_scaling_factor','get_cond',
    '_generate_frames_for_trajectory','generate_trajectory_frames'}
UTIL_FUNCTIONS = {'average_camera_pose','encode_image','encode_vae_image','do_sample','tensor_to_pil'}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def write_new(path, value):
    with Path(path).open('x') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False)
        handle.write('\n');handle.flush();os.fsync(handle.fileno())


def load_source(path):
    spec=importlib.util.spec_from_file_location('s35_check_'+Path(path).stem,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def snapshot(value):
    """Copy only explicit tiny fixture values; no hidden/model introspection."""
    if isinstance(value,torch.Tensor):
        return value.detach().cpu().numpy().copy()
    if isinstance(value,np.ndarray):
        return value.copy()
    if isinstance(value,Image.Image):
        return {'synthetic_pil':True,'mode':value.mode,'size':tuple(value.size),'pixels':np.asarray(value).copy()}
    if isinstance(value,dict):
        return {k:snapshot(v) for k,v in value.items()}
    if isinstance(value,list):
        return [snapshot(v) for v in value]
    if isinstance(value,tuple):
        return tuple(snapshot(v) for v in value)
    if isinstance(value,np.generic):
        return value.copy()
    if value is None or isinstance(value,(str,bool,int,float)):
        return value
    raise TypeError('Unexpected fixture value: '+str(type(value)))


def equal_values(left,right,path='value'):
    if isinstance(left,np.ndarray) or isinstance(right,np.ndarray):
        require(isinstance(left,np.ndarray) and isinstance(right,np.ndarray),path+': array type differs')
        require(left.dtype==right.dtype and left.shape==right.shape and left.tobytes()==right.tobytes(),path+': array bits differ')
    elif isinstance(left,dict):
        require(isinstance(right,dict) and list(left)==list(right),path+': ordered keys differ')
        for key in left:equal_values(left[key],right[key],path+'.'+str(key))
    elif isinstance(left,(list,tuple)):
        require(type(left)==type(right) and len(left)==len(right),path+': sequence differs')
        for i,(a,b) in enumerate(zip(left,right)):equal_values(a,b,path+'['+str(i)+']')
    elif isinstance(left,float):
        require(isinstance(right,float) and struct.pack('<d',left)==struct.pack('<d',right),path+': float bits differ')
    else:
        require(type(left)==type(right) and left==right,path+': scalar differs')


def rng_state():
    return snapshot({'python':random.getstate(),'numpy_legacy':np.random.get_state(),'torch_cpu':torch.get_rng_state()})


def grad_modes():
    return {'grad_enabled':bool(torch.is_grad_enabled()),
            'inference_mode_enabled':bool(torch.is_inference_mode_enabled())}


def cache_values(p):
    return snapshot({name:getattr(p,name) for name in
        ('pil_frames','latents','encoder_embeddings','c2ws','Ks','surfel_depths','surfel_Ks')})


def map_values(p):
    return snapshot({'surfels':[{'position':s.position,'normal':s.normal,'radius':s.radius,
        'color':s.color,'source_ids':list(p.surfel_to_timestep[i])} for i,s in enumerate(p.surfels)],
        'surfel_to_timestep':p.surfel_to_timestep,'surfel_depths':p.surfel_depths,'surfel_Ks':p.surfel_Ks})


class InjectedSecondBatchError(RuntimeError):
    pass


class TinyFixture:
    def __init__(self, fail_second=False):
        self.counts=Counter()
        self.fail_second=fail_second
        self.failure=InjectedSecondBatchError('S35_EXPLICIT_SYNTHETIC_SECOND_SAMPLER_FAILURE')
        self.sampler_inputs=[]
        self.sampler_outputs=[]
        self.clip_outputs=[]
        self.decoded=[]
        self.geometry=[]
        self.commits=[]
        self.selected_ids=[]


class TinyModel:
    def __init__(self,fixture):self.fixture=fixture
    def forward(self,x,sigma,c,**kwargs):
        self.fixture.counts['main_model_forward']+=1
        require(kwargs.get('num_frames')==8,'Original do_sample T changed')
        return x*.25+c['replace'][:,:4]*.01+c['crossattn'].mean()*.001


class TinyAE:
    def __init__(self,fixture):self.fixture=fixture
    def encode(self,image,t):
        self.fixture.counts['vae_encode']+=1
        require(t==1,'Original encode alias argument differs')
        return image.mean(dim=(1,2,3),keepdim=True).repeat(1,4,72,72)
    def decode(self,z,t):
        self.fixture.counts['vae_decode']+=1
        require(torch.is_inference_mode_enabled(),'Original CPU do_sample inference scope disappeared')
        require(t==1 and tuple(z.shape)==(8,4,72,72),'Original all-eight latent shape differs')
        value=torch.sigmoid(z[:,:3,:4,:4])
        self.fixture.decoded.append(snapshot(value))
        return value


class TinyCLIP:
    def __init__(self,fixture):self.fixture=fixture
    def __call__(self,image):return self.forward(image)
    def forward(self,image):
        self.fixture.counts['clip_forward']+=1
        value=image.mean(dim=(2,3))
        self.fixture.clip_outputs.append(snapshot(value))
        return value


class TinySampler:
    """Exactly TWO artificial steps, explicitly not the original 50-step model."""
    def __init__(self,fixture):self.fixture=fixture
    def sampler_step(self,denoiser,value,cond):
        self.fixture.counts['synthetic_sampler_step']+=1
        return denoiser(value,torch.tensor(1.,dtype=torch.float32),cond)
    def __call__(self,denoiser,noise,**kwargs):
        f=self.fixture
        f.counts['sampler_call']+=1
        require(tuple(noise.shape)==(8,4,72,72),'Original hardcoded H576/W576/F8/T8 noise layout changed')
        f.sampler_inputs.append(snapshot({'noise':noise,'inputs':{k:kwargs[k] for k in
            ('scale','cond','uc','c2w','K','input_frame_mask')},'rng':rng_state()}))
        noise.mul_(1.25)  # Deliberately exposes pre-mutation archival correctness.
        delta=random.random()+float(np.random.random())
        value=noise+torch.randn_like(noise)*.001+delta*.001
        if f.fail_second and f.counts['sampler_call']==2:
            raise f.failure
        for _ in range(2):
            value=self.sampler_step(denoiser,value,kwargs['cond'])
        f.sampler_outputs.append(snapshot({'output':value,'rng':rng_state()}))
        return value


def tiny_denoiser(model,value,sigma,c,**kwargs):
    return model.forward(value,sigma,c,**kwargs)


def tiny_pluckers(*,extrinsics_src,extrinsics,intrinsics,target_size):
    """Explicit zero-ray fixture; no claim to original camera-ray numerics."""
    return torch.zeros((len(extrinsics),6,*target_size),dtype=torch.float32)


def tiny_geometry(input_images,fixture,**kwargs):
    fixture.counts['synthetic_geometry']+=1
    n=len(input_images)
    require(n in (5,9) and kwargs['niter']==400 and kwargs['lr']==.01,'Original scene-call controls changed')
    require((kwargs['depths'] is None) == (n==5),'Old depth feed-through differs')
    depth=torch.arange(1,n+1,dtype=torch.float32)[:,None,None].expand(n,4,4).clone()
    points=torch.zeros((n,4,4,3),dtype=torch.float32);points[...,2]=depth
    conf=torch.ones((n,4,4),dtype=torch.float32)*2
    result={'point_clouds':[points[i:i+1] for i in range(n)],
        'confidences':[conf[i:i+1] for i in range(n)],'depths':[depth[i:i+1] for i in range(n)],
        'camera_info':{'focal':np.arange(320,320+n,dtype=np.float32)[:,None]}}
    fixture.geometry.append(snapshot(result))
    return result


def fixture_construct_scene(self,input_images,time_indices,niter=1000,lr=.01,device=None):
    """Synthetic scene/map only; no CUT3R, GA, clean, merge or actual renderer."""
    f=self._fixture
    require(not torch.is_inference_mode_enabled(),'Observation incorrectly imposed global inference_mode')
    f.counts['synthetic_construct_scene']+=1
    ids=time_indices.detach().cpu().tolist() if isinstance(time_indices,torch.Tensor) else list(time_indices)
    f.selected_ids.append(ids)
    scene=self._fixture_module.run_inference_from_pil(input_images,f,
        poses=self.get_transformed_c2ws(),depths=torch.from_numpy(np.array(self.surfel_depths)) if self.surfel_depths else None,
        niter=niter,lr=lr,device=device,visualize=False)
    n=len(input_images)
    self.surfel_Ks.extend([x.copy() for x in scene['camera_info']['focal']])
    self.surfel_depths=[x[0].numpy().copy() for x in scene['depths']]
    for i in range(len(self.surfels),n):
        self.surfels.append(SimpleNamespace(position=np.array([i,.25,1.],dtype=np.float32),
            normal=np.array([0,0,1.],dtype=np.float32),radius=.05,
            color=None if i%2==0 else np.array([i,2,3],dtype=np.uint8)))
        self.surfel_to_timestep[i]=[i]
    f.commits.append({'map':map_values(self),'cache':cache_values(self)})


def fixture_render(self,surfels,c2w,K,**kwargs):
    self._fixture.counts['synthetic_render']+=1
    return {'depth':np.ones((2,3),dtype=np.float32),
        'index':np.array([[0,1,2],[3,4,-1]],dtype=np.int64),
        'cosine':np.ones((2,3),dtype=np.float32)}


def fixture_retrieval(self,result):
    self._fixture.counts['synthetic_retrieval']+=1
    return [(i,1.) for i in range(5)],[(i,1) for i in range(5)]


def ast_module(path,name,globals_map,nodes):
    module=ModuleType(name);module.__file__=str(path)
    module.__dict__.update(globals_map)
    future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
    tree=ast.Module(body=[future]+deepcopy(nodes),type_ignores=[])
    ast.fix_missing_locations(tree)
    exec(compile(tree,str(path),'exec'),module.__dict__)
    sys.modules[name]=module
    return module


def prepare_runtime(label,fail_second):
    # Only selected original AST definitions execute. Top-level model imports and
    # VMemPipeline.__init__ are neither executed nor copied into this class.
    tree=ast.parse(UTIL.read_text())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in UTIL_FUNCTIONS]
    require({n.name for n in nodes}==UTIL_FUNCTIONS,'Original utility AST domain changed')
    util=ast_module(UTIL,'s35_fixture_util_'+label,dict(np=np,torch=torch,Image=Image,math=math),nodes)
    p_tree=ast.parse(PIPELINE.read_text())
    original=next(n for n in p_tree.body if isinstance(n,ast.ClassDef) and n.name=='VMemPipeline')
    cls=deepcopy(original)
    cls.body=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in PIPELINE_METHODS]
    require({n.name for n in cls.body}==PIPELINE_METHODS,'Original pipeline AST domain changed')
    symbols=dict(np=np,torch=torch,deepcopy=deepcopy,repeat=repeat,get_plucker_coordinates=tiny_pluckers,
        run_inference_from_pil=tiny_geometry)
    symbols.update({n:getattr(util,n) for n in UTIL_FUNCTIONS})
    module=ast_module(PIPELINE,'s35_fixture_pipeline_'+label,symbols,[cls])
    p=object.__new__(module.VMemPipeline)
    f=TinyFixture(fail_second)
    p._fixture=f;p._fixture_module=module
    p.config=SimpleNamespace(model=SimpleNamespace(num_frames=8,context_num_frames=4,target_num_frames=4,
        cfg=2.,translation_distance_weight=1),surfel=SimpleNamespace(niter=400,lr=.01,width=512,height=288),
        inference=SimpleNamespace(visualize=False,visualize_pointcloud=False))
    p.device='cpu';p.dtype=torch.float32;p.camera_scale=1.;p.use_non_maximum_suppression=True
    p.pil_frames=[];p.latents=[];p.encoder_embeddings=[];p.c2ws=[];p.Ks=[]
    p.surfels=[];p.surfel_to_timestep={};p.surfel_depths=[];p.surfel_Ks=[]
    p.vae=TinyAE(f);p.image_encoder=TinyCLIP(f);p.model_wrapper=TinyModel(f)
    p.sampler=[TinySampler(f)];p.denoiser=tiny_denoiser
    p.construct_and_store_scene=MethodType(fixture_construct_scene,p)
    p.render_surfels_to_image=MethodType(fixture_render,p)
    p.process_retrieved_spatial_information=MethodType(fixture_retrieval,p)
    nav_tree=ast.parse(NAVIGATION.read_text())
    nav_nodes=[n for n in nav_tree.body if isinstance(n,ast.ClassDef) and n.name=='Navigator']
    require(len(nav_nodes)==1,'Original Navigator class changed')
    nav_module=ast_module(NAVIGATION,'s35_fixture_navigation_'+label,
        dict(np=np,torch=torch,Image=Image,os=os,shutil=shutil,json=json,spt=spt),nav_nodes)
    navigator=nav_module.Navigator(p,step_size=.1,num_interpolation_frames=4)
    image=torch.linspace(-.5,.5,3*576*576,dtype=torch.float32).reshape(1,3,576,576)
    return dict(pipeline=p,navigator=navigator,pipeline_module=module,image=image,
        initial_pose=np.eye(4),initial_K=np.array([[500,0,288],[0,500,288],[0,0,1]],dtype=np.float64))


def original_bindings(runtime):
    p=runtime['pipeline'];module=runtime['pipeline_module']
    objects=[(module,n) for n in ['_S35_GENERATION_OBSERVER','encode_image','encode_vae_image','run_inference_from_pil']]
    objects += [(p,n) for n in PIPELINE_METHODS|{'construct_and_store_scene','render_surfels_to_image','process_retrieved_spatial_information'}]
    objects += [(p.model_wrapper,'forward'),(p.vae,'encode'),(p.vae,'decode'),
                (p.image_encoder,'forward'),(p.sampler[0],'sampler_step')]
    return [(o,n,o.__dict__.get(n,MISSING)) for o,n in objects]


def bindings_restored(bindings):
    for obj,name,original in bindings:
        require(obj.__dict__.get(name,MISSING) is original,'Hook not restored: '+name)


@contextmanager
def fresh_cwd(path):
    path.mkdir(exist_ok=False)
    old=Path.cwd();os.chdir(path)
    try:yield
    finally:os.chdir(old)


def run_case(output,label,fail_second,observed,modules,identities,contract_sha):
    directory=output/label;directory.mkdir(exist_ok=False)
    random.seed(42);np.random.seed(42);torch.manual_seed(42)
    runtime=prepare_runtime(label,fail_second)
    bindings=original_bindings(runtime)
    before=rng_state();modes_before=grad_modes();returns=[];trace=archive=None;error=None;summary=None
    with fresh_cwd(directory/'cwd'):
        if observed:
            def validate(gate):
                require(gate=={'evidence_kind':'synthetic_test'},'Artificial gate mismatch')
                return gate
            def create_trace(gate):
                nonlocal trace
                trace=modules['trace'].TraceWriter(directory/'trace',evidence_kind='synthetic_test',
                    source_identities=identities,manifest_sha256=contract_sha)
                return trace
            def create_archive(gate):
                nonlocal archive
                archive=modules['archive'].FullOutputArchive(directory/'archive',evidence_kind='synthetic_test',
                    source_identities=identities,manifest_sha256=contract_sha,
                    required_events={'initial_output':1,'sample_output':2,'cache_commit':2,'map_commit':2})
                return archive
            try:
                result=modules['integration'].run_original(lambda gate:runtime,
                    resource_gate={'evidence_kind':'synthetic_test'},check_resource_gate=validate,
                    create_trace=create_trace,create_archive=create_archive,
                    source_manifest={'identities':identities,'pipeline_source':str(PIPELINE)},evidence_kind='synthetic_test')
                require(result['runtime'] is runtime and result['archive'] is archive,'Original runtime/archive replaced')
                returns=[result['initial_return'],result['left_return'],result['right_return']]
                summary=result['observation_summary']
                archive.finalize(status='COMPLETE',metadata={'purpose':'S35_NEW_SYNTHETIC_WIRING_CHECK'})
            except InjectedSecondBatchError as exc:error=exc
        else:
            nav=runtime['navigator']
            try:
                with torch.no_grad():
                    returns.append(nav.initialize(runtime['image'],runtime['initial_pose'],runtime['initial_K']))
                    returns.append(nav.turn_left(5))
                    returns.append(nav.turn_right(5))
            except InjectedSecondBatchError as exc:error=exc
    after=rng_state();modes_after=grad_modes();bindings_restored(bindings)
    equal_values(modes_before,modes_after,'Route exit gradient/inference modes restored')
    f=runtime['pipeline']._fixture
    require((error is f.failure)==fail_second,'Injected original exception identity not preserved')
    if not fail_second:
        require(returns[0] is runtime['pipeline'].pil_frames[0],'Initial returned PIL identity changed')
        # Original first return aliases the history list: five at return time,
        # nine after the second append. Preserve this, rather than "fix" it.
        require(returns[1] is runtime['pipeline'].pil_frames and len(returns[1])==9,'Original first-return live-list alias changed')
        require(len(returns[2])==4 and all(a is b for a,b in zip(returns[2],runtime['pipeline'].pil_frames[-4:])),
                'Original second-return PIL object identities changed')
    state={'cache':cache_values(runtime['pipeline']),'map':map_values(runtime['pipeline']),
        'pose_history':snapshot(runtime['navigator'].pose_history),'navigator_frames':snapshot(runtime['navigator'].frames),
        'current_pose':snapshot(runtime['navigator'].current_pose),'current_K':snapshot(runtime['navigator'].current_K),
        'global_step':runtime['pipeline'].global_step,'selected_context_ids':f.selected_ids,
        'initial_threshold':snapshot(getattr(runtime['pipeline'],'initial_threshold',None)),
        'counts':dict(f.counts),'rng_before':before,'rng_after':after,
        'modes_before':modes_before,'modes_after':modes_after}
    if not fail_second:state['returns']=snapshot(returns)
    return {'directory':directory,'runtime':runtime,'fixture':f,'state':state,
        'trace':trace,'archive':archive,'summary':summary,'error':error,'restored':True}


def read_archive(directory):
    """Read back only this run's artificial archive; full file/hash checks."""
    manifest=json.loads((directory/'manifest.json').read_text())
    require(manifest['evidence_kind']=='synthetic_test' and manifest['scientific_status']=='NOT_EVALUATED','Synthetic archive label lost')
    for name,item in manifest['files'].items():
        path=directory/name
        require(path.resolve().is_relative_to(directory.resolve()),'Unexpected archival path')
        require(path.stat().st_size==item['bytes'] and sha(path)==item['sha256'],'New archive payload differs: '+name)
    def decode(node):
        kind=node['kind']
        if kind=='tensor':
            raw=(directory/node['blob']).read_bytes()
            base={k:v for k,v in node.items() if k not in ('sha256','blob')}
            require(len(raw)==node['nbytes'] and hashlib.sha256(raw).hexdigest()==node['bytes_sha256'],'Raw tensor mismatch')
            require(hashlib.sha256(canonical(base)+b'\0'+raw).hexdigest()==node['sha256'],'Tensor identity mismatch')
            return np.frombuffer(raw,dtype=np.dtype(node['dtype']).newbyteorder('<')).reshape(node['shape']).copy()
        if kind=='pil_image':
            pixels=decode(node['pixels'])
            with Image.open(directory/node['png']['path']) as image:
                image.load()
                require(image.mode==node['mode'] and list(image.size)==node['size'],'Archived synthetic PIL metadata differs')
                equal_values(pixels,np.asarray(image),'PIL pixels/PNG')
            return {'synthetic_pil':True,'mode':node['mode'],'size':tuple(node['size']),'pixels':pixels}
        if kind=='dict':return {decode(item['key']):decode(item['value']) for item in node['items']}
        if kind in ('list','tuple'):
            values=[decode(item) for item in node['items']]
            return tuple(values) if kind=='tuple' else values
        if kind=='scalar':return node['value']
        if kind=='python_float64':return struct.unpack('<d',bytes.fromhex(node['little_endian_hex']))[0]
        if kind=='torch_metadata':return node['value']
        if kind=='bytes':return (directory/node['blob']['path']).read_bytes()
        raise AssertionError('Unexpected archive kind '+kind)
    events=[];previous='0'*64
    for seq,line in enumerate((directory/'events.jsonl').read_text().splitlines()):
        row=json.loads(line);digest=row.pop('sha256')
        require(row['seq']==seq and row['previous_sha256']==previous and hashlib.sha256(canonical(row)).hexdigest()==digest,'Archive event chain differs')
        previous=digest
        if row['event']=='capture_complete':events.append((row['payload']['name'],decode(row['payload']['tree'])))
    require(previous==manifest['last_event_sha256'],'Archive tail differs')
    return manifest,events


def check_archived_case(case,complete):
    manifest,events=read_archive(case['directory']/'archive')
    groups={name:[v for n,v in events if n==name] for name,_ in events}
    f=case['fixture'];n=2 if complete else 1
    require(manifest['status']==('ARCHIVE_COMPLETE' if complete else 'ARCHIVE_PARTIAL'),'Wrong partial archive status')
    equal_values(groups['initial_output'][0]['cache']['pil_frames'][0],case['state']['cache']['pil_frames'][0],'Initial canonical PIL')
    require(len(groups['initial_output'][0]['cache']['pil_frames'])==1,'Initial history not archived')
    for j in range(n):
        sample=groups['sample_output'][j]
        equal_values(sample['samples'],f.decoded[j],'All eight samples')
        equal_values(sample['samples_z'],f.sampler_outputs[j]['output'],'All eight samples_z')
        require(sample['samples'].shape[0]==8 and sample['samples_z'].shape[0]==8,'Padding outputs truncated')
        cc=groups['cache_commit'][j]
        equal_values(cc['target_encoder_embeddings'],f.clip_outputs[j+1],'Full target CLIP rows')
        require(cc['target_encoder_embeddings'].shape[0]==(7 if j==0 else 4),'Wrong seven/four target rows')
        equal_values(groups['map_commit'][j]['map'],f.commits[j]['map'],'All original supplied map fields')
        equal_values(groups['map_commit'][j]['cache'],f.commits[j]['cache'],'All original supplied cache fields')
        require(len(groups['map_commit'][j]['cache']['pil_frames'])==(5 if j==0 else 9),'Five/nine canonical history missing')
        require(len(groups['map_commit'][j]['map']['surfel_Ks'])==(5 if j==0 else 14),'Original-shaped K history was normalized away')
        require(len(groups['map_commit'][j]['map']['surfel_depths'])==(5 if j==0 else 9),'Five/nine depth cache missing')
        equal_values(groups['geometry_output'][j]['scene'],f.geometry[j],'Complete synthetic dense scene return')
        pre=groups['condition_input'][j]['args'][1]
        post=groups['condition_output'][j]['result']['all_c2ws']
        expected=pre.copy();expected[:,:,[1,2]]*=-1
        equal_values(post,expected,'Original zero-translation get_cond camera flip')
        require(pre.tobytes()!=post.tobytes(),'Synchronous get_cond pre/post state was lost')
    for j,expected in enumerate(f.sampler_inputs):
        actual={k:groups['sampler_input'][j][k] for k in ('noise','inputs','rng')}
        equal_values(actual,expected,'Actual sampler arguments and pre-mutation RNG/noise')
    for j,expected in enumerate(f.sampler_outputs):
        actual={k:groups['sampler_output'][j][k] for k in ('output','rng')}
        equal_values(actual,expected,'Actual sampler output/RNG')
    require(len(groups['sample_output'])==n and len(groups['cache_commit'])==n and len(groups['map_commit'])==n,'Unexecuted stage was fabricated')
    require(len(groups['navigator_return'])==(3 if complete else 2),'Unexecuted navigator return was fabricated/lost')
    require(len(groups['navigator_return'][1]['return'])==5,'Synchronous first-return five-frame snapshot lost')
    equal_values(groups['navigator_return'][1]['return'],f.commits[0]['cache']['pil_frames'],
                 'First navigator returned snapshot before second append')
    require(len(groups['nms_selection'])==1 and len(groups['nms_threshold'])==1,'Default original len5 NMS branch was not observed')
    threshold=groups['nms_threshold'][0]
    distances=threshold['pairwise_distances']
    require(len(distances)==10 and threshold['percentile_idx']==5,
            'Original five-camera ten-pair threshold metadata differs')
    require(all(distances[i]<=distances[i+1] for i in range(9)) and
            threshold['initial_threshold']==distances[5],
            'Stored original threshold is not zero-based sorted item five')
    equal_values(threshold['initial_threshold'],case['state']['initial_threshold'],
                 'Archived/persistent original NMS threshold')
    selected=groups['nms_selection'][0]['selected_indices']
    actual_second_ids=groups['context_output'][1]['context_info']['context_time_indices'].tolist()
    equal_values(selected,actual_second_ids,'NMS selection/actual original second context return IDs')
    if complete:
        equal_values(selected,f.selected_ids[1],'NMS selection/actual second scene input IDs')
    return {'archive_status':manifest['status'],'archive_manifest_sha256':sha(case['directory']/'archive/manifest.json'),
        'complete_sample_batches':n,'retained_history':len(case['state']['cache']['pil_frames']),
        'full_payload_file_count':len(manifest['files']),'all_eight_slots_and_seven_four_rows_checked':True,
        'nms_saved_values_check':{'pair_count':len(distances),'zero_based_percentile_idx':threshold['percentile_idx'],
            'initial_threshold':threshold['initial_threshold'],'selected_second_context_ids':actual_second_ids,
            'scope':'Existing stored distances/threshold/IDs only; no geodesic recomputation'},
        'source':'All supplied artificial arrays/PIL read back and compared; no real generation or rendering quality'}


def check_pre_factory_rejection(integration):
    calls=Counter();marker=RuntimeError('S35_SYNTHETIC_RESOURCE_REJECTION')
    def reject(gate):calls['gate']+=1;raise marker
    def factory(gate):calls['factory']+=1;raise AssertionError('Factory must not be called')
    caught=None
    try:
        integration.run_original(factory,resource_gate={'evidence_kind':'synthetic_test'},check_resource_gate=reject,
            create_trace=factory,create_archive=factory,source_manifest={},evidence_kind='synthetic_test')
    except RuntimeError as exc:caught=exc
    require(caught is marker and calls=={'gate':1},'Resource callback did not reject before all three factories')
    return {'original_exception_identity_preserved':True,'gate_calls':calls['gate'],'all_three_factory_calls':0,
            'model_constructors':0,'scope':'Synthetic callback only, not the actual missing-resource launcher test'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract',required=True)
    parser.add_argument('--contract-sha256',required=True)
    args=parser.parse_args()
    require(sha(args.contract)==args.contract_sha256,'Frozen artificial contract SHA differs')
    contract=json.loads(Path(args.contract).read_text())
    require(contract['schema']=='s35-artificial-wiring-contract-v1' and contract['status']=='FROZEN_SYNTHETIC_TEST'
            and contract['evidence_kind']=='synthetic_test','Explicit synthetic contract required')
    paths=[PIPELINE,NAVIGATION,UTIL,Path(__file__).resolve(),HERE/'integrate_original.py',
           HERE/'archive_outputs.py',ROOT/'src/s20_generation_trace.py']
    identities={str(p):sha(p) for p in paths}
    require(contract['source_identities']==identities,'Artificial source domain differs')
    require(contract['limits']=={'cpu_threads':1,'seconds':120,'rss_bytes':2*1024**3},'External artificial budget differs')
    output=Path(contract['output_root']);require(output.is_absolute(),'Absolute fresh artificial output root required')
    output.mkdir(parents=True,exist_ok=False)
    record={'schema':'s35-artificial-wiring-results-v1','status':'RUNNING_SYNTHETIC_ONLY','started_utc':utc(),
        'evidence_kind':'synthetic_test','contract_sha256':args.contract_sha256,'source_identities':identities,
        'real_images_gt_weights_npz_read':0,'real_model_constructors':0,'real_ga_or_renderer_calls':0,
        'scientific_status':'NOT_EVALUATED','external_budget_enforced_here':False}
    try:
        global np,torch,Image,spt,repeat
        import numpy as np
        import torch
        from PIL import Image
        import scipy.spatial.transform as spt
        from einops import repeat
        require('modeling.pipeline' not in sys.modules and 'navigation' not in sys.modules,'Real pipeline/navigation module unexpectedly imported')
        torch.set_num_threads(1)
        modules={'trace':load_source(ROOT/'src/s20_generation_trace.py'),
            'archive':load_source(HERE/'archive_outputs.py'),'integration':load_source(HERE/'integrate_original.py')}
        record['resource_rejection']=check_pre_factory_rejection(modules['integration'])
        plain=run_case(output,'plain_success',False,False,modules,identities,args.contract_sha256)
        observed=run_case(output,'observed_success',False,True,modules,identities,args.contract_sha256)
        equal_values(plain['state'],observed['state'],'Plain/observed full returned pixels/cache/poses/counts/RNG')
        require([len(x) for x in observed['fixture'].selected_ids]==[1,4],'Original context1/context4 shape changed')
        require(any(i>0 for i in observed['fixture'].selected_ids[1]),'Second artificial batch did not consume artificial generated ID')
        require([len(x) for x in observed['fixture'].clip_outputs]==[1,7,4],'Complete CLIP target inputs changed')
        record['success_archive']=check_archived_case(observed,True)
        record['success_trace']=modules['trace'].verify_trace(observed['directory']/'trace')
        require(record['success_trace']['status']=='VALID_CLOSED_TRACE' and
            [v['state'] for v in record['success_trace']['batches'].values()]==['batch_complete','batch_complete'],
            'Success synthetic trace was not completely closed')
        require(observed['fixture'].counts==Counter(vae_encode=1,vae_decode=2,clip_forward=3,
            sampler_call=2,synthetic_sampler_step=4,main_model_forward=4,synthetic_geometry=2,
            synthetic_construct_scene=2,synthetic_render=1,synthetic_retrieval=1),'Actual synthetic success call counts differ')
        record['success_counts']=dict(observed['fixture'].counts)
        record['success_grad_modes']={label:{key:case['state'][key] for key in ('modes_before','modes_after')}
            for label,case in (('plain',plain),('observed',observed))}
        record['observed_counter_summary']=observed['summary']
        for observed_key,fixture_key in {'main_model_forward':'main_model_forward','vae_encode':'vae_encode',
            'vae_decode':'vae_decode','clip_forward':'clip_forward','euler_step':'synthetic_sampler_step',
            'sampler_call':'sampler_call','geometry':'synthetic_geometry','construct_scene':'synthetic_construct_scene',
            'render':'synthetic_render','retrieval':'synthetic_retrieval'}.items():
            require(observed['summary']['counts'][observed_key]==observed['fixture'].counts[fixture_key],
                    'Observer counter does not equal actual fixture calls: '+observed_key)
        plain_failure=run_case(output,'plain_second_batch_failure',True,False,modules,identities,args.contract_sha256)
        observed_failure=run_case(output,'observed_second_batch_failure',True,True,modules,identities,args.contract_sha256)
        equal_values(plain_failure['state'],observed_failure['state'],'Plain/observed failure prefix/cache/poses/counts/RNG')
        require(observed_failure['trace'].closed and observed_failure['archive'].closed,'Both failure prefixes were not closed')
        record['failure_archive']=check_archived_case(observed_failure,False)
        failure_events=[json.loads(line) for line in (observed_failure['directory']/'trace/events.jsonl').read_text().splitlines()]
        require(sum(x['event']=='batch_complete' for x in failure_events)==1 and
                sum(x['event']=='failure' for x in failure_events)==1,'Failure trace fabricated/lost batch completion')
        record['failure_trace']=modules['trace'].verify_trace(observed_failure['directory']/'trace')
        require(record['failure_trace']['status']=='VALID_CLOSED_TRACE' and
            [v['state'] for v in record['failure_trace']['batches'].values()]==['batch_complete','failure'],
            'Closed failure trace was misclassified as two completed batches')
        require(observed_failure['fixture'].counts==Counter(vae_encode=1,vae_decode=1,clip_forward=2,
            sampler_call=2,synthetic_sampler_step=2,main_model_forward=2,synthetic_geometry=1,
            synthetic_construct_scene=1,synthetic_render=1,synthetic_retrieval=1),'Actual synthetic failure call counts differ')
        record['failure_counts']=dict(observed_failure['fixture'].counts)
        record['failure_grad_modes']={label:{key:case['state'][key] for key in ('modes_before','modes_after')}
            for label,case in (('plain',plain_failure),('observed',observed_failure))}
        record['hook_restoration_all_cases']=all(c['restored'] for c in (plain,observed,plain_failure,observed_failure))
        require('modeling.pipeline' not in sys.modules and 'navigation' not in sys.modules,'Real pipeline/navigation import occurred')
        record.update(status='PASS_NEW_SYNTHETIC_WIRING_ARCHIVE_CHECKS_ONLY',
            retained_original_ast_methods=sorted(PIPELINE_METHODS),retained_original_util_functions=sorted(UTIL_FUNCTIONS),
            navigator_ast='Full original class copied; only construction/initialize/interpolation/left/right turn route exercised',
            comparison='Exact returned PIL pixels, cache/map, actual source-selected IDs, fixture calls, Python/NumPy/Torch RNG; original exception identity and hooks restored',
            limitations=['Tiny two-step sampler/AE/CLIP/geometry/ray/render/retrieval substitutes; no original 50-step or 400-GA test',
                'Only original AST route/get_cond/NMS/navigation/do_sample and observation mechanics are exercised',
                'Synthetic callback rejection is not real resource readiness',
                'Valid failed trace or partial archive is not generation success'])
    except BaseException as exc:
        record.update(status='FAILED_SYNTHETIC_WIRING_CHECKS',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
    finally:
        record['completed_utc']=utc()
        record['sources_unchanged']=all(sha(p)==h for p,h in identities.items())
        if not record['sources_unchanged']:record['status']='FAILED_SOURCE_CHANGED'
        write_new(output/'receipt.json',record)
    return 0 if record['status']=='PASS_NEW_SYNTHETIC_WIRING_ARCHIVE_CHECKS_ONLY' else 1


if __name__=='__main__':
    raise SystemExit(main())
