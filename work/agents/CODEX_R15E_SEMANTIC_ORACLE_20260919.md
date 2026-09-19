# Round 15-E：语义 oracle 压力测试与裁定（2026-09-19）

## 先给裁定

这个方向不能用“某字段没有出现在 `reset()`”作为充分证据。它最多是静态异常信号。一个可辩护的 oracle 必须把判定对象提升到**公共生命周期合同**：对用户可调用的 API，先写出可观察的前置/后置不变量，或写出事前固定的等价调用关系；再用代码路径和执行结果证明违反。字段是否应该清除，只能作为归因问题，不能作为 oracle 本身。

对两个实例的结论不同：

- **GEN3C：有可辩护的 oracle。** 最强证据不是两个字段名字相似，而是同一个公共服务层已经形成了不变量：`model_seeded == True` 时，`request_inference()` 可以放行；因此它必须代表一个可用的 3D cache。重置缓存后，重新 seeding 在 `seeding_method(...)` 抛异常，服务捕获 HTTP 400，而旧的 `model_seeded=True` 可保留，随后推理仍可能被放行。这是公共 admission safety invariant（准入安全不变量）的反例。`model_was_seeded=False` 的清除是跨层一致性证据，会加强归因，但不是唯一依据。
- **VMem：当前没有足够的静态语义 oracle。** `initial_threshold` 未在 `__init__` 初始化、在 NMS-off 路径写入、在部分 NMS-on 路径读取，且 `reset()` 不清除它，足以证明跨调用依赖的可达性和未初始化风险；但不能仅凭这些证明它按公开生命周期“本应被清零”。`reset()` 的 docstring/调用方式可以产生候选合同，然而仓库没有把 `initial_threshold` 明确纳入 reset 后置条件。需要另行声明并验证一个公共可观察的 metamorphic relation（变形关系），否则本实例应标为 **INTENT-ORACLE-UNRESOLVED**，而不是 HIT。

所以，若问题是“现在能否对两个实例都给出同一套静态语义裁定”，答案是**不能**。若问题是“是否存在一条可以继续的研究路线”，答案是：GEN3C 可按公共合同收束；VMem 必须改成事前声明的用户可观察关系，否则在本轮关闭。

## 1. 仓库与公开源码核验

### 1.1 VMem

仓库中的三个副本逐字节一致，实际 `sha256sum` 均为：

`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`

核验文件：

- `work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py`
- `work/S17_cpu_preflight/original/modeling/pipeline.py`
- `work/S102_gate0_3dmatch/adapter_v1/sources/vmem_pipeline.py`

固定源码的关键链如下（以第一份副本为准，另外两份相同）：

- `:674`：`is_second_step = len(self.pil_frames) == 5`。
- `:681-700`：NMS-enabled 分支只在 `is_second_step` 为真时给 `initial_threshold` 赋值；无 pairwise distance 时赋 `1`，有距离时赋 percentile。
- `:704-705`：NMS-disabled 分支无条件执行 `self.initial_threshold = 1e8`。
- `:707-708`：随后无条件读取 `current_threshold = self.initial_threshold`。
- `:135-146`：`reset()` 清理 11 个以上列表/字典字段和 `global_step`，不清理 `initial_threshold`；也不清理 `c2ws` 或 `pil_frames`。
- `:149-163`：`initialize()` 的 docstring 写着 “Reset internal state”，随后调用 `reset()`。
- `:180`：`initialize()` 将 `self.c2ws = [c2w]`。
- `:1249`：`get_context_info(target_c2ws, use_non_maximum_suppression)`。
- `:1263`：`torch.cat([context_c2ws, target_c2ws])`。
- `:1265`：`get_translation_scaling_factor(all_c2ws)`。
- `:1297`：生成帧写回 `self.c2ws.append(...)`。
- `:1360`：`undo_latest_move()` 还会 `self.c2ws.pop()`。

