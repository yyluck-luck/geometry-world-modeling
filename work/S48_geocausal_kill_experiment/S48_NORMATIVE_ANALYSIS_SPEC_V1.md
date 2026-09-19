# S48 source-only normative analysis/edit/guard specification V1

- 建立时间：2026-09-08T15:43:24.654804+08:00。
- 状态：`SOURCE_ONLY_DRAFT_FOR_FRESH_REVIEW`。
- 目的：关闭 V4 独立审查的 `M-V4-1`，把会改变处理、placebo 资格和 arm 守卫的自由度写成唯一公式。
- `S48 execution authorization=NONE`；`novelty_authorization=NONE`。
- 本规范没有导入或运行模型，没有创建 S48 arm，没有读取、映射、解码或查看 C1/C2 的 tensor、image 或 pixel 正文。

本文件与同目录 `s48_analysis_reference_v1.py` 构成一个待审规范包；`test_s48_analysis_reference_v1.py` 只提供合成边界验证。若文字与代码不一致，结论是 **BLOCKED**，执行者不得任选更有利的一项。三个文件必须以 whole-file SHA 一起进入未来 G7，并接受新的不同作者前审；本文件不能追认 V4 PASS，也不能授权模型实验。

## 1. 规范覆盖范围

本版固定以下 source-only 或纯数组对象：

1. fractional support 的二值拓扑、连通分量、周长、面积、直方图、质心、IoU 和 canonical SHA；
2. 可见 metric depth 的有限差分、深度边界局部密度、mask 加权中位数、全 target 四分位及 ties；
3. `G_shape/G_camera/G_source` 共同使用的 mask caliper 数值对象；
4. 两个 source appearance edit family、完整剂量 ladder、source-only 数值门和唯一剂量选择；
5. 普通运行 complete memory roster 中未选来源的资格、排除 flow 和稳定顺序；
6. 原生输出图的相机/整体质量守卫、A0 replay floor 和等号规则。

本版不实现 renderer、camera-pose 扰动、surfel/provenance 重投影、模型 hook、CLIP/LPIPS 网络、reference warp、Benefit、process isolation 或任何生成。第 9 节列出因此仍保持 BLOCKED 的项目。

术语接口与当前主 preregistration V5 对齐：本包的 mask/caliper 只处理干预前的 `W_t` 与 context maps；未来 Localization 的 effect 输入由 V5 另行定义为每个 `family f × seed s × sign a` 的 `Y^edit−Y^matched-zero` 直接 pair，再形成逐像素 replay/matched-negative 校准的 `e^a_excess`。本包不读取、计算或替换该 effect map。

## 2. 数据域、有效性和等号规则

### 2.1 公共规则

- 所有公式按 NumPy `float64` 计算。求和、均值、方差和距离均禁止隐式降为 `float32`。
- `W` 必须是非空二维有限数组，且逐元素位于闭区间 `[0,1]`。`W>0` 是唯一 binary support；不能另设阈值。
- 输出 guard 的 RGB 输入必须来自原生 `576×576` 三通道保存 PNG：逐通道 uint8 值除以 255 后成为 `[0,1]` float64 sRGB。不 resize、不 crop、不颜色线性化、不曝光归一化。
- source edit 的规范输入是固定 source RGB 字节按同样方式转成 `[0,1]` float64 sRGB；公式结果 clip 到 `[0,1]` 后直接交给未来绑定的唯一 preprocessor。是否必须先重新量化为 uint8 属于 adapter 语义，当前未绑定，因此真实 hook 仍 BLOCKED；不得由执行者临时选择。
- metric depth 的单位沿用数据 manifest 的唯一 scene length unit。只有有限且严格 `z>0` 的像素有效；0、负值、NaN 和无穷均无效。
- projection confidence 只有在 depth 有效、confidence 有限且位于 `[0,1]` 时有效。
- 缺失值以显式 validity mask 表达。参考实现对无效位置输出有限占位值 0，并同时返回 `False`；不得把 0 当真实观测，也不得用 NaN 参与排序。
- 所有上界均用 `<=` 通过，所有下界均用 `>=` 通过。仅 depth-discontinuity 的定义使用严格 `>`；处在其阈值上不算边界。
- 任一必需统计量非有限、分母为 0、shape 不一致或必需集合为空时抛出 `SpecError`，该 candidate/arm 失败。不得填 0 后继续，也不得跳过难例重算聚合。

