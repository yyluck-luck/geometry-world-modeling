# 创新北极星 V3：Reference-Anchored Interventional Memory Audit

- 冻结时间：2026-09-08T09:35:41Z（北京时间17:35:41）
- 工作简称：`RAIMA`，只为沟通方便，不构成新颖性声明
- 状态：`V3_MEASUREMENT_CANDIDATE_PENDING_FRESH_ADVERSARIAL_REVIEW`
- 方法状态：`NO_METHOD_SELECTED`
- 新颖性授权：`NONE`
- 新模型运行：`0`
- 被替代决策：V2 SHA `574311ced8f5bcbf2ad21854a0f7895195bc49d4fe968012d3f33bca7b662f36`
- 直接触发审查：V2 adversarial review SHA `03b4e3d9b2cd6465f30239364d6234a1f3d40195dd1e51b58d59b2dafa551356`，总体裁决`PIVOT`
- 证据边界：这是结果前研究设计；没有真实source intervention、gap频率、reference utility或方法收益

## 给新手的一句话

V2把“输出没变”叫“模型没用记忆”，把“影响跑到几何区域外”叫“用错位置”。这两句话都太强。V3只测我们真正看得见的东西：

> **一条已经存储、选中且可寻址的历史来源，在严格成对实验中能造成多大可观察输出变化；这个变化与3D投影区域如何对应；它相对可靠的真实参考是帮忙还是添乱。**

先测清楚，再解释机制。当前不再给方法起名字。

## 1. 精确研究问题

### 主问题

在具有稳定source ID、显式检索和可枚举appearance consumer的视频世界模型中，传统retrieval/addressability证据能否预测下列三个操作性量：

1. source-conditioned observable influence；
2. geometry support与输出effect的对齐；
3. reference-conditioned signed utility。

### 可能的非显然发现

只有真实确认性数据通过后，才能报告：

> 在3D地址和检索均成功的条件下，某些历史来源仍表现出可重复的低可观察影响、support-effect不匹配或负reference-conditioned utility；这些现象没有被普通retrieval/return分数解释。

这比“检索失败”更难预料，因为显式3D memory通常被期待把正确历史证据送到正确目标区域。当前仍只是候选。

## 2. 明确删除三种过度解释

### 2.1 不再写“Access–Use Gap”

零输出effect可能来自冗余、抵消、功效不足或edit没有触碰充分统计量。因此只写：

`Access–Observable-Influence Gap (AOIG)`

它表示在指定edit family、source set、target与matched noise下，没有检测到超过预注册最小效应的输出响应。除非另有隐藏状态、中介和冗余实验，不得写“没有使用”。

### 2.2 不再写“Use–Location Gap”

阴影、反射、遮挡、光照和全局布局可能让合理影响超出source的直接3D投影。因此只写：

`Support–Effect Mismatch (SEM)`

它描述effect map与预冻结geometry support的差异。只有support外effect同时使独立reference loss恶化，且多种合理support定义一致，才可升级为`harmful mislocalization`。

### 2.3 不再写“causal Benefit”

同步自然重访仍会受光照、曝光、动态物体和配准误差影响。因此只写：

`Reference-Conditioned Signed Utility (RCSU)`

它是条件于reference roster、metric、edit、replacement、source set、target与seed的操作性效用，不是来源的永久属性，也不是现实世界反事实真值。

## 3. 可识别范围

主分析明确条件于：

`source already stored ∩ ordinarily selected ∩ numerically addressable`

所以本实验不能由post-selection edit识别Store或Select的因果贡献。六级`Store → Select → Address → Influence → Localization → Benefit`只保留为审计清单；正式estimand从Address之后开始。

若源码审计不能枚举全部source-dependent appearance descendant，只能写“两个已枚举consumer接口的析因审计”，禁止写all-path或all-consumer。

## 4. 技术周期与重要性门

这个问题现在可执行，依赖四个同时出现的工程条件：

1. 显式3D memory暴露稳定source ID；
2. 扩散/生成路径可固定noise与RNG并做matched replay；
3. appearance consumer可在post-selection边界被枚举和干预；
4. 3D投影与真实回访数据允许预先冻结support和reference。

这解释“为什么现在能测”，不证明“以前没人想到”。

Hamming重要性也设硬门：若确认性研究中，普通指标通过但至少一个操作性gap出现的scene比例低于20%，或其reference-conditioned loss量级不超过reference自身不确定性，则停止“领域大象”表述，只保留有限诊断。

## 5. 两阶段数据设计，防止按结果挑样本

### Stage D：发现性本机pilot

