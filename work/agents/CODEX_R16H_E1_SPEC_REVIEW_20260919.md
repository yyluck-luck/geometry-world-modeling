# Round 16-H — E1 sealed-spec adversarial review

## 审查边界与结论

我核对了项目提交 `c97f4f2a81c770e4423c29d220ae1fe8180da4ed` 中的
`work/S120_lifecycle_audit/E1_SPEC_PREDECLARED_20260919.md`。该文件的 SHA-256 是
`080ffc5bcf1f160e34d7fdd4451a332aa3372d7a7e4b62cf3cae3a1e5815f5e7`，与 sealed spec 声明一致。
GEN3C 源码使用只读 checkout `nv-tlabs/GEN3C@db2ffe12ced12ddafcec5e0422ee46ce8520746b`；该 SHA 同时是
本地 checkout 的 HEAD 和 `origin/main`。

**裁定：当前 sealed spec 不应执行。** Q1 的“这是 harness 自己制造的失败”异议成立；Q2 的 P3 只有同步准入证据，没有实际推理后果证据；而且按 spec 未声明的状态初始化，S1 还可能在 stub 被调用前因缺少历史列表而失败。必须保留当前 spec 不变，另写一个新 spec 并重新 seal。下面的 replacement text 只供新 spec 使用，不能回写 sealed 文件。

本审查没有运行 harness、GEN3C server、GPU、训练、微调或权重下载，也没有修改任何已有文件。

## Q1 — 失败是否来自 released code

异议成立。sealed spec 明确规定 stub 的 `seed_model_from_values` “call 1 succeeds; call 2 raises a controlled exception”（`E1_SPEC_PREDECLARED_20260919.md:42-49`），S2 也明确写成“stub raises on call 2”（`:59-63`）。因此即使 P2 成立，它直接证明的是：released `CosmosBaseModel.seed_model` 在一个由 harness 注入的任意异常上如何处理，而不是 GEN3C 的 released seeding implementation 是否会产生该异常。它不能把 spec 中列出的 `gen3c_persistent.py:208` 变成实际触发源。

released wrapper 的控制流本身核对无误：`CosmosBaseModel.seed_model` 在
`gui/api/server_cosmos_base.py:46-55` 先清 `self.model.clear_cache()` 和两个历史列表，在
`:57-70` 调用 `seed_model_from_values`，只有返回后才在 `:71` 写 `self.model_seeded = True`。
公共 flag 在 `gui/api/server_base.py:59-60` 初始化为 `False`，准入读取在 `:121-131`。
真正的 released multi-frame validation 在
`cosmos_predict1/diffusion/inference/gen3c_persistent.py:137-156,206-210`：当 `n > 1` 且
`depths_np is None` 时，`:208` 抛出精确的
`NotImplementedError("Seeding from multiple frames requires providing depth values.")`。

这个 failure route 可以在零权重、零模型构造的条件下接通，但必须把它写进新 spec：导入
released `Gen3cPersistentModel` 后，用 `Gen3cPersistentModel.__new__` 得到不执行
`:79-131` 重模型构造的 probe；call 2 将 kwargs 原样传给 released
`Gen3cPersistentModel.seed_model_from_values`，不得由 proxy 自己 `raise`。req_B 必须是合法的
多帧 `SeedingRequest`，`n > 1`、`depths=None`，相机矩阵可逆，使执行能到达 released `:208`。
必须记录异常类型、精确消息和 traceback 中的 released path/line。若导入该模块、绑定该方法或
导入其 `torchvision` 依赖失败，结果是 **E1 INFEASIBLE**，不能退回到复制同一异常文本的 stub。

为了减少第二个“cache 也是 stub”的异议，新 spec 还应让 probe 的 `clear_cache` 绑定
released `Gen3cPersistentModel.clear_cache`（`:551-553`），而不是只实现同名的 harness 清理函数。
S1 的成功仍可用轻量 adapter 返回 `None`，但报告必须说清：成功 seed 的数据处理不是 released
model success；released attribution 只覆盖清理路径和 call-2 validation path。公共配置不能注入
该 probe：`gui/api/server.py:77-91` 只按固定 model name 建实例，`gui/api/server_cosmos.py:55-96`
随后构造真实 `Gen3cPersistentModel` 或 `MultiGPUInferenceAR`。

