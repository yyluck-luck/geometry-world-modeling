# S101 GPU 清单与 S102 数据资格独立审查

**审查时间：** 2026-09-15（Asia/Shanghai；文件实际写入时间见主账）  
**审查身份：** 独立合同/安全审查（不是 GPU 运行结果，也不是 Gate0 通过）  
**审查对象：** `work/S101_GPU_RUN_MANIFEST_TEMPLATE.md`、`work/agents/gpu_experiment_contract_20260915.md`、`work/S102_gate0_schema_20260915.md`、`work/S102_gate0/README.md`、`work/S102_gate0/GATE0_RESULT.json`

## 1. 审查结论

当前模板和 schema 已经覆盖了最重要的科学边界：未见数据资格门、预测封存后才读 GT、RGB-D 时间配对、K/pose/深度单位、`k=2/4/8`、强基线、停止条件和失败保留。它们足以作为**预运行设计草案**，但还不足以直接当作学校服务器上的最终可执行合同。

本审查结论为：**CONDITIONAL_PASS_FOR_PREPARATION；NO_PASS_FOR_GPU_SUBMISSION**。

原因不是发现了一个已发生的数据泄漏，而是模板仍有若干字段和语义检查缺口。尤其是：

1. S102 结构 schema 没有强制每帧确实包含 RGB、depth、pose、timestamp 等正确类型的 modality；部分字段只检查“有数组/有字符串”，不能保证投影数学有效。
2. 预算只在 Markdown 中描述，缺少机器可读的 GPU 显存、wall time、I/O、forward 次数、重试和 seed 上限。
3. 可复现信息没有形成完整的不可变运行身份，包括 Git dirty 状态、容器/环境锁、PyTorch/CUDA/驱动、命令行和确定性设置。
4. SSH 迁移说明禁止上传密钥和凭据，但尚未要求 host key 指纹核对、最小权限、远端路径穿越检查、传输后 SHA 回读和作业网络/凭据隔离。
5. 许可回执只有路径和状态字段，尚未机器可读地记录许可证版本、允许的用途、取得时间、数据主体/场景限制和是否允许远端处理。

因此，只有补齐下面的 P0 项并通过独立静态检查，才可把模板状态从 `TEMPLATE_ONLY_NOT_SUBMITTED` 改成可提交版本。即使补齐，也仍必须先对新的合法 held-out 数据运行 S102 Gate0；现有 TUM 开发数据的 `BLOCKED_DEVELOPMENT_DATA_NOT_HELD_OUT` 结果不改变。

## 2. 四个重点维度逐项审查

| 维度 | 当前已有证据 | 判定 | 必须补充 |
|---|---|---|---|
| GT 隔离 | S101 要求未来答案在 prediction seal 后读取；S102 `gt_read_phase=after_prediction_seal`；README 明确禁止 future depth/pose 进入 selector | **部分通过** | 机器可读的 `future_body_read_before_prediction_seal=false` 运行回执；区分公共 query camera 控制量与作为答案的 future pose；审计缓存、预处理特征、shell 环境变量和人工选择目录，防止间接泄漏 |
| 预算 | Markdown 固定 `k=2/4/8`、候选池、输出数量、相同权重/seed，并要求 GPU 显存和 wall time 记录 | **部分通过** | 将每个 job 的 slot/token、forward 数、最大显存、CPU/RAM、wall time、读取字节、重试次数、分片数和 scheduler 资源写入冻结 JSON；明确是否允许 warm-up、失败重试和缓存命中 |
| 可复现性 | 要求源码、权重、数据 manifest、协议 SHA、seed、`ENV_RECEIPT.json`、`RUN.json`、预测 seal、评分和独立复核 | **部分通过** | 增加 Git commit + dirty diff SHA、容器/conda lock、Python/PyTorch/CUDA/driver、硬件 UUID、命令行、环境变量白名单、确定性 flags、locale/timezone、job ID 和退出码；所有分片必须绑定同一冻结身份 |
| SSH 安全 | 明确 host/user/port 等未知时不连接；禁止上传 OpenRouter key、DSH state、SSH 私钥和无关个人文件；建议 dry-run 和传输后哈希 | **部分通过** | 首次连接记录 host key 指纹并要求人工/官方来源确认；只用 SSH agent/短期凭据，不把 secret 写入 manifest/log；限制远端根目录和 `..`/绝对路径；传输清单、回读 SHA、权限/umask、作业身份、网络访问和删除策略 |

