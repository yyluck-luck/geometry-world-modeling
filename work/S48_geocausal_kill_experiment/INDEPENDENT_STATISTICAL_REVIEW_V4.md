# S48 V4 独立统计、因果与可复算性审查

- 审查者：`/root/s48_v4_fresh_reviewer`；未参与本版草案撰写。
- 审查完成时间：2026-09-08T15:19:49+08:00。
- 精确被审文件：`work/S48_geocausal_kill_experiment/S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT.md`。
- 输入 whole-file SHA-256：`850ab1346716f16bd2eda9aa45226a7eb857912edebe940b562f11d7e88492d7`。
- **裁决：BLOCKED。CRITICAL 1 项，MAJOR 4 项，MINOR 3 项。**
- 本报告 canonical SHA-256：`b932b3c62277beeb4205744964967c67fcb7f72cf83c17905ceb8556869aac56`；计算时删除本字段所在整行，保留其余 UTF-8 字节和 LF。whole-file SHA 在交付消息给出，避免自引用哈希。
- 权限边界：只审文字和数学合同；0 模型导入/运行，0 S48 arm 创建/执行，0 C1/C2 tensor/image/pixel 正文读取、映射、解码或查看；草案未修改。

## 1. 结论

V4 实质关闭了 V3 的多项漏洞：fractional 权重在三类 placebo 间统一，刚性变换不裁切/插值，camera/source 使用同一 provenance 规则，三类 library 不混合；support 改为逐实际 target 相机重投影；Influence 超过 replay/sham/negative 的最大平均响应后还需达到 SESOI；所有判定 arm 均需过相同单位的守卫；Benefit 加入 10 ms、动态排除、确定性 roster 和 family×seed 门。不能继续沿用“这些内容都没定义”的旧裁决。

本次 BLOCKED 有新的独立理由。首先，扣掉**全图平均** sham 响应，并没有扣掉 sham 的**空间分布**。当前定位仍直接使用 `|F11−F00|`，所以重新编码造成的局部变化可以提供全部定位富集，而新增外观处理的响应完全均匀。这直接破坏 RQ2 的处理归因。其次，`B_local` 的正负两侧平均只反映两侧平均损失，不证明原外观分别优于两侧或是局部最优。此外，G7 仍需首次选择若干主要指标和编辑定义；reference 在 support 外的有效评分域、真实时间轴及 reference 专用相机资格尚未闭合。

这不是说当前已经出现上述失败，也不是模型无效的证据。它说明仍存在可满足文字规则、却不支持预期解释的情况。G0/G7 的禁止执行条款是有效硬门；本报告不把“尚未实现”本身当成新的科学错误，更不授权绕过这些门。

## 2. 精确输入与方法

| 实际读取的辅助文件 | 本轮实测 whole-file SHA-256 | 使用范围 |
|---|---|---|
| `INDEPENDENT_STATISTICAL_REVIEW_V3.md` | `7f0bc591aca198223cfa01792ea5eb9feb8f4f28f27cfc930085763a12c2b163` | 独立形成当前问题后对照关闭表；不继承裁决 |
| `TOP_VENUE_METHOD_FIXES_FOR_V3.md` | `f9b506bf5d24b1b3854e74b611dfd0fa16eb7aba947ee16bd85e9bfcc2c21863` | 读取方法修复建议；未重新核验其论文或代码结论 |
| `SOURCE_HOOK_STATIC_AUDIT_V2_README.md` | `427aadcad8102b24447cf8ebc0935b65001f4a48612668cd609ec12414b30483` | 仅核其陈述及证据边界；没有读取/执行所引用脚本或 JSON |

先读项目 `AGENTS.md`、`RESEARCH_PRINCIPLES.md`、`RESEARCH_MEMORY.md` 及最新 `RESEARCH_LOG.md`，以恢复访问限制。中央 `MEMORY.md` 的 S48/GEOCAUSAL 关键词检索没有命中，不依赖中央记忆结论。应用 `/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md` 的偏差、构念效度、反例和证据比例审查；这是一份局部协议审查，不是正式系统综述。未进行外网检索，因而近邻覆盖只评价本草案的主张边界，不认证最新文献完整性。

以下行号仅对应上述精确草案 SHA。模型和实际数据是否满足资格都没有在本次审查中测量。

## 3. V3 问题逐项关闭表

