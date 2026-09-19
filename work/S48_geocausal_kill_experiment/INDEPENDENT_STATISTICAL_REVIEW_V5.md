# S48 V5 独立统计、因果与源码对抗审查

- 审查者：`/root/s48_v5_adversarial_review`；未参与 V5 协议、normative spec、reference implementation 或 tests 的撰写。
- 审查完成时间：2026-09-08T16:20:26+08:00。
- 主协议 whole-file SHA-256：`b8b98ec99d89abdbb83ae45bded2981ef0e654533f051bb351cf82bf355f767c`。
- normative spec whole-file SHA-256：`a88efa8f5f3e23da75132c2167fd5bd1f5cb58de5498425df4f7656a402718de`。
- reference implementation whole-file SHA-256：`2cacc5c312af92dfe823db7c7519cffc4f2f16fc4c9b8d9a34d6aa94a81359c7`。
- synthetic tests whole-file SHA-256：`f611e22deb68402ed1b04764f31214d759334679feb5c9514f6a6270abd27bb1`。
- V4 review whole-file SHA-256：`c7f55fc50869b8294fbf5b3148ece759f96fbed59b63fd887ceae1cdd1dae0b4`。
- **裁决：BLOCKED。CRITICAL 2 项，MAJOR 6 项，MINOR 3 项。**
- 本报告 canonical SHA-256：`2b66553a8f3f96a556dc92228cff68c8db33706bd4508719cef9ba6402a2d44c`；计算时删除本字段所在整行，保留其余 UTF-8 字节和 LF。whole-file SHA 在交付消息中给出，避免自引用哈希。
- 权限边界：只读审查上述冻结源码/文本并运行内存合成数组；0 模型导入或运行，0 S48 arm，0 formal prepare/attach/auth/launch，0 C1/C2 tensor/image/pixel 正文读取、映射、解码或查看；四个冻结输入和项目总账均未修改。

## 1. 结论

V5 有实质进步。它把主处理改成每个 `family × seed × sign` 的 `edit−matched-zero` 直接配对；`B_local` 改为正负两侧逐项合取；reference 的 target-camera 距离不再错误排除精确目标相机；common-valid、outside 和 full-support 域也已显式列出。4-connectivity、exposed-edge perimeter、`W>0` histogram、metric-depth gradient、quartile ties、两个 edit family、未选来源 roster 和固定 NumPy matcher 都比 V4 更接近有限合同。

但 V5 仍不能通过 fresh review，原因不是“代码还没运行”这么简单，而是两处规则本身可让主结论失去唯一含义或产生假阳性。

第一，主协议先规定 PNG 读入后已经除以 255，却在直接效应公式里再次除以 255。一个灰阶码值的变化会被解释为 `1/255` 或 `1/65025`，足以翻转 `delta_I=0.5/255` 的继续判定。第二，V5 用空间上不匹配的未选来源 effect magnitude 逐像素扣除 target effect magnitude。这个运算能把完全均匀的 target 直接效应雕刻成位于真 support 的 `e_excess`，即使 negative 的全图平均只有 target 的 15%。下面给出实际 8-bit 网格、全部现有 arm guard 通过的复算反例。

此外，matched-zero 的精确零剂量路径在 reference code 中不存在；replay floor 只数记录数量而不绑定 pair identity；输出 guard 接受任意连续浮点图且会漏掉周期纹理中的局部位移；Benefit 的 identity、同步、视图配对、loss 单位和 matched replacement comparator 仍不唯一。因此本报告不授权 G7、hook、任何 S48 arm 或 novelty/method claim。

## 2. 审查方法与实际执行

审查顺序为：先重算四个指定 SHA，任一不匹配就立即停止；通读 V4 review 后，把 `C-V4-1`、`M-V4-1..4` 和三项 MINOR 转为可验证条件；逐函数对照 V5、normative spec、reference code 和 tests；最后运行原 23 项测试以及不修改冻结源的临时反例与边界探针。

采用项目 `RESEARCH_PRINCIPLES.md` 的证据分级，并应用本地 `/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md` 中的构念效度、对照、混杂、反例和证据比例检查。没有外网检索；本报告不重新认证近邻文献覆盖。