## 3. S102 schema 的结构和语义缺口

### P0：运行前必须修复

**P0-1：强制 modality 语义。** `frame.modalities` 目前只要求至少 3 个元素，未要求恰好/至少包含正确的 `kind`。一个错误的 JSON 仍可能放入三个 `pose` 或三个未知 modality 并通过结构层。语义检查器必须逐帧要求：历史帧有 `history_rgb`、`history_depth`、`timestamp`、`intrinsics`、`pose`；future query 有明确的 `future_rgb`/`future_depth`/`pose` 角色，并将评分答案与公共控制量分开。

**P0-2：固定几何数组的数值形状。** `camera.K` 的 `prefixItems` 只限制行长度，没有限制每个元素为 finite number；`camera.pose` 只限制外层长度 4，没有限制 4×4、最后一行、旋转正交性、平移单位或有限值。应在语义检查中检查 3×3/4×4、finite、`fx>0, fy>0`、SE(3) 旋转误差和 Z 正值投影。

**P0-3：要求 BODY_VERIFIED。** `body_verification` 允许 `METADATA_ONLY`，但 Gate0 的通过条件要求合法完整帧正文。对进入 `HELD_OUT_TEST` 的 RGB/depth/pose/timestamp/K，必须要求 `BODY_VERIFIED`；`METADATA_ONLY` 只能停留在数据发现/准备状态。

**P0-4：明确答案读取字段。** 当前 `future_body_read_before_prediction_seal` 的语义容易误读为“字段为 true 表示允许”。建议在 receipt 中改成布尔事实字段：`future_body_read_before_prediction_seal: false`，并另设 `future_body_read_forbidden: true`。同理，`future_camera_pose_if_protocol_allows` 必须写明是控制相机轨迹还是 GT pose；若是 GT pose，不能让 selector 看到其数值。

**P0-5：补充身份唯一性和路径安全。** 语义检查器必须拒绝重复 `scene_id`/`trajectory_id`/`sample_id`、历史与 future 重叠、重复 timestamp、符号链接、绝对路径和包含 `..` 的 `relative_path`。规范化后的真实路径必须仍在声明的 `data_root` 内。

**P0-6：许可回执必须可审计。** `permission_status` 和 `evidence_path` 不足以证明允许在学校服务器处理完整帧。增加 `license_name`、`license_version_or_url`、`research_use_allowed`、`remote_compute_allowed`、`redistribution_allowed`、`verified_at_utc`、`verified_by`（不记录不必要个人信息）和证据 SHA。缺字段保持 `AMBIGUOUS_NOT_VERIFIED`。

### P1：进入正式多场景实验前修复

**P1-1：开发/校准/测试交集不仅看路径。** 增加原始来源、room/subject/session、连续时间段和预处理缓存身份的交集检查。相同房间的 reference/rescan、相邻时间片或同一图像的派生深度不能仅因路径不同就算独立 held-out。

**P1-2：记录配对和时间语义。** schema 要求严格 `<20,000,000 ns`，但需额外检查时间戳非负、单调性、同一 RGB 不复用 depth、历史到 future 间隔、断点和重复 query。不能仅由文件序号推断时间。

**P1-3：深度字段约束。** 对 `bit_depth`、`depth_unit`、无效值编码、有效率、分辨率和 dtype 做允许值或来源声明；记录零、NaN、Inf、越界和裁剪计数。无效 GT 必须进入固定分母规则，不能在评分时静默删除。

**P1-4：写入运行预算合同。** 推荐新增机器可读对象：

```json
{
  "budget": {
    "memory_slots": [2, 4, 8],
    "max_input_tokens": null,
    "max_forward_calls_per_condition": 1,
    "max_retries": 0,
    "max_gpu_memory_bytes": null,
    "max_host_memory_bytes": null,
    "max_wall_seconds": null,
    "max_read_bytes": null,
    "seed_set": [0, 1, 2]
  }
}
```

