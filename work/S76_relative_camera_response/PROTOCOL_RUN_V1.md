# S76可执行单臂协议V1（源文件待独立复审，尚未运行）

本文件接续PROTOCOL_DRAFT.md，保留旧草案与pilot_rules.py原件。唯一问题、+5度旋转符号、实际图像网格随机流、预定H、全部四目标和同匹配评分均不变。本版补齐具体单臂runner、保存后scorer与外部观察器，不搭新框架。

## 精确运行路线

`RUN_CONTRACT.json`冻结S70 root接受链、独立生成核验、旧worker回执、原worker/source manifest、S69原utils/pipeline代码、pilot_rules.py和资源/评分规则。实际运行首先核这些元数据SHA，再加载S70已有的geometry条件NPZ；不会读取pose14条件、真实目标照片或深度。

`run_single_yaw.py`从已核字节加载S70 worker为普通模块，只使用其load_code/read_conditions/load_models/model_snapshot/RNG/array helpers，不调用原三臂run。不改S70源文件/结果。保留原CPU8/FP32/相同版本/50步/MultiviewCFG/full8 decode与原uint8量化路径。

原get_cond重新构造所有c/uc与相机下游。运行时逐项要求history camera、所有中心、K/mask、crossattn/replace、history rays字节不变，target rays确实变化。预定old/new相机、H和两个方向共同FOV mask在加载视频模型/生成前写入 `prescribed_geometry.npz`、`new_conditions.npz` 和 `PRE_GENERATION_GEOMETRY.json`。

恢复旧common_rng.json实际状态，逐步检查原noise body、entry、50次before/after、terminal状态；模型旧value/modes与新值相等，新进程前后identity/value/modes一致。所有传入的c/uc与c2ws/K/masks均为新get_cond的实际返回值。一次完整新臂保存all8 latent、4目标raw FP32及原uint8。停止或失败保留已经生成的数组和逐步进度，不自动重跑新臂或A0。

## 外部观察器及预算

`observe_single_yaw.py`只接受root实际完成独立审查后写的 `ROOT_RUN_BINDING.json` SHA。binding字段：

- `status`: `ACCEPTED_S76_SOURCE_SET`
- `reviewed_files_sha256`: 经过实际独立审查的文件绝对路径到SHA映射，至少包含三新源码、RUN_CONTRACT、pilot_rules和本协议；root可加入复核文件。
- `argv`: `[项目/.venv-cut3r/bin/python, -B, 本阶段/run_single_yaw.py, RUN_CONTRACT_SHA]`，保留venv词法路径，不能resolve成基础解释器。

冻结worker3540秒，外部3600秒总墙钟，采样进程树RSS45GiB，磁盘空闲10GiB。观察器每0.5秒采样，不称瞬时硬内存保证；任何外部错误/中止尽力杀进程组并回收进程，保存返回/原因和主账。采用S70同类观察方式，仅保留一臂和一小时总限制，未误用S75的180秒预算。实际单臂可能约S70已有25分钟量级，但本轮耗时未知，这只是历史成本参考。

启动命令由root在源审接受后执行：

```
.venv-cut3r/bin/python -B work/S76_relative_camera_response/observe_single_yaw.py ROOT_RUN_BINDING_SHA
```

## 保存后固定评分

实际生成返回且完整stream/model检查通过后，root读取并固定新worker/external回执SHA，然后单次执行scorer（外部60秒，scorer内部55秒）：

```
.venv-cut3r/bin/python -B work/S76_relative_camera_response/score_single_yaw.py RUN_CONTRACT_SHA GENERATION_RECEIPT_SHA EXTERNAL_RECEIPT_SHA
```

scorer检查外部return0、无停止原因、worker完整及可比；读取旧A0/new yaw的原uint8数组和生成前的H/FOV。逐数组核file/body SHA和shape/dtype，重算H/FOV须与生成前存量完全一致。固定SIFT参数、ratio<.75双向互惠匹配，无RANSAC、拟合、对齐或角度选择。

对同一接受匹配算identity/H残差与paired identity-H。all-valid主报告和common-FOV次级条件报告均保存原坐标、逐点残差、q25/50/75/95/max、符号计数、全部invalid/outside/缺失计数、源图feature总体与common-source分母/覆盖。每个目标有完整JSON和两张原quantized PNG，禁止丢弃不足匹配的目标。分别形成all4中位方向事件；任一目标median未定义，事件为None，不能过滤后all()。

这是一场景一次随机实现的方向诊断。生成SIFT对应不是点真值，共同FOV不是无遮挡保证。同图像网格噪声不是几何附着噪声，没有精确H-equivariance定理；方向结果不能当绝对camera正确、isolated-ray因果、真实场景重建或方法创新。新生成图片已经封存后才读回评分，旧A0和本场景此前已见，不叫未见测试。

## 本次作者实际检查与剩余事项

仅编译三新程序、核原AST方法/函数闭包名称及旧元数据/源码SHA；0新模型、0科学数组正文、0实际RNG正文。未执行inert模型导入或数值模拟，不能把compile PASS说成运行验证。`execution_01`、`scoring_01`均不存在。

实现已提供。剩余是不同作者审查精确最终源码/合同，root接受并启动实际单臂；返回后团队内不同作者独立复算保存相机/H/FOV、点坐标与统计、查看全部4目标。旧draft架构审不是本版新代码的执行票。若实际状态或输出不支持复用旧A0，原失败保留，再按新协议决定是否有必要另做fresh pair，不立即重跑。