## Q2 — P3 是否足够

P3 按当前定义只测 admission。`InferenceModel.request_inference` 在
`gui/api/server_base.py:121-131` 检查 flag、request id 和 frame bounds，然后在 `:128`
调用 `asyncio.create_task(self.run_inference(req))` 并返回 Task。创建 Task 不会同步执行 coroutine
主体；如果 harness 在同一个 event loop 中不让出控制权，`run_inference` 甚至尚未开始。

所以 P3 可以支持一个很窄的结论：**outer API gate 在 stale flag 为 True 时接受并排队 request**。
它不能支持“真正的 invalid-cache inference consequence”。真实错误可能稍后才发生。released
wrapper 的 `run_inference` 在 `gui/api/server_cosmos_base.py:98-146` 先读 `model.W/H`、历史列表
和 `model.inference_overlap_frames`，再调用 `model.inference_on_cameras`；`torch.cuda.Event`
在同文件 `:156-162` 才被创建。若使用真实 inner implementation，
`Gen3cPersistentModel.inference_on_cameras` 在
`cosmos_predict1/diffusion/inference/gen3c_persistent.py:271-312` 的 `:308` 解引用
`self.cache.render_cache(...)`，`cache=None` 才会在此形成 released cache failure。然而，当前四成员
stub 没有 `W`、`H` 或 `inference_overlap_frames`，任务会先因 harness 缺属性失败；如果 stub 返回
正常 tuple，任务还会走到无 GPU 的 `torch.cuda.Event()`，该错误也与 claim 无关。

若要声称 downstream consequence，新 spec 至少必须让 event loop 运行 Task、等待 Task 完成并
读取 `task.exception()`，或通过 `inference_result_or_none`（`server_base.py:141-168`）观察异常。
优先要求异常来自 released `cache.render_cache` path；缺属性、CUDA、导入或 sentinel 以外的环境错误
均标为 INCONCLUSIVE/INFEASIBLE，不能算 CONFIRMED。若不愿接通这条 zero-GPU 的 downstream route，
则把 P3 的名称和许可证收窄为 `MEASURED_SERVER_ADMISSION`，明确不声称 generation/runtime
consequence，并主动 cancel+await pending Task 以免出现 pending-task 噪音。

另一个可见边界是 HTTP 路由：`gui/api/server.py:123-147` 只捕获同步 admission 异常并返回
202；后台 Task 的异常不会在该处变成同步拒绝，后续结果读取才在
`server_base.py:141-155` 重新抛出。因此“返回 Task”与“用户收到成功视频”不能混写。

## Q3 — P4 是否是足够的 control

P4 不是无效 control，但它很弱。将同一实例的 `model_seeded` 手动设为 `False` 后，
`request_inference` 在 `server_base.py:122-123` 抛异常，只证明该 `if` 分支仍在工作，不能证明
flag 的语义确实是“inner 3D cache 可用”。它不排除 gate 从未检查 cache，也不检验失败 seed 在
初始 flag 为 False 时不会把 flag 错写成 True。

更强的 primary control 是 failure-first：fresh instance 初始 flag 为 False；用同一个合法的
released invalid req_B 触发 `:208`；确认异常返回后 flag 仍为 False；随后以新的 request id 调用
同样合法的 req_C，必须在建 Task、改 `inference_tasks` 或改 `request_history` 之前于
`server_base.py:122-123` 抛 `ValueError`。现有 S4 可保留为 secondary control。再加一个
successful-seed/cache-present positive control，能区分“成功状态可准入”和“失败后 stale flag
可准入”。最好记录这个 2×2 最小表：

| outer `model_seeded` | inner cache | 预期 admission |
|---|---|---|
| False | None | raise before Task |
| True | None | stale case: Task only, or released downstream failure if P3b is enabled |
| False | sentinel/nonempty | raise before Task |
| True | sentinel/nonempty | admit |

这张表验证 gate 依赖 outer flag，而不是偷偷读取 inner cache；它仍不会单独证明 generation
quality 或 published result 受影响。

