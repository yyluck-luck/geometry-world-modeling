# 评测与数据规划（2026-09-15 检索结论）

**来源：** 子检索四（数据集与评测）完整报告，含 30 个数据集的逐项核验；本人已对主选序列做**独立复算**（见 `GATE0_TUM_QUALIFICATION_20260915.md`）。
**性质：** 规划文档。**不自行宣布 Gate 0 通过**；正式判定须按 S102 schema 运行。

---

## 1. 核心结论：**2026 给的是"指标"，TUM 给的是"合规数据"——两者要配对使用**

子检索四核实：**2024–2026 年没有任何数据集同时提供"真实拍摄的离开—返回视频 + GT 深度 + GT 位姿 + 真硬件时间戳"。**

回访类 benchmark 要么是**合成**的（MIND / UE5、LoopNav / Minecraft、iWorld-Bench / 模拟器），要么只是**协议**（R2M-Bench、WorldScore）。

**⇒ 策略：指标取自 2026 论文，数据取自 TUM。**

---

## 2. 数据推荐（三档）

### 🥇 主选：TUM RGB-D `freiburg3_*`

**唯一在数据属性上全项通过 Gate 0 的数据集**（本人独立复算，见 `GATE0_TUM_QUALIFICATION_20260915.md`）。直连 HTTP、无需注册、CC BY 4.0。

| 序列 | 字节 | GT 覆盖 | 用途 |
|---|---|---|---|
| **`freiburg3_long_office_household`** | 1,483,556,251 | 87.09 / 87.10 s **全覆盖** | **主选**：大回访闭环（109,280 对） |
| `freiburg3_nostructure_texture_near_withloop` | 781,054,296 | 56.48 / 56.49 s | 闭环 + 纹理丰富 |
| `freiburg3_nostructure_notexture_near_withloop` | 484,772,347 | 37.74 / 37.72 s | 最小闭环选项 |
| `freiburg3_walking_xyz` | 527,550,055 | 28.83 / 28.84 s | **动态人物（陈旧记忆用例）** |
| `freiburg3_sitting_xyz` | 775,406,859 | 42.50 / 42.51 s | 动态人物 |
| `freiburg1_360` | 417,954,230 | 全覆盖 | 360° 转身 |
| `freiburg1_desk` | 344,011,403 | 全覆盖 | 文档称"数个闭环" |
| ~~`freiburg3_long_office_household_validation`~~ | 1,532,741,250 | — | ⚠️ **不带 GT 位姿，不可用于需要位姿的 held-out** |

**建议的 held-out 设计：** 把 `freiburg3_long_office_household` 作为**测试场景**，其余 fr3/fr1 录制作为上下文；切片 mocap 轨迹构造离开—返回用例（结构确实存在）。

**最大风险（已核实）：** 若干 `fr2` 序列的 mocap GT **不覆盖整段录制**。使用任何 TUM 序列前必须核对下载页的 **"Duration" 与 "Duration with ground-truth" 两列**。详细数字见 Gate 0 证据包 §5.2。

### 🥈 次选：Bonn RGB-D Dynamic（用于"真变了" vs "幻觉"的判别）

**唯一同时提供"静态场景 GT"与"动态内容"的真实拍摄数据集**：Leica BLK360 激光扫描的静态环境完整点云（394,109,339 点 PLY ASCII；子采样版 676,032,657 B），**外加** 24 条动态序列（人物操纵箱子/气球）。**正是区分"物体真的变了"与"模型幻觉"所需的基底。** TUM 格式，现有工具可用。

**最大风险：** 官方页面**未声明许可**（`UNVERIFIED`）——这是 Bonn 唯一无法举证的门项。且项目此前在此踩过"缺失传感器 GT 帧"。

### 🥉 第三：ARKitScenes（务实备选）

摩擦最小的真实 RGB-D + 真时间戳：**无协议门槛**、Apple CDN 直连、逐视频 zip（~65 MB）可抽样而不必下 623 GB；真实 LiDAR 毫米深度 + 置信度通道、K 在 `.pincam`、文件名带时间戳、2,257 个子集有激光扫描 `highres_depth` GT。

**最大风险：** 自定义**非商用** Apple 许可（含 700M MAU 条款），可能过不了"许可清楚"这一关；位姿是**估计的 ARKit 位姿而非 GT**。

---

## 3. 必须修正的两条项目旧记录

| 旧记录 | 核实结果 |
|---|---|
| `DynaBench` 数据集"缺失/不完整" | **不存在。**检索无任何证据表明该数据集或 benchmark 存在（作为"不存在"处理，而非"暂时拿不到"） |
| `RTMV-X` | **不存在。**在 RTMV 论文、项目页、HF 及所有检索中均无；**不要引用** |

---

## 4. ⚠️ 建议修订 Gate 0 的一条要求（重要）

**"数据集提供校验和"这条要求按字面是"不可能满足"的。**

子检索四核实：**没有任何数据集同时提供**校验和 + 真时间戳 + RGB-D + 位姿 + 清楚许可。只有 Co3Dv2（完整 SHA-256 清单）、Dynamic Replica、TartanAir（3 条测试轨的 MD5）提供任何校验和；**TUM、Bonn、ScanNet、ScanNet++、ARKitScenes、WildRGB-D 一律不提供**。

