"""DRAFT: original common4 MST + one objective backward; zero optimizer steps.

Requires a root-frozen contract. No action occurs on import. Uses saved S26
original4 heads, original PIL preprocessing, and the sealed common camera path.
This is new initialization/gradient evidence, never a historical MST snapshot.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


class DiagnosticComplete(BaseException):
    """Expected exit after exactly one backward and before optimizer creation."""


def execute(contract_path, expected_sha):
    require(sha(contract_path) == expected_sha, 'Exact root-frozen contract required')
    c = read(contract_path)
    require(c['status'] == 'FROZEN', 'Draft cannot execute')
    require(c['schema'] == 's27m-common4-mst-one-backward-v1', 'Wrong contract')
    require(c['maximum_optimizer_steps'] == 0 and c['objective_backward_calls'] == 1,
            'Only zero-step, one-backward diagnostic is supported')
    for path, digest in c['identities'].items():
        require(sha(path) == digest, 'Changed diagnostic identity: ' + path)
    out = Path(c['output_dir'])
    require(not out.exists(), 'Never repeat or overwrite this diagnostic')
    out.mkdir(parents=True)
    receipt = dict(status='RUNNING', started_utc=utc(), contract_sha256=expected_sha,
                   model_forwards=0, optimizer_steps=0, sensor_depth_reads=0,
                   new_initialization_replay=True, historical_MST_snapshot=False)
    write(out / 'receipt.json', receipt)
    patches = []
    try:
        spec = importlib.util.spec_from_file_location('s27m_frozen_s26b', c['parent_runner'])
        b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(b)
        m = b.manifest(c['parent_manifest_sha256'])
        require(m['continuation']['common_files']['output.npz']['path'] == c['old_common_output'],
                'Compare the originally saved common4 producer')
        require(m['continuation']['common_files']['output.npz']['sha256'] ==
                c['identities'][c['old_common_output']], 'Old common seal is inherited')
        control = read(c['control_receipt'])
        require(control['status'] == 'PASS' and control['output_sha256'] == sha(c['control_camera']),
                'Use the already sealed camera control')
        require(control['manifest_sha256'] == m['continuation']['original_manifest_sha256'],
                'Original camera producer identity')

        # Match original common4 setup order: all eight PIL views, original four
        # saved heads, then repeat fixed seeds after all geometry imports.
        np, torch, a, ns, views, proof = b.original_context(m)
        cameras = torch.from_numpy(np.load(c['control_camera'], allow_pickle=False)[:4].copy())
        records = m['candidate']['archives']['common_old_depth_original4']
        require(len(records) == 4 and len(views) == 8, 'Exact existing common4 inputs')
        predictions = a.load_saved_predictions(records)
        output = a.assemble_saved_output(ns, views[:4], predictions)
        align = importlib.import_module('cloud_opt.dust3r_opt')
        init = importlib.import_module('cloud_opt.dust3r_opt.init_im_poses')
        base = importlib.import_module('cloud_opt.dust3r_opt.base_opt')
        opt = importlib.import_module('cloud_opt.dust3r_opt.optimizer')
        observed = dict(mst_calls=0, alignment_calls=0, pnp_calls=0,
                        original_objective_forwards=0, backwards=0,
                        original_loop_entry=0, optimizer_step_attempts=0,
                        clean_attempts=0, phase='setup')
        state = {}
        temporary_depth_stacks = []

        def patch(obj, name, replacement):
            old = getattr(obj, name)
            patches.append((obj, name, old))
            setattr(obj, name, replacement(old))

        def array(x):
            return np.array(x.detach().cpu().numpy() if hasattr(x, 'detach') else x, copy=True)

        def grad_info(p):
            g = p.grad
            return dict(requires_grad=bool(p.requires_grad), is_leaf=bool(p.is_leaf),
                        grad_is_none=g is None,
                        grad_finite=None if g is None else bool(torch.isfinite(g).all()),
                        grad_l2=None if g is None else float(g.detach().norm()),
                        grad_max_abs=None if g is None else float(g.detach().abs().max()))

        def wrap_aligner(old):
            def call(*args, **kwargs):
                scene = old(*args, **kwargs)
                require(scene.edges == [(0, 1), (0, 2), (0, 3)], 'Original common4 star')
                state['scene'] = scene
                return scene
            return call

        def wrap_alignment(old):
            def call(src, target):
                answer = old(src, target)
                index = observed['alignment_calls']
                observed['alignment_calls'] += 1
                scale, rotation, translation = answer
                np.savez_compressed(out / f'alignment_{index}.npz',
                                    predicted_c2w=array(src), given_c2w=array(target),
                                    scale=array(scale), rotation=array(rotation),
                                    translation=array(translation))
                return answer
            return call

        def wrap_pnp(old):
            def call(*args, **kwargs):
                answer = old(*args, **kwargs)
                index = observed['pnp_calls']
                observed['pnp_calls'] += 1
                record = dict(index=index, success=answer is not None,
                              niter_PnP=kwargs.get('niter_PnP'))
                if answer is not None:
                    record['focal'] = float(answer[0])
                    np.savez_compressed(out / f'pnp_{index}.npz',
                                        focal=array(answer[0]), c2w=array(answer[1]))
                state.setdefault('pnp_records', []).append(record)
                return answer
            return call

        def wrap_mst(old):
            def call(scene, *args, **kwargs):
                require(observed['mst_calls'] == 0, 'Exactly one new MST invocation')
                observed['phase'] = 'MST'
                answer = old(scene, *args, **kwargs)
                observed['mst_calls'] += 1
                require(scene is state['scene'], 'Capture the actual original scene')
                require(not scene.im_poses.requires_grad and not scene.norm_pw_scale,
                        'Given poses fixed; pairwise scale normalization disabled')
                require(all(p.requires_grad for p in scene.im_depthmaps),
                        'Original common4 registered depth flags')
                require(torch.allclose(scene.get_im_poses(), cameras, atol=1e-5, rtol=1e-6),
                        'Original given camera condition preserved')
                with torch.no_grad():
                    state['mst_depth'] = np.stack([array(x) for x in scene.get_depthmaps()])
                    state['parameters_before_backward'] = {
                        name: p.detach().clone() for name, p in scene.named_parameters()}
                    np.savez_compressed(out / 'mst_state.npz',
                        depth=state['mst_depth'],
                        registered_log_depth=np.stack([array(p) for p in scene.im_depthmaps]),
                        point_cloud=np.stack([array(x) for x in scene.get_pts3d()]),
                        focal=array(scene.get_focals()), pp=array(scene.get_principal_points()),
                        c2w=array(scene.get_im_poses()), pw_scale=array(scene.get_pw_scale()),
                        pw_poses=array(scene.get_pw_poses()), adaptors=array(scene.get_adaptors()))
                observed['phase'] = 'after_MST'
                write(out / 'progress.json', dict(stage='MST_CAPTURED', utc=utc(), counts=observed))
                return answer
            return call

        def wrap_stack(old):
            def call(params, *args, **kwargs):
                answer = old(params, *args, **kwargs)
                if (observed['phase'] == 'single_forward' and state.get('scene') is not None
                        and params is state['scene'].im_depthmaps):
                    temporary_depth_stacks.append(answer)
                return answer
            return call

        def stop_at_loop(old):
            def call(scene, *args, **kwargs):
                observed['original_loop_entry'] += 1
                require(observed['mst_calls'] == 1 and observed['phase'] == 'after_MST',
                        'Sentinel must follow the original MST')
                require(kwargs == dict(niter=400, schedule='linear', lr=0.01),
                        'Original wrapper requested its unchanged loop arguments')
                require(scene is state['scene'], 'Same scene at zero-step boundary')
                registered = dict(scene.named_parameters())
                require(set(registered) == set(state['parameters_before_backward']),
                        'Registered parameter names unchanged since MST capture')
                optimizer_candidates = {id(p) for p in scene.parameters() if p.requires_grad}
                require(all(p.grad is None for p in registered.values()),
                        'One clean backward, no accumulated registered gradients')
                observed['phase'] = 'single_forward'
                with torch.enable_grad():
                    loss = scene()
                    observed['original_objective_forwards'] += 1
                    require(bool(torch.isfinite(loss)) and loss.requires_grad, 'Finite original objective')
                    loss.backward()
                    observed['backwards'] += 1
                observed['phase'] = 'after_backward'
                require(len(temporary_depth_stacks) == 1, 'One observed depth ParameterStack in original forward')
                registered_after = dict(scene.named_parameters())
                require(set(registered_after) == set(registered),
                        'Backward must preserve the complete registered parameter name set')
                for name, parameter in registered.items():
                    require(registered_after[name] is parameter,
                            'Backward must preserve registered parameter object identity: ' + name)
                    require(torch.equal(parameter.detach(), state['parameters_before_backward'][name]),
                            'No registered parameter value may change: ' + name)
                state['gradient_report'] = dict(
                    loss=float(loss.detach()),
                    registered_parameters={name:dict(**grad_info(p),
                        in_original_optimizer_candidates=id(p) in optimizer_candidates)
                        for name, p in registered.items()},
                    temporary_depth_stacks=[dict(**grad_info(p),
                        in_registered_parameters=any(p is q for q in registered.values()),
                        in_original_optimizer_candidates=id(p) in optimizer_candidates)
                        for p in temporary_depth_stacks])
                require(all(v['grad_finite'] is not False
                            for v in state['gradient_report']['registered_parameters'].values()),
                        'Registered gradients must be finite when present')
                require(all(grad_info(p)['grad_finite'] is not False for p in temporary_depth_stacks),
                        'Temporary gradients must be finite when present')
                write(out / 'gradient_report.json', state['gradient_report'])
                raise DiagnosticComplete()
            return call

        def forbid_step(old):
            def call(*args, **kwargs):
                observed['optimizer_step_attempts'] += 1
                raise RuntimeError('Forbidden optimizer step in zero-step diagnostic')
            return call

        def forbid_clean(old):
            def call(*args, **kwargs):
                observed['clean_attempts'] += 1
                raise RuntimeError('Diagnostic must terminate before original clean')
            return call

        patch(align, 'global_aligner', wrap_aligner)
        patch(init, 'align_multiple_poses', wrap_alignment)
        patch(init, 'fast_pnp', wrap_pnp)
        patch(init, 'init_minimum_spanning_tree', wrap_mst)
        patch(opt, 'ParameterStack', wrap_stack)
        patch(base, 'global_alignment_loop', stop_at_loop)
        patch(torch.optim.Adam, 'step', forbid_step)
        patch(base.BasePCOptimizer, 'clean_pointcloud', forbid_clean)
        b.numeric_setup()  # Exact baseline post-import seed reset.
        sentinel = False
        try:
            a.run_original_ga(ns, output, control_c2ws=cameras, old_depth=None, output_dir=out)
        except DiagnosticComplete:
            sentinel = True
        require(sentinel, 'Original wrapper must leave through the diagnostic sentinel')
        require(observed['mst_calls'] == observed['original_loop_entry'] ==
                observed['original_objective_forwards'] == observed['backwards'] == 1,
                'Exactly one MST, objective and backward')
        require(observed['optimizer_step_attempts'] == observed['clean_attempts'] == 0,
                'No optimizer/clean work')

        # Read the old final only after new initialization and gradient evidence
        # are persisted. This comparison never supplies a depth prior to scene.
        require(sha(c['old_common_output']) == c['identities'][c['old_common_output']],
                'Old common output identity')
        with np.load(c['old_common_output'], allow_pickle=False) as previous:
            old_depth = previous['depth'].copy()
        replay_depth = state['mst_depth']
        require(old_depth.shape == replay_depth.shape == (4, 384, 512), 'Common4 depth schema')
        require(old_depth.dtype == replay_depth.dtype == np.float32, 'Unchanged depth dtype')
        delta = np.abs(old_depth.astype(np.float64) - replay_depth.astype(np.float64))
        comparison = dict(
            evidence_scope='New MST replay versus an old final; not a saved historical initialization',
            exact_equal=bool(np.array_equal(replay_depth, old_depth)),
            descriptive_allclose_1e6=bool(np.allclose(replay_depth, old_depth, atol=1e-6, rtol=1e-6)),
            max_abs_difference=float(delta.max()),
            per_frame_max_abs=[float(x.max()) for x in delta],
            per_frame_mean_abs=[float(x.mean()) for x in delta],
            replay_depth_sha256=hashlib.sha256(replay_depth.tobytes()).hexdigest(),
            old_depth_sha256=hashlib.sha256(old_depth.tobytes()).hexdigest())
        write(out / 'old_final_comparison.json', comparison)
        loaded = {}
        embedded = Path(m['binding']['embedded_root']).resolve()
        for name, module in list(sys.modules.items()):
            if name.startswith(('cloud_opt.', 'dust3r.', 'src.dust3r.', 'models.', 'croco.')):
                origin = getattr(module, '__file__', None)
                if origin:
                    path = Path(origin).resolve()
                    require(path.is_relative_to(embedded), 'Mixed geometry source: ' + name)
                    require(m['binding']['source_identities'].get(str(path)) == sha(path),
                            'Changed loaded source: ' + name)
                    loaded[name] = str(path)
        loaded_deps = {}
        loaded_dep_identities = {}
        overlay = Path(m['binding']['overlay']).resolve()
        for name, module in list(sys.modules.items()):
            origin = getattr(module, '__file__', None)
            if origin:
                path = Path(origin).resolve()
                if path.is_relative_to(overlay):
                    digest = sha(path)
                    require(m['dependency_identities'].get(str(path)) == digest,
                            'Changed/unbound loaded overlay module: ' + name)
                    loaded_deps[name] = str(path)
                    loaded_dep_identities[str(path)] = digest
        for path, digest in c['identities'].items():
            require(sha(path) == digest, 'Input identity changed during diagnostic: ' + path)
        for path, digest in m['identities'].items():
            require(sha(path) == digest, 'Parent source/control changed during diagnostic: ' + path)
        # Scientific outcomes are recorded, not required to match a hypothesis.
        registered_depth = {name:value for name,value in state['gradient_report']['registered_parameters'].items()
                            if name.startswith('im_depthmaps.')}
        require(len(registered_depth) == 4, 'Four original registered depth leaves observed')
        receipt.update(status='PASS_DIAGNOSTIC_EXECUTED', completed_utc=utc(),
            counts=observed, source_proof=proof, loaded_geometry_modules=loaded,
            loaded_overlay_modules=loaded_deps, loaded_overlay_identities=loaded_dep_identities,
            parent_identities_rechecked_at_exit=len(m['identities']),
            original_depth_gradient_none={name:v['grad_is_none'] for name,v in registered_depth.items()},
            old_final_depth_exact_equal=comparison['exact_equal'],
            registered_parameter_names_and_objects_preserved=True,
            no_registered_parameter_values_changed=True,
            pnp_records=state.get('pnp_records', []),
            evidence_scope='New original common4 MST plus one original objective backward; zero optimizer steps; not old historical initialization or improved depth',
            outputs={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='receipt.json'})
        write(out / 'receipt.json', receipt)
    except BaseException as exc:
        receipt.update(status='FAILED', failed_utc=utc(), error=repr(exc), traceback=traceback.format_exc())
        write(out / 'receipt.json', receipt)
        raise
    finally:
        for obj, name, original in reversed(patches):
            setattr(obj, name, original)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True)
    parser.add_argument('--contract-sha256', required=True)
    args = parser.parse_args()
    execute(args.contract, args.contract_sha256)


if __name__ == '__main__':
    main()
