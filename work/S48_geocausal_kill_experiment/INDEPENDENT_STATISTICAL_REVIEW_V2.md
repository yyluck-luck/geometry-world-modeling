# S48 GeoCausal 最小否证实验：独立统计／因果复审 V2

- 审查角色：fresh independent statistical/causal reviewer；本轮不继承 V1 的结论
- 审查时间：2026-09-08 14:05 CST（UTC+08:00）
- 被审文件：`S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT.md`
- 被审 V2 SHA-256：`ef92be76a8f8f2d6cd6fe70e629f77114751d9ed2a05228618038087e6fda92d`
- 冻结 V1 路径：`archive/S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT_v1_sha69ad32b9.md`
- 冻结 V1 SHA-256：`69ad32b932369e6c5cc9b1fde65d20d2caca1892fd47e2a5e94c3d15b5c8ef32`
- 版本核验：**V2 与 V1 不同**；V1 文件及 SHA 未被本轮改动
- 只读源码：`work/S20_environment/isolated_vmem_source/modeling/pipeline.py`
- 只读源码 SHA-256：`680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255`
- 审查边界：只读项目文字与源码结构；未运行或导入模型；未打开、解码或检查 C1/C2 tensor、image、pixel；未修改被审草案
- 审查文件自身 SHA-256（删除本字段所在整行后计算）：`bc2c40761b450b4ae8509cd811758ab5a766de64ec5a22aebb5fa77bd05aabcb`
- **总裁决：BLOCKED**

## 1. 独立结论

V2 是实质修订，不是措辞修补。它已经把研究对象收窄为 `baseline-selected source` 的 **post-selection downstream appearance effect**；给出了不按 F11 效果挑 source 的规则；加入 exact replay、独立 SESOI、两类 edit、sham、正负控制、fresh-state/randomization 要求、独立 reference、`B_local/B_matched` 公式，并把 confirmation 完整移到未来 S49。旧 C4 的确认样本量阻断因而已成功从 S48 pilot 中移除。

本轮仍不能给 S48 arm execution PASS。主 blocker 是 Localization 的 `p_mask` 仍不具备其声称的有限随机化 p 值含义：真实 support 与由三种不同机制筛出的假 mask 没有被定义为同一零假设下可交换的随机分配，混合比例、抽样概率和实现阶段也未冻结。`K=199` 只让秩的最小分辨率达到 0.005，并不会自动使秩成为校准的 p 值。与此同时，当前源码并没有在所写注入边界返回 source support，且内置 `reset()` 没有清空若干真实运行字段；这两项使“已冻结 support”和“无 carryover”目前还不能由协议直接保证。

| 等级 | 数量 | 对当前阶段的含义 |
|---|---:|---|
| CRITICAL | 1 | RQ2 的主零假设尚未识别，不能用 `p_mask<=0.05` 宣称 geometry-specific localization |
| MAJOR | 7 | 精确 hook/support、mask 实现阶段、状态重置、相机量纲、Benefit 对齐、多 edit 聚合、近邻边界仍需冻结 |
| MINOR | 3 | 数值域、退化量、若干术语仍不够可复算 |

## 2. V1 问题逐项 closure audit

状态含义：`CLOSED` 表示 V2 文本已解决；`CLOSED_BY_SCOPE` 表示通过明确排除该阶段而解决；`CLOSED_CONDITIONAL` 表示 estimand 已正确，但执行前仍须在 G7 绑定源码；`PARTIAL` 表示已有实质修复但仍有识别或可计算缺口；`OPEN` 表示原阻断仍成立。

