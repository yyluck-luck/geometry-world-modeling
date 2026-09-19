#!/usr/bin/env python3
"""Evidence-bound Gate0 pre-run readiness and separate post-run acceptance.

This file does not change any existing contract and cannot submit a job. Run it on
the same filesystem used by the predictor, with an explicit local contract path:
  python validate_gate0_v2.py CONTRACT.json --stage pre-run
  python validate_gate0_v2.py CONTRACT.json --stage post-run
  python validate_gate0_v2.py --template
  python validate_gate0_v2.py --self-test

Schema: {schema, protocol, review_ref, post_run}. protocol contains only frozen
pre-run facts; review_ref binds its canonical JSON SHA, avoiding circular hashes.
Every *_ref is {path, sha256, bytes}. Relative paths resolve against the contract.
Future outcome paths are declared in a scorer manifest, but never opened in the
pre-run stage. The predictor manifest contains only allowed, staged input files.
An explicit independent review is still needed: matching hashes alone do not
prove camera calibration, a good research design, or model effectiveness.

Exit 0: ready/accepted for the displayed scope; 2: incomplete/failed evidence;
3: malformed contract or runtime exception. No pre-run check requires predictions.
"""
from __future__ import annotations
import argparse
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

SCHEMA = 'gwm-gate0-staged-v2'
HEX = re.compile(r'^[0-9a-f]{64}$')
HISTORY_ROLES = {'history_rgb', 'history_depth', 'history_pose'}
STATIC_PREDICTOR_ROLES = {'camera_intrinsics'}
OUTCOME_ROLES = {'future_rgb', 'future_depth', 'future_pose'}
SCOPES = {'development_baseline', 'heldout_baseline', 'heldout_method'}
CONFIG_KEYS = ('model.height', 'model.width', 'model.context_num_frames',
               'model.target_num_frames', 'model.num_frames', 'model.inference_num_steps', 'seed')
IDENTITY_KEYS = ('dataset_id', 'scene_id', 'sequence_id')

def frame_identity(record):
    """Use dataset/scene/sequence as well as the normalized frame identifier."""
    return tuple(record[key] for key in IDENTITY_KEYS) + (str(record['frame_id']),)

def positive_int(value):
    return type(value) is int and value > 0

def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()

def independent_reviewer(review, author):
    """Require a named reviewer whose normalized identity differs from the author."""
    reviewer = review.get('reviewer') if isinstance(review, dict) else None
    return (isinstance(reviewer, str) and bool(reviewer.strip()) and
            reviewer.strip() != str(author or '').strip())

def substantive_review(review):
    """Require auditable findings and an explicit limitations list."""
    if not isinstance(review, dict):
        return False
    findings = review.get('findings')
    limitations = review.get('limitations')
    return (isinstance(findings, list) and bool(findings) and
            all(isinstance(item, str) and bool(item.strip()) for item in findings) and
            isinstance(limitations, list) and
            all(isinstance(item, str) and bool(item.strip()) for item in limitations))

def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def lookup(obj, dotted):
    for key in dotted.split('.'):
        obj = obj[key]
    return obj

