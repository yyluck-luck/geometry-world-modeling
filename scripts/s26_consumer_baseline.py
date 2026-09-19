"""S26 saved-head replay through VMem's unchanged constrained GA.

Four/eight real frames are a component pilot, not a new method or video result.
Workers use fresh processes. No network model or checkpoint is loaded.
"""
from __future__ import annotations
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / 'work/S26_consumer_baseline_preparation'
WORK = ROOT / 'work/S26_execution'
OUT = ROOT / 'results/S26_consumer_baseline'
MANIFEST = PREP / 'run_manifest.json'
MODES = ('common_old', 'cut3r', 'ttt3r', 'filt3r')


def utc(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def write(p, value):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    tmp.replace(p)
def require(condition, message):
    if not condition: raise RuntimeError(message)
def array(x):
    import numpy as np
    return np.array(x.detach().cpu().numpy() if hasattr(x, 'detach') else x, copy=True)


def manifest(expected):
    require(sha(MANIFEST) == expected, 'Exact frozen S26 manifest required')
    m = read(MANIFEST)
    for p, h in m['identities'].items(): require(sha(p) == h, 'Changed source/contract: '+p)
    return m


def adapter():
    sys.path.insert(0, str(PREP))
    return importlib.import_module('saved_heads_adapter')


def numeric_setup():
    import numpy as np
    import torch
    torch.set_num_threads(8)
    torch.manual_seed(0)
    np.random.seed(0)
    random.seed(0)
    import cv2
    cv2.setRNGSeed(0)
    require(np.__version__ == '1.26.4' and torch.__version__ == '2.7.0', 'Numerical environment')
    return np, torch


def source_views(m, variant):
    """Same baseline preprocessing, in a process with its original namespace."""
    repo = Path(m['preprocess_repos'][variant])
    sys.path[:0] = [str(repo/'src'), str(repo/'src/croco')]
    np, torch = numeric_setup()
    from dust3r.utils.image import load_images_for_eval
    source = Path(m['preprocess_function'])
    tree = ast.parse(source.read_text())
    found = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'prepare_input']
    require(len(found)==1, 'Exactly one original baseline prepare_input')
    fn = found[0]
    ns = dict(torch=torch, np=np, load_images=load_images_for_eval, deepcopy=copy.deepcopy)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), 'exec'), ns)
    frames = m['candidate']['frames']
    for f in frames: require(sha(f['path']) == f['sha256'], 'RGB bytes changed')
    views = ns['prepare_input']([f['path'] for f in frames], [True]*8, size=512, crop=True, revisit=1, update=True)
    vals = {f'img_{i}': array(v['img']) for i,v in enumerate(views)}
    vals.update({f'shape_{i}': array(v['true_shape']) for i,v in enumerate(views)})
    np.savez_compressed(WORK / (variant+'_views.npz'), **vals)
    write(WORK / (variant+'_views_receipt.json'), dict(status='PASS', completed_utc=utc(),
        manifest_sha256=sha(MANIFEST), source=str(repo), frame_count=8,
        outputs={variant+'_views.npz':sha(WORK/(variant+'_views.npz'))}, model_forwards=0))


