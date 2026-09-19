"""One selective saved-output readback after an actual S64 terminal return.

Source preparation only. No model import, image codec, image display or generation.
The reviewed S40 numerical consumption checks are reused; their whole-archive
payload sweep is deliberately not used. Prefix differences are diagnostics.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time
import traceback
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'work/S40_result_readback/readback.py'
BASE_SHA = 'd4c22504569ad1fb1fcc74ea1da83b4f244f4de803f5d0fadc16e8da06777933'
LAUNCHER_SHA = '2998383f07bd9437440b24f465ef5624d7291890b8f750c9b6ce2795c33bfb35'
AUTHOR_SHA = 'd418449ac50228dabbe2c1aac1281c775ecc3e2c61a8c09af1c228116aa10e17'
OLD = ROOT / 'results/S47B_C2_confirmation_generation_v9/archive'
OLD_MANIFEST_SHA = '7cfd56b59924fb3c603a3eb54c34f387db8439c72fc4a6fe08e3097dcf659b4c'
OLD_EVENTS_SHA = 'b51b39e1772a7a2cbc0221bc0846d95cd3b7c8b21f8978ddbbd0f1d2443f6ef7'
ROW = 'C2_UNIT_REPAIRED_S64'
VARIANT = 's64_positive_camera_depth_median_units_v1'


def checked_source(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('Frozen source differs: ' + str(path))
    return ast.parse(raw, filename=str(path))


def derive_helpers(compile_only=False):
    """Extract pure definitions and the unchanged S40 numerical check block."""
    tree = checked_source(BASE, BASE_SHA)
    names = {'TensorDescriptor', 'utc', 'require', 'canonical', 'signature',
             'write_new', 'Reader', 'trace_states'}
    selected = [copy.deepcopy(n) for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names
                or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name)
                and t.id in ('WIDTHS', 'FIELDS') for t in n.targets)]
    run = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run'))
    first = next(i for i, n in enumerate(run.body) if isinstance(n, ast.FunctionDef) and n.name == 'groups')
    run.name = 'check_consumption'
    run.args = ast.parse('def f(a,r,m,am,ad,ar,tr,summary,states): pass').body[0].args
    run.body = run.body[first:]
    # Only omit the old five-image cross-cache loop. Numeric cache continuity is
    # still checked; generated first-prefix RGB bodies are checked separately.
    omitted = [n for n in run.body if isinstance(n, ast.For)
               and 'cross_batch:pixels' in ast.unparse(n)]
    if len(omitted) != 1:
        raise ValueError('Expected exactly the existing cross-cache RGB loop')
    run.body = [n for n in run.body if n is not omitted[0]]
    selected.append(run)
    original_unit = checked_source(HERE / 'launch_generation.py', LAUNCHER_SHA)
    selected.append(copy.deepcopy(next(n for n in original_unit.body
                   if isinstance(n, ast.FunctionDef) and n.name == 'collect_unit_receipts')))
    module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    code = compile(module, str(BASE) + '[S64 selective postrun]', 'exec')
    proof = dict(parent_sha256=BASE_SHA, numerical_block_starts_at_line=run.body[0].lineno,
                 omitted_original_cross_cache_RGB_loop=1,
                 remaining_numerical_statements_unchanged=True,
                 original_collect_unit_receipts_AST_unchanged=True)
    if compile_only:
        return proof
    ns = dict(globals())
    exec(code, ns)
    return ns, proof


def prepare_reader(ns):
    class SelectiveReader(ns['Reader']):
        def __init__(self):
            super().__init__(300)
            self.archives = {}
            self.rgb_paths = set()
        def descriptor(self, d, ad, require_blob=True):
            if require_blob:
                manifest = self.archives[str(Path(ad).resolve())]
                ns['require'](manifest['tensor_descriptors'][d['blob']] == dict(d),
                              'Event and archive descriptor differ')
                item = manifest['files'][d['blob']]
                ns['require'](item['sha256'] == d['bytes_sha256'] and item['bytes'] == d['nbytes'],
                              'Archive and descriptor body identity differ')
            return super().descriptor(d, ad, require_blob)
        def array(self, d, ad):
            self.descriptor(d, ad)
            return super().array(d, ad)
    return SelectiveReader()


def archive_metadata(r, ns, ad, expected=None, complete=True):
    require = ns['require']
    am = r.doc(ad / 'manifest.json', expected)
    r.archives[str(ad.resolve())] = am
    require(am['status'] == ('ARCHIVE_COMPLETE' if complete else 'ARCHIVE_PARTIAL')
            and am['evidence_kind'] == 'recorded_execution' and am['failed_captures'] == 0,
            'Unexpected archive status')
    if complete:
        require(not am['missing_required_names'], 'Required capture missing')
        actual = {str(p.relative_to(ad)) for p in ad.rglob('*') if p.is_file() and p != ad / 'manifest.json'}
        require(actual == set(am['files']), 'Archive inventory differs')
        for name, item in am['files'].items():
            require(r.path(ad, name).stat().st_size == item['bytes'], 'Archive file size differs')
    rows = r.chain(ad / 'events.jsonl', 's35-full-original-output-archive-v1')
    require(len(rows) == am['event_count'] and rows[-1]['sha256'] == am['last_event_sha256']
            and rows[0]['event'] == 'archive_start' and rows[-1]['event'] == 'archive_finalize',
            'Archive event closure differs')
    groups = defaultdict(list)
    pending = {}
    for row in rows:
        p, ev = row['payload'], row['event']
        if ev == 'capture_begin':
            pending[row['seq']] = (p['name'], p['occurrence'])
        elif ev == 'capture_complete':
            require(pending.pop(p['begin_seq']) == (p['name'], p['occurrence'])
                    and p['occurrence'] == len(groups[p['name']]), 'Capture pairing differs')
            groups[p['name']].append((row['seq'], r.metadata(p['tree'])))
        else:
            require(ev in ('archive_start', 'archive_finalize')
                    or not complete and ev == 'caller_failure', 'Unexpected archive event')
    require(not pending and {k: len(v) for k, v in groups.items()} == am['archived_name_counts'],
            'Capture coverage differs')
    # Classify only potential RGB reads. This walks metadata, not image bodies.
    for name, items in groups.items():
        for _, obj in items:
            rgb = []
            if name == 'sample_output': rgb.append(obj['samples'])
            if name == 'encode_image_input': rgb.append(obj['image'])
            if 'cache' in obj:
                rgb.extend(i['pixels'] for i in obj['cache'].get('pil_frames', []))
            r.rgb_paths.update(str((ad / d['blob']).resolve()) for d in rgb)
    return am, groups, rows


def terminal(a, r, ns):
    require = ns['require']
    mpath = HERE / 'review_attachment_01/manifest.json'
    m = r.doc(mpath, a.manifest_sha256)
    require(m['row'] == ROW and m['retrieval_variant']['id'] == VARIANT
            and m['retrieval_variant']['eligible_for_original_cohort'] is False
            and m['variant']['repo'] == 'stabilityai/sd-vae-ft-mse', 'Wrong scientific identity')
    require(Path(m['output_root']) == ROOT / 'results/S64_unit_repaired_generation'
            and len(m['source_identities']) == 221, 'Wrong S64 output or source domain')
    r.doc(HERE / 'AUTHOR_DELIVERY.json', AUTHOR_SHA)
    for path, digest in m['source_identities'].items(): r.hash(path, digest)
    r.hash(HERE / 'launch_generation.py', LAUNCHER_SHA)
    ex, out = HERE / 'execution_01', Path(m['output_root'])
    extdir = HERE / 'external_launch_01'
    ext = r.doc(extdir / 'receipt.json', a.external_receipt_sha256)
    commit = r.doc(ex / 'supervisor_terminal_commit.json', a.terminal_commit_sha256)
    paths = dict(parent_receipt_sha256=ex/'receipt.json', worker_receipt_sha256=ex/'worker_receipt.json',
                 watchdog_receipt_sha256=ex/'watchdog_receipt.json',
                 attempt_started_sha256=ex/'supervisor_attempt_started.json',
                 terminal_provisional_sha256=ex/'supervisor_terminal_provisional.json',
                 manifest_sha256=mpath, launcher_sha256=HERE/'launch_generation.py')
    for key, path in paths.items(): r.hash(path, commit[key])
    parent, worker, watchdog = [r.doc(paths[k]) for k in
                               ('parent_receipt_sha256', 'worker_receipt_sha256', 'watchdog_receipt_sha256')]
    for stream in ('stdout', 'stderr'): r.hash(extdir/(stream+'.txt'), ext[stream+'_sha256'])
    require(ext['returncode'] == parent['returncode'] == watchdog['worker_returncode']
            == commit['parent_returncode'] == 0 and ext['external_timeout'] is False,
            'S64 did not return successfully; stop before scientific payload bodies')
    expected_argv = [str(ROOT/'.venv-cut3r/bin/python'), '-B', str(HERE/'launch_generation.py'),
                     '--manifest', str(mpath), '--manifest-sha256', a.manifest_sha256,
                     '--execution-directory', str(ex)]
    require(ext['argv'] == expected_argv and ext['supervisor_pid'] == commit['supervisor_pid'],
            'External return does not identify this launcher invocation')
    require(commit['outcome_status'] == 'RUN_RETURNED_PENDING_INDEPENDENT_REVIEW'
            and commit['standalone_success'] is False and commit['row'] == worker['row'] == ROW
            and commit['retrieval_variant'] == worker['retrieval_variant'] == m['retrieval_variant'],
            'Terminal variant or outcome mismatch')
    require(parent['status'] == 'C2_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW'
            and worker['status'] == parent['worker_status'] == 'C2_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW'
            and parent['worker_receipt_sha256'] == commit['worker_receipt_sha256']
            and parent['manifest_sha256'] == worker['manifest_sha256'] == a.manifest_sha256
            and parent['source_sha256'] == worker['source_sha256'] == LAUNCHER_SHA
            and worker['runtime_factory_calls'] == worker['full_resource_checks'] == 1
            and parent['source_unchanged_at_close'] and worker['source_unchanged_at_close'],
            'Worker/parent completion mismatch')
    require(watchdog['cleanup_complete'] and watchdog['all_registered_descendants_gone']
            and watchdog['supervisor_completed_protocol'] and not watchdog['supervisor_liveness_lost'],
            'Watchdog did not confirm completion')
    for name in ('.execution_01.supervisor_failure.json', '.execution_01.watchdog_failure.json'):
        require(not os.path.lexists(HERE/name), 'Root failure receipt exists')
    consumed = worker['scientific_consumption_binding']
    require(consumed == commit['scientific_consumption_binding']
            and consumed['all_required_resources_consumed'] is True, 'Actual resource consumption incomplete')
    for obj in (commit, worker, watchdog):
        for key, path in [('execution_identity', ex), ('output_identity', out)]:
            if key in obj:
                st = path.stat()
                require(obj[key]['device'] == st.st_dev and obj[key]['inode'] == st.st_ino,
                        'Terminal directory identity differs')
    fd = os.open(out, os.O_RDONLY)
    try:
        def validate_output():
            held, current = os.fstat(fd), out.stat()
            expected = commit['output_identity']
            require(held.st_dev == current.st_dev == expected['device']
                    and held.st_ino == current.st_ino == expected['inode'], 'Unit output directory changed')
        def read_json_at(receipt_fd, name, label):
            require(receipt_fd == fd, 'Unit helper selected a different directory')
            path = r.path(out, name)
            return r.doc(path), r.hash(path)
        ns['read_json_at'] = read_json_at
        binding = ns['collect_unit_receipts'](SimpleNamespace(fd=fd, validate=validate_output), m, a.manifest_sha256)
        validate_output()
    finally:
        os.close(fd)
    require(binding['complete'] and binding == worker['retrieval_unit_binding']
            == commit['retrieval_unit_binding'], 'Actual unit call/terminal SHA binding differs')
    loading = r.doc(out/'runtime_loading.json')
    require(loading['status'] == 'PASS_S47_C2_DECLARED_VARIANT_COMPONENT_LOADING_ONLY'
            and loading['manifest_sha256'] == a.manifest_sha256 and loading['row'] == ROW
            and loading['retrieval_variant'] == m['retrieval_variant'] and loading['variant'] == m['variant'],
            'Runtime scientific identity differs')
    return m, worker, binding


def prefix_diagnostic(r, ns, new_groups, ad):
    require = ns['require']
    r.hash(OLD/'events.jsonl', OLD_EVENTS_SHA)
    _, old, _ = archive_metadata(r, ns, OLD, OLD_MANIFEST_SHA, complete=False)
    def fields(groups):
        require(all(len(groups[k]) >= 1 for k in ('sampler_input', 'sample_output', 'cache_commit')),
                'First prefix captures missing')
        sample, cache = groups['sample_output'][0][1], groups['cache_commit'][0][1]['cache']
        result = {'noise': groups['sampler_input'][0][1]['noise'],
                  'samples_z': sample['samples_z'], 'samples': sample['samples']}
        for key in ns['FIELDS']:
            require(len(cache[key]) == 5, 'First prefix cache does not have five rows')
            for i, d in enumerate(cache[key]): result[f'cache.{key}.{i}'] = d
        for i in range(1, 5): result[f'cache.pil_frames.{i}.pixels'] = cache['pil_frames'][i]['pixels']
        return result
    before, after, items = fields(old), fields(new_groups), []
    for name, left in before.items():
        right = after[name]
        declared = all(left[k] == right[k] for k in ('dtype', 'shape', 'nbytes', 'bytes_sha256'))
        r.descriptor(left, OLD); r.descriptor(right, ad)
        actual_equal = (left['dtype'] == right['dtype'] and left['shape'] == right['shape']
                        and r.hash(OLD/left['blob']) == r.hash(ad/right['blob']))
        items.append(dict(field=name, declared_content_identity_equal=declared,
                          actual_body_identity_equal=actual_equal,
                          old_descriptor=left, new_descriptor=right))
    return dict(scope='first occurrence only; diagnostic, never an engineering-success or retry gate',
                fields=items, all_actual_body_identities_equal=all(i['actual_body_identity_equal'] for i in items),
                difference_is_not_causal_proof=True, image_display_count=0)


def run(a, r, ns):
    require = ns['require']
    m, worker, unit = terminal(a, r, ns)
    out = Path(m['output_root']); ad = out/'archive'
    ref = worker['archive_receipt']
    require(Path(ref['path']) == ad/'manifest.json', 'Wrong archive binding')
    am, groups, ar = archive_metadata(r, ns, ad, ref['sha256'])
    require(am['caller_manifest_sha256'] == a.manifest_sha256
            and am['source_identities'] == m['source_identities'], 'Archive source identity differs')
    r.groups = groups
    tr = r.chain(out/'trace/events.jsonl', 's20-generation-trace-v1')
    r.hash(out/'trace/events.jsonl', worker['trace_events_sha256'])
    require(tr[0]['payload']['manifest_sha256'] == a.manifest_sha256
            and tr[0]['payload']['source_identities'] == m['source_identities'], 'Trace identity differs')
    states = ns['trace_states'](tr)
    summary = r.doc(out/'observation_summary.json', worker['observation_summary_sha256'])
    for name in ('render_input', 'render_output', 'retrieval_output'):
        require(len(groups[name]) == 1, 'Expected one actual second-context ' + name)
    require(groups['map_commit'][0][0] < groups['render_input'][0][0]
            < groups['render_output'][0][0] < groups['retrieval_output'][0][0]
            < groups['context_output'][1][0], 'Actual unit/retrieval/second-context order differs')
    consumed = ns['check_consumption'](a, r, m, am, ad, ar, tr, summary, states)
    require(len(consumed['actual_selected_context_ids'][1]) == 4, 'Second context did not return four legal IDs')
    consumed.pop('trace_descriptors_without_saved_blob', None)
    consumed['scope'] = 'Selective actual tensor-body checks: two completed batches, real cache -> get_cond -> sampler -> retained cache; archive inventory and metadata, not every archive body'
    return dict(row=ROW, retrieval_variant=m['retrieval_variant'], terminal_and_unit_binding=unit,
                engineering_consumption=consumed, first_prefix=prefix_diagnostic(r, ns, groups, ad),
                evidence_kind='existing_generated_data_readback', quality_status='NOT_EVALUATED',
                eligible_for_original_cohort=False, new_method_validated=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compile-only', action='store_true')
    for name in ('manifest-sha256', 'external-receipt-sha256', 'terminal-commit-sha256', 'out'):
        parser.add_argument('--' + name)
    a = parser.parse_args()
    if a.compile_only:
        print(json.dumps(derive_helpers(True), indent=2)); return 0
    if not all((a.manifest_sha256, a.external_receipt_sha256, a.terminal_commit_sha256, a.out)):
        parser.error('Actual completed-run manifest, external receipt, terminal commit SHA and create-only output are required')
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=False)
    ns, proof = derive_helpers(); r = prepare_reader(ns)
    record = dict(schema='s64-selective-postrun-readback-v1', started_utc=ns['utc'](),
                  status='CHECKING', passed=False, derivation=proof,
                  source_sha256=r.hash(Path(__file__)), model_calls=0, image_display_count=0)
    try:
        report = run(a, r, ns)
        for path, item in r.files.items():
            ns['require'](list(ns['signature'](Path(path))) == item['stat'], 'Input changed before seal')
        ns['write_new'](out/'report.json', report)
        record.update(status='PASS_S64_ENGINEERING_READBACK_ONLY', passed=True,
                      report_sha256=r.hash(out/'report.json'))
    except BaseException as error:
        record.update(status='FAILED_OR_PARTIAL_S64_READBACK', error_type=type(error).__name__,
                      error=str(error), traceback=traceback.format_exc())
    finally:
        payloads = {p: dict(r.files[p], dtype=d['dtype'], shape=d['shape'],
                           content_kind='RGB_body' if p in r.rgb_paths else 'numeric_body')
                    for p, d in r.tensor_files.items()}
        record.update(completed_utc=ns['utc'](), elapsed_seconds=time.monotonic()-r.started,
                      unique_verified_payload_files=len(payloads),
                      unique_verified_payload_bytes=sum(v['bytes'] for v in payloads.values()),
                      unique_verified_RGB_body_bytes=sum(v['bytes'] for v in payloads.values() if v['content_kind']=='RGB_body'),
                      payload_readlist=payloads, all_file_readlist=r.files,
                      RGB_note='FP32 samples and uint8 pixel bytes are RGB body reads even without display; byte totals are unique files, not physical I/O counts',
                      quality_status='NOT_EVALUATED', new_method_validated=False,
                      limitations=['No model/renderer/get_cond recomputation, image viewing or quality score.',
                                   'Source and event identities plus selected payload bodies; unselected bodies are inventory/size only.',
                                   'Prefix mismatch is retained diagnostic data, not grounds for a retry or causal attribution.'])
        ns['write_new'](out/'receipt.json', record)
    return 0 if record['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