| V3 项 | V4 证据 | 独立状态 | 剩余边界 |
|---|---|---|---|
| C-V3-1 fractional 权重与 pooled family | §4.1；L224–252 | **核心测度/分族 CLOSED，生成器细节 PARTIAL** | 三族同域、fractional 公式和逐族 rank 已闭合；caliper 描述符/直方图分母仍见 M-V4-1 |
| M-V3-1 平均 pose 代替逐 target | §4.1；L224、237–238 | **CLOSED_AS_CONTRACT** | 逐实际 c2w/K、renderer、provenance 明确；实现仍待 G7 |
| M-V3-2 Influence 未超过 controls、部分 arm 无 guard | L190–192、212–218 | **CLOSED_FOR_SCALAR_INFLUENCE_AND_ARM_SCOPE** | 平均效应门已修正；不能由此推出空间 artifact 被排除，见 C-V4-1 |
| M-V3-3 时间/dynamic/identity/reference 选择 | L262–268 | **PARTIAL** | 10 ms、动态 union、唯一排序、baseline 公式均已给出；实际参考视角资格和评分域仍见 M-V4-2/4 |
| M-V3-4 B_local 缺 family×seed | L272–292 | **CLOSED_FOR_INDEX_AND_CONJUNCTION** | 四项全部过门已明确；两侧平均的解释另见 M-V4-3 |
| M-V3-5 把合同写成可执行 hook | §4.1、L296–311、393 | **CLOSED_AS_CLAIM** | 诚实声明 API 缺失；不是代码 PASS |
| N-V3-1 静态回执 provenance | L301；V2 README | **ADDRESSED_IN_SCHEMA, NOT_INDEPENDENTLY_VERIFIED** | 本次没有读取 JSON/脚本，只读 README，不冒充双解释器独立复核 |
| N-V3-2 seed-specific replay floor | L212–218 | **CLOSED** | 每 seed 的原 F00 加至少三 replay，所有 pair×target 最大值已明确 |
| N-V3-3 DiD 无公式但参与判定 | L292 | **CLOSED_BY_EXPLORATORY_ONLY** | 不进继续门，未预冻四 cell/代码则不算 |
| p 值/科学样本量/近邻边界 | RQ2、§7–12 | **CLOSED_FOR_PILOT_CLAIMS** | 没有 p/CI/总体显著性；scene 才是外推单位；novelty NONE |

fractional 闭合可以直接从 V4 公式推出：对每个 provenance 完整且非空的像素，若求和遍历全部唯一 source IDs，则 `Σ_source w_source(p)=1`；对仅被选中的 source 子集，和一般小于等于 1。剩余部分属于未选 provenance，不能把它再次归一化到已选集合。空/无 provenance 像素为 0。这一约定合理，但它是归因定义，不能冒充模型实际 routing 权重。建议未来代码增加全来源闭合和 selected-subset residual 的断言，而不是改公式。

## 4. CRITICAL

### C-V4-1：平均 control 校准不能阻止 sham 提供全部空间定位信号

**位置：** L177–183、208–218、224–252；亦影响 L274 的原始 versus re-encoded 比较解释。

V4 定义 `I=D_target−max(tau,D_sham,D_negative)`，然后对未经空间 control 校准的 `d_target=|Y_edit−Y_F00|` 做定位。两个量回答不同问题：前者证明平均响应更大，后者可能仍主要定位了无编辑重编码自身的变化。现有所有 target/family/seed 合取、placebo 家族和相机守卫，都没有要求 sham 的空间定位失败，或要求 edited-versus-sham 的直接响应定位通过。

**不用模型即可复算的构造反例。** 令 support 为有效域的 10%，其权重为 1（这是 fractional 的合法特例），`a=1/255`；设两侧平均的 sham 响应为 `a·1_S`，target 响应为 `a·(1+1_S)`，negative 为 0、replay 为 0。这可表示“相同重编码在 S 内造成一单位灰阶变化；真正编辑额外造成全域一单位变化”。则：

- `D_sham=0.1/255`，`D_target=1.1/255`；
- `I=1/255 > 0.5/255`，所以主 Influence 门通过；
- 真 support 的 `mass=0.2/1.1≈0.181818`，`area=0.1`，`L_area≈0.081818>0.02`，`ER≈1.81818`；
- 若按其他预处理资格获得 199 个同面积且低 IoU 的 placebo，每个收集的 mass 都低于真 support，因此 rank 可为 `1/200`；两个 family/seed/target 重复此结构也会全部通过；
- 但 edited-versus-sham 的净新增变化为全图常数 `a`，其 `mass(S)=area(S)`，没有定位。