def control_input(m):
    """GT cameras are an explicit shared experimental condition, not an answer."""
    np, torch = numeric_setup()
    from scipy.spatial.transform import Rotation
    condition = m['candidate']['given_pose_condition']
    write(WORK/'control_receipt.json', dict(status='READING_ALLOWED_CAMERA_INPUT', started_utc=utc(),
        camera_source=condition['source'], role=condition['role'], sensor_depth_used=False))
    require(sha(condition['source']) == condition['expected_sha256'], 'Control camera source SHA')
    selected = {f['gt_time'] for f in m['candidate']['frames']}
    rows = {}
    for line in Path(condition['source']).read_text().splitlines():
        if not line.strip() or line.startswith('#'): continue
        fields = line.split()
        if float(fields[0]) in selected:
            t = float(fields[0]); require(t not in rows, 'Duplicate selected GT timestamp')
            rows[t] = [float(x) for x in fields[1:]]
    cams = np.repeat(np.eye(4, dtype=np.float64)[None], 8, axis=0)
    for i,f in enumerate(m['candidate']['frames']):
        row = rows[f['gt_time']]; require(len(row)==7 and np.isfinite(row).all(), 'Selected camera row')
        require(abs(np.linalg.norm(row[3:])-1) < 1e-3, 'Quaternion normalization sanity')
        cams[i,:3,:3] = Rotation.from_quat(row[3:]).as_matrix()
        cams[i,:3,3] = row[:3]
    # TUM c2w is already optical. This worker enters the GA interface after
    # VMem's OpenGL-to-optical conversion: no additional Y/Z flip is applied.
    np.save(WORK/'control_c2w.npy', cams.astype(np.float32))
    write(WORK/'control_receipt.json', dict(status='PASS', completed_utc=utc(),
        manifest_sha256=sha(MANIFEST), frame_count=8, sensor_depth_used=False,
        role=condition['role'], coordinates='TUM optical c2w, no flip, absolute metric world',
        output_sha256=sha(WORK/'control_c2w.npy')))


def original_context(m):
    np, torch = numeric_setup()
    a = adapter()
    ns, proof = a.configure_original_geometry(m['binding'])
    views = a.load_original_views(ns, m['candidate']['frames'])
    return np, torch, a, ns, views, proof


def compare_nested(x,y,torch):
    if isinstance(x, dict):
        require(set(x)==set(y), 'Assembly keys')
        for k in x: compare_nested(x[k],y[k],torch)
    elif torch.is_tensor(x):
        require(x.dtype==y.dtype and x.shape==y.shape, 'Assembly tensor schema')
        require(bool(((x==y)|(torch.isnan(x)&torch.isnan(y))).all()) if x.is_floating_point() else torch.equal(x,y), 'Exact assembly values')
    else: require(x==y, 'Assembly list/scalar values')


def compatibility(m):
    np, torch, a, ns, views, proof = original_context(m)
    checks = []
    for variant in m['preprocess_repos']:
        receipt = read(WORK/(variant+'_views_receipt.json'))
        require(receipt['status']=='PASS' and receipt['manifest_sha256']==sha(MANIFEST), 'Preprocess receipt')
        p = WORK/(variant+'_views.npz')
        require(sha(p)==receipt['outputs'][p.name], 'Preprocess archive seal')
        with np.load(p, allow_pickle=False) as z:
            for i,v in enumerate(views):
                require(np.array_equal(array(v['img']),z[f'img_{i}']), 'Exact RGB preprocessing '+variant)
                require(np.array_equal(array(v['true_shape']),z[f'shape_{i}']), 'Exact processed shape')
        checks.append(variant+'_eight_preprocess_exact')
    for name,records in m['candidate']['archives'].items():
        predictions = a.load_saved_predictions(records)
        n = len(predictions)
        output = a.assemble_saved_output(ns, views[:n], predictions)
        # Independent explicit star construction, not the AST assembly loop.
        expected = {
            'view1': ns['collate_with_cat']([views[0]]*(n-1)),
            'view2': ns['collate_with_cat'](views[1:n]),
            'pred1': ns['collate_with_cat']([predictions[0]]*(n-1)),
            'pred2': ns['collate_with_cat'](predictions[1:n]),
        }
        compare_nested(output, expected, torch)
        checks.append(name+'_all_heads_and_star_exact')
    write(WORK/'compatibility_receipt.json', dict(status='PASS', completed_utc=utc(),
        manifest_sha256=sha(MANIFEST), checks=checks, source_proof=proof,
        model_forwards=0, GA_runs=0, sensor_depth_used=False,
        scope='real saved-array/preprocessing integration; no new neural compatibility claim'))


