# S48 GeoCausal 最小否证实验：独立统计／因果复审 V3

- 审查角色：`/root/c1_blind_score_builder`，作为全新独立统计／因果审查者
- 审查时间：2026-09-08T14:36:41+08:00
- 被审 V3：`S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT.md`
- V3 SHA-256：`02f3be4120ba4c7ee7da719313c1d430d133185cafbe56bb80eea3788b5896c1`
- hook 可行性审计 SHA-256：`cb68ad5ed3d9be8e3db03eccb1f90fd00ec0925c68e41e59bba00cebf4561344`
- Python 3.12 静态审计 JSON SHA-256：`94f763c6ba0946b058633f4c5889fc019a953d632e776bf4b31ec5fa2daf1012`
- Python 3.13 静态审计 JSON SHA-256：`0cf9eb7671a5591c90d260197a4e5bf05a76b01dc2e4573ee0b342af0a1ea140`
- V2 独立审查 SHA-256：`3470ae9a421bc3b8ce916b8e6959d36d49e1ccc9f12e7002e841fdd22ff1b372`
- 审查边界：只读上述文字、JSON及V2审查；没有运行或导入模型，没有运行hook/audit脚本，没有打开、映射、解码或查看C1/C2 tensor、image、pixel；没有修改V3草案
- **总裁决：BLOCKED**

## 1. 独立结论

V3再次是实质修订。它明确把199个matched masks降为描述性placebo
排名，承认没有assignment/exchangeability，删除了随机化p值和显著性
含义；它也强制每个arm使用fresh process、按指标拆分replay floor、固定
two-family × two-seed的intersection式继续门、定义uint8 sRGB主数值域，
并增加双向common-visible Benefit和I3DM/I²AM/AGRA边界。这些修改真正
关闭了V2的大部分问题。

本轮仍不能PASS。主要原因已经不是“排名不是p值”，而是这个描述性排名
本身尚未唯一：真support使用fractional `w_i(p)`，但V3没有定义每类
placebo的权重场、变换/碰撞/归一化规则以及加权面积与二值拓扑caliper的
关系。因此`mass(M)`、`L^matched`与`r_mask`存在多个都符合当前文字、但
会给出不同继续/停止裁决的实现。把metric代码留给G7能够阻止立即运行，
却不能替代预注册对主要科学统计量的定义。

此外，Benefit虽然已有双向z-buffer、重投影、深度与hole门，但仍只要求
记录reference时间，没有冻结时间容差、动态区域排除、多个reference的
确定性选择以及“同一对象identity”的可复算判据。它仍允许把时间变化或
reference选择差异解释成source benefit。Localization的support还来自“平均
target pose”检索图，而不是每个真实输出target的相机/K；Influence门也没有
超过sham/negative实际响应，Benefit局部门没有把两个edit family纳入唯一
聚合。这三处都可能在不违反现有文字时改变主裁决。

V3当前的G0/G7确实是有效的fail-closed门，所以本裁决不表示可以绕过它们
运行。裁决的含义是：V3还不能成为G7的上位统计合同；先修正下述定义，再
让新审查者复审。

| 等级 | 数量 | 含义 |
|---|---:|---|
| CRITICAL | 1 | RQ2唯一主统计量仍非唯一，可能改变Pilot-C继续/停止 |
| MAJOR | 5 | target-frame support、control-calibrated Influence、Benefit reference/聚合及hook实施仍需收口 |
| MINOR | 3 | 静态回执 provenance、seed-specific replay符号和一个次要DiD仍不完全可复算 |

## 2. V2 CRITICAL／MAJOR逐项关闭审计

状态只评价V3文字与随附静态证据，不把未来G7或尚未实现的hook当成已经
完成的事实。

