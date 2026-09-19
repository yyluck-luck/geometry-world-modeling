# Round 17-I — static/dynamic decomposition review

## 核验边界

本轮没有运行 harness、GEN3C、GPU、训练、权重下载或包安装，也没有修改任何既有文件。当前项目 checkout 是 `9cfad745f3ba58fbb98983e9c829401d102059c0`；GEN3C 的 `gui/api` 和 `cosmos_predict1` 源码不在这个 checkout 中。因此，下面的 GEN3C 代码结论来自公开仓库 `nv-tlabs/GEN3C` 的固定提交 `db2ffe12ced12ddafcec5e0422ee46ce8520746b` 的逐行读取，而不是把项目 ledger 当作源码。该 SHA 也由 `git ls-remote` 核对为当前 `main`。

按项目规则尝试了 `gpt-6-astra` / `ultra` 外部复核；本地 Codex 客户端对 Responses API 返回 `401 Unauthorized`，所以没有把该失败当作证据，也没有用它替代源码核验。

VMem 旁证也核过：项目 checkout `9cfad745f3ba58fbb98983e9c829401d102059c0` 中三份 pipeline 文件的 SHA-256 都是 `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`；三份都在 `:1249` 调 `get_context_info(...)`，`:1263` 拼接 `context_c2ws` 与 `target_c2ws`，`:1265` 调 `get_translation_scaling_factor(all_c2ws)`。`self.c2ws` 的赋值/追加点确为 `:180` 与 `:1297`，没有 setter；若“写入”包括列表删除，则还必须报告 `:1360 self.c2ws.pop()`。这与本轮 GEN3C 裁决无关。

## Q1 — 分解是否 sound

裁定是：**在明确限定后，分解作为 source-level control-flow proof 是 sound；原句的“任意异常都留下 stale=True”过宽。**

在固定提交的 `gui/api/server_cosmos_base.py` 中，`CosmosBaseModel.seed_model` 在 `:46-47` 进入方法后先导入 `torch`；`:51-52` 的条件只控制日志，`:53-55` 无条件调用 `self.model.clear_cache()` 并清空两个 history；`:57-60` 取得 `seed_model_from_values`；`:62-70` 调用它；只有正常返回后才在 `:71` 写 `self.model_seeded = True`。这一段没有 `try/except/finally`、异常类型分支、回滚或状态恢复。因此，若对象此前已经成功 seed（外层 flag 已为 `True`），且一个普通 `Exception` 在清理完成后、`:71` 执行前从 seeding invocation（含参数求值）抛出，则 cache/history 的清理与旧的外层 `True` 会保留，与异常具体是 `NotImplementedError`、`ValueError` 还是其他 `Exception` 无关。GEN3C 的 `clear_cache` 本身在 `cosmos_predict1/diffusion/inference/gen3c_persistent.py:551-553` 把内层 `cache` 设为 `None`、`model_was_seeded` 设为 `False`，但它没有清外层 flag。

`gui/api/server.py:150-176` 的 `/seed-model` 在 `:165-168` await wrapper，并在 `:169-172` 对普通 `Exception` 统一记录后返回 HTTP 400；handler 没有清理或恢复。因此，异常类型不改变上述状态后果；错误文本当然可能随 `str(e)` 改变。`gui/api/server_base.py:59-60` 显示外层 flag 初始为 `False`，`:121-131` 的 admission 只在 `:122-123` 检查该 flag，之后检查 request id/请求合法性并在 `:128` 建立 Task；它不检查内层 cache。

需要保留四个边界：

1. 失败前若外层 flag 是 `False`，失败后仍是 `False`，没有 stale-`True`。所以必须是“成功 seed A → 失败 seed B”的序列。
2. `torch` 导入、`clear_cache`、history `.clear()` 或 `req.world_to_cameras()` 在 seeding invocation 之前失败时，不能套用“清理已发生”的结论；例如 `server_cosmos_base.py:47` 的 `ModuleNotFoundError` 会先退出。
3. `BaseException` 不属于 handler 的 `except Exception`；而在 `seed_model` 成功返回后、`server_cosmos_base.py:74-95` 的结果后处理中再抛异常，也不是同一个“`:62-70` 失败前未写 flag”的路径。
4. 直接构造 `CosmosBaseModel` 还不够：其构造器只有 `server_cosmos_base.py:37-38` 的 `super()`，不会建立 history 或真实 inner model；缺少这些成员的 `AttributeError` 是 harness 初始化失败，不是目标异常。

