"""Narrow final delta audit; preserves previous artificial test results."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
H=R/'work/S26B_independent_review'
P=R/'work/S26B_preparation'
OLD='Scoring previously seen sensor data after four new GA producer seals; not novel-method, memory-mechanism, or video-generation evidence.'
NEW='Scoring previously seen sensor data after one IMPORT_VALIDATED saved producer and three newly completed GA producer seals; not novel-method, memory-mechanism, or video-generation evidence.'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())


def main():
    started=datetime.now(timezone.utc).isoformat()
    prior=read(H/'check_receipt.json'); m=read(P/'manifest_candidate.json')
    expected='d84a395c02514ba26f4eca2664af22551195d688cc6e1fe2db4342728540993f'
    checks=[]
    def check(name,value):
        assert value,name
        checks.append({'name':name,'passed':True})
    check('exact_final_candidate',sha(P/'manifest_candidate.json')==expected)
    checked,deferred={},{}
    for p,h in m['identities'].items():
        if Path(p).suffix.lower() in ('.npz','.npy','.png','.jpg','.jpeg','.pt','.pth','.safetensors'):
            deferred[p]=h
        else:
            assert sha(p)==h,p
            checked[p]=h
    changes={p for p,h in checked.items() if prior['source_control_identities_rehashed'].get(p)!=h}
    allowed={str(R/'scripts/score_s26b_consumer.py'),str(P/'plan.md'),str(P/'prepare_draft.py'),str(P/'derivation_proof.json')}
    check('only_four_expected_control_identity_changes',changes==allowed)
    check('all_data_identities_unchanged',deferred==prior['data_identities_deferred_to_frozen_import'])
    check('tested_importer_and_runner_unchanged',all(checked[str(p)]==prior['source_control_identities_rehashed'][str(p)]
          for p in (P/'import_previous.py',R/'scripts/s26b_consumer_baseline.py')))
    old=(R/'scripts/score_s26_consumer.py').read_text();new=(R/'scripts/score_s26b_consumer.py').read_text()
    check('exact_single_provenance_sentence_replacement',old.count(OLD)==new.count(NEW)==1 and OLD not in new)
    def normalized(text):
        tree=ast.parse(text.replace(NEW,OLD))
        tree.body=[n for n in tree.body if not(isinstance(n,ast.Assign) and
                   any(isinstance(t,ast.Name) and t.id in ('BASE','PROTOCOL') for t in n.targets))]
        return ast.dump(tree,include_attributes=False)
    check('scorer_AST_identical_except_two_paths_and_one_sentence',normalized(old)==normalized(new))
    ns={'__name__':'s26b_delta_metadata_only','__file__':str(R/'scripts/score_s26b_consumer.py')}
    exec(compile(new,ns['__file__'],'exec'),ns)
    ns['validate_config'](m['scoring'])
    check('current_scoring_metadata_validates',True)
    proof=read(P/'derivation_proof.json')
    check('derivation_proof_matches_current_scorer',proof['derived_scorer_sha256']==sha(R/'scripts/score_s26b_consumer.py')
          and proof['scorer_AST_identical_except_BASE_PROTOCOL_and_evidence_scope'] is True)
    check('candidate_unchanged_at_end',sha(P/'manifest_candidate.json')==expected)
    out={'passed':True,'schema':'s26b-provenance-text-delta-review-v1','started_utc':started,
         'completed_utc':datetime.now(timezone.utc).isoformat(),'candidate_sha256':expected,
         'checks':checks,'check_count':len(checks),'changed_controls':sorted(changes),
         'source_control_identities_rehashed':checked,'data_identities_deferred_to_frozen_import':deferred,
         'prior_artificial_checks_receipt_sha256':sha(H/'check_receipt.json'),
         'artificial_imports_repeated':0,'true_array_decodes':0,'NPZ_NPY_RGB_sensor_image_byte_reads':0,
         'model_runs':0,'GA_runs':0,'true_imports':0,'GT_reads':0}
    target=H/'delta_check_receipt.json';assert not target.exists();target.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':len(checks),'candidate_sha256':expected,'sha256':sha(target)}))


if __name__=='__main__':main()