class Check:
    def __init__(self, base):
        self.base = Path(base).resolve()
        self.errors = []
        self.verified = []

    def need(self, condition, message):
        if not condition:
            self.errors.append(message)
        return bool(condition)

    def path(self, value):
        p = Path(value)
        return (p if p.is_absolute() else self.base / p).resolve()

    def artifact(self, ref, label, parse=None):
        if not self.need(isinstance(ref, dict), label + ': missing file descriptor'):
            return None
        try:
            path = self.path(ref['path'])
            if not self.need(path.is_file(), label + ': file does not exist: ' + str(path)):
                return None
            if not self.need(isinstance(ref.get('sha256'), str) and HEX.fullmatch(ref['sha256']),
                             label + ': invalid SHA-256'):
                return None
            ok = self.need(path.stat().st_size == ref.get('bytes'), label + ': size mismatch')
            actual = file_sha(path)
            ok = self.need(actual == ref['sha256'], label + ': SHA-256 mismatch') and ok
            if not ok:
                return None
            self.verified.append({'label': label, 'path': str(path), 'sha256': actual})
            if parse == 'json':
                return json.loads(path.read_text())
            if parse == 'config':
                if path.suffix.lower() == '.json':
                    return json.loads(path.read_text())
                try:
                    import yaml
                except ImportError:
                    self.errors.append(label + ': use the project Python with PyYAML, or an effective JSON config')
                    return None
                return yaml.safe_load(path.read_text())
            return path
        except (KeyError, TypeError, ValueError, OSError) as exc:
            self.errors.append(label + ': ' + str(exc))
            return None

    def declared_records(self, obj, label):
        if not self.need(isinstance(obj, dict) and isinstance(obj.get('records'), list)
                         and len(obj['records']) > 0, label + ': empty/missing records'):
            return []
        records = obj['records']
        identities = []
        for record in records:
            try:
                self.need(all(isinstance(record[key], str) and record[key].strip()
                              for key in IDENTITY_KEYS), label + ': incomplete dataset/scene/sequence identity')
                self.need(isinstance(record['frame_id'], (str, int)) and
                          not isinstance(record['frame_id'], bool) and str(record['frame_id']).strip(),
                          label + ': invalid frame identity')
                identities.append(frame_identity(record) + (record['role'],))
            except (KeyError, TypeError):
                self.errors.append(label + ': incomplete identity/role')
        self.need(len(identities) == len(set(identities)), label + ': duplicate identities')
        return records