静态半边确实有对应的 released path：`gui/api/api_types.py:138-169` 允许 `SeedingRequest.depths` 为 `None`，并只在非 `None` 时做 depth shape 检查；`server.py:156-168` 接受该类型并调用 wrapper；`gen3c_persistent.py:206-210` 对 `n > 1` 且 `depths_np is None` 在 `:208` 抛出指定的 `NotImplementedError`。构造请求仍须满足其余 schema 和可逆相机要求，因为 `server_cosmos_base.py:66` 会先调用 `req.world_to_cameras()`，而 `api_types.py:71-75` 会求逆。

这里的“可达”应读作静态的 route-to-wrapper/branch 可达性，而不是每种部署配置都已确认。固定提交的 `gui/api/server.py:77-91` 在 debug 模式选择 `DebugInferenceModel`（`:78-80`），只有 `model_name` 为 `cosmos`/`cosmos-predict1` 才选择 `CosmosModel`（`:81-83`）。具体模型构造还在 `gui/api/server_cosmos.py:55-96`：`gpu_count==1` 才构造 `Gen3cPersistentModel`（`:92-93`），否则选择 `MultiGPUInferenceAR`（`:94-96`），`gpu_count==0` 还会先在 `:69-71` 查询 CUDA 设备数。因而未执行的静态结论不能替所有 debug/model/GPU 配置声称相同的具体 runtime 行为。

所以可辩护的命题是：**已成功 seed 的实例上，公开 schema 可表达的多帧无 depth 请求，若实际进入 released seeding call 并抛普通异常，wrapper 会留下外层 stale flag 并让 admission gate 放行。** 不可辩护的宽命题是：“任何异常、任何初始状态、任何运行环境都必然留下 stale=True。”

## Q2 — 审稿人会如何看

审稿人可以接受“released raise 的静态可达性 + wrapper 的异常无关控制流”作为一个**代码级生命周期缺陷/条件性反例**，因为这两个前提在 source 上可独立核查；end-to-end 运行不是这条窄逻辑蕴含的必要条件。

但审稿人不会把它等同于 **end-to-end released-trigger demonstration**。运行仍然承担证据职责：

- 证明当前使用的 checkout、导入路径、依赖和路由确实选择了这些 released 文件；
- 证明合法请求实际穿过序列化、参数求值、构造和 dispatch，没有在目标行之前被 guard、缺失成员或环境错误拦住；
- 证明所选的 concrete model configuration 确实是 `Gen3cPersistentModel`，而不是 `server_cosmos.py:92-96` 的另一分支；
- 观察真实异常类型、traceback 和 handler/gate 行为，而不是 harness 复制了同一异常文本；
- 给出可被另一人复现的运行证据，减少“代码看起来可能这样”的可信度风险。

因此，静态合取可以支持“released source contains a reachable conditional defect”，不能支持“released `:208` 已在本次运行被触发”、真实 inference 已因空 cache 失败、视频/图像质量受影响、发生率/普遍性或论文结果受影响。`request_inference` 在 `server_base.py:128` 只同步创建 Task；仅得到 Task/HTTP 202 仍是 admission，不是 downstream execution。真实 inner cache 的第一次相关使用还在 `gen3c_persistent.py:292-312` 的 `:308`，要声称该后果必须让 Task 实际运行并排除 missing-attribute、CUDA 和 harness sentinel。

## Q3 — Tier-A-only 记录、门和标签

先写一个不可省略的 preflight：虽然 `server_cosmos_base.py` 模块可以延迟导入 torch，但 released `seed_model` 的 `:47` 在方法入口执行 `import torch`。因此“clean venv 只有 numpy、loguru、opencv，且无 torch”只能证明 **module importability**，不能证明可以原样调用 released wrapper。没有现成 torch 时，不安装包；结果应为 `DESIGNED_NOT_EXECUTED_TIER_A`。若另行注入最小 `sys.modules['torch']` shim，只能把它标成 harness/dependency-shim witness，不能称 native runtime。preflight 还应记录 Python、OS、模块 `__file__`、固定 checkout/SHA、依赖版本，以及是否初始化 CUDA。

若 preflight 允许执行（或明确采用 shim），Tier-A 只记录 wrapper/gate，不触达 released `gen3c_persistent.py:208`：