| V2编号 | V2问题 | V3证据 | V3状态 | 判断 |
|---|---|---|---|---|
| C-V2-1 | `p_mask`无可交换assignment | §1 RQ2、§6.2、§7.1反复声明只作描述性尾部rank，不称p值/显著性/零分布 | **CLOSED_AS_INFERENCE_CLAIM** | 未校准p值问题已真正关闭；但fractional placebo权重与family mixture使新的描述性主统计量仍非唯一，形成下述C-V3-1 |
| M-V2-1 | 当前源码不返回slot/support共同hook | §4.1明确承认接口缺失，并要求同次选择物化slot、全surfel membership、稀疏权重、appearance轴和trace；G3/G7失败即停 | **CLOSED_AS_A_HARD_PRECONDITION** | 文本不再假装当前源码已经提供support；静态审计也一致证明“边界存在、API缺失”。实现仍未完成，不能运行 |
| M-V2-2 | mask冻结阶段矛盾、199个可行性未知 | §6.2把matching限于干预前source/geometry；在任何A0/F00/F11/Benefit前做无生成输出feasibility，固定seed、唯一mask、proposal/拒绝flow和失败即停 | **PARTIAL** | post-treatment matching漏洞已关闭；但placebo权重语义、family配额/汇总与negative-placebo判据未唯一化 |
| M-V2-3 | `reset()`遗漏真实状态 | §5.4禁止当前SHA的任何in-process reset，每个arm从同一只读snapshot启动fresh process，并记录PID/process-group/return/resource/receipt | **CLOSED** | 当前源码下没有reset逃生分支；未来修复必须另SHA双审 |
| M-V2-4 | 不同单位共用一个replay floor | §5.4分别定义px、RGB、ratio、percentage-point的A0 floor与阈值，§5.4/§6.1冻结PNG/uint8/sRGB域 | **PARTIAL** | 数学量纲已对齐；但Pilot-B controls未全部过守卫，Influence也未把sham/negative floor纳入效应门 |
| M-V2-5 | reference/common-visible不可计算 | §6.4给正反投影、1 px、相对深度0.02、双向z-buffer、覆盖0.70、hole 0.10、pose/FoV门和common support损失 | **PARTIAL** | 空间配准显著改善；时间、动态对象、reference候选选择与identity仍没有唯一资格规则 |
| M-V2-6 | 多edit/dose/seed主图可事后选择 | §5.3固定±dose平均为`d_{f,s}`，2 family × 2 seed四图逐一通过，单位摘要取最小值，控制门固定 | **PARTIAL** | Influence/Localization主聚合已唯一；`B_local`仍没有family×seed索引或跨family唯一规则 |
| M-V2-7 | I3DM/I²AM/AGRA与强基线边界缺失 | §8逐项列入proxy/baseline，§10–§12明确3D support、区域图、空间干预、gate均不是单独创新 | **CLOSED_FOR_CURRENT_SCOPE** | 当前仍是VMem-scoped measurement proposal，novelty authorization保持NONE |

因此，V2唯一CRITICAL的**推断称谓问题已经关闭**；7个MAJOR中2个关闭、
1个按硬门关闭、4个仍部分关闭。新C-V3-1来自V3新增fractional support
与placebo统计之间的接口，而不是恢复旧的p值主张。

## 3. CRITICAL

### C-V3-1：fractional真support与placebo library之间没有唯一测度，RQ2主门不可复算

随附hook审计§4给真实source建议了多值归因：若同一可见surfel属于多个
普通运行已选source，则`w_i(p)=1/|A(p)|`。V3 §6.2随后以该fractional权重
定义：

`mass(S_i)=Σ w_i(p)d(p)/(Σd+ε)`，

`area_i=Σw_i(p)/|Ω_i|`。

这两式对真实support内部一致，也正确避免把共享pixel复制成多个独立
pixel。但V3对`mass(M)`只写“同上”，没有定义假support `M` 的
`w_M(p)`。至少以下实现都符合现有自然语言，却会改变结果：

1. 所有placebo使用二值权重1；
2. 平移/旋转真实support时搬运fractional权重，未选source和camera
   placebo使用二值权重；
3. 每类placebo按自身`surfel_to_all_sources`重新分配fractional权重；
4. 变换后对碰撞pixel求和、取最大值或重新归一化；
5. area ±2%匹配使用`Σw`，而连通分量/周长/IoU使用`1[w>0]`，或全部
   使用二值面积。

这不是呈现细节。不同权重会同时改变`mass(M)`、matched median、尾部
rank、面积caliper的入选集合，最终改变`r_mask<=0.05`是否通过。