因此，“`self.c2ws` 只有两个写入站点”只有在“写入”严格指赋值和 append 时才成立；按可变状态 mutation 计数，`:1360` 是第三个修改站点。源码没有 `@property` setter 或其他 `c2ws` setter。`initial_threshold` 只在上述函数路径赋值，未在 `__init__` 初始化。

这组事实支持“跨调用状态依赖可达”，不单独支持“作者意图必须清除该字段”。此外，`c2ws` 本身也被 `initialize()` 重置并可由 `undo_latest_move()` 删除，说明“reset 集合中的字段是否完全同质”不能从名字或列表邻近性直接推出。

公开论文和仓库身份：Runjia Li, Philip Torr, Andrea Vedaldi, Tomas Jakab, **“VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory,”** arXiv:2506.18903，ICCV 2025；源码固定 commit `39291e4f272f6b4f270691d930926ab5930f942e`：<https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py>。本文件对 VMem 只作源码静态判断，没有把 GPU smoke、报告或历史 panel 当作该 oracle 的执行验证。

### 1.2 GEN3C

固定 commit 为 `db2ffe12ced12ddafcec5e0422ee46ce8520746b`。公开 raw 文件逐行核对如下：

- `gui/api/server_cosmos_base.py:46-71`：`seed_model()` 调用 `self.model.clear_cache()` (`:53`)，清空 `pose_history_w2c` 和 `intrinsics_history` (`:54-55`)，之后才调用 `seeding_method(...)` (`:62-70`)，最后才写 `self.model_seeded = True` (`:71`)。
- `cosmos_predict1/diffusion/inference/gen3c_persistent.py:206-208`：多帧 seeding 在缺少 depth 时抛出 `NotImplementedError`。
- `cosmos_predict1/diffusion/inference/gen3c_persistent.py:551-553`：模型层 `clear_cache()` 设置 `self.cache = None` 和 `self.model_was_seeded = False`。
- `gui/api/server_base.py:59-60`：服务层初始化 `self.model_seeded = False`。
- `gui/api/server_base.py:121-129`：`request_inference()` 在 `:122-123` 只检查 `self.model_seeded`，通过后创建推理任务；这里没有检查模型层的 `cache` 或 `model_was_seeded`。
- `gui/api/server.py:168-174`：seeding 异常被捕获并返回 HTTP 400；进程不会因该异常退出。

因此，只有在服务原来已经 `model_seeded=True` 时，失败的二次 seeding 才会留下“旧的服务标志仍为 True、模型 cache 已清空、推理准入仍打开”的状态。若服务原来为 False，失败后仍是 False，不能把两种前置状态混写。GEN3C README 还把再次点击 Seed 描述为清除已有 3D cache 并从头开始：<https://github.com/nv-tlabs/GEN3C/blob/main/gui/README.md>。本轮没有运行 GEN3C 服务；**失败后下一次真实 inference 是否最终创建成功：UNVERIFIED（未运行）**。上述其余内容是固定源码的静态可达性和 API 处理证据。

公开论文身份：Xuanchi Ren et al., **“GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera Control,”** Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) 2025，Highlight，arXiv:2503.03751，DOI `10.1109/CVPR52734.2025.00574`；代码固定 commit：<https://github.com/nv-tlabs/GEN3C/tree/db2ffe12ced12ddafcec5e0422ee46ce8520746b>。

## 2. 对“内部不一致即意图证据”的攻击与改进

### 2.1 它能否泛化？覆盖率是多少？

原命题是：同一个概念在两个层有近名字段，其中一层在 reset 中清除，另一层不清除，因此可推断后者也应清除。

这个命题可以泛化为一个**重复生命周期状态的一致性检查器**，但覆盖面严格限于同时满足以下条件的系统：

1. 能够可靠地证明两个字段表示同一个生命周期概念，而不是只相似命名；
2. 两层的 reset/clear 方法确实参与同一公共操作；
3. 外层字段被用于公共准入、输出或错误处理；
4. 允许的状态关系可以写成可观察不变量。