这不是实际图像或实验结果，只是当前公式允许的数值反例。其 RGB 改变量很小，不必移动相机或使 support 外亮度越过 `2/255`；全局质量守卫不能在逻辑上排除此情形。“sham 同量级即停”也没有唯一比率，且本例 target 的平均响应是 sham 的 11 倍，不能用这句概括代替空间控制。

**解除条件：** 在规范合同中固定与无编辑 sham 使用完全相同编码/替换路径的主处理对照，或另设预注册的 edited-versus-sham 直接配对空间效应门；明确其 estimand、正负剂量聚合、replay/negative 比较及所有定位门。保留 `F11−原始 F00` 作为整体管线响应诊断。不能简单逐像素相减两个绝对差图后声称它等于直接因果差异，因绝对值不具可加性。若坚持当前原始 map，必须把 RQ2 缩为“含重新编码流程的复合干预响应位置”，禁止把它归因于所设计的外观 edit；B_local 也需相同的编码对照边界。

## 5. MAJOR

### M-V4-1：G7 仍首次决定核心科学自由度，不能称只做绑定

**位置：** L170–177、190–191、236–242、280、296–309。

已经写明的旋转/平移、camera 网格、权重携带和 top-199 排序应保留。问题在排序前的资格函数仍不是唯一：

1. `binary connected-component` 未指定 4 邻域或 8 邻域；对角相接可使相同候选通过或失败。尺度归一化周长未定义是何种栅格边界长度及除以何种面积尺度。
2. weight histogram 未指定是在全部 Ω（含大量零权重）还是仅 `W>0` 上归一化。`depth-gradient`、`boundary density` 的计算及每个 mask 的汇总权重未定义；“全 target 地图的四分位”未指定分位总体究竟是像素值、候选区域摘要，还是空间块。量化法和 ties 可随后实现，但总体本身必须先定。
3. 两 edit families 还只有名称，没有完整函数、纹理生成规则、剂量表及 LPIPS/CLIP/edge/clipping 数值上界。它们直接定义处理和科学 estimand，不是设备绑定字段。
4. matcher、descriptor、displacement 从何种模型估计、锐度指标和撕裂指标仍无唯一函数，会改变所有 arm 的有效性。
5. “按普通 slot 顺序的第一个未选 source”没有给未选来源的顺序；selection 输出的 slot 列表只包含被选项。必须指定候选 memory/insertion roster 的稳定顺序和资格函数，不能在 G7 临时解释普通 slot 的含义。

这些选择全部发生在结果前，确实能防止一部分结果驱动调参；但“结果前任选一种实现”仍不等于“当前合同已有唯一主统计对象”。**解除条件：** 在新版本中绑定一份规范性 analysis/edit/guard 配置和有限 reference implementation，明确以上公式、数值、总体与顺序，由新审查共同绑定 SHA。可以让 G7 成为该规范合同的组成部分，但需诚实声明统计设计到那个时点才冻结；不能以当前正文 PASS 代替这次新审查。无模型的合成边界样例应验证对角连通、零权重直方图、ties、NaN、空候选和两侧剂量唯一选择。

### M-V4-2：Benefit 的 support 外守卫与全 support 敏感性没有共同有效 reference 域

**位置：** L262–270、274–292。

主 `C_local/C_matched` 是通过真实视图双向可见性得到的共同域，方向正确。但是 `ℓ_out` 被写成 `Ω_i\S_i` 上的 MSE，原 `S_i` 全区也要求评分；这两个集合没有保证 `R` 在对应 target 像素有效、静态、可见、无 hole。主区域允许只覆盖 70%，其余 30% 不能在敏感性里忽然变成可靠 RGB 答案。把 invalid warp 置零、填洞、静默丢弃或要求全域可见，会得到不同数值，尤其会改变 `delta_out=0.0005` 的强制门。

`S_i` 是 fractional map，集合差也应明确为 `Ω\{S>0}`，否则有“补权重 1−S”和“二值补集”两种含义。reference 是实拍不同相机视图，`ℓ(Y,R)` 必须明确使用 target-grid 的冻结 `R_warp,t`，并明确 RGB 插值核/边界及 relative-depth 差的分母；当前文中虽提到 RGB 插值，却没有唯一指定这些评分操作。

**解除条件：** 为每个 target 明定 `C_out,t`、`C_fullsupport,t`，全部与冻结 `V_R,t`、静态域及需要的 `V_O/V_P` 相交；预设覆盖下限、空集/不足动作和完整分母。若必须原 support 全域评分，则要求全域 reference 有效，否则该敏感性记 NA，不能填洞。明确 outside loss 的 paired difference、逐 sign/family/seed/replacement/target 聚合和守卫对象，正负两侧的伤害不能因未声明的平均互相抵消。所有配准只用真实预处理量，不能用 arm 图优化。

