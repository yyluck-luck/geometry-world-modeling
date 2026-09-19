"""Artificial CPU autograd diagnostic; no model or real-data imports."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import torch
from torch import nn


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
SOURCE = ROOT / "work/S20_environment/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py"
EXPECTED_SHA = "f78f52eee0fc5e435e2c8b16a868174a285e7155577c11eef0f82a464e207b11"
OUTPUT = BASE / "OPTIMIZER_GRADIENT_DIAGNOSTIC.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def describe_parameter(name, value):
    return {
        "name": name,
        "python_id": id(value),
        "shape": list(value.shape),
        "is_leaf": value.is_leaf,
        "requires_grad": value.requires_grad,
        "value": value.detach().tolist(),
        "grad": None if value.grad is None else value.grad.detach().tolist(),
    }


def run():
    if OUTPUT.exists():
        raise RuntimeError("Refusing to overwrite the existing diagnostic receipt")
    started = utc()
    timer = time.perf_counter()
    source_bytes = SOURCE.read_bytes()
    if sha(source_bytes) != EXPECTED_SHA:
        raise RuntimeError("Source SHA differs from the execution contract")
    tree = ast.parse(source_bytes.decode("utf-8"))
    optimizer_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PointCloudOptimizer")
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("ParameterStack", "_ravel_hw")]
    nodes.append(next(n for n in optimizer_class.body if isinstance(n, ast.FunctionDef) and n.name == "get_depthmaps"))
    if {n.name for n in nodes} != {"ParameterStack", "_ravel_hw", "get_depthmaps"}:
        raise RuntimeError("AST extraction differs from the execution contract")
    namespace = {"torch": torch, "nn": nn}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), namespace)
    actual_stack = namespace["ParameterStack"]
    captured = []

    def capture_stack(*args, **kwargs):
        result = actual_stack(*args, **kwargs)
        captured.append(result)
        return result

    namespace["ParameterStack"] = capture_stack

    class LocalChain(nn.Module):
        get_depthmaps = namespace["get_depthmaps"]

        def __init__(self):
            super().__init__()
            self.imshapes = [(1, 2), (1, 2)]
            self.max_area = 2
            self.im_depthmaps = nn.ParameterList([
                nn.Parameter(torch.tensor([[0.0, 1.0]], dtype=torch.float32, device="cpu")),
                nn.Parameter(torch.tensor([[2.0, 3.0]], dtype=torch.float32, device="cpu")),
            ])

    class OfficialStyleControl(LocalChain):
        """Only the official register-once/direct-exp structure, not its full class."""

        def __init__(self):
            super().__init__()
            self.im_depthmaps = actual_stack(self.im_depthmaps, is_param=True, fill=self.max_area)

        def get_depthmaps(self, raw=False):
            res = self.im_depthmaps.exp()
            if not raw:
                res = [dm[:h * w].view(h, w) for dm, (h, w) in zip(res, self.imshapes)]
            return res

    def evaluate(name, module, capture_temporary):
        registered = list(module.named_parameters())
        before = [p.detach().clone() for _, p in registered]
        params = [p for _, p in registered if p.requires_grad]
        optimizer = torch.optim.Adam(params, lr=0.01, betas=(0.9, 0.9))
        optimizer.zero_grad()
        depthmaps = module.get_depthmaps(raw=False)
        loss = sum(d.sum() for d in depthmaps)
        loss.backward()
        temporary = captured[-1] if capture_temporary else None
        after_backward = [describe_parameter(n, p) for n, p in registered]
        temporary_record = None if temporary is None else describe_parameter("temporary_ParameterStack_output", temporary)
        optimizer.step()
        return {
            "arm": name,
            "loss_before_step": loss.item(),
            "registered_after_backward": after_backward,
            "registered_before_step": [p.tolist() for p in before],
            "registered_after_step": [p.detach().tolist() for _, p in registered],
            "registered_changed": [not torch.equal(a, p.detach()) for a, (_, p) in zip(before, registered)],
            "temporary_leaf": temporary_record,
            "temporary_in_optimizer": None if temporary is None else any(temporary is p for p in params),
            "optimizer_parameter_ids": [id(p) for p in params],
            "optimizer_state_count_after_step": len(optimizer.state),
        }

    local = evaluate("local_actual_AST_call_chain", LocalChain(), True)
    control = evaluate("official_style_registered_stack_then_direct_exp", OfficialStyleControl(), False)
    local_none = all(p["grad"] is None for p in local["registered_after_backward"])
    temporary_nonzero = local["temporary_leaf"]["grad"] is not None and bool(torch.tensor(local["temporary_leaf"]["grad"]).ne(0).any())
    control_nonzero = all(p["grad"] is not None and bool(torch.tensor(p["grad"]).ne(0).any()) for p in control["registered_after_backward"])
    confirmed = local_none and temporary_nonzero and not any(local["registered_changed"]) and control_nonzero and all(control["registered_changed"])
    falsified = any(p["grad"] is not None for p in local["registered_after_backward"]) and any(local["registered_changed"])
    receipt = {
        "started_utc": started,
        "completed_utc": utc(),
        "wall_seconds": time.perf_counter() - timer,
        "source": {"path": str(SOURCE), "bytes": len(source_bytes), "sha256": sha(source_bytes)},
        "checker_sha256": sha(Path(__file__).read_bytes()),
        "contract_sha256": sha((BASE / "OPTIMIZER_GRADIENT_DIAGNOSTIC_CONTRACT.md").read_bytes()),
        "extracted_functions": [{"name": n.name, "start_line": n.lineno, "end_line": n.end_lineno} for n in nodes],
        "python": sys.executable,
        "torch_version": torch.__version__,
        "dtype": "float32",
        "device": "cpu",
        "artificial_input": "Two 1x2 log-depth maps [0,1] and [2,3]; loss=sum(exp(log_depth))",
        "arms": [local, control],
        "diagnosis": "CONFIRMED_FOR_ARTIFICIAL_CALL_CHAIN" if confirmed else "FALSIFIED_FOR_ARTIFICIAL_CALL_CHAIN" if falsified else "INCONCLUSIVE",
        "boundary": "No full optimizer, reconstruction, RGB/depth data, checkpoint, sampler, or historical S26 run. Does not imply other optimizer parameters cannot change or historical losses were invalid.",
        "official_reference": "https://raw.githubusercontent.com/naver/dust3r/main/dust3r/cloud_opt/optimizer.py",
        "official_scope": "Prior code read: init registers stacked im_depthmaps once; get_depthmaps directly applies exp. Control reproduces this dataflow only.",
    }
    OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"receipt": str(OUTPUT), "diagnosis": receipt["diagnosis"], "wall_seconds": receipt["wall_seconds"], "receipt_sha256": sha(OUTPUT.read_bytes())}, ensure_ascii=False))


if __name__ == "__main__":
    run()
