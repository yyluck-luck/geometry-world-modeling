#!/usr/bin/env python3
"""Header-only S13 oracle prerequisite inspection; never decodes support arrays."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
S12 = ROOT / 'results/S12_matched_budget'
OUT = ROOT / 'results/S13_oracle_headroom_preflight'
DESIGN = ROOT / 'docs/S13_ORACLE_HEADROOM_DESIGN.md'
EXPECTED_RECORDS = '29bb3fb2b8676038a08d44ceddf2a55d8d7bff240bba277cae07053f4175f128'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def npy_header(package: zipfile.ZipFile, name: str) -> dict:
    """Read only the .npy header inside an NPZ member, never its array payload."""
    with package.open(name) as handle:
        assert handle.read(6) == b'\x93NUMPY'
        major, minor = handle.read(2)
        width = 2 if major == 1 else 4
        length = int.from_bytes(handle.read(width), 'little')
        header = ast.literal_eval(handle.read(length).decode('latin1'))
    assert set(header) == {'descr', 'fortran_order', 'shape'}
    assert header['descr'] == '|b1' and header['fortran_order'] is False
    return dict(dtype=header['descr'], shape=list(header['shape']))


def main() -> None:
    assert not OUT.exists(), 'Preserve previous preflight/failure directory'
    assert S12.is_dir() and DESIGN.is_file()
    metadata = json.loads((S12 / 'run_metadata.json').read_text())
    records_path = S12 / 'records.json'
    assert metadata['status'] == 'completed'
    assert sha(records_path) == EXPECTED_RECORDS
    records = json.loads(records_path.read_text())
    main_rows = [r for r in records if r['main_comparison']]
    assert len(records) == 192 and len(main_rows) == 24
    observed = set()
    checks = 0
    for row in main_rows:
        ident = tuple(row[k] for k in ('stage', 'block', 'query'))
        assert ident not in observed
        observed.add(ident)
        assert row['stride'] == 8 and row['arm'] == 'A0P0'
        for pool_name, chosen in [
            ('geometry14_candidates', row['old_readouts']['official']['selected']),
            ('pose14_ranked_candidates', row['pose14']['selected']),
        ]:
            pool = row[pool_name]
            assert len(pool) == len(set(pool)) == 14
            assert all(isinstance(i, int) and 0 <= i < 20 for i in pool)
            assert len(chosen) == len(set(chosen)) == 4 and set(chosen).issubset(pool)
            checks += 5
    headers = []
    for stage, block, query in sorted(observed):
        for stride in (8, 12):
            path = ROOT / ('results/S7_event_replay' if stage == 'S7' else 'results/S8_event_replay_v2') / f'block{block}_stride{stride}' / f'query{query}_scoring.npz'
            assert path.is_file() and not path.is_symlink()
            with zipfile.ZipFile(path) as package:
                # The saved file also contains target/common/map fields.  This
                # preflight opens only the two declared S13 fields' headers.
                assert {'support.npy', 'valid.npy'}.issubset(package.namelist())
                support, valid = npy_header(package, 'support.npy'), npy_header(package, 'valid.npy')
            assert support['shape'] == [20, 112, 112] and valid['shape'] == [112, 112]
            headers.append(dict(stage=stage, block=block, query=query, stride=stride,
                                path=str(path.relative_to(ROOT)), support=support, valid=valid,
                                sha256=sha(path)))
            checks += 6
    assert len(headers) == 48
    OUT.mkdir(parents=True)
    receipt = dict(schema='s13-oracle-prerequisites-v1', recorded_utc=datetime.now(timezone.utc).isoformat(),
                   status='PASS', scope='Header-only input/candidate inspection; support/valid payloads not decoded and no oracle score computed.',
                   records_sha256=sha(records_path), design_sha256=sha(DESIGN), main_rows=24,
                   candidate_pools_checked=48, scoring_npz_headers=48, explicit_checks=checks,
                   arrays_decoded=0, oracle_combinations_scored=0, renderer_calls=0, model_calls=0,
                   headers=headers)
    (OUT / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('status', 'main_rows', 'candidate_pools_checked', 'scoring_npz_headers', 'explicit_checks', 'arrays_decoded', 'oracle_combinations_scored')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
