# S40：真实两批生成入口准备

更新UTC：2026-09-07T04:34:34.382312+00:00。本阶段完成源码与不同作者前审，**没有运行模型或生成视频**。原VMem未完整下载，CLIP下载会话36631仍运行；真实S39加载回执尚无。

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

## 04:43前后实际资源推进

资源最新更新UTC：2026-09-07T04:43:28.864722+00:00。**原CLIP已完整下载，3,944,517,836字节及完整SHA于04:40:51通过。旧会话36631已退出0。原VMem低并发attempt3已单独启动，会话71130/PID84800，04:42:22仍活跃；临时文件当时0字节且Xet有1条TLS EOF警告，未判成功或失败。** 接续同一71130，不重启；外控总时限预计05:11:16UTC，精确终态以新receipt为准。它成功后才能冻结全部文件并实际加载。


[CLIP完整校验回执](../work/S39_auth_recovery/companion_download_receipt.json)；[原VMem当前attempt3](../work/S39_auth_recovery/vmem_low_concurrency_attempt3/receipt.json)。仅完成资源与源码准备，无新模型/生成。