| V1 编号 | V1 问题 | V2 证据 | 本轮状态 | 本轮判断 |
|---|---|---|---|---|
| C1 | treatment timing 与 total/post-selection effect 混写 | §4.1 明确 Store→Select→Address→intervention→consumer，并明确不称 total effect；§4.2–4.3 区分冻结量和必须重算中介 | **CLOSED_CONDITIONAL** | 因果称谓已对齐；但当前源码 `get_context_info()` 不返回 support，精确 hook 仍必须由 G7 物化和独立复审 |
| C2 | area baseline 不能识别 geometry-specific localization | §6.2 新增 199 masks、`L_matched`、placebos 和 sensitivity | **OPEN / 仍为 CRITICAL** | 增加了形状匹配，但没有定义使 observed support 与 null masks 可交换的随机化机制；当前 `p_mask` 不能按 p 值解释 |
| C3 | independent reference、`B_local/B_matched` 不可计算 | §6.4 排除进入 memory 的 reference，给出两种公式、SESOI 和匹配 calipers | **PARTIAL** | 数学方向和符号已修正；仍缺 reference 共视/配准/光度资格及 replacement 的双向 common-support 规则 |
| C4 | confirmation 样本量、SESOI、检验与 multiplicity 未冻结 | §5.5、§7.2 明确 S48 不授权 CONF，S49 必须另立且冻结 alpha/power/n_scene/test/SHA | **CLOSED_BY_SCOPE** | 当前 S48 不再作总体确认；在 S49 通过 fresh review 前不得运行 CONF |
| M1 | replay floor 与 SESOI 不充分 | §5.1 给至少 3 次 replay、所有 pair、最大 floor、`delta_I=0.5/255` | **CLOSED** | 对 RGB Influence pilot 足够；相机/画质各自 replay floor 的量纲问题另列 M4 |
| M2 | discovery/confirmation 与 source-selection bias | §3.2 固定 C1→C2 顺序和第一个普通 eligible source；§7.2 独立 screening seed | **CLOSED** | C1/C2 只作 CAL；不得按 F11/Localization/Benefit 挑 source 的规则明确 |
| M3 | scene、seed、mask 等伪重复 | §3.1 固定 scene 为 cluster，seed/edit/replay/mask 为技术重复；§7.1 禁止抬高 n | **CLOSED** | 对 S48 描述性 pilot 足够；S49 仍须给整数 scene 数 |
| M4 | camera/quality 未成为 arm 级守卫 | §5.4 新增 homography、brightness、sharpness、saturation、matching 等门 | **PARTIAL** | 形式已升级为硬门，但用同一个“replay 最大值”跨 px、RGB、比例等不同单位，当前不可执行 |
| M5 | 单 edit 无法排除 corruption artifact | §5.3 新增两 edit families、±dose、sham、negative/positive controls | **PARTIAL** | 组件齐全；但多 edit/±dose/seed 到唯一 `d_i`/`L_i` 的聚合与控制门阈值未定义 |
| M6 | arm 顺序、cache carryover、invalid/missing | §5.4 要求同 noise、随机顺序、fresh process 或 validated reset、完整 attempts | **OPEN** | 规则方向正确；但候选源码的 `reset()` 与真实状态字段不一致，当前 SHA 下只能允许 fresh process |
| M7 | multiplicity 和 prediction claim | §7.1 限定 pilot；§7.2 fixed sequence、IUT/Holm；§10 将 acceptance head 后移 | **CLOSED_FOR_PILOT** | S48 不作总体 p/CI 或预测结论；S49/acceptance head 必须各自重新冻结 |
| M8 | CUE-R/activation patching/TetherCache/I²AM/AGRA 重叠 | §5.3、§8、§10 已覆盖 CUE-R、TetherCache、普通 gate 与 corruption controls | **PARTIAL** | CUE-R/TetherCache 边界明显改善；I3DM 缺席，I²AM/AGRA 也从 V2 的最近工作与强基线中消失 |
| N1 | RGB 数值域、颜色、resize/alignment 未冻结 | §5.4 说代码、resize、颜色域在 arm 前冻结 | **PARTIAL** | 仍未在协议中说明输出是 uint8 还是 float、sRGB/linear、量化和插值时点 |
| N2 | epsilon、empty/full support、zero mass 未定义 | §6.2 仍写 `ε`，只对不足 199 masks 判 invalid | **OPEN** | epsilon 值与退化 support/mass 规则仍缺失 |
| N3 | “稳定/一致/匹配”等术语未操作化 | 多数已增加数值门 | **PARTIAL** | `tearing`、`known real consumer`、same object identity、跨 edit “有反应”仍没有唯一判据 |
| N4 | selection flow/denominator 未要求 | §7.1 要求完整 flow、invalid、失败及每层单位 | **CLOSED** | 满足 pilot 报告要求 |

旧问题汇总：4 个旧 CRITICAL 中，1 个条件关闭、1 个仍开放、1 个部分关闭、1 个按 S48 scope 关闭；8 个旧 MAJOR 中 4 个关闭或对 pilot 关闭、4 个仍部分/开放；4 个旧 MINOR 中 1 个关闭、3 个仍部分/开放。

## 3. CRITICAL

### C-V2-1：`p_mask` 不是当前定义下可校准的有限随机化 p 值

