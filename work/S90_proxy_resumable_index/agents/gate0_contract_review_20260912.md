# Gate 0 / Gate 2 合同审查（本机离线版）

<!-- EXPERIMENT_NAME_LEGEND_20260912_BEGIN -->
> **S编号与具体试验名称说明（2026-09-12更新）**  
> 文档中的 `S86`–`S90` 是项目内部阶段编号，保留它们是为了让结果、日志和回执可以追溯；括号内是给新读者看的具体名称。编号不是论文术语、结果等级或“实验成功”的标志。S88–S90主要是数据资格/传输与协议审查，不能误读成模型性能实验。
>
> - **S86（单场景四目标几何条件注入基线实验）**：在一个已见静态场景、四个相关目标上，比较历史几何注入方式的真实生成链和RGB误差。
> - **S87（末端引导强度控制与多步引导必要性反例实验）**：复用S86缓存，比较末端处理强度与持续多步引导；它只检验该已见场景的有限反例，不验证GRC或长期几何收益。
> - **S88（RTMV相机JSON元数据与静态投影数据资格检查）**：核对归档身份、相机元数据和可访问的静态文件头；不是RGB-D配对性能实验。
> - **S89（RTMV配对数据TLS接续失败审查）**：记录两种TLS/传输接续尝试及其失败边界；失败本身不等于数据缺失或科学负结果。
> - **S90（RTMV归档配对数据恢复与索引协议审查）**：检查受限Range传输、归档成员身份、断点恢复和索引安全条件；已恢复的512B文件头不等于取得可用深度正文。
>
> 后续报告首次出现编号时应同时写成“**S86（单场景四目标几何条件注入基线实验）**”这类形式；后文可使用编号，但不要只写编号来替代试验名称。
<!-- EXPERIMENT_NAME_LEGEND_20260912_END -->


时间：2026-09-12（Asia/Shanghai，具体记录时间由主账保存）  
审查者：独立数据资格/实验合同岗  
范围：只读当前 Gate 0 数据资格合同、GRC-Memory Gate 2 pilot 设计，并实现一个不联网的 manifest/schema 检查器。没有发起网络请求，没有下载、解码或评分新的 RGB、深度、相机或模型输出。

## 1. 审查结论

当前 Gate 0 **尚未通过**。原因不是脚本不能运行，而是项目目前没有一个同时包含历史 RGB/几何/相机、未来 RGB-D/独立几何答案、时间关系、坐标/单位说明和答案隔离记录的冻结 manifest。RTMV 的 tar 头和相机元数据只能证明有界传输或发布目录信息，不能证明一个可评分的历史—未来配对单元；S86/S87 也只是一个已见静态生成场景的局部结果。

Gate 2 的科学问题是合理的，但只能在 Gate 0 通过后启动：

> 在同一候选历史池、同一槽位数、同一消费预算和 past-only 特征下，历史几何风险能否预测并改善未见未来查询的几何误差？

当前不能以 schema PASS、tar 206、程序坐标自洽、RGB MSE 或选择器输出代替未来几何答案。`new_method_validated=false` 应继续保持。

## 2. 对现有合同的核验

### Gate 0：必须保留的硬条件

现有 `agents/innovation_next_gate_20260912.md` 和 `agents/grc_real_experiment_freeze_checklist.md` 的核心条件正确，应继续作为硬门：

1. 至少三个独立 `scene_id`；每个候选研究单元至少六个历史候选和三个未来查询。这个是小型 pilot 的最低判别门，不是统计泛化保证。
2. 每个历史帧有稳定 ID、严格早于查询时刻的时间、RGB/几何输入、K 和明确方向的位姿；查询相机只包含部署时确实可见的请求条件。
3. 未来目标有独立深度/三维参考、目标相机、有效 mask、深度单位和语义（例如 camera-Z、ray-range、disparity）。没有这些只能降级为外观或静态投影诊断。
4. 选择器、风险标量化和阈值只能读 past/history 与冻结的 query camera，禁止读目标 RGB、目标深度、未来位姿、未来误差、目标 mask 或生成后的质量分数。
5. 训练、校准、测试按物理场景或明确轨迹家族切分。只按帧号切分或把视角数字 ID当连续时间不合格。
6. 选择输出先封存，答案读取器后启动；必须保留缺失、无效、空集和排除原因，不能静默删除难例。

### Gate 2：必须从“风险上界”收窄为可检验选择比较

当前合同应采用以下较窄的第一轮定义：

- 比较 `random-k`、`recent-k`、`nearest-pose-k`、`coverage-k`、`confidence-only`、`utility-only`、`risk-only` 和待测 `risk+utility`；有可运行实现时补 Fisher/EIG/VMem 原始规则。
- 所有策略共享 eligible history、槽位数 `k`、目标相机输入、生成/几何消费者和预算；选择成本也要计入或单独报告。
- 先用廉价几何消费者计算未来深度/三维投影误差，再考虑昂贵视频生成。几何消费者通过不等于视频质量通过。
- 主指标只选一个并预注册（优先三维 position error；若只能有目标深度，则声明为替代指标），像素数、支持率和 RGB MSE 只作辅助量。
- 用 query/scene 层 paired difference 和不确定区间；不要把像素、候选帧、随机 seed 当独立场景。
- 如果使用 conformal calibration，校准对象应是完整的集合级策略损失，而不是把每条候选残差自动称为未来误差上界；只能声称合同满足的边际期望控制。
- `oracle` 可以作为上界单列，但不能参加可部署方法排名，也不能用于调阈值。