**建议改为：**

> ~~"数据集提供校验和"~~ → **"我们在下载时记录校验和清单并固定它"**

否则该门项**在构造上不可满足**，会把所有合规数据都挡在门外。这不是降低标准——**provenance 照样被固定**，只是由我们承担而不是指望数据集发布方。

---

## 5. 记忆评测指标（应采用）

### 5.1 主指标：R2M-Bench 的 MemoryGain / NMR

- **出处：** [arXiv:2608.27328](https://arxiv.org/abs/2608.27328)，代码 <https://github.com/AMAP-ML/R2MBench>，数据 181 MB MIT
- **它解决的问题：** *"首访和回访帧高度相似，不代表模型记住了场景；可能是中间过程几乎没变。"*
- **协议：** 挖掘被命令的离开—返回对；每对与**同一条 rollout 内**两个对照比较——**gap-matched 非回访对**（测一般时间稳定性）与**短程对**（测短时一致性）。回访判据：位置 ≤ τ_pos、yaw ≤ τ_rot、间隔 ≥ max(0.2T, 10)。
- **指标：** `MemoryGain (MG)` = 回访相对 gap-matched 基线的优势；`NMR` = MG 用"短程到基线的动态范围"归一。
- **五个维度：** 外观保真、场景身份、物体身份、局部几何对应、持久状态推理。
- **验证：** Overall NMR 与人类判断 Spearman ρ=0.547（95% CI [0.45,0.63]）；与生成运动的模型内相关 0.072，而原始回访相似度是 0.207——**相对校准移除了大部分慢动作捷径**。
- **落地方式：** 把该协议**移植到 TUM**，那里有真 GT 帧。

### 5.2 辅助：DreamX-World 的 gain-based 回访指标

[arXiv:2606.16993](https://arxiv.org/abs/2606.16993) §5.3。回访对判据：`|θi−θj| ≤ 2°`、`‖ti−tj‖ ≤ 0.1`、间隔 ≥ ⌊0.2T⌋。逐对指标：PSNR、SSIM、LPIPS、DINO-Sim、VPR-Sim、SP-Match（SuperPoint+LightGlue 匹配比）、CLIP-Video。**独立地表达了与 R2M-Bench 相同的洞见**："绝对相似度会被缓慢的相机运动抬高，而非真实记忆"，故所有指标以对非回访基线的**增益**报告。

### 5.3 几何项：经典 ATE / RPE

TUM 官方工具（<https://cvg.cit.tum.de/data/datasets/rgbd-dataset/tools>）：**ATE**（对齐后绝对平移误差 RMSE，米）适合测**全局闭环/配准误差**；**RPE** 适合测**漂移**。

**⇒ 与上面的回访选择性协议配对使用**，使"记住了这个地方"是相对**同 rollout 基线**测量的。

### 5.4 其他可借

- **MIND**（[2602.08025](https://arxiv.org/abs/2602.08025)）的 `L_mem` / `L_lcm` 与动作精度（ViPE 恢复轨迹 + Sim(3) Umeyama 对齐）
- **MBench**（[2606.00793](https://arxiv.org/abs/2606.00793)）的 M-Score = 关系一致性与触发覆盖率的调和平均——**明确惩罚"什么都不生成以求一致"的退化解**
- **LoopNav**（[2505.22976](https://arxiv.org/abs/2505.22976)）的 A→B→A 协议与 SGCS；含**合成扰动验证**（颜色/平移/旋转/尺度/删物体/换位），可作为自建指标的验证模板

---

## 6. 磁盘

推荐项全部 **< 6 GB**（全部 TUM ≈ 88.6 GB）。**放不下**的：ScanNet 1.2 TB、ScanNet++ 1.5 TB、DL3DV 730 GB–44 TB、MBench 678 GB、iWorld-Bench 970 GB、LoopNav 775 GB、PointOdyssey 185 GB、RTMV 675 GB。

⚠️ **大文件应暂存本地卷而非共享 NFS**（`/tmp` 有 381 GB 可用）。家目录 NFS 仅 162 GB 可用。

---

## 7. 边界

1. 本文是**检索与规划**，不是数据资格判定；Gate 0 正式判定须按 S102 schema 运行。
2. 主选序列的时间戳/配对/覆盖/闭环数字由**本人独立复算**；其余数据集的具体数字来自子检索四，**本人未逐个复算**。
3. TUM 的**许可与内参条款正文本人未逐字复核**（来自子检索）。
4. 未解码任何图像像素；0 次模型调用。
5. 所引用论文中，部分为预印本，**同行评审状态未核实**；其主张按"论文声称"记录。

**原始报告：** [`innovation_scan/memory-world-model-survey.md`](innovation_scan/memory-world-model-survey.md)（30 数据集对照 + 评测指标 + 查询清单）、[`innovation_scan/dataset-verification-report.md`](innovation_scan/dataset-verification-report.md)（10 个真实拍摄数据集的字节级核验）。