实际解释器为 `/opt/homebrew/opt/python@3.13/bin/python3.13`，Python `3.13.0`，NumPy `2.4.6`。执行：

```text
python3 -m py_compile s48_analysis_reference_v1.py test_s48_analysis_reference_v1.py
python3 test_s48_analysis_reference_v1.py
```

结果为 `Ran 23 tests in 2.262s — OK`。AST 也确认恰有 23 个 `test_*` 方法。Python 3.12 本机没有 NumPy，实际得到 `ModuleNotFoundError: No module named 'numpy'`，所以本审查没有声称跨两个解释器通过。所有临时探针只创建内存中的合成数组；探针不保存、不搜索实验图像。

23 项原测试通过只证明被测试的边界与当前实现一致。它不能覆盖测试没有表达的 causal estimand、单位、pair identity、周期纹理、浮点输入来源或 reference 资格。

## 3. V4 问题关闭表

| V4 项 | V5 状态 | 本轮独立判断 |
|---|---|---|
| `C-V4-1` spatial sham 假定位 | matched-zero 直接 pair 已正确移除原始 sham-vs-F00 混杂 | **PARTIAL / STILL BLOCKED**：原反例关闭，但 pixelwise negative subtraction 产生新的假定位，见 `C-V5-2`；零剂量 matched path 也未在 reference code 中实现 |
| `M-V4-1` 核心数组、edit、guard、roster 自由度 | 大部分纯数组公式已写成有限版本 | **PARTIAL**：source adapter/zero dose、placebo generators 和实际 input-domain enforcement 未闭合；reference/tests 还有与文字不一致的边界 |
| `M-V4-2` Benefit common-valid/outside/full-support | 已明确 `C_local/C_out/C_fullsupport/C_matched(P)` 和 70% coverage | **PARTIAL**：loss 数值域/公式、hole 分母及逐视图 identity 域仍不唯一；见 `M-V5-5` |
| `M-V4-3` 两侧平均掩盖一侧改善 | 改为每个 `f×s×a×t` 均 `>=delta_B` | **CLOSED_AS_CONTRACT**：逐 sign 合取正确；不得再用对称平均代替 |
| `M-V4-4` reference 相机、时间、identity | target-camera caliper 已与 replacement caliper 分开；`t_target` 指向 sensor capture | **PARTIAL**：同步 residual 的观测定义、identity agreement、动态/亮度的视图 pair 和若干排序换算仍缺失 |
| `N-V4-1` 等号与 target 粒度 | Influence 与 Benefit 都按每 target、每 sign 使用 `>=`；episode 仅描述 | **CLOSED** |
| `N-V4-2` 辅助文件 SHA 混写 | V5 不再依赖错误的 method-fix SHA | **CLOSED_FOR_THIS_INPUT_SET** |
| `N-V4-3` static hook V2 未独立核验 | V5 明确仍未复核且保持执行 BLOCKED | **OPEN_BUT_HONESTLY_DECLARED**；不能作为 hook evidence PASS |

## 4. CRITICAL

### C-V5-1：主 RGB 直接效应有 255 倍单位歧义，继续门可被同一像素差翻转

**位置：** 主协议 L155、L209–223；亦影响 L277–297 的 Benefit SESOI。

L209 规定 PNG 的 uint8 通道“读取后转 float64 再除以 255”。因此若在后续公式中令 `Y` 表示已读入的数组，`Y∈[0,1]`。但 L211 又定义：

`e(p)=mean_c |Y_edit(p,c)-Y_zero(p,c)|/255`。

这会再次除以 255。对恰好一个码值的 RGB 变化：

- 若 `Y` 是 raw uint8，正确归一化差为 `1/255≈0.00392157`，超过 `delta_I=0.5/255`；
- 若严格执行 L209 后再执行 L211，结果是 `1/65025≈0.00001538`，不超过同一门。

两种解释都能从现有文字得到，却给相反的继续/停止结果。类似地，L277 称 Benefit 为“uint8 sRGB MSE”，但没有说明先除以 255 再平方，还是在 0–255 上平方。两者相差 `255²=65025`，而 `delta_B=0.001` 没有随域改变。