缺少任一条件时，结果只是可疑点。对本轮的两个实例，重复字段只覆盖 GEN3C；VMem 的 `initial_threshold` 在当前代码中没有同名或语义已证实的 sibling。因此按该 oracle，GEN3C 是可判定候选，VMem 是**不覆盖**，不是阴性结果。

### 2.2 两层合法不同生命周期的假阳性

一个具体假阳性模式是：外层 `model_seeded` 表示“用户已提供一份可复用的 seed 元数据”，内层 `model_was_seeded` 表示“当前 GPU cache 已物化”。实现可以合法地在清 cache 后保留外层元数据，并在下一次推理前懒重建。此时两层不同时清零并非缺陷。相似名字和同一调用链都不足以排除这种设计。

GEN3C 的假阳性防御在当前固定源码下失败，是因为：

- `clear_cache()` 明确让模型 cache 为空并把模型层标志置 False；
- `request_inference()` 只看外层标志，不做懒重建，也不看 cache；
- 失败发生在 cache 已清之后，且 HTTP 层只返回 400。

所以这里可以证明一个更强的公共安全不变量违反：

> **I-GEN3C：在任何可接受的服务状态中，`model_seeded=True` 必须蕴含一个可供 `request_inference()` 使用的有效 3D cache。**

`clear_cache()` 清内层标志是该不变量的内部一致性证据，但判定不依赖“两个名字近似”。如果未来代码加入 lazy rebuild，原结论必须重新审计，不能机械沿用。

### 2.3 “同一 reset 方法中与 peers 不一致”是否足够？

不是。把 `reset()` 中清空的字段组成 peer group，然后把唯一未清字段标为 defect，是一个有用的**异常排序 heuristic**，不是语义 oracle。它会把以下合法字段误报为 defect：模型权重、配置、日志计数器、随机数流、锁、共享缓存、跨请求索引，以及任何明确设计为 session-persistent 的状态。

对 VMem，`initial_threshold` 的异常度很高，因为它在一个路径被写、在另一个路径被读，而且没有构造函数初值；但 `c2ws`/`pil_frames` 与 `reset()` 的不齐也说明仅凭 peer-group non-uniformity 会得到多个候选。要把该信号升级成 oracle，至少要再有一项：

- 公开 docstring/README/type contract 明确声明 reset 后相关选择状态为空或与 fresh instance 等价；或
- 事前声明的公共 metamorphic relation 被执行结果违反；或
- 同层 admission/output invariant 被违反。

否则正确标签仍是 `SUSPICIOUS_STATE_DEPENDENCY`，不是 `DEFECT_PROVEN`。

## 3. 其他 oracle 家族调查

### 3.1 动态不变量、规格和 typestate inference

**Daikon** 从执行轨迹报告 “likely invariants”，不是规范真值。原始论文：Michael D. Ernst, Jake Cockrell, William G. Griswold, David Notkin, **“Dynamically discovering likely program invariants to support program evolution,”** *IEEE Transactions on Software Engineering* 27(2), 2001, DOI `10.1109/32.908957`。它能发现诸如“某程序点字段为空”或“某值范围”的候选，但未观察到的路径不会被覆盖；一个候选长期不变也可能只是测试集偏差。Daikon 没有内建“哪些字段必须加入 reset 集”的规范语义。

更具体的 API 协议挖掘也不能直接解决 reset-set：

- Glenn Ammons, Rastislav Bodík, James R. Larus, **“Mining specifications,”** *POPL 2002*, DOI `10.1145/503272.503275`：从调用轨迹挖掘协议/FSM；频繁路径被当成典型行为，未给出字段级 reset 规范。
- Michael Pradel, Thomas R. Gross, **“Automatic Generation of Object Usage Specifications from Large Method Traces,”** *ASE 2009*, DOI `10.1109/ASE.2009.60`：从大规模方法轨迹生成对象使用规格，明确依赖“频繁行为大体正确”的假设；可以提示非法调用序列，但不能证明某个字段在 reset 后必须为初值。

