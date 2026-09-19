# S35 原生成接线：不同作者审查要求

记录 UTC：2026-09-06T22:43:04.282113+00:00。状态：**SOURCE_REQUIREMENTS_READY；尚未审完 S35 实现，未运行任何生成。** 本文件仅明确既有 S20 未实现的接线与完整归档门，不新增方法、数据条件或采样预算。0 权重/真实 RGB/GT/预测数组读取，0 模型/GA/人工测试执行；不重跑 S20 已成功的 15 项接口检查。

## 已确认的真实缺口

`work/S20_protocol_review/trace_completion_review.json` 是 `PASS_PREPARATION_MODULE_REVIEW_NOT_INTEGRATED`，其 `not_yet_done` 明列原循环接线与 full output archive。原 `TraceWriter` 的噪声、RNG 和地图有原字节；条件、cache、samples/samples_z 仅身份，PIL 仅长度，dense depth/focal 没完整归档。`VALID_CLOSED_TRACE` 还可以包含失败批次。这些已有记录没有被追认为生成成功。

## 实际必须观察的位置

| 原位置 | 新接线应取到的实际证据 | 必须保持的语义 |
|---|---|---|
| 构造器之前与初始化之后 | 四原组件完整身份/加载入口门；实际初始化 normalized tensor、PIL、VAE latent、CLIP embedding、camera/K 和 ID0 | 缺组件在 `VMemPipeline.__init__` 创建大模型前终止；不得先随机实例化再把缺件标通过。初图与真实编码各一次，专用空 cwd 隔离 Navigator 对 `visualization` 的删除。 |
| `_generate_frames_for_trajectory` 中 `get_context_info` 返回后 | 当时完整缓存、有序选中 ID、cast 后四类 context、原 target/K 与实际 padding | `GenerationBatch` 在原 `get_cond` 前创建；第二批原 Torch 整型 ID 的顺序/重复不得归一化为集合。实际 context 少于4或为空时原失败/协议失败保留，不补假候选。 |
| 原 translation/get_cond 调用前后 | 拼接的原相机/K、translation factor、原函数实际返回 c/uc/处理后相机/mask | 只调用原函数一次。`get_translation_scaling_factor` 和 `get_cond` 原地改变局部 all_c2ws；观察前同步保存副本，返回后另存，不能将临时结果回填历史。 |
| 实际 `do_sample` 与 sampler | 原8槽条件与全部返回 samples/samples_z、实际初始 noise、RNG 前后、步与模型调用 | **实际别名是 pipeline 顶层 `from utils import do_sample`**，不是仅改 `utils.util`。传给 `event.sample` 的 callable 应保留原签名；只委托一次并返回原结果对象。实例特殊方法 `__call__` 的替换不一定被 `obj(...)` 使用，实际目标必须核到。 |
| CLIP 完整 target 输出与原 append 循环之后 | 第1批7行/第2批4行的实际 CLIP 输出；history1→5→9，保留槽对应真实 samples_z/cache | 先原采样、PIL转换、CLIP、append，再 `commit_cache`；首批3 padding全部输出留档但不进历史。不得重编码生成 PIL 伪造 latent。最终9帧取 `pipeline.pil_frames`，不拿 Navigator.frames 的原返回重复初图凑帧数。 |
| `construct_and_store_scene` 前与真实返回后 | scene实际 dense point/conf/depth/focal、map完整字段/有序sources、cache版本；原5图/9图输入与5旧depth来源 | `commit_map` 只在原构图返回后发生；首批全5候选，次批非空图追加尾4。保留原400步、原getter/尺度数学，不能带入 S33/S34 修正。surfel_Ks原0→5→14、depth5→9，不改成9项K。 |
| 第二批原 get_context_info 内部 | render输入/实际render返回、来源票权/配额、候选及距离排序、原10相机对距离、阈值索引5、实际NMS选中结果 | 观察实际局部值或只委托返回，不能额外调用render/process/geodesic/NMS再称“观察”。默认 NMS 在 len5 建立，保留来源首次贡献双加及原舍入。未走到的分支记未观察。 |
| 批次返回、失败与会话结束 | 原返回对象、计数、已完成阶段、完整事件和输出封存；第二批是否真实消费generated ID | 首批采样成功而构图失败仍是部分结果；完整 trace/归档成功不自动是技术生成成功。源缓存已在历史中或地图有generated来源也不等于其进入第二批条件。 |

## 最可能改变语义的陷阱

