# 复核问题 × 领域实际做法：原始来源对照（2026-09-17）

为回答"顶会论文到底怎么做"，对人工复核清单的 7 项逐条检索原始来源。所有引用均来自实际抓取的
论文全文或会议官方页面，不是记忆或转述。抓取脚本与原文缓存在 `/tmp/gwm_innov_scan/`、
`/tmp/vmem.txt`、`/tmp/sober.txt`（临时目录，非仓库产物）。

本文只回答"领域怎么做"，**不改变任何科学状态**：`new_method_validated=false`,
`novelty_authorization=NONE`。

---

## ① 目标位姿作为输入 — 领域做法：这是标准，而且本项目用的 VMem 自己就这么做

**决定性证据（VMem 原论文，arXiv 2506.18903v3，Li/Torr/Vedaldi/Jakab）：**

> "Beginning from the first frame of each ground-truth test sequence, the model autoregressively
> generates images **along the ground truth camera trajectories** with 10-frame intervals."

同一篇论文把任务本身定义为：

> "We evaluate our method on established benchmarks for **camera-conditioned** autoregressive view
> generation from a single image."

以及对问题设定的描述：

> "the user tells the model which camera path to follow"

**结论**：把真值相机轨迹交给模型是这条线的**标准评测协议**，不是缺陷。本项目 `command_camera`
= 目标帧位姿的做法与 VMem 原论文一致；`M = 4 target views` 也与 VMem 的配置（M=4）一致。

**但是**：VMem 论文里这件事只写在 Experiments 正文一句话里，没有机器可读声明。本项目 v11 合同的
`future_modality_disclosure` 把它变成验证器强制检查的结构化字段，**严于领域常规**。

**对复核的意义**：①不是"要不要接受一个缺陷"，而是"确认采用领域标准协议并显式声明"。可以接受。

---

## ② 访问/泄漏审计 — 领域做法：视觉生成论文基本不做；相关实践在 LLM 侧

检索 `sandbox + evaluation + container/isolation + benchmark` 返回的全部是 **LLM agent 安全**
方向（HarnessRisk 2608.17597、SkillAtlas 2609.13353、Thinkingbox 2608.19741 等），
**没有**一篇是"视觉/视频生成评测的运行时泄漏隔离"。

LLM 侧确实把污染当成一等问题：
- *Search-Time Data Contamination*（2508.13180）："Data contamination refers to the leakage of
  evaluation data into model training data, resulting in overfitting to supposedly held-out test
  sets and **compromising test validity**."
- *Test Set Contamination in LLMs for Speech Recognition*（2505.22251）发现 LibriSpeech/
  Common Voice 有大量泄漏。
- *The Poisoned Chalice of LLM Evaluation*（2607.07481）："the validity of these evaluations is
  often undermined by uncertainty about whether benchmark instances were seen during pretraining."

**结论**：把未来 GT 的可达性做成**容器挂载白名单 + 运行时 open 事件审计**，在视觉生成方向
**找不到先例**。本项目在这一项上**显著高于领域常规**。

**对复核的意义**：F-1 修复（常量→真测量）不是补短板，是把已经超出常规的做法做实。审计钩子
只覆盖 CPython 文件 API 这个局限必须写进 limitations——但即便如此仍高于同行。

---

## ③ 权重哈希 / 可复现 — 领域做法：会议要求"可复现路径"，不要求哈希

**NeurIPS Paper Checklist 官方原文**（neurips.cc/public/guides/PaperChecklist）：

> "While NeurIPS **does not require releasing code**, we do require all submissions to provide some
> reasonable avenue for reproducibility... release of a model checkpoint, or other means that are
> appropriate to your research."

没有任何一条要求 checkpoint 的 SHA-256 或加载时校验。

**结论**：F-3（进程内重算 12.5GB 权重哈希后才 `torch.load`）**远超**会议要求。

---

## ④ 标定措辞 — 领域做法：有专门论文证明"参考算法即真值"会扭曲结论

**决定性证据：Brachmann, Humenberger, Rother, Sattler,
*On the Limits of Pseudo Ground Truth in Visual Camera Re-localisation*, ICCV 2021
（arXiv 2109.00524）**：

> "To obtain poses for thousands of images, it is common to use a reference algorithm to generate
> **pseudo ground truth**. Popular choices include Structure-from-Motion (SfM) and
> Simultaneous-Localisation-and-Mapping (SLAM) using additional sensors like depth cameras...
> Re-localisation benchmarks thus measure **how well each method replicates the results of the
> reference algorithm**."

> "evaluation outcomes indeed **vary with the choice of the reference algorithm**. We thus question
> common beliefs in the re-localisation literature, namely that learning-based scene coordinate
> regression outperforms classical feature-based methods, and that RGB-D-based methods outperform
> RGB-based methods."

