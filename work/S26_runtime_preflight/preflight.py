"""Bounded synthetic interface preflight. Never invokes a real GA or network.

Parent launches a fresh CPU1 worker and enforces 60 s / 1 GiB process-tree RSS.
The two explicit thread-report shims exercise CPU8-only interface guards while
keeping actual PyTorch threads at one; this is not CPU8 numerical validation.
"""
from __future__ import annotations
import ast
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNNER = ROOT / 'scripts/s26_consumer_baseline.py'
ADAPTER = ROOT / 'work/S26_consumer_baseline_preparation/saved_heads_adapter.py'
WRAPPER = ROOT / 'work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/surfel_inference.py'
BASELINE = ROOT / 'work/S21_baseline_preparation/ttt3r_original/eval/relpose/launch.py'


def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, value): Path(p).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
def require(ok, why):
    if not ok: raise AssertionError(why)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def worker():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    checks = []
    report = dict(status='RUNNING', started_utc=utc(), checks=checks,
                  model_instantiations=0, model_forwards=0, real_GA_calls=0,
                  optimizer_instantiations=0, real_RGB_NPZ_GT_reads=0,
                  synthetic_only=True, numerical_GA_compatibility='NOT_TESTED')
    identities = {str(p): sha(p) for p in (RUNNER, ADAPTER, WRAPPER, BASELINE, Path(__file__))}
    report['reviewed_identities'] = identities

    def audit(event, args):
        if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
            candidate = Path(os.fsdecode(args[0])).resolve()
            if candidate.is_relative_to(ROOT/'data') or candidate.is_relative_to(ROOT/'results'):
                raise RuntimeError('Real experimental data access forbidden in preflight')
        if event in ('socket.connect', 'socket.connect_ex'):
            raise RuntimeError('Network access forbidden in preflight')
    sys.addaudithook(audit)

    try:
        runner = load_module('s26_preflight_runner', RUNNER)
        adapter = load_module('s26_preflight_adapter', ADAPTER)
        require('torch' not in sys.modules and 'numpy' not in sys.modules,
                'Importing runner/adapter must not eagerly initialize numerical runtime')
        checks.append('runner_and_adapter_import_without_numerical_or_data_side_effect')

        tree = ast.parse(BASELINE.read_text())
        found = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'prepare_input']
        require(len(found) == 1, 'Unique nested baseline prepare_input')
        require(not any(n is found[0] for n in tree.body), 'Fixture must expose prior nested-AST bug')
        compile(ast.Module(body=found, type_ignores=[]), str(BASELINE), 'exec')
        runner_ast = ast.parse(RUNNER.read_text())
        fn = next(n for n in runner_ast.body if isinstance(n, ast.FunctionDef) and n.name == 'source_views')
        require(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and isinstance(n.func.value, ast.Name) and n.func.value.id == 'ast'
                    and n.func.attr == 'walk' for n in ast.walk(fn)), 'Runner uses ast.walk')
        checks.append('nested_baseline_prepare_input_unique_and_compiles')
        original = ast.parse(WRAPPER.read_text())
        names = ('listify', 'collate_with_cat', 'prepare_input_from_pil', 'prepare_output', 'run_inference_from_pil')
        require(all(sum(isinstance(n, ast.FunctionDef) and n.name == name for n in original.body)==1 for name in names),
                'Original wrapper function identities unique')
        _, proof = adapter.derive_original_functions(WRAPPER.read_text())
        report['original_ast_proof'] = proof
        checks.append('original_wrapper_functions_unique_and_unchanged_AST_derivation_compiles')

        sig = inspect.signature(adapter.CommonOldDepth)
        require(list(sig.parameters) == ['values','original4_ga_seal_sha256','expected_depth_tensor_sha256',
                                        'control_pose_prefix_tensor_sha256','provenance_kind'], 'Dataclass signature')
        require(list(inspect.signature(adapter.run_original_ga).parameters) ==
                ['namespace','output','control_c2ws','old_depth','output_dir'], 'GA adapter signature')
        checks.append('adapter_and_CommonOldDepth_signatures')

        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        real_set_threads = torch.set_num_threads
        requested_threads = []
        def cap_threads(n):
            requested_threads.append(n)
            require(n == 8, 'Unchanged runner CPU8 request expected')
            return real_set_threads(1)
        torch.set_num_threads = cap_threads
        try:
            np, returned_torch = runner.numeric_setup()
        finally:
            torch.set_num_threads = real_set_threads
        import cv2
        cv2.setNumThreads(1)
        require(returned_torch is torch and torch.get_num_threads()==1 and torch.get_num_interop_threads()==1,
                'Actual CPU1 maintained')
        report['numeric_packages'] = {name: {'version': mod.__version__, 'path': str(mod.__file__)}
                                      for name,mod in [('numpy',np),('torch',torch),('cv2',cv2)]}
        report['preflight_thread_shims'] = dict(numeric_setup_requested_threads=requested_threads,
            actual_torch_threads=1, actual_torch_interop_threads=1,
            adapter_guard_report_only=8, explanation='CPU1 preflight only; not CPU8 numerical verification')
        checks.append('numeric_setup_imports_versions_seeds_with_explicit_CPU1_cap')

        # Nontrivial analytic camera; no GT coordinate enters this calculation.
        angle = np.float32(.37)
        c,s = np.cos(angle),np.sin(angle)
        camera = np.eye(4, dtype=np.float32)
        camera[:3,:3] = [[c,-s,0],[s,c,0],[0,0,1]]
        camera[:3,3] = [.25,-.4,1.2]
        flip = np.diag(np.array([1,-1,-1,1],dtype=np.float32))
        pipeline = camera @ flip
        recovered = pipeline.copy(); recovered[:3,1:3] *= -1
        require(np.array_equal(recovered,camera), 'Optical/pipeline flip exact analytic roundtrip')
        require(np.allclose(camera[:3,:3].T@camera[:3,:3],np.eye(3),atol=1e-7), 'SO3 analytic input')
        require(float(np.linalg.det(camera[:3,:3]))>0, 'Proper optical rotation')
        checks.append('nontrivial_analytic_optical_pipeline_flip_roundtrip')

        cams8 = torch.from_numpy(np.repeat(camera[None], 8, axis=0))
        depth = torch.linspace(1.,2.,4*384*512).reshape(4,384,512)
        packet = adapter.CommonOldDepth(depth, 'a'*64, adapter.tensor_sha256(depth),
                                       adapter.tensor_sha256(cams8[:4]))
        require(adapter.tensor_sha256(depth.clone())==packet.expected_depth_tensor_sha256,
                'Synthetic content hash reproducible')
        try:
            packet.provenance_kind = 'altered'
        except FrozenInstanceError:
            checks.append('CommonOldDepth_metadata_is_frozen')
        else: raise AssertionError('Frozen dataclass unexpectedly mutable')

        spy_calls = []
        def prepare_output_spy(*args, **kwargs):
            # Does not instantiate a scene, optimize, or invoke any source GA.
            spy_calls.append((args,kwargs))
            return 'SPY_ONLY_NO_GA'
        def probe(n, prior, cams=None):
            return adapter.run_original_ga({'prepare_output':prepare_output_spy},
                {'view2':{'idx':list(range(1,n))}}, control_c2ws=cams8[:n] if cams is None else cams,
                old_depth=prior, output_dir=HERE/'NEVER_CREATED')
        real_get_threads = torch.get_num_threads
        torch.get_num_threads = lambda:8  # Guard-only report. Native thread count remains one.
        try:
            require(probe(4,None)=='SPY_ONLY_NO_GA', 'Valid common4 delegates')
            require(probe(8,packet)=='SPY_ONLY_NO_GA', 'Valid shared old4/eight delegates')
            require(len(spy_calls)==2, 'Only two accepted synthetic dispatches')
            for args,kwargs in spy_calls:
                require(kwargs==dict(lr=.01,niter=400,outdir=str(HERE/'NEVER_CREATED'),device='cpu',save_flag=False),
                        'Original fixed call configuration')
            checks.append('valid_synthetic_4_and_8_delegate_to_spy_with_original_call_configuration')
            def reject(label, callback, fragment):
                before=len(spy_calls)
                try: callback()
                except RuntimeError as error:
                    require(fragment in str(error), label+' correct rejection')
                else: raise AssertionError(label+' unexpectedly accepted')
                require(len(spy_calls)==before, label+' rejected before spy')
                checks.append(label)
            reject('four_rejects_prior',lambda:probe(4,packet),'must have no depth prior')
            reject('eight_requires_prior',lambda:probe(8,None),'requires the common old')
            reject('depth_content_sha_rejects_tamper',lambda:probe(8,replace(packet,expected_depth_tensor_sha256='b'*64)),
                   'content differs')
            reject('pose_prefix_sha_rejects_tamper',lambda:probe(8,replace(packet,control_pose_prefix_tensor_sha256='b'*64)),
                   'different prefix camera')
            changed_cams = cams8.clone(); changed_cams[0,0,3] += .1
            reject('actual_pose_prefix_change_rejected',lambda:probe(8,packet,changed_cams),'different prefix camera')
            depth[0,0,0] += .1
            reject('mutable_tensor_tamper_rejected',lambda:probe(8,packet),'content differs')
            depth[0,0,0] = 0
            reject('nonpositive_depth_rejected',lambda:probe(8,packet),'Invalid common old-depth tensor')
            reject('wrong_depth_shape_rejected',lambda:probe(8,replace(packet,values=depth[:3])),
                   'Invalid common old-depth tensor')
            reject('wrong_depth_dtype_rejected',lambda:probe(8,replace(packet,values=depth.double())),
                   'Invalid common old-depth tensor')
            reject('wrong_camera_dtype_rejected',lambda:probe(8,packet,cams8.double()),'CPU FP32')
            reject('wrong_camera_count_rejected',lambda:probe(8,packet,cams8[:4]),'complete prefix')
            reject('provenance_kind_rejected',lambda:probe(8,replace(packet,provenance_kind='sensor_depth')),
                   'sealed original CUT')
            reject('short_seal_identity_rejected',lambda:probe(8,replace(packet,original4_ga_seal_sha256='a')),
                   'sealed original CUT')
        finally:
            torch.get_num_threads = real_get_threads
        require(real_get_threads()==1 and not (HERE/'NEVER_CREATED').exists(), 'Actual CPU1/no output side effects')
        require(not any(name.startswith(('cloud_opt','dust3r','src.dust3r')) for name in sys.modules),
                'No geometry/model module imported')
        report['synthetic_prepare_output_spy_calls']=len(spy_calls)
        report['actual_threads_at_end']=real_get_threads()
        require(all(sha(p)==h for p,h in identities.items()),'Reviewed source changed during preflight')
        report.update(status='PASS', completed_utc=utc(), check_count=len(checks),
                      self_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except BaseException as error:
        report.update(status='FAILED',completed_utc=utc(),error=type(error).__name__+': '+str(error),
                      traceback=traceback.format_exc(),check_count=len(checks))
        write(HERE/'worker_receipt.json',report)
        raise
    write(HERE/'worker_receipt.json',report)
    print(json.dumps({k:report[k] for k in ('status','check_count','real_GA_calls','model_forwards','real_RGB_NPZ_GT_reads')}))


def tree_rss(pid):
    rows = subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,rss='],text=True)
    table = [tuple(map(int,line.split())) for line in rows.splitlines() if line.strip()]
    descendants={pid}
    while True:
        new={p for p,parent,rss in table if parent in descendants}
        if new.issubset(descendants): break
        descendants |= new
    return sum(rss*1024 for p,parent,rss in table if p in descendants)


def supervise():
    require(not (HERE/'receipt.json').exists(),'Preserve every preflight attempt; no overwrite')
    env=os.environ.copy()
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS',
                 'NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS'):
        env[name]='1'
    env['PYTHONDONTWRITEBYTECODE']='1'
    python=ROOT/'.venv-cut3r/bin/python'
    report=dict(status='RUNNING',started_utc=utc(),wall_limit_seconds=60,rss_limit_bytes=1024**3,
                command=[str(python),str(Path(__file__).resolve()),'--worker'],peak_tree_rss_bytes=0,
                scope='synthetic CPU1 adapter/import preflight, no real data/models/GA')
    write(HERE/'receipt.json',report)
    started=time.monotonic()
    with (HERE/'stdout.txt').open('w') as out,(HERE/'stderr.txt').open('w') as err:
        proc=subprocess.Popen(report['command'],cwd=ROOT,env=env,stdout=out,stderr=err,start_new_session=True)
        try:
            while proc.poll() is None:
                report['peak_tree_rss_bytes']=max(report['peak_tree_rss_bytes'],tree_rss(proc.pid))
                require(time.monotonic()-started<=60,'Preflight 60 second deadline')
                require(report['peak_tree_rss_bytes']<=1024**3,'Preflight 1 GiB RSS cap')
                time.sleep(.1)
        except BaseException as error:
            import signal
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=1)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            report['error']=type(error).__name__+': '+str(error)
    report.update(status='PASS' if proc.returncode==0 and 'error' not in report else 'FAILED',
                  returncode=proc.returncode,completed_utc=utc(),wall_seconds=time.monotonic()-started)
    child=HERE/'worker_receipt.json'
    if child.exists():
        report['worker_receipt_sha256']=sha(child)
        child_report=json.loads(child.read_text())
        report['worker_status']=child_report['status']
        report['check_count']=child_report['check_count']
        report['reviewed_identities']=child_report['reviewed_identities']
        report['actual_torch_threads']=child_report.get('actual_threads_at_end')
    report['script_sha256']=sha(__file__)
    write(HERE/'receipt.json',report)
    print(json.dumps(report,indent=2))
    require(report['status']=='PASS','Preflight failed; inspect preserved receipt')


if __name__=='__main__':
    worker() if sys.argv[1:]==['--worker'] else supervise()
