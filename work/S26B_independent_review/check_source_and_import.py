"""Bound static audit and artificial-byte importer checks; no true-array reads."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE = Path(__file__).resolve().parent
PREP = ROOT / 'work/S26B_preparation'
CP = PREP / 'manifest_candidate.json'
EXPECTED = '1b4610c48aaaf12faa4648e73adf69273e0233050d48f71b07da925091643aa8'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_bytes())


def write(p, value):
    Path(p).write_text(json.dumps(value, indent=2) + '\n')


def definition(p, name):
    candidates = [n for n in ast.parse(Path(p).read_text()).body
                  if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name]
    assert len(candidates) == 1
    return candidates[0]


class RemoveCheckpoint(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        if node.name == 'checkpoint':
            return None
        return self.generic_visit(node)

    def visit_Expr(self, node):
        if (isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == 'checkpoint'):
            return None
        return self.generic_visit(node)


def main():
    started = datetime.now(timezone.utc).isoformat()
    assert not (HERE / 'check_receipt.json').exists()
    checks = []

    def check(name, condition):
        assert condition, name
        checks.append({'name': name, 'passed': True})

    check('exact_final_candidate', sha(CP) == EXPECTED)
    m = read(CP)
    old = read(ROOT / 'work/S26_consumer_baseline_preparation/run_manifest.json')
    checked, deferred = {}, {}
    for p, h in m['identities'].items():
        if Path(p).suffix.lower() in ('.npz', '.npy', '.png', '.jpg', '.jpeg', '.pt', '.pth', '.safetensors'):
            deferred[p] = h
        else:
            assert sha(p) == h, p
            checked[p] = h
    check('current_nondata_control_source_hashes_match', True)
    for key in ('candidate','binding','preprocess_repos','preprocess_function','dependency_identities','core_versions',
                'given_cameras','sensor_depth','model_forwards','ga_steps_per_run'):
        assert m[key] == old[key], key
    check('all_shared_experimental_conditions_unchanged', True)
    check('only_three_new_400_step_GA', m['ga_runs'] == 3 and m['continuation']['new_GA_steps'] == 1200
          and m['continuation']['imported_original_GA_steps'] == 400)
    scoring_old, scoring_new = copy.deepcopy(old['scoring']), copy.deepcopy(m['scoring'])
    for k in ('producer_dirs','scoring_output','control_sha256'):
        scoring_old.pop(k); scoring_new.pop(k)
    check('scoring_config_math_and_GT_identity_unchanged', scoring_old == scoring_new)
    old_runner = ROOT/'scripts/s26_consumer_baseline.py'
    runner = ROOT/'scripts/s26b_consumer_baseline.py'
    original_ga = definition(old_runner,'ga_worker')
    revised_ga = definition(runner,'ga_worker')
    assert 'S26B never reruns common_old GA' in ast.unparse(revised_ga.body[0])
    revised_ga.body = revised_ga.body[1:]
    revised_ga = RemoveCheckpoint().visit(revised_ga)
    check('GA_AST_identical_except_denial_guard_and_logging', ast.dump(original_ga, include_attributes=False)
          == ast.dump(revised_ga, include_attributes=False))
    observer = RemoveCheckpoint().visit(definition(runner,'SceneObserver'))
    check('observer_AST_identical_except_logging', ast.dump(observer, include_attributes=False)
          == ast.dump(definition(old_runner,'SceneObserver'), include_attributes=False))
    old_scorer = ROOT/'scripts/score_s26_consumer.py'
    new_scorer = ROOT/'scripts/score_s26b_consumer.py'
    def strip_paths(p):
        tree = ast.parse(p.read_text())
        tree.body = [n for n in tree.body if not (isinstance(n,ast.Assign) and
                     any(isinstance(t,ast.Name) and t.id in ('BASE','PROTOCOL') for t in n.targets))]
        return ast.dump(tree,include_attributes=False)
    check('whole_scorer_AST_identical_except_BASE_PROTOCOL', strip_paths(old_scorer)==strip_paths(new_scorer))
    # Import definitions only: scorer's validation is standard-library metadata,
    # unlike its separate score entry point, which is never called here.
    scorer_ns = {'__name__':'s26b_independent_definition_check','__file__':str(new_scorer)}
    exec(compile(new_scorer.read_text(),str(new_scorer),'exec'),scorer_ns)
    scorer_ns['validate_config'](m['scoring'])
    check('actual_frozen_scoring_object_passes_current_validation', True)
    c = m['continuation']; recovery = read(c['recovery_receipt_path'])
    check('exact_author_independent_recovery_contract', recovery['status']=='IMPORT_VALIDATED'
          and recovery['passed'] is True and sha(c['recovery_receipt_path'])==c['recovery_receipt_sha256']
          and recovery['old_manifest_sha256']==c['original_manifest_sha256']
          and recovery['old_output_npz_sha256']==c['common_files']['output.npz']['sha256'])
    for key in ('input_identities_before_after','control_identities'):
        assert all(m['identities'].get(p)==h for p,h in recovery[key].items())
    check('all_recovery_input_and_validator_identity_closure', True)
    assert set(c['common_files']) == {'output.npz','preclean_conf.npz','pairwise_state.npz',
           'preset_parameters.npz','consumed_inputs.npz','input_colors.npz','optimization_trace.jsonl'}
    for entry in (*c['common_files'].values(),*c['shared_artifacts'].values()):
        assert recovery['input_identities_before_after'].get(entry['path'])==entry['sha256']
        assert m['identities'].get(entry['path'])==entry['sha256']
    check('every_imported_artifact_bound_to_recovery_and_candidate', True)
    bridge = (PREP/'numerical_reference.py').read_text()
    check('bridge_retains_old_objective_and_new_clean',
          sha(ROOT/'work/S17C_independent_preparation/numerical_reference.py') in bridge
          and sha(ROOT/'work/S26_clean_recovery/clean_reference_torch_fp32.py') in bridge
          and 'pair_objective=old.pair_objective' in bridge and 'clean_reference=revised.clean_reference' in bridge)
    importer_path = PREP/'import_previous.py'
    ns = {'__name__':'s26b_artificial_import_check','__file__':str(importer_path)}
    exec(compile(importer_path.read_text(),str(importer_path),'exec'),ns)

    def fixture(label, invalid_status=False):
        base = HERE/'artificial'/label
        base.mkdir(parents=True,exist_ok=False)
        source, work, output = base/'old',base/'new_work',base/'new_output'
        source.mkdir();work.mkdir()
        manifest = source/'manifest.json';write(manifest,{'status':'FROZEN','synthetic':True})
        failed = source/'receipt.json';write(failed,{'status':'FAILED','manifest_sha256':sha(manifest)})
        data=source/'output.npz';data.write_bytes(b'ARTIFICIAL BYTES ONLY; NOT A NUMPY ARCHIVE')
        camera=source/'control_c2w.npy';camera.write_bytes(b'ARTIFICIAL CAMERA BYTES ONLY')
        control=source/'control_receipt.json';write(control,{'status':'PASS','manifest_sha256':sha(manifest),'output_sha256':sha(camera)})
        compat=source/'compatibility_receipt.json';write(compat,{'status':'PASS','manifest_sha256':sha(manifest)})
        validator=source/'validator.py';validator.write_text('# artificial validator identity\n')
        recover=source/'recovery.json'
        rr={'status':'WRONG' if invalid_status else 'IMPORT_VALIDATED','passed':True,
            'old_manifest_sha256':sha(manifest),'revised_clean_sha256':'a'*64,'old_output_npz_sha256':sha(data),
            'historical_observations_not_recorded':{'postfinal':'NOT_RECORDED'},'checks':[{'passed':True}],
            'input_identities_before_after':{str(p):sha(p) for p in (manifest,failed,data,camera,control,compat)},
            'control_identities':{str(validator):sha(validator)},'depth_tensor_sha256':'b'*64,
            'control_pose_prefix_tensor_sha256':'c'*64}
        write(recover,rr)
        entry=lambda p:{'path':str(p),'sha256':sha(p)}
        cc={'original_manifest_path':str(manifest),'original_manifest_sha256':sha(manifest),
            'original_common_receipt_path':str(failed),'recovery_receipt_path':str(recover),
            'recovery_receipt_sha256':sha(recover),'revised_clean_sha256':'a'*64,
            'common_files':{'output.npz':entry(data)},
            'shared_artifacts':{'control_receipt.json':entry(control),'control_c2w.npy':entry(camera),'compatibility_receipt.json':entry(compat)}}
        mm={'continuation':cc,'candidate':{'archives':{'common_old_depth_original4':[]}}}
        parent=base/'new_manifest.json';write(parent,mm)
        return mm,parent,work,output,validator,rr

    args = fixture('successful_import')
    ns['import_previous'](*args[:4])
    imported=read(args[3]/'common_old/receipt.json')
    check('artificial_import_copies_bytes_and_records_narrow_PASS',
          imported['status']=='PASS' and imported['validation_status']=='IMPORT_VALIDATED'
          and imported['producer_kind']=='IMPORT_VALIDATED_SAVED_ORIGINAL_GA'
          and imported['new_GA_runs']==imported['new_optimizer_steps']==0
          and imported['historical_observations_not_recorded']=={'postfinal':'NOT_RECORDED'}
          and sha(args[3]/'common_old/output.npz')==args[0]['continuation']['common_files']['output.npz']['sha256'])
    check('artificial_old_FAILED_and_all_sources_unchanged',
          all(sha(p)==h for p,h in args[5]['input_identities_before_after'].items()))
    bad=fixture('invalid_recovery_status',invalid_status=True)
    try:
        ns['import_previous'](*bad[:4]);raise AssertionError('Expected invalid recovery to stop')
    except RuntimeError as e:
        check('invalid_recovery_rejected_before_output_writes','narrow import validation' in str(e) and not bad[3].exists())
    bad=fixture('changed_during_copy')
    original_copy=shutil.copyfile
    def mutate_control_after_copy(src,dst):
        result=original_copy(src,dst)
        bad[4].write_text('# artificial mutation during copy\n')
        return result
    ns['shutil']=SimpleNamespace(copyfile=mutate_control_after_copy)
    try:
        ns['import_previous'](*bad[:4]);raise AssertionError('Expected changed source to stop')
    except RuntimeError as e:
        check('mutation_during_copy_rejected_without_common_PASS',
              'Recovery controls changed during import' in str(e) and not (bad[3]/'common_old/receipt.json').exists())
    check('no_numerical_library_or_experiment_loaded','numpy' not in sys.modules and 'torch' not in sys.modules)
    check('candidate_unchanged_at_end',sha(CP)==EXPECTED)
    record={'schema':'s26b-independent-source-and-artificial-import-check-v1','passed':True,
            'started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),
            'candidate_sha256':EXPECTED,'checks':checks,'check_count':len(checks),
            'source_control_identities_rehashed':checked,'data_identities_deferred_to_frozen_import':deferred,
            'true_array_decodes':0,'NPZ_NPY_RGB_sensor_image_byte_reads':0,'sensor_GT_reads':0,'model_runs':0,'GA_runs':0,
            'artificial_import_invocations':3,'scope':'Source/JSON plus fake-byte filesystem importer semantics; no real importer/GA/scoring execution'}
    write(HERE/'check_receipt.json',record)
    print(json.dumps({'passed':True,'checks':len(checks),'rehashed_controls':len(checked),
                      'data_identities_deferred':len(deferred),'receipt_sha256':sha(HERE/'check_receipt.json')}))


if __name__ == '__main__':
    main()