def validate(contract, base, stage='pre-run'):
    c = Check(base)
    c.need(contract.get('schema') == SCHEMA, 'wrong schema')
    p = contract.get('protocol', {})
    c.need(isinstance(p, dict), 'protocol must be an object')
    if not isinstance(p, dict):
        p = {}
    scope = p.get('scope')
    c.need(scope in SCOPES, 'scope must be development_baseline, heldout_baseline, or heldout_method')
    c.need(bool(p.get('run_id')), 'run_id missing')
    c.need(p.get('status') == 'FROZEN', 'protocol is not frozen')
    c.need(bool(p.get('author')), 'protocol author missing')

    # A review of frozen pre-run material is required, never a post-run score.
    review = c.artifact(contract.get('review_ref'), 'independent pre-run review', 'json') or {}
    c.need(review.get('verdict') == 'PRE_RUN_APPROVED', 'independent pre-run review not approved')
    c.need(independent_reviewer(review, p.get('author')),
           'pre-run reviewer must differ from protocol author')
    c.need(review.get('protocol_sha256') == canonical_sha(p), 'review does not bind current protocol SHA')
    c.need(substantive_review(review),
           'independent pre-run review must contain non-empty findings and an explicit limitations list')

    cfg = c.artifact(p.get('effective_config_ref'), 'effective runtime config', 'config')
    expected = p.get('expected_config', {})
    for key in CONFIG_KEYS:
        if not c.need(key in expected, 'expected config missing: ' + key):
            continue
        if cfg is not None:
            try:
                c.need(lookup(cfg, key) == expected[key], 'effective config mismatch: ' + key)
            except (KeyError, TypeError):
                c.need(False, 'effective config missing: ' + key)
    if cfg is not None:
        try:
            m = cfg['model']
            c.need(m['num_frames'] == m['context_num_frames'] + m['target_num_frames'],
                   'total frame count differs from context plus target')
            c.need(m['height'] > 0 and m['width'] > 0 and m['height'] % 8 == 0 and m['width'] % 8 == 0,
                   'model dimensions invalid for declared VAE spatial scale')
        except (KeyError, TypeError):
            c.need(False, 'effective frame/dimension fields incomplete')

    source = c.artifact(p.get('source_manifest_ref'), 'source manifest', 'json') or {}
    c.need(bool(source.get('files')), 'source manifest is empty')
    for i, ref in enumerate(source.get('files', [])):
        c.artifact(ref, 'source file ' + str(i))
    runtime = c.artifact(p.get('runtime_binding_ref'), 'runtime bindings', 'json') or {}
    c.need(runtime.get('effective_config_sha256') == (p.get('effective_config_ref') or {}).get('sha256'),
           'runtime does not bind effective config hash')
    c.need(runtime.get('source_manifest_sha256') == (p.get('source_manifest_ref') or {}).get('sha256'),
           'runtime does not bind source manifest hash')
    checkpoints = p.get('checkpoints', {})
    required = {'vmem', 'vae', 'clip'} | ({'cut3r'} if p.get('uses_cut3r') else set())
    c.need(required <= set(checkpoints), 'required checkpoint descriptor missing')
    for name in required:
        actual = c.artifact(checkpoints.get(name), name + ' checkpoint')
        bound = runtime.get('checkpoint_paths', {}).get(name)
        c.need(actual is not None and bound is not None and actual == c.path(bound),
               name + ': runtime checkpoint path mismatch')
    c.need(p.get('vae_variant') in {'original_verified', 'declared_substitute'}, 'VAE variant must be explicit')

    predictor = c.artifact(p.get('predictor_inputs_ref'), 'predictor input manifest', 'json')
    scorer = c.artifact(p.get('scorer_inputs_ref'), 'scorer input manifest', 'json')
    # Scorer manifest metadata is read, but not the outcome files it references.
    pred = c.declared_records(predictor, 'predictor inputs')
    score = c.declared_records(scorer, 'scorer inputs')
    camera_policy = p.get('target_camera_policy')
    c.need(camera_policy in {'predeclared_command', 'predicted_by_model'}, 'target camera policy undefined')
    roots = p.get('isolation', {})
    staged = c.path(roots.get('predictor_root', '__MISSING_PREDICTOR_ROOT__'))
    outcome_paths = set()
    for row in score:
        c.need(row.get('role') in OUTCOME_ROLES, 'scorer record has non-outcome role')
        try:
            outcome_paths.add(c.path(row['file']['path']))
        except (KeyError, TypeError):
            c.need(False, 'scorer file path missing')
    for row in pred:
        role = row.get('role')
        c.need(role in HISTORY_ROLES or role in STATIC_PREDICTOR_ROLES or
               (role == 'command_camera' and camera_policy == 'predeclared_command'),
               'predictor role not allowed: ' + str(role))
        path = c.artifact(row.get('file'), 'predictor input ' + str(row.get('frame_id')))
        if path is not None:
            c.need(path.is_relative_to(staged), 'predictor input escapes staging root')
            c.need(path not in outcome_paths, 'outcome file also supplied to predictor')
            c.need(path.suffix.lower() not in {'.zip', '.tar', '.tgz', '.gz'}, 'whole archives cannot be predictor inputs')
    c.need(bool(pred) and any(x.get('role') == 'history_rgb' for x in pred), 'no history RGB input')
    intrinsics = [x for x in pred if x.get('role') == 'camera_intrinsics']
    c.need(len(intrinsics) == 1, 'exactly one hashed camera_intrinsics input is required')
    if intrinsics:
        try:
            c.need(Path(intrinsics[0]['file']['path']).suffix.lower() == '.json',
                   'camera_intrinsics input must be a JSON artifact')
        except (KeyError, TypeError):
            c.need(False, 'camera_intrinsics file descriptor missing')
    if camera_policy == 'predeclared_command':
        c.need(any(x.get('role') == 'command_camera' for x in pred), 'declared target camera command absent')

    isolation = c.artifact(roots.get('receipt_ref'), 'runtime isolation preflight', 'json') or {}
    c.need(isolation.get('method') in {'container_mount_whitelist', 'linux_namespace', 'separate_user_acl'},
           'isolation must be an enforced runtime boundary, not a substring guard')
    for key in ['allowed_history_probe_passed', 'denied_outcome_probe_passed', 'full_archive_unavailable']:
        c.need(isolation.get(key) is True, 'isolation probe missing/failed: ' + key)
    c.need(isolation.get('predictor_inputs_sha256') == (p.get('predictor_inputs_ref') or {}).get('sha256'),
           'isolation probe does not bind predictor manifest')
    c.need(isolation.get('runtime_binding_sha256') == (p.get('runtime_binding_ref') or {}).get('sha256'),
           'isolation probe does not bind runtime configuration')
    c.need(isolation.get('scorer_inputs_sha256') == (p.get('scorer_inputs_ref') or {}).get('sha256'),
           'isolation probe does not bind current scorer/outcome manifest')
    wrapper_sha = (p.get('predictor_wrapper_ref') or {}).get('sha256')
    c.need(isinstance(wrapper_sha, str) and HEX.fullmatch(wrapper_sha), 'predictor wrapper SHA missing/invalid')
    c.need(isolation.get('predictor_wrapper_sha256') == wrapper_sha,
           'isolation probe does not bind current predictor wrapper')
    c.need(runtime.get('predictor_wrapper_sha256') == wrapper_sha,
           'runtime does not bind current predictor wrapper')
    boundary_id = roots.get('execution_boundary_id')
    c.need(isinstance(boundary_id, str) and bool(boundary_id.strip()), 'execution boundary identifier missing')
    c.need(isolation.get('execution_boundary_id') == boundary_id and
           runtime.get('execution_boundary_id') == boundary_id,
           'isolation/runtime execution boundary identifier mismatch')
    # The launcher may be tested from a login node and executed on a compute node.
    # Bind the tested boundary implementation, not incidental host/user labels.
    probe_root = isolation.get('predictor_root')
    c.need(isinstance(probe_root, str) and c.path(probe_root) == staged,
           'isolation probe does not bind the current predictor staging root')

    adapters = p.get('datasets', {})
    for dataset in sorted({x.get('dataset_id', '') for x in pred + score}):
        data = adapters.get(dataset, {})
        c.need(bool(data), 'dataset contract missing: ' + dataset)
        camera = data.get('camera', {})
        c.need(camera.get('calibration_status') == 'verified', dataset + ': calibration unverified')
        k = camera.get('K')
        c.need(isinstance(k, list) and len(k) == 3 and all(isinstance(x, list) and len(x) == 3 for x in k),
               dataset + ': invalid K dimensions')
        c.need(camera.get('rgb_depth_registration') in {'registered', 'explicit_extrinsic_transform'},
               dataset + ': RGB-depth registration missing')
        for key in ['pixel_center_convention', 'resize_crop_K_rule', 'pose_time_association']:
            c.need(bool(camera.get(key)), dataset + ': camera rule missing: ' + key)
        depth = data.get('depth', {})
        c.need(depth.get('raw_to_metres_divisor', 0) > 0, dataset + ': invalid depth scale')
        c.need(bool(depth.get('invalid_values')), dataset + ': missing invalid depth rule')
        c.need(depth.get('interpretation') in {'optical_axis_z', 'radial_with_frozen_conversion'},
               dataset + ': missing depth interpretation')
        c.artifact(data.get('adapter_ref'), dataset + ' adapter')
        adapter_author = data.get('adapter_author')
        c.need(isinstance(adapter_author, str) and bool(adapter_author.strip()),
               dataset + ': adapter author identity missing')
        evidence = c.artifact(data.get('adapter_review_ref'), dataset + ' adapter review', 'json') or {}
        c.need(evidence.get('status') == 'ADAPTER_ACCEPTED' and
               evidence.get('adapter_sha256') == data.get('adapter_ref', {}).get('sha256'),
               dataset + ': adapter not independently bound')
        c.need(independent_reviewer(evidence, p.get('author')),
               dataset + ': adapter reviewer must differ from protocol author')
        c.need(independent_reviewer(evidence, adapter_author),
               dataset + ': adapter reviewer must differ from adapter author')
        c.need(substantive_review(evidence),
               dataset + ': adapter review must contain non-empty findings and an explicit limitations list')

    evaluation_scenes = {x.get('scene_id') for x in score}
    calibration_scenes = set(p.get('calibration_scene_ids', []))
    if scope in {'heldout_baseline', 'heldout_method'}:
        c.need(bool(evaluation_scenes) and evaluation_scenes.isdisjoint(calibration_scenes),
               'held-out evaluation scene overlaps calibration')
        exposure = c.artifact(p.get('heldout_exposure_review_ref'), 'held-out exposure review', 'json') or {}
        c.need(exposure.get('status') == 'HELDOUT_PROTOCOL_ACCEPTED' and
               set(exposure.get('evaluation_scene_ids', [])) == evaluation_scenes,
               'held-out protocol/scope not accepted')
        if scope == 'heldout_method':
            baseline = c.artifact(p.get('baseline_acceptance_ref'), 'baseline result acceptance', 'json') or {}
            c.need(baseline.get('status') == 'POST_RUN_ACCEPTED', 'method comparison lacks accepted baseline')
    else:
        c.need(p.get('development_data_exposed') is True, 'development exposure must be declared')

    # Quantitative comparisons need concrete windows and an explicit fixed budget.
    windows = p.get('windows', [])
    c.need(isinstance(windows, list) and bool(windows), 'history/future windows are not frozen')
    context_count = expected.get('model.context_num_frames')
    target_count = expected.get('model.target_num_frames')
    c.need(positive_int(context_count), 'expected context frame count must be a positive integer')
    c.need(positive_int(target_count), 'expected target frame count must be a positive integer')
    declared_history, declared_targets = set(), set()
    window_history_counts = []
    for window in windows:
        if not c.need(isinstance(window, dict), 'window must be an object'):
            continue
        if not c.need(all(isinstance(window.get(key), str) and window[key].strip()
                          for key in IDENTITY_KEYS), 'window dataset/scene/sequence identity missing'):
            continue
        history_ids, target_ids = window.get('history_ids', []), window.get('target_ids', [])
        valid_ids = lambda ids: isinstance(ids, list) and bool(ids) and all(
            isinstance(x, (str, int)) and not isinstance(x, bool) and str(x).strip() for x in ids)
        if not c.need(valid_ids(history_ids) and valid_ids(target_ids), 'window frame IDs missing/invalid'):
            continue
        prefix = tuple(window[key] for key in IDENTITY_KEYS)
        history = {prefix + (str(x),) for x in history_ids}
        targets = {prefix + (str(x),) for x in target_ids}
        c.need(len(history) == len(history_ids) and len(targets) == len(target_ids),
               'window contains duplicate normalized frame identities')
        c.need(history.isdisjoint(targets), 'window history/target identities overlap')
        c.need(len(targets) == target_count, 'window target count differs from effective config')
        declared_history.update(history)
        declared_targets.update(targets)
        window_history_counts.append(len(history))
        c.need(window.get('chronological') is True, 'window chronology must be declared and adapter-reviewed')
    c.need(declared_history.isdisjoint(declared_targets), 'history/target full identities overlap across windows')
    def role_identities(records, roles):
        found = set()
        for row in records:
            if isinstance(row, dict) and row.get('role') in roles:
                try:
                    found.add(frame_identity(row))
                except (KeyError, TypeError):
                    c.need(False, 'cannot bind manifest frame identity to windows')
        return found
    pred_history = role_identities(pred, HISTORY_ROLES)
    score_targets = role_identities(score, OUTCOME_ROLES)
    c.need(pred_history == declared_history, 'predictor history identities do not exactly match declared windows')
    c.need(role_identities(pred, {'history_rgb'}) == declared_history,
           'each declared history frame needs exactly one RGB record')
    c.need(score_targets == declared_targets, 'scorer target identities do not exactly match declared windows')
    c.need(role_identities(score, {'future_rgb'}) == declared_targets,
           'each declared target frame needs exactly one future RGB record')
    c.need(pred_history.isdisjoint(score_targets), 'predictor history and scorer targets overlap by full identity')
    if camera_policy == 'predeclared_command':
        c.need(role_identities(pred, {'command_camera'}) == declared_targets,
               'command camera identities do not exactly match declared targets')
    budget = p.get('budget', {})
    for key in ['candidate_count', 'selection_k', 'output_count', 'sampling_steps', 'dtype',
                'rng_policy', 'timeout_seconds', 'metric_definition_ref']:
        c.need(key in budget, 'budget missing: ' + key)
    selection_k, candidate_count = budget.get('selection_k'), budget.get('candidate_count')
    counts_valid = positive_int(selection_k) and positive_int(candidate_count)
    c.need(counts_valid and selection_k <= candidate_count, 'invalid selection budget')
    c.need(selection_k == context_count, 'selection budget differs from effective context frame count')
    c.need(budget.get('output_count') == target_count, 'output budget differs from effective target frame count')
    c.need(all(n == candidate_count for n in window_history_counts), 'window history count differs from candidate budget')
    if scope in {'development_baseline', 'heldout_baseline'}:
        c.need(candidate_count == context_count, 'selector-free baseline candidate count differs from context frame count')
    c.need(budget.get('sampling_steps') == expected.get('model.inference_num_steps'), 'budget/config steps mismatch')
    c.artifact(budget.get('metric_definition_ref'), 'metric definition')
    c.artifact(p.get('predictor_wrapper_ref'), 'predictor wrapper')
    c.artifact(p.get('scorer_ref'), 'scorer implementation')
    c.artifact(p.get('verifier_ref'), 'independent verifier implementation')
    c.artifact(p.get('validator_ref'), 'Gate0 validator implementation')

    pre_ready = not c.errors
    if stage == 'post-run':
        post = contract.get('post_run', {})
        seal = c.artifact(post.get('prediction_seal_ref'), 'prediction seal', 'json') or {}
        scoring = c.artifact(post.get('scoring_receipt_ref'), 'scoring receipt', 'json') or {}
        recompute = c.artifact(post.get('independent_recompute_ref'), 'independent metric recompute', 'json') or {}
        for label, obj in [('seal', seal), ('scoring', scoring), ('recompute', recompute)]:
            c.need(obj.get('run_id') == p.get('run_id'), label + ': run_id mismatch')
            c.need(obj.get('protocol_sha256') == canonical_sha(p), label + ': protocol hash mismatch')
        c.need(bool(seal.get('files')), 'prediction seal contains no output files')
        for i, ref in enumerate(seal.get('files', [])):
            c.artifact(ref, 'sealed prediction ' + str(i))
        c.need(seal.get('predictor_exit_code') == 0 and seal.get('unauthorized_input_reads') == 0,
               'prediction failed or unauthorized input was read')
        try:
            sealed_at = dt.datetime.fromisoformat(seal['sealed_at_utc'])
            opened_at = dt.datetime.fromisoformat(scoring['outcomes_first_opened_at_utc'])
            c.need(sealed_at.tzinfo is not None and opened_at.tzinfo is not None and opened_at >= sealed_at,
                   'future outcome opened before seal or timestamp timezone absent')
        except (KeyError, TypeError, ValueError):
            c.need(False, 'valid seal and first-outcome timestamps required')
        c.need(scoring.get('prediction_seal_sha256') == (post.get('prediction_seal_ref') or {}).get('sha256'),
               'scorer did not bind prediction seal')
        metrics = c.artifact(scoring.get('metrics_ref'), 'scored metrics')
        c.need(metrics is not None and recompute.get('metrics_sha256') == (scoring.get('metrics_ref') or {}).get('sha256'),
               'independent recompute did not bind metrics')
        c.need(recompute.get('status') == 'METRICS_RECOMPUTED_MATCH', 'independent metric recompute did not match')
        c.need(bool(recompute.get('reviewer')) and recompute.get('reviewer') != p.get('author'),
               'independent recompute reviewer missing/same author')

    return {'schema': SCHEMA, 'stage': stage, 'scope': scope, 'run_id': p.get('run_id'),
            'status': ('PRE_RUN_READY' if stage == 'pre-run' else 'POST_RUN_ACCEPTED') if not c.errors else 'BLOCKED',
            'pre_run_ready': pre_ready, 'protocol_sha256': canonical_sha(p),
            'errors': c.errors, 'verified_artifacts': c.verified,
            'opens_future_outcome_files': False,
            'scientific_method_validated': False,
            'note': 'Readiness is scoped execution permission; scientific conclusions require post-run acceptance and an appropriate design.'}

