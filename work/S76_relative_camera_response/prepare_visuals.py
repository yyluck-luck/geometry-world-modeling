#!/usr/bin/env python3
"""只展示封存评分PNG：左A0、右yaw_plus5，完整保留目标20至23。"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import io
import json
import sys

D = Path(__file__).resolve().parent
TARGETS = [20, 21, 22, 23]
FONT = Path('/System/Library/Fonts/Helvetica.ttc')
HEADER = 64
WIDTH = HEIGHT = 576


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def write_json(path, data):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')
    path.chmod(0o444)


def main():
    if sys.argv[1:] == ['--compile-only']:
        compile(Path(__file__).read_bytes(), __file__, 'exec')
        print('COMPILE_ONLY_NO_IMAGE_READ')
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt', type=Path, help='本轮scoring_01/receipt.json的绝对路径')
    parser.add_argument('receipt_sha256', help='已封存评分回执的SHA256')
    args = parser.parse_args()
    expected = D / 'scoring_01/receipt.json'
    require(args.receipt.resolve() == expected.resolve(), 'Only this stage scoring_01/receipt.json is accepted')
    body = expected.read_bytes()
    require(sha(body) == args.receipt_sha256, 'Scoring receipt SHA differs')
    score = json.loads(body)
    require(score.get('status') == 'COMPLETE_SAVED_YAW_DIRECTION_DIAGNOSTIC',
            'Refusing visualization: scoring is not COMPLETE')
    rows = score.get('targets', [])
    require([row.get('target_id') for row in rows] == TARGETS and score.get('unrun_target_ids') == [],
            'All four fixed targets must be complete and in order; no selection permitted')
    require(score.get('new_method_validated') is False, 'Unexpected scientific claim in score receipt')
    out = D / 'visuals_01'
    require(not out.exists(), 'Existing visuals preserved; no overwrite or automatic retry')
    # Pillow and image bytes are touched only after the sealed completion gate.
    from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version
    font = ImageFont.truetype(str(FONT), 22)
    small_font = ImageFont.truetype(str(FONT), 16)
    images = []
    sources = []
    for row in rows:
        target = row['target_id']; pair = []; source_pair = {}
        for arm in ['A0', 'yaw_plus5']:
            item = row['images'][arm]
            p = Path(item['path'])
            require(p.resolve() == (D / 'scoring_01' / f'{arm}_target_{target}.png').resolve(),
                    'PNG path differs from fixed scoring output')
            b = p.read_bytes()
            require(sha(b) == item['sha256'], 'Source PNG file SHA differs')
            with Image.open(io.BytesIO(b)) as opened:
                require(opened.format == 'PNG' and opened.mode == 'RGB' and opened.size == (WIDTH, HEIGHT),
                        'Source PNG must be unmodified 576x576 RGB')
                image = opened.copy()
            pixel_sha = sha(image.tobytes())
            require(pixel_sha == item['pixel_sha256'], 'Source PNG decoded pixel SHA differs')
            pair.append(image)
            source_pair[arm] = dict(path=str(p), file_sha256=sha(b), pixel_sha256=pixel_sha,
                                    width=WIDTH, height=HEIGHT, mode='RGB')
        images.append(pair)
        sources.append(dict(target_id=target, matching_status=row.get('status'),
                            match_count=row.get('match_count'), source_pngs=source_pair))
    out.mkdir(exist_ok=False)
    started = utc()
    manifest = dict(schema='s76-native-pixel-all-four-display-v1', started_utc=started,
                    status='PREPARING', source_receipt_path=str(expected), source_receipt_sha256=sha(body),
                    script_sha256=sha(Path(__file__).read_bytes()), pillow_version=pillow_version,
                    font_path=str(FONT), font_sha256=sha(FONT.read_bytes()),
                    targets=TARGETS, generated_images=True, real_photographs=False,
                    scope='Display only: model-generated images, not real photographs. Native pixels; no enhancement, crop, resize, alignment, selection, new matching or image generation. All four targets retained regardless of matching status. Visual inspection and scientific acceptance are separate.',
                    pairs=[], contact_sheet=None)
    write_json(out / 'started.json', dict(started_utc=started, source_receipt_sha256=sha(body)))
    combined = Image.new('RGB', (WIDTH * 2, (HEIGHT + HEADER) * len(TARGETS)), 'white')
    try:
        for index, target in enumerate(TARGETS):
            canvas = Image.new('RGB', (WIDTH * 2, HEIGHT + HEADER), 'white')
            draw = ImageDraw.Draw(canvas)
            for column, arm in enumerate(['A0', 'yaw_plus5']):
                x = column * WIDTH
                title = f'Target {target} | ' + ('A0 (reused baseline)' if arm == 'A0' else 'yaw_plus5 (+5 deg)')
                draw.text((x + 12, 5), title, fill='black', font=font)
                draw.text((x + 12, 35), 'MODEL-GENERATED | not a real photograph', fill='black', font=small_font)
                canvas.paste(images[index][column], (x, HEADER))
                require(canvas.crop((x, HEADER, x + WIDTH, HEADER + HEIGHT)).tobytes() == images[index][column].tobytes(),
                        'Display placement changed source pixels')
            dst = out / f'target_{target}_pair.png'
            with dst.open('xb') as handle:
                canvas.save(handle, format='PNG')
            dst.chmod(0o444)
            combined.paste(canvas, (0, index * (HEIGHT + HEADER)))
            manifest['pairs'].append(dict(**sources[index], path=str(dst), file_sha256=sha(dst.read_bytes()),
                                          pixel_sha256=sha(canvas.tobytes()), width=canvas.width, height=canvas.height))
        dst = out / 'ALL_FOUR_TARGET_PAIRS.png'
        with dst.open('xb') as handle:
            combined.save(handle, format='PNG')
        dst.chmod(0o444)
        manifest['contact_sheet'] = dict(path=str(dst), file_sha256=sha(dst.read_bytes()),
                                         pixel_sha256=sha(combined.tobytes()), width=combined.width, height=combined.height)
        manifest['status'] = 'COMPLETE_DISPLAY_ONLY_PENDING_VISUAL_QA'
    except Exception as error:
        manifest.update(status='FAILED_PRESERVED', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        manifest['completed_utc'] = utc()
        write_json(out / 'manifest.json', manifest)
    print(json.dumps(dict(status=manifest['status'], output=str(out))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
