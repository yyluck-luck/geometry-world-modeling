# S48 GeoCausal kill experiment preregistration draft V2 (source-only V7)

- Package status: `SOURCE_ONLY_V7_CANDIDATE_PENDING_FRESH_INDEPENDENT_REVIEW`
- Execution authorization: `NONE`
- Model/arm authorization: `NONE`
- Novelty authorization: `NONE`
- Scientific-result count: `0`
- Real C1/C2 array or pixel access in this package: `0`
- RAIMA language anchor: `work/S43_paradigm_shift_audit/INNOVATION_NORTH_STAR_V3.md`, SHA-256 `f0e5893ad4892f11f36641476f8858ca9347db4075b35b32faf5beaf4ce102aa`
- Repair trigger: `INDEPENDENT_STATISTICAL_REVIEW_V6.md`, SHA-256 `9c6900e18388519d9b274ce60c2d42c66c6694eb24290f4e1903b83fb3aef09a`

这是第七个**源码候选**，文件后缀使用 draft V2 / spec V3 / Python v3。它保留 V6 四件套不变，只修复 V6 独立审查发现的证据绑定、reference、replacement、效用解释和顺序执行问题。70 项本地合成测试通过只能说明有限代码合同按测试工作，不能说明 VMem、AOIG、SEM、RCSU、方法收益或创新已经得到真实验证。

## 0. 当前数据门先于一切分析

完整 RCSU 主分析要求每个 target 至少三个从未进入 memory 或 conditioning 的独立 reference capture，并且每个 capture 与 target 的校准时间差不超过 10 ms。当前本机 TUM fr1/fr2 单 RGB 流在任意 20 ms 区间最多只有一个 capture，最小帧间隔分别约 27.457 ms 与 23.974 ms；C1/C2 也没有独立 R。该结果由独立 metadata 检查给出，证据文件为工作区 `work/resumption_20260908/reference_time_feasibility.json`，SHA-256 `02dd1b304fc9e84bc4f99cd3b3ccfcf0fdee0685f7f14907edaa21959e07c8eb`。

因此：

1. 当前本机 B0/C1/C2 **不能实施完整 reference-conditioned RCSU/Benefit 分析**；
2. 不允许放宽 `>=3 references` 或 `+-10 ms` 来迁就已有数据；
3. reference 协议只适用于能提供足够独立同步观测的多传感器数据，或另行冻结且通过审查的状态同步/观测模型；
4. 当前 V7 的 reference、utility 和顺序 ledger 仅是 finite source contract 与合成自测，不是 experiment-ready 证明。

## 1. 可识别问题与禁用表述

本设计条件于 source 已经 stored、selected、addressable，且已枚举 consumer。它不能识别 Store 或 Select 的因果贡献。

- `AOIG` 只表示：在注册 intervention、positive/negative control、replay 和五个 paired seeds 下，输出对该操作的可观察影响低于阈值。禁止写“source 未使用”。
- `support-effect screen` 只比较 raw matched-zero effect map 与冻结 support。V7 若 screen 失败只输出 `SEM_DESCRIPTIVE_STOP`；它没有实现 RAIMA V3 对 harmful SEM 所需的两套稳健 support、4/5 seed 合取和 reference harm 条件。禁止写“位置错误”或“有害错位”。
- `LOCAL_EDIT_PREFERENCE` 是 edit 相对 same-path zero 的局部偏好；`MATCHED_REPLACEMENT_RCSU` 是 O 相对已注册 P 的 reference-conditioned signed utility；`SOURCE_ABSENCE_RCSU` 是额外的 O 与 absence 对比。三者不得互换。
- 即使 absence contrast 为负，也只有在未来执行层另行证明 same-state、same-layout、fixed-null-slot 与唯一 source-presence 差异后，才可能讨论 source-presence harmfulness。当前代码合同本身不作该因果声明。

## 2. 固定实验单位与输入格

确认性单位是预冻结 scene，不把 seed、target、sign、family 或 replacement 当独立科学样本。每个 source-target 使用：

