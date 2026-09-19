# S35 原生成接线实现（准备稿）

状态：**SOURCE_WIRING_PREPARED_NOT_EXECUTED**。只写新模块、解析/编译原函数AST和核来源；没有加载模型、读取权重/真实图片/预测数组/GT，没有运行原初始化、Navigator、采样、GA或人工闭环。原S20文件不变。普通观察接线不构成科研创新。

`integrate_original.py` 仅顶层导入标准库。根任务先执行独立本地资源门，再创建记录器/归档器/真实runtime；禁止下载、登录或资源替代。根资源字段由其 `check_resource_gate` 校验，本模块不重复猜测配置或角色规则。

## 根任务接口

```python
result = run_original(
    create_runtime,
    resource_gate=gate,
    check_resource_gate=validate_gate,
    create_trace=create_trace,
    create_archive=create_archive,
    source_manifest=source_manifest,
    evidence_kind="recorded_execution",  # 专用人工协议必须 synthetic_test
)
```

严格顺序：`check_resource_gate(gate)`成功返回matching evidence的mapping → `create_trace(checked)` → `create_archive(checked)` → `create_runtime(checked)`。前三个factory与实际模型加载/输出预算由root合同冻结；缺资源时任何factory都不调用。真实runtime必须返回pipeline、navigator、pipeline_module、image、initial_pose、initial_K，且未初始化。后续延迟导入Torch，用原S20外层no_grad保留GA内部enable_grad；拒绝覆盖它的外层inference_mode。不设置种子/线程/device/training flags，不改root原始配置。

原Navigator.initialize一次、turn_left(5)一次、turn_right(5)一次。返回dict含runtime与这三次原返回对象，以及observation_summary、trace、archive；不替换原返回列表，也不将Navigator.frames的重复初图当第10个历史ID。trace成功路径close；archive交root检查/finalize。故返回状态只叫`OBSERVED_ROUTE_RETURNED_NOT_QUALITY_VERIFIED`，不自动给生成/科研成功。

`install_observers(pipeline, *, navigator, pipeline_module, trace, archive, source_manifest)`另行导出context manager，可用于未来另冻的专用人工接线验证；本轮没有使用假模型执行它。该接口不代替真实资源门。

## 精确插入点

- 从实际S20隔离pipeline源派生`_generate_frames_for_trajectory`。原get_context返回后、原get_cond前建立S20 batch；原do_sample调用只变为`event.sample(原pipeline别名, 原参数)`；原append后、construct前commit_cache；原construct返回后commit_map。全部原语句原次序保留，原global_step/可视化/return也保留。
- 从同一源派生get_context_info，只在三条原initial_threshold赋值之后记录其实际分支局部量，以及最终context tensor生成前记录实际候选、距离排序、NMS选择与阈值。没有新geodesic、render或NMS调用；len1未走分支就没有伪造NMS事件。
- 两个派生函数去掉观察节点、反转sample委托后，均须与原函数全AST一致。运行globals仍绑定原pipeline模块字典，不复制旧别名而漏掉hook。派生代码只生成在内存；原文件不改。该语法证明不能冒称数值/RNG等价已测。
- initialize、get_context、translation scaling、get_cond分别在原调用前后同步归档。get_cond/translation会原地改局部all_c2ws，因此前态必须当时保存，不能等末尾取引用，也不回填历史。
- encode_image、encode_vae_image、run_inference_from_pil挂实际pipeline模块的全局别名。每个原函数委托一次；后者在返回后、consumer进一步处理前归档完整真实scene。原model/AE/CLIP只在未来真实执行时发生。
- sampler使用两层纯委托：S20 event的observed_sampler→新增archive_sampler→原sampler。完整原noise/cond/uc/camera/K/mask/scale与Python/NumPy legacy/Torch CPU随机状态，在原prepare_sampling_loop原地缩放noise前同步保存；再保存原返回与随机状态。不抽噪声、不重播种、不改kwargs或数学。
- 主VMemWrapper.forward、AE顶层encode/decode、CLIPConditioner.forward和Euler sampler_step分别计数。没有替换实例`__call__`这一无效路径；counter只存形状/序号，不保存50步全部激活。Euler步、模型forward、S20 denoiser callback是不同计数，不相互充当。

## 归档协议

另一个作者的 `FullOutputArchive.capture(name,payload)`同步取现有对象的原字节；payload只含明确tensor/ndarray/已load PIL/嵌套树。capture不得延迟保存可变引用，不调用模型或取随机数。

必要事件包括initial_input/output、context_input/output、translation_input/output、condition_input/output、sampler_input/output、sample_output、cache_commit、geometry_input/output、map_commit、render_input/output、retrieval_output、nms_threshold/nms_selection和navigator_begin/return。每项带operation_index/name与当前batch_id；get_context期间尚未建立batch，batch_id为null，用operation身份关联，不预造batch成功。

sample_output保留8槽samples和samples_z；cache_commit包含原完整7/4行target_encoder_embeddings、保留ID/实际contextIDs/padding及完整cache。map_commit显式保存每surfel的位置/法线/半径/颜色/有序来源，另全部depth/focal缓存；原0→5→14焦距累计不修正。initial/cache/nav快照的PIL是原已产生对象，不是重做编码或伪照片。原geometry scene包含point_clouds/colors/depths/confidences/camera_info，无简化替代。

## 异常与验收边界

任何委托或归档失败都停止并抛原异常；S20 batch记录实际失败阶段。所有实例属性/模块别名以逆序恢复，即便安装中途失败也清理。次要清理异常附在原异常上，不能覆盖它。runtime factory失败时也保留operation_failure、archive PARTIAL和可关闭trace前缀。硬kill/磁盘失败可能只能保留前缀，不宣称完整关闭。

根任务负责完整组件加载、真实两批资源监督、最终必要事件/实际计数、九规范历史帧、第二批generated ID确实消费、全输出封存和独立复核。当前只做stdlib源派生AST/compile，不重跑S20成功15项；新接线人工验证须另冻synthetic合同，不能给真实evidence_kind或宣称原50步模型已运行。原合法权重仍缺，实际生成未获执行资格。