把它们用于本题的合理方式是：先挖掘 `initialize/reset → get_context_info/request_inference` 的候选协议，再用独立公共合同验证；不能把 mined invariant 本身当成作者意图。

### 3.2 文档、注释和类型标注

注释和 docstring 是意图证据，但可靠性有限。

- Yukinao Hirata, Osamu Mizuno, **“Do comments explain codes adequately? Investigation by text filtering,”** *MSR 2011*, DOI `10.1145/1985441.1985482`：以代码/注释文本距离等方法评估解释充分性，不提供生命周期合同的可靠性保证。
- Walid M. Ibrahim, Nicolas Bettenburg, Bram Adams, Ahmed E. Hassan, **“On the relationship between comment update practices and Software Bugs,”** *Journal of Systems and Software* 85(10), 2012, DOI `10.1016/j.jss.2011.09.019`：注释和代码不一致的变化值得审查，但不一致并不自动意味着 bug。
- Pooja Rani et al., **“A decade of code comment quality assessment: A systematic literature review,”** *Journal of Systems and Software* 195, 111515, 2023, DOI `10.1016/j.jss.2022.111515`；预印本 arXiv:2209.08165：系统综述报告质量没有唯一标准，研究大量依赖人工评估和特定启发式。

因此，VMem `initialize()` 的 “Reset internal state” 可以把 fresh-instance equivalence 提升为候选合同，但它没有逐项命名 `initial_threshold`；类型标注通常只约束 shape/type，不表达跨调用时序。文档派 oracle 需要另一个可观察行为或显式测试契约确认。

### 3.3 Differential / metamorphic oracle

变形测试的关键不是“字段应该清除”，而是预先写出输入/调用序列之间的输出关系。基础来源：

- Tsong Yueh Chen, Shing-Chi Cheung, Siu-Ming Yiu, **“Metamorphic Testing: A New Approach for Generating Next Test Cases,”** HKUST Technical Report HKUST-CS98-01 (1998)；后续 arXiv 上传为 arXiv:2002.12543。原始技术报告没有 DOI。
- Huai Liu, Fei-Ching Kuo, Dave Towey, Tsong Yueh Chen, **“How Effectively Does Metamorphic Testing Alleviate the Oracle Problem?”** *IEEE Transactions on Software Engineering* 40(1), 2014, DOI `10.1109/TSE.2013.46`：实验证明合适的 metamorphic relations 可以替代昂贵的单次输出 oracle，但 relation 本身需要领域知识。
- Tsong Yueh Chen et al., **“Metamorphic testing: a review of challenges and opportunities,”** *ACM Computing Surveys* 51(1), Article 4, 2018, DOI `10.1145/3143561`：明确把 relation identification 列为核心难点。

这一路线确实可以绕过内部意图，但只有当 relation 是公共 API 合同，而不是审查者凭直觉认为“这两条序列应该一样”。

### 3.4 测试污染/顺序依赖 oracle

四个用户指定方法的 oracle 都是行为或状态差异，不是“作者本来想清什么”的证明：

1. Alex Gyori, August Shi, Farah Hariri, Darko Marinov, **“Reliable Testing: Detecting State-Polluting Tests to Prevent Test Dependency,”** *ISSTA 2015*, DOI `10.1145/2771783.2771793`。PolDet 记录测试前后的共享 heap/filesystem 差异，过滤不可由后续测试观察到的差异，再报告 potential polluters；它不把每个共享状态写入都判为应清除。
2. Alessio Gambi, Jonathan Bell, Andreas Zeller, **“Practical Test Dependency Detection,”** *IEEE ICST 2018*, DOI `10.1109/ICST.2018.00011`。PRADET 建立动态、alias-aware 依赖图，并重排测试；若只改变一个依赖方向就改变测试结果，依赖被确认。oracle 是结果变化。
3. Chengpeng Li, Chenguang Zhu, Wenxi Wang, August Shi, **“Repairing Order-Dependent Flaky Tests via Test Generation,”** *ICSE 2022*, DOI `10.1145/3510003.3510173`。ODRepair 比较通过/失败顺序中的 heap，逐个恢复候选字段；若恢复后 victim 通过，才把字段归因为污染根。oracle 是修复后通过，不是静态 diff。
4. Anjiang Wei, Pu Yi, Zhengxi Li, Tao Xie, Darko Marinov, Wing Lam, **“Preempting Flaky Tests via Non-Idempotent-Outcome Tests,”** *ICSE 2022*, DOI `10.1145/3510003.3510170`。NIO 在同一 JVM/interpreter 中重复同一测试，若第一次通过、第二次失败则判定非幂等结果。它检测共享状态影响，不证明某状态按 API 规范必须 reset。

