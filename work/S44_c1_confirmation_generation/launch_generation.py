"""Bounded C1 two-batch entry, reversibly derived from the sealed S35 supervisor."""
from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S35 = ROOT / "work/S35_generation_integration"
PARENT = S35 / "launch_original.py"
PARENT_SHA256 = "8744cb8959cded2394c1471c660dd84f929b5ae24ac97e81379304aed0be702e"
LABELS = {
    "s35-original-generation-run-v1": "s44-c1-confirmation-two-batch-v1",
    "FROZEN_REAL_EXECUTION": "FROZEN_C1_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION",
    "s35-original-worker-v1": "s44-c1-confirmation-worker-v1",
    "s35-original-launch-v1": "s44-c1-confirmation-launch-v1",
    "ORIGINAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW": "C1_BASELINE_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW",
    "COMPLETED_EXTERNAL_RUN_PENDING_INDEPENDENT_REVIEW": "C1_BASELINE_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW",
    "FAILED_OR_PARTIAL_ORIGINAL_RUN": "FAILED_OR_PARTIAL_C1_BASELINE_RUN",
}


def derive_launcher(*, compile_only=False):
    parent_bytes = PARENT.read_bytes()
    if hashlib.sha256(parent_bytes).hexdigest() != PARENT_SHA256:
        raise RuntimeError("Sealed S35 launcher changed")
    original = ast.parse(parent_bytes, filename=str(PARENT))
    changes = {}
    counts = {label: 0 for label in LABELS}
    routes = {"resource_gate.py": 0, "runtime_factory.py": 0}
    here_count = 0

    def changed(old, new):
        new = ast.copy_location(new, old)
        key = (type(new).__name__, new.lineno, new.col_offset)
        if key in changes:
            raise RuntimeError("Overlapping C1 launcher derivation edits")
        changes[key] = (copy.deepcopy(old), ast.dump(new, include_attributes=False))
        return new

    class Route(ast.NodeTransformer):
        def visit_Assign(self, node):
            nonlocal here_count
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "HERE"
            ):
                here_count += 1
                replacement = copy.deepcopy(node)
                replacement.value = ast.Call(
                    func=ast.Name(id="Path", ctx=ast.Load()),
                    args=[ast.Constant(str(S35))],
                    keywords=[],
                )
                return changed(node, replacement)
            return self.generic_visit(node)

        def visit_BinOp(self, node):
            if (
                isinstance(node.op, ast.Div)
                and isinstance(node.left, ast.Name)
                and node.left.id == "HERE"
                and isinstance(node.right, ast.Constant)
                and node.right.value in routes
            ):
                name = node.right.value
                routes[name] += 1
                target = "generation_gate.py" if name == "resource_gate.py" else "runtime_adapter.py"
                return changed(
                    node,
                    ast.Call(
                        func=ast.Name(id="Path", ctx=ast.Load()),
                        args=[ast.Constant(str(HERE / target))],
                        keywords=[],
                    ),
                )
            return self.generic_visit(node)

        def visit_Constant(self, node):
            if isinstance(node.value, str) and node.value in LABELS:
                counts[node.value] += 1
                return changed(node, ast.Constant(LABELS[node.value]))
            return node

    derived = Route().visit(copy.deepcopy(original))
    ast.fix_missing_locations(derived)
    expected = {label: 1 for label in LABELS}
    expected["ORIGINAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW"] = 3
    expected["COMPLETED_EXTERNAL_RUN_PENDING_INDEPENDENT_REVIEW"] = 2
    expected["FAILED_OR_PARTIAL_ORIGINAL_RUN"] = 2
    if counts != expected or routes != {"resource_gate.py": 2, "runtime_factory.py": 1} or here_count != 1:
        raise RuntimeError(
            "Unexpected S35 launcher route/label locations: " + str((counts, routes, here_count))
        )

    restored_keys = set()

    class Restore(ast.NodeTransformer):
        def generic_visit(self, node):
            key = (type(node).__name__, getattr(node, "lineno", None), getattr(node, "col_offset", None))
            if key in changes:
                old, derived_dump = changes[key]
                if ast.dump(node, include_attributes=False) != derived_dump:
                    raise RuntimeError("C1 launcher derivation subtree changed")
                restored_keys.add(key)
                return copy.deepcopy(old)
            return super().generic_visit(node)

    restored = Restore().visit(copy.deepcopy(derived))
    if len(restored_keys) != len(changes) or ast.dump(
        restored, include_attributes=False
    ) != ast.dump(original, include_attributes=False):
        raise RuntimeError("C1 launcher differs from S35 beyond the declared route/label edits")
    code = compile(derived, str(PARENT) + "[S44 C1 route/labels]", "exec")
    proof = {
        "parent_sha256": PARENT_SHA256,
        "label_counts": counts,
        "route_counts": routes,
        "here_assignments": here_count,
        "reversible_full_AST_equal": True,
        "original_budget_and_trace_boundary_math_unchanged": True,
        "row": "C1",
    }
    if compile_only:
        return proof
    namespace = {"__file__": str(Path(__file__).resolve()), "__name__": "_s44_c1_derived_supervisor"}
    exec(code, namespace)
    return namespace


if __name__ == "__main__":
    raise SystemExit(derive_launcher()["main"]())

