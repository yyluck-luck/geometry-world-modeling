#!/usr/bin/env python3
"""One sealed S87 scoring pass: all24 new rows,16 historical rows labelled.

No model, projection, registration, parameter fitting or prediction changes.
The fixed six-strategy envelope is explicitly retrospective and descriptive.
"""
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
             'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'
STRATEGIES = tuple((f'{family}_l{tag}', family, strength)
                  for tag, strength in [('050', .5), ('075', .75), ('100', 1.)]
                  for family in ('Gpaste', 'Gterminal'))
TARGETS = (20, 21, 22, 23)
REGIONS = ('full', 'support', 'hole')


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, why):
    if not bool(ok):
        raise ValueError(why)


def write_json(path, data):
    with path.open('x') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def quantize(np, raw):
    image = raw.transpose(1, 2, 0)
    branch = bool(image.min() < -.1)
    if branch:
        image = (image + 1) / 2.
    return np.clip(image * 255, 0, 255).astype(np.uint8), branch


def summarize(rows):
    result = {}
    for arm, family, strength in STRATEGIES:
        selected = [x for x in rows if x['arm'] == arm]
        require(len(selected) == 4, 'all four targets required')
        value = dict(family=family, strength=strength, status='COMPLETE')
        for region in REGIONS:
            sse = sum(x[region + '_sse'] for x in selected)
            count = sum(x[region + '_channels'] for x in selected)
            nonempty = all(not x[region + '_empty'] for x in selected)
            mean = (sse / (3981312 * 65025) if region == 'full' else
                    sum(x[region + '_mse'] for x in selected) / 4 if nonempty else None)
            value[region] = dict(total_sse=sse, total_channels=count,
                                 equal_frame_mean_mse=mean,
                                 pooled_mse=sse / (count * 65025) if count else None,
                                 complete_four_frames=nonempty)
        result[arm] = value
    return result