## Q4 — 未声明、可能使 run 无效的 assumptions

1. **CosmosBaseModel 的历史列表没有在其构造器中创建。** `server_cosmos_base.py:32-38`
   的 `CosmosBaseModel.__init__` 只调用 `super()`；它不建立 `self.model`、
   `pose_history_w2c`、`intrinsics_history`、`aabb_min` 或 `aabb_max`。但 `seed_model` 在同文件
   `:51` 和 `:54-55` 立即读/清两个历史列表。若 harness 只按 sealed S0 “instantiate and attach
   stub” 执行，S1 会在 stub 前 `AttributeError`。新 spec 必须显式设两个空列表；这不是 released
   source edit。

2. **四成员 stub 不足以支持 S1 的所有合法请求。** `seed_model` 在
   `server_cosmos_base.py:74-76` 中，当 `req.depths is None` 时调用
   `self.model.get_cache_input_depths().cpu().numpy()`。因此 req_A 必须明确提供 non-None depths，
   且 S1 adapter 最安全地返回 `None`；否则 stub 还需声明第 5 个成员。若返回四元组，则
   `:78-95` 还会逐项做 Tensor/shape 处理。

3. **请求 dataclass 不是任意 NumPy 容器。** `api_types.py:53-69` 检查 resolutions 与精确
   batch shapes；`RequestBase.__len__` 在 `:101-102` 返回 `cameras_to_world.shape[0]`。
   `SeedingRequest` 还在 `:162-169` 检查 images/depths/masks。`world_to_cameras()` 在
   `api_types.py:71-75` 调 `np.linalg.inv`；所以 3×4 c2w 必须组成可逆的 4×4 齐次矩阵，
   不能照搬 all-zero camera。`SeedingRequest.depths` 在 `:153-160` 没有默认值，构造时必须
   显式传 `None` 或合法数组。`InferenceRequest` 的 timestamps shape 检查在 `:297-326`。

4. **len 与 frame bounds 必须事前固定。** `check_valid_request` 在
   `server_base.py:193-199` 用 `len(req)` 做 inclusive range 检查；CosmosBaseModel 的
   `min_frames_per_request` 与 `max_frames_per_request` 在 `server_cosmos_base.py:226-234`
   都返回 `self.model.frames_per_batch`。因此 stub 的 frames_per_batch 必须是正整数，req_C 的
   frame 数必须完全等于它；每个 request id 也必须唯一，因为 gate 在 `server_base.py:124-125`
   拒绝重复 id。

5. **异步语义必须声明。** `request_inference` 要求当前有 running event loop；同步调用会在
   `asyncio.create_task` 处失败。S1/S2 使用 `await` 不能替代 S3 对 Task 的 drain/cancel 规则。
   若让 Task 运行，`run_inference` 在 `server_cosmos_base.py:134-135` 先追加 pose/intrinsics
   history，即使 inner call 失败也可能留下新状态，必须记录任务前后历史。

6. **downstream probe 需要额外成员和返回合同。** `run_inference` 的 `:106-146` 需要
   model.W、model.H、inference_overlap_frames、inference_on_cameras，以及五项 tuple 或
   指定 dict 形状；sealed “exactly four members”不能同时满足这些需求。若只测 admission，
   不应暗示 inference_on_cameras 已被触达。

7. **`torch.cuda.Event` 使“让 Task 完成”不是纯 CPU 默认路径。** `run_inference` 在
   `server_cosmos_base.py:156-162` 无条件创建 CUDA event。不能把 no-driver/CUDA exception
   当 stale-cache evidence。要么让 released inner method 在其 `cache.render_cache`（
   `gen3c_persistent.py:308`）先失败，要么明确把 P3 限制为 admission-only；不能用未声明的
   CUDA monkeypatch 把结果写成 released execution。