> "any claims on ranking... should take **the type of the reference algorithm, and the similarity
> of the methods to the reference algorithm, into account."

RGB-D Scenes v2 的位姿正是 **RGB-D Mapping（一种 SLAM/重建参考算法）估计值**，与该论文所指的
pseudo ground truth 完全同类。而本项目 pipeline 里还用了 CUT3R（同样做几何估计），存在
"方法与参考算法同源"的相似性风险，正是该论文警告的情形。

**结论**：把 `calibration_status` 从 `"verified"` 改成
`dataset_declared_intrinsics_no_independent_calibration` + 书面依据，**有顶会论文直接支撑**，
不是过度保守。这一项我此前的建议**偏弱了**——应当在结果文档里进一步写明"评的是与 RGB-D
Mapping 参考算法的一致性，不是与物理真值的一致性"。

---

## ⑤ 隔离边界证据 — 领域做法：没有先例

同 ②。视觉生成论文不提供 Slurm 作业级的隔离回执。本项目的 `EXACT_BOUNDARY_PROBE_PASS`
（job 593971）在领域内**没有对应实践**。

**对复核的意义**：这一项不存在"领域怎么做"的参照，只能按自身标准判断；证据本身是完整的。

---

## ⑥ N=4、单 seed、无复放 — 领域做法：⚠️ 这一项本项目**低于**已知最佳实践，且有量化证据

这是唯一一项检索结果**加重**而非减轻担忧的。

### 会议官方要求

**NeurIPS Paper Checklist — Experiment Statistical Significance**：

> "The authors should answer 'Yes' if the results are accompanied by error bars, confidence
> intervals, or statistical significance tests, **at least for the experiments that support the
> main claims**... The factors of variability that the error bars are capturing should be clearly
> stated (for example, train/test split, **initialization, random drawing of some parameter, or
> overall run with given experimental conditions**)."

同时明确允许拒绝并说明理由：

> "it is perfectly acceptable to answer 'no' provided a proper justification is given
> (e.g., '**error bars are not reported because it would be too computationally expensive**')"

**Limitations 条目**还特别点名小样本：

> "The authors should reflect on the scope of the claims made, e.g., if the approach was only
> tested on **a few datasets or with a few runs**."

### 量化证据：小样本 + 单 seed 有多危险

**Hochlehnert et al., *A Sober Look at Progress in Language Model Reasoning*, COLM 2025
（arXiv 2504.07086v2）**，20 次独立运行 × 9 个模型：

> "Pass@1 values show surprisingly high standard deviation—**ranging from 5 to 15 percentage
> points across seeds**. This issue is particularly severe for AIME'24 and AMC'23, which have
> only **30 and 40 test samples** respectively. A change in just one question shifts Pass@1 by
> **2.5–3.3 percentage points**."

> "**Takeaway 1: Single-seed evaluations on small datasets are highly unstable. Accurate reporting
> requires averaging over multiple seeds.**"

> "**Takeaway 2: Small benchmarks like AIME'24 (30 samples) yield unreliable comparisons**—
> single-question differences shift Pass@1 by 3%, making rankings unstable when models cluster
> around similar performance levels."

结论性图注：

> "the observed improvements from recent methods fall **entirely within the variance range** of
> DeepSeek-R1 1.5B model performance. This suggests that these methods **do not significantly
> outperform the base model**."

他们采用的标准：小基准（30–40 样本）**平均 10 个 seed**，MATH500（500 样本）平均 3 个 seed。

### 更坏的消息：固定 seed 也挡不住硬件差异

同一篇论文第 3 阶段实验：

> "Suspecting non-deterministic GPU operations, we enforced strict determinism by setting
> `torch.use_deterministic_algorithms(True)`, fixing CUDA seeds, and disabling cuDNN benchmarking.
> Comparing A100 and H100 clusters, **variance decreased but persisted**: OpenThinker2-7B scored
> 53.0% ±4.6 on A100 versus 57.1% ±5.2 on H100."

> "Despite identical hardware specifications and containerized environments, we observed notable
> performance differences... a **4 percentage point gap that exceeds the standard deviation**."

**直接命中本项目**：本项目的作业分别落在 **dgx-09、dgx-21、dgx-27** 三个不同节点上
（sacct 记录：589823/589826→dgx-09，590696→dgx-27，591500/593971→dgx-21）。Slurm 不保证下次
调度到同一节点。因此"seed 42 固定 ⇒ 可精确复放"这个假设**在跨节点时未经验证**。

### 对比：VMem 论文自己也没报 error bar

VMem 的 Table 1/2/3 全部是单值（LPIPS/PSNR/SSIM/FID/Rdist/Tdist），无 ±、无 seed 说明。
即领域常规确实宽松。

