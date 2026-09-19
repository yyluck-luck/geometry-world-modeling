from pathlib import Path
import hashlib, json, subprocess, sys, tempfile, traceback
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'scripts'))
from verify_s8_results import pose_at_closed, normalized_from_raw, rebuilt_observations, sampling_from_timestamps, verify_state
from verify_s7_replay import Checks, now, sha
results=[]
def record(name, fn):
    try:
        detail=fn(); results.append(dict(name=name,status='passed',detail=detail))
    except Exception:
        results.append(dict(name=name,status='failed',traceback=traceback.format_exc())); raise

def closed():
    gt=np.array([[0,1,2,3,0,0,0,1],[.1,2,3,4,0,0,0,1],[.4,4,5,6,0,0,0,1]],float)
    for i in range(3):
        p,g=pose_at_closed(gt,gt[i,0]); assert g==0 and np.array_equal(p[:3,3],gt[i,1:4])
    p,g=pose_at_closed(gt,.05); assert g==.1 and np.array_equal(p[:3,3],[1.5,2.5,3.5])
    for t in (-.01,.2,.41):
        try: pose_at_closed(gt,t)
        except ValueError: pass
        else: raise AssertionError('Expected rejection')
    return 'exact first/internal/isolated-final GT, interpolation and gap/extrapolation rejection'
record('closed_GT_pose_wrapper',closed)

def sampling():
    stamps=np.arange(0,40,.03)
    rgb=[(float(t),f'rgb/{i}.png') for i,t in enumerate(stamps)]
    dep=[(float(t+.001),f'depth/{i}.png') for i,t in enumerate(stamps)]
    gt=np.zeros((4001,8)); gt[:,0]=np.arange(4001)*.01; gt[:,7]=1
    accepted,ids,n=sampling_from_timestamps(rgb,dep,gt)
    assert len(accepted)==4 and ids==[0,1,3] and n==len(rgb)
    assert [a['nominal_start'] for a in accepted]==[0.,8.969999999999999,17.939999999999998,26.91]
    return dict(windows=len(accepted),indices=ids,paired=n)
record('synthetic_sampling_fixed_window',sampling)

def gate():
    with tempfile.TemporaryDirectory() as d:
        directory=Path(d); run=directory/'run'; run.mkdir(); (run/'run_metadata.json').write_text('{"status":"running","phase":"prediction_only"}')
        output=directory/'no_output'
        command=[sys.executable,str(root/'scripts/verify_s8_results.py')]
        for name in ('manifest','protocol','freeze','runs','data'): command += ['--'+name,str(directory/('missing_'+name))]
        command+=['--results',str(run),'--output',str(output)]
        p=subprocess.run(command,capture_output=True,text=True)
        assert p.returncode==2 and 'not completed' in p.stderr and not output.exists()
        assert sorted(x.name for x in directory.iterdir())==['run']
        return dict(exit_code=p.returncode,output_created=False,new_data_paths_all_nonexistent=True)
record('running_status_refuses_before_data',gate)

def old_format():
    before={}
    def track(path): before[str(path)]=sha(path); return path
    def load(path):
        with np.load(track(path)) as z: return {k:z[k] for k in z.files}
    raw=load(root/'results/S6_cut3r_cpu/block0/predictions.npz'); depths,poses,norm=normalized_from_raw(raw)
    frozen=load(root/'results/S6_memory_bridge/block0_normalized_input.npz')
    assert np.array_equal(depths[0],frozen['first_depth'])
    assert np.allclose(poses,frozen['poses'],atol=1e-9,rtol=1e-10)
    manifest=json.loads(track(root/'data/cut3r/S5_inputs.json').read_text()); rgbs=[]
    for frame in manifest['blocks'][0]['frames'][:20]:
        path=track(root/'data/tum/rgbd_dataset_freiburg1_xyz'/frame['rgb']['path'])
        with Image.open(path) as image: rgbs.append(np.asarray(image.convert('RGB').resize((299,224),Image.Resampling.LANCZOS).crop((37,0,261,224))))
    differences={}
    for stride in (8,12):
        obs=load(root/f'results/S7_event_replay/block0_stride{stride}/observations.npz')
        rebuilt,filters=rebuilt_observations(depths,[raw[f'frame{i}_conf_self'][0] for i in range(20)],rgbs,poses,stride)
        case=json.loads(track(root/f'results/S7_event_replay/block0_stride{stride}/prediction_only_selection.json').read_text())
        assert filters==case['filters']
        for key,value in rebuilt.items():
            if key in ('points','normals','radii'):
                assert np.allclose(value,obs[key],atol=1e-9,rtol=1e-10)
                differences[f'stride{stride}/{key}']=float(np.max(np.abs(value-obs[key])))
            else: assert np.array_equal(value,obs[key])
    state=json.loads(track(root/'results/S6_cut3r_cpu/block0/run_metadata.json').read_text())
    check=Checks(); verify_state(state,check,'old_compatibility')
    assert all(sha(Path(path))==digest for path,digest in before.items())
    return dict(old_source_files=len(before),raw_old_RGBs=20,strides=[8,12],attribute_max_differences=differences,
                metadata_checks=len(check.items),all_original_hashes_unchanged=True)
record('old_audited_readonly_format_and_observations',old_format)
report=dict(status='passed',completed_utc=now(),new_S8_data_read=False,model_or_renderer_executed=False,
    verifier_sha256=sha(root/'scripts/verify_s8_results.py'),checks=results)
(root/'work/s8_audit_preparation/preparation_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
