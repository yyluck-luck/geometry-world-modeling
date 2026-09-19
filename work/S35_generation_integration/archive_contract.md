# S35 原生成产物完整归档模块合同

状态：源码实现与标准库编译准备；未读取真实图片、GT、权重或 NPZ，未执行科学库、假模型或人工数组检查。真实 loop 接线由另一作者负责，原 S20 `TraceWriter` 和所有既有文件不改。本文件不是运行许可、模型可用性证明或两批生成成功声明。

## 1. 解决的具体缺项

已全文核对 `docs/S20_GENERATION_TRACE_CONTRACT.md`、`docs/S20_MINIMAL_VIDEO_PROTOCOL_DRAFT.md` 的完整档案要求，以及 `docs/S20_TRACE_INTERFACE_REVIEW.md`。原 S20 trace 保存 noise/RNG/Surfel 原字节，但 c/uc、samples/samples_z、latent/embedding 等通常只有 fingerprint，PIL 像素、dense depth/focal 值亦未完整归档。新模块为 **调用者实际传入的原对象** 保存完整载荷；它不执行 VMem、不读任意 pipeline 属性、不填充缺失对象、不再调用编码器或渲染器。

实际输入来源应覆盖原两批 T8/50 步、历史 1→5→9；不得引入 S34 八帧档案或假缓存作为生成闭环。首批三 padding 槽也必须保存在完整 samples/samples_z 中，只是没有 history ID。最终九帧采用 `pipeline.pil_frames`，不用可能重复初图的 `Navigator.frames` 代替。

## 2. 精确 API

```python
archive = FullOutputArchive(
    fresh_directory,
    evidence_kind="recorded_execution",  # 人工接口验证只能写 synthetic_test
    source_identities=frozen_source_sha256,
    manifest_sha256=frozen_run_manifest_sha256,
    required_events=required_name_minimum_counts,
)
reference = archive.capture("sample_output", {
    "operation_index": operation_index,
    "batch_id": actual_batch_id,
    "samples": samples,
    "samples_z": samples_z,
})
# 原函数仍返回原 samples/samples_z 对象；reference 仅供写事件索引。
receipt = archive.finalize(status="COMPLETE", metadata=plain_json_metadata)
# 异常由外层保留原异常并重新抛出：
archive.fail(error, phase="original_sample_or_archive")
```

`capture(name, payload)` 同步保存，原地修改函数之前/之后分别调用才对应各自状态。相同 name 可重复，每次有独立 seq、occurrence 和 begin/complete 关联，不覆盖此前事件。`required_events` 可为名称序列（至少一次）或名称→最少次数的字典；它只验证调用者指定的原始对象事件已归档，不认证名字背后的模型、两批流程、实际维度/行数、闭环或质量。未指定名称时不虚构覆盖要求。

`finalize(status="COMPLETE")` 只返回 `ARCHIVE_COMPLETE`，并显式 `scientific_status="NOT_EVALUATED"`。有 capture 失败或缺必需名称不能这样关闭。`PARTIAL` 可保留不完整前缀；`fail` 尽力落失败阶段、异常和已写文件身份，返回后外层仍须重新抛出原异常并保留外 caller 回执。正常关闭 trace/归档均不等于 `SUCCESS_BASELINE_TECHNICAL`。

真实模式必须有单独冻结运行 manifest SHA，并在 source_identities 中绑定本模块绝对路径/SHA 与 `src/s20_generation_trace.py` 的固定 SHA。模块在创建和关闭时主动核这两个小源码，并记录前后相同身份；其余 source/大权重身份由外 caller 核并传入，不为归档反复读取 GB 权重。没有替用户建立新审批流程。

## 3. 显式 payload 域与接线分工

integrator 已约定提供 `operation_index`（0初始化，1左转，2右转）和实际 batch_id，并只提取现有值。基础事件名为：

| 名称 | 应传入的实际原值，不能靠名称代替内容 |
|---|---|
| initial_input / initial_output | 预处理 normalized tensor、已加载 PIL、初 camera/K；原 VAE latent、原 CLIP embedding 与 ID0 cache |
| context_output | 实际有序 ID（保留重复）、从历史取出的各类 cache、cast 后 context 张量、target camera/K、原 padding/slot 对应 |
| condition_input / condition_output | `get_cond` 原地转换之前输入与原返回全部条件，含实际 c/uc/相机/K/mask；同步前后保存 |
| sampler_input / sampler_output（或同义明确域） | 原 sampler 实际接收的初始 noise、cond/uc、c2w/K/mask/scale、其实际返回；实际调用前后 RNG 状态 |
| sample_output | 原 `do_sample` 返回的全部八槽 samples 和 samples_z，包括首批 padding，不切成只留四张 |
| cache_commit | 全部实际 CLIP 目标行（首批7、第二批4）与历史逐ID latent/embedding/c2w/K/PIL；长度1→5→9由调用者/trace核 |
| geometry_output | 原 `run_inference_from_pil` 真实返回的完整 dict，包括实际 dense 字段；不重跑模型/GA补抓 |
| map_commit | 显式完整有序 Surfel position/normal/radius/color/source_ids，color=None也留；全部 surfel_Ks、surfel_depths 与历史 cache |
| render_output / retrieval_output | 原渲染的depth/index/cosine、实际query相机/K、原候选/票权/配额/NMS返回及实测阈值状态；不伪造 defaults |
| navigator_begin / navigator_return / integration_failure | 只记录真实阶段、原返回与失败信息，不把预期计数填为实际 |

