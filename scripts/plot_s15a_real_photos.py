#!/usr/bin/env python3
"""Render all 20 sealed S15A history RGBs after a completed real model run.

This reporting script never opens target/depth/trajectory files, model weights,
or prediction NPZs. It does not run a model and never rewrites source photographs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import sys
import traceback
from zoneinfo import ZoneInfo


SCHEMA = 's15a-real-history-photo-index-v1'
SEAL_SCHEMA = 's15a-history-combined-seal-v1'
TITLE = 'Bonn real RGB | history only | no accuracy result'
SHA_RE = re.compile(r'^[0-9a-f]{64}$')
HISTORY_COUNT = 20


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'Timestamp must include timezone')
    return parsed.astimezone(timezone.utc)


def canonical(value: str) -> Path:
    path = Path(value)
    require(path.is_absolute() and str(path.resolve()) == value,
            'Bound file path must be absolute and canonical: ' + value)
    return path


def read_bound_json(path: Path, identities: dict, report: dict) -> dict:
    key = str(path)
    expected = identities.get(key)
    require(isinstance(expected, str) and SHA_RE.fullmatch(expected) is not None,
            'JSON control missing from externally sealed identities: ' + key)
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    require(actual == expected, 'Sealed JSON identity mismatch: ' + key)
    report['verified_control_files'].append(
        dict(path=key, sha256=actual, bytes=len(data), verified_utc=utc()))
    result = json.loads(data)
    require(isinstance(result, dict), 'JSON object required: ' + key)
    return result


def controls(manifest_path: Path, samples_path: Path, seal_path: Path,
             expected_seal_sha: str, report: dict) -> tuple[list[dict], dict]:
    """Check only allowed JSON controls; deliberately do not hash all seal files."""
    require(SHA_RE.fullmatch(expected_seal_sha) is not None, 'Valid external seal SHA required')
    seal_bytes = seal_path.read_bytes()
    require(hashlib.sha256(seal_bytes).hexdigest() == expected_seal_sha,
            'Externally supplied combined seal SHA mismatch')
    seal = json.loads(seal_bytes)
    require(seal.get('schema') == SEAL_SCHEMA, 'Expected completed S15A combined seal')
    ids = seal.get('identities')
    require(isinstance(ids, dict), 'Combined seal identities must be a map')
    require(seal.get('manifest') == str(manifest_path), 'Manifest path must equal sealed manifest role')
    manifest = read_bound_json(manifest_path, ids, report)
    samples = read_bound_json(samples_path, ids, report)
    require(manifest.get('schema') == 's15-history-manifest-v1', 'S15 history manifest schema')
    require(samples.get('schema') == 's15a-fixed-samples-v1', 'S15 fixed samples schema')
    require(samples.get('source') == 'Bonn static_close_far', 'Expected Bonn source')
    mids = manifest.get('identities')
    require(isinstance(mids, dict), 'Manifest identities map')
    require(mids.get(str(samples_path)) == ids[str(samples_path)],
            'Model manifest and combined seal must bind the same samples')
    require(all(ids.get(key) == value for key, value in mids.items()),
            'Combined seal must preserve all manifest identity values')
    contract = manifest.get('contract', {})
    require(contract.get('history_count') == HISTORY_COUNT and contract.get('query_count') == 0,
            'Exactly 20 history inputs and no queries')
    require(contract.get('history_rgb_allowed') is True
            and contract.get('target_rgb_allowed') is False
            and contract.get('target_depth_allowed') is False,
            'History-only input contract')
    history = manifest.get('history_images')
    require(isinstance(history, list) and len(history) == HISTORY_COUNT,
            'Exactly 20 ordered history image records')
    rows = samples.get('samples')
    require(isinstance(rows, list) and len(rows) == 24, 'Exactly 24 sample metadata rows')
    require([x.get('index') for x in history] == list(range(HISTORY_COUNT)), 'Ordered manifest indices')
    require([x.get('index') for x in rows] == list(range(24)), 'Ordered sample metadata indices')
    require(all(x.get('role') == 'history' for x in rows[:20])
            and all(x.get('role') == 'future_target' for x in rows[20:]),
            'History/future role boundary')

    # Metadata may describe arrays, but this program never opens those payloads.
    run_dir = canonical(seal['run_dir'])
    meta_path = run_dir / 'run_metadata.json'
    caller_path = canonical(seal['caller_receipt'])
    require(meta_path.suffix == '.json' and caller_path.suffix == '.json', 'JSON controls only')
    meta = read_bound_json(meta_path, ids, report)
    caller = read_bound_json(caller_path, ids, report)
    require(meta.get('schema') == 's15-history-run-v1'
            and meta.get('status') == 'SUCCESS' and meta.get('phase') == 'complete',
            'Actual model history run must have completed successfully')
    require(caller.get('schema') == 's14d-caller-v1' and caller.get('status') == 'PASS'
            and caller.get('returncode') == 0 and caller.get('monitor_ok') is True
            and caller.get('before_after_identity_pass') is True
            and caller.get('timed_out') is False and caller.get('rss_limit_exceeded') is False,
            'Actual externally monitored model caller must have passed')
    require(meta.get('manifest_sha256') == ids[str(manifest_path)]
            and caller.get('manifest_sha256') == ids[str(manifest_path)],
            'Completed run and caller must bind this exact manifest')
    require(timestamp(caller['started_utc']) <= timestamp(meta['started_utc'])
            <= timestamp(meta['completed_utc']) <= timestamp(caller['completed_utc'])
            <= timestamp(seal['sealed_utc']) <= timestamp(report['started_utc']),
            'Actual model/caller/seal/plot time ordering')
    paths = [x.get('path') for x in history]
    require(len(set(paths)) == HISTORY_COUNT, 'Distinct history file paths')
    require(meta.get('history_images') == history
            and meta.get('image_open_attempt_paths') == paths
            and meta.get('image_opened_paths') == paths,
            'These exact history images must have been processed by the completed model')
    counters = meta.get('counters', {})
    require(counters.get('history_rgb_decoded') == HISTORY_COUNT
            and counters.get('target_rgb_decoded') == 0
            and counters.get('target_depth_decoded') == 0
            and counters.get('query_calls') == 0,
            'Actual completed model counters must respect history-only scope')

    selected_origin = Decimal(rows[0]['rgb_timestamp'])
    require(selected_origin.is_finite(), 'Finite selected timestamp origin')
    resolved = []
    for item, sample in zip(history, rows[:HISTORY_COUNT]):
        path = canonical(item['path'])
        member = Path(sample['rgb_member'])
        require(not member.is_absolute() and '..' not in member.parts
                and len(member.parts) == 3
                and member.parts[:2] == ('rgbd_bonn_static_close_far', 'rgb')
                and member.suffix == '.png', 'Native Bonn RGB member path')
        require(path.parts[-3:] == member.parts, 'Manifest path must match selected RGB member')
        require(mids.get(str(path)) == item['sha256'] == ids.get(str(path))
                and SHA_RE.fullmatch(item['sha256']) is not None,
                'Photo identity bound identically by manifest and seal')
        absolute_time = Decimal(sample['rgb_timestamp'])
        require(absolute_time.is_finite() and absolute_time >= selected_origin,
                'Finite ordered selected timestamps')
        require(member.stem == sample['rgb_timestamp'], 'Timestamp must match native PNG name')
        resolved.append(dict(index=item['index'], path=str(path), sha256=item['sha256'],
                             rgb_member=str(member), rgb_timestamp=sample['rgb_timestamp'],
                             seconds_since_first_selected_rgb=str(absolute_time-selected_origin)))
    require(all(Decimal(a['rgb_timestamp']) < Decimal(b['rgb_timestamp'])
                for a,b in zip(resolved, resolved[1:])), 'Strict chronological history order')
    report.update(seal_path=str(seal_path), seal_sha256=expected_seal_sha,
                  sealed_utc=seal['sealed_utc'], manifest_path=str(manifest_path),
                  manifest_sha256=ids[str(manifest_path)], samples_path=str(samples_path),
                  samples_sha256=ids[str(samples_path)],
                  selected_first_rgb_timestamp=rows[0]['rgb_timestamp'],
                  archive_first_rgb_timestamp=samples.get('first_rgb_timestamp'),
                  actual_model_completed_utc=meta['completed_utc'],
                  actual_caller_completed_utc=caller['completed_utc'],
                  pre_image_gate_completed_utc=utc())
    return resolved, ids


def run(manifest_path: str, samples_path: str, seal_path: str,
        seal_sha256: str, output: str) -> int:
    out = Path(output).resolve()
    require(not out.exists(), 'Output must be a fresh directory; previous results are immutable')
    out.mkdir(parents=True)
    report = dict(schema=SCHEMA, status='RUNNING', started_utc=utc(),
                  script_path=str(Path(__file__).resolve()),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  verified_control_files=[], images=[], source_rgb_byte_reads=0,
                  source_rgb_decode_attempts=0, source_rgb_decodes=0,
                  source_rgb_after_hash_reads=0, target_rgb_reads=0,
                  target_depth_reads=0, trajectory_reads=0, prediction_npz_reads=0,
                  model_calls=0, accuracy_evaluated=False,
                  source_files_rewritten=0, original_images_cropped=False,
                  title=TITLE, note='Reporting artifact, not accuracy or generalization evidence.')
    figure = None
    try:
        manifest = canonical(str(Path(manifest_path).resolve()))
        samples = canonical(str(Path(samples_path).resolve()))
        seal = canonical(str(Path(seal_path).resolve()))
        rows, _ = controls(manifest, samples, seal, seal_sha256, report)

        import PIL
        from PIL import Image
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        report['versions'] = dict(python=sys.version, pillow=PIL.__version__,
                                  matplotlib=matplotlib.__version__)
        report['layout'] = dict(rows=5, columns=4, order='row-major chronological',
                                font='DejaVu Sans', panel_font_pt=11, title_font_pt=18,
                                dpi=180, native_image_aspect='equal; fit without crop',
                                photometric_adjustments=False)
        # Verify all 20 original byte identities before the first image decoder call.
        payloads = []
        for row in rows:
            data = Path(row['path']).read_bytes()
            report['source_rgb_byte_reads'] += 1
            require(hashlib.sha256(data).hexdigest() == row['sha256'],
                    'Original RGB SHA changed: ' + row['path'])
            payloads.append(data)
        report['all_20_rgb_hashes_verified_utc'] = utc()
        decoded = []
        for row, data in zip(rows, payloads):
            item = dict(row, bytes=len(data), decode_started_utc=utc())
            report['images'].append(item)
            report['source_rgb_decode_attempts'] += 1
            with Image.open(BytesIO(data)) as image:
                require(image.format == 'PNG', 'Expected native PNG payload')
                require(getattr(image, 'n_frames', 1) == 1, 'Expected one native RGB frame')
                image.load()
                report['source_rgb_decodes'] += 1
                item.update(native_size=list(image.size), native_mode=image.mode,
                            native_format=image.format, decode_completed_utc=utc())
                require(image.mode == 'RGB', 'Native RGB mode required; do not silently recolor inputs')
                decoded.append(image.copy())

        # Photographs are necessarily raster; only the contact sheet is resized for display.
        ratio = max(img.height / img.width for img in decoded)
        width = 16.0
        height = 5 * (3.75 * ratio + 0.34) + 1.35
        with plt.rc_context({'font.family':'DejaVu Sans','font.size':11,
                             'figure.facecolor':'white','axes.facecolor':'white'}):
            figure, axes = plt.subplots(5, 4, figsize=(width, height))
            figure.subplots_adjust(left=0.02,right=0.98,top=0.93,bottom=0.055,
                                   wspace=0.05,hspace=0.16)
            figure.suptitle(TITLE, fontsize=18, y=0.985, fontweight='semibold')
            figure.text(0.5, 0.957,
                        'static_close_far | all 20 selected history frames | original files unchanged',
                        ha='center',va='center',fontsize=11)
            for axis, img, row in zip(axes.flat, decoded, rows):
                axis.imshow(img, aspect='equal', interpolation='nearest')
                axis.set_title('history {:02d} | +{} s'.format(
                    row['index'], format(Decimal(row['seconds_since_first_selected_rgb']),'.5f')),
                    fontsize=11,pad=6)
                axis.set_axis_off()
            figure.text(0.5,0.026,
                        't = 0: first selected history RGB. Read left to right, then top to bottom.\n'
                        'Full native field of view in every panel; no generated images, depth maps, or accuracy scores.',
                        ha='center',va='center',fontsize=10,linespacing=1.5)
            png = out/'s15a_all_20_real_history_photos.png'
            figure.savefig(png,dpi=180,facecolor='white')
            report['output_png'] = dict(path=str(png),bytes=png.stat().st_size,
                                       sha256=hashlib.sha256(png.read_bytes()).hexdigest())
            report['layout']['figure_inches'] = [width,height]

        # Detect source/control changes during reporting without decoding originals again.
        for row in rows:
            data = Path(row['path']).read_bytes()
            report['source_rgb_after_hash_reads'] += 1
            require(hashlib.sha256(data).hexdigest() == row['sha256'],
                    'Original RGB changed during plotting: ' + row['path'])
        require(hashlib.sha256(seal.read_bytes()).hexdigest() == seal_sha256, 'Combined seal changed')
        for item in report['verified_control_files']:
            require(hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() == item['sha256'],
                    'Bound JSON changed during plotting')
        require(report['source_rgb_decodes'] == HISTORY_COUNT, 'All 20 originals decoded exactly once')
        report.update(status='PASS',all_source_hashes_unchanged=True,
                      visual_inspection='Pending root inspection of generated PNG; not performed by this script')
    except Exception as exc:
        report.update(status='FAIL',error=repr(exc),traceback=traceback.format_exc())
    finally:
        if figure is not None:
            import matplotlib.pyplot as plt
            plt.close(figure)
        report['completed_utc'] = utc()
        report['completed_asia_shanghai'] = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
        (out/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],real_rgb_decodes=report['source_rgb_decodes'],
                          result=str(out/'receipt.json')),ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True)
    parser.add_argument('--samples',required=True)
    parser.add_argument('--seal',required=True)
    parser.add_argument('--seal-sha256',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    return run(args.manifest,args.samples,args.seal,args.seal_sha256,args.output)


if __name__ == '__main__':
    raise SystemExit(main())
