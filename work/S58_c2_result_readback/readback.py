#!/usr/bin/env python3
"""Candidate C2 saved-output readback, reversibly derived from S40 v3.3.

The module is source preparation only until its exact source/protocol pair has
independent reviews and a terminal C2 binding exists.  Derivation and static
review import only the standard library.  Runtime NumPy remains deferred to
already identity-verified archived tensors inside the reviewed S40 v3.3 code.
"""
from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / "work/S40_result_readback/readback.py"
BASE_SHA256 = "d4c22504569ad1fb1fcc74ea1da83b4f244f4de803f5d0fadc16e8da06777933"

C2_GENERATION = ROOT / "work/S47B_c2_confirmation_generation_v9"
C2_PINS = {
    "generation_gate.py": "4cd5c2179d2eaf17b85890acb5198d8573d2525be3e787a7ce00a17e7f2473cd",
    "runtime_adapter.py": "5e6f2e89c724cfc3f5b4eb486eb2a9384fde9b23fb12010576f5c7f3f98e8d7f",
    "launch_generation.py": "54c17a221e16b41c62b208cabe54895b0b0d8fc9c12528eb4d997408bb150693",
    "create_launch_authorization.py": "34666995d93a4e9a4629ac31b75b7c65e3fc989a0efe10732113c358284053a5",
    "PROTOCOL.md": "18c8a1ea3ce8f7c1b82195e3fc46adabc24488b6ce474d16a09cf79bbde17599",
}