**解除条件：** 唯一选择并贯穿所有公式、代码和 receipt。建议明确 `u=PNG raw uint8`，`x=u.astype(float64)/255`，然后定义 `e=mean_c|x_edit-x_zero|`，不再除以 255；所有 `q_replay/q_negative/tau_output/brightness/MSE/delta` 都在 `[0,1]` float64 域。加入一个恰好 1 code-value 的 Influence 和 Benefit 边界测试，并绑定 decoder/PNG mode/shape。

### C-V5-2：pixelwise negative-control magnitude subtraction 能从均匀 target effect 制造真 support 富集

**位置：** 主协议 L182–186、L211–223、L229–257、L370/L377。

matched-zero 直接 pair 确实修复了 V4 的“sham 自身局部变化”问题。但新的

`e_excess=max(0,e_target-max(q_replay,q_negative))`

把来自不同 source、通常具有不同空间作用区的非负 magnitude map 当成可逐像素交换的 nuisance map。它们并不具有这种空间可交换性。逐像素相减可以创造 target map 原本没有的相对空间结构。

**有限、实际 8-bit 网格反例。** 取 576×576 textured grayscale F00，通道值为整数 `80..175` 后除以 255；真 support 为前 86 行，`area=86/576=0.14930556`。令 target edit 与 matched zero 的输出差在全图每个像素恒为 RGB 整数向量 `(8,-5,4)/255`；令 negative edit 与 its zero 的输出差只在 support 外为 `(1,-1,1)/255`，support 内为 0；replay 为 0。这些向量都保持在有效 8-bit 网格，BT.601 灰度改变量分别仅为 `-0.087/255` 与 `-0.174/255`。

实际复算：

```text
E_target                 = 0.022222222222222227
Q_negative               = 0.0033360566448801623
Q_negative / E_target    = 0.15012254901960728
I                        = 0.018886165577342063 >= 0.5/255
area(S)                  = 0.14930555555555555
mass_excess(S)           = 0.17567892333573645
L_area                   = 0.02637336778018090 >= 0.02
ER                       = 1.1766402307137698 > 1
same-area disjoint mass  = 0.14467676039413602
L_vs_disjoint            = 0.03100216294160044 > 0
```

target 的 **raw direct effect 完全均匀**，所以它没有“作用集中在真 support”的性质；富集完全由 support 外扣掉一小张 negative magnitude 造成。任意满足低 IoU 的同面积 placebo 都会收集更少的 `e_excess`，因此在存在 199 个合格 mask 时尾部 rank 也可通过。

更关键的是，此构造通过当前全部七项 arm guard：target 和 negative 都有 289 个 mutual matches，median/P95 displacement 为 0，outside brightness 分别约 `0.0003412/0.0006824`，sharpness deviation 近 0，saturation increase 0，tear excess 近 0；`arm_guard_decision` 均返回 `(True, ())`。negative 的全图 effect 只有 target 的 15%，所以 L370/L377 没有数值定义的“同量级”不能可靠排除此例。

这不证明真实模型会产生该模式；它证明现有规则允许该模式被错误解释为 Localization PASS。

**解除条件：** Localization 的主 map 应使用 matched-zero 后的 raw direct effect `e_target`，这样均匀效应必然回到面积基线。negative control 应作为单独、预注册的反证门，例如比较同一个 target support 上的 localization statistic 或要求它自身不超过明确的 numeric bound；若要做 difference-in-differences，必须用有符号 output contrast、明确共同空间 estimand，并证明 negative/source/geometry 可交换。不能用不同 source 的 absolute magnitude map 逐像素扣除后继续声称 target direct effect 定位。修订后加入本反例的永久测试。

## 5. MAJOR

### M-V5-1：matched zero-edit 是核心 comparator，但冻结 reference code 无法表达 `dose=0`

**位置：** 主协议 L169–186；normative spec L152–207、L325–334；reference L664–686、L788–820。

V5 要求 zero arm 与 edit arm 走完全相同的 `decode→edit→encode→all-consumer-replace` 调用序列，唯一差别是参数为 0。但是 `edit_preclip/apply_source_edit` 只接受非零 ladder，`dose=0` 会抛出 `SpecError`；23 项测试也没有 zero-path test。执行者只能绕开 frozen function，或另写未审代码，二者都不能证明调用路径相同。