1. **只挂错别名或只观察预期。** `pipeline.do_sample`、`encode_image`、`encode_vae_image`、`run_inference_from_pil` 都是导入后绑定；挂源模块不代表原调用已截获。若以 AST 插入，应保留未插入原语句并给完整差异/准确定位，所有原调用计数从实际委托取得。sampler回调、Euler steps、VMem主model forward、VAE顶层编码/解码及CLIP调用分别计数，不能互相替代；预期100次主前向不是本轮实测。
2. **改变随机状态或梯度范围。** 原 `prepare_sampling_loop` 会原地放大传入noise；每步仍 `randn_like`，`sigma_hat` 仍有1e-6。入参必须在调用前同步序列化，不能留可变引用等终点再取值。观察不能播种/抽噪声/重跑采样；第二批不重播种。保留 do_sample 局部 inference_mode，外层仅 no_grad，让原几何 enable_grad 生效，不能全局 inference_mode。
3. **归档补算冒充原输出。** 归档只对已有返回/缓存做无修改快照和编码，不新增VAE/CLIP/GA/renderer调用。完整c/uc、cast前后cache、全部8槽samples_z与samples、7/4目标embedding、9规范PIL、dense几何/focal和NMS中间证据有原字节且含dtype/shape/ID映射；有限性按字段检查，世界Z不强制为正。PNG是实际生成tensor/PIL导出，不称实拍。未保存的全50步激活不补造。
4. **异常或退出污染原程序。** 委托异常原样重抛，已保存前缀不覆盖，只有实际append/map完成才写相应commit。with/finally还原模块别名和观察hook；保存失败不能悄悄关闭记录继续跑。完整原模型装载、两批实际完成、真实generated cache进入第二批条件、预算/身份与不同作者结果核验共同成立，才可给技术baseline成功。
5. **资源门与执行状态混淆。** 主任务负责真实本地原权重/loader合同，四组件缺项时 fail-before-load；元数据公开或伪路径不算权重。未来CPU8/每批1800秒45GiB仍须正式冻结，当前不以准备脚本PASS宣布资源可用/生成成功。未齐备资源时可以完成这次接线准备；不能用人工路径升格 `recorded_execution`。

## 最少必要人工验证建议（仅针对新接线，不是当前已执行）

- 一个**真正调用已派生原 trajectory 方法的两批小人工闭环**：人工组件代替模型，比较未观察原入口与新观察入口的委托计数、原返回对象/缓存字节和完整 Python/NumPy/Torch RNG。检查真实 pipeline 别名确被接到、1→5→9、首批padding排除、第二批generated ID来源；同时用小原始数组/PIL回读新archive，核全8槽、条件、dense/cache和元数据原字节。该例只验证新接线/归档，不能叫完整模型或50步复现。
- 一个**中途失败前缀**：原sampler或构图委托按固定位置抛错，确认原错误不吞、后续阶段未调用、已完成输出留存、未发生的map/第二批不写成功，hook恢复且有效关闭日志不晋升生成成功。不必再重复旧ID类型/旧hash篡改15项。
- 主任务的**缺件入口检查**：在当前真实缺项下运行只含资源门的路径，必须在任何权重加载/模型构造前退出，保存明确缺件回执且无生成载荷。若回执声称没有科学库导入，也应按实际调用验证该更窄事实。

以上是三个目的，可合并实现检查，无需为增加数量再拆测试。所有人工证据单独目录、标明 synthetic；实际生成仍要后续合法资源与正式合同。不同作者前审只在实现者给稳定源码/候选SHA后进行一次；不轮询、不自动执行新科学路径。

## 本轮技能与来源范围

应用 Supervisor `vibe-research-workflow` 的小步/明确输入输出/先读原代码，及本地 Claude scientific-critical-thinking 已读的构念与替代解释部分；不调用Claude模型，不声称用户逐句核验或学校披露已完成，不新增审批流程。全量长期历史未重新审，S20成功人工测试未重跑。

下表SHA绑定实际读取版本；“局部”不冒称全文件通读。

| 来源 | 阅读范围 | SHA256 |
|---|---|---|
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S20_MINIMAL_VIDEO_PROTOCOL_DRAFT.md` | 全文 | `02d95bcddd8401e3df397d58269f3dcf6ba479d9cdfc47b446bb556bd52d60ad` |
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S20_GENERATION_TRACE_CONTRACT.md` | 全文 | `d7be737383fa2436d1e6f74aec3ad1505af873a79bb3b001679b1e7fb3d77300` |
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S20_TRACE_INTERFACE_REVIEW.md` | 全文 | `2023ce9a7f9dc5e856d2a5fd1af6fa25f48c929c9770c8c3faeb56665c5e1951` |
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_protocol_review/trace_completion_review.json` | 全文元数据 | `b2e5935492e2a1e257397b7746522e8df5e5038fa3830b8a4878c0bf8a0d3e27` |
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_trace_preparation/preparation_receipt.json` | 全文元数据 | `6f1c268f3a6bbfb4e400186821d9f98716da04acc9eb895cfc18820af7742a18` |
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/src/s20_generation_trace.py` | 1–379：身份、写入器、batch委托与commit；离线verifier仅合同/既有前审范围 | `daf841dbcb635417865ba8287ad305bbdf6105181fd39e169be2e666e1bfbc57` |
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/modeling/pipeline.py` | 1–191、505–770、950–1338：真实alias/init/context/scene/cond/loop | `680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255` |
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/utils/util.py` | 642–739：真实encode/do_sample | `30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e` |
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/utils/__init__.py` | 全文：util导出 | `e20d1aa48f3eddd8b27dd05a04eb7a54a6345865d32bc169c9b6cd4cc1cd476a` |
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/navigation.py` | init/interpolate/turn_left/right/_turn局部，未重审无关导航方式 | `6d267365d5dcccf9f7cd6d535f19f80521f60a9634dffb35b9af398407389fcf` |
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/modeling/sampling.py` | scale rule/CFG及335–443真实Euler循环局部 | `dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24` |
| `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/configs/inference/inference.yaml` | 全文 | `8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3` |
| `/Users/rocket/.codex/skills/vibe-research-workflow/SKILL.md` | 全文 | `c26a9f011cb8e88d6d5000c1b1844db7278334c07e84be4bae7ea8d08084a333` |
| `/Users/rocket/.codex/skills/vibe-research-workflow/references/vibe-coding.md` | 全文 | `0e09e54c3a129f47f93898a40e63174e1953d6d877dc1cf7e8ae2e86a6300f57` |