三个proposal family的混合也没有在V3中限定固定配额或family-specific
判据。G7虽要求“matched-placebo generator”，§6.2也禁止事后改变
mixture，但当前上位协议允许把199个候选按任意预冻结比例分配给容易或
困难的family。一个pooled top-5% rank因而取决于任意mixture权重。最后
一句“未选source投影与camera-geometry placebo均不能通过同一四条件门”
还没有说明是每个mask、每个family摘要、leave-one-out rank，还是对应的
negative-control arm；这些对象已经同时充当library member和falsification
control。

**解除条件：** 在V4正文中直接冻结或精确绑定一份规范性合同，至少包括：

- 真support明确采用的多值归因式，以及`Σ_i w_i(p)`的闭合/未归属规则；
- 每个proposal family的`w_M(p)`、像素变换、边界裁切、碰撞、孔洞、
  interpolation、重新归一化和去重规则；
- weighted area和binary topology各自使用哪个字段，所有caliper的分母；
- 三family固定proposal分布、接受后目标配额、短缺动作和pooled mixture；
- observed support在每个family内分别报告的percentile/enrichment及唯一
  family-level继续规则；若保留pooled rank，只能作为精确mixture内的
  附加描述；
- “placebo不得通过”的唯一对象、统计量、比较集合以及是否leave-one-out。

该合同及代码SHA必须在任何生成输出前进入G7并fresh review。修复后仍应
称matched-placebo descriptive enrichment，不能重新使用p值语言。

## 4. MAJOR

### M-V3-1：检索用“平均target pose”support不能直接充当每个输出target frame的局部性support

可行性审计明确记录：当前检索先把surfels渲染到**平均target pose**，由此得到
`retrieval_surfel_index_map`。这个图可以证明普通选择使用了哪些可见surfel，
却不自动与每个被评分输出frame的像素坐标、遮挡和视场相同。V3 §6.2把同一
`S_i`直接用于`d_{f,s}(p)`，没有要求针对每个实际输出target的`c2w/K`重新投影
同一批已归因surfel。执行者可以使用平均pose图、最近target图或逐frame图，三者
都会改变`mass`、面积、placebo匹配和尾部rank。

即使完成逐frame投影，它也只能叫“VMem检索几何推导的预期作用区域”；它不是
渲染像素确实经过该source的routing证明。输出干预的局部响应才是被检验量。

**解除条件：** 保留同次普通选择的surfel/source归因，随后对每个实际输出target
的精确`c2w/K`，用冻结resolution、投影、z-buffer、遮挡、边界和无效深度规则
重投影；在任何对应arm前封存每帧权重图及SHA。检索平均pose图只用于选择审计，
不得替代逐target评价support。论文与G7必须使用“geometry-implied expected
locus”边界，不能把support本身称为pixel routing证据。

### M-V3-2：Influence没有超过实际非目标控制响应，且Pilot-B守卫未覆盖全部arm

当前主门为`D_{f,s}>tau_output,s+delta_I`，同时只要求sham与未选source
negative不超过这个相同界。于是target可以只比negative大任意小的正数，仍与
negative一起贴近同一阈值两侧而通过；这没有证明target响应相对实际非目标控制
还达到预注册SESOI。

此外，§5.4明确把相机/画质守卫施加于F11及Benefit placebos；§5.3却用F10、
F01、sham、未选source negative和positive control决定路径完整性与停止。
这些Pilot-B arm没有被明确要求逐一过相同守卫。positive control和F10/F01
可能因相机漂移或全局崩坏越过响应下界，从而被误读为consumer/path响应。

**解除条件：** 对每个family/seed分别冻结并报告replay、sham及同edit/dose的
未选source negative。目标Influence至少满足
`D_target,f,s > max(tau_output,s, D_sham,s, D_negative,f,s) + delta_I`；若保留
多个未选source negative，预先规定为逐项全部比较或取其最大值，不能pooled后
选择。matched-support的三个proposal family仍按C-V3-1分别处理，不能混作
Influence arm。所有进入response、path-conflict、control或Benefit判定的生成arm都必须
对同seed F00通过同一套逐指标相机/整体质量守卫。positive control还必须同时
满足静态injection trace；守卫失败不能算response，也不能用另一个arm替代。