- 两个 edit family：`exposure_log_gain` 与 `texture_highpass`；
- 两个 sign：exact integer `-1,+1`；
- exactly five paired seeds；
- 全部预冻结 targets；
- 至少三个 eligible reference captures；
- 全部 eligible matched replacements；
- 可选、单独标记的 source-absence contrast。

`ExperimentPlan` 冻结完整 Cartesian product 及 reference/replacement receipt SHA。`evaluate_sequential_ledger` 拒绝 missing、duplicate、extra、substituted、mixed-state、mixed-zero 和 out-of-order evidence。

## 3. Source edit 与 same-path zero

唯一 finite API 是 `apply_source_bundle(source_u8,family,sign,dose)`。输入必须为真实 NumPy uint8 RGB。zero dose 和 treatment 走相同七阶段：decode、family edit、clip、乘 255 并 ties-to-even 取整、uint8、semantic consumer、latent consumer。两个 consumer 的顺序、调用数与 tensor SHA 都记录。finite reference preprocessing 不是 VMem 的真实 CLIP/VAE 实现；未来 hook 必须另行冻结真实 adapter 与 consumer inventory。

## 4. Typed replay 与 Influence

每个 seed-target 的 `ReplayLedger` 必须保存：

- exactly four 只读 native `576x576x3 uint8` 输出；
- state/noise/RNG/snapshot/target-roster identities；
- 一份只读 support；
- exactly six、按 `(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)` 排序的 replay pairs；
- 每对输出 SHA、从真实绑定输出重算的 full-frame distance 和 symmetric guard metrics；
- `tau_output=max(1e-6,max six distances)`。

validator 从绑定输出和 support 重新计算全部距离与 guard。自由 replay scalar、自由输出 SHA、乱序 pair、可写数组和 stale canonical hash 均失败。

`InfluenceReceipt` 绑定 exact `ReplayLedger`、`ArmIdentityReceipt` 和六个只读输出（target edit/zero、negative edit/zero、positive edit/zero）。它从这些数组重算三张 raw maps、均值和

`D = E_target - max(tau_output,E_negative)`。

阈值 `Delta_I=0.5/255`。不存在接受自由 `influence_value` 的 public API。

## 5. Raw support-effect screen 与 mask ledger

Localization 只使用 `abs(Y_edit-Y_zero)` 的 raw target map；negative/replay 不做逐像素相减。`PlaceboMaskLedger` 保存每张 exact float64 mask 的压缩 bytes、原始 mask SHA、压缩 SHA、顺序与 generator SHA。shape/camera 各至少 199 张。

`SupportEffectReceipt` 内嵌 Influence、只读 true support、shape ledger 与 camera ledger。validator 解压每张 mask，重算全部 placebo mass、lower median、tail rank、raw-map `L_area`、ER、negative ratio 和 reasons；调用方不能注入 tail dict 或 scalar。

当前继续门要求 raw target `ER>1`、`L_area>=0.02`，negative full-effect ratio `<=0.25`、negative support `L_area<=0.01`，两类 placebo true mass 高于 lower median 且 tail rank `<=0.05`。这只是支持对齐筛选。uniform-effect 的 V5 8-bit 反例必须失败。

## 6. Reference可靠性

`ObservationExclusionLedger` 绑定 target capture/file、完整 memory observation roster 和 conditioning roster。target answer 不能出现在后两者。`ReferenceRosterReceipt` 内嵌该 ledger，并保存所有候选的 eligible/excluded flow。

每个 eligible R 必须同时满足：capture/file 与 target 不同，capture/file 未进入 memory 或 conditioning，同 scene，校准时间差 `<=10 ms`，位置比 `<=0.10`，旋转 `<=2 deg`，FoV 差 `<=1 deg`，O/R identity、view-pair、support/outside exact-role valid-domain 均通过。至少三条独立 capture 与 file；single-reference API 永久 fail closed。

`ReferenceUncertaintyReceipt` 内嵌 roster、三条以上只读 reference RGB、validity masks 和 support，重算所有 pairwise primary loss：

