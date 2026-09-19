"""S21 frozen local CUT3R/TTT3R trajectory probe; source functions remain intact."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, ast, contextlib, copy, hashlib, io, json, os, resource, subprocess, sys, time, traceback
ROOT=Path(__file__).resolve().parents[1]
W=ROOT/'work/S21_baseline_preparation'
REPO=W/'ttt3r_original'
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
    source=json.loads((W/'source_manifest_v3.json').read_text());assert source['passed']
    for e in source['files']:assert sha(REPO/e['path'])==e['sha256']
    assert (REPO/'src/croco/models/pos_embed.py').read_bytes()==(ORIGINAL/'src/croco/models/pos_embed.py').read_bytes()
    def rows(p):return [s.split() for s in p.read_text().splitlines()if s.strip() and not s.startswith('#')]
    # Only timestamps and RGB paths are used here; GT coordinate strings are not parsed.
    rgb={float(r[0]):r[1]for r in rows(DATA/'rgb.txt')}
    gt={float(r[0]):None for r in rows(DATA/'groundtruth.txt')}
    f=definitions(REPO/'datasets_preprocess/long_prepare_tum.py',['associate'],{})['associate']
    pairs=f(rgb,gt,0.0,0.02)[:300];assert len(pairs)==300
    frames=[dict(index=i,rgb_time=a,gt_time=b,path=str(DATA/rgb[a]),sha256=sha(DATA/rgb[a]))for i,(a,b)in enumerate(pairs)]
    assert [e['path']for e in frames]==sorted(e['path']for e in frames)
    paths=[Path(__file__),ROOT/'scripts/cut3r_rope_compat.py',ROOT/'docs/S21_BASELINE_PROTOCOL.md',W/'source_manifest_v3.json']
    paths += [REPO/e['path']for e in source['files']]
    paths += list((ORIGINAL/'src').rglob('*.py'))
    checkpoint=ROOT/'data/cut3r/cut3r_512_dpt_4_64.pth'
    assert checkpoint.stat().st_size==3173761006
    m=dict(schema='s21-baseline-v1',frozen_utc=utc(),frames=frames,methods=['cut3r','ttt3r'],original_prefix=4,
           checkpoint=str(checkpoint),checkpoint_sha256='45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103',
           checkpoint_identity_basis='S17 verified SHA; size and stat recorded here; no redundant multi-GB hash',
           checkpoint_stat=[checkpoint.stat().st_size,checkpoint.stat().st_mtime_ns],
           gt_file=str(DATA/'groundtruth.txt'),gt_sha256=sha(DATA/'groundtruth.txt'),
           identities={str(p.resolve()):sha(p)for p in paths},
           contract=dict(size=512,crop=True,frames=300,threads=8,seed=0,device='cpu',dtype='float32',revisit=1,solve_pose=False,
                         max_seconds=1800,max_rss_bytes=32*1024**3,gt_numeric_scoring_after_both_sealed=True))
    write(target,m);print(json.dumps(dict(manifest=str(target),sha256=sha(target),frames=len(frames),frozen=m['frozen_utc'])))
def run(mode,out):
    assert not out.exists();out.mkdir(parents=True)
    m=json.loads((W/'run_manifest.json').read_text());r=dict(started_utc=utc(),status='RUNNING',mode=mode,frames_completed=0,manifest_sha256=sha(W/'run_manifest.json'))
    write(out/'receipt.json',r)
    try:
        for p,h in m['identities'].items():assert sha(p)==h,p
        cp=Path(m['checkpoint']);assert [cp.stat().st_size,cp.stat().st_mtime_ns]==m['checkpoint_stat']
        repo=ORIGINAL if mode=='original4' else REPO
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
        frames=m['frames'][:4]if mode=='original4'else m['frames']
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
        if mode!='original4':model.config.model_update_type=mode
        r.update(model_load_seconds=time.perf_counter()-start,training_flag=model.training,parameters=sum(p.numel()for p in model.parameters()),
                 stochastic_modules=[dict(name=n,type=type(x).__name__,p=float(getattr(x,'p',getattr(x,'drop_prob',0))))for n,x in model.named_modules()if isinstance(x,torch.nn.Dropout)and x.p>0],
                 batchnorm_modules=[n for n,x in model.named_modules()if isinstance(x,torch.nn.modules.batchnorm._BatchNorm)],
                 actual_source=str(repo),torch_version=torch.__version__,numpy_version=np.__version__,weights_only=True)
        poses=[];input_ids=[];saved=[];forward_start=time.perf_counter()
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
        if mode=='original4':
            from dust3r.inference import inference_recurrent
            outputs,_=inference_recurrent(views,model,'cpu',verbose=False)
        else:
            from dust3r.inference import inference_recurrent_lighter
            outputs,_=inference_recurrent_lighter(views,model,'cpu',verbose=False)
        h.remove();assert len(saved)==len(frames)==len(outputs['pred'])
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
    for mode in ['original4','cut3r','ttt3r']:
        out=ROOT/'results/S21_baseline'/mode;out.parent.mkdir(parents=True,exist_ok=True)
        assert not out.exists()
        control=ROOT/'work/S21_execution'/mode;control.mkdir(parents=True,exist_ok=False)
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
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','dispatch']);p.add_argument('--mode');p.add_argument('--output',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='run':run(a.mode,a.output)
    else:dispatch()
