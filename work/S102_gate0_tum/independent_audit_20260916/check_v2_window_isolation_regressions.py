#!/usr/bin/env python3
"""Synthetic readiness regressions. Never opens research data or dispatches jobs."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
VALIDATOR = HERE.parent / 'validate_gate0_v2.py'
spec = importlib.util.spec_from_file_location('gate0_validator_under_review', VALIDATOR)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def ref(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size}


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) if not isinstance(value, str) else value)
    return ref(path)


def approve(root, contract):
    contract['review_ref'] = put(root, 'review.json', {
        'verdict': 'PRE_RUN_APPROVED', 'reviewer': 'synthetic_fixture_reviewer',
        'protocol_sha256': v.canonical_sha(contract['protocol']),
        'scope': 'software fixture only; no scientific clearance or dispatch'})


def replace_artifact(root, contract, key, obj, refresh_isolation=False):
    p = contract['protocol']
    p[key] = put(root, key + '.json', obj)
    if refresh_isolation:
        isolation = read(p['isolation']['receipt_ref'])
        mapping = {'predictor_inputs_ref': 'predictor_inputs_sha256',
                   'scorer_inputs_ref': 'scorer_inputs_sha256',
                   'runtime_binding_ref': 'runtime_binding_sha256'}
        isolation[mapping[key]] = p[key]['sha256']
        p['isolation']['receipt_ref'] = put(root, 'isolation.json', isolation)


def read(descriptor):
    return json.loads(Path(descriptor['path']).read_text())


def fixture(root, scenes=('scene_13',)):
    config = {'model': {'height': 576, 'width': 576, 'context_num_frames': 4,
                       'target_num_frames': 4, 'num_frames': 8, 'inference_num_steps': 50}, 'seed': 42}
    cfg_ref = put(root, 'config.json', config)
    wrapper = put(root, 'predictor.py', '# synthetic wrapper; no execution\n')
    source_file = put(root, 'source.py', '# synthetic source; not a model\n')
    source_ref = put(root, 'source_manifest.json', {'files': [source_file]})
    checkpoints = {name: put(root, 'weights/' + name, 'synthetic checkpoint bytes only')
                   for name in ('vmem', 'vae', 'clip', 'cut3r')}
    boundary = 'SYNTHETIC_BOUNDARY_V1_NOT_FOR_DISPATCH'
    runtime = {'effective_config_sha256': cfg_ref['sha256'],
               'source_manifest_sha256': source_ref['sha256'],
               'predictor_wrapper_sha256': wrapper['sha256'],
               'checkpoint_paths': {name: item['path'] for name, item in checkpoints.items()},
               'execution_boundary_id': boundary,
               'execution_host': 'synthetic-compute-node'}
    runtime_ref = put(root, 'runtime.json', runtime)
    staged = root / 'staged'
    predictor, scorer, windows = [], [], []
    for scene in scenes:
        base = {'dataset_id': 'synthetic_3dmatch', 'scene_id': scene, 'sequence_id': 'seq_01'}
        windows.append({**base, 'history_ids': [0, 1, 2, 3], 'target_ids': [4, 5, 6, 7],
                        'chronological': True})
        for frame in range(4):
            for role in ('history_rgb', 'history_depth', 'history_pose'):
                payload = put(root, f'staged/{scene}/{role}/{frame}.fixture',
                              f'Synthetic {role} frame {frame}; not research data')
                predictor.append({**base, 'frame_id': str(frame), 'role': role, 'file': payload})
        commands = put(root, f'staged/{scene}/commands.json',
                       {'synthetic': True, 'target_frame_ids': [4, 5, 6, 7]})
        for frame in range(4, 8):
            predictor.append({**base, 'frame_id': str(frame), 'role': 'command_camera', 'file': commands})
            for role in ('future_rgb', 'future_depth', 'future_pose'):
                # Outcomes are declared but intentionally nonexistent: pre-run must not open them.
                outcome = {'path': str(root / 'unopened_outcomes' / scene / role / str(frame)),
                           'sha256': '0' * 64, 'bytes': 7}
                scorer.append({**base, 'frame_id': str(frame), 'role': role, 'file': outcome})
    pred_ref = put(root, 'predictor_inputs.json', {'records': predictor})
    score_ref = put(root, 'scorer_inputs.json', {'records': scorer})
    isolation = {'method': 'linux_namespace', 'allowed_history_probe_passed': True,
                 'denied_outcome_probe_passed': True, 'full_archive_unavailable': True,
                 'predictor_inputs_sha256': pred_ref['sha256'],
                 'scorer_inputs_sha256': score_ref['sha256'],
                 'runtime_binding_sha256': runtime_ref['sha256'],
                 'predictor_wrapper_sha256': wrapper['sha256'],
                 'execution_boundary_id': boundary, 'predictor_root': str(staged),
                 'probe_host': 'synthetic-login-node',
                 'scope': 'synthetic booleans, never usable as real isolation evidence'}
    adapter = put(root, 'adapter.py', '# synthetic adapter only\n')
    adapter_review = put(root, 'adapter_review.json', {
        'status': 'ADAPTER_ACCEPTED', 'adapter_sha256': adapter['sha256']})
    protocol = {'status': 'FROZEN', 'run_id': 'SYNTHETIC_REGRESSION_NOT_FOR_DISPATCH',
                'author': 'synthetic_fixture_author', 'scope': 'development_baseline',
                'development_data_exposed': True, 'effective_config_ref': cfg_ref,
                'expected_config': {key: v.lookup(config, key) for key in v.CONFIG_KEYS},
                'source_manifest_ref': source_ref, 'runtime_binding_ref': runtime_ref,
                'uses_cut3r': True, 'checkpoints': checkpoints, 'vae_variant': 'declared_substitute',
                'predictor_inputs_ref': pred_ref, 'scorer_inputs_ref': score_ref,
                'target_camera_policy': 'predeclared_command',
                'isolation': {'predictor_root': str(staged), 'execution_boundary_id': boundary,
                              'receipt_ref': put(root, 'isolation.json', isolation)},
                'datasets': {'synthetic_3dmatch': {
                    'camera': {'calibration_status': 'verified', 'K': [[540, 0, 320], [0, 540, 240], [0, 0, 1]],
                               'rgb_depth_registration': 'registered', 'pixel_center_convention': 'synthetic',
                               'resize_crop_K_rule': 'synthetic', 'pose_time_association': 'synthetic'},
                    'depth': {'raw_to_metres_divisor': 1000, 'invalid_values': [0],
                              'interpretation': 'optical_axis_z'},
                    'adapter_ref': adapter, 'adapter_review_ref': adapter_review}},
                'calibration_scene_ids': list(scenes), 'windows': windows,
                'budget': {'candidate_count': 4, 'selection_k': 4, 'output_count': 4,
                           'sampling_steps': 50, 'dtype': 'float16', 'rng_policy': 'synthetic',
                           'timeout_seconds': 1500,
                           'metric_definition_ref': put(root, 'metrics.md', 'Synthetic metric specification')},
                'predictor_wrapper_ref': wrapper,
                'scorer_ref': put(root, 'scorer.py', '# synthetic scorer; never executed\n'),
                'verifier_ref': put(root, 'verifier.py', '# synthetic verifier; never executed\n')}
    contract = {'schema': v.SCHEMA, 'protocol': protocol, 'post_run': {}}
    approve(root, contract)
    return contract


def main():
    cases = []
    def check(name, mutation=None, expected_error=None, scenes=('scene_13',)):
        with tempfile.TemporaryDirectory(prefix='gate0-window-isolation-') as temp:
            root = Path(temp)
            contract = fixture(root, scenes)
            if mutation:
                mutation(root, contract)
            # Reapprove every mutation so rejection demonstrates a semantic guard,
            # not a stale protocol digest or an intentionally absent file.
            approve(root, contract)
            result = v.validate(contract, root, 'pre-run')
            passed = result['status'] == 'PRE_RUN_READY' if expected_error is None else (
                result['status'] == 'BLOCKED' and any(expected_error in x for x in result['errors']))
            cases.append({'name': name, 'passed': passed, 'actual_status': result['status'],
                          'expected_error': expected_error, 'errors': result['errors']})

    check('valid four-plus-four scoped development fixture; no prediction artifacts')
    check('same bare frame IDs in different scenes remain distinct; shared command bundle accepted',
          scenes=('scene_13', 'scene_14'))

    def wrong_history(root, c):
        obj = read(c['protocol']['predictor_inputs_ref'])
        obj['records'][0]['frame_id'] = '99'
        replace_artifact(root, c, 'predictor_inputs_ref', obj, True)
    check('history payload identity differs from frozen window', wrong_history,
          'predictor history identities do not exactly match')

    def wrong_target(root, c):
        obj = read(c['protocol']['scorer_inputs_ref'])
        obj['records'][0]['frame_id'] = '99'
        replace_artifact(root, c, 'scorer_inputs_ref', obj, True)
    check('scorer frame identity differs from frozen window', wrong_target,
          'scorer target identities do not exactly match')

    def copied_history(root, c):
        obj = read(c['protocol']['scorer_inputs_ref'])
        obj['records'][0]['frame_id'] = '0'
        replace_artifact(root, c, 'scorer_inputs_ref', obj, True)
    check('different paths cannot disguise same history/outcome identity', copied_history,
          'predictor history and scorer targets overlap by full identity')

    def wrong_command(root, c):
        obj = read(c['protocol']['predictor_inputs_ref'])
        next(row for row in obj['records'] if row['role'] == 'command_camera')['frame_id'] = '99'
        replace_artifact(root, c, 'predictor_inputs_ref', obj, True)
    check('command camera must address an actual declared target', wrong_command,
          'command camera identities do not exactly match')
    check('window needs sequence identity',
          lambda r, c: c['protocol']['windows'][0].pop('sequence_id'),
          'window dataset/scene/sequence identity missing')
    check('normalized duplicate frame IDs rejected',
          lambda r, c: c['protocol']['windows'][0].update(history_ids=[0, '0', 1, 2]),
          'duplicate normalized frame identities')
    check('output budget cannot differ from effective four targets',
          lambda r, c: c['protocol']['budget'].update(output_count=5),
          'output budget differs from effective target frame count')
    check('selection count cannot differ from effective four context frames',
          lambda r, c: c['protocol']['budget'].update(selection_k=3),
          'selection budget differs from effective context frame count')
    check('window cannot add a fifth target while config produces four',
          lambda r, c: c['protocol']['windows'][0]['target_ids'].append(8),
          'window target count differs from effective config')

    def stale_wrapper(root, c):
        c['protocol']['predictor_wrapper_ref'] = put(root, 'replacement_wrapper.py', '# different synthetic wrapper\n')
    check('old isolation receipt cannot approve replacement wrapper', stale_wrapper,
          'isolation probe does not bind current predictor wrapper')
    def stale_scorer(root, c):
        obj = read(c['protocol']['scorer_inputs_ref']); obj['revision'] = 'changed synthetic outcome manifest'
        replace_artifact(root, c, 'scorer_inputs_ref', obj)
    check('isolation must bind current outcome manifest', stale_scorer,
          'isolation probe does not bind current scorer/outcome manifest')
    def stale_runtime(root, c):
        obj = read(c['protocol']['runtime_binding_ref']); obj['launcher_revision'] = 'changed synthetic launcher'
        replace_artifact(root, c, 'runtime_binding_ref', obj)
    check('isolation must bind current runtime definition', stale_runtime,
          'isolation probe does not bind runtime configuration')
    check('boundary identifier cannot be silently replaced',
          lambda r, c: c['protocol']['isolation'].update(execution_boundary_id='DIFFERENT_SYNTHETIC_BOUNDARY'),
          'isolation/runtime execution boundary identifier mismatch')
    check('probe must attest exact staging root',
          lambda r, c: c['protocol']['isolation'].update(predictor_root=str(r)),
          'isolation probe does not bind the current predictor staging root')
    receipt = {'schema': 'gate0-v2-window-isolation-regression-v1',
               'recorded_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'validator_sha256': ref(VALIDATOR)['sha256'], 'script_sha256': ref(Path(__file__))['sha256'],
               'scope': 'Synthetic software regressions only. No research data, model, SSH, GPU or job dispatch.',
               'status': 'PASS' if all(x['passed'] for x in cases) else 'FAIL',
               'passed': sum(x['passed'] for x in cases), 'total': len(cases), 'cases': cases}
    path = HERE / 'V2_WINDOW_ISOLATION_REGRESSION_RECEIPT.json'
    path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'passed': receipt['passed'],
                      'total': receipt['total'], 'receipt': str(path)}, indent=2))
    return 0 if receipt['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
