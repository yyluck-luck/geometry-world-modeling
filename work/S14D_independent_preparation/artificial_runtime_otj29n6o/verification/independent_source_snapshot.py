#!/usr/bin/env python3
"""Independent post-run S14D ray-only probe validation. Never imports the model.

The trained encoding is origin=t, direction=normalize(R K^-1 [u,v,1] + t).
This deliberately retains translation inside encoded_direction.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import traceback
from datetime import datetime, timezone

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ATOL, RTOL = 1e-6, 1e-5
SIZE = 224
FIELDS = ['state_feat', 'state_pos', 'init_state_feat', 'mem', 'init_mem']
INPUT_KEYS = ['history_pose_encodings', 'history_poses', 'target_poses', 'K', 'ray_maps']
REQUIRED_OUTPUTS = ['pts3d_in_self_view', 'pts3d_in_other_view', 'conf_self', 'conf', 'camera_pose']
FILES = ['probe_inputs.npz', 'query_outputs.npz', 'state_before.npz', 'state_after.npz']
TARGET_INDICES = [0, 0, 1, 2, 3]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def array_sha(value):
    return digest(np.ascontiguousarray(value).tobytes(order='C'))


def read_json(data):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError('Duplicate JSON key: ' + key)
            out[key] = value
        return out
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False, ensure_ascii=False, default=repr) + '\n')


def require(condition, label):
    if not condition:
        raise ValueError(label)


class Audit:
    """Count meaningful field/array checks rather than individual scalar elements."""
    def __init__(self):
        self.checks = []
        self.max_abs_difference = 0.0

    def exact(self, observed, reference, label):
        if observed != reference:
            self.checks.append({'label': label, 'status': 'FAIL', 'observed': observed, 'reference': reference})
            raise ValueError('Exact mismatch: ' + label)
        self.checks.append({'label': label, 'status': 'PASS', 'kind': 'exact'})

    def same_array(self, observed, reference, label):
        require(observed.shape == reference.shape and observed.dtype == reference.dtype, label + ': shape/dtype')
        self.exact(array_sha(observed), array_sha(reference), label + ': exact bytes')

    def close(self, observed, reference, label):
        observed, reference = np.asarray(observed), np.asarray(reference, dtype=np.float64)
        require(observed.shape == reference.shape, label + ': shape')
        require(np.isfinite(observed).all() and np.isfinite(reference).all(), label + ': finite')
        delta = np.abs(observed.astype(np.float64) - reference)
        bound = ATOL + RTOL * np.abs(reference)
        maximum = float(delta.max(initial=0.))
        self.max_abs_difference = max(self.max_abs_difference, maximum)
        failed = np.argwhere(delta > bound)
        row = {'label': label, 'status': 'PASS' if len(failed) == 0 else 'FAIL', 'kind': 'numeric',
               'shape': list(reference.shape), 'elements': int(reference.size), 'max_abs_difference': maximum}
        if len(failed):
            index = tuple(failed[0])
            row.update(first_bad_index=list(index), observed=float(observed[index]),
                       reference=float(reference[index]), bound=float(bound[index]))
        self.checks.append(row)
        require(len(failed) == 0, 'Floating mismatch: ' + label)


def decode_npz(data, name, audit):
    with np.load(io.BytesIO(data), allow_pickle=False) as package:
        audit.exact(len(package.files), len(set(package.files)), name + ': unique keys')
        values = {key: package[key] for key in package.files}
    for key, value in values.items():
        require(value.dtype.kind in 'biuf', name + '/' + key + ': numeric non-object dtype')
        require(value.size > 0 and np.isfinite(value).all(), name + '/' + key + ': finite nonempty array')
        audit.checks.append({'label': name + '/' + key + ': array validity', 'status': 'PASS',
                             'shape': list(value.shape), 'dtype': str(value.dtype), 'sha256': array_sha(value)})
    return values


def decode_history_pose(encodings):
    """Quaternion Rodrigues form, independent of the official element formula."""
    require(np.shape(encodings) == (20, 7), '20 history translation/quaternion encodings')
    output = []
    for encoding in np.asarray(encodings, dtype=np.float64):
        t, q = encoding[:3], encoding[3:]
        norm = math.hypot(*q)
        require(math.isfinite(norm) and norm > 0, 'nonzero finite quaternion')
        w, x, y, z = [float(v / norm) for v in q]
        vector = [x, y, z]
        skew = [[0., -z, y], [z, 0., -x], [-y, x, 0.]]
        diagonal = w*w - math.fsum(v*v for v in vector)
        pose = np.eye(4, dtype=np.float64)
        for i in range(3):
            for j in range(3):
                pose[i, j] = (diagonal if i == j else 0.) + 2*vector[i]*vector[j] + 2*w*skew[i][j]
        pose[:3, 3] = t
        output.append(pose)
    return np.stack(output)


def make_targets(history):
    require(np.shape(history) == (20, 4, 4), '20 history poses')
    history = np.asarray(history, dtype=np.float64)
    origin = history[0, :3, 3]
    distances = [math.hypot(*(pose[:3, 3] - origin)) for pose in history]
    positives = [d for d in distances if d > 1e-6]
    require(bool(positives), 'positive history baseline exists')
    step = .05 * statistics.median(positives)
    require(math.isfinite(step) and step > 0, 'positive finite offset step')
    offsets = [[0., 0., 0.], [step, 0., 0.], [-step, 0., 0.], [0., 0., step]]
    anchor = history[-1]
    result = []
    for offset in offsets:
        pose = anchor.copy()
        for axis in range(3):
            pose[axis, 3] = float(anchor[axis, 3]) + math.fsum(float(anchor[axis, j])*offset[j] for j in range(3))
        result.append(pose)
    return np.stack(result), step, distances


def independent_rays(pose, K, height=SIZE, width=SIZE):
    """Pixel/axis expansion with math.fsum/hypot; no matrix-multiply ray helper."""
    pose, K = np.asarray(pose, dtype=np.float64), np.asarray(K, dtype=np.float64)
    require(pose.shape == (4, 4) and K.shape == (3, 3), 'ray pose/K shape')
    require(K[0, 0] > 0 and K[1, 1] > 0, 'positive focal lengths')
    require(np.array_equal(K, [[K[0, 0], 0., K[0, 2]], [0., K[1, 1], K[1, 2]], [0., 0., 1.]]),
            'fixed diagonal pseudo-intrinsics')
    t = [float(pose[i, 3]) for i in range(3)]
    rays = np.empty((height, width, 6), dtype=np.float64)
    for v in range(height):
        yc = (v - float(K[1, 2])) / float(K[1, 1])
        for u in range(width):
            xc = (u - float(K[0, 2])) / float(K[0, 0])
            encoded = [math.fsum([float(pose[i, 0])*xc, float(pose[i, 1])*yc,
                                  float(pose[i, 2]), t[i]]) for i in range(3)]
            norm = math.hypot(*encoded)
            require(math.isfinite(norm) and norm > 0, 'finite nonzero encoded direction')
            rays[v, u] = t + [value/norm for value in encoded]
    return rays


def verify_arrays(inputs, outputs, before, after, audit):
    audit.exact(set(inputs), set(INPUT_KEYS), 'fixed input NPZ members')
    shapes = {'history_pose_encodings': (20, 7), 'history_poses': (20, 4, 4), 'target_poses': (4, 4, 4),
              'K': (3, 3), 'ray_maps': (4, SIZE, SIZE, 6)}
    for name, shape in shapes.items():
        audit.exact(inputs[name].shape, shape, 'input shape/' + name)
    audit.exact(str(inputs['ray_maps'].dtype), 'float32', 'FP32 active ray maps')
    audit.close(inputs['history_poses'], decode_history_pose(inputs['history_pose_encodings']), 'history poses from new history encodings')
    targets, step, distances = make_targets(inputs['history_poses'])
    audit.close(inputs['target_poses'], targets, 'targets from latest history pose and local offsets')
    focal = math.sqrt(2 * SIZE * SIZE)
    expected_K = np.array([[focal, 0., 112.], [0., focal, 112.], [0., 0., 1.]])
    audit.close(inputs['K'], expected_K, 'official fixed pseudo K')
    for target in range(4):
        expected = independent_rays(inputs['target_poses'][target], inputs['K'])
        audit.close(inputs['ray_maps'][target], expected, f'all pixels official translated ray formula/target{target}')
    audit.exact(set(before), set(FIELDS), 'five anchor fields before')
    audit.exact(set(after), set(FIELDS), 'five anchor fields after')
    for field in FIELDS:
        audit.same_array(after[field], before[field], 'unchanged anchor/' + field)
    by_call = []
    consumed = set()
    for call in range(5):
        prefix = f'call{call}_'
        selected = {name[len(prefix):]: value for name, value in outputs.items() if name.startswith(prefix)}
        require(set(REQUIRED_OUTPUTS) <= set(selected), 'required query prediction tensors')
        if call:
            audit.exact(set(selected), set(by_call[0]), f'complete output tensor key set/call{call}')
            for key in selected:
                audit.exact(selected[key].shape, by_call[0][key].shape, f'output shape/call{call}/{key}')
                audit.exact(str(selected[key].dtype), str(by_call[0][key].dtype), f'output dtype/call{call}/{key}')
        for key in ['pts3d_in_self_view', 'pts3d_in_other_view']:
            audit.exact(selected[key].shape, (1, SIZE, SIZE, 3), f'geometry shape/call{call}/{key}')
        for key in ['conf_self', 'conf']:
            audit.exact(selected[key].shape, (1, SIZE, SIZE), f'confidence shape/call{call}/{key}')
        audit.exact(selected['camera_pose'].shape, (1, 7), f'pose-encoding shape/call{call}')
        by_call.append(selected)
        consumed.update(prefix + name for name in selected)
    audit.exact(consumed, set(outputs), 'all output NPZ members assigned to exactly one of five calls')
    for key in by_call[0]:
        audit.same_array(by_call[1][key], by_call[0][key], 'NaN versus zero dummy all output equality/' + key)
    response = []
    for call, target in [(2, 1), (3, 2), (4, 3)]:
        differences = {key: float(np.max(np.abs(by_call[call][key].astype(np.float64) - by_call[0][key].astype(np.float64))))
                       for key in ['pts3d_in_self_view', 'pts3d_in_other_view']}
        response.append({'call': call, 'target_index': target, 'geometry_max_abs_differences': differences,
                         'any_geometry_response_over_1e_6': max(differences.values()) > 1e-6})
    return {'offset_step': step, 'history_translation_distances': distances, 'response_diagnostics': response,
            'response_threshold': 1e-6, 'response_is_not_a_technical_pass_gate': True,
            'dummy_invariance_all_tensor_keys': list(by_call[0]),
            'state_reference_hashes': {field: array_sha(before[field]) for field in FIELDS}}


def verify_metadata(metadata, manifest, inputs, outputs, before, numerical, audit):
    audit.exact(metadata['schema'], 's14d-ray-only-probe-v1', 'probe metadata schema')
    audit.exact(metadata['status'], 'SUCCESS', 'technical run success')
    audit.exact(metadata['device'], 'cpu', 'CPU probe')
    for key in ['video_generated', 'new_model_trained', 'accuracy_evaluated']:
        audit.exact(metadata[key], False, 'scope/' + key)
    expected_counters = {'history_rgb_decoded': 20, 'query_rgb_decoded': 0, 'gt_files_decoded': 0,
                         'query_calls': 5, 'query_image_encoder_batches': 0, 'query_ray_encoder_calls': 5,
                         'history_image_open_attempts': 20, 'history_images_opened': 20, 'query_call_attempts': 5}
    audit.exact(metadata['counters'], expected_counters, '20 history RGB and ray-only query counters')
    for key in ['image_open_attempt_paths', 'image_opened_paths', 'decoded_image_paths']:
        audit.exact(metadata[key], [p['path'] for p in manifest['history_images']], 'actual ordered image boundary/' + key)
    audit.exact(metadata['ray_patch_embed'], 'PatchEmbedDust3R', 'audited ray patch-embedding interface')
    audit.exact(metadata['checkpoint_all_keys_matched'], True, 'checkpoint key match')
    audit.exact(metadata['weights_only'], True, 'recorded restricted checkpoint load')
    audit.exact(set(metadata['state_before']), set(FIELDS), 'state metadata field set')
    for field in FIELDS:
        expected = {'shape': list(before[field].shape), 'dtype': str(before[field].dtype), 'sha256': array_sha(before[field])}
        audit.exact(metadata['state_before'][field], expected, 'state-before identity/' + field)
    audit.exact(len(metadata['query_runs']), 5, 'five recorded direct query calls')
    run_start = datetime.fromisoformat(metadata['started_utc'])
    run_end = datetime.fromisoformat(metadata['completed_utc'])
    last_end = run_start
    for index, call in enumerate(metadata['query_runs']):
        audit.exact(call['call'], index, 'call order')
        audit.exact(call['target_index'], TARGET_INDICES[index], 'target call order')
        audit.exact(call['dummy'], 'zero' if index == 1 else 'nan', 'dummy call order')
        audit.exact(call['flags'], {'img_mask': [False], 'ray_mask': [True], 'update': [False], 'reset': [False]},
                    f'query flags/call{index}')
        audit.exact(call['state_hashes'], numerical['state_reference_hashes'], f'all five anchor hashes/call{index}')
        present = {name[len(f'call{index}_'):] for name in outputs if name.startswith(f'call{index}_')}
        audit.exact(set(call['output_keys']), present, f'all dynamic tensor outputs recorded/call{index}')
        audit.exact(len(call['output_keys']), len(present), f'no duplicate dynamic tensor output keys/call{index}')
        start, end = datetime.fromisoformat(call['started_utc']), datetime.fromisoformat(call['completed_utc'])
        require(last_end <= start <= end <= run_end, 'ordered bounded direct calls')
        last_end = end
        require(type(call['seconds']) in (int, float) and math.isfinite(call['seconds']) and call['seconds'] >= 0,
                'finite measured call duration')
        expected_shapes = {'img': [1, 3, SIZE, SIZE], 'ray_map': [1, SIZE, SIZE, 6],
                           'true_shape': [1, 2], 'camera_pose': [1, 4, 4]}
        audit.exact(call['input_shapes'], expected_shapes, f'query input shapes/call{index}')
        audit.exact(call['input_dtypes'], {'img': 'torch.float32', 'ray_map': 'torch.float32',
                                         'true_shape': 'torch.int64', 'camera_pose': 'torch.float32'},
                    f'query input dtypes/call{index}')
        audit.exact(call['true_shape'], [[SIZE, SIZE]], f'explicit H,W/call{index}')
        audit.close(np.array(call['target_camera_pose']), inputs['target_poses'][TARGET_INDICES[index]][None],
                    f'camera-pose input matches ray target/call{index}')
    audit.exact(metadata['dummy_all_outputs_exact'], True, 'declared dummy tensor invariance')
    audit.exact(len(metadata['response_diagnostics']), 3, 'three retained shifted target diagnostics')
    for reported, calculated in zip(metadata['response_diagnostics'], numerical['response_diagnostics']):
        for key in ['call', 'target_index']:
            audit.exact(reported[key], calculated[key], 'response identity/' + key)
        expected_difference = max(calculated['geometry_max_abs_differences'].values())
        audit.exact(reported['max_abs_geometry_difference'], expected_difference, 'response direct geometry maximum')
        audit.exact(reported['threshold'], 1e-6, 'fixed response threshold')
        audit.exact(reported['response_detected'], expected_difference > 1e-6, 'response boolean is diagnostic')
        audit.exact(reported['quality_evidence'], False, 'response is not quality evidence')
    audit.close(np.array(metadata['target_step']), np.array(numerical['offset_step']), 'recorded target offset scale')
    audit.close(np.asarray(metadata['history_distances']), np.asarray(numerical['history_translation_distances']),
                'recorded 20 history translation distances')
    audit.exact(metadata['before_after_identity_pass'], True, 'runner input/source identity verdict')


def verify_manifest(manifest, metadata, source_sha, audit):
    audit.exact(manifest['schema'], 's14d-ray-only-manifest-v1', 'manifest schema')
    identities = manifest['identities']
    require(isinstance(identities, dict) and bool(identities), 'nonempty frozen identity set')
    audit.exact(identities[str(Path(__file__).resolve())], source_sha, 'frozen independent source SHA')
    images = manifest['history_images']
    audit.exact(len(images), 20, 'exactly twenty frozen historical RGB files')
    paths = [item['path'] for item in images]
    audit.exact(len(set(paths)), 20, 'unique frozen history RGB identities')
    image_identity_paths = {path for path in identities if Path(path).suffix.lower() in ['.png', '.jpg', '.jpeg']}
    audit.exact(image_identity_paths, set(paths), 'no additional target image frozen as probe input')
    require(not any(Path(path).suffix.lower() in ['.npz', '.npy'] for path in identities),
            'no old prediction/query/GT array package is a frozen probe input')
    for item in images:
        path = Path(item['path'])
        require(path.is_absolute() and path.suffix.lower() in ['.png', '.jpg', '.jpeg'], 'absolute historical image path')
        require(path.resolve() == path, 'history file no path redirection')
        audit.exact(identities[str(path)], item['sha256'], 'history image bound in frozen identities')
    contract = manifest['contract']
    audit.exact(contract['call_target_indices'], TARGET_INDICES, 'frozen call target order')
    audit.exact(contract['query_dummy_values'], ['nan', 'zero', 'nan', 'nan', 'nan'], 'frozen dummy order')
    audit.exact(contract['response_threshold'], 1e-6, 'frozen response diagnostic threshold')
    # Complete contract is copied into the receipt. Formula and actual targets are
    # independently checked from saved arrays; no old query pose/scoring file is decoded.
    for name, module in metadata['loaded_upstream_modules'].items():
        path = Path(module['path'])
        require(path.is_relative_to(Path(manifest['repo'])) and path.suffix == '.py', 'loaded upstream module source path')
        audit.exact(identities[str(path)], module['sha256'], 'loaded upstream frozen source/' + name)
    return identities


def run(manifest_path, result, caller_path, output):
    output.mkdir(parents=True, exist_ok=False)
    audit = Audit()
    source_data, manifest_data, caller_data = Path(__file__).read_bytes(), manifest_path.read_bytes(), caller_path.read_bytes()
    source_sha, manifest_sha, caller_sha = digest(source_data), digest(manifest_data), digest(caller_data)
    (output / 'independent_source_snapshot.py').write_bytes(source_data)
    receipt = {'schema': 's14d-independent-ray-only-verification-v1', 'status': 'RUNNING', 'started_utc': now(),
               'python': sys.version, 'numpy': np.__version__, 'platform': platform.platform(),
               'source_sha256': source_sha, 'manifest_sha256': manifest_sha, 'caller_sha256': caller_sha,
               'atol': ATOL, 'rtol': RTOL, 'formula': 'origin=t; encoded_direction=normalize(R K^-1 [u,v,1]+t)',
               'target_images_decoded': 0, 'gt_or_quality_scores_decoded': 0, 'model_calls': 0,
               'response_is_technical_pass_gate': False, 'frozen_identity_before': {}, 'frozen_identity_after': {}}
    dump(output / 'verification.json', receipt)
    try:
        manifest, caller = read_json(manifest_data), read_json(caller_data)
        metadata_data = (result / 'run_metadata.json').read_bytes()
        metadata = read_json(metadata_data)
        audit.exact(metadata['manifest_sha256'], manifest_sha, 'run uses this frozen manifest')
        audit.exact(caller['schema'], 's14d-caller-v1', 'external caller schema')
        audit.exact(caller['status'], 'PASS', 'external caller complete status')
        audit.exact(caller['monitor_ok'], True, 'external timeout/RSS monitor healthy')
        audit.exact(caller['manifest_sha256'], manifest_sha, 'external caller manifest binding')
        audit.exact(caller['returncode'], 0, 'external caller exit status')
        audit.exact(caller['timed_out'], False, 'external caller no timeout')
        audit.exact(caller['rss_limit_exceeded'], False, 'external caller no RSS limit breach')
        audit.exact(caller['before_after_identity_pass'], True, 'external caller identity verdict')
        audit.exact(caller['limits'], {'seconds': 600, 'rss_bytes': 34359738368}, 'frozen external wall-clock/RSS budgets')
        require(type(caller['maxrss']) in (int, float) and math.isfinite(caller['maxrss']) and 0 < caller['maxrss'] <= 34359738368,
                'external caller recorded peak RSS within budget')
        require(type(caller['elapsed_seconds']) in (int, float) and math.isfinite(caller['elapsed_seconds'])
                and 0 <= caller['elapsed_seconds'] <= 600, 'external caller elapsed within 600 seconds')
        command = caller['command']
        require(type(command) is list and len(command) == 6, 'external caller exact argument shape')
        audit.exact(command[:3], [manifest['python'], manifest['runner'], '--manifest'], 'external caller frozen runtime and runner')
        audit.exact(command[4], '--output', 'external caller output option')
        audit.exact(Path(command[3]).resolve(), manifest_path.resolve(), 'external caller manifest argument')
        audit.exact(Path(command[5]).resolve(), result.resolve(), 'external caller result argument')
        require(datetime.fromisoformat(caller['started_utc']) <= datetime.fromisoformat(metadata['started_utc'])
                <= datetime.fromisoformat(metadata['completed_utc']) <= datetime.fromisoformat(caller['completed_utc']),
                'probe time inside caller interval')
        identities = verify_manifest(manifest, metadata, source_sha, audit)
        for path, expected in identities.items():
            require(Path(path).is_absolute() and Path(path).is_file(), 'frozen identity absolute regular file')
            value = sha(path)
            receipt['frozen_identity_before'][path] = value
            audit.exact(value, expected, 'current frozen source/input SHA/' + path)
        receipt['contract'] = manifest['contract']
        declared = metadata['output_sha256']
        call_files = [f'query_call_{i}.npz' for i in range(5)]
        expected_files = set(FILES + ['frozen_manifest.json', 'source_snapshot.py', 'checkpoint_load.txt',
                                     'extracted_ray_factory.py'] + call_files)
        audit.exact(set(declared), expected_files, 'complete production output manifest')
        cache = {name: (result / name).read_bytes() for name in declared}
        for name, data in cache.items():
            audit.exact(digest(data), declared[name], 'saved output byte identity/' + name)
        audit.exact(cache['frozen_manifest.json'], manifest_data, 'exact frozen manifest copy')
        source_path = str((ROOT / 'scripts/run_s14d_ray_only_probe.py').resolve())
        audit.exact(digest(cache['source_snapshot.py']), identities[source_path], 'frozen production source snapshot')
        receipt['result_hashes_before'] = dict(declared, **{'run_metadata.json': digest(metadata_data)})
        receipt['all_bytes_verified_before_npz_decode_utc'] = now()
        packages = {name: decode_npz(cache[name], name, audit) for name in FILES}
        sidecar_array_count = 0
        for call, filename in enumerate(call_files):
            expected = {name[len(f'call{call}_'):]: value for name, value in packages['query_outputs.npz'].items()
                        if name.startswith(f'call{call}_')}
            with np.load(io.BytesIO(cache[filename]), allow_pickle=False) as package:
                audit.exact(len(package.files), len(set(package.files)), filename + ': no duplicate members')
                audit.exact(set(package.files), set(expected), filename + ': complete per-call tensor set')
                for key in package.files:
                    audit.same_array(package[key], expected[key], filename + ': exact combined-file copy/' + key)
                    sidecar_array_count += 1
        numerical = verify_arrays(packages['probe_inputs.npz'], packages['query_outputs.npz'],
                                  packages['state_before.npz'], packages['state_after.npz'], audit)
        verify_metadata(metadata, manifest, packages['probe_inputs.npz'], packages['query_outputs.npz'],
                        packages['state_before.npz'], numerical, audit)
        receipt['numerical'] = numerical
        for path, expected in identities.items():
            value = sha(path)
            receipt['frozen_identity_after'][path] = value
            audit.exact(value, expected, 'frozen source/input unchanged after/' + path)
        receipt['result_hashes_after'] = {name: sha(result / name) for name in receipt['result_hashes_before']}
        audit.exact(receipt['result_hashes_after'], receipt['result_hashes_before'], 'all results unchanged after')
        audit.exact(sha(manifest_path), manifest_sha, 'manifest unchanged after')
        audit.exact(sha(caller_path), caller_sha, 'caller receipt unchanged after')
        audit.exact(sha(__file__), source_sha, 'independent source unchanged after')
        receipt.update(status='PASS', checked_npz_files=9, full_numerical_npz_files=4, per_call_identity_npz_files=5,
                       checked_npz_arrays=sum(len(package) for package in packages.values()) + sidecar_array_count,
                       rays_checked=4 * SIZE * SIZE, query_calls_checked=5,
                       scope='Interface/encoding/dummy/state consistency only; response diagnostics do not establish geometry accuracy or video quality')
    except BaseException as exc:
        receipt.update(status='FAIL', exception=repr(exc), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(completed_utc=now(), checks=audit.checks, check_count=len(audit.checks),
                       max_abs_difference=audit.max_abs_difference, source_sha256_after=sha(__file__))
        dump(output / 'verification.json', receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--result', required=True, type=Path)
    parser.add_argument('--caller', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    run(args.manifest.resolve(), args.result.resolve(), args.caller.resolve(), args.output.resolve())
