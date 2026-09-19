"""Independent stdlib readback of S35's already-completed synthetic evidence.

Never import the test, models, scientific libraries or original pipeline. Read
only fixed new synthetic outputs and their source/contract identities. Byte
hashes do not reproduce in-memory pointer/RNG comparisons or PNG decoding.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import hashlib
import json
import struct
import time

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
EXPECTED = {
    'artificial_wiring_frozen_v1.json': 'e206b03c0843c9dacba4f7ba0f194b6e49346488d5b0e12a8423ae5f987b9200',
    'synthetic_wiring_checks_v1/receipt.json': '239d5608e8ac15c0b95017043191c11cd711788ecef354be2dc9e89c8ae28940',
    'synthetic_execution_v1/receipt.json': 'efa96de1afe01d368ca836a87a30b283dee096b646733ac92a11b63236aff185',
    'run_artificial_supervised.py': 'd6c32c305a31346291eb835e7ef0d5843e1929ecfc5c73b7df03d98397b901d3',
}
IDENTITIES = {}


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def read(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    h = digest(raw)
    if str(path) in IDENTITIES:
        assert IDENTITIES[str(path)] == h, 'Changed during independent readback: ' + str(path)
    IDENTITIES[str(path)] = h
    return raw


def document(path):
    return json.loads(read(path))


def tensor_refs(tree, directory):
    count = 0
    if isinstance(tree, dict):
        if tree.get('kind') == 'tensor' and 'blob' in tree:
            p = (directory/tree['blob']).resolve()
            assert p.is_relative_to(directory.resolve())
            raw = read(p)
            base = {k: v for k, v in tree.items() if k not in ('sha256', 'blob')}
            assert len(raw) == tree['nbytes'] and digest(raw) == tree['bytes_sha256']
            assert digest(canonical(base) + b'\0' + raw) == tree['sha256']
            return 1
        for value in tree.values():
            count += tensor_refs(value, directory)
    elif isinstance(tree, list):
        for value in tree:
            count += tensor_refs(value, directory)
    return count


def chain(path, schema):
    raw = read(path)
    assert raw.endswith(b'\n')
    rows = [json.loads(s) for s in raw.splitlines()]
    previous = '0'*64
    for seq, row in enumerate(rows):
        h = row['sha256']
        data = {k: v for k, v in row.items() if k != 'sha256'}
        assert row['schema'] == schema and row['seq'] == seq
        assert row['previous_sha256'] == previous and digest(canonical(data)) == h
        assert row['evidence_kind'] == 'synthetic_test'
        previous = h
    return rows


def metadata(node):
    """Decode archived scalar/container metadata; retain tensor/PIL descriptors."""
    kind = node['kind']
    if kind == 'dict':
        return {metadata(x['key']): metadata(x['value']) for x in node['items']}
    if kind in ('list', 'tuple'):
        return [metadata(x) for x in node['items']]
    if kind == 'scalar':
        return node['value']
    if kind == 'python_float64':
        return struct.unpack('<d', bytes.fromhex(node['little_endian_hex']))[0]
    return node


def inspect_case(label, success, result, contract_sha):
    directory = BASE/'synthetic_wiring_checks_v1'/label
    td, ad = directory/'trace', directory/'archive'
    rows = chain(td/'events.jsonl', 's20-generation-trace-v1')
    ar = chain(ad/'events.jsonl', 's35-full-original-output-archive-v1')
    am = document(ad/'manifest.json')
    prefix = 'success' if success else 'failure'
    tr, aa = result[prefix+'_trace'], result[prefix+'_archive']
    assert rows[0]['payload']['manifest_sha256'] == contract_sha and rows[-1]['event'] == 'session_end'
    assert len(rows) == tr['events'] and rows[-1]['sha256'] == tr['last_sha256']
    references = sum(tensor_refs(r['payload'], td) for r in rows)
    assert references == tr['blob_references_checked']
    assert IDENTITIES[str((ad/'manifest.json').resolve())] == aa['archive_manifest_sha256']
    assert am['evidence_kind'] == 'synthetic_test' and am['scientific_status'] == 'NOT_EVALUATED'
    assert am['caller_manifest_sha256'] == contract_sha
    assert len(ar) == am['event_count'] and ar[-1]['sha256'] == am['last_event_sha256']
    assert len(am['files']) == aa['full_payload_file_count']
    actual_files = {str(p.relative_to(ad)) for p in ad.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    assert actual_files == set(am['files'])
    for name, item in am['files'].items():
        path = (ad/name).resolve()
        assert path.is_relative_to(ad.resolve())
        raw = read(path)
        assert len(raw) == item['bytes'] and digest(raw) == item['sha256']
    for desc in am['tensor_descriptors'].values():
        tensor_refs(desc, ad)
    groups = defaultdict(list)
    for row in ar:
        if row['event'] == 'capture_complete':
            tensor_refs(row['payload']['tree'], ad)
            groups[row['payload']['name']].append(metadata(row['payload']['tree']))
    assert dict(Counter({k: len(v) for k, v in groups.items()})) == am['archived_name_counts']
    completed = [r for r in rows if r['event'] == 'batch_complete']
    failures = [r for r in rows if r['event'] == 'failure']
    n = 2 if success else 1
    assert len(completed) == n and len(failures) == int(not success)
    assert am['status'] == ('ARCHIVE_COMPLETE' if success else 'ARCHIVE_PARTIAL')
    assert len(groups['sample_output']) == len(groups['cache_commit']) == len(groups['map_commit']) == n
    assert len(groups['navigator_return']) == n+1
    assert len(groups['initial_output'][0]['cache']['pil_frames']) == 1
    assert len(groups['navigator_return'][1]['return']) == 5
    retained, selected = [], []
    for j in range(n):
        cc, mc, sample = groups['cache_commit'][j], groups['map_commit'][j], groups['sample_output'][j]
        ids = list(range(1+4*j, 5+4*j))
        assert cc['retained_ids'] == completed[j]['payload']['retained_frame_ids'] == ids
        assert len(mc['cache']['pil_frames']) == 5+4*j
        assert len(mc['map']['surfel_Ks']) == [5,14][j] and len(mc['map']['surfel_depths']) == 5+4*j
        assert sample['samples']['shape'][0] == sample['samples_z']['shape'][0] == 8
        assert cc['target_encoder_embeddings']['shape'][0] == [7,4][j]
        tc = [r for r in rows if r['event'] == 'cache_commit'][j]['payload']['retained']
        for frame in tc:
            for key in ('latents','encoder_embeddings','c2ws','Ks'):
                assert cc['cache'][key][frame['frame_id']]['sha256'] == frame['cache'][key]['sha256']
        retained.append(ids)
    begin = [r for r in rows if r['event'] == 'batch_begin']
    selected = [r['payload']['selected_context_ids'] for r in begin]
    assert selected == [[0], [0,2,4,1]]
    threshold, selection = groups['nms_threshold'][0], groups['nms_selection'][0]
    assert len(groups['nms_threshold']) == len(groups['nms_selection']) == 1
    distances = threshold['pairwise_distances']
    assert len(distances) == 10 and distances == sorted(distances) and threshold['percentile_idx'] == 5
    assert threshold['initial_threshold'] == distances[5] == aa['nms_saved_values_check']['initial_threshold']
    assert selection['selected_indices'] == selected[1] == aa['nms_saved_values_check']['selected_second_context_ids']
    desc = groups['context_output'][1]['context_info']['context_time_indices']
    assert desc['dtype'] == 'int64' and desc['shape'] == [4]
    assert list(struct.unpack('<4q', read(ad/desc['blob']))) == selected[1]
    counters = Counter()
    for row in rows:
        if row['event'] == 'observation' and row['payload'].get('name') == 'actual_call':
            v = row['payload']['values']; counters[v['label']] += 1
            assert v['ordinal'] == counters[v['label']]
    for name, fixture_name in [('euler_step','synthetic_sampler_step'), ('main_model_forward','main_model_forward'),
                               ('vae_encode','vae_encode'),('vae_decode','vae_decode'),('clip_forward','clip_forward'),
                               ('construct_scene','synthetic_construct_scene')]:
        assert counters[name] == result[prefix+'_counts'][fixture_name]
    if not success:
        failure = failures[0]['payload']
        assert failure['phase'] == 'sampling' and failure['exception_type'] == 'InjectedSecondBatchError'
        assert failure['message'] == 'S35_EXPLICIT_SYNTHETIC_SECOND_SAMPLER_FAILURE'
        assert failure['sampler_calls'] == 1 and failure['denoiser_calls'] == 0
        assert set(am['missing_required_names']) == {'sample_output','cache_commit','map_commit'}
        assert ar[-1]['payload']['caller_metadata']['exception_type'] == failure['exception_type']
    return {'trace_events':len(rows), 'archive_events':len(ar), 'archive_payload_files':len(am['files']),
            'trace_blob_references':references, 'status':am['status'], 'retained_ids':retained,
            'selected_context_ids':selected, 'initial_threshold':threshold['initial_threshold'],
            'observed_method_counts':dict(counters), 'completed_batches':n,
            'failure_after_second_sampler_entry':not success, 'payload_bytes_hashed_not_pixel_or_model_recomputed':True}


def main():
    started, t0 = utc(), time.monotonic()
    out = BASE/'executed_results_review.json'
    assert not out.exists()
    for name, expected in EXPECTED.items():
        assert digest(read(BASE/name)) == expected
    c = document(BASE/'artificial_wiring_frozen_v1.json')
    result = document(BASE/'synthetic_wiring_checks_v1/receipt.json')
    external = document(BASE/'synthetic_execution_v1/receipt.json')
    assert result['status'] == 'PASS_NEW_SYNTHETIC_WIRING_ARCHIVE_CHECKS_ONLY'
    assert result['contract_sha256'] == EXPECTED['artificial_wiring_frozen_v1.json']
    assert result['evidence_kind'] == c['evidence_kind'] == 'synthetic_test'
    assert result['source_identities'] == c['source_identities']
    for path, expected in c['source_identities'].items():
        assert digest(read(path)) == expected
    for field in ['source_pre_review','preparation_protocol']:
        assert digest(read(c[field]['path'])) == c[field]['sha256']
    assert digest(read(ROOT/'scripts/s26b_consumer_baseline.py')) == c['external_supervisor']['base_sha256']
    assert EXPECTED['run_artificial_supervised.py'] == c['external_supervisor']['wrapper_sha256']
    dt = datetime.fromisoformat
    assert dt(c['frozen_utc']) < dt(external['started_utc']) <= dt(result['started_utc'])
    assert dt(result['completed_utc']) <= dt(external['completed_utc'])
    assert external['status'] == 'PASS' and external['returncode'] == 0
    assert external['wall_seconds'] < c['limits']['seconds'] and external['peak_rss_bytes'] < c['limits']['rss_bytes']
    assert external['command'][-1] == EXPECTED['artificial_wiring_frozen_v1.json']
    cases = {label:inspect_case(label, success, result, result['contract_sha256']) for label,success in
             [('observed_success',True),('observed_second_batch_failure',False)]}
    for path, expected in list(IDENTITIES.items()):
        assert digest(Path(path).read_bytes()) == expected
    record = {'schema':'s35-executed-synthetic-independent-readback-v1',
        'status':'PASS_SAVED_SYNTHETIC_EVIDENCE_REVIEW_ONLY','passed':True,
        'reviewer':'/root/supervisor_full_readthrough','started_utc':started,'completed_utc':utc(),
        'readback_wall_seconds':time.monotonic()-t0,'readback_source_sha256':digest(Path(__file__).read_bytes()),
        'evidence_kind':'synthetic_test','identities':IDENTITIES,'cases':cases,
        'source_review_scope':'Full 49-line supervisor wrapper and bounded supervisor function; artificial test run_case/readback/main and tiny-component definitions inspected to qualify claims. No new full audit or test execution.',
        'external_execution':external, 'contract_frozen_utc':c['frozen_utc'],
        'independently_readback_verified':['Frozen/source/result SHA and chronological order','Both complete hash chains and all archive physical file bytes plus referenced trace blobs','Synthetic labels; complete versus failure prefix and original exception type/message','1/5/9 and 1/5 histories, raw all-eight shapes and complete 7/4 embedding rows','NMS actual ten saved distances, index five, threshold and ordered returned context IDs','Original trace method counters, ordinal order and cache descriptor identities'],
        'runtime_assertions_reported_not_reperformed':['In-memory exception object identity and original return-object identity','Plain versus observed complete arrays and Python/NumPy/Torch RNG equality','All hook identity restoration and global gradient/inference mode restoration','PNG pixels decoded equal to fixture values'],
        'limits':['No original neural network, 50-step sampler, 400-GA, original renderer or real generation was executed in this synthetic test.','Independent byte hashing is not neural/mathematical recomputation or quality scoring.','External peak is sampled process-tree RSS; inherited artificial supervisor is not the new full-run launcher and its kill-tree behavior was not exercised.','Draft refusal and resource rejection are separate from full real resource readiness.'],
        'new_model_ga_renderer_or_test_runs':0,'scientific_library_imports':0,'real_photos_gt_weights_npz_read':0,
        'synthetic_metadata_and_saved_bytes_read':True,'scientific_status':'NOT_EVALUATED'}
    with out.open('x') as handle:
        json.dump(record,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print(json.dumps({'path':str(out),'sha256':digest(out.read_bytes()),'status':record['status'],
                      'cases':cases,'readback_wall_seconds':record['readback_wall_seconds']},indent=2))


if __name__ == '__main__':
    main()
