"""S40 declared-variant generation gate; never authorizes a draft or invents S39 evidence."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S39 = ROOT/'work/S39_component_variant'
PINS = {'s39_variant_gate.py':'cf667bdc0bc43f902d0dca3041c4dbf33a53d908ee4e5d13ebfba2f853a78f4e',
        'load_components.py':'7b554276d5f00e6f14283a0c3a3d06bccda73b3c9dd2b6a9ef2514287732738e'}
SCHEMA = 's40-declared-variant-two-batch-v1'
FROZEN = 'FROZEN_DECLARED_VARIANT_TWO_BATCH_EXECUTION'
SOURCES = ('generation_gate.py','runtime_adapter.py','launch_generation.py','PROTOCOL_DRAFT.md')
REVIEW_STATUSES = {'source_review':'PASS_S40_GENERATION_SOURCE_REVIEW',
                   'runtime_freeze':'READY_TO_ATTEMPT_S40_DECLARED_GENERATION'}
LIMITS = dict(seconds_per_batch=1800,total_seconds=3600,rss_bytes=45*1024**3,
              minimum_free_bytes=10*1024**3,threads=8,poll_seconds=0.5)


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    with Path(path).open('rb') as h:
        return hashlib.file_digest(h,'sha256').hexdigest()


def bind_s39():
    for name, expected in PINS.items():
        require(sha(S39/name) == expected, 'Reviewed S39 source changed: '+name)
    path = S39/'s39_variant_gate.py'
    spec = importlib.util.spec_from_file_location('_s40_s39_gate',path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S39_GATE = bind_s39()  # Bound standard-library modules only.
VARIANT = S39_GATE.VARIANT
RUNTIME = S39_GATE.REF.RUNTIME  # Unchanged S35 parent import paths.


def core_sha256(m):
    return S39_GATE.REF.core_sha256(m)


def read_json_record(entry):
    require(isinstance(entry,dict) and set(entry)=={'path','sha256'}, 'Actual path/SHA record required')
    raw, expected = entry['path'], entry['sha256']
    require(isinstance(raw,str) and Path(raw).is_absolute() and
            isinstance(expected,str) and S39_GATE.REF.HEX.fullmatch(expected), 'Missing actual evidence identity')
    require(Path(raw).is_file() and sha(raw)==expected, 'Evidence missing or changed: '+raw)
    return json.loads(Path(raw).read_text())


def required_sources():
    ids = S39_GATE.required_sources()
    for name in SOURCES:
        p = HERE/name
        require(p.is_file(),'Missing prepared S40 source: '+name)
        ids[str(p)] = sha(p)
    return ids


def read_frozen(path, expected):
    require(isinstance(expected,str) and S39_GATE.REF.HEX.fullmatch(expected),'Frozen S40 SHA required')
    p = Path(path).resolve()
    require(p.is_file() and sha(p)==expected,'S40 manifest missing/changed')
    m = json.loads(p.read_text())
    require(m.get('schema')==SCHEMA and m.get('status')==FROZEN and m.get('variant')==VARIANT,
            'A separately frozen declared-variant generation manifest is required')
    require(m['controls']==S39_GATE.REF.CONTROLS and m['runtime']==RUNTIME and m['generation_limits']==LIMITS,
            'Original generation controls/runtime/budgets changed')
    require(m['source_identities']==required_sources(),'Exact inherited and S40 source domain required')
    require(Path(m['output_root']).is_absolute(),'Dedicated absolute S40 output required')
    return m


def loading_chain(m):
    """Validate actual prior loading evidence; not a claim of codec/video quality."""
    parent = read_json_record(m['s39_loading_manifest'])
    binding = m['s39_loading_manifest']
    S39_GATE.check_manifest(binding['path'],binding['sha256'],metadata_only=True)
    require(m['s39_resource_core_sha256']==core_sha256(parent),'S39 resource core identity differs')
    require(parent['components']==m['components'] and parent['config']==m['config'] and
            parent['input_image']==m['input_image'],'Generation changed the actually loaded resources/input')
    require(parent['source_identities']==S39_GATE.required_sources(),'S39 resource/source identity changed')
    ev = m['s39_loading_evidence']
    require(set(ev)=={'launch','worker','runtime_loading','full_resource_gate'},'Four actual loading records required')
    r = {name:read_json_record(entry) for name,entry in ev.items()}
    launch,worker,loading,full = (r[n] for n in ('launch','worker','runtime_loading','full_resource_gate'))
    pending = 'VARIANT_LOADING_RETURNED_PENDING_INDEPENDENT_REVIEW'
    for record in (launch,worker):
        require(record['status']==pending and record['manifest_sha256']==binding['sha256'] and
                record['source_sha256']==PINS['load_components.py'] and record['variant']==VARIANT and
                record['source_unchanged_at_close'] is True,'S39 loading did not return with exact source/manifest')
    require(launch['worker_spawned'] is True and launch['returncode']==0 and
            not any(k in launch for k in ('limit_exceeded','unexpected_live_descendants')) and
            launch['worker_receipt_sha256']==ev['worker']['sha256'] and launch['worker_status']==pending,
            'S39 loading external completion failed')
    require(worker['runtime_factory_calls']==1 and worker['runtime_loading_sha256']==ev['runtime_loading']['sha256'] and
            worker['generation_calls']==0 and worker['encode_decode_calls_requested']==0,'Wrong S39 loading scope/binding')
    require(loading['status']=='PASS_DECLARED_VARIANT_COMPONENT_LOADING_ONLY' and
            loading['manifest_sha256']==binding['sha256'] and loading['variant']==VARIANT and
            loading['variant_invariants']==worker['variant_invariants'] and loading['network_attempts']==0 and
            loading['generation_completed'] is False,'Returned S39 component invariants differ')
    loads = loading['state_dict_loads']
    require(isinstance(loads,list) and loads and loads==worker['state_dict_loads'] and
            all(isinstance(x,dict) and x.get('missing_keys')==[] and x.get('unexpected_keys')==[] and
                'strict_requested' in x for x in loads),'Incomplete actual loading records')
    require(all(not loading['vae_loading_info'].get(k) for k in
                ('missing_keys','unexpected_keys','mismatched_keys','error_msgs')),'S39 VAE loading information failed')
    require(full['manifest_sha256']==binding['sha256'] and
            full['manifest_path']==str(Path(binding['path']).resolve()),'S39 full gate is from another run')
    S39_GATE.validate_gate(full)  # Prior content identity + current stat/small source checks, not GB rehash.
    review = read_json_record(m['s39_loading_review'])
    require(review.get('status')=='PASS_S39_LOADING_EVIDENCE_REVIEW' and review.get('variant')==VARIANT and
            review.get('loading_manifest_sha256')==binding['sha256'] and
            review.get('resource_core_sha256')==m['s39_resource_core_sha256'] and
            review.get('evidence_sha256')=={k:v['sha256'] for k,v in ev.items()},
            'Actual different-author S39 loading evidence review is absent/unbound')
    return parent


def check_manifest(path, expected, *, metadata_only=False):
    m = read_frozen(path,expected)
    # Every actual prerequisite and review is required before new large content reads.
    loading_chain(m)
    require(set(m['review_receipts'])==set(REVIEW_STATUSES),'Two actual S40 core reviews required')
    for name,status in REVIEW_STATUSES.items():
        review = read_json_record(m['review_receipts'][name])
        require(review.get('status')==status and review.get('variant')==VARIANT and
                review.get('core_sha256')==core_sha256(m),'S40 core review is absent/unbound')
    for filename,digest in m['source_identities'].items():
        require(sha(filename)==digest,'Changed generation source: '+filename)
    if metadata_only:
        return dict(schema='s40-generation-metadata-v1',status='PASS_METADATA_ONLY',variant=VARIANT,
                    manifest_sha256=expected,execution_authorized=False,
                    scope='Actual prior loading chain and S40 reviews; new worker full content verification remains')
    binding = m['s39_loading_manifest']
    full = S39_GATE.check_manifest(binding['path'],binding['sha256'])  # One new complete five-component hash.
    return dict(schema='s40-generation-resource-gate-v1',status='PASS_DECLARED_GENERATION_RESOURCE_GATE',
        manifest_path=str(Path(path).resolve()),manifest_sha256=expected,variant=VARIANT,
        components=full['components'],controls=m['controls'],source_identities=m['source_identities'],
        s39_full_gate=full,evidence_kind='recorded_execution',verified_utc=datetime.now(timezone.utc).isoformat(),
        identity_scope='Declared official-ft-mse variant; not exact original SD2.1 baseline')


def validate_gate(gate):
    require(isinstance(gate,dict) and gate.get('schema')=='s40-generation-resource-gate-v1' and
            gate.get('status')=='PASS_DECLARED_GENERATION_RESOURCE_GATE' and gate.get('variant')==VARIANT,
            'A completed S40 full gate is required')
    m = read_frozen(gate['manifest_path'],gate['manifest_sha256'])
    require(gate['controls']==m['controls'] and gate['source_identities']==m['source_identities'] and
            gate['components']==gate['s39_full_gate']['components'],'S40 gate data changed')
    S39_GATE.validate_gate(gate['s39_full_gate'])
    require(gate['s39_full_gate']['manifest_sha256']==m['s39_loading_manifest']['sha256'],
            'S40 gate has another resource parent')
    # Rebind all small approvals, prior actual records and current source bytes.
    check_manifest(gate['manifest_path'],gate['manifest_sha256'],metadata_only=True)
    return gate
