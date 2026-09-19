"""Build and audit S25 instrumentation. No torch, model, RGB, or GT loading."""
import ast
import copy
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import sys

from state_intervention_adapter import (
    ACTIONS, HERE, S_FIELDS, STATE_FIELDS, Checkpoint, _original_function, derive_function,
    select_branch_states, sha256, validate_checkpoint,
)

ROOT = HERE.parent.parent
SOURCE_ROOT = ROOT / "work/S22_filt_shared_precision/filt3r_shared_precision"
MANIFEST = ROOT / "work/S22_filt_shared_precision/source_manifest_v2.json"
MODEL = SOURCE_ROOT / "src/dust3r/model.py"
SIGNED_ROPE = ROOT / "scripts/cut3r_rope_compat.py"


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    started = datetime.now(timezone.utc).isoformat()
    manifest = json.loads(MANIFEST.read_text())
    identities = {str(MANIFEST): sha256(MANIFEST), str(SIGNED_ROPE): sha256(SIGNED_ROPE)}
    for row in manifest["files"]:
        path = SOURCE_ROOT / row["path"]
        actual = sha256(path)
        if actual != row["sha256"]:
            raise RuntimeError(f"Source manifest mismatch: {path}")
        identities[str(path)] = actual
    binding = {
        "schema": "s25-static-source-binding-v1",
        "model_source": str(MODEL),
        "signed_rope_helper": str(SIGNED_ROPE),
        "source_commit": manifest["commit"],
        "source_file_count": len(manifest["files"]),
        "identities": identities,
        "only_prior_controlled_adaptation": "CPU RoPE dtype FP16, inherited from S22; no S25 source mutations",
    }
    write_json("source_binding.json", binding)
    write_json("static_field_contract.json", {
        "schema": "s25-complete-loop-local-state-v1",
        "persistent_loop_fields": list(STATE_FIELDS),
        "freeze_s_group": list(S_FIELDS),
        "freeze_m_group": ["mem"],
        "structural_fields": ["state_pos", "init_state_feat", "init_mem", "prev_reset", "device"],
        "resume_controls": ["next_index", "frame_ids"],
        "next_index_rule": "type is int (not bool), >=1, equals len(complete unique prefix frame_ids)",
        "recomputed_and_verified": {"update_type": "filt3r", "need_attn_for_update": False},
        "pre_capture_anchor": "immediately after ress.append(res_cpu), before Kalman/state/M commit",
        "post_capture_anchor": "after _apply_stream_reset, prev_reset assignment, and _advance_prev_buffers",
        "current_head": "one computation shared by all four branch checkpoints; immutable evidence",
        "actions": {
            "normal": {"S_and_aux": "post", "M": "post"},
            "freeze_s_aux": {"S_and_aux": "pre", "M": "post"},
            "freeze_m": {"S_and_aux": "post", "M": "pre"},
            "freeze_all": {"S_and_aux": "pre", "M": "pre"},
        },
        "runtime_snapshot_beyond_loop_locals": ["named_buffers", "RoPE.cache", "PositionGetter.cache_positions",
                                               "torch_cpu_rng", "python_rng", "numpy_rng_if_loaded"],
        "guarded_runtime_identity": ["bound source SHAs", "signed RoPE function source and identity",
                                     "RoPE base=100 F0=1", "parameters identity/version", "effective hparams",
                                     "original per-module training flags", "audited method identities"],
        "unsupported": ["reset", "update suppression", "GPU", "batch size >1", "cross-process resume",
                        "active dropout/stochastic depth", "training BatchNorm", "external observation hooks",
                        "automatic event/horizon selection", "multi-frame write-freezing policy"],
        "upstream_output_only_not_checkpoint": ["ress", "all_state_args (always empty in lighter)"],
        "ephemeral_current_frame": ["feat_i", "new_state_feat", "new_mem", "dec", "head_input", "res", "res_cpu"],
        "numerical_compatibility": "NOT_RUN",
        "future_causal_forwards_from_rgb": "K+1+4H, K>=1 H>=1",
        "future_full_compatibility_plus_four_branches_forwards": "3(K+1)+6H",
        "experiment_decision": "pending parent natural-failure evidence gate and protocol freeze",
    })
    source = MODEL.read_text()
    module, proof = derive_function(source)
    original = ast.unparse(_original_function(source)) + "\n"
    derived = ast.unparse(module) + "\n"
    (HERE / "original_forward.normalized.py").write_text(original)
    (HERE / "derived_forward.py").write_text(derived)
    (HERE / "instrumentation.diff").write_text("".join(difflib.unified_diff(
        original.splitlines(keepends=True), derived.splitlines(keepends=True),
        fromfile="FILT3R/model.py::forward_recurrent_lighter (AST-normalized)",
        tofile="S25/derived_forward.py (AST-normalized)")))

    # Plain dict/list values test write-group semantics and alias isolation.
    # These are software tests, not model predictions or synthetic experiments.
    pre = {key: {"nested": [f"old:{key}"]} for key in STATE_FIELDS}
    post = {key: {"nested": [f"new:{key}"]} for key in STATE_FIELDS}
    pre["prev_reset"] = post["prev_reset"] = False
    before_pre, before_post = copy.deepcopy(pre), copy.deepcopy(post)
    branches = select_branch_states(pre, post)
    checks = {}
    for action, state in branches.items():
        for key in STATE_FIELDS:
            use_pre = ((action in ("freeze_s_aux", "freeze_all") and key in S_FIELDS)
                       or (action in ("freeze_m", "freeze_all") and key == "mem"))
            checks[f"{action}.{key}.group_selection"] = state[key] == (pre if use_pre else post)[key]
    branches["freeze_s_aux"]["kalman_stats"]["nested"].append("branch-only-mutation")
    checks["nested_mutation_does_not_change_original_pre"] = pre == before_pre
    checks["nested_mutation_does_not_change_original_post"] = post == before_post
    checks["nested_mutation_does_not_change_other_frozen_branch"] = (
        branches["freeze_all"]["kalman_stats"] == pre["kalman_stats"])
    checks["nested_mutation_does_not_change_normal_branch"] = (
        branches["normal"]["kalman_stats"] == post["kalman_stats"])
    checks["no_torch_imported"] = "torch" not in sys.modules
    checks["all_four_actions_present"] = tuple(branches) == ACTIONS
    good_checkpoint = Checkpoint(2, ("rgb-a", "rgb-b"), "normal", copy.deepcopy(post), {}, 123)
    validate_checkpoint(good_checkpoint)
    checks["valid_absolute_checkpoint_accepted"] = True
    for label, bad_index in (("bool", True), ("negative", -1), ("zero", 0),
                             ("float", 2.0), ("wrong_count", 3)):
        checkpoint = Checkpoint(bad_index, good_checkpoint.frame_ids, "normal", post, {}, 123)
        try:
            validate_checkpoint(checkpoint)
        except (TypeError, ValueError):
            checks[f"malformed_checkpoint_index_{label}_rejected"] = True
        else:
            checks[f"malformed_checkpoint_index_{label}_rejected"] = False
    bad_pre = copy.deepcopy(pre)
    bad_pre["prev_reset"] = True
    try:
        select_branch_states(bad_pre, post)
    except ValueError:
        checks["reset_collision_rejected"] = True
    else:
        checks["reset_collision_rejected"] = False

    # Review generated text as loaded from disk, not just an in-memory AST.
    compile((HERE / "derived_forward.py").read_text(), "derived_forward.py", "exec")
    checks["generated_python_compiles_without_import_or_execution"] = True
    original_tree = _original_function(source)
    original_for = [n for n in ast.walk(original_tree) if isinstance(n, ast.For)]
    checks["exactly_one_upstream_for_loop"] = len(original_for) == 1
    checks["return_state_is_empty_in_upstream_lighter"] = (
        sum(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name) and n.func.value.id == "all_state_args"
            for n in ast.walk(original_tree)) == 0)
    if not all(checks.values()):
        raise RuntimeError(json.dumps({k: v for k, v in checks.items() if not v}))

    proof.update({
        "schema": "s25-static-preparation-receipt-v1",
        "started_utc": started,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "passed": True,
        "scope": "AST derivation and plain-container software checks only",
        "checks": checks,
        "model_instantiations": 0,
        "frame_forwards": 0,
        "S24_results_read": False,
        "RGB_or_GT_arrays_read": False,
        "frozen_source_files_modified": 0,
        "main_ledger_modified": False,
        "experiment_approved": False,
        "evidence_gate": "Await parent analysis of S24 natural failure; no event/horizon/resource budget selected",
        "identities": {str(HERE / name): sha256(HERE / name) for name in (
            "state_intervention_adapter.py", "prepare_static.py", "source_binding.json",
            "original_forward.normalized.py", "derived_forward.py", "instrumentation.diff",
            "STATE_CONTRACT.md", "static_field_contract.json")},
        "bound_source_file_count": len(manifest["files"]),
        "model_source_sha256": sha256(MODEL),
    })
    write_json("static_preparation_receipt.json", proof)
    print(json.dumps({
        "passed": True, "check_count": len(checks),
        "original_statement_count": proof["original_statement_count"],
        "guard_sites_removed": proof["guard_sites_removed"],
        "source_files_bound": len(manifest["files"]),
        "model_forwards": 0, "torch_imported": "torch" in sys.modules,
        "numerical_compatibility": "NOT_RUN",
        "receipt": str(HERE / "static_preparation_receipt.json"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