8. **import-time 依赖被低估。** `server_base.py:16-24` 本身导入 asyncio/loguru/numpy 和
   api_types；`api_types.py:16-28` 导入 encoding，并在 `:21-23` 设置
   `OPENCV_IO_ENABLE_OPENEXR`；`encoding.py:16-22` 导入 cv2/numpy。`server_cosmos_base.py`
   的 torch 是方法内 import（`:46-47`、`:98-100`），所以轻量 wrapper 仍要求 torch package。
   要走 released raise，`gen3c_persistent.py:1-19` 在模块级导入 MoGe、torch、Gen3cPipeline、
   torchvision/Cosmos utilities、Cache3D 与 `torch.nn.functional` 的依赖链；其
   `seed_model_from_values` 又在 `:146` import `torchvision.transforms.functional`。相关传递依赖
   还包括 `warp`/Megatron/einops 等。静态源码没有显示这些 import 必然分配 GPU，但缺包或模块
   级副作用足以在到达 `:208` 前失败。该失败应标作环境 infeasible，不能换成 stub 结果。

9. **真实 constructor 不属于 zero-GPU harness。** `Gen3cPersistentModel.__init__` 在
   `gen3c_persistent.py:79-131` 使用 torch、构造 Gen3cPipeline 和 MoGe；`server_cosmos.py:55-96`
   导入并构造它，且 `:69-72` 在 gpu_count=0 时查询 CUDA device count。新 spec 必须声明不调用
   真实 constructor；否则“zero GPU”不成立。

10. **import path/shadowing 是可审计前提。** released server files 使用非 package-relative
    imports（`server_base.py:23`、`server_cosmos_base.py:27-29`），官方 GUI README 要求在
    `GEN3C/gui` 安装/运行（`gui/README.md:12-21,33-42`）。harness 必须声明精确的
    `sys.path`/cwd，并断言 `api_types.__file__`、`server_base.__file__`、
    `server_cosmos_base.__file__` 都指向该 checkout；否则同名 harness module 可能被导入。

11. **OS/Python/dependency contract 也不能省略。** released `INSTALL.md:1-4` 写明 Cosmos
    只支持 Linux、测试 Ubuntu、要求 Python 3.10.x；`gui/requirements.txt:1-14` 包含 FastAPI、
    imageio、loguru、numpy、OpenCV、pyexr、scipy 等。macOS 或不同 Python 的导入失败不能算
    科学 refutation。应在 import-only preflight 记录 Python、OS、module paths、依赖版本、
    torch CUDA availability 和是否发生 CUDA initialization；该 preflight 仍不是 harness result。

## Q5 — 应否 amendment，以及 replacement text

**应 amendment，但不能改 sealed 文件。** 以下文本适合写入新文件，例如 E1-v2，再在任何执行前
重新计算 hash 并 seal。

### Replacement A — released failure trigger

```text
Trigger attribution (mandatory). The call-2 failure arm MUST call
Gen3cPersistentModel.seed_model_from_values from
nv-tlabs/GEN3C@db2ffe12ced12ddafcec5e0422ee46ce8520746b/
cosmos_predict1/diffusion/inference/gen3c_persistent.py, using a lightweight
constructor-bypassed probe (`__new__`) with a valid n>1 request and
`depths_np=None`. The proxy MUST NOT raise its own exception on this arm.
The released method MUST raise
NotImplementedError("Seeding from multiple frames requires providing depth values.")
from line 208; the captured traceback must contain the released path. Bind the
probe's `clear_cache` to the released `clear_cache` implementation at lines
551-553 where feasible. If importing/binding this released path requires a
checkpoint, GPU, or unavailable dependency, classify E1 as INFEASIBLE; do not
substitute a copied harness exception.
```

### Replacement B — P3 split admission from execution

```text
P3a (admission): request_inference(req_C) returns an asyncio.Task without a
synchronous exception, with the same valid request and cache=None.

P3b (downstream, required for any invalid-cache consequence claim): yield to the
running event loop, await the Task to completion, and record task.exception()
(or the exception surfaced by inference_result_or_none). The probe MUST expose
all attributes needed to enter released CosmosBaseModel.run_inference. A
CONFIRMED downstream result requires the task to enter the released inner
inference path and fail at the released cache dereference, or another separately
justified released failure. Missing attributes, import errors, CUDA errors, and
harness sentinels are INCONCLUSIVE, not CONFIRMED. If P3b is omitted, the result
label is MEASURED_SERVER_ADMISSION only and no inference/runtime consequence may
be claimed. Any pending Task is explicitly cancelled and awaited before teardown.
```

