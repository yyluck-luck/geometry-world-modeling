#!/usr/bin/env python3
"""Candidate C1 saved-output readback, reversibly derived from S40 v3.3.

The module is source preparation only until its exact source/protocol pair has
independent reviews and a terminal C1 binding exists.  Derivation and static
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

C1_GENERATION = ROOT / "work/S44_c1_confirmation_generation"
C1_PINS = {
    "launch_generation.py": "c94a982b0c0cb3fa895323ca9d7aa4e2b91eb7146eece35bdb0aedd1c157a74b",
    "generation_gate.py": "961b9550f5ea438a338eb24ba9f36dd18f22d7f0719f9b54109e182755ab43dc",
    "runtime_adapter.py": "afedaadca7bff62616368541d980a28f24131e1256eafef7af81275aa09dfb4e",
    "PROTOCOL.md": "77c72263f6f58f77e5990a7db1557773013b9b84b14fb040f20faaaae6e701b5",
}

LABELS = {
    "s40-declared-variant-two-batch-v1": "s44-c1-confirmation-two-batch-v1",
    "FROZEN_DECLARED_VARIANT_TWO_BATCH_EXECUTION":
        "FROZEN_C1_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION",
    "PASS_S40_GENERATION_SOURCE_REVIEW": "PASS_S44_C1_GENERATION_SOURCE_REVIEW",
    "READY_TO_ATTEMPT_S40_DECLARED_GENERATION":
        "READY_TO_ATTEMPT_S44_C1_BASELINE_GENERATION",
    "DECLARED_VARIANT_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW":
        "C1_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW",
    "DECLARED_VARIANT_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW":
        "C1_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW",
    "PASS_S40_DECLARED_VARIANT_COMPONENT_LOADING_ONLY":
        "PASS_S44_C1_DECLARED_VARIANT_COMPONENT_LOADING_ONLY",
    "s40-real-saved-output-readback-v1": "s45-c1-real-saved-output-readback-v1",
    "PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY":
        "PASS_SAVED_C1_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY",
    "FAILED_OR_PARTIAL_S40_READBACK": "FAILED_OR_PARTIAL_C1_READBACK",
    "Real frozen S40 manifest required": "Real frozen C1 manifest required",
    "Unreviewed S40 source version": "Unreviewed C1 generation source version",
    "Unbound S40 approval": "Unbound C1 generation approval",
    "Synthetic events cannot satisfy S40": "Synthetic events cannot satisfy C1",
    "No BF16 numeric conversion in CPU-FP32 S40 comparisons":
        "No BF16 numeric conversion in CPU-FP32 C1 comparisons",
    "Saved complete archive identities and actual first-output/cache/second-condition/sampler latent chain; no model, rendering or video quality recomputation":
        "Saved C1 complete archive identities and actual first-output/cache/second-condition/sampler latent chain; no model, rendering or image-quality recomputation",
}


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def derive_readback(*, compile_only: bool = False):
    """Build the C1 reader from the exact reviewed S40 v3.3 AST.

    The transformation replaces only the generation-root/PINS assignments and
    the fixed row/schema/status labels above.  It then reverses every edit and
    requires full AST equality with the reviewed parent before it can execute.
    """
    if _sha256(BASE) != BASE_SHA256:
        raise RuntimeError("Reviewed S40 v3.3 readback parent changed")
    original = ast.parse(BASE.read_bytes(), filename=str(BASE))
    derived = copy.deepcopy(original)
    changes = {}
    label_counts = {label: 0 for label in LABELS}
    assignment_counts = {"S40": 0, "PINS": 0}

    def changed(old, new):
        new = ast.copy_location(new, old)
        key = (type(new).__name__, new.lineno, new.col_offset)
        if key in changes:
            raise RuntimeError("Overlapping C1 readback derivation edits")
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
                        right=ast.Constant("work/S44_c1_confirmation_generation"),
                    )
                    return changed(node, replacement)
                if name == "PINS":
                    assignment_counts[name] += 1
                    replacement = copy.deepcopy(node)
                    replacement.value = ast.Dict(
                        keys=[ast.Constant(key) for key in C1_PINS],
                        values=[ast.Constant(value) for value in C1_PINS.values()],
                    )
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
    if any(count != 1 for count in label_counts.values()):
        raise RuntimeError("Unexpected C1 label replacement count: " + str(label_counts))

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
                    raise RuntimeError("C1 readback derivation subtree changed")
                restored_keys.add(key)
                return copy.deepcopy(old)
            return super().generic_visit(node)

    restored = Restore().visit(copy.deepcopy(derived))
    if len(restored_keys) != len(changes) or ast.dump(
        restored, include_attributes=False
    ) != ast.dump(original, include_attributes=False):
        raise RuntimeError("C1 readback differs from S40 v3.3 beyond declared edits")

    code = compile(derived, str(BASE) + "[S45 C1 route/labels]", "exec")
    proof = {
        "parent_path": str(BASE),
        "parent_sha256": BASE_SHA256,
        "assignment_counts": assignment_counts,
        "label_counts": label_counts,
        "reversible_full_AST_equal": True,
        "inherits_v3_3_tensor_descriptor_provenance": True,
        "inherits_v3_3_list_tuple_scalar_contract": True,
        "inherits_v3_3_pil_pixel_descriptor_contract": True,
        "inherits_two_cache_commit_and_cross_batch_checks": True,
        "model_renderer_generation_imports_or_calls": 0,
        "row": "C1",
    }
    if compile_only:
        return proof

    namespace = {
        "__file__": str(Path(__file__).resolve()),
        "__name__": "_s45_c1_derived_readback",
    }
    exec(code, namespace)
    parent_run = namespace["run"]
    require = namespace["require"]

    def run_c1(args, reader):
        report = parent_run(args, reader)
        captures = report.get("actual_archive_capture_counts", {})
        selected = report.get("actual_selected_context_ids", [])
        generated = report.get("verified_generated_ids_in_second_context", [])
        require(captures.get("cache_commit") == 2,
                "C1 must contain exactly two completed cache_commit captures")
        require(len(selected) == 2 and bool(generated),
                "C1 second context did not consume first-batch generated history")
        report.update(
            row="C1",
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

    namespace["run"] = run_c1
    namespace["DERIVATION_PROOF"] = proof
    return namespace


def main():
    return derive_readback()["main"]()


if __name__ == "__main__":
    raise SystemExit(main())
