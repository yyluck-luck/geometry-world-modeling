"""Fixed saved-cache conditioning experiment. No models, images, depth or selection."""
from __future__ import annotations

import ast
from bisect import bisect_left
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import traceback
from types import SimpleNamespace

HERE = Path(__file__).absolute().parent
ROOT = HERE.parents[1]
INPUT_SHA = '9b66b2f7b4449e11f400c342068d069e95b96caae84e659dc497123cb5e5238f'
ORIGINAL = ROOT / 'work/S20_environment/isolated_vmem_source'
S52 = ROOT / 'work/S52_next_discriminating_prediction'
S68 = ROOT / 'work/S68_tum_vmem_cache_bridge'
HELPERS = {'get_default_intrinsics', 'to_hom', 'to_hom_pose', 'get_image_grid',
           'img2cam', 'cam2world', 'get_center_and_ray', 'get_plucker_coordinates'}
METHODS = {'get_translation_scaling_factor', 'get_cond'}
INTERPOLATORS = {'ns', 'qmatrix', 'custom_slerp', 'interpolate'}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(body):
    return hashlib.sha256(body).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, data):
    with path.open('x') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def definitions(body, path, names, env, class_name=None, constant=False):
    tree = ast.parse(body, filename=str(path))
    parent = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                  and n.name == class_name) if class_name else tree
    selected = [n for n in parent.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require({n.name for n in selected} == names, 'Incomplete original definition closure')
    if constant:
        selected = [n for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'DEFAULT_FOV_RAD'
                            for t in n.targets)] + selected
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), env)


