"""Read-only saved S27M review; no MST, backward, GA, network or sensor GT."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, os, sys, time
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=ROOT/'results/S27M_mst_gradient_diagnostic'

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def require(ok,msg):
    if not ok:raise RuntimeError(msg)

def main():
    require(not (HERE/'attempt.json').exists(),'Keep all previous attempts')
    started=utc();timer=time.perf_counter()
    write(HERE/'attempt.json',{'started_utc':started,'command':[sys.executable,str(Path(__file__).resolve())],
          'script_sha256':sha(__file__),'scope':'Existing saved products and source identity only; zero new MST/backward/GA/model/sensorGT'})
    ids={str(Path(__file__).resolve()):sha(__file__)}
    def bind(path,expected=None):
        path=Path(path);h=sha(path)
        require(expected is None or h==expected,'Identity mismatch: '+str(path))
        ids[str(path)]=h;return path
    def read(path,expected=None):return json.loads(bind(path,expected).read_text())
    r=read(BASE/'receipt.json')
    caller=read(ROOT/'work/S27M_execution/diagnostic/receipt.json')
    cpath=ROOT/'work/S27M_preparation/contract.json'
    c=read(cpath,r['contract_sha256'])
    pre=read(c['independent_pre_review']['path'],c['independent_pre_review']['sha256'])
    require(r['status']=='PASS_DIAGNOSTIC_EXECUTED' and caller['status']=='PASS' and caller['returncode']==0,'Completed diagnostic and caller required')
    require(pre['status']=='PASS_STATIC_PRE_EXECUTION_REVIEW' and c['status']=='FROZEN','Reviewed frozen source required')
    require(caller['command'][1:]==[str(ROOT/'scripts/s27m_mst_gradient_diagnostic.py'),'--contract',str(cpath),'--contract-sha256',sha(cpath)],'Caller command binding')
    require(c['maximum_optimizer_steps']==0 and c['objective_backward_calls']==1,'Diagnostic scope')
    m=read(c['parent_manifest'],c['parent_manifest_sha256'])
    for path,h in c['identities'].items():
        # Read no RGB, saved heads, or control-camera payload in this review.
        if Path(path).suffix in {'.py','.md','.json'}:bind(path,h)
    require(r['parent_identities_rechecked_at_exit']==len(m['identities']),'Recorded parent control extent')
    for name,path in r['loaded_geometry_modules'].items():
        bind(path,m['binding']['source_identities'][path])
    require(set(r['loaded_overlay_modules'].values())==set(r['loaded_overlay_identities']),'Complete recorded overlay path identities')
    for path,h in r['loaded_overlay_identities'].items():
        require(m['dependency_identities'][path]==h,'Overlay hash not in parent')
        bind(path,h)
    for name,h in r['outputs'].items():bind(BASE/name,h)
    require(set(r['outputs'])=={p.name for p in BASE.iterdir() if p.is_file() and p.name!='receipt.json'},'Output inventory')
    expected_counts={'mst_calls':1,'alignment_calls':1,'pnp_calls':3,'original_objective_forwards':1,'backwards':1,'original_loop_entry':1,'optimizer_step_attempts':0,'clean_attempts':0}
    for k,v in expected_counts.items():require(r['counts'][k]==v,'Recorded count: '+k)
    for k in ('model_forwards','optimizer_steps','sensor_depth_reads'):require(r[k]==0,'Producer scope: '+k)
    require(r['historical_MST_snapshot'] is False and r['new_initialization_replay'] is True,'Replay scope')
    require(r['registered_parameter_names_and_objects_preserved'] and r['no_registered_parameter_values_changed'],'Recorded parameter guards')

    g=read(BASE/'gradient_report.json',r['outputs']['gradient_report.json'])
    expected_names={'pw_poses','pw_adaptors','im_poses','im_focals','im_pp'}
    expected_names|={f'{prefix}.0_{j}' for prefix in ('pred_i','pred_j','conf_i','conf_j') for j in (1,2,3)}
    expected_names|={f'{prefix}.{i}' for prefix in ('im_conf','im_depthmaps') for i in range(4)}
    require(set(g['registered_parameters'])==expected_names,'All25 registered gradient records')
    gradient_rows=[]
    for name,row in g['registered_parameters'].items():
        require(set(row)=={'requires_grad','is_leaf','grad_is_none','grad_finite','grad_l2','grad_max_abs','in_original_optimizer_candidates'},'Gradient schema')
        require(row['is_leaf'] is True and row['in_original_optimizer_candidates']==row['requires_grad'],'Registered membership/leaf')
        if row['grad_is_none']:
            require(all(row[k] is None for k in ('grad_finite','grad_l2','grad_max_abs')),'Missing grad is not zero grad')
        else:
            require(row['requires_grad'] and row['grad_finite'] is True,'Present registered grad domain')
            require(all(math.isfinite(row[k]) and row[k]>=0 for k in ('grad_l2','grad_max_abs')),'Finite gradient summaries')
            require(row['grad_l2']>=row['grad_max_abs'],'Gradient norm bound')
        gradient_rows.append({'name':name,**row})
    for i in range(4):
        row=g['registered_parameters'][f'im_depthmaps.{i}']
        require(row['requires_grad'] and row['grad_is_none'] and r['original_depth_gradient_none'][f'im_depthmaps.{i}'],'Registered depth record')
    require({n for n,row in g['registered_parameters'].items() if not row['grad_is_none']}=={'pw_poses','im_focals'},'All recorded non-None gradient groups')
    require(len(g['temporary_depth_stacks'])==1,'One temporary leaf record')
    tmp=g['temporary_depth_stacks'][0]
    require(tmp['requires_grad'] and tmp['is_leaf'] and not tmp['grad_is_none'] and tmp['grad_finite'],'Temporary nonzero finite gradient')
    require(not tmp['in_registered_parameters'] and not tmp['in_original_optimizer_candidates'],'Temporary leaf not registered candidate')
    require(math.isfinite(tmp['grad_l2']) and math.isfinite(tmp['grad_max_abs']) and tmp['grad_l2']>=tmp['grad_max_abs']>0,'Temporary norms')
    require(math.isfinite(g['loss']),'Finite reported objective')
    write(HERE/'gradient_record_audit.json',{'reported_original_objective':g['loss'],'all_registered_records':gradient_rows,'temporary_records':g['temporary_depth_stacks'],
        'scope':'All saved scalar records and logical consistency checked; raw gradient tensors were not saved, so norms are not independently recomputed; no new backward.'})

    import numpy as np
    import torch
    torch.set_num_threads(1)
    oldpath=bind(c['old_common_output'],c['identities'][c['old_common_output']])
    with np.load(BASE/'mst_state.npz',allow_pickle=False) as z:
        depth=z['depth'].copy();logdepth=z['registered_log_depth'].copy();mst_pose=z['c2w'].copy()
        mst_header={k:{'shape':list(z[k].shape),'dtype':str(z[k].dtype)} for k in ('depth','registered_log_depth','c2w')}
    with np.load(oldpath,allow_pickle=False) as z:old=z['depth'].copy()
    require(depth.shape==old.shape==logdepth.shape==(4,384,512) and depth.dtype==old.dtype==logdepth.dtype==np.float32,'Depth/log schema')
    require(np.isfinite(depth).all() and np.isfinite(logdepth).all() and np.isfinite(old).all() and (depth>0).all() and (old>0).all(),'Finite positive depths')
    reported=read(BASE/'old_final_comparison.json',r['outputs']['old_final_comparison.json'])
    bitwise=bool(np.array_equal(depth.view(np.uint32),old.view(np.uint32)))
    require(bitwise and reported['exact_equal'] and r['old_final_depth_exact_equal'],'Exact old-final/MST depth equality')
    depth_sha=hashlib.sha256(depth.tobytes()).hexdigest();old_sha=hashlib.sha256(old.tobytes()).hexdigest()
    require(depth_sha==old_sha==reported['replay_depth_sha256']==reported['old_depth_sha256'],'Raw depth SHA')
    delta=depth.astype(np.float64)-old.astype(np.float64)
    require(reported['max_abs_difference']==float(np.abs(delta).max())==0.,'Full-grid maximum difference')
    require(reported['per_frame_max_abs']==[0.]*4 and reported['per_frame_mean_abs']==[0.]*4,'All old-depth per-frame differences')
    with torch.no_grad():fp32_exp=torch.from_numpy(logdepth).exp().numpy()
    fp64_exp=np.exp(logdepth.astype(np.float64))
    numeric=fp64_exp-depth.astype(np.float64)
    exp_report={'torch_version':torch.__version__,'numpy_version':np.__version__,'torch_cpu_threads':1,
       'fp32_torch_exp_bitwise_equal':bool(np.array_equal(fp32_exp.view(np.uint32),depth.view(np.uint32))),
       'fp32_torch_exp_max_abs':float(np.abs(fp32_exp.astype(np.float64)-depth.astype(np.float64)).max()),
       'fp64_numpy_exp_max_abs':float(np.abs(numeric).max()),'fp64_numpy_exp_max_relative':float((np.abs(numeric)/depth).max()),
       'fp64_numpy_exp_within_existing_1e6_atol_rtol':bool(np.allclose(fp64_exp,depth,atol=1e-6,rtol=1e-6)),
       'scope':'Torch FP32 repeats saved-output encoding math only, without autograd. NumPy FP64 is a different precision/libm comparison, not an expected bitwise identity or GT check.'}
    require(exp_report['fp64_numpy_exp_within_existing_1e6_atol_rtol'],'Saved log-depth numerical consistency')
    write(HERE/'depth_checks.json',{'shape':[4,384,512],'all_pixels':int(depth.size),'all_four_frames_included':True,'bitwise_equal':bitwise,
        'mst_and_old_depth_sha256':depth_sha,'max_abs_mst_minus_old':0.,'per_frame_pixels':[384*512]*4,'exp':exp_report,'decoded_mst_keys':mst_header})

    with np.load(BASE/'alignment_0.npz',allow_pickle=False) as z:
        require(set(z.files)=={'predicted_c2w','given_c2w','scale','rotation','translation'},'Alignment schema')
        src=z['predicted_c2w'].astype(np.float64);tgt=z['given_c2w'].astype(np.float64)
        scale=float(z['scale']);rotation=z['rotation'].astype(np.float64);translation=z['translation'].astype(np.float64)
    require(src.shape==tgt.shape==(4,4,4) and rotation.shape==(3,3) and translation.shape==(3,),'Saved alignment shapes')
    require(all(np.isfinite(a).all() for a in (src,tgt,rotation,translation)) and math.isfinite(scale) and scale>0,'Finite alignment')
    mapped_centers=np.array([scale*(rotation@x[:3,3])+translation for x in src])
    mapped_rotations=np.array([rotation@x[:3,:3] for x in src])
    residual=mapped_centers-tgt[:,:3,3]
    norms=np.linalg.norm(residual,axis=1)
    frame_rows=[]
    for i in range(4):
        relative=tgt[i,:3,:3].T@mapped_rotations[i]
        cosine=float(np.clip((np.trace(relative)-1)/2,-1,1))
        frame_rows.append({'frame':i,'predicted_center':src[i,:3,3].tolist(),'given_center':tgt[i,:3,3].tolist(),
            'mapped_center':mapped_centers[i].tolist(),'mapped_minus_given_m':residual[i].tolist(),'center_residual_norm_m':float(norms[i]),
            'rotation_frobenius_residual':float(np.linalg.norm(mapped_rotations[i]-tgt[i,:3,:3])),
            'rotation_trace_angle_deg_approx':math.degrees(math.acos(cosine))})
    pairs=[]
    for i in range(4):
        for j in range(i+1,4):
            a=float(np.linalg.norm(src[i,:3,3]-src[j,:3,3]));b=float(np.linalg.norm(tgt[i,:3,3]-tgt[j,:3,3]))
            pairs.append({'i':i,'j':j,'predicted_center_distance':a,'given_center_distance_m':b,'scaled_predicted_distance_m':scale*a})
    mst_given=mst_pose.astype(np.float64)-tgt
    alignment={'recorded_scale':scale,'recorded_rotation':rotation.tolist(),'recorded_translation':translation.tolist(),
       'rotation_det':float(np.linalg.det(rotation)),'rotation_orthogonality_max_abs':float(np.abs(rotation.T@rotation-np.eye(3)).max()),
       'formula':'mapped camera center = s*R*predicted_center+t; mapped orientation = R*predicted_orientation; no refitting',
       'frames':frame_rows,'all_six_camera_pairs':pairs,'center_rmse_m':float(np.sqrt(np.mean(norms**2))),
       'center_max_m':float(norms.max()),'mst_saved_pose_minus_given_max_abs':float(np.abs(mst_given).max()),
       'interpretation':'This recorded Sim3 maps predicted initialization cameras into the given-camera frame; s is not depth GT calibration. Residual describes this fit, not why initial depth is inaccurate. The original fit uses augmented z-axis points; center-only residual need not be its full minimized objective.',
       'rotation_angle_limit':'Angles from saved approximate float matrices via clipped trace; raw Frobenius residual and R orthogonality are also preserved. No projection ontoSO3 or alignment refit.'}
    write(HERE/'alignment_description.json',alignment)
    pnp=[]
    for row in r['pnp_records']:
        require(row['success'] is True,'Saved result has three successful PnP calls')
        with np.load(BASE/f"pnp_{row['index']}.npz",allow_pickle=False) as z:
            f=float(z['focal']);pose=z['c2w']
        require(f==row['focal'] and pose.shape==(4,4) and np.isfinite(pose).all(),'PnP saved result record')
        pnp.append({'index':row['index'],'focal':f,'pose_shape':[4,4],'finite':True})
    for path,h in ids.items():require(sha(path)==h,'Reviewed file changed: '+path)
    receipt={'status':'PASS_SAVED_RESULT_REVIEW','started_utc':started,'completed_utc':utc(),'wall_seconds':time.perf_counter()-timer,
       'command':[sys.executable,str(Path(__file__).resolve())],'reviewer':'research_novelty_routes; different from S27M producer, same author as S27M pre-review',
       'all_depth_elements_compared':int(depth.size),'gradient_registered_records_checked':len(gradient_rows),'temporary_gradient_records_checked':1,
       'new_MST':0,'new_PnP':0,'new_forward':0,'new_backward':0,'new_optimizer_steps':0,'new_model_runs':0,'new_sensor_GT_reads':0,
       'camera_data_scope':'Existing saved alignment source and given-control matrices only; no new GT trajectory file parse',
       'producer_timing_from_caller':{k:caller[k] for k in ('started_utc','completed_utc','wall_seconds','peak_rss_bytes','returncode')},
       'source_and_overlay_actual_files_rehashed':{'geometry_module_entries':len(r['loaded_geometry_modules']),'overlay_unique_paths':len(r['loaded_overlay_identities'])},
       'pnp_record_checks':pnp,'identities_before_after':ids,
       'limits':['Raw gradients and before/after full parameter tensors were not all saved; their norms/unchanged status are checked as source-bound producer observations, not recomputed by new backward.','Independent full-depth equality and numerical log-exp consistency were actually recomputed.','New replay equality with old final is strong compatibility evidence, not a recovered historical initial snapshot.','No sensor-depth accuracy, causal explanation of scale bias, repaired-optimizer benefit, or generated-video improvement measured.'],
       'outputs':{p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.name not in {'receipt.json','attempt.json'}}}
    write(HERE/'receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'wall_seconds':receipt['wall_seconds'],'depth_elements':int(depth.size),
       'exp':exp_report,'alignment_scale':scale,'camera_center_rmse_m':alignment['center_rmse_m'],'camera_center_max_m':alignment['center_max_m'],
       'receipt_sha256':sha(HERE/'receipt.json')},indent=2))

if __name__=='__main__':
    try:main()
    except BaseException as e:
        if (HERE/'attempt.json').exists() and not (HERE/'receipt.json').exists():
            write(HERE/'receipt.json',{'status':'FAIL','failed_utc':utc(),'error':repr(e),'new_MST_backward_GA_model_GT':0})
        raise