def main():
    cfg_raw = (HERE / 'SCORING_CONTRACT.json').read_bytes()
    cfg = json.loads(cfg_raw)
    require(sha(Path(__file__).read_bytes()) == cfg['scorer_sha256'], 'scorer identity')
    out = HERE / 'scoring_01'
    out.mkdir(exist_ok=False)
    began = time.monotonic()
    report = dict(status='STARTED', started_utc=utc(), reads=[], emission_checks=[],
                  scoring_contract_sha256=sha(cfg_raw), model_calls=0,
                  geometry_calls=0, new_method_validated=False, reference_reads=0)
    rows, code = [], 1

    def budget():
        require(time.monotonic() - began < 120, 'score time budget')
        require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 1024**3, 'score RSS budget')

    def read(path, digest=None):
        budget()
        data = Path(path).read_bytes()
        report['reads'].append(dict(path=str(path), bytes=len(data), sha256=sha(data), utc=utc()))
        require(digest is None or sha(data) == digest, 'input SHA: ' + str(path))
        return data

    def load(spec):
        return json.loads(read(spec['path'], spec['sha256']))

    def array(spec, shape, dtype, expected_path):
        require(spec['path'] == str(expected_path), 'array path identity')
        result = np.load(io.BytesIO(read(spec['path'], spec['file_sha256'])), allow_pickle=False)
        require(type(result) is np.ndarray and result.shape == shape and str(result.dtype) == dtype
                and result.flags.c_contiguous, 'array schema')
        require(spec['shape'] == list(shape) and spec['dtype'] == dtype
                and spec['body_bytes'] == result.nbytes
                and spec['body_sha256'] == sha(result.tobytes()), 'array body identity')
        result.flags.writeable = False
        return result

    def alarm(signum, frame):
        raise TimeoutError('score wall budget')

    previous = signal.signal(signal.SIGALRM, alarm)
    signal.alarm(120)
    try:
        import numpy as np
        require(np.__version__ == '1.26.4', 'NumPy version')
        binding_raw = read(HERE / 'ROOT_SCORING_BINDING.json')
        binding = json.loads(binding_raw)
        require(binding['accepted'] is True, 'root binding must be accepted')
        require(binding['scoring_contract_sha256'] == sha(cfg_raw), 'sealed scoring contract identity')
        graw = read(HERE / 'execution_01/RECEIPT.json', binding['generation_receipt_sha256'])
        g = json.loads(graw)
        contract = load(cfg['generation_contract'])
        require(g['contract_sha256'] == cfg['generation_contract']['sha256'], 'generation contract identity')
        require(contract['target_ids'] == list(TARGETS) and contract['history_ids'] == [19,18,13,12]
                and contract['interpretation']['fixed_seen_Gguide_total_SSE'] == 13571317266,
                'fixed generation question and slots')
        require(g['status'] == 'COMPLETE_SIX_DERIVED_CONTROLS_PENDING_REVIEW'
                and g['unrun_arms'] == [] and bool(g['completed_utc']), 'complete generation required')
        review = json.loads(read(HERE / 'INDEPENDENT_DERIVATIVE_REVIEW.json', binding['derivative_review_sha256']))
        require(review['status'] == 'PASS', 'independent derivative review PASS required')
        require(any(x['path'] == str(HERE / 'execution_01/RECEIPT.json') and x['sha256'] == sha(graw)
                    for x in review['reads']), 'review must bind this generation')
        names = [x[0] for x in STRATEGIES]
        require(set(g['arms']) == set(names), 'six exact strategies')
        require(g['order'] == names, 'fixed generation order')
        require(g['counts']['denoiser_calls'] == g['counts']['encoder_calls'] == 0
                and g['counts']['decoder_calls'] == 3 and g['counts']['decoder_chunks'] == 24
                and g['counts']['completed_decoder_chunks'] == 24
                and g['derived_rng_unchanged'] is True, 'actual call counts/RNG')
        old_summary = load(cfg['old_summary'])
        old_rows = load(cfg['old_rows'])
        old_csv = read(cfg['old_csv']['path'], cfg['old_csv']['sha256'])
        require(len(old_rows) == 16 and old_summary['Gguide']['full']['total_sse'] == 13571317266,
                'fixed historical16 and guide comparator')
        require([(x['arm'], x['target_id']) for x in old_rows] ==
                [(a, t) for a in ('G0', 'Gpaste', 'Gterminal', 'Gguide') for t in TARGETS],
                'historical row order')
        write_json(out / 'INPUT_BINDING.json', dict(recorded_utc=utc(),
                   root_binding_sha256=sha(binding_raw), generation_receipt_sha256=sha(graw),
                   derivative_review_sha256=binding['derivative_review_sha256'],
                   prediction_descriptors={a: g['arms'][a]['arrays'] for a in names},
                   mask_descriptor=g['image_mask'], scope='Before any arrays/reference read'))
        report['generation_receipt_sha256'] = sha(graw)
        mask = array(g['image_mask'], (4, 1, 576, 576), 'bool', Path(cfg['mask_path']))[:, 0]
        require([int(x.sum()) for x in mask] == [312396, 292217, 267572, 263594], 'fixed support counts')
        emitted = {}
        for arm, family, strength in STRATEGIES:
            item = g['arms'][arm]
            own = json.loads(read(HERE / 'execution_01' / arm / 'receipt.json'))
            require(item == own and item['status'] == 'COMPLETE_DERIVED' and bool(item['completed_utc'])
                    and item['family'] == family and item['strength'] == strength, 'strategy receipt')
            raw = array(item['arrays']['targets_fp32'], (4, 3, 576, 576), 'float32',
                        HERE / 'execution_01' / arm / 'targets_fp32.npy')
            actual = array(item['arrays']['targets_uint8'], (4, 576, 576, 3), 'uint8',
                           HERE / 'execution_01' / arm / 'targets_uint8.npy')
            require(np.isfinite(raw).all() and len(item['quantizer']) == 4, 'finite raw/full quantizer')
            if family == 'Gpaste':
                require(((raw >= 0) & (raw <= 1)).all(), 'paste RGB01')
            for i, target in enumerate(TARGETS):
                expected, branch = quantize(np, raw[i])
                require(expected.tobytes() == actual[i].tobytes(), 'exact raw to uint8 emission')
                info = dict(target_id=target, raw_min=float(raw[i].min()), raw_max=float(raw[i].max()),
                            maps_minus1_plus1=branch)
                require(all(item['quantizer'][i][k] == v for k, v in info.items()), 'quantizer fields')
                report['emission_checks'].append(dict(arm=arm, **info, exact_uint8_match=True))
            emitted[arm] = actual
            del raw
        require(len(report['emission_checks']) == 24, 'validate all24 before reference')
        read(HERE / 'execution_01/RECEIPT.json', sha(graw))
        ref = cfg['reference']
        reference_raw = read(ref['path'], ref['sha256'])
        require(len(reference_raw) == ref['bytes'], 'reference bytes')
        reference = np.load(io.BytesIO(reference_raw), allow_pickle=False)
        require(reference.shape == (4, 576, 576, 3) and reference.dtype == np.uint8, 'reference schema')
        report['reference_reads'] = 1
        for arm, family, strength in STRATEGIES:
            for i, target in enumerate(TARGETS):
                diff = emitted[arm][i].astype(np.int64) - reference[i].astype(np.int64)
                squares = diff * diff
                s = int(mask[i].sum())
                values = [(331776, int(squares.sum())), (s, int(squares[mask[i]].sum())),
                          (331776 - s, int(squares[~mask[i]].sum()))]
                require(values[0][1] == values[1][1] + values[2][1], 'SSE partition')
                row = dict(batch='S87', arm=arm, family=family, strength=strength,
                           target_id=target, status='COMPLETE', missing_reason='')
                for region, (pixels, sse) in zip(REGIONS, values):
                    count = 3 * pixels
                    row.update({region+'_pixels':pixels, region+'_channels':count, region+'_sse':sse,
                                region+'_mse':sse/(count*65025) if count else None, region+'_empty':not count})
                rows.append(row)
                budget()
        summary = summarize(rows)
        guide_rows = {x['target_id']:x for x in old_rows if x['arm'] == 'Gguide'}
        whole, pairs = [], []
        for arm, family, strength in STRATEGIES:
            item = dict(arm=arm, family=family, strength=strength, comparison=arm+'-S86_Gguide')
            for region in REGIONS:
                a, b = summary[arm][region], old_summary['Gguide'][region]
                require(a['total_channels'] == b['total_channels'], 'pooled comparison denominator')
                delta = a['total_sse'] - b['total_sse'];count = a['total_channels']
                am, bm = a['equal_frame_mean_mse'], b['equal_frame_mean_mse']
                item[region+'_total_sse_difference'] = delta
                item[region+'_pooled_mse_difference'] = delta/(count*65025) if count else None
                item[region+'_mean_mse_difference'] = (delta/(3981312*65025) if region=='full' else
                                                       am-bm if am is not None and bm is not None else None)
            whole.append(item)
            for x in [r for r in rows if r['arm'] == arm]:
                other=guide_rows[x['target_id']];pair=dict(arm=arm, target_id=x['target_id'])
                for region in REGIONS:
                    count=x[region+'_channels'];require(count==other[region+'_channels'], 'per-target denominator')
                    delta=x[region+'_sse']-other[region+'_sse']
                    pair[region+'_sse_difference']=delta;pair[region+'_mse_difference']=delta/(count*65025) if count else None
                pairs.append(pair)
        envelope={}
        for family in ('Gpaste','Gterminal','all_six_new'):
            subset=[a for a,f,s in STRATEGIES if family=='all_six_new' or f==family]
            minimum=min(summary[a]['full']['total_sse'] for a in subset)
            envelope[family]=dict(candidate_arms=subset, min_total_sse=minimum,
                                 min_mse=minimum/(3981312*65025),
                                 tied_minimum_arms=[a for a in subset if summary[a]['full']['total_sse']==minimum])
        hits=[a for a in names if summary[a]['full']['total_sse']<=13571317266]
        decision=dict(status='COMPLETE_SIX_STRATEGIES', all_six_complete=True, counterexample_arms=hits,
                      multistep_necessary_for_this_MSE_refuted=bool(hits),
                      decision='STOP_NECESSITY_CLAIM' if hits else 'FINITE_CONTROL_FAMILY_NOT_SUFFICIENT',
                      envelope=envelope, selection='Retrospective already-seen-reference envelope; no validation result.',
                      old_references='S86 Gpaste(.25)/Gterminal(.25) separate; G0 original chain once, not lambda0 replay.',
                      limits='No perceptual/geometric/long-horizon/novelty inference; visible ghosting remains.')
        fields=list(rows[0])
        with(out/'FRAME_SCORES.csv').open('x',newline='')as handle:
            writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        write_json(out/'FRAME_SCORES.json',rows);write_json(out/'ARM_SUMMARY.json',summary)
        write_json(out/'CONTRASTS.json',dict(overall=whole,per_target=pairs))
        write_json(out/'DECISION.json',decision)
        with(out/'HISTORICAL_S86_FRAME_SCORES.csv').open('xb')as handle:handle.write(old_csv)
        write_json(out/'HISTORICAL_S86_FRAME_SCORES.json',old_rows)
        write_json(out/'HISTORICAL_S86_ARM_SUMMARY.json',old_summary)
        read(HERE/'execution_01/RECEIPT.json',sha(graw))
        require(sum(q.stat().st_size for q in out.iterdir())<8*1024**2,'output budget')
        report.update(status='COMPLETE_24_NEW_16_HISTORICAL_SCORES_PENDING_REVIEW',new_rows=24,historical_rows=16)
        code=0
    except BaseException as exc:
        report.update(status='FAILED_SCORING_PARTIAL_PRESERVED',error=repr(exc),traceback=traceback.format_exc())
        write_json(out/'PARTIAL_ROWS.json',rows)
        write_json(out/'ALL_24_ROW_STATUSES.json',[
            dict(arm=a,target_id=t,status='SCORED_NOT_ACCEPTED' if any(x['arm']==a and x['target_id']==t for x in rows)
                 else 'NOT_SCORED',reason='See failed receipt; no reduced-frame means') for a,f,s in STRATEGIES for t in TARGETS])
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous)
        report.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-began,rows_computed=len(rows),
                      peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        report['artifacts']=[dict(path=str(q),bytes=q.stat().st_size,sha256=sha(q.read_bytes())) for q in sorted(out.iterdir())if q.is_file()]
        write_json(out/'RECEIPT.json',report)
    print(json.dumps(dict(status=report['status'],rows=len(rows))))
    return code


if __name__ == '__main__':
    sys.exit(main())