normative spec L33 同时把“是否重新量化为 uint8”留给未来 adapter。量化发生在 edit 前、clip 后或两条 consumer 各自预处理时，会改变 zero sham、source gates 和真实处理对象。这个诚实的 BLOCKED 声明值得保留，但意味着 `M-V4-1` 和 `C-V4-1` 尚不能被当前三文件包关闭。

**解除条件：** 在下一冻结版本实现并测试每个 family/sign 的 exact zero 参数，保证与非零 edit 进入同一函数和 adapter；固定 clip/round/uint8 conversion 的次序、rounding rule、semantic/latent preprocessor 和逐路径 tensor SHA。另做相同输入两次 zero 的 determinism test。

### M-V5-2：replay floor 只验证记录数，不证明完整 pair；方向性指标与“unordered pair”冲突

**位置：** normative spec L276–290；reference L967–1067；tests L292–309。

`replay_guard_floors(metrics,replay_instance_count=4)` 只检查 `len(metrics)==6`。记录没有 replay instance ID、pair ID、seed、target 或 canonical `i<j`；六份相同记录会被接受。原测试 `test_replay_floors_are_componentwise_maxima` 本身使用 `first,second` 的重复列表，`test_replay_floor_requires_every_unordered_pair` 只测试长度不够，因此测试名声称的“每个 unordered pair”没有被验证。

同时，saturation increase、sharpness ratio 和 tear excess 都是方向性量。只保存 unordered pair 的一个方向会因文件顺序得到不同 floor。`arm_guard_decision` 也不验证 `ArmGuardFloors`：六个字段全是 NaN 时，Python 的 `max(fixed,nan)` 会保留 fixed bound，本轮实际得到 `(True,())`。`p95>=median` 也未检查。

**解除条件：** floor API 接收带 `seed,target,replay_i,replay_j` 的 typed receipts，要求精确等于预期 canonical pair set、无重复、无缺失；将方向性量改为对称定义或对每个 pair 保存两个方向并取最大。验证 floors 全有限、在数学域内、`p95>=median`，并加入 duplicate/high-pair omission/NaN/reversed-direction 攻击测试。

### M-V5-3：guard 的“native uint8 PNG”域未被代码执行，原测试反而使用连续浮点图

**位置：** normative spec L30–38、L250–290；reference L136–148；tests L244–265。

文字要求 guard 输入来自 native 576×576 saved PNG 的 uint8 值除以 255。`_validate_rgb` 只把任意输入强制转换成 float64 并检查 `[0,1]`；它不要求 `x×255` 为整数，也不接收/验证 PNG receipt。原 guard 测试用 `rng.uniform(0.1,0.9)` 生成连续浮点图；本轮测得离最近 uint8 grid 的最大距离约为 `0.49999997` code value，仍被公开 guard API 接受并产生 289 matches。

这会改变 exact saturation、clipping、edge threshold 和 code-value SESOI 的边界。一个 pre-save float 的 0.999 值不算 saturated，保存/读回后可能成为 1.0。

**解除条件：** 输出 guard API 最安全的合同是只接受 `np.uint8` H×W×3，再在内部唯一转换；或严格验证 normalized array 的每个值恰在 uint8 grid，并绑定 image decoder receipt。source edit 的连续 float 域应使用不同函数名/类型，避免与 output guard 混用。测试必须使用真实 uint8 synthetic arrays。

### M-V5-4：固定 matcher/guards 可被周期纹理和局部位移规避，不能单独排除结构替代解释

**位置：** 主协议 L193–195；normative spec L250–290；reference L823–964。

本轮构造 32×32 随机 uint8 tile 平铺到 576×576，在一个 16×16 区域加 8 code-value marker，再把整图循环平移 32 px；周期背景不变，marker 的 512 个 old/new pixels 移动。support 覆盖 old/new marker 区，因而 outside brightness 为 0。当前 guard 返回：

```text
match_count=289, median=0, p95=0,
outside_brightness=0, sharpness_deviation=0,
saturation_increase=0, tear_excess=0.00012255,
decision=(True,())
```

