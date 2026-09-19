#!/usr/bin/env python3
"""Static, no-import audit of the VMem post-selection intervention boundary."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


EXPECTED_PIPELINE_SHA256 = "90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e"
REQUIRED_CONTEXT_KEYS = {
    "context_c2ws",
    "context_latents",
    "context_encoder_embeddings",
    "context_Ks",
    "context_time_indices",
}
REQUIRED_COND_KEYS = {"crossattn", "replace", "concat", "dense_vector"}
LIVE_STATE_FIELDS = {
    "latents",
    "encoder_embeddings",
    "Ks",
    "surfels",
    "surfel_Ks",
    "surfel_depths",
    "surfel_to_timestep",
    "pil_frames",
    "c2ws",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def method(class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
    matches = [n for n in class_node.body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one {name}, found {len(matches)}")
    return matches[0]


def string_dict_keys(node: ast.AST) -> set[str]:
    keys: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Dict):
            for key in child.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.add(key.value)
    return keys


def self_assignments(node: ast.AST) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for child in ast.walk(node):
        if not isinstance(child, (ast.Assign, ast.AnnAssign)):
            continue
        targets = child.targets if isinstance(child, ast.Assign) else [child.target]
        for target in targets:
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                result.setdefault(target.attr, []).append(child.lineno)
    return result


def calls(node: ast.AST, name: str) -> list[ast.Call]:
    found: list[ast.Call] = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Attribute) and func.attr == name:
            found.append(child)
        elif isinstance(func, ast.Name) and func.id == name:
            found.append(child)
    return found


def has_global_embedding_mean(node: ast.AST) -> tuple[bool, list[int]]:
    lines: list[int] = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if not (isinstance(func, ast.Attribute) and func.attr == "mean"):
            continue
        if not child.args or not isinstance(child.args[0], ast.Name):
            continue
        if child.args[0].id != "encoder_embeddings":
            continue
        dim_one = any(
            kw.arg == "dim" and isinstance(kw.value, ast.Constant) and kw.value.value == 0
            for kw in child.keywords
        )
        if dim_one:
            lines.append(child.lineno)
    return bool(lines), lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_path = args.source.resolve()
    payload = source_path.read_bytes()
    digest = sha256_bytes(payload)
    if digest != EXPECTED_PIPELINE_SHA256:
        raise AssertionError(f"pipeline SHA changed: {digest}")

    text = payload.decode("utf-8")
    tree = ast.parse(text, filename=str(source_path))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    candidates = [
        cls
        for cls in classes
        if {"get_context_info", "get_cond", "reset"}.issubset(
            {n.name for n in cls.body if isinstance(n, ast.FunctionDef)}
        )
    ]
    if len(candidates) != 1:
        raise AssertionError(f"expected one pipeline class, found {len(candidates)}")
    cls = candidates[0]

    get_context = method(cls, "get_context_info")
    get_cond = method(cls, "get_cond")
    reset = method(cls, "reset")
    render = method(cls, "render_surfels_to_image")
    process = method(cls, "process_retrieved_spatial_information")

    context_keys = string_dict_keys(get_context)
    cond_keys = string_dict_keys(get_cond)
    reset_fields = set(self_assignments(reset))
    missing_live_reset = sorted(LIVE_STATE_FIELDS - reset_fields)
    global_mean, global_mean_lines = has_global_embedding_mean(get_cond)

    trajectory_candidates: list[ast.FunctionDef] = []
    for node in cls.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if calls(node, "get_context_info") and calls(node, "get_cond"):
            trajectory_candidates.append(node)
    if len(trajectory_candidates) != 1:
        raise AssertionError(
            f"expected one consumer method, found {[n.name for n in trajectory_candidates]}"
        )
    consumer = trajectory_candidates[0]
    context_call_lines = [n.lineno for n in calls(consumer, "get_context_info")]
    cond_call_lines = [n.lineno for n in calls(consumer, "get_cond")]

    checks = {
        "exact_pipeline_sha": digest == EXPECTED_PIPELINE_SHA256,
        "context_keys_present": REQUIRED_CONTEXT_KEYS.issubset(context_keys),
        "context_does_not_return_support": not bool(
            {"support", "source_support", "surfel_index_map"} & context_keys
        ),
        "render_exposes_surfel_index_map": "surfel_index_map" in string_dict_keys(render),
        "retrieval_uses_surfel_to_timestep": any(
            isinstance(n, ast.Attribute) and n.attr == "surfel_to_timestep"
            for n in ast.walk(process)
        ),
        "global_embedding_mean_dim0": global_mean,
        "condition_has_required_paths": REQUIRED_COND_KEYS.issubset(cond_keys),
        "single_post_selection_pre_cond_boundary": len(context_call_lines) == 1
        and len(cond_call_lines) == 1
        and context_call_lines[0] < cond_call_lines[0],
        "current_reset_misses_live_state": bool(missing_live_reset),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise AssertionError(f"source audit failed: {failed}")

    report = {
        "schema": "s48_post_selection_hook_source_audit_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "static_source_no_import_no_model",
        "source": str(source_path),
        "source_sha256": digest,
        "pipeline_class": cls.name,
        "checks": checks,
        "evidence": {
            "context_return_keys": sorted(context_keys & REQUIRED_CONTEXT_KEYS),
            "context_function_lines": [get_context.lineno, get_context.end_lineno],
            "get_cond_function_lines": [get_cond.lineno, get_cond.end_lineno],
            "global_embedding_mean_lines": global_mean_lines,
            "consumer_method": consumer.name,
            "get_context_info_call_lines": context_call_lines,
            "get_cond_call_lines": cond_call_lines,
            "reset_function_lines": [reset.lineno, reset.end_lineno],
            "reset_fields": sorted(reset_fields),
            "live_fields_missing_from_reset": missing_live_reset,
            "required_condition_paths": sorted(REQUIRED_COND_KEYS),
        },
        "interpretation": {
            "hook_status": "SOURCE_BOUNDARY_EXISTS_BUT_SUPPORT_API_MISSING",
            "consumer_asymmetry_hypothesis": (
                "slotwise latent replace is preserved while source embeddings are globally averaged"
            ),
            "execution_authorization": "NONE",
            "novelty_authorization": "NONE",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

