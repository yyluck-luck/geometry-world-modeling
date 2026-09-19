"""Independent integer-arithmetic verification of S70's fixed emitted-RGB score."""
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import time
import traceback
from datetime import datetime, timezone

D = Path(__file__).resolve().parent
CONTRACT_SHA = 'a776fd9cc1af9014de2e9226364f8990e9a2461c45b23aa6e03e5354370df8ac'
SCORER_SHA = '4c698efddeca50a2c35812632516ca458ab0f1a8f9dec8f4aa4cdde0f1584ab5'
IDS = [20, 21, 22, 23]
ARMS = ('A0', 'A1', 'B')
POINTS_YX = [(0,0), (0,575), (575,0), (575,575), (288,288),
             (123,234), (421,197), (96,96), (479,479)]
ATOL = RTOL = 1e-12


def require(value, message):
    if not value:
        raise RuntimeError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    if sys.argv[1:] == ['--compile-only']:
        compile(Path(__file__).read_bytes(), str(Path(__file__)), 'exec')
        print('PASS_COMPILE_ONLY_NO_SCIENTIFIC_READ')
        return 0
    require(len(sys.argv) == 2, 'Expected exact ROOT_RGB_VERIFY_BINDING.json SHA')
    out = D/'rgb_verification_01'
    out.mkdir()  # Preserve every created result/failure; never reuse this directory.
    start = time.monotonic()
    report = dict(schema='s70-independent-integer-rgb-verification-v1', status='RUNNING',
                  started_utc=utc(), verifier_sha256=digest(Path(__file__).read_bytes()),
                  binding_sha256=sys.argv[1], contract_sha256=CONTRACT_SHA,
                  reads=[], comparisons=[], frames=[], target_ids=IDS,
                  new_method_validated=False, generated_or_reference_images_viewed=False)

    def read(path, expected, kind):
        raw = Path(path).read_bytes()
        actual = digest(raw)
        report['reads'].append(dict(path=str(path), sha256=actual, bytes=len(raw), kind=kind))
        require(actual == expected, 'File SHA differs: '+str(path))
        return raw

    def close(label, actual, expected):
        if actual == 'Infinity':
            passed = expected == 'Infinity'
            error = None
        else:
            passed = (isinstance(expected, (int,float)) and not isinstance(expected, bool)
                      and math.isfinite(expected) and math.isfinite(actual)
                      and abs(actual-expected) <= ATOL+RTOL*abs(expected))
            error = abs(actual-expected) if isinstance(expected, (int,float)) else None
        report['comparisons'].append(dict(field=label, independent=actual, scored=expected,
                                          absolute_error=error, passed=passed))
        require(passed, 'Score differs: '+label)

    def load(path, expected, shape, dtype, kind):
        raw = read(path, expected, kind)
        array = np.load(io.BytesIO(raw), allow_pickle=False)
        require(isinstance(array,np.ndarray) and list(array.shape) == shape
                and array.dtype == np.dtype(dtype) and np.isfinite(array).all(),
                'Array type/shape/dtype/finite differs: '+str(path))
        return array

    def integer_score(a, b):
        # Every difference and squared accumulation is int64; the largest sum is below2^63.
        delta = a.astype(np.int64)-b.astype(np.int64)
        squared_sum = int(np.sum(delta*delta, dtype=np.int64))
        count = int(a.size)
        return dict(squared_integer_sum=squared_sum, channel_value_count=count,
                    denominator=count*255*255, mse=squared_sum/(count*255*255))

    def decibels(value):
        return 'Infinity' if value == 0 else -10*math.log10(value)

    try:
        binding = json.loads(read(D/'ROOT_RGB_VERIFY_BINDING.json', sys.argv[1], 'verification_binding'))
        require(binding['status'] == 'ACCEPTED_S70_SCORED_OUTPUTS_FOR_INDEPENDENT_RGB_VERIFY',
                'Score has not been bound for independent verification')
        source_map = binding['source_files_sha256']
        require(source_map[str(Path(__file__).resolve())] == report['verifier_sha256'], 'Unbound verifier')
        require(str(D/'RGB_VERIFY_PLAN.md') in source_map, 'Missing frozen verification plan')
        for path, expected in source_map.items():
            read(path, expected, 'bound_verification_source')
        contract = json.loads(read(D/'SCORING_CONTRACT.json', CONTRACT_SHA, 'fixed_scoring_contract'))
        read(D/'score_fixed_contexts.py', SCORER_SHA, 'score_interface_source_not_executed')
        old_binding = json.loads(read(D/'ROOT_SCORING_BINDING.json',
                                      binding['root_scoring_binding_sha256'], 'original_scoring_binding'))
        score = json.loads(read(D/'scoring_01/receipt.json', binding['score_receipt_sha256'],
                               'sealed_score_receipt'))
        require(old_binding['status'] == 'ACCEPTED_S70_COMPLETE_GENERATION_FOR_FIXED_SCORING'
                and old_binding['target_ids'] == IDS and contract['target_ids'] == IDS
                and old_binding['ordered_reference_ids'] == contract['arms']
                and list(contract['arms']) == list(ARMS)
                and contract['arms'] == dict(A0=[19,18,13,12],A1=[19,18,13,12],B=[19,18,14,13]),
                'Fixed targets/arms or generation acceptance changed')
        require(score['status'] == 'COMPLETE_FIXED_RGB_SCORE_PENDING_INDEPENDENT_RECOMPUTE'
                and score['contract_sha256'] == CONTRACT_SHA and score['scorer_sha256'] == SCORER_SHA
                and score['binding_sha256'] == binding['root_scoring_binding_sha256']
                and score['target_ids'] == IDS and len(score['frames']) == 4
                and [f['target_id'] for f in score['frames']] == IDS,
                'Sealed score identity or complete frame order differs')
        from importlib.metadata import version
        import numpy as np
        from PIL import Image
        report['versions'] = {k:version(k) for k in ('numpy','pillow')}
        require(report['versions'] == {'numpy':'1.26.4','pillow':'10.3.0'}, 'Numeric/PIL versions differ')
        report['python_version'] = sys.version
        files = old_binding['result_files_sha256']
        predictions = {}
        for arm in ARMS:
            path = D/'execution_01'/arm/'targets_uint8.npy'
            predictions[arm] = load(path, files[str(path)], [4,576,576,3], 'uint8', 'emitted_RGB_array')
        replay = {}
        for name, shape, field in [('all8_latents.npy',[8,4,72,72],'full8_latent_bytes_equal'),
                                  ('targets_fp32.npy',[4,3,576,576],'four_raw_FP32_RGB_bytes_equal')]:
            pair = []
            for arm in ('A0','A1'):
                path = D/'execution_01'/arm/name
                pair.append(load(path, files[str(path)], shape, 'float32',
                                 'raw_generated_RGB_array' if 'targets' in name else 'generated_latent_array'))
            replay[field] = pair[0].tobytes(order='C') == pair[1].tobytes(order='C')
        replay['four_emitted_uint8_RGB_bytes_equal'] = (
            predictions['A0'].tobytes(order='C') == predictions['A1'].tobytes(order='C'))
        replay['all_passed'] = all(replay.values())
        report['replay'] = replay
        require(replay == score['replay'], 'Exact raw replay status differs')
        refpath = D/'scoring_01/transformed_targets_uint8.npy'
        references = load(refpath, score['outputs_before_receipt'][refpath.name]['sha256'],
                          [4,576,576,3], 'uint8', 'saved_transformed_reference_RGB_array')
        report['reference_support_checks'] = []
        require([item['id'] for item in contract['targets']] == IDS, 'Reference identity order changed')
        for i, item in enumerate(contract['targets']):
            png = read(item['path'], item['sha256'], 'original_known_reference_PNG')
            require(item['native_wh'] == [640,480], 'Native geometry changed')
            with Image.open(io.BytesIO(png)) as image:
                require(image.mode == 'RGB' and image.size == (640,480), 'Native RGB PNG geometry differs')
                native = np.array(image)
            require(native.shape == (480,640,3) and native.dtype == np.uint8, 'Native decoded RGB differs')
            for y,x in POINTS_YX:
                # Independent adaptive-area bin boundaries: floor(start), ceil(end), crop x+96.
                y0, y1 = y*480//576, ((y+1)*480+575)//576
                x0, x1 = (x+96)*640//768, ((x+97)*640+767)//768
                count = (y1-y0)*(x1-x0)
                summed = native[y0:y1,x0:x1].astype(np.int64).sum(axis=(0,1),dtype=np.int64)
                ideal_uint8 = summed//count
                actual = references[i,y,x].astype(np.int64)
                error = np.abs(actual-ideal_uint8)
                row = dict(target_id=item['id'], y=y, x=x, native_support_yx=[y0,y1,x0,x1],
                           support_count=count, integer_sum=summed.tolist(),
                           exact_mean_truncated=ideal_uint8.tolist(), saved_uint8=actual.tolist(),
                           absolute_levels=error.tolist(), passed=bool(np.all(error<=1)))
                report['reference_support_checks'].append(row)
                require(row['passed'], 'Frozen reference area/crop support spot check failed')
        aggregate_sums = {arm:0 for arm in ARMS}
        total_count = 0
        for i, target_id in enumerate(IDS):
            reference = references[i]
            current = score['frames'][i]
            independently = {arm:integer_score(predictions[arm][i],reference) for arm in ARMS}
            count = reference.size
            require(count == 576*576*3, 'Incomplete full-frame count')
            total_count += count
            for arm in ARMS:
                row = independently[arm]
                aggregate_sums[arm] += row['squared_integer_sum']
                close(f'{target_id}/{arm}/mse', row['mse'], current['mse'][arm])
                close(f'{target_id}/{arm}/psnr', decibels(row['mse']), current['psnr'][arm])
            delta_numerator = independently['B']['squared_integer_sum']-independently['A0']['squared_integer_sum']
            delta = delta_numerator/(count*255*255)
            close(f'{target_id}/delta_B_minus_A0', delta, current['delta_B_minus_A0'])
            diagnostics = dict(replay_emitted_mse=integer_score(predictions['A0'][i],predictions['A1'][i]),
                               replacement_emitted_mse=integer_score(predictions['A0'][i],predictions['B'][i]))
            for key,value in diagnostics.items():
                close(f'{target_id}/{key}', value['mse'], current[key])
            report['frames'].append(dict(target_id=target_id, scores=independently,
                delta_B_minus_A0=delta, signed_integer_delta=delta_numerator, diagnostics=diagnostics))
        require(total_count == 4*576*576*3, 'Missing aggregate channel values')
        denominator = total_count*255*255
        means = {arm:aggregate_sums[arm]/denominator for arm in ARMS}
        for arm in ARMS:
            close(f'aggregate/{arm}/mse', means[arm], score['mean_frame_mse'][arm])
            close(f'aggregate/{arm}/psnr', decibels(means[arm]), score['psnr_from_mean_frame_mse'][arm])
        signed_integer_delta = aggregate_sums['B']-aggregate_sums['A0']
        signed_delta = signed_integer_delta/denominator
        close('aggregate/delta_B_minus_A0', signed_delta, score['delta_B_minus_A0'])
        support = bool(signed_integer_delta>0) if replay['all_passed'] else None
        require(score['context_comparison_interpretable'] is replay['all_passed']
                and score['fixed_case_higher_support_lower_emitted_rgb_error'] is support
                and score['new_method_validated'] is False and score['limits'] == contract['limits'],
                'Strict signed/replay/claim boundary differs')
        report.update(status='PASS_INDEPENDENT_INTEGER_RGB_SCORE', mean_frame_mse=means,
            total_channel_values=total_count, normalization_denominator=denominator,
            aggregate_squared_integer_sums=aggregate_sums, signed_integer_delta=signed_integer_delta,
            delta_B_minus_A0=signed_delta, fixed_case_higher_support_lower_emitted_rgb_error=support,
            tolerance=dict(absolute=ATOL,relative=RTOL),
            reference_validation_scope='36 fixed pixels/108 channels, not full preprocessing reproduction',
            neural_reproduction=False, full_prediction_emission_recomputed=False,
            limits=contract['limits'])
        require(time.monotonic()-start <= 120, 'Verification120s budget exceeded')
    except Exception as error:
        report.update(status='FAILED_PRESERVED', error_type=type(error).__name__, error=str(error),
                      traceback=traceback.format_exc())
    report.update(completed_utc=utc(), elapsed_seconds=time.monotonic()-start,
                  actual_input_bytes=sum(row['bytes'] for row in report['reads']))
    with (out/'receipt.json').open('x') as stream:
        json.dump(report,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write('\n')
    (out/'receipt.json').chmod(0o444)
    print(json.dumps(dict(status=report['status'],receipt=str(out/'receipt.json'))))
    return 0 if report['status'] == 'PASS_INDEPENDENT_INTEGER_RGB_SCORE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
