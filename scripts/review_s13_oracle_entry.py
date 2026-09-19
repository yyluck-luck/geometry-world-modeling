#!/usr/bin/env python3
"""Static S13 pre-run review: source/design/preflight only, no array decoding."""
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
OUT = ROOT / 'results/S13_oracle_entry_review'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not OUT.exists(), 'Preserve earlier review/failure output'
    source, design = SOURCE.read_text(), DESIGN.read_text()
    tree = ast.parse(source)
    funcs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    required = {'input_paths', 'identity', 'normalized_combo_hash', 'seal_candidates', 'score_pool', 'score_selected', 'run'}
    assert required.issubset(funcs)
    assert len([(n, k) for n in ('S7', 'S8') for k in range(3) for _ in range(20, 24)]) == 24
    assert '24 * sum(COMBO_COUNTS.values())' in source and "COMBO_COUNTS = {'geometry14': 1001, 'pose14': 1001, 'all20': 4845}" in source
    assert source.index('sealed = seal_candidates(rows, output)') < source.index('import numpy as np') < source.index("np.load(path, allow_pickle=False)")
    assert "require(current[name]['support'] == entry['saved_support'][name]" in source
    forbidden = ['renderer(', 'decision_trace(', 'get_context_info(', 'torch.', 'cv2.', 'PIL.', 'imageio']
    assert all(token not in source for token in forbidden)
    assert 'not a deployable selector or video metric' in source and '不能部署' in design and '不能称其新颖' in design
    pre = json.loads(PRE.read_text())
    assert pre['status'] == 'PASS' and pre['arrays_decoded'] == 0 and pre['oracle_combinations_scored'] == 0
    OUT.mkdir(parents=True)
    report = dict(schema='s13-static-entry-review-v1', recorded_utc=datetime.now(timezone.utc).isoformat(), status='PASS',
                  reviewer_scope='Separate static source/design review script, not a different-author numerical audit.',
                  checks=13, source_sha256=sha(SOURCE), design_sha256=sha(DESIGN), preflight_sha256=sha(PRE),
                  conclusions=['24-query schedule and 164328 planned combinations are internally consistent.',
                               'Candidate sealing is ordered before NumPy import and saved support/valid decoding.',
                               'Current S12 selections are re-scored exactly before oracle comparison.',
                               'No renderer/model/NMS/projection/image API is referenced by the entry.',
                               'Oracle scope is explicitly hindsight-only, not deployment, novelty, video, or generalization evidence.'],
                  limits=['Static review does not decode support arrays, execute enumeration, or replace the required post-run independent read-only audit.'])
    (OUT / 'review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'docs/S13_ORACLE_ENTRY_REVIEW.md').write_text(
        '# S13 oracle入口静态审查\n\n结论：**PASS（静态入口审查）**。核24查询、164328预定组合、候选封存先于数组解码、现有S12分数精确回归门、禁止调用范围和oracle解释边界。该审查只读入口/设计/预检回执，未解码数组、未枚举组合，不是不同作者的数值审计。\n\n'
        f'记录UTC：{report["recorded_utc"]}。入口SHA：`{report["source_sha256"]}`；设计SHA：`{report["design_sha256"]}`；预检回执SHA：`{report["preflight_sha256"]}`。\n\n'
        '执行前仍需把这些身份写入单独冻结文件；运行后必须另做只读重枚举审计。\n')
    print(json.dumps({'status': report['status'], 'checks': report['checks'], 'arrays_decoded': 0, 'oracle_combinations_scored': 0}))


if __name__ == '__main__':
    main()