class SceneObserver:
    def __init__(self, out, n, cameras, old_depth, torch):
        self.out, self.n, self.cameras, self.old, self.T = out,n,cameras,old_depth,torch
        self.patches=[]; self.scene=None; self.steps=0; self.clean_calls=0
        self.frozen=None; self.snapshot=None
        self.report={}; self.optimizer=None; self.adam_steps=0; self.mst_calls=0
    def patch(self,obj,name,wrapper):
        old=getattr(obj,name); self.patches.append((obj,name,old)); setattr(obj,name,wrapper(old))
    def params(self,s):
        # Original clean intentionally rewrites the non-trainable im_conf list.
        # Its exact behavior is checked separately, not treated as a pose/depth constraint.
        return {n:p.detach().clone() for n,p in s.named_parameters()
                if not p.requires_grad and not n.startswith('im_conf.')}
    def check_fixed(self,s):
        require(s.im_poses.requires_grad is False and not s.norm_pw_scale, 'All poses fixed, metric pair scale')
        require([p.requires_grad for p in s.im_depthmaps]==([True]*self.n if self.old is None else [False]*4+[True]*4), 'Old/new depth trainability')
        require(s.im_focals.requires_grad and not s.im_pp.requires_grad, 'Original focal/pp policy')
        require(self.T.allclose(s.get_im_poses(),self.cameras,atol=1e-5,rtol=1e-6), 'Given poses preserved')
        if self.old is not None:
            require(self.T.allclose(self.T.stack(s.get_depthmaps()[:4]),self.old,atol=1e-6,rtol=1e-6), 'Old depth log/exp tolerance')
    def install(self):
        align=importlib.import_module('cloud_opt.dust3r_opt')
        base=importlib.import_module('cloud_opt.dust3r_opt.base_opt')
        init=importlib.import_module('cloud_opt.dust3r_opt.init_im_poses')
        def wrap_align(old):
            def call(*args,**kwargs):
                s=old(*args,**kwargs); self.scene=s
                require(s.edges==[(0,j) for j in range(1,self.n)], 'Exact original directed star')
                import numpy as np
                np.savez_compressed(self.out/'consumed_inputs.npz',
                    pred_i=array(s._stacked_pred_i),pred_j=array(s._stacked_pred_j),
                    weight_i=array(s._weight_i),weight_j=array(s._weight_j),
                    edge_i=array(s._ei),edge_j=array(s._ej))
                return s
            return call
        self.patch(align,'global_aligner',wrap_align)
        def wrap_compute(old):
            def call(s,*args,**kw):
                require(kw==dict(init='mst',niter=400,schedule='linear',lr=.01), 'Original GA arguments')
                self.check_fixed(s); self.frozen=self.params(s)
                import numpy as np
                np.savez_compressed(self.out/'preset_parameters.npz',**{k:array(v) for k,v in self.frozen.items()})
                self.report['parameter_flags']={n:p.requires_grad for n,p in s.named_parameters()}
                result=old(s,*args,**kw)
                self.check_fixed(s)
                for name,p in self.params(s).items(): require(self.T.equal(p,self.frozen[name]), 'Fixed parameter changed: '+name)
                self.report['returned_pre_last_step_loss']=float(result)
                return result
            return call
        self.patch(base.BasePCOptimizer,'compute_global_alignment',wrap_compute)
        def wrap_mst(old):
            def call(s,*args,**kw):
                self.mst_calls+=1
                result=old(s,*args,**kw)
                self.check_fixed(s)
                for name,p in self.params(s).items(): require(self.T.equal(p,self.frozen[name]), 'MST changed fixed parameter '+name)
                return result
            return call
        self.patch(init,'init_minimum_spanning_tree',wrap_mst)
        def wrap_pnp(old):
            def call(*args,**kw):
                result=old(*args,**kw)
                record=dict(success=result is not None,niter_PnP=kw.get('niter_PnP'))
                if result is not None:record['focal']=float(result[0])
                self.report.setdefault('pnp_calls',[]).append(record)
                return result
            return call
        self.patch(init,'fast_pnp',wrap_pnp)
        def wrap_iter(old):
            def call(net,cur_iter,niter,lr_base,lr_min,optimizer,schedule):
                require(cur_iter==self.steps and niter==400 and lr_base==.01 and schedule=='linear', 'Iteration contract')
                if self.optimizer is None:
                    self.optimizer=optimizer
                    def wrap_step(step):
                        def counted(*args,**kw):
                            result=step(*args,**kw);self.adam_steps+=1;return result
                        return counted
                    self.patch(optimizer,'step',wrap_step)
                require(self.optimizer is optimizer and isinstance(optimizer,self.T.optim.Adam),'Same original Adam')
                result=old(net,cur_iter,niter,lr_base,lr_min,optimizer,schedule)
                loss,lr=result; require(math.isfinite(float(loss)) and math.isfinite(float(lr)), 'Finite GA trajectory')
                self.steps+=1
                with (self.out/'optimization_trace.jsonl').open('a') as f:
                    f.write(json.dumps(dict(iteration=cur_iter,loss_before_step=float(loss),lr=float(lr),utc=utc()))+'\n')
                if self.steps%25==0: write(self.out/'progress.json',dict(status='RUNNING',iterations=self.steps,utc=utc()))
                return result
            return call
        self.patch(base,'global_alignment_iter',wrap_iter)
        def wrap_clean(old):
            def capture(s):
                import numpy as np
                return dict(depth=np.stack([array(v) for v in s.get_depthmaps()]),
                    point_cloud=np.stack([array(v) for v in s.get_pts3d()]),
                    conf=np.stack([array(v) for v in s.get_conf(mode='none')]),
                    focal=array(s.get_focals()),pp=array(s.get_principal_points()),c2w=array(s.get_im_poses()))
            def call(s,*args,**kw):
                import numpy as np
                require(not args and not kw and self.clean_calls==0, 'Original cleaning defaults once')
                before=capture(s)
                with self.T.no_grad():self.report['postfinal_objective']=float(s())
                result=old(s,*args,**kw); after=capture(s)
                for k in before:
                    if k!='conf': require(np.array_equal(before[k],after[k]), 'Cleaning changed geometry: '+k)
                self.check_fixed(s)
                for name,p in self.params(s).items(): require(self.T.equal(p,self.frozen[name]), 'Clean changed fixed parameter '+name)
                np.savez_compressed(self.out/'preclean_conf.npz',conf=before['conf'])
                np.savez_compressed(self.out/'pairwise_state.npz',pw_poses=array(s.get_pw_poses()),adaptors=array(s.get_adaptors()))
                self.report['clean_changed_pixels']=[int(np.count_nonzero(x!=y)) for x,y in zip(before['conf'],after['conf'])]
                self.snapshot=after; self.clean_calls+=1
                return result
            return call
        self.patch(base.BasePCOptimizer,'clean_pointcloud',wrap_clean)
    def restore(self):
        for obj,name,old in reversed(self.patches): setattr(obj,name,old)


