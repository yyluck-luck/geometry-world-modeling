#!/usr/bin/env python3
"""Static regression for S103 predictor input/write boundaries; no model import."""
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PREDICTOR = ROOT / "predictor_s103.py"
VALIDATOR = ROOT.parent / "S102_gate0_tum" / "validate_gate0_v2.py"


def main():
    source = PREDICTOR.read_text()
    tree = ast.parse(source, filename=str(PREDICTOR))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    mutating_names = []
    for call in calls:
        func = call.func
        if isinstance(func, ast.Attribute) and func.attr in {"mkdir", "symlink_to"}:
            mutating_names.append(func.attr)
    checks = [
        ["predictor compiles", True],
        ["no runtime mkdir or symlink creation", not mutating_names],
        ["camera intrinsics read through hashed read helper",
         "read(by_role['camera_intrinsics'][0]['file'],'camera_intrinsics')" in source],
        ["manifest declares four scientific roles",
         "['history_rgb','history_pose','command_camera','camera_intrinsics']" in source],
        ["predictor requires 13 bound records", "require(len(records)==13" in source],
        ["VAE loads from read-only weights root", "orig_vae(str(WEIGHTS)" in source],
        ["history and query intrinsics share one resize/crop helper",
         "k=model_grid_K(K0)" in source and "query_K=model_grid_K(K0)" in source],
        ["intrinsics are not globally scaled or cropped twice",
         "K0*1.2" not in source and "all_K[:,0,2]-=96" not in source],
        ["homogeneous row and common principal point are runtime-guarded",
         "history/query K homogeneous rows differ" in source
         and "history/query K principal points differ" in source
         and "history/query transformed intrinsics differ" in source],
        ["validator explicitly permits and requires camera intrinsics",
         "STATIC_PREDICTOR_ROLES = {'camera_intrinsics'}" in VALIDATOR.read_text()
         and "exactly one hashed camera_intrinsics input is required" in VALIDATOR.read_text()],
    ]
    result = {
        "schema": "s103-predictor-static-contract-regression-v1",
        "scope": "source-only; no model, data, future outcome, or GPU",
        "checks": checks,
        "status": "PASS" if all(row[1] for row in checks) else "FAIL",
        "mutating_calls_found": mutating_names,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