### M-V3-3：Benefit的空间配准已操作化，但时间、动态内容和reference选择仍可改变收益符号

V3 §6.4的双向重投影、深度、z-buffer、coverage和hole门实质关闭了V2的
单向support漏洞。但G6只说相机/时间/身份“可复核”；正文只给相机/FoV
数值阈值，没有给：

- reference相对target/source的最大时间差及单位；
- 动态物体、遮挡变化、光照突变的预处理mask和失败门；
- 若有多个未进入memory的真实reference，按什么预冻结候选清单和确定性
  规则选择唯一`R_i`；
- “同一对象identity”的标签来源、冲突处理和机器可判failure code；
- “平移baseline相对差<=10%”的精确分子、分母与零baseline动作。

只封存timestamp不会使不同时间的RGB成为同一质量答案。当前规则允许两个
执行者在不看Benefit arm的前提下，仍选出不同reference/动态mask并得到相反
`B_local/B_matched`。这会破坏RQ3的唯一性。

**解除条件：** 在正文/G7必填schema中加入固定reference候选roster与唯一
selection rule、数值temporal caliper、动态/遮挡mask来源和代码SHA、identity
oracle与分歧动作、baseline公式及零分母停止规则。所有资格只能看预处理
reference/source/geometry，且在第一个Benefit arm启动前封存。无法满足时
维持现有正确动作：RQ3停止，不能发展acceptance head。

### M-V3-4：`B_local`没有family索引，两个edit family的Benefit聚合仍可事后选择

§5.3说两个edit family × 两个seed的四张图分别通过Influence和Localization；
§6.4却把局部收益写成没有family索引的`B_i^local(delta)`，只要求“两个paired
seed”通过。当前文字允许执行者只用曝光/白平衡族、只用纹理族，或先在family
内平均后再按seed判断。三种实现都合规，但可能给出不同Benefit符号与继续门。

**解除条件：** 把局部收益写成`B_local,f,s`，冻结每个family的±dose、每个seed
的reference/common-visible集合和唯一单位摘要，并要求2 family × 2 seed四项
全部超过`delta_B`且与`B_matched,s`符号一致；或者在任何输出前只指定一个明确
的Benefit primary family，并把另一个永久标为不进入RQ3 gate的敏感性分析。
不得依据Influence/Localization/Benefit输出选择family。

### M-V3-5：hook缺失被正确设为硬门，但§11仍把规格写成了“已加入可执行hook”

两份静态JSON除时间外内容一致，都把当前源码判为
`SOURCE_BOUNDARY_EXISTS_BUT_SUPPORT_API_MISSING`。可行性审计也明确说必须
先写observer/controlled-replacement patch并重新双审。V3 §99–109对此陈述
诚实，G3/G7也能阻止现源码运行。

但§11允许结论写“加入可执行的source-support hook”。目前加入的是**待实现
合同**，不是可执行hook。这个措辞会把source feasibility误报为implementation
evidence。

**解除条件：** 在patch、合成trace、全consumer枚举和fresh双源码审查完成
前，将其改为“规定了hook合同且当前API仍缺失”。G7必须绑定实际导入源码、
patch、observer output schema、consumer enumeration和测试回执SHA；不能只
绑定自然语言审计。

## 5. MINOR

### N-V3-1：两份静态JSON没有自证Python版本或审计程序身份

`SOURCE_HOOK_STATIC_AUDIT_PY312.json`与`...PY313.json`除`created_utc`外完全
一致，所有布尔检查均为true，源SHA也一致。但JSON内部没有
`python_version`、interpreter path、command、audit script SHA、exit code或
reviewer role。文件名不能独立证明跨版本执行。它们可作辅助静态证据，不能
单独充当未来hook的双解释器或双作者源码审查。G7回执应加入这些字段并绑定
输出SHA。

### N-V3-2：`tau_output`与`tau_output,s`符号需要唯一化

§5.1把所有F00–F00配对最大值写成`tau_replay`/`tau_output`；§6.1改用
`tau_output,s`。请明确每个seed单独以至少3次replay取最大值，还是跨所有
seed取一个更保守最大值。二者都可，但必须只有一个公式，并同样用于sham、
negative和positive control。

