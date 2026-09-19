#!/usr/bin/env python3
"""S17C: original embedded VMem CUT3R + unconstrained geometry alignment, two RGB only."""
from __future__ import annotations
import argparse
from collections import defaultdict
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import platform
import random
import resource
import shutil
import sys
import time
import traceback
from typing import Any

FIELDS = ['state_feat', 'state_pos', 'init_state_feat', 'mem', 'init_mem']
STATE_SCHEMA = {'state_feat': ([1, 768, 768], 'float32'),
                'state_pos': ([1, 768, 2], 'int64'),
                'init_state_feat': ([1, 768, 768], 'float32'),
                'mem': ([1, 256, 1536], 'float32'), 'init_mem': ([1, 256, 1536], 'float32')}
OUTPUT_SHAPES = {'pts3d_in_self_view': [1, 384, 512, 3],
                 'pts3d_in_other_view': [1, 384, 512, 3],
                 'conf_self': [1, 384, 512], 'conf': [1, 384, 512],
                 'camera_pose': [1, 7], 'rgb': [1, 384, 512, 3]}
FLAGS = {'img_mask': True, 'ray_mask': False, 'update': True, 'reset': False}
COMMIT = '39291e4f272f6b4f270691d930926ab5930f942e'
CHECKPOINT_SHA256 = '45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103'
CHECKPOINT_BYTES = 3173761006
HISTORY_SHA256 = [
    '7caa6f1b9fd1ac5b6938812682c55e3d7926a1348c7554c23e1012b47759cc39',
    '77bebdb3ac737221ef05a4404a1124676bcff536dbffdbb6e197b59bcdf811ae',
]
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def tensor_id(a):
    import numpy as np
    a = np.ascontiguousarray(a)
    return dict(shape=list(a.shape), dtype=str(a.dtype), sha256=hashlib.sha256(a.tobytes()).hexdigest())


def validate_array(a, shape, dtype, label):
    import numpy as np
    require(list(a.shape) == shape and str(a.dtype) == dtype, 'Array schema: ' + label)
    require(np.isfinite(a).all(), 'Array finite gate: ' + label)


SOURCE_PLAN_SHA = 'e90ee3c071912ac594d6b41ed88be23321baae3bac60a221522d67cee4eb482d'
LABEL = 'VMem嵌入CUT3R无先验建图与全局对齐组件'
EXPECTED_CONTRACT = dict(history_count=2, query_count=0, device='cpu', cpu_threads=8,
    seed=0, size=512, processed_size=[384, 512], raw_image_size=[640, 480],
    dtype='float32', niter=400, lr=0.01, poses=None, depths=None,
    visualize=False, save_flag=False, wall_seconds=600, monitored_rss_bytes=34359738368,
    external_monitor_required=True, main_generator_calls=0, sensor_depth_reads=0,
    video_generated=False, postfinal_objective_evaluations=1)


def validate_contract(m):
    require(m['schema'] == 's17c-embedded-two-frame-geometry-manifest-v1', 'Manifest schema')
    require(m['source_commit'] == COMMIT, 'Fixed original VMem commit')
    for k, v in EXPECTED_CONTRACT.items():
        require(m['contract'].get(k, 'MISSING') == v, 'Contract: ' + k)
    ids = m['identities']
    for p, h in ids.items():
        require(Path(p).is_absolute() and p == str(Path(p).resolve()), 'Canonical identity ' + p)
        require(len(h) == 64 and all(c in '0123456789abcdef' for c in h), 'SHA ' + p)
    for k in ['source_root', 'python', 'runner', 'checkpoint', 'source_plan', 'overlay', 'dependency_plan', 'environment_receipt', 'import_smoke']:
        require(Path(m[k]).is_absolute(), 'Absolute role ' + k)
        if k not in ['source_root', 'python', 'overlay']:
            require(m[k] in ids, 'Frozen role ' + k)
    require(ids[m['checkpoint']] == CHECKPOINT_SHA256, '512 DPT checkpoint identity')
    require(ids[m['source_plan']] == SOURCE_PLAN_SHA, 'Three-patch frozen source plan')
    hist = m['history_images']
    require(len(hist) == 2 and [r['index'] for r in hist] == [0, 1], 'Only ordered original 0/1')
    require([r['sha256'] for r in hist] == HISTORY_SHA256, 'Exact Bonn bytes')
    paths = [r['path'] for r in hist]
    require(len(set(paths)) == 2, 'Two distinct photos')
    for r in hist:
        require(ids.get(r['path']) == r['sha256'] and Path(r['path']).suffix == '.png', 'RGB identity')
    src = Path(m['source_root']).resolve()
    upstream = {p for p in ids if Path(p).is_relative_to(src)}
    overlay = Path(m['overlay']).resolve()
    deps = set(m['overlay_files'])
    require(all(Path(p).is_relative_to(overlay) and p in ids for p in deps), 'Frozen overlay files')
    controls = set(m['control_files'])
    require(len(controls) == len(m['control_files']), 'Unique controls')
    require(all(p in ids and Path(p).suffix in {'.md', '.json', '.py', '.txt'} for p in controls), 'Control allowlist')
    allowed = upstream | deps | controls | set(paths) | {m[k] for k in ['runner', 'checkpoint', 'source_plan', 'dependency_plan', 'environment_receipt', 'import_smoke']}
    require(set(ids) == allowed, 'Unexpected data or unfrozen identity')
    require(all(Path(p).name not in {'groundtruth.txt', 'rgb.txt', 'depth.txt'} for p in ids), 'Dataset metadata forbidden')
    return paths