`Delta_ref=max pairwise normalized RGB MSE on common-valid support`

`Delta_U=max(0.001,2*Delta_ref)`。

若 `Delta_ref>0.001`，primary RCSU 被阻断。

## 7. Replacement P eligibility

`QualityCalibrationReceipt` 固定 metric `CAL_SOURCE_REPROJECTION_RGB_MSE_V1`、CAL manifest SHA、至少八个值和 nearest-rank Q1/Q2/Q3。边界值用 `searchsorted(...,side="right")` 进入较高 quartile。

每个 P 同时要求：非 O、same scene、insertion-event 距离 `<=2`、target camera thresholds、binary support IoU `>=0.80`、`sum(W_P)/sum(W_O)` 在 `[0.90,1.10]`、同 CAL quartile、exact O/R/P identity、完整 O_R/R_PREV_R/R_R_NEXT/P_R view pairs、以及 support/outside O/R/P valid domains。所有候选进入完整 canonical flow，所有 eligible P 都进入计划，不能看结果挑 P。

## 8. 三个效用键与符号

输出 loss 为 common-valid domain 上的 normalized RGB MSE，只有一次 uint8-to-float `/255`。

- `LOCAL_EDIT_PREFERENCE = loss(edit,R)-loss(zero,R)`；正值表示 zero/original appearance 在该 reference 下较好。
- `MATCHED_REPLACEMENT_RCSU = loss(P,R)-loss(O-reinsert,R)`；正值表示 O 在该 reference/protocol 下优于 P。
- `SOURCE_ABSENCE_RCSU = loss(absent,R)-loss(O-reinsert,R)`；正值表示 O 优于 absence，负值表示 absence 较好，但不自动等于 causal harmfulness。

`UtilityReceipt` 内嵌 exact reference uncertainty、三张只读输出、valid mask 与 support，并重算 support utility、outside difference、`Delta_U`、符号与 outside veto。outside tolerance 是 `max(0.0005,2*Delta_ref)`。

RCSU 稳定性要求每个 registered key 对五个 seeds 至少 4/5 同号、median absolute utility `>=Delta_U`，三个以上 references 同号，并且每条 outside veto 通过。一次 P、跨 P 平均或 reference-dependent sign 不能变成来源固有标签。

## 9. 顺序 kill ledger

顺序严格为：

1. exact Influence grid；positive control 任一失败即 `STOP_POSITIVE_CONTROL_INVALID`；
2. positive 全过且所有 target edit 都低于 `Delta_I`，输出 `AOIG_CANDIDATE_STOP`，禁止后续证据；
3. target influence 混合，输出 `INTERVENTION_SENSITIVITY_STOP`；
4. target influence 全过才接受 exact support-effect grid；任一 alignment 失败输出 `SEM_DESCRIPTIVE_STOP`，禁止 utility；
5. alignment 全过才接受 exact utility grid；outside 失败停止；seed/reference 符号不稳停止；
6. 最终动作只陈述 typed ledger 已完整，仍不等于真实实验、因果结论或创新。

## 10. V6 blocker closure claim

本作者候选声称在源码层修复 V6 的 3 个 CRITICAL 与 4 个 MAJOR：typed replay/output derivation、tail recomputation、reference exclusion、统一 P selector、明确 CAL/IoU、区分三种效用、exact valid roles、typed sequential ledger。该声明必须由不同作者对 exact hashes 做 fresh adversarial review；在此之前状态仍是 `PENDING_FRESH_INDEPENDENT_REVIEW`。

## 11. 允许的唯一结论

“S48 source-only V7 candidate 实现了一个有限、fail-closed、typed/bound 的合成分析合同，并在两个本机 Python/NumPy 环境通过其冻结测试。它没有访问真实 C1/C2 像素或运行模型。当前 TUM/C1/C2 又无法满足三 reference 同步合同，所以完整 RCSU/Benefit 仍为 data-infeasible；AOIG、SEM、RCSU、方法收益和创新均未得到真实证明。”