LABELS = {
    "s40-declared-variant-two-batch-v1": "s47-c2-confirmation-two-batch-v1",
    "FROZEN_DECLARED_VARIANT_TWO_BATCH_EXECUTION":
        "FROZEN_C2_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION",
    "PASS_S40_GENERATION_SOURCE_REVIEW": "PASS_S47_C2_GENERATION_SOURCE_REVIEW",
    "READY_TO_ATTEMPT_S40_DECLARED_GENERATION":
        "READY_TO_ATTEMPT_S47_C2_BASELINE_GENERATION",
    "DECLARED_VARIANT_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW":
        "C2_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW",
    "DECLARED_VARIANT_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW":
        "C2_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW",
    "PASS_S40_DECLARED_VARIANT_COMPONENT_LOADING_ONLY":
        "PASS_S47_C2_DECLARED_VARIANT_COMPONENT_LOADING_ONLY",
    "s40-real-saved-output-readback-v1": "s58-c2-real-saved-output-readback-v1",
    "PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY":
        "PASS_SAVED_C2_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY",
    "FAILED_OR_PARTIAL_S40_READBACK": "FAILED_OR_PARTIAL_C2_READBACK",
    "Real frozen S40 manifest required": "Real frozen C2 manifest required",
    "Unreviewed S40 source version": "Unreviewed C2 generation source version",
    "Unbound S40 approval": "Unbound C2 generation approval",
    "Synthetic events cannot satisfy S40": "Synthetic events cannot satisfy C2",
    "No BF16 numeric conversion in CPU-FP32 S40 comparisons":
        "No BF16 numeric conversion in CPU-FP32 C2 comparisons",
    "Saved complete archive identities and actual first-output/cache/second-condition/sampler latent chain; no model, rendering or video quality recomputation":
        "Saved C2 complete archive identities and actual first-output/cache/second-condition/sampler latent chain; no model, rendering or image-quality recomputation",
}


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def derive_readback(*, compile_only: bool = False):
    """Build the C2 reader from the exact reviewed S40 v3.3 AST.

    The transformation replaces only the generation-root/PINS assignments and
    the fixed row/schema/status labels above, and the unique source-domain count
    assertion from 218 to 219 for V9's fifth row-specific source.  It then reverses every edit and
    requires full AST equality with the reviewed parent before it can execute.
    """
    if _sha256(BASE) != BASE_SHA256:
        raise RuntimeError("Reviewed S40 v3.3 readback parent changed")
    original = ast.parse(BASE.read_bytes(), filename=str(BASE))
    derived = copy.deepcopy(original)
    changes = {}
    label_counts = {label: 0 for label in LABELS}
    assignment_counts = {"S40": 0, "PINS": 0}
    source_count_edits = []

    def changed(old, new):
        new = ast.copy_location(new, old)
        key = (type(new).__name__, new.lineno, new.col_offset)
        if key in changes:
            raise RuntimeError("Overlapping C2 readback derivation edits")
        changes[key] = (copy.deepcopy(old), ast.dump(new, include_attributes=False))
        return new

    class Route(ast.NodeTransformer):
        def visit_Assign(self, node):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                if name == "S40":
                    assignment_counts[name] += 1
                    replacement = copy.deepcopy(node)
                    replacement.value = ast.BinOp(
                        left=ast.Name(id="ROOT", ctx=ast.Load()),
                        op=ast.Div(),
                        right=ast.Constant("work/S47B_c2_confirmation_generation_v9"),
                    )
                    return changed(node, replacement)
                if name == "PINS":
                    assignment_counts[name] += 1
                    replacement = copy.deepcopy(node)
                    replacement.value = ast.Dict(
                        keys=[ast.Constant(key) for key in C2_PINS],
                        values=[ast.Constant(value) for value in C2_PINS.values()],
                    )
                    return changed(node, replacement)
            return self.generic_visit(node)

        def visit_Compare(self, node):
            expected = ast.parse("len(m['source_identities']) == 218", mode="eval").body
            if ast.dump(node, include_attributes=False) == ast.dump(expected, include_attributes=False):
                replacement = copy.deepcopy(node)
                replacement.comparators[0] = ast.copy_location(ast.Constant(219), node.comparators[0])
                source_count_edits.append({"from": 218, "to": 219, "line": node.lineno})
                return changed(node, replacement)
            return self.generic_visit(node)

        def visit_Constant(self, node):
            if isinstance(node.value, str) and node.value in LABELS:
                label_counts[node.value] += 1
                return changed(node, ast.Constant(LABELS[node.value]))
            return node

    derived = Route().visit(derived)
    ast.fix_missing_locations(derived)
    if assignment_counts != {"S40": 1, "PINS": 1}:
        raise RuntimeError("Unexpected S40/PINS assignment count in reviewed parent")
    if len(source_count_edits) != 1:
        raise RuntimeError("Expected exactly one source-domain 218-to-219 assertion edit")
    if any(count != 1 for count in label_counts.values()):
        raise RuntimeError("Unexpected C2 label replacement count: " + str(label_counts))

    restored_keys = set()

    class Restore(ast.NodeTransformer):
        def generic_visit(self, node):
            key = (
                type(node).__name__,
                getattr(node, "lineno", None),
                getattr(node, "col_offset", None),
            )
            if key in changes:
                old, derived_dump = changes[key]
                if ast.dump(node, include_attributes=False) != derived_dump:
                    raise RuntimeError("C2 readback derivation subtree changed")
                restored_keys.add(key)
                return copy.deepcopy(old)
            return super().generic_visit(node)

    restored = Restore().visit(copy.deepcopy(derived))
    if len(restored_keys) != len(changes) or ast.dump(
        restored, include_attributes=False
    ) != ast.dump(original, include_attributes=False):
        raise RuntimeError("C2 readback differs from S40 v3.3 beyond declared edits")

    code = compile(derived, str(BASE) + "[S58 C2 route/labels]", "exec")
    proof = {
        "parent_path": str(BASE),
        "parent_sha256": BASE_SHA256,
        "assignment_counts": assignment_counts,
        "source_count_edits": source_count_edits,
        "unchanged_numeric_tree_trace_AST": True,
        "label_counts": label_counts,
        "reversible_full_AST_equal": True,
        "inherits_v3_3_tensor_descriptor_provenance": True,
        "inherits_v3_3_list_tuple_scalar_contract": True,
        "inherits_v3_3_pil_pixel_descriptor_contract": True,
        "inherits_two_cache_commit_and_cross_batch_checks": True,
        "model_renderer_generation_imports_or_calls": 0,
        "row": "C2",
    }
    if compile_only:
        return proof

    namespace = {
        "__file__": str(Path(__file__).resolve()),
        "__name__": "_s58_c2_derived_readback",
    }
    exec(code, namespace)
    parent_run = namespace["run"]
    require = namespace["require"]

    def run_c2(args, reader):
        report = parent_run(args, reader)
        captures = report.get("actual_archive_capture_counts", {})
        selected = report.get("actual_selected_context_ids", [])
        generated = report.get("verified_generated_ids_in_second_context", [])
        require(captures.get("cache_commit") == 2,
                "C2 must contain exactly two completed cache_commit captures")
        require(len(selected) == 2 and bool(generated),
                "C2 second context did not consume first-batch generated history")
        report.update(
            row="C2",
            derivation_parent={"path": str(BASE), "sha256": BASE_SHA256},
            saved_quantity_consumption_status=(
                "VERIFIED_BY_IDENTITY_BOUND_ARCHIVED_ARRAY_CHAIN_IF_THIS_REPORT_PASSES"
            ),
            pixel_identity_status=(
                "ARCHIVED_PIL_PIXEL_TENSORS_AND_ARCHIVE_FILE_BYTES_IDENTITY_ONLY"
            ),
            png_decode_or_visual_quality_status="NOT_EVALUATED",
            second_cache_commit_rule={
                "required_cache_commit_captures": 2,
                "actual_cache_commit_captures": captures.get("cache_commit"),
                "history_contract": [1, 5, 9],
                "second_context_must_include_generated_id": True,
                "actual_generated_ids_in_second_context": generated,
            },
            evidence_boundary=(
                "Saved quantities and cross-batch archived pixel-tensor identities only; "
                "no PNG decoding, human viewing, image quality, camera compliance, method gain, or novelty"
            ),
        )
        return report

    namespace["run"] = run_c2
    namespace["DERIVATION_PROOF"] = proof
    return namespace


def main():
    return derive_readback()["main"]()


if __name__ == "__main__":
    raise SystemExit(main())
