# S64 完整单位修复生成变体

本候选从 C2 V9 有效生命周期实现派生，科学身份为 `row=C2_UNIT_REPAIRED_S64`、`retrieval_variant.id=s64_positive_camera_depth_median_units_v1`，输出固定 `results/S64_unit_repaired_generation`。原 V9 的 return1、部分档案与已消耗授权不变。S64 是看过 C2 失败后设计的工程恢复，`eligible_for_original_cohort=false`；不能补成原 cohort 的同条件 C2 行，也不能救回原至少2/3事件假设或称为创新。

已有 S60/S61/S62/S63 验收不再重跑。S63 原失败输入接线实际通过且独立结果票 SHA 为 `90c3eff57423f0360ada6bdfb3ebcbbdf428b707962568698634eae63528a426`，仅证明保存输入的 get_context_info 返回；S64 是否完成真实生成仍未知。

## 唯一科学实现变化

原 S35 factory 和原 pipeline 保持字节不变。新 runtime_adapter 在原模型及 ft-mse VAE 不变量检查完成后、返回 runtime 前，只为该 pipeline 实例安装 unit_renderer_hook。原 bound renderer 被闭包保存，不回查已包装属性，不改类或其他实例。

S61 固定 adapter 位于 `work/S61_unit_consistent_retrieval/unit_consistent_renderer.py`，SHA `a90410b517b20bfa137cdd00a0bbc3b73c1489ebb8a8d0ab672cb06e6387de6c`。它以所有严格正相机 z 的中位数为长度单位，共同复制换算全部 surfel position/radius 与 render-camera translation，保持 R/focal/normal/source ID/缓存不变；仅向原 caller 返回 depth/index/cos maps，receipt 另存。返回 depth 为 `dimensionless_camera_depth_in_positive_median_units`，实际检索权重变为原 `cos/(1+z/m)`；这不是物理尺度标定，不保持原绝对深度语义。无新 fallback、筛帧、步数或生成数学变化。

gate 的 exact_retrieval_variant 对象记录上述行为、hook/adapter 实际路径与 SHA，并贯穿 manifest/core、metadata/full gate、runtime_loading、worker 和 supervisor 终态。原 ft-mse VAE 的 `variant` 对象独立保留。原 gate 原先仅允许相对 B0 的 input/seed 差异，现明确增加 retrieval_variant 科学差异；其余 controls/config/component/runtime/budget 等式保持。实际 required_sources 重建后必须包含本地 hook 与外部固定 S61 adapter；不把旧219项直接当完整新集合。新 hook/adapter 都由现有 execute_verified_module 从同一次核 SHA 的源码字节编译执行，不通过另一次路径重开或缓存 loader。原 renderer 源码也按 manifest 身份核验。

原 integration 在 create_runtime 之后安装观察器，所以外层顺序为：原坐标 render_input 归档 → 单位 hook → 原 renderer → 规范深度 render_output 归档。wraps 保留 inspect.unwrap 到原函数的来源链，只证明底层原 source，不能称科学行为未改。新 wrapper 与 adapter 的身份另列。

每次真实 hook 调用写一份 create-only `retrieval_unit_call_0001.json`（后续按序编号），记录实际时间、manifest SHA、新 row/variant、三份源码身份、原 adapter 单位票和成功/异常。安装记录不冒充调用。原两批路线第一次 history=1 跳过 renderer，第二次 history=5 调用，完整成功预期恰一份成功单位票。worker 和外层 supervisor 分别从实际输出读取票、核内容并绑定文件 SHA；两层绑定必须相同且完整，否则外层不能返回成功。所有失败和部分票保留。

## 原控制与从头运行

固定原 `living_room.jpg`（SHA `e9d718849d2ddbe5dda7ed3fa80df7d93e99f2d509b07a46019818c2e188d278`）、seed44、CPU8/FP32、ft-mse VAE、576×576、T8/context4/target4、每批50 diffusion steps、400几何迭代。一个worker加载一次，依次 initialize→turn_left(5)→turn_right(5)，历史1→5→9，两批间不重置任何 RNG。

从原图重跑两批，不续接旧 cache：V9 最后 sampler RNG 快照后几何优化仍消耗随机数，没有同切点完整检查点。保留每批1800秒、总3600秒、进程树45GiB、空盘至少10GiB、0.5秒监控。约45–50分钟是历史外推，不是新运行保证或实测。本候选作者不执行 prepare/attach/authorization/模型/RGB；root 负责后续阶段与当前机器资源检查。

## 复用既有生命周期

保留 V9 的 source-review → 唯一 prepare → 两份不同作者 core review → attach → 两份最终 attachment/readiness review → 一次 authorization → 一次受监督 launch → 独立结果检查。固定路径均由 S64 新目录解析，不复制任何旧 formal review、授权或 consumed execution。新目录里的 `freeze_c2_manifest.py` 名称及 `s47-c2-*` schema/status 是兼容行政标签；实际科学身份以新 row、retrieval_variant、output 与 manifest SHA 为准。原固定 sentinels、same-descriptor 来源/资源核验、watchdog、进程树清理、终态 commit 与外部真实 return 要求复用；不新增权限状态机或攻击矩阵。

准备前两名不同作者只审本次明确差异及最终文件 SHA。局部作者检查仅验证 fake 实例安装/返回/观察器顺序/实际调用票、规范variant元数据与来源闭合、原 factory/launcher 派生编译；不重复 S60–S63 场景计算，不加载模型或图片。具体 prepare/attach 参数合同见 FREEZE_PROTOCOL.md。作者最终所有责任文件为0444后交付；正式消费后的纠正另存，不覆盖旧证据。

真实完整退出和两批档案之后，才对这个新变体重新绑定原读回/相机/九帧评分方法及全部图像QA。外部return0、hook调用、unit票、原observer档案均不自动成为画质或方法收益。`NO_METHOD_SELECTED`、`new_method_validated=false`、`novelty_authorization=NONE`。
