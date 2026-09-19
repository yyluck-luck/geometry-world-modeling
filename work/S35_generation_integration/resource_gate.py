"""Standard-library preflight; missing resources stop before scientific imports.

This verifies a separately frozen, reviewed real-run manifest. It does not
download, authorize account access, instantiate a model, or establish quality.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROLES = {'vmem', 'vae_config', 'vae_weight', 'clip', 'cut3r'}
PUBLISHED = {
    'vmem': (5056346672, '675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4'),
    'clip': (3944517836, '0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5'),
    'cut3r': (3173761006, '45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103'),
}
CONTROLS = dict(device='cpu', dtype='float32', threads=8, seed=42,
                height=576, width=576, num_frames=8, context_num_frames=4,
                target_num_frames=4, inference_num_steps=50,
                use_non_maximum_suppression=True, operations=['turn_left(5)', 'turn_right(5)'],
                seconds_per_batch=1800, rss_bytes=45*1024**3)
HEX = re.compile(r'^[0-9a-f]{64}$')
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'work/S20_environment/isolated_vmem_source'
S20_MANIFEST=ROOT/'work/S20_environment/source_manifest.json'
S20_MANIFEST_SHA='66f913d7a7be7890447ea01e766c4bef10e2818fcafd7a8141d2e01d7bdbe841'
S20_TRACE_SHA='daf841dbcb635417865ba8287ad305bbdf6105181fd39e169be2e666e1bfbc57'
ORIGINAL_CONFIG_SHA='8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3'
RUNTIME=dict(python_executable=str(ROOT/'.venv-cut3r/bin/python'),
             pythonpath=[str(HERE),str(ROOT/'src'),str(ROOT/'work/S20_environment/site-packages'),str(ROOT/'work/S17C_environment/site-packages')])


class NotReady(RuntimeError):
    pass


def require(value, message):
    if not value:
        raise NotReady(message)


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def stat_record(path):
    path = Path(path)
    s = path.stat()
    return dict(path=str(path.resolve()), size=s.st_size, mtime_ns=s.st_mtime_ns,
                device=s.st_dev, inode=s.st_ino)


def same_stat(record):
    try:
        current = stat_record(record['path'])
    except (KeyError, OSError, TypeError):
        return False
    return all(current[k] == record[k] for k in current)


def core_sha256(manifest):
    """Review bindings exclude review receipts themselves, avoiding a hash cycle."""
    core={k:v for k,v in manifest.items() if k!='review_receipts'}
    return hashlib.sha256(json.dumps(core,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def required_sources():
    require(sha(S20_MANIFEST)==S20_MANIFEST_SHA, 'Inherited S20 source manifest changed')
    old=json.loads(S20_MANIFEST.read_text())
    result={str(SOURCE/x['path']):x['final_sha256'] for x in old['source_files']}
    result[str(S20_MANIFEST)]=S20_MANIFEST_SHA
    result[str(ROOT/'src/s20_generation_trace.py')]=S20_TRACE_SHA
    for name in ['resource_gate.py','runtime_factory.py','integrate_original.py','archive_outputs.py','launch_original.py']:
        p=HERE/name
        require(p.is_file(), 'Runtime source not yet implemented: '+name)
        result[str(p)]=sha(p)
    return result


def check_manifest(path, expected_sha256, *, metadata_only=False):
    """Check *all* metadata/files before hashing any GB-scale resource."""
    path = Path(path).resolve()
    require(HEX.fullmatch(expected_sha256 or ''), 'A separately frozen manifest SHA is required')
    require(path.is_file() and sha(path) == expected_sha256, 'Manifest missing or changed')
    m = json.loads(path.read_text())
    require(m.get('schema') == 's35-original-generation-run-v1', 'Wrong manifest schema')
    require(m.get('status') == 'FROZEN_REAL_EXECUTION', 'Draft preparation cannot execute')
    require(m.get('controls') == CONTROLS, 'Only the reviewed S20 CPU two-batch controls are accepted')
    require(m.get('runtime') == RUNTIME, 'Fixed scientific Python and import paths are required')
    require(isinstance(m.get('output_root'),str) and Path(m['output_root']).is_absolute(), 'Dedicated absolute output root is required')
    components = m.get('components', {})
    require(set(components) == ROLES, 'All five original component files are required')
    records = {}
    for role in sorted(ROLES):
        item = components[role]
        require(isinstance(item, dict), 'Missing component metadata: '+role)
        raw_path = item.get('path')
        require(isinstance(raw_path, str) and Path(raw_path).is_absolute(), 'Absolute local component path required: '+role)
        p = Path(raw_path)
        require(p.is_file(), 'Original component file unavailable: '+role)
        require(type(item.get('size')) is int and item['size'] > 0, 'Positive component size required: '+role)
        require(isinstance(item.get('sha256'), str) and HEX.fullmatch(item['sha256']), 'Full component identity required: '+role)
        require(p.stat().st_size == item['size'], 'Component size mismatch: '+role)
        if role in PUBLISHED:
            require((item['size'],item['sha256']) == PUBLISHED[role], 'Wrong original component identity: '+role)
        records[role] = {**stat_record(p), 'sha256':item['sha256']}
    vc, vw = components['vae_config'], components['vae_weight']
    require(Path(vc['path']).name == 'config.json', 'Exact VAE config is required')
    require(Path(vw['path']).name in ('diffusion_pytorch_model.safetensors','diffusion_pytorch_model.bin'), 'Unsupported original VAE filename')
    require(Path(vc['path']).resolve().parent == Path(vw['path']).resolve().parent, 'VAE config and parameter files must share a local directory')
    require(set(x.name for x in Path(vc['path']).resolve().parent.iterdir() if x.is_file()) == {Path(vc['path']).name,Path(vw['path']).name}, 'Use a dedicated two-file VAE directory to avoid implicit alternate weights')
    provenance = m.get('vae_provenance', {})
    require(provenance.get('repo') == 'stabilityai/stable-diffusion-2-1-base' and provenance.get('subfolder') == 'vae', 'Original VAE provenance is required')
    require(isinstance(provenance.get('revision'), str) and re.fullmatch(r'[0-9a-f]{40}', provenance['revision']), 'Actual original VAE revision is still required')
    source_ids = m.get('source_identities', {})
    require(isinstance(source_ids, dict) and source_ids==required_sources(), 'Exact inherited and new runtime source domain is required')
    evidence = m.get('review_receipts', {})
    require(set(evidence) == {'source_review','vae_provenance_review','runtime_freeze'}, 'Three separately reviewed preparation receipts are required')
    small = dict(source_ids)
    for entry in evidence.values():
        require(isinstance(entry,dict) and set(entry)=={'path','sha256'}, 'Review receipt must have a path and SHA')
        small[entry['path']] = entry['sha256']
    for name,key in (('input_image','sha256'),('config','sha256')):
        item=m.get(name,{})
        require(isinstance(item.get('path'),str) and Path(item['path']).is_absolute(), 'Frozen local '+name+' required')
        small[item['path']]=item.get(key)
    require(m['config']['sha256']==ORIGINAL_CONFIG_SHA, 'Complete original inference YAML identity is required')
    for name,expected in small.items():
        require(Path(name).is_absolute() and Path(name).is_file(), 'Frozen source/input/review file missing: '+str(name))
        require(isinstance(expected,str) and HEX.fullmatch(expected), 'Complete source/input/review identity required')
    if metadata_only:
        return dict(schema='s35-metadata-precheck-v1',status='PASS_METADATA_ONLY',
                    manifest_path=str(path),manifest_sha256=expected_sha256,
                    controls=CONTROLS,runtime=RUNTIME,output_root=m['output_root'],
                    components=records,weight_bytes_read=0,image_bytes_read=0,
                    execution_authorized=False,
                    limits='Source names/current small source hashes and all required file metadata checked; review payload identities and component content still require worker full check.')
    for name,expected in small.items():
        require(sha(name)==expected, 'Frozen source/input/review changed: '+name)
    core=core_sha256(m)
    for name,status in [('source_review','PASS_S35_SOURCE_REVIEW'),('runtime_freeze','READY_TO_ATTEMPT_REAL_LOADING')]:
        review=json.loads(Path(evidence[name]['path']).read_text())
        require(review.get('status')==status and review.get('core_sha256')==core,
                'Review did not approve this exact source/control/input core: '+name)
    review=json.loads(Path(evidence['vae_provenance_review']['path']).read_text())
    require(review.get('status')=='VERIFIED_ORIGINAL_VAE_IDENTITY' and review.get('vae_provenance')==provenance
            and review.get('components')=={'vae_config':vc,'vae_weight':vw}, 'VAE review does not bind the actual original config and parameters')
    for role,record in records.items():
        require(sha(record['path'])==record['sha256'], 'Full component SHA mismatch: '+role)
        require(same_stat(record), 'Component changed while verifying: '+role)
    return dict(schema='s35-resource-gate-v1', status='PASS_RESOURCE_GATE',
                evidence_kind='recorded_execution', manifest_path=str(path),
                manifest_sha256=expected_sha256, components=records,
                source_identities=source_ids, verified_utc=datetime.now(timezone.utc).isoformat(),
                controls=CONTROLS, model_constructors=0, network_requests=0)


def validate_gate(gate):
    """Rebind the just-created gate before constructing the first model.

    SHA verification belongs to check_manifest; this cheap immediate recheck
    prevents accidental stale paths without reading the same GB files twice.
    It is a trusted-project guard, not an adversarial filesystem sandbox.
    """
    require(isinstance(gate,dict) and gate.get('schema')=='s35-resource-gate-v1' and gate.get('status')=='PASS_RESOURCE_GATE', 'Successful real resource gate required')
    require(gate.get('evidence_kind')=='recorded_execution' and gate.get('controls')==CONTROLS, 'Real CPU controls required')
    require(sha(gate['manifest_path'])==gate['manifest_sha256'], 'Frozen manifest changed after preflight')
    manifest=json.loads(Path(gate['manifest_path']).read_text())
    require(manifest.get('schema')=='s35-original-generation-run-v1' and manifest.get('status')=='FROZEN_REAL_EXECUTION'
            and manifest.get('controls')==gate['controls'] and manifest.get('runtime')==RUNTIME, 'Gate differs from frozen manifest')
    require(set(gate['components'])==ROLES, 'Incomplete resource gate')
    for role,record in gate['components'].items():
        item=manifest['components'][role]
        require(record['path']==str(Path(item['path']).resolve()) and record['size']==item['size'] and record['sha256']==item['sha256'], 'Gate component differs from frozen manifest: '+role)
        require(same_stat(record), 'Verified file changed before model loading: '+role)
    require(gate['source_identities']==manifest['source_identities']==required_sources(), 'Gate source domain differs from frozen manifest')
    for path,expected in gate['source_identities'].items():
        require(sha(path)==expected, 'Source changed before model loading: '+path)
    return gate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True)
    parser.add_argument('--manifest-sha256',required=True)
    parser.add_argument('--receipt',required=True)
    args=parser.parse_args()
    out=Path(args.receipt)
    require(not out.exists(), 'Never overwrite a readiness receipt')
    try:
        result=check_manifest(args.manifest,args.manifest_sha256)
    except (NotReady, OSError, ValueError, KeyError, TypeError) as exc:
        result=dict(status='NOT_READY_BEFORE_MODEL_IMPORT', error=str(exc),
                    checked_utc=datetime.now(timezone.utc).isoformat(),
                    model_constructors=0, network_requests=0,
                    scientific_imports=0, scientific_execution=False)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as handle:
        json.dump(result,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print(result['status'])
    return 0 if result['status']=='PASS_RESOURCE_GATE' else 2


if __name__=='__main__':
    raise SystemExit(main())