def ga_worker(m, mode):
    out=OUT/mode
    require(not out.exists(),'Never overwrite or repeat an existing GA run')
    out.mkdir(parents=True)
    n=4 if mode=='common_old' else 8
    r=dict(status='RUNNING',started_utc=utc(),mode=mode,frame_count=n,manifest_sha256=sha(MANIFEST),
           sensor_depth_used=False,model_forwards=0)
    write(out/'receipt.json',r)
    try:
        cr=read(WORK/'control_receipt.json'); compat=read(WORK/'compatibility_receipt.json')
        require(cr['status']=='PASS' and compat['status']=='PASS', 'Controls/compatibility required')
        require(cr['manifest_sha256']==compat['manifest_sha256']==sha(MANIFEST), 'Control manifest identity')
        require(sha(WORK/'control_c2w.npy')==cr['output_sha256'],'Camera input seal')
        np,torch,a,ns,views,proof=original_context(m)
        cameras=torch.from_numpy(np.load(WORK/'control_c2w.npy',allow_pickle=False)[:n].copy())
        name='common_old_depth_original4' if mode=='common_old' else mode
        records=m['candidate']['archives'][name]
        predictions=a.load_saved_predictions(records)
        output=a.assemble_saved_output(ns,views[:n],predictions)
        old=None; common_seal=None
        common_tensor_sha=None; common_pose_sha=None
        if n==8:
            prior=read(OUT/'common_old/receipt.json')
            require(prior['status']=='PASS' and prior['manifest_sha256']==sha(MANIFEST),'Common old-depth producer')
            require(sha(OUT/'common_old/output.npz')==prior['outputs']['output.npz'],'Common depth output seal')
            require(sha(OUT/'common_old/inputs_seal.json')==prior['inputs_seal_sha256'],'Common input seal')
            with np.load(OUT/'common_old/output.npz',allow_pickle=False) as z: old=torch.from_numpy(z['depth'].copy())
            common_seal=sha(OUT/'common_old/receipt.json')
            common_tensor_sha=prior['depth_tensor_sha256'];common_pose_sha=prior['control_pose_prefix_tensor_sha256']
            require(a.tensor_sha256(old)==common_tensor_sha and a.tensor_sha256(cameras[:4])==common_pose_sha,'Common old depth/camera tensor identity')
        seal=dict(manifest_sha256=sha(MANIFEST),mode=mode,frame_count=n,sensor_depth_used=False,
            saved_heads=records,control_c2w_sha256=cr['output_sha256'],
            common_old_receipt_sha256=common_seal,compatibility_receipt_sha256=sha(WORK/'compatibility_receipt.json'))
        write(out/'inputs_seal.json',seal); r['inputs_seal_sha256']=sha(out/'inputs_seal.json'); write(out/'receipt.json',r)
        observer=SceneObserver(out,n,cameras,old,torch); observer.install()
        numeric_setup()  # Repeat the fixed seeds after all geometry imports.
        started=time.perf_counter()
        try:
            result=a.run_original_ga(ns,output,control_c2ws=cameras,
                old_depth=None if old is None else a.CommonOldDepth(old,common_seal,common_tensor_sha,common_pose_sha),output_dir=out)
        finally: observer.restore()
        require(observer.steps==observer.adam_steps==400 and observer.clean_calls==observer.mst_calls==1,'Complete original GA/Adam/MST/clean')
        points,colors,depths,confs,cam=result
        original_colors=np.clip(np.concatenate([array(v['img']) for v in views[:n]]).transpose(0,2,3,1)*.5+.5,0,1)
        actual_colors=array(torch.cat(colors))
        require(np.array_equal(actual_colors,original_colors),'Wrapper colors are the input images')
        np.savez_compressed(out/'input_colors.npz',colors=actual_colors)
        c2w=np.repeat(np.eye(4,dtype=np.float32)[None],n,axis=0); c2w[:,:3,:3]=cam['R'];c2w[:,:3,3]=cam['t']
        vals=dict(depth=array(torch.cat(depths)),point_cloud=array(torch.cat(points)),
            conf=array(torch.cat(confs)),focal=array(cam['focal']),pp=array(cam['pp']),c2w=c2w)
        shapes=dict(depth=(n,384,512),point_cloud=(n,384,512,3),conf=(n,384,512),focal=(n,1),pp=(n,2),c2w=(n,4,4))
        for k,shape in shapes.items():
            require(vals[k].shape==shape and vals[k].dtype==np.float32 and np.isfinite(vals[k]).all(),'Output schema '+k)
            require(np.array_equal(vals[k],observer.snapshot[k]),'Wrapper output matches scene '+k)
        require((vals['depth']>0).all() and (vals['focal']>0).all() and (vals['conf']>=0).all(),'Output domain')
        # Save the complete original result even if a subsequent math gate fails.
        np.savez_compressed(out/'output.npz',**vals)
        spec=importlib.util.spec_from_file_location('s26_independent_reference',m['numerical_reference'])
        ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
        with np.load(out/'preclean_conf.npz',allow_pickle=False) as z:preconf=z['conf'].copy()
        expected,visits,margins=ref.clean_reference(preconf,vals['depth'],vals['point_cloud'],vals['focal'],vals['pp'],vals['c2w'][:,:3,:3],vals['c2w'][:,:3,3])
        mismatch=expected!=vals['conf'];observer.report['independent_clean_mismatch_pixels']=int(mismatch.sum())
        write(out/'independent_clean_visits.json',visits)
        if mismatch.any():np.savez_compressed(out/'clean_mismatch_diagnostics.npz',**margins,mismatch=mismatch)
        del margins
        require(not mismatch.any(),'Independent FP32 clean mismatch; no exemptions')
        with np.load(out/'pairwise_state.npz',allow_pickle=False) as z:
            objectives=[ref.pair_objective(vals['point_cloud'][[0,j]],array(predictions[0]['pts3d_in_self_view'])[0],
                array(predictions[j]['pts3d_in_other_view'])[0],array(predictions[0]['conf_self'])[0],array(predictions[j]['conf'])[0],
                z['pw_poses'][j-1],z['adaptors'][j-1]) for j in range(1,n)]
        independent_loss=float(np.mean(objectives))
        require(np.isclose(independent_loss,observer.report['postfinal_objective'],atol=1e-5,rtol=1e-4),'Independent original objective')
        observer.report['independent_objective']=independent_loss
        # Different NumPy row-vector implementation of depth->world reconstruction.
        yy,xx=np.indices((384,512),dtype=np.float64)
        maxerror=0.
        for i in range(n):
            d=vals['depth'][i].astype(float); f=float(vals['focal'][i,0]); p=vals['pp'][i]
            campts=np.stack([(xx-p[0])*d/f,(yy-p[1])*d/f,d],-1)
            world=campts@vals['c2w'][i,:3,:3].astype(float).T+vals['c2w'][i,:3,3]
            maxerror=max(maxerror,float(np.abs(world-vals['point_cloud'][i]).max()))
            require(np.allclose(world,vals['point_cloud'][i],atol=1e-5,rtol=1e-5),'Independent backprojection')
        # Verify the modules actually used came from the bound embedded source.
        loaded={}
        embedded=Path(m['binding']['embedded_root']).resolve()
        for name,module in list(sys.modules.items()):
            if name.startswith(('cloud_opt.','dust3r.','src.dust3r.','models.','croco.')):
                origin=getattr(module,'__file__',None)
                if origin:
                    p=Path(origin).resolve();require(p.is_relative_to(embedded),'Mixed geometry namespace '+name)
                    require(m['binding']['source_identities'].get(str(p))==sha(p),'Unbound geometry module '+name)
                    loaded[name]=str(p)
        loaded_deps={}
        overlay=Path(m['binding']['overlay']).resolve()
        for name,module in list(sys.modules.items()):
            origin=getattr(module,'__file__',None)
            if origin:
                p=Path(origin).resolve()
                if p.is_relative_to(overlay):
                    require(m['dependency_identities'].get(str(p))==sha(p),'Unbound loaded overlay module '+name)
                    loaded_deps[name]=str(p)
        r.update(status='PASS',completed_utc=utc(),ga_with_observation_seconds=time.perf_counter()-started,
            outputs={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name not in {'receipt.json','progress.json'}},
            depth_tensor_sha256=a.tensor_sha256(torch.from_numpy(vals['depth'])),
            control_pose_prefix_tensor_sha256=a.tensor_sha256(cameras[:4]),
            iterations=observer.steps,adam_steps=observer.adam_steps,clean_calls=observer.clean_calls,observer=observer.report,
            loaded_geometry_modules=loaded,
            loaded_overlay_modules=loaded_deps,
            independent_backprojection_max_abs=maxerror,original_source_proof=proof)
        write(out/'receipt.json',r)
    except BaseException as e:
        r.update(status='FAILED',failed_utc=utc(),error=type(e).__name__+': '+str(e));write(out/'receipt.json',r)
        (out/'traceback.txt').write_text(traceback.format_exc());raise


