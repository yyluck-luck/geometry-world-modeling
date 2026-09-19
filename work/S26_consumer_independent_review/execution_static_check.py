"""Independent source/JSON checks only. Never import the experiment or open data."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE = Path(__file__).resolve().parent
CP = ROOT / 'work/S26_consumer_baseline_preparation/manifest_candidate.json'
EXPECTED = '2af4f8bb13caee8923ce180e0dcc02bb2a6538b3a3c0f87684bd8db33af0dccf'
DATA_SUFFIXES = {'.npz', '.npy', '.png', '.jpg', '.jpeg', '.pt', '.pth', '.safetensors'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    assert Path(path).suffix == '.json'
    return json.loads(Path(path).read_bytes())


def function(path, name):
    found = [n for n in ast.walk(ast.parse(Path(path).read_text()))
             if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(found) == 1
    return found[0]


def main():
    started = datetime.now(timezone.utc).isoformat()
    checks = []

    def check(name, value):
        if not value:
            raise AssertionError(name)
        checks.append({'name': name, 'passed': True})

    check('exact_parent_candidate', sha(CP) == EXPECTED)
    m = read(CP)
    check('candidate_stage', m['status'] == 'CANDIDATE_PENDING_INDEPENDENT_REVIEW')
    check('no_model_four_original_ga', m['model_forwards'] == 0 and m['ga_runs'] == 4
          and m['ga_steps_per_run'] == 400)
    checked, skipped = {}, {}
    for name, expected in m['identities'].items():
        p = Path(name)
        assert p.is_absolute()
        if p.suffix.lower() in DATA_SUFFIXES:
            skipped[name] = expected
        else:
            assert sha(p) == expected, name
            checked[name] = expected
    check('all_559_nonimage_control_source_identities', len(checked) == 559)
    check('six_skipped_images_are_repository_demo_assets_only', len(skipped) == 6
          and all('/src/croco/assets/' in p for p in skipped))
    for name in ('scripts/s26_consumer_baseline.py', 'scripts/score_s26_consumer.py',
                 'scripts/prepare_s26_consumer.py',
                 'work/S26_consumer_baseline_preparation/saved_heads_adapter.py'):
        ast.parse((ROOT / name).read_text())
    check('four_current_programs_parse_without_import', True)
    ci = read(ROOT / 'work/S26_consumer_baseline_preparation/candidate_inputs.json')
    sc = read(ROOT / 'work/S26_scoring_preparation/candidate_scoring_inputs.json')
    check('candidate_inputs_and_scoring_embedded_exactly', ci == m['candidate'] and sc == m['scoring'])
    check('frame_domain_old4_new4', ci['prefix_length'] == 4 and ci['new_frame_indices'] == [4, 5, 6, 7]
          and [f['index'] for f in ci['frames']] == list(range(8)))
    check('archive_counts_common4_then_three8', {k: len(v) for k, v in ci['archives'].items()}
          == {'common_old_depth_original4': 4, 'cut3r': 8, 'ttt3r': 8, 'filt3r': 8})
    for rows in ci['archives'].values():
        assert [r['index'] for r in rows] == list(range(len(rows)))
    check('archive_index_order_metadata', True)
    ttt = Path(m['preprocess_function'])
    filt = Path(m['preprocess_repos']['filt']) / 'eval/relpose/launch.py'
    check('ttt_filt_prepare_input_same_AST', ast.dump(function(ttt, 'prepare_input'), include_attributes=False)
          == ast.dump(function(filt, 'prepare_input'), include_attributes=False))
    for category in ('control_sha256', 'metadata_sources_sha256'):
        for p, expected in sc[category].items():
            assert sha(ROOT / p) == expected
    check('all_scoring_control_and_metadata_SHA_match', True)
    history = read(ROOT / 'results/S23_geometry_diagnostic/gt_receipt.json')
    inherited = {(r['index'], r['path']): r['sha256'] for r in history['files']}
    check('eight_GT_identities_inherited_without_PNG_reads',
          len(sc['gt_depth_frames']) == 8 and all(
              inherited[(r['index'], r['path'])] == r['sha256'] for r in sc['gt_depth_frames']))
    check('scoring_common4_three8_interface', sc['producer_frame_counts']
          == {'common_old': 4, 'cut3r': 8, 'ttt3r': 8, 'filt3r': 8})
    check('scoring_domains_and_no_fitting_masks', sc['old_frame_indices'] == list(range(4))
          and sc['new_frame_indices'] == list(range(4, 8)) and sc['gt_scale_fit'] is False
          and sc['confidence_mask'] is False and sc['far_depth_cut'] is False
          and sc['old_depth_tolerance'] == {'atol': 1e-6, 'rtol': 1e-6})
    old = read(HERE / 'review_receipt.json')
    check('earlier_preparation_semantic_review_still_bound', all(
          sha(p) == expected for p, expected in old['reviewed_identities'].items()))
    root_review = read(ROOT / 'work/S26_root_review/scorer_review.json')
    check('different_author_arithmetic_receipt_binds_current_scorer', root_review['passed'] is True
          and root_review['scorer_sha256'] == sha(ROOT / 'scripts/score_s26_consumer.py'))
    check('candidate_unchanged_at_end', sha(CP) == EXPECTED)
    result = {
        'schema': 's26-independent-execution-static-check-v1',
        'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
        'passed': True, 'checks': checks, 'check_count': len(checks),
        'candidate_sha256': EXPECTED, 'checked_identities': checked,
        'skipped_repository_demo_image_identities': skipped,
        'dependency_identities_inherited_not_rehashed': len(m['dependency_identities']),
        'real_data_byte_reads': 0, 'real_prediction_decodes': 0, 'GT_coordinate_parses': 0,
        'sensor_depth_decodes': 0, 'experiment_imports': 0, 'model_runs': 0, 'GA_runs': 0,
        'scope': 'Standard-library JSON, SHA and AST checks; no source program imported or executed.'
    }
    target = HERE / 'execution_static_check_receipt.json'
    assert not target.exists(), 'Preserve previous static receipt'
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'passed': True, 'checks': len(checks), 'receipt': str(target), 'sha256': sha(target)}))


if __name__ == '__main__':
    main()
