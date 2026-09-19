# S32 完整评分与缺失值协议（候选，未执行）

当前仅源码/元数据准备，0 RGB/预测 NPZ/sensor-depth PNG 字节读取，0科学计算或模型/GA。使用既有 Supervisor 基线与完整负结果原则、已读 Claude scientific-critical-thinking 的分母/证据边界。评分复用冻结 `scripts/score_s26b_consumer.py` 中原 `load_sensor_depths`、`depth_metrics`、`aggregate`；之后由另一实现复算。本文件不会把候选准备说成实测 PASS。

## 固定域与输入接口

主域固定四窗口 `fr2_desk_j1/fr2_desk_j2/fr1_xyz_j1/fr1_xyz_j2`，每窗三个端点 `initial_0step/corrected_getter_400/global_rescaled_400`，每端点四帧：**12 组、48 行**。原元数据选择 SHA 为 `4574c2635851e83f5389da0d099819e7cbfd2ad9b8fe543ddf163e0fbf7e6cc6`；root 后续实际封存 RGB 的派生文件 `work/S32_input_freeze/selected_windows_rgb_sealed.json` SHA 为 `ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318`，生产回执使用后一 SHA。两者都绑定并核原起点/逐帧时间配对不变，不得混用身份。每窗是首次四帧消费者，不是 old4→new4 完整链。

`manifest_candidate.json` 含 selection_path/sha、windows、endpoints、control_sha256、output_root、resource 与 upstream_seal_receipts。每窗 `id/availability/reason/producer_receipt/frames/endpoints`。frames 固定 index/rgb_time/depth_time/depth_path/depth_sha256；该 SHA 当前为 null，root 只能在所有端点终态封存后实际读取图片字节产生。可用端点只接受原 NPZ 的 depth 键，前两个 FP32、单标量端点 FP64，全部 4×384×512，**不将 FP64 下转**。

共享整窗回执：`producer_receipt={path,sha256}`；真实回执须有 `status/window_id/selection_sha256/outputs`，其中 PASS 的 outputs 是相对其目录的文件名→SHA，覆盖三端点。一个 PASS 绑定三端点；若整窗 GA FAILED，三端点统一不可用，不评分未有独立 PASS 的初态半成品。失败回执同样须带 window_id/selection_sha256。UNAVAILABLE 端点的 path/sha 均为 null，不能指向未完成数组。

availability 仅正式允许 `AVAILABLE`、`UNAVAILABLE_MISSING_POSE`、`UNAVAILABLE_PRODUCER_FAILED`。fr2_desk_j1 固定为缺 pose，三个端点共 **12 行 NA**，由 B 的 `UNAVAILABLE` 元数据回执记录，不可补相机/插值/换窗。其他窗口必须实际 PASS 或实际 FAILED；全部四份回执终态先封存，PENDING/RUNNING 不得伪装失败或提前结算。upstream_seal_receipts 是 root 对端点/GT 字节冻结顺序的带 SHA 证据清单；此评分器复核其身份，不冒称独立重建这些历史事件。

## 封存和一次解码

1. 先验证选择、代码/协议/原评分源码、全部窗口终态回执、每个 PASS 的全部产物和三端点 SHA。FAILED 半成品完全不读。写 prediction_input_seal 后，才解码可用预测；任何源、哈希或数组 dtype/shape 不符，评分整体 FAIL 保留，不悄悄记成科学 NA。
2. 所有可用端点已封存后，本评分器才读 GT。每个需要评分的帧按原全域配对使用同一 sensor 文件；预 hash 完全部所需 GT，再调用原 loader，每张图片解码一次，三个端点复用。不能为了缺 pose 的窗口解码 GT 凑像素统计；若其他窗口终态失败也不读该窗 GT。最多 12 张（当前三个 pose 可用窗口），可能因终态失败更少。
3. root 生成 manifest 的 sensor SHA 时已经读过字节；该过程须在端点封存后单独记录。这里“未读”只约束本评分器自身顺序，不恢复盲测状态。原 loader 为保持冻结源码不改会重读先前预 hash 的 PNG 字节，不能把一次解码说成一次文件读取。RGB 图片完全不属于评分器读取范围。

## 数值与 NA 的不同含义

原 sensor 480×640 整数 PNG，除 5000 得米，中心最近邻到 384×512；GT 正有限像素为唯一分母。无远点截断、conf筛选或GT尺度拟合。有效 GT 上任一无效预测使该帧 AbsRel/RMSE 为 null，严格 δ1 仍以全部有效 GT 作分母；空 GT 的指标按原代码 null。它们是已评分数组的无效/空 GT，**不同于尚无预测或无配对的 NA**。

缺窗/缺关联行保留固定 window_id/endpoint/index、具体原因、预定 grid_pixels=196608；未观测的 GT/预测计数为 null，不能填 0 冒充已读空图或全坏预测。NA 行不调用度量函数。现有数据的 sensor 时间配对都是完整的，但这不保证解码后的有效像素覆盖。

每组始终四帧等权：只有该指标四帧全部有定义才给均值，否则 null；每个指标保留 defined_frames。完整组直接调用原 aggregate。含缺失行的包装遵循同一公式，保留完整和已知的计数分别命名（sum_descriptive 遇未知为 null；known_sum_descriptive 只描述已观测部分），绝不将未知计数算 0。缺失帧、空 GT 帧、无效预测帧分别列出。

总主分母是**四个预定窗口**，不是实际跑通数；端点的 all_four_prespecified 等窗均值需四窗全定义，因此本轮因固定缺 pose 应保持 NA。另给清楚标注的 three_preselected_pose_eligible 描述，它固定另外三窗，在新运行前已经确定；其中任一失败/缺失也使该三窗均值 NA，不能临时改成两窗均值。每窗三控与全部胜负是核心读数，不能只报成功窗平均。四窗存在场景和时间关联，像素/帧不能作为独立样本做显著性检验。

输出 per_frame.csv 全48行、metrics.json 全12组与两种明确的窗级汇总、预测/GT封存回执、PASS/FAILED receipt。表完成 PASS 只表示评分程序和缺失表按规则完成，不表示12组都实测成功、更不表示任何方法改善。身份/数值实现故障会整体 FAIL 并保留中间文件，不自动重跑或降门槛。

## 运行边界

根任务审后另冻 manifest，通过显式 `--manifest --sha256` 单次调用；已有输出目录拒绝覆盖。建议外控 CPU1/180 秒/2 GiB RSS，线程环境在 NumPy 导入前固定 1。源码不导入模型、GA 或 Torch，也不运行反传。产物目录 `results/S32_consumer_scoring`。当前候选含 PENDING 与空 SHA，严格不可执行。
