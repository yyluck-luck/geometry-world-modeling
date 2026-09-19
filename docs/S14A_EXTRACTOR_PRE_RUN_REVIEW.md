# S14A提取器执行前独立源码审查

**状态：需修正后再冻结执行（BLOCKED_SOURCE_PRECISION_GUARD）。** 在当前源码SHA `188061a33c107043f7396c401affb10b5112fcd71db941159c9cde9dbedf12f3` 中发现一处历史FP32减法与Python float减法的身份守卫不一致，可能误拒合法旧记录。没有读取真实30输入，不能宣称本域实际已经触发；但代码的守卫语义不能按现有版本批准。

审查者为 `research_novelty_routes`，与编写提取器和19项人工测试的作者不同。本次只读源码、准备文档及人工回执，另外做一个不调用提取器的人工标量减法示例。没有运行真实特征提取、读取实验JSON/GT/评分数组、重新选图或训练模型。以下是源码审读，不是19项同作者人工测试变成了真实数据验证。

## 必须修正：来源权重间隔的精度守卫

提取器在 `extract_row` 中先将保存的20个权重转为Python float，然后计算：

```python
gap = weights[13] - weights[14]
require(finite(official["cutoff_gap_14_15"], "saved source weight gap") == gap,
        "Saved 14/15 source weight gap mismatch")
```

旧 `src/vmem_retrieval_kernel.py` 的renderer深度与cos缓冲为FP32，`process_retrieved_spatial_information`累加并归一化这些来源票权；旧 `src/rgbd_retrieval.py::select` 记录间隔的表达式是 `float(ranked[13][1]-ranked[14][1])`，先在原NumPy标量上减，再转Python float。当前固定NumPy2语义下，这不等于一般情况下先提升两个操作数再相减。两个值接近时可能恰好完全一致，不能从接近案例推定所有合法权重都一样。

人工标量（只用标准库struct作IEEE单精度舍入）：

| 项目 | 数值 |
|---|---:|
| a，FP32中的0.03 | 0.029999999329447746 |
| b，FP32中的0.001 | 0.0010000000474974513 |
| 旧FP32相减后转float | 0.028999999165534973 |
| 当前Python float相减 | 0.028999999281950295 |
| 差 | 1.1641532182693481e-10 |

这是**MAJOR执行前问题**：守卫可能因为检查器自己的精度变化拒绝并未被改坏的原输入。它不说明已有科研数据错误，也不是实际30输入失败结果。

具体修复建议：用标准库struct明确复现FP32相减，并与保存间隔精确相等核对；特征可以直接复用通过校验的保存FP32 gap。若作者确实需要Python提升精度后的差值，必须在列定义中明确新区别，并只按旧FP32语义验证原存档。不能事后扩大任意容差。需补一条能区分两种运算的人工案例，重新绑定源码/检查器/回执哈希，然后进行修正版审读。

## 已通过的源码语义审读