def template():
    return {'schema': SCHEMA, 'protocol': {'status': 'DRAFT', 'run_id': None, 'author': None,
            'scope': 'development_baseline', 'development_data_exposed': True,
            'effective_config_ref': None, 'expected_config': {x: None for x in CONFIG_KEYS},
            'source_manifest_ref': None, 'runtime_binding_ref': None,
            'uses_cut3r': True, 'checkpoints': {'vmem': None, 'vae': None, 'clip': None, 'cut3r': None},
            'vae_variant': 'declared_substitute', 'predictor_inputs_ref': None, 'scorer_inputs_ref': None,
            'target_camera_policy': 'predeclared_command',
            'isolation': {'predictor_root': None, 'execution_boundary_id': None, 'receipt_ref': None},
            'datasets': {}, 'calibration_scene_ids': [], 'heldout_exposure_review_ref': None,
            'baseline_acceptance_ref': None, 'windows': [], 'budget': {},
            'predictor_wrapper_ref': None, 'scorer_ref': None, 'verifier_ref': None,
            'validator_ref': None},
            'review_ref': None, 'post_run': {}}

def self_test():
    """Narrow regression: absent outputs never block pre-run; false evidence never passes."""
    checks = []
    with tempfile.TemporaryDirectory(prefix='gate0-v2-test-') as temp:
        root = Path(temp)
        c = Check(root)
        p = root / 'present'; p.write_text('synthetic fixture only')
        ref = {'path': str(p), 'sha256': file_sha(p), 'bytes': p.stat().st_size}
        checks.append(('real artifact accepted', c.artifact(ref, 'fixture') == p.resolve()))
        wrong = dict(ref, sha256='0' * 64)
        checks.append(('wrong hash blocked', Check(root).artifact(wrong, 'fixture') is None))
        missing = dict(ref, path=str(root / 'absent'))
        checks.append(('absent artifact blocked', Check(root).artifact(missing, 'fixture') is None))
        malformed = template(); malformed['protocol']['isolation']['predictor_root'] = str(root / 'staged')
        result = validate(malformed, root, 'pre-run')
        checks.append(('draft cannot pass', result['status'] == 'BLOCKED'))
        checks.append(('pre-run does not require predictions', not any('prediction seal' in x or
                       'metric recompute' in x for x in result['errors'])))
        post = validate(malformed, root, 'post-run')
        checks.append(('post-run requires real prediction seal', any('prediction seal' in x for x in post['errors'])))
        checks.append(('all production modes avoid opening outcome payloads', not result['opens_future_outcome_files']))
        checks.append(('same-author review identity rejected',
                       not independent_reviewer({'reviewer': ' codex-root-20260916 '},
                                                'codex-root-20260916')))
        checks.append(('different reviewer identity accepted',
                       independent_reviewer({'reviewer': 'external-reviewer-1'},
                                            'codex-root-20260916')))
        checks.append(('empty review substance rejected',
                       not substantive_review({'findings': [], 'limitations': []})))
        checks.append(('findings and explicit limitations accepted',
                       substantive_review({'findings': ['hash and convention checked'],
                                           'limitations': ['development-only scope']})))
    print(json.dumps({'test_scope': 'synthetic software checks only', 'checks': checks,
                      'status': 'PASS' if all(x[1] for x in checks) else 'FAIL'}, indent=2))
    return 0 if all(x[1] for x in checks) else 2

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('contract', nargs='?')
    ap.add_argument('--stage', choices=['pre-run', 'post-run'], default='pre-run')
    ap.add_argument('--template', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if args.template:
        print(json.dumps(template(), indent=2)); return 0
    if args.self_test:
        return self_test()
    if not args.contract:
        ap.error('contract path is required')
    path = Path(args.contract).resolve()
    try:
        obj = json.loads(path.read_text())
        result = validate(obj, path.parent, args.stage)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'status': 'MALFORMED', 'error': str(exc)}, indent=2)); return 3
    print(json.dumps(result, indent=2))
    return 0 if result['status'] != 'BLOCKED' else 2

if __name__ == '__main__':
    raise SystemExit(main())