def array(value):
    import numpy as np
    if hasattr(value, 'detach'):
        value = value.detach().cpu().numpy()
    return np.array(value, copy=True)


def validate_import_smoke(smoke):
    require(smoke['status']=='PASS_IMPORT_ONLY_NO_MODEL', 'Completed import-only smoke; no model claim')


def save_npz(out, name, values, report):
    import numpy as np
    arrays = {k: array(v) for k, v in values.items()}
    np.savez_compressed(out / name, **arrays)
    report.setdefault('array_files', {})[name] = {k: tensor_id(v) for k, v in arrays.items()}
    return arrays


def capture_scene(scene):
    import numpy as np
    return dict(world_points=np.stack([array(x) for x in scene.get_pts3d()]),
        depths=np.stack([array(x) for x in scene.get_depthmaps()]),
        confidence=np.stack([array(x) for x in scene.get_conf(mode='none')]),
        poses=array(scene.get_im_poses()), focal=array(scene.get_focals()),
        pp=array(scene.get_principal_points()), intrinsics=array(scene.get_intrinsics()),
        pw_poses=array(scene.get_pw_poses()), adaptors=array(scene.get_adaptors()),
        colors=np.stack([array(x) for x in scene.imgs]))


def validate_scene(d):
    import numpy as np
    shapes = dict(world_points=[2,384,512,3], depths=[2,384,512], confidence=[2,384,512],
        poses=[2,4,4], focal=[2,1], pp=[2,2], intrinsics=[2,3,3], pw_poses=[1,4,4],
        adaptors=[1,3], colors=[2,384,512,3])
    for k, s in shapes.items():
        validate_array(d[k], s, 'float32', k)
    require((d['depths'] > 0).all(), 'Camera depth strictly positive; world Z unrestricted')
    require((d['focal'] > 0).all(), 'Positive focal')
    require((d['confidence'] >= 0).all(), 'Clean confidence nonnegative including zero')
    require((d['colors'] >= 0).all() and (d['colors'] <= 1).all(), 'Real input color range')
    R = d['poses'][:, :3, :3].astype(np.float64)
    require(np.allclose(R.transpose(0,2,1) @ R, np.eye(3), atol=1e-4, rtol=0)
        and np.allclose(np.linalg.det(R), 1, atol=1e-4, rtol=0), 'Proper camera rotation')
    require(np.array_equal(d['poses'][:,3,:], np.tile([0,0,0,1], (2,1))), 'Camera homogeneous row')


