#!/usr/bin/env python3
"""S8 external-scene event replay: seal every prediction-only choice, then score.

No old scene maps, measurements, input lists, or predictions are loaded. The
unchanged S6 construction/scoring and S7 event/readout functions are reused.
Depth bytes may be hashed before sealing; depth decoding, GT pose interpolation
and metric scale fitting occur only after all six cases have been sealed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import sys
import traceback
import zipfile

import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from s7_event_replay import observations, record_path, replay, arrays, decision_trace
from s6_memory_bridge import normalize_predictions, make_selector, memory_digest, crop_intrinsics
from rgbd_retrieval import select, initial_nms_threshold
from learned_pair_metrics import resize_crop, measured_target, first_frame_scale
from run_s6_memory import measured_support, project_depth
from rgbd_experiment import residual_stats
from tum_rgbd import read_trajectory
from run_s8_sequence import (read_json, parse_protocol, validate_manifest, safe_data_path,
    verify_query_policy, verify_output_arrays, RUNNER_SHA, BASE_RUNNER_SHA, CHECKPOINT_SHA,
    CHECKPOINT_BYTES, COMMIT, ADAPTER_SHA, MAX_RSS_BYTES, PRECISION)

MAPS = ('A0P0', 'A0P1', 'A1P0', 'A1P1')
READOUTS = ('official', 'candidate_no_nms', 'all20_nms', 'all20_no_nms')
REPLAY_CONTRACT = dict(schema='s8-replay-v1', strides=[8, 12], width=160,
    maps=list(MAPS), readouts=list(READOUTS), block_count=3, frames_per_block=24,
    history_count=20, query_count=4, splits=['test']*3, native_size=[640, 480],
    native_intrinsics=[525.0, 525.0, 319.5, 239.5], depth_divisor=5000.0,
    extra_depth_scale=1.0, gt_pose_timestamp='rgb', max_gt_gap_seconds=0.1,
    measurement_after_all_selections_sealed=True)
REQUIRED_SOURCES = (
    'scripts/run_s8_replay.py', 'scripts/run_s8_sequence.py', 'scripts/run_s6_cut3r.py',
    'scripts/run_cut3r_local.py', 'scripts/cut3r_rope_compat.py',
    'scripts/run_s6_memory.py', 'scripts/evaluate_cut3r_pair.py',
    'src/s7_event_replay.py', 'src/s6_memory_bridge.py', 'src/rgbd_memory.py',
    'src/rgbd_metrics.py', 'src/rgbd_retrieval.py', 'src/rgbd_experiment.py',
    'src/rgbd_dataset.py', 'src/experiment_io.py', 'src/learned_pair_metrics.py', 'src/tum_rgbd.py',
    'src/retrieval_diagnostic.py', 'src/vmem_memory_kernel.py', 'src/vmem_retrieval_kernel.py')


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return read_json(Path(path).read_text())


def write(path, value):
    path = Path(path)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    temp.replace(path)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_path(name):
    p = Path(name)
    return (p if p.is_absolute() else ROOT / p).resolve(strict=True)


def archive_name(path):
    """Stable safe names for project files and arbitrary external source roots."""
    path = Path(path).resolve(strict=True)
    if path.is_relative_to(ROOT):
        return str(path.relative_to(ROOT))
    parent_id = hashlib.sha256(str(path.parent).encode()).hexdigest()[:16]
    return 'external/' + parent_id + '/' + path.name


def parse_replay_contract(text):
    blocks = re.findall(r'^```s8-replay-json\s*\n(.*?)^```\s*$', text,
                        flags=re.MULTILINE | re.DOTALL)
    require(len(blocks) == 1, 'Protocol needs exactly one s8-replay-json fence')
    value = read_json(blocks[0])
    require(isinstance(value, dict), 'Replay contract must be an object')
    for key, expected in REPLAY_CONTRACT.items():
        actual = value.get(key)
        require(type(actual) is type(expected) and actual == expected,
                'Replay protocol declaration differs: ' + key)
    return value


def validate_freeze(args):
    freeze = read(args.freeze)
    require(freeze.get('protocol_sha256') == sha(args.protocol), 'Protocol changed after freeze')
    require(freeze.get('manifest_sha256') == sha(args.manifest), 'Manifest changed after freeze')
    execution = freeze.get('execution_source_sha256', {})
    require(isinstance(execution, dict), 'Missing execution source freeze')
    identities = {source_path(name): digest for name, digest in execution.items()}
    require(len(identities) == len(execution), 'Duplicate execution source path aliases')
    require(all((ROOT / name).resolve() in identities for name in REQUIRED_SOURCES),
            'Freeze omits a required executed/imported source')
    for path, digest in identities.items():
        require(sha(path) == digest, 'Execution source changed after freeze: ' + str(path))
    measured = freeze.get('measurement_file_sha256', {})
    require(isinstance(measured, dict), 'Missing measurement source freeze')
    measurement = {source_path(name): digest for name, digest in measured.items()}
    require(len(measurement) == len(measured), 'Duplicate measurement source path aliases')
    trajectory_path = safe_data_path(args.data, 'groundtruth.txt')
    require(trajectory_path in measurement, 'Freeze must bind the new groundtruth.txt bytes')
    for path, digest in measurement.items():
        require(sha(path) == digest, 'Measurement bytes changed after freeze: ' + str(path))
    # These are integrity hashes, not decoded depth or trajectory pose access.
    return freeze, identities, measurement


def verify_sequence(args, manifest_sha, protocol_sha):
    sequence = read(args.runs / 'sequence_metadata.json')
    require(sequence.get('schema') == 's8-sequence-metadata-v1' and
            sequence.get('ok') is True and sequence.get('phase') == 'complete',
            'S8 model controller has not completed successfully')
    require(sequence.get('arrays_verified') == 504 and
            sequence.get('runner_sha256') == RUNNER_SHA, 'Unexpected model array count or runner')
    require(sequence.get('manifest_sha256') == manifest_sha and
            sequence.get('protocol_sha256') == protocol_sha, 'Controller inputs/protocol differ')
    require(sha(args.runs / 'frozen_inputs.json') == manifest_sha and
            sha(args.runs / 'frozen_protocol.md') == protocol_sha, 'Controller frozen copies differ')
    require(sha(args.runs / 'sequence_runner_snapshot.py') == sequence['sequence_runner_sha256'] ==
            sha(ROOT / 'scripts/run_s8_sequence.py'), 'Controller snapshot/source differs')
    download = read(args.runs / 'checkpoint_download_manifest.json')
    require(download.get('status') == 'verified_download' and download.get('sha256') == CHECKPOINT_SHA and
            download.get('actual_size') == CHECKPOINT_BYTES, 'Controller checkpoint download evidence differs')
    rope = read(args.runs / 'signed_rope_check.json')
    require(rope.get('ok') is True and rope.get('commit') == COMMIT and
            rope.get('adapter_sha256') == ADAPTER_SHA, 'Signed RoPE evidence did not pass')
    require(sequence.get('depth_files_decoded_by_controller') is False and
            sequence.get('s5_history_comparison_performed') is False,
            'Controller scope differs from independent-scene policy')
    blocks = sequence.get('blocks', [])
    require([b.get('block') for b in blocks] == [0, 1, 2], 'Missing or duplicate model block')
    for entry in blocks:
        require(entry.get('ok') is True and entry.get('split') == 'test' and
                entry.get('arrays_verified') == 168 and entry.get('history_only_memory_ok') is True,
                'Incomplete controller block checks')
        peak = entry.get('process_peak_rss_bytes')
        require(type(peak) is int and 0 < peak <= MAX_RSS_BYTES,
                'Model process peak lacks a valid within-budget measurement')
        require(entry.get('returncode') == 0 and entry.get('monitored_seconds', float('inf')) <= 900,
                'Model process failed or exceeded the fixed time budget')
    return sequence


def load_model(directory, block, sequence):
    """Read actual new outputs and local snapshots, without old scene paths."""
    entry = next(x for x in sequence['blocks'] if x['block'] == block['block'])
    metadata = read(directory / 'run_metadata.json')
    require(sha(directory / 'run_metadata.json') == entry['metadata_sha256'], 'Model metadata changed')
    required = dict(ok=True, phase='complete', inference_ok=True, device='cpu', dtype='float32',
        cpu_threads=8, seed=0, views=24, runner_sha256=RUNNER_SHA, base_runner_sha256=BASE_RUNNER_SHA,
        commit=COMMIT, tracked_changes='', actual_head_type='linear', actual_patch_image_size=[224, 224],
        parameters=748443655, checkpoint_all_keys_matched=True,
        upstream_source_files_unmodified=True, upstream_execution_unmodified=False,
        precision_semantics=PRECISION, input_tensor_shapes=[[1, 3, 224, 224]]*24,
        all_outputs_finite=True, required_outputs_present=True)
    for key, value in required.items():
        require(metadata.get(key) == value, 'Model metadata differs: ' + key)
    require(metadata.get('checkpoint', {}).get('sha256') == CHECKPOINT_SHA and
            metadata['checkpoint'].get('bytes') == CHECKPOINT_BYTES and
            metadata['checkpoint'] == sequence.get('checkpoint'), 'Model checkpoint differs')
    require(metadata.get('peak_process_rss_bytes') == entry['process_peak_rss_bytes'],
            'Model/controller peak memory measurements differ')
    require(metadata.get('checkpoint_serialization', {}).get('weights_only') is True and
            metadata.get('model_config', {}).get('downstream_head_class') ==
            'dust3r.heads.linear_head.LinearPts3dPose', 'Checkpoint loading or concrete head differs')
    require(sha(directory / 'runner_snapshot.py') == RUNNER_SHA, 'Model runner snapshot changed')
    require([x['sha256'] for x in metadata['images']] == [x['rgb_sha256'] for x in block['frames']],
            'Model RGB order differs from manifest')
    compat = metadata.get('runtime_compatibility', {})
    require(compat.get('signed_rope_adapter') is True and compat.get('blocking_input_staging') is True and
            compat.get('adapter_sha256') == ADAPTER_SHA and
            compat.get('validation_sha256') == sequence['signed_rope_check_sha256'] ==
            sha(directory.parent / 'signed_rope_check.json'), 'Compatibility evidence differs')
    staging = metadata.get('input_device_staging', {})
    fields = ('img', 'ray_map', 'camera_pose', 'img_mask', 'ray_mask', 'update', 'reset')
    checks = staging.get('checks', [])
    require(staging.get('all_values_preserved') is True and len(checks) == 168 and
            {(c['view'], c['field']) for c in checks} == {(i, f) for i in range(24) for f in fields} and
            all(c.get('values_preserved') is True for c in checks), 'Input staging audit is incomplete')
    verify_query_policy(metadata)
    require(sha(directory / 's8_output_verification.json') == entry['verification_sha256'],
            'Model output verification changed')
    verification = read(directory / 's8_output_verification.json')
    require(verification.get('ok') is True and verification.get('arrays_verified') == 168 and
            verification.get('metadata_sha256') == entry['metadata_sha256'], 'Model output audit failed')
    require(sha(directory / 'predictions.npz') == metadata['predictions_sha256'] ==
            entry['predictions_sha256'] == verification['predictions_sha256'], 'Prediction bytes changed')
    actual = verify_output_arrays(directory / 'predictions.npz', metadata['outputs'])
    require(actual == verification['arrays'], 'Actual output arrays differ from controller audit')
    with np.load(directory / 'predictions.npz', allow_pickle=False) as values:
        raw = {key: values[key] for key in values.files}
    return metadata, raw


def assert_sealed(output, metadata):
    for name, digest in metadata['sealed_root_files'].items():
        require(sha(output / name) == digest, 'Sealed normalized input changed: ' + name)
    for entry in metadata['cases']:
        for name, digest in entry['sealed_files'].items():
            require(sha(output / entry['directory'] / name) == digest, 'Sealed prediction changed: ' + name)


def run(args):
    output = args.output
    require(not output.exists() and not output.is_symlink(), 'Use a fresh output directory; old attempts remain')
    output.mkdir(parents=True, exist_ok=False)
    meta = dict(schema='s8-replay-metadata-v1', started_utc=utc(), status='running', phase='preflight',
        distinct_queries=12, primary_test_queries=12, cases=[], sealed_root_files={}, normalizations={},
        environment=dict(python=sys.version, packages={n: version(n) for n in ('numpy', 'scipy', 'torch', 'Pillow')},
            torch_default_dtype=str(torch.get_default_dtype()),
            sorting='explicit torch.float32; library-default torch.argsort stability'),
        measurement_policy='new PNG depth and trajectory poses only after all selection files sealed; '
            'timestamp-only GT availability may be used earlier for sampling; integrity hashes do not decode depth',
        evidence_level='external-scene validation of frozen component mechanisms; no video generation')
    def checkpoint():
        write(output / 'run_metadata.json', meta)
    checkpoint()
    sources = {}
    def add_source(path, expected=None):
        path = Path(path).resolve(strict=True)
        digest = sha(path)
        require(expected is None or digest == expected, 'Source changed: ' + str(path))
        require(path not in sources or sources[path] == digest, 'Source changed during execution: ' + str(path))
        sources[path] = digest
    try:
        torch.set_num_threads(1)
        freeze, execution, measurements = validate_freeze(args)
        for path in (args.manifest, args.protocol, args.freeze):
            add_source(path)
        for path, digest in execution.items():
            add_source(path, digest)
        for name in ('vendor/provenance.json', 'vendor/VMEM_LICENSE'):
            add_source(ROOT / name)
        protocol_text = args.protocol.read_text()
        controller_contract = parse_protocol(protocol_text)
        meta['replay_contract'] = parse_replay_contract(protocol_text)
        require(controller_contract['splits'] == ['test']*3, 'All S8 blocks must be external test')
        manifest = read(args.manifest)
        _, input_identities = validate_manifest(manifest, args.data, sha(args.protocol), controller_contract)
        meta.update(manifest_sha256=sha(args.manifest), protocol_sha256=sha(args.protocol),
            freeze_sha256=sha(args.freeze), freeze=freeze, dataset=manifest.get('dataset'),
            input_identities=input_identities, crop_intrinsics=list(crop_intrinsics()))
        sequence = verify_sequence(args, meta['manifest_sha256'], meta['protocol_sha256'])
        for name in ('sequence_metadata.json', 'sequence_runner_snapshot.py', 'frozen_inputs.json',
                     'frozen_protocol.md', 'signed_rope_check.json', 'checkpoint_download_manifest.json'):
            add_source(args.runs / name)
        meta['phase'] = 'prediction_only'
        checkpoint()
        reference_identity, model_sources = None, {}
        for block in manifest['blocks']:
            b = block['block']
            run_path = args.runs / f'block{b}'
            model, raw = load_model(run_path, block, sequence)
            identity = {k: model[k] for k in ('commit', 'model_config', 'versions', 'runner_sha256',
                'runtime_compatibility', 'dtype', 'seed', 'cpu_threads', 'checkpoint', 'precision_semantics')}
            require(reference_identity is None or identity == reference_identity, 'Model identity differs between blocks')
            reference_identity = identity
            model_sources[str(b)] = model['predictions_sha256']
            for name in ('run_metadata.json', 'runner_snapshot.py', 's8_output_verification.json'):
                add_source(run_path / name)
            depths, poses, norm = normalize_predictions(raw)
            require(len(depths) == 24 and len(poses) == 24, 'Expected 24 normalized frames')
            meta['normalizations'][str(b)] = dict(first_prediction_inverse_median=norm)
            normalized_path = output / f'block{b}_normalized_input.npz'
            np.savez_compressed(normalized_path, first_depth=depths[0], poses=np.stack(poses))
            meta['sealed_root_files'][normalized_path.name] = sha(normalized_path)
            rgbs = []
            for f in block['frames'][:20]:
                path = safe_data_path(args.data, f['rgb']['path'])
                require(sha(path) == f['rgb_sha256'], 'RGB changed')
                with Image.open(path) as image:
                    require(image.size == (640, 480), 'Unexpected native RGB resolution')
                    crop, _ = resize_crop(image.convert('RGB'), Image.Resampling.LANCZOS)
                    rgbs.append(np.asarray(crop))
            confs = [raw[f'frame{i}_conf_self'][0] for i in range(20)]
            threshold = initial_nms_threshold(poses[:20])
            for stride in (8, 12):
                name = f'block{b}_stride{stride}'
                case_dir = output / name
                case_dir.mkdir()
                frames, ids, filters = observations(depths[:20], confs, rgbs, poses[:20], stride)
                flat = [s for row in frames for s in row]
                require(flat, 'No accepted history observations; retain this failed case')
                np.savez_compressed(case_dir / 'observations.npz', ids=ids,
                    points=np.array([s.position for s in flat]), normals=np.array([s.normal for s in flat]),
                    radii=np.array([s.radius for s in flat]), colors=np.array([s.color for s in flat]),
                    offsets=np.cumsum([0] + [len(f) for f in frames]))
                np.savez_compressed(case_dir / 'predicted_poses.npz', poses=np.stack(poses))
                maps, info, checks = {}, {}, []
                for a, method in enumerate(('first_write', 'frame_mean')):
                    recorded, events = record_path(frames, method)
                    write(case_dir / f'A{a}_events.json', events)
                    write(case_dir / f'A{a}_recorded_build_trace.json', recorded.records)
                    np.savez_compressed(case_dir / f'A{a}_recorded_map.npz', **arrays(recorded))
                    write(case_dir / f'A{a}_recorded_sources.json', recorded.mapping)
                    for p, rule in enumerate(('first_write', 'frame_mean')):
                        label = f'A{a}P{p}'
                        memory = replay(frames, events, rule)
                        maps[label] = memory
                        values = arrays(memory)
                        np.savez_compressed(case_dir / f'{label}.npz', **values)
                        write(case_dir / f'{label}_sources.json', memory.mapping)
                        info[label] = dict(points=len(memory.surfels), digest=memory_digest(memory))
                        if a == p:
                            require(memory_digest(memory) == memory_digest(recorded), 'Replay diagonal digest differs')
                            for key, value in values.items():
                                require(np.array_equal(value, arrays(recorded)[key]), 'Replay diagonal array differs: ' + key)
                                checks.append(label + ':recorded_' + key)
                            require(memory.mapping == recorded.mapping, 'Replay diagonal source mapping differs')
                            checks.extend([label + ':recorded_sources', label + ':recorded_digest'])
                    first, mean = maps[f'A{a}P0'], maps[f'A{a}P1']
                    for key in ('normals', 'radii', 'colors', 'counts'):
                        require(np.array_equal(arrays(first)[key], arrays(mean)[key]), 'Fixed path changed ' + key)
                    require(first.mapping == mean.mapping, 'Fixed path changed source sets')
                    checks.append(f'A{a}:nonposition_attributes_and_sources_fixed')
                queries = []
                kernels = {k: make_selector(m, poses[:20], width=160, threshold=threshold) for k, m in maps.items()}
                for q in range(20, 24):
                    choices = {}
                    for label, kernel in kernels.items():
                        before = memory_digest(maps[label])
                        official = select(kernel, poses[q])
                        traced = decision_trace(kernel, poses[q], official['candidate_counts'], nms=True)
                        require(traced['selected'] == official['selected'], 'Decision trace differs from official ordered selection')
                        controls = dict(official=traced,
                            candidate_no_nms=decision_trace(kernel, poses[q], official['candidate_counts'], False),
                            all20_nms=decision_trace(kernel, poses[q], [[i, 1] for i in range(20)], True),
                            all20_no_nms=decision_trace(kernel, poses[q], [[i, 1] for i in range(20)], False))
                        np.savez_compressed(case_dir / f'query{q}_{label}_render.npz', **kernel.last_render)
                        choices[label] = dict(readouts=controls, official_trace=official)
                        require(before == memory_digest(maps[label]), 'Readout mutated explicit memory')
                    for control in ('all20_nms', 'all20_no_nms'):
                        require(len({tuple(c['readouts'][control]['selected']) for c in choices.values()}) == 1,
                                'Map-independent control depends on map')
                    queries.append(dict(frame=q, maps=choices))
                case = dict(block=b, split='test', stride=stride, width=160, prediction_normalization=norm,
                    maps=info, filters=filters, diagonal_checks=checks, queries=queries)
                write(case_dir / 'prediction_only_selection.json', case)
                sealed = {str(f.relative_to(case_dir)): sha(f) for f in sorted(case_dir.iterdir()) if f.is_file()}
                meta['cases'].append(dict(directory=name, block=b, stride=stride, sealed_files=sealed))
                checkpoint()
                print(json.dumps(dict(case=name, phase='prediction_sealed', utc=utc())), flush=True)
        require(len(meta['cases']) == 6, 'Missing prediction-only cases')
        assert_sealed(output, meta)
        meta['model_prediction_sha256'] = model_sources
        meta['model_identity'] = reference_identity
        meta['official_ordered_selection_checks'] = 96
        meta['selections_sealed_utc'] = utc()
        meta['phase'] = 'measurement_scoring'
        checkpoint()
        # First pose decoding and depth decoding in this runner are below the seal.
        for path, digest in measurements.items():
            add_source(path, digest)
        trajectory_path = safe_data_path(args.data, 'groundtruth.txt')
        meta['first_gt_pose_decode_utc'] = utc()
        checkpoint()
        trajectory = read_trajectory(trajectory_path)
        for name in ('rgb.txt', 'depth.txt'):
            add_source(safe_data_path(args.data, name))
        results, measurement_hashes = [], {archive_name(p): d for p, d in measurements.items()}
        for block in manifest['blocks']:
            b = block['block']
            targets, masks, gt, brackets, geometries = [], [], [], [], []
            for f in block['frames']:
                path = safe_data_path(args.data, f['depth']['path'])
                require(sha(path) == f['depth_sha256'], 'Measured depth changed')
                measurement_hashes[archive_name(path)] = f['depth_sha256']
                if 'first_depth_decode_utc' not in meta:
                    meta['first_depth_decode_utc'] = utc()
                    checkpoint()
                with Image.open(path) as image:
                    require(image.size == (640, 480), 'Unexpected native measured depth resolution')
                    native = np.asarray(image, dtype=np.float64) / 5000.0
                target, mask, geometry = measured_target(native)
                pose = trajectory.interpolate(f['rgb']['timestamp'], max_gap_seconds=.1)
                # Timestamp availability, also checked on depth time, cannot bridge a GT gap.
                trajectory.interpolate(f['depth']['timestamp'], max_gap_seconds=.1)
                targets.append(target); masks.append(mask); gt.append(pose.c2w)
                brackets.append(pose.gap_seconds); geometries.append(geometry)
            with np.load(output / f'block{b}_normalized_input.npz', allow_pickle=False) as normalized:
                scale, count = first_frame_scale(normalized['first_depth'], targets[0], masks[0])
            meta['normalizations'][str(b)].update(scoring_only_metric_scale=scale,
                scoring_only_calibration_pixels=count, scale_fitted_utc=utc())
            np.savez_compressed(output / f'block{b}_measurements.npz', targets=np.stack(targets),
                masks=np.stack(masks), gt_poses=np.stack(gt), rgb_pose_bracket_gap_seconds=np.array(brackets),
                rgb_timestamps=np.array([f['rgb']['timestamp'] for f in block['frames']]),
                depth_timestamps=np.array([f['depth']['timestamp'] for f in block['frames']]))
            write(output / f'block{b}_measurement_geometry.json', geometries)
            for entry in [c for c in meta['cases'] if c['block'] == b]:
                assert_sealed(output, meta)
                case_dir = output / entry['directory']
                case = read(case_dir / 'prediction_only_selection.json')
                metric_maps = {}
                for label in MAPS:
                    with np.load(case_dir / f'{label}.npz', allow_pickle=False) as values:
                        metric_maps[label] = (values['points'] * scale) @ gt[0][:3, :3].T + gt[0][:3, 3]
                for query in case['queries']:
                    q = query['frame']
                    support, valid, target = measured_support(targets, masks, gt, q, crop_intrinsics())
                    require(int(valid.sum()) > 0, 'No valid scoring target; retain failed case')
                    projected = {k: project_depth(points, gt[q], crop_intrinsics()) for k, points in metric_maps.items()}
                    diagonal = valid & np.isfinite(projected['A0P0']) & np.isfinite(projected['A1P1'])
                    common = valid & np.logical_and.reduce([np.isfinite(z) for z in projected.values()])
                    scores, geometry = {}, {}
                    for label, choice in query['maps'].items():
                        scores[label] = {}
                        for name, value in choice['readouts'].items():
                            supported = int((support[value['selected']].any(axis=0) & valid).sum())
                            scores[label][name] = dict(selected=value['selected'], supported_pixels=supported,
                                support=supported / int(valid.sum()))
                        own = valid & np.isfinite(projected[label])
                        geometry[label] = dict(common_four=residual_stats(projected[label], target, common),
                            own=residual_stats(projected[label], target, own), coverage=float(own.sum()/valid.sum()))
                        if label in ('A0P0', 'A1P1'):
                            geometry[label]['common_diagonal'] = residual_stats(projected[label], target, diagonal)
                    np.savez_compressed(case_dir / f'query{q}_scoring.npz', target=target, valid=valid,
                        support=support, common_four=common, common_diagonal=diagonal, **projected)
                    results.append(dict(block=b, split='test', stride=case['stride'], frame=q,
                        valid_pixels=int(valid.sum()), common_four_pixels=int(common.sum()),
                        common_diagonal_pixels=int(diagonal.sum()),
                        all20_supported_pixels=int((support.any(axis=0) & valid).sum()),
                        all20_support=int((support.any(axis=0) & valid).sum()) / int(valid.sum()),
                        readouts=scores, geometry=geometry))
        write(output / 'records.json', results)
        meta['measurement_source_sha256'] = measurement_hashes
        assert_sealed(output, meta)
        # Validate originals at completion, then archive the exact sources used.
        validate_freeze(args)
        for path, digest in sources.items():
            require(sha(path) == digest, 'Source changed during execution: ' + str(path))
        names = [archive_name(p) for p in sources]
        require(len(names) == len(set(names)), 'Source archive name collision')
        meta['source_sha256'] = {archive_name(p): digest for p, digest in sources.items()}
        meta['source_original_paths'] = {archive_name(p): str(p) for p in sources}
        # Bind every archived byte string to the digest already checked above.
        source_payloads = {p: p.read_bytes() for p in sources}
        for path, payload in source_payloads.items():
            require(hashlib.sha256(payload).hexdigest() == sources[path],
                    'Source changed during archive capture: ' + str(path))
        with zipfile.ZipFile(output / 'experiment_source.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
            for path, payload in source_payloads.items():
                archive.writestr(archive_name(path), payload)
        meta['experiment_source_sha256'] = sha(output / 'experiment_source.zip')
        meta['query_conditions'] = len(results)
        meta['readout_conditions'] = sum(sum(len(v) for v in r['readouts'].values()) for r in results)
        require(len(results) == 24 and meta['readout_conditions'] == 384, 'Incomplete fixed S8 conditions')
        require(len({(r['block'], r['frame']) for r in results}) == 12, 'Wrong unique external query count')
        meta['status'] = 'completed'
        meta['phase'] = 'complete'
    except BaseException:
        meta['status'] = 'failed'
        meta['phase_failed'] = meta['phase']
        meta['traceback'] = traceback.format_exc()
        raise
    finally:
        meta['completed_utc'] = utc()
        checkpoint()
    print(json.dumps(dict(status=meta['status'], completed_utc=meta['completed_utc'])), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'protocol', 'freeze', 'runs', 'data', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    for name in ('manifest', 'protocol', 'freeze', 'runs', 'data'):
        setattr(args, name, getattr(args, name).resolve())
    # Preserve a broken output symlink for the fresh-directory refusal in run().
    args.output = args.output.absolute()
    run(args)


if __name__ == '__main__':
    main()
