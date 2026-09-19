# S61新单位适配器的已有数据验收

固定于UTC 2026-09-08T18:18:37.551027+00:00，已看过S60结果后的工程验收。输入仅C2 V9 archive seq58中的515个surfel位置/半径/法线/来源、实际render pose/focal/kwargs；不解码其他seq58树或任何RGB。参考为S60已冻结的median_depth_unit数值图和来源结果。

接收作者最终只读source和有限检查后，root核SHA并取得不同作者源码审查，再执行。原pipeline SHA680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255与archive事件SHA b51b39e1772a7a2cbc0221bc0846d95cd3b7c8b21f8978ddbbd0f1d2443f6ef7保持；编译原renderer/分配/聚合三函数AST，不导入完整pipeline或加载权重。

同一保存输入只取长度倍率1、1e-6、1e6三个单位条件，所有点/相机平移/半径同乘，R/K/法线/来源不变。每条件恰好一次新adapter调用绑定原renderer；不得静默重试、改倍数或阈值。报告3条件全部结果；保留失败目录。原单位经新adapter结果应匹配S60中位单位参考；另两条件检验单位变化后的投影/栅格/权重一致性。depth/cos允许float32 roundoff abs1e-6,rel1e-6；indices要求完全相同，来源权重abs1e-6；不得因未通过临时松容差。检查调用前后全部输入数值未变、输出单位明确。

外部上限120秒，一次create-only execution_01；有限测试和数据条件共用原CPU环境，没有新模型/GT/质量评分。以上3条件来自同一场景，不是跨场景3重复。若仅此验证通过，状态为组件已实现并在保存几何通过，仍需未来完整管线集成和新变体生成，不填补原C2评分行，不改原NMS/输入/ROI/阈值。
