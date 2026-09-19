"""Source-only identities and AST contract for the S26 commit-consistency audit."""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
REPO=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem')
COMMIT='39291e4f272f6b4f270691d930926ab5930f942e'
FILES=('modeling/pipeline.py','extern/CUT3R/surfel_inference.py',
       'extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py',
       'extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py',
       'extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py',
       'configs/inference/inference.yaml','utils/util.py')

def sha(data):return hashlib.sha256(data).hexdigest()
def fndef(tree,name):
    found=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(found)==1,name
    return found[0]

def main():
    ids={}
    for relative in FILES:
        p=REPO/relative
        live=p.read_bytes()
        pinned=subprocess.check_output(['git','show',f'{COMMIT}:{relative}'],cwd=REPO)
        assert live==pinned,relative
        ids[str(p)]={'sha256':sha(live),'matches_pinned_commit':True}
    pipeline=ast.parse((REPO/'modeling/pipeline.py').read_text())
    construct=fndef(pipeline,'construct_and_store_scene')
    wrapper=ast.parse((REPO/'extern/CUT3R/surfel_inference.py').read_text())
    prepare=fndef(wrapper,'prepare_output')
    attrs=lambda tree,name:[n for n in ast.walk(tree) if isinstance(n,ast.Attribute) and n.attr==name]
    focal_lines=sorted(n.lineno for n in attrs(pipeline,'surfel_Ks'))
    assert focal_lines==[122,141,637,995],focal_lines
    focal_writes=[n for n in attrs(construct,'surfel_Ks') if n.lineno==995]
    assert len(focal_writes)==1
    assert not attrs(prepare,'preset_focal')
    assert [n.lineno for n in attrs(prepare,'preset_depth')]==[187]
    assert [n.lineno for n in attrs(prepare,'preset_pose')]==[189]
    calls=[n for n in ast.walk(construct) if isinstance(n,ast.Call)
           and isinstance(n.func,ast.Name) and n.func.id=='run_inference_from_pil']
    assert len(calls)==1
    keys=[k.arg for k in calls[0].keywords]
    assert 'poses' in keys and 'depths' in keys and 'focals' not in keys and 'intrinsics' not in keys
    merge=fndef(pipeline,'merge_surfels')
    old_field_stores=[(n.attr,n.lineno) for n in ast.walk(merge)
                      if isinstance(n,ast.Attribute) and isinstance(n.ctx,ast.Store)
                      and n.attr in ('position','normal','radius','color')]
    assert old_field_stores==[]
    undo=fndef(pipeline,'undo_latest_move')
    assert not attrs(undo,'surfel_Ks')
    # Inventory source references only; no arrays or numerical packages needed.
    report={
        'schema':'s26-commit-consistency-source-only-v1',
        'recorded_utc':datetime.now(timezone.utc).isoformat(),
        'source_commit':COMMIT,'source_identity_checks_passed':True,
        'source_file_count':len(ids),'reviewed_source_identities':ids,
        'observations':{
            'surfel_Ks_attribute_lines':focal_lines,
            'normal_focal_cache_operation':'extend all N output focal snapshots each reconstruction',
            'query_focal_operation':'0.65 * mean(all historical reconstruction snapshots)',
            'prepare_output_preset_focal_calls':0,
            'geometry_call_keyword_names':keys,
            'normal_merge_geometric_field_attribute_stores':old_field_stores,
            'undo_surfel_Ks_references':0,
        },
        'model_instantiations':0,'model_forwards':0,'GA_runs':0,
        'RGB_or_GT_arrays_read':False,'S24_S26_predictions_or_scores_read':False,
        'torch_or_numpy_imported':('torch' in sys.modules or 'numpy' in sys.modules),
        'source_files_modified':0,'main_ledger_modified':False,
        'report_sha256':sha((HERE/'audit.md').read_bytes()),
        'audit_script_sha256':sha(Path(__file__).read_bytes()),
        'evidence_level':'SOURCE_ONLY; possible change is not an observed error or benefit',
        'verdict':'Two distinct testable mechanisms; future zero-GA saved-output diagnostic before new method or intervention',
        'correction_history':[{
            'initial_static_check':'expected preset_depth/preset_pose at lines 188/190',
            'outcome':'AssertionError in source-only audit; no numerical import or model/GA/data access',
            'verified_correction':'nl and AST confirm actual call lines 187/189; fixed line assertions only',
        }],
    }
    assert not report['torch_or_numpy_imported']
    (HERE/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('recorded_utc','source_identity_checks_passed','source_file_count','evidence_level')},ensure_ascii=False))

if __name__=='__main__':main()
