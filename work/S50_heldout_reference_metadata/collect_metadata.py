#!/usr/bin/env python3
"""Bounded text metadata audit. Never opens image, tensor, model, or archive bodies."""
from bisect import bisect_left
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
reads = {}
started = datetime.now(timezone.utc).isoformat()

def read_text(relative):
    p = ROOT / relative
    if p.suffix not in {'.md', '.json', '.jsonl', '.txt', '.py'}:
        raise ValueError(f'Non-text extension prohibited: {p}')
    raw = p.read_bytes()
    txt = raw.decode('utf-8')
    reads[str(p)] = {'sha256': sha256(raw).hexdigest(), 'bytes': len(raw),
                     'kind': 'TEXT_BYTES_READ_AND_HASHED', 'observed_utc': datetime.now(timezone.utc).isoformat()}
    return txt

def js(p):
    return json.loads(read_text(p))

def rows(p):
    return [line.split() for line in read_text(p).splitlines()
            if line.strip() and not line.lstrip().startswith('#')]

def ns(x):
    return int(Decimal(str(x)) * Decimal(10**9))

def stat_only(p):
    p = Path(p)
    result = {'path': str(p), 'existence': p.exists(), 'body_opened': False,
              'image_hash_recomputed': False}
    if p.exists():
        s = p.stat()
        result.update(size_bytes=s.st_size, inode=s.st_ino, device=s.st_dev,
                      mtime_ns=s.st_mtime_ns, resolved_path=str(p.resolve()))
    return result

scope_docs = ['AGENTS.md', 'RESEARCH_PRINCIPLES.md',
              'work/S49_reference_data_feasibility/DECISION_AFTER_V4_REVIEW.md',
              'work/S49_reference_data_feasibility/reference_time_feasibility.json',
              'docs/S15B_BONN_POSE_RESOLUTION.md', 'docs/S15B_PREFIX_PROTOCOL.md',
              'docs/S20_MINIMAL_VIDEO_PROTOCOL_DRAFT.md', 'scripts/run_s8_replay.py']
for path in scope_docs:
    read_text(path)

seqroots = {
    'fr1_xyz': 'data/tum/rgbd_dataset_freiburg1_xyz',
    'fr2_desk_original': 'data/tum/fr2_desk_download/extracted/rgbd_dataset_freiburg2_desk',
    'fr2_desk_guarded_alias': 'data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk'}
sequences = {}
trajectories = {}
for name, base in seqroots.items():
    rgb = rows(f'{base}/rgb.txt')
    depth = rows(f'{base}/depth.txt')
    gt = rows(f'{base}/groundtruth.txt')
    trajectories[name] = gt
    sequences[name] = {
        'root': str(ROOT / base), 'rgb_index_rows': len(rgb),
        'rgb_path_exists_count': sum((ROOT / base / r[1]).exists() for r in rgb),
        'depth_index_rows': len(depth), 'gt_rows': len(gt),
        'gt_distinct_timestamp_count': len({r[0] for r in gt}),
        'gt_duplicate_timestamp_text': [t for t,n in Counter(r[0] for r in gt).items() if n>1],
        'rgb_first_last_time_text': [rgb[0][0], rgb[-1][0]],
        'gt_first_last_time_text': [gt[0][0], gt[-1][0]],
        'gt_columns': ['timestamp', 'tx', 'ty', 'tz', 'qx', 'qy', 'qz', 'qw'],
        'image_body_read_count': 0,
        'distinct_sequence': name != 'fr2_desk_guarded_alias'}

