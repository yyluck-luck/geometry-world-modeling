"""Validate saved failed-run output for a separately recorded import.

Only stored heads, allowed derived cameras, views and GA output are decoded.
No sensor GT, backbone, optimizer, model construction or GA is used.
"""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace
import time

import numpy as np
import torch
import scipy
from scipy.spatial.transform import Rotation

R = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
H = R / 'work/S26_clean_recovery'
D = R / 'results/S26_consumer_baseline/common_old'
W = R / 'work/S26_execution'
E = R / 'work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tensor_sha(x):
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_bytes())


def arrays(p):
    with np.load(p, allow_pickle=False) as z:
        return {k: z[k].copy() for k in z.files}


def module(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def extract(path, names, ns, nested=False):
    tree = ast.parse(Path(path).read_text())
    nodes = ast.walk(tree) if nested else tree.body
    body = [n for n in nodes if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(body) == len(names)
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), ns)


def main():
    start = time.monotonic()
    started = datetime.now(timezone.utc).isoformat()
    target = H / 'recovery_receipt.json'
    assert not target.exists(), 'Preserve previous import validation'
    torch.set_num_threads(8)
    assert (np.__version__, torch.__version__, scipy.__version__) == ('1.26.4', '2.7.0', '1.16.2')
    seal = read(H / 'recovery_input_seal.json')
    for p, expected in seal['identities'].items():
        assert sha(p) == expected, p
    manifest_path = R / 'work/S26_consumer_baseline_preparation/run_manifest.json'
    manifest = read(manifest_path)
    # Current filesystem checks cannot recreate the old process module inventory.
    source_checked = 0
    for p, expected in manifest['identities'].items():
        assert sha(p) == expected, p
        source_checked += 1
    for p, expected in manifest['dependency_identities'].items():
        assert sha(p) == expected, p
    a = arrays(D / 'output.npz')
    consumed = arrays(D / 'consumed_inputs.npz')
    preset = arrays(D / 'preset_parameters.npz')
    pair = arrays(D / 'pairwise_state.npz')
    preconf = arrays(D / 'preclean_conf.npz')['conf']
    colors = arrays(D / 'input_colors.npz')['colors']
    cameras = np.load(W / 'control_c2w.npy', allow_pickle=False)[:4].copy()
    records = read(D / 'inputs_seal.json')['saved_heads']
    heads = [arrays(row['path']) for row in records]
    checks = []

    def check(name, condition, **detail):
        if not condition:
            raise AssertionError(name)
        checks.append({'name': name, 'passed': True, **detail})

    shapes = dict(depth=(4,384,512), point_cloud=(4,384,512,3), conf=(4,384,512),
                  focal=(4,1), pp=(4,2), c2w=(4,4,4))
    check('complete_finite_FP32_original_output', set(a) == set(shapes)
          and all(x.shape == shapes[k] and x.dtype == np.float32 and np.isfinite(x).all() for k,x in a.items()))
    check('physical_domains', (a['depth'] > 0).all() and (a['focal'] > 0).all() and (a['conf'] >= 0).all())
    check('given_camera_input_preserved', np.allclose(a['c2w'], cameras, atol=1e-5, rtol=1e-6),
          maximum_absolute_error=float(np.abs(a['c2w']-cameras).max()))
    check('exact_star_edge_ids', np.array_equal(consumed['edge_i'], [0,0,0])
          and np.array_equal(consumed['edge_j'], [1,2,3]))
    for j in range(1,4):
        edge = f'0_{j}'
        for label, field, raw in [('i','pts3d_in_self_view',heads[0]), ('j','pts3d_in_other_view',heads[j])]:
            expected = raw[field][0]
            check(f'actual_consumed_and_preset_prediction_{label}_{edge}',
                  np.array_equal(consumed['pred_'+label][j-1].reshape(384,512,3), expected)
                  and np.array_equal(preset['pred_'+label+'.'+edge], expected))
        for label, field, raw in [('i','conf_self',heads[0]), ('j','conf',heads[j])]:
            expected = raw[field][0]
            weights = torch.log(torch.from_numpy(expected)).numpy()
            check(f'actual_consumed_log_weights_and_preset_conf_{label}_{edge}',
                  np.array_equal(consumed['weight_'+label][j-1].reshape(384,512), weights)
                  and np.array_equal(preset['conf_'+label+'.'+edge], expected))
    expected_conf = np.stack([heads[0]['conf_self'][0], *[heads[j]['conf'][0] for j in range(1,4)]])
    check('preclean_conf_from_unmodified_star_heads', np.array_equal(preconf, expected_conf))
    for variant in ('original','ttt','filt'):
        view = arrays(W / (variant+'_views.npz'))
        images = np.concatenate([view[f'img_{i}'] for i in range(4)])
        expected = np.clip(images.transpose(0,2,3,1)*.5+.5, 0, 1)
        check('colors_match_sealed_'+variant+'_views', np.array_equal(colors, expected))
    q = preset['im_poses'][:,:4].astype(np.float64)
    t = preset['im_poses'][:,4:7].astype(np.float64)
    pose_from_preset = np.repeat(np.eye(4)[None], 4, axis=0)
    pose_from_preset[:,:3,:3] = Rotation.from_quat(q).as_matrix()
    pose_from_preset[:,:3,3] = np.sign(t)*np.expm1(np.abs(t))
    check('saved_preset_pose_matches_final_given_pose', np.allclose(pose_from_preset,a['c2w'],atol=1e-5,rtol=1e-6),
          maximum_absolute_error=float(np.abs(pose_from_preset-a['c2w']).max()))
    check('saved_preset_pp_matches_final', np.array_equal(preset['im_pp']*10+np.array([256,192],np.float32),a['pp']))
    raw_adapt = torch.from_numpy(preset['pw_adaptors'])
    expected_adapt = torch.exp(torch.cat((raw_adapt[:,:1],raw_adapt),-1)/20).numpy()
    check('saved_fixed_pair_adaptors_match_final', np.array_equal(expected_adapt,pair['adaptors']))
    reference = module(R/'work/S17C_independent_preparation/numerical_reference.py','independent_math')
    edge_loss = [reference.pair_objective(a['point_cloud'][[0,j]],heads[0]['pts3d_in_self_view'][0],
                 heads[j]['pts3d_in_other_view'][0],heads[0]['conf_self'][0],heads[j]['conf'][0],
                 pair['pw_poses'][j-1],pair['adaptors'][j-1]) for j in range(1,4)]
    independent_objective = float(np.mean(edge_loss))
    ns = {'torch':torch,'np':np}
    extract(E/'src/dust3r/utils/geometry.py', ('geotrf',), ns)
    extract(E/'cloud_opt/dust3r_opt/commons.py', ('l1_dist',), ns)
    extract(E/'cloud_opt/dust3r_opt/optimizer.py', ('forward',), ns, nested=True)
    frozen_state = SimpleNamespace(
        get_pw_poses=lambda:torch.from_numpy(pair['pw_poses']),
        get_adaptors=lambda:torch.from_numpy(pair['adaptors']),
        get_pts3d=lambda raw=False:torch.from_numpy(a['point_cloud']).reshape(4,-1,3),
        dist=ns['l1_dist'], total_area_i=3*384*512, total_area_j=3*384*512,
        _stacked_pred_i=torch.from_numpy(consumed['pred_i']), _stacked_pred_j=torch.from_numpy(consumed['pred_j']),
        _weight_i=torch.from_numpy(consumed['weight_i']), _weight_j=torch.from_numpy(consumed['weight_j']),
        _ei=torch.from_numpy(consumed['edge_i']), _ej=torch.from_numpy(consumed['edge_j']))
    with torch.no_grad():
        recomputed_original_objective = float(ns['forward'](frozen_state))
    check('saved_state_original_forward_vs_independent_float64_objective',
          np.isclose(independent_objective,recomputed_original_objective,atol=1e-5,rtol=1e-4),
          original_forward_recomputed_now=recomputed_original_objective,
          independent_float64=independent_objective, per_edge_independent=edge_loss,
          old_process_postfinal_scalar='NOT_RECORDED; these are new saved-state recomputations')
    world = reference.reconstruct_world(a['depth'],a['focal'],a['pp'],a['c2w'][:,:3,:3],a['c2w'][:,:3,3])
    check('independent_float64_backprojection',np.allclose(world,a['point_cloud'],atol=1e-5,rtol=1e-5),
          maximum_absolute_error_m=float(np.abs(world-a['point_cloud']).max()))
    revised_path = H/'clean_reference_torch_fp32.py'
    new = module(revised_path,'independent_clean')
    conf, visits, margins = new.clean_reference(preconf,a['depth'],a['point_cloud'],a['focal'],a['pp'],a['c2w'][:,:3,:3],a['c2w'][:,:3,3])
    check('new_clean_all_pixels_byte_exact',tensor_sha(conf)==tensor_sha(a['conf']),pixels=int(conf.size),pairs=len(visits))
    del margins
    lines = [json.loads(s) for s in (D/'optimization_trace.jsonl').read_text().splitlines()]
    check('complete_400_finite_step_trace',len(lines)==400 and [x['iteration'] for x in lines]==list(range(400))
          and all(math.isfinite(x['loss_before_step']) and math.isfinite(x['lr']) for x in lines))
    lr_error = max(abs(x['lr']-(.01+(1e-6-.01)*i/400)) for i,x in enumerate(lines))
    check('original_linear_schedule_all400',lr_error < 1e-15,maximum_absolute_error=lr_error)
    original_failed = read(D/'receipt.json')
    check('original_failure_remains_intact',original_failed['status']=='FAILED'
          and original_failed['error']=='RuntimeError: Independent FP32 clean mismatch; no exemptions')
    for p, expected in seal['identities'].items():
        assert sha(p)==expected,p
    record = {
        'schema':'s26-saved-common-old-import-validation-v1','status':'IMPORT_VALIDATED','passed':True,
        'validation_scope':'Saved-output import only; original S26 remains FAILED. No retrospective producer PASS.',
        'started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'wall_seconds':time.monotonic()-start,
        'old_manifest_sha256':sha(manifest_path),'old_output_npz_sha256':sha(D/'output.npz'),
        'revised_clean_sha256':sha(revised_path),'revised_clean_path':str(revised_path),
        'old_receipt_sha256':sha(D/'receipt.json'),'old_inputs_seal_sha256':sha(D/'inputs_seal.json'),
        'depth_tensor_sha256':tensor_sha(a['depth']),'control_pose_prefix_tensor_sha256':tensor_sha(cameras),
        'input_identities_before_after':seal['identities'],'inputs_unchanged':True,
        'checks':checks,'check_count':len(checks),
        'current_disk_identity_checks':{'source_controls':source_checked,'overlay_dependencies':len(manifest['dependency_identities']),
                                        'meaning':'Current complete byte identity checks; not historical loaded-module inventory'},
        'historical_observations_not_recorded':{
            'postfinal_objective_scalar':'NOT_RECORDED; source function and independent formula recomputed now from sealed saved state',
            'parameter_flags_and_intermediate_snapshots':'NOT_RECORDED as final report; preset values exist and final decoded quantities checked; original successful observer assertions inferred from frozen failure control-flow',
            'PnP_call_details':'NOT_RECORDED; no invented success/focal values',
            'loaded_geometry_and_overlay_module_inventory':'NOT_RECORDED; current bound bytes verified without claiming original module inventory',
            'returned_pre_last_step_loss':'NOT_RECORDED as observer field; actual per-iteration trace exists'},
        'historical_control_flow_evidence':[
            'Frozen runner exception at independent clean gate occurs after observed Adam400/MST1/clean1 completion assertion.',
            'Preset, after-MST, after-GA and after-clean fixed-parameter equality assertions preceded this failure; no posthoc snapshots are invented.',
            'Original wrapper returned and six fields matched observer snapshot; schema, domain and input-color assertions preceded the saved output and failure.'],
        'true_saved_prediction_head_archives_decoded':4,'saved_preprocess_archives_decoded':3,
        'new_GT_sensor_bytes_read':0,'GT_groundtruth_text_parses':0,'derived_allowed_camera_array_read':True,
        'new_RGB_files_decoded':0,'new_model_runs':0,'new_GA_runs':0,'optimizer_steps_in_recovery':0,
        'new_saved_state_original_objective_evaluations':1,
        'control_identities':{str(p):sha(p) for p in (Path(__file__),revised_path,H/'recovery_input_seal.json',H/'diagnostic_receipt.json')},
        'scope_limits':['Post-failure recovery using already observed data; not an independent blind experiment',
                        'Shared Torch inverse/matmul is a numerical conformance choice, while clean masks use an independent dense-gather formula',
                        'No sensor-depth score or method/gen-video benefit is inferred',
                        'Downstream S26B must bind this receipt and copy exact old bytes into an explicitly recovered producer, preserving old FAILED artifacts']}
    target.write_text(json.dumps(record,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({'status':record['status'],'checks':len(checks),'wall_seconds':record['wall_seconds'],
                      'objective_original_recomputed':recomputed_original_objective,'objective_independent':independent_objective,
                      'depth_tensor_sha256':record['depth_tensor_sha256'],'control_pose_prefix_tensor_sha256':record['control_pose_prefix_tensor_sha256'],
                      'receipt_sha256':sha(target)},indent=2))


if __name__ == '__main__':
    main()
