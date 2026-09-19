# Round 14-C：Reset-semantics audit 的占用核查（2026-09-19）

本文件只回答占用问题，不提出新方向、不排序、不作 funding 或 method verdict。结论区分了三种证据：仓库源码静态核对、已发表论文的原文核对、以及本轮检索范围内没有找到的东西。对“没有找到”的表述均是 **search-bounded negative**，不把有限检索写成全世界不存在。

## 先给四个问题的答案

**Q1 — defect-class claim：在本轮核实的文献中没有找到已发表的等价 claim。** 我没有找到一篇工作同时把下面这件事作为跨系统 defect class 来声明并给出 prevalence：released、stateful、generative/video/world-memory systems 存在 incomplete reset/state-isolation semantics，且缺陷是“一个路径写入实例状态，另一条路径在自己的写入未触发时读取，生命周期 reset/initialize 不清除”，最后在多个 released systems 上报告 `M/N` 并给出 frozen-weight 行为后果。

最近邻 [**Persistent Computational State: A Session-Centric Runtime for Generative World Models**（arXiv:2607.21686）](https://arxiv.org/abs/2607.21686) 确实在 Cosmos3、WorldMem、Matrix-Game 2.0 三种模型上做了状态恢复实验，但它把问题归因于 request-centric **serving/runtime** 丢弃模型运行时状态，贡献是 PCS、checkpoint/restore/fork 和 session-centric runtime；它没有审计 released model implementation 内部的 `reset()`/`initialize()`，没有跨 released repositories 统计 reset defect prevalence，也没有报告候选的“branch-A write → guarded branch-B read → reset omission”实例。因此它是相邻的 runtime-state work，不是本 claim 的已占用证据。

**Q2 — audit predicate：没有找到等价的五条件 static + dynamic predicate；但组成部件分别已有很强的邻居。** 软件工程中 test pollution/order-dependence 已经有成熟的动态检测和修复工作；ML/DL bug studies 已经有广泛 taxonomy；视频/world-model 文献已经有 memory/state 行为 benchmark。它们没有把这些部件组合成“released generative model class 的 documented lifecycle/reset audit + 跨仓库 prevalence + frozen-weight consequence”。

**Q3 — 本轮仍未占用的交集可以准确写成：**

> 在本轮核实的文献范围内，尚未见一种可迁移到新 released stateful generative repository 的、明确检查“跨调用路径实例状态写入/条件保护读取/公开 reset 或 initialize 未清除/公共 API 序列可达/冻结权重行为差异”的静态加动态审计谓词，并将其应用到多个 releases 后报告该 defect class 的 `M/N` prevalence。

这是一条**占用缺口陈述**，不是“创新已成立”的宣称。它还没有证明审计协议可跨实现工作，也没有证明任意一个具体 `M/N`。

**Q4 — 最强结构性反对意见：审稿人会把它视为 test-pollution/order-dependence 的跨域改名，除非证明模型生命周期语义带来了不可约的新对象和新证据。** 现有 PolDet、PRADET、ODRepair、NIO 等工作已经处理了共享状态被一个测试写入、后续调用读取、清理不完整以及行为差异；它们还报告了真实项目中的 prevalence 和修复结果。若新工作只有一个 VMem code path、没有第二个 released consumer、没有 held-out repository、没有公开 lifecycle contract、没有跨系统 `M/N`，审稿人可以认为“一个已知状态污染 bug 加一个行为复现”。更尖锐的语义问题是：没有明确的 reset/initialize contract 时，“该字段没有清除”不自动等于 defect；它可能是有意持久化状态。候选审计必须证明该字段按公开生命周期语义**应当**被清除，而不是仅仅没有出现在某个函数体内。

## 仓库源码核对：哪些事实成立，哪些不能混写

### 三份 pinned VMem 源码

以下三份文件在本轮逐段核对，且三者 SHA-256 都是 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`，`cmp` 两两一致：

- `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`
- `work/S17_cpu_preflight/original/modeling/pipeline.py`
- `work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py`

用户指定的三行逐字命中：

- `pipeline.py:1249`：`get_context_info(target_c2ws, use_non_maximum_suppression)`；
- `pipeline.py:1263`：`torch.cat([context_c2ws, target_c2ws])`；
- `pipeline.py:1265`：`get_translation_scaling_factor(all_c2ws)`。

`self.c2ws` 的精确事实是：

- `pipeline.py:180`：`self.c2ws = [c2w]`；
- `pipeline.py:1297`：`self.c2ws.append(...)`；
- `pipeline.py:1360`：`self.c2ws.pop()`，这是删除，不是 setter/relabel/update；
- 没有发现命名为 setter 或等价的相机标签重写接口。

所以“只有两个创建/追加写入点、没有 setter”是准确的；但“`reset()` 不清 `c2ws`”不能单独作为 stale-state 证据：`initialize()` 在 `pipeline.py:162–163` 调 `reset()` 后，于 `:180` 直接重建 `self.c2ws`。这也是为什么 T1-5 的**接口可行性结论**可以成立，而不能把 `c2ws` omission 直接写成跨 initialize 的泄漏。

### 真正形成候选五条件链的字段是 `initial_threshold`

在同一 pinned source 中，静态链如下：

1. **写入路径 A。** NMS 关闭时，`pipeline.py:704–705` 无条件写 `self.initial_threshold = 1e8`。
2. **另一条读取路径且自身写入有守卫。** NMS 开启时只有 `is_second_step = (len(self.pil_frames) == 5)` 的分支（`:674`, `:681–700`）才重写该属性；随后 `:708` 无条件读 `current_threshold = self.initial_threshold`。
3. **reset omission。** `reset()`（`:135–146`）清理多组列表和 `global_step`，没有清理 `initial_threshold`。
4. **公共 API 可达性（静态）。** `navigation.py:185/187` 和 `:234/236` 的 move 路径显式传 `use_non_maximum_suppression=False`；`navigation.py:321` 的 turn 路径不传该参数，进入 `pipeline.py:1318` 的默认 `None`，再在 `:678–679` 解析为配置值。因而“先两次 move，再 turn”的混合调用序列在源码控制流上可达。
5. **冻结权重的行为后果。** 本轮没有运行 demo，也没有把静态可达性写成已测量输出。因而该条件在本仓库证据中是 **UNVERIFIED（动态行为）**；已核实的是 source-level path reachability。项目技术报告也明确把它标为静态 reachability，而非 demo measurement。

这一区分很重要：源码已经足以支持“有一个具体的 released VMem state-handling defect candidate”，不足以支持“该 defect class 在多个系统中的 prevalence”。

## 最近邻一：2607.21686 的全文判定

我按要求读了论文的 arXiv HTML 和 29 页 PDF。书目信息是：Zhen Lin, **“Persistent Computational State: A Session-Centric Runtime for Generative World Models”**, arXiv:2607.21686v1, DOI [10.48550/arXiv.2607.21686](https://doi.org/10.48550/arXiv.2607.21686), [arXiv URL](https://arxiv.org/abs/2607.21686)。

逐项回答：

| 用户问题 | 原文位置与核对结果 | 与候选五条件的关系 |
|---|---|---|
| (a) 模型实现内部 defect，还是 serving/runtime？ | §1.2–§2（PDF pp.3–5；HTML §§1.2–2）把 failure 写成 runtime 在 request boundary 丢弃 observation/RNG、memory bank 或 KV context；§8（p.23）通过五方法 adapter (`initial_state`, `step`, `capture`, `restore`, `embed`) 接入真实模型。§3 的 boundary 把 model code/RNG source 留在 framework，论文层是 serving/runtime。 | 不是对 released model class 内部写读路径的源码审计。 |
| (b) audit/detection predicate，还是 runtime design？ | §4（pp.7–8）给出 `Fingerprint(M,D,ε,probe)`：对可寻址 runtime buffers 做 necessity/sufficiency/redundancy ablation；§5 构建 session runtime；§6 给 checkpoint→leave→restore→continue 的 return-consistency conformance test。 | 这是动态 PCS fingerprinting/conformance，不是 static source audit，也不检查 reset/initialize completeness。 |
| (c) reset/initialize completeness？ | 全文未发现模型类 `reset()` 审计；全文的 “initialize” 只在 §7.2（p.12）出现为重新初始化 CUDA 的进程语境。 | 没有候选条件 3。 |
| (d) exact predicate instance？ | 未报告“branch A 写 attribute、branch B 条件读取、reset 未清除”的实例。§7.1–§7.2 的三模型结果是 PCS 组成和 byte-identical restore，不是 stale instance attribute。 | 没有候选五条件组合。 |

因此 2607.21686 **没有占用 Q1 的 defect-class claim，也没有占用 Q2 的 audit predicate**。它占用的是相邻问题：如何测量和持久化 serving 层的不可重算状态。其 `snapshot completeness`（§3, I4）不能改称 `reset completeness`；其 return-consistency test（§6）不能改称 reset audit。

## 软件工程、MLOps 与 DL bug 文献的距离

### 直接的 test state-pollution 邻居

- [**“Reliable Testing: Detecting State-Polluting Tests to Prevent Test Dependency”**](https://doi.org/10.1145/2771783.2771793), ISSTA 2015。PolDet 在测试前后比较共享 heap/file-system 状态，寻找污染测试；其动机包括一个测试改写共享字段、后续测试读到旧值、fixture 没有在每次 test 前重置。它是候选 predicate 的最接近软件工程先例之一，且有真实项目统计；但对象是测试套件的共享状态，非 released generative-model instance，未检查 guarded branch，也不需要 documented model reset contract。
- [**“Practical Test Dependency Detection”**](https://doi.org/10.1109/ICST.2018.00011), ICST 2018。PRADET 以 data-flow/dynamic execution 检测 test dependencies，并报告未知依赖。它仍以测试顺序依赖为对象，不扫描模型类的 reset/initialize 语义。
- [**“Repairing Order-Dependent Flaky Tests via Test Generation”**](https://doi.org/10.1145/3510003.3510173), ICSE 2022。ODRepair 根据 passing/failing test orders 定位 heap/static-state pollution，再搜索 cleaner/reset method 并生成修复。它与“行为差异 + 清理缺失”很接近，但前提是已有 order-dependent victim/polluter；没有对 released model repositories 做静态生命周期审计，也没有候选的 guarded-read 条件。
- [**“Preempting Flaky Tests via Non-Idempotent-Outcome Tests”**](https://doi.org/10.1145/3510003.3510170), ICSE 2022。NIO 检测同一 test 在同一环境第一次 pass、第二次 fail 的 self-pollution，并在 Java/Python 项目中报告 prevalence。它说明“同一对象重复调用的状态污染”已是有名且规模化测量的概念；但仍是 test object，不是 released stateful video/world model，也不审计 documented reset path。
- [**“An Empirical Analysis of Flaky Tests”**](https://doi.org/10.1145/2635868.2635920), 2014。该工作把 test-order dependency 与 shared state 联系起来；后续综述报告其研究样本中 12% 属于 order dependency、其中许多通过清理共享状态修复。它进一步强化了“单纯写入/读取/清理缺失”本身不能作为跨域新颖性。

这些工作已经占据“共享状态污染导致后续调用结果变化”的一般软件工程轴，但没有占据本候选的**对象范围、公开 model lifecycle、跨 released repositories 的 defect prevalence 和 frozen-weight consequence**的联合交集。

### ML 测试与 DL bug studies

还有三篇更接近“stateful deep-learning testing”的工作，但它们审计的是神经网络隐藏状态的行为模型，而不是 Python/服务对象的 lifecycle 字段：

- [**“DeepStellar: Model-Based Quantitative Analysis of Stateful Deep Learning Systems”**](https://doi.org/10.1145/3338906.3338954), ESEC/FSE 2019。它把 RNN 的 hidden-state 行为抽象为 DTMC，定义 trace-similarity metrics 和 coverage criteria，并对四个 stateful DL systems 做 guided/adversarial testing。它没有检查 `reset()`/`initialize()` 完整性、跨 public call path 的实例属性读写或 released-repository prevalence。
- [**“DeepCruiser: Automated Guided Testing for Stateful Deep Learning Systems”**](https://arxiv.org/abs/1812.05339), arXiv:1812.05339，DOI [10.48550/arXiv.1812.05339](https://doi.org/10.48550/arXiv.1812.05339)。它自动构造 RNN state-transition abstraction 并按 stateful coverage 引导测试；state 指的是 recurrent hidden state，不是 model object 的 stale attribute，也没有 reset contract audit。
- [**“Marble: Model-based Robustness Analysis of Stateful Deep Learning Systems”**](https://doi.org/10.1145/3324884.3416564), ASE 2020。它用 MDP 对 RNN hidden states 做 robustness analysis，并在六个 RNN 上评测；没有候选五条件中的 source-path、documented reset 或 released-system prevalence。
- [**“Machine Learning Testing: Survey, Landscapes and Horizons”**](https://arxiv.org/abs/1906.10742), arXiv:1906.10742。该 survey 综述 144 篇 ML-testing 工作，并按 workflow、properties、components 和 application scenarios 组织；其 component/测试轴没有形成 instance-state isolation 或 reset-completeness 这一类。因此它是对广泛 ML-testing literature 的负向覆盖证据，而不是候选 predicate 的先例。

- [**“Detecting Flaky Tests in Probabilistic and Machine Learning Applications”**](https://doi.org/10.1145/3395363.3397366), ISSTA 2020。研究 Pyro、PyMC3、TensorFlow Probability、PyTorch 的 75 个 flaky-test reports/commits，并用 FLASH 通过重复运行检测随机数序列导致的 assertion flakiness；这是 ML-specific testing，但处理的是 algorithmic nondeterminism / unsynchronized randomness，不是 stale instance state 或 reset omission。
- [**“Taxonomy of Real Faults in Deep Learning Systems”**](https://arxiv.org/abs/1910.11015), ICSE 2020，DOI [10.1145/3377811.3380395](https://doi.org/10.1145/3377811.3380395)。论文分析 1059 个 GitHub/Stack Overflow artifacts、访谈 20 位实践者，并用 21 位开发者验证 taxonomy。其顶层是 Model、Tensors & Inputs、Training、GPU Usage、API 等；即使包含广义 state-sharing/initialization 语义，也没有把 incomplete reset/stale instance state 作为命名 defect class，更没有该类的 prevalence 数字。
- [**“A Comprehensive Study on Deep Learning Bug Characteristics”**](https://arxiv.org/abs/1906.01388), ESEC/FSE 2019，arXiv:1906.01388。它挖掘 2,716 个 Stack Overflow posts 和 500 个 GitHub bug-fix commits，分类中有 broad `Initialization Bug` 与 `Control and Sequence Bug`；这些不是 lifecycle reset、stale instance-state 或跨调用 write/read predicate，因此其 prevalence 不能被重用为本候选类的 prevalence。
- [**“The symptoms, causes, and repairs of bugs inside a deep learning library”**](https://doi.org/10.1016/j.jss.2021.110935), Journal of Systems and Software 2021。它对 TensorFlow library bug 做系统研究，给出症状、根因和修复模式；没有候选五条件的 model-instance reset audit。
- [**“An Empirical Study on Bugs Inside PyTorch: A Replication Study”**](https://arxiv.org/abs/2307.13777), arXiv:2307.13777。它按 PyTorch bugs 的 causes/symptoms/fix patterns 做复制研究；本轮全文搜索没有发现把 reset omission/stale instance state 命名为类别。它因此不能提供候选 defect class 的 prevalence。
- [**“An Empirical Study on the Bugs Found while Reusing Pre-trained Natural Language Processing Models”**](https://arxiv.org/abs/2212.00105), arXiv:2212.00105。该文从 9,214 issues 得到 984 bugs 并建立 taxonomy，重点是黑盒复用、输入/API/resource 等问题；不是模型实例生命周期审计。
- [**“Towards Enhancing the Reproducibility of Deep Learning Bugs: An Empirical Study”**](https://arxiv.org/abs/2401.03069), arXiv:2401.03069。研究 668 个 DL bugs，抽样尝试复现 165 个并成功复现 148 个，贡献是 reproduction information/edit actions；它不是 reset/state-isolation audit。

因此，对“经验 bug study 已否把 incomplete reset/stale instance state 作为带 prevalence 的命名类别？”的答案是：**本轮核实到的 studies 没有这样做。** 它们占据了“DL bugs 可以被 taxonomy 化和统计”的方法先例，却没有占据本候选类别。

### 另一个跨域系统审计先例

[**“Automatic Reliability Testing For Cluster Management Controllers”**](https://www.usenix.org/conference/osdi22/presentation/sun), OSDI 2022（Sieve）对 Kubernetes controllers 注入 intermediate/stale/unobserved cluster states，用 differential oracles 比较行为，并在多个 controllers 上发现 serious bugs。它证明“预先规定状态扰动 + 行为 oracle + 多系统统计”可以成为系统 artifact；但其 stale state 是 controller/cluster state injection，不是 released generative-model class 的 reset/initialize completeness。因此它是审计工程的强邻居，不是本 claim 的占用。

## 视频 / world-model memory 文献：测能力，不审计 reset

以下三篇都直接测“离开视野后世界状态是否保持”，但原文的对象是生成视频行为和 benchmark，不是 released model implementation 的 lifecycle source：

- [**“Current World Models Lack a Persistent State Core”**](https://arxiv.org/abs/2606.20545), arXiv:2606.20545，WRBench：23 models、9,600 videos；camera intervention 后检查 re-observed state consistency。论文 §3–§4 的 artifact 是 benchmark/toolkit/human calibration，没有 reset audit。
- [**“MBench: A Comprehensive Benchmark on Memory Capability for Video World Models”**](https://arxiv.org/abs/2606.00793), arXiv:2606.00793；定义 entity/environment/causal consistency 和 12 个子维度，评测长期 memory capability。它没有 branch-level source audit。
- [**“MemoBench: Benchmarking World Modeling in Dynamically Changing Environments”**](https://arxiv.org/abs/2606.27537), arXiv:2606.27537；360 个 synthetic/real ground-truth clips，Visible–Disappear–Reappear，检查动态状态回归。它没有 reset/initialize completeness 检查。
- [**“MIND: Benchmarking Memory Consistency and Action Control in World Models”**](https://arxiv.org/abs/2602.08025), arXiv:2602.08025；250 个闭环视频，测 memory consistency 与 action control。它仍是行为 benchmark，不检查 released implementation 的 instance-field lifecycle。
- [**“Do Video Generators Track the World Across Segments? A Benchmark and Method for World-State Reasoning in Video Continuation”**](https://arxiv.org/abs/2609.03673), arXiv:2609.03673；StateBench 测 past-visible、occluded-process 和 complex-transition states，并提出 StateAgent。它是 benchmark + continuation method，未审计 reset/initialize 或跨调用 stale state。

另一个概念性 benchmark 是 [**“The Trinity of Consistency as a Defining Principle for General World Models”**](https://arxiv.org/abs/2602.23152), arXiv:2602.23152（CoW-Bench）；它讨论 modal/spatial/temporal consistency，不是 implementation audit。以上工作共同说明：视频 memory/state 行为评价这条轴已经很活跃，但“行为失败来自模型能力还是 serving/lifecycle defect”仍不能由 benchmark 单独回答。

## 为什么 algorithmic unit tests 和 rliable 不是同一件事

- [**“Reproducibility in Multiple Instance Learning: A Case For Algorithmic Unit Tests”**](https://arxiv.org/abs/2310.17867), NeurIPS 2023，DOI [10.48550/arXiv.2310.17867](https://doi.org/10.48550/arXiv.2310.17867)。它用 synthetic datasets 预先编码 MIL 的因果/不对称假设，以 model-agnostic algorithmic unit tests 发现五个模型违反假设。它是“可迁移行为单元测试 + 多模型统计”的直接 artifact 先例；但 predicate 检测的是数学任务假设，不是源码写读路径、reset completeness 或 public API reachability。
- [**“Deep Reinforcement Learning at the Edge of the Statistical Precipice”**](https://arxiv.org/abs/2108.13264), NeurIPS 2021，DOI [10.48550/arXiv.2108.13264](https://doi.org/10.48550/arXiv.2108.13264)。它提出 interval estimates、performance profiles、IQM 和开源 `rliable`，把 evaluation uncertainty 变成可复用方法。它说明“protocol + reusable software/data + statistically honest reporting”可以构成贡献；但其对象是 run-level statistical uncertainty，不是 instance-state isolation。

这两篇回答的是“什么样的检测协议能够成为 artifact”，不是“候选五条件 predicate 已经被占用”。

## 证据边界与 UNVERIFIED 项

1. 本轮对三份 pinned VMem copies 做了本地逐行和字节一致性核对；**没有在本轮重新从远端 GitHub 下载 public HEAD**。因此“pinned copies 等于某个当前远端 commit”的远端状态在本文件中标为 **UNVERIFIED（本轮未重拉）**，不能把它当成新网络证据。
2. `initial_threshold` 的 branch/read/reset omission 和 navigation reachability 是静态源码事实；**demo 的实际视觉/数值差异本轮未运行，标为 UNVERIFIED**。不要把它写成论文 benchmark 数字已被污染。
3. “没有找到等价文献”是截至本轮检索的范围性负结果；它不等于逻辑证明不存在。尤其不能把未检索到的 proprietary serving code 或未公开作者评测脚本当作已审计。
4. 2607.21686 的三模型状态恢复结果是论文报告的 frozen-model/runtime experiments；本轮没有重新执行其 Cosmos3/WorldMem/Matrix-Game 代码，因此不把论文数字写成独立复现。

## 最终占用判断

- **Q1：未发现 defect-class claim 的已发表 prevalence 证据。** 2607.21686 是最危险邻居，但它是 serving/runtime state-discard diagnosis and repair，不是 released model implementation reset audit。
- **Q2：未发现等价五条件 audit predicate。** 一般 state pollution/order dependence、ML flakiness、DL bug taxonomies、controller stale-state testing、algorithmic unit tests 和 video memory benchmarks 都分别占据邻近轴。
- **Q3：剩余的是“released stateful generative repositories 的 reset/lifecycle defect audit + cross-release prevalence + frozen-weight consequence”的联合交集，且目前只是待检验的占用缺口。**
- **Q4：最强反对意见是跨域重命名 test pollution，加上 reset contract 缺失时 defect 判定没有语义 oracle。** 没有多 released consumers、公开 lifecycle contract、held-out repos 和 `M/N`，单个 VMem worked example 不足以把它从普通状态污染提升为独立 defect class。