def supervised(command,name,seconds,rss_limit):
    import psutil
    import shutil
    require(shutil.disk_usage(ROOT).free>=10*1024**3,'10 GiB free disk required')
    path=WORK/name; path.mkdir(exist_ok=False)
    r=dict(status='RUNNING',started_utc=utc(),command=command,peak_rss_bytes=0)
    write(path/'receipt.json',r);start=time.monotonic()
    with (path/'stdout.txt').open('w') as out,(path/'stderr.txt').open('w') as err:
        p=subprocess.Popen(command,cwd=ROOT,stdout=out,stderr=err)
        try:
            while p.poll() is None:
                try:
                    proc=psutil.Process(p.pid)
                    rss=sum(x.memory_info().rss for x in [proc,*proc.children(recursive=True)])
                    r['peak_rss_bytes']=max(r['peak_rss_bytes'],rss)
                except psutil.NoSuchProcess: pass
                require(time.monotonic()-start<=seconds and r['peak_rss_bytes']<=rss_limit,'Stage resource cap')
                time.sleep(.5)
        except BaseException as e:
            p.terminate()
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill();p.wait()
            r.update(status='FAILED',error=str(e),completed_utc=utc(),returncode=p.returncode)
            write(path/'receipt.json',r);raise
    r.update(status='PASS' if p.returncode==0 else 'FAILED',completed_utc=utc(),returncode=p.returncode,wall_seconds=time.monotonic()-start)
    write(path/'receipt.json',r);require(p.returncode==0,'Worker failed: '+name)


