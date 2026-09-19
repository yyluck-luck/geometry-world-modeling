"""Copy the completed S35 code and synthetic evidence without changing originals."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
WS = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
PREP = ROOT/'work/S35_generation_integration'
OUT = WS/'outputs/S35_原循环接线准备与人工检查_2026-09-07'


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    final_report = ROOT/'docs/S35_RESULTS.md'
    assert sha(final_report) == '1b8d88c979e61ee113f393a5df5321cdac7da98adfe7af350f5e723df20d447a'
    assert (PREP/'report_claim_review.json').is_file()
    assert (PREP/'executed_results_review.json').is_file()
    OUT.mkdir(parents=True, exist_ok=False)
    sources = [p for p in PREP.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    mapping = {p: OUT/'代码与完整人工记录'/p.relative_to(PREP) for p in sources}
    mapping[final_report] = OUT/'S35报告.md'
    pattern = re.compile(r'(?<!!)\[([^\]]*)\]\((<[^>]*>|[^)\n]*)\)')
    records = []
    for source, dest in mapping.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        raw = source.read_bytes()
        original_sha = hashlib.sha256(raw).hexdigest()
        converted = False
        if source.suffix.lower() == '.md':
            text = raw.decode('utf-8')
            def rewrite(match):
                target = match.group(2).strip('<>')
                if not target or target.startswith(('#','http:','https:','mailto:')):
                    return match.group(0)
                path, marker, fragment = target.partition('#')
                absolute = Path(path) if Path(path).is_absolute() else source.parent/path
                absolute = absolute.resolve()
                resolved = mapping.get(absolute, absolute)
                return '['+match.group(1)+'](<'+str(resolved)+(marker+fragment if marker else '')+'>)'
            raw = pattern.sub(rewrite, text).encode('utf-8')
            converted = hashlib.sha256(raw).hexdigest() != original_sha
        with dest.open('xb') as handle:
            handle.write(raw)
        assert dest.read_bytes() == raw
        records.append(dict(path=str(dest.relative_to(OUT)), bytes=dest.stat().st_size,
            sha256=sha(dest), source=str(source), source_sha256=original_sha,
            markdown_link_rewrite_only=converted))
    # Preserve the exact primary report bytes alongside its readable link copy.
    original = OUT/'原报告字节/S35_RESULTS.md.txt'
    original.parent.mkdir()
    shutil.copy2(final_report, original)
    records.append(dict(path=str(original.relative_to(OUT)), bytes=original.stat().st_size,
        sha256=sha(original), source=str(final_report), source_sha256=sha(final_report),
        markdown_link_rewrite_only=False))
    readme = OUT/'先读我.md'
    readme.write_text(f'''# S35：接线准备与人工检查

**这轮完成了记录工具和人工检查，没有生成真实视频。** 检查实际运行约3.11秒；开启记录前后结果一致，第二批故意出错时保留了第一批。另一位agent核过完整保存证据。

- [看完整报告](<{OUT/'S35报告.md'}>)：做了什么、检查结果、具体时间、哪些还没做。
- [看代码与全部人工记录](<{OUT/'代码与完整人工记录'}>)：包括修改前版本、审查、冻结文件、成功与失败前缀；其中PNG全部是人工检查图，不是照片或真实模型效果。
- [上一轮8张真实照片和几何结果](<{WS/'outputs/S34_固定旧地图三条件与真实照片_2026-09-07/先读我.md'}>)。
- [当前项目记忆](<{ROOT/'RESEARCH_MEMORY.md'}>)和[实际时间账](<{ROOT/'RESEARCH_LOG.md'}>)：后续状态优先以这两个文件为准。

真实原模型组件仍未齐备，原50步采样、400步几何、完整视频和新方法收益均未完成。已成功的人工检查不用重复运行。

给下一位AI：这是本机档案快照，保留全部本轮人工载荷，但不是自带模型、依赖和原始项目的独立运行包。代码中的原项目路径应在科研项目内使用；本目录副本不应直接当作新的运行入口。`manifest.json`记录每份载荷的原件和副本SHA；Markdown仅转换链接，原报告字节单独保留。源审和失败历史按其实际时间解读，最终结果以S35报告和当前主账为准。
''')
    records.append(dict(path='先读我.md', bytes=readme.stat().st_size, sha256=sha(readme),
                        source=None, source_sha256=None, markdown_link_rewrite_only=False))
    manifest = dict(schema='s35-local-delivery-snapshot-v1', created_utc=datetime.now(timezone.utc).isoformat(),
        scope='Complete S35 code and synthetic evidence snapshot, linked to local original project; no real models or real video',
        payload_file_count=len(records), payload_bytes=sum(r['bytes'] for r in records), files=records)
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(directory=str(OUT), files=len(records)+1,
        payload_bytes=manifest['payload_bytes'], manifest_sha256=sha(OUT/'manifest.json')),ensure_ascii=False))


if __name__ == '__main__':
    main()
