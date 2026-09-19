#!/usr/bin/env python3
"""Create an immutable dated S14E evidence snapshot without copying large weights."""
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import hashlib
import json
import shutil

R=Path(__file__).resolve().parents[1]
WS=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())


def main():
    audit=read(R/'work/S14E_completion_review/receipt.json');assert audit['status']=='PASS'
    now=datetime.now(timezone.utc);local=now.astimezone(ZoneInfo('Asia/Shanghai'))
    dest=WS/'outputs'/('S14E真实深度实验_'+local.strftime('%Y-%m-%d_%H%M%S'));dest.mkdir(parents=True,exist_ok=False)
    sources=set()
    for parent in [R/'docs',R/'scripts']:
        sources.update(p for p in parent.iterdir() if p.is_file() and 's14e' in p.name.lower())
    for parent in [R/'work',R/'results']:
        for top in parent.glob('S14E*'):
            sources.update(p for p in ([top] if top.is_file() else top.rglob('*')) if p.is_file() and '__pycache__' not in p.parts)
    basics=['AGENTS.md','RESEARCH_PRINCIPLES.md','RESEARCH_MEMORY.md','RESEARCH_LOG.md','research_events.jsonl','workflow_checks.jsonl',
            'docs/RESEARCH_HANDOFF_CURRENT.md','docs/RESEARCH_WORKFLOW_CHECKLIST.md','docs/PROJECT_DELIVERY_TRACKER.md','docs/EXPERIMENT_REALITY_EXPLAINED.md',
            'requirements-cut3r.txt','requirements-rgbd.txt','requirements-cpu.txt','requirements-retrieval.txt','vendor/provenance.json']
    sources.update(R/p for p in basics)
    for name in ['PREPARE','MODEL','SCORE']:
        m=read(R/f'docs/S14E_{name}_EXECUTION_MANIFEST.json')
        for p,d in m['identities'].items():
            assert sha(p)==d,'Frozen source or input changed: '+p
            sources.add(Path(p))
    prior=read(R/'docs/S14D_RAY_ONLY_EXECUTION_MANIFEST_V2.json');repo=Path(prior['repo'])
    sources.update(Path(x['path']) for x in prior['history_images'])
    sources.update(R/'results/S14D_ray_only_probe'/p for p in ['run_metadata.json','state_before.npz','probe_inputs.npz','query_call_1.npz'])
    rgb=read(R/'work/S14E_reporting_rgb_manifest.json');sources.update(Path(x['rgb_path']) for x in rgb['targets'])
    skillroot=Path('/Users/rocket/.codex/skills')
    for skill in ['idea-evaluator','vibe-research-workflow','figure-designer']:
        sources.update((skillroot/skill).rglob('*.md'))
    claude=Path('/Users/rocket/.claude/skills/sci-scientific-critical-thinking')
    sources.update(claude.rglob('*.md'))
    copied=[];external=[]
    for source in sorted(sources):
        size=source.stat().st_size
        if size>256*1024**2:
            external.append(dict(path=str(source),bytes=size,sha256=sha(source),reason='Existing large checkpoint; pointer only'))
            continue
        if source.is_relative_to(R): rel=Path('project')/source.relative_to(R)
        elif source.is_relative_to(repo): rel=Path('upstream/CUT3R')/source.relative_to(repo)
        elif source.is_relative_to(skillroot): rel=Path('skills/Supervisor')/source.relative_to(skillroot)
        elif source.is_relative_to(claude): rel=Path('skills/Claude/scientific-critical-thinking')/source.relative_to(claude)
        else: raise ValueError('Unmapped source: '+str(source))
        target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        digest=sha(source);assert sha(target)==digest
        copied.append(dict(path=str(rel),source=str(source),bytes=size,sha256=digest))
    for label,items in [('真实目标照片_4张',rgb['targets']),('历史输入照片_20张',prior['history_images'])]:
        for i,item in enumerate(items):
            source=Path(item.get('rgb_path',item.get('path')))
            target=dest/label/f'{i:02d}_{source.name}';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    shutil.copy2(R/'work/S14E_reporting/s14e_all_four_targets.png',dest/'真实照片与深度对照.png')
    shutil.copy2(R/'RESEARCH_PRINCIPLES.md',dest/'科研长期原则.md')
    (dest/'external_large_inputs.json').write_text(json.dumps(external,ensure_ascii=False,indent=2)+'\n')
    (dest/'先读我.md').write_text('''# 本轮已完成真实深度实验

先看 `真实照片与深度对照.png`、`科研长期原则.md` 和 `project/docs/S14E_RESULTS.md`。

四个已见目标位置：公开CUT3R模型记忆查询平均δ1为93.0974%，历史点云重投影85.8008%，相差7.2966个百分点；共同有效域MAE也更小。这是组件诊断，不是自创新方法、未见场景或视频结果。

`真实目标照片_4张`是评分后仅作参照的实拍照片，模型未读取；`历史输入照片_20张`是产生已有模型状态的历史实拍。图中传感器测量与模型输出分别标注。

长期原则在项目RESEARCH_PRINCIPLES.md持续维护。恢复工作先看project/AGENTS.md、RESEARCH_MEMORY.md、RESEARCH_LOG.md和docs/RESEARCH_HANDOFF_CURRENT.md第23节。results/S14E*是真实运行产物；work中的artificial/fake_root等是明确标注的人工代码检查，不能当真实效果。

本包保存源码、技能说明、依赖清单、输入/输出、完整表格、纠错、核验与交接。约3GB已有权重只列路径、大小和SHA于external_large_inputs.json，未重复复制。冻结manifest绑定原机绝对路径，是可审查证据；此包没有在新电脑重新运行，不宣称开箱即完成外部复现。

后续先明确“模型补全何时可靠”的新信息、机制、反证和最近工作差别，再推进Bonn候选的真实新场景；不重跑本轮成功实验、不以旧数据调参包装创新。完整项目未完成项见project/docs/PROJECT_DELIVERY_TRACKER.md。
''')
    files=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(dest.rglob('*')) if p.is_file()]
    manifest=dict(schema='s14e-evidence-delivery-v1',created_utc=now.isoformat(),snapshot_scope='Dated evidence snapshot; canonical ledger continues in source project',files=files,copied_source_bindings=copied,external_large_inputs=external)
    (dest/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    assert all(sha(dest/x['path'])==x['sha256'] for x in files)
    old=[]
    for path,expected in [(WS/'outputs/完整研究路线与交接/研究路线与记录_轻量交接.zip','a7bb5e0836ae6fc997a51f321102be3064180de67d6167dbc2aa9b79d51bd634'),(WS/'outputs/四图选择上限诊断/S13_四图上限证据.zip','31c3e0654ff80d010320201d9f44121aa667c302d727d93bee866a79f558b2a6')]:
        entry=dict(path=str(path),exists=path.exists())
        if path.exists():entry.update(sha256=sha(path),matches_previous=sha(path)==expected)
        old.append(entry)
    receipt=dict(schema='s14e-delivery-receipt-v1',status='PASS',created_utc=now.isoformat(),directory=str(dest),payload_count=len(files),payload_bytes=sum(x['bytes'] for x in files),manifest_sha256=sha(dest/'manifest.json'),all_copied_bytes_verified=True,old_archives=old)
    output=R/'docs/S14E_DELIVERY_RECEIPT.json';assert not output.exists();output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':main()
