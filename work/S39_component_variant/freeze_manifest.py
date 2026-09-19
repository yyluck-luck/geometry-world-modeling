"""Prepare an immutable S39 resource core; attach real external reviews separately.

Standard library only. This tool never imports a model, creates a review, or
replaces the loading worker's full content verification with a cached signature.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GATE_SHA = 'cf667bdc0bc43f902d0dca3041c4dbf33a53d908ee4e5d13ebfba2f853a78f4e'
DRAFT_SHA = '21443f4b2fdd7c91e166c55a6ed2855d397ae5ba71b49da4d7d417d443ff6ee2'
CHANGI = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/test_samples/changi.jpg')
CONFIG = ROOT/'work/S20_environment/isolated_vmem_source/configs/inference/inference.yaml'
TOOL_FILES = [Path(__file__).resolve(), HERE/'FREEZE_PROTOCOL_DRAFT.md']


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def signature(path):
    path = Path(path).resolve(strict=True)
    s = path.stat()
    require(stat.S_ISREG(s.st_mode), 'Regular file required: '+str(path))
    return dict(path=str(path), size=s.st_size, mtime_ns=s.st_mtime_ns,
                ctime_ns=s.st_ctime_ns, device=s.st_dev, inode=s.st_ino)


def from_fd(s, path):
    return dict(path=path, size=s.st_size, mtime_ns=s.st_mtime_ns,
                ctime_ns=s.st_ctime_ns, device=s.st_dev, inode=s.st_ino)


def write_new(path, payload):
    with Path(path).open('x') as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


def bind_gate():
    path = HERE/'s39_variant_gate.py'
    require(sha(path) == GATE_SHA, 'Pinned v2 gate changed')
    spec = importlib.util.spec_from_file_location('_s39_freeze_bound_gate', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Only the pinned standard-library gate.
    return module


def hash_once(record, expected, audit, label):
    """One streaming body read, with pathname and opened-descriptor stat checks."""
    require(signature(record['path']) == record, 'File changed before hash: '+label)
    h = hashlib.sha256(); count = 0
    with Path(record['path']).open('rb') as handle:
        require(from_fd(os.fstat(handle.fileno()), record['path']) == record, 'Opened file differs: '+label)
        while block := handle.read(8*1024*1024):
            h.update(block); count += len(block)
        require(from_fd(os.fstat(handle.fileno()), record['path']) == record, 'File changed during hash: '+label)
    digest = h.hexdigest()
    item = dict(label=label, **record, actual_sha256=digest, expected_sha256=expected,
                bytes_read=count, checked_utc=utc(), stat_unchanged=signature(record['path']) == record)
    audit.write(json.dumps(item, ensure_ascii=False, allow_nan=False)+'\n')
    audit.flush(); os.fsync(audit.fileno())
    require(item['stat_unchanged'] and count == record['size'], 'File changed during hash: '+label)
    require(expected is None or digest == expected, 'Full content SHA mismatch: '+label)
    return digest


def common_metadata(m, gate):
    require(m['schema'] == gate.SCHEMA and m['variant'] == gate.VARIANT, 'Wrong component variant')
    require(m['controls'] == gate.REF.CONTROLS and m['runtime'] == gate.RUNTIME and
            m['loading_limits'] == gate.LIMITS, 'Fixed settings changed')
    require(m['source_identities'] == gate.required_sources(), 'Pinned source domain changed')
    require(m['config']['path'] == str(CONFIG) and m['config']['sha256'] == gate.REF.ORIGINAL_CONFIG_SHA,
            'Original inference YAML changed')
    output = Path(m['output_root'])
    require(output.is_absolute() and not output.exists() and output.parent.is_dir(), 'Fresh output root required')
    require(Path(gate.RUNTIME['python_executable']).is_file() and
            all(Path(p).is_dir() for p in gate.RUNTIME['pythonpath']), 'Missing runtime paths')


def prepare(a, out, gate, receipt):
    draft = HERE/'manifest_draft.json'
    require(sha(draft) == DRAFT_SHA, 'Pinned v2 draft changed; review a new tool version first')
    m = json.loads(draft.read_text())
    require(m['status'] == 'DRAFT_NOT_READY_FOR_COMPONENT_LOADING' and m['review_receipts'] == {}, 'Not the unreviewed draft')
    require(m['input_image']['path'] == str(CHANGI), 'Fixed changi path changed')
    common_metadata(m, gate)
    paths = dict(vmem=a.vmem, clip=a.clip, cut3r=m['components']['cut3r']['path'],
                 vae_config=str(Path(a.vae_directory)/'config.json'),
                 vae_weight=str(Path(a.vae_directory)/'diffusion_pytorch_model.safetensors'))
    records = {}; missing = []
    # Check every component and small input before any component body is read.
    for role, raw in paths.items():
        try:
            require(Path(raw).is_absolute(), 'Absolute component path required')
            records[role] = signature(raw)
            require(records[role]['size'] == gate.PUBLISHED[role][0], 'Incomplete component: '+role)
        except (OSError, ValueError) as exc:
            missing.append(dict(role=role, error=str(exc)))
    receipt['metadata_problems'] = missing
    require(not missing, 'One or more of the five components is missing/incomplete')
    directory = Path(records['vae_config']['path']).parent
    require(Path(records['vae_weight']['path']).parent == directory and
            {p.name for p in directory.iterdir() if p.is_file()} ==
            {'config.json', 'diffusion_pytorch_model.safetensors'}, 'Ambiguous VAE directory')
    small_expected = dict(m['source_identities'])
    small_expected[str(CHANGI)] = None
    for p in TOOL_FILES:
        small_expected[str(p)] = sha(p)
    small_records = {path:signature(path) for path in small_expected}
    require(len({r['path'] for r in records.values()}) == 5, 'Component paths alias each other')
    receipt['all_metadata_present_before_weight_read'] = True
    digests = {}
    with (out/'content_hashes.jsonl').open('x') as audit:
        for path, rec in small_records.items():
            digests[path] = hash_once(rec, small_expected[path], audit, 'source_or_input:'+path)
        for role, rec in records.items():
            digest = hash_once(rec, gate.PUBLISHED[role][1], audit, role)
            m['components'][role] = dict(path=rec['path'], size=rec['size'], sha256=digest)
    for rec in [*small_records.values(), *records.values()]:
        require(signature(rec['path']) == rec, 'Input changed before core publication')
    m['input_image'] = dict(path=str(CHANGI.resolve()), sha256=digests[str(CHANGI)],
                            scope='Fixed original changi pathname; full bytes hashed during freeze, pixels not decoded')
    m.pop('blocking_reasons', None)
    m.update(status=gate.FROZEN, evidence_kind='recorded_component_variant_loading',
             review_receipts={}, created_utc=utc())
    m['freeze_preparation'] = dict(schema='s39-content-freeze-v1',
        template_path=str(draft), template_sha256=DRAFT_SHA,
        tool_sources={str(p):digests[str(p)] for p in TOOL_FILES},
        component_signatures=records, input_image_signature=small_records[str(CHANGI)],
        resource_bodies_hashed_once_each=True, pixels_decoded=False,
        purpose='Await separately authored review receipts; this core alone cannot pass the runtime gate')
    require(sha(draft) == DRAFT_SHA, 'Draft changed before core publication')
    core_path = out/'manifest_core.json'
    write_new(core_path, m); core_path.chmod(0o444)
    receipt.update(status='CORE_FROZEN_AWAITING_REAL_REVIEWS', core_path=str(core_path),
        core_file_sha256=sha(core_path), core_sha256=gate.REF.core_sha256(m),
        components=m['components'], input_image=m['input_image'],
        component_bytes_read=sum(r['size'] for r in records.values()),
        content_hashes_sha256=sha(out/'content_hashes.jsonl'), execution_authorized=False)


def attach_reviews(a, out, gate, receipt):
    core_path, core = gate.read_manifest(a.core, a.core_sha256)
    require(core['status'] == gate.FROZEN and core['review_receipts'] == {}, 'Only an unreviewed frozen core is accepted')
    common_metadata(core, gate)
    freeze = core['freeze_preparation']
    require(freeze['schema'] == 's39-content-freeze-v1' and freeze['template_sha256'] == DRAFT_SHA,
            'Wrong freeze preparation')
    require(freeze['tool_sources'] == {str(p):sha(p) for p in TOOL_FILES}, 'Freeze tool/protocol changed')
    require(set(freeze['component_signatures']) == gate.REF.ROLES, 'Missing prepared signatures')
    for role, rec in freeze['component_signatures'].items():
        item = core['components'][role]
        require(signature(rec['path']) == rec and item['path'] == rec['path'] and
                (item['size'], item['sha256']) == gate.PUBLISHED[role] and rec['size'] == item['size'],
                'Component changed after freeze: '+role)
    require(core['input_image']['path'] == str(CHANGI.resolve()) and
            signature(core['input_image']['path']) == freeze['input_image_signature'], 'Fixed input changed')
    for filename, digest in {**core['source_identities'], core['input_image']['path']:core['input_image']['sha256']}.items():
        require(sha(filename) == digest, 'Small source/input changed: '+filename)
    m = copy.deepcopy(core)
    bindings = dict(source_review=(a.source_review, a.source_review_sha256),
                    runtime_freeze=(a.runtime_freeze, a.runtime_freeze_sha256))
    for role, (raw, expected) in bindings.items():
        p = Path(raw).resolve()
        require(gate.REF.HEX.fullmatch(expected) and sha(p) == expected, 'Actual review file SHA mismatch: '+role)
        review = json.loads(p.read_text())
        require(review.get('status') == gate.REVIEW_STATUSES[role] and review.get('variant') == gate.VARIANT and
                review.get('core_sha256') == gate.REF.core_sha256(core), 'Review does not approve this core: '+role)
        m['review_receipts'][role] = dict(path=str(p), sha256=expected)
    require(gate.REF.core_sha256(m) == gate.REF.core_sha256(core), 'Review attachment changed immutable core')
    require(sha(core_path) == a.core_sha256, 'Core changed during attachment')
    final = out/'manifest.json'
    write_new(final, m); final.chmod(0o444)
    digest = sha(final)
    metadata = gate.check_manifest(final, digest, metadata_only=True)
    write_new(out/'metadata_gate.json', metadata)
    receipt.update(status='REVIEWS_ATTACHED_METADATA_GATE_PASSED', manifest_path=str(final),
        manifest_sha256=digest, core_sha256=gate.REF.core_sha256(m),
        core_file_sha256=a.core_sha256, component_bytes_read=0,
        execution_authorized=False, worker_full_content_verification_still_required=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='mode', required=True)
    q = sub.add_parser('prepare')
    q.add_argument('--vmem', required=True); q.add_argument('--clip', required=True)
    q.add_argument('--vae-directory', required=True); q.add_argument('--out', required=True)
    q = sub.add_parser('attach-reviews')
    for name in ('core', 'core-sha256', 'source-review', 'source-review-sha256',
                 'runtime-freeze', 'runtime-freeze-sha256', 'out'):
        q.add_argument('--'+name, required=True)
    a = p.parse_args()
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=False)
    receipt = dict(schema='s39-freeze-tool-receipt-v1', started_utc=utc(), mode=a.mode,
        source_sha256=sha(__file__), status='CHECKING', execution_authorized=False,
        model_constructors=0, scientific_imports=0, pixels_decoded=0, generation_calls=0)
    try:
        gate = bind_gate()
        (prepare if a.mode == 'prepare' else attach_reviews)(a, out, gate, receipt)
    except BaseException as exc:
        receipt.update(status='NOT_READY_FREEZE_OR_REVIEW_ATTACHMENT_FAILED',
                       error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
    finally:
        receipt['completed_utc'] = utc()
        receipt['source_unchanged'] = sha(__file__) == receipt['source_sha256']
        if not receipt['source_unchanged']:
            receipt['status'] = 'FAILED_SOURCE_CHANGED'
        write_new(out/'receipt.json', receipt)
    print(json.dumps({k:receipt[k] for k in ('status','completed_utc')}, ensure_ascii=False))
    return 0 if receipt['status'] in ('CORE_FROZEN_AWAITING_REAL_REVIEWS','REVIEWS_ATTACHED_METADATA_GATE_PASSED') else 2


if __name__ == '__main__':
    sys.exit(main())
