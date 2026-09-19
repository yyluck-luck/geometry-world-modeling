"""Record source identity checks only; no scientific data or numeric imports."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
VMEM = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem')
HERE = ROOT / 'work/S27_scale_diagnosis_source'
COMMIT = '39291e4f272f6b4f270691d930926ab5930f942e'
EMBEDDED = ROOT / 'work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    rels = ['modeling/pipeline.py', 'navigation.py', 'app.py',
            'configs/inference/inference.yaml', 'utils/util.py',
            'extern/CUT3R/surfel_inference.py',
            'extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py',
            'extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py',
            'extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py',
            'extern/CUT3R/cloud_opt/commons.py',
            'extern/CUT3R/src/dust3r/utils/geometry.py']
    sources = {}
    for rel in rels:
        path = VMEM / rel
        committed = subprocess.check_output(['git', 'show', COMMIT + ':' + rel], cwd=VMEM)
        data = path.read_bytes()
        assert data == committed, rel
        record = dict(sha256=sha(path), line_count=len(data.splitlines()),
                      byte_equal_to_pinned_commit=True)
        if rel.startswith('extern/CUT3R/'):
            actual = EMBEDDED / rel.removeprefix('extern/CUT3R/')
            assert actual.read_bytes() == data, rel
            record.update(execution_source=str(actual),
                          execution_source_sha256=sha(actual),
                          execution_source_byte_equal=True)
        sources[str(path)] = record
    project = [ROOT / 'scripts/s26_consumer_baseline.py',
               ROOT / 'scripts/s26b_consumer_baseline.py',
               ROOT / 'work/S26_consumer_baseline_preparation/saved_heads_adapter.py',
               ROOT / 'work/S26B_execution_attempt2_preparation/continue.py',
               ROOT / 'work/S26B_execution_attempt2_preparation/contract.json',
               ROOT / 'work/S26_consumer_baseline_preparation/source_binding.json',
               HERE / 'audit.md', Path(__file__)]
    report = dict(status='SOURCE_AUDIT_COMPLETE', recorded_utc=datetime.now(timezone.utc).isoformat(),
                  pinned_vmem_commit=COMMIT, sources=sources,
                  project_source_identities={str(p):sha(p) for p in project},
                  new_model_forwards=0, new_GA_steps=0, new_PnP_solves=0,
                  new_backward_calls=0, prediction_arrays_read=0,
                  GT_arrays_or_camera_coordinates_read=0, main_ledger_modified=False,
                  findings=['Registered depth flags do not establish gradient connectivity: original ParameterStack detaches the stack and may create an unregistered leaf.',
                            'MST uses similarity scale alignment; its depth snapshot was not historically saved.',
                            'Metric pose input disables scale normalization but leaves pairwise scale trainable.',
                            'Generation-only camera centering/scaling is not applied to the original GA input.',
                            'Objective homogeneity is a source-level reparameterization, not a claim about actual Adam depth updates.'],
                  limitation='No current large-error cause is assigned. Runtime microchecks and the prepared S27M saved-input diagnostic are separate evidence.',
                  search_limitations='Some early source lookups used the wrong source root and were immediately corrected; an overbroad JSON text search showed package metadata and was replaced by selected-key JSON reads. No data arrays were accessed.')
    (HERE / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status=report['status'], source_files=len(sources),
                          report_sha256=sha(HERE/'audit.md'),
                          receipt_sha256=sha(HERE/'receipt.json')), indent=2))


if __name__ == '__main__':
    main()