### 2.2 Canonical weight-map bytes

weight map SHA 的字节串唯一为：

```text
UTF8/ASCII("S48_WEIGHT_MAP_V1\n{height}\t{width}\n")
+ C-order little-endian float64 raw bytes
```

输入先通过上述 `[0,1]`/finite 检查，不重新归一化；IEEE-754 `-0.0` 在写 raw bytes 前规范为 `+0.0`。相同 SHA 的 mask 是重复项；同一 family 内只保留一次，并保留 generator 固定词典序中最早的参数 tuple。

## 3. Mask topology、caliper 与排序

### 3.1 四邻域连通分量

定义 `B(p)=1{W(p)>0}`。两个正像素只有共享一条水平或垂直边时相邻；对角接触不相邻。连通分量数由此 4-connectivity 唯一定义，不得改为 8-connectivity。

### 3.2 Exposed-edge perimeter

每个 `B=1` 像素的四条单位 lattice edge 分别检查。若邻侧越过图像边界或邻像素 `B=0`，该 edge 贡献 1。所有贡献之和为整数周长 `P(W)`。binary area 为：

`A_bin(W)=sum_p B(p)`。

尺度归一化周长唯一为：

`P_norm(W)=P(W)/sqrt(A_bin(W))`。

`A_bin=0` 时无定义并拒绝。候选相对真 support 的周长误差为：

`e_P=|P_norm(M)-P_norm(S)|/P_norm(S)`，要求 `e_P<=0.10`。

### 3.3 Weighted area、histogram、centroid 和 IoU

- weighted area 用 `A_w(W)=sum_p W(p)`。同 shape 下相对误差为 `|A_w(M)-A_w(S)|/A_w(S)`，要求 `<=0.02`；真 support 分母必须大于 0。
- weight histogram 只在 `W>0` 像素上计算。10 个 bin 是 `[0,.1), [.1,.2), …, [.8,.9), [.9,1]`，每个计数除以正权重像素数；零权重既不计数也不进分母。候选与真 support 的 10-bin L1 距离要求 `<=0.05`。
- weighted centroid 使用 pixel center。对 height `H`、width `L`，第 `(r,c)` 像素坐标为 `((r+0.5)/H,(c+0.5)/L)`，按 `W` 加权。两坐标各用 `floor(4x)` 并 clip 到 3，形成 row-major 4×4 cell；候选必须与真 support 同 cell。
- binary IoU 为 `sum(B_S and B_M)/sum(B_S or B_M)`，要求 `<=0.10`。union 为空拒绝。
- 用于 top-199 排序的 centroid distance 是两个归一化质心恢复到 pixel units 后的 Euclidean distance。

### 3.4 同一套 caliper

每个 `G_shape`、`G_camera` 和 `G_source` 候选必须同时满足：

1. weighted-area relative error `<=0.02`；
2. 4-connected component count 完全相同；
3. normalized-perimeter relative error `<=0.10`；
4. 同一 4×4 centroid cell；
5. binary IoU `<=0.10`；
6. positive-weight histogram L1 `<=0.05`；
7. 第 4 节四个 pre-treatment context descriptor 全部同 quartile stratum。

任一项失败即拒绝，并保留全部 failure codes。`G_shape/G_camera` 在各自主协议的完整固定网格中先枚举、再按 mask SHA 去重、再过上述 caliper，最后按下列 key 升序：

```text
(weighted-area relative error,
 positive-weight histogram L1,
 normalized-perimeter relative error,
 centroid distance in pixels,
 generator parameter tuple,
 canonical mask SHA)
```

