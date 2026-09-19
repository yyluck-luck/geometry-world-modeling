"""Disposable diagnostic of frozen V11 production emission statements only.

No formal_supervision invocation and no real C1 tensor/image body is read.
The original full synthetic function supplies a valid synthetic observation;
then the exact production tail AST is executed with unchanged globals.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import traceback
import types


SOURCE = Path(__file__).resolve().parents[1] / "supervise_camera_guard.py"
EXPECTED_SHA = "4d0c746dd03ae5bca8b858026623f18abf9788c33e2bc79a0f8c41ceddfbb16a"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("uncaught", "caught"), required=True)
    parser.add_argument("--diagnostic-json", required=True)
    args = parser.parse_args()
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA
    tree = ast.parse(raw.decode(), filename=str(SOURCE))
    module = types.ModuleType("_diagnostic_frozen_c1v11_supervisor")
    module.__file__ = str(SOURCE)
    exec(compile(tree, str(SOURCE), "exec"), module.__dict__)
    assert "write_all" not in module.__dict__

    # Observe the real production constructor's synthetic arguments without
    # changing its behavior or writing any source file.
    saved = []
    constructor = module.build_external_pass_seal

    def observe_constructor(*values):
        result = constructor(*values)
        saved.append((copy.deepcopy(values), copy.deepcopy(result)))
        return result

    module.build_external_pass_seal = observe_constructor
    preceding_chain = module.synthetic_prebound_full_success_path()
    module.build_external_pass_seal = constructor
    assert len(saved) == 1
    observation, supervisor_sha, worker_sha, lock_sha, governance_sha = saved[0][0]
    formal = next(node for node in tree.body
                  if isinstance(node, ast.FunctionDef)
                  and node.name == "formal_supervision")
    body = next(node for node in formal.body if isinstance(node, ast.Try))
    start = next(index for index, node in enumerate(body.body)
                 if isinstance(node, ast.Assign)
                 and isinstance(node.value, ast.Constant)
                 and node.value.value == "EXTERNAL_HELD_FD_AUTHORITY_EMISSION")
    tail = copy.deepcopy(body.body[start:])
    assert tail[2].lineno == 2186 and tail[3].lineno == 2187
    if args.mode == "caught":
        # Exact original catch block: output_fd is already None after the
        # original successful close sequence, so there is no failure write.
        function_body = [ast.Try(body=tail, handlers=copy.deepcopy(body.handlers),
                                orelse=[], finalbody=[])]
    else:
        function_body = tail
    function = ast.FunctionDef(
        name="diagnostic_tail", args=ast.arguments(
            posonlyargs=[], args=[], vararg=None, kwonlyargs=[],
            kw_defaults=[], kwarg=None, defaults=[]),
        body=function_body, decorator_list=[])
    fragment = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    module.__dict__.update(
        terminal_observation=observation,
        args=argparse.Namespace(self_sha256=supervisor_sha,
                                worker_sha256=worker_sha,
                                governance_attestation_sha256=governance_sha),
        lock_sha256=lock_sha, output_fd=None, process=None,
        worker=None, details={})
    exec(compile(fragment, str(SOURCE), "exec"), module.__dict__)
    diagnostic = {
        "mode": args.mode,
        "source_sha256": EXPECTED_SHA,
        "source_tail_lines": [body.body[start].lineno, body.body[-1].end_lineno],
        "write_all_global_defined": False,
        "preceding_synthetic_function_chain": preceding_chain,
        "all_synthetic_closes_completed_before_tail": True,
        "actual_formal_supervision_calls": 0,
        "real_c1_tensor_body_bytes_read": 0,
        "pixels_decoded": 0,
    }
    try:
        result = module.diagnostic_tail()
        diagnostic["tail_returncode"] = result
    except BaseException as error:
        diagnostic["exception_type"] = type(error).__name__
        diagnostic["exception"] = str(error)
        diagnostic["traceback"] = traceback.format_exc()
        raise
    finally:
        with Path(args.diagnostic_json).open("x") as handle:
            json.dump(diagnostic, handle, indent=2)
            handle.write("\n")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