### M-V4-3：正的 B_local 是两侧平均优势，不证明分别优于两侧或局部最优

**位置：** RQ3 H1-benefit-local；L274–278、292。

`B_local=0.5(L_plus+L_minus)−L_0` 唯一可计算，但解释仍过强。例：`L_0=0.010`、`L_plus=0.014`、`L_minus=0.009`，则 `B_local=0.0015>delta_B`，尽管负向编辑改善原来源。四个 family×seed 都出现此值仍全部通过，不能支持“原来源同时优于两侧”。在局部二次表达 `L(δ)=c+gδ+hδ²` 中，当前 B 只保留 `hδ²`，完全消去一阶项 `gδ`；因此 B 正并不排除沿某一方向继续改善。

**解除条件：** 二选一并冻结：保留当前式，准确改称“相对对称两侧等权混合的平均局部收益”，禁止同时优于两侧/局部最优推断，并完整报告两侧差；或若 H1 真要求两侧都更差，使用两侧各自超过 SESOI 的合取门，例如 `min(L_plus−L_0,L_minus−L_0)>delta_B`。无须更换 B_matched 的定义；其相对于全部合格替代的均值效用解释目前是适当的。还须按 C-V4-1 区分原始编码与 no-op 重编码 comparator。

### M-V4-4：reference 使用 replacement 的 baseline caliper，且真实时间/身份映射仍未唯一绑定

**位置：** G6；L262–268、280。

10 ms 本身是明确的项目容差；给整数时间戳和唯一排序也是实质改进。但它还需要 `t_target` 是什么真实物理时刻、如何与视频 target 索引对应、同步残差来自哪些观测的定义。生成进程 wall-clock、视频呈现时间和实拍传感器时间不能互换。当前 C1/C2 未证明存在这种 reference，草案对此坦诚，故本问题不授权寻找或补造答案。

reference 的 translation 资格目前是 `|b_R−b_O|/b_O<=0.1`。这能匹配 replacement 与原来源的 source-target baseline，却会排除**位于精确 target 相机中心**的独立 reference：若 `c_R=c_t` 且 `b_O>1e-6`，该比率恒为 1。它反而允许距 target 近似原来源距离的侧视 reference。经过严格 warp，侧视 reference 可以成为合法局部答案；但这需要明确称为 warped held-out multiview reference，不能同时称要求“目标视角 reference”且把上述 source-baseline 比例当目标相机接近度。

同样，“support 内 instance identity”需要确定标签空间和比较对象：support 包含多个实例/背景时，用精确 ID 集合、逐 3D 实例对应还是主实例？仅写缺失/冲突即拒绝不能定义何为相同。L266 的 RGB 中位残差还未指出是哪一对真实视图/时刻计算；多个参考目标时，必须保存 `R_t` 或明确一张 R 同时满足所有 t。

**解除条件：** 将 reference 与 replacement 两种相机资格分开。精确 target reference 应有独立的 target-camera 平移误差容差；若采用可重投影侧视答案，明确唯一资格、每 target reference、覆盖和尺度依据。固定真实 timestamp 映射、同步误差定义、instance 标签比较规则及动态/亮度检查的视图配对。保留无法取得合格 reference 即停止 RQ3，不得由 ID0、生成图或放宽时间阈值补齐。

## 6. MINOR

### N-V4-1：等号和 target 粒度存在局部冲突

L196“**不超过** delta_I 即停”意味着只有严格 `>` 才过，而 L218 用 `>=`。一单位平均 RGB 的有理数边界并非不可能达到，应固定一种。L183 的“target 响应”与 L212 的先 frame 后 episode 平均需明确：Influence 是 episode gate 还是每 frame gate；目前 §6.1 最明确的是 episode 平均，应保留该含义并报告逐帧值，不把它写成每帧均达 SESOI。Localization 在 L252 的所有 `f×s×t` 均过门及 episode 等权摘要已经唯一，不应被 episode 平均取代。

### N-V4-2：辅助修复包的 SHA 不能从旧日志复制

本轮实际 `TOP_VENUE_METHOD_FIXES_FOR_V3.md` whole-file SHA 为 `f9b506bf...21863`，与最新项目日志曾记载的 `42a4b426...412f` 不同；文件还含有自己定义的 canonical hash，三者不能混写。本报告只依赖实测文件作辅助阅读，不对哪次变动下结论。未来 manifest 应记录当前实测 whole-file SHA 和历史版本；不需要回改旧日志。