迁移到 VMem/GEN3C 时，顺序依赖文献的**用户可观察结果 oracle**可以转移：固定随机流和输入后，比较 fresh/reused、不同调用顺序或失败后调用的结果/准入；但“同一方法更名为 memory pollution audit”本身没有新 oracle。PolDet/PRADET/ODRepair/NIO 已经占据了“状态差异、重排结果差异、恢复字段后通过、重复运行结果差异”这些一般机制。新工作若要避免跨领域 rename objection，必须把公共合同、生成器状态和可复现的用户后果写成领域特有且可证伪的关系。

## 4. Q1：逐实例裁定

### Instance 1 — VMem `initial_threshold`

**当前裁定：没有完成的 intent oracle；只能报告结构风险。**

已有证据能证明：

- NMS-off 写入 `1e8`；
- NMS-on 在 `len(self.pil_frames) != 5` 时不重新赋值而读取旧值；
- `reset()` 不清该字段；
- `__init__` 不初始化该字段；
- 固定源码存在公共调用者 `:1249`，并把 context/target 一起传入统一坐标处理 `:1263-1265`。

这些事实支持跨调用状态泄漏和未初始化异常。它们不能单独证明 `reset()` 的公开语义包括该标量。peer-group 非一致性和“字段名看起来像临时阈值”都只是先验。fresh/reused 变形关系在本轮**UNVERIFIED（未执行）**。

**可以把 VMem 变成可判定实例的最小 oracle：**事前声明 `initialize(x)` 后的任一合法公共导航序列，与 fresh pipeline 在同一输入、同一随机流、同一模型状态下的可观察 context-selection/exception/output 必须相同；或声明 `reset()` 后 `get_context_info()` 的选择结果必须与新实例相同。若执行出现差异，缺陷成立而不需要证明 `initial_threshold` 的作者意图。当前本文件没有执行这个 relation，也不把既有 panel 数字当作执行证明。

### Instance 2 — GEN3C `model_seeded`

**当前裁定：有可辩护 oracle，且比“重复字段不一致”更强。**

最小公共合同是：

> `request_inference()` 放行的服务状态必须拥有可用 3D cache；如果一次 reseed 在清 cache 后失败，服务必须拒绝推理，或明确恢复旧 cache/旧服务状态。

固定代码允许旧 `model_seeded=True` 在失败后继续存在，同时模型层已经 `cache=None; model_was_seeded=False`，且 admission gate 不检查模型层状态。此时对用户可观察的是“失败后 HTTP 400 但后续 inference 被接受/启动”，这已经是公共生命周期错误。若实际执行再确认后续请求路径，属于行为证据；当前结论是静态可达性，不能写成已运行的后果。

## 5. Q2：排序与单一最佳 oracle

按本项目的“意图争议最小化”排序：