**但是**：VMem 的测试集是 RealEstate10K / Tanks-and-Temples 的**多条序列**，本项目是
**4 帧、1 序列、1 场景**。AIME'24 的 30 样本已被称为 "unreliable comparisons"，本项目是 4。

**对复核的意义（这是最重要的一条）**：
- 作为**跑通性验证**（development baseline）：完全没问题，N=4 足够。
- 作为**任何比较的基准**：证据明确显示不可以。必须先建立复放包络，**且包络必须在同一节点类型上
  测**，否则跨节点方差会被误读成方法效应。
- 建议 limitations 措辞应比我原先的更强：不只是"建议先做复放"，而是
  **"跨节点复放方差未知；在同节点 ≥3 次逐字节复放包络建立之前，本数值不得与任何其他数值比较"**。

---

## ⑦ 复核者身份 / AI 参与复核 — 领域做法：允许但强制披露、责任归人

**ICLR 2026 Reviewer Guide 官方原文**（iclr.cc/Conferences/2026/ReviewerGuide）：

> "**The Use of Large Language Models (LLMs).** The use of LLMs is allowed as a general-purpose
> writing assistance tool. However, reviewers should understand that they **take full
> responsibility for the contents written under their name**, including content generated by LLMs
> that could be construed as plagiarism, scientific misconduct, or low quality (e.g., **fabrication
> of facts**)."

> "new this year, we **mandate that reviewers disclose the use of LLMs in their reviews**. The
> review form will include a field to specify how you used LLMs, if at all. **Failing to disclose
> this usage may put the reviewers' papers at risk for desk rejection**."

对作者侧同样要求：

> "we are asking that authors **disclose any significant usage of LLMs in research
> ideation/writing**."

arXiv 侧亦印证 LLM 已广泛用于 pre-submission self-review（2609.09076、2609.05788），但定位是
**author-facing 自查**，不是同行评审替代品。

**结论**：本项目的做法（人类 = protocol 复核者并承担责任；AI = adapter 复核者且在复核件里写明
身份与局限）**与 ICLR 2026 的明文要求一致**：允许 AI 参与、**责任归署名者**、**必须披露**。

**对复核的意义**：⑦ 是合规的，前提是复核件里如实写明 (a) 哪些核查由 AI 执行，(b) 决定由人做，
(c) 这是 different-author review 而非 independent reproduction。这三句缺一不可。

---

## 汇总：本项目相对领域常规的位置

| 项 | 领域常规 | 本项目 | 判断 |
|---|---|---|---|
| ① 目标位姿作输入 | VMem 等标准做法（给 GT 轨迹） | 同做法 + 机器可读强制声明 | **严于常规** |
| ② 泄漏审计 | 视觉侧无先例 | 挂载白名单 + open 事件审计 | **无先例，远严于常规** |
| ③ 权重哈希 | 会议不要求 | 进程内 12.5GB 重算后加载 | **远严于常规** |
| ④ 标定措辞 | 普遍含糊；有 ICCV 论文专门警告 | 已降级为自限值 + 书面依据 | **符合该警告，可再强化** |
| ⑤ 隔离回执 | 无先例 | Slurm 作业级回执 | **无先例** |
| ⑥ **样本量/seed** | VMem 无 error bar；但测试集是多序列 | **N=4、1 场景、1 seed、0 复放** | ⚠️ **低于最佳实践** |
| ⑦ AI 参与复核 | ICLR 2026 允许但强制披露、责任归人 | 人类担责 + AI 披露 | **合规** |

**一句话**：七项里六项本项目做得比领域常规严，唯独第 ⑥ 项（统计范围）是真实短板，而且检索到的
证据比我原先估计的更严重——因为它同时暴露了"跨节点复放方差未知"这个此前没被记录的风险。

---

## 由此产生的、原复核清单中没有的新建议

**N-1（新增，建议纳入 limitations）**：复放包络必须在**同一节点类型**上测量。现有 sacct 记录
显示作业已分散在 dgx-09/21/27；`A Sober Look` 证明即使强制确定性算法，跨硬件仍有超过标准差的
系统性差异。因此 F-4 的表述应从"≥3 次逐字节复放"加强为"**同节点 ≥3 次复放建立包络，另测
跨节点差异并单独报告**"。

**N-2（新增，建议纳入结果文档）**：依据 Brachmann et al. ICCV 2021，本次评分应表述为
"与 RGB-D Mapping 参考算法结果的一致性"，而非"与真实几何的一致性"；且因 pipeline 含 CUT3R
（同为几何估计方法），需声明存在"方法与参考算法同源"的相似性偏置风险。

**N-3（观察，不阻塞）**：本项目在 ②③⑤ 三项上的做法在视觉生成方向没有先例。这本身可能是可发表的
**方法学/评测协议贡献**，但必须先有真实实验结果支撑，不能以"流程严格"本身充当科学贡献。
`novelty_authorization=NONE` 不变。