V2 §6.2 把 199 个候选混合自：未选 source 的投影、真实 support 的刚性平移/旋转、预注册相机平移。候选又经过面积、连通分量、周长、位置格、IoU、edge、replay variance、reference error、depth 等 caliper 筛选。协议没有给出：

1. 三个生成族各占多少、如何抽样、重复候选如何去重，以及固定随机种子；
2. 为什么真实 `S_i` 在零假设下与这 199 个经筛选的 `M_{i,b}` 可交换；
3. observed support 本身可由哪个同一随机机制生成，以及它在参考集合中的概率；
4. 是对三个 null family 分别过门，还是先混合后过门；
5. 非选 source projection 和 camera translation 既作为 null 候选又作为必须失败的 placebo 时，如何避免同一对象承担两个不同逻辑角色。

因此

`(1 + #{mass(M)>=mass(S)})/(K+1)`

目前只是一个经验尾部秩。它可以作为描述性 matched-placebo score，但没有 randomization test 所需的 assignment/exchangeability 依据。严格 caliper 和 `K=199` 不能补回这一识别条件。以 `p_mask<=0.05` 作为 Pilot-C 的主门，会把生成器选择、空间非平稳性和几何定位混在一起。

**可执行修复有且只有两条合法路线：**

- **描述性 pilot 路线（推荐，最省算力）：** 删除“p 值”和 `p<=0.05` 语言；冻结三个 mask family 的数量、参数分布、seed、去重和不足规则；分别报告真实 support 在每个 family 中的 percentile/enrichment，并要求三族预设方向一致。结论仅称“超过这些预设 matched placebos 的局部富集”。
- **有效随机化路线：** 写出明确的有限 assignment set 或群作用，使真实 placement 和假 placements 在 H0 下可交换；给每个 assignment 的概率、约束、seed 和精确/Monte Carlo 检验。若 conditioning/caliper 使真实 support 不可能由同一机制产生，就不得称随机化 p 值。

在二者之一被写入并 fresh reviewed 前，RQ2 不能通过，S48 arm execution 维持 **BLOCKED**。

## 4. MAJOR

### M-V2-1：概念处理时点正确，但当前源码没有草案声称的 `selected IDs/slot/support` 共同返回边界

源码顺序支持 post-selection estimand：`pipeline.py:1250` 调用 `get_context_info`，`1252–1261` 取回 context tensors，`1268` 才调用 `get_cond`，因此可以在两者之间替换已经选中的 appearance tensors。V2 关于“固定 selection/address，重算全部 appearance descendants”的因果解释是正确的。

但 `get_context_info()` 的实际返回字典（`pipeline.py:759–765`）只有 `context_c2ws/context_latents/context_encoder_embeddings/context_Ks/context_time_indices`；没有返回 support，也没有显式 source-slot/support ownership map。`retrieved_info` 只在函数内部构造（`639–647`），随后丢弃。更进一步，一个 surfel 可映射到多个 timestep（`462–502`），所以“目标 source 的几何投影 support”不是从当前返回值直接可得的唯一量。

**修复：** G7 必须绑定一个经过源码审查的 instrumentation patch，而不能只在 manifest 中写自然语言：

- 保存普通选择后的 `context_time_indices` 及 slot；
- 保存 `surfel_index_map` 和每个 surfel 的 timestep membership；
- 冻结多 timestep surfel 的 source attribution 规则（exclusive、fractional 或 union 中只能选一个）；
- 定义 occlusion/z-buffer、空洞、边界和 resolution 转换；
- 在任何 F arm 输出前写出 support artifact 的 hash；
- 精确列出替换的 `context_latents` 与 `context_encoder_embeddings` tensor slice，并验证没有遗漏新增 appearance path。

若做不到，执行 G7 的既定 stop，不得用 attention map 或事后输出差异反推 support。

### M-V2-2：matched-mask 的冻结阶段内部矛盾，且 199 个有效候选的可行性尚未证明

§6.2 要求 mask matching 使用当前 unit 的 `F00 edge density`、`replay variance` 和 `independent-reference baseline error`；§7.1 又要求所有 masks 在读取任何输出前冻结。当前 F00/A0/reference error 本身就是运行后量，不可能同时满足这两条，除非这些 strata 全部来自独立 CAL 数据，而非当前 unit。

**修复：** 二选一并写成不可绕过的状态机：

