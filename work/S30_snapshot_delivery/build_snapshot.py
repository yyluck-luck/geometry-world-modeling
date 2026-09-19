"""Copy sealed S30 text/figures and original RGB photos; never decode NPZ or GT."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import re
import sys
import urllib.parse

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WS = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
HERE = Path(__file__).resolve().parent
OUT = WS / 'outputs/S30_优化损坏准确起点的真实证据_2026-09-07'
PREVIOUS = WS / 'outputs/S29_初始化尺度的真实证据_2026-09-07'
REPORT_SHA = '9efdb256bd988c1ed91aaa42a887dbd9c852918bdfc538b84f12312de040934c'
CONTRACT_SHA = '000fa5d5b19cc516a581b382e457dcf8e03494da50b220d8f32c0ad0b16224a3'
FIGURE_MANIFEST_SHA = '365dff0cbcd50cedbe7290a8be9505d5a686f7b971fa43a4f0ddb5caae38e6ee'
LINKS = re.compile(r'(!?\[[^\]\n]*\])\((<[^>]+>|[^)]+)\)')


def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
def link(label, p): return f'[{label}](<{p}>)'


def main():
    started = now()
    assert not OUT.exists(), 'Do not overwrite an existing snapshot'
    report = ROOT / 'docs/S30_RESULTS.md'
    prep = ROOT / 'work/S30_scale_optimization_preparation'
    figures = ROOT / 'work/S30_reporting'
    result = ROOT / 'results/S30_scale_optimization'
    audit = ROOT / 'work/S30_independent_numeric_review'
    assert sha(report) == REPORT_SHA
    assert sha(prep / 'contract.json') == CONTRACT_SHA
    assert sha(figures / 'manifest.json') == FIGURE_MANIFEST_SHA
    assert sha(PREVIOUS / 'manifest.json') == '82c727f6e76dc59b82be6d4a3236626ee30047c758fa1788d168d1d058188fe9'
    write(HERE / 'attempt.json', dict(started_utc=started, target=str(OUT), command=[sys.executable, str(Path(__file__))], script_sha256=sha(Path(__file__))))
    planned = []
    def add(source, destination): planned.append((source, destination))
    add(report, 'S30_RESULTS.md')
    add(report, '证据/S30_RESULTS.original_source.txt')
    for name in ('contract.json', 'PLAN_CANDIDATE.md', 'EXECUTION_NOTES.md', 'run_s30.py', 'score_s30.py', 'prepare_s30.py', 'getter.diff', 'observer.diff', 'worker.diff', 'derivation_proof.json', 'source_read_manifest.json'):
        add(prep / name, '合同与代码/' + name)
    figure_manifest = read(figures / 'manifest.json')
    for name, metadata in figure_manifest['files'].items():
        assert sha(figures / name) == metadata['sha256']
        add(figures / name, '图表/' + name)
    add(figures / 'manifest.json', '图表/manifest.json')
    producers = {}
    for arm in ('C2t', 'C2a'):
        base = result / arm
        receipt = read(base / 'receipt.json')
        assert receipt['status'] == 'PASS' and receipt['s30_contract_sha256'] == CONTRACT_SHA
        assert receipt['adam_steps'] == 400 and receipt['iterations'] == 400
        producers[arm] = receipt
        add(base / 'receipt.json', f'真实优化/{arm}/receipt.json')
        # Full saved logs and metadata. No NPZ access, including hashing.
        for name, identity in receipt['outputs'].items():
            if name.endswith(('.json', '.jsonl')):
                assert sha(base / name) == identity
                add(base / name, f'真实优化/{arm}/{name}')
        for name in ('optimization_trace.jsonl', 'gradient_depth_trace.jsonl'):
            assert len((base / name).read_text().splitlines()) == 400
        old = ROOT / 'results/S29_scale_control' / arm
        old_receipt = read(old / 'receipt.json')
        assert old_receipt['status'] == 'PASS_INITIALIZATION_EXECUTED'
        add(old / 'receipt.json', f'已存S29零步/{arm}/receipt.json')
        for name in ('initial_raw_metadata.json', 'inputs_seal.json'):
            assert sha(old / name) == old_receipt['outputs'][name]
            add(old / name, f'已存S29零步/{arm}/{name}')
    add(ROOT / 'results/S29_scale_control/validation/receipt.json', '已存S29零步/validation_receipt.json')
    score = read(result / 'scoring/receipt.json')
    assert score['status'] == 'PASS' and score['contract_sha256'] == CONTRACT_SHA
    assert score['per_frame_rows'] == 16 and score['endpoint_groups'] == 4
    add(result / 'scoring/receipt.json', '四端点评分/receipt.json')
    for name, identity in score['outputs'].items():
        assert sha(result / 'scoring' / name) == identity
        add(result / 'scoring' / name, '四端点评分/' + name)
    with (result / 'scoring/per_frame.csv').open() as f:
        assert len(list(csv.DictReader(f))) == 16
    numeric = read(audit / 'receipt.json')
    assert numeric['status'] == 'PASS' and numeric['contract_sha256'] == CONTRACT_SHA
    add(audit / 'receipt.json', '不同作者数值复核/receipt.json')
    for name, identity in numeric['outputs'].items():
        assert sha(audit / name) == identity
        add(audit / name, '不同作者数值复核/' + name)
    for name in ('protocol.md', 'recompute.py'):
        add(audit / name, '不同作者数值复核/' + name)
    add(ROOT / 'work/S30_independent_numeric_execution/review/receipt.json', '不同作者数值复核/caller_receipt.json')
    add(ROOT / 'work/S30_launch/receipt.json', '执行/launch_receipt.json')
    add(ROOT / 'work/S30_execution/dispatch_receipt.json', '执行/dispatch_receipt.json')
    for phase in ('C2t', 'C2a', 'scoring'):
        add(ROOT / 'work/S30_execution' / phase / 'receipt.json', f'执行/{phase}_caller_receipt.json')
    for name in ('final_pre_review.json', 'final_pre_review.md'):
        add(ROOT / 'work/S30_independent_review' / name, '执行/不同作者前审/' + name)
    add(ROOT / 'work/S30_root_pre_review/final_review.json', '执行/root_pre_review.json')
    photo_source = PREVIOUS / '真实照片_本轮4帧/照片来源.json'
    photos = read(photo_source)
    assert len(photos['frames']) == 4
    for row in photos['frames']:
        src = PREVIOUS / row['copied_file']
        assert sha(src) == row['original_manifest_sha256'] == row['copied_sha256']
        add(src, row['copied_file'])
    add(photo_source, '真实照片_本轮4帧/S29照片来源原件.json')
    # Resolve all copied report links to this snapshot when available, otherwise
    # retain a checked canonical absolute path. Only Markdown destinations change.
    mapping = {source: OUT / dest for source, dest in planned if not dest.endswith('.txt')}
    assert len({dest for _, dest in planned}) == len(planned)
    rewrites = []
    def normalize(text, source):
        def sub(m):
            raw = m.group(2).strip().strip('<>')
            if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', raw) or raw.startswith('#'):
                return m.group(0)
            path = Path(urllib.parse.unquote(raw))
            path = path if path.is_absolute() else (source.parent / path).resolve()
            assert path.exists(), str(path)
            target = mapping.get(path, path)
            rewrites.append(dict(source=str(source), original=raw, target=str(target)))
            return f'{m.group(1)}(<{target}>)'
        return LINKS.sub(sub, text)
    records = []
    for source, name in planned:
        target = OUT / name
        original = source.read_bytes()
        identity = hashlib.sha256(original).hexdigest()
        payload = normalize(original.decode(), source).encode() if target.suffix == '.md' else original
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        assert target.read_bytes() == payload and sha(source) == identity
        records.append(dict(path=name, source=str(source), source_sha256=identity, sha256=sha(target), bytes=len(payload), byte_identical_to_source=payload == original, verification='Exact byte copy' if payload == original else 'Only Markdown link destinations normalized; source and transformed bytes checked'))
    write(OUT / '真实照片_本轮4帧/照片来源.json', dict(recorded_utc=now(), previous_photo_record=str(photo_source), previous_photo_record_sha256=sha(photo_source), previous_snapshot_manifest_sha256=sha(PREVIOUS / 'manifest.json'), frames=[dict(index=row['index'], rgb_time=row['rgb_time'], original_rgb_path=row['original_rgb_path'], original_sha256=row['original_manifest_sha256'], immediate_copy_source=str(PREVIOUS / row['copied_file']), copied_file=row['copied_file'], copied_sha256=sha(OUT / row['copied_file'])) for row in photos['frames']], scope='Four byte-identical real RGB photos. No sensor-depth PNG, generated image, or image editing.'))
    big = []
    for stage, folder in [('S29', ROOT / 'results/S29_scale_control'), ('S30', result)]:
        for arm in ('C2t', 'C2a'):
            receipt_path = folder / arm / 'receipt.json'
            for name, identity in read(receipt_path)['outputs'].items():
                if name.endswith('.npz'):
                    path = folder / arm / name
                    assert path.is_file()
                    big.append(dict(stage=stage, arm=arm, path=str(path), bytes=path.stat().st_size, expected_sha256=identity, sha_source=str(receipt_path), copied=False, payload_read=False, verification='Existence and stat only; identity inherited from sealed producer, not rehashed during packaging'))
    write(OUT / '大型数组_仅链接.json', dict(recorded_utc=now(), files=big))
    (OUT / '大型数组_仅链接.md').write_text('# 大型数组：保留本机链接\n\n本次打包只检查存在与大小；SHA 沿用封存的 producer 回执，没有读取、解码或重新哈希 NPZ。复制到另一台电脑时需同时迁移原项目，或重映射这些路径。\n\n' + '\n'.join('- ' + link(x['stage'] + '/' + x['arm'] + '/' + Path(x['path']).name, x['path']) for x in big) + '\n')
    (OUT / '先读我.md').write_text(f'''# 先读我：S30 优化损坏准确起点的真实证据

**这四张已见照片上，较准的起点经过原来的 400 步优化后明显变差。** 单位尺度起点 C2a 的平均相对深度误差从 **5.039050% 升至 42.379473%**；原尺度起点 C2t 从 **83.338230% 升至 87.471275%**。误差越低越好，两臂自己的优化目标都在下降。这给出了一个需要解释的真实失败，尚未形成新方法。

先看 {link('完整报告', OUT / 'S30_RESULTS.md')} 和 {link('四个端点结果图', OUT / '图表/s30_endpoint_accuracy.png')}，再看 {link('全部优化和深度轨迹', OUT / '图表/s30_optimization_trajectories.png')}。图中保留全部 16 个逐帧评分点、4 个等帧均值、800 条真实优化记录与两项实际终点目标；没有伪造逐步 GT 准确率或独立重复实验误差条。两图已有作者与 root 实际 PNG 查看记录，PDF/SVG 未另作渲染认证。

本快照收录：

- {link('本轮四张真实 RGB 照片', OUT / '真实照片_本轮4帧')}：从 S29 快照原样复制，逐字节匹配原冻结输入 SHA；这些是已有实拍照片。
- {link('全部 16 行评分', OUT / '四端点评分/per_frame.csv')}、{link('精确指标', OUT / '四端点评分/metrics.json')}与{link('评分封存回执', OUT / '四端点评分/receipt.json')}。
- {link('C2t 全部真实轨迹', OUT / '真实优化/C2t/gradient_depth_trace.jsonl')}、{link('C2a 全部真实轨迹', OUT / '真实优化/C2a/gradient_depth_trace.jsonl')}，以及每臂原普通优化日志、33 项初态元数据和终态证据。
- {link('冻结合同与最小派生代码', OUT / '合同与代码')}、{link('真实执行回执', OUT / '执行/launch_receipt.json')}、{link('不同作者完整数值复核', OUT / '不同作者数值复核/receipt.json')}和{link('中文图注', OUT / '图表/caption_zh.md')}。
- {link('S29 已存零步来源', OUT / '已存S29零步')}及{link('大型数组的本机链接', OUT / '大型数组_仅链接.md')}。数组没有全复制，运行源码也依赖原项目的已封存父实现；此目录不是可脱离原项目独立运行的环境。

四组分数使用每帧有效 GT 像素计算指标，再对四帧等权平均；不是把所有像素混合计分。给定 GT 相机是明确的 oracle 输入条件，传感器深度只在四端点全部封存后评分。两臂均修复原深度梯度断链；只有初始化尺度不同，训练期间尺度仍自由，未以 GT 拟合尺度、选步或按置信度筛像素。

S30 实际执行 UTC 2026-09-06 18:12:29.415572 至 18:13:32.552760（北京时间次日 02:12:29 至 02:13:32），包含 800 新 Adam 步、800 次反传、2 次初始化、6 次 PnP、0 新网络。不同作者保存量复核 UTC 18:21:29.386122 至 18:21:31.143825 完成，不重跑模型或优化。本快照打包开始于 {started}，只复制与核对已存文件，不新增模型、GT 读取、评分、数组解码或优化。

截至本快照，S31 仍只是准备：用预测自身的起终点做一个不看 GT 的公共尺度分解，判断统一缩放能解释多少变化，再决定下一项实验。尚无跨场景、长期记忆干预、完整视频生成或新方法收益；PhD 深度与 CCF A 投稿质量仍是目标。报告源 SHA：`{REPORT_SHA}`。

快照内的 Markdown 链接已转换为绝对本机路径并检查存在；可复制的主要证据指向本快照，少量当前记忆/前序报告链接指向原项目，后者会随研究继续更新。{link('完整文件身份清单', OUT / 'manifest.json')}记录本次截点。
''')
    # Manifest is generated after link checking; count its known pending path as
    # an explicit artifact, then verify it exists immediately after writing.
    checked = []
    for doc in OUT.rglob('*.md'):
        for m in LINKS.finditer(doc.read_text()):
            raw = m.group(2).strip().strip('<>')
            if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', raw) or raw.startswith('#'):
                continue
            path = Path(urllib.parse.unquote(raw))
            assert path.is_absolute() and (path.exists() or path == OUT / 'manifest.json'), f'{doc}: {path}'
            checked.append(dict(document=str(doc.relative_to(OUT)), target=str(path)))
    write(OUT / '本地链接核查.json', dict(status='PASS', checked_utc=now(), scope='All active snapshot Markdown local destinations; final manifest link checked after manifest write', count=len(checked), links=checked, rewrites=rewrites))
    for record in records:
        assert sha(Path(record['source'])) == record['source_sha256']
        assert sha(OUT / record['path']) == record['sha256']
    known = {r['path']: r for r in records}
    files = [known.get(str(p.relative_to(OUT)), dict(path=str(p.relative_to(OUT)), sha256=sha(p), bytes=p.stat().st_size, source='Generated navigation or provenance from saved metadata')) for p in sorted(OUT.rglob('*')) if p.is_file()]
    manifest = dict(status='PASS_SNAPSHOT_COPY_AND_LINK_CHECK', started_utc=started, completed_utc=now(), root=str(OUT), source_report_sha256=REPORT_SHA, source_contract_sha256=CONTRACT_SHA, figure_manifest_sha256=FIGURE_MANIFEST_SHA, payload_file_count=len(files), total_file_count_including_manifest=len(files) + 1, payload_bytes=sum(x['bytes'] for x in files), copy_count=len(records), copies_source_and_destination_sha_verified=True, active_markdown_links_checked=len(checked), all_active_local_links_exist=True, script_path=str(Path(__file__)), script_sha256=sha(Path(__file__)), command=[sys.executable, str(Path(__file__))], state_cutoff='S30 optimization and different-author numerical review complete; S31 preparation only', limits=['Seen common4 with given GT-camera oracle input; no new method, generalization or video result', 'All saved records included, not new scoring or gradient replication', 'NPZ never read/copied/rehashed here; producer identities inherited and file existence checked', 'Parent-source code and external links require the canonical project; not a standalone environment', 'Plot PNGs viewed by author and root; PDF/SVG not independently raster-rendered'], files=files)
    write(OUT / 'manifest.json', manifest)
    assert all(Path(x['target']).exists() for x in checked)
    assert len([p for p in OUT.rglob('*') if p.is_file()]) == len(files) + 1
    delivery = dict(status=manifest['status'], started_utc=started, completed_utc=now(), snapshot=str(OUT), manifest_sha256=sha(OUT / 'manifest.json'), file_count=len(files) + 1, payload_bytes=manifest['payload_bytes'], links_checked=len(checked), copied_RGB_photos=4, saved_metric_rows=16, saved_trace_rows_per_log_type=800, NPZ_payload_reads=0, GT_reads=0, new_optimization=0)
    write(HERE / 'receipt.json', delivery)
    print(json.dumps(delivery, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        write(HERE / 'failure.json', dict(status='FAILED', recorded_utc=now(), error=repr(exc), snapshot=str(OUT), originals_untouched=True))
        raise
