#!/usr/bin/env python3
"""S7: record fixed observation assignments, replay four maps, seal, then score."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback
import zipfile
from importlib.metadata import version
import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from s7_event_replay import observations, record_path, replay, arrays, decision_trace
from s6_memory_bridge import normalize_predictions, make_selector, memory_digest, crop_intrinsics
from rgbd_retrieval import select, initial_nms_threshold
from learned_pair_metrics import resize_crop
from evaluate_cut3r_pair import load_run
from run_s6_memory import project_depth
from rgbd_experiment import residual_stats
from tum_rgbd import read_trajectory


def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(p, value): Path(p).write_text(json.dumps(value, indent=2, allow_nan=False))


def run(output):
    if output.exists():
        raise ValueError('A fresh output directory is required')
    protocol = ROOT/'docs/S7_EVENT_REPLAY_PROTOCOL.md'
    freeze = read(ROOT/'docs/S7_PROTOCOL_FREEZE.json')
    if freeze['protocol_sha256'] != sha(protocol):
        raise ValueError('Protocol changed after freeze')
    for name, digest in freeze['execution_source_sha256'].items():
        if sha(ROOT/name) != digest:
            raise ValueError('Execution source changed after freeze: '+name)
    output.mkdir(parents=True)
    meta = dict(started_utc=utc(), status='running', phase='prediction_only',
                protocol_sha256=sha(protocol), freeze=freeze, cases=[],
                distinct_queries=12, primary_test_queries=8,
                environment=dict(python=sys.version, packages={n: version(n) for n in ('numpy','scipy','torch','Pillow')},
                                 torch_default_dtype=str(torch.get_default_dtype()),
                                 sorting='explicit torch.float32, torch.argsort with library-default stability'),
                measurement_policy='reuse S6 arrays after seal; exact comparison to independent S6 audit',
                evidence_level='post-S6 exploratory component mechanism; no new video generation')
    def checkpoint(): write(output/'run_metadata.json', meta)
    checkpoint()
    sources = [protocol, ROOT/'docs/S7_PROTOCOL_FREEZE.json'] + [ROOT/n for n in freeze['execution_source_sha256']]
    try:
        torch.set_num_threads(1)
        manifest_path = ROOT/'data/cut3r/S5_inputs.json'
        if sha(manifest_path) != '7ffa1467f5640bee2013a1ed1d30313be14da339ab28f7c364cfc2790f16f126':
            raise ValueError('Frozen input changed')
        manifest = read(manifest_path)
        sources.append(manifest_path)
        data = ROOT/'data/tum/rgbd_dataset_freiburg1_xyz'
        model_sources = {}
        for block in manifest['blocks']:
            b = block['block']
            run_path = ROOT/f'results/S6_cut3r_cpu/block{b}'
            model_meta, raw, _ = load_run(run_path, 'cpu',
                {'images': [{'sha256': f['rgb_sha256']} for f in block['frames']]}, views=24)
            if not model_meta.get('history_only_memory_ok') or not model_meta['query_state_write_audit']['ok']:
                raise ValueError('S6 history/query state contract is not met')
            model_sources[str(b)] = model_meta['predictions_sha256']
            depths, poses, norm = normalize_predictions(raw)
            rgbs = []
            for f in block['frames'][:20]:
                p = data/f['rgb']['path']
                if sha(p) != f['rgb_sha256']:
                    raise ValueError('RGB changed')
                crop, _ = resize_crop(Image.open(p).convert('RGB'), Image.Resampling.LANCZOS)
                rgbs.append(np.asarray(crop))
            confs = [raw[f'frame{i}_conf_self'][0] for i in range(20)]
            threshold = initial_nms_threshold(poses[:20])
            for stride in (8, 12):
                name = f'block{b}_stride{stride}'
                case_dir = output/name
                case_dir.mkdir()
                old = ROOT/'results/S6_memory_bridge'/name
                old_selection = read(old/'prediction_only_selection.json')
                frames, ids, filters = observations(depths[:20], confs, rgbs, poses[:20], stride)
                flat = [s for row in frames for s in row]
                np.savez_compressed(case_dir/'observations.npz', ids=ids,
                    points=np.array([s.position for s in flat]), normals=np.array([s.normal for s in flat]),
                    radii=np.array([s.radius for s in flat]), colors=np.array([s.color for s in flat]),
                    offsets=np.cumsum([0]+[len(f) for f in frames]))
                np.savez_compressed(case_dir/'predicted_poses.npz', poses=np.stack(poses))
                maps, info, checks = {}, {}, []
                for a, method in enumerate(('first_write', 'frame_mean')):
                    recorded, events = record_path(frames, method)
                    write(case_dir/f'A{a}_events.json', events)
                    write(case_dir/f'A{a}_recorded_build_trace.json', recorded.records)
                    logic = []
                    for row in recorded.records:
                        value = {k: v for k, v in row.items() if k != 'elapsed_seconds'}
                        value['position_threshold_normalized'] = value.pop('position_threshold_m')
                        value['radius_normalized_quantiles'] = value.pop('radius_m_quantiles')
                        logic.append(value)
                    expected_logic = [{k: v for k, v in row.items() if k != 'elapsed_seconds'}
                        for row in old_selection['maps'][method]['build_trace']]
                    if logic != expected_logic:
                        raise ValueError('Recorded logical build trace differs from S6')
                    checks.append(f'A{a}:S6_build_logic_without_timing')
                    for p, rule in enumerate(('first_write', 'frame_mean')):
                        label = f'A{a}P{p}'
                        memory = replay(frames, events, rule)
                        maps[label] = memory
                        values = arrays(memory)
                        np.savez_compressed(case_dir/f'{label}.npz', **values)
                        write(case_dir/f'{label}_sources.json', memory.mapping)
                        info[label] = dict(points=len(memory.surfels), digest=memory_digest(memory))
                        if a == p:
                            if memory_digest(memory) != memory_digest(recorded):
                                raise ValueError('Replay diagonal does not reproduce recorded path')
                            if memory_digest(memory) != old_selection['maps'][method]['digest']:
                                raise ValueError('Replay diagonal does not reproduce S6 digest')
                            with np.load(old/f'{method}.npz') as original:
                                for key, value in values.items():
                                    if not np.array_equal(value, original[key]):
                                        raise ValueError('S6 diagonal array mismatch '+key)
                                    checks.append(label+':S6_'+key)
                            old_sources = {int(k): v for k, v in read(old/f'{method}_provenance.json').items()}
                            if memory.mapping != old_sources:
                                raise ValueError('S6 diagonal source mapping mismatch')
                            checks.extend([label+':S6_sources', label+':recorded_digest', label+':S6_digest'])
                    first, mean = maps[f'A{a}P0'], maps[f'A{a}P1']
                    for key in ('normals', 'radii', 'colors', 'counts'):
                        if not np.array_equal(arrays(first)[key], arrays(mean)[key]):
                            raise ValueError('Fixed path changed '+key)
                    if first.mapping != mean.mapping:
                        raise ValueError('Fixed path changed sources')
                    checks.append(f'A{a}:nonposition_attributes_fixed')
                queries = []
                kernels = {k: make_selector(m, poses[:20], width=160, threshold=threshold) for k, m in maps.items()}
                for q in range(20, 24):
                    choices = {}
                    for label, kernel in kernels.items():
                        before = memory_digest(maps[label])
                        official = select(kernel, poses[q])
                        replayed = decision_trace(kernel, poses[q], official['candidate_counts'], nms=True)
                        if replayed['selected'] != official['selected']:
                            raise ValueError('Instrumented NMS differs from official selector')
                        if label in ('A0P0', 'A1P1'):
                            method = 'first_write' if label == 'A0P0' else 'frame_mean'
                            expected = old_selection['selected'][q-20]['retrieval']['160'][method]
                            for field in ('selected', 'candidate_counts', 'weights'):
                                if official[field] != expected[field]:
                                    raise ValueError('S6 diagonal selection trace differs: '+field)
                        controls = dict(official=replayed,
                            candidate_no_nms=decision_trace(kernel, poses[q], official['candidate_counts'], False),
                            all20_nms=decision_trace(kernel, poses[q], [[i, 1] for i in range(20)], True),
                            all20_no_nms=decision_trace(kernel, poses[q], [[i, 1] for i in range(20)], False))
                        np.savez_compressed(case_dir/f'query{q}_{label}_render.npz', **kernel.last_render)
                        choices[label] = dict(readouts=controls, official_trace=official)
                        if before != memory_digest(maps[label]):
                            raise ValueError('Readout mutated memory')
                    for control in ('all20_nms', 'all20_no_nms'):
                        if len({tuple(c['readouts'][control]['selected']) for c in choices.values()}) != 1:
                            raise ValueError('Map-independent control depends on map')
                    queries.append(dict(frame=q, maps=choices))
                case = dict(block=b, split=block['split'], stride=stride, width=160,
                    prediction_normalization=norm, maps=info, filters=filters,
                    diagonal_checks=checks, queries=queries,
                    s6_prediction_selection_sha256=sha(old/'prediction_only_selection.json'))
                write(case_dir/'prediction_only_selection.json', case)
                sealed = {str(f.relative_to(case_dir)): sha(f) for f in sorted(case_dir.iterdir()) if f.is_file()}
                meta['cases'].append(dict(directory=name, block=b, stride=stride, sealed_files=sealed))
                checkpoint()
                print(json.dumps(dict(case=name, phase='prediction_sealed', utc=utc())), flush=True)
        meta['model_prediction_sha256'] = model_sources
        meta['selections_sealed_utc'] = utc()
        meta['phase'] = 'measurement_scoring'
        checkpoint()
        # First access to measured arrays, metric scale and GT is after this seal.
        for name, digest in freeze['measurement_file_sha256'].items():
            if sha(ROOT/name) != digest:
                raise ValueError('Frozen measurement source changed: '+name)
        old_meta = read(ROOT/'results/S6_memory_bridge/run_metadata.json')
        audit = read(ROOT/'results/S6_independent_audit/verification.json')
        if old_meta['status'] != 'completed' or audit['status'] != 'passed':
            raise ValueError('S6 score source is not independently verified')
        trajectory_path = data/'groundtruth.txt'
        if sha(trajectory_path) != old_meta['source_sha256'][str(trajectory_path.relative_to(ROOT))]:
            raise ValueError('GT changed since S6')
        trajectory = read_trajectory(trajectory_path)
        measurement_hashes, results = {}, []
        for entry in meta['cases']:
            case_dir = output/entry['directory']
            for name, digest in entry['sealed_files'].items():
                if sha(case_dir/name) != digest:
                    raise ValueError('Sealed prediction changed')
            case = read(case_dir/'prediction_only_selection.json')
            b = entry['block']
            frames = manifest['blocks'][b]['frames']
            gt = [trajectory.interpolate(f['rgb']['timestamp'], max_gap_seconds=.1).c2w for f in frames]
            scale = old_meta['normalizations'][str(b)]['scoring_only_metric_scale']
            metric_maps = {}
            for label in case['maps']:
                with np.load(case_dir/f'{label}.npz') as z:
                    metric_maps[label] = (z['points']*scale) @ gt[0][:3, :3].T + gt[0][:3, 3]
            for query in case['queries']:
                q = query['frame']
                original = ROOT/'results/S6_memory_bridge'/entry['directory']/f'query{q}_scoring.npz'
                independent = ROOT/'results/S6_independent_audit'/f"block{b}_stride{entry['stride']}_query{q}.npz"
                for f in (original, independent): measurement_hashes[str(f.relative_to(ROOT))] = sha(f)
                with np.load(original) as z, np.load(independent) as v:
                    for key in ('target', 'valid', 'support', 'common'):
                        if not np.array_equal(z[key], v[key], equal_nan=True):
                            raise ValueError('S6 independent measurements differ')
                    target, valid, support = z['target'], z['valid'], z['support']
                    projected = {k: project_depth(p, gt[q], crop_intrinsics()) for k, p in metric_maps.items()}
                    for label, method in (('A0P0', 'first_write'), ('A1P1', 'frame_mean')):
                        if not np.array_equal(projected[label], z[method], equal_nan=True):
                            raise ValueError('Diagonal geometry does not reproduce S6')
                    diagonal_common = valid & np.isfinite(projected['A0P0']) & np.isfinite(projected['A1P1'])
                    if not np.array_equal(diagonal_common, z['common']):
                        raise ValueError('Diagonal common mask changed')
                common = valid & np.logical_and.reduce([np.isfinite(z) for z in projected.values()])
                scores, geometry = {}, {}
                for label, choice in query['maps'].items():
                    scores[label] = {name: dict(selected=value['selected'],
                        support=float(support[value['selected']].any(axis=0)[valid].mean()))
                        for name, value in choice['readouts'].items()}
                    own = valid & np.isfinite(projected[label])
                    geometry[label] = dict(common_four=residual_stats(projected[label], target, common),
                        own=residual_stats(projected[label], target, own),
                        coverage=float(own.sum()/valid.sum()))
                np.savez_compressed(case_dir/f'query{q}_scoring.npz', target=target, valid=valid,
                    support=support, common_four=common, common_diagonal=diagonal_common, **projected)
                results.append(dict(block=b, split=case['split'], stride=case['stride'], frame=q,
                    valid_pixels=int(valid.sum()), common_four_pixels=int(common.sum()),
                    all20_support=float(support.any(axis=0)[valid].mean()), readouts=scores, geometry=geometry))
        write(output/'records.json', results)
        meta['measurement_source_sha256'] = measurement_hashes
        meta['source_sha256'] = {str(p.relative_to(ROOT)): sha(p) for p in sources}
        with zipfile.ZipFile(output/'experiment_source.zip', 'w', zipfile.ZIP_DEFLATED) as z:
            for p in sources: z.write(p, str(p.relative_to(ROOT)))
        meta['query_conditions'] = len(results)
        meta['readout_conditions'] = sum(len(r['readouts'])*4 for r in results)
        if len(results) != 24 or meta['readout_conditions'] != 384:
            raise ValueError('Incomplete S7 condition count')
        meta['status'] = 'completed'
        meta['phase'] = 'complete'
    except Exception:
        meta['status'] = 'failed'
        meta['traceback'] = traceback.format_exc()
        raise
    finally:
        meta['completed_utc'] = utc()
        checkpoint()
    print(json.dumps(dict(status=meta['status'], completed_utc=meta['completed_utc'])), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT/'results/S7_event_replay')
    args = p.parse_args()
    run(args.output.resolve())