1. 全部 matching covariates 只来自干预前 geometry/source 和独立历史 CAL；manifest、realized masks 都在 F00/F11 前冻结；或
2. generator 代码、参数和 seed 先冻结；只生成 A0/F00 并保持 F11 sealed；由独立脚本只读取 control outputs 物化 199 masks、写 hash 和 feasibility report；随后才允许 F11。操作者在 mask hash 前不得读取 F11。

同时必须先做**无 F11 的 feasibility audit**，报告每个 generator family 的 proposal 数、acceptance rate、失败 caliper 和最终唯一 mask 数。`无法得到199个则停止`是正确的 fail-safe，但不能替代生成分布的预注册，也不能在失败后更换 mixture 或放宽 caliper。

### M-V2-3：当前候选源码的 `reset()` 不能作为 full-reset 分支

源码初始化的真实运行状态包括 `self.latents`、`self.encoder_embeddings`、`self.Ks`、`self.surfels`、`self.surfel_to_timestep`、`self.pil_frames`，后续还实际使用 `self.c2ws`。但 `pipeline.py:135–146` 的 `reset()` 清空的是 `rgb_vae_latents`、`rgb_encoder_embeddings`、`poses`、`focal_lengths`、`all_pil_frames` 等不同名字；它没有清空 `latents`、`encoder_embeddings`、`c2ws` 或 `pil_frames`。输出又会在 `1294–1310` 被追加并写回 scene memory。

这意味着 V2 §5.4 的“fresh process 或逐字段验证的 full reset”在当前源码 SHA 下不能把内置 `reset()` 当成已验证选项。

**修复：** 当前 SHA 的所有 A0/F00/F11/edit/control arm 一律使用 fresh process，并从同一个只读 state snapshot 重建；进程退出码和资源终态进入 manifest。只有 reset 修复另有代码 SHA、逐字段测试和独立源码复审后，才可启用 in-process reset。任何 matching/guard 计算失败若与 arm 有关，应按 gate failure 处理，不能以 engineering invalid 删除。

### M-V2-4：camera/quality 守卫把不同单位的 replay floor 混成了一个数

§5.4 分别使用 px 的 homography displacement、归一化 RGB 的亮度差、比例尺度的 sharpness ratio、百分点的 saturation increase，却都写 `max(阈值, replay最大值)`。§5.1 的 `tau_replay` 是归一化 RGB 主距离，不能与 px 或百分点取最大值；即便“replay最大值”意图为各指标自己的 replay，也没有明确写出。

**修复：** 为每个守卫建立独立的 A0 paired replay 分布与同单位 floor，例如 `tau_h_med_px`、`tau_h_p95_px`、`tau_brightness_rgb`、`tau_sharpness_ratio`、`tau_saturation_pp`。固定 resize、matcher、RANSAC、failure code 和 minimum-match rule。少于 50 matches、NaN、全黑或 tearing 应视为该 arm 守卫失败；`tearing` 若参与 gate，必须由可复算指标定义，不能只靠主观观察。

### M-V2-5：独立 reference 已有，但像素损失仍缺共视配准和光度可比性

§6.4 正确排除了进入 memory/conditioning 的 reference，并冻结 camera/time/file SHA；这解决了“拿输入本身当答案”的泄漏。但 support 内 RGB MSE 只有在 `R_i` 与生成目标处于同一像素坐标、同一可见表面和可比光度域时才识别相对正确性。仅记录 camera/time 不保证 sub-pixel alignment、曝光一致、动态物体一致或遮挡一致。

`B_matched` 还把不同未选帧的 appearance 塞进原 source 的固定 geometry/address。即使投影 IoU≥0.80，也可能存在单向可见区域和 warping holes；直接在原 `S_i` 上计分会把覆盖差异当作 appearance benefit。

**修复：** 在 arm 输出前冻结：reference 的 pose/FoV/时间容差；相机重投影/配准算法及最大残差；颜色空间和允许的曝光归一化；动态/遮挡排除；原 source 与 replacement 的**双向 common-visible support**；warping hole 比例上限。资格失败则 RQ3 invalid-stop。主 `B_matched` 只在预先冻结的 common support 上计算，同时报告原 support 和 support 外结果。reference eligibility 只能读取 reference、camera、geometry 和 control/CAL 信息，不能看任何 Benefit arm。

### M-V2-6：存在多个 F11，但 `d_i`、Localization 和控制门仍被写成单一统计量