浮点数使用实际 float64 值比较，不舍入显示值。parameter tuple 的各元素和枚举顺序必须由主 preregistration/G7 固定；本包不生成 camera/surfel mask。每个 shape/camera family 取前 199；去重和 caliper 后不足 199 时停止 Localization，不扩网格、不放宽阈值。`G_source` 使用全部合格项，不抽样、不补齐。

## 4. Metric depth、boundary density 与 quartile ties

### 4.1 Metric-depth finite differences

在有效当前像素上，每个轴分别使用：

1. 前后两个邻居都有效：central difference `(z_next-z_previous)/2`；
2. 只有后邻居有效：forward difference `z_next-z_current`；
3. 只有前邻居有效：backward difference `z_current-z_previous`；
4. 两侧都无有效邻居：该轴无效。

图像边缘自然使用单侧差分。只有 x、y 两个轴都有效时，gradient 有效：

`g=sqrt((dz/dx)^2+(dz/dy)^2)`，单位是 scene length per pixel。

单行或单列图无法同时得到两轴，gradient 全部无效。不能跨无效 depth hole 做 central difference。

### 4.2 Pre-treatment local depth-boundary density

只比较水平/垂直相邻且 depth 均有效的 pair。相对差唯一为：

`q(z1,z2)=|z1-z2|/max(z1,z2,1e-6)`。

当且仅当 `q>0.02` 时，把 pair 的两个端点都标为 depth-boundary pixel。无效邻居不制造边界。对每个 pixel，以自身为中心取图像内截断的 `5×5` 窗口（radius 2）：

`boundary_density = 窗内boundary pixel数 / 窗内有效depth pixel数`。

分母为 0 时该位置无效；否则值位于 `[0,1]`。这是 **scene depth-boundary density**，不是 support 自身周长的重复命名。

### 4.3 Mask summary、population 和 ties

四个 descriptor 分别是：

1. visible metric depth `z`；
2. metric depth-gradient magnitude `g`；
3. projection confidence；
4. local depth-boundary density。

对每个 descriptor：

- quartile population 是该实际 target 的整张 pre-treatment map 中全部有效像素；每像素等权，不读取生成输出、reference loss 或 candidate roster；
- `Q1/Q2/Q3` 使用 Hyndman-Fan type 7：对升序 `x_(0)…x_(n-1)`，`h=(n-1)p`，结果为 `x_floor(h)+(h-floor(h))×(x_ceil(h)-x_floor(h))`；
- 一个 mask 的 summary 是有效交集内、以 `W(p)` 为权重的 lower weighted median：累计正权重第一次达到总权重 `0.5` 时的最小数值；相等数值不加 jitter；
- descriptor 有效交集所覆盖的 `W` 至少占 mask 总 `W` 的 `0.95`。不足时拒绝该 candidate；
- strata 唯一为 `[-∞,Q1)`, `[Q1,Q2)`, `[Q2,Q3)`, `[Q3,+∞)`。值恰等于 cutpoint 进入较高编号；cutpoint 重复会产生空 stratum，这是合法且必须保留的 ties 结果。

候选与真 support 在四个 descriptor 上分别计算 summary，并要求对应 stratum 全相同。不能 pool 四个 descriptor，也不能在候选 mask 内重新算 quartile cutpoints。

## 5. 两个 edit family 和 source-only gates

### 5.1 Family E：`exposure_log_gain`

对 source RGB 每个 channel 独立应用全局曝光：

`preclip(x;a,δ)=x×2^(aδ)`，其中 `a∈{-1,+1}`。

完整严格升序 dose ladder 为：

`δ∈{1/64, 1/32, 1/16, 1/8}` EV。

本版不加入可调 white-balance 向量；这样该 family 只有一个确定处理方向。若未来需要 white balance，必须成为新 family/new spec version，而不能在本 family 中临时选 channel gain。

### 5.2 Family T：`texture_highpass`

先对三个 channel 分别做 separable 5×5 low-pass。每轴 kernel 固定为：

`k=[1,4,6,4,1]/16`。

