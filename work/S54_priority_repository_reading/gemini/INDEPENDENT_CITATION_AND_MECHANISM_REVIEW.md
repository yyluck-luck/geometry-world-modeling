# Gemini 本轮回答的独立引用与机制复核

**结论：原答可作为提出反对意见的材料，不能直接作为论文依据或实验判定规则。** LEACE 的真实题名和 NeurIPS 2023 发表身份已核实，但其“原空间完美正交消除”的解释错误；Geiger 的所列题名和 ICLR 2022 归属未能核实。冻结 L 的中介效应解释、单次替换的全局结论、正交机制的成立条件和计算成本均需纠正。**不采用新命名机制，不宣称发现了新方法或已达到顶会水平。**

## 复核对象、证据边界

- 对象：`response_1.md`，7037 bytes，SHA256 `821fb11e25d2ca132cff90aabafa648183aae8d676765ef71e7a4b261ed07d7b`。本复核实际重读了完整文件。原答由 root 本轮从 Gemini 的 Copy response 功能转存；UI 模型档位与复制过程由 root 的记录负责，本独立复核不将它们当作论文证据。
- **SOURCE FACT**：论文原文、正式论文集信息或所列本地源码中确实出现的内容。**INFERENCE**：我们根据明确计算图或数学作出的推论。**UNSUPPORTED**：现有证据不足以成立，包含已被反例否定的普遍命题。未找到不等于证明不存在。
- 本次 0 次模型调用、0 次生成、0 次实验图像或实验数组读取；仅核查文本、论文和两个标准整数反例。LEACE 正式 PDF 已下载并转为文本，未复现作者实验。没有运行 Claude 模型。

## 两项引用逐条核对