两类 edit × `+δ/-δ` × 至少两个 paired seed 会产生多个 F11 effect map。§6.1 只定义一个 `d_i`；§6.2 用这个单一图计算 `L_i/L_matched_i`；§5.3 只说“若仅一个 family 有反应则降级”，没有说明：

- Influence/Localization 的 primary family 与 dose 是哪个；
- 是先在 ±dose 内平均 effect maps，还是分别过门；
- 两个 seed、两个 family 的通过规则是 intersection、均值、最小值还是其他预先函数；
- sham、negative control 和 positive control 的最大允许/最小期望响应相对 replay 与 SESOI 是多少；
- positive control 的“known real consumer”是哪条 tensor path，验证方向是什么。

这些缺口会允许在看到结果后选最漂亮的 effect map，并使 matched-mask test 的被检验统计量不唯一。

**修复：** 在 G7 指定一个唯一 unit-level map/statistic。保守方案是每个 seed 与每个 edit family 分别过 Influence 和 Localization，主 claim 用 intersection-union；±dose 的 effect map 按预先固定的均值形成 family map。固定 sham/negative 的上界和 positive 的下界；控制失败即 stop/降级。任何 alternative aggregation 均可，但必须在输出读取前唯一化。

### M-V2-7：CUE-R/TetherCache 边界改善，但 I3DM 与已识别的因果空间近邻缺席

V2 §8/§10 已明确：CUE-R 占据 per-item REMOVE/REPLACE/DUPLICATE 与 signed utility；TetherCache 占据 attention+diversity selection、trusted alignment 和 generic gate/repair。该边界足够支持“不能把 item intervention 或 gate 本身称新”。

但项目同日 nearest-work audit 已把 **I3DM** 列为 Select/Consume/Localize 的直接压力：空间置信图、最大覆盖、3D alignment 和 reliable-region injection。V2 的强基线和参考列表没有 I3DM，也没有把其 uncertainty/coverage 或 reliable warp region 纳入未来 proxy comparison。V1 明确提醒的 I²AM 随机区域/双向 attribution 与 AGRA 世界模型 spatial-token intervention/matched sensitivity 也未进入 V2 最近工作段。

**修复：** 在 S48 结论边界中明确：3D support、geometry-aware retrieval/injection、区域图、mask 内外敏感性都不是单独创新。Pilot 报告至少加入 I3DM confidence/coverage 与可靠 warping area 作为 geometry proxy；未来 acceptance head 在同数据/预算下比较 I3DM-style confidence/coverage、TetherCache-style selection/repair、attention、pose/retrieval 和普通 gate。I²AM/AGRA 作为 measurement nearest neighbors 进入引用与差异表。S48 即使通过也只能称 VMem-scoped measurement evidence，不能据此声称方法新颖性。

## 5. MINOR

### N-V2-1：RGB 主距离仍缺唯一数值域

`mean |Y_F11-Y_F00|/255` 只在 `Y` 是 `[0,255]` 标度时成立。必须冻结 decode 后/量化前还是保存 PNG 后、uint8 或 float、sRGB 或 linear RGB、clipping、resize/crop、插值与有效像素 mask。若在 `[0,1]` float 上计算则不得再次除以 255。

### N-V2-2：`ε` 与退化 support 仍未定义

冻结 `ε` 的数值和单位。`S_i` 为空、覆盖全部 `Ω_i`、`area_i=0/1`、总 effect mass 为 0 或非有限值时，Localization 应预先记 `NOT_IDENTIFIABLE`，不得输出任意 `ER/L_matched/p`。这些规则应先于 199-mask feasibility gate。

### N-V2-3：少数 gate 术语仍需变成机器可判规则

给 `stable natural failure`、`same object identity`、`known real consumer`、`tearing`、跨 edit/seed “方向一致”各自定义字段、阈值、判定代码和失败动作。人工视觉检查保持 secondary 是正确选择。

## 6. 对关键问题的直接回答

