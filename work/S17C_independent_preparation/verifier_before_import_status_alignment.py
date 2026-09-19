#!/usr/bin/env python3
"""Independent S17C saved-output verification. No Torch/PIL/model imports."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import platform
import resource
import signal
import time
import traceback
import zipfile
import numpy as np
import scipy

COMMIT = '39291e4f272f6b4f270691d930926ab5930f942e'
WEIGHT_SHA = '45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103'
SOURCE_PLAN_SHA = 'e90ee3c071912ac594d6b41ed88be23321baae3bac60a221522d67cee4eb482d'
MATH_SHA = '5d3661d314456a83d47f1e2326c1d3756838445280327a47e86cbe651a8424f7'
HISTORY_SHA = ['7caa6f1b9fd1ac5b6938812682c55e3d7926a1348c7554c23e1012b47759cc39',
               '77bebdb3ac737221ef05a4404a1124676bcff536dbffdbb6e197b59bcdf811ae']
HEAD = {'pts3d_in_self_view': (1,384,512,3), 'pts3d_in_other_view': (1,384,512,3),
        'conf_self': (1,384,512), 'conf': (1,384,512), 'rgb': (1,384,512,3), 'camera_pose': (1,7)}
STATE = {'state_feat': ((1,768,768),'float32'), 'state_pos': ((1,768,2),'int64'),
         'init_state_feat': ((1,768,768),'float32'), 'mem': ((1,256,1536),'float32'),
         'init_mem': ((1,256,1536),'float32')}
SCENE = {'world_points': (2,384,512,3), 'depths': (2,384,512), 'confidence': (2,384,512),
         'poses': (2,4,4), 'focal': (2,1), 'pp': (2,2), 'intrinsics': (2,3,3),
         'pw_poses': (1,4,4), 'adaptors': (1,3), 'colors': (2,384,512,3)}
FINAL = {'point_clouds': (2,384,512,3), 'colors': (2,384,512,3), 'depths': (2,384,512),
         'confidences': (2,384,512), 'focal': (2,1), 'pp': (2,2), 'R': (2,3,3), 't': (2,3)}
SCENE_FILES = ['scene_constructed.npz','scene_after_mst.npz','scene_before_clean.npz','scene_after_clean.npz']


def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok, label):
    if not ok: raise ValueError(label)
def aid(a):
    a = np.ascontiguousarray(a)
    return dict(shape=list(a.shape), dtype=str(a.dtype), sha256=hashlib.sha256(a.tobytes()).hexdigest())
def float_schema(shapes): return {k:(s,'float32') for k,s in shapes.items()}


def inspect_npz(path, schema, recorded, check, report):
    check(set(recorded)==set(schema), 'recorded array domain '+path.name)
    with zipfile.ZipFile(path) as z:
        members = z.infolist()
        check(len(members)==len(schema) and {m.filename for m in members}=={k+'.npy' for k in schema}, 'exact NPZ members '+path.name)
        for m in members:
            shape,dtype = schema[m.filename[:-4]]
            check(0<=m.file_size<=int(np.prod(shape))*np.dtype(dtype).itemsize+16384 and not m.flag_bits&1, 'bounded numeric NPY '+m.filename)
    values = {}
    with np.load(path,allow_pickle=False) as z:
        for key,(shape,dtype) in schema.items():
            a = z[key]
            report['array_decodes'] += 1
            check(a.shape==tuple(shape) and a.dtype==np.dtype(dtype), 'actual array schema '+path.name+':'+key)
            check(np.isfinite(a).all(), 'actual finite '+path.name+':'+key)
            check(aid(a)==recorded[key], 'actual array identity '+path.name+':'+key)
            values[key] = a
    return values


def verify_saved_math(run, meta, check, report, output, ref):
    schemas = {'predictions.npz': float_schema({f'frame{i}_{k}':s for i in range(2) for k,s in HEAD.items()}),
               'state.npz': STATE,
               'history_poses.npz': float_schema({'history_pose_encodings':(2,7),'history_poses':(2,4,4)}),
               'processed_inputs.npz': float_schema({'frame0_img':(1,3,384,512),'frame1_img':(1,3,384,512)}),
               'final_result.npz': float_schema(FINAL)}
    schemas.update({name:float_schema(SCENE) for name in SCENE_FILES})
    pnp = meta['pnp_results']
    check(meta['counters']['pnp_calls']==len(pnp)==1, 'one original second-camera PnP invocation')
    check([x['index'] for x in pnp]==[0] and all(x['kwargs']=={'niter_PnP':10} for x in pnp), 'original PnP default ten RANSAC iterations')
    for item in pnp:
        if item['success']:
            check(np.isfinite(item['focal']) and item['focal']>0, 'PnP finite positive focal')
            schemas[f'pnp_{item["index"]}.npz'] = float_schema({'pose':(4,4)})
    check(set(meta['array_files'])==set(schemas), 'exact raw/scene/PnP archive file domain')
    check({p.name for p in run.glob('*.npz')}==set(schemas), 'no extra or omitted numeric payload')
    data = {name:inspect_npz(run/name,schema,meta['array_files'][name],check,report) for name,schema in schemas.items()}
    raw,state,pose = data['predictions.npz'],data['state.npz'],data['history_poses.npz']
    enc = np.concatenate([raw[f'frame{i}_camera_pose'] for i in range(2)])
    check(np.array_equal(enc,pose['history_pose_encodings']), 'raw pose encoding concat')
    independent_pose = ref.raw_pose_scipy(enc)
    check(np.allclose(independent_pose,pose['history_poses'],atol=1e-6,rtol=1e-5), 'independent SciPy raw camera quaternion conversion',
          max_absolute_error=float(np.max(abs(independent_pose-pose['history_poses']))))
    positions = np.array([[i//27,i%27] for i in range(768)],dtype=np.int64)[None]
    check(np.array_equal(state['state_pos'],positions), 'independent state position grid')
    inputs = np.concatenate([data['processed_inputs.npz'][f'frame{i}_img'] for i in range(2)])
    check(np.all((inputs>=-1)&(inputs<=1)), 'normalized real input tensor bounds')
    colors = ref.normalized_input_colors(inputs)
    for name in SCENE_FILES:
        s = data[name]
        check(np.all(s['depths']>0) and np.all(s['focal']>0), 'positive camera z and focal '+name)
        check(np.all(s['confidence']>=0), 'nonnegative unnormalized confidence '+name)
        check(np.array_equal(s['poses'][:,3],np.tile([0,0,0,1],(2,1))), 'camera homogeneous rows '+name)
        check(np.array_equal(s['pp'],np.array([[256,192]]*2)), 'fixed center principal point '+name)
        r = s['poses'][:,:3,:3].astype(np.float64)
        check(np.allclose(r.transpose(0,2,1)@r,np.eye(3),atol=1e-4,rtol=0) and
              np.allclose(np.linalg.det(r),1,atol=1e-4,rtol=0), 'proper c2w rotation '+name)
        check(np.array_equal(s['colors'],colors), 'input colors exact; not predicted RGB '+name)
        k = np.zeros((2,3,3),dtype=np.float32)
        k[:,0,0]=k[:,1,1]=s['focal'][:,0]; k[:,:2,2]=s['pp']; k[:,2,2]=1
        check(np.array_equal(k,s['intrinsics']), 'intrinsics construction '+name)
        points = ref.reconstruct_world(s['depths'],s['focal'],s['pp'],r,s['poses'][:,:3,3])
        errors = abs(points-s['world_points'])
        good = np.isclose(points,s['world_points'],atol=1e-5,rtol=1e-5).all(-1)
        check(good.all(), 'independent dense world reconstruction '+name,
              max_absolute_error=float(errors.max()), failed_pixels=int((~good).sum()))
    before,after,final = data['scene_before_clean.npz'],data['scene_after_clean.npz'],data['final_result.npz']
    for k in SCENE:
        if k!='confidence': check(np.array_equal(before[k],after[k]), 'clean preserved '+k)
    raw_conf = np.stack([raw['frame0_conf_self'][0],raw['frame1_conf'][0]])
    check(np.array_equal(raw_conf,before['confidence']), 'one directed edge raw head confidence binding')
    check(np.array_equal(raw_conf,data['scene_constructed.npz']['confidence']) and
          np.array_equal(raw_conf,data['scene_after_mst.npz']['confidence']), 'confidence unchanged through scene optimization')
    expected,visits,margins = ref.clean_reference(before['confidence'],before['depths'],before['world_points'],before['focal'],before['pp'],before['poses'][:,:3,:3],before['poses'][:,:3,3])
    mismatch = expected!=after['confidence']
    np.savez_compressed(output/'clean_full_diagnostics.npz',**margins,expected_confidence=expected,
                        actual_confidence=after['confidence'],mismatch_mask=mismatch,
                        all_mismatch_indices=np.column_stack(np.nonzero(mismatch)))
    report['clean_diagnostics'] = dict(visits=visits, mismatch_pixels=int(mismatch.sum()),
          file='clean_full_diagnostics.npz', sha256=sha(output/'clean_full_diagnostics.npz'),
          interpretation='Independent FP32 component projection margins; no exclusions or after-result tolerance changes.')
    check(not mismatch.any(), 'all clean confidence pixels exact in independent FP32 path', mismatch_pixels=int(mismatch.sum()))
    changed = np.count_nonzero(before['confidence']!=after['confidence'],axis=(1,2)).tolist()
    zero = np.count_nonzero(after['confidence']==0,axis=(1,2)).tolist()
    check(meta['clean_changed_pixels']==changed and meta['clean_zero_pixels']==zero, 'clean complete counts')
    mapping = {'point_clouds':'world_points','colors':'colors','depths':'depths','confidences':'confidence','focal':'focal','pp':'pp'}
    for fk,sk in mapping.items(): check(np.array_equal(final[fk],after[sk]), 'original wrapper return exact '+fk)
    check(np.array_equal(final['R'],after['poses'][:,:3,:3]) and np.array_equal(final['t'],after['poses'][:,:3,3]), 'optimized c2w returned as R/t')
    loss = ref.pair_objective(before['world_points'],raw['frame0_pts3d_in_self_view'][0],raw['frame1_pts3d_in_other_view'][0],
                              raw['frame0_conf_self'][0],raw['frame1_conf'][0],before['pw_poses'][0],before['adaptors'][0])
    check(np.isfinite(loss) and np.isclose(loss,meta['postfinal_objective'],atol=1e-5,rtol=1e-4), 'independent Euclidean norm log-weighted original pair objective',
          independent=loss,actual=meta['postfinal_objective'],absolute_error=float(abs(loss-meta['postfinal_objective'])))
    report['arrays_verified'] = report['array_decodes']
    report['pnp_success'] = pnp[0]['success']
    report['postfinal_objective_independent'] = loss


def verify(manifest,manifest_sha,seal,seal_sha,run,caller,output):
    output = Path(output).resolve(); require(not output.exists(),'fresh output');output.mkdir(parents=True)
    started = time.monotonic()
    report = dict(schema='s17c-embedded-independent-verification-v1',status='RUNNING',started_utc=utc(),
                  numpy=np.__version__,scipy=scipy.__version__,checks=[],file_hashes=[],array_decodes=0,
                  checkpoint_deserializations=0,image_decodes=0,gt_reads=0,model_calls=0,optimizer_runs=0,
                  interpretation='Component identity and numerical integrity only; no geometry accuracy or full pipeline/video claim.',
                  tolerances=dict(world_atol=1e-5,world_rtol=1e-5,rotation_atol=1e-4,clean='exact_no_exemptions',loss_atol=1e-5,loss_rtol=1e-4,lr_atol=1e-12))
    def check(ok,label,**detail):
        report['checks'].append(dict(name=label,passed=bool(ok),**detail)); require(ok,label)
    def hash_check(p,h,label):
        digest=sha(p);report['file_hashes'].append(dict(path=str(p),sha256=digest,role=label,utc=utc()));check(digest==h,label+' '+str(p))
    def alarm(*unused): raise TimeoutError('600 second verifier bound')
    previous = signal.getsignal(signal.SIGALRM);signal.signal(signal.SIGALRM,alarm);signal.alarm(600)
    try:
        manifest,seal,run,caller = [Path(p).resolve() for p in (manifest,seal,run,caller)]
        hash_check(manifest,manifest_sha,'bound manifest');hash_check(seal,seal_sha,'bound output seal')
        m=json.loads(manifest.read_text());se=json.loads(seal.read_text());ids=se['identities']
        check(m['schema']=='s17c-embedded-two-frame-geometry-manifest-v1' and m['source_commit']==COMMIT,'VMem source identity and schema')
        check(ids.get(str(manifest))==manifest_sha and str(caller) in ids,'caller and manifest bound by seal')
        files={str(p.resolve()) for p in run.rglob('*') if p.is_file()}
        check(files<=set(ids),'all recursively saved outputs sealed')
        for p,h in ids.items():
            check(Path(p).is_absolute() and str(Path(p).resolve())==p,'canonical seal path')
            hash_check(p,h,'sealed output')
        meta=json.loads((run/'run_metadata.json').read_text());cr=json.loads(caller.read_text())
        check(meta['schema']=='s17c-embedded-two-frame-geometry-run-v1' and meta['status']=='SUCCESS','successful actual producer before array reads')
        check(cr['status']=='PASS' and cr['returncode']==0 and cr['monitor_ok'] and cr['before_after_identity_pass'] and not cr['timed_out'] and not cr['rss_limit_exceeded'],'successful external caller')
        check(cr['limits']==dict(seconds=600,rss_bytes=34359738368) and 0<cr['maxrss']<=34359738368 and cr['elapsed_seconds']<600,'external caller 600s/32GiB')
        check(cr['command']==[m['python'],m['runner'],'--manifest',str(manifest),'--output',str(run)],'exact external execution command')
        check(meta['manifest_sha256']==cr['manifest_sha256']==manifest_sha,'both execution receipts bind manifest')
        check(sha(run/'frozen_manifest.json')==manifest_sha and sha(run/'source_snapshot.py')==m['identities'][m['runner']],'frozen executed source and manifest')
        expected_outputs=files-{str(run/'run_metadata.json')}
        check({str(run/p) for p in meta['output_files']}==expected_outputs,'complete producer file inventory')
        for p,info in meta['output_files'].items():
            check(ids.get(str(run/p))==info['sha256'] and (run/p).stat().st_size==info['bytes'],'payload size and hash bound '+p)
        mids=m['identities'];check(mids[m['checkpoint']]==WEIGHT_SHA and Path(m['checkpoint']).stat().st_size==3173761006,'complete checkpoint identity')
        check(mids[m['source_plan']]==SOURCE_PLAN_SHA,'fixed three-patch source plan')
        h=m['history_images'];paths=[x['path'] for x in h]
        check(len(h)==2 and [x['index'] for x in h]==[0,1] and [x['sha256'] for x in h]==HISTORY_SHA and len(set(paths))==2,'original exact Bonn0/1 inputs')
        for x in h: check(mids[x['path']]==x['sha256'],'photo manifest binding')
        expected=dict(history_count=2,query_count=0,device='cpu',cpu_threads=8,seed=0,size=512,processed_size=[384,512],raw_image_size=[640,480],dtype='float32',niter=400,lr=.01,poses=None,depths=None,visualize=False,save_flag=False,wall_seconds=600,monitored_rss_bytes=34359738368,external_monitor_required=True,main_generator_calls=0,sensor_depth_reads=0,video_generated=False,postfinal_objective_evaluations=1)
        check(all(m['contract'].get(k,'MISSING')==v for k,v in expected.items()),'fixed free-pose two-image component contract')
        src=Path(m['source_root']);overlay=Path(m['overlay'])
        source_plan=json.loads(Path(m['source_plan']).read_text())
        expected_src={k:v['sha256'] for k,v in source_plan['source_files'].items()};expected_src.update({v['path']:v['sha256'] for v in source_plan['patches']})
        check({p:h for p,h in mids.items() if Path(p).is_relative_to(src)}=={str(src/k):v for k,v in expected_src.items()},'exact transparent source tree')
        deps=set(m['overlay_files']);controls=set(m['control_files'])
        check(all(Path(p).is_relative_to(overlay) for p in deps),'isolated overlay inventory')
        allowed={str(src/k) for k in expected_src}|deps|controls|set(paths)|{m[k] for k in ['runner','checkpoint','source_plan','dependency_plan','environment_receipt','import_smoke']}
        check(set(mids)==allowed and all(Path(p).name not in {'groundtruth.txt','rgb.txt','depth.txt'} for p in mids),'exact source/control/photo input allowlist')
        for p,hsh in mids.items(): hash_check(p,hsh,'frozen source/dependency/input bytes only')
        check(json.loads(Path(m['import_smoke']).read_text())['status']=='PASS','actual prior import-only gate')
        for name,v in meta['embedded_module_identities'].items():
            check(Path(v['path']).is_relative_to(src) and mids.get(v['path'])==v['sha256'],'actual loaded embedded source '+name)
        check([x['when'] for x in meta['identity_checks']]==['before','after'] and all(x['all_match'] and x['count']==len(mids) for x in meta['identity_checks']),'actual full before-after identity passes')
        check(meta['history_images']==h and meta['contract']==m['contract'],'producer input contract recorded exactly')
        check([x['path'] for x in meta['input_reads']]==paths and all(x['role']=='native_rgb_decode' and x['size']==[640,480] and x['mode']=='RGB' for x in meta['input_reads']),'only original two RGB decodes')
        counts=dict(history_rgb_decoded=2,target_rgb_decoded=0,sensor_depth_reads=0,main_generator_calls=0,wrapper_calls=1,prepare_input_calls=1,inference_attempts=1,inference_calls=1,model_forward_calls=1,history_frames_saved=2,supplied_image_frames=2,supplied_ray_frames=0,image_encoder_calls=1,image_encoder_frames=2,dummy_ray_encoder_calls=1,dummy_ray_encoder_frames=1,encoder_first_calls=1,encoder_last_calls=1,global_aligner_calls=1,mst_calls=1,pnp_calls=1,optimization_iterations=400,optimizer_steps=400,clean_calls=1,postfinal_objective_evaluations=1,scene_objective_calls=401,query_calls=0)
        check(meta['counters']==counts,'all actual call and input counters')
        flags=dict(img_mask=True,ray_mask=False,update=True,reset=False)
        check(meta['processed_input_shapes']==[[1,3,384,512]]*2 and meta['processed_true_shapes']==[[[384,512]]]*2 and meta['history_flags']==[flags]*2,'actual official input shapes and masks')
        observations=meta['encoder_observations'];ev=[('image_encoder',[2,3,384,512]),('encoder_first',[2,768,1024]),('encoder_last',[2,768,1024]),('dummy_ray_encoder',[1,6,384,512])]
        check([(v['kind'],v['input_shape']) for v in observations]==ev and all(v['dtype']=='torch.float32' for v in observations),'four actual FP32 encoder boundary observations')
        check(observations[0]['output_token_shape']==[2,768,1024] and observations[3]['output_token_shape']==[1,768,1024] and observations[3]['all_zero'],'internal zero dummy; not an effective ray query')
        architecture=dict(head_type='dpt',output_mode='pts3d+pose',image_patch_class='PatchEmbedDust3R',ray_patch_class='PatchEmbedDust3R',patch_image_size=[512,512],downstream_head_class='DPTPts3dPose',encoder_blocks=24)
        check(all(meta['architecture'].get(k)==v for k,v in architecture.items()),'actual official DPT architecture')
        check(meta['weights_only'] and meta['checkpoint_all_keys_matched'],'safe matched public checkpoint load')
        check(meta['scene_edges']==[[0,1]] and meta['scene_config']==dict(type='PointCloudOptimizer',norm_pw_scale=True,base_scale=.5,min_conf_thr=3),'single directed edge and free geometry scale convention')
        check(meta['alignment_arguments']==dict(init='mst',niter=400,schedule='linear',lr=.01) and meta['mst_kwargs']==dict(niter_PnP=10),'original global alignment arguments')
        check(meta['optimizer']['type']=='Adam' and meta['optimizer']['defaults']['betas']==[.9,.9],'original Adam betas')
        for v in meta['scene_parameters']:
            check(v['dtype']=='torch.float32','scene parameter dtype')
            if v['name'] in {'im_pp','pw_adaptors'}:check(v['requires_grad'] is False,'frozen scene parameter '+v['name'])
        trace=meta['optimization_trace'];disk=[json.loads(l) for l in (run/'optimization_trace.jsonl').read_text().splitlines()]
        check(trace==disk and len(trace)==400 and [v['iteration'] for v in trace]==list(range(400)) and [v['optimizer_steps'] for v in trace]==list(range(1,401)),'all actual optimizer iterations saved')
        check(np.isfinite([v['loss_before_step'] for v in trace]).all(),'all losses finite; no monotonic condition')
        mathfile=Path(__file__).resolve().parents[1]/'work/S17C_independent_preparation/numerical_reference.py'
        check(mids.get(str(mathfile))==MATH_SHA and sha(mathfile)==MATH_SHA,'independent numerical helper bound')
        spec=importlib.util.spec_from_file_location('s17c_independent_math',mathfile);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
        check(np.allclose([v['lr'] for v in trace],ref.expected_learning_rates(),atol=1e-12,rtol=0),'fixed 400-step linear learning rates')
        check(meta['alignment_returned_loss_before_last_step']==trace[-1]['loss_before_step'],'returned loss is before last step')
        check(all(meta[k] is False for k in ['video_generated','new_model_trained','accuracy_evaluated','supplied_pose_prior','supplied_depth_prior','surfel_objects_created']),'component boundary preserved')
        check(meta['device']=='cpu' and meta['cpu_threads']==8 and meta['seed']==0 and meta['rngs_seeded_after_import']==['python','numpy','torch','opencv'],'actual CPU and post-import RNG settings')
        verify_saved_math(run,meta,check,report,output,ref)
        check(0<meta['peak_rss_bytes']<=34359738368 and meta['elapsed_seconds']<600,'producer resource bound')
        check(datetime.fromisoformat(cr['started_utc'])<=datetime.fromisoformat(meta['started_utc'])<=datetime.fromisoformat(meta['finished_utc'])<=datetime.fromisoformat(cr['completed_utc']),'caller and producer chronology')
        for p,hsh in ids.items():hash_check(p,hsh,'post-verification sealed output')
        check(sha(manifest)==manifest_sha and sha(seal)==seal_sha,'binding files unchanged')
        report.update(status='PASS',inputs_unchanged=True)
    except BaseException as exc:
        report.update(status='FAIL',error=repr(exc),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        report.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-started,source_sha256=sha(__file__),
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if platform.system()=='Darwin' else 1024))
        (output/'verification.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ['status','completed_utc','array_decodes']}))
    return int(report['status']!='PASS')


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for key in ['manifest','manifest-sha256','seal','seal-sha256','run-dir','caller-receipt','output']:ap.add_argument('--'+key,required=True)
    a=ap.parse_args();raise SystemExit(verify(a.manifest,a.manifest_sha256,a.seal,a.seal_sha256,a.run_dir,a.caller_receipt,a.output))
