#!/usr/bin/env python3
"""Frozen S13 hindsight support-headroom diagnostic on S12's saved queries.

This is an oracle analysis: support arrays are deliberately used only after
candidate pools are sealed.  It is not a deployable selector or video metric.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import resource
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
S12 = ROOT / 'results/S12_matched_budget'
RUNS = {'S7': ROOT / 'results/S7_event_replay', 'S8': ROOT / 'results/S8_event_replay_v2'}
DESIGN = ROOT / 'docs/S13_ORACLE_HEADROOM_DESIGN.md'
PRE = ROOT / 'results/S13_oracle_headroom_preflight/receipt.json'
REVIEW = ROOT / 'results/S13_oracle_entry_review_v3/review.json'
FREEZE = ROOT / 'docs/S13_ORACLE_EXECUTION_FREEZE.json'
EXPECTED_RECORDS = '29bb3fb2b8676038a08d44ceddf2a55d8d7bff240bba277cae07053f4175f128'
SCHEDULE = [(stage, block, query) for stage in ('S7', 'S8') for block in range(3) for query in range(20, 24)]
COMBO_COUNTS = {'geometry14': 1001, 'pose14': 1001, 'all20': 4845}
WALL_SECONDS, PEAK_BYTES = 600, 16 * 1024**3


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for part in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(part)
    return digest.hexdigest()


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def peak_rss() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == 'darwin' else value * 1024


def input_paths() -> list[Path]:
    paths = [S12 / 'run_metadata.json', S12 / 'records.json', DESIGN, PRE]
    for stage, block, query in SCHEDULE:
        for stride in (8, 12):
            paths.append(RUNS[stage] / f'block{block}_stride{stride}' / f'query{query}_scoring.npz')
    return paths


def identity(paths: list[Path]) -> dict[str, str]:
    result = {}
    for path in paths:
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT), f'Invalid input {path}')
        name = str(path.relative_to(ROOT))
        require(name not in result, f'Duplicate input {name}')
        result[name] = sha(path)
    return result


def normalized_combo_hash(pool: list[int]) -> tuple[int, str]:
    digest, count = hashlib.sha256(), 0
    for combo in itertools.combinations(sorted(pool), 4):
        digest.update((','.join(map(str, combo)) + '\n').encode())
        count += 1
    return count, digest.hexdigest()


def seal_candidates(rows: list[dict], output: Path) -> dict[tuple[str, int, int], dict]:
    main = [row for row in rows if row['main_comparison']]
    require(len(main) == 24, 'Expected exactly 24 S12 main rows')
    sealed, seen = {}, set()
    for row in main:
        key = tuple(row[k] for k in ('stage', 'block', 'query'))
        require(key in SCHEDULE and key not in seen, f'Invalid/duplicate query {key}')
        seen.add(key)
        pools = {'geometry14': sorted(row['geometry14_candidates']),
                 'pose14': sorted(row['pose14_ranked_candidates']), 'all20': list(range(20))}
        selected = {'geometry14': sorted(row['old_readouts']['official']['selected']),
                    'pose14': sorted(row['pose14']['selected'])}
        for name, pool in pools.items():
            expected = 20 if name == 'all20' else 14
            require(len(pool) == len(set(pool)) == expected and all(isinstance(i, int) and 0 <= i < 20 for i in pool),
                    f'Bad {name} pool {key}')
            count, digest = normalized_combo_hash(pool)
            require(count == COMBO_COUNTS[name], f'Bad combination count {key}/{name}')
            pools[name] = pool
            row.setdefault('_combo_hashes', {})[name] = digest
        for name, ids in selected.items():
            require(len(ids) == len(set(ids)) == 4 and set(ids).issubset(pools[name]), f'Bad saved selected IDs {key}/{name}')
        sealed[key] = dict(stage=key[0], block=key[1], query=key[2], split=row['split'],
                           pools=pools, selected=selected, combo_hashes=row['_combo_hashes'],
                           saved_support={'geometry14': row['old_readouts']['official']['support'], 'pose14': row['pose14']['support']})
    require(set(sealed) == set(SCHEDULE), 'Incomplete schedule')
    manifest = dict(schema='s13-candidate-seal-v1', sealed_utc=utc(), queries=[sealed[k] for k in SCHEDULE],
                    scope='Candidate domains and static combination identity only; no support/valid payload decoded.')
    save(output / 'candidate_seal.json', manifest)
    return sealed


def score_pool(support, valid, pool: list[int]) -> dict:
    best_pixels, best, ties = -1, None, 0
    for combo in itertools.combinations(pool, 4):
        pixels = int((support[list(combo)].any(axis=0) & valid).sum())
        if pixels > best_pixels:
            best_pixels, best, ties = pixels, combo, 1
        elif pixels == best_pixels:
            ties += 1
    denominator = int(valid.sum())
    return dict(selected=list(best), supported_pixels=best_pixels, valid_pixels=denominator,
                support=best_pixels / denominator, optimal_combination_count=ties)


def score_selected(support, valid, ids: list[int]) -> dict:
    pixels = int((support[ids].any(axis=0) & valid).sum())
    denominator = int(valid.sum())
    return dict(selected=ids, supported_pixels=pixels, valid_pixels=denominator, support=pixels / denominator)


def run(args) -> None:
    output = args.output.resolve()
    require(not output.exists() and not output.is_symlink(), 'Output already exists; preserve earlier runs')
    start = time.monotonic()
    output.mkdir(parents=True)
    metadata = dict(schema='s13-oracle-headroom-run-v1', status='running', started_utc=utc(),
                    candidate_sealed_utc=None, first_scoring_decode_utc=None, completed_utc=None,
                    oracle_combinations_planned=24 * sum(COMBO_COUNTS.values()), renderer_calls=0, model_calls=0,
                    raw_pixels_decoded=False, gt_pose_values_parsed=False, performance_timing=False,
                    scope='Hindsight support upper-bound diagnostic on 24 seen S12 queries; not deployable selection or video evaluation.')
    save(output / 'run_metadata.json', metadata)
    try:
        paths, before = input_paths(), identity(input_paths())
        require(before['results/S12_matched_budget/records.json'] == EXPECTED_RECORDS, 'Unexpected S12 records')
        require(json.loads((S12 / 'run_metadata.json').read_text())['status'] == 'completed', 'S12 incomplete')
        require(json.loads(PRE.read_text())['status'] == 'PASS', 'S13 preflight incomplete')
        require(REVIEW.is_file() and FREEZE.is_file(), 'Missing static review or execution freeze')
        freeze = json.loads(FREEZE.read_text())
        require(freeze['status'] == 'approved_for_execution', 'S13 execution is not approved')
        require(freeze['sources'] == {
            'scripts/run_s13_oracle_headroom.py': sha(Path(__file__)),
            'docs/S13_ORACLE_HEADROOM_DESIGN.md': sha(DESIGN),
            'results/S13_oracle_headroom_preflight/receipt.json': sha(PRE),
            'results/S13_oracle_entry_review_v3/review.json': sha(REVIEW),
        }, 'Frozen S13 sources or reviews changed')
        require(freeze['input_sha256'] == before, 'Frozen S13 inputs changed')
        rows = json.loads((S12 / 'records.json').read_text())
        sealed = seal_candidates(rows, output)
        metadata['candidate_sealed_utc'] = json.loads((output / 'candidate_seal.json').read_text())['sealed_utc']
        metadata['candidate_seal_sha256'] = sha(output / 'candidate_seal.json')
        metadata['input_sha256'] = before
        metadata['execution_freeze_sha256'] = sha(FREEZE)
        metadata['phase'] = 'saved_support_oracle_scoring'
        save(output / 'run_metadata.json', metadata)
        import numpy as np
        results = []
        for stage, block, query in SCHEDULE:
            key, entry = (stage, block, query), sealed[stage, block, query]
            arrays = []
            for stride in (8, 12):
                path = RUNS[stage] / f'block{block}_stride{stride}' / f'query{query}_scoring.npz'
                with np.load(path, allow_pickle=False) as package:
                    if metadata['first_scoring_decode_utc'] is None:
                        metadata['first_scoring_decode_utc'] = utc(); save(output / 'run_metadata.json', metadata)
                    arrays.append((package['support'], package['valid']))
            (support, valid), (support12, valid12) = arrays
            require(support.dtype == valid.dtype == np.dtype('bool') and support.shape == (20, 112, 112) and valid.shape == (112, 112) and bool(valid.any()), 'Bad scoring arrays')
            require(support.tobytes() == support12.tobytes() and valid.tobytes() == valid12.tobytes(), 'Stride scoring identity differs')
            current = {name: score_selected(support, valid, ids) for name, ids in entry['selected'].items()}
            for name in current:
                require(current[name]['support'] == entry['saved_support'][name], f'S12 current score differs {key}/{name}')
            oracle = {name: score_pool(support, valid, pool) for name, pool in entry['pools'].items()}
            results.append(dict(**entry, current=current, oracle=oracle,
                headroom_pp={name: 100 * (oracle[name]['support'] - current[name]['support']) for name in current},
                all20_over_geometry14_pp=100 * (oracle['all20']['support'] - current['geometry14']['support']),
                all20_over_pose14_pp=100 * (oracle['all20']['support'] - current['pose14']['support'])))
            require(time.monotonic() - start <= WALL_SECONDS and peak_rss() <= PEAK_BYTES, 'Soft resource budget exceeded')
        def aggregate(subset, label):
            require(subset, f'Empty stratum {label}')
            n = len(subset)
            return dict(stratum=label, n_queries=n,
                geometry14_current_mean= sum(x['current']['geometry14']['support'] for x in subset) / n,
                geometry14_oracle_mean= sum(x['oracle']['geometry14']['support'] for x in subset) / n,
                geometry14_headroom_mean_pp=sum(x['headroom_pp']['geometry14'] for x in subset) / n,
                pose14_current_mean=sum(x['current']['pose14']['support'] for x in subset) / n,
                pose14_oracle_mean=sum(x['oracle']['pose14']['support'] for x in subset) / n,
                pose14_headroom_mean_pp=sum(x['headroom_pp']['pose14'] for x in subset) / n,
                all20_oracle_mean=sum(x['oracle']['all20']['support'] for x in subset) / n)
        strata = [aggregate([x for x in results if x['stage'] == 'S7' and x['block'] == 0], 'S7_development_4'),
                  aggregate([x for x in results if x['stage'] == 'S7' and x['block'] in (1, 2)], 'S7_test_8'),
                  aggregate([x for x in results if x['stage'] == 'S8'], 'S8_test_12')]
        save(output / 'records.json', results)
        save(output / 'summary.json', dict(schema='s13-oracle-headroom-summary-v1', unique_seen_queries=24, strata=strata,
             scope='Descriptive hindsight upper bounds only; no pooled scene claim, p-value, speed, video-quality, novelty or deployable-method claim.'))
        require(identity(paths) == before, 'Input changed during run')
        metadata.update(status='completed', completed_utc=utc(), phase='completed', peak_rss_bytes=peak_rss(),
                        elapsed_seconds=time.monotonic() - start, oracle_combinations_scored=24 * sum(COMBO_COUNTS.values()))
        save(output / 'run_metadata.json', metadata)
        print(json.dumps(dict(status='completed', rows=len(results), strata=len(strata), **{k: metadata[k] for k in ('oracle_combinations_scored', 'peak_rss_bytes')})))
    except Exception as error:
        metadata.update(status='failed', failed_utc=utc(), error_type=type(error).__name__, error=str(error), peak_rss_bytes=peak_rss())
        save(output / 'run_metadata.json', metadata)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'results/S13_oracle_headroom')
    run(parser.parse_args())