1. **公共 API 的显式 invariant / postcondition，加上执行或可复现路径证据。** 例如 GEN3C 的 `model_seeded ⇒ usable_cache`。
2. **事前固定的公共 metamorphic relation**，fresh/reused、reset/no-reset、失败前后等价关系以用户可观察输出、准入和错误作为 oracle。
3. **文档化生命周期合同与 differential replay**，包括 docstring/README/类型约束，但要独立做行为确认。
4. **跨层 duplicate-state consistency**：字段 sibling + 相同 clear 操作 + 公共 gate；适合归因和候选排序，不能单独定罪。
5. **动态 invariant / typestate / protocol mining**：能生成候选协议，受轨迹覆盖和“频繁即正确”假设限制。
6. **peer-group non-uniformity**：很便宜、很适合 triage，但最容易退化成 style checking。
7. **单独依赖注释或变量名**：只能作弱证据。

单一最佳 oracle 的精确陈述是：

> **公共生命周期关系 oracle：**对一个预先写入并由文档/API 语义支持的关系 (R)，若两条调用序列从等价的公共初态出发，且 (R) 声明它们在公共可观察结果（成功/失败、错误类别、准入、返回值或固定随机流下的输出）上应相等或满足指定变换，那么观察到 (R) 被违反即可判定生命周期缺陷；字段是否清除只作为后续归因，不作为判定前提。

这是唯一同时能处理“作者没有写 reset”与“内部字段只是实现细节”两种反对意见的定义。它的前提是关系 (R) 必须来自公开合同或事前冻结的产品语义，不能看过结果后再创造。

## 6. Q3：metamorphic route 是否解决问题？

分三部分回答：

**(a) Sound：条件成立时是。** 若“等价”来自文档化公共 API 合同，且控制了随机性、外部 I/O、并发和模型版本，那么 relation violation 是对用户可观察合同的反例，不必证明 `initial_threshold` 或 `model_seeded` 在实现层应该怎样清。若等价关系只是“审查者觉得这两序列应等价”，问题只是从字段意图换成 relation 意图，不能算 sound。

**(b) Already occupied：一般路线是。** 变形测试和测试依赖研究已经占据“用多次运行之间的关系代替单次输出 oracle”的一般思想；上面的 Chen/Liu，以及 PolDet/PRADET/ODRepair/NIO 都是可核验先例。因此“使用 metamorphic relation”本身不能作为新颖性主张。

**(c) Applicable to both：原则上可以，当前尚未执行。**

- VMem 可检验：fresh pipeline 与“先使用旧历史、再调用 `initialize()`、随后执行同一合法导航轨迹”是否产生同一 context selection、错误类别和固定随机流下输出。这里的 relation 可由 `initialize()` docstring 的 “Reset internal state” 支持，但必须事前把“internal state”解释成影响公共行为的全部状态，并实际执行；当前没有完成，所以不能把 VMem 宣布为已判定。
- GEN3C 可检验：在已 seeded 状态下发起会失败的 reseed，随后请求 inference；公共关系是“失败后不得在无 cache 时被准入，除非旧状态已恢复”。这个关系来自 admission precondition 和清 cache 调用链，比比较两个字段更强。它可以在 API 层验证，无需生成视频。

所以 metamorphic route **可以消除内部字段意图问题，但不能自动消除关系本身的语义来源问题**。它适用于两实例的下一步设计，但当前仓库证据只足以直接裁定 GEN3C。

## 7. Q4：是否应现在关闭方向？

不必关闭整个方向，但必须关闭一个过强的版本：

- 关闭“reset peer 不齐 + 跨层近名字段不齐 = 已证明缺陷”的静态总 oracle；
- 保留 GEN3C 的公共 admission invariant 作为可复核 HIT；
- VMem 暂停为 `INTENT-ORACLE-UNRESOLVED`，除非先冻结并执行 fresh/reused 或 reset/no-reset 的公共 metamorphic relation；
- 若该 relation 不能从 VMem 的公开 API 合同中成立，Vmem 这一实例应正式判为**没有可辩护 oracle**，不再用它支持广泛方法主张。

这也是对 rename objection 的诚实处理：一般状态污染和顺序依赖 oracle 已有成熟先例；本项目只有在“面向生成器/世界模型公共 API 的生命周期合同 + 可重复用户后果 + 领域特有关系”三者同时存在时，才可能有超出已有测试污染工作的贡献。

