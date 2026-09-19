#!/usr/bin/env python3
"""Read metadata and NPY headers only; no arrays, GT labels, or new selections."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import itertools
import json
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name('inventory.json')
JSON_INPUTS = []


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    name = str(path.relative_to(ROOT))
    assert 'scoring' not in name and path.name not in ('records.json', 'summary.json')
    JSON_INPUTS.append({'path': name, 'sha256': sha(path)})
    return json.loads(path.read_text())


def header_inventory(path):
    assert 'scoring' not in str(path) and 'measurement' not in str(path)
    members = {}
    with zipfile.ZipFile(path) as package:
        for item in package.infolist():
            assert item.filename.endswith('.npy')
            with package.open(item) as stream:
                assert stream.read(6) == b'\x93NUMPY'
                version = tuple(stream.read(2))
                assert version in ((1, 0), (2, 0), (3, 0))
                n = 2 if version == (1, 0) else 4
                length = struct.unpack('<H' if n == 2 else '<I', stream.read(n))[0]
                assert 0 < length <= 1024 * 1024
                raw = stream.read(length)
                assert len(raw) == length
                header = ast.literal_eval(raw.decode('utf-8' if version == (3, 0) else 'latin1'))
                assert isinstance(header, dict) and set(header) == {'descr', 'fortran_order', 'shape'}
                assert isinstance(header['descr'], str) and 'O' not in header['descr']
                assert stream.tell() == 8 + n + length
            members[item.filename[:-4]] = {
                'shape': list(header['shape']), 'dtype': header['descr'],
                'fortran_order': header['fortran_order'],
                'npy_header_bytes_requested': 8 + n + length,
                'npy_total_bytes': item.file_size, 'compressed_bytes': item.compress_size,
                'zip_crc32': item.CRC,
            }
    return {'path': str(path.relative_to(ROOT)), 'sha256_compressed_file': sha(path),
            'bytes': path.stat().st_size, 'members': members,
            'numerical_array_payload_decoded': False}


def shape(value):
    return {'type': type(value).__name__, 'length': len(value) if isinstance(value, (list, dict)) else None}


def selected_pair_availability(trace):
    needed = {tuple(sorted(pair)) for pair in itertools.combinations(trace['selected'], 2)}
    present = {tuple(sorted((step['frame'], pair[0])))
               for step in trace['steps'] if 'frame' in step for pair in step['comparisons']}
    return {'selected_pair_count': len(needed), 'all_selected_pairs_saved': needed <= present,
            'saved_unique_pairs_anywhere': len(present),
            'fallback_present': any('fallback_added' in step for step in trace['steps'])}


def main():
    assert not OUT.exists(), 'Preserve earlier inventory'
    started = datetime.now(timezone.utc).isoformat()
    case_rows, query_rows, metadata_rows, headers = [], [], [], []
    for stage, folder, raw_folder in [('S7', 'S7_event_replay', 'S6_cut3r_cpu'),
                                    ('S8', 'S8_event_replay_v2', 'S8_cut3r_cpu_v2')]:
        for block in range(3):
            base = ROOT / 'results' / folder / f'block{block}_stride8'
            case = read_json(base / 'prediction_only_selection.json')
            assert case['stride'] == 8 and case['block'] == block
            assert len(case['filters']) == 20 and [q['frame'] for q in case['queries']] == [20, 21, 22, 23]
            case_rows.append({'stage': stage, 'block': block, 'path': str((base/'prediction_only_selection.json').relative_to(ROOT)),
                'top_level_fields': sorted(case), 'history_filter_fields': sorted(case['filters'][0]),
                'history_filter_rows': len(case['filters']), 'query_count': len(case['queries'])})
            for query in case['queries']:
                q = query['frame']
                official = query['maps']['A0P0']['official_trace']
                reads = query['maps']['A0P0']['readouts']
                ppath = ROOT / 'results/S12_matched_budget/selections' / f'{stage}_block{block}_query{q}.json'
                pose = read_json(ppath)
                assert not any('support' in k.lower() or 'score' in k.lower() for k in pose)
                assert len(official['weights']) == 20 and len(official['candidates']) == 14
                assert len(pose['full20_distances_float32']) == 20 and len(pose['pose14_ranked_candidates']) == 14
                query_rows.append({'stage': stage, 'block': block, 'query': q,
                    'source_trace_schema': {k: shape(v) for k,v in official.items()},
                    'source_readout_fields': sorted(reads['official']), 'pose_selection_fields': sorted(pose),
                    'source_selected_pair_availability': selected_pair_availability(reads['official']),
                    'pose_selected_pair_availability': selected_pair_availability(pose['trace']),
                    'pose_selection_path': str(ppath.relative_to(ROOT)),
                    'feature_values_computed': False, 'label_values_read': False})
            for name in ['predicted_poses.npz', 'A0P0.npz', 'observations.npz', 'query20_A0P0_render.npz']:
                headers.append(header_inventory(base/name))
            model = ROOT / 'results' / raw_folder / f'block{block}'
            meta = read_json(model/'run_metadata.json')
            flags = meta.get('view_flags_before_inference', meta.get('prepared_view_flags'))
            assert len(flags) == 24 and all(v['img_mask'] == [True] for v in flags)
            assert all(v['update'] == [i < 20] and v['reset'] == [False] for i,v in enumerate(flags))
            assert meta['history_only_memory_ok'] is True
            metadata_rows.append({'stage': stage, 'block': block, 'history_count': meta['history_count'],
                'query_count': meta['query_count'], 'history_only_memory_ok': meta['history_only_memory_ok'],
                'state_write_policy': meta['state_write_policy'], 'all_query_img_mask_true': True,
                'raw_outputs_fields': sorted(meta['outputs']),
                'per_output_summary_fields': sorted(meta['outputs']['frame0_conf_self']),
                'confidence_mode': meta['model_config']['runtime_attributes']['conf_mode'],
                'checkpoint_commit': meta['commit'], 'predictions_sha256_recorded': meta['predictions_sha256']})
            h = header_inventory(model/'predictions.npz')
            for i in range(24):
                for key in ('conf_self', 'conf', 'pts3d_in_self_view', 'pts3d_in_other_view', 'camera_c2w'):
                    assert f'frame{i}_{key}' in h['members']
            assert h['sha256_compressed_file'] == meta['predictions_sha256']
            headers.append(h)
    source_files = [
        'src/rgbd_retrieval.py', 'src/vmem_retrieval_kernel.py', 'src/retrieval_diagnostic.py',
        'src/s6_memory_bridge.py', 'src/s7_event_replay.py', 'scripts/run_s7_replay.py',
        'scripts/run_s8_replay.py', 'scripts/run_s12_matched_budget.py', 'scripts/run_s6_cut3r.py',
        'vendor/vmem_snapshot/modeling/pipeline.py', 'vendor/cut3r_evaluation_snapshot/src/dust3r/heads/linear_head.py']
    report = {'schema': 's14-deployable-feature-feasibility-inventory-v1', 'status': 'METADATA_AND_HEADER_INSPECTION_COMPLETE',
        'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
        'root': str(ROOT), 'inspector_sha256': sha(Path(__file__)), 'scope': {'stages': ['S7', 'S8'],
            'blocks_per_stage': 3, 'query_ids': [20,21,22,23], 'main_arm': 'A0P0', 'stride': 8,
            'unique_seen_queries': 24, 'independent_scenes': 2},
        'counters': {'prediction_only_json_files': 6, 's12_selection_json_files': 24, 'model_metadata_json_files': 6,
            'npz_files_header_inspected': len(headers), 'npy_headers': sum(len(h['members']) for h in headers),
            'numerical_prediction_arrays_decoded': 0, 'scoring_files_opened': 0, 'raw_images_opened': 0,
            'new_selections': 0, 'thresholds_fitted': 0, 'model_calls': 0, 'feature_value_tables_written': 0},
        'source_code_sha256': {name: sha(ROOT/name) for name in source_files},
        'json_inputs': JSON_INPUTS, 'cases': case_rows, 'queries': query_rows,
        'model_metadata': metadata_rows, 'npz_headers': headers,
        'limits': ['JSON parsing includes prediction-only numerical metadata but computes no candidate-risk features.',
                   'Only NPY header bytes requested through ZipExtFile; ZIP internals can buffer decompressed bytes; no numerical payload interpretation.',
                   'Full compressed NPZ byte streams hashed without loading arrays.',
                   'All queries already seen in prior research; extraction isolation does not restore researcher blindness.',
                   'Current query poses come from real query RGB; deployment for generation-before-query requires a separate interface validation.']}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'inventory': str(OUT), 'sha256': sha(OUT), 'counters': report['counters']}))


if __name__ == '__main__':
    main()
