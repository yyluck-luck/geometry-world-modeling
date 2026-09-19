"""Import already validated S26 bytes; never runs a model, GA, or GT parser.

PASS on the imported common_old receipt means IMPORT_VALIDATED only. It does
not change the original FAILED run or reconstruct its unrecorded observations.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def read(p): return json.loads(Path(p).read_text())
def require(ok, message):
    if not ok: raise RuntimeError(message)
def write(p, value):
    Path(p).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def import_previous(manifest, manifest_path, work, output):
    c=manifest['continuation']
    parent_sha=sha(manifest_path)
    require(sha(c['original_manifest_path'])==c['original_manifest_sha256'],'Original frozen parent changed')
    recovery_path=Path(c['recovery_receipt_path'])
    require(sha(recovery_path)==c['recovery_receipt_sha256'],'Recovery author receipt identity')
    r=read(recovery_path)
    require(r.get('status')=='IMPORT_VALIDATED' and r.get('passed') is True,'Independent narrow import validation required')
    require(r['old_manifest_sha256']==c['original_manifest_sha256'],'Recovery original parent identity')
    require(r['revised_clean_sha256']==c['revised_clean_sha256'],'Recovery clean reference identity')
    require(r['old_output_npz_sha256']==c['common_files']['output.npz']['sha256'],'Recovery exact original output')
    require(isinstance(r.get('historical_observations_not_recorded'),(dict,list)),
            'Historical observation omissions must remain explicit')
    require(isinstance(r.get('checks'),(dict,list)) and bool(r['checks']),'Recovery checks absent')
    require(isinstance(r.get('input_identities_before_after'),dict) and r['input_identities_before_after'],
            'Recovery complete input binding absent')
    for p,h in r['input_identities_before_after'].items():
        require(sha(p)==h,'Recovery input changed: '+p)
    require(isinstance(r.get('control_identities'),dict) and r['control_identities'],
            'Recovery validation code/seal identities absent')
    for p,h in r['control_identities'].items():
        require(sha(p)==h,'Recovery validation code/seal changed: '+p)
    for entry in c['shared_artifacts'].values():
        require(sha(entry['path'])==entry['sha256'],'Previously PASS artifact changed')
    for entry in c['common_files'].values():
        require(sha(entry['path'])==entry['sha256'],'Original common output changed')
    original_receipt=read(c['original_common_receipt_path'])
    require(original_receipt['status']=='FAILED' and original_receipt['manifest_sha256']==c['original_manifest_sha256'],
            'Keep original failure and identity')

    # All identity validation precedes writes. Copy outputs exactly; no decode.
    work=Path(work); output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    common=output/'common_old'
    require(not common.exists(),'Never replace/re-import an existing common_old')
    common.mkdir()
    for name,entry in c['shared_artifacts'].items():
        if name.endswith('_receipt.json') or name=='compatibility_receipt.json': continue
        destination=work/name
        require(not destination.exists(),'Never replace shared artifact '+name)
        shutil.copyfile(entry['path'],destination)
        require(sha(destination)==entry['sha256'],'Shared byte copy identity')
    imported_shared={}
    for name,entry in c['shared_artifacts'].items():
        if not (name.endswith('_receipt.json') or name=='compatibility_receipt.json'):continue
        old=read(entry['path'])
        require(old['status']=='PASS' and old['manifest_sha256']==c['original_manifest_sha256'],
                'Only actual prior PASS control/compat/preprocess receipts can be reused')
        new=dict(old)
        new.update(manifest_sha256=parent_sha,producer_kind='IMPORTED_PREVIOUS_PASS_ARTIFACT',
            imported_utc=datetime.now(timezone.utc).isoformat(),
            import_source_receipt=str(entry['path']),import_source_sha256=entry['sha256'],
            original_manifest_sha256=c['original_manifest_sha256'],
            evidence_scope='Previous control/preprocess/assembly PASS reused under identical inputs and bound implementation; not rerun')
        require(not (work/name).exists(),'Never replace imported receipt '+name)
        write(work/name,new);imported_shared[name]=sha(work/name)
    for name,entry in c['common_files'].items():
        shutil.copyfile(entry['path'],common/name)
        require(sha(common/name)==entry['sha256'],'Common output byte copy identity')

    camera=read(work/'control_receipt.json')
    seal=dict(manifest_sha256=parent_sha,mode='common_old',frame_count=4,sensor_depth_used=False,
        producer_kind='IMPORT_VALIDATED_SAVED_ORIGINAL_GA',
        original_failed_receipt_path=c['original_common_receipt_path'],
        original_failed_receipt_sha256=sha(c['original_common_receipt_path']),
        original_manifest_sha256=c['original_manifest_sha256'],
        recovery_receipt_path=str(recovery_path),recovery_receipt_sha256=sha(recovery_path),
        saved_heads=manifest['candidate']['archives']['common_old_depth_original4'],
        control_c2w_sha256=camera['output_sha256'],
        compatibility_receipt_sha256=sha(work/'compatibility_receipt.json'))
    write(common/'inputs_seal.json',seal)
    receipt=dict(status='PASS',validation_status='IMPORT_VALIDATED',mode='common_old',frame_count=4,
        producer_kind='IMPORT_VALIDATED_SAVED_ORIGINAL_GA',manifest_sha256=parent_sha,
        completed_utc=datetime.now(timezone.utc).isoformat(),sensor_depth_used=False,
        model_forwards=0,new_GA_runs=0,new_optimizer_steps=0,
        historical_GA_steps=400,historical_step_evidence='Frozen original runner checks before recorded exception plus exact 400-row trace; see recovery receipt',
        evidence_scope='Saved-output import only. Original S26 remains FAILED; no missing historical observations are fabricated.',
        inputs_seal_sha256=sha(common/'inputs_seal.json'),
        outputs={name:sha(common/name) for name in c['common_files']},
        depth_tensor_sha256=r['depth_tensor_sha256'],
        control_pose_prefix_tensor_sha256=r['control_pose_prefix_tensor_sha256'],
        recovery_receipt_sha256=sha(recovery_path),recovery_checks=r['checks'],
        historical_observations_not_recorded=r['historical_observations_not_recorded'])
    # Recheck original bytes after copying. This worker never edits old paths.
    for p,h in r['input_identities_before_after'].items():require(sha(p)==h,'Original source changed during import')
    for p,h in r['control_identities'].items():require(sha(p)==h,'Recovery controls changed during import')
    write(common/'receipt.json',receipt)
    write(work/'import_receipt.json',dict(status='PASS',completed_utc=datetime.now(timezone.utc).isoformat(),
        manifest_sha256=parent_sha,common_import_receipt_sha256=sha(common/'receipt.json'),
        shared_receipts=imported_shared,recovery_receipt_sha256=sha(recovery_path),
        original_S26_status='FAILED_UNCHANGED',array_decodes=0,GT_reads=0,new_GA_runs=0,new_model_forwards=0))
