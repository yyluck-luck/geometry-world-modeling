# S14E 独立运行前审读

当前状态：**Predictor部分通过；prepare、score和最终manifest尚待完整审查，不是整项执行放行。** 不同作者审读者为s14e_camera_calibration_audit。实际时间与源码SHA见work/S14E_pre_run_review/，旧产物、原尺度审计和勘误均未改。

## Predictor已完成核查

已逐段阅读373行 `scripts/run_s14e_state_reuse_queries.py`、作者准备说明、S14D实际runner及上游direct接口，并另写独立人工检查器 `work/S14E_pre_run_review/check_predictor_independent.py`。它没有复用作者的测试程序，也没有导入CUT3R模型；只调用生产纯schema/控制流函数与人工stub。

实际独立检查118项通过：6组控制流场景包括正常五次、第二次异常、第四次非有限输出、最后一次int64状态被改动、最后一次多余tensor、第二次未经过ray encoder；另通过2个main早期失败场景（畸形JSON、禁读目标PNG身份）。异常均按预期阻断后续调用，已有返回输出先保存，之前成功文件保留，尝试/返回数符合路径。测试日志中的traceback是刻意注入的预期人工失败，不是真实模型失败。真实NPZ/RGB/depth/trajectory解码0、权重读取0、模型调用0。

| 审查点 | 结论与限定 |
|---|---|
| 环境Git | 程序明确调用/usr/bin/git，实际只读验证版本2.50.1、固定commit和clean；不受PATH旧git worktreeconfig错误影响 |
| Q0恢复控制 | zero占位、旧query_call_1，idx20、instance、flags、true_shape int64与S14D一致；six tensor需shape/dtype/字节一致，NaN/数值近似不能混过 |
| 状态 | 固定五字段schema和旧metadata字节SHA；state_pos为int64，其他原FP32；每次后精确核anchor，未把返回新状态传播 |
| NPZ范围 | 四允许角色，17个数组，allow_pickle=False、全key域与逐键白名单；旧parity条件只读3字段，不解码其history字段 |
| 新条件 | predictor只证shape/finite/底行/正焦距，不假装它验证了proper rotation或ray意义；这些是prepare待审的门 |
| 读取边界 | 禁止常见图像/额外NPZ及原始轨迹文件进入predictor身份表，模型段拒绝PIL.Image.open；源码追踪不是OS沙箱证明 |
| 异常及计数 | 返回即保存再验六输出/state/encoder/parity；普通Python异常写FAILED与计数。外部强杀可能中断最近一次日志更新，只能据caller和落盘状态报告，不能补造精确完成次数 |
| 模型条件 | 原CPU8线程/seed0/已有精度；安全全局白名单与现有checkpoint绑定；本审读未打开权重，是否真实加载一致仍待冻结后实际Q0门 |

最新 `docs/S14E_FINAL_PROTOCOL.md` 已统一zero/query_call_1，解决旧设计草案NaN/call0措辞差异；两份旧控制输出曾字节相同也不能替代最终文稿明确性。

## 后续必须按最终单位审查

本前审唯一采用 `work/S14E_calibration_audit/scale_definition_clarification.md` 的**模型单位/米**：A=Rpred0*Rgt0.T，s=Σ[A(C_i−C_0)]·(p_i−p_0)/Σ||A(C_i−C_0)||²，c=p_0−s*A*C_0，target model=(A*G_q,s*A*C_q+c)，主深度self_z/s。原审计反向OLS是未采用候选，不能混进实现。

待prepare审查：只解码历史白名单、history缓存与S14D pose/状态锚身份、GT历史RGB时间与target depth时间、proper rotations/插值/退化尺度、K224/像素映射、官方编码与标准pinhole分离、全部基线和条件封存。待score审查：静态manifest/动态预测seal身份与时间、答案只在封存后读取、固定单位/掩码/δ1完整分母/共同域/空域、失败保留及独立数学复算。

最终冻结必须绑定实际完成的源码与控制文件版本。当前部分通过不意味着可以提前读取真实数组或运行S14E。
