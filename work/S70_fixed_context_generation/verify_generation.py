"""Verify a completed S70 generation from saved evidence; never load a neural model."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
import re
import stat
import sys
import time
import traceback

D = Path(__file__).absolute().parent
R = D.parents[1]
ARMS = ('A0', 'A1', 'B')
PIN = {
    'generate_fixed_contexts.py': 'ba3a5fb9954e10b51bc56b717fe3de213728560f5dd3c6bc7e319594f1391b92',
    'INPUTS.json': '2a5551e348f1f389ef44ca6fac7d47e8853b44772884cbd38cecb0064a6e80e7',
    'PROTOCOL.md': '59841e88324b86d784dfc584ea731be2138618f18dd758ac9d22341e7f4e008d',
    'AUTHOR_DELIVERY.json': '73ed164b183f7da80b0c1186e0beb027d0b7a5a2f7a174eaac9dd0e0c864193d',
    'observe_generation.py': '39b1de2db3a04c21c4fe138a44a4510f1b6fef212a2e2822eba2b5f0d4aa67c3',
    'SOURCE_REVIEW.json': '795e546c6c6d90eac21fb7eb0f450ff3c619805dd5bb7f186ac17abf4a475939',
    'PROTOCOL_FIELD_COUNT_ERRATUM.json': '7098b7a284912a6558228a8d082c83d0f6cb6ef825c624e4ca9836c3ff7173e6',
    'QUANTIZER_METADATA_BOUNDARY.json': '2d564dcf619100e768717bbc54f96b54bfc13376da4f02a628e55b6ff3e5136a',
    'ROOT_RUN_BINDING.json': '9aa55530c48ee122485e73bdd5760420a92fd57d010d28a25cf797526ed05735',
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def main():
    if sys.argv[1:] == ['--compile-only']:
        compile(Path(__file__).read_bytes(), str(Path(__file__)), 'exec')
        print('COMPILE_ONLY_NO_GENERATION_PAYLOAD_READ')
        return 0
    assert len(sys.argv) == 3 and all(re.fullmatch('[0-9a-f]{64}', s) for s in sys.argv[1:]), \
        'Pass actual completed external receipt SHA then actual worker receipt SHA'
    outer_sha, worker_sha = sys.argv[1:]
    out = D / 'generation_verification_01'
    out.mkdir(exist_ok=False)
    begin = time.monotonic()
    report = dict(schema='s70-independent-generation-verification-v1', status='RUNNING',
                  verifier_author_role='/root/c2_v9_source_primary', started_utc=utc(),
                  verifier_sha256=sha(Path(__file__).read_bytes()), actual_outer_sha256=outer_sha,
                  actual_worker_sha256=worker_sha, checks=[], reads=[], blockers=[], arms={},
                  weight_body_bytes=0, reference_RGB_or_depth_bytes=0, model_instances=0,
                  original_sampling_or_decode_calls=0, generated_images_viewed=False,
                  new_method_validated=False)
    bodies = {}

    def read(path, expected=None, kind='metadata'):
        path = Path(path)
        key = str(path)
        if key not in bodies:
            with path.open('rb') as f:
                before = os.fstat(f.fileno())
                body = f.read()
                after = os.fstat(f.fileno())
            assert (before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns), key
            bodies[key] = body
            report['reads'].append(dict(path=key, sha256=sha(body), bytes=len(body), kind=kind,
                                       mode=format(stat.S_IMODE(path.stat().st_mode), '04o')))
        body = bodies[key]
        assert expected is None or sha(body) == expected, key
        return body

    def js(path, expected=None, kind='metadata'):
        return json.loads(read(path, expected, kind))

    def check(name, passed, detail=None):
        passed = bool(passed)
        report['checks'].append(dict(name=name, passed=passed, detail=detail))
        if not passed:
            report['blockers'].append(name)
        return passed

    def require(name, passed, detail=None):
        if not check(name, passed, detail):
            raise RuntimeError(name)

    def described_json(record, expected_path):
        require(str(expected_path) + '/path_binding', record['path'] == str(expected_path))
        body = read(expected_path, record['sha256'])
        require(str(expected_path) + '/file_size', len(body) == record['size_bytes'])
        return json.loads(body)

    try:
        import numpy as np
        require('reviewer_runtime', sys.version_info[:2] == (3, 12) and np.__version__ == '1.26.4')
        report['versions'] = dict(python=sys.version, numpy=np.__version__)
        for n, h in PIN.items():
            read(D / n, h, 'reviewed_source_or_contract')
        manifest = js(D / 'INPUTS.json', PIN['INPUTS.json'])
        outer = js(D / 'external_01/receipt.json', outer_sha, 'actual_terminal_metadata')
        worker = js(D / 'execution_01/receipt.json', worker_sha, 'actual_terminal_metadata')
        require('actual_outer_completion', outer['returncode'] == 0 and outer['stop_reason'] is None
                and outer['observer_error'] is None and outer['worker_receipt_sha256'] == worker_sha)
        require('actual_worker_completion', worker['status'] == 'COMPLETE_THREE_FIXED_GENERATION_ARMS'
                and outer['worker_status'] == worker['status'] and worker['unrun_arms'] == [])
        require('actual_executable_and_input', worker['executable_sha256'] == PIN['generate_fixed_contexts.py']
                and worker['input_sha256'] == PIN['INPUTS.json'] and outer['observer_sha256'] == PIN['observe_generation.py'])
        require('actual_argv', outer['argv'] == [str(R / '.venv-cut3r/bin/python'), '-B', str(D / 'generate_fixed_contexts.py')])
        require('actual_fixed_controls', worker['controls'] == manifest['controls']
                and worker['variant'] == manifest['variant'] and worker['versions'] == manifest['versions']
                and worker['target_ids'] == [20, 21, 22, 23])
        require('declared_generation_exposure_boundary', worker['reference_rgb_body_bytes'] == 0
                and worker['reference_depth_body_bytes'] == 0 and worker['generated_rgb_viewed'] is False
                and worker['claim_boundary'] == manifest['claim_boundary'])
        binding = js(D / 'ROOT_RUN_BINDING.json', outer['binding_sha256'], 'actual_run_binding')
        require('bound_argv', binding['argv'] == outer['argv'])
        for p, h in binding['reviewed_files_sha256'].items():
            require('root_binding_source_metadata_only/' + p, Path(p).suffix in {'.py', '.json', '.md'})
            read(p, h, 'reviewed_source_or_contract')
        stdout = read(D / 'external_01/stdout.txt', outer['stdout_sha256'], 'terminal_output')
        read(D / 'external_01/stderr.txt', outer['stderr_sha256'], 'terminal_output')
        last = json.loads(stdout.decode().splitlines()[-1])
        require('worker_stdout_completion', last['status'] == worker['status']
                and last['receipt'] == str(D / 'execution_01/receipt.json'))
        started = js(D / 'external_01/started.json')
        require('external_started_binding', all(outer[k] == v for k, v in started.items()))
        monitor = [json.loads(s) for s in read(D / 'external_01/monitor.jsonl', kind='resource_trace').splitlines()]
        require('actual_resources_recorded', outer['rss_samples'] > 0 and len(monitor) > 0
                and outer['sampled_peak_process_tree_rss_bytes'] <= 45 * 1024**3
                and outer['elapsed_seconds'] <= 5521
                and outer['total_seconds_limit'] == 5520 and outer['per_arm_seconds_limit'] == 1800
                and outer['rss_limit_bytes'] == 45 * 1024**3 and outer['free_disk_min_bytes'] == 10 * 1024**3)
        require('stored_resource_samples_within_limits', all(x['rss_bytes'] <= outer['sampled_peak_process_tree_rss_bytes']
                and x['disk_free_bytes'] >= 10 * 1024**3 for x in monitor))
        require('worker_boundary_resources', worker['peak_self_rss_bytes'] <= 45 * 1024**3
                and worker['elapsed_seconds'] <= 5520)
        try:
            os.kill(outer['pid'], 0)
        except ProcessLookupError:
            check('registered_worker_exited', True)
        else:
            check('registered_worker_exited', False, 'PID exists; possible PID reuse requires separate identity check')
        for p, h in manifest['source_sha256'].items():
            read(p, h, 'original_source')
        for p, h in manifest['metadata_sha256'].items():
            read(p, h, 'accepted_input_metadata')
        require('three_arm_order', manifest['arm_order'] == [['A0', 'geometry'], ['A1', 'geometry'], ['B', 'pose14']]
                and list(worker['arms']) == list(ARMS))

        def array_descriptor(a):
            a = np.ascontiguousarray(a)
            return dict(shape=list(a.shape), dtype=str(a.dtype), body_bytes=a.nbytes,
                        body_sha256=sha(memoryview(a).cast('B')))

        def load_array(desc, expected_path, shape, dtype, kind):
            require(str(expected_path) + '/path', desc['path'] == str(expected_path))
            body = read(expected_path, desc['file_sha256'], kind)
            a = np.load(io.BytesIO(body), allow_pickle=False)
            require(str(expected_path) + '/shape_dtype_finite', isinstance(a, np.ndarray)
                    and list(a.shape) == shape and a.dtype == np.dtype(dtype) and np.isfinite(a).all())
            require(str(expected_path) + '/body_identity', all(desc[k] == v for k, v in array_descriptor(a).items()))
            return a

        for name, c in manifest['conditions'].items():
            body = read(c['path'], c['sha256'], 'accepted_condition_npz')
            require(name + '/condition_file_size', len(body) == c['size_bytes'])
            with np.load(io.BytesIO(body), allow_pickle=False) as z:
                require(name + '/condition_field_set18', set(z.files) == set(c['fields']) and len(z.files) == 18)
                for key in z.files:
                    a = z[key]
                    require(name + '/' + key + '/condition_descriptor', array_descriptor(a) == c['fields'][key] and np.isfinite(a).all())
                require(name + '/fixed_context_target_order', z['ordered_ids'].tolist() == manifest['ordered_history_ids'][name] + [20, 21, 22, 23]
                        and z['input_masks'].tolist() == [True] * 4 + [False] * 4)
        expected_reads = [(str(D / 'INPUTS.json'), 'input_metadata', PIN['INPUTS.json'], len(bodies[str(D / 'INPUTS.json')]))]
        expected_reads += [(p, 'accepted_metadata', h, len(bodies[p])) for p, h in manifest['metadata_sha256'].items()]
        expected_reads += [(p, 'original_source', h, len(bodies[p])) for p, h in manifest['source_sha256'].items()]
        expected_reads += [(c['path'], 'saved_S69_conditions', c['sha256'], c['size_bytes']) for c in manifest['conditions'].values()]
        for name, kind in [('vmem', 'vmem_weight'), ('vae_config', 'vae_config'), ('vae_weight', 'vae_weight')]:
            c = manifest['components'][name]
            expected_reads.append((c['path'], kind, c['sha256'], c['size']))
        require('actual_exact_worker_readlist', [(x['path'], x['kind'], x['sha256'], x['bytes']) for x in worker['reads']] == expected_reads)
        require('readlist_artifact_binding', described_json(worker['readlist'], D / 'execution_01/readlist.json') == worker['reads'])
        require('actual_model_load_discrepancies_empty', worker['vmem_loading_info'] == dict(missing_keys=[], unexpected_keys=[])
                and not any(worker['vae_loading_info'].get(k) for k in ['missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs']))
        require('VAE_decoder_one_bound_route', worker['vae_weight_decoder_calls'] == [str(D / 'execution_01/local_vae/diffusion_pytorch_model.safetensors')])
        local = D / 'execution_01/local_vae'
        require('VAE_local_config_identity', sha(read(local / 'config.json', manifest['components']['vae_config']['sha256'], 'copied_model_config'))
                == manifest['components']['vae_config']['sha256'])
        require('VAE_weight_link_only_stat', (local / 'diffusion_pytorch_model.safetensors').is_symlink()
                and str((local / 'diffusion_pytorch_model.safetensors').resolve()) == str(Path(manifest['components']['vae_weight']['path']).resolve()))
        baseline = described_json(worker['model_baseline'], D / 'execution_01/model_baseline.json')
        baseline_keys = ('value_sha256', 'identity_sha256', 'modes_sha256')
        for field, key in [('values', 'value_sha256'), ('identity', 'identity_sha256'), ('modes', 'modes_sha256')]:
            require('baseline/' + key + '/aggregate_consistency', sha(canonical(baseline[field])) == baseline[key])
        require('baseline_modes_frozen', all(not x[2] for x in baseline['modes'])
                and all(not x[-1] for x in baseline['identity']) and {x[0] for x in baseline['modes']} == {'vmem', 'vae'})
        require('baseline_value_descriptors', len(baseline['values']) == len(baseline['identity'])
                and all(re.fullmatch('[0-9a-f]{64}', x['body_sha256'])
                        and math.prod(x['shape']) * np.dtype(x['dtype']).itemsize == x['body_bytes'] for x in baseline['values']))
        common = described_json(worker['common_rng'], D / 'execution_01/common_rng.json')
        common_hash = sha(canonical(common))
        require('common_actual_rng_hash', common_hash == worker['common_rng_state_sha256'])
        require('actual_rng_state_schema', set(common) == {'python', 'numpy', 'torch_cpu'}
                and common['numpy']['engine'] == 'MT19937' and len(common['numpy']['keys']) == 624
                and len(common['torch_cpu']) > 0 and all(isinstance(x, int) and 0 <= x <= 255 for x in common['torch_cpu']))

        body_hashes, streams, decoded = {}, {}, {}
        for name, condition in manifest['arm_order']:
            a = worker['arms'][name]
            arm_dir = D / 'execution_01' / name
            require(name + '/complete_original_arm', a['status'] == 'COMPLETE_ARM' and a['arm'] == name and a['condition'] == condition
                    and a['condition_npz_sha256'] == manifest['conditions'][condition]['sha256']
                    and a['ordered_history_ids'] == manifest['ordered_history_ids'][condition]
                    and a['target_ids'] == [20, 21, 22, 23] and a['completed_steps'] == 50 and a['sampler_calls'] == 1)
            require(name + '/actual_full8_decode_and_budget', a['full_decoded_shape'] == [8, 3, 576, 576]
                    and a['full_decoded_dtype'] == 'torch.float32' and a['elapsed_seconds'] <= 1800)
            saved_receipt = described_json(a['receipt'], arm_dir / 'receipt.json')
            require(name + '/standalone_receipt_consistency', saved_receipt == {k: v for k, v in a.items() if k != 'receipt'})
            outputs = described_json(a['outputs'], arm_dir / 'outputs.json')
            require(name + '/outputs_binding', outputs['status'] == a['status'] and outputs['arm'] == name
                    and outputs['target_ids'] == [20, 21, 22, 23] and outputs['arrays'] == a['arrays']
                    and outputs['quantizer'] == a['quantizer'] and set(a['arrays']) == {'all8_latents', 'targets_fp32', 'targets_uint8'})
            require(name + '/model_value_identity_modes_unchanged', a['model_unchanged'] is True
                    and a['model_before'] == a['model_after'] == {k: baseline[k] for k in baseline_keys})
            require(name + '/actual_restored_full_rng_state', a['restored_rng_state_sha256'] == common_hash)
            entry = described_json(a['sampler_entry_rng'], arm_dir / 'sampler_entry_rng.json')
            terminal = described_json(a['terminal_rng'], arm_dir / 'terminal_rng.json')
            entry_hash, terminal_hash = sha(canonical(entry)), sha(canonical(terminal))
            require(name + '/entry_terminal_full_rng_identities', entry_hash == a['sampler_entry_rng_state_sha256']
                    and terminal_hash == a['terminal_rng_state_sha256'] and entry_hash != common_hash
                    and entry['python'] == terminal['python'] == common['python']
                    and entry['numpy'] == terminal['numpy'] == common['numpy'])
            steps = [json.loads(line) for line in read(arm_dir / 'steps.jsonl', kind='step_rng_trace').splitlines()]
            require(name + '/all50_actual_steps', steps == a['steps'] and [s['step'] for s in steps] == list(range(1, 51)))
            require(name + '/step_return_shapes_and_random_chain', all(s['finite'] is True
                    and s['shape'] == [8, 4, 72, 72] and s['dtype'] == 'torch.float32'
                    and s['rng_before'] != s['rng_after'] for s in steps)
                    and steps[0]['rng_before'] == entry_hash and steps[-1]['rng_after'] == terminal_hash
                    and all(x['rng_after'] == y['rng_before'] for x, y in zip(steps, steps[1:])))
            noise = load_array(a['noise'], arm_dir / 'noise.npy', [8, 4, 72, 72], 'float32', 'actual_initial_noise_array')
            arrays = {
                'all8_latents': load_array(a['arrays']['all8_latents'], arm_dir / 'all8_latents.npy', [8, 4, 72, 72], 'float32', 'generated_latent_array'),
                'targets_fp32': load_array(a['arrays']['targets_fp32'], arm_dir / 'targets_fp32.npy', [4, 3, 576, 576], 'float32', 'raw_generated_RGB_array'),
                'targets_uint8': load_array(a['arrays']['targets_uint8'], arm_dir / 'targets_uint8.npy', [4, 576, 576, 3], 'uint8', 'emitted_generated_RGB_array'),
            }
            decoded[name] = arrays
            body_hashes[name] = {k: array_descriptor(v)['body_sha256'] for k, v in arrays.items()}
            streams[name] = dict(noise=array_descriptor(noise)['body_sha256'], entry_rng=entry_hash,
                                 step_rng=[[s['rng_before'], s['rng_after']] for s in steps], terminal_rng=terminal_hash)
            emission = []
            require(name + '/quantizer_target_order', [x['target_id'] for x in a['quantizer']] == [20, 21, 22, 23])
            for slot, target_id in enumerate([20, 21, 22, 23]):
                image = arrays['targets_fp32'][slot].transpose(1, 2, 0)
                minimum = image.min()
                branch = bool(minimum < -.1)
                mapped = (image + 1) / 2 if branch else image
                expected = np.clip(mapped * 255, 0, 255).astype(np.uint8)
                require(name + '/' + str(target_id) + '/authoritative_original_emission',
                        expected.tobytes() == arrays['targets_uint8'][slot].tobytes())
                flag = a['quantizer'][slot]
                require(name + '/' + str(target_id) + '/reported_raw_minimum', flag['raw_min'] == float(minimum))
                advisory_disagrees = flag['maps_minus1_plus1'] is not branch
                require(name + '/' + str(target_id) + '/advisory_flag_disclosed_boundary_only',
                        not advisory_disagrees or (minimum == np.float32(-.1) and flag['maps_minus1_plus1'] is False and branch is True))
                emission.append(dict(target_id=target_id, raw_min=float(minimum), raw_max=float(image.max()),
                                     authoritative_numpy_rescale_branch=branch, advisory_torch_flag=flag['maps_minus1_plus1'],
                                     disclosed_boundary_difference=advisory_disagrees, exact_emitted_uint8=True))
            expected_files = {'noise.npy', 'sampler_entry_rng.json', 'all8_latents.npy', 'targets_fp32.npy',
                              'targets_uint8.npy', 'steps.jsonl', 'terminal_rng.json', 'outputs.json', 'receipt.json'}
            require(name + '/exact_readonly_arm_namespace', {p.name for p in arm_dir.iterdir()} == expected_files
                    and all(stat.S_IMODE(p.stat().st_mode) == 0o444 for p in arm_dir.iterdir()))
            report['arms'][name] = dict(condition=condition, ordered_history_ids=a['ordered_history_ids'],
                                       target_ids=a['target_ids'], completed_steps=50, noise_body_sha256=streams[name]['noise'],
                                       output_body_sha256=body_hashes[name], model_unchanged=True,
                                       restored_rng_state_sha256=common_hash, entry_rng_state_sha256=entry_hash,
                                       terminal_rng_state_sha256=terminal_hash, emission=emission,
                                       elapsed_seconds=a['elapsed_seconds'])

        shared = streams['A0'] == streams['A1'] == streams['B']
        require('3x50steps_shared_recorded_actual_random_stream', shared and worker['shared_actual_random_stream_pass'] is True)
        replay = {k: body_hashes['A0'][k] == body_hashes['A1'][k] for k in body_hashes['A0']}
        require('replay_field_reports_exact', replay == worker['exact_replay_fields']
                and all(replay.values()) is worker['exact_replay_pass']
                and worker['attributable_fixed_bundle_comparison'] is (shared and all(replay.values())))
        report['exact_replay_fields'] = replay
        report['exact_replay_pass'] = all(replay.values())
        report['attributable_fixed_bundle_comparison'] = shared and all(replay.values())
        report['output_differences'] = {}
        for k in body_hashes['A0']:
            for other in ['A1', 'B']:
                x, y = decoded['A0'][k], decoded[other][k]
                report['output_differences']['A0_vs_' + other + '/' + k] = dict(
                    byte_equal=body_hashes['A0'][k] == body_hashes[other][k],
                    different_value_count=int(np.count_nonzero(x != y)), total_values=int(x.size),
                    max_abs_difference=float(np.max(np.abs(x.astype(np.float64) - y.astype(np.float64)))))
        progress = [json.loads(s) for s in read(D / 'execution_01/progress.jsonl', worker['progress_sha256'], 'worker_progress').splitlines()]
        require('all_actual_progress_pid', all(x['pid'] == outer['pid'] for x in progress))
        require('complete_progress_end', progress[0]['phase'] == 'start' and progress[-1]['phase'] == 'complete'
                and progress[-1]['status'] == worker['status'] and not any(x['phase'] == 'failure' for x in progress))
        require('fixed_arm_progress_order', [x['arm'] for x in progress if x['phase'] == 'arm_start'] == list(ARMS)
                and [x['arm'] for x in progress if x['phase'] == 'arm_complete'] == list(ARMS))
        for name in ARMS:
            require(name + '/50_progress_steps', [x['step'] for x in progress if x['phase'] == 'step' and x['arm'] == name] == list(range(1, 51)))
        required_root = {'A0', 'A1', 'B', 'local_vae', 'progress.jsonl', 'model_baseline.json', 'common_rng.json', 'readlist.json', 'receipt.json'}
        require('exact_worker_root_namespace', {p.name for p in (D / 'execution_01').iterdir()} == required_root)
        require('completed_worker_files_readonly', all(stat.S_IMODE(p.stat().st_mode) == 0o444
                for p in (D / 'execution_01').rglob('*') if p.is_file() and not p.is_symlink()))
        require('verifier_final_120_second_budget', time.monotonic() - begin <= 120)
        report['evidence'] = dict(external_receipt=dict(path=str(D / 'external_01/receipt.json'), sha256=outer_sha),
                                  worker_receipt=dict(path=str(D / 'execution_01/receipt.json'), sha256=worker_sha),
                                  root_binding_sha256=outer['binding_sha256'], reviewed_source_sha256=PIN,
                                  worker_recorded_model_baseline=worker['model_baseline'],
                                  original_elapsed_seconds=outer['elapsed_seconds'], original_started_utc=outer['started_utc'],
                                  original_completed_utc=outer['completed_utc'], sampled_peak_tree_RSS=outer['sampled_peak_process_tree_rss_bytes'],
                                  worker_peak_self_RSS=worker['peak_self_rss_bytes'])
        report['status'] = 'PASS_S70_INDEPENDENT_GENERATION_RESULT_REVIEW' if not report['blockers'] else 'BLOCKED_S70_INDEPENDENT_GENERATION_RESULT_REVIEW'
    except BaseException as e:
        report['status'] = 'BLOCKED_S70_INDEPENDENT_GENERATION_RESULT_REVIEW'
        report['exception'] = traceback.format_exc()
        report['blockers'].append(type(e).__name__ + ': ' + str(e))
    finally:
        report.update(completed_utc=utc(), elapsed_seconds=time.monotonic() - begin,
                      actual_unique_read_count=len(report['reads']), actual_file_bytes=sum(x['bytes'] for x in report['reads']))
        report['read_scope_by_kind'] = {k: dict(files=sum(x['kind'] == k for x in report['reads']),
                                               bytes=sum(x['bytes'] for x in report['reads'] if x['kind'] == k))
                                      for k in sorted({x['kind'] for x in report['reads']})}
        report['limits'] = [
            'Different-author team-internal saved-result verification; no external neural reproduction.',
            'Model load/value immutability verifies consistency of actual worker-recorded byte hashes and audited consumption source; reviewer never reads/re-hashes model weight or parameter bodies.',
            'Recorded actual common/noise/step/terminal RNG agreement under fixed original draw path, not regeneration of every step epsilon.',
            'No reference RGB/depth is read and no image is displayed. Generated RGB arrays are explicitly read for byte identity and emission checks.',
            'Replay false can be accurately verified with PASS but attribution remains false; no retry or removal of B.',
            'No quality score, oldC2/cohort completion, online retrieval or novelty claim; original known-target/GT/approximateK/ft-mse boundaries remain.',
        ]
        with (out / 'receipt.json').open('x') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\n')
        (out / 'receipt.json').chmod(0o444)
    print(json.dumps(dict(status=report['status'], blockers=report['blockers'], receipt=str(out / 'receipt.json'))))
    return 0 if report['status'].startswith('PASS') else 2


if __name__ == '__main__':
    raise SystemExit(main())
