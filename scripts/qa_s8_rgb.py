#!/usr/bin/env python3
"""Check and copy all 72 frozen S8 RGB photographs without choosing new frames.

The manifest/protocol are sealed locally before any image header or pixels are
opened. Depth files are only hashed by the input validator; GT poses are never
parsed. Contact sheets are viewing aids; the original photographs are copied
byte for byte, never resaved or enhanced.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import io
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from run_s8_sequence import read_json, parse_protocol, validate_manifest, safe_data_path

DATASET = 'rgbd_dataset_freiburg2_desk'
SOURCES = ('scripts/qa_s8_rgb.py', 'scripts/run_s8_sequence.py')
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
ATTRIBUTION = {
    'dataset': 'TUM RGB-D Benchmark, rgbd_dataset_freiburg2_desk',
    'dataset_url': 'https://cvg.cit.tum.de/data/datasets/rgbd-dataset',
    'sequence_url': 'https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download',
    'current_official_license': 'Creative Commons Attribution 4.0 International (CC BY 4.0)',
    'license_source_url': 'https://cvg.cit.tum.de/data/datasets/rgbd-dataset#license',
    'license_url': 'https://creativecommons.org/licenses/by/4.0/',
    'paper': 'Sturm et al., A Benchmark for the Evaluation of RGB-D SLAM Systems, IROS 2012',
    'paper_url': 'https://cvg.cit.tum.de/_media/spezial/bib/sturm12iros.pdf',
    'local_verified_source': 'docs/S8_DATA_SOURCE_REVIEW.md',
    'license_scope_note': 'Current official website states CC BY 4.0; the original 2012 paper stated CC BY 3.0. '
                          'Both historical records are retained in the local source review.',
    'photo_modifications': 'None: original PNG bytes copied exactly; only containing folder and filename labels change.',
    'contact_sheet_modifications': 'Photographs displayed at reduced size with identification labels in a separate overview.',
    'generated_photos': False,
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    tmp.replace(path)


def fresh_outputs(output, photo_output):
    """Check both destinations before creating either, including broken links."""
    output, photo_output = Path(output).absolute(), Path(photo_output).absolute()
    for path in (output, photo_output):
        require(not path.exists() and not path.is_symlink(), 'Use fresh output directories; previous attempts remain: ' + str(path))
    a, b = output.resolve(), photo_output.resolve()
    require(a != b and not a.is_relative_to(b) and not b.is_relative_to(a),
            'QA and photograph output directories must be distinct and not nested')
    return output, photo_output


def readme_text(completed, count, error=None):
    state = '已完成全部72张原照片的格式、解码与字节核对' if completed else '尚未完成；请勿当作已通过核验的完整交付'
    text = f'''# S8 独立场景的真实相机照片

状态：**{state}**。当前已核验并复制 {count}/72 张。

这些照片来自 TUM RGB-D Benchmark 的 freiburg2/desk 相机实拍序列，不是AI生成照片，也不是本项目生成的新视角。三个片段各24张，前20张“历史”用于建立记忆，后4张“查询”用于测试；B0、B1、B2全部为外部测试块。文件名增加片段/顺序/用途标签，PNG内容逐字节保持原样。没有因为画面或结果更换已冻结的样本。

每张图片的原始路径、时间戳、SHA256及副本路径见 `照片来源清单.csv` 和 `照片来源清单.json`。`联系表` 文件夹中的三张总览仅作浏览辅助，缩小显示照片并附顺序标签，不替代原始PNG；其显示处理不改变72张原照片。

数据来源：[TUM RGB-D Benchmark]({ATTRIBUTION['dataset_url']})；[官方序列下载页]({ATTRIBUTION['sequence_url']})。

根据本项目已核实的[当前官方许可说明]({ATTRIBUTION['license_source_url']})，数据采用 [CC BY 4.0]({ATTRIBUTION['license_url']})。请保留本说明、数据来源和原论文引用：Sturm 等，*A Benchmark for the Evaluation of RGB-D SLAM Systems*，IROS 2012，[论文]({ATTRIBUTION['paper_url']})。2012原论文当时记载CC BY 3.0；当前网站记录与该历史差异见本项目来源审查。

本次整理只验证已固定的RGB照片。没有在此读取GT位姿数值、解码深度图或运行模型，也没有据此得出实验效果结论。
'''
    if error:
        text += '\n本次核验中断，已保留现有文件。失败原因见QA目录的run_metadata.json；下一次重试必须使用新目录。\n'
    return text


def check_png(payload):
    """Verify original PNG integrity and fully decode exactly its RGB pixels."""
    from PIL import Image
    require(payload.startswith(PNG_SIGNATURE), 'Frozen RGB file lacks PNG signature')
    with Image.open(io.BytesIO(payload)) as image:
        fmt, mode, size = image.format, image.mode, image.size
        require(fmt == 'PNG' and mode == 'RGB' and size == (640, 480),
                f'Expected a 640x480 RGB PNG, got format={fmt}, mode={mode}, size={size}')
        require(getattr(image, 'n_frames', 1) == 1, 'Expected one photograph, not an animated PNG')
        image.verify()  # Pillow checks PNG chunk checksums without accepting truncated data.
    with Image.open(io.BytesIO(payload)) as image:
        image.load()  # A separate pass fully decompresses pixels after verify closed its stream.
        require(image.mode == mode and image.size == size and image.format == fmt,
                'PNG identity changed between verify and full decode')
        require(len(image.tobytes()) == 640 * 480 * 3, 'Decoded RGB byte count differs')
    return dict(format=fmt, mode=mode, size=list(size), png_crc_verified=True, full_decode_ok=True)


def copy_exact(payload, target, expected_sha):
    require(hashlib.sha256(payload).hexdigest() == expected_sha, 'Source bytes differ from frozen RGB hash')
    with Path(target).open('xb') as stream:
        stream.write(payload)
    digest = sha(target)
    require(digest == expected_sha, 'Copied photograph hash differs')
    return digest


def render_contact_sheet(records, destination, block):
    """A scientific QA overview, created separately from unchanged originals."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image
    require(len(records) == 24 and [r['frame'] for r in records] == list(range(24)),
            'Contact sheet needs all 24 fixed frames in order')
    fig, axes = plt.subplots(4, 6, figsize=(18, 10.9), constrained_layout=False)
    fig.patch.set_facecolor('white')
    for ax, row in zip(axes.flat, records):
        path = Path(row['copied_path'])
        require(sha(path) == row['rgb_sha256'], 'Copied photograph changed before contact sheet')
        with Image.open(path) as image:
            image.load()
            ax.imshow(image)
        role = 'history' if row['frame'] < 20 else 'query'
        ax.set_title(f"{row['frame']+1:02d}  {role}  |  {row['rgb_timestamp']:.6f}", fontsize=8,
                     color='#175e43' if role == 'history' else '#9d3c1f', pad=4)
        ax.set_axis_off()
    fig.suptitle(f'TUM freiburg2/desk | B{block} external test | 20 history + 4 query photographs',
                 fontsize=17, y=.986)
    fig.text(.5, .012, 'Original camera photographs; viewing overview only. PNG originals remain byte-identical. '
             'Source: TUM RGB-D Benchmark; current official data license: CC BY 4.0.', ha='center', fontsize=9)
    fig.subplots_adjust(left=.014, right=.986, bottom=.045, top=.936, wspace=.055, hspace=.16)
    fig.savefig(destination, dpi=135, facecolor='white', metadata={
        'Title': f'S8 B{block} frozen RGB photograph contact sheet',
        'Description': '24 TUM photographs; image display resized only in this separate overview.',
        'Source': ATTRIBUTION['dataset_url'], 'License': ATTRIBUTION['license_url']})
    plt.close(fig)
    with Image.open(destination) as image:
        image.verify()
    return dict(block=block, path=str(Path(destination).resolve()), sha256=sha(destination),
                images=24, original_photo_pixels_modified=False,
                overview_transform='separate resized display with identification labels')


