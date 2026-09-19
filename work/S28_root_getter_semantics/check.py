"""Artificial getter-gradient contract only; no real scene or model imported."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R/cloud_opt/dust3r_opt/optimizer.py'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    assert not (HERE / 'attempt.json').exists(), 'Preserve every attempt'
    start = datetime.now(timezone.utc).isoformat()
    tick = time.perf_counter()
    ids = {str(SOURCE): sha(SOURCE), str(Path(__file__)): sha(__file__)}
    assert ids[str(SOURCE)] == 'f78f52eee0fc5e435e2c8b16a868174a285e7155577c11eef0f82a464e207b11'
    (HERE / 'attempt.json').write_text(json.dumps({'started_utc': start, 'identities': ids}, indent=2))
    import torch
    torch.set_num_threads(1)
    tree = ast.parse(SOURCE.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'PointCloudOptimizer')
    original = copy.deepcopy(next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'get_depthmaps'))
    helpers = [copy.deepcopy(n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ['ParameterStack', '_ravel_hw']]
    assert len(helpers) == 2
    assert ast.unparse(original.body[0]) == 'res = ParameterStack(self.im_depthmaps, is_param=False).exp()'
    repaired = copy.deepcopy(original)
    repaired.name = 'get_depthmaps_repaired'
    repaired.body[0] = ast.parse('res = torch.stack(list(self.im_depthmaps)).float().exp()').body[0]
    scope = {'torch': torch, 'nn': torch.nn}
    module = ast.fix_missing_locations(ast.Module(body=helpers + [original, repaired], type_ignores=[]))
    exec(compile(module, str(SOURCE), 'exec'), scope)
    (HERE / 'getter_diff.txt').write_text('- res = ParameterStack(self.im_depthmaps, is_param=False).exp()\n+ res = torch.stack(list(self.im_depthmaps)).float().exp()\n')
    (HERE / 'repaired_function.py').write_text(ast.unparse(repaired) + '\n')
    rows = []
    backwards = 0
    for label, flags in [('all4_trainable', [True] * 4), ('old4_frozen_new4_trainable', [False] * 4 + [True] * 4)]:
        n = len(flags)
        values = torch.arange(1, 6 * n + 1, dtype=torch.float32).reshape(n, 2, 3) / 20 - 1
        weights = torch.arange(1, 6 * n + 1, dtype=torch.float32).reshape(n, 2, 3)
        for mode in ['original', 'repaired']:
            scene = torch.nn.Module()
            scene.im_depthmaps = torch.nn.ParameterList([torch.nn.Parameter(v.clone(), requires_grad=f) for v, f in zip(values, flags)])
            scene.imshapes = [(2, 3)] * n
            params = dict(scene.named_parameters())
            before = {name: p.detach().clone() for name, p in params.items()}
            function = scope['get_depthmaps' if mode == 'original' else 'get_depthmaps_repaired']
            raw = function(scene, raw=True)
            listed = function(scene, raw=False)
            assert torch.equal(raw, values.exp()) and torch.equal(torch.stack(listed), raw)
            loss = (raw * weights).sum()
            if loss.requires_grad:
                loss.backward()
                backwards += 1
            actual_flags = []
            for i, (name, parameter) in enumerate(params.items()):
                assert dict(scene.named_parameters())[name] is parameter
                assert torch.equal(parameter.detach(), before[name])
                expected_connected = mode == 'repaired' and flags[i]
                assert (parameter.grad is not None) == expected_connected
                if expected_connected:
                    assert torch.isfinite(parameter.grad).all()
                    assert torch.equal(parameter.grad, weights[i] * values[i].exp())
                actual_flags.append(parameter.grad is not None)
            assert set(dict(scene.named_parameters())) == set(params)
            rows.append(dict(case=label, mode=mode, source_flags=flags,
                             output_shape=list(raw.shape), forward_exact=True,
                             output_requires_grad=bool(raw.requires_grad),
                             registered_grad_present=actual_flags,
                             all_connected_vjp_exact=True, names_objects_values_preserved=True))
    assert all(sha(p) == digest for p, digest in ids.items())
    result = dict(status='PASS_ARTIFICIAL_GETTER_CONTRACT', started_utc=start,
                  completed_utc=datetime.now(timezone.utc).isoformat(), wall_seconds=time.perf_counter() - tick,
                  identities=ids, torch_version=torch.__version__, input_scope='Explicit arange FP32 2x3 tensors only',
                  configurations=rows, synthetic_backwards=backwards,
                  new_real_backwards=0, model_forwards=0, ga_steps=0, real_arrays_read=0, sensor_depth_reads=0,
                  scope='Root-authored test of original getter AST and single-expression replacement; final S28 routing still needs separate static review and real execution')
    (HERE / 'receipt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['status', 'wall_seconds', 'synthetic_backwards']}, indent=2))


if __name__ == '__main__':
    main()
