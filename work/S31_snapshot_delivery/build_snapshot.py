"""Package saved S31 evidence only. No NPZ/GT bytes or scientific execution."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import json
import re
import sys
import urllib.parse

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WS = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
HERE = Path(__file__).resolve().parent
OUT = WS / 'outputs/S31_尺度恢复后仍输给起点_2026-09-07'
PREVIOUS = WS / 'outputs/S30_优化损坏准确起点的真实证据_2026-09-07'
CONTRACT_SHA = '85d535ca913ed5a913cd259070bacd8b316a34e40aef1a55dd5043303b5f2587'
PREVIOUS_SHA = 'b3e920ba3c0404f5c34389291576d20f091223a355f5b96839ab717de72cfeb9'
PAT = re.compile(r'(!?\[[^\]\n]*\])\((<[^>]+>|[^)]+)\)')

def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def link(label, p): return f'[{label}](<{p}>)'
def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main(report_sha):
    started = now()
    report = ROOT / 'docs/S31_RESULTS.md'
    prep = ROOT / 'work/S31_scale_shape_preparation'
    result = ROOT / 'results/S31_scale_shape_diagnostic'
    audit = ROOT / 'work/S31_root_numeric_review'
    assert re.fullmatch('[0-9a-f]{64}', report_sha) and sha(report) == report_sha
    assert not OUT.exists(), 'Do not overwrite a snapshot'
    assert sha(prep / 'contract.json') == CONTRACT_SHA
    assert sha(PREVIOUS / 'manifest.json') == PREVIOUS_SHA
    write(HERE / 'attempt.json', dict(started_utc=started, source_report_sha256=report_sha, script_sha256=sha(Path(__file__)), target=str(OUT), command=[sys.executable, str(Path(__file__)), '--report-sha', report_sha]))
    plan = [(report, 'S31_RESULTS.md'), (report, '证据/S31_RESULTS.original_source.txt')]
    def add(p, name): plan.append((p, name))
    receipt = read(result / 'receipt.json')
    assert receipt['status'] == 'PASS' and receipt['contract_sha256'] == CONTRACT_SHA
    assert receipt['per_frame_rows'] == 8 and receipt['old_endpoint_rows_imported'] == 16 and receipt['old_endpoint_scores_recomputed'] == 0
    add(result / 'receipt.json', '完整诊断与8行评分/receipt.json')
    for name, identity in receipt['output_sha256'].items():
        if name.endswith(('.json', '.csv')):
            assert sha(result / name) == identity
            add(result / name, '完整诊断与8行评分/' + name)
    with (result / 'per_frame.csv').open() as f:
        assert len(list(csv.DictReader(f))) == 8
    for name in ('contract.json', 'protocol.md', 'run_s31.py', 'prepare_candidate.py', 'synthetic_check.py', 'synthetic_check_receipt.json'):
        source = prep / name
        assert sha(source) == receipt['input_sha256'][str(source)]
        add(source, '合同与代码/' + name)
    independent = read(audit / 'receipt.json')
    assert independent['status'] == 'PASS' and independent['contract_sha256'] == CONTRACT_SHA
    add(audit / 'receipt.json', '不同作者另式复核/receipt.json')
    for name, identity in independent['output_sha256'].items():
        assert sha(audit / name) == identity
        add(audit / name, '不同作者另式复核/' + name)
    for name in ('protocol.md', 'recompute.py'):
        source = audit / name
        assert sha(source) == receipt['input_sha256'][str(source)]
        add(source, '不同作者另式复核/' + name)
    for sub, names in [
        ('S31_independent_pre_review', ('final_pre_review.json', 'final_pre_review.md', 'source_check_receipt.json')),
        ('S31_root_pre_review', ('review.json',)),
        ('S31_reference_static_review', ('review.json', 'review.md')),
    ]:
        for name in names:
            add(ROOT / 'work' / sub / name, '执行前审/' + sub + '/' + name)
    add(ROOT / 'work/S31_execution/dispatch_receipt.json', '两阶段执行/dispatch_receipt.json')
    add(ROOT / 'work/S31_freeze_and_launch.py', '两阶段执行/freeze_and_launch.py')
    for stage in ('diagnostic', 'independent_review'):
        caller = ROOT / 'work/S31_execution' / stage / 'receipt.json'
        assert read(caller)['status'] == 'PASS'
        add(caller, '两阶段执行/' + stage + '_receipt.json')
    # The old endpoint scores remain imported S30 scores; the snapshot does not
    # evaluate them again or relabel them as eight new S31 rows.
    imported = read(result / 'imported_S30_scores.json')
    assert sha(Path(imported['source'])) == imported['sha256']
    photo_record = PREVIOUS / '真实照片_本轮4帧/照片来源.json'
    photos = read(photo_record)
    assert len(photos['frames']) == 4
    for row in photos['frames']:
        source = PREVIOUS / row['copied_file']
        assert sha(source) == row['original_sha256'] == row['copied_sha256']
        add(source, row['copied_file'])
    add(photo_record, '真实照片_本轮4帧/S30照片来源原件.json')
    mapping = {p: OUT / name for p, name in plan if not name.endswith('.txt')}
    assert len({name for _, name in plan}) == len(plan)
    records, rewrites = [], []
    def normalized(text, source):
        def replace(m):
            raw = m.group(2).strip().strip('<>')
            if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', raw) or raw.startswith('#'): return m.group(0)
            p = Path(urllib.parse.unquote(raw))
            p = p if p.is_absolute() else (source.parent / p).resolve()
            assert p.exists(), str(p)
            target = mapping.get(p, p)
            rewrites.append(dict(source=str(source), original=raw, target=str(target)))
            return f'{m.group(1)}(<{target}>)'
        return PAT.sub(replace, text)
    for source, name in plan:
        target = OUT / name
        original = source.read_bytes()
        identity = hashlib.sha256(original).hexdigest()
        content = normalized(original.decode(), source).encode() if target.suffix == '.md' else original
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        assert target.read_bytes() == content and sha(source) == identity
        records.append(dict(path=name, source=str(source), source_sha256=identity, sha256=sha(target), bytes=len(content), byte_identical_to_source=original == content, verification='Exact bytes' if original == content else 'Only Markdown destinations normalized; source and transformed bytes checked'))
    write(OUT / '真实照片_本轮4帧/照片来源.json', dict(recorded_utc=now(), previous_record=str(photo_record), previous_record_sha256=sha(photo_record), previous_manifest_sha256=PREVIOUS_SHA, frames=[dict(index=row['index'], original_rgb_path=row['original_rgb_path'], original_sha256=row['original_sha256'], immediate_copy_source=str(PREVIOUS / row['copied_file']), copied_file=row['copied_file'], copied_sha256=sha(OUT / row['copied_file'])) for row in photos['frames']], scope='Same four real RGB photos from S30, byte-identical to original sealed identities; no image editing or GT images'))
    # Copy exact saved mean values into a six-row presentation table. No mean,
    # scale coefficient, diagnostic decomposition or score is recomputed here.
    metrics = read(result / 'metrics.json')
    table = []
    for arm in ('C2t', 'C2a'):
        for endpoint in ('initial', 'final', 'normalized_final'):
            old = endpoint != 'normalized_final'
            group = imported['metrics']['common4'][arm][endpoint] if old else metrics['normalized_common4'][arm]
            table.append(dict(arm=arm, endpoint=endpoint, absrel=group['absrel'], rmse_m=group['rmse_m'], delta1=group['delta1'], aggregation=group['aggregation'], source='imported_S30_scores.json' if old else 'metrics.json', score_role='Imported original S30 score; no new scoring here' if old else 'Existing S31 normalized-output score; no new scoring here'))
    with (OUT / '六端点完整均值.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(table[0])); writer.writeheader(); writer.writerows(table)
    names = {'initial': '零步起点（S29 保存、S30 已评分）', 'final': '原 400 步终点（S30 已评分）', 'normalized_final': '单公共尺度归一后（S31 已评分）'}
    table_text = '| 臂 | 端点 | AbsRel（%）↓ | RMSE（米）↓ | δ1（%）↑ |\n|---|---|---:|---:|---:|\n' + '\n'.join(f"| {row['arm']} | {names[row['endpoint']]} | {100*row['absrel']:.6f} | {row['rmse_m']:.9f} | {100*row['delta1']:.6f} |" for row in table)
    (OUT / '六端点完整均值.md').write_text('# 六端点完整均值\n\n' + table_text + '\n\n四帧各自计算指标后等权平均，不混合像素计分。表中四个原端点直接继承 S30 已封存分数，两个归一端点直接抄录 S31 已封存分数；本次只作表格格式化。百分数是保存的小数乘 100 显示，完整小数见同名 CSV。全部原 16 行和新 8 行均收录于“完整诊断与8行评分”中的 imported_S30_scores.json 与 per_frame.csv。\n')
    big = []
    for name, identity in receipt['output_sha256'].items():
        if name.endswith('.npz'):
            p = result / name; assert p.is_file()
            big.append(dict(path=str(p), bytes=p.stat().st_size, expected_sha256=identity, sha_source=str(result / 'receipt.json'), copied=False, payload_read=False))
    for arm in ('C2t', 'C2a'):
        for folder, name in [(ROOT / 'results/S29_scale_control' / arm, 'initial_decoded.npz'), (ROOT / 'results/S30_scale_optimization' / arm, 'output.npz')]:
            p = folder / name; assert p.is_file()
            big.append(dict(path=str(p), bytes=p.stat().st_size, expected_sha256=receipt['input_sha256'][str(p)], sha_source=str(result / 'receipt.json'), copied=False, payload_read=False))
    write(OUT / '大型数组_仅链接.json', dict(recorded_utc=now(), scope='Existence/stat only; SHA inherited from sealed receipt, not rehashed or decoded during packaging', files=big))
    (OUT / '大型数组_仅链接.md').write_text('# 大型数组：只提供本机链接\n\nSHA 沿用封存回执，本次仅检查存在与大小，未读取、解码或重哈希数组。\n\n' + '\n'.join('- ' + link(str(Path(row['path']).relative_to(ROOT)), row['path']) for row in big) + '\n')
    ca = read(result / 'C2a/decomposition.json'); ct = read(result / 'C2t/decomposition.json')
    (OUT / '先读我.md').write_text(f'''# 先读我：S31 尺度恢复后仍输给起点

**按预测自身恢复一个公共尺度后，C2a 的平均相对深度误差从 42.379473% 降到 11.566812%，仍高于零步起点的 5.039050%。** C2t 也从 87.471275% 降到 84.053104%，仍高于自己的 83.338230% 起点。误差越低越好。

{table_text}

这次不是又训练或优化了一遍。每臂从已存的全部四帧起点和终点深度计算同一个系数：`k=exp(-mean(log(D400)-log(D0)))`，再看 `k*D400`。C2a 的 k 为 `{ca['k']}`，C2t 为 `{ct['k']}`。没有用 GT 选择 k，没有逐帧调尺度、平移拟合或挑选有利步数；传感器深度只在输出封存后用于评分。

已保存的 log 深度变化中，公共项占 C2a 的 `{100*ca['components']['common_global_mean']['fraction_of_total']:.6f}%` 和 C2t 的 `{100*ct['components']['common_global_mean']['fraction_of_total']:.6f}%`。**这是 log 变化平方和的分解比例，不是 GT 误差解释率。** 有限结论是：统一输出缩放能恢复一部分准确性，却没有胜过不优化的起点；不能因此声称已经找到优化器的全部原因、物理形状破坏机制或新方法。

建议打开：

1. {link('完整正式报告', OUT / 'S31_RESULTS.md')}与{link('六端点完整均值', OUT / '六端点完整均值.md')}。
2. {link('全部 8 行归一结果', OUT / '完整诊断与8行评分/per_frame.csv')}、{link('原 16 行来源', OUT / '完整诊断与8行评分/imported_S30_scores.json')}，以及 {link('C2a 完整分解', OUT / '完整诊断与8行评分/C2a/decomposition.json')}和{link('C2t 完整分解', OUT / '完整诊断与8行评分/C2t/decomposition.json')}。
3. {link('两阶段实际回执', OUT / '两阶段执行')}、{link('不同作者另式复核', OUT / '不同作者另式复核/receipt.json')}、{link('冻结协议与源码', OUT / '合同与代码')}。
4. {link('本轮四张真实照片', OUT / '真实照片_本轮4帧')}：从 S30 快照原样复制并匹配原冻结 SHA；不是生成图。{link('大型数组只保留本机链接', OUT / '大型数组_仅链接.md')}，没有重复复制大数组。S30 的两张轨迹图仍在{link('前轮快照', PREVIOUS / '先读我.md')}；S31 不重画或冒用新曲线。

本轮实际诊断 UTC 2026-09-06 18:39:38.377241 至 18:39:39.991019，另式复核 18:39:40.439971 至 18:39:41.224466；北京时间为次日 02:39。两阶段都是已有保存量工作，0 新模型、MST、GA、反传或 Adam；诊断新增 8 行评分，原 16 行只导入，复核另算全部两臂结果。本次快照打包开始于 {started}，打包本身没有 GT/NPZ 读取、评分、绘图或新实验。

均值是四帧等权平均，四帧属于已见 common4，给定 GT 相机仍是 oracle 输入条件。源报告 SHA `{report_sha}`；本快照不把后续计划写成已完成，也不声称跨场景或视频收益。现有证据仍未达到原 proposal 的完整创新与生成验收目标。

主要证据链接指向本快照，剩余链接指向原项目；跨电脑迁移需保留原项目或重映射路径。{link('文件身份清单', OUT / 'manifest.json')}记录此交付截点，源码也仍依赖原项目，不能把这个文件夹当成独立运行环境。
''')
    checked = []
    for doc in OUT.rglob('*.md'):
        for m in PAT.finditer(doc.read_text()):
            raw = m.group(2).strip().strip('<>')
            if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', raw) or raw.startswith('#'): continue
            p = Path(urllib.parse.unquote(raw))
            assert p.is_absolute() and (p.exists() or p == OUT / 'manifest.json'), f'{doc}: {p}'
            checked.append(dict(document=str(doc.relative_to(OUT)), target=str(p)))
    write(OUT / '本地链接核查.json', dict(status='PASS', checked_utc=now(), count=len(checked), links=checked, rewrites=rewrites, scope='All active Markdown local links; pending manifest link verified after writing'))
    for row in records:
        assert sha(Path(row['source'])) == row['source_sha256'] and sha(OUT / row['path']) == row['sha256']
    known = {row['path']: row for row in records}
    files = [known.get(str(p.relative_to(OUT)), dict(path=str(p.relative_to(OUT)), sha256=sha(p), bytes=p.stat().st_size, source='Generated navigation/provenance or presentation table from saved JSON only')) for p in sorted(OUT.rglob('*')) if p.is_file()]
    manifest = dict(status='PASS_SNAPSHOT_COPY_AND_LINK_CHECK', started_utc=started, completed_utc=now(), root=str(OUT), source_report_sha256=report_sha, contract_sha256=CONTRACT_SHA, previous_snapshot_manifest_sha256=PREVIOUS_SHA, payload_file_count=len(files), total_file_count_including_manifest=len(files)+1, payload_bytes=sum(row['bytes'] for row in files), copy_count=len(records), all_source_copy_sha_verified=True, active_local_links_checked=len(checked), all_local_links_exist=True, script_path=str(Path(__file__)), script_sha256=sha(Path(__file__)), state_cutoff='S31 saved-data diagnostic and different-author root numerical review PASS; no new experiment or method claim', counts=dict(new_score_rows_already_produced=8, original_score_rows_imported=16, endpoint_means_presented=6, copied_RGB_photos=4, packaging_GT_reads=0, packaging_NPZ_reads=0, packaging_new_score=0, packaging_new_experiment=0, packaging_new_figure=0), limits=['Known common4 and given GT-camera oracle condition', 'Global log-change square-sum fraction is not GT-error explained fraction', 'Prediction-only output normalization is post-hoc diagnostic, not optimizer intervention or novelty', 'NPZ identities inherited; payload neither decoded nor rehashed during packaging', 'Absolute external links and inherited runtime sources require canonical local project'], files=files)
    write(OUT / 'manifest.json', manifest)
    assert all(Path(row['target']).exists() for row in checked)
    assert len([p for p in OUT.rglob('*') if p.is_file()]) == len(files)+1
    delivery = dict(status=manifest['status'], started_utc=started, completed_utc=now(), snapshot=str(OUT), manifest_sha256=sha(OUT / 'manifest.json'), file_count=len(files)+1, payload_bytes=manifest['payload_bytes'], links_checked=len(checked), source_report_sha256=report_sha, counts=manifest['counts'])
    write(HERE / 'receipt.json', delivery)
    print(json.dumps(delivery, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-sha', required=True)
    args = parser.parse_args()
    try:
        main(args.report_sha)
    except BaseException as exc:
        write(HERE / 'failure.json', dict(status='FAILED', recorded_utc=now(), error=repr(exc), originals_untouched=True))
        raise
