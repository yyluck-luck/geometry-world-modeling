"""Prospective four-target emitted-RGB score; no model or parameter fitting."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import time
import traceback
from typing import Optional, Tuple, Union

D = Path(__file__).resolve().parent
R = D.parents[1]
CONTRACT_SHA = 'a776fd9cc1af9014de2e9226364f8990e9a2461c45b23aa6e03e5354370df8ac'
ARMS = ('A0', 'A1', 'B')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, data):
    with path.open('x') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def main():
    if sys.argv[1:] == ['--compile-only']:
        compile(Path(__file__).read_bytes(), str(Path(__file__)), 'exec')
        print('COMPILE_ONLY_NO_ARRAY_OR_RGB_READ')
        return 0
    assert len(sys.argv) == 2, 'Expected root scoring binding SHA'
    binding_bytes = (D / 'ROOT_SCORING_BINDING.json').read_bytes()
    assert sha(binding_bytes) == sys.argv[1]
    binding = json.loads(binding_bytes)
    assert binding['status'] == 'ACCEPTED_S70_COMPLETE_GENERATION_FOR_FIXED_SCORING'
    assert binding['target_ids'] == [20, 21, 22, 23]
    for path, expected in binding['source_files_sha256'].items():
        assert sha(Path(path).read_bytes()) == expected, path
    assert binding['source_files_sha256'][str(Path(__file__).resolve())] == sha(Path(__file__).read_bytes())
    contract_bytes = (D / 'SCORING_CONTRACT.json').read_bytes()
    assert sha(contract_bytes) == CONTRACT_SHA
    contract = json.loads(contract_bytes)
    assert binding['ordered_reference_ids'] == contract['arms']
    out = D / 'scoring_01'
    out.mkdir(exist_ok=False)
    t0 = time.monotonic()
    report = dict(schema='s70-fixed-rgb-score-v1', started_utc=utc(), status='RUNNING',
                  contract_sha256=CONTRACT_SHA, binding_sha256=sys.argv[1],
                  scorer_sha256=sha(Path(__file__).read_bytes()), reads=[], frames=[],
                  target_ids=contract['target_ids'], new_method_validated=False)

    def read_bound(path, expected, kind):
        path = Path(path)
        data = path.read_bytes()
        got = sha(data)
        report['reads'].append(dict(path=str(path), kind=kind, bytes=len(data), sha256=got))
        assert got == expected, 'Input identity mismatch: ' + str(path)
        return data

    def load_result(arm, name, shape, dtype):
        path = D / 'execution_01' / arm / name
        data = read_bound(path, binding['result_files_sha256'][str(path)], 'saved_generation_array')
        arr = np.load(io.BytesIO(data), allow_pickle=False)
        assert arr.shape == shape and arr.dtype == np.dtype(dtype) and np.isfinite(arr).all()
        return arr

    def array_equal(a, b):
        return a.shape == b.shape and a.dtype == b.dtype and a.tobytes(order='C') == b.tobytes(order='C')

    def mse(a, b):
        diff = a.astype(np.float64) / 255.0 - b.astype(np.float64) / 255.0
        return float(np.mean(diff * diff, dtype=np.float64))

    def psnr(value):
        return 'Infinity' if value == 0.0 else float(-10.0 * math.log10(value))

    try:
        from importlib.metadata import version
        import numpy as np
        import torch
        import torch.nn.functional as F
        import torchvision.transforms.functional as TF
        from PIL import Image
        versions = {name: version(name) for name in contract['versions']}
        assert versions == contract['versions']
        report['versions'] = versions
        torch.set_num_threads(8)
        torch.set_num_interop_threads(1)
        env = dict(torch=torch, np=np, F=F, TF=TF, Image=Image, math=math,
                   Optional=Optional, Tuple=Tuple, Union=Union)
        util = contract['original_util']
        data = read_bound(util['path'], util['sha256'], 'original_preprocessing_source')
        names = set(contract['original_preprocess_helpers'])
        nodes = [x for x in ast.parse(data, filename=util['path']).body
                 if isinstance(x, ast.FunctionDef) and x.name in names]
        assert {x.name for x in nodes} == names
        exec(compile(ast.Module(body=nodes, type_ignores=[]), util['path'], 'exec'), env)
        raw, emitted, latent = {}, {}, {}
        for arm in ARMS:
            latent[arm] = load_result(arm, 'all8_latents.npy', (8, 4, 72, 72), 'float32')
            raw[arm] = load_result(arm, 'targets_fp32.npy', (4, 3, 576, 576), 'float32')
            emitted[arm] = load_result(arm, 'targets_uint8.npy', (4, 576, 576, 3), 'uint8')
        report['replay'] = dict(full8_latent_bytes_equal=array_equal(latent['A0'], latent['A1']),
                               four_raw_FP32_RGB_bytes_equal=array_equal(raw['A0'], raw['A1']),
                               four_emitted_uint8_RGB_bytes_equal=array_equal(emitted['A0'], emitted['A1']))
        report['replay']['all_passed'] = all(report['replay'].values())
        report['emission_checks'] = []
        for arm in ARMS:
            for i, target_id in enumerate(contract['target_ids']):
                image = raw[arm][i].transpose(1, 2, 0)
                low, high = float(image.min()), float(image.max())
                rescaled = bool(image.min() < -0.1)
                mapped = (image + 1) / 2.0 if rescaled else image
                expected = np.clip(mapped * 255, 0, 255).astype(np.uint8)
                assert array_equal(expected, emitted[arm][i]), 'Original emission mismatch'
                report['emission_checks'].append(dict(arm=arm, target_id=target_id,
                                                      raw_min=low, raw_max=high,
                                                      original_range_rescale_branch=rescaled,
                                                      exact_original_uint8_match=True))
        references = []
        for item in contract['targets']:
            png = read_bound(item['path'], item['sha256'], 'historically_seen_reference_png')
            with Image.open(io.BytesIO(png)) as img:
                assert img.size == tuple(item['native_wh']) and img.mode == 'RGB'
            with torch.inference_mode():
                image, _ = env['load_img_and_K'](io.BytesIO(png), None, K=None, device='cpu')
                image, _ = env['transform_img_and_K'](image, (576, 576), mode='crop', K=None)
            assert image.shape == (1, 3, 576, 576) and image.dtype == torch.float32
            assert torch.isfinite(image).all() and image.min() >= -1 and image.max() <= 1
            array = image[0].permute(1, 2, 0).cpu().numpy()
            reference = (np.clip((array + 1) / 2.0, 0, 1) * 255).astype(np.uint8)
            references.append(reference)
            Image.fromarray(reference).save(out / f'reference_{item["id"]}.png')
        references = np.stack(references)
        with (out / 'transformed_targets_uint8.npy').open('xb') as f:
            np.save(f, references, allow_pickle=False)
        for i, target_id in enumerate(contract['target_ids']):
            losses = {arm: mse(emitted[arm][i], references[i]) for arm in ARMS}
            report['frames'].append(dict(target_id=target_id, mse=losses,
                                         psnr={arm: psnr(losses[arm]) for arm in ARMS},
                                         delta_B_minus_A0=losses['B'] - losses['A0'],
                                         replay_emitted_mse=mse(emitted['A0'][i], emitted['A1'][i]),
                                         replacement_emitted_mse=mse(emitted['A0'][i], emitted['B'][i])))
        means = {arm: float(np.mean([x['mse'][arm] for x in report['frames']], dtype=np.float64))
                 for arm in ARMS}
        delta = means['B'] - means['A0']
        report['mean_frame_mse'] = means
        report['psnr_from_mean_frame_mse'] = {arm: psnr(means[arm]) for arm in ARMS}
        report['delta_B_minus_A0'] = delta
        report['context_comparison_interpretable'] = report['replay']['all_passed']
        report['fixed_case_higher_support_lower_emitted_rgb_error'] = bool(delta > 0) if report['replay']['all_passed'] else None
        report['counting_unit'] = 'one known sequence; four correlated targets; one A repeat'
        report['limits'] = contract['limits']
        report['status'] = 'COMPLETE_FIXED_RGB_SCORE_PENDING_INDEPENDENT_RECOMPUTE'
    except BaseException as exc:
        report['status'] = 'FAILED_PRESERVED'
        report['error'] = f'{type(exc).__name__}: {exc}'
        report['traceback'] = traceback.format_exc()
    report['completed_utc'] = utc()
    report['elapsed_seconds'] = time.monotonic() - t0
    report['outputs_before_receipt'] = {p.name: dict(bytes=p.stat().st_size, sha256=sha(p.read_bytes()))
                                         for p in sorted(out.iterdir()) if p.is_file()}
    save_json(out / 'receipt.json', report)
    for p in out.iterdir():
        if p.is_file():
            p.chmod(0o444)
    print(json.dumps({k: report[k] for k in ('status', 'completed_utc', 'elapsed_seconds')}, ensure_ascii=False))
    return 0 if report['status'].startswith('COMPLETE') else 1


if __name__ == '__main__':
    raise SystemExit(main())
