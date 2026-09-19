"""S24 complete additional real sequence. Existing methods, no new algorithm.
The run() body derives from S22 with manifest-selected source and FILT-only hooks.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, ast, contextlib, copy, hashlib, io, json, os, resource, shutil, subprocess, sys, time, traceback
ROOT=Path(__file__).resolve().parents[1]
W=ROOT/'work/S24_baseline_expansion'
B=ROOT/'results/S24_baseline_expansion'
SOURCES={'cut3r':ROOT/'work/S21_baseline_preparation/ttt3r_original',
         'ttt3r':ROOT/'work/S21_baseline_preparation/ttt3r_original',
         'filt3r':ROOT/'work/S22_filt_shared_precision/filt3r_shared_precision'}
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
    candidate=json.loads((W/'candidate_inputs.json').read_text())
    assert candidate['status']=='DATA_CANDIDATE_ONLY_NOT_RUN_OR_FROZEN'
    paths=[Path(__file__),ROOT/'scripts/score_s24_baseline.py',ROOT/'scripts/cut3r_rope_compat.py',
           ROOT/'docs/S24_BASELINE_EXPANSION_PROTOCOL.md',W/'candidate_inputs.json',
           W/'independent_input_review.json',W/'independent_pre_review.json',
           ROOT/'work/S21_baseline_preparation/run_manifest.json',
           ROOT/'results/S21_baseline/compatibility.json',
           ROOT/'results/S22_filt_shared_precision/compatibility.json']
    review=json.loads((W/'independent_pre_review.json').read_text())
    assert review['passed']
    for p,h in review['reviewed_identities'].items():assert sha(p)==h,p
    assert json.loads(paths[-1].read_text())['passed'] and json.loads(paths[-2].read_text())['passed']
    for rel,repo in [('work/S21_baseline_preparation/source_manifest_v3.json',SOURCES['cut3r']),
                     ('work/S22_filt_shared_precision/source_manifest_v2.json',SOURCES['filt3r'])]:
        manifest=ROOT/rel;source=json.loads(manifest.read_text());assert source['passed'];paths.append(manifest)
        for e in source['files']:
            p=repo/e['path'];assert sha(p)==e['sha256'];paths.append(p)
    launch=SOURCES['filt3r']/'eval/relpose/launch.py'
    hp=[ast.literal_eval(n.value)for n in ast.parse(launch.read_text()).body
        if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='FILT3R_DEFAULT_HPARAMS'for t in n.targets)]
    assert len(hp)==1 and hp[0]['kalman_tau_q']==3.0
    frames=[dict(index=e['index'],rgb_time=e['rgb_time'],gt_time=e['gt_time'],path=e['rgb_file'],sha256=sha(e['rgb_file'])) for e in candidate['frames']]
    assert len(frames)==candidate['rgb_gt_pairs']==796
    assert [x['index']for x in frames]==list(range(len(frames)))
    assert len({x['rgb_time']for x in frames})==len({x['gt_time']for x in frames})==len(frames)
    assert all(abs(x['rgb_time']-x['gt_time'])<.02 for x in frames)
    assert all(frames[i]['rgb_time']<frames[i+1]['rgb_time'] and frames[i]['gt_time']<frames[i+1]['gt_time']for i in range(len(frames)-1))
    cp=Path(old['checkpoint']);assert [cp.stat().st_size,cp.stat().st_mtime_ns]==old['checkpoint_stat']
    gt=ROOT/'data/tum/rgbd_dataset_freiburg1_xyz/groundtruth.txt'
    contract=dict(size=512,crop=True,frames=len(frames),threads=8,seed=0,device='cpu',
                  outer_dtype='float32',encoder_rope_qk_dtype='float16',revisit=1,update=True,reset=False,
                  solve_pose=False,max_seconds_per_method=3600,max_rss_bytes=48*1024**3,
                  min_free_disk_bytes=30*1024**3,all_three_sealed_before_gt_coordinate_scoring=True,
                  no_tuning=True,metric_atol=1e-6,metric_rtol=1e-5,block_size=100)
    m=dict(schema='s24-full-sequence-v1',frozen_utc=utc(),methods=['cut3r','ttt3r','filt3r'],
           sources={k:str(v)for k,v in SOURCES.items()},frames=frames,scope=candidate['source_scene'],
           span_seconds=candidate['span_seconds'],hparams=hp[0],contract=contract,
           identities={**review['reviewed_identities'],**{str(p.resolve()):sha(p)for p in paths}},gt_file=str(gt),gt_sha256=sha(gt),
           previously_exposed=True,new_method=False,old_s21_s22_s23_scores_available=True,
           gt_access_note='GT bytes and timestamps read during association; no S24 numeric coordinates parsed before sealed predictions. Earlier project GT exposure exists.')
    for key in ['checkpoint','checkpoint_sha256','checkpoint_identity_basis','checkpoint_stat']:m[key]=old[key]
    assert shutil.disk_usage(ROOT).free>=contract['min_free_disk_bytes']
    write(target,m);print(json.dumps(dict(manifest=str(target),sha256=sha(target),frames=len(frames),frozen=m['frozen_utc'])))

def run(mode,out):
    assert mode in {'cut3r','ttt3r','filt3r'}
    assert not out.exists();out.mkdir(parents=True)
    m=json.loads((W/'run_manifest.json').read_text());r=dict(started_utc=utc(),status='RUNNING',mode=mode,frames_completed=0,manifest_sha256=sha(W/'run_manifest.json'))
    write(out/'receipt.json',r)
    try:
        for p,h in m['identities'].items():assert sha(p)==h,p
        cp=Path(m['checkpoint']);assert [cp.stat().st_size,cp.stat().st_mtime_ns]==m['checkpoint_stat']
        repo=Path(m['sources'][mode])
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
        frames=m['frames']
        for e in frames:assert sha(e['path'])==e['sha256']
        ns=definitions(repo/'eval/relpose/launch.py',['prepare_input'],dict(torch=torch,np=np,load_images=load_images_for_eval,deepcopy=copy.deepcopy))
        views=ns['prepare_input']([e['path']for e in frames],[True]*len(frames),size=512,crop=True,revisit=1,update=True)
        assert len(views)==len(frames)and all(list(v['img'].shape)==[1,3,384,512]for v in views)
        allowed=[DictConfig,ContainerMetadata,Any,dict,defaultdict,AnyNode,Metadata]
        unsafe=torch.serialization.get_unsafe_globals_in_checkpoint(cp)
        assert set(unsafe)<={f'{x.__module__}.{x.__qualname__}'for x in allowed}
        log=io.StringIO();start=time.perf_counter()
        with contextlib.redirect_stdout(log),torch.serialization.safe_globals(allowed):model=ARCroco3DStereo.from_pretrained(str(cp)).float().to('cpu')
        (out/'checkpoint_load.txt').write_text(log.getvalue());assert 'All keys matched successfully'in log.getvalue()
        model.config.model_update_type=mode
        if mode=='filt3r':
            if not hasattr(model,'hparams')or not isinstance(model.hparams,dict):model.hparams={}
            model.hparams.update(m['hparams'])
            for key,value in m['hparams'].items():
                if hasattr(model.config,key):setattr(model.config,key,value)
            r['official_hparam_overrides']=m['hparams']
        if mode=='filt3r':
            assert model._resolve_model_update_type()==mode
            r['resolved_filt_hparams']={k:model._get_hparam(k)for k in list(m['hparams'])+['kalman_k_min','kalman_k_max']}
        else:
            assert model.config.model_update_type==mode
        r['actual_policy']=mode
        r.update(model_load_seconds=time.perf_counter()-start,training_flag=model.training,parameters=sum(p.numel()for p in model.parameters()),
                 stochastic_modules=[dict(name=n,type=type(x).__name__,p=float(getattr(x,'p',getattr(x,'drop_prob',0))))for n,x in model.named_modules()if isinstance(x,torch.nn.Dropout)and x.p>0],
                 batchnorm_modules=[n for n,x in model.named_modules()if isinstance(x,torch.nn.modules.batchnorm._BatchNorm)],
                 actual_source=str(repo),torch_version=torch.__version__,numpy_version=np.__version__,weights_only=True)
        assert not r['stochastic_modules'] and not r['batchnorm_modules']
        poses=[];saved=[];forward_start=time.perf_counter()
        gain_events=[]
        if mode=='filt3r':
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
        assert len(gain_events)==(len(frames)-1 if mode=='filt3r'else 0)
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
    m=json.loads((W/'run_manifest.json').read_text());c=m['contract']
    for mode in m['methods']:
        out=B/mode;out.parent.mkdir(parents=True,exist_ok=True)
        assert not out.exists()
        assert shutil.disk_usage(ROOT).free>=c['min_free_disk_bytes']
        control=ROOT/'work/S24_execution'/mode;control.mkdir(parents=True,exist_ok=False)
        cmd=[sys.executable,str(Path(__file__).resolve()),'run','--mode',mode,'--output',str(out)]
        r=dict(started_utc=utc(),command=cmd,status='RUNNING',peak_tree_rss=0,limits=c,
               manifest_sha256=sha(W/'run_manifest.json'))
        start=time.monotonic()
        with (control/'stdout.txt').open('w')as stdout,(control/'stderr.txt').open('w')as stderr:
            p=subprocess.Popen(cmd,stdout=stdout,stderr=stderr);r['pid']=p.pid
            while p.poll()is None:
                try:
                    parent=psutil.Process(p.pid)
                    rss=sum(x.memory_info().rss for x in [parent]+parent.children(recursive=True))
                    r['peak_tree_rss']=max(rss,r['peak_tree_rss'])
                except psutil.NoSuchProcess:
                    continue
                if time.monotonic()-start>c['max_seconds_per_method'] or r['peak_tree_rss']>c['max_rss_bytes']:
                    r['failure']='resource limit';p.terminate()
                    try:p.wait(timeout=10)
                    except subprocess.TimeoutExpired:p.kill();p.wait()
                    break
                write(control/'receipt.json',r);time.sleep(1)
            r.update(returncode=p.wait(),elapsed_seconds=time.monotonic()-start,completed_utc=utc())
        r['status']='PASS'if r['returncode']==0 and 'failure'not in r else 'FAILED';write(control/'receipt.json',r)
        print(json.dumps(dict(mode=mode,status=r['status'],elapsed_seconds=r['elapsed_seconds'])),flush=True)
        if r['status']!='PASS':raise RuntimeError(mode+' failed; preserved, no automatic rerun or score')
    scorer=ROOT/'scripts/score_s24_baseline.py'
    assert sha(scorer)==m['identities'][str(scorer)]
    scored=subprocess.run([sys.executable,str(scorer),'score'],capture_output=True,text=True)
    ctrl=ROOT/'work/S24_execution';(ctrl/'scoring_stdout.txt').write_text(scored.stdout);(ctrl/'scoring_stderr.txt').write_text(scored.stderr)
    write(ctrl/'dispatch_receipt.json',dict(completed_utc=utc(),status='PASS'if scored.returncode==0 else'FAILED_SCORING',score_returncode=scored.returncode,manifest_sha256=sha(W/'run_manifest.json')))
    if scored.returncode:raise RuntimeError('S24 scoring failed; retain predictions and error')
    print('All three actual runs and post-seal scoring completed.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','dispatch']);p.add_argument('--mode');p.add_argument('--output',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='run':run(a.mode,a.output)
    else:dispatch()