边界 padding 固定为 reflect-101，即镜像时不重复边缘像素；height/width 小于 5 拒绝。令 `G5(x)` 为该 low-pass：

`preclip(x;a,δ)=x+aδ[x-G5(x)]`，`a∈{-1,+1}`。

完整严格升序 dose ladder 为：

`δ∈{0.05,0.10,0.20,0.30}`。

正号增强已有高频，负号抑制已有高频；不平移像素、warp 或生成新噪声纹理。两 family 都逐元素 `clip(preclip,0,1)` 后得到 source edit。

### 5.3 Source-only measurements

每个 dose 的 `+/-` 两侧分别计算：

| 量 | 唯一定义 | 通过条件 |
|---|---|---|
| RGB MAD | clip 后 RGB 与原 RGB 的全部有效 scalar channel 平均绝对差 | `>=0.5/255` 且 `<=8/255` |
| clipped fraction | `preclip<0 or preclip>1` 的 scalar channel 数除以 `H×W×3` | `<=0.005` |
| edge IoU | 下述 fixed Sobel binary edge support 的 IoU | `>=0.95` |
| CLIP cosine | G7 绑定的唯一模型/预处理对原图和 edit 的 cosine | `>=0.995` |
| LPIPS | G7 绑定的唯一模型/预处理对原图和 edit 的 LPIPS | `<=0.05` |

Sobel 先以 BT.601 `gray=.299R+.587G+.114B` 转灰度，再用 reflect-101 padding 和 kernel

```text
Gx = [[-1,0,1],[-2,0,2],[-1,0,1]] / 8
Gy = transpose(Gx)
```

得到 `sqrt(Gx²+Gy²)>=8/255` 的 edge support。两图 edge union 为空时 edge IoU 定为 1；只有一侧为空时为 0。

CLIP/LPIPS 不是 NumPy 统计；参考实现只接受外部有限 scalar，不计算或伪造它们。未来 G7 必须绑定 exact architecture、revision、weights SHA、input resize/crop、RGB normalization、library/code SHA 和 device determinism。任一缺失时真实 dose selection 保持 **BLOCKED**。

### 5.4 唯一 dose selection

按 ladder 从小到大检查。一个 dose 只有在 `+δ` 与 `-δ` 各自通过上述五门时才合格；唯一选择第一个合格 dose，并对所有 seed/path/Benefit-local 固定。任一侧失败就检查下一预定 dose。完整 ladder 无合格 dose 时返回 `NO_DOSE_PASSES_BOTH_SIGNS` 并停止该 family；不得看生成输出后增加 dose、修改 gate 或只保留一侧。

## 6. Complete unselected-source roster

负控制必须从 ordinary run 的 **complete pre-selection memory/insertion roster** 产生，不能从已选 slot 列表反推。每条记录恰好包含：

```text
insertion_event: nonnegative integer
source_id: unique nonempty Unicode string without ASCII control characters
file_sha256: 64 lowercase hex
active: bool
selected: bool
is_target: bool
is_reference: bool
provenance_complete: bool
artifacts_complete: bool
renderable_all_targets: bool
```

使用严格 bool；整数 `0/1` 不能冒充。`source_id` 在 complete roster 中必须唯一。eligible unselected source 的合取为：

```text
active
and not selected
and not is_target
and not is_reference
and provenance_complete
and artifacts_complete
and renderable_all_targets
```

全部记录先按 `(insertion_event, UTF-8 bytes(source_id), file_sha256)` 升序。每条不合格记录按以下固定顺序保留所有适用原因：

1. `INACTIVE_OR_TOMBSTONED`
2. `SELECTED_IN_ORDINARY_RUN`
3. `TARGET_OBSERVATION`
4. `HELD_OUT_REFERENCE`
5. `PROVENANCE_INCOMPLETE`
6. `SCIENTIFIC_ARTIFACTS_INCOMPLETE`
7. `NOT_RENDERABLE_FOR_ALL_PREREGISTERED_TARGETS`