s8 = js('data/cut3r/S8_fr2desk_inputs_v2/S8_inputs.json')
s8_run = js('results/S8_cut3r_cpu_v2/block0/run_metadata.json')
old_cam = js('work/S15B_root_preparation_v2/later_cameras_and_samples.json')
prefix_cam = js('work/S15B_root_preparation_v2/prefix_cameras.json')
s14d = js('results/S14D_ray_only_probe/run_metadata.json')
s14d_manifest = js('docs/S14D_RAY_ONLY_EXECUTION_MANIFEST_V2.json')
prepare = js('results/S14E_known_camera_prepare/frozen_manifest.json')
queries = js('results/S14E_known_camera_queries/frozen_manifest.json')
s24 = js('work/S24_baseline_expansion/run_manifest.json')
s24_unmatched = js('work/S24_baseline_expansion/independent_unmatched_rgb.json')
s24_run = js('results/S24_baseline_expansion/cut3r/receipt.json')
bonn_samples = js('work/S15A_samples_v2/samples.json')
bonn_run = js('results/S15A_bonn_history/run_metadata.json')
bonn_rgb = rows('work/S15A_metadata_fetch/members/rgbd_bonn_static_close_far/rgb.txt')
bonn_depth = rows('work/S15A_metadata_fetch/members/rgbd_bonn_static_close_far/depth.txt')
for p in ['data/cut3r/inference_inputs.json', 'data/cut3r/S5_inputs.json',
          'data/cut3r/S8_fr2desk_inputs_v2/sampling_metadata.json',
          'results/S15C_bonn_calibration/frozen_manifest.json',
          'data/bonn_s15a_history_combined/receipt.json', 'data/bonn_s15c_depth/receipt.json',
          'work/S15B_bonn_resolution/public_matrix_analysis.json',
          'work/S14_bonn_metadata_access/member_inventory.json',
          'work/S24_baseline_expansion/candidate_inputs.json',
          'results/S24_baseline_expansion/filt3r/receipt.json',
          'results/S24_baseline_expansion/ttt3r/receipt.json']:
    js(p)

gt = trajectories['fr2_desk_guarded_alias']
gt_ns = [ns(row[0]) for row in gt]
assert gt_ns == sorted(gt_ns) and len(gt_ns) == len(set(gt_ns))
raw_gt = trajectories['fr2_desk_original']
raw_gt_ns = [ns(row[0]) for row in raw_gt]
assert raw_gt_ns == sorted(raw_gt_ns)
def capture(index, role):
    f = s8['blocks'][0]['frames'][index]
    t = ns(f['rgb']['timestamp'])
    j = bisect_left(gt_ns, t)
    assert 0 < j < len(gt)
    before, after = gt[j-1], gt[j]
    width = gt_ns[j] - gt_ns[j-1]
    assert width > 0 and gt_ns[j-1] < t <= gt_ns[j]
    raw_j = bisect_left(raw_gt_ns, t)
    raw_equal = [before, after] == raw_gt[raw_j-1:raw_j+1]
    assert raw_equal
    return {'role': role, 'existing_block': 0, 'existing_frame_index': index,
            'rgb_capture_timestamp_text': str(f['rgb']['timestamp']),
            'rgb_capture_timestamp_ns': t,
            'rgb_file': stat_only(ROOT / seqroots['fr2_desk_guarded_alias'] / f['rgb']['path']),
            'associated_depth_timestamp_text': str(f['depth']['timestamp']),
            'rgb_minus_depth_ns': t - ns(f['depth']['timestamp']),
            'rgb_time_gt_bracket': {'before_values_as_published_text': before,
                                    'after_values_as_published_text': after,
                                    'gap_ns': width,
                                    'gt_source': 'fr2_desk_guarded_alias/groundtruth.txt',
                                    'bracketing_rows_identical_in_original_raw_trajectory': raw_equal,
                                    'interpolation_fraction': str(Decimal(t-gt_ns[j-1])/Decimal(width)),
                                    'interpolated_pose_computed_this_audit': False},
            'historical_s8_image_entry': s8_run['images'][index],
            'historical_s8_view_flags': s8_run['view_flags_before_inference'][index],
            'historical_hash_status': 'COPIED_FROM_PRIOR_TEXT_RECEIPT_NOT_REHASHED',
            'historically_model_exposed': True}

