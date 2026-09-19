# 人工复核清单 — S103-VMemBase 协议 v11

**给 `yliutz-human-review-20260917` 的核对材料。这不是复核件本身，是你做决定的依据。**

复核目标（必须逐字绑定，错一个字符验证器就拒绝）：

```
protocol SHA-256 = e2842de94a17159f6ee8aab40b4725582fa779d91bf415764846ddba374523c4
合同文件         = work/S103_selector_free_baseline/window_scene13_w001_20260916/GATE0_CONTRACT_ADAPTER_BOUND_v11.json
文件 SHA-256     = 81d76b7863a134b57aa5b3a691f2c9c66e13617360c4458d90483019be51cf4d
```

---

## 这次要批准的到底是什么

**一次**运行，跑在 HKUST SuperPOD 的一块 H800 上：

| 项目 | 值 |
|---|---|
| 数据 | RGB-D Scenes v2, scene_13, seq-01（**已暴露的开发数据，不是盲测**） |
| 历史输入 | 4 张 RGB + 4 个位姿，帧 0 / 15 / 30 / 45 |
| 目标 | 帧 60 / 75 / 90 / 105，共 4 个输出 |
| 相机指令 | **就是目标帧的位姿**（数据集估计值）→ 位姿是输入，不是盲的 |
| 模型 | VMem 完整前向，50 步采样，576×576，fp16 计算 / fp32 保存 |
| 随机性 | seed 42，1 次运行，**无重复、无对照臂** |
| 评分 | **仅 RGB** 重建误差（MSE/MAE/PSNR），全像素分母，不排除任何像素 |
| 时限 | 3600 秒 |

**它能证明什么**：VMem 能在受审计的隔离边界内跑通完整前向，并产出可复算的 RGB 重建分数。

**它不能证明什么**：任何 held-out 结果、任何几何结论、任何记忆/选择收益、任何泛化、任何创新。合同里 `claim_boundary` 已写死这句话。

---

## 逐项核对（每项都请你自己判断"我认不认可"）

### 1. 目标位姿是输入 — 你接受吗？
四个 `command_camera` 就是帧 60/75/90/105 的数据集估计位姿。合同 `future_modality_disclosure` 现在明写：
- `target_pose_gt_provided_as_command: true`
- `future_modalities_withheld: ["future_rgb", "future_depth"]`

评分只用 RGB，所以位姿**不会同时既是输入又是答案**（无循环论证）。但这也意味着**永远不能把这次运行称为盲测或 held-out**。

**你要确认的**：你接受"这是相机受控的未来视角生成，不是预测未来相机位姿"这个定位。

### 2. 访问记录现在是真测量 — 你认可这个方法吗？
原来 predictor 里那三个"没碰未来数据"的字段是**写死的常量**（我在审查中发现的 F-1）。现在改成 CPython `sys.addaudithook` 监听 `open` 事件的**实际记录**。
- 碰到项目树 / 数据集根 → 记为 `forbidden_root_opens`，**判失败**
- 碰到白名单外的其它路径 → 只记录不判失败（避免库探测未挂载缓存目录造成假阳性）

**局限（必须接受）**：审计钩子只看 CPython 的文件 API，绕过它的原生代码读不到。所以它**加强但不取代**容器挂载白名单这个主防线。

### 3. 权重身份现在进程内校验 — 够不够？
四个 checkpoint（vmem 5.06GB / cut3r 3.17GB / clip 3.94GB / vae 334MB）在第一次 `torch.load(weights_only=False)` 之前逐个重算 SHA-256 并断言。这关掉了原来"探针作业校验过、正式作业不校验"的跨作业时间窗（F-3）。

### 4. 标定措辞已降级 — 你同意这个说法吗？
`calibration_status` 从 `"verified"` 改为 `"dataset_declared_intrinsics_no_independent_calibration"`，并新增依据字段说明：内参抄自官方发行版，位姿是 RGB-D Mapping 估计值而非动捕真值，本项目**没有**做过独立标定。

**为什么重要**：当初否掉 7-Scenes Chess 就是因为未标定。一个 "verified" 会被将来的人断章取义。

### 5. 隔离边界 — 证据你信吗？
Slurm job **593971**，dgx-21，COMPLETED，exit 0:0，26 秒：
- 项目根目录不可见、数据集根不可见、所有声明的 outcome 路径不可见
- 只读挂载确实只读（写探测全部 `Errno 30`）
- 绑定的 predictor SHA = `d98569c6...`（就是这次要跑的那份）
- H800 CUDA matmul 正常

### 6. 统计范围 — 你接受这个限制吗？（这条最容易出事）
N = 4 帧，1 窗口，1 序列，1 场景，1 个 seed，**没有重复运行**。

**因此：在做过至少 3 次逐字节相同的复放、建立噪声底之前，这个数字不能和任何别的数字比较。** S86 那个负结果之所以能解读，正是因为 A0/A1 逐字节相同把噪声底钉成了 0。

**建议你在复核件的 limitations 里写死这一条。**

### 7. 复核者身份 — 你清楚这意味着什么吗？
- adapter 角色：`claude-session-review-20260917`（AI，就是我）
- protocol 角色：`yliutz-human-review-20260917`（你）

白名单是**你授权**扩的。其它检查一条都没放宽：复核者仍必须不同于作者、必须绑定精确 protocol SHA、必须提供带时区时间戳+逐项证据哈希+全通过检查+findings+limitations。

**必须如实记录**：这是"不同作者复核"，**不是外部独立复现**。

---

## 仍然存在、没有修掉的问题

| # | 问题 | 状态 |
|---|---|---|
| F-4 | 无复放方差包络 | **未修**。属于 post-run 约束，建议写进 limitations |
| — | 审计钩子看不到原生代码的读 | 已在 adapter 复核 limitations 里声明 |
| — | `heldout_exposure_review_ref` / `baseline_acceptance_ref` 仍为 null | 对 development 范围是正确的，但不能忘 |
| — | sealer/scorer 只重审了本次改动路径，未逐行全审 | 已声明 |

---

## 你的决定

只有两种：

- **批准**（`PRE_RUN_APPROVED`）→ 我写复核件记录你的决定，跑验证器，建 bundle，提交 GPU 作业
- **拒绝**（说明理由）→ 不提交，按你的意见继续改

如果批准，请告诉我你要写进 `limitations` 的话（或者用我上面建议的）。**复核件记录的是你的判断，我只是代笔和做哈希计算——这一点会写在复核件里。**