| Gemini 的引用 | 官方核对与结论 |
|---|---|
| *Probing as Causal Abstraction*，Geiger et al.，ICLR 2022 | 对该精确题名与作者、OpenReview 限域检索，未确认这组题名/年份/会议。**UNSUPPORTED：不得照抄进参考文献。** 可核实的相邻著作是 Geiger、Lu、Icard、Potts 的 [Causal Abstractions of Neural Networks，NeurIPS 2021](https://papers.nips.cc/paper/2021/hash/4f5c422f4d49a5a807eda27434231040-Abstract.html)，以及 Geiger 等的 [Inducing Causal Structure for Interpretable Neural Networks，ICML 2022，PMLR 162:7324–7338](https://proceedings.mlr.press/v162/geiger22a.html)。只能说可能混淆，不能替 Gemini 猜定它本来指哪一篇。 |
| *LEACE: Perfect Linear Concept Erasure in Closed Form*，Belrose et al.，NeurIPS 2023，OpenReview ID `fNlEqJOnD9` | **SOURCE FACT：题名、作者和 NeurIPS 2023 主会身份成立。** 正式署名 Nora Belrose、David Schneider-Joseph、Shauli Ravfogel、Ryan Cotterell、Edward Raff、Stella Biderman，见 [NeurIPS 官方页](https://papers.nips.cc/paper_files/paper/2023/hash/d066d21c619d0a78c5b557fa3291a8f4-Abstract-Conference.html)。所给 OpenReview ID 未验证；网页无法读取，API 返回 403，**这不证明 ID 不存在**。搜索还返回另一 PDF ID `awIpKpwTwF`，其 API 同样 403。本次采用已成功获取的 [官方 PDF](https://papers.nips.cc/paper_files/paper/2023/file/d066d21c619d0a78c5b557fa3291a8f4-Paper-Conference.pdf)，不依赖任一未验证论坛页。 |

Geiger 两篇本轮只核对正式元数据及摘要中的方法定位，没有声称完成全文精读。ICML 2022 摘要明确 IIT 是训练网络匹配给定因果模型的互换反事实；这不能改写成所有冻结网络已经具备严格线性对齐子空间，也不能支持极小批次的稳定无偏估计。以上“不能推出”是我们的逻辑判断，不是冒称读到了该论文否定定理。

## LEACE 原文究竟保证什么

**SOURCE FACT，正式 PDF §3、定理 4.2/4.3、§4.2–4.3：** 对中心化、有限二阶矩的 X、Z，LEACE 在 `Cov(PX,Z)=0` 约束下最小化期望二次表征改变量，闭式形式为：

```text
W = (ΣXX^(1/2))⁺
Π = (WΣXZ)(WΣXZ)⁺
P* = I − W⁺ Π W
```

未中心化时加 `b*=E[X]−P*E[X]`。符号 `⁺` 是伪逆，允许奇异协方差；**满秩不是该定理的必要前提**。白化空间的 Π 是正交投影，但整个 P* 通常是斜投影，原文 §4.2 专门解释这一点。[官方原文](https://papers.nips.cc/paper_files/paper/2023/file/d066d21c619d0a78c5b557fa3291a8f4-Paper-Conference.pdf)

分类结论受原文 predictor/loss 类及标签条件限定；连续 Z 的扩展采用线性最小二乘。不能扩大为任意非线性信息完全消除。最小“表征改变量”也不是最小“任务性能损失”。小样本的协方差泛化仍需验证，不能从总体定理直接得到测试域保证。冻结权重上的一次表征变换不会自动训练出互补能力；这是对拟议迁移的判断，并非 LEACE 自称提供的能力。

## 机制和诊断纠错

| 原答主张 | 分类与纠正 |
|---|---|
| 冻结 L、干预 c，阻断直接路径并隔离 `c→L→Y` | **UNSUPPORTED，因果方向颠倒。** 若 L 真是 c 的中介，固定 L 会阻断这条中介变化；测到的是固定中介值时的受控作用。我们当前 `get_cond` 源码中，均值 embedding 形成 cross-attention 条件，另一个输入 `context_latents` 形成 replace 条件，没有显示输入 c 生成输入 L 的边。将下游扩散状态也叫 L 会混淆不同变量。先定义计算图，再给效应命名。 |
| c 有非零梯度，但可能只是偏置/温度 | **INFERENCE：值得保留的竞争解释。** 梯度非零不证明质量收益，也不说明信息内容。但一次“非均匀输出改变”仍不能独自排除温度变化经非线性下游传播的解释，不能成为几何信息的充分证据。 |
| LEACE 擦除 L 中与 c 平行的部分，强迫网络学习互补 | **UNSUPPORTED。** LEACE 操作统计交叉协方差所定义的子空间，不等于删除一条样本 c 的平行分量；其保证也不是条件独立或任务互补。冻结网络可以改变响应，不会因前向投影自动学习。 |
| 把 c 投到 L 当前几何流形的正交补 | **UNSUPPORTED，数学对象未定义。** 本项目 c 是池化后的全局 embedding，L 是空间 latent 张量；不能仅凭命名直接定义二者内积、共享坐标或平行。需定义共同表示、度量及子空间；流形的正交补还需指定切空间和基点。“语义与几何近乎正交”没有本项目证据。即使构造出投影，也可能丢掉有用信息。 |
| q 经刚体变换后 D 不变，就证明交互平凡 | **UNSUPPORTED。** 场景与全部相机一致变换可能只是坐标系变更，此时不变性反而合理。只改变目标 q 则可能改变实际视点，需要明确图像坐标如何对应、期望的不变性或等变性及可见性。没有统一规则要求 D 的绝对幅值必须变。 |
| 最终 `D≠0` 就能解释分支机制 | **INFERENCE：D 只否定所测输出上的局部可加性，不能定位非线性发生在哪。** S55 已实际核算 `h=a+b; Y=h²`：h 的 D 为 0，Y 的 D 为 2。它是标准标量反例，不是网络实测或新定理。首步 D 为 0 也不能否定后续步出现真实交互。 |
| 四次前向无需重算下游、耗时极低 | **UNSUPPORTED，与完整 Y 定义不相容。** 条件改变后，所有受影响的采样步骤和最终解码都需重算；只有不受干预影响的前缀可复用。四次单个去噪器调用只测局部响应，不等于四次完整视频生成。源码的循环逐步更新状态，还含实际噪声注入，不能忽略状态重放。 |
| 一次随机替换 `Δ≈0` ⇒ 网络根本不用 c | **UNSUPPORTED。** 只能说该替换、状态、输出量和容差下未检测到影响。零差异可能来自对称、抵消、剂量不足或测量不敏感。下面整数反例已执行。 |
| 基线同时胜过两个破坏条件 ⇒ 两路有益互补、缺一不可 | **UNSUPPORTED，结论过强。** 仅支持这两个特定破坏使该样例损失增加；破坏可能离开自然数据支持，尚未区分可加收益、不可替代性和联合效应。 |
| 随机 c 的损失更低 ⇒ 正确语义干扰正确几何，并证明均值平滑 | **UNSUPPORTED。** 单例损失改善不能证明任一路输入正确，更不能定位平滑机制。需要独立合法参考、对应基线及控制混杂；当前 proposal 的参考未暴露约束不能省略。 |
| ARC-JSD 仅事后归因，拟议方法是此前没有的硬约束 | **SOURCE FACT 反驳这种近邻描述：** [作者 v5 §7](https://arxiv.org/html/2505.16415v5) 表 4 包含内部 attention/MLP 门控及随机对照，表 5 和图 4 还有激活消融。我们本轮确认的是这些设计实际写在原文中，没有复现其收益。是否为硬约束不能单独证明创新。 |
| 投影后“纯几何扰动”使输出不变，一批便证明机制有效 | **UNSUPPORTED。** 若扰动被所定义投影直接消掉，这可能只验证实现的代数不变性，不能证明干预确实纯几何或输出质量提高。 |
| 一次诊断负结果就能直接写高价值 ICLR/NeurIPS 分析论文 | **UNSUPPORTED。** 需要现象稳定性、代表性、竞争解释排除、近邻差别与有价值后果；四个样本条件本身不能承诺论文水平。 |

本地源码证据：`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py` 的 `get_cond`（1123–1168 行），以及 `modeling/sampling.py` 的 `sampler_step`/采样循环（380–437 行）。阅读源码只能确认这段实现的消费者关系；它不替代真实执行结果。

## 两个已执行的最小算术反例

1. 假设中介系统 `L=2c，Y=3c+L`，把 c 从 0 改为 1。总变化 5；冻结 `L=0` 后变化 3；由 L 变化传递的部分为 2。**固定 L 测不到这条中介变化**。这是预先定义的确定性示例，不是在估计 VMem 的中介效应。
2. `Y(c)=c²`，从 c=1 换为 c=−1，输出均为 1，差为 0；但 c=0 时输出为 0。因此一次零差不能证明函数从不用 c。

实际运行时间、整数输出见 `INDEPENDENT_ALGEBRA_CHECK.json`。这两项只纠正推理，不计入真实模型实验、创新收益或新数学定理。

## 对本项目下一步的有限影响

保留 Gemini 提出的“先区分可能的竞争解释”和“影响与收益分开”两条方向，其余按上文收紧。继续采用 S53 已有的单一来源、两条消费路径的小诊断；S55 建议的共同实际状态下首步观测，仅帮助区分当前观测点与下游输出，不能解释全轨迹。**本次不新增大协议、不采用正交流新名称、不启动模型。**

S53 记录的历史两批 CPU 耗时是约 44.74 分钟，六次完整两批的算术外推约 4.47 小时；这是旧配置成本估计，并非本次实际运行，也不是免除启动条件的授权。本次没有重新测时或读取 C1/C2 结果体。

技能落实：Supervisor `idea-evaluator` 的近邻核验与致命缺陷检查；handbook 2.3 的隐含假设检查；本地 Claude `sci-scientific-critical-thinking` 的构念效度、因果混杂和证据强度检查。具体使用是纠正未经定义的正交关系、错误效应命名和单例全局化，不以 skill 数量增加创新完成度。

保持 `NO_METHOD_SELECTED`、`novelty_authorization=NONE`、`new_method_validated=false`。

## 检索与实际阅读范围

- 检索词：精确题名 `"Probing as Causal Abstraction" Geiger`、`"Probing as Causal" Geiger`、`site:openreview.net "Probing as Causal Abstraction"`；LEACE 官方 NeurIPS 条目与两个 OpenReview ID。未核实项保留未核实，不由无结果推导不存在。
- 2026-09-08（Asia/Shanghai）实际打开并再次核对上述 NeurIPS/PMLR 正式页面；Geiger 两篇止于元数据/摘要定位，不当全文方法依据。
- LEACE 下载 URL、实际请求起止、HTTP 状态及 PDF SHA 在 `independent_sources/FETCH_RECEIPT.json`。PDF SHA256：`33c6e3d215dc1c73c2d76d59d2dbfb46b19b10b52ab9168cfa91302c4db055e8`。实际读 §3、定理 4.2/4.3、§4.2–4.3、§6.2/§7 相关范围及文本检索返回的附录 F/H 片段；未声称全文附录精读。
- ARC-JSD 仅重读上述 v5 的 §7 相关门控与消融原文；沿用 S53 已核对的近邻身份，不把这次复核记作新论文发现。
- 精确写入时刻与本地输入/产物身份由本报告 receipt 记录；网页读取只保留实际日期，不虚构未捕获的秒级访问时刻。正文的所有数学和项目迁移推论均与作者原文事实区分。
