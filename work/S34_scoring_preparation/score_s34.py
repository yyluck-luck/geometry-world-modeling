#!/usr/bin/env python3
"""Fixed S34 three-condition/new-four-frame sensor scoring, no model imports."""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import io
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SELF = Path(__file__).resolve()
PROTOCOL = HERE / 'protocol.md'
ORIGINAL = ROOT / 'scripts/score_s26b_consumer.py'
ORIGINAL_SHA = '02317889281583ae0fd8a12a1148811c9e9a0afb7bcf75275aea9fd1a34f5cc7'
METADATA = ROOT / 'work/S26_scoring_preparation/candidate_scoring_inputs.json'
BASE = ROOT / 'results/S34_geometry_producer'
OUT = ROOT / 'results/S34_depth_scoring'
ENDS = ('old_fixed_zero', 'old_fixed_free_400', 'old_fixed_common_scale_400')
MODES = ('common_old',) + ENDS
NEW = [4, 5, 6, 7]
SCHEMA = 's34-fixed-new4-depth-scoring-v1'

def utc():
    return datetime.now(timezone.utc).isoformat()

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def write(p, value):
    Path(p).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')

def require(ok, why):
    if not ok:
        raise ValueError(why)

def load_original():
    spec = importlib.util.spec_from_file_location('s34_fixed_s26b_metric', ORIGINAL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run(manifest, expected):
    require(sha(manifest) == expected, 'Caller must bind frozen scoring manifest')
    config = read(manifest)
    require(config['schema'] == SCHEMA and config['status'] == 'FROZEN', 'Only frozen protocol can run')
    require(config['endpoints'] == list(ENDS) and config['new_indices'] == NEW, 'All fixed three endpoints and new four')
    require(config['output_root'] == str(OUT), 'Fixed destination')
    require(config['resource'] == dict(cpu_threads=1, wall_seconds=120, rss_bytes=2 * 1024**3), 'Fixed scoring budget')
    controls = config['control_sha256']
    require({str(SELF), str(PROTOCOL), str(ORIGINAL), str(METADATA)} <= set(controls), 'Every metric/source control bound')
    require(controls[str(ORIGINAL)] == ORIGINAL_SHA, 'Original metric source identity')
    require(not OUT.exists(), 'Do not overwrite any previous attempt')
    OUT.mkdir(parents=True)
    receipt = dict(status='RUNNING', started_utc=utc(), scoring_manifest_sha256=expected,
                   model_runs=0, MST_runs=0, Adam_steps=0, backward_calls=0, clean_calls=0,
                   sensor_GT_byte_reads_started=False, prediction_decode_started=False)
    write(OUT / 'receipt.json', receipt)
    try:
        ids = {str(manifest): expected, **controls}
        for p, h in ids.items():
            require(sha(p) == h, 'Changed source/control: ' + p)
        inherited = read(METADATA)['gt_depth_frames'][4:8]
        require(config['gt_depth_frames'] == inherited, 'Exact previous four GT identities; no rematching')
        require([r['index'] for r in inherited] == NEW, 'Fixed frame order')
        producer = config['producer_contract']
        require(sha(producer['path']) == producer['sha256'], 'Producer contract changed')
        require(read(producer['path'])['status'] == 'FROZEN', 'Producer contract must have been frozen')
        ids[producer['path']] = producer['sha256']
        barrier_ref = config['terminal_barrier']
        require(sha(barrier_ref['path']) == barrier_ref['sha256'], 'Whole producer and consumer terminal barrier')
        ids[barrier_ref['path']] = barrier_ref['sha256']
        barrier = read(barrier_ref['path'])
        require(barrier['status'] == 'SEALED_ALL_GEOMETRY_AND_CONSUMER_TERMINAL', 'Do not score unfinished endpoints')
        require(barrier['producer_contract_sha256'] == producer['sha256'], 'Common experiment binding')
        require(set(barrier['producer_receipts']) == set(MODES), 'All four producers retained')
        # Hash all output bytes before the first array decode or GT byte read.
        for p, h in barrier['sealed_files'].items():
            require(sha(p) == h, 'Terminal byte barrier changed: ' + p)
            ids[p] = h
        buffers = {}
        for mode in MODES:
            directory = BASE / mode
            rp = directory / 'receipt.json'
            require(str(rp) in ids and ids[str(rp)] == barrier['producer_receipts'][mode], 'Exact producer receipt seal')
            r = read(rp)
            require(r['status'] == 'PASS' and r['contract_sha256'] == producer['sha256'], 'Producer must pass fixed inputs')
            npz = directory / 'packet.npz'
            require(str(npz) in ids and ids[str(npz)] == r['outputs']['packet.npz'], 'Exact clean packet seal')
            for relative, h in r['outputs'].items():
                p = directory / relative
                require(str(p) in ids and ids[str(p)] == h, 'All producer outputs bound')
            buffers[mode] = npz.read_bytes()
            require(hashlib.sha256(buffers[mode]).hexdigest() == ids[str(npz)], 'Read buffer belongs to barrier')
        consumer = barrier['consumer_terminal']
        require(consumer['status'] in ('PASS_ORIGINAL_CONSUMER_COMPONENTS', 'FAILED_PRESERVED'), 'Actual consumer terminal state required')
        require(consumer['receipt_path'] in ids, 'Consumer terminal receipt sealed')
        cr = read(consumer['receipt_path'])
        require(cr['status'] == consumer['status'], 'Consumer status matches actual receipt')
        cmref = consumer['manifest']
        require(cmref['path'] == str(ROOT / 'work/S34_consumer_preparation/manifest.json'), 'Fixed consumer manifest path')
        require(cmref['path'] in ids and ids[cmref['path']] == cmref['sha256'] == cr['manifest_sha256'], 'Actual consumer manifest identity')
        cm = read(cmref['path'])
        require(cm['status'] == 'FROZEN' and cm['schema'] == 's34-original-consumer-manifest-v1', 'Same formal consumer experiment')
        require(cm['producer_contract'] == producer and list(cm['packets']) == list(MODES), 'Consumer binds this producer and all four packets')
        for mode, binding in cm['packets'].items():
            require(binding['receipt_sha256'] == barrier['producer_receipts'][mode]
                    and binding['sha256'] == ids[str(BASE / mode / 'packet.npz')], 'Consumer used these exact packets')
        for relative, h in cr.get('outputs', {}).items():
            cp = str(Path(consumer['receipt_path']).parent / relative)
            require(cp in ids and ids[cp] == h, 'Consumer outputs included in terminal seal')
        write(OUT / 'pre_score_seal.json', dict(status='PASS_BYTE_BARRIER', utc=utc(), input_sha256=ids,
              sensor_GT_bytes_read=False, prediction_arrays_decoded=False, consumer_terminal=consumer))
        receipt.update(prediction_decode_started=True)
        write(OUT / 'receipt.json', receipt)
        import numpy as np
        arrays, diagnostics = {}, {}
        for mode, raw in buffers.items():
            n = 4 if mode == 'common_old' else 8
            shapes = dict(depth=(n,384,512), point_cloud=(n,384,512,3), conf=(n,384,512),
                          focal=(n,1), pp=(n,2), c2w=(n,4,4))
            with np.load(io.BytesIO(raw), allow_pickle=False) as z:
                require(set(z.files) == set(shapes), 'Fixed six packet fields')
                arrays[mode] = {k: z[k] for k in shapes}
            diagnostics[mode] = {}
            for key, shape in shapes.items():
                a = arrays[mode][key]
                require(a.shape == shape and a.dtype == np.float32, 'FP32 packet schema: ' + mode + '/' + key)
                diagnostics[mode][key] = dict(shape=list(a.shape), dtype=str(a.dtype), nonfinite=int((~np.isfinite(a)).sum()))
        del buffers
        old = arrays['common_old']['depth'].astype(np.float64)
        require(np.isfinite(old).all() and (old > 0).all(), 'Valid common old depth')
        old_checks = {}
        for mode in ENDS:
            a = arrays[mode]['depth'][:4].astype(np.float64)
            delta = np.abs(a - old)
            bad = (~np.isfinite(a)) | (a <= 0) | (delta > 1e-5 + 1e-5 * np.abs(old))
            old_checks[mode] = dict(max_abs_difference_m=float(delta.max()), outside_tolerance_count=int(bad.sum()),
                                    atol=1e-5, rtol=1e-5, raw_frozen_gate='See producer; output roundtrip is not raw object identity')
            require(not bad.any(), 'Frozen old output roundtrip violated')
        write(OUT / 'schema_and_old_prefix.json', dict(schema=diagnostics, old_prefix_checks=old_checks))
        helper = load_original()
        receipt.update(sensor_GT_byte_reads_started=True, sensor_GT_read_started_utc=utc())
        write(OUT / 'receipt.json', receipt)
        gt, gt_records, gt_ids = helper.load_sensor_depths(inherited)
        ids.update(gt_ids)
        write(OUT / 'gt_receipt.json', dict(utc=utc(), files=gt_records, already_seen=True, images_decoded=4))
        rows = []
        for mode in ENDS:
            for i, g in zip(NEW, gt):
                rows.append(dict(endpoint=mode, index=i, partition='new', **helper.depth_metrics(arrays[mode]['depth'][i], g)))
        groups = {mode: helper.aggregate([r for r in rows if r['endpoint'] == mode], NEW) for mode in ENDS}
        require(len(rows) == 12, 'Complete fixed twelve-row denominator')
        write(OUT / 'metrics.json', dict(schema=SCHEMA, scoring_manifest_sha256=expected, per_frame=rows,
              primary_new4=groups, prespecified_rows=12, prespecified_groups=3, consumer_terminal=consumer,
              GT_scale_fit=False, confidence_mask=False, far_depth_cut=False, global_rescaling=False,
              evidence_scope='Saved real eight-frame replay; shared old4 depth; given GT cameras; descriptive new4 sensor scoring, no retrieval or video-quality verdict'))
        with (OUT / 'per_frame.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        for p, h in ids.items():
            require(sha(p) == h, 'Input changed while scoring: ' + p)
        receipt.update(status='PASS', completed_utc=utc(), sensor_GT_images_decoded=4, per_frame_rows=12,
                       endpoint_groups=3, input_sha256=ids, inputs_unchanged=True, consumer_terminal=consumer,
                       outputs={p.name: sha(p) for p in OUT.iterdir() if p.name != 'receipt.json'},
                       meaning='Scoring completed; NA and consumer failures remain explicit, not full project or novelty success')
        write(OUT / 'receipt.json', receipt)
        print(json.dumps(dict(status='PASS', rows=12, primary_new4=groups)))
    except BaseException as exc:
        receipt.update(status='FAILED', failed_utc=utc(), error=repr(exc))
        write(OUT / 'receipt.json', receipt)
        raise

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', required=True)
    p.add_argument('--sha256', required=True)
    a = p.parse_args()
    run(Path(a.manifest).resolve(), a.sha256)
