"""Bounded synthetic-only validation of fixed scorer math and original transforms."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import io
import json
import math
import subprocess
import sys
import time
import traceback
from typing import Optional, Tuple, Union

D = Path(__file__).absolute().parent
R = D.parents[1]


def main():
    out = D / 'synthetic_source_check_01'
    out.mkdir(exist_ok=False)
    start = time.monotonic()
    report = dict(status='RUNNING_SYNTHETIC_ONLY', started_utc=datetime.now(timezone.utc).isoformat(),
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), checks=[],
                  real_RGB_bytes=0, real_NPZ_bytes=0, real_GT_bytes=0, weight_bytes=0, model_instances=0)
    try:
        from importlib.metadata import version
        import numpy as np
        import torch
        import torch.nn.functional as F
        import torchvision.transforms.functional as TF
        from PIL import Image
        contract = json.loads((D / 'SCORING_CONTRACT.json').read_text())
        assert hashlib.sha256((D / 'SCORING_CONTRACT.json').read_bytes()).hexdigest() == 'a776fd9cc1af9014de2e9226364f8990e9a2461c45b23aa6e03e5354370df8ac'
        versions = {n: version(n) for n in contract['versions']}
        assert versions == contract['versions']
        report['versions'] = versions
        torch.set_num_threads(8)
        torch.set_num_interop_threads(1)
        util = Path(contract['original_util']['path'])
        text = util.read_bytes()
        assert hashlib.sha256(text).hexdigest() == contract['original_util']['sha256']
        env = dict(torch=torch, np=np, F=F, TF=TF, Image=Image, math=math,
                   Optional=Optional, Tuple=Tuple, Union=Union)
        names = set(contract['original_preprocess_helpers']) | {'tensor_to_pil'}
        nodes = [x for x in ast.parse(text).body if isinstance(x, ast.FunctionDef) and x.name in names]
        assert {x.name for x in nodes} == names
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(util), 'exec'), env)
        scorer_path = D / 'score_fixed_contexts.py'
        score_bytes = scorer_path.read_bytes()
        assert hashlib.sha256(score_bytes).hexdigest() == '4c698efddeca50a2c35812632516ca458ab0f1a8f9dec8f4aa4cdde0f1584ab5'
        score_tree = ast.parse(score_bytes)
        scorer_main = next(n for n in score_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        maths = [n for n in scorer_main.body if isinstance(n, ast.FunctionDef) and n.name in {'array_equal', 'mse', 'psnr'}]
        assert len(maths) == 3
        exec(compile(ast.Module(body=maths, type_ignores=[]), str(scorer_path), 'exec'), env)

        # Distinct spatial structure tests actual resize/crop against scalar adaptive-area supports.
        y, x = np.indices((480, 640))
        rgb = np.stack([x % 251, y % 239, ((x // 8 + y // 8) % 2) * 255], axis=-1).astype(np.uint8)
        buf = io.BytesIO()
        Image.fromarray(rgb).save(buf, format='PNG')
        with torch.inference_mode():
            image, _ = env['load_img_and_K'](io.BytesIO(buf.getvalue()), None, K=None, device='cpu')
            got, _ = env['transform_img_and_K'](image, (576, 576), mode='crop', K=None)
        assert got.shape == (1, 3, 576, 576) and got.dtype == torch.float32
        errors = []
        points = [(0, 0), (0, 575), (575, 0), (575, 575), (1, 1), (2, 2), (95, 96),
                  (123, 234), (287, 287), (288, 288), (400, 501), (574, 573)]
        for oy, ox in points:
            ry, rx = oy, ox + 96
            y0, y1 = math.floor(ry * 480 / 576), math.ceil((ry + 1) * 480 / 576)
            x0, x1 = math.floor(rx * 640 / 768), math.ceil((rx + 1) * 640 / 768)
            expected = (rgb[y0:y1, x0:x1].astype(np.float64) / 255 * 2 - 1).mean(axis=(0, 1))
            error = float(np.max(np.abs(got[0, :, oy, ox].numpy().astype(np.float64) - expected)))
            assert error <= 1e-6
            errors.append(dict(output_yx=[oy, ox], input_support_yxyx=[y0, x0, y1, x1], max_abs_error=error))
        report['checks'].append(dict(name='original_two_stage_area_crop_vs_independent_scalar_support',
                                     points=errors, atol=1e-6, passed=True))

        # Use the actual emitted-uint8 scorer assignment nodes; compare the original helper.
        emission = [n for n in ast.walk(scorer_main) if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id in {'rescaled', 'mapped', 'expected'} for t in n.targets)
                    and 120 <= n.lineno <= 124]
        assert len(emission) == 3
        emission.sort(key=lambda n: n.lineno)
        emission_code = compile(ast.Module(body=emission, type_ignores=[]), str(scorer_path), 'exec')
        emission_rows = []
        for minimum in [-0.2, -0.1001, -0.0999, 0.1]:
            values = np.linspace(minimum, 1.2, 24, dtype=np.float32).reshape(3, 2, 4)
            original = np.asarray(env['tensor_to_pil'](torch.from_numpy(values.copy())))
            local = dict(env, image=values.transpose(1, 2, 0))
            exec(emission_code, local)
            assert np.array_equal(original, local['expected'])
            emission_rows.append(dict(minimum=float(values.min()), rescaled=bool(local['rescaled']), exact_match=True))
        report['checks'].append(dict(name='actual_scorer_emission_matches_original_both_branches', cases=emission_rows, passed=True))

        reference = np.zeros((4, 2, 2, 3), np.uint8)
        A, B = reference.copy(), reference.copy()
        for i in range(4):
            A[i].reshape(-1)[:i] = 255
            B[i].reshape(-1)[:i + 1] = 255
        am = [env['mse'](A[i], reference[i]) for i in range(4)]
        bm = [env['mse'](B[i], reference[i]) for i in range(4)]
        delta = sum(bm) / 4 - sum(am) / 4
        assert math.isclose(delta, 1 / 12, abs_tol=1e-15, rel_tol=0)
        assert math.isclose(env['mse'](A, reference), 6 / 48, abs_tol=1e-15, rel_tol=0)
        assert math.isclose(env['mse'](B, reference), 10 / 48, abs_tol=1e-15, rel_tol=0)
        assert env['psnr'](0) == 'Infinity' and env['psnr'](1) == 0
        assert math.isclose(env['psnr'](.01), 20, abs_tol=1e-12)
        plus, minus = np.array([0.], np.float32), np.array([-0.], np.float32)
        assert np.array_equal(plus, minus) and not env['array_equal'](plus, minus)
        assert env['array_equal'](A, A.copy()) and not env['array_equal'](A, B)
        report['checks'].append(dict(name='analytic_signed_MSE_equal_frames_PSNR_and_byte_replay',
                                     delta_B_minus_A=delta, expected_delta=1/12, zero_psnr=env['psnr'](0),
                                     opposite_signed_zero_fails_byte_replay=True, passed=True))
        report['status'] = 'PASS_SYNTHETIC_SOURCE_CHECK_ONLY'
    except BaseException as e:
        report.update(status='FAILED_SYNTHETIC_SOURCE_CHECK_PRESERVED', error=str(e), traceback=traceback.format_exc())
    report.update(completed_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - start)
    with (out / 'receipt.json').open('x') as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write('\n')
    (out / 'receipt.json').chmod(0o444)
    print(json.dumps(dict(status=report['status'], receipt=str(out / 'receipt.json'), elapsed_seconds=report['elapsed_seconds'])))
    return 0 if report['status'].startswith('PASS') else 2


if __name__ == '__main__':
    raise SystemExit(main())
