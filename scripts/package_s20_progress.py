#!/usr/bin/env python3
"""Create an immutable S20 incremental handoff, hashing every copied file."""
from pathlib import Path
import datetime,hashlib,json,shutil
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
WS=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
now=datetime.datetime.now(datetime.timezone.utc)
OUT=WS/'outputs'/('S20_完整生成环境与记录工具_'+now.astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d_%H%M%S'))
OUT.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selected=set(ROOT.glob('docs/S20*'))
for name in ['AGENTS.md','RESEARCH_PRINCIPLES.md','RESEARCH_MEMORY.md','RESEARCH_LOG.md','research_events.jsonl','workflow_checks.jsonl','docs/RESEARCH_HANDOFF_CURRENT.md','docs/START_HERE_CURRENT.md','docs/PROJECT_DELIVERY_TRACKER.md','docs/PAPER_LOGIC_CURRENT.md','docs/RESEARCH_WORKFLOW_CHECKLIST.md','docs/S17_BASELINE_ENTRY_CORRECTION_S19.md','docs/S19_FEEDBACK_PATH_AUDIT.md','src/s20_generation_trace.py','scripts/package_s20_progress.py','scripts/research_log.py']:
 selected.add(ROOT/name)
for directory in ROOT.glob('work/S20*'):
 for p in directory.rglob('*'):
  rel=p.relative_to(directory)
  if p.is_file() and not any(x in {'site-packages','pip-cache','matplotlib-config','huggingface-cache','__pycache__'} for x in rel.parts) and p.suffix!='.pyc':selected.add(p)
rows=[]
for p in sorted(selected):
 assert p.is_file(),str(p)
 rel=p.relative_to(ROOT);q=OUT/rel;q.parent.mkdir(parents=True,exist_ok=True);digest=sha(p);shutil.copy2(p,q);assert sha(q)==digest;rows.append({'path':str(rel),'bytes':q.stat().st_size,'sha256':digest,'source':str(p)})
intro='''# 从这里开始：S20增量交接

这一轮完成完整VMem程序的隔离依赖安装与实际导入，新增生成来源观察工具，并真实验证了视频文件保存。**没有加载主生成器或生成真实场景视频。** 红绿蓝黄色块MP4只验证软件。

1. [本轮完整进展](docs/S20_PROGRESS.md)：实际完成、错误、限制与下一步。
2. [环境安装与导入](docs/S20_ENVIRONMENT_RESULTS.md)、[原依赖访问](docs/S20_DEPENDENCY_ACCESS.md)。
3. [生成记录工具合同](docs/S20_GENERATION_TRACE_CONTRACT.md)、[原两批入口草案](docs/S20_MINIMAL_VIDEO_PROTOCOL_DRAFT.md)。
4. [人工视频编解码](docs/S20_CODEC_SMOKE.md)。
5. [当前交接](docs/RESEARCH_HANDOFF_CURRENT.md)、[原则](RESEARCH_PRINCIPLES.md)、[最新记忆](RESEARCH_MEMORY.md)、[时间主账](RESEARCH_LOG.md)。

这是有日期的增量快照：包含本轮代码、失败/成功回执、源码、11份哈希wheel及人工测试载荷。原Python环境、S17C几何overlay、GB模型权重、既有实拍和旧科学结果仍在主项目/上一完整交接包，不复制、不改成合成数据；此包并非另一台电脑上一键复现完整项目。所有本轮复制文件逐一核SHA，MANIFEST.json不包含其自身。

接手先读主项目最新AGENTS、原则、记忆尾部及日志，随后读本包。成功的S17/S18模型/地图和S20软件组件不无故重跑。先补原主权重和原VAE合法访问，以及公开CLIP原权重；再连接观察器到真实原loop、冻结正式输入/预算、执行原T8/50步两批。草案不是已冻结真实运行合同。没有新方法效果或投稿保证，不能继续复活S19已否决的设想。
'''
(OUT/'从这里开始.md').write_text(intro)
rows.append({'path':'从这里开始.md','bytes':(OUT/'从这里开始.md').stat().st_size,'sha256':sha(OUT/'从这里开始.md'),'source':'generated package entry'})
manifest={'schema':'s20-incremental-delivery-v1','created_utc':now.isoformat(),'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root_project':str(ROOT),'file_count_excluding_manifest':len(rows),'bytes_excluding_manifest':sum(x['bytes'] for x in rows),'files':rows,'scope':'Software preparation evidence, no VMem generated scene video; requires canonical old environment and earlier research assets.'}
(OUT/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
receipt={'path':str(OUT),'completed_utc':manifest['completed_utc'],'file_count_excluding_manifest':len(rows),'bytes_excluding_manifest':manifest['bytes_excluding_manifest'],'manifest_sha256':sha(OUT/'MANIFEST.json')}
(ROOT/'docs'/('S20_DELIVERY_RECEIPT_'+now.astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d_%H%M%S')+'.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
(ROOT/'work/S20_delivery').mkdir(exist_ok=True)
(ROOT/'work/S20_delivery/location.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipt,ensure_ascii=False))