class Observers:
    """Delegate original functions exactly once; observations cannot change their return values."""
    def __init__(self, out, report, phase, torch, modules):
        self.out, self.report, self.phase, self.torch = out, report, phase, torch
        self.modules = modules
        self.originals, self.handles = [], []
        self.scene = None
        self.optimizer = None

    def patch(self, obj, name, wrapper):
        old = getattr(obj, name)
        self.originals.append((obj, name, old))
        setattr(obj, name, wrapper(old))

    def install(self):
        T = self.torch
        r = self.report
        c = r['counters']
        def wrap_prepare(old):
            def call(*a, **kw):
                v = old(*a, **kw)
                c['prepare_input_calls'] += 1
                require(len(v) == 2, 'Two native views')
                r['processed_input_shapes'] = [list(x['img'].shape) for x in v]
                r['processed_true_shapes'] = [x['true_shape'].tolist() for x in v]
                r['history_flags'] = [{k: bool(x[k].item()) for k in FLAGS} for x in v]
                for i, x in enumerate(v):
                    require(list(x['img'].shape) == [1,3,384,512] and bool(T.isfinite(x['img']).all()), 'Processed image')
                    require(x['true_shape'].tolist() == [[384,512]] and x['idx'] == i, 'Native view index/shape')
                    require(r['history_flags'][i] == FLAGS, 'Native flags')
                    require(list(x['ray_map'].shape) == [1,6,384,512] and bool(T.isnan(x['ray_map']).all()), 'Native unused NaN rays')
                    require(T.equal(x['camera_pose'], T.eye(4).unsqueeze(0)), 'Native placeholder camera only')
                c['supplied_image_frames'] = sum(int(x['img_mask'].sum()) for x in v)
                c['supplied_ray_frames'] = sum(int(x['ray_mask'].sum()) for x in v)
                save_npz(self.out, 'processed_inputs.npz', {f'frame{i}_img': x['img'] for i,x in enumerate(v)}, r)
                self.phase('native_inputs_saved')
                return v
            return call
        self.patch(self.modules['wrapper'], 'prepare_input_from_pil', wrap_prepare)
        def wrap_inference(old):
            def call(*a, **kw):
                c['inference_attempts'] += 1
                require(c['inference_attempts'] == 1, 'One original inference call')
                self.phase('native_inference_started')
                t = time.perf_counter()
                outputs, states = old(*a, **kw)
                r['native_inference_seconds'] = time.perf_counter() - t
                c['inference_calls'] += 1
                require(len(outputs['pred']) == 2 and len(states) == 3 and len(states[-1]) == 5, 'Original raw return schema')
                raw = save_npz(self.out, 'predictions.npz', {f'frame{i}_{k}':v for i,p in enumerate(outputs['pred']) for k,v in p.items() if T.is_tensor(v)}, r)
                state = save_npz(self.out, 'state.npz', dict(zip(FIELDS, states[-1])), r)
                self.phase('raw_predictions_saved_before_gates')
                for i,p in enumerate(outputs['pred']):
                    require({k for k,v in p.items() if T.is_tensor(v)} == set(OUTPUT_SHAPES), 'Six raw heads')
                    for k,s in OUTPUT_SHAPES.items():
                        validate_array(raw[f'frame{i}_{k}'],s,'float32',k)
                for k in FIELDS:
                    validate_array(state[k],*STATE_SCHEMA[k],k)
                enc = T.cat([p['camera_pose'] for p in outputs['pred']])
                with T.no_grad():
                    poses = self.modules['camera'].pose_encoding_to_camera(enc)
                save_npz(self.out,'history_poses.npz',dict(history_pose_encodings=enc,history_poses=poses),r)
                c['history_frames_saved'] = 2
                return outputs, states
            return call
        self.patch(self.modules['inference'], 'inference', wrap_inference)
        def wrap_align(old):
            def call(*a, **kw):
                scene = old(*a, **kw)
                self.scene = scene
                c['global_aligner_calls'] += 1
                r['scene_edges'] = [list(e) for e in scene.edges]
                require(r['scene_edges'] == [[0,1]], 'Original single star edge')
                r['scene_parameters'] = [dict(name=n,shape=list(p.shape),dtype=str(p.dtype),requires_grad=p.requires_grad,numel=p.numel()) for n,p in scene.named_parameters()]
                r['scene_config'] = dict(type=type(scene).__name__, norm_pw_scale=bool(scene.norm_pw_scale),base_scale=scene.base_scale, min_conf_thr=scene.min_conf_thr)
                self.handles.append(scene.register_forward_hook(lambda *unused: c.__setitem__('scene_objective_calls', c['scene_objective_calls']+1)))
                save_npz(self.out,'scene_constructed.npz',capture_scene(scene),r)
                return scene
            return call
        self.patch(self.modules['aligner'],'global_aligner',wrap_align)
        def wrap_mst(old):
            def call(scene,*a,**kw):
                c['mst_calls'] += 1
                r['mst_kwargs'] = kw
                ans = old(scene,*a,**kw)
                save_npz(self.out,'scene_after_mst.npz',capture_scene(scene),r)
                self.phase('mst_initialized')
                return ans
            return call
        self.patch(self.modules['init'],'init_minimum_spanning_tree',wrap_mst)
        def wrap_pnp(old):
            def call(*a,**kw):
                idx = c['pnp_calls']; c['pnp_calls'] += 1
                ans = old(*a,**kw)
                record = dict(index=idx,success=ans is not None, kwargs={k:v for k,v in kw.items() if k == 'niter_PnP'})
                if ans is not None:
                    record['focal'] = float(ans[0])
                    save_npz(self.out,f'pnp_{idx}.npz',dict(pose=ans[1]),r)
                r.setdefault('pnp_results',[]).append(record)
                return ans
            return call
        self.patch(self.modules['init'],'fast_pnp',wrap_pnp)
        def wrap_iter(old):
            def call(net,cur_iter,niter,lr_base,lr_min,optimizer,schedule):
                require(cur_iter == c['optimization_iterations'] and niter == 400 and lr_base == .01 and schedule == 'linear', 'Native fixed optimization schedule')
                if self.optimizer is None:
                    self.optimizer = optimizer
                    def wrap_step(step):
                        def counted(*a,**kw):
                            result = step(*a,**kw)
                            c['optimizer_steps'] += 1
                            return result
                        return counted
                    self.patch(optimizer,'step',wrap_step)
                    r['optimizer'] = dict(type=type(optimizer).__name__,defaults={k:v for k,v in optimizer.defaults.items() if isinstance(v,(int,float,bool,tuple)) or v is None})
                require(optimizer is self.optimizer, 'One original optimizer')
                loss, lr = old(net,cur_iter,niter,lr_base,lr_min,optimizer,schedule)
                c['optimization_iterations'] += 1
                item = dict(iteration=cur_iter, loss_before_step=float(loss),lr=float(lr), utc=utc(), optimizer_steps=c['optimizer_steps'])
                r['optimization_trace'].append(item)
                with (self.out/'optimization_trace.jsonl').open('a') as f:
                    f.write(json.dumps(item,allow_nan=False)+'\n')
                require(__import__('math').isfinite(loss) and __import__('math').isfinite(lr), 'Finite native loss/lr')
                if (cur_iter+1) % 25 == 0:
                    self.phase('geometry_iteration_'+str(cur_iter+1))
                return loss,lr
            return call
        self.patch(self.modules['base'],'global_alignment_iter',wrap_iter)
        def wrap_compute(old):
            def call(scene,*a,**kw):
                r['alignment_arguments'] = kw
                result = old(scene,*a,**kw)
                r['alignment_returned_loss_before_last_step'] = float(result)
                return result
            return call
        self.patch(self.modules['base'].BasePCOptimizer,'compute_global_alignment',wrap_compute)
        def wrap_clean(old):
            def call(scene,*a,**kw):
                c['clean_calls'] += 1
                require(not a and not kw, 'Original cleaning defaults')
                before = save_npz(self.out,'scene_before_clean.npz',capture_scene(scene),r)
                with T.no_grad():
                    r['postfinal_objective'] = float(scene())
                c['postfinal_objective_evaluations'] += 1
                result = old(scene,*a,**kw)
                after = save_npz(self.out,'scene_after_clean.npz',capture_scene(scene),r)
                for k in before:
                    if k != 'confidence':
                        require(__import__('numpy').array_equal(before[k],after[k]),'Cleaning changed geometry: '+k)
                validate_scene(after)
                r['clean_changed_pixels'] = [int((before['confidence'][i] != after['confidence'][i]).sum()) for i in range(2)]
                r['clean_zero_pixels'] = [int((after['confidence'][i] == 0).sum()) for i in range(2)]
                self.phase('clean_geometry_and_confidence_saved')
                return result
            return call
        self.patch(self.modules['base'].BasePCOptimizer,'clean_pointcloud',wrap_clean)

    def restore(self):
        for h in self.handles:
            h.remove()
        for obj,name,old in reversed(self.originals):
            setattr(obj,name,old)


