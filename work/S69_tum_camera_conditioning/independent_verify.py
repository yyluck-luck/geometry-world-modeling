"""One finite, independent saved-result verification; no author numerical imports."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from bisect import bisect_left
import hashlib
import io
import json
import os
import stat
import sys
import time
import traceback

D = Path(__file__).absolute().parent
R = D.parents[1]
INNER = '9bc6539fed473e85b8cb2058c9f3ca6628c9603b4dd5c0160ce0a7cf71d610c7'
OUTER = '5fb0fcfe14e4e7f289abca568dd5825fcdbdad223104050a9b7810dd24686773'
PINS = {
    'assemble_conditions.py': 'a9cfaf59a0e2f8edfdaae3200d0977ca3030a2556f9f60998d3d49730c1ec89c',
    'PROTOCOL.md': '29e424e4f56429ebf2de3121f557adb8d27e4ec5901fb482b334c6286b01902e',
    'INPUTS.json': '9b66b2f7b4449e11f400c342068d069e95b96caae84e659dc497123cb5e5238f',
    'AUTHOR_DELIVERY.json': '0300fb66a9983b0d67046cdc36081abc1ab95ea09177f1f9005b1e799ba94f63',
    'SOURCE_REVIEW.json': '5825cbc04b2ebf9176f02c3ae881716267c3ec021b809e18520e58e07a2daf12',
    'SOURCE_REVIEW.md': 'bd5c1a300db226ad44b0236b70d3d2419dfdcff5709345e3c37f38a1a4482435',
    'ROOT_PRE_RUN_PREDICTION.md': '4e0ab591cb9ce175c94a615e5f2695595ab80e96f11bce95e5241a97efc6dae9',
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(b):
    return hashlib.sha256(b).hexdigest()


def main():
    if sys.argv[1:] == ['--compile-only']:
        compile(Path(__file__).read_bytes(), __file__, 'exec')
        print('COMPILE_ONLY_NO_NUMERICAL_OR_SCIENTIFIC_READ')
        return 0
    assert not sys.argv[1:]
    out = D / 'independent_review_01'
    out.mkdir(exist_ok=False)
    started = time.monotonic()
    report = dict(schema='s69-independent-numeric-verification-v1', status='RUNNING',
                  reviewer_role='/root/c2_v9_source_primary', started_utc=utc(),
                  source_sha256=digest(Path(__file__).read_bytes()), checks=[], comparisons=[],
                  reads=[], blockers=[], predictions={}, arms={}, cameras=[],
                  zero_rgb_depth_weight_bytes=True, original_numeric_functions_called=0,
                  models_imported_or_instantiated=0, get_cond_calls=0, new_method_validated=False)
    loaded = {}

    def check(name, ok, details=None):
        ok = bool(ok)
        report['checks'].append(dict(name=name, passed=ok, details=details))
        if not ok:
            report['blockers'].append(name)
        return ok

    def read(path, expected=None, kind='metadata'):
        path = Path(path)
        key = str(path)
        if key not in loaded:
            with path.open('rb') as f:
                a = os.fstat(f.fileno())
                body = f.read()
                b = os.fstat(f.fileno())
            assert (a.st_ino, a.st_size, a.st_mtime_ns) == (b.st_ino, b.st_size, b.st_mtime_ns)
            loaded[key] = body
            report['reads'].append(dict(path=key, sha256=digest(body), bytes=len(body), kind=kind,
                                       mode=format(stat.S_IMODE(path.stat().st_mode), '04o')))
        body = loaded[key]
        if expected is not None:
            assert digest(body) == expected, key
        return body

    def js(path, expected=None):
        return json.loads(read(path, expected))

    try:
        import numpy as np
        import scipy
        from scipy.spatial.transform import Rotation
        report['versions'] = dict(python=sys.version, numpy=np.__version__, scipy=scipy.__version__)
        assert sys.version_info[:2] == (3, 12) and np.__version__ == '1.26.4' and scipy.__version__ == '1.16.2'

        def compare(name, got, expected, atol=2e-5, rtol=2e-5, gate=True):
            a, b = np.asarray(got), np.asarray(expected)
            assert a.shape == b.shape, (name, a.shape, b.shape)
            diff = np.abs(a.astype(np.float64) - b.astype(np.float64))
            allowance = atol + rtol * np.abs(b.astype(np.float64))
            passed = bool(np.isfinite(a).all() and np.isfinite(b).all() and np.all(diff <= allowance))
            item = dict(name=name, shape=list(a.shape), max_abs_error=float(diff.max(initial=0)),
                        atol=atol, rtol=rtol, passed=passed, gate=gate,
                        max_tolerance_fraction=float(np.max(diff / np.maximum(allowance, 1e-300), initial=0)))
            report['comparisons'].append(item)
            if gate and not passed:
                report['blockers'].append(name)
            return item

        def descriptor(a):
            a = np.ascontiguousarray(a)
            return dict(shape=list(a.shape), dtype=str(a.dtype), body_bytes=a.nbytes,
                        body_sha256=digest(a.tobytes()))

        def npz(path, expected, fields, kind):
            body = read(path, expected, kind)
            with np.load(io.BytesIO(body), allow_pickle=False) as z:
                assert set(z.files) == set(fields)
                result = {k: z[k].copy() for k in z.files}
            for k, a in result.items():
                check(str(Path(path).name) + '/' + k + '/descriptor_finite',
                      descriptor(a) == fields[k] and np.isfinite(a).all())
            return result

        for name, h in PINS.items():
            read(D / name, h, 'source_or_fixed_metadata')
            check(name + '/readonly', stat.S_IMODE((D / name).stat().st_mode) == 0o444)
        m = js(D / 'INPUTS.json', PINS['INPUTS.json'])
        outer = js(D / 'external_01/receipt.json', OUTER)
        worker = js(D / 'execution_01/receipt.json', INNER)
        check('external_return_and_worker_binding', outer['returncode'] == 0
              and outer['stop_reason'] is None and outer['worker_receipt_sha256'] == INNER
              and outer['timeout_seconds'] == 60)
        check('worker_source_and_status', worker['source_sha256'] == PINS['assemble_conditions.py']
              and worker['input_sha256'] == PINS['INPUTS.json']
              and worker['status'] == 'COMPLETE_TWO_FIXED_CONDITION_ASSEMBLIES_PENDING_INDEPENDENT_RAY_REVIEW')
        check('actual_argv', outer['argv'] == [str(R / '.venv-cut3r/bin/python'), '-B', str(D / 'assemble_conditions.py')])
        binding = js(D / 'ROOT_RUN_BINDING.json', outer['binding_sha256'])
        for p, h in binding['reviewed_files'].items():
            read(p, h, 'source_or_fixed_metadata')
        read(D / 'observe_once.py', outer['observer_sha256'], 'source')
        stdout = read(D / 'external_01/stdout.txt', outer['stdout_sha256'], 'terminal')
        stderr = read(D / 'external_01/stderr.txt', outer['stderr_sha256'], 'terminal')
        check('terminal_stdout_stderr', not stderr and json.loads(stdout)['status'] == worker['status'])
        try:
            os.kill(outer['pid'], 0)
        except ProcessLookupError:
            check('worker_pid_exited', True)
        else:
            check('worker_pid_exited', False, 'PID exists; investigate possible reuse separately')
        for p, h in m['source_sha256'].items():
            read(p, h, 'source')
        metadata = {p: json.loads(read(p, h)) if p.endswith('.json') else read(p, h).decode()
                    for p, h in m['metadata_sha256'].items()}
        frozen = metadata[str(R / 'results/S8_cut3r_cpu_v2/frozen_inputs.json')]['blocks'][0]['frames']
        for rec in m['records']:
            old = frozen[rec['id']]
            check('camera/' + str(rec['id']) + '/RGB_identity',
                  rec['rgb_timestamp_text'] == Path(old['rgb']['path']).stem
                  and rec['rgb_path_metadata_only'].endswith('/' + old['rgb']['path'])
                  and rec['rgb_sha256_metadata_only'] == old['rgb_sha256'])

        gt = m['groundtruth']
        gt_body = read(gt['path'], gt['sha256'], 'GT_pose_text')
        assert len(gt_body) == gt['size_bytes']
        rows = [line.split() for line in gt_body.decode().splitlines() if line.strip() and not line.startswith('#')]
        ns = lambda s: int(Decimal(s) * Decimal(1000000000))
        times = [ns(row[0]) for row in rows]
        assert all(a < b for a, b in zip(times, times[1:])) and all(len(row) == 8 for row in rows)
        saved = metadata[str(R / 'work/S52_next_discriminating_prediction/RGB_TIME_CAMERA_RECEIPT.json')]
        saved_by_id = {x['frame_index']: x['rgb_camera'] for x in saved['camera_results']}
        actual_cameras = {x['id']: x for x in worker['cameras']}
        camera_record = worker['camera_archive']
        optical = npz(camera_record['path'], camera_record['sha256'], camera_record['fields'], 'S69_numeric_npz')
        assert js(D / 'execution_01/optical_cameras.json') == camera_record
        assert js(D / 'execution_01/camera_interpolation.json') == worker['cameras']
        ids = [x['id'] for x in m['records']]
        check('nine_camera_ids', ids == [12, 13, 14, 18, 19, 20, 21, 22, 23]
              and np.array_equal(optical['ids'], ids) and set(actual_cameras) == set(ids))
        independently_interpolated = {}
        for slot, rec in enumerate(m['records']):
            i, t = rec['id'], ns(rec['rgb_timestamp_text'])
            j = bisect_left(times, t)
            assert 0 < j < len(rows)
            a, b = rows[j - 1], rows[j]
            fraction = (t - times[j - 1]) / (times[j] - times[j - 1])
            assert 0 <= fraction <= 1
            r0, r1 = Rotation.from_quat(np.array(a[4:], float)), Rotation.from_quat(np.array(b[4:], float))
            rotation = (r0 * Rotation.from_rotvec(fraction * (r0.inv() * r1).as_rotvec())).as_matrix()
            C = np.eye(4)
            C[:3, :3] = rotation
            C[:3, 3] = np.array(a[1:4], float) * (1 - fraction) + np.array(b[1:4], float) * fraction
            independently_interpolated[i] = C
            observed = actual_cameras[i]['rgb_camera']
            check('camera/' + str(i) + '/GT_brackets_and_time', observed['before'] == a and observed['after'] == b
                  and observed['timestamp'] == rec['rgb_timestamp_text'] and observed['gap_ns'] == times[j] - times[j - 1]
                  and observed['fraction'] == fraction and optical['rgb_timestamps_ns'][slot] == t)
            compare('camera/' + str(i) + '/independent_SO3_interpolation', optical['c2ws'][slot], C, 1e-10, 0)
            check('camera/' + str(i) + '/archive_matches_receipt', np.array_equal(optical['c2ws'][slot], observed['c2w']))
            if i in m['reused_camera_ids']:
                check('camera/' + str(i) + '/saved_reuse_exact', observed == saved_by_id[i]
                      and actual_cameras[i]['origin'] == 'S52_saved_RGB_camera_no_reinterpolation')
            else:
                check('camera/' + str(i) + '/new_origin', actual_cameras[i]['origin'] == 'new_S52_original_interpolation_at_RGB_time')
            report['cameras'].append(dict(id=i, rgb_timestamp_text=rec['rgb_timestamp_text'], bracket_gap_ns=times[j] - times[j - 1],
                                         fraction=fraction, origin=actual_cameras[i]['origin']))

        cache = {}
        for row in m['appearances']:
            old = metadata[str(R / ('work/S68_tum_vmem_cache_bridge/execution_01/history_' + str(row['history_id']) + '.json'))]
            assert all(row[k] == v for k, v in old.items())
            cache[row['history_id']] = npz(row['npz_path'], row['npz_sha256'], row['tensors'], 'S68_appearance_npz')
        expected_reads = [(str(D / 'INPUTS.json'), 'input_metadata', PINS['INPUTS.json'])]
        expected_reads += [(p, 'source', h) for p, h in m['source_sha256'].items()]
        expected_reads += [(p, 'existing_metadata' if p.endswith('.json') else 'existing_source_contract', h)
                           for p, h in m['metadata_sha256'].items()]
        expected_reads += [(gt['path'], 'GT_pose_text', gt['sha256'])]
        expected_reads += [(x['npz_path'], 'S68_appearance_npz', x['npz_sha256']) for x in m['appearances']]
        actual_reads = [(x['path'], x['kind'], x['sha256']) for x in worker['reads']]
        check('worker_exact_read_scope_24', actual_reads == expected_reads and len(actual_reads) == 24)
        check('worker_read_bytes_match_actual', all(x['bytes_read'] == len(loaded[x['path']]) for x in worker['reads'])
              and worker['gt_text_bytes_read'] == 1417998 and worker['appearance_npz_bytes_read'] == 440740)

        arms = {}
        shapes = {'crossattn': (8, 1, 1024), 'replace': (8, 5, 72, 72), 'concat': (8, 7, 72, 72), 'dense_vector': (8, 6, 72, 72)}
        for name, contexts in m['arms'].items():
            a = worker['arms'][name]
            check(name + '/complete', a['status'] == 'COMPLETE_ORIGINAL_CONDITION_ASSEMBLY'
                  and a['ordered_history_ids'] == contexts and a['target_ids'] == [20, 21, 22, 23])
            assert js(D / ('execution_01/' + name + '_receipt.json')) == a
            assert js(D / ('execution_01/' + name + '.json')) == a['output']
            z = npz(a['output']['path'], a['output']['sha256'], a['output']['fields'], 'S69_numeric_npz')
            arms[name] = z
            order = contexts + [20, 21, 22, 23]
            C64 = np.stack([independently_interpolated[i] for i in order])
            # Cast the authoritative archived values exactly as the original consumer.
            saved_C = np.stack([optical['c2ws'][ids.index(i)] for i in order]).astype(np.float32)
            check(name + '/ordered_ids_and_optical_cast', np.array_equal(z['ordered_ids'], order)
                  and np.array_equal(z['optical_c2ws_fp32'], saved_C))
            raw = saved_C.copy()
            raw[:, :, 1:3] *= -1
            check(name + '/local_basis_exact', np.array_equal(z['consumer_raw_c2ws'], raw))
            t = raw[:, :3, 3].copy()
            lower_median = np.sort(t, axis=0)[3]
            distances = np.sqrt(np.sum((t - lower_median) ** 2, axis=1, dtype=np.float32))
            cutoff = min(float(np.quantile(distances, .97, method='linear')) * 10, 1e6)
            valid = distances <= cutoff
            mu = np.mean(t[valid], axis=0, dtype=np.float32)
            centered = raw.copy()
            centered[:, :3, 3] -= mu
            first_distance = float(np.linalg.norm(centered[0, :3, 3]))
            expected_scale = 2.0 if first_distance <= 1e-5 else 2.0 / first_distance + .01
            scale = float(z['scale'].reshape(-1)[0])
            check(name + '/scale_shape_finite', z['scale'].shape == (1,) and np.isfinite(scale) and scale > 0)
            compare(name + '/independent_centering', z['centered_consumer_c2ws'], centered)
            compare(name + '/independent_natural_scale', np.array(scale), np.array(expected_scale))
            check(name + '/receipt_scale_exact', scale == a['scale'])
            expected_post = centered.copy()
            expected_post[:, :, 1:3] *= -1
            expected_post[:, :3, 3] *= np.float32(scale)
            compare(name + '/post_cond_optical', z['post_cond_optical_c2ws'], expected_post)
            K = np.stack([cache[i]['K_pixels_576'] for i in contexts] + [cache[19]['K_pixels_576']] * 4)
            check(name + '/all_K_exact', np.array_equal(K, z['K_pixels_576']))
            check(name + '/mask_exact', z['input_masks'].dtype == np.bool_ and np.array_equal(z['input_masks'], [True] * 4 + [False] * 4))
            L, E = np.stack([cache[i]['latent'] for i in contexts]), np.stack([cache[i]['embedding'] for i in contexts])
            check(name + '/cache_slots_exact', np.array_equal(z['context_latents'], L) and np.array_equal(z['context_embeddings'], E))
            for group in ['c', 'uc']:
                for field, shape in shapes.items():
                    value = z[group + '__' + field]
                    check(name + '/' + group + '/' + field + '/layout', value.shape == shape and value.dtype == np.float32)
            expected_replace = np.zeros((8, 5, 72, 72), np.float32)
            expected_replace[:4, :4], expected_replace[:4, 4] = L, 1
            check(name + '/replace_slots_and_placeholders', np.array_equal(z['c__replace'], expected_replace))
            check(name + '/unconditional_appearance_zero', np.count_nonzero(z['uc__replace']) == 0 and np.count_nonzero(z['uc__crossattn']) == 0)
            mean = E.astype(np.float64).sum(axis=0) / 4
            compare(name + '/CLIP_mean', z['c__crossattn'], np.broadcast_to(mean, (8, 1, 1024)))
            check(name + '/ray_aliases_and_concat_masks', np.array_equal(z['c__dense_vector'], z['uc__dense_vector'])
                  and np.array_equal(z['c__concat'][:, 1:], z['c__dense_vector'])
                  and np.array_equal(z['uc__concat'][:, 1:], z['c__dense_vector'])
                  and np.array_equal(z['c__concat'][:, 0], np.broadcast_to(z['input_masks'][:, None, None], (8, 72, 72)))
                  and np.count_nonzero(z['uc__concat'][:, 0]) == 0)
            # Independent relative camera ray construction, not inverse extrinsics helpers.
            y, x = np.meshgrid(np.arange(72) + .5, np.arange(72) + .5, indexing='ij')
            pixels = np.stack([x, y, np.ones_like(x)], axis=-1)
            source_R, source_t = C64[0, :3, :3], C64[0, :3, 3]
            predicted = []
            for slot in range(8):
                K72 = K[slot].copy()
                K72[:2] /= np.float32(576)
                K72[:2] *= np.float32(72)
                local = pixels @ np.linalg.inv(K72.astype(np.float64)).T
                direction = local @ (source_R.T @ C64[slot, :3, :3]).T
                direction /= np.linalg.norm(direction, axis=-1, keepdims=True)
                center = scale * (source_R.T @ (C64[slot, :3, 3] - source_t))
                moment = np.cross(center, direction)
                predicted.append(np.concatenate([direction, moment], axis=-1).transpose(2, 0, 1))
            predicted = np.stack(predicted)
            for slot, i in enumerate(order):
                compare(name + '/ray/' + str(slot) + '_id' + str(i), z['c__dense_vector'][slot], predicted[slot])
            dirs, moments = z['c__dense_vector'][:, :3], z['c__dense_vector'][:, 3:]
            compare(name + '/ray_unit', np.linalg.norm(dirs.astype(np.float64), axis=1), np.ones((8, 72, 72)), 2e-5, 0)
            compare(name + '/direction_moment_dot', np.sum(dirs.astype(np.float64) * moments, axis=1), np.zeros((8, 72, 72)), 2e-5, 0)
            report['arms'][name] = dict(ordered_ids=order, scale=scale, independently_expected_scale=expected_scale,
                                      center_mean=mu.tolist(), valid_indices=np.flatnonzero(valid).tolist(),
                                      lower_median=lower_median.tolist(), cutoff=cutoff,
                                      npz_path=a['output']['path'], npz_sha256=a['output']['sha256'])

        A, B = arms['geometry'], arms['pose14']
        check('both_arms_same_raw_target_C_K', np.array_equal(A['optical_c2ws_fp32'][4:], B['optical_c2ws_fp32'][4:])
              and np.array_equal(A['consumer_raw_c2ws'][4:], B['consumer_raw_c2ws'][4:])
              and np.array_equal(A['K_pixels_576'][4:], B['K_pixels_576'][4:]))
        report['predictions']['target_directions'] = compare('prediction/target_directions', A['c__dense_vector'][4:, :3], B['c__dense_vector'][4:, :3], 1e-5, 1e-5, False)
        report['predictions']['target_moment_over_scale'] = compare('prediction/target_moment_over_scale',
            A['c__dense_vector'][4:, 3:].astype(np.float64) / float(A['scale'][0]),
            B['c__dense_vector'][4:, 3:].astype(np.float64) / float(B['scale'][0]), 1e-5, 1e-5, False)
        expected_delta = (cache[12]['embedding'].astype(np.float64) - cache[14]['embedding'].astype(np.float64)) / 4
        report['predictions']['crossattn_replacement'] = compare('prediction/crossattn_replacement',
            A['c__crossattn'].astype(np.float64) - B['c__crossattn'].astype(np.float64),
            np.broadcast_to(expected_delta, (8, 1, 1024)), 1e-5, 1e-5, False)
        report['observed_between_arm_changes'] = {
            k: dict(max_abs_difference=float(np.max(np.abs(A[k].astype(np.float64) - B[k].astype(np.float64)))),
                    different_elements=int(np.count_nonzero(A[k] != B[k])), total_elements=int(A[k].size))
            for k in ['c__crossattn', 'c__replace', 'c__concat', 'c__dense_vector', 'uc__crossattn', 'uc__replace', 'uc__concat', 'uc__dense_vector']}
        expected_files = {'receipt.json', 'optical_cameras.npz', 'optical_cameras.json', 'camera_interpolation.json',
                          'geometry.npz', 'geometry.json', 'geometry_receipt.json', 'pose14.npz', 'pose14.json', 'pose14_receipt.json'}
        check('exact_readonly_result_namespace', {p.name for p in (D / 'execution_01').iterdir()} == expected_files
              and all(stat.S_IMODE(p.stat().st_mode) == 0o444 for p in (D / 'execution_01').iterdir()))
        report['evidence'] = dict(worker=dict(path=str(D / 'execution_01/receipt.json'), sha256=INNER),
                                  external=dict(path=str(D / 'external_01/receipt.json'), sha256=OUTER),
                                  original_elapsed_seconds=outer['elapsed_seconds'], original_started_utc=outer['started_utc'],
                                  original_completed_utc=outer['completed_utc'], source_pins=PINS)
        report['status'] = 'PASS_S69_INDEPENDENT_CAMERA_CONDITIONING_RESULT_REVIEW' if not report['blockers'] else 'BLOCKED_S69_INDEPENDENT_CAMERA_CONDITIONING_RESULT_REVIEW'
    except BaseException as e:
        report['blockers'].append(type(e).__name__ + ': ' + str(e))
        report['exception'] = traceback.format_exc()
        report['status'] = 'BLOCKED_S69_INDEPENDENT_CAMERA_CONDITIONING_RESULT_REVIEW'
    finally:
        report.update(completed_utc=utc(), elapsed_seconds=time.monotonic() - started,
                      actual_unique_read_count=len(report['reads']), actual_bytes=sum(x['bytes'] for x in report['reads']))
        report['read_scope_totals'] = {k: dict(files=sum(x['kind'] == k for x in report['reads']),
                                              bytes=sum(x['bytes'] for x in report['reads'] if x['kind'] == k))
                                     for k in sorted({x['kind'] for x in report['reads']})}
        report['scientific_file_bytes'] = sum(x['bytes'] for x in report['reads']
                                              if x['kind'] in ['GT_pose_text', 'S68_appearance_npz', 'S69_numeric_npz'])
        report['limits'] = ['Team-internal different-author saved-result verification, not external model reproduction.',
                            'GT interpolation and approximate K/no-undistortion contract only; not physical optical calibration.',
                            'Known post-selection contexts and previously exposed target RGB; no online retrieval, new generation, score or novel method.']
        path = out / 'numeric_verification.json'
        with path.open('x') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\n')
        path.chmod(0o444)
    print(json.dumps(dict(status=report['status'], blockers=report['blockers'], report=str(path), sha256=digest(path.read_bytes()))))
    return 0 if not report['blockers'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