特别提醒：仅保存 `get_cond` 输出不等于保存 `do_sample` 内部 cast/padding 后 sampler 真正输入。原 S20 的 sampler c/uc fingerprint 也不能替代这一完整原值事件。需要 integrator 在原 callable 委托点加被动归档；缺项时保留为接线未完成，不能由本模块重新构造条件。

RNG由 integrator 显式传入原阶段只读 `random.getstate()`、`np.random.get_state()`、`torch.get_rng_state()` 结果；本模块不自行调用 getter、不设seed、不消耗随机数。CPU协议不虚写CUDA/MPS状态。仅初始noise不是全部随机性，不重采样每步noise，也不为此保存50步全部激活。

地图 cache 按原实现保留 `surfel_Ks` 0→5→14 和 dense depth 5/9，不更改为9项K。dense旧depth版本与旧Surfel坐标是不同对象；来源关联日志不是因果证据。第二批是否实际消费第一批生成缓存由原trace/索引复核判定，本归档不代判。

## 4. 原字节、类型和文件格式

`archive_outputs.py` 模块导入只有标准库。首次真实 tensor 归档时加载固定 S20 `_tensor_bytes`，复用其已经检查过的 little-endian/C-order 编码，不重写 codec 或重复旧人工/codec 测试。Torch沿原 helper 做 detach/CPU/contiguous/resolve_conj/resolve_neg 后获取原位字节；不赋回、不修改原 device/dtype/梯度模式/返回对象。非连续值按逻辑C顺序保存，保留 FP16/BF16 位模式，不把 BF16 升 FP32。NumPy 数值数组和 scalar 都保留 dtype；拒绝 object/string数组及非dense/量化Tensor。

每个 tensor 保存完整 `tensors/<identity>.bin` 和 `.json` sidecar。descriptor 包含 dtype、shape、byteorder、order、nbytes、原字节SHA与包含元数据的 canonical identity，和原 S20 tensor identity 兼容。sidecar先写，若后续磁盘故障仍尽可能留下待写数组形状/身份；只有完整blob完成才在 capture_complete 中引用。相同内容可引用已经核到的完整blob，不能只留下不存在的 fingerprint。

树保留 dict 的字符串/整数键、原插入顺序，list/tuple类别、None、bool/int/string；Python float 用 little-endian 64位hex，保留 -0、非有限值和NaN位，不产非法JSON。支持 bytes、torch.device/dtype元数据；循环容器/任意对象/隐式文件路径读取拒绝，调用者必须显式提取值。所有 tensor，包括非有限数组，先如实归档；科学有效性由原执行门另判，不裁剪修补坏值。

已加载的 PIL L/RGB/RGBA 对象可直接传入：复制对象后保存原像素tensor和无损PNG，不resize/调色/改mode；有尚未关闭fp的懒加载图像拒绝，避免归档触发额外文件加载。PNG是图像容器序列化，不是VAE/CLIP重新encode；其像素身份不宣称等于原JPEG文件容器。也可由integrator对原已加载PIL显式取uint8数组传入，但规范九帧PNG另须按原对象保存，不可重新生成。

`events.jsonl` 包含UTC/seq/previous SHA/事件SHA，capture_begin、完整树或capture_failed区分。`manifest.json` 包含完整tensor descriptor、每份物理文件大小/SHA、事件尾身份、名称次数和source身份；manifest不自引用，其SHA由返回值/外caller绑定。每次同步事件与payload均flush/fsync；单进程多个线程用锁串行，fork进程共享对象拒绝。新目录必须不存在，payload首次O_EXCL写，已存在同内容仅可逐字身份匹配后复用，绝不续写旧实验目录。

硬终止、磁盘满或I/O故障无法保证失败尾记录，可能只保留已fsync前缀、sidecar或部分blob；不删除这些证据、不自动续跑或覆盖。归档复制/压缩/hash的真实时间和内存计入原worker外部预算，不能声称零开销或CPU全尺寸预算已验证。

## 5. 本轮验证边界

只做标准库AST parse/compile、小源码身份清单；未 import 本模块执行 constructor、未 import 科学库、未运行任何人工数组/假模型/新编码器/原模型。本轮不重复已有 S20 codec 与接口人工测试。root之后组织明确的小型人工接口检查和不同作者源码审，再随实际集成统一冻结；这些仍不能替代四原组件真实加载、两批原生成、完整9帧/trace/归档一致性和独立结果核验。
