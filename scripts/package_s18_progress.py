#!/usr/bin/env python3
"""Create a hash-verified S18 incremental handoff; keep earlier full snapshots."""
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import argparse, hashlib, json, shutil

ROOT=Path(__file__).resolve().parents[1]
WS=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert not out.exists();out.mkdir(parents=True)
    start=datetime.now(timezone.utc).isoformat()
    sources=set()
    for folder in ('docs','scripts','src','work','results'):
        for x in (ROOT/folder).rglob('*'):
            if x.is_file() and not any(v in ('__pycache__','.DS_Store') for v in x.parts) and any(any(stage in part.lower() for stage in ('s18','s19')) for part in x.relative_to(ROOT).parts):sources.add(x)
    for rel in ('AGENTS.md','RESEARCH_PRINCIPLES.md','RESEARCH_QUALITY_TARGETS.md','RESEARCH_QUALITY_TARGETS_ERRATA.md','RESEARCH_MEMORY.md','RESEARCH_LOG.md','research_events.jsonl','workflow_checks.jsonl','docs/RESEARCH_HANDOFF_CURRENT.md','docs/START_HERE_CURRENT.md','docs/PROJECT_DELIVERY_TRACKER.md','docs/PAPER_LOGIC_CURRENT.md','src/vmem_memory_kernel.py','src/vmem_retrieval_kernel.py','scripts/research_log.py','scripts/run_s14d_controlled.py','docs/S17C_EXECUTION_MANIFEST.json','docs/S17C_OUTPUT_SEAL.json','results/S17C_embedded_independent/verification.json','results/S17C_embedded_geometry/run_metadata.json','results/S17C_embedded_geometry/final_result.npz'):
        sources.add(ROOT/rel)
    rows=[]
    for source in sorted(sources):
        assert source.exists() and source.is_file()
        rel=source.relative_to(ROOT);target=out/rel;target.parent.mkdir(parents=True,exist_ok=True)
        digest=sha(source);shutil.copy2(source,target);assert sha(target)==digest
        rows.append(dict(path=str(rel),sha256=digest,bytes=target.stat().st_size,source=str(source)))
    original=Path(json.loads((ROOT/'docs/S18_EXECUTION_MANIFEST.json').read_text())['source_root'])
    for rel in ['modeling/pipeline.py','utils/util.py','configs/inference/inference.yaml','navigation.py','app.py','LICENSE']:
        source=original/rel;target=out/'referenced_sources/vmem'/rel;target.parent.mkdir(parents=True,exist_ok=True)
        digest=sha(source);shutil.copy2(source,target);assert sha(target)==digest
        rows.append(dict(path=str(target.relative_to(out)),sha256=digest,bytes=target.stat().st_size,source=str(source)))
    text='''# S18 地图与照片来源连接：接手入口

这是S18新增成果、S19问题筛选及复现证据的逐文件核验快照。先读 `docs/S18_RESULTS.md` 与 `docs/S19_FEEDBACK_PATH_AUDIT.md`，再读主交接和当前记忆；正式运行规则见S18_EXECUTION_PROTOCOL，原始输出/独立验证/失败记录完整保留。新记忆优先于旧的带日期快照。

本轮复用此前两张真实Bonn照片的模型几何输出，没有新跑CUT3R或生成视频；S18不能被称为新算法获胜或完整科研项目完成。每个阶段的实际结果状态见回执。

本增量包包含S17C最终几何输入及原控制件；原20实拍、前序完整源码/实验和点云查看器在同级 `S15BC_S16_S17_研究进展与证据_2026-09-06_194851` 完整快照中。原GB权重/运行环境仍在主项目，不能宣称新机器已复跑。清单内保存原绝对路径是来源记录，迁移机器需明确重定位后另立执行清单。

主项目：/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling

报告图：work/S18_reporting/s18_memory_visibility.png，PDF/SVG在同目录。结果图来自实际封存栅格，原照片请读上轮20照片目录；不要把深度彩图当实拍。
'''
    (out/'从这里开始.md').write_text(text)
    q=out/'从这里开始.md';rows.append(dict(path=q.name,sha256=sha(q),bytes=q.stat().st_size,source='generated package entry'))
    manifest=dict(schema='s18-incremental-handoff-v1',started_utc=start,completed_utc=datetime.now(timezone.utc).isoformat(),root=str(ROOT),files=rows,file_count=len(rows),bytes=sum(r['bytes'] for r in rows),verification='Each copied file SHA equals source; this is packaging verification, not a new scientific/model execution.')
    (out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    receipt=dict(status='PASS',output=str(out),manifest_sha256=sha(out/'MANIFEST.json'),file_count=len(rows),bytes=manifest['bytes'],completed_utc=manifest['completed_utc'])
    print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
