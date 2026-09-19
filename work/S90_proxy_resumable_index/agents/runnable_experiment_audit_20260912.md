# 本机可运行实验审计（2026-09-12）

## 目的

审计当前 geometry-world-modeling checkout，判断在没有新网络数据、没有远程 GPU 的条件下，是否存在可以立即执行、且仍然属于真实科研证据的最小下一实验。本文不修改核心代码，不把已有缓存重评分伪装成新实验。

## 直接核验的输入

- `work/S86_fixed_warp_consumer/S86_RESULTS.md`
- `work/S86_fixed_warp_consumer/execution_01/RECEIPT.json`
- `work/S87_terminal_strength_audit/S87_RESULTS.md`
- `work/S87_terminal_strength_audit/execution_01/RECEIPT.json`
- `work/S87_terminal_strength_audit/NEXT_SCIENTIFIC_DECISION.md`
- `work/S87_terminal_strength_audit/INDEPENDENT_GEOMETRY_EVALUATION_OPTIONS.md`
- `work/S90_proxy_resumable_index/agents/gate0_probe_existing_candidate_report.json`
- 本地 `data/` 文件清单（只检查路径与已存在的项目材料，不下载数据）

已确认 S86 是一条真实 50 步生成链及派生控制；S87 是 6 个有限强度控制，其中 3 组完整八槽解码，但复用 S86 的 G0 末态、warp 和同一噪声历史。S87 的执行回执显示 `denoiser_calls=0`、`encoder_calls=0`、`decoder_calls=3`、`decoder_chunks=24`，因此不能重新描述为 6 条新生成链。

## 结论：没有可立即执行的“新方法/未来几何”实验

当前最小科学实验必须至少有：

1. 独立于历史选择的 RGB 或 RGB-D 场景；
2. 已冻结的相机内外参与时间关系；
3. 过去帧与未来查询帧的明确划分；
4. 可验证的未来几何答案（深度、点轨迹或其他外部标签）；
5. 预先固定的记忆选择、风险计算和比较预算。

现有 Gate 0 检查结果仍是 `REJECT / DATA_NOT_AVAILABLE`，因此这些条件没有同时满足。没有完整的历史—未来配对 manifest 时，运行 GRC 选择器或未来几何评分只会产生合成诊断、缓存重算或自评估，不能称真实新实验。

## 可以做但不能称新科研实验的本机动作

### A. S86/S87 缓存一致性复核（审计动作）

可运行的命令入口：

```bash
/Users/rocket/Desktop/HKUST\ IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python \
  work/S87_terminal_strength_audit/check_saved_scores.py --binding-sha256 <已冻结绑定值>
```

它检查保存的 CSV/JSON、数组形状、SHA、分母和旧 Gguide 绑定。该动作不调用新模型、不产生新样本，也不引入新场景，所以结果只能标为“保存结果复核”，不能递增 S87 的样本量或称为新实验。

### B. S87 视觉材料再读

可以重新查看 `work/S87_terminal_strength_audit/visuals_01/` 中已保存的 24 张图与总览。这只能改善报告解释，不能产生新的盲评或几何真值证据。原报告已经记录非盲观察和目标 22 失败，不能因为再次查看而改变结论。

### C. 已有 S73/S74/S77/S80/S81 外部几何观察的账本复核

可以运行现有结果的 schema/绑定检查，但它们已经是完成的旧实验；复核不增加场景、目标或独立样本。不能把复核重命名成“新正负控制”。

## 不应在当前条件下启动的动作

- 不继续细扫 S87 的 λ，不二分、不插值、不按目标挑最优强度；这会把已见场景的事后选择继续扩大。
- 不用 S86 的 warp 或目标图作为未来几何真值；那只能测“输出是否接近自己的参考”。
- 不用 synthetic NumPy 或已有渲染器输出宣称动态世界建模效果。
- 不因 PointOdyssey/WorldScore 的网页和文件列表存在，就宣称数据已下载、配对关系已验证或可运行。
- 不把已保存的 S86/S87 数值重读写成新模型运行。

## Gate 0 通过后的最小真实实验

名称应写成：**未来几何风险增量预测试验（GRC-Pilot）**。括号说明：在固定历史预算下，比较低风险与高风险历史集合对同一未来查询的外部几何误差。

最低规模建议：至少 3 个独立场景、每场景至少 6 个历史帧和 3 个未来查询；过去帧严格早于查询帧；固定 K、world-from-camera 姿态、深度单位、遮挡/缺失规则；先跑无选择、最近帧、随机固定种子和 GRC 候选四个臂。主要指标应是未来点/深度几何误差、失败率和完整分母，同时记录 RGB 指标，不能只报 MSE。

执行顺序：

1. 冻结数据 manifest 和 SHA；
2. 运行 `verify_gate0_manifest.py`，只有 PASS 才进入实验；
3. 生成 risk-only 选择结果，不调用生成模型；
4. 以固定随机性和固定计算预算运行未来查询；
5. 由独立 scorer 读取未来真值并计算几何指标；
6. 做跨场景结果与反例分析；若“低风险历史 → 更低未来误差”不稳定，则停止 GRC-Memory 方法化。

## 证据边界

本审计确认了现有缓存和合同的位置，但没有新模型调用、没有新网络数据、没有新未来几何分数。当前状态仍是 `new_method_validated=false`、`novelty_authorization=NONE`。下一步不是“马上跑一个伪实验”，而是先取得并通过 Gate 0 所需的真实配对数据；在此之前，最有价值的本机工作是保持缓存复核和协议修正，避免污染科学账本。