### N-V4-3：静态 V2 自报跨解释器通过仍不是本次独立核验

README 清楚区分 producer 与 reviewer，修订方向正确。本轮没有打开它引用的两 JSON 和脚本，故不能据此给“当前三文件已独立 PASS”。若要关闭此工程证据门，另做绑定精确 SHA 的只读审计；它仍不替代 hook 合成测试或真模型证据。

## 7. 运行前门与允许下一步

1. 修正 C-V4-1 的主对照与定位归因，统一 B_local 的编码 comparator；用手工有限样例证明均匀净 edit 加局部 sham 不会获“编辑具有局部作用”的 PASS。
2. 修正 M-V4-3 的 B_local 假设与公式含义；两侧差分别可复算。
3. 固定 M-V4-1 的规范性 edit、caliper、guard 与 negative roster；可先做纯合成/源码实现。未实现 hook 本身继续诚实标 `API_MISSING`。
4. 若保留 Benefit，关闭 M-V4-2/4 的独立 reference、真实时间、identity、target-grid 评分域与 coverage。做不到则在新范围中关闭 RQ3 arms，最多保留前两项诊断；不能进入 acceptance head。
5. 新协议/规范补充文件精确 SHA 经新统计与源码审查通过后，才有资格进入完整 G7。G0/G1 自然失败及 C1/C2 同等级闭环仍必需；本报告未验证其当前通过状态。
6. observer/replacement patch、全 consumer 清单、进程隔离、mask generator、registration/metric 及无模型 feasibility 均需绑定当前实现并由不同作者复核。没有实物 PASS 就不创建 A0/F00/F10/F01/F11/edit/control/Benefit arm。

没有自然失败、没有 199 个合格 shape/camera masks、source baseline 为零或 reference 不可得，都是**资格/可识别性失败**；不得报告成“已测得因果效应为零”。特别是小相机扰动与低 IoU 严格匹配是否可同时提供 199 个候选，只能由无输出 feasibility 判断；本次没有数据，因此不宣称可行或必然不可行。

## 8. claim、novelty 与可复算性边界

当前允许的结论是“V4 的权重与主要分族合同已显著收口，但仍被新的对照归因反例和 Benefit/规范定义问题阻断”。普通 Select 被条件固定后的作用范围已经表述正确：它不是 Store/Select 全流程总效应。geometry-projected expected locus 不等于 denoiser routing；描述性前 5% 不等于 p 值。B_matched 只比较冻结的匹配替代分布，不能写成 item 的绝对价值。

新增 Spatia、WorldStereo、PlenopticDreamer、LongDiff 以及 I3DM/I²AM/AGRA 等基线边界，在本草案里用于收窄 claim 是正确方向。本次未重新检索其原文，不认证覆盖完整性、出版状态或实现公平性。F10/F01 路径差异也只能提供消费者诊断，不能单独证明“来源身份同步”是新方法。`novelty_authorization=NONE`、未有 method gain、未有跨 scene/consumer confirmation、未达到 PhD/CCF A 成果，均应保持。

## 9. 访问与写入账本

| 动作 | 实际范围/数量 |
|---|---|
| 必需连续性读取 | 项目 AGENTS、PRINCIPLES、MEMORY、最新 LOG；中央 MEMORY 仅关键词查无命中 |
| 科学审查输入 | 精确 V4 全文，多次定位行号；V3 审查；方法修复包的相关前 210 行；静态 V2 README |
| 本地技能 | scientific-critical-thinking SKILL.md 只读；未运行其工具 |
| 原 VMem/pipeline 源码重新读取 | 0；只阅读草案及静态说明中的源码陈述 |
| 静态审计脚本/JSON 执行或读取 | 0 |
| 模型导入、加载、forward、renderer、生成 | 0 |
| C1/C2 tensor/image/pixel bytes 读取/映射/解码/查看 | 0 |
| C1/C2 数据目录扫描、payload 哈希 | 0 |
| S48 arm 创建/执行 | 0 |
| 主草案/旧审查修改 | 0 |
| 写入 | 仅本报告；不编辑共享研究主账，由父任务以精确最终 SHA 追加本次审查事件 |
| 数值反例 | 纯公式推导，不是 synthetic 模型实验、真实数据或视频结果 |

最终：**BLOCKED，S48 execution authorization=NONE，novelty_authorization=NONE。**
