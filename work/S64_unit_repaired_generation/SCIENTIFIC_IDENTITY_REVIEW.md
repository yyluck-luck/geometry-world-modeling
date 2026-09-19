# S64独立科学身份与准入差异审查

**PASS_S64_SCIENTIFIC_IDENTITY_SOURCE_REVIEW_ONLY，无本范围阻塞。** 实际完成 2026-09-08T21:20:18.360791+00:00（北京时间 2026-09-09T05:20:18.360791+08:00）；审查者 `/root/negative_result_question_triage`，作者 `/root/c2_v9_recovery_author`。绑定最终作者票SHA `d418449ac50228dabbe2c1aac1281c775ecc3e2c61a8c09af1c228116aa10e17`，其17项文件及自身均核SHA/尺寸/0444。仅静态源码、配置和JSON元数据；0模型/RGB/张量体、0renderer、0正式阶段。本票不是core/attachment正式票、授权或生成结果；实际hook与生命周期由primary另审。

## 科学比较合同成立

| 必须分清的事项 | 最终实现及边界 |
|---|---|
| 新旧身份 | `row=C2_UNIT_REPAIRED_S64`、新output、`retrieval_variant.id=s64_positive_camera_depth_median_units_v1`；原ft-mse VAE variant保留。兼容`s47-c2-*`标签不覆盖新科学身份。 |
| 唯一额外科学行为 | 正相机z中位单位同时缩放位置、半径和render相机平移；返回规范深度，权重为`cos/(1+z/m)`。这是实际检索行为改变，不能只称near/far等价修复或物理尺度标定。 |
| 原输入与计算 | living_room SHA `e9d718849d2ddbe5dda7ed3fa80df7d93e99f2d509b07a46019818c2e188d278`；seed44 YAML与V9字节相同。原CPU8/FP32、576×576、T8/context4/target4、50步、400次几何迭代不变。 |
| 从头及资源 | 原空history入口，initialize→left(5)→right(5)，一次加载、两批不重置RNG。1800秒/批、3600秒总、45GiB、空盘≥10GiB；45–50分钟只是历史估计，允许超时/失败。 |
| 结论范围 | 已见C2失败后设计，`eligible_for_original_cohort=false`、`new_method_validated=false`；旧V9失败、原B0/C1分数及不可达2/3假设保留。单例恢复不证明画质收益、跨场景效用或创新。 |

S63最终独立票SHA `90c3eff57423f0360ada6bdfb3ebcbbdf428b707962568698634eae63528a426`及中文结果已读：原空列表异常重现，组件路径返回四类真实缓存；证据止于context，不等于生成。继续从头有明确理由：旧seq36 RNG之后optimizer仍调用随机初始化，五份cache不是完整切点。原观察器的render_input位于规范化前，render_output为规范深度；unwrap只核底层原函数来源，不能将包装入口计数解释为未改原renderer证据。

## 必要差异已进入现有绑定链

实际逐行核S47→S64差异：gate `exact_retrieval_variant/required_sources/exact_derivation_policy/read_frozen`明确新行为及身份；freeze `build_core`加入row和variant，canonical core仅排除review_receipts，因而上述行为及hook/adapter SHA被绑定。attach仅加入review票，core SHA不变；旧component/control/runtime等式保持。

独立静态重建并核SHA：旧219来源全部保持；移除5个V9本地来源，加入6个S64本地来源及固定S61 adapter，得到**221项**，全部当前SHA匹配。另核freeze自身作者票与6项SOURCE_HASHES、launcher/auth的gate pin、协议及YAML pin；AST语法检查通过。S64的LIMITS、runtime `derive_factory`及authorization `main`与V9对应AST相同，保留原seed转换和既有授权逻辑。此处没有导入科学模块或执行gate/model；作者局部check实际先fixture失败、修正临时目录后return0的两份记录均保留，我未重复该fake检查。

新row/variant贯穿core/manifest、metadata/fullgate、runtime_loading、授权与worker/outer终态。现有六SHA授权链足以绑定新增字段，无需新权限状态机。`collect_unit_receipts`检查实际票的manifest/row/variant及三份来源、正有限单位与恰一份成功调用；worker与outer重读并绑定同一个文件SHA集合。不提前填写未来unit SHA；安装票不冒充调用票。其实际调用/异常与退出接线另由primary核验。

root接下来的必要步骤是现有顺序：两份最终源码审查后唯一prepare；核实际core并取得两份不同作者core票后attach；核实际六SHA及两份最终attachment/readiness票后一次authorization；当前资源复核后一次外部监督启动，保留实际outer return、commit/watchdog和失败。成功终态之后才新绑定既有读回/九帧评分；本票不替代任何尚未实际产生的文件。没有要求新检查矩阵、重新运行S60–S63或改变主评分。

## 仅结果后诊断：第一批前缀应不受hook影响

这是**结果前预期、非启动/成功门**。原第一批history=1跳过renderer，新hook按设计尚未作用；完整新运行后比较旧V9与新S64的第一批实际噪声、缓存和输出身份，可发现非预期前缀变化。最小旧来源如下，均为occurrence=0；新档案按name/occurrence匹配，不预设新seq。

| V9事件 | 最小字段 | 旧descriptor尺寸 |
|---|---|---|
| seq34 sampler_input | noise | float32[8,4,72,72]，663552 B |
| seq38 sample_output | samples_z；samples | 同上；float32[8,3,576,576]，31850496 B |
| seq44 cache_commit.cache | 五份c2ws/Ks/latents/encoder_embeddings；生成帧pil_frames[1:5].pixels | 真实保留cache；每帧uint8[576,576,3]，995328 B |

先比较dtype、shape及`bytes_sha256`等内容身份，避开必变时间/运行路径/event-chain SHA，RGB用像素descriptor而非PNG封装身份。descriptor匹配仅是归档声明层，需按后续实际文件核验范围区分与内容重哈希。本次只读这些descriptor，未读取数组或RGB。若噪声已不同，定位随机状态/初始化与顺序；若噪声相同而后续值不同，检查数值执行等因素；不将任何一种模式直接判成因果证明。相同seed不保证逐位相同；差异如实保留，不删失败重挑、不增改阈值，不替代主评分或回填原cohort。无需因此先写新框架。

本轮应用本地Claude科学批判SKILL的设计/构念效度、事后假设偏差与声明比例检查；只用skill，未调用Claude模型。既有S61近邻与单位语义仍足以约束此工程变体，未扩大新主张或重复外部检索。