def verify_modules(source_root, report, identities):
    found = {}
    for name, module in list(sys.modules.items()):
        if name in {'surfel_inference', 'add_ckpt_path', 'dust3r', 'src.dust3r', 'models', 'cloud_opt', 'croco'} or name.startswith(('dust3r.', 'src.dust3r.', 'models.', 'cloud_opt.', 'croco.')):
            f = getattr(module, '__file__', None)
            if f:
                p = Path(f).resolve()
                require(p.is_relative_to(source_root), 'Mixed original/standalone source module: '+name)
                digest = sha(p)
                require(identities.get(str(p)) == digest, 'Loaded module absent from frozen manifest: '+name)
                found[name] = dict(path=str(p),sha256=digest)
    require(found, 'Embedded module paths observed')
    report['embedded_module_identities'] = found


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args()
    require(not a.output.exists(), 'Fresh output directory required')
    a.output.mkdir(parents=True)
    start = time.perf_counter()
    counts = ['history_rgb_decoded','target_rgb_decoded','sensor_depth_reads','main_generator_calls','wrapper_calls',
        'prepare_input_calls','inference_attempts','inference_calls','model_forward_calls','history_frames_saved',
        'supplied_image_frames','supplied_ray_frames','image_encoder_calls','image_encoder_frames',
        'dummy_ray_encoder_calls','dummy_ray_encoder_frames','encoder_first_calls','encoder_last_calls',
        'global_aligner_calls','mst_calls','pnp_calls','optimization_iterations','optimizer_steps','clean_calls',
        'postfinal_objective_evaluations','scene_objective_calls','query_calls']
    r = dict(schema='s17c-embedded-two-frame-geometry-run-v1',label=LABEL,status='RUNNING',started_utc=utc(),
        counters={k:0 for k in counts},optimization_trace=[],input_reads=[],encoder_observations=[],
        video_generated=False,new_model_trained=False,accuracy_evaluated=False,
        supplied_pose_prior=False,supplied_depth_prior=False,surfel_objects_created=False)
    def phase(name):
        r.update(phase=name,updated_utc=utc(),elapsed_seconds=time.perf_counter()-start,
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if platform.system()=='Darwin' else 1024))
        write(a.output/'run_metadata.json',r)
        print(json.dumps(dict(phase=name,utc=utc())),flush=True)
    def check_ids(ids, when):
        for path,digest in ids.items():
            require(sha(path)==digest,'Changed frozen input: '+path)
        r.setdefault('identity_checks',[]).append(dict(when=when,utc=utc(),count=len(ids),all_match=True))
    observer = None
    hooks = []
    oldopen = None
    pil_images = []
    try:
        phase('manifest_validation')
        m = json.loads(a.manifest.read_text())
        paths = validate_contract(m)
        require(str(Path(__file__).resolve())==m['runner'],'Runner identity')
        require(os.path.realpath(sys.executable)==os.path.realpath(m['python']),'Python identity')
        require(Path(m['checkpoint']).stat().st_size==CHECKPOINT_BYTES,'Complete public DPT size')
        check_ids(m['identities'],'before')
        source_plan=json.loads(Path(m['source_plan']).read_text())
        src=Path(m['source_root']).resolve()
        expected={k:v['sha256'] for k,v in source_plan['source_files'].items()}
        expected.update({v['path']:v['sha256'] for v in source_plan['patches']})
        source_ids={str(src/k):v for k,v in expected.items()}
        require({p:h for p,h in m['identities'].items() if Path(p).is_relative_to(src)}==source_ids,'Exact 198 original files plus three transparent patch identities')
        smoke=json.loads(Path(m['import_smoke']).read_text())
        validate_import_smoke(smoke)
        shutil.copy2(a.manifest,a.output/'frozen_manifest.json')
        shutil.copy2(__file__,a.output/'source_snapshot.py')
        r.update(manifest_sha256=sha(a.manifest),source_commit=COMMIT,source_plan_sha256=SOURCE_PLAN_SHA,
            checkpoint_identity=dict(path=m['checkpoint'],bytes=CHECKPOINT_BYTES,sha256=CHECKPOINT_SHA256),
            history_images=m['history_images'],contract=m['contract'],python=sys.version,executable=sys.executable)
        os.environ['HF_HUB_OFFLINE']='1'
        os.environ['TRANSFORMERS_OFFLINE']='1'
        os.environ['MPLBACKEND']='Agg'
        os.environ['MPLCONFIGDIR']=str(a.output/'matplotlib_config')
        os.environ['TORCH_FORCE_WEIGHTS_ONLY_LOAD']='1'
        require(str(os.environ.get('TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD','')).lower() not in {'1','y','yes','true'},'Unsafe load override')
        embedded=src/'extern/CUT3R'
        sys.path[:0]=[m['overlay'],str(embedded),str(embedded/'src'),str(embedded/'src/croco')]
        import numpy as np
        import torch
        import cv2
        from PIL import Image
        from dust3r.model import ARCroco3DStereo
        modules={k:importlib.import_module(n) for k,n in dict(wrapper='surfel_inference',
            inference='src.dust3r.inference',camera='dust3r.utils.camera',
            aligner='cloud_opt.dust3r_opt',base='cloud_opt.dust3r_opt.base_opt',init='cloud_opt.dust3r_opt.init_im_poses').items()}
        verify_modules(src,r,m['identities'])
        import scipy
        r['core_dependency_paths'] = {k:dict(path=str(Path(x.__file__).resolve()),version=x.__version__) for k,x in [('numpy',np),('torch',torch),('scipy',scipy)]}
        require(np.__version__=='1.26.4' and torch.__version__=='2.7.0' and scipy.__version__=='1.16.2','Frozen existing numerical versions')
        require(all(not Path(v['path']).is_relative_to(Path(m['overlay']).resolve()) for v in r['core_dependency_paths'].values()), 'Overlay cannot replace existing NumPy/Torch/SciPy')
        random.seed(0); np.random.seed(0); torch.manual_seed(0); cv2.setRNGSeed(0)
        torch.set_num_threads(8)
        r.update(torch_version=torch.__version__,numpy_version=np.__version__,cv2_version=cv2.__version__,
            pillow_version=Image.__version__,device='cpu',cpu_threads=8,seed=0,
            rngs_seeded_after_import=['python','numpy','torch','opencv'],precision='FP32; original q/k FP16 RoPE interface')
        phase('checkpoint_load')
        from omegaconf import DictConfig
        from omegaconf.base import ContainerMetadata,Metadata
        from omegaconf.nodes import AnyNode
        allowed=[DictConfig,ContainerMetadata,Any,dict,defaultdict,AnyNode,Metadata]
        allowed_names={f'{v.__module__}.{v.__qualname__}' for v in allowed}
        unsafe=torch.serialization.get_unsafe_globals_in_checkpoint(m['checkpoint'])
        require(not(set(unsafe)-allowed_names),'Unapproved checkpoint globals')
        log=io.StringIO()
        try:
            with contextlib.redirect_stdout(log),torch.serialization.safe_globals(allowed):
                model=ARCroco3DStereo.from_pretrained(m['checkpoint']).float().to('cpu').eval()
        finally:
            (a.output/'checkpoint_load.txt').write_text(log.getvalue())
        require('All keys matched successfully' in log.getvalue(),'Checkpoint keys matched')
        require(model.head_type=='dpt' and list(model.patch_embed.img_size)==[512,512], '512 DPT architecture')
        require(type(model.downstream_head).__name__=='DPTPts3dPose' and len(model.enc_blocks)==24,'DPT six heads/encoder24')
        r.update(weights_only=True,checkpoint_all_keys_matched=True,checkpoint_unsafe_globals=unsafe,
            architecture=dict(head_type=model.head_type,output_mode=model.output_mode,image_patch_class=type(model.patch_embed).__name__,
                ray_patch_class=type(model.patch_embed_ray_map).__name__,patch_image_size=list(model.patch_embed.img_size),
                downstream_head_class=type(model.downstream_head).__name__,encoder_blocks=len(model.enc_blocks),parameters=sum(x.numel() for x in model.parameters())))
        c=r['counters']
        def model_hook(*unused): c['model_forward_calls']+=1
        def encoder_hook(kind):
            def hook(module,inputs,output):
                c[kind+'_calls']+=1
                rec=dict(kind=kind,input_shape=list(inputs[0].shape),dtype=str(inputs[0].dtype))
                if kind in {'image_encoder','dummy_ray_encoder'}:
                    c[kind+'_frames']+=int(inputs[0].shape[0]);rec['output_token_shape']=list(output[0].shape)
                if kind=='dummy_ray_encoder': rec['all_zero']=bool((inputs[0]==0).all())
                r['encoder_observations'].append(rec)
            return hook
        hooks=[model.register_forward_hook(model_hook),model.patch_embed.register_forward_hook(encoder_hook('image_encoder')),
            model.patch_embed_ray_map.register_forward_hook(encoder_hook('dummy_ray_encoder')),
            model.enc_blocks[0].register_forward_hook(encoder_hook('encoder_first')),
            model.enc_blocks[-1].register_forward_hook(encoder_hook('encoder_last'))]
        phase('decode_only_two_native_photos')
        oldopen=Image.open
        def guarded_open(fp,*args,**kw):
            path=str(Path(fp).resolve());i=c['history_rgb_decoded']
            require(i<2 and path==paths[i],'Image read outside exact two ordered RGB inputs')
            im=oldopen(fp,*args,**kw)
            require(im.mode=='RGB' and list(im.size)==[640,480],'Native Bonn RGB 640x480')
            im.load();c['history_rgb_decoded']+=1
            r['input_reads'].append(dict(role='native_rgb_decode',path=path,index=i,mode=im.mode,size=list(im.size),utc=utc()))
            return im
        Image.open=guarded_open
        pil_images=[Image.open(path) for path in paths]
        observer=Observers(a.output,r,phase,torch,modules);observer.install()
        phase('original_wrapper_started')
        c['wrapper_calls']+=1
        result=modules['wrapper'].run_inference_from_pil(pil_images,model,poses=None,depths=None,lr=.01,niter=400,
            device='cpu',size=512,visualize=False,save_flag=False,output_dir=str(a.output/'native_unused_output'))
        require(set(result)=={'point_clouds','colors','depths','confidences','camera_info'},'Original result categories')
        require(set(result['camera_info'])=={'focal','pp','R','t'},'Original camera info')
        final={k:np.concatenate([array(x) for x in result[k]],axis=0) for k in ['point_clouds','colors','depths','confidences']}
        final.update(result['camera_info']);save_npz(a.output,'final_result.npz',final,r)
        after=capture_scene(observer.scene)
        for k,j in [('point_clouds','world_points'),('colors','colors'),('depths','depths'),('confidences','confidence'),('focal','focal'),('pp','pp')]:
            require(np.array_equal(final[k],after[j]),'Returned value equality: '+k)
        require(np.array_equal(final['R'],after['poses'][:,:3,:3]) and np.array_equal(final['t'],after['poses'][:,:3,3]),'Returned camera equality')
        require(all(p.grad is None for p in model.parameters()),'No neural network training gradients')
        require(not model.training,'Model remains eval')
        model_ids={id(p) for p in model.parameters()}
        require(not model_ids.intersection(id(p) for g in observer.optimizer.param_groups for p in g['params']), 'Alignment optimizer contains no neural weights')
        exact=dict(history_rgb_decoded=2,target_rgb_decoded=0,sensor_depth_reads=0,main_generator_calls=0,wrapper_calls=1,
            prepare_input_calls=1,inference_attempts=1,inference_calls=1,model_forward_calls=1,history_frames_saved=2,
            supplied_image_frames=2,supplied_ray_frames=0,image_encoder_calls=1,image_encoder_frames=2,
            dummy_ray_encoder_calls=1,dummy_ray_encoder_frames=1,encoder_first_calls=1,encoder_last_calls=1,
            global_aligner_calls=1,mst_calls=1,optimization_iterations=400,optimizer_steps=400,clean_calls=1,
            postfinal_objective_evaluations=1,scene_objective_calls=401,query_calls=0)
        for k,v in exact.items(): require(c[k]==v,'Actual counter: '+k)
        require(np.isfinite(r['postfinal_objective']),'Finite postfinal objective')
        verify_modules(src,r,m['identities']);check_ids(m['identities'],'after')
        phase('final_outputs_validated')
        require(r['elapsed_seconds']<=600 and r['peak_rss_bytes']<=34359738368,'Internal resource gate; external caller authoritative')
        r['status']='SUCCESS'
    except BaseException as ex:
        r.update(status='FAILED',error_type=type(ex).__name__,error=str(ex),traceback=traceback.format_exc())
        if observer is not None and observer.scene is not None:
            try: save_npz(a.output,'scene_failure.npz',capture_scene(observer.scene),r)
            except Exception as capture_error: r['failure_snapshot_error']=repr(capture_error)
    finally:
        if observer is not None: observer.restore()
        for h in hooks: h.remove()
        if oldopen is not None: Image.open=oldopen
        for im in pil_images: im.close()
        r['finished_utc']=utc()
        r['output_files']={str(p.relative_to(a.output)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(a.output.rglob('*')) if p.is_file() and p.name!='run_metadata.json'}
        phase('finished')
    return 0 if r['status']=='SUCCESS' else 1


if __name__=='__main__':
    raise SystemExit(main())