1. **处理节点与 estimand 是否一致？** 概念上已一致：这是 post-selection downstream appearance effect，不是 Store→Select total effect。实现上仍须解决当前源码不返回 support 的 hook 问题，所以是 conditional closure。
2. **geometry 固定是否冻结中介？** 对当前 post-selection estimand，`Z/G` 在处理前已产生，固定它们不是冻结处理后中介；CLIP、VAE/latent、attention、denoising 和 writeback 必须重算。V2 这点正确。若未来声称 Store 前 total effect，则必须另立实验并允许 geometry/selection 改变。
3. **Influence 是否可计算？** RGB Influence 的 replay 与 SESOI 已可计算，前提是冻结数值域和唯一跨 edit 聚合。
4. **Localization 是否识别目标？** 当前不识别其声称的随机化 p 值目标。匹配变量很多，但 assignment/exchangeability 未定义；这是唯一 CRITICAL blocker。
5. **`B_local/B_matched` 是否可计算且非循环？** 公式和独立 reference 原则已建立；生成后结果不参与 source/match 选择，避免了主要循环。但 reference/common-support 配准不足，当前仍不能把 RGB loss 差异解释为可靠 benefit。
6. **source 是否无 outcome 挑选？** 是。C1→C2 顺序、第一个普通 eligible source、禁止读取 F11/Localization/Benefit 后选择，已解决旧 selection bias；结论只限 screen-positive CAL pilot。
7. **pilot-confirmation 是否分离？** 是。S48 不需要现在冻结 confirmation 的整数样本量；S49 的未来条件已足够作为阻断合同，但不是 S49 的预先 PASS。
8. **multiple testing 是否控制？** 对不作总体推断的 S48 pilot 基本足够；matched-mask 不能借“只有一个 p”绕过无效零分布。S49 必须按其 manifest 再独立审查。
9. **camera/quality 混杂是否解决？** 部分解决；硬门已建立，量纲和 metric-specific replay 尚需修复。
10. **CUE-R / activation patching / TetherCache overlap 是否处理？** CUE-R、activation/corruption controls 与 TetherCache 边界已明显改善；I3DM、I²AM、AGRA 缺口仍使新颖性边界不完整。

## 7. 解阻后的唯一可执行顺序

1. 修订 §6.2：选择“描述性 matched-placebo rank”或真正的 randomization design；不得保留当前未校准 `p_mask` 的称谓。
2. 只做 source/geometry/control-side 的 mask feasibility audit；不运行 F11，不打开既有 C1/C2 图像或 tensor；冻结 generator family、参数、seed、proposal/acceptance flow。
3. 为当前 `pipeline.py` 写精确 hook/support 规格，独立源码复审后绑定 patch SHA；定义 multi-timestep surfel attribution。
4. 当前源码一律使用每 arm fresh process；修复并独立验证 reset 之前，不允许走 in-process reset 分支。
5. 把 camera/quality replay floor 拆成每指标同单位阈值；唯一化多 edit/seed 的主 effect map 与 controls gate。
6. 在不看 Benefit outputs 的条件下完成 reference/common-support eligibility 与 registration feasibility；失败即删除 RQ3，不降低 caliper。
7. 补 I3DM、I²AM、AGRA 边界和 proxy/baseline；重申 S48 通过也不是方法新颖性结果。
8. 生成包含代码、配置、mask/reference artifacts、随机顺序和全部阈值 SHA 的 G7 manifest，再做一次 fresh pre-run review。只有该复审 PASS 才能运行 S48 arms。
9. 若 pilot 存活，再创建 S49；在新 scene 的任何 CONF 输出前冻结实际整数样本量、唯一检验、alpha/power、missingness 和分析 SHA，并重新独立审查。

## 8. 最终裁决与允许边界

**BLOCKED。** V2 已解决多数 V1 设计缺陷，但 matched-mask 主检验仍未识别，当前源码的 support boundary 与 reset 也没有满足文本承诺。此版本不能授权 A0/F00/F11、edit、control 或 Benefit arm 的模型运行。

当前允许继续的工作仅包括：文本修订、源码 hook 枚举、无生成输出的 mask proposal feasibility、reference/registration eligibility 设计、metric/control 代码实现与静态/合成自测，以及新的冻结 manifest。不能打开既有 C1/C2 tensor/image/pixel 来反向调 mask、阈值或 reference。

解除本轮阻断的最低条件：

- 把 `p_mask` 改为诚实的描述性 rank，或给出有效且可复算的随机化 assignment；
- 精确物化 source slot/support 和 all-path appearance hook；
- 当前源码强制 fresh process，或提交并独立验证 reset 修复；
- 按单位拆分 camera/quality replay floors；
- 唯一化多 edit/seed 的统计聚合与控制门；
- 冻结 reference registration 与双向 common-visible support；
- 补齐 I3DM/I²AM/AGRA 最近工作边界；
- 对完整 G7 manifest 做 fresh independent review。

在这些条件完成前，不能写“已证明几何局部因果”“已证明记忆有益/有害”“已提出新方法”或“已达到顶会水平”。
