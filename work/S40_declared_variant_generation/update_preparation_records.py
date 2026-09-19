from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,re,sys
R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling');W=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip');H=R/'work/S40_declared_variant_generation';now=datetime.now(timezone.utc);stamp=now.isoformat()
previous=json.loads((R/'work/S39_auth_recovery/progress_handoff.json').read_text());paths=[Path(x['path']) for x in previous['current_files']]
b=H/'current_before_update'/now.strftime('%Y%m%dT%H%M%SZ');b.mkdir(parents=True,exist_ok=False)
for i,p in enumerate(paths):(b/f'{i:02d}_{p.name}').write_bytes(p.read_bytes())
review=json.loads((H/'independent_source_review.json').read_text());assert review['passed'] and review['core_sha256'] is None and review['runtime_authorized'] is False
report=f'''# S40：真实两批生成入口准备

更新UTC：{stamp}。本阶段完成源码与不同作者前审，**没有运行模型或生成视频**。原VMem未完整下载，CLIP下载会话36631仍运行；真实S39加载回执尚无。

## 为什么做这一步

proposal要研究AI能否长期记住同一空间。必须先让基线实际连续生成，且下一批真能消费上一批产生的记忆，再谈它在哪些情形失效。这次准备原changi图像→左转5度→右转5度，保留原576分辨率、8样本槽、4上下文/4新帧、50采样步、默认NMS、原400次GA。实际历史应1→5→9，不用人工缓存或小模型代替。

## 已完成与可查证据

- S35原循环、trace、archive与数值设置不改；新入口只做可逆AST的门/工厂路由和身份标签派生。
- 新工厂沿用S39 v2的完整state_dict载入记录检查，不能把内部吞掉的加载异常当成功。
- 运行前必须绑定S39四份实际加载回执、另一作者实际加载审查，以及S40正式core和两份真实批准。当前candidate是DRAFT，所有真实加载位置空；源码审查不代替运行批准。
- 不同作者源审04:31:42.342240UTC通过，核真实字段接口与218项源域；0模型、GT、照片、权重字节、新旧人工测试。原S35/S39源文件保持。

[运行协议](../work/S40_declared_variant_generation/PROTOCOL_DRAFT.md)；[入口](../work/S40_declared_variant_generation/launch_generation.py)；[资源与实际加载门](../work/S40_declared_variant_generation/generation_gate.py)；[工厂路由](../work/S40_declared_variant_generation/runtime_adapter.py)；[作者回执](../work/S40_declared_variant_generation/preparation_receipt.json)；[不同作者源码审查](../work/S40_declared_variant_generation/independent_source_review.json)。

## 结果怎样才算实际发生

不是有9张图或退出0就验收。要保存两批原输出张量、被选context缓存、原noise/RNG、几何与地图提交，然后核第二批所用完整缓存对应第一批提交的真实内容。未消费生成历史也保留失败，不改选图规则来过门。视频质量、摄像机运动遵循和长程场景一致性仍需其后的独立指标与跨场景比较。

版本名称固定为“VMem + stabilityai/sd-vae-ft-mse”。原SD2.1 VAE历史来源UNKNOWN，不是精确原版；后续所有方法对照必须共用同一组件版本。两批8新帧只是初次真实闭环，不是长期一致性实验，也不是新方法。

## 接续资源状态

S39正式认证和ft-mse两文件完整校验已完成。04:33:01UTC CLIP临时文件大小2883860369B，未完成。原VMem此前Xet/HTTP失败终态都保留；低并发attempt3脚本和进程组清理修订已经不同作者源码审查通过，仍未启动。先等CLIP终态，再单独执行一次，外控1800秒，保持原repo/revision/SHA。

本轮流程检查04:26:13.766313UTC完成，距前次26.614071分钟；下次目标04:53:13UTC、截止04:56:13UTC。[主记忆](../RESEARCH_MEMORY.md)与[追加时间账](../RESEARCH_LOG.md)记录后续真实变化。
'''
(R/'docs/S40_GENERATION_PREPARATION.md').write_text(report)
summary=f'''更新UTC：{stamp}。**真实两批视频入口已完成源码准备和不同作者审查，尚未执行。** 保留原576分辨率、50采样步、400次几何优化和连续历史1→5→9，实际运行后还要核第二批确实消费第一批生成缓存。

正式HF认证已成功，ft-mse配置/权重已完整校验。CLIP仍为下载会话36631；04:33:01临时文件大小约2.88GB，未完成。原VMem两次传输失败均已结束，新的低并发attempt3先等待CLIP终态，不启动重复并行下载。真实加载、视频生成与质量比较仍未发生。

版本明确使用官方ft-mse VAE，原SD2.1来源仍UNKNOWN，不能称精确原版复现。继续按Supervisor强基线→自然失败→原因→方法；S38的CLIP平均问题仍待验证，新方法及PhD/CCF A质量目标未完成。

[最新准备报告](<{R}/docs/S40_GENERATION_PREPARATION.md>)；[认证与下载记录](<{R}/docs/S39_AUTH_AND_COMPONENT_LOADING.md>)；[完整时间账](<{R}/RESEARCH_LOG.md>)；[主记忆](<{R}/RESEARCH_MEMORY.md>)。以下旧状态按各自时间理解，不覆盖最新更新。
'''
for p in paths:
 s=p.read_text()
 if '<!-- CURRENT_STATUS_BEGIN -->' in s:s=re.sub(r'<!-- CURRENT_STATUS_BEGIN -->.*?<!-- CURRENT_STATUS_END -->','<!-- CURRENT_STATUS_BEGIN -->\n'+summary+'<!-- CURRENT_STATUS_END -->',s,count=1,flags=re.S)
 elif p.name=='RESEARCH_MEMORY.md':
  s=re.sub(r'更新UTC：[^\n]+',f'更新UTC：{stamp}；S40真实两批入口源码准备与独立源审完成，0真实加载/生成；CLIP同一下载在运行，原VMem单独低并发尝试待CLIP终态。',s,count=1)
  s=s.replace('## S39当前：认证已恢复，资源与加载准备','## S40当前：两批原流程入口准备完成\n\n'+summary+'\n## S39历史与仍有效的资源记录：认证已恢复，资源与加载准备',1)
 elif p.name in ('START_HERE_CURRENT.md','最新科研进展.md'):s='# 最新科研进展\n\n'+summary
 elif p.name=='MODEL_ACCESS_CURRENT.md':s='# 当前模型访问状态\n\n'+summary+'\n精确下载身份/认证与传输终态见S39；当前实际句柄优先于旧快照。\n'
 p.write_text(s)