### N-V3-3：Benefit末尾的common-support matched-placebo DiD尚无公式

§6.4要求“再报告common-support相对matched-placebo的difference-in-
differences”，但没有指定四个cell、placebo对象和聚合。若它只是次要探索，
应明确标为exploratory并禁止进入继续门；若是稳健性门，则需给唯一公式。

## 6. 已确认关闭且不应回退的设计

以下修改是正确的，后续修订不应删除：

1. estimand只叫baseline-selected/addressable source的post-selection
   downstream appearance effect；Store→Select total effect另立实验；
2. 只冻结处理前`Z/G`与非目标初态，目标appearance的CLIP、VAE/latent、
   attention、denoising、output和writeback descendants全部重算；
3. C1→C2固定CAL选择、first eligible source和CAL/CONF scene永久隔离；
4. 当前源码所有arm强制fresh process，禁止使用已知不完整`reset()`；
5. Influence/Localization的two-family × two-seed × symmetric-dose map已唯一化
   并要求四者全部通过；
6. RGB域、SESOI、epsilon、empty/full/zero-mass退化规则和逐指标同单位floor；
7. independent reference、双向common-visible与support外非劣门；
8. S48不给总体p/CI，S49另冻scene-level estimator、power、multiplicity；
9. I3DM、I²AM、AGRA、TetherCache、CUE-R和普通gate均作为直接边界，
   novelty authorization保持NONE。

## 7. 运行前唯一解阻顺序

1. 修正C-V3-1，唯一化fractional support到每类placebo的测度、family配额与
   family-level描述性判据。
2. 用每个实际target frame的冻结camera/K重投影同一归因surfel，封存逐帧
   geometry-implied expected locus；平均target pose图只留作retrieval审计。
3. 把Influence门改为超过replay、sham和各预注册未选source negative实际响应
   的最大值再加`delta_I`，并把逐指标相机/质量守卫扩展到F10/F01及全部
   control/Benefit arm。
4. 修正reference roster、时间/dynamic/identity/baseline规则；若做不到，在协议
   中预先删除RQ3和Benefit arms。
5. 唯一化`B_local,f,s`的family × seed聚合，或在任何输出前指定唯一primary
   Benefit family并把其余永久排除出RQ3 gate。
6. 把§11的hook表述降为“合同待实现”；实现最小observer/replacement patch，
   绑定精确源码与合成trace，并由两个新角色双审。
7. 生成包含上述字段、所有代码/config/artifact SHA和明确状态机的G7；由未
   参与撰写/实现的统计与源码审查者fresh review。
8. 只有新的V4审查PASS、G0–G7实际证据全部满足，才可启动第一个S48 arm。

## 8. 最终裁决与允许边界

**BLOCKED。** V3正确解决了最危险的虚假随机化p值称谓，也关闭了fresh
process、单位、聚合和近邻边界的大部分漏洞；但RQ2的fractional
matched-placebo主统计量仍可由多个合规实现得出不同裁决。平均target pose
support尚未被逐实际camera/K重投影，target Influence也未越过实际非目标控制
响应加SESOI；RQ3还可能混入时间/动态/reference选择差异并事后选择edit
family。因此本版不能作为S48 arm的统计授权。

当前允许继续：V4文字修订、placebo-weight/reference合同、hook代码与静态/
合成测试、双源码审查、G7 schema和无生成输出的feasibility实现。当前禁止：
A0/F00/F10/F01/F11、edit/control/Benefit模型arm，读取既有C1/C2 tensor/image/
pixel来调support、mask、reference或阈值，以及任何Influence/Localization/
Benefit/新颖性/顶会水平主张。

## 9. 访问与授权账本

- 被审V3、hook可行性审计、两份静态JSON、V2审查：只读
- V3草案修改：0
- pipeline源码重新读取：0；本轮只审查已封存的静态审计证据
- 模型导入/运行：0
- 生成/renderer/readback调用：0
- C1/C2 manifest、receipt、event读取：0
- C1/C2 tensor body读取或array映射：0
- C1/C2 image/pixel打开、解码或查看：0
- S48 arm执行：0
- 本裁决授权S48执行：否
- 本裁决授权新颖性或方法主张：否