def dispatch(m,expected):
    require(not (WORK/'dispatch_receipt.json').exists(),'No automatic re-run')
    require(read(ROOT/'work/S24_execution/dispatch_receipt.json')['status']=='PASS','Finish existing S24 before new GA')
    WORK.mkdir(parents=True,exist_ok=True)
    r=dict(status='RUNNING',started_utc=utc(),manifest_sha256=expected,phases=[])
    write(WORK/'dispatch_receipt.json',r)
    try:
        phases=[('control',180,2),*((f'views_{v}',180,2) for v in m['preprocess_repos']),('compat',240,4),
                ('common_old',600,16),('cut3r',1200,16),('ttt3r',1200,16),('filt3r',1200,16)]
        for phase,seconds,gib in phases:
            command=[sys.executable,str(Path(__file__).resolve()),'worker','--phase',phase,'--manifest-sha256',expected]
            supervised(command,phase,seconds,gib*1024**3)
            r['phases'].append(phase);write(WORK/'dispatch_receipt.json',r)
        command=[sys.executable,str(ROOT/'scripts/score_s26_consumer.py'),'score','--manifest',str(MANIFEST),'--manifest-sha256',expected]
        supervised(command,'scoring',180,2*1024**3)
        r.update(status='PASS',completed_utc=utc());write(WORK/'dispatch_receipt.json',r)
    except BaseException as e:
        r.update(status='FAILED',failed_utc=utc(),error=str(e));write(WORK/'dispatch_receipt.json',r);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['dispatch','worker']);p.add_argument('--phase')
    p.add_argument('--manifest-sha256',required=True);args=p.parse_args()
    m=manifest(args.manifest_sha256)
    if args.command=='dispatch':dispatch(m,args.manifest_sha256)
    elif args.phase=='control':control_input(m)
    elif args.phase=='compat':compatibility(m)
    elif args.phase.startswith('views_'):source_views(m,args.phase[6:])
    elif args.phase in MODES:ga_worker(m,args.phase)
    else:raise ValueError('Unknown phase')
