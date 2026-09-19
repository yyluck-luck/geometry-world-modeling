from pathlib import Path
from types import SimpleNamespace
import contextlib, copy, hashlib, importlib.util, io, json, sys, tempfile
import numpy as np
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'scripts'))
from verify_s8_results import sampling_from_timestamps
spec=importlib.util.spec_from_file_location('original_reviewed_auditor',root/'work/s8_sampling_audit_review/original_auditor_snapshot.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); module.ROOT=root
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
write=lambda p,v:Path(p).write_text(json.dumps(v,indent=2)+'\n')
results=[]
with tempfile.TemporaryDirectory() as td:
    td=Path(td); data=td/'synthetic_data'; data.mkdir();(data/'rgb').mkdir();(data/'depth').mkdir()
    stamps=np.arange(0,40,.03); rgb=[(float(t),f'rgb/{i}.png') for i,t in enumerate(stamps)]
    depth=[(float(t+.001),f'depth/{i}.png') for i,t in enumerate(stamps)]
    for kind,rows in [('rgb',rgb),('depth',depth)]:
        (data/f'{kind}.txt').write_text(''.join(f'{t:.12f} {p}\n' for t,p in rows))
    # Regenerate from serialized timestamps, as the actual audit will do.
    rgb=module.timestamp_rows(data/'rgb.txt',2);depth=module.timestamp_rows(data/'depth.txt',2)
    times=np.arange(4001)*.01
    (data/'groundtruth.txt').write_text(''.join(f'{t:.12f} never parse these seven pose value tokens\n' for t in times))
    gt=np.asarray(module.timestamp_rows(data/'groundtruth.txt',8)); assert gt.shape==(4001,1)
    accepted,chosen,n=sampling_from_timestamps(rgb,depth,gt)
    text_hashes={f:sha(data/f) for f in ('rgb.txt','depth.txt','groundtruth.txt')}
    manifest=dict(schema='s8-inputs-v1',dataset='rgbd_dataset_freiburg2_desk',
        protocol_sha256=sha(root/'docs/S8_EXTERNAL_SCENE_PROTOCOL.md'),
        runner_sha256='cc3ae6fd6243ce3531e540dc8c70ef61af0e868c919c7232a16616cf750ba292',
        archive_sha256='a'*64,text_file_sha256=text_hashes,blocks=[])
    for b,wi in enumerate(chosen):
        window=accepted[wi];frames=[]
        for fi,(mi,r,d) in enumerate(window['rows']):
            f=dict(frame=fi,match_index=mi,target_timestamp=window['target_timestamps'][fi],snap_error_seconds=window['snap_errors'][fi])
            for kind,(stamp,path) in zip(('rgb','depth'),(r,d)):
                (data/path).write_bytes(f'unique synthetic {kind} bytes at {stamp!r}'.encode())
                f[kind]=dict(timestamp=stamp,path=path);f[kind+'_sha256']=sha(data/path)
            frames.append(f)
        stamps=[f['rgb']['timestamp'] for f in frames]
        manifest['blocks'].append(dict(block=b,split='test',accepted_window_index=wi,
            nominal_start=window['nominal_start'],nominal_end=window['nominal_end'],
            actual_duration_seconds=stamps[-1]-stamps[0],
            rgb_minus_depth_seconds=[f['rgb']['timestamp']-f['depth']['timestamp'] for f in frames],
            rgb_intervals_seconds=[y-x for x,y in zip(stamps,stamps[1:])],frames=frames))
    windows=[dict(index=i,segment=0,gt_interval=0,nominal_start=w['nominal_start'],nominal_end=w['nominal_end'],
        target_timestamps=w['target_timestamps'],snap_errors_seconds=w['snap_errors'],
        match_indices=[r[0] for r in w['rows']],rgb_timestamps=[r[1][0] for r in w['rows']]) for i,w in enumerate(accepted)]
    sampling=dict(status='completed',manifest_sha256='',protocol_sha256=manifest['protocol_sha256'],
        preparation_source_sha256=sha(root/'scripts/prepare_s8_inputs.py'),archive_sha256='a'*64,
        images_decoded=False,gt_pose_values_parsed=False,gt_timestamp_count=len(gt),rgb_count=len(rgb),depth_count=len(depth),
        selected_rgb_frames=72,selected_depth_files=72,text_file_sha256=text_hashes,paired_count=n,
        plan=dict(accepted_windows=windows,selected_window_indices=chosen))
    def run_case(name,change_manifest=None,change_sampling=None,change_file=None):
        m=copy.deepcopy(manifest);s=copy.deepcopy(sampling)
        if change_manifest: change_manifest(m)
        if change_sampling: change_sampling(s)
        mp=td/(name+'_manifest.json');sp=td/(name+'_sampling.json');write(mp,m);s['manifest_sha256']=sha(mp);write(sp,s)
        restore=None
        if change_file:
            f=data/m['blocks'][0]['frames'][0]['rgb']['path']; restore=(f,f.read_bytes());f.write_bytes(b'mutated raw input')
        args=SimpleNamespace(manifest=mp,sampling=sp,protocol=root/'docs/S8_EXTERNAL_SCENE_PROTOCOL.md',
            design_freeze=root/'docs/S8_DESIGN_FREEZE.json',data=data,output=td/(name+'_audit'))
        try:
            with contextlib.redirect_stdout(io.StringIO()): module.run(args)
            status='passed';error=None
        except Exception as e: status='failed';error=str(e)
        finally:
            if restore:restore[0].write_bytes(restore[1])
        report=json.loads((args.output/'verification.json').read_text())
        results.append(dict(case=name,status=status,error=error,checks_passed=report['checks_passed']))
    run_case('valid_timestamp_only')
    run_case('wrong_pair_index',lambda m:m['blocks'][0]['frames'][0].__setitem__('match_index',999999))
    run_case('wrong_middle_choice',lambda m:m['blocks'][1].__setitem__('accepted_window_index',0))
    run_case('wrong_candidate_target',change_sampling=lambda s:s['plan']['accepted_windows'][0]['target_timestamps'].__setitem__(1,999.))
    run_case('wrong_raw_input_sha',change_file=True)
    run_case('wrong_perframe_target',lambda m:m['blocks'][0]['frames'][0].__setitem__('target_timestamp',999.))
    run_case('wrong_perframe_snap_error',lambda m:m['blocks'][0]['frames'][0].__setitem__('snap_error_seconds',999.))
    run_case('wrong_block_cadence',lambda m:m['blocks'][0].update(nominal_start=999.,nominal_end=1000.,actual_duration_seconds=1.,rgb_minus_depth_seconds=[999.]*24,rgb_intervals_seconds=[999.]*23))
    run_case('wrong_sampling_source',change_sampling=lambda s:s.update(protocol_sha256='b'*64,preparation_source_sha256='c'*64,archive_sha256='d'*64))
    run_case('wrong_accepted_window_RGB',change_sampling=lambda s:s['plan']['accepted_windows'][0]['rgb_timestamps'].__setitem__(0,999.))
    run_case('wrong_frame_scalar_types',lambda m:m['blocks'][0]['frames'][0].__setitem__('frame',False))
report=dict(reviewed_source_sha256=sha(root/'work/s8_sampling_audit_review/original_auditor_snapshot.py'),
    real_S8_data_read=False,image_decoding_executed=False,GT_pose_tokens_numeric=False,
    fixture_gt_shape=[4001,1],synthetic_only=True,cases=results)
write(root/'work/s8_sampling_audit_review/original_checks.json',report)
print(json.dumps(report,indent=2))