这不是说任一 image matcher 能从完全无纹理区域恢复相机；normative spec L264 已正确承认 numeric camera guard 是独立前置门。问题是主协议仍让这些 guard 承担“整体画质/撕裂替代解释已排除”的硬门，而 P95 全局 grid 会忽略占不到 5% matches 的 support 内结构移动，所有非位移 guard 又主要在灰度/全局量上工作。`C-V5-2` 的低幅 RGB 构造也表明三通道差异可在 BT.601 灰度几乎不变时全部通过。

**解除条件：** 限定 guard 的允许解释，不能写成已排除所有相机/geometry artifact；增加 support 内与 support 邻域的 coverage、位移分位数和 RGB/chroma outside metric，报告每个 grid cell match coverage。周期/重复纹理、低纹理、局部 object shift 和 pure-chroma tests 必须进入冻结 suite。requested camera/K 的数值守卫继续独立存在。

### M-V5-5：Benefit common-valid 集合有进步，但 reference/identity/loss 仍不是唯一可复算对象

**位置：** 主协议 L265–297。

以下关键选择仍会改变纳入候选或 `B` 是否越过 SESOI：

1. “同步校准实测残差”没有定义用哪些 sensor observations、怎样拟合 offset/drift、怎样聚合 residual；仅给 `<=10 ms` 不足以重算。
2. `S_t` 加权的 per-pixel identity agreement 没有写比较 `O↔R`、`O↔P`、三者全相等中的哪一个，也没有明确 invalid/hole 的分母。ID set equality 不能替代逐像素对应。
3. “非动态区几何 warp 后每通道 RGB 中位差”没有列出必须计算的 view pairs；`O↔R`、`R` 两侧邻帧、`P↔R` 会给不同资格。
4. warping-hole ratio 的 numerator/denominator 未定义；相机相对角、FoV 差和 μdeg/ppm 排序值的计算/舍入也未冻结。
5. `ℓ^W_C/ℓ^full_C/ℓ_out` 没有有限公式说明 channel/pixel 聚合与 RGB normalization；`C-V5-1` 使 SESOI 的单位更加不确定。

因此 `M-V4-2/M-V4-4` 只能记 partial。G7 表格说未来绑定实现是正确的停止门，但不能把尚未写出的实现算当前协议已唯一。

**解除条件：** 增加 reference/Benefit normative spec 与 finite implementation，显式给每个 domain、valid mask、warp、hole、identity pair、channel aggregation、timestamp mapping、camera metric 和 stable sort conversion；用 exact-target camera、partial visibility、swapped identity、empty outside、boundary equality和多 reference tie 做 synthetic tests。

### M-V5-6：`B_matched` 没有保证 O 与 P 走相同替换/重编码路径，P 的时间资格也不明确

**位置：** 主协议 L289–297。

`B_matched=loss(Y(P),R)-loss(Y(O),R)` 没有说明 `Y(O)` 是 untouched ordinary F00，还是把 O 通过与 P 完全相同的 decode/encode/all-consumer replacement adapter 重插入目标 slot。若 P 需要重编码/替换而 O 沿原 stored tensors，`B_matched` 会把 adapter effect 算进 source utility，重复 V4 sham 类混杂。局部 Benefit 已有 matched zero 思路，matched replacement 也必须同样处理。

另外，P 被称为历史未选帧，却又要求“逐 P 的时间门”，没有说明时间是匹配 O 的 source time、target time，还是只检查 reference synchronization。三者定义不同的候选集合和 scientific question。

**解除条件：** 固定 `O-reinsert` comparator：O 和每个 P 使用相同 injection point、编码/量化、fresh process、noise/RNG 和 consumer trace，唯一差别是 source content；保存 ordinary F00 只作管线诊断。把 P 的时间变量、比较对象和容差写成公式；若不需要 target-synchronous P，删除含混的“时间门”。

## 6. MINOR

### N-V5-1：十进制 histogram 边界在代码中并不都等于文字边界