其中 `null` 在冻结前必须由学校调度器/模型实测或明确合同填值，不能把未知资源写成无限制。若允许 warm-up 或缓存，必须分别计数，不得把缓存命中伪装成一次完整 forward。

## 4. SSH/远端运行安全检查清单

在主机信息实际取得后，提交任何作业前必须生成一份不含凭据的 `SSH_PREFLIGHT.json`，至少包含：

1. 主机名、端口、远端用户、调度器和项目根目录由官方/导师渠道确认；不使用猜测值。
2. 首次连接的 host key 指纹已记录，并与可信渠道核对；禁止用 `StrictHostKeyChecking=no` 绕过验证。
3. 本机只使用 SSH agent、短期 token 或调度器安全机制；私钥、OpenRouter key、DSH state、浏览器 cookie 不进入代码、manifest、stdout 或远端快照。
4. 远端 job 只拥有项目目录所需权限；`data_root` 和输出目录做 canonical path 检查，拒绝符号链接逃逸、`..` 和绝对路径混入 manifest。
5. 上传先做代码/协议/小 manifest dry-run；传输后逐文件回读 SHA-256 和字节数。大数据使用服务器已有副本时也要核对身份，不以文件名代替哈希。
6. 作业环境保存 Python、PyTorch、CUDA、driver、GPU 型号/UUID、容器或 lockfile SHA、命令行和 scheduler job ID；退出码、stdout、stderr 和 signal 全部保留。
7. 远端网络默认最小化；若需要下载权重或数据，单独记录 URL、证书/响应身份和下载 SHA，禁止把凭据注入模型进程。
8. 失败 job 不覆盖旧目录；修复后使用新版本目录和新冻结 SHA。清理/删除策略必须在实验结束后另行记录，不自动删除失败证据。

## 5. 对 S101 远端实验顺序的审查

顺序总体合理：环境 smoke test → S102 Gate0 → S103 baseline → S104 强基线 → S105 GRC → S106–S109。需要加一条硬门：

> **S103 smoke test 也不得读取 held-out future body 或 GT；它只能使用公开的输入接口和 synthetic/no-GT 单样本，或在 Gate0 PASS 后使用已冻结的测试预测流程。**

如果 smoke test 使用了 future RGB/depth/pose 的正文，即使没有评分，也会污染正式 held-out 身份。推荐把环境 smoke test 绑定到独立 development fixture，禁止复用 held-out 路径。

此外，S104 强基线应先冻结 candidate pool、预算和 seeds，再运行；不能先看 confidence/coverage 结果后决定 GRC 的候选池。S105 的 risk calibration 必须只在 `CALIBRATION_ONLY` 上拟合，`HELD_OUT_TEST` 只用于一次冻结后的评估。

## 6. 本次审查没有发现的事项

- 没有发现学校服务器已连接或 GPU 已运行的证据。
- 没有发现新的合法 held-out 数据已经通过 Gate0。
- 没有把现有 TUM `DEVELOPMENT_SEEN` 数据升级为测试数据。
- 没有把 S99/S100 的 source-block 缓存重渲染当作完整 VMem/GRC 结果。
- 没有修改旧实验、旧失败目录或已有冻结结果。

## 7. 最终行动建议

**现在可以做：** 将本审查作为 S101 的条件性前审，补机器可读预算/环境/SSH preflight 模板；在本机用人工 fixture 测试路径逃逸、重复身份、future body 读取和 schema 类型错误分支；继续寻找合法 held-out 数据。

**现在不能做：** 猜测学校 SSH 主机、上传凭据、把开发 TUM 送入正式 GRC、在 Gate0 前运行 S103/S105，或用 GPU 模型加载成功代替真实 forward 和未来 GT 评分。

**验收条件：** P0-1 至 P0-6 和预算/环境/SSH 清单完成后，由不同实现做一次静态复核；取得合法数据后重新运行完整 S102 Gate0。只有 `formal_gate0=PASS`、prediction seal 已封存且独立复核通过，才可提交学校 GPU 的正式长时程实验。

**科学状态保持：** `new_method_validated=false`；`novelty_authorization=NONE`。