eligible subsequence 保持这一顺序；第一个就是唯一 negative source。空集时 RQ1 停止，不改为任意未选帧。完整 all-record flow 连同 eligibility 和原因以 tab-separated canonical rows加末尾 LF 做 SHA；未来 manifest 还必须保存原始 roster 的来源和文件 SHA，不能只保存最后一个 ID。

## 7. 原生输出 arm guards

### 7.1 Deterministic mutual patch displacement

该 guard 不是语义相似度模型。它在两张原生 `576×576` RGB 输出上使用固定 NumPy patch matcher：

1. 按 BT.601 转灰度；
2. reference grid center 为每轴 `{16+32k | <560}`；
3. patch 半径 4，即 `9×9`；以 `RMS=sqrt(mean((P-mean(P))²))` 衡量纹理，`RMS<2/255` 的 source/target patch 不合格；
4. 标准化 patch 为 `(P-mean(P))/(RMS+1e-12)`；
5. 在 center 周围 `dy,dx∈[-8,8]` 全枚举，按 `(dy,dx)` 词典序；score 为标准化 patch 的 MSE；保留最小 score，ties 保留第一个；最小 score 必须 `<=0.25`；
6. 从找到的 candidate center 反向执行同一搜索；只有反向搜索按同一 tie 规则选回原 reference center 才是 mutual match；
7. 少于 50 个 mutual matches，arm 失败；否则 displacement 为 match center 的 Euclidean pixel distance，报告 type-7 median 和 P95。

该实现的 manifest 名固定为 `mutual_grid_patch_v1`，descriptor 固定为上述 z-normalized `9×9` 灰度 patch；`ratio_test=NOT_APPLICABLE`、`RANSAC=NOT_APPLICABLE`。执行者不能临时加入 SIFT/learned matcher、ratio test 或 homography 后继续沿用本规范版本。该固定 matcher 的目的只是拒绝 gross displacement/tear 解释，不证明 requested camera/K 正确；相机数值守卫仍是独立前置门。

### 7.2 其余五个 guard quantities

所有量都比较 arm 与同 seed F00：

- **outside brightness difference**：在 `W==0` 的二值 support 外，对两图 BT.601 灰度逐像素绝对差取平均。outside 为空即失败。
- **sharpness ratio deviation**：对整图灰度做 reflect-101 4-neighbor Laplacian `[[0,1,0],[1,-4,1],[0,1,0]]`，用全部响应的 population variance；若 F00 variance `<=1e-12` 则失败，否则为 `|Var_arm/Var_F00-1|`。
- **saturation increase**：pixel 的任一 channel 恰为 0 或 1 即 saturated；返回 `100×(fraction_arm-fraction_F00)` percentage points。负值保留，不 clip 到 0。
- **tear excess**：每对相邻 row 计算跨所有 column 的平均绝对灰度跳变，每对相邻 column 同理；对每条线取 `arm_jump-F00_jump`，最后返回全部 row/column 与 0 的最大值。
- 非有限输入、全黑/全白等导致匹配不足或 sharpness 分母无定义时，arm 明确失败，不用默认 0 通过。

### 7.3 Replay floors 和通过门

每个 seed 至少有 4 个 A0/F00 replay 实例。必须计算所有无序 pair；若实例数为 `n`，回执数必须恰为 `n(n-1)/2`。每个量的 replay floor 是这些 pair 的逐分量最大值。arm 通过要求：

| 守卫 | 通过上界 |
|---|---|
| mutual match count | `>=50` |
| median displacement | `<=max(1 px, replay median max)` |
| P95 displacement | `<=max(3 px, replay P95 max)` |
| outside brightness | `<=max(2/255, replay outside-brightness max)` |
| sharpness ratio deviation | `<=max(0.10, replay sharpness-deviation max)` |
| saturation increase | `<=max(1 percentage point, replay saturation-increase max)` |
| tear excess | `<=max(2/255, replay tear-excess max)` |

全部七项合取；每个失败 code 都保存。replay pair 本身如果 invalid，不可只删除该 pair 后取较小最大值；该 seed 的守卫标定失败。