### Replacement C — stronger control

```text
Primary clean control (failure-first): on a fresh harness whose outer
`model_seeded` is initially False, submit the same valid released invalid seed
(req_B, n>1, depths=None). Require the released NotImplementedError, require
`model_seeded` to remain False, then submit a fresh valid req_C and require a
ValueError at the outer admission check before any Task, inference_tasks entry,
or request_history mutation. The current manual flag-clear-after-S2 control is
secondary only. Also record a successful-seed/cache-present positive control.
```

### Replacement D — explicit harness contract and preflight

```text
Before S0, initialize `pose_history_w2c=[]` and `intrinsics_history=[]` on the
direct CosmosBaseModel instance. For any downstream Task probe, expose
`frames_per_batch`, `W`, `H`, `inference_overlap_frames`, `clear_cache`,
`seed_model_from_values`, and `inference_on_cameras`, and declare the exact
return shape. req_A uses non-None depths (or the probe implements
`get_cache_input_depths`); req_B has n>1 and depths=None. Use invertible identity-like
cameras, exact dataclass shapes, unique request ids, and a frame count equal to
`frames_per_batch`. Before execution, perform import-only provenance checks,
assert all imported module paths resolve inside the pinned checkout, record
Python/OS/dependency versions and torch/CUDA import side effects, and never call
Gen3cPersistentModel.__init__.
```

### Replacement E — revised pass language

```text
A CONFIRMED MEASURED_SERVER_ADMISSION result requires P1, P2 with the released
exception path, P3a, and the failure-first control. A CONFIRMED
MEASURED_SERVER_CONTRACT_CONSEQUENCE additionally requires P3b and a released
inner-path failure; otherwise the result is admission-only. Any preflight,
import, missing-state, request-construction, event-loop, or CUDA failure that
prevents the declared path is INFEASIBLE/INCONCLUSIVE, never REFUTED.
```

## Q6 — 是否值得运行

**当前 sealed 版本不值得运行。** 即使它“成功”，主要观测也会是 harness 自己决定在 call 2
抛异常后 outer flag 没有被清掉；如果 S3 只返回 Task，结果还不能说明实际 inference 是否因空
cache 失败。缺历史列表、req 构造和 import path 等未声明前提又会制造与 claim 无关的失败。这个
结果不足以回答 frozen-weight consequence，也不足以说明画质、网络行为、published results、
prevalence 或 novelty。

**另立并重新 seal 后，修正版有有限价值。** 它可以作为低成本的 server/API lifecycle witness：
把静态可达性变成 released validation branch 的可复现执行证据，并清楚区分 admission-only 和
actual downstream failure。若资源只能在“修正版 E1”和“冻结权重下的实际 consequence”之间二选一，
应先做后者；修正版 E1 只能补 API 合同审计证据，不能替代生成质量或冻结权重结论。

## Requested VMem side check

用户同时要求核对的 VMem 事实也成立：三份 `pipeline.py` 的 SHA-256 都是
`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`；三份文件在
`:1249` 调 `get_context_info(target_c2ws, use_non_maximum_suppression)`，在 `:1263` 做
`torch.cat([context_c2ws, target_c2ws])`，在 `:1265` 调
`get_translation_scaling_factor(all_c2ws)`。以
`work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py` 为例，`self.c2ws`
的赋值点是 `:180` 和 `:1297`，读取/列表 mutation 另有 `:1360 self.c2ws.pop()`；没有找到
setter。该旁证与本 E1 GEN3C review 无关，不改变 sealed E1 的结论。

## Provenance note

本文件的 GEN3C 行号来自上述 commit 的只读 checkout；项目 spec 行号来自 sealed commit。并行的
独立源码审查也复核了相同路径。按项目强制 external Astra 命令尝试过本轮最高配置，但本地
Codex client 返回 HTTP 401/未提供 bearer token；该服务错误不是科学实验结果，也没有用它替代
源码核验。
