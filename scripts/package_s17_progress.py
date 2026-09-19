#!/usr/bin/env python3
"""Create a dated, hash-verified local research handoff snapshot, excluding GB weights."""
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import hashlib,json,shutil

R=Path(__file__).resolve().parents[1]
W=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    instant=datetime.now(timezone.utc);stamp=instant.astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d_%H%M%S')
    out=W/'outputs'/('S15BC_S16_S17_研究进展与证据_'+stamp);out.mkdir(parents=True,exist_ok=False)
    paths=set();omitted=[];external_paths={}
    for name in ['AGENTS.md','RESEARCH_PRINCIPLES.md','RESEARCH_QUALITY_TARGETS.md','RESEARCH_QUALITY_TARGETS_ERRATA.md','RESEARCH_MEMORY.md','RESEARCH_LOG.md','research_events.jsonl','workflow_checks.jsonl']:
        paths.add(R/name)
    for directory in [R/'docs',R/'scripts']:
        paths.update(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for directory in sorted((R/'results').iterdir()):
        if directory.is_dir() and directory.name.startswith(('S15B','S15C','S16','S17')):
            for p in directory.rglob('*'):
                if p.is_file() and '__pycache__' not in p.parts:paths.add(p)
    # Preserve scientific figures, contracts, source copies, errors and review records.
    for directory in sorted((R/'work').iterdir()):
        if directory.is_dir() and directory.name.startswith(('S15B','S15C','S16','S17')):
            for p in directory.rglob('*'):
                if not p.is_file() or '__pycache__' in p.parts or '.git' in p.parts:continue
                if 'site-packages' in p.parts:continue
                if p.suffix in {'.bin','.pth','.whl','.partial'} or p.stat().st_size>120*1024*1024:
                    omitted.append(dict(path=str(p),bytes=p.stat().st_size,reason='Large acquisition/dependency payload stays in canonical project'));continue
                paths.add(p)
    # Actual photographs, with original paths, not generated model RGB heads.
    original=json.loads((R/'docs/S15A_HISTORY_EXECUTION_MANIFEST.json').read_text())
    for item in original['history_images']:
        p=Path(item['path']);assert sha(p)==item['sha256'];paths.add(p)
    gallery=R/'work/S15A_reporting/s15a_all_20_real_history_photos.png'
    if gallery.exists():paths.add(gallery)
    for directory in [R/'data/bonn_s15c_depth',R/'vendor']:
        if directory.exists():paths.update(p for p in directory.rglob('*') if p.is_file() and p.stat().st_size<20*1024*1024 and '.git' not in p.parts)
    # Include the exact standalone CUT3R source bytes executed by S17B.
    b_manifest=json.loads((R/'docs/S17B_EXECUTION_MANIFEST.json').read_text())
    standalone=Path(b_manifest['repo'])
    for name,digest in b_manifest['identities'].items():
        source=Path(name)
        if source.is_relative_to(standalone):
            assert sha(source)==digest
            paths.add(source);external_paths[source]=Path('referenced_sources/cut3r_standalone')/source.relative_to(standalone)
    rows=[]
    for p in sorted(paths):
        rel=external_paths[p] if p in external_paths else p.relative_to(R);dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        before=sha(p);shutil.copy2(p,dest);assert sha(dest)==before==sha(p)
        rows.append(dict(path=str(rel),bytes=dest.stat().st_size,sha256=before,canonical_path=str(p)))
    weights=[]
    for name in ['cut3r_224_linear_4.pth','cut3r_512_dpt_4_64.pth']:
        p=R/'data/cut3r'/name
        weights.append(dict(path=str(p),present=p.exists(),bytes=p.stat().st_size if p.exists() else None,copy_included=False))
    (out/'权重和省略载荷索引.json').write_text(json.dumps(dict(weights=weights,omitted=omitted),ensure_ascii=False,indent=2)+'\n')
    (out/'先读我.md').write_text(f'''# 当前研究进展与接手入口

本快照创建于北京时间 {instant.astimezone(ZoneInfo('Asia/Shanghai')).isoformat()}。当前状态请先读[现在在做什么](docs/START_HERE_CURRENT.md)、[研究记忆](RESEARCH_MEMORY.md)及[研究日志](RESEARCH_LOG.md)。这是本机可复查的阶段快照；创建之后的新记录以[主项目](<{R}/RESEARCH_MEMORY.md>)为准。

## 给新手和老师看的材料

- [20张真实照片索引](work/S15A_reporting/s15a_all_20_real_history_photos.png)：原实拍也按原路径复制在data中。
- [S15B七种规则的完整真实评分](docs/S15B_RESULTS.md)。
- [S15C传感器缺失与全部固定帧评分](docs/S15C_RESULTS.md)。
- [S16已保存数据的来源相互作用诊断](docs/S16_RESULTS.md)。
- [两张真实照片与512模型预测](work/S17B_reporting/s17b_two_photos_dpt_depth.png)。
- [S17C真实建图、400步优化及完整验证](docs/S17C_RESULTS.md)。
- [单文件点云查看器](work/S17C_viewer/viewer.html)：本机HTTP预览交互已实际检查，直接file打开未通过内置浏览器策略。
- [下一阶段地图连接草案](docs/S18_MEMORY_BRIDGE_PREPARATION.md)：准备状态，不是已运行新方法。
- [原视频基线的资源与接口缺项](docs/S17_FULL_VIDEO_BASELINE_FEASIBILITY.md)及[CPU实际预检增补](docs/S17_FULL_VIDEO_BASELINE_FEASIBILITY_ADDENDUM.md)。
- [论文逻辑与待补创新证据](docs/PAPER_LOGIC_CURRENT.md)：未成立的主张如实标出。

## 下一位AI怎样接手

先读[完整交接路线](docs/RESEARCH_HANDOFF_CURRENT.md)，再读取主项目最新AGENTS、原则、记忆和主账，确认是否仍有下载或模型进程。不要根据本快照重复成功运行。执行manifest使用原机绝对路径，旧阶段输入与约3GB权重留在主项目及既有日期快照，位置列在[载荷索引](权重和省略载荷索引.json)。这里不宣称已在新机器独立重跑。S17B实际执行的99份standalone源码另存referenced_sources/cut3r_standalone；其原路径与SHA在清单和原manifest中对应。

本包包含S15B/C、S16及当前已落盘S17结果、源码、前审、失败、科学图和主账快照；大权重、下载分块、虚拟环境没有复制。所有复制文件逐一核SHA，清单见MANIFEST.json。人工软件测试、实拍模型推理、保存数据复算和完整视频是不同证据类型；完整VMem生成与新方法创新尚不能用组件成功代替。
''')
    for name in ['先读我.md','权重和省略载荷索引.json']:
        p=out/name;rows.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p),canonical_path=None))
    manifest=dict(schema='research-progress-snapshot-v1',created_utc=instant.isoformat(),canonical_root=str(R),snapshot_path=str(out),files=rows,files_count=len(rows),payload_bytes=sum(x['bytes'] for x in rows),copy_hash_verification=True,weights_copied=False,new_machine_rerun=False)
    (out/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    receipt=dict(completed_utc=datetime.now(timezone.utc).isoformat(),status='PASS',path=str(out),files=len(rows),bytes=manifest['payload_bytes'],manifest_sha256=sha(out/'MANIFEST.json'))
    dest=R/'docs'/f'S17_DELIVERY_RECEIPT_{stamp}.json';dest.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