## 8. 有限参考实现与合成边界测试

参考实现依赖纯 Python 标准库和 NumPy；它不调用 OpenCV、Torch、CLIP、LPIPS、renderer 或模型。所有公开数值函数只返回有限值和显式 validity，或抛出 `SpecError`。

当前测试覆盖 23 个独立边界，包括：

- 对角像素在 4-connectivity 下分离；
- 单像素/双像素 exposed perimeter；
- `W=0` 不进入 histogram，`.1` 和 `1.0` 的 bin 边界；
- pixel-center centroid、empty support 拒绝和 canonical mask SHA；
- 平面 metric depth 的 central/one-sided exact gradient；
- NaN depth 输出有限占位加 invalid mask；
- depth relative jump 恰等于/严格超过阈值；
- lower weighted median、重复 quartile ties 和 stratum 边界；
- context valid-weight coverage 失败；
- exposure 公式、constant image 的 texture fixed point、非 ladder dose/NaN 拒绝；
- source gate 上下界等号通过、双侧最小 dose；
- complete roster 排序、多重排除原因、重复 ID 和 truthy integer bool 拒绝；
- 原生合成纹理的 mutual matcher/全部 guard 零差，以及已知 1-pixel 平移的恢复；
- guard 阈值等号通过和每项超界 failure code；
- A0 replay 必须含全部无序 pair及逐分量最大值。

标准运行方式：

```bash
python3 -m py_compile \
  work/S48_geocausal_kill_experiment/s48_analysis_reference_v1.py \
  work/S48_geocausal_kill_experiment/test_s48_analysis_reference_v1.py
python3 work/S48_geocausal_kill_experiment/test_s48_analysis_reference_v1.py
```

本次作者自检结果是 `Ran 23 tests ... OK`，只属于 synthetic/source-code evidence。fresh reviewer 必须从冻结 SHA 重跑；作者自检不等于独立审查。

## 9. 明确保持 BLOCKED 的自由度

以下项目无法在不读取新证据或实现真实系统的情况下严谨完成，因此本版不假装闭合：

1. **source edit adapter**：连续 float64 edit 如何进入 VMem 的实际 semantic 与 latent preprocessing，是否重新量化以及两条路径是否字节/张量一致，尚无绑定 patch 和 trace。
2. **CLIP/LPIPS**：阈值已冻结，但 exact weights、revision、preprocessing 和 deterministic execution 未绑定；在此之前不能正式选择 dose。
3. **placebo generators**：本包固定 caliper/statistics，不实现 `G_shape` 变换、camera renderer 或 source provenance projection；199 个 mask 的 feasibility 未测。
4. **arm process/hook**：没有 observer/replacement API、consumer completeness、fresh-process launcher 或 positive-control trace；不能创建 F00/F10/F01/F11/sham/negative/positive arm。
5. **causal contrast**：本包不独立解决 V4 的 `C-V4-1`。当前主 preregistration V5 另行规定每个 `f×s×a` 的 `edit−matched-zero` 直接 pair，并以 `max(0,e^a-max(q_replay,q^a_negative))` 的逐像素 control-excess magnitude 做 Localization；该因果合同、arm 实现和反例测试仍须随 V5 fresh review。本包只为其输入 support/placebo 提供纯数组规范，不能把自己写成 C-V4-1 的关闭证据。
6. **Benefit/reference**：本包没有定义 reference target-time mapping、identity、warp/common-visible 或两侧 Benefit 合取；RQ3 仍不得运行。
7. **scientific adequacy**：fixed NumPy matcher 与 source gates 目前只通过合成边界，未证明在合格真实非输出预处理数据上有足够覆盖；无输出 feasibility 和 fresh adversarial review 仍必需。

因此，本规范包唯一允许的表述是：**M-V4-1 所列纯数组自由度已有一个有限、可反驳、待独立审查的确定版本。** 它不是模型结果、不是因果效应、不是方法增益，也不是创新证据。
