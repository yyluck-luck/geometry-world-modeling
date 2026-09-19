# S32 B 不同作者最终源码前审

结论：**PASS_B_SOURCE_PRE_REVIEW**。仅源码、JSON 元数据、AST 派生和新进程 `--help`；本审查没有读取任何预测 NPZ、RGB、sensor-depth PNG 或 GT pose 文本，也没有运行模型、MST、GA、反传。实际数值是否通过仍须由正式 B 运行及后续独立保存量复核判断。

已全文阅读当前 `run_consumer.py`、`prepare_consumer_candidate.py`、B 计划、两份完整派生 diff 与证明；候选内四窗与已封存选择 JSON 完整等值核对。候选控制部分、原 `ga_worker`、`original_context`、`SceneObserver`、原 adapter、S28 observer/getter 派生、S30 observer 适配以及 S31 decompose 已按本次实际调用链核查。较早独立核验的 FP32 clean 与原 pair objective 没有重复执行；本次核其桥接和实际文件 SHA。

关键结论：

1. **来源闭合。** B 不调用旧 `b.manifest()` 全量历史检查，但新候选直接绑定 S26B 父 manifest、runner、adapter、S28/S30/S31 源码、numeric bridge 和两条数学参考。原 `configure_original_geometry` 仍在每可用窗调用，检查继承的 203 项 geometry source，再建立 fresh namespace。原 producer 末尾仍核实际加载 geometry 来源及 overlay 每模块 SHA。独立静态检查复核了全部 27 个直接身份和 203 个继承源码身份；没有再扫描整个依赖树。
2. **三端点同起点。** 一个可用窗口只做一次原 MST。C2a 保留原单次求出的 R0，使用 s=1 与相机中心均值平移；没有声明逐帧完美对齐或真尺度。observer 在任何 Adam 前复制并保存完整 33 项参数/buffer，逐字核自己实际快照和初始 objective；改 getter 后对象、flags、深度 forward 与 objective 均逐字保持。零步端点从这份实际保存的 initial_decoded 取 depth，不借用旧 S29 producer 或伪造原清理。
3. **原优化和独立门保留。** 新 worker AST 只有 guard、n=4 与 archive route 改动。修 getter 的 S30 observer 逻辑仍要求四个 depth.grad 每步非 None/finite，400 原 Adam、400 原迭代记录、400 梯度记录、1 MST、3 PnP、1 clean。两次 getter 边界 no-grad objective 加 400 优化及 1 postfinal 为 403；该计数来自已审调用链，不是新加求值。原固定相机/pp、优化器对象及成员、clean 全像素 exact、独立原目标、反投影、wrapper colors/source 来源门都在。
4. **新窗口输入正确。** 只读该窗 A 四份六头存档，核 frame index、RGB SHA 和 anchor=0，依原 star 消费首帧 self 与其余 other。B 原 PIL 四 img/true_shape 与 A 已保存预处理逐字比较，再复用同一批核过的 views。给定相机按冻结 timestamp 从已允许 optical c2w 文本取得，不加 Y/Z 翻转；sensor-depth 不参与任何 B 计算。
5. **普通单标量。** 直接调用固定 S31 decompose，本窗所有 786,432 个初/末深度像素求一个 k，没有 GT、pose、conf、删点、逐帧 k 或 shift。前两端点 FP32，归一端点 FP64；它只输出 depth，没有声称改过 world 或 optimizer state。
6. **完整失败分母。** fr2_desk_j1 在导入 Torch/读数组/相机文本前写 UNAVAILABLE。其余固定窗必须整窗成功后才有三端点 PASS；任何 worker 或外控失败都保留部分产物并将三端点统一不可用，不重复成功窗口。外控按 CPU8、每窗 120 秒/4 GiB 顺序运行；最后封存全部四份终态回执，评分仍是另一阶段的 48 行/12 组。

最小入口检查实际通过：两个新文件 AST/compile、两项派生的原/新 AST 与完整 diff 重建、candidate 提前拒绝执行、已有 Python 新进程 `--help` exit 0。未启动 B；此时 `PASS` 只允许根任务冻结当前版本，不能作为真实实验或创新结论。

保留的局限：这些是给定相机下首次四帧消费者的普通对照；不覆盖 old4→new4、surfel 检索或视频。S32 的原 inference/eval 入口不同于 S21 的 recurrent 路径，跨 S30/S32 变化不能只归因窗口；下一结论应比较 S32 同窗三端点。三可用窗若都完成，才有 36 实测行与固定 12 NA；任何额外失败都保留原分母，不取 available-case 均值。

精确审查时间、当前源码/候选 SHA、完整受审身份及实际访问边界见同目录 `B_final_pre_review.json` 和 `B_source_check_receipt.json`。
