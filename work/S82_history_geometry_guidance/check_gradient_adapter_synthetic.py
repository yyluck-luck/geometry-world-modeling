"""One artificial local adapter check; never imports the full geometry class."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import traceback

import torch
from torch import nn

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "work/S20_environment/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py"
EXPECTED_SOURCE_SHA = "f78f52eee0fc5e435e2c8b16a868174a285e7155577c11eef0f82a464e207b11"
ADAPTER = HERE / "gradient_preserving_optimizer.py"
OUTPUT = HERE / "GRADIENT_ADAPTER_SYNTHETIC.json"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    started, timer = utc(), time.perf_counter()
    record = dict(schema="S82-local-depth-adapter-artificial-check-v1", status="RUNNING",
                  started_utc=started, python=sys.executable, torch_version=torch.__version__,
                  dtype="float32", device="cpu", artificial_shape=[4, 2, 3],
                  artificial_log_depth="arange(24).reshape(4,2,3)/10 - 1",
                  loss="0.5 * sum(get_depthmaps(raw=True)) + 0.5 * sum(get_depthmaps(raw=False))",
                  adam=dict(lr=.01, betas=[.9, .9], steps_per_arm=1),
                  source=dict(path=str(SOURCE), sha256=sha(SOURCE)),
                  adapter=dict(path=str(ADAPTER), sha256=sha(ADAPTER)),
                  checker_sha256=sha(Path(__file__)), arms=[], checks={},
                  model_calls=0, full_geometry_class_instances=0, scientific_input_array_reads=0,
                  boundary="Artificial getter/gradient/Adam test, not a scene objective, camera/K validation, or geometric accuracy test")
    with OUTPUT.open("x") as f:
        json.dump(record, f, indent=2)
    try:
        assert record["source"]["sha256"] == EXPECTED_SOURCE_SHA
        torch.set_num_threads(1)
        tree = ast.parse(SOURCE.read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PointCloudOptimizer")
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"ParameterStack", "_ravel_hw"}]
        nodes += [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "get_depthmaps"]
        assert {n.name for n in nodes} == {"ParameterStack", "_ravel_hw", "get_depthmaps"}
        ns = dict(torch=torch, nn=nn)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), ns)
        adapter_ns = {}
        exec(compile(ADAPTER.read_text(), str(ADAPTER), "exec"), adapter_ns)

        class GetterOnly(nn.Module):
            get_depthmaps = ns["get_depthmaps"]

            def __init__(self):
                super().__init__()
                self.imshapes = [(2, 3)] * 4
                self.max_area = 6
                initial = torch.arange(24, dtype=torch.float32).reshape(4, 2, 3) / 10 - 1
                self.im_depthmaps = nn.ParameterList([nn.Parameter(x.clone()) for x in initial])

        fixed_class = adapter_ns["with_gradient_preserving_depths"](GetterOnly)
        old, fixed = GetterOnly(), fixed_class()
        raw_old, raw_fixed = old.get_depthmaps(True), fixed.get_depthmaps(True)
        list_old, list_fixed = old.get_depthmaps(False), fixed.get_depthmaps(False)
        record["checks"].update(raw_shape_old=list(raw_old.shape), raw_shape_fixed=list(raw_fixed.shape),
            raw_values_exact=torch.equal(raw_old, raw_fixed),
            list_shapes_old=[list(x.shape) for x in list_old],
            list_shapes_fixed=[list(x.shape) for x in list_fixed],
            list_values_exact=all(torch.equal(a, b) for a, b in zip(list_old, list_fixed)),
            raw_dtype_equal=raw_old.dtype == raw_fixed.dtype == torch.float32,
            raw_device_equal=raw_old.device == raw_fixed.device == torch.device("cpu"),
            fixed_raw_is_leaf=raw_fixed.is_leaf, fixed_raw_grad_fn=type(raw_fixed.grad_fn).__name__)
        assert raw_fixed.shape == (4, 2, 3)
        assert all(x.shape == (2, 3) for x in list_fixed)
        assert record["checks"]["raw_values_exact"] and record["checks"]["list_values_exact"]
        assert record["checks"]["raw_dtype_equal"] and record["checks"]["raw_device_equal"]

        for name, module, raw, listed in [("original_AST", old, raw_old, list_old),
                                           ("local_adapter", fixed, raw_fixed, list_fixed)]:
            before_names = [n for n, _ in module.named_parameters()]
            before_ids = [id(p) for p in module.parameters()]
            before = [p.detach().clone() for p in module.parameters()]
            optimizer = torch.optim.Adam(module.parameters(), lr=.01, betas=(.9, .9))
            loss = .5 * raw.sum() + .5 * sum(x.sum() for x in listed)
            loss.backward()
            grads = [None if p.grad is None else p.grad.detach().clone() for p in module.parameters()]
            optimizer.step()
            after = [p.detach().clone() for p in module.parameters()]
            changed = [not torch.equal(a, b) for a, b in zip(before, after)]
            identity_unchanged = before_ids == [id(p) for p in module.parameters()]
            expected = [torch.tensor([[math.exp(float(v)) for v in row] for row in p], dtype=torch.float64) for p in before]
            grad_errors = [None if g is None else float((g.double() - e).abs().max()) for g, e in zip(grads, expected)]
            record["arms"].append(dict(name=name, loss_before_step=float(loss.detach()),
                registered_names=before_names, registered_leaf_ids=before_ids,
                registered_identities_unchanged=identity_unchanged,
                registered_all_leaf=all(p.is_leaf for p in module.parameters()),
                before=[p.tolist() for p in before], gradients=[None if g is None else g.tolist() for g in grads],
                gradient_max_absolute_errors_vs_scalar_exp=grad_errors,
                after=[p.tolist() for p in after], changed=changed,
                optimizer_state_count=len(optimizer.state)))
            assert len(before_ids) == 4 and identity_unchanged
            if name == "original_AST":
                assert all(g is None for g in grads) and not any(changed) and len(optimizer.state) == 0
            else:
                assert all(g is not None and bool(torch.isfinite(g).all()) for g in grads)
                assert all(e is not None and e <= 2e-6 for e in grad_errors)
                assert all(changed) and len(optimizer.state) == 4
        record["status"] = "PASS_ARTIFICIAL_ADAPTER_ONLY"
    except BaseException:
        record.update(status="FAILED", traceback=traceback.format_exc())
        raise
    finally:
        record.update(completed_utc=utc(), measured_seconds_after_torch_import=time.perf_counter() - timer)
        OUTPUT.write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(dict(status=record["status"], receipt=str(OUTPUT), receipt_sha256=sha(OUTPUT),
                         seconds=record["measured_seconds_after_torch_import"])))


if __name__ == "__main__":
    main()