- 固定使用已经排队的B0/C1/C2；
- B0已见，C1/C2协议已受现有工作影响，三者全部只能作discovery；
- 不估计总体频率，不做显著性，不挑漂亮样例当主结果；
- 目的仅是检查自然失败、hook可行性、量级、预算与reference可靠性。

Stage D即使发现大effect，也不能成为“系统性”主张。

### Stage C：结果前冻结的确认性cohort

最低设计：

- `8`个未用于协议设计的独立物理scene；
- 每scene `2`条预定义return trajectory；
- 每trajectory `5`个固定seed；
- 共`16`个scene-trajectory主单位、`80`个ordinary baseline seed-run；
- source/target进入规则在看生成像素前冻结；
- 成功与失败trajectory全部保留，不能只审计自然失败。

独立统计单位是scene；trajectory嵌套在scene，seed只是配对重复，不冒充独立样本。若本机预算无法完成，Stage C保持未运行，不能降低样本数后沿用确认性表述。

## 6. Reference可靠性合同

Stage C先限定静态或状态锁定场景。每个target至少要有`3`个从未进入模型memory的合格reference观测；每个reference继续满足S48 V6的同步、pose、rotation、FoV、identity、validity和warp residual门。

定义reference不确定性：

`Delta_ref = max pairwise primary-loss among the eligible reference roster`

定义有效效用最小量：

`Delta_U = max(0.001, 2 * Delta_ref)`

若合格reference少于3个，或`Delta_ref > 0.001`，该target只能作描述性案例，不能进入RCSU主分析。动态场景必须另有状态同步或观测模型，不与静态主分析混合。

Primary loss固定为common-valid support上的normalized RGB MSE。LPIPS、几何误差与support外loss是secondary；若不同合理metric给出相反符号，RCSU机制解释被否决。

## 7. 三个操作性estimand

### 7.1 AOIG：可观察影响不足

对source `i`、target `t`、consumer组合 `c`、edit family `f`和seed `s`：

`E(i,t,c,f,s) = mean_pixel |Y_edit - Y_same_path_zero|`

控制后的直接量：

`D = E_target - max(replay_p95, E_negative)`

固定最小可观察效应：

`Delta_I = 0.5 / 255`

每个source-target只有在以下条件全部成立时才标记`operationally insensitive under tested interventions`：

1. 已通过Store/Select/Address运行证据；
2. 已知consumer positive control在5/5 seed都满足`D >= Delta_I`；
3. 两个预注册in-distribution edit family在5/5 seed都满足`D < Delta_I`；
4. same-path zero、exact replay、sham与matched unselected-source负控全部通过；
5. 两类edit没有改变token数、layout、顺序或非目标source。

即使成立也不写“未使用”。若不同edit family方向不一致，只报告intervention sensitivity。

### 7.2 SEM：support与effect不匹配

Localization只使用raw target matched-zero direct map，不做逐像素negative/replay相减。定义：

`L_area = effect_mass_inside / effect_mass_total - support_area_fraction`

基础SEM仅是描述性量。标记`harmful support mismatch`必须同时满足：

1. target influence已通过；
2. `L_area <= 0`在至少4/5 seed和两个edit family上成立；
3. base support与结果前冻结的uncertainty-dilated support给出同方向；
4. support外primary reference loss相对matched zero增加超过`max(0.0005, 2*Delta_ref)`；
5. depth、pose、shape和camera placebo不产生同等结果。

若support外effect改善reference，或support定义改变结论，就不能写错位。

### 7.3 RCSU：reference条件式signed utility

对ordinary source reinsertion `O`与matched replacement `P`：

`U_i = loss(Y_P, R) - loss(Y_O-reinsert, R)`

正值表示在该reference与protocol下保留O优于P，负值表示P优于O。每个source-target的符号要求：

- 5个seed的median绝对值`>= Delta_U`；
- 至少4/5 seed同号；
- 三个合格reference分别计算时同号；
- source-local与全局主损失不出现“局部改善靠别处明显恶化”未披露；
- replacement分层完整报告，不把一次P的结果当来源固有标签。

若reference或metric改变符号，只报告不稳定RCSU。

## 8. 主endpoint与统计规则

### Primary endpoint

每个scene先把两条trajectory中的全部合格source-target聚合，形成一个描述性的scene-level `retrieval–operation discrepancy rate`：

`retrieval/address passes AND (AOIG OR harmful SEM OR negative stable RCSU)`

先把一个scene定义为阳性：其两条trajectory聚合后的retrieval–operation discrepancy rate `>=20%`。进入下一阶段的最低门：

