#!/usr/bin/env python3
"""Read-only S87 display export, only after SHA-bound root scientific acceptance.

24 new native PNGs + four 2x5 overviews; no scoring, models, crop, or resize.
Old reference/warp/G0/Gguide are verified already-exported S86 PNGs.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import signal
import time
import traceback
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'S86_fixed_warp_consumer'
TARGETS = [20, 21, 22, 23]
ARMS = ['Gpaste_l050', 'Gterminal_l050', 'Gpaste_l075', 'Gterminal_l075',
        'Gpaste_l100', 'Gterminal_l100']
GRID = [['reference', 'G0', 'Gpaste_l050', 'Gpaste_l075', 'Gpaste_l100'],
        ['warp', 'Gguide', 'Gterminal_l050', 'Gterminal_l075', 'Gterminal_l100']]
LABELS = {'reference': '真实参考 | Saved real reference',
          'warp': '历史投影（灰格=孔洞）| Fixed warp',
          'G0': 'S86 G0 原链 | Original chain',
          'Gguide': 'S86 Gguide 50步 / .25 | 50 steps'}
for arm in ARMS:
    strength = {'050': '0.50', '075': '0.75', '100': '1.00'}[arm[-3:]]
    family = 'RGB贴图' if arm.startswith('Gpaste') else '末步融合'
    LABELS[arm] = f'S87 {arm.split("_")[0]} {strength} | {family}'
GENERATION_CONTRACT_SHA = '337982b200182b50ade46aee4625c5c7ff3d87f5acce01bd48343451015c2538'
OLD_EXPORT_SHA = '2c625dbf0b1ac8dda159603018f23caea891a570527a479c7657fb98b0d7ebb9'
FONT = {'path': '/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 'bytes': 23278008,
        'sha256': '876af2cd4854644e7f3e7feb2f688997fdb3343c6df6693611209c9dfb47ccec'}
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
            'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not bool(ok):
        raise RuntimeError(message)


def main(acceptance_sha256):
    out = HERE / 'visuals_01'
    out.mkdir(exist_ok=False)
    started = time.monotonic()
    report = dict(schema='S87_FIXED_COMPARISON_EXPORT_V1', status='STARTED', started_utc=now(),
                  exporter_sha256=sha(Path(__file__).read_bytes()), root_acceptance_sha256=acceptance_sha256,
                  reads=[], images=[], reused_images=[], target_order=TARGETS, grid=GRID,
                  model_calls=0, score_calls=0, projection_calls=0, resize_calls=0,
                  limits=dict(seconds=120, peak_self_rss_bytes=1024**3, output_bytes=128*1024**2),
                  new_method_validated=False)

    def write(path, value):
        with path.open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')

    def read(path, role, expected, size=None):
        path = Path(path)
        raw = path.read_bytes()
        report['reads'].append(dict(path=str(path), role=role, sha256=sha(raw), bytes=len(raw), utc=now()))
        require(sha(raw) == expected and (size is None or len(raw) == size), 'Input identity: ' + str(path))
        return raw

    def budget():
        require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 1024**3, 'Export self RSS1GiB')
        require(sum(p.stat().st_size for p in out.iterdir() if p.is_file()) <= 128*1024**2,
                'Export output128MiB')

    def timeout(signum, frame):
        raise TimeoutError('Export exceeded120s')

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(120)
    result = 1
    try:
        import numpy as np
        import PIL
        from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
        require(np.__version__ == '1.26.4' and PIL.__version__ == '10.3.0', 'Display runtime versions')
        report['versions'] = {'numpy': np.__version__, 'Pillow': PIL.__version__}
        approval_raw = read(HERE / 'ROOT_RESULT_ACCEPTANCE.json', 'root_scientific_acceptance', acceptance_sha256)
        approval = json.loads(approval_raw)
        require(approval['accepted'] is True and bool(approval['accepted_utc']), 'Scientific acceptance absent')
        gpath, spath = HERE / 'execution_01/RECEIPT.json', HERE / 'scoring_01/RECEIPT.json'
        graw = read(gpath, 'generation_receipt', approval['generation_receipt_sha256'])
        sraw = read(spath, 'scoring_receipt', approval['scoring_receipt_sha256'])
        generation, scoring = json.loads(graw), json.loads(sraw)
        contract = json.loads(read(HERE / 'GENERATION_CONTRACT.json', 'generation_contract', GENERATION_CONTRACT_SHA))
        scfg = json.loads(read(HERE / 'SCORING_CONTRACT.json', 'scoring_contract', scoring['scoring_contract_sha256']))
        require(generation['contract_sha256'] == GENERATION_CONTRACT_SHA
                and contract['target_ids'] == TARGETS and generation['order'] == ARMS
                and generation['status'] == 'COMPLETE_SIX_DERIVED_CONTROLS_PENDING_REVIEW'
                and generation['unrun_arms'] == [] and set(generation['arms']) == set(ARMS),
                'Generation completion/identity')
        require(scoring['generation_receipt_sha256'] == sha(graw)
                and scoring['status'] == 'COMPLETE_24_NEW_16_HISTORICAL_SCORES_PENDING_REVIEW'
                and scoring['new_rows'] == 24 and scoring['historical_rows'] == 16
                and scfg['generation_contract']['sha256'] == GENERATION_CONTRACT_SHA,
                'Completed scoring must bind these generated images')
        require(len(scoring['emission_checks']) == 24
                and all(r['exact_uint8_match'] is True for r in scoring['emission_checks']),
                'All24 emission checks required')
        old_export = json.loads(read(OLD / 'visuals_01/EXPORT_RECEIPT.json', 'S86_export_receipt', OLD_EXPORT_SHA))
        require(old_export['status'] == 'COMPLETE_FIXED_COMPARISON_EXPORT_PENDING_VISUAL_QA', 'Old export incomplete')
        write(out / 'INPUT_BINDING.json', dict(recorded_utc=now(), root_acceptance_sha256=acceptance_sha256,
              generation_receipt_sha256=sha(graw), scoring_receipt_sha256=sha(sraw),
              generation_contract_sha256=GENERATION_CONTRACT_SHA,
              scoring_contract_sha256=scoring['scoring_contract_sha256'], S86_export_receipt_sha256=OLD_EXPORT_SHA,
              scope='All binding checks above precede new array and old image pixel reads. Display only; no score computation.'))
        methods = {}
        for arm in ARMS:
            item = generation['arms'][arm]
            require(item['status'] == 'COMPLETE_DERIVED', 'Incomplete derived arm')
            desc = item['arrays']['targets_uint8']
            path = HERE / 'execution_01' / arm / 'targets_uint8.npy'
            require(desc['path'] == str(path), 'Unexpected generated image path')
            require(any(r['path'] == str(path) and r['sha256'] == desc['file_sha256']
                        for r in scoring['reads']), 'Image absent from scored input list')
            data = read(path, 'accepted_emitted_uint8', desc['file_sha256'])
            a = np.load(io.BytesIO(data), allow_pickle=False)
            require(a.shape == (4,576,576,3) and a.dtype == np.uint8 and a.flags.c_contiguous
                    and desc['shape'] == list(a.shape) and desc['dtype'] == str(a.dtype)
                    and desc['body_bytes'] == a.nbytes and desc['body_sha256'] == sha(a.tobytes()),
                    'Generated display array body identity')
            a.flags.writeable = False
            methods[arm] = a
        font_bytes = read(FONT['path'], 'display_font', FONT['sha256'], FONT['bytes'])
        font = ImageFont.truetype(io.BytesIO(font_bytes), 22)
        title_font = ImageFont.truetype(io.BytesIO(font_bytes), 30)

        def save_png(im, path, role, target):
            text = f'Target {target} | {LABELS.get(role, role)}'
            metadata = PngImagePlugin.PngInfo()
            metadata.add_itxt('Description', text)
            im.save(path, format='PNG', pnginfo=metadata)
            raw = path.read_bytes()
            with Image.open(io.BytesIO(raw)) as check:
                check.load()
                require(check.mode == im.mode and check.size == im.size and check.tobytes() == im.tobytes(),
                        'PNG pixel readback mismatch')
            report['images'].append(dict(path=str(path), target_id=target, role=role, label=text,
                size=list(im.size), mode=im.mode, bytes=len(raw), sha256=sha(raw),
                pixel_sha256=sha(im.tobytes()), pixel_readback_exact=True))
            budget()

        for i, target in enumerate(TARGETS):
            tiles = {}
            for role in ('reference', 'warp', 'G0', 'Gguide'):
                matches = [r for r in old_export['images'] if r['target_id'] == target and r['role'] == role]
                require(len(matches) == 1, 'Old native image unique role')
                desc = matches[0]
                expected_name = f'target_{target}_' + ('warp_holes_marked' if role == 'warp' else role) + '.png'
                require(desc['path'] == str(OLD / 'visuals_01' / expected_name), 'Old image fixed path')
                raw = read(desc['path'], 'reused_S86_' + role, desc['sha256'], desc['bytes'])
                with Image.open(io.BytesIO(raw)) as old_image:
                    old_image.load()
                    require(old_image.mode == 'RGB' and old_image.size == (576,576)
                            and sha(old_image.tobytes()) == desc['pixel_sha256'], 'Old image pixel identity')
                    tiles[role] = old_image.copy()
                report['reused_images'].append(desc)
            for arm in ARMS:
                tiles[arm] = Image.fromarray(methods[arm][i], 'RGB')
                save_png(tiles[arm], out / f'target_{target}_{arm}.png', arm, target)
            overview = Image.new('RGB', (2952,1400), (245,245,245))
            draw = ImageDraw.Draw(overview)
            draw.text((12,8), f'S87 目标 {target} | 六个新末端对照 + 四个既有参照', font=title_font, fill='black')
            draw.text((12,50), '每格原尺寸576，无裁剪/缩放。灰格=无历史投影支持，不是真实可见性；低MSE不代表重影消失。',
                      font=font, fill='black')
            draw.text((12,80), 'Native 576px. Historical RGB warp; checkerboard = no support. No perceptual or geometry claim.',
                      font=font, fill='black')
            for row, roles in enumerate(GRID):
                for column, role in enumerate(roles):
                    x, y = 12 + column*588, 118 + row*638
                    draw.text((x,y), LABELS[role], font=font, fill='black')
                    overview.paste(tiles[role], (x,y+40))
            save_png(overview, out / f'overview_target_{target}_2x5.png', '全部固定对照 | All fixed comparisons', target)
        require(len(report['images']) == 28 and len(report['reused_images']) == 16, 'All24 new +4 overviews +16 reused required')
        write(out / 'IMAGE_INDEX.json', report['images'])
        require(read(gpath, 'generation_final_recheck', sha(graw)) == graw
                and read(spath, 'scoring_final_recheck', sha(sraw)) == sraw
                and read(HERE / 'ROOT_RESULT_ACCEPTANCE.json', 'root_acceptance_final_recheck', acceptance_sha256) == approval_raw,
                'Accepted identities changed during display export')
        report['status'] = 'COMPLETE_24_NATIVE_4_OVERVIEWS_PENDING_VISUAL_QA'
        result = 0
    except BaseException as error:
        report.update(status='FAILED_PARTIAL_EXPORT_PRESERVED', error_type=type(error).__name__,
                      error=str(error), traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        report.update(completed_utc=now(), elapsed_seconds=time.monotonic()-started,
                      peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      total_pngs=len(report['images']),
                      native_pngs=sum(r['size']==[576,576] for r in report['images']))
        write(out / 'EXPORT_RECEIPT.json', report)
    print(json.dumps(dict(status=report['status'],receipt=str(out/'EXPORT_RECEIPT.json'))))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--acceptance-sha256', required=True)
    args = parser.parse_args()
    raise SystemExit(main(args.acceptance_sha256))