| 阶段 | 必须记录 | 通过条件 |
|---|---|---|
| S0 | 外层 `model_seeded`、inner cache sentinel、两个 history 的长度/内容、clear 调用计数；直接 wrapper 实例显式建立 history 并挂上 lightweight model double | 初态和所有注入成员与协议一致；否则是 protocol invalid/infeasible |
| S1 positive control | 合法 `req_A` 的返回、异常、flag、cache/history；给出 non-`None` depths，避免成功后的 `:74-76` 走未提供的 depth fallback | seed 成功，flag 变 `True`，inner cache 有预设可见状态 |
| S2 failure arms | 先成功 S1，再分别用至少两种普通 `Exception`（例如不同类型）让 lightweight `seed_model_from_values` 抛出；记录精确 type/message/traceback、clear 次数、cache/history 和 outer flag | 每个 arm 都显示清理已发生、异常传播/route 400（若实际调用 route）、outer `True` 未被改写；traceback 必须明确这是 harness 注入，不得写成 released `:208` 观测 |
| S3 stale admission | 使用新 request id、满足 frame bounds 的合法 `req_C`，在运行 event loop 中调用 `request_inference`；记录是否创建 Task、`inference_tasks`/`request_history` 的前后变化，立即 cancel+await pending Task | flag 为 `True` 且 cache 为 `None` 时 admission 通过；只报告“accepted/admitted”，不让缺属性或 CUDA 失败冒充 downstream consequence |
| S4 non-vacuity / failure-first | 新实例保持初始 flag `False`，用同样合法的失败 req 触发异常，再提交新 id 的 `req_C` | 必须在 `server_base.py:122-123` 抛 `ValueError`，且在建 Task、写 `inference_tasks` 或 `request_history` 前拒绝。可加手动 flag=False 的 secondary control 和 success/cache-present positive control |

S2 至少用两种异常类型的意义是验证 wrapper 的异常无关性；它不能把异常来源伪装成 released implementation。若 S4 也放行，说明 gate 可能是恒放行或 control 无效，结果是 **VACUOUS/INCONCLUSIVE**；若 S3 不放行，则动态 wrapper 命题被 refuted（若请求/初始化不合法则是 protocol invalid）。任何 `torch` 缺失、import/path shadowing、schema/camera、event-loop、missing attribute 或 CUDA 错误阻止目标路径时，均是 **INFEASIBLE/INCONCLUSIVE**，不是对科学命题的 refutation。

允许的结果标签：

- 仅 source 审计：`STATIC_RELEASED_REACHABILITY_PLUS_EXCEPTION_AGNOSTIC_WRAPPER_CONTROL_FLOW`；
- 真实执行 lightweight wrapper/gate（异常由 harness 注入）：`MEASURED_TIER_A_SERVER_ADMISSION`；若用了 torch shim，应改为 `MEASURED_WRAPPER_SEMANTICS_UNDER_DEPENDENCY_SHIM`。

禁止使用的标签：`MEASURED_RELEASED_TRIGGER`、`END_TO_END_RELEASED_FAILURE`、`released :208 observed`、真实 inference/runtime consequence、视频/图像质量、prevalence、published-result impact 或新方法验证。若本轮坚持 clean venv 无 torch 且不使用 shim，正确记录就是 **E1 designed but not executed**，静态证据单独保留。

## Q4 — 是否值得 Tier B build

**不值得为 E1 现在安装 torch + MoGe + cosmos_predict1 依赖链。** Tier B 的主要增量是把 S2 的异常归属从 harness 注入提升为 released `Gen3cPersistentModel.seed_model_from_values` 在 `gen3c_persistent.py:208` 的实际调用；它仍不自动提供空 cache 的 downstream runtime 证据，更不提供生成质量或冻结权重影响。此前已判断 E1 的价值有限，在这个成本/证据增量比下不应为一个较窄的审稿人争议建立重依赖环境。

因此本轮的诚实裁决是：**E1 designed but not executed**（若没有既有 torch 且不允许 shim），并保留以下静态结论：公开 schema/route 可表达该失败形状；wrapper/handler 对普通 seeding-call `Exception` 没有按类型恢复，成功 seed 后失败可留下 stale outer flag 并通过 admission gate。只有当未来必须回答“released `:208` 是否在真实依赖环境被触发”这一更强问题、且得到单独资源与执行授权时，Tier B 才有针对性价值；它不能替代 end-to-end consequence 证据。
