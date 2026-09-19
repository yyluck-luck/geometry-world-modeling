# S80 新观察器源码交付（待 root 核读）

实际开始实现：2026-09-10T15:33:34Z。交付记录时间：2026-09-10T15:44:22.376683+00:00。

本次仅编写合同与程序，并完成一次合成算术/语法自测。**0 原图读取、0 特征提取、0 新模型加载、0 LightGlue 推理**。setup_01 的此前组件加载保持原记录，不重写为本次实验。禁止在 root 完整核读这两个精确 SHA 前启动。

## 冻结内容

- RUN_CONTRACT.json：ba89adbcdd246e60c02d75a5e1ca29c7db202a607885ccb4f48c0d3b50a14251（19633 字节）。
- run_observer.py：99b65cde2e0604b7179907e9a40e52d6d5240c7c670290ad5232a4e6f44a68cd（26024 字节）。
- SOURCE_SELFTEST_01.json：196177a1f9badc3161cd27d9cd7041aa0bb720cfee3623680d58e518d3a2b10c。

合同绑定已有回执中的全部 13 张原评分 PNG 路径/字节数/SHA；本次只检查路径存在，运行才核原图字节。一次提取 13 份官方 RootSIFT，再由 BF 和 LG 共用同样完整数组，按 target20→23、real/A0/B、BF→LG 顺序写 24 行。新提取器不等于 S73 旧特征，旧 S73/S77 不改。

官方 SIFT 的 num_octaves=4 在 opencv backend 对应 nOctaveLayers=4，first_octave 参数在该 backend 不使用。nms_radius=0 仍执行官方像素去重。resize=None；尺度沿用 OpenCV keypoint.size，方向为弧度，描述子为官方 RootSIFT。两匹配器的完整 matches0/1 和各自分数语义分别保存；LG 仅按 indices>=0 接受，不能按正分数筛选。

BF 使用严格双向 ratio .75 及互选；LG CPU FP32、9 层、4 heads、无自适应/flash/mp，filter .1。只从已验证本地权重 bytes 用 weights_only=True 加载，按官方规则重命名旧键。每个学习参数必须存在、FP32 且与 checkpoint tensor 精确相等；仅允许缺少非学习 confidence_thresholds buffer。运行时显式构造 features=None/weights=None 并禁 torch.hub 隐式下载。

固定 S72 F 只在接受匹配全部保留之后计算原标签和固定交换标签的残差，含各方向距离、均值、有效掩码、所有分位/2、5、10px计数、分母、覆盖、逐点配对差。没有几何筛选和科学成功阈值。零匹配统计为空；特征空/提取异常为 missing，未知 N 不填 0。每份原始 matcher 输出在后续验证/评分前保存，错误和中断留档。

## 有界启动方式（本交付未执行）

root 阅读接受后，可调用下列唯一正式入口；输出目录必须全新，已有 execution_01 会被拒绝覆盖，不会续跑或自动重试：

```sh
'/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python' -B '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S80_lightglue_observer/run_observer.py' --execute --contract-sha ba89adbcdd246e60c02d75a5e1ca29c7db202a607885ccb4f48c0d3b50a14251 --source-sha 99b65cde2e0604b7179907e9a40e52d6d5240c7c670290ad5232a4e6f44a68cd --output execution_01
```

同一文件的薄监督分支启动 worker，进程树每 0.5 秒加 ps 开销采样；外部 600 秒、采样 RSS 超 8 GiB 则停止。**8 GiB 不是瞬时硬内存保证**，退出清理最多另有 3 秒等待和有界 ps 开销。运行限定 Torch2 线程/OpenCV1 线程、seed80。参数/解释器/依赖版本/源和输入身份不同则失败，不自行改合同。

输出包含 STARTED/EXTERNAL_RECEIPT、逐行监视、stdout/stderr、组件参数身份、全特征 NPZ、全 matcher 原始 NPZ、包含坐标与正确/错标签残差的 pair NPZ、每 pair JSON、最终 ROWS.json 的全部24行和 worker receipt。中断可能没有最终汇总，以外部终态和已封存的增量记录为准；不能把缺少 receipt 当成已完成。COMPLETE_DESCRIPTIVE_ONLY 仅表示程序完成，不表示 matcher 更准或新方法成立。

## 实际自测范围

SOURCE_SELFTEST_01：2026-09-10T15:43:04.127685Z–15:43:04.224250Z，外部 0.096435 秒，return0，AST PASS。只用 NumPy 合成数组核双向极线公式、F 符号/尺度不变性、零 F/空集、分位数、严格 ratio 边界、重复零距离/非互选拒绝、正分数拒绝点不被接受及覆盖格。没有运行 OpenCV 特征提取或原图/模型。本自测不替代 root 源码审查或实际结果的独立复算。

停止扩大工程：本文件交付后不自行加载图片或测试真实模型；root 审查只需检查合同—实际源码—官方接口一致性与资源/失败记录，再决定是否执行一次新观察器测量。