## 3. 发现的主要风险与修正

| 风险 | 为什么会误导结论 | 修正 |
|---|---|---|
| 把 RTMV 视角编号当时间 | 静态多视角的数字 ID不保证轨迹或未来状态 | manifest 明确 `trajectory_id`、`timestamp_s` 和 `future_horizon_s`；不满足则只能做静态诊断 |
| 只保存 RGB/K/RT | 无法得到独立未来几何损失 | 缺少目标深度/三维参考时 Gate 0 REJECT，不能启动 GRC 方法验证 |
| 直接把深度文件名当 camera-Z | EXR 可能是 ray-range、渲染距离或其他语义 | 强制写 `depth_semantics.kind/unit/registered_to/invalid_value`，从导出说明核对 |
| 用 future 做归一化或选样 | 产生答案泄漏 | 保存 `selection_input_paths`，离线检查未来答案路径不在其中；未来评分分阶段读取 |
| 只比较 `k` | 选择器可能用了更多特征或 CPU/GPU 时间 | 保存预处理、特征、排序、消费和峰值内存成本，必要时做总成本匹配 |
| 只报平均 MSE | 单个困难查询可能变差，且 MSE不是几何真值 | 保存每个 query/scene 的几何误差、覆盖、空值和分母；预注册最小效应与否决规则 |
| 一个场景调参后再报测试 | 不能支持跨场景或未见泛化 | calibration/test 按 scene-level 隔离；单场景只能标 pilot |

## 4. 新增离线检查器

已新增：

`work/S90_proxy_resumable_index/agents/verify_gate0_manifest.py`

它只使用 Python 标准库，具体检查：

- manifest schema 和必需的 source/split/unit 字段；
- development/calibration/test 列表和 unit ID 重叠；
- 每个 unit 的 scene、查询时间、未来跨度、历史数量和未来 target；
- 历史时间是否严格早于 query time；
- 历史与查询相机的 K、4×4 位姿、坐标方向和位移单位；
- future depth 的语义、单位、无效值和 RGB 注册说明；
- 本地 RGB/depth/mask/pose 文件存在、声明字节数和 SHA-256（可用 `--no-hash` 只审 schema/path）；
- future answer 文件是否出现在 `selection_input_paths`，作为一个明确的答案隔离检查；
- 独立 scene 数是否达到三、历史候选是否至少六、未来查询是否至少三；
- 输出 `gate0-report-v1`，明确 `network_used=false` 和“qualification only, no method gain measured”。

静态验证已经完成：

```text
python3 -m py_compile work/S90_proxy_resumable_index/agents/verify_gate0_manifest.py  # PASS
python3 work/S90_proxy_resumable_index/agents/verify_gate0_manifest.py --help          # PASS
```

没有创建伪造 manifest 或伪造数据来取得 PASS。真实 manifest 到位后，建议先执行：

```text
python3 work/S90_proxy_resumable_index/agents/verify_gate0_manifest.py \
  --manifest /path/to/frozen_gate0_manifest.json \
  --report /path/to/gate0_report.json
```

返回码 `0` 仅表示 Gate 0 的本地 schema/身份/隔离检查通过；它不表示未来几何关系成立、GRC 优于基线或论文创新成立。返回码 `2` 表示资格门拒绝，必须保留报告并修复数据/合同。

## 5. Gate 2 的最小可执行顺序

1. **不联网的 manifest 审查**：先用新增检查器完成字段、文件、hash、时间、scene split 和答案隔离。
2. **独立前审**：由另一作者复核 manifest 和选择器代码，确认没有未来读取、事后调参和隐藏候选。
3. **封存选择输出**：在答案不可读阶段保存每个方法的 selected IDs、风险、utility、成本和随机状态。
4. **答案释放后评分**：由独立 scorer 读取目标深度/位姿，计算预注册的几何损失和完整分母。
5. **基线对照与停止**：若 risk 与 signed future benefit 不稳定、成本匹配后不优于简单 baseline、或仅单场景有效，则停止 GRC 方法主张，保留失败边界。

## 6. 给 root 的下一步

- 把本检查器作为 Gate 0 的工程入口，但不要把它称为实验结果。
- 在取得真实配对数据前，不运行 GRC selector、不读取新的答案文件、不做 Gate 2 生成。
- S90 RTMV 索引仍应先修复其独立审查列出的断点/归档身份问题；索引获得 JSON 也只进入候选数据资格，不自动通过 Gate 0。
- 记录本轮为“合同审查 + 离线工具实现”，而不是新模型、网络数据或未来几何评分。

**最终裁决：** Gate 0 目前 `REJECT / DATA_NOT_AVAILABLE`; Gate 2 `BLOCKED_ON_GATE0`。新增脚本使下一步具备可审计入口，但没有提高 GRC 的科学证据等级。