def write_photo_ledger(photo_output, metadata):
    names = ('block', 'frame', 'role', 'rgb_timestamp', 'manifest_relative_path', 'path',
             'rgb_sha256', 'copied_path', 'copy_sha256', 'format', 'mode', 'width', 'height',
             'png_crc_verified', 'full_decode_ok', 'checked_utc')
    with (photo_output / '照片来源清单.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=names)
        writer.writeheader()
        for row in metadata['images']:
            values = {key: row.get(key) for key in names}
            values['width'], values['height'] = row['size']
            writer.writerow(values)
    write_json(photo_output / '照片来源清单.json', dict(status=metadata['status'], dataset=DATASET,
        manifest_sha256=metadata.get('manifest_sha256'), protocol_sha256=metadata.get('protocol_sha256'),
        checked_rgb_images=len(metadata['images']), images=metadata['images'],
        contact_sheets=metadata['contact_sheets'], attribution=ATTRIBUTION,
        input_manifest_sealed_utc=metadata.get('input_manifest_sealed_utc'),
        first_rgb_decode_utc=metadata.get('first_rgb_decode_utc'), updated_utc=utc()))


def run(args):
    output, photo_output = fresh_outputs(args.output, args.photo_output)
    output.mkdir(parents=True, exist_ok=False)
    meta = dict(schema='s8-rgb-qa-v1', status='running', started_utc=utc(), phase='preflight',
        dataset=DATASET, output=str(output.resolve()), photo_output=str(photo_output.resolve()),
        checked_rgb_images=0, depth_decoded=False, gt_pose_values_parsed=False,
        model_run=False, new_samples_selected=False, generated_photos=False,
        images=[], contact_sheets=[], source_sha256={}, attribution=ATTRIBUTION,
        contact_sheets_visually_reviewed=False,
        environment=dict(python=sys.version, packages={}))
    def checkpoint():
        write_json(output / 'run_metadata.json', meta)
    checkpoint()
    created_photos = False
    sources = {}
    try:
        meta['environment']['packages'] = {n: version(n) for n in ('Pillow', 'matplotlib')}
        photo_output.mkdir(parents=True, exist_ok=False)
        created_photos = True
        (photo_output / '先看这里.md').write_text(readme_text(False, 0))
        (photo_output / 'README.md').write_text(readme_text(False, 0))
        snapshots = output / 'source_snapshot'
        snapshots.mkdir()
        for name in SOURCES:
            source = ROOT / name
            payload = source.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            (snapshots / source.name).write_bytes(payload)
            sources[source.resolve()] = digest
            meta['source_sha256'][name] = digest
        protocol_bytes, manifest_bytes, design_bytes = (Path(p).read_bytes() for p in
            (args.protocol, args.manifest, args.design_freeze))
        protocol_sha = hashlib.sha256(protocol_bytes).hexdigest()
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        design_sha = hashlib.sha256(design_bytes).hexdigest()
        design = read_json(design_bytes.decode('utf-8'))
        require(design.get('protocol_sha256') == protocol_sha, 'Design freeze does not match supplied protocol')
        require(design.get('new_images_read') is False and design.get('new_model_run') is False,
                'Expected the design freeze before reading new images or model outputs')
        protocol = parse_protocol(protocol_bytes.decode('utf-8'))
        require(protocol['splits'] == ['test']*3, 'All three S8 blocks must be external test')
        manifest = read_json(manifest_bytes.decode('utf-8'))
        require(manifest.get('schema') == 's8-inputs-v1' and manifest.get('dataset') == DATASET,
                'Unexpected S8 input manifest or dataset')
        _, identities = validate_manifest(manifest, args.data, protocol_sha, protocol)
        for name, payload in (('frozen_inputs.json', manifest_bytes), ('frozen_protocol.md', protocol_bytes),
                              ('design_freeze.json', design_bytes)):
            (output / name).write_bytes(payload)
        meta['input_sealed_file_sha256'] = {'frozen_inputs.json': manifest_sha,
            'frozen_protocol.md': protocol_sha, 'design_freeze.json': design_sha}
        for name, digest in meta['input_sealed_file_sha256'].items():
            require(sha(output / name) == digest, 'Frozen QA input copy differs: ' + name)
        meta.update(manifest_sha256=manifest_sha, protocol_sha256=protocol_sha,
            design_freeze_sha256=design_sha, design_frozen_utc=design['frozen_utc'],
            manifest_path=str(Path(args.manifest).resolve()), protocol_path=str(Path(args.protocol).resolve()),
            design_freeze_path=str(Path(args.design_freeze).resolve()), input_identities=identities,
            input_manifest_sealed_utc=utc(), phase='rgb_validation')
        require(datetime.fromisoformat(design['frozen_utc']) <= datetime.fromisoformat(meta['input_manifest_sealed_utc']),
                'Design freeze is dated after this QA seal')
        checkpoint()
        # No Image.open, PNG header inspection or image decompression occurs above.
        for block in manifest['blocks']:
            b = block['block']
            directory = photo_output / f'片段{b+1}_B{b}_外部测试'
            directory.mkdir()
            for frame in block['frames']:
                q = frame['frame']
                role = '历史' if q < 20 else '查询'
                original = safe_data_path(args.data, frame['rgb']['path'])
                payload = original.read_bytes()
                require(hashlib.sha256(payload).hexdigest() == frame['rgb_sha256'], 'RGB changed after input seal')
                if 'first_rgb_decode_utc' not in meta:
                    meta['first_rgb_decode_utc'] = utc()
                    checkpoint()
                facts = check_png(payload)
                target = directory / f'{q+1:02d}_{role}_{original.name}'
                copied_sha = copy_exact(payload, target, frame['rgb_sha256'])
                require(sha(original) == frame['rgb_sha256'], 'Original RGB changed while validating/copying')
                row = dict(block=b, frame=q, role=role, rgb_timestamp=frame['rgb']['timestamp'],
                    manifest_relative_path=frame['rgb']['path'], path=str(original),
                    rgb_sha256=frame['rgb_sha256'], copied_path=str(target.resolve()), copy_sha256=copied_sha,
                    bytes=len(payload), checked_utc=utc(), **facts)
                meta['images'].append(row)
                meta['checked_rgb_images'] = len(meta['images'])
                checkpoint()
            print(json.dumps(dict(phase='RGB_block_verified', block=b, checked_rgb_images=len(meta['images']), utc=utc())), flush=True)
        require(len(meta['images']) == 72, 'Expected all 72 frozen photographs')
        require(len({r['rgb_sha256'] for r in meta['images']}) == 72 and
                len({r['copied_path'] for r in meta['images']}) == 72, 'Photograph identity duplication')
        meta['phase'] = 'contact_sheets'
        checkpoint()
        contacts = output / 'contact_sheets'
        contacts.mkdir()
        photo_contacts = photo_output / '联系表'
        photo_contacts.mkdir()
        for b in range(3):
            name = f'片段{b+1}_B{b}_24张真实照片.png'
            destination = contacts / name
            record = render_contact_sheet([r for r in meta['images'] if r['block'] == b], destination, b)
            contact_copy = photo_contacts / name
            copy_exact(destination.read_bytes(), contact_copy, record['sha256'])
            record.update(copied_path=str(contact_copy.resolve()), copy_sha256=sha(contact_copy))
            meta['contact_sheets'].append(record)
            checkpoint()
        for path, expected in ((args.manifest, manifest_sha), (args.protocol, protocol_sha),
                               (args.design_freeze, design_sha), *sources.items()):
            require(sha(path) == expected, 'Frozen input/source changed during QA: ' + str(path))
        for name, digest in meta['input_sealed_file_sha256'].items():
            require(sha(output / name) == digest, 'Frozen QA input copy changed: ' + name)
        for row in meta['images']:
            require(sha(row['path']) == row['rgb_sha256'] == sha(row['copied_path']),
                    'Original or copied photograph changed during QA')
        meta['status'] = 'completed'
        meta['phase'] = 'complete'
        write_photo_ledger(photo_output, meta)
        for name in ('先看这里.md', 'README.md'):
            (photo_output / name).write_text(readme_text(True, 72))
        meta['photo_manifest_path'] = str((photo_output / '照片来源清单.json').resolve())
        meta['photo_manifest_sha256'] = sha(photo_output / '照片来源清单.json')
        meta['photo_csv_path'] = str((photo_output / '照片来源清单.csv').resolve())
        meta['photo_csv_sha256'] = sha(photo_output / '照片来源清单.csv')
        meta['photo_readme_sha256'] = {name: sha(photo_output / name) for name in ('先看这里.md', 'README.md')}
    except BaseException:
        meta['status'] = 'failed'
        meta['phase_failed'] = meta['phase']
        meta['traceback'] = traceback.format_exc()
        if created_photos:
            write_photo_ledger(photo_output, meta)
            for name in ('先看这里.md', 'README.md'):
                (photo_output / name).write_text(readme_text(False, len(meta['images']), error=True))
        raise
    finally:
        meta['completed_utc'] = utc()
        checkpoint()
    print(json.dumps(dict(status=meta['status'], checked_rgb_images=meta['checked_rgb_images'],
                         completed_utc=meta['completed_utc'])), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'protocol', 'design-freeze', 'data', 'output', 'photo-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    run(args)


if __name__ == '__main__':
    main()