candidates = [capture(18, 'provisional_alternative'), capture(19, 'provisional_original_source'),
              capture(20, 'provisional_target')]
assert candidates[-1]['historical_s8_view_flags']['img_mask'] == [True]
assert candidates[-1]['historical_s8_view_flags']['update'] == [False]
assert candidates[-1]['rgb_minus_depth_ns'] == 15005000

bonn_paths = [p for p in (ROOT / 'data').rglob('*.png') if 'bonn' in str(p) and p.parent.name == 'rgb']
bonn_unique_names = sorted(set(p.name for p in bonn_paths))
future = []
for f in bonn_samples['samples']:
    if f['role'] == 'future_target':
        matching = [str(p) for p in bonn_paths if p.name == Path(f['rgb_member']).name]
        future.append({'sample_index': f['index'], 'rgb_timestamp': f['rgb_timestamp'],
                       'archive_member_name': f['rgb_member'], 'local_matches_in_data': matching,
                       'absence_scope': 'filename/stat inventory under project data only, not global access history'})

current_generation = []
for stage, path in [('S40', 'work/S40_declared_variant_generation/freeze_attempt_01/manifest_core.json'),
                    ('C1', 'work/S44_c1_confirmation_generation/freeze_attempt_01/manifest_core.json')]:
    m = js(path)
    current_generation.append({'stage': stage, 'manifest': path, 'input_image': m['input_image'],
                               'controls': m['controls'],
                               'same_scene_as_tum_candidates_proven': False,
                               'real_target_correspondence': 'NOT_ESTABLISHED',
                               'payload_or_input_image_opened_this_audit': False})

