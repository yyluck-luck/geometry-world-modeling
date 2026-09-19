#!/usr/bin/env python3
"""Create a frozen timestamp-exclusion derivative without decoding image/pose data.

Only the first token of an eight-column GT data row is parsed numerically.
Python float (IEEE-754 binary64) keys define duplicates; a GT row is excluded
iff abs(t - d) <= 0.051 for any duplicate key d, using those float values.
Other files are copied independently, with complete source/destination hashes.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import stat
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
DATASET = 'rgbd_dataset_freiburg2_desk'
HALF_WIDTH = 0.051
MAX_INTERPOLATION_GAP = 0.100
RULE = {
    'timestamp_parser': 'Python float from the first whitespace-delimited byte token only',
    'numeric_representation': 'IEEE-754 binary64; no Decimal, rounding, isclose or tolerance expansion',
    'duplicate_key': 'equality of parsed finite float timestamps over the entire original GT',
    'exclusion_predicate': 'any(abs(t - d) <= 0.051 for d in all_duplicate_float_timestamps)',
    'half_width_seconds': HALF_WIDTH,
    'union': 'all GT rows satisfying at least one closed-neighborhood predicate are excluded',
    'line_policy': 'preserve original bytes and order of every retained data/comment/blank line',
    'pose_values': 'seven pose tokens are counted structurally but never parsed as numbers',
    'barrier_requirement': 'each duplicate key has nearest retained GT gap strictly greater than 0.100 seconds, or is at a retained trajectory boundary',
    'output_requirement': 'at least one GT data row, unique strictly increasing retained float timestamps',
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def byte_sha(value):
    return hashlib.sha256(value).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strict_json(payload):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'Duplicate JSON key: ' + key)
            value[key] = item
        return value
    def bad(value):
        raise ValueError('Nonfinite JSON token: ' + value)
    return json.loads(payload, object_pairs_hook=unique, parse_constant=bad)


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    temporary.replace(path)


def tree_inventory(root):
    """Enumerate and hash regular files, rejecting every symbolic/special entry."""
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), 'Source/data root must be a real directory, not a symlink')
    root = root.resolve(strict=True)
    pending, directories, files = [root], [], []
    while pending:
        folder = pending.pop()
        for path in sorted(folder.iterdir(), key=lambda p: p.name):
            mode = path.lstat().st_mode
            require(not stat.S_ISLNK(mode), 'Symbolic link rejected: ' + str(path))
            relative = str(path.relative_to(root))
            if stat.S_ISDIR(mode):
                directories.append(relative)
                pending.append(path)
            elif stat.S_ISREG(mode):
                before = path.stat()
                digest = sha(path)
                after = path.stat()
                require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
                        (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
                        'File changed while hashing source tree: ' + relative)
                files.append(dict(path=relative, sha256=digest, bytes=after.st_size,
                                  inode=[after.st_dev, after.st_ino]))
            else:
                raise ValueError('Only regular files/directories are allowed: ' + str(path))
    return dict(directories=sorted(directories), files=sorted(files, key=lambda row: row['path']))


def derive_gt(payload):
    """Return original retained line bytes and a timestamp-only audit record.

    Malformed rows/nonfinite time fail immediately. Output/barrier validation
    flags are returned so a failed real attempt can retain the full exclusion
    audit before refusing release. No pose token is parsed or rewritten.
    """
    lines = payload.splitlines(keepends=True)
    rows = []
    for number, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith(b'#'):
            continue
        fields = raw.split()
        require(len(fields) == 8, f'GT line {number} must have exactly 8 columns')
        try:
            timestamp = float(fields[0])
        except (ValueError, OverflowError) as error:
            raise ValueError(f'Invalid timestamp at GT line {number}') from error
        require(math.isfinite(timestamp), f'Nonfinite timestamp at GT line {number}')
        rows.append(dict(original_line=number, timestamp=timestamp, raw_line_sha256=byte_sha(raw)))
    counts = Counter(row['timestamp'] for row in rows)
    duplicates = sorted(t for t, count in counts.items() if count > 1)
    excluded, retained_rows = [], []
    for row in rows:
        matches = [d for d in duplicates if abs(row['timestamp'] - d) <= HALF_WIDTH]
        if matches:
            excluded.append(dict(row, duplicate_keys_covering_row=matches,
                reason='within_fixed_closed_binary64_neighborhood_of_duplicate_timestamp'))
        else:
            retained_rows.append(row)
    excluded_numbers = {row['original_line'] for row in excluded}
    kept_numbers = [i for i in range(1, len(lines)+1) if i not in excluded_numbers]
    source_to_output = {old: new for new, old in enumerate(kept_numbers, 1)}
    derived = b''.join(lines[i-1] for i in kept_numbers)
    row_times = {row['original_line']: row['timestamp'] for row in rows}
    mapping = [dict(original_line=i, derived_line=source_to_output[i],
        raw_line_sha256=byte_sha(lines[i-1]), kind='gt_data' if i in row_times else 'comment_or_blank',
        **({'timestamp': row_times[i]} if i in row_times else {})) for i in kept_numbers]
    retained = [dict(row, derived_line=source_to_output[row['original_line']]) for row in retained_rows]
    times = [row['timestamp'] for row in retained]
    ordered_unique = all(b > a for a, b in zip(times, times[1:]))
    barriers = []
    # For the neighbor check, sorted lookup does not change the emitted order.
    # An unsorted emitted trajectory is separately rejected, never silently sorted.
    sorted_rows = sorted(retained, key=lambda row: row['timestamp'])
    sorted_times = [row['timestamp'] for row in sorted_rows]
    for d in duplicates:
        left_index = bisect_left(sorted_times, d)-1
        right_index = bisect_right(sorted_times, d)
        left = sorted_rows[left_index] if left_index >= 0 else None
        right = sorted_rows[right_index] if right_index < len(sorted_rows) else None
        if left is not None and right is not None:
            gap = right['timestamp']-left['timestamp']
            require(math.isfinite(gap), 'Nonfinite gap between retained GT neighbors')
            boundary, passed = None, gap > MAX_INTERPOLATION_GAP
        else:
            gap = None
            boundary = 'no_retained_rows' if left is None and right is None else (
                'left_trajectory_boundary' if left is None else 'right_trajectory_boundary')
            passed = True
        barriers.append(dict(duplicate_timestamp=d,
            duplicate_original_lines=[row['original_line'] for row in rows if row['timestamp'] == d],
            left_retained=left, right_retained=right, gap_seconds=gap, boundary=boundary,
            satisfies_strict_gap_or_boundary=passed))
    # The transform is checked through independent source-line subtraction.
    expected_lines = [raw for number, raw in enumerate(lines, 1) if number not in excluded_numbers]
    byte_identity = derived == b''.join(expected_lines)
    # splitlines preserves source line endings; deleting lines can only join a
    # final unterminated line when it was already final in the source.
    line_identity = derived.splitlines(keepends=True) == expected_lines
    report = dict(rule=RULE, original_gt_sha256=byte_sha(payload), derived_gt_sha256=byte_sha(derived),
        original_total_lines=len(lines), derived_total_lines=len(kept_numbers),
        original_gt_rows=len(rows), derived_gt_rows=len(retained),
        duplicate_groups=[dict(timestamp=d, count=counts[d],
            original_lines=[row['original_line'] for row in rows if row['timestamp'] == d]) for d in duplicates],
        excluded_gt_rows=len(excluded), excluded_rows=excluded, retained_gt_rows=retained,
        retained_line_mapping=mapping, barriers=barriers,
        validation=dict(nonempty_gt=bool(retained), timestamps_strictly_increasing_and_unique=ordered_unique,
            every_duplicate_key_removed=not any(t in counts and counts[t] > 1 for t in times),
            every_barrier_valid=all(row['satisfies_strict_gap_or_boundary'] for row in barriers),
            exact_original_minus_declared_excluded_lines=byte_identity,
            retained_line_bytes_and_order_exact=line_identity))
    report['validation']['all_passed'] = all(report['validation'].values())
    return derived, report


def source_path(name):
    path = Path(name)
    return (path if path.is_absolute() else ROOT / path).resolve(strict=True)


def copy_independent(source, target, expected_sha):
    """Exclusive streamed copy; a new inode is mandatory, not just a new name."""
    h = hashlib.sha256()
    with Path(source).open('rb') as src, Path(target).open('xb') as dst:
        for chunk in iter(lambda: src.read(1024*1024), b''):
            h.update(chunk)
            dst.write(chunk)
    require(h.hexdigest() == expected_sha and sha(target) == expected_sha, 'Independent copy SHA mismatch: ' + str(source))
    original, copied = Path(source).stat(), Path(target).stat()
    require((original.st_dev, original.st_ino) != (copied.st_dev, copied.st_ino),
            'Copy shares the original inode: ' + str(source))
    return dict(source_inode=[original.st_dev, original.st_ino], derived_inode=[copied.st_dev, copied.st_ino],
                independent_inode=True, source_sha256=expected_sha, derived_sha256=expected_sha,
                bytes=copied.st_size)


def run(args):
    output = Path(args.output).absolute()
    require(not output.exists() and not output.is_symlink(), 'Use a fresh derivative output parent; preserve prior attempts')
    source_input = Path(args.source)
    require(not source_input.is_symlink(), 'Symbolic source root rejected')
    source = source_input.resolve(strict=True)
    require(source.is_dir(), 'Source must be a directory')
    require(source.name == DATASET, 'Unexpected source dataset name')
    resolved_output = output.resolve()
    require(not resolved_output.is_relative_to(source) and not source.is_relative_to(resolved_output),
            'Derivative output and original source must not contain each other')
    output.mkdir(parents=True, exist_ok=False)
    derived_root = output / DATASET
    report = dict(schema='tum-timestamp-derivative-v1', status='running', started_utc=utc(), phase='freeze_validation',
        source=str(source), output=str(output.resolve()), derived_dataset_path=str(derived_root.resolve()),
        derivative_not_original_dataset=True, rule=RULE, images_decoded=False, gt_pose_values_parsed=False,
        model_run=False, samples_selected=False, files=[])
    def checkpoint():
        write_json(output / 'derivation_metadata.json', report)
    checkpoint()
    try:
        (output / 'README.md').write_text('本目录为本研究的时间戳排除派生数据准备，尚未完成。原始数据不能据此标为已修复。\n')
        protocol_bytes = Path(args.protocol).read_bytes()
        freeze_bytes = Path(args.design_freeze).read_bytes()
        freeze = strict_json(freeze_bytes)
        protocol_sha = byte_sha(protocol_bytes)
        require(freeze.get('protocol_sha256') == protocol_sha, 'V2 protocol changed after design freeze')
        identities = {source_path(name): digest for name, digest in freeze.get('source_sha256', {}).items()}
        require(len(identities) == len(freeze.get('source_sha256', {})), 'Duplicate frozen source path aliases')
        require(Path(__file__).resolve() in identities, 'Design freeze must include this derivation script source hash')
        for path, digest in identities.items():
            require(sha(path) == digest, 'Frozen source changed: ' + str(path))
        (output / 'frozen_protocol.md').write_bytes(protocol_bytes)
        (output / 'design_freeze.json').write_bytes(freeze_bytes)
        (output / 'derivation_runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
        report.update(protocol_sha256=protocol_sha, design_freeze_sha256=byte_sha(freeze_bytes),
            design_frozen_utc=freeze['frozen_utc'], runner_sha256=identities[Path(__file__).resolve()],
            frozen_source_sha256=freeze['source_sha256'], freeze_verified_utc=utc())
        require(datetime.fromisoformat(freeze['frozen_utc']) <= datetime.fromisoformat(report['freeze_verified_utc']),
                'Design freeze is dated after processing')
        report['phase'] = 'source_inventory'
        checkpoint()
        before = tree_inventory(source)
        require(any(row['path'] == 'groundtruth.txt' for row in before['files']), 'Missing original GT file')
        source_hashes = {row['path']: row['sha256'] for row in before['files']}
        require(source_hashes['groundtruth.txt'] == freeze.get('original_gt_sha256'),
                'Original GT does not match the frozen source identity')
        report['source_inventory_before'] = before
        report['original_gt_sha256'] = source_hashes['groundtruth.txt']
        report['phase'] = 'timestamp_only_derivation'
        checkpoint()
        original_gt = source / 'groundtruth.txt'
        original_payload = original_gt.read_bytes()
        require(byte_sha(original_payload) == source_hashes['groundtruth.txt'], 'Original GT changed before parsing')
        derived_payload, gt_report = derive_gt(original_payload)
        report['gt_derivation'] = gt_report
        report['derived_gt_sha256'] = gt_report['derived_gt_sha256']
        checkpoint()
        require(gt_report['validation']['all_passed'], 'Derived GT failed strict order/nonempty/barrier/line-byte validation')
        derived_root.mkdir()
        for relative in before['directories']:
            (derived_root / relative).mkdir(parents=True, exist_ok=True)
        report['phase'] = 'independent_file_copies'
        checkpoint()
        for row in before['files']:
            relative = row['path']
            src, dst = source / relative, derived_root / relative
            require(not src.is_symlink() and src.is_file() and sha(src) == row['sha256'],
                    'Source file changed before copy: ' + relative)
            if relative == 'groundtruth.txt':
                with dst.open('xb') as stream:
                    stream.write(derived_payload)
                target_stat, source_stat = dst.stat(), src.stat()
                require(sha(dst) == gt_report['derived_gt_sha256'], 'Written derivative GT differs from retained bytes')
                require((target_stat.st_dev, target_stat.st_ino) != (source_stat.st_dev, source_stat.st_ino),
                        'Derived GT shares the source inode')
                record = dict(source_sha256=row['sha256'], derived_sha256=gt_report['derived_gt_sha256'],
                    source_inode=[source_stat.st_dev, source_stat.st_ino],
                    derived_inode=[target_stat.st_dev, target_stat.st_ino], independent_inode=True,
                    bytes=target_stat.st_size, transformation='fixed_timestamp_neighborhood_exclusion')
            else:
                record = copy_independent(src, dst, row['sha256'])
                record['transformation'] = 'byte_identical_independent_copy'
            report['files'].append(dict(path=relative, **record))
        report['phase'] = 'final_full_integrity'
        checkpoint()
        after = tree_inventory(source)
        report['source_inventory_after'] = after
        require(before == after, 'Original source tree files/directories/inodes/hashes changed during derivation')
        derived_inventory = tree_inventory(derived_root)
        report['derived_inventory'] = derived_inventory
        require(derived_inventory['directories'] == before['directories'] and
                [r['path'] for r in derived_inventory['files']] == [r['path'] for r in before['files']],
                'Derivative file or directory membership differs from original')
        expected = {r['path']: r['derived_sha256'] for r in report['files']}
        originals_by_path = {r['path']: r for r in before['files']}
        for row in derived_inventory['files']:
            require(row['sha256'] == expected[row['path']], 'Derivative changed after copy: ' + row['path'])
            original_row = originals_by_path[row['path']]
            require(row['inode'] != original_row['inode'], 'Derivative shares original inode: ' + row['path'])
            if row['path'] != 'groundtruth.txt':
                require(row['sha256'] == original_row['sha256'] and row['bytes'] == original_row['bytes'],
                        'Non-GT bytes changed: ' + row['path'])
        require(sha(original_gt) == freeze['original_gt_sha256'] == report['original_gt_sha256'],
                'Original GT changed at completion')
        # Freshly subtract original lines again; do not merely trust output hash.
        excluded = {r['original_line'] for r in gt_report['excluded_rows']}
        subtraction = b''.join(raw for i, raw in enumerate(original_gt.read_bytes().splitlines(keepends=True), 1)
                               if i not in excluded)
        require((derived_root / 'groundtruth.txt').read_bytes() == subtraction == derived_payload,
                'Final derivative is not exactly original minus declared excluded lines')
        for path, expected_sha in identities.items():
            require(sha(path) == expected_sha, 'Frozen source changed during derivation: ' + str(path))
        require(sha(args.protocol) == protocol_sha and sha(args.design_freeze) == byte_sha(freeze_bytes),
                'V2 protocol/design freeze changed during derivation')
        require(sha(output / 'derivation_runner_snapshot.py') == report['runner_sha256'] and
                sha(output / 'frozen_protocol.md') == protocol_sha and
                sha(output / 'design_freeze.json') == byte_sha(freeze_bytes), 'Saved freeze/source snapshot changed')
        report.update(status='completed', phase='complete', source_tree_unchanged=True,
            original_gt_unchanged=True, non_gt_copies_verified=len(report['files'])-1,
            all_copy_inodes_independent=True, exact_declared_line_subtraction_verified=True,
            text_file_sha256={name: sha(derived_root / name) for name in ('rgb.txt', 'depth.txt', 'groundtruth.txt')
                              if (derived_root / name).is_file()})
        (output / 'README.md').write_text(
            '本目录为本研究的时间戳排除派生版本，已按冻结V2规则完成字节与时间戳核验。\n\n'
            'groundtruth.txt对所有重复float时间键按 abs(t-d)<=0.051 的固定闭邻域取并集弃用；'
            '每个保留行原字节和顺序不变。其他全部文件是原件的独立字节副本。'
            '这不是未改的官方解压树，也不是对官方位姿真值已修复或无误差的声明。\n\n'
            '未解码图片、未解析位姿值、未选取新样本、未运行模型。完整源/新SHA、独立inode、'
            '排除行及保留映射见derivation_metadata.json；原包和原解压树保持不变。\n')
    except BaseException:
        report['status'] = 'failed'
        report['phase_failed'] = report['phase']
        report['traceback'] = traceback.format_exc()
        (output / 'README.md').write_text('本研究的时间戳派生准备尚未完成，失败证据保留。请勿使用为完成输入。'
                                        '见derivation_metadata.json；重试须用全新目录。\n')
        raise
    finally:
        report['completed_utc'] = utc()
        checkpoint()
    print(json.dumps(dict(status=report['status'], source_tree_unchanged=report['source_tree_unchanged'],
        original_gt_sha256=report['original_gt_sha256'], derived_gt_sha256=report['derived_gt_sha256'],
        excluded_gt_rows=report['gt_derivation']['excluded_gt_rows'],
        non_gt_copies_verified=report['non_gt_copies_verified'], completed_utc=report['completed_utc'])), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'output', 'protocol', 'design-freeze'):
        parser.add_argument('--' + name, type=Path, required=True)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