def main():
    if sys.argv[1:] == ['--compile-only']:
        compile(Path(__file__).read_bytes(), __file__, 'exec')
        print('COMPILE_ONLY_ZERO_SCIENTIFIC_READ_OR_CONDITION_CALL')
        return 0
    require(not sys.argv[1:], 'Fixed inputs only; no runtime scientific overrides')
    out = HERE / 'execution_01'
    out.mkdir(exist_ok=False)
    start = time.monotonic()
    report = dict(schema='s69-camera-conditioning-result-v1', status='RUNNING',
                  started_utc=utc(), reads=[], cameras=[], arms={},
                  source_sha256=sha(Path(__file__).read_bytes()),
                  rgb_file_bytes_read=0, depth_file_bytes_read=0, weight_bytes_read=0,
                  model_instances=0, generation_calls=0, new_method_validated=False)

    def budget():
        require(time.monotonic() - start <= 55, 'Internal 55 second stop budget')

    def read(path, expected, kind, size=None):
        path = Path(path)
        with path.open('rb') as f:
            before = os.fstat(f.fileno())
            body = f.read()
            after = os.fstat(f.fileno())
        report['reads'].append(dict(path=str(path), kind=kind, bytes_read=len(body),
                                    sha256=sha(body), expected_sha256=expected))
        require(before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
                'Input changed during read')
        require(sha(body) == expected and (size is None or len(body) == size),
                'Input identity mismatch: ' + str(path))
        return body

    try:
        m = json.loads(read(HERE / 'INPUTS.json', INPUT_SHA, 'input_metadata'))
        sources = {p: read(p, h, 'source') for p, h in m['source_sha256'].items()}
        metadata = {p: json.loads(read(p, h, 'existing_metadata'))
                    if p.endswith('.json') else read(p, h, 'existing_source_contract').decode()
                    for p, h in m['metadata_sha256'].items()}
        require(m['history_ids'] == [12, 13, 14, 18, 19]
                and m['target_ids'] == [20, 21, 22, 23]
                and m['arms'] == {'geometry': [19, 18, 13, 12], 'pose14': [19, 18, 14, 13]},
                'Fixed scientific ordering changed')
        report.update(input_sha256=INPUT_SHA, variant=m['variant'],
                      scientific_boundary=m['scientific_boundary'], tolerances=m['tolerances'])
        import importlib.metadata
        import numpy as np
        import torch
        from einops import repeat
        from scipy.spatial.transform import Rotation, Slerp
        versions = {k: importlib.metadata.version(k) for k in m['versions']}
        require(versions == m['versions'], 'Package version mismatch')
        require(sys.version_info[:2] == (3, 12), 'Use the frozen Python 3.12 virtual environment')
        report['versions'] = versions
        torch.set_num_threads(8)
        torch.set_num_interop_threads(1)
        env = dict(torch=torch, np=np, repeat=repeat, bisect_left=bisect_left,
                   Decimal=Decimal, Rotation=Rotation, Slerp=Slerp)
        util = ORIGINAL / 'utils/util.py'
        pipeline = ORIGINAL / 'modeling/pipeline.py'
        interpolation = S52 / 'interpolate_rgb_cameras.py'
        definitions(sources[str(util)], util, HELPERS, env, constant=True)
        definitions(sources[str(pipeline)], pipeline, METHODS, env, class_name='VMemPipeline')
        definitions(sources[str(interpolation)], interpolation, INTERPOLATORS, env)
        gt = m['groundtruth']
        rows = [line.split() for line in read(gt['path'], gt['sha256'], 'GT_pose_text',
                gt['size_bytes']).decode().splitlines() if line.strip() and not line.startswith('#')]
        times = [env['ns'](row[0]) for row in rows]
        require(all(a < b for a, b in zip(times, times[1:])), 'GT timestamps not strictly increasing')
        require(all(len(row) == 8 for row in rows), 'Invalid GT row schema')
        env.update(rows=rows, times=times)
        saved = metadata[str(S52 / 'RGB_TIME_CAMERA_RECEIPT.json')]
        require(saved['groundtruth_sha256'] == gt['sha256'], 'S52 GT identity differs')
        saved_by_id = {row['frame_index']: row['rgb_camera'] for row in saved['camera_results']}
        require(set(saved_by_id) == {18, 19, 20}, 'S52 reused camera IDs differ')
        cameras = {}
        for item in m['records']:
            i, timestamp = item['id'], item['rgb_timestamp_text']
            require(timestamp == Path(item['rgb_path_metadata_only']).stem, 'Timestamp/path mismatch')
            if i in m['reused_camera_ids']:
                camera = saved_by_id[i]
                require(camera['timestamp'] == timestamp, 'Reused RGB camera timestamp mismatch')
                origin = 'S52_saved_RGB_camera_no_reinterpolation'
            else:
                require(i in m['new_interpolation_ids'], 'Unplanned interpolation ID')
                camera = env['interpolate'](timestamp)
                origin = 'new_S52_original_interpolation_at_RGB_time'
            C = np.asarray(camera['c2w'], dtype=np.float64)
            require(C.shape == (4, 4) and np.isfinite(C).all()
                    and np.array_equal(C[3], [0., 0., 0., 1.]), 'Invalid optical homogeneous matrix')
            require(np.allclose(C[:3, :3].T @ C[:3, :3], np.eye(3), rtol=0, atol=1e-10)
                    and abs(np.linalg.det(C[:3, :3]) - 1) <= 1e-10, 'Invalid optical rotation')
            cameras[i] = C
            report['cameras'].append(dict(id=i, origin=origin, rgb_camera=camera))
        require(len(cameras) == 9, 'Incomplete nine-camera set')

        def array_descriptor(a):
            a = np.ascontiguousarray(a)
            return dict(shape=list(a.shape), dtype=str(a.dtype), body_bytes=a.nbytes,
                        body_sha256=sha(a.tobytes(order='C')))

        def store_arrays(name, arrays):
            arrays = {k: np.ascontiguousarray(v) for k, v in arrays.items()}
            path = out / (name + '.npz')
            with path.open('xb') as f:
                np.savez(f, **arrays)
            receipt = dict(path=str(path), sha256=sha(path.read_bytes()),
                           fields={k: array_descriptor(a) for k, a in arrays.items()})
            save_json(out / (name + '.json'), receipt)
            return receipt

        order = [x['id'] for x in m['records']]
        report['camera_archive'] = store_arrays('optical_cameras', dict(
            ids=np.asarray(order, np.int64), c2ws=np.stack([cameras[i] for i in order]),
            rgb_timestamps_ns=np.asarray([env['ns'](x['rgb_timestamp_text']) for x in m['records']], np.int64)))
        save_json(out / 'camera_interpolation.json', report['cameras'])
        cache, original_cache_sha = {}, {}
        for row in m['appearances']:
            body = read(row['npz_path'], row['npz_sha256'], 'S68_appearance_npz', row['npz_size_bytes'])
            with np.load(io.BytesIO(body), allow_pickle=False) as z:
                require(set(z.files) == set(row['tensors']), 'Unexpected S68 archive fields')
                fields = {k: z[k].copy() for k in z.files}
            for k, a in fields.items():
                require(array_descriptor(a) == row['tensors'][k] and np.isfinite(a).all(),
                        'S68 array descriptor or finite check failed')
            cache[row['history_id']] = fields
            original_cache_sha[row['history_id']] = {k: sha(a.tobytes()) for k, a in fields.items()}
        require(set(cache) == set(m['history_ids']), 'Sparse source ID mapping incomplete')
        target_K = cache[19]['K_pixels_576'].copy()
        require(all(np.array_equal(a['K_pixels_576'], target_K) for a in cache.values()),
                'One sensor/crop K cannot be shared across targets')
        require(np.array_equal(target_K[2], [0, 0, 1]) and target_K[0, 0] > 0
                and target_K[1, 1] > 0, 'Invalid pixel K')
        budget()
        Consumer = type('OriginalConditioningOnly', (), {name: env[name] for name in METHODS})
        for arm, ids in m['arms'].items():
            budget()
            arm_record = dict(status='RUNNING', ordered_history_ids=ids, target_ids=m['target_ids'])
            report['arms'][arm] = arm_record
            try:
                all_ids = ids + m['target_ids']
                optical = torch.tensor(np.stack([cameras[i] for i in all_ids]), dtype=torch.float32)
                D = torch.diag(torch.tensor([1., -1., -1., 1.], dtype=torch.float32))
                consumer_raw = optical @ D
                require(torch.equal(consumer_raw @ D, optical), 'Optical-to-consumer local basis roundtrip failed')
                latent = torch.tensor(np.stack([cache[i]['latent'] for i in ids]), dtype=torch.float32)
                embedding = torch.tensor(np.stack([cache[i]['embedding'] for i in ids]), dtype=torch.float32)
                Ks = torch.tensor(np.stack([cache[i]['K_pixels_576'] for i in ids]
                                            + [target_K.copy() for _ in m['target_ids']]), dtype=torch.float32)
                masks = torch.tensor([True] * 4 + [False] * 4)
                obj = Consumer()
                obj.device, obj.dtype, obj.camera_scale = 'cpu', torch.float32, 2.0
                obj.config = SimpleNamespace(model=SimpleNamespace(num_frames=8))
                with torch.inference_mode():
                    scale, centered = obj.get_translation_scaling_factor(consumer_raw.clone())
                    centered_before_cond = centered.clone()
                    result = obj.get_cond(latent.clone(), centered, Ks.clone(), scale,
                                          embedding.clone(), masks.clone())
                scale_tensor = torch.as_tensor(scale, dtype=torch.float32).reshape(())
                arrays = dict(ordered_ids=np.asarray(all_ids, np.int64), optical_c2ws_fp32=optical.numpy(),
                    consumer_raw_c2ws=consumer_raw.numpy(), centered_consumer_c2ws=centered_before_cond.numpy(),
                    post_cond_optical_c2ws=result['all_c2ws'].numpy(), scale=scale_tensor.numpy(),
                    K_pixels_576=Ks.numpy(), input_masks=masks.numpy(),
                    context_latents=latent.numpy(), context_embeddings=embedding.numpy())
                for group in ['c', 'uc']:
                    arrays.update({group + '__' + k: v.numpy() for k, v in result[group].items()})
                arm_record['output'] = store_arrays(arm, arrays)
                require(torch.isfinite(scale_tensor) and scale_tensor > 0, 'Invalid natural original scale')
                require(set(result) == {'c', 'uc', 'all_c2ws', 'all_Ks', 'input_masks', 'num_cameras'}
                        and result['num_cameras'] == 8, 'Unexpected original result schema')
                expected = {'crossattn': (8, 1, 1024), 'replace': (8, 5, 72, 72),
                            'concat': (8, 7, 72, 72), 'dense_vector': (8, 6, 72, 72)}
                for group in ['c', 'uc']:
                    require(set(result[group]) == set(expected), 'Unexpected conditioning fields')
                    for key, shape in expected.items():
                        v = result[group][key]
                        require(tuple(v.shape) == shape and v.dtype == torch.float32
                                and torch.isfinite(v).all(), 'Condition shape/dtype/finite failure')
                c, uc = result['c'], result['uc']
                require(torch.equal(c['replace'][:4, :4], latent)
                        and torch.all(c['replace'][:4, 4] == 1)
                        and torch.count_nonzero(c['replace'][4:]) == 0, 'Context slot/target placeholder mismatch')
                require(torch.count_nonzero(uc['replace']) == 0
                        and torch.count_nonzero(uc['crossattn']) == 0, 'Unconditional appearance mismatch')
                require(torch.equal(c['crossattn'], embedding.mean(0)[None, None].expand(8, 1, 1024)),
                        'Selected CLIP mean/broadcast differs')
                require(torch.equal(c['dense_vector'], uc['dense_vector'])
                        and torch.equal(c['concat'][:, 1:], c['dense_vector'])
                        and torch.equal(uc['concat'][:, 1:], c['dense_vector'])
                        and torch.equal(c['concat'][:, 0], masks[:, None, None].expand(8, 72, 72))
                        and torch.count_nonzero(uc['concat'][:, 0]) == 0, 'c/uc ray or mask mismatch')
                ray = c['dense_vector'][:, :3]
                moment = c['dense_vector'][:, 3:]
                require(torch.allclose(torch.linalg.vector_norm(ray, dim=1), torch.ones(8, 72, 72),
                                       rtol=0, atol=2e-5)
                        and torch.max(torch.abs((ray * moment).sum(1))) <= 2e-5,
                        'Basic normalized Plucker identity failed')
                require(torch.equal(result['all_Ks'], Ks) and torch.equal(result['input_masks'], masks)
                        and torch.isfinite(result['all_c2ws']).all(), 'Returned camera/K/mask failure')
                arm_record.update(status='COMPLETE_ORIGINAL_CONDITION_ASSEMBLY',
                                  scale=float(scale_tensor),
                                  completed_utc=utc())
            except BaseException as e:
                arm_record.update(status='FAILED_ARM', error_type=type(e).__name__,
                                  error=str(e), traceback=traceback.format_exc(), completed_utc=utc())
            save_json(out / (arm + '_receipt.json'), arm_record)
        for i, fields in cache.items():
            require({k: sha(a.tobytes()) for k, a in fields.items()} == original_cache_sha[i],
                    'Original S68 in-memory cache changed')
        budget()
        require(all(a['status'] == 'COMPLETE_ORIGINAL_CONDITION_ASSEMBLY'
                    for a in report['arms'].values()), 'At least one arm failed')
        report['status'] = 'COMPLETE_TWO_FIXED_CONDITION_ASSEMBLIES_PENDING_INDEPENDENT_RAY_REVIEW'
        code = 0
    except BaseException as e:
        report.update(status='FAILED_CAMERA_CONDITIONING', error_type=type(e).__name__,
                      error=str(e), traceback=traceback.format_exc())
        code = 2
    finally:
        report.update(completed_utc=utc(), elapsed_seconds=time.monotonic() - start)
        report['gt_text_bytes_read'] = sum(x['bytes_read'] for x in report['reads'] if x['kind'] == 'GT_pose_text')
        report['appearance_npz_bytes_read'] = sum(x['bytes_read'] for x in report['reads']
                                                  if x['kind'] == 'S68_appearance_npz')
        save_json(out / 'receipt.json', report)
        for p in out.iterdir():
            if p.is_file():
                p.chmod(0o444)
    print(json.dumps({'status': report['status'], 'receipt': str(out / 'receipt.json')}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