- 至少`5/8` scene的retrieval–operation discrepancy rate `>=20%`；
- 8个scene等权平均rate `>=20%`；
- leave-one-scene-out后平均rate仍`>=15%`。

在8个scene可视为独立抽样的前提下，`5/8`对应对`H0: scene-positive probability <=0.20`的单侧精确二项尾概率`0.0104064`；两侧95% Clopper–Pearson下界约`0.244863`。这只是结果前go/no-go门和小样本敏感性说明，不是人口比例的精确估计；若scene来源相关或复用同一物理环境，该推断无效。

### Secondary endpoints

- AOIG、harmful SEM、negative stable RCSU分别的scene-level rate；
- retrieval/access score对三个endpoint的held-out预测增量；
- source、target、trajectory与seed异质性；
- support外质量、相机服从、wall time与峰值内存。

三项secondary families使用Holm family-wise `alpha=0.05`。置信区间以scene为cluster；16个trajectory不能冒充16个scene，80个seed-run不能冒充80个独立样本。

### Missingness

- 每个预定run都留在CONSORT式flow；
- 相机失从、全局崩溃、模型失败、hook失败、reference失败分别计数；
- 主分析只对预定义eligible source-target计算，但同时报告以全部计划单位为分母的worst-case sensitivity；
- 禁止删除失败seed、换trajectory或补跑直到“成功”。

## 9. 交互只作机制follow-up

来源效用可能冗余、协同或冲突。只有negative stable RCSU已跨scene成立后，才对普通选中集合内预先排序前两来源做`2×2` factorial：

`I_ij = L_11 - L_10 - L_01 + L_00`

其中四格使用相同noise/RNG、token数、layout、consumer顺序与matched reinsertion。交互进入方法研究的最低门：

- `median |I_ij| >= Delta_U`；
- 至少4/5 seed同号；
- 至少4/8 scene出现；
- additive模型之外的leave-one-scene-out utility prediction绝对误差下降至少10%；
- Holm校正后仍通过；
- 预算内完整报告所有预注册pair。

若交互只有统计显著但低于effect floor，或不改善held-out prediction，就删除集合治理路线。

## 10. 方法保持空白，按真实失败分流

当前`NO_METHOD_SELECTED`。Stage D/C之后才按证据选择：

| 真实剩余失败 | 只允许进入的研究问题 | 必须先胜过的近邻/基线 |
|---|---|---|
| 稳定AOIG | 哪个明确consumer/表示瓶颈抑制source effect | per-source token、source ID、独立/统一attention、容量匹配 |
| harmful SEM | 几何投影在哪个具体下游路径失去空间约束 | WorldStereo、Geometry-as-context、Spatia、I3DM式局部注入 |
| negative RCSU但近似可加 | 普通source reliability是否足够 | pose/retrieval/attention/age gate、Ada-RefSR、TetherMem |
| negative RCSU且强集合交互 | 视频特有set-conditioned机制能否预测风险 | CUE-R、CF-RAG、CoRM-RAG、CAMA思想迁移、统一attention |
| 无稳定gap | 不开发方法 | 报告负结果并停止当前创新线 |

`re-observe`从被动生成任务删除。只有未来存在可审计observation API、动作可达性、状态同步和固定成本模型时，才另立active sensing研究。

## 11. 顶会/强预印本碰撞后的边界

以下均不能作为本项目的新意：

- access不等于utilization：MomentSeeker、UtilMem；
- harmful/conflicting evidence：ClashEval、CUE-R；
- counterfactual evidence arbitration：CF-RAG；
- counterfactual teacher到轻量critic：CoRM-RAG；
- provenance依赖与主动恢复：CAMA；
- 视频query/region/age条件memory routing：TetherMem；
- 旧状态删除/更新：GaME、WorldMM、WorldCraft、Spatia、StableWorld；
- reference-based或hierarchical评价：Ref4D-VideoBench、Hi3DEval；
- source binding、geometry gate和global memory：Movie Weaver、WorldStereo、Geometry-as-context、VRAG、SPMEM。

当前只允许检验的窄空间是：**显式视频世界memory中，ordinary-selected runtime source在已枚举appearance consumer上的reference-anchored操作性响应，及3D support、输出effect与reference utility三者之间的联合关系。** 没有真实新现象时，这个交集也不能靠拼接组件成为贡献。

## 12. Supervisor-Skills 2.3检查

