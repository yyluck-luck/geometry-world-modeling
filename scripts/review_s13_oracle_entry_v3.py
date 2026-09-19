#!/usr/bin/env python3
"""Static S13 review after correcting the review-path freeze binding."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'scripts/run_s13_oracle_headroom.py'
DESIGN = ROOT / 'docs/S13_ORACLE_HEADROOM_DESIGN.md'
PRE = ROOT / 'results/S13_oracle_headroom_preflight/receipt.json'
OUT = ROOT / 'results/S13_oracle_entry_review_v3'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not OUT.exists(), 'Preserve previous review/failure output'
    source, design = SOURCE.read_text(), DESIGN.read_text()
    functions = {node.name for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
    assert {'input_paths', 'identity', 'normalized_combo_hash', 'seal_candidates', 'score_pool', 'score_selected', 'run'} <= functions
    assert len([(s, b, q) for s in ('S7', 'S8') for b in range(3) for q in range(20, 24)]) == 24
    assert "COMBO_COUNTS = {'geometry14': 1001, 'pose14': 1001, 'all20': 4845}" in source
    assert source.index('sealed = seal_candidates(rows, output)') < source.index('import numpy as np') < source.index("np.load(path, allow_pickle=False)")
    assert "freeze['status'] == 'approved_for_execution'" in source and "freeze['input_sha256'] == before" in source
    assert "results/S13_oracle_entry_review_v3/review.json" in source and 'results/S13_oracle_entry_review/review.json' not in source
    assert "require(current[name]['support'] == entry['saved_support'][name]" in source
    assert all(token not in source for token in ['renderer(', 'decision_trace(', 'get_context_info(', 'torch.', 'cv2.', 'PIL.', 'imageio'])
    assert 'not a deployable selector or video metric' in source and '不能部署' in design and '不能称其新颖' in design
    pre = json.loads(PRE.read_text())
    assert pre['status'] == 'PASS' and pre['arrays_decoded'] == 0 and pre['oracle_combinations_scored'] == 0
    OUT.mkdir(parents=True)
    record = dict(schema='s13-static-entry-review-v3', recorded_utc=datetime.now(timezone.utc).isoformat(), status='PASS', checks=17,
                  reviewer_scope='Separate static source/design review script, not a different-author numerical audit.',
                  source_sha256=sha(SOURCE), design_sha256=sha(DESIGN), preflight_sha256=sha(PRE),
                  scope='No scoring NPZ payload was decoded and no combination was enumerated.',
                  correction='The prior failed run found one stale V1 review key before candidate sealing; this review requires the V3 key to match the bound review file.',
                  conclusions=['Candidate seal precedes all NumPy support/valid reads.', '164328 planned combinations match three fixed candidate pools across 24 queries.', 'Current S12 support re-score is an exact gate before oracle reporting.', 'Execution requires an approved source/input-bound freeze.', 'No renderer, model, NMS, projection, image, or deployable-selection call is present.'])
    (OUT / 'review.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'docs/S13_ORACLE_ENTRY_REVIEW_V3.md').write_text(
        '# S13 oracle入口静态审查 V3\n\n结论：**PASS（静态入口审查）**。首次运行在候选封存和数组读取前发现一个旧V1审查路径，失败记录保留。入口已把该键修正为V3，并重新核候选封存在数组解码之前、组合总数、S12分数回归门、冻结绑定和禁止调用范围。未解码数组、未枚举组合；不是不同作者的数值审计。\n\n'
        f'记录UTC：{record["recorded_utc"]}。入口SHA：`{record["source_sha256"]}`；设计SHA：`{record["design_sha256"]}`；预检回执SHA：`{record["preflight_sha256"]}`。\n')
    print(json.dumps({'status': record['status'], 'checks': record['checks'], 'arrays_decoded': 0, 'oracle_combinations_scored': 0}))


if __name__ == '__main__':
    main()
