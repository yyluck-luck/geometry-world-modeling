实际审查记录UTC：2026-09-10T18:57:59.030500+00:00。

# S84 单锚点 camera-Z 前后比较：独立设计审查

**结论：未发现阻止一次既定范围评分的设计性 blocker。** 该设计比较的是 S83 初始化（已经过原 MST）与第 100 次更新后、清理前，history 19 的保存 camera-Z 对同一张既有关联传感器深度的条件误差。它没有比较原始 S82 head 与传感器，也不评价生成图。实施仍需核作者最终源码/合同是否落实以下已定规则；本文件不新增实验条件或质量筛选。

## 对比较正确性直接有影响的检查

1. **camera-Z 与单位。** S83 `snapshot` 的 `depth` 来自 `scene.get_depthmaps()`，局部 adapter 对原注册 log-depth 取 exp；原 `depth_to_pts3d` 用 `[(u-cx)Z/f,(v-cy)Z/f,Z]` 再乘固定 optical c2w。因此直接比较的是相机光轴 Z，不是射线长度、world_points 的第三分量、raw self/cross head 或对数值。S83 四个给定 c2w 的平移沿既有米单位坐标；本次不加 VMem scale/轴翻转或拟合尺度。米单位约束不保证预测准确，也不能把预测世界坐标数值直接当传感器 Z。
2. **history 与阶段身份。** 只取两个完整档案中唯一的 history ID 19，必须核四 ID/实际 shape、输入档案及 body SHA；不可凭数组行号 19 或默认最后一行。两档应为 INITIALIZED_STATE 与 FINAL_BEFORE_CLEAN，不能挑最优中间步、清理后支持集或换 raw 结果。S83 两档来自同一次已接受计算，S82 的三个原始尝试不是三次前后对照。
3. **512→native。** S82 的已冻结 `native_to_512=diag(.8,.8,1)` 和 K512 的 420/255.6/191.6，与原名义 K 的 525/319.5/239.5 一致；因此整数网格的逆变换是 1.25×(u,v)。这是沿用原 K 坐标近似，不是逐个 RGB 重采样支撑的物理等价。不得直接复用 S81 的576裁剪逆变换、额外加半像素或根据误差重新校准 K。可通过已接受元数据身份与保存 K 绑定这条映射，不必重跑 RGB 预处理。固定网格在 native 的最大连续坐标为 (638.75,478.75)，按现有域规则全部在域内；该事实来自尺寸算术，不是本轮传感器统计。
4. **取整与传感器解码。** 最近邻必须是 floor(native+.5)，不是银行家舍入 `rint/round`；例如 u=2→2.5→3，u=510→637.5→638。保留连续域与最终索引域检查，不裁边、不邻域回填。官方存档和 S81 均指定注册 PNG 原值/5000 米、raw0 缺失，fr2 的1.031已应用，不能重复乘。16-bit grayscale PNG 经 Pillow 可成为32位整数数组，核 PNG header/640×480/整数范围0…65535即可，不能因为解码 dtype 不叫 uint16 就错误拒绝或先强转掩盖异常。
5. **固定支持分母。** N=512×384=196608；V 只由固定映射和传感器 raw>0 决定，两阶段共享完全相同的 V。非有限与非正预测须在 V 上逐阶段互斥计数，不允许以 confidence、clean、深度阈、遮挡、边缘或预测有效性重定义主支持。全部 N 行留坐标和原因。主量为 FP64 的 Σ|Zpred−Zref|/V 米，AbsRel 为 Σ(|误差|/Zref)/V（无量纲），中位绝对误差为米；非有效参考不能进入分母或补0误差。
6. **配对与无效分支。** 同一像素前后绝对误差比较，改善/相等/恶化计数必须列完整 V；若任何阶段在 V 上有无效预测，主比较不可评分，不能靠共同有限子集主张成功。V=0同样不可评分。共同有限子集若另列，明确是解释性辅助且不能替代主量。

## 两处需要在最终实现消除的原稿歧义

