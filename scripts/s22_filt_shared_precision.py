"""S22 official FILT3R baseline; derived from frozen S21 runner with recorded diff."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, ast, contextlib, copy, hashlib, io, json, os, resource, subprocess, sys, time, traceback
ROOT=Path(__file__).resolve().parents[1]
W=ROOT/'work/S22_filt_shared_precision'
REPO=W/'filt3r_shared_precision'
ORIGINAL=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local')
DATA=ROOT/'data/tum/fr2_desk_download/extracted/rgbd_dataset_freiburg2_desk'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def definitions(path,names,namespace):
    tree=ast.parse(Path(path).read_text())
    nodes=[n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
    return namespace
def prepare():
    target=W/'run_manifest.json';assert not target.exists()
    old=json.loads((ROOT/'work/S21_baseline_preparation/run_manifest.json').read_text())
    source=json.loads((W/'source_manifest_v2.json').read_text());assert source['passed']
    for e in source['files']:assert sha(REPO/e['path'])==e['sha256']
    tree=ast.parse((REPO/'eval/relpose/launch.py').read_text());hparams=None
    for n in tree.body:
        if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='FILT3R_DEFAULT_HPARAMS'for t in n.targets):hparams=ast.literal_eval(n.value)
    assert hparams and hparams['kalman_tau_q']==3.0
    paths=[Path(__file__),ROOT/'scripts/cut3r_rope_compat.py',ROOT/'docs/S22_FILT_SHARED_PRECISION_PROTOCOL.md',W/'source_manifest_v2.json',ROOT/'work/S21_baseline_preparation/run_manifest.json']
    paths += [REPO/e['path']for e in source['files']]
    m=copy.deepcopy(old);m.update(schema='s22-filt-shared-precision-v2',frozen_utc=utc(),methods=['filt3r'],compatibility_prefix=4,hparams=hparams,identities={str(p.resolve()):sha(p)for p in paths})
    m['contract'].pop('gt_numeric_scoring_after_both_sealed',None)
    m['contract']['gt_numeric_scoring_after_current_method_sealed']=True
    m['contract']['rope_encoder_qk_dtype']='float16, matching original CUT3R/TTT3R; outer weights/inputs FP32'
    m['S21_scoring_available_at_freeze']=True
    write(target,m);print(json.dumps(dict(manifest=str(target),sha256=sha(target),frames=len(m['frames']),frozen=m['frozen_utc'])))
def run(mode,out):
    assert mode in {'cut3r4','filt3r'}
    assert not out.exists();out.mkdir(parents=True)
    m=json.loads((W/'run_manifest.json').read_text());r=dict(started_utc=utc(),status='RUNNING',mode=mode,frames_completed=0,manifest_sha256=sha(W/'run_manifest.json'))
    write(out/'receipt.json',r)
    try:
        for p,h in m['identities'].items():assert sha(p)==h,p
        cp=Path(m['checkpoint']);assert [cp.stat().st_size,cp.stat().st_mtime_ns]==m['checkpoint_stat']
        repo=REPO
        sys.path[:0]=[str(repo/'src'),str(repo/'src/croco'),str(ROOT/'scripts')]
        import numpy as np,torch
        from typing import Any
        from collections import defaultdict
        from omegaconf import DictConfig
        from omegaconf.base import ContainerMetadata,Metadata
        from omegaconf.nodes import AnyNode
        from dust3r.model import ARCroco3DStereo
        from dust3r.utils.image import load_images_for_eval
        from dust3r.utils.camera import pose_encoding_to_camera
        from models.pos_embed import RoPE2D
        import cut3r_rope_compat
        cut3r_rope_compat.install(RoPE2D)
        torch.set_num_threads(8);torch.manual_seed(0);np.random.seed(0)
        frames=m['frames'][:4]if mode=='cut3r4'else m['frames']
        for e in frames:assert sha(e['path'])==e['sha256']
        ns=definitions(REPO/'eval/relpose/launch.py',['prepare_input'],dict(torch=torch,np=np,load_images=load_images_for_eval,deepcopy=copy.deepcopy))
        views=ns['prepare_input']([e['path']for e in frames],[True]*len(frames),size=512,crop=True,revisit=1,update=True)
        assert len(views)==len(frames)and all(list(v['img'].shape)==[1,3,384,512]for v in views)
        allowed=[DictConfig,ContainerMetadata,Any,dict,defaultdict,AnyNode,Metadata]
        unsafe=torch.serialization.get_unsafe_globals_in_checkpoint(cp)
        assert set(unsafe)<={f'{x.__module__}.{x.__qualname__}'for x in allowed}
        log=io.StringIO();start=time.perf_counter()
        with contextlib.redirect_stdout(log),torch.serialization.safe_globals(allowed):model=ARCroco3DStereo.from_pretrained(str(cp)).float().to('cpu')
        (out/'checkpoint_load.txt').write_text(log.getvalue());assert 'All keys matched successfully'in log.getvalue()
        model.config.model_update_type='cut3r'if mode=='cut3r4'else 'filt3r'
        if mode=='filt3r':
            if not hasattr(model,'hparams')or not isinstance(model.hparams,dict):model.hparams={}
            model.hparams.update(m['hparams'])
            for key,value in m['hparams'].items():
                if hasattr(model.config,key):setattr(model.config,key,value)
            r['official_hparam_overrides']=m['hparams']
        assert model._resolve_model_update_type()==('cut3r'if mode=='cut3r4'else'filt3r')
        r['actual_policy']=model._resolve_model_update_type()
        r['resolved_filt_hparams']={k:model._get_hparam(k)for k in list(m['hparams'])+['kalman_k_min','kalman_k_max']}
        r.update(model_load_seconds=time.perf_counter()-start,training_flag=model.training,parameters=sum(p.numel()for p in model.parameters()),
                 stochastic_modules=[dict(name=n,type=type(x).__name__,p=float(getattr(x,'p',getattr(x,'drop_prob',0))))for n,x in model.named_modules()if isinstance(x,torch.nn.Dropout)and x.p>0],
                 batchnorm_modules=[n for n,x in model.named_modules()if isinstance(x,torch.nn.modules.batchnorm._BatchNorm)],
                 actual_source=str(repo),torch_version=torch.__version__,numpy_version=np.__version__,weights_only=True)
        poses=[];input_ids=[];saved=[];forward_start=time.perf_counter()
        gain_events=[]
        original_gain=model._compute_kalman_ema_gain_and_cov
        def observed_gain(*a,**kw):
            returned=original_gain(*a,**kw)
            gain,cov,_=returned
            event=dict(frame_index=len(saved)-1,affects='subsequent recurrent state; current head was already emitted',mean_gain=float(gain.mean()),min_gain=float(gain.min()),max_gain=float(gain.max()),mean_covariance=float(cov.mean()))
            gain_events.append(event)
            with (out/'gain_events.jsonl').open('a')as f:f.write(json.dumps(event)+'\n')
            return returned
        model._compute_kalman_ema_gain_and_cov=observed_gain
        def hook(module,inputs,result):
            i=len(saved);arrays={k:v.detach().cpu().numpy().copy()for k,v in result.items()if torch.is_tensor(v)}
            assert set(arrays)=={'pts3d_in_self_view','pts3d_in_other_view','conf_self','conf','camera_pose','rgb'}
            path=out/f'frame_{i:04d}.npz';np.savez_compressed(path,**arrays)
            saved.append(dict(index=i,file=path.name,sha256=sha(path)))
            assert all(np.isfinite(a).all()for a in arrays.values())
            poses.append(pose_encoding_to_camera(result['camera_pose'].clone()).detach().cpu().numpy()[0])
            r.update(frames_completed=len(saved),last_frame_utc=utc(),elapsed_forward_with_archival_seconds=time.perf_counter()-forward_start)
            write(out/'receipt.json',r)
            if len(saved)%25==0 or len(saved)==len(frames):print(json.dumps(dict(mode=mode,frames=len(saved),seconds=r['elapsed_forward_with_archival_seconds'])),flush=True)
        h=model.downstream_head.register_forward_hook(hook)
        from dust3r.inference import inference_recurrent_lighter
        outputs,_=inference_recurrent_lighter(views,model,'cpu',verbose=False)
        h.remove();assert len(saved)==len(frames)==len(outputs['pred'])
        assert len(gain_events)==(299 if mode=='filt3r'else 0)
        r['gain_update_calls']=len(gain_events)
        np.save(out/'poses.npy',np.stack(poses))
        r.update(status='PASS',completed_utc=utc(),peakrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,outputs=saved,
                 poses_sha256=sha(out/'poses.npy'),frames_expected=len(frames),gt_coordinates_used=False,
                 forward_with_archival_seconds=time.perf_counter()-forward_start)
        write(out/'receipt.json',r);print(json.dumps({k:v for k,v in r.items()if k not in {'outputs','stochastic_modules','batchnorm_modules'}}),flush=True)
    except BaseException as e:
        r.update(status='FAILED',error=repr(e),traceback=traceback.format_exc(),completed_utc=utc());write(out/'receipt.json',r);raise
def dispatch():
    sys.path.append(str(ROOT/'work/S17C_environment/site-packages'))
    import psutil
    m=json.loads((W/'run_manifest.json').read_text())
    for mode in ['cut3r4','filt3r']:
        out=ROOT/'results/S22_filt_shared_precision'/mode;out.parent.mkdir(parents=True,exist_ok=True)
        assert not out.exists()
        control=ROOT/'work/S22_shared_execution'/mode;control.mkdir(parents=True,exist_ok=False)
        cmd=[sys.executable,str(Path(__file__).resolve()),'run','--mode',mode,'--output',str(out)]
        r=dict(started_utc=utc(),command=cmd,status='RUNNING',peak_tree_rss=0,limits=m['contract'])
        start=time.monotonic()
        with (control/'stdout.txt').open('w')as stdout,(control/'stderr.txt').open('w')as stderr:
            p=subprocess.Popen(cmd,stdout=stdout,stderr=stderr);r['pid']=p.pid
            while p.poll()is None:
                try:
                    parent=psutil.Process(p.pid);rss=sum(x.memory_info().rss for x in [parent]+parent.children(recursive=True));r['peak_tree_rss']=max(rss,r['peak_tree_rss'])
                except psutil.NoSuchProcess:continue
                if time.monotonic()-start>1800 or r['peak_tree_rss']>32*1024**3:
                    r['failure']='resource limit';p.terminate();p.wait(timeout=10);break
                write(control/'receipt.json',r);time.sleep(1)
            r.update(returncode=p.wait(),elapsed_seconds=time.monotonic()-start,completed_utc=utc())
        r['status']='PASS'if r['returncode']==0 and 'failure'not in r else 'FAILED';write(control/'receipt.json',r)
        print(json.dumps(dict(mode=mode,status=r['status'],elapsed_seconds=r['elapsed_seconds'])),flush=True)
        if r['status']!='PASS':raise RuntimeError(mode+' failed; retained output, no automatic rerun')
        if mode=='cut3r4':
            import numpy as np
            checks=[]
            for i in range(4):
                with np.load(ROOT/'results/S21_baseline/original4'/f'frame_{i:04d}.npz')as x,np.load(out/f'frame_{i:04d}.npz')as y:
                    assert set(x.files)==set(y.files)
                    for key in x.files:
                        atol=1e-4 if key=='camera_pose'else 5e-4
                        checks.append(dict(frame=i,head=key,atol=atol,rtol=1e-4,max_abs=float(np.max(np.abs(x[key]-y[key]))),passed=bool(np.allclose(x[key],y[key],atol=atol,rtol=1e-4))))
            verdict=dict(utc=utc(),passed=all(c['passed']for c in checks),checks=checks,gt_coordinates_read=False)
            write(out.parent/'compatibility.json',verdict)
            assert verdict['passed'],'Keep incompatibility; do not run 300-frame FILT3R yet'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','dispatch']);p.add_argument('--mode');p.add_argument('--output',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='run':run(a.mode,a.output)
    else:dispatch()