result = {
 'schema': 's50-heldout-reference-metadata-feasibility-v1',
 'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
 'evidence_kind': 'LOCAL_TEXT_METADATA_AND_PATH_STAT_ONLY',
 'audit_attempt_note': 'The first audit execution stopped before writing evidence because a global unique-timestamp assertion failed on original fr2 groundtruth (one repeated timestamp with differing poses). The collector then explicitly selected the already-frozen guarded trajectory, kept both source hashes/counts, and checked candidate bracketing rows match the raw trajectory. No dataset was modified; exact first-attempt clock was not separately captured.',
 'verdict': 'CANDIDATE_WITH_EXPLICIT_MISSING_PROVENANCE_NOT_READY',
 'scope': {'image_bodies_read_or_hashed': 0, 'image_decodes': 0, 'tensor_payload_reads': 0,
           'model_calls': 0, 'downloads': 0, 'c1_c2_pixels_read': 0,
           'zero_counts_basis': 'this audit code and commands; not an OS-wide access attestation'},
 'selection_rule': 'Reuse pre-existing S8 block0 first target index20 and immediately preceding source19 / alternative18 as an illustrative candidate. No target image, generated image, measured error, or predicted score used to select.',
 'sequences': sequences, 'candidate_chain': candidates,
 'candidate_contract_status': {
     'preexisting_capture_identity_and_file_presence': True,
     'published_rgb_time_gt_brackets_available': True,
     'calibration': {'historically_declared_native_K': [[525,0,319.5],[0,525,239.5],[0,0,1]],
                     'historically_declared_resolution': [640,480],
                     'historically_derived_224_K': old_cam['K'],
                     'reference': 'scripts/run_s8_replay.py native_intrinsics; docs/S15B_PREFIX_PROTOCOL.md; results/S14E_known_camera_prepare/frozen_manifest.json',
                     'fresh_sensor_calibration_verified': False,
                     'future_576_preprocessing_and_K_binding': 'MISSING'},
     'old_target_pose_time': old_cam['pose_time_target'],
     'old_target_pose_can_be_reused_as_rgb_pose_without_conversion': False,
     'new_generation_exclusion_manifest': 'MISSING',
     'new_upstream_geometry_input_exclusion_manifest': 'MISSING',
     'target_never_conditioned_in_current_candidate_generation': 'NOT_ESTABLISHED_NO_SUCH_RUN',
     'globally_never_model_seen': False,
     'historically_independent_confirmation': False,
     'matched_original_alternative_pose_fov_visibility_eligibility': 'NOT_YET_ESTABLISHED',
     'fixed_valid_scoring_domain': 'MISSING',
     'allowable_next_stage': 'future explicitly discovery-only split after positive exclusion provenance is frozen; no existing generation scoring authorization'},
 'historical_usage': {
    'fr1_s24': {'manifest': 'work/S24_baseline_expansion/run_manifest.json', 'declared_input_count': len(s24['frames']),
               'manifest_previously_exposed': s24['previously_exposed'],
               'cut3r_status': s24_run['status'], 'cut3r_frames_completed': s24_run['frames_completed'],
               'two_other_indexed_rgb': s24_unmatched['unmatched_rgb'],
               'two_other_rgb_never_used': 'UNKNOWN; S24 exclusion was only one-to-one timestamp matching, not global exposure proof'},
    'fr2_s8': {'block0_images': len(s8_run['images']), 'target20_img_mask': s8_run['view_flags_before_inference'][20]['img_mask'],
               'target20_update': s8_run['view_flags_before_inference'][20]['update'],
               'interpretation': 'No state update is not absence of image conditioning. Candidate target20 has positive historical RGB input evidence.'},
    'fr2_s14d': {'history_manifest_image_count': len(s14d_manifest['history_images']),
                 'actual_opened_image_count': len(s14d['image_opened_paths']),
                 'counters': s14d['counters'], 'target20_present_in_open_list': any(Path(p).name==Path(candidates[-1]['rgb_file']['path']).name for p in s14d['image_opened_paths']),
                 'scope': 'Historical run receipt supports a 20-RGB history-only rerun, but its synthetic target-camera probe and old S14E depth-time target cameras are not a new VMem real-RGB target binding.'},
    'bonn': {'index_rgb_count': len(bonn_rgb), 'index_depth_count': len(bonn_depth),
             'local_data_unique_rgb_filenames': bonn_unique_names,
             'local_data_unique_rgb_filename_count': len(bonn_unique_names),
             's15a_actual_opened_count': len(bonn_run['image_opened_paths']),
             's15a_counters': bonn_run['counters'], 'future_four': future,
             'optical_pose_semantics': 'UNRESOLVED_POSE_SEMANTICS in existing docs/S15B_BONN_POSE_RESOLUTION.md',
             'native_K_and_distortion': 'historical public calibration exists, but this audit did not reacquire or certify optical pose / distortion / clock mapping'}},
 'current_generation': current_generation,
 'important_nonclaims': ['No absence-of-record is treated as never-used evidence.',
                       'No TUM capture is a valid reference for the unrelated changi/jesus demo generations.',
                       'A future run can hold out an historically exposed RGB for a declared discovery diagnostic; it cannot turn it into a new independent confirmation scene.',
                       'One observed reference allows a paired observed loss only, not absolute memory utility or expected scene risk.',
                       'The original three-reference contract remains unsatisfied; this audit does not amend it.'],
 'text_sources_read_and_hashed': reads,
}
target = OUT / 'evidence.json'
if target.exists():
    raise FileExistsError('Preserve prior evidence.json; use a versioned follow-up if needed')
target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'path': str(target), 'sha256': sha256(target.read_bytes()).hexdigest(),
                  'text_sources': len(reads), 'candidate_times': [c['rgb_capture_timestamp_text'] for c in candidates],
                  'gt_bracket_gaps_ms': [c['rgb_time_gt_bracket']['gap_ns']/1e6 for c in candidates],
                  'bonn_local_unique_rgb':len(bonn_unique_names), 'verdict':result['verdict']},ensure_ascii=False))