reference 用 `np.linspace(0,1,11)` 生成 edges。float64 下 edge 3 是 `0.30000000000000004`，而输入 literal `0.3` 更小，所以 `0.3` 被放入 `[0.2,0.3)` 的第 3 个 bin，而非文字规定的 `[0.3,0.4)`；`0.6` 和 `0.7` 也分别落入前一 bin。本轮逐边界探针得到 bin indices `1,2,2,4,5,5,6,8,9`，预期应为 `1..9`。这可能改变 histogram L1 的等号资格。

建议用冻结的 `index=min(floor(10×W),9)` 公式并逐一测试 `.1` 到 `.9`，或把 exact binary64 edges 写入规范。

### N-V5-2：显式 validity mask 会被静默强转为 bool

`context_descriptor` 使用 `np.asarray(valid,dtype=bool)`，因此 NaN、非零整数和任意非零 float 都会变成 `True`。本轮传入含 NaN 的 validity array，函数仍返回 `summary=1.0, valid_weight_fraction=1.0`。内部 `mask_context_strata` 当前产生 bool，故这不是已观察到的主路径错误；公开 reference API 仍应拒绝非-bool dtype，避免未来 adapter 把 malformed validity 当有效。

### N-V5-3：reference roster 排序的整数单位换算没有 ties 规则

L267 用 angular difference μdeg、position ratio ppm 和 FoV difference μdeg 排序，但没有规定 round-half-even、floor、精确有理比较或先比较 float64。临界候选可能因实现换序。建议保存 raw float64 bits 和唯一整数 conversion rule；file SHA 只能解决前面字段完全相等后的 tie，不能解决换算差异。

## 7. 已确认的优点

1. 四个指定输入 SHA 在审前、原测试后均精确不变；没有串版。
2. `B_local` 逐 sign/seed/family/target 合取正确关闭 V4 对称平均反例。
3. `C_out/C_fullsupport/C_matched(P)` 明确与真实 view validity 相交，且失败不填洞、不换 reference，这比 V4 明显严格。
4. reference target-camera distance 与 replacement baseline caliper 已分开；精确 target camera 可通过。
5. 4-connectivity、exposed-edge perimeter、`W>0` histogram、type-7 cuts、lower weighted median、depth finite difference、roster reasons 和 most array thresholds 基本与文字一致。
6. tests 对已包含的 23 个边界均通过；empty/NaN/dose/tie/threshold 的多项拒绝是有效工程证据。
7. 文本持续声明 `execution authorization=NONE`、`novelty_authorization=NONE`，没有把 source-only 合成测试写成模型结果。

这些优点说明 V5 是有效修订，不改变 BLOCKED 裁决。

## 8. 下一版解除顺序

1. 先统一 RGB 单位并给 Influence、guard、Benefit 共用的 typed array contract；加入 one-code-value tests。
2. Localization 回到 raw matched-zero direct map；重新设计 negative 的独立空间反证门，并永久加入 `C-V5-2` 反例。
3. 在 frozen reference 中实现同路径 `dose=0`、source adapter quantization 和 repeated-zero determinism。
4. 让 replay receipts 带完整 pair identity；修复方向性、NaN floors 和 metric domain。
5. 修复 histogram 全部边界、strict uint8 guard input、periodic/chroma/local-shift tests。
6. 为 Benefit/reference 写独立 normative code，闭合 identity、sync、warp/hole、loss 和 matched O-reinsert comparator。
7. 新四件套重新冻结 SHA，并交不同作者做 fresh protocol+source review。只有这一审查 PASS，且 G0/G1 自然失败、hook、launcher、consumer completeness、placebo feasibility 和 reference 都分别有实物 PASS，才有资格创建 S48 arm。

## 9. 允许与禁止的结论

当前允许的结论是：V5 关闭了 V4 的两侧平均问题，并用 matched-zero 正确改变了主处理对比；但其 RGB 单位和 pixelwise negative spatial calibration 仍阻断主 Influence/Localization 解释，normative/reference/Benefit 包也不完整。

本报告没有观察到真实模型中的反例，也没有证据说明 VMem 无效。它只证明当前规则存在可满足协议却不支持预期解释的有限构造。

继续禁止写：已发现自然失败、已证明来源被使用、已证明 geometry-localized causal effect、已证明 Benefit、PC-DPM 有效或新颖、S48 已运行、已达到 PhD/CCF A 或任何录用水平。
