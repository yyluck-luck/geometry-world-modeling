#!/usr/bin/env python3
"""Create a verified local S15A evidence snapshot; never bundle the 3GB weight."""
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
WS=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    now=datetime.now(timezone.utc);stamp=now.astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d_%H%M%S')
    out=WS/'outputs'/('S15A_Bonn真实照片与推理_'+stamp);assert not out.exists();out.mkdir(parents=True)
    m=json.loads((ROOT/'docs/S15A_HISTORY_EXECUTION_MANIFEST.json').read_text());repo=Path(m['repo'])
    verification=json.loads((ROOT/'results/S15A_bonn_history_independent/verification.json').read_text());assert verification['status']=='PASS'
    sources={Path(p) for p in m['identities'] if p!=m['checkpoint']}
    sources|={ROOT/n for n in ['AGENTS.md','RESEARCH_PRINCIPLES.md','RESEARCH_MEMORY.md','RESEARCH_LOG.md','research_events.jsonl','workflow_checks.jsonl','docs/RESEARCH_HANDOFF_CURRENT.md','docs/PROJECT_DELIVERY_TRACKER.md','docs/EXPERIMENT_REALITY_EXPLAINED.md','scripts/package_s15a_delivery.py']}
    sources|=set((ROOT/'docs').glob('S15*'))
    sources|=set((ROOT/'scripts').glob('*s15*.py'))
    sources|=set((ROOT/'results/S15A_bonn_history').iterdir())
    sources|=set((ROOT/'results/S15A_bonn_history_independent').iterdir())
    sources|=set((ROOT/'work/S14_bonn_metadata_access').glob('*'))
    for folder in (ROOT/'work').glob('S15*'):
        if folder.is_dir():
            for p in folder.rglob('*'):
                if p.is_file() and not {'cases','fixtures','__pycache__'}&set(p.parts) and p.suffix not in {'.npz','.npy','.pyc'}:sources.add(p)
    for folder in (ROOT/'data').glob('bonn_s15a*'):
        for p in folder.glob('*'):
            if p.is_file():sources.add(p)
    files=[]
    def copy(source,destination):
        assert source.is_file();destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists():assert sha(source)==sha(destination);return
        digest=sha(source);shutil.copy2(source,destination);assert sha(destination)==digest
        files.append(dict(path=str(destination.relative_to(out)),source=str(source),sha256=digest,bytes=destination.stat().st_size))
    for p in sorted(sources):
        if not p.is_file():continue
        if p.is_relative_to(ROOT):destination=out/'evidence/project'/p.relative_to(ROOT)
        elif p.is_relative_to(repo):destination=out/'evidence/upstream'/p.relative_to(repo)
        else:raise ValueError('Unexpected snapshot input '+str(p))
        copy(p,destination)
    for item in m['history_images']:copy(Path(item['path']),out/'真实照片'/f"{item['index']:02d}_{Path(item['path']).name}")
    for label,path in [('idea-evaluator','/Users/rocket/.codex/skills/idea-evaluator/SKILL.md'),('vibe-research-workflow','/Users/rocket/.codex/skills/vibe-research-workflow/SKILL.md'),('figure-designer','/Users/rocket/.codex/skills/figure-designer/SKILL.md'),('claude-scientific-critical-thinking','/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md')]:copy(Path(path),out/'evidence/skills'/label/'SKILL.md')
    copy(ROOT/'work/S15A_reporting/s15a_all_20_real_history_photos.png',out/'全部20张实拍.png')
    weight=dict(path=m['checkpoint'],sha256=m['identities'][m['checkpoint']],bytes=Path(m['checkpoint']).stat().st_size,reason='Existing local large weight; omitted from snapshot, not re-downloaded')
    (out/'external_large_inputs.json').write_text(json.dumps(weight,ensure_ascii=False,indent=2)+'\n')
    (out/'先读我.md').write_text('''# S15A：Bonn新来源真实照片与模型推理

本机已真实处理20张原生实拍，保存预测与记忆状态，并通过不同作者数值完整性复核。**尚未测几何准确率、验证新算法或生成视频。**

- [这一轮的中文结果](evidence/project/docs/S15A_RESULTS.md)
- [全部20张实拍索引图](全部20张实拍.png)，逐张原图在 `真实照片/`。
- [最新研究记忆](evidence/project/RESEARCH_MEMORY.md)与[完整交接路线](evidence/project/docs/RESEARCH_HANDOFF_CURRENT.md)。
- [创新近邻与下一机制](evidence/project/docs/S15_MECHANISM_AND_NEAREST_WORK.md)。
- [长期科研原则](evidence/project/RESEARCH_PRINCIPLES.md)与[实际时间主账](evidence/project/RESEARCH_LOG.md)。

`evidence/project/results/`含实际127个数组的三个NPZ与独立核验；`evidence/project/work/`保留原文检索、人工准备、缺失索引、网络失败和真实运行回执。人工数据/准备记录不能算真实模型效果。脚本与99份官方源码一并保留。

约3GB已有模型权重只列在 `external_large_inputs.json`，未复制。原始执行manifest绑定原机绝对路径；这是经过逐文件SHA核对的本地交接包，不是新电脑已经复跑的证明，也未上传公网。数据完整再分发许可证未被推断。

快照反映创建时刻；之后继续工作，以原项目 `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling` 的当前记忆与追加主账为准。本轮20历史已经暴露，不能在未来机制试验中重新称为未见见证；4预留目标RGB及所有depth/trajectory仍未获取。
''')
    for p in [out/'external_large_inputs.json',out/'先读我.md']:files.append(dict(path=str(p.relative_to(out)),source='generated local snapshot index',sha256=sha(p),bytes=p.stat().st_size))
    manifest=dict(schema='s15a-local-delivery-v1',created_utc=now.isoformat(),file_count=len(files),payload_bytes=sum(x['bytes'] for x in files),files=files,large_weight_included=False,external_replication=False)
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    assert all(sha(out/x['path'])==x['sha256'] for x in files)
    receipt=dict(status='PASS',completed_utc=datetime.now(timezone.utc).isoformat(),output=str(out),file_count=len(files),payload_bytes=manifest['payload_bytes'],manifest_sha256=sha(out/'manifest.json'),all_copy_hashes_pass=True)
    p=ROOT/'docs/S15A_DELIVERY_RECEIPT.json';assert not p.exists();p.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