## 8. 可追溯来源清单（已核验）

### 项目源码与论文

- VMem code, commit `39291e4f272f6b4f270691d930926ab5930f942e`: <https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py>
- Runjia Li et al., **“VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory,”** arXiv:2506.18903; ICCV 2025: <https://arxiv.org/abs/2506.18903>
- GEN3C code, commit `db2ffe12ced12ddafcec5e0422ee46ce8520746b`: <https://github.com/nv-tlabs/GEN3C/tree/db2ffe12ced12ddafcec5e0422ee46ce8520746b>
- Xuanchi Ren et al., **“GEN3C: 3D-Informed World-Consistent Video Generation with Precise Camera Control,”** CVPR 2025, arXiv:2503.03751, DOI `10.1109/CVPR52734.2025.00574`: <https://arxiv.org/abs/2503.03751>

### 规格、注释和 metamorphic testing

- Ernst et al., **“Dynamically discovering likely program invariants to support program evolution,”** IEEE TSE 2001, DOI `10.1109/32.908957`: <https://doi.org/10.1109/32.908957>
- Ammons, Bodík, Larus, **“Mining specifications,”** POPL 2002, DOI `10.1145/503272.503275`: <https://doi.org/10.1145/503272.503275>
- Pradel and Gross, **“Automatic Generation of Object Usage Specifications from Large Method Traces,”** ASE 2009, DOI `10.1109/ASE.2009.60`: <https://doi.org/10.1109/ASE.2009.60>
- Hirata and Mizuno, **“Do comments explain codes adequately? Investigation by text filtering,”** MSR 2011, DOI `10.1145/1985441.1985482`: <https://doi.org/10.1145/1985441.1985482>
- Ibrahim et al., **“On the relationship between comment update practices and Software Bugs,”** JSS 2012, DOI `10.1016/j.jss.2011.09.019`: <https://doi.org/10.1016/j.jss.2011.09.019>
- Rani et al., **“A decade of code comment quality assessment: A systematic literature review,”** JSS 2023, DOI `10.1016/j.jss.2022.111515`; arXiv:2209.08165: <https://doi.org/10.1016/j.jss.2022.111515>
- Chen, Cheung, Yiu, **“Metamorphic Testing: A New Approach for Generating Next Test Cases,”** HKUST-CS98-01, 1998; arXiv upload arXiv:2002.12543: <https://arxiv.org/abs/2002.12543>
- Liu et al., **“How Effectively Does Metamorphic Testing Alleviate the Oracle Problem?”** IEEE TSE 2014, DOI `10.1109/TSE.2013.46`: <https://doi.org/10.1109/TSE.2013.46>
- Chen et al., **“Metamorphic testing: a review of challenges and opportunities,”** ACM CSUR 2018, DOI `10.1145/3143561`: <https://doi.org/10.1145/3143561>

### 测试污染与顺序依赖

- Gyori et al., **“Reliable Testing: Detecting State-Polluting Tests to Prevent Test Dependency,”** ISSTA 2015, DOI `10.1145/2771783.2771793`: <https://doi.org/10.1145/2771783.2771793>
- Gambi, Bell, Zeller, **“Practical Test Dependency Detection,”** IEEE ICST 2018, DOI `10.1109/ICST.2018.00011`: <https://doi.org/10.1109/ICST.2018.00011>
- Li et al., **“Repairing Order-Dependent Flaky Tests via Test Generation,”** ICSE 2022, DOI `10.1145/3510003.3510173`: <https://doi.org/10.1145/3510003.3510173>
- Wei et al., **“Preempting Flaky Tests via Non-Idempotent-Outcome Tests,”** ICSE 2022, DOI `10.1145/3510003.3510170`: <https://doi.org/10.1145/3510003.3510170>

没有把无法逐一核验的额外论文、作者声称、运行结果或“VMem 已被论文 benchmark 污染”写入本报告；本轮对 GEN3C 的后果仍标为静态可达性，未标为已执行行为结果。
