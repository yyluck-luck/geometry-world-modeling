#!/usr/bin/env python3
"""Post-hoc, separately authored S13 verification; never imports the runner.

NumPy only opens existing support/valid arrays. Four explicit index loops and
Python integer OR/AND/bit_count re-enumerate the entire domain. A second Python
set union checks every current selection and reported optimum. This script
writes only to a new audit directory and preserves all original experiment data.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import platform
import resource
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'results/S13_oracle_headroom_retry01'
FREEZE = ROOT / 'docs/S13_ORACLE_EXECUTION_FREEZE.json'
S12 = ROOT / 'results/S12_matched_budget'
DERIVED_ATOL = 1e-12
SCHEDULE = [(stage, block, query) for stage in ('S7', 'S8')
            for block in range(3) for query in range(20, 24)]
COUNTS = Counter()
MAX_DIFFERENCE = 0.0


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def require(condition, label, category):
    COUNTS[category] += 1
    if not condition:
        raise AssertionError(label)


def exact(actual, expected, label, category):
    require(actual == expected, f'{label}: {actual!r} != {expected!r}', category)


def derived(actual, rational, label):
    global MAX_DIFFERENCE
    expected = float(rational)
    difference = abs(actual - expected)
    MAX_DIFFERENCE = max(MAX_DIFFERENCE, difference)
    require(math.isfinite(actual) and difference <= DERIVED_ATOL,
            f'{label}: difference={difference}', 'derived_float')


def identity(paths):
    result = {}
    for path in sorted(set(paths)):
        require(path.is_file() and not path.is_symlink() and
                path.resolve().is_relative_to(ROOT), str(path), 'file_identity')
        result[str(path.relative_to(ROOT))] = digest(path)
    return result


def combos(pool):
    # Independent of production itertools.combinations, with lexicographic IDs.
    size = len(pool)
    for a in range(size - 3):
        for b in range(a + 1, size - 2):
            for c in range(b + 1, size - 1):
                for d in range(c + 1, size):
                    yield pool[a], pool[b], pool[c], pool[d]


def score(bits, valid_bits, selected):
    union = 0
    for index in selected:
        union |= bits[index]
    return (union & valid_bits).bit_count()


def main(output):
    require(not output.exists() and not output.is_symlink(),
            'Use a new directory; previous output must be preserved', 'output_guard')
    output.mkdir(parents=True)
    start = time.monotonic()
    verification = dict(schema='s13-independent-audit-v1', status='RUNNING',
                        started_utc=now(), reviewer='separately authored sub-agent',
                        timing='post-hoc audit, authored after S13 results existed',
                        fixed_derived_float_atol=DERIVED_ATOL,
                        integer_id_tie_hash_tolerance=0,
                        production_runner_imported=False,
                        raw_images_or_gt_poses_opened=False,
                        model_renderer_projection_nms_calls=0,
                        environment=dict(python=sys.version, executable=sys.executable,
                                         platform=platform.platform()),
                        auditor_sha256=digest(Path(__file__)))
    write(output / 'verification.json', verification)
    (output / 'auditor_snapshot.py').write_bytes(Path(__file__).read_bytes())
    write(output / 'audit_plan.json', dict(recorded_utc=now(),
          scope='Post-hoc verification of S13 saved support, not a preregistered study',
          schedule=SCHEDULE, pools={'geometry14': 14, 'pose14': 14, 'all20': 20},
          count_per_pool=[math.comb(n, 4) for n in (14, 14, 20)],
          expected_combinations=164328,
          method='Four nested index loops; Python integer bitsets; independent set checks for 120 selected/optimal sets',
          saved_trace='Every enumerated combination and integer score is saved in gzip CSV',
          exact=['candidate IDs', 'selected IDs', 'integer numerator/denominator',
                 'lexicographic optimum', 'tie counts', 'combination hashes', 'file hashes', 'single ratios'],
          derived_float_atol=DERIVED_ATOL,
          no_pooling=True, no_nms_constraints_in_oracle=True))
    try:
        freeze, metadata = read(FREEZE), read(RUN / 'run_metadata.json')
        extra = [S12 / 'summary.json',
                 ROOT / 'results/S12_matched_budget_independent_audit/verification.json',
                 ROOT / 'results/S12_matched_budget_independent_audit/audited_result_sha256.json']
        inputs = [ROOT / name for name in freeze['input_sha256']]
        sources = [ROOT / name for name in freeze['sources']]
        protected = inputs + sources + extra + [FREEZE] + list(RUN.glob('*.json')) + [Path(__file__)]
        before = identity(protected)
        write(output / 'audited_input_sha256.json', before)
        exact(metadata['status'], 'completed', 'S13 completed', 'metadata')
        exact(freeze['status'], 'approved_for_execution', 'S13 freeze', 'metadata')
        exact(len(inputs), 52, '52 input entries', 'freeze_binding')
        exact(len(sources), 4, '4 source entries', 'freeze_binding')
        for name, expected in freeze['input_sha256'].items():
            exact(before[name], expected, name, 'freeze_binding')
        for name, expected in freeze['sources'].items():
            exact(before[name], expected, name, 'freeze_binding')
        exact(metadata['input_sha256'], freeze['input_sha256'], 'run input map', 'freeze_binding')
        exact(metadata['execution_freeze_sha256'], digest(FREEZE), 'run freeze SHA', 'freeze_binding')
        exact(metadata['candidate_seal_sha256'], digest(RUN / 'candidate_seal.json'), 'candidate file SHA', 'seal')
        expected_paths = {'results/S12_matched_budget/run_metadata.json',
                          'results/S12_matched_budget/records.json',
                          'docs/S13_ORACLE_HEADROOM_DESIGN.md',
                          'results/S13_oracle_headroom_preflight/receipt.json'}
        for stage, block, query in SCHEDULE:
            folder = 'S7_event_replay' if stage == 'S7' else 'S8_event_replay_v2'
            expected_paths.update(f'results/{folder}/block{block}_stride{stride}/query{query}_scoring.npz'
                                  for stride in (8, 12))
        exact(set(freeze['input_sha256']), expected_paths, 'precise input set', 'freeze_binding')
        # Retrospective supplemental validation, never mislabelled pre-run binding.
        previous_audit = read(extra[1])
        exact(previous_audit['status'], 'PASS', 'prior S12 audit status', 'supplemental_s12')
        previous_identity = read(extra[2])
        for name in ('summary.json', 'run_metadata.json', 'records.json'):
            exact(digest(S12 / name), previous_identity[name], 'S12 audit reference ' + name, 'supplemental_s12')
        review = read(ROOT / 'results/S13_oracle_entry_review_v3/review.json')
        exact(review['status'], 'PASS', 'static review status', 'metadata')
        exact(review['source_sha256'], digest(ROOT / 'scripts/run_s13_oracle_headroom.py'),
              'static review current runner SHA', 'metadata')
        seal = read(RUN / 'candidate_seal.json')
        exact(seal['sealed_utc'], metadata['candidate_sealed_utc'], 'seal time identity', 'chronology')
        times = [datetime.fromisoformat(x) for x in (freeze['created_utc'], metadata['started_utc'],
                 metadata['candidate_sealed_utc'], metadata['first_scoring_decode_utc'], metadata['completed_utc'])]
        require(all(a < b for a, b in zip(times, times[1:])), 'Recorded phase chronology', 'chronology')
        all_s12 = read(S12 / 'records.json')
        main_rows = [row for row in all_s12 if row['main_comparison']]
        results = read(RUN / 'records.json')
        exact(len(main_rows), 24, 'S12 main count', 'domain')
        exact(len(results), 24, 'S13 result count', 'domain')
        exact(len(seal['queries']), 24, 'S13 seal count', 'domain')
        key = lambda row: (row['stage'], row['block'], row['query'])
        old = {key(row): row for row in main_rows}
        exact(set(old), set(SCHEDULE), 'S12 full schedule', 'domain')
        exact([key(row) for row in results], SCHEDULE, 'S13 ordered full schedule', 'domain')
        exact([key(row) for row in seal['queries']], SCHEDULE, 'seal ordered full schedule', 'domain')
        import numpy as np
        verification['environment']['numpy'] = np.__version__
        # Manual cases cover duplicate support, all-zero optimum/ties, masking.
        manual = [([1, 2, 4, 8, 0], 15, [0, 1, 2, 3], 4, 1),
                  ([0, 0, 0, 0, 0], 15, [0, 1, 2, 3], 0, 5),
                  ([1, 1, 2, 2, 4], 3, [0, 1, 2, 3], 2, 5)]
        for bits, valid, optimum, numerator, ties in manual:
            scored = [(score(bits, valid, item), item) for item in combos(list(range(5)))]
            maximum = max(value for value, _ in scored)
            winners = [ids for value, ids in scored if value == maximum]
            exact((maximum, list(min(winners)), len(winners)),
                  (numerator, optimum, ties), 'manual bitset control', 'manual_control')
        independent, total, npz_count = [], 0, 0
        with gzip.open(output / 'all_combination_scores.csv.gz', 'wt', encoding='utf-8', newline='') as trace:
            trace.write('stage,block,query,pool,id0,id1,id2,id3,supported_pixels,valid_pixels\n')
            for run_row, sealed_row in zip(results, seal['queries']):
                ident = key(run_row)
                stage, block, query = ident
                previous = old[ident]
                exact((previous['arm'], previous['stride']), ('A0P0', 8), str(ident), 'domain')
                split = 'development' if stage == 'S7' and block == 0 else 'test'
                exact(previous['split'], split, 'source split', 'domain')
                exact(run_row['split'], split, 'output split', 'domain')
                pools = {'geometry14': sorted(previous['geometry14_candidates']),
                         'pose14': sorted(previous['pose14_ranked_candidates']), 'all20': list(range(20))}
                current_source = {'geometry14': previous['old_readouts']['official'], 'pose14': previous['pose14']}
                selected = {name: sorted(item['selected']) for name, item in current_source.items()}
                expected_seal = dict(stage=stage, block=block, query=query, split=split,
                                     pools=pools, selected=selected,
                                     saved_support={name: item['support'] for name, item in current_source.items()},
                                     combo_hashes={})
                folder = 'S7_event_replay' if stage == 'S7' else 'S8_event_replay_v2'
                arrays = []
                for stride in (8, 12):
                    path = ROOT / f'results/{folder}/block{block}_stride{stride}/query{query}_scoring.npz'
                    with np.load(path, allow_pickle=False) as archive:
                        support, valid = archive['support'], archive['valid']
                    npz_count += 1
                    exact((support.dtype.str, support.shape), ('|b1', (20, 112, 112)), str(path), 'array_header')
                    exact((valid.dtype.str, valid.shape), ('|b1', (112, 112)), str(path), 'array_header')
                    arrays.append((support.tobytes(order='C'), valid.tobytes(order='C')))
                exact(arrays[0], arrays[1], 'two stride arrays bytes ' + str(ident), 'array_bytes')
                support_bytes, valid_bytes = arrays[0]
                require(set(support_bytes) <= {0, 1} and set(valid_bytes) <= {0, 1},
                        'canonical boolean bytes ' + str(ident), 'array_bytes')
                width = len(valid_bytes)
                valid_positions = {i for i, value in enumerate(valid_bytes) if value}
                valid_bits = int.from_bytes(valid_bytes, 'little')
                denominator = len(valid_positions)
                require(denominator > 0, 'Nonempty valid ' + str(ident), 'denominator')
                exact(valid_bits.bit_count(), denominator, 'set/bit denominator', 'denominator')
                rows_bytes = [support_bytes[i * width:(i + 1) * width] for i in range(20)]
                bits = [int.from_bytes(raw, 'little') for raw in rows_bytes]
                sets = [{i for i, value in enumerate(raw) if value} for raw in rows_bytes]
                fractions = {}
                current = {}
                for name, ids in selected.items():
                    require(len(ids) == len(set(ids)) == 4 and set(ids) <= set(pools[name]),
                            'current legal ' + str(ident), 'domain')
                    numerator = score(bits, valid_bits, ids)
                    exact(numerator, len(set.union(*(sets[i] for i in ids)) & valid_positions),
                          'current independent set count', 'second_method')
                    current[name] = dict(selected=ids, supported_pixels=numerator,
                                         valid_pixels=denominator, support=numerator / denominator)
                    exact(run_row['current'][name], current[name], 'current record ' + str(ident), 'current_score')
                    for field in ('supported_pixels', 'valid_pixels', 'support'):
                        exact(current[name][field], current_source[name][field], 'S12 current ' + field, 'current_score')
                    fractions[name + '_current'] = Fraction(numerator, denominator)
                oracle, pool_counts = {}, {}
                for name, pool in pools.items():
                    size = 20 if name == 'all20' else 14
                    exact(len(pool), size, 'pool size', 'domain')
                    exact(len(set(pool)), size, 'pool unique', 'domain')
                    require(all(type(i) is int and 0 <= i < 20 for i in pool), 'pool IDs', 'domain')
                    best, winner, ties, count = -1, None, 0, 0
                    combo_sha = hashlib.sha256()
                    for combo in combos(pool):
                        numerator = score(bits, valid_bits, combo)
                        count += 1
                        combo_sha.update((','.join(str(i) for i in combo) + '\n').encode('ascii'))
                        trace.write(f'{stage},{block},{query},{name},{combo[0]},{combo[1]},{combo[2]},{combo[3]},{numerator},{denominator}\n')
                        if numerator > best:
                            best, winner, ties = numerator, combo, 1
                        elif numerator == best:
                            winner, ties = min(winner, combo), ties + 1
                    exact(count, math.comb(size, 4), 'enumerated pool count', 'combination_count')
                    total += count
                    pool_counts[name] = count
                    expected_seal['combo_hashes'][name] = combo_sha.hexdigest()
                    oracle[name] = dict(selected=list(winner), supported_pixels=best,
                                        valid_pixels=denominator, support=best / denominator,
                                        optimal_combination_count=ties)
                    exact(oracle[name], run_row['oracle'][name], 'oracle record ' + str(ident) + name, 'oracle_score')
                    exact(best, len(set.union(*(sets[i] for i in winner)) & valid_positions),
                          'oracle independent set count', 'second_method')
                    fractions[name + '_oracle'] = Fraction(best, denominator)
                exact(expected_seal, sealed_row, 'all sealed fields ' + str(ident), 'seal')
                for field, value in expected_seal.items():
                    exact(run_row[field], value, 'output carries seal ' + field, 'seal')
                for name in selected:
                    gap = 100 * (fractions[name + '_oracle'] - fractions[name + '_current'])
                    derived(run_row['headroom_pp'][name], gap, 'within-pool headroom')
                    derived(run_row[f'all20_over_{name}_pp'],
                            100 * (fractions['all20_oracle'] - fractions[name + '_current']), 'all20 headroom')
                    require(oracle[name]['supported_pixels'] >= current[name]['supported_pixels'],
                            'oracle dominates current', 'upper_bound')
                    require(oracle['all20']['supported_pixels'] >= oracle[name]['supported_pixels'],
                            'all20 dominates subset pool', 'upper_bound')
                independent.append(dict(**expected_seal, current=current, oracle=oracle,
                                        enumerated_combinations=pool_counts,
                                        exact_fractions={name: str(value) for name, value in fractions.items()}))
        exact(total, 164328, 'actual enumerated total', 'combination_count')
        exact(total, metadata['oracle_combinations_scored'], 'metadata scored count', 'combination_count')
        exact(total, metadata['oracle_combinations_planned'], 'metadata planned count', 'combination_count')
        exact(npz_count, 48, 'opened NPZ files', 'array_header')
        summary = read(RUN / 'summary.json')
        exact(summary['unique_seen_queries'], 24, 'summary query count', 'summary')
        specs = [('S7_development_4', 'S7', (0,), 4), ('S7_test_8', 'S7', (1, 2), 8),
                 ('S8_test_12', 'S8', (0, 1, 2), 12)]
        exact([row['stratum'] for row in summary['strata']], [spec[0] for spec in specs], 'strata', 'summary')
        strata = []
        for saved, (label, stage, blocks, size) in zip(summary['strata'], specs):
            rows = [row for row in independent if row['stage'] == stage and row['block'] in blocks]
            exact(len(rows), size, label + ' size', 'summary')
            exact(saved['n_queries'], size, label + ' saved size', 'summary')
            means = {name: sum((Fraction(row['exact_fractions'][name]) for row in rows), Fraction()) / size
                     for name in rows[0]['exact_fractions']}
            values = {name + '_mean': value for name, value in means.items()}
            for name in ('geometry14', 'pose14'):
                values[name + '_headroom_mean_pp'] = 100 * (means[name + '_oracle'] - means[name + '_current'])
            exact(set(saved), {'stratum', 'n_queries'} | set(values), label + ' field set', 'summary')
            for name, value in values.items():
                derived(saved[name], value, label + '/' + name)
            strata.append(dict(stratum=label, n_queries=size,
                               **{name: float(value) for name, value in values.items()},
                               exact_fraction_means={name: str(value) for name, value in values.items()}))
        write(output / 'independent_records.json', independent)
        write(output / 'independent_summary.json', dict(strata=strata, unique_seen_queries=24))
        # Reopen trace: the new audit trace records actual loops rather than a copied planned counter.
        reopened_count = 0
        with gzip.open(output / 'all_combination_scores.csv.gz', 'rt', encoding='utf-8') as trace:
            next(trace)
            for line in trace:
                require(len(line.rstrip('\n').split(',')) == 10, 'trace row width', 'saved_trace')
                reopened_count += 1
        exact(reopened_count, total, 'saved trace has every actual combination', 'saved_trace')
        after = identity(protected)
        exact(after, before, 'all original sources/inputs/results unchanged during audit', 'post_integrity')
        write(output / 'post_audit_input_sha256.json', after)
        verification.update(status='PASS', protocol_status='DISCLOSED_DEVIATION',
                            verdict='PASS_NUMERICAL_WITH_PROTOCOL_DEVIATION_AND_SCOPE_LIMITATIONS',
                            completed_utc=now(), elapsed_seconds=time.monotonic() - start,
                            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024),
                            counts=dict(COUNTS), check_count=sum(COUNTS.values()),
                            max_derived_float_difference=MAX_DIFFERENCE,
                            arrays_opened=npz_count, actual_combinations_enumerated=total,
                            original_inputs=52, original_sources=4,
                            all_original_files_unchanged=True,
                            supplementary_s12_validation='Current S12 summary, metadata and records match the prior audit manifest; S12 audit PASS. This is post-hoc, not a repaired original freeze.',
                            protocol_deviations=[
                                'Design step 1 says to bind S12 summary and independent audit; actual 52-input map does not directly bind them.'],
                            limitations=[
                                'Oracle enumerates all four-subsets and does not enforce NMS; headroom includes relaxation of that constraint.',
                                'Known GT-derived support and seen queries; no deployable selector, novelty, generalization, video or timing claim.',
                                'S7 development 4, S7 test 8, S8 test 12 are related queries in two scenes, not independent scene replications.',
                                'Recorded scoring marker is written before array access, not an OS access measurement.',
                                'S13 originally saves only optimum aggregates, not every combination score. This audit saves all its own 164328 scores.',
                                'Current source hashes match the run-bound freeze; without an S13 source archive/after-source hash, transient historical mutations cannot be ruled out from file hashes alone.',
                                'The S13 original metadata omit Python/NumPy versions; environment here describes this audit only.',
                                'This audit reopens old saved support/valid arrays; it does not rederive them from raw images or GT poses.'
                            ])
        write(output / 'verification.json', verification)
        write(output / 'audit_output_sha256.json',
              {p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()})
        print(json.dumps({key: verification[key] for key in ('status', 'protocol_status', 'actual_combinations_enumerated', 'check_count', 'completed_utc')}, ensure_ascii=False))
    except Exception as error:
        verification.update(status='FAIL', failed_utc=now(), error_type=type(error).__name__, error=str(error),
                            counts=dict(COUNTS), check_count=sum(COUNTS.values()))
        write(output / 'verification.json', verification)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results/S13_independent_audit')
    main(parser.parse_args().output.resolve())