| 项目 | 结论与边界 |
|---|---|
| 恰切输入域 | `expected_paths`为S7/S8×3块的6份stride8 prediction_only_selection，加2×3×4份S12 selection，共30。manifest条目只允许path/sha256，缺失、重复、多余或非64位小写哈希拒绝。 |
| 域不沿数据扩展 | 文件名由固定stage/block/query构造，不沿JSON中任何路径打开其它文件。源码与manifest属于控制文件，另于30实验文件之外读取。 |
| A0P0/stride8/24query | 固定循环2stage×3block×4query；源元数据核block/stride/split，query完整20–23，取maps.A0P0。pose元数据核stage/block/query/split，末尾要求24行。 |
| 候选与最终图 | 两池均14唯一ID，selected均4唯一ID且在候选内。来源配额20ID中0/1值仅核候选；pose14为已存完整20距离排序前14。 |
| 来源票权 | HHI、max-share、熵用保存weights重新归一化，未用candidate_counts伪造概率。旧首次初始化后又累加的行为被保留；这些量不等于校准可靠度。 |
| 六个最终pair | selected的后3帧必须与accepted steps顺序一致；依次比较前1/2/3个已选ID，严格覆盖6个无向pair。只将这些accepted比较写入特征/溯源。 |
| 拒绝缺失与fallback | 非空fallback拒绝；缺失、重复比较ID、非有限/负distance、错误accepted标志拒绝。未用拒绝步骤里的偶然比较填补缺pair。 |
| 拒绝步骤的范围 | 源码也验证拒绝步骤比较字段的合法性，但它们不进入pair均值/最小值；不能把这一点说成完全不读取拒绝步骤。 |
| 15特征/6元数据 | FEATURE_COLUMNS含15项，METADATA_COLUMNS含6项。metadata与特征在JSON分别声明；CSV共列不构成强制隔离，后续消费者必须显式只取FEATURE_COLUMNS。 |
| 距离来源 | query距离用保存的全20 FP32值，核两trace中的候选距离相等；pair用保存的FP64比较值，不重新计算距离或NMS。f32/f64说明历史来源精度，均值由Python float/math.fsum计算。 |
| 输入身份 | 30文件全部SHA验证成功才解码任何实验JSON；解码使用已验证缓存字节。特征计算后重开30文件验证SHA，并核源码及manifest字节前后一致。 |
| 输出 | 已存在output在读取manifest前拒绝。新目录中的字段/输入错误保存failed元数据；manifest/schema/source错误发生在建目录前，需要调用方保留控制台记录。成功时保存源码与manifest快照。 |
| 调用边界 | 仅标准库，无模型、renderer、GT评分路径、网络、实验runner导入、拟合或路由调用。源码内六个ID-pair的组合检查不是新距离或oracle评分实验。 |
| 人工回执 | v2回执19项passed与所给源码/检查器SHA一致；人工known-row的15个预期值按定义可手算。没有重跑该检查器，也没有把同作者测试列作独立真实输入运行。 |

## 另一个文字修正建议

准备文档称姿态组合量为“0.1 × 归一化平移距离 + 旋转角”。实际 `geodesic_distance` 内是 `0.1 * torch.norm(t1-t2) + angular_distance`，没有单独归一化平移距离的操作。建议改为“保存的预测坐标中的欧氏平移距离”；继续保留不是物理米或纯角度的提醒。级别MINOR，不需为此改提取器代码。

## 必须保持的研究边界

工具的固定路径和字段白名单属于工程隔离；解析仍解码整份获批JSON，不是操作系统沙盒或让未知键消失。它不会恢复研究团队已知S7/S8旧答案之前的状态，更不使24相关已见query变成独立未见测试。

本次审查未读取30份真实文件，不能替父任务批准将来manifest的具体30个哈希来源。当前只核代码能强制固定域；父任务仍须从已核输入清单生成manifest，另冻协议/最后源码/人工回执和本审查。修复后如果真实数据缺pair，必须保留失败而不能用0、其它结果或GT填补。

源码复用旧NMS决定和距离，不检查每步阈值逻辑或重新证明原NMS正确；这依赖以前独立审计。metadata分离也是字段合同，不是拟合时自动阻断场景泄漏。query相机源于已经看过的query RGB，不能直接声称在生成前只有轨迹时可部署。

即使未来24×15特征提取成功，也只完成数据准备，不产生新方法准确率、信号有效性、速度收益或视频质量结果。也不能仅凭集合重叠/熵这些普通量宣布创新。

## 实际skill与下一步

实际读取 [本地Claude scientific-critical-thinking](</Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md>) 并应用测量定义、输入可用性、构念有效性、已见数据偏差和证据/解释分离的原则。未调用Claude模型，未套用临床GRADE；本次执行前审查使用代码/合同表，不新增生成式示意图或文献综述。

下一步是修正精度守卫、补人工差异案例、更新冻结身份并复审。当前报告不批准执行旧SHA。原代码、人工回执和本次发现证据应保留，不能把后续修正版通过倒写成旧版已经通过。