- 原稿允许用扩展值 +∞ 标示阶段失败；当两阶段都失败时，直接相减会形成 NaN。最小正确做法是保留阶段 invalid 数与失败标记，整体比较写 UNSCORABLE，不执行 ∞−∞。这是无效分支的表示问题，不要求增加新模型或挑点。
- 原稿同时写“Δ≥0否决”与“数值容差内无法分辨”，正的小变化会落入两条。冻结实现须用互斥三段：Δ<−ε、|Δ|≤ε、Δ>ε。ε 为提前写清的数值判断精度，不是传感器准确度、实际意义阈值或统计置信区间；不得根据真实结果调整。

作者已在消息中确认上述两点将写成 UNSCORABLE 与互斥三分支，同时说明已采用 floor(+.5) 和整数解码范围检查。**本审查未据该消息宣称最终代码已验收**；仍以即将冻结的准确版本为准。

## 结论允许到哪里

若共同固定 V 完整可评分，且最终 MAE 更低，只支持“该锚点、该时刻、该既定预算下，模型预测拟合目标下降伴随更低的此参考 MAE”。它不支持每点变好、100步收敛、物理几何同比改善、四历史整体更准或新方法成立。若 MAE 未改善，否决本锚点预先指定的伴随改善命题，不能外推所有几何引导无效。

该传感器参考已在 S81 使用，本次不是盲测或独立新场景。深度晚于 RGB 17.126ms；注册、近似 K、无额外去畸变及运动/遮挡边缘误差继续存在。它们限制解释，但在固定前后比较中不自动构成执行 blocker。既有共同相机是合法输入，不能虚构成新增 GT 泄漏；真正的边界是评分参考不回流调整 S83 参数、尺度、选择或指标。相邻像素高度相关，196608位置不是196608独立样本，不做据此推断的p值或置信区间。

## 实际读取范围

本次只读设计、S81合同及取样/解码/指标源码、S83已冻结入口/合同、S82坐标合同及保存预处理字段的源码、TUM既有官方网页本地存档的单位/注册/校正段，并恢复项目原则与当前主账。没有联网，没有读真实 PNG/header/像素或 NPZ 科学数组，没有运行评分/模型/优化器，没有修改作者源码、实验或旧报告。以下 SHA 是本次重新读取文字字节计算；不能当作本次二进制输入复核。

- `work/S83_fixed_camera_geometry/NEXT_DEPTH_DIAGNOSTIC_PLAN.md` — `27235cbd8b74a3141c50e6b9883565a375370dd2b39112a4938800d5f7df5f66`
- `work/S83_fixed_camera_geometry/CONTRACT.json` — `0ff3a1f1c4aeaadb455ec6a3e832217978148172ae0018a5bf97b53859a7be5a`
- `work/S83_fixed_camera_geometry/run_fixed_geometry.py` — `76c5a6a4a67a391e97e6ebaa7c13cc0a520092be563a10f27a8cebad3f33afc3`
- `work/S81_anchor_depth_reprojection/CONTRACT.json` — `ae317145a909f12fe94cd0ad221fa54da1a032855f585b73bc996b3ec0cc57a4`
- `work/S81_anchor_depth_reprojection/run_reprojection.py` — `ce9f929e2d106b831144a262ff9f616e4e45d5ba8d82f733fc1af70524cd8d73`
- `work/S81_anchor_depth_reprojection/SOURCE_FEASIBILITY.md` — `fa1a9efa50345bc5b3e8b3a200622ce35af561d0c7ba64776de8157d2283185b`
- `work/S82_history_geometry_guidance/FOUR_HISTORY_CONTRACT_V3.json` — `2b08a75003468ced7b15ea92d4b8c01c00e7f532d0893dcde0958d4fd33d45f1`
- `work/S82_history_geometry_guidance/build_four_history_geometry_v3.py` — `e789370a0f7871238596a30ceae02c01567b25fadc38f0a6e9304ca69eb20eb3`
- `work/S14_new_scene_identity/tum_formats.html` — `bb7d80dca9a4bbb19b52a22284219ae39387a0461f4b7cb077a550954f58843b`