receipt={'prepared_utc':stamp,'status':'GENERATION_SOURCE_PREPARED_AND_INDEPENDENTLY_REVIEWED_NOT_EXECUTED','backup_directory':str(b),'new_model_runs':0,'source_review_sha256':hashlib.sha256((H/'independent_source_review.json').read_bytes()).hexdigest(),'report_sha256':hashlib.sha256((R/'docs/S40_GENERATION_PREPARATION.md').read_bytes()).hexdigest(),'current_files':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
(H/'current_preparation_records.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,str(R/'scripts'));from research_log import append_event
append_event('S40原两批具名组件入口源码准备与独立前审完成','新入口保留原S35全循环/576/50steps/400GA/同worker RNG及历史消费记录，以可逆AST路由与标签派生；实际S39加载4回执和精确core审核门就绪但当前全DRAFT。不同作者04:31:42源审PASS，0模型/权重/照片/GT/新旧人工测试。10当前入口已备份并同步。CLIP仍同会话下载，原VMemattempt3尚待单独运行；不是完整生成或创新成立。',evidence=['docs/S40_GENERATION_PREPARATION.md','work/S40_declared_variant_generation/current_preparation_records.json','work/S40_declared_variant_generation/independent_source_review.json'],next_step='接续CLIP至完整验收，再独立原VMemattempt3；资源到位先实际S39加载与审核。',occurred_at=stamp)
print(json.dumps({'recorded_utc':stamp,'files':len(paths),'source_review':'PASS_NOT_RUNTIME_APPROVAL'}))