| 2.3路线 | V3动作 | 仍可能失败的证据 |
|---|---|---|
| 第一性原理 | 从“有memory”回到“历史证据是否改善真实生成”，并把不可识别的use/correct/causal措辞降级 | 普通retrieval/reference指标已充分预测全部结果 |
| 隐藏假设 | 显式检验retrieval/address是否高估observable influence与reference utility | gap rate或effect低于硬门 |
| 房间里的大象 | 用完整ordinary cohort估计retrieval–operation discrepancy，不只挑失败case | 少于5/8 scene，或后果小于reference uncertainty |
| 技术周期 | stable source ID、matched replay、consumer hook与3D support使审计可执行 | all-consumer不可枚举或第二架构不支持 |
| Hamming问题 | 长时世界memory能否知道历史证据何时无效/有害 | 只在VMem实现bug或单scene成立 |

当前结论仍是`FOLLOWED_IN_PROCESS; PARADIGM_SHIFT_NOT_ESTABLISHED`。

## 13. Kill rules

1. C1/C2没有相机服从的自然失败：Stage D停止，不制造失败。
2. positive control不敏感：AOIG不可识别，停止。
3. edit family/replacement/token layout主导方向：降级为intervention sensitivity。
4. support外effect有益或support定义不稳：删除mislocalization。
5. reference不确定性与utility同量级或符号依赖metric：删除utility机制解释。
6. 8个确认scene中少于5个过主门：删除systematic/elephant主张。
7. all-consumer不可枚举：降级为局部接口审计。
8. interaction不改善held-out prediction：删除集合方法。
9. 普通gate、TetherMem式routing或统一attention解释全部增量：删除方法贡献。
10. 第二个stable-source架构不复现：降级为VMem-specific诊断或bug report。

## 14. 当前允许和禁止的对外表述

允许：

> 我们正在结果前冻结一个reference-anchored interventional audit，用于检验3D retrieval/addressability是否高估某条已选视频memory source的可观察输出影响、几何support对齐和reference-conditioned utility。该问题和阈值仍待独立审查与真实数据验证。

禁止：

- 模型没有使用该来源；
- 模型把来源用错位置；
- 已识别来源的真实causal Benefit；
- 已发现系统性memory failure；
- 已提出新的routing/arbitration方法；
- 已实现颠覆式创新或达到PhD/CCF A水平；
- 保证导师反应或录用。

## 15. 下一门

1. 非作者对V3的estimand、阈值、样本量、reference合同和新增近邻做fresh审查；
2. C1 V7、C2 V6继续source-only修订与fresh双审；
3. S48 V6独立审查需吸收V3的可识别性措辞；若S48 V6与V3冲突，先修协议，不运行arm；
4. 只在合法C1/C2 baseline结果产生后执行Stage D；
5. Stage C必须另行冻结完整数据manifest、power/sensitivity与计算预算。

## 16. 一手来源

- Supervisor-Skills 2.3：<https://github.com/HKUSTDial/Supervisor-Skills/blob/main/handbook/02_Idea_Generation/2.3_%E8%BF%9B%E9%98%B6_%E5%A6%82%E4%BD%95%E5%81%9A%E9%A2%A0%E8%A6%86%E5%BC%8F%E5%88%9B%E6%96%B0.md>
- TetherMem（arXiv 2026）：<https://arxiv.org/abs/2608.26902>
- CF-RAG（ICLR 2026）：<https://proceedings.iclr.cc/paper_files/paper/2026/hash/1c078897dc08d46091d0d361d9955c6b-Abstract-Conference.html>
- CoRM-RAG（SIGIR 2026/arXiv）：<https://arxiv.org/abs/2605.01302>
- CUE-R（arXiv 2026）：<https://arxiv.org/abs/2604.05467>
- CAMA（arXiv 2026）：<https://arxiv.org/abs/2608.19701>
- UtilMem（arXiv 2026）：<https://arxiv.org/abs/2608.30508>
- GaME（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/html/Yugay_Gaussian_Mapping_for_Evolving_Scenes_CVPR_2026_paper.html>
- WorldMM（CVPR 2026）：<https://openaccess.thecvf.com/content/CVPR2026/html/Yeo_WorldMM_Dynamic_Multimodal_Memory_Agent_for_Long_Video_Reasoning_CVPR_2026_paper.html>
- WorldCraft（arXiv 2026）：<https://arxiv.org/abs/2605.25077>
- ClashEval（NeurIPS 2024 Datasets and Benchmarks）：<https://proceedings.neurips.cc/paper_files/paper/2024/hash/3aa291abc426d7a29fb08418c1244177-Abstract-Datasets_and_Benchmarks_Track.html>
- Causal LLM Routing（NeurIPS 2025）：<https://proceedings.neurips.cc/paper_files/paper/2025/hash/357774d53e5ee21c5f08ba779e3b5dd9-Abstract-Conference.html>
