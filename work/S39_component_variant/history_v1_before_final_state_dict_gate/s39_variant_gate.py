"""Explicit ft-mse component-variant gate; never grants S35 original identity.

Standard-library only. Full checking is separate from cheap metadata inspection.
No downloader, model constructor, or original-provenance override is present.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S35 = ROOT / 'work/S35_generation_integration'
REFERENCE_SHA = 'c949f85573b8fa23db59c8782354608cb6ca1334ea782712fcd9c334337df759'
FACTORY_SHA = 'a7f812717c053b401433bac423ba0a63028a9dc1874b1cba3c4fbca6c276e3d0'
LAUNCHER_SHA = '8744cb8959cded2394c1471c660dd84f929b5ae24ac97e81379304aed0be702e'


def sha(path):
    import hashlib
    with Path(path).open('rb') as h:
        return hashlib.file_digest(h, 'sha256').hexdigest()


def load_reference():
    path = S35 / 'resource_gate.py'
    if sha(path) != REFERENCE_SHA:
        raise RuntimeError('Pinned S35 helper source changed')
    spec = importlib.util.spec_from_file_location('_s39_s35_gate_helpers', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REF = load_reference()  # Only the bound standard-library module, not its main.
require, NotReady = REF.require, REF.NotReady
VARIANT = dict(
    name='VMem + stabilityai/sd-vae-ft-mse (declared VAE component variant)',
    repo='stabilityai/sd-vae-ft-mse', revision='31f26fdeee1355a5c34592e401dd41e45d25a493',
    subfolder='', original_sd21_vae_identity='UNKNOWN', exact_original_baseline=False)
PUBLISHED = dict(REF.PUBLISHED,
    vae_config=(547, '92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e'),
    vae_weight=(334643276, 'a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815'))
RUNTIME = dict(REF.RUNTIME, pythonpath=[str(HERE)] + REF.RUNTIME['pythonpath'])
LIMITS = dict(seconds=1800, rss_bytes=45*1024**3, threads=8,
              minimum_free_bytes=10*1024**3, poll_seconds=0.5)
SCHEMA = 's39-declared-vae-variant-loading-v1'
FROZEN = 'FROZEN_COMPONENT_VARIANT_LOADING_ONLY'
REVIEW_STATUSES = dict(source_review='PASS_S39_SOURCE_REVIEW',
                      runtime_freeze='READY_TO_ATTEMPT_DECLARED_VARIANT_LOADING')


def required_sources():
    require(sha(S35/'runtime_factory.py') == FACTORY_SHA, 'Pinned S35 factory changed')
    require(sha(S35/'launch_original.py') == LAUNCHER_SHA, 'Pinned S35 launcher helper changed')
    sources = REF.required_sources()
    extra = [HERE/'s39_variant_gate.py', HERE/'load_components.py', HERE/'PROTOCOL_DRAFT.md',
             ROOT/'work/S38_original_resources/vae_provenance/report.md',
             ROOT/'work/S36_resource_recovery/vae_relation_review.md']
    base = ROOT/'work/S20_environment/site-packages/diffusers'
    extra += [base/'models/autoencoders/autoencoder_kl.py',
              base/'configuration_utils.py', base/'models/modeling_utils.py']
    for path in extra:
        require(path.is_file(), 'Required bound source missing: '+str(path))
        sources[str(path)] = sha(path)
    return sources


def read_manifest(path, expected):
    path = Path(path).resolve()
    require(isinstance(expected, str) and REF.HEX.fullmatch(expected), 'Frozen manifest SHA required')
    require(path.is_file() and sha(path) == expected, 'Manifest missing or changed')
    m = json.loads(path.read_text())
    require(m.get('schema') == SCHEMA and m.get('variant') == VARIANT,
            'Explicit named component variant is required; never original identity')
    return path, m


def check_manifest(path, expected, *, metadata_only=False):
    path, m = read_manifest(path, expected)
    require(m.get('status') == FROZEN, 'Draft is not authorization to load')
    require(m.get('controls') == REF.CONTROLS and m.get('loading_limits') == LIMITS,
            'Inherited scientific settings or bounded loading budget changed')
    require(m.get('runtime') == RUNTIME, 'Wrong virtualenv or import order')
    require(isinstance(m.get('output_root'), str) and Path(m['output_root']).is_absolute(),
            'Fresh absolute variant output root required')
    components = m.get('components', {})
    require(set(components) == REF.ROLES, 'All five component files required')
    records = {}
    # Finish all metadata checks before any large component content read.
    for role in sorted(REF.ROLES):
        item = components[role]
        require(isinstance(item, dict) and (item.get('size'), item.get('sha256')) == PUBLISHED[role],
                'Wrong published component identity: '+role)
        raw = item.get('path')
        require(isinstance(raw, str) and Path(raw).is_absolute(), 'Missing absolute local component: '+role)
        p = Path(raw)
        require(p.is_file() and p.stat().st_size == item['size'], 'Missing/incomplete component: '+role)
        records[role] = dict(REF.stat_record(p), sha256=item['sha256'])
    vc, vw = components['vae_config'], components['vae_weight']
    directory = Path(vc['path']).resolve().parent
    require(Path(vc['path']).name == 'config.json' and
            Path(vw['path']).name == 'diffusion_pytorch_model.safetensors' and
            Path(vw['path']).resolve().parent == directory, 'One exact official VAE directory required')
    require({p.name for p in directory.iterdir() if p.is_file()} ==
            {'config.json', 'diffusion_pytorch_model.safetensors'}, 'Ambiguous alternate VAE files')
    source_ids = m.get('source_identities', {})
    require(source_ids == required_sources(), 'Exact inherited and variant source domain required')
    evidence = m.get('review_receipts', {})
    require(set(evidence) == set(REVIEW_STATUSES), 'Two real reviews of this variant core required')
    small = dict(source_ids)
    for entry in evidence.values():
        require(isinstance(entry, dict) and set(entry) == {'path', 'sha256'}, 'Invalid review record')
        small[entry['path']] = entry['sha256']
    for key in ('config', 'input_image'):
        item = m.get(key, {})
        require(isinstance(item.get('path'), str) and Path(item['path']).is_absolute(), 'Missing '+key)
        small[item['path']] = item.get('sha256')
    require(m['config']['sha256'] == REF.ORIGINAL_CONFIG_SHA, 'Original inference YAML must remain fixed')
    for filename, digest in small.items():
        require(Path(filename).is_absolute() and Path(filename).is_file(), 'Missing source/input/review '+str(filename))
        require(isinstance(digest, str) and REF.HEX.fullmatch(digest), 'Missing source/input/review SHA')
    # Review approval is checked before expensive content hashes, also in metadata mode.
    core = REF.core_sha256(m)
    for name, status in REVIEW_STATUSES.items():
        entry = evidence[name]
        require(sha(entry['path']) == entry['sha256'], 'Review SHA changed')
        review = json.loads(Path(entry['path']).read_text())
        require(review.get('status') == status and review.get('core_sha256') == core and
                review.get('variant') == VARIANT, 'Review did not approve this declared variant core')
    if metadata_only:
        return dict(schema='s39-variant-metadata-v1', status='PASS_METADATA_ONLY', variant=VARIANT,
                    manifest_path=str(path), manifest_sha256=expected, execution_authorized=False,
                    weight_bytes_read=0, image_bytes_read=0,
                    scope='Paths/sizes/published identities, current source domain and review bindings only; full content verification still required')
    for filename, digest in small.items():
        require(sha(filename) == digest, 'Frozen source/input/review changed: '+filename)
    for role, record in records.items():
        require(sha(record['path']) == record['sha256'] and REF.same_stat(record),
                'Component content mismatch or changed during SHA: '+role)
    return dict(schema='s39-variant-resource-gate-v1', status='PASS_DECLARED_VARIANT_RESOURCE_GATE',
                variant=VARIANT, manifest_path=str(path), manifest_sha256=expected,
                controls=REF.CONTROLS, components=records, source_identities=source_ids,
                evidence_kind='recorded_component_variant_loading', verified_utc=datetime.now(timezone.utc).isoformat(),
                scope='Exact declared ft-mse identities; original SD2.1 VAE remains UNKNOWN')


def validate_gate(gate):
    require(isinstance(gate, dict) and gate.get('schema') == 's39-variant-resource-gate-v1' and
            gate.get('status') == 'PASS_DECLARED_VARIANT_RESOURCE_GATE' and
            gate.get('variant') == VARIANT, 'A completed declared-variant full gate is required')
    _, m = read_manifest(gate['manifest_path'], gate['manifest_sha256'])
    require(m.get('status') == FROZEN and m['controls'] == gate['controls'] == REF.CONTROLS and
            m['runtime'] == RUNTIME and m['loading_limits'] == LIMITS, 'Gate core changed')
    require(set(gate['components']) == REF.ROLES, 'Incomplete resource gate')
    for role, record in gate['components'].items():
        item = m['components'][role]
        require(record['path'] == str(Path(item['path']).resolve()) and
                (record['size'], record['sha256']) == (item['size'], item['sha256']) == PUBLISHED[role]
                and REF.same_stat(record), 'Verified component changed: '+role)
    require(gate['source_identities'] == m['source_identities'] == required_sources(), 'Source domain changed')
    for filename, digest in gate['source_identities'].items():
        require(sha(filename) == digest, 'Source changed before/after loading: '+filename)
    for key in ('config', 'input_image'):
        require(sha(m[key]['path']) == m[key]['sha256'], 'Small frozen runtime input changed: '+key)
    return gate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', required=True); p.add_argument('--manifest-sha256', required=True)
    p.add_argument('--receipt', required=True); p.add_argument('--metadata-only', action='store_true')
    a = p.parse_args(); out = Path(a.receipt)
    require(not out.exists(), 'Never overwrite a prior check')
    try:
        result = check_manifest(a.manifest, a.manifest_sha256, metadata_only=a.metadata_only)
    except (NotReady, OSError, ValueError, KeyError, TypeError) as exc:
        result = dict(status='NOT_READY_BEFORE_SCIENTIFIC_IMPORT', variant=VARIANT,
                      error=str(exc), checked_utc=datetime.now(timezone.utc).isoformat(),
                      model_constructors=0, scientific_execution=False)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x') as h:
        json.dump(result, h, ensure_ascii=False, indent=2); h.write('\n')
    print(result['status'])
    return 0 if result['status'] in ('PASS_METADATA_ONLY', 'PASS_DECLARED_VARIANT_RESOURCE_GATE') else 2


if __name__ == '__main__':
    sys.exit(main())
